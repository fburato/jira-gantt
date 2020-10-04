from jira import JIRA
from tasks import Task
from typing import List


def extract_tasks_from_search(user: str, password: str, jira_url: str, search: str, dependency_types: List[str]) -> List[Task]:
    jira = JIRA(jira_url, auth=(user, password))
    issues = jira.search_issues(search)
    tasks = []
    for issue in issues:
        hours = (
            issue.fields.timeoriginalestimate if issue.fields.timeoriginalestimate else 0) / 3600
        remaining = (
            issue.fields.timeestimate if issue.fields.timeestimate else 0) / 3600
        code = issue.key
        description = issue.fields.summary
        block_list = []
        for link in issue.fields.issuelinks:
            if link.type.name in dependency_types:
                if hasattr(link, "outwardIssue"):
                    block_list.append(link.outwardIssue.key)
        tasks.append(Task(code=code,
                          blocks=block_list,
                          description=description,
                          original_estimate_hours=hours,
                          remaining_estimate_hours=remaining,
                          link=f"{jira_url}/browse/{code}"))
    return tasks
