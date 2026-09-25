CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sale_date TEXT NOT NULL,       -- ISO date, e.g. '2024-01-15'
    region TEXT NOT NULL,          -- 'North', 'South', 'East', 'West'
    revenue REAL NOT NULL,
    quarter TEXT NOT NULL          -- 'Q1', 'Q2', 'Q3', 'Q4'
);

CREATE TABLE IF NOT EXISTS customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    region TEXT NOT NULL,
    signup_date TEXT NOT NULL,
    churn_date TEXT               -- NULL if the customer is still active
);
