import plotly.express as px
import pandas as pd
from datetime import datetime
from tasks import *
from jira import JIRA
import argparse


def main():
    arg = parser()
    tasks = extract_tasks_from_search(arg.user, arg.password, arg.jira_url, arg.jira_query, arg.dependency_types)
    timeline_tasks = compute_timeline_tasks(arg.start_date, float(arg.day_duration), arg.exclude, arg.holiday_weekday, tasks)
    make_gantt(timeline_tasks, arg.output)


def parser():
    p = argparse.ArgumentParser()
    p.add_argument("--exclude", action="store", nargs="+", dest="exclude", required=False, default=[], help="Dates in the YYYY-mm-dd format for non-working days")
    p.add_argument("--holiday-weekday", action="store", nargs="+", dest="holiday_weekday", required=False, default=[5, 6], help="Non working days of the week (0 for Monday, 6 for Sunday)")
    p.add_argument("--start-date", action="store", dest="start_date", required=True, help="Start date in the YYYY-mm-dd format from which to start computing the Gantt")
    p.add_argument("--user", action="store", dest="user", required=True, help="User to use to authenticate to Jira")
    p.add_argument("--password", action="store", dest="password", required=True, help="Password to use to authenticate to Jira")
    p.add_argument("--output", action="store", dest="output", required=False, default="gantt", help="Filename (without extension) where the Gantt chart will be saved")
    p.add_argument("--dependency-types", action="store", nargs="+", dest="dependency_types", required=False, default=['Blocks'], help="Forward dependency that indicates a blocking link")
    p.add_argument("--jira-url", action="store", dest="jira_url", required=True, help="URL for the Jira server to connect to")
    p.add_argument("--day-duration", action="store", dest="day_duration", required=False, default=8, help="Workday duration in hours")
    p.add_argument("jira_query", help="JQL query that returns all Jira tickets to add to the Gantt calculation")
    return p.parse_args()


def extract_tasks_from_search(user: str, password: str, jira_url: str, search: str, dependency_types: List[str]) -> List[Task]:
    jira = JIRA(jira_url, auth=(user, password))
    issues = jira.search_issues(search)
    tasks = []
    for issue in issues:
        hours = (issue.fields.timeoriginalestimate if issue.fields.timeoriginalestimate else 0) / 3600
        remaining = (issue.fields.timeestimate if issue.fields.timeestimate else 0) / 3600
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


def compute_timeline_tasks(start_date: str,
                           day_duration: float,
                           excluded_dates: List[str],
                           holiday_weekday: List[str], tasks: List[Task]) -> List[TimelineTask]:

    parsed_start_date = parse_date(start_date)
    parsed_excluded_dates = list(map(lambda d: parse_date(d.strip()), excluded_dates))
    parsed_holiday_weekday = list(map(lambda d: int(d), holiday_weekday))
    timeline = TimelineCalculator(parsed_start_date, day_duration, parsed_excluded_dates, parsed_holiday_weekday)
    task_repository = TaskRepository()
    for task in tasks:
        task_repository.save(task)
    return timeline.compute_original_timeline(task_repository)


def parse_date(string_date: str) -> date:
    return datetime.strptime(string_date, "%Y-%m-%d").date()


def make_gantt(timeline_tasks: List[TimelineTask], output: str):
    df_dictionary = []
    for task in timeline_tasks:
        df_dictionary.append(dict(JiraID=task.code,
                                  Summary=task.description,
                                  Start=task.start.strftime("%Y-%m-%d"),
                                  End=task.end.strftime("%Y-%m-%d"),
                                  Link=task.link))
    df = pd.DataFrame(df_dictionary)
    fig = px.timeline(df, x_start="Start", x_end="End", y="JiraID", hover_data=["Summary", "JiraID", "Link"])
    fig.update_yaxes(autorange="reversed")
    fig.write_html(f"{output}.html")


if __name__ == "__main__":
    main()
