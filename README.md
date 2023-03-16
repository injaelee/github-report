# Data Extraction
## Execute
```bash
python pr_data_pull.py \
--from_date 2020-01-01 \
--to_date 2023-03-01 \
--repo XRPLF/rippled > 20200101.20230301.tsv
```

# To Individual Table Input Files
## Filter Content of Output

```bash
cat 20200101.20230301.tsv | \
grep PRINFO | \
cut -f2,3,4,5,6,7,8,9,10,11,12 \
> docker/data/20200101.20230301.pull_requests.tsv
```

```bash
cat 20200101.20230301.tsv | \
grep PRCOMMENT | \
cut -f2,3,4,5,6,7,8 \
> docker/data/20200101.20230301.pull_request_comments.tsv
```

```bash
cat 20200101.20230301.tsv | \
grep PRASSIGNMENT | \
cut -f2,3,4,5,6 \
> docker/data/20200101.20230301.pull_request_assignments.tsv
```

# PostgreSQL
## Loading CSV
```sql
-- PG specific
--
COPY rxgithub.pull_request_info(
    repo_tag,
    pr_num,
    author,
    state,
    additions,
    deletions,
    review_comments,
    created_at,
    merged_at,
    closed_at,
    url
)
FROM '/pg/data/20200101.20220101.pull_requests.tsv'
DELIMITER E'\t' NULL '';
```

```sql
-- PG specific
--
COPY rxgithub.pull_request_comment(
    repo_tag,
    pr_num,
    comment_id,
    login,
    state,
    submitted_at,
    url
)
FROM '/pg/data/20200101.20220101.pull_request_comments.tsv'
DELIMITER E'\t' NULL '';
```

```sql
-- PG specific
--
COPY rxgithub.pull_request_assignment(
    repo_tag,
    pr_num,
    assignment_type,
    name,
    name_type
)
FROM '/pg/data/20200101.20220101.pull_request_assignments.tsv'
DELIMITER E'\t' NULL '';
```

# LINE CHANGES
```sql
WITH raw_line_change_cte AS (
    -- obtain the raw line changes 
    -- by year, author
    --
    SELECT
      DATE_PART('year', created_at) AS created_year,
      author,
      SUM(additions) + SUM(deletions) AS total_line_changes
    FROM
      rxgithub.pull_request_info
    GROUP BY
      1, 2

), ranked_cte AS (
    -- rank the authors by line changes 
    -- for each year
    --   rank 1 being the most changes
    --
    SELECT
      created_year,
      author,
      total_line_changes,
      RANK() OVER (
        PARTITION BY
          created_year
        ORDER BY
          total_line_changes DESC
      ) AS rank
    FROM
      raw_line_change_cte

)
SELECT
  created_year,
  author,
  total_line_changes,
  rank
FROM
  ranked_cte
ORDER BY
  1, 4 ASC
-- put WHERE clause here to filter based on RANK
--
```

# LINE CHANGE PER PR
```sql
WITH raw_line_change_cte AS (
    -- obtain the 
    --   raw line changes
    --   unique PR contributions
    --   LINE CHANGE / PR contribution ratio
    -- by year, author
    --
    SELECT
      DATE_PART('year', created_at) AS created_year,
      author,
      COUNT(DISTINCT pr_num) AS pr_count,
      SUM(additions) + SUM(deletions) AS total_line_changes,
      (SUM(additions) + SUM(deletions)) / COUNT(DISTINCT pr_num) AS lc_per_pr
    FROM
      rxgithub.pull_request_info
    GROUP BY
      1, 2

), ranked_cte AS (
    -- rank by LINE CHANGE per PR ratio
    -- with rank 1 being the higest ratio
    --
    SELECT
      created_year,
      author,
      pr_count,
      total_line_changes,
      lc_per_pr,
      RANK() OVER (
        PARTITION BY
          created_year
        ORDER BY
          lc_per_pr DESC
      ) AS rank
    FROM
      raw_line_change_cte

)
SELECT
  created_year,
  author,
  pr_count,
  total_line_changes,
  lc_per_pr,
  rank
FROM
  ranked_cte
ORDER BY
  1, 6 ASC
-- put WHERE clause here to filter based on RANK
--
```

# PR STATS
```sql
SELECT
  DATE_PART('year', created_at) AS created_year,
  SUM(additions) + SUM(deletions) AS total_line_changes,
  COUNT(DISTINCT author) AS author_count,
  COUNT(DISTINCT pr_num) AS pr_count,
  (SUM(additions) + SUM(deletions)) / COUNT(DISTINCT pr_num) AS lc_per_pr
FROM
  rxgithub.pull_request_info
GROUP BY
  1
```

# PR PARTICIPATION WITH FILTER
```sql
WITH pr_meta_filtered_cte AS (

    SELECT
      pr_num,
      author,
      state,
      additions,
      deletions,
      review_comments,
      created_at,
      merged_at,
      closed_at,
      url
    FROM
      rxgithub.pull_request_info
    WHERE
         additions + deletions > 16
      AND state = 'closed'
      AND merged_at IS NOT NULL

), pr_interested_cte AS (

    SELECT
      prc.pr_num,
      prc.login,
      prc.state,
      prc.submitted_at,
      filtered.created_at AS pr_created_at,
      prc.url
    FROM
      rxgithub.pull_request_comment AS prc
      JOIN
      pr_meta_filtered_cte AS filtered
      ON
         prc.pr_num = filtered.pr_num

), distinct_pr_user_cte AS (

    SELECT
      DISTINCT
        DATE_PART('year', pr_created_at) AS pr_created_year,
        pr_num,
        login
    FROM
      pr_interested_cte
    WHERE
      state IN ('COMMENTED', 'APPROVED', 'CHANGES_REQUESTED')
), pr_count_by_year_cte AS (

    SELECT
      pr_created_year,
      COUNT(DISTINCT pr_num) AS pr_count
    FROM 
      distinct_pr_user_cte
    GROUP BY
      1
)
SELECT
  pr_user.pr_created_year,
  pr_user.login,
  pr_cnt.pr_count,
  COUNT(*) AS commented_pr_count,
  ROUND(
    1.0 * COUNT(*) / pr_cnt.pr_count,
    4
  ) AS participation_perc
FROM
  distinct_pr_user_cte pr_user
  LEFT JOIN
  pr_count_by_year_cte pr_cnt
  ON
     pr_user.pr_created_year = pr_cnt.pr_created_year
GROUP BY
  1, 2, 3
ORDER BY
  1, 4 DESC
```

# PR PARTICIPATION WITH NO FILTER
```sql
WITH pr_meta_filtered_cte AS (

    SELECT
      pr_num,
      author,
      state,
      additions,
      deletions,
      review_comments,
      created_at,
      merged_at,
      closed_at,
      url
    FROM
      rxgithub.pull_request_info

), pr_interested_cte AS (

    SELECT
      prc.pr_num,
      prc.login,
      prc.state,
      prc.submitted_at,
      filtered.created_at AS pr_created_at,
      prc.url
    FROM
      rxgithub.pull_request_comment AS prc
      JOIN
      pr_meta_filtered_cte AS filtered
      ON
         prc.pr_num = filtered.pr_num

), distinct_pr_user_cte AS (

    SELECT
      DISTINCT
        DATE_PART('year', pr_created_at) AS pr_created_year,
        pr_num,
        login
    FROM
      pr_interested_cte
    WHERE
      state IN ('COMMENTED', 'APPROVED', 'CHANGES_REQUESTED')
), pr_count_by_year_cte AS (

    SELECT
      pr_created_year,
      COUNT(DISTINCT pr_num) AS pr_count
    FROM 
      distinct_pr_user_cte
    GROUP BY
      1
)
SELECT
  pr_user.pr_created_year,
  pr_user.login,
  pr_cnt.pr_count,
  COUNT(*) AS commented_pr_count,
  ROUND(
    1.0 * COUNT(*) / pr_cnt.pr_count,
    4
  ) AS participation_perc
FROM
  distinct_pr_user_cte pr_user
  LEFT JOIN
  pr_count_by_year_cte pr_cnt
  ON
     pr_user.pr_created_year = pr_cnt.pr_created_year
GROUP BY
  1, 2, 3
ORDER BY
  1, 4 DESC
```

# PR EVENTS
```sql
WITH raw_event_data_cte AS (

    SELECT 
      DATE_PART('year', submitted_at) AS event_year,
      state AS event, 
      login AS author,
      COUNT(DISTINCT pr_num) AS unique_pr_count,
      COUNT(*) AS raw_event_count
    FROM 
      rxgithub.pull_request_comment 
    GROUP BY 
      1, 2, 3

)
SELECT
  event_year,
  event,
  author,
  unique_pr_count,
  raw_event_count,
  RANK() OVER (
    PARTITION BY
      event_year
    ORDER BY
      unique_pr_count DESC
  ) AS rank
FROM
  raw_event_data_cte
ORDER BY
  1, 2, 6 ASC
```

# PR EVENTS - MONTHLY
```sql
WITH raw_event_data_cte AS (

    SELECT 
      DATE_PART('year', submitted_at) AS event_year,
      DATE_PART('month', submitted_at) AS event_month,
      state AS event, 
      login AS author,
      COUNT(DISTINCT pr_num) AS unique_pr_count,
      COUNT(*) AS raw_event_count
    FROM 
      rxgithub.pull_request_comment 
    GROUP BY 
      1, 2, 3, 4

)
SELECT
  event_year,
  event_month,
  event,
  author,
  unique_pr_count,
  raw_event_count,
  RANK() OVER (
    PARTITION BY
      event_year, event_month
    ORDER BY
      unique_pr_count DESC
  ) AS rank
FROM
  raw_event_data_cte
ORDER BY
  1, 2, 3, 7 ASC
```

## SUMMARY
```sql
WITH raw_event_data_cte AS (

    SELECT 
      DATE_PART('year', submitted_at) AS event_year,
      DATE_PART('month', submitted_at) AS event_month,
      state AS event, 
      login AS author,
      COUNT(DISTINCT pr_num) AS unique_pr_count,
      COUNT(*) AS raw_event_count
    FROM 
      rxgithub.pull_request_comment 
    GROUP BY 
      1, 2, 3, 4

), rank_by_unique_pr_count AS (

	SELECT
	  event_year,
	  event_month,
	  event,
	  author,
	  unique_pr_count,
	  raw_event_count,
	  RANK() OVER (
	    PARTITION BY
	      event_year, event_month
	    ORDER BY
	      unique_pr_count DESC
	  ) AS rank
	FROM
	  raw_event_data_cte
	WHERE
	  event = 'APPROVED'
)
SELECT
  author,
  COUNT(*) AS included_in_count
FROM
  rank_by_unique_pr_count
WHERE
  rank <= 10 -- change to 5 or whatever
GROUP BY
  1
ORDER BY
  2 DESC
```
