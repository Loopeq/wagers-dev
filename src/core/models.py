import datetime
import enum
from typing import Annotated
import uuid as uuid_pkg

from sqlalchemy import (
    ForeignKey,
    Index,
    text, UniqueConstraint,
)
from src.core.db.base import (Base, str_128, str_64)
from sqlalchemy.orm import Mapped, mapped_column


intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]
updated_at = Annotated[datetime.datetime, mapped_column(
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=datetime.datetime.utcnow,
    )]


class BetTypeEnum(enum.Enum):
    total = 'total'
    spread = 'spread'


class MatchResultEnum(enum.Enum):
    win = 'win'
    lose = 'lose'


class MatchSideEnum(enum.Enum):
    home = 'home'
    away = 'away'


class Sport(Base):
    __tablename__ = 'sport'

    id: Mapped[intpk] = mapped_column(autoincrement=False)
    name: Mapped[str_64] = mapped_column(unique=True, nullable=False)


class League(Base):
    __tablename__ = 'league'

    id: Mapped[intpk] = mapped_column(autoincrement=False)
    sport_id: Mapped[int] = mapped_column(ForeignKey('sport.id'), nullable=False)
    name: Mapped[str_128] = mapped_column(nullable=False)
    _table_args__ = (
        UniqueConstraint('name', 'sport_id', name='uq_league_combination'),
    )


class Match(Base):
    __tablename__ = 'match'

    id: Mapped[intpk] = mapped_column(autoincrement=False)
    league_id: Mapped[int] = mapped_column(ForeignKey('league.id'), nullable=False)
    start_time: Mapped[datetime.datetime] = mapped_column(nullable=False, index=True)


class MatchMember(Base):
    __tablename__ = 'match_member'

    id: Mapped[intpk]
    match_id: Mapped[int] = mapped_column(ForeignKey('match.id', ondelete='CASCADE'), nullable=False, index=True)
    name: Mapped[str_64] = mapped_column(nullable=False)
    status: Mapped[MatchResultEnum] = mapped_column(nullable=True)
    side: Mapped[MatchSideEnum] = mapped_column(nullable=False)

    __table_args__ = (
        UniqueConstraint('match_id', 'side', name='uq_match_combination'),
        Index('ix_match_member_match_id_side', 'match_id', 'side')
    )


class Bet(Base):
    __tablename__ = 'bet'

    id: Mapped[intpk]
    match_id: Mapped[int] = mapped_column(ForeignKey('match.id', ondelete='CASCADE'), nullable=False, index=True)
    point: Mapped[float] = mapped_column(nullable=False)
    home_cf: Mapped[float] = mapped_column(nullable=False)
    away_cf: Mapped[float] = mapped_column(nullable=False)
    type: Mapped[BetTypeEnum] = mapped_column(nullable=False)
    period: Mapped[int] = mapped_column(nullable=False)
    version: Mapped[int] = mapped_column(nullable=False, default=1)
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False, index=True)


class User(Base):

    __tablename__ = 'user'

    uuid: Mapped[uuid_pkg.UUID] = mapped_column(
        primary_key=True, unique=True, default=uuid_pkg.uuid4, nullable=False
    )
    password: Mapped[str] = mapped_column(nullable=False)
    disabled: Mapped[bool] = mapped_column(nullable=False, default=False)
    superuser: Mapped[bool] = mapped_column(nullable=False, default=False)


class MatchResult(Base):

    __tablename__ = 'match_result'

    id: Mapped[intpk]
    match_id: Mapped[int] = mapped_column(ForeignKey('match.id', ondelete='CASCADE'), nullable=False, index=True)
    period: Mapped[int] = mapped_column(nullable=False, index=True)
    team_1_score: Mapped[int] = mapped_column(nullable=False)
    team_2_score: Mapped[int] = mapped_column(nullable=False)


