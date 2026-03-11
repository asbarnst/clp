import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random

def generate_student_id():
    """Generate a unique student ID"""
    year = datetime.now().year
    random_num = random.randint(1000, 9999)
    return f"S{year}{random_num}"

def generate_course_id():
    """Generate a course ID"""
    dept_code = random.choice(['CS', 'MATH', 'PHY', 'CHEM', 'ENG'])
    number = random.randint(100, 499)
    return f"{dept_code}{number}"

def calculate_gpa(grades_df):
    """Calculate GPA from grades"""
    if grades_df.empty:
        return 0.0
    
    grade_points = {'A': 4.0, 'B': 3.0, 'C': 2.0, 'D': 1.0, 'F': 0.0}
    
    total_points = 0
    total_courses = 0
    
    for grade in grades_df['final_grade'].dropna():
        if grade in grade_points:
            total_points += grade_points[grade]
            total_courses += 1
    
    return round(total_points / total_courses, 2) if total_courses > 0 else 0.0

def create_grade_distribution_chart(grades_df):
    """Create a pie chart of grade distribution"""
    if grades_df.empty:
        return None
    
    grade_counts = grades_df['final_grade'].value_counts()
    
    fig = px.pie(
        values=grade_counts.values,
        names=grade_counts.index,
        title="Grade Distribution",
        color_discrete_sequence=px.colors.qualitative.Set3
    )
    return fig

def create_attendance_trend(attendance_df):
    """Create attendance trend line chart"""
    if attendance_df.empty:
        return None
    
    attendance_by_date = attendance_df.groupby('date')['status'].apply(
        lambda x: (x == 'present').mean() * 100
    ).reset_index()
    
    fig = px.line(
        attendance_by_date,
        x='date',
        y='status',
        title="Attendance Trend Over Time",
        labels={'status': 'Attendance Rate (%)', 'date': 'Date'}
    )
    return fig

def validate_email(email):
    """Simple email validation"""
    return '@' in email and '.' in email

def validate_phone(phone):
    """Simple phone validation"""
    return phone.replace('+', '').replace('-', '').replace(' ', '').isdigit()
