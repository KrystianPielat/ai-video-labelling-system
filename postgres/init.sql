CREATE USER auth_user WITH PASSWORD 'Auth123';

CREATE DATABASE auth;

\c auth;

GRANT ALL PRIVILEGES ON DATABASE auth TO auth_user;


CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

GRANT ALL PRIVILEGES ON TABLE users TO auth_user;

INSERT INTO users (email, password) VALUES ('krystian.pielat@onet.pl', 'Admin123');
