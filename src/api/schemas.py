import enum


class OrderBy(enum.Enum):
    last_update = 'last_update'
    change_count = 'change_count'
    start_time = 'start_time'
