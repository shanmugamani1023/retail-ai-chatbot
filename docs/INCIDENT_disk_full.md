# 🚨 Runbook: GCP VM Full Disk → Bot Down + SSH Locked Out

**Incident date:** 2026-07-16 · **VM:** `retail-bot` (project `ai-retail-chatbot`, zone `asia-south2-a`)

---

## The Problem

- **Symptom 1:** Telegram bot replied *"Sorry, I'm having trouble right now. Please try again in a moment."*
- **Symptom 2:** Could not SSH into the VM — *"SSH authentication has failed."*
- **Root cause:** the **10 GB boot disk filled to 100%** over ~10 days, from:
  - Docker **container logs** growing unbounded (biggest culprit)
  - Old **Docker image layers** left from `--build` rebuilds
- **Why it deadlocked:** a 100%-full Linux disk cannot write *anything* — not the SSH
  key (→ SSH auth fails), not app logs (→ bot errors), not even the OS auto-resize tool
  (→ reboots didn't help).

## Why the simple fixes failed

| Attempt | Why it didn't work |
|---|---|
| Reset/reboot the VM | Disk still full — nothing freed. |
| Resize disk 10 → 30 GB in console | The *disk* grew, but the *filesystem/partition* stayed 9.9 GB. Ubuntu's auto-grow needs free temp space to run — and there was none. |
| Startup scripts (`growpart`, prune) | Couldn't even run — no space to write the script to disk. |

**Diagnosis proof (serial console):** `OSError: [Errno 28] No space left on device` and
`No usable temporary directory found in ['/tmp', '/var/tmp', '/usr/tmp', '/']`.

---

## ✅ The Solution — "Rescue Disk" Method

**Key idea:** run the repair from a **healthy** VM (whose `/tmp` has space), not the
broken one. All steps done via the `gcloud` CLI from the laptop.

### 0. Setup (one-time)
Cloud Shell was blocked on the network (`shell.cloud.google.com refused to connect`),
so gcloud was installed locally:
```powershell
winget install --id Google.CloudSDK -e
gcloud auth login
gcloud config set project ai-retail-chatbot
```
> gcloud path on this box: `C:\Users\shanm\AppData\Local\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd`
> (gcloud SSH logs in as user `shanm`; the app repo lives under `/home/shanmugamanimeyialagan/retail-ai-chatbot`).

### 1. Resize the disk
GCP Console → **Compute Engine → Disks → `retail-bot` → Edit → Size 10 → 30 GB → Save.**
(Or `gcloud compute disks resize retail-bot --size=30 --zone=asia-south2-a`.)

### 2. Stop the VM + detach its disk
```bash
gcloud compute instances stop retail-bot --zone=asia-south2-a
gcloud compute instances detach-disk retail-bot --disk=retail-bot --zone=asia-south2-a
```

### 3. Create a rescue VM + attach the full disk to it
```bash
gcloud compute instances create rescue-vm --zone=asia-south2-a --machine-type=e2-small \
  --image-family=ubuntu-2204-lts --image-project=ubuntu-os-cloud
gcloud compute instances attach-disk rescue-vm --disk=retail-bot --zone=asia-south2-a
```

### 4. Grow the filesystem (from the rescue VM)
SSH in and check `lsblk` — the attached disk appears as `/dev/sdb` (its full partition is `/dev/sdb1`):
```bash
gcloud compute ssh rescue-vm --zone=asia-south2-a
# on the rescue VM:
lsblk                          # confirm the disk is /dev/sdb, partition /dev/sdb1
sudo growpart /dev/sdb 1       # partition 9.9 GB -> 29.9 GB
sudo e2fsck -fy /dev/sdb1      # check the filesystem (safe: not mounted)
sudo resize2fs /dev/sdb1       # grow the filesystem to fill the partition
lsblk /dev/sdb                 # verify sdb1 is now ~29.9 GB
```

### 5. Put the disk back + restart the bot
```bash
gcloud compute instances detach-disk rescue-vm --disk=retail-bot --zone=asia-south2-a
gcloud compute instances attach-disk retail-bot --disk=retail-bot --boot --zone=asia-south2-a
gcloud compute instances start retail-bot --zone=asia-south2-a
```
Containers auto-start (`restart: unless-stopped`). Verify:
```bash
gcloud compute ssh retail-bot --zone=asia-south2-a
df -h /                        # should show ~29 GB with free space
sudo docker ps -a              # all 5 containers Up
```

### 6. Clean up
```bash
gcloud compute instances delete rescue-vm --zone=asia-south2-a
gcloud compute instances remove-metadata retail-bot --zone=asia-south2-a --keys=startup-script
```

**Result:** partition 9.9 GB → 29.9 GB, all 5 containers back, **all data intact.**

---

## 🛡️ Prevention (applied 2026-07-16)

Cap Docker logs so they can never fill the disk again. On the VM:
```bash
sudo tee /etc/docker/daemon.json >/dev/null <<'EOF'
{ "log-driver": "json-file", "log-opts": { "max-size": "10m", "max-file": "3" } }
EOF
sudo truncate -s 0 /var/lib/docker/containers/*/*-json.log   # clear existing bloat
sudo systemctl restart docker
cd /home/shanmugamanimeyialagan/retail-ai-chatbot
docker compose -f docker-compose.prod.yml up -d --force-recreate   # so containers inherit it
# verify:
docker inspect retail-ai-chatbot-bot-1 --format '{{json .HostConfig.LogConfig}}'
# -> {"Type":"json-file","Config":{"max-file":"3","max-size":"10m"}}
```

> **NOTE:** `daemon.json` lives on the VM only, not in git. For a fresh redeploy, either
> re-add it, or bake the `logging:` block into `docker-compose.prod.yml` per service:
> ```yaml
> logging:
>   driver: "json-file"
>   options: { max-size: "10m", max-file: "3" }
> ```

Routine cleanup when disk creeps up:
```bash
docker system prune -af           # remove unused images + build cache
sudo journalctl --vacuum-size=50M # trim system logs
df -h /
```

---

## 💡 Key Lessons

1. **A full disk breaks SSH** — the guest agent can't write your key. "SSH auth failed"
   on a healthy VM often means **disk full**. Check the **serial console** for
   `No space left on device`.
2. **Resizing a disk ≠ resizing the filesystem.** After growing the disk you must run
   `growpart` + `resize2fs`, and if the disk is full you must do it from a rescue VM.
3. **Always cap Docker logs in production** — the default `json-file` driver grows forever.
4. **10 GB is too small** for a 24/7 Docker stack. Use **30 GB+**.
5. **Cloud Shell blocked?** Install `gcloud` locally and drive everything from your laptop.
