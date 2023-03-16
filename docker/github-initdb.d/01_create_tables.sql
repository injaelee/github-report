-- connect to the 'eksignaldb' database
--
\c rxgithubdb;

-- Github Pull Request Info
--
CREATE TABLE rxgithub.pull_request_info (
  repo_tag         VARCHAR(512) NOT NULL,
  pr_num           INT NOT NULL,
  author           VARCHAR(512) NOT NULL,
  state            VARCHAR(12) NOT NULL,
  additions        INT NOT NULL,
  deletions        INT NOT NULL,
  review_comments  INT NOT NULL,
  created_at       TIMESTAMP NOT NULL,
  merged_at        TIMESTAMP,
  closed_at        TIMESTAMP,
  url              VARCHAR(1024) NOT NULL,
  PRIMARY KEY (repo_tag, pr_num)
);

-- Github Pull Request Comments
--
CREATE TABLE rxgithub.pull_request_comment (
  repo_tag      VARCHAR(512) NOT NULL,
  pr_num        INT NOT NULL,
  comment_id    BIGINT NOT NULL,
  login         VARCHAR(512) NOT NULL,
  state         VARCHAR(28) NOT NULL,
  submitted_at  TIMESTAMP NOT NULL,
  url           VARCHAR(1024) NOT NULL,
  PRIMARY KEY (repo_tag, pr_num, comment_id)
);

-- Github PR Assignments
--
CREATE TABLE rxgithub.pull_request_assignment (
    repo_tag         VARCHAR(512) NOT NULL,
    pr_num           INT NOT NULL,
    assignment_type  VARCHAR(10) NOT NULL,
    name             VARCHAR(512) NOT NULL,
    name_type        VARCHAR(10) NOT NULL,
    PRIMARY KEY (repo_tag, pr_num, assignment_type, name)
)