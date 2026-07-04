-- Handy queries to explore the retail catalog in your SQL tool.
-- (The `products` table appears after running Phase 1 ingestion:
--    python -m src.ingest )

-- Sanity check
SELECT version();

-- See everything
SELECT * FROM products ORDER BY id;

-- How many products total?
SELECT COUNT(*) AS total_products FROM products;

-- Stock of a specific product (semantic match on name)
SELECT name, stock, price FROM products WHERE name ILIKE '%pepsi%';

-- Cheapest 5 items
SELECT name, price FROM products ORDER BY price ASC LIMIT 5;

-- Products under Rs.50 that are in stock
SELECT name, price, stock FROM products WHERE price < 50 AND stock > 0 ORDER BY price;

-- Count of products per category
SELECT category, COUNT(*) AS items FROM products GROUP BY category ORDER BY items DESC;

-- Total inventory value (price * stock) per category
SELECT category, SUM(price * stock) AS inventory_value
FROM products GROUP BY category ORDER BY inventory_value DESC;
