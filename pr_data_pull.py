from configparser import ConfigParser
from datetime import datetime
from github import Github, PullRequest
from github.Commit import Commit
from github.NamedUser import NamedUser
from github.PaginatedList import PaginatedList
from github.Team import Team
from typing import List, Optional
import argparse
import logging


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


pr_info_cols = [
    "repo_tag",
    "pr_num",
    "author",
    "state",
    "adds",
    "deletes",
    "review_comments",
    "created_at",
    "merged_at",
    "closed_at",
    "url",
]

pr_comment_cols = [
    "repo_tag",
    "pr_num",
    "review_id",
    "login",
    "state",
    "submitted_at",
    "url",
]

pr_assignment_cols = [
    "repo_tag",
    "pr_num",
    "assignment_type",
    "name",
    "name_type",
]

def generate_template(
    tag_name: str,
    columns: List[str],
) -> str:
    return f"{tag_name}\t" + \
        "\t".join(["{%s}" % c for c in columns])

pr_info_template = generate_template("PRINFO", pr_info_cols)
pr_comment_template = generate_template("PRCOMMENT", pr_comment_cols)
pr_user_assignment_template = generate_template("PRASSIGNMENT", pr_assignment_cols)

def extract_and_format(
    repo_tag_name: str,
    issues: PaginatedList,
):
    for issue in issues:
        created_at = issue.created_at
        
        # convert to PR
        pr = issue.as_pull_request()

        # type: assignee, reviewer
        for assignee in pr.assignees:
            print(pr_user_assignment_template.format(
                repo_tag = repo_tag_name,
                pr_num = pr.number,
                assignment_type = "ASSIGNED",
                name = assignee.login,
                name_type = "USER",
            ))

        for requests in pr.get_review_requests():
            for req in requests:
                print(pr_user_assignment_template.format(
                    repo_tag = repo_tag_name,
                    pr_num = pr.number,
                    assignment_type = "REVIEWER",
                    name = req.login if type(req) is NamedUser else req.name,
                    name_type = "USER" if type(req) is NamedUser else "TEAM",
                ))

        print(pr_info_template.format(
            repo_tag = repo_tag_name,
            pr_num = pr.number,
            author = pr.user.login,
            adds = pr.additions,
            deletes = pr.deletions,
            review_comments = pr.review_comments,
            created_at = pr.created_at if pr.created_at else "",
            merged_at = pr.merged_at if pr.merged_at else "",
            closed_at = pr.closed_at if pr.closed_at else "",
            url = pr.html_url,
            state = pr.state,
        ))

        # collect the reviews for the PR
        # Doc Link:
        #   https://pygithub.readthedocs.io/en/latest/github_objects/PullRequestReview.html
        for review in pr.get_reviews():
            print(pr_comment_template.format(
                repo_tag = repo_tag_name,
                pr_num = pr.number,
                review_id = review.id,
                login = review.user.login if review.user else "N/A",
                state = review.state,
                submitted_at = review.submitted_at,
                url = review.html_url,
            ))


def parse_arguments() -> argparse.Namespace:
    arg_parser = argparse.ArgumentParser()

    arg_parser.add_argument(
        "-fd",
        "--from_date",
        help = "specify the inclusive start date in YYYY-MM-DD format",
        type = str,
        default = None,
    )

    arg_parser.add_argument(
        "-td",
        "--to_date",
        help = "specify the exclusive start date in YYYY-MM-DD format",
        type = str,
        default = None,
    )

    arg_parser.add_argument(
        "-r",
        "--repo",
        help = "specify the repo",
        type = str,
        default = "XRPLF/rippled",
    )

    arg_parser.add_argument(
        "-c",
        "--config",
        help = "config INI file containing the Github token",
        type = str,
        default = "github.ini",
    )

    return arg_parser.parse_args()


def date_range_arg(
    from_date: str,
    to_date: str,
):
    if from_date and to_date:
        query_date_range_str = "{}..{}".format(from_date, to_date)
    elif from_date:
        query_date_range_str = ">={}".format(from_date)
    elif to_date:
        query_date_range_str = "<{}".format(to_date)
    else:
        raise ValueError("require 'from_date' or 'to_date'")

    return query_date_range_str


def get_github_token(
    token_filepath: str,
):
    ini_config = ConfigParser()
    ini_config.read(token_filepath)
    return ini_config.get("github", "token")


if __name__ == "__main__":
    args = parse_arguments()

    query_date_range = date_range_arg(
        from_date = args.from_date,
        to_date = args.to_date,
    )
    full_query_str = f"is:pr repo:{args.repo} created:{query_date_range} sort:created-asc"
    logger.info("Github Query: '%s'", full_query_str)

    logger.info("Reading Github Token from '%s'", args.config)
    github_token = get_github_token(args.config)
    github_client = Github(github_token)
    
    # look at the PR's that have been created since 2022/01/01 inclusive
    issues = github_client.search_issues(
        query = full_query_str,
    )
    extract_and_format(
        repo_tag_name = args.repo,
        issues = issues,
    )
    


"""




"""

"""


SELECT
  author,
  COUNT(*) AS pr_count,
  SUM(additions) AS total_additions,
  SUM(deletions) AS total_deletions,
  SUM(additions) + SUM(deletions) AS total_adds_dels 
FROM 
  rxgithub.pull_request_info
GROUP BY 
  1 
ORDER BY 
  5 DESC


pr_num       | integer                     |           | not null |
 comment_id   | bigint                      |           | not null |
 login        | character varying(512)      |           | not null |
 state        | character varying(28)       |           | not null |
 submitted_at | timestamp without time zone |           | not null |
 url          | character varying(1024)     |           | not null |

SET timezone TO UTC;
SELECT
  login,
  EXTRACT(HOUR FROM TIMEZONE('US/Pacific', submitted_at)) AS hour_of_day,
  COUNT(*) AS comment_count
FROM
  rxgithub.pull_request_comment
GROUP BY
  1, 2
ORDER BY
  1, 2


SELECT
  login,
  state,
  COUNT(*)
FROM
  rxgithub.pull_request_comment
WHERE
  state in ('COMMENTED', 'APPROVED')
GROUP BY
  1, 2
ORDER BY
  2, 3 DESC


SELECT 
  name,
  assignment_type,
  COUNT(DISTINCT pr_num) AS pr_count
FROM 
  rxgithub.pull_request_assignment 
GROUP BY 
  1, 2 
ORDER BY 
  2, 3 DESC;


# Comments By Individual
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
    -- WHERE
      --    additions + deletions > 16
      -- AND state = 'closed'
      -- AND merged_at IS NOT NULL

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

```

```

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
      merged_at IS NOT NULL

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
        pr_num,
        login
    FROM
      pr_interested_cte
    WHERE
      state IN ('APPROVED') -- ('COMMENTED', 'APPROVED', 'CHANGES_REQUESTED')
)
SELECT
  login,
  ROUND(
    1.0 * COUNT(*) / (SELECT COUNT(DISTINCT pr_num) FROM distinct_pr_user_cte),
    4
  ) AS participation_perc,
  COUNT(*) AS commented_pr_count,
  (SELECT COUNT(DISTINCT pr_num) FROM distinct_pr_user_cte) AS total_count
FROM
  distinct_pr_user_cte
GROUP BY
  1
ORDER BY
  2
```


```
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
      state = 'closed'
  AND merged_at IS NOT NULL


```

# Metrics
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

), rank_approval_cte AS (

    SELECT
      pr_num,
      submitted_at,
      login,
      state,
      url,
      pr_created_at,
      RANK() OVER (
        PARTITION BY
          pr_num
        ORDER BY
          submitted_at DESC
      )
    FROM
      pr_interested_cte
    WHERE
      state = 'APPROVED'

), rank_comments_cte AS (

    SELECT
      pr_num,
      submitted_at,
      login,
      state,
      url,
      pr_created_at,
      RANK() OVER (
        PARTITION BY
          pr_num
        ORDER BY
          submitted_at ASC
      )
    FROM
      pr_interested_cte
    WHERE
      state = 'COMMENTED'
)
-- Different metrics:
--   Cycle Time: Time Diff (Created) - (Last Approval)
--   Pickup Time: Time Diff (Created) - (First Review / Comment)
--   Review TIme: Time Diff (First Review / Comment) - (Last Approval)
--
SELECT
  apr.pr_num,
  apr.pr_created_at,
  cmt.submitted_at AS first_commented_time,
  apr.submitted_at AS last_approved_time,
  apr.submitted_at - cmt.submitted_at AS review_duration,
  apr.submitted_at - apr.pr_created_at AS cycle_duration,
  cmt.submitted_at - apr.pr_created_at AS pickup_duration
FROM
  rank_approval_cte apr
  JOIN
  rank_comments_cte cmt
  ON
     apr.pr_num = cmt.pr_num
WHERE
      apr.rank = 1
  AND cmt.rank = 1
  AND apr.submitted_at >= cmt.submitted_at
ORDER BY
  1
```

# Authored
```sql
SELECT
  author,
  SUM(additions) + SUM(deletions) AS total_line_changes
FROM
  rxgithub.pull_request_info
WHERE
      additions + deletions > 16
  AND state = 'closed'
  AND merged_at IS NOT NULL
  AND created_at >= '2022-01-01T00:00:00'::TIMESTAMP
GROUP BY
  1
ORDER BY
  2 DESC
```

```sql
-- get the top 7 line change contributors
-- by year and state
--
WITH raw_line_change_cte AS (

    SELECT
      DATE_PART('year', created_at) AS created_year,
      author,
      state,
      SUM(additions) + SUM(deletions) AS total_line_changes
    FROM
      rxgithub.pull_request_info
    GROUP BY
      1, 2, 3

), ranked_cte AS (

    SELECT
      created_year,
      author,
      state,
      total_line_changes,
      RANK() OVER (
        PARTITION BY
          created_year, state
        ORDER BY
          total_line_changes DESC
      ) AS rank
    FROM
      raw_line_change_cte

)
SELECT
  *
FROM
  ranked_cte
WHERE
  rank <= 7;
```

```sql
-- get the top 7 line change contributors
-- by year
--
WITH raw_line_change_cte AS (

    SELECT
      DATE_PART('year', created_at) AS created_year,
      author,
      SUM(additions) + SUM(deletions) AS total_line_changes
    FROM
      rxgithub.pull_request_info
    GROUP BY
      1, 2

), ranked_cte AS (

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
  *
FROM
  ranked_cte
WHERE
  rank <= 7;
```

```sql
WITH individual_lcs_cte AS (

    -- individual total line changes
    --
    SELECT
      author,
      SUM(additions) + SUM(deletions) AS line_changes
    FROM
      rxgithub.pull_request_info
    GROUP BY
      1

)
SELECT
  author,
  line_changes,
  SUM(line_changes) OVER (),
  ROUND(
    1.0 * line_changes / SUM(line_changes) OVER (),
    4
  ) AS contribution_perc
FROM
  individual_lcs_cte
ORDER BY
  4 DESC
```


```sql
SELECT
  DATE_PART('year', created_at) AS created_year,
  SUM(additions) + SUM(deletions) AS total_line_changes,
  COUNT(DISTINCT pr_num) AS pr_count,
  COUNT(DISTINCT author) AS uniq_pr_author,
  SUM(additions) + SUM(deletions) / total_lc_by_author,
  SUM(additions) + SUM(deletions) / total_lc_by_pr_count
FROM
  rxgithub.pull_request_info
WHERE
  author <> 'manojsdoshi'
GROUP BY
  1
```


```sql
SELECT
  DATE_PART('year', created_at) AS created_year,
  SUM(additions) + SUM(deletions) AS total_line_changes,
  COUNT(author) AS author_count,
  COUNT(DISTINCT pr_num) AS pr_count,
  (SUM(additions) + SUM(deletions)) / COUNT(DISTINCT pr_num) AS lc_per_pr
FROM
  rxgithub.pull_request_info
WHERE
  author <> 'manojsdoshi'
GROUP BY
  1


WITH raw_line_change_cte AS (

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
  *
FROM
  ranked_cte


```


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

"""