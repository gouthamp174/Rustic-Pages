DROP TABLE IF EXISTS reviews;
DROP TABLE IF EXISTS books;
DROP TABLE IF EXISTS users;

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  user_name VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(128) NOT NULL,
  password_salt VARCHAR(128) NOT NULL,
  first_name VARCHAR NOT NULL,
  last_name VARCHAR NOT NULL
);

CREATE TABLE books (
  id SERIAL PRIMARY KEY,
  isbn VARCHAR(20) NOT NULL UNIQUE,
  title VARCHAR(100) NOT NULL,
  author VARCHAR(100),
  published INTEGER
);

CREATE TABLE reviews (
  id SERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  book_id INTEGER REFERENCES books,
  user_id INTEGER REFERENCES users,
  rating NUMERIC(3,2) NOT NULL CHECK (rating >= 0.00 AND rating <= 5.00),
  title VARCHAR(100) NOT NULL,
  review VARCHAR(300) NOT NULL,
  UNIQUE (book_id, user_id)
);
