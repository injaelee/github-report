CREATE EXTENSION IF NOT EXISTS pgcrypto;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- create the 'rxcliodev' database
--
CREATE DATABASE rxgithubdb;
\c rxgithubdb;


-- create schema 'rxgithub'
--
CREATE SCHEMA IF NOT EXISTS rxgithub;

-- create the rxobs user
--
CREATE USER rxobs WITH ENCRYPTED PASSWORD 'passw0rd';
GRANT USAGE ON SCHEMA rxgithub TO rxobs;
