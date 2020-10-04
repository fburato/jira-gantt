import plotly.express as px
import pandas as pd
from datetime import datetime
from tasks import Task, TaskRepository, TimelineCalculator, TimelineTask, TimelineTaskWithResource
from jira_task_extraction import extract_tasks_from_search
from typing import List
import argparse
from datetime import date


def main():
    arg = parser()
    tasks = extract_tasks_from_search(
        arg.user, arg.password, arg.jira_url, arg.jira_query, arg.dependency_types)
    timeline_calculator = make_timeline_calculator(arg.start_date, float(
        arg.day_duration), arg.exclude, arg.holiday_weekday)
    repository = make_repository(tasks)
    if arg.mode == "original":
        timeline_tasks = timeline_calculator.compute_original_resource_allocation(
            repository, arg.resources)
    else:
        timeline_tasks = timeline_calculator.compute_remaining_timeline(
            repository, arg.resources)
    make_timeline(timeline_tasks, arg.output)


def parser():
    p = argparse.ArgumentParser()
    p.add_argument("--exclude", action="store", nargs="+", dest="exclude", required=False,
                   default=[], help="Dates in the YYYY-mm-dd format for non-working days")
    p.add_argument("--resources", action="store", nargs="+", dest="resources",
                   required=True, help="Resources amongst which allocate the tasks")
    p.add_argument("--holiday-weekday", action="store", nargs="+", dest="holiday_weekday",
                   required=False, default=[5, 6], help="Non working days of the week (0 for Monday, 6 for Sunday)")
    p.add_argument("--start-date", action="store", dest="start_date", required=True,
                   help="Start date in the YYYY-mm-dd format from which to start computing the Gantt")
    p.add_argument("--user", action="store", dest="user",
                   required=True, help="User to use to authenticate to Jira")
    p.add_argument("--password", action="store", dest="password",
                   required=True, help="Password to use to authenticate to Jira")
    p.add_argument("--output", action="store", dest="output", required=False, default="gantt",
                   help="Filename (without extension) where the Gantt chart will be saved")
    p.add_argument("--dependency-types", action="store", nargs="+", dest="dependency_types",
                   required=False, default=['Blocks'], help="Forward dependency that indicates a blocking link")
    p.add_argument("--jira-url", action="store", dest="jira_url",
                   required=True, help="URL for the Jira server to connect to")
    p.add_argument("--day-duration", action="store", dest="day_duration",
                   required=False, default=8, help="Workday duration in hours")
    p.add_argument("--mode", action="store", dest="mode",
                   choices=["original", "remaining"], required=False, default="original", help="Use original estimate or remaining estimate (default original)")
    p.add_argument(
        "jira_query", help="JQL query that returns all Jira tickets to add to the Gantt calculation")
    return p.parse_args()


def make_timeline_calculator(start_date: str,
                             day_duration: float,
                             excluded_dates: List[str],
                             holiday_weekday: List[str]) -> TimelineCalculator:
    parsed_start_date = parse_date(start_date)
    parsed_excluded_dates = list(
        map(lambda d: parse_date(d.strip()), excluded_dates))
    parsed_holiday_weekday = list(map(lambda d: int(d), holiday_weekday))
    return TimelineCalculator(
        parsed_start_date, day_duration, parsed_excluded_dates, parsed_holiday_weekday)


def make_repository(tasks: List[Task]) -> TaskRepository:
    task_repository = TaskRepository()
    for task in tasks:
        task_repository.save(task)
    return task_repository


def parse_date(string_date: str) -> date:
    return datetime.strptime(string_date, "%Y-%m-%d").date()


def make_timeline(timeline_tasks: List[TimelineTaskWithResource], output: str):
    df_dictionary = []
    for task in timeline_tasks:
        df_dictionary.append(dict(JiraID=task.code,
                                  Resource=task.resource,
                                  Summary=task.description,
                                  Start=task.start.strftime("%Y-%m-%d"),
                                  End=task.end.strftime("%Y-%m-%d"),
                                  Link=task.link))
    df = pd.DataFrame(df_dictionary)
    fig = px.timeline(df, x_start="Start", x_end="End",
                      y="Resource", hover_data=["Summary", "JiraID", "Link"], color="Resource")
    fig.write_html(f"{output}.html")


if __name__ == "__main__":
    main()
