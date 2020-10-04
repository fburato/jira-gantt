from dataclasses import dataclass
from typing import List, Dict, Optional, Set, Callable, Tuple
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


@dataclass
class TimelineTaskWithResource:
    code: str
    resource: str
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
        helper = self._CalculatorHelper(self, task_repository, [])
        return helper.compute_original_timeline()

    def compute_remaining_timeline(self, task_repository: TaskRepository) -> List[TimelineTask]:
        helper = self._CalculatorHelper(self, task_repository, [])
        return helper.compute_remaining_timeline()

    def compute_original_resource_allocation(self, task_repository: TaskRepository, resources: List[str]) -> List[TimelineTaskWithResource]:
        helper = self._CalculatorHelper(self, task_repository, resources)
        return helper.compute_original_resource_allocation()

    def compute_remaining_resource_allocation(self, task_repository: TaskRepository, resources: List[str]) -> List[TimelineTaskWithResource]:
        helper = self._CalculatorHelper(self, task_repository, resources)
        return helper.compute_remaining_resource_allocation()

    class _CalculatorHelper:

        @dataclass
        class ResourceAllocationState:
            resource_availability: Dict[str, date]
            allocated_task: Dict[str, TimelineTaskWithResource]

        def __init__(self, timeline_calculator, task_repository: TaskRepository, resources: List[str]):
            self._task_repository = task_repository
            self._timeline_calculator = timeline_calculator
            self._allocated_tasks: Set[str] = set()
            self._resources = resources
            self._remaining_tasks = self._task_repository.codes()
            self._is_blocked_by = self._task_repository.is_blocked_by_map()
            self._result_timeline: Dict[str, TimelineTask] = {}
            self._resources_state = self.ResourceAllocationState(
                resource_availability={
                    r: self._timeline_calculator._start_date for r in self._resources},
                allocated_task={}
            )

        def compute_original_timeline(self) -> List[TimelineTask]:
            return self._compute_timeline(lambda task: task.original_estimate_hours)

        def compute_remaining_timeline(self) -> List[TimelineTask]:
            return self._compute_timeline(lambda task: task.remaining_estimate_hours)

        def _compute_timeline(self, remaining_extractor: Callable[[Task], float]) -> List[TimelineTask]:
            while self._remaining_tasks:
                root_tasks = self._get_tasks_without_blockers()
                for task in root_tasks:
                    task_start_date = self._get_start_date(task)
                    task_days = self._task_days(remaining_extractor(task))
                    task_end = self._end_date_allocation_with_exclusion(
                        task_start_date, task_days)
                    self._result_timeline[task.code] = TimelineTask(code=task.code,
                                                                    description=task.description,
                                                                    link=task.link,
                                                                    start=task_start_date,
                                                                    end=task_end)
                    self._allocated_tasks.add(task.code)
                    self._remaining_tasks.remove(task.code)
            return list(self._result_timeline.values())

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
            is_caused_by_timelines = filter(lambda o: o, map(lambda code: self._result_timeline[code] if code in self._result_timeline else None,
                                                             self._is_blocked_by[task.code]))
            max_end_date = functools.reduce(lambda x, y: y if x < y else x,
                                            map(lambda timeline: timeline.end,
                                                is_caused_by_timelines),
                                            self._get_next_available_date(self._timeline_calculator._start_date))
            return self._get_next_available_date(max_end_date)

        def _get_next_available_date(self, day: date) -> date:
            search_day = day
            while self._excluded(search_day):
                search_day = search_day + timedelta(days=1)
            return search_day

        def _excluded(self, day: date) -> bool:
            return day.weekday() in self._timeline_calculator._skipped_weekdays or day in self._timeline_calculator._skipped_dates

        def _end_date_allocation_with_exclusion(self, day: date, allocation: int) -> date:
            allocated = 0
            end_date = day
            while allocated < allocation:
                if not self._excluded(end_date):
                    allocated += 1
                end_date = end_date + timedelta(days=1)
            return end_date

        def compute_original_resource_allocation(self) -> List[TimelineTaskWithResource]:
            return self._compute_allocation(lambda task: task.original_estimate_hours)

        def compute_remaining_resource_allocation(self) -> List[TimelineTaskWithResource]:
            return self._compute_allocation(lambda task: task.remaining_estimate_hours)

        def _compute_allocation(self, remaining_extractor: Callable[[Task], float]) -> List[TimelineTaskWithResource]:
            while self._remaining_tasks:
                root_tasks = self._get_tasks_without_blockers()
                for task in root_tasks:
                    prospected_task_start_date = self._get_start_date_for_resource(
                        task)
                    available_resource = self._find_available_resource(
                        prospected_task_start_date)
                    resource_availability_date = self._resources_state.resource_availability[
                        available_resource]
                    task_start_date = resource_availability_date if resource_availability_date >= prospected_task_start_date else prospected_task_start_date
                    task_days = self._task_days(remaining_extractor(task))
                    task_end = self._end_date_allocation_with_exclusion(
                        task_start_date, task_days)
                    self._resources_state.resource_availability[available_resource] = task_end
                    self._resources_state.allocated_task[task.code] = TimelineTaskWithResource(code=task.code,
                                                                                               resource=available_resource,
                                                                                               description=task.description,
                                                                                               link=task.link,
                                                                                               start=task_start_date,
                                                                                               end=task_end)
                    self._allocated_tasks.add(task.code)
                    self._remaining_tasks.remove(task.code)
            return list(self._resources_state.allocated_task.values())

        def _get_start_date_for_resource(self, task: Task):
            is_caused_by_timelines = filter(lambda o: o, map(lambda code: self._resources_state.allocated_task[code] if code in self._resources_state.allocated_task else None,
                                                             self._is_blocked_by[task.code]))
            max_end_date = functools.reduce(lambda x, y: y if x < y else x,
                                            map(lambda timeline: timeline.end,
                                                is_caused_by_timelines),
                                            self._get_next_available_date(self._timeline_calculator._start_date))
            return self._get_next_available_date(max_end_date)

        def _find_available_resource(self, prospected_start_date: date) -> str:
            def find_resource_available_at_prospected() -> str:
                minimum_available = None
                matching_resource = None
                for resource, available in self._resources_state.resource_availability.items():
                    if available <= prospected_start_date:
                        if not minimum_available or available < minimum_available:
                            minimum_available = available
                            matching_resource = resource
                return matching_resource

            def find_first_resource_available() -> str:
                minimum_available = None
                matching_resource = None
                for resource, available in self._resources_state.resource_availability.items():
                    if not minimum_available or available <= minimum_available:
                        matching_resource = resource
                        minimum_available = available
                return matching_resource

            available_at_prospected = find_resource_available_at_prospected()
            if available_at_prospected:
                return available_at_prospected
            else:
                return find_first_resource_available()


__all__ = ["Task", "TaskRepository", "TimelineTask", "TimelineCalculator"]
