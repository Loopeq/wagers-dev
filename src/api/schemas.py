import enum
from typing import List, Optional, Any

from pydantic import BaseModel


class ApiBaseDTO(BaseModel):
    @classmethod
    def from_list(cls, tpl):
        return cls(**{k: v for k, v in zip(cls.__fields__.keys(), tpl)})


class TimeFilter(BaseModel):
    id: int
    title: str
    hour: Optional[int] = None
    finished: Optional[bool] = None


class ValueFilterType(enum.Enum):
    last_change_time = 'last_change_time'
    count_of_changes = 'count_of_changes'
    match_start_time = 'match_start_time'


class ValueFilter(BaseModel):
    id: int
    title: str
    type: ValueFilterType


class FilterResponse(BaseModel):
    time_filters: List[TimeFilter]
    value_filters: List[ValueFilter]


class FilterRequest(BaseModel):
    hour: Optional[int] = None
    finished: Optional[bool] = None
    not_null_point: bool
    filter: ValueFilterType


filters = FilterResponse(
    time_filters=[
        TimeFilter(id=0, title='Ближайшие матчи'),
        TimeFilter(id=1, title='1 час до матча', hour=1),
        TimeFilter(id=2, title='3 часа до матча', hour=3),
        TimeFilter(id=3, title='Завершенные матчи', finished=True)],
    value_filters=[
        ValueFilter(id=0, title='По времени последнего движения', type=ValueFilterType.last_change_time),
        ValueFilter(id=1, title='По количеству движений', type=ValueFilterType.count_of_changes),
        ValueFilter(id=2, title='По времени начала матча', type=ValueFilterType.match_start_time)
    ])
