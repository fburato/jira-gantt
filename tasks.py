from dataclasses import dataclass
from typing import List, Dict, Optional, Set
from datetime import date, timedelta
import math
import functools


@dataclass
class Task:
    code: str
    blocks: List[str]
    description: Optional[str] = None
    link: Optional[str] = None
    original_estimate_hours: float = 0
    remaining_estimate_hours: float = 0


@dataclass
class TimelineTask:
    code: str
    description: Optional[str]
    link: Optional[str]
    start: date
    end: date


class TaskRepository:

    def __init__(self):
        self._tasks: Dict[str, Task] = {}

    def save(self, task: Task):
        self._tasks[task.code] = task

    def get(self, code: str) -> Optional[Task]:
        if code in self._tasks:
            return self._tasks[code]
        else:
            return None

    def codes(self) -> Set[str]:
        return set(self._tasks.keys())

    def is_blocked_by_map(self) -> Dict[str, Set[str]]:
        result = {}
        for task in self._tasks.keys():
            result[task] = set()
        for task in self._tasks.values():
            for code_blocked in task.blocks:
                if code_blocked in self._tasks.keys():
                    result[code_blocked].add(task.code)
        return result


class TimelineCalculator:

    def __init__(self, start_date: date,
                 hours_in_day: float,
                 skipped_dates: List[date] = None,
                 skipped_weekdays: List[int] = None):
        self._start_date = start_date
        self._hours_in_day = hours_in_day
        self._skipped_dates = skipped_dates if skipped_dates else []
        self._skipped_weekdays = skipped_weekdays if skipped_weekdays else []

    def compute_original_timeline(self, task_repository: TaskRepository) -> List[TimelineTask]:
        helper = self._CalculatorHelper(self, task_repository)
        return helper.compute_original_timeline()

    class _CalculatorHelper:

        def __init__(self, timeline_calculator, task_repository: TaskRepository):
            self._task_repository = task_repository
            self._timeline_calculator = timeline_calculator
            self._allocated_tasks: Set[str] = set()
            self._remaining_tasks = self._task_repository.codes()
            self._is_blocked_by = self._task_repository.is_blocked_by_map()
            self._result: Dict[str, TimelineTask] = {}

        def compute_original_timeline(self) -> List[TimelineTask]:
            while self._remaining_tasks:
                root_tasks = self._get_tasks_without_blockers()
                for task in root_tasks:
                    task_start_date = self._get_start_date(task)
                    task_days = self._task_days(task.original_estimate_hours)
                    task_end = self._get_next_available_date(task_start_date + timedelta(days=task_days))
                    self._result[task.code] = TimelineTask(code=task.code,
                                                           description=task.description,
                                                           link=task.link,
                                                           start=task_start_date,
                                                           end=task_end)
                    self._allocated_tasks.add(task.code)
                    self._remaining_tasks.remove(task.code)
            return list(self._result.values())

        def _task_days(self, hours: float) -> int:
            return int(math.ceil(hours / self._timeline_calculator._hours_in_day))

        def _get_tasks_without_blockers(self) -> List[Task]:
            result = []
            for remaining in self._remaining_tasks:
                task = self._task_repository.get(remaining)
                if not self._is_blocked_by[task.code].difference(self._allocated_tasks):
                    result.append(task)
            return result

        def _get_start_date(self, task: Task):
            is_caused_by_timelines = filter(lambda o: o, map(lambda code: self._result[code] if code in self._result else None,
                                                                  self._is_blocked_by[task.code]))
            max_end_date = functools.reduce(lambda x, y: y if x < y else x,
                                            map(lambda timeline: timeline.end, is_caused_by_timelines),
                                            self._get_next_available_date(self._timeline_calculator._start_date))
            return self._get_next_available_date(max_end_date)

        def _get_next_available_date(self, day: date):
            search_day = day
            while search_day.weekday() in self._timeline_calculator._skipped_weekdays or search_day in self._timeline_calculator._skipped_dates:
                search_day = search_day + timedelta(days=1)
            return search_day
