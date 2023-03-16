-- connect to the 'rxgithubdb' database
--
\c rxgithubdb;


-- grant access
--
GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA rxgithub TO rxobs;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA rxgithub TO rxobs;