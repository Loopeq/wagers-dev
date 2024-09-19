import datetime
import enum
from typing import Annotated, Optional
from sqlalchemy import (
    TIMESTAMP,
    DateTime,
    CheckConstraint,
    Column,
    Enum,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    PrimaryKeyConstraint,
    String,
    Table,
    text, UniqueConstraint,
)
from src.data.database import (Base, str_256, str_128, str_64)
from sqlalchemy.orm import Mapped, mapped_column, relationship


intpk = Annotated[int, mapped_column(primary_key=True, autoincrement=True)]
created_at = Annotated[datetime.datetime, mapped_column(server_default=text("TIMEZONE('utc', now())"))]
updated_at = Annotated[datetime.datetime, mapped_column(
        server_default=text("TIMEZONE('utc', now())"),
        onupdate=datetime.datetime.utcnow,
    )]


class BetTypeEnum(enum.Enum):
    moneyline = 'moneyline'
    total = 'total'
    spread = 'spread'
    teamtotal = 'team_total'


class MatchResultEnum(enum.Enum):
    win = 'win'
    lose = 'lose'


class MatchSideEnum(enum.Enum):
    home = 'home'
    away = 'away'


class BetStatusEnum(enum.Enum):
    open = 'open'
    closed = 'closed'


class BetValueTypeEnum(enum.Enum):
    home = 'home'
    away = 'away'
    over = 'over'
    under = 'under'


class Sport(Base):
    __tablename__ = 'sport'

    id: Mapped[intpk] = mapped_column(autoincrement=False)
    name: Mapped[str_64] = mapped_column(unique=True, nullable=False)

    leagues = relationship('League', back_populates='sport')


class League(Base):
    __tablename__ = 'league'

    id: Mapped[intpk] = mapped_column(autoincrement=False)
    sport_id: Mapped[int] = mapped_column(ForeignKey('sport.id'), nullable=False)
    name: Mapped[str_128] = mapped_column(unique=True, nullable=False)

    sport = relationship('Sport', back_populates='leagues')
    matches = relationship('Match', back_populates='league')


class Match(Base):
    __tablename__ = 'match'

    id: Mapped[intpk] = mapped_column(autoincrement=False)
    league_id: Mapped[int] = mapped_column(ForeignKey('league.id'), nullable=False)
    start_time: Mapped[datetime.datetime] = mapped_column(nullable=False)

    league = relationship('League', back_populates='matches')
    match_members = relationship('MatchMember', back_populates='match')
    bets = relationship('Bet', back_populates='match')


class MatchMember(Base):
    __tablename__ = 'match_member'

    id: Mapped[intpk]
    match_id: Mapped[int] = mapped_column(ForeignKey('match.id'), nullable=False)
    name: Mapped[str_64] = mapped_column(nullable=False)
    status: Mapped[MatchResultEnum] = mapped_column(nullable=True)
    side: Mapped[MatchSideEnum] = mapped_column(nullable=False)
    match = relationship('Match', back_populates='match_members')

    __table_args__ = (
        UniqueConstraint('match_id', 'side', name='uq_match_combination'),
    )


class Bet(Base):
    __tablename__ = 'bet'

    id: Mapped[intpk]
    match_id: Mapped[int] = mapped_column(ForeignKey('match.id'), nullable=False)
    type: Mapped[BetTypeEnum] = mapped_column(nullable=False)
    period: Mapped[int] = mapped_column(nullable=False)
    bet_values = relationship('BetValue', back_populates='bet')
    match = relationship('Match', back_populates='bets')
    __table_args__ = (
        UniqueConstraint('match_id', 'type', 'period', name='uq_match_member_combination'),
    )


class BetValue(Base):
    __tablename__ = "bet_value"

    id: Mapped[intpk]
    bet_id: Mapped[int] = mapped_column(ForeignKey('bet.id'), nullable=False)
    version: Mapped[int]
    value: Mapped[float] = mapped_column(nullable=False)
    point: Mapped[float] = mapped_column(nullable=True)
    status: Mapped[BetStatusEnum] = mapped_column(Enum(BetStatusEnum, name="betstatusenum"), nullable=False,
                                                  default=BetStatusEnum.open)
    type: Mapped[BetValueTypeEnum] = mapped_column(Enum(BetValueTypeEnum, name='betvaluetypeenum'), nullable=False)
    created_at: Mapped[datetime.datetime] = mapped_column(nullable=False)
    bet = relationship('Bet', back_populates='bet_values')


