from typing import Annotated

from sqlalchemy import String
from sqlalchemy.orm import DeclarativeBase

str_256 = Annotated[str, 256]
str_128 = Annotated[str, 128]
str_64 = Annotated[str, 64]


class Base(DeclarativeBase):
    type_annotation_map = {
        str_256: String(256)
    }

    def to_dict(self):
        return {column.name: getattr(self, column.name) for column in self.__table__.columns}

