# DB connector

import os
from dotenv import load_dotenv
from sqlalchemy import String, Integer, DateTime, create_engine, Float
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Mapped, mapped_column
from datetime import datetime

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set")


class Base(DeclarativeBase):
    pass


engine = create_engine(DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# tables
class OccupancyReading(Base):
    __tablename__ = "occupancy_readings"
    hour_str: Mapped[str] = mapped_column(String(13), primary_key=True)
    occupant_count: Mapped[int] = mapped_column(Integer, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

class EnvironmentalReading(Base):
    __tablename__ = "environmental_readings"
    zone: Mapped[str] = mapped_column(String(25), primary_key = True)
    zone_type: Mapped[str] = mapped_column(String(30), nullable=False)
    temperature_c: Mapped[float] = mapped_column(Float, nullable=False)
    noise_db: Mapped[float] = mapped_column(Float, nullable=False)
    humidity_percent: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)





def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()