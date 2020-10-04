# Jira Gantt

The `jira_gantt` script generates an interactive Gantt chart with [plotly](https://plotly.com) from a collection of Jira tickets extracted through the Jira rest api. A JQL query is provided to the script to query a Jira instance and all the issues returned will be used to calculate their Gantt. The way the duration of the tasks is calculated is by using the original estimate field and based on links in the tickets, the tasks are ordered so that tickets that block other tickets are executed before.

The `jira_resource_allocation` script generates a timeline of a possible allocation of tasks between a set of resources which can be allocated to complete the tasks. It takes the source information from Jira like `jira_gantt`. The proposed resource allocation uses a greedy strategy for the allocation of resources (i.e. take the first resource available to allocate the next task), so the allocation might not be optimal.

A few configuration options (start date, non-working day to exclude from the diagram, duration of a day in hours, non-working days of a week) allow to produce a Gantt diagram that takes into consideration the actual working day available.

## Options

### Jira Gantt
```
usage: jira_gantt.py [-h] [--exclude EXCLUDE [EXCLUDE ...]] [--holiday-weekday HOLIDAY_WEEKDAY [HOLIDAY_WEEKDAY ...]] --start-date START_DATE --user USER
                     --password PASSWORD [--output OUTPUT] [--dependency-types DEPENDENCY_TYPES [DEPENDENCY_TYPES ...]] --jira-url JIRA_URL
                     [--day-duration DAY_DURATION] [--mode {original,remaining}]
                     jira_query

positional arguments:
  jira_query            JQL query that returns all Jira tickets to add to the Gantt calculation

optional arguments:
  -h, --help            show this help message and exit
  --exclude EXCLUDE [EXCLUDE ...]
                        Dates in the YYYY-mm-dd format for non-working days
  --holiday-weekday HOLIDAY_WEEKDAY [HOLIDAY_WEEKDAY ...]
                        Non working days of the week (0 for Monday, 6 for Sunday)
  --start-date START_DATE
                        Start date in the YYYY-mm-dd format from which to start computing the Gantt
  --user USER           User to use to authenticate to Jira
  --password PASSWORD   Password to use to authenticate to Jira
  --output OUTPUT       Filename (without extension) where the Gantt chart will be saved
  --dependency-types DEPENDENCY_TYPES [DEPENDENCY_TYPES ...]
                        Forward dependency that indicates a blocking link
  --jira-url JIRA_URL   URL for the Jira server to connect to
  --day-duration DAY_DURATION
                        Workday duration in hours
  --mode {original,remaining}
                        Use original estimate or remaining estimate (default original)
```

### Jira resource allocation

```
usage: jira_resource_allocation.py [-h] [--exclude EXCLUDE [EXCLUDE ...]] --resources RESOURCES [RESOURCES ...]
                                   [--holiday-weekday HOLIDAY_WEEKDAY [HOLIDAY_WEEKDAY ...]] --start-date START_DATE --user USER --password PASSWORD
                                   [--output OUTPUT] [--dependency-types DEPENDENCY_TYPES [DEPENDENCY_TYPES ...]] --jira-url JIRA_URL
                                   [--day-duration DAY_DURATION] [--mode {original,remaining}]
                                   jira_query

positional arguments:
  jira_query            JQL query that returns all Jira tickets to add to the Gantt calculation

optional arguments:
  -h, --help            show this help message and exit
  --exclude EXCLUDE [EXCLUDE ...]
                        Dates in the YYYY-mm-dd format for non-working days
  --resources RESOURCES [RESOURCES ...]
                        Resources amongst which allocate the tasks
  --holiday-weekday HOLIDAY_WEEKDAY [HOLIDAY_WEEKDAY ...]
                        Non working days of the week (0 for Monday, 6 for Sunday)
  --start-date START_DATE
                        Start date in the YYYY-mm-dd format from which to start computing the Gantt
  --user USER           User to use to authenticate to Jira
  --password PASSWORD   Password to use to authenticate to Jira
  --output OUTPUT       Filename (without extension) where the Gantt chart will be saved
  --dependency-types DEPENDENCY_TYPES [DEPENDENCY_TYPES ...]
                        Forward dependency that indicates a blocking link
  --jira-url JIRA_URL   URL for the Jira server to connect to
  --day-duration DAY_DURATION
                        Workday duration in hours
  --mode {original,remaining}
                        Use original estimate or remaining estimate (default original)

```

## Installation

Install [pipenv](https://pypi.org/project/pipenv/) in your system, then run

```sh
pipenv install
```

to install all the dependencies.

## Run

Activate the virtualenv for the pip environment with

```sh
pipenv shell
```

And then run 

```sh
python <script> <options>
```
