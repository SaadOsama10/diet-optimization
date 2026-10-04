-- Minimal schema used by the optimizer (portable across SQLite and MySQL).
-- Only the columns the code reads are kept; no names, usernames or password hashes.

CREATE TABLE foods (
  id INT PRIMARY KEY,
  name VARCHAR(200),
  foodGroupId INT,
  cost DOUBLE,
  preference DOUBLE,
  preparingTime DOUBLE,
  cookingTime DOUBLE,
  co2 DOUBLE
);

CREATE TABLE nutrients (
  id INT PRIMARY KEY,
  name VARCHAR(100)
);

CREATE TABLE food_nutrients (
  foodId INT,
  nutrientId INT,
  quantity DOUBLE
);

CREATE TABLE dri (
  nutrient_id INT,
  low_age INT,
  up_age INT,
  gender VARCHAR(10),
  RLL DOUBLE,
  RUL DOUBLE
);

CREATE TABLE user (
  id INT PRIMARY KEY,
  age INT,
  gender VARCHAR(20)
);

CREATE TABLE user_foods (
  userId INT,
  foodId INT,
  preference DOUBLE
);
