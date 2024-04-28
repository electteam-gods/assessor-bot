from typing import Optional
from os import getenv

from sqlmodel import Field, Relationship, SQLModel, create_engine
from dotenv import load_dotenv

load_dotenv()


class Course(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    lessons: "Lesson" = Relationship(back_populates="course")


class Lesson(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    content: str
    course_id: int = Field(default=None, foreign_key="course.id", nullable=False)
    course: Course = Relationship(back_populates="lessons")
    type: str


postgres_uri = f"postgresql+psycopg2://postgres:{getenv("POSTGRES_PASSWORD")}@db:5432/postgres"
print(postgres_uri)
engine = create_engine(postgres_uri)

SQLModel.metadata.create_all(engine)
