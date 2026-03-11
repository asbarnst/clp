from dataclasses import dataclass
from datetime import datetime
from typing import Optional

@dataclass
class Student:
    student_id: str
    first_name: str
    last_name: str
    date_of_birth: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    enrollment_date: str = datetime.now().strftime("%Y-%m-%d")
    status: str = "active"

@dataclass
class Course:
    course_id: str
    course_name: str
    credits: int = 3
    department: Optional[str] = None
    instructor: Optional[str] = None
    semester: Optional[str] = None
    max_students: Optional[int] = None

@dataclass
class Enrollment:
    student_id: str
    course_id: str
    semester: str
    enrollment_date: str = datetime.now().strftime("%Y-%m-%d")
    grade: Optional[str] = None
    status: str = "enrolled"

@dataclass
class Grade:
    enrollment_id: int
    assignment_name: str
    score: float
    max_score: float = 100
    weight: float = 1.0
    date_recorded: str = datetime.now().strftime("%Y-%m-%d")
