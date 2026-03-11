import sqlite3
import pandas as pd
from datetime import datetime
import hashlib
import os

class Database:
    def __init__(self, db_path='data/students.db'):
        """Initialize database connection and create tables if they don't exist"""
        # Ensure data directory exists
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()
    
    def create_tables(self):
        """Create all necessary tables"""
        
        # Students table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
                student_id TEXT PRIMARY KEY,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                date_of_birth TEXT,
                email TEXT UNIQUE,
                phone TEXT,
                address TEXT,
                enrollment_date TEXT,
                status TEXT DEFAULT 'active'
            )
        ''')
        
        # Courses table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS courses (
                course_id TEXT PRIMARY KEY,
                course_name TEXT NOT NULL,
                credits INTEGER,
                department TEXT,
                instructor TEXT,
                semester TEXT,
                max_students INTEGER
            )
        ''')
        
        # Enrollments table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrollments (
                enrollment_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                course_id TEXT,
                enrollment_date TEXT,
                grade TEXT,
                semester TEXT,
                status TEXT DEFAULT 'enrolled',
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (course_id) REFERENCES courses(course_id),
                UNIQUE(student_id, course_id, semester)
            )
        ''')
        
        # Grades table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS grades (
                grade_id INTEGER PRIMARY KEY AUTOINCREMENT,
                enrollment_id INTEGER,
                assignment_name TEXT,
                score REAL,
                max_score REAL,
                weight REAL,
                date_recorded TEXT,
                FOREIGN KEY (enrollment_id) REFERENCES enrollments(enrollment_id)
            )
        ''')
        
        # Attendance table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS attendance (
                attendance_id INTEGER PRIMARY KEY AUTOINCREMENT,
                student_id TEXT,
                course_id TEXT,
                date TEXT,
                status TEXT,
                FOREIGN KEY (student_id) REFERENCES students(student_id),
                FOREIGN KEY (course_id) REFERENCES courses(course_id)
            )
        ''')
        
        # Users table for system access
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE,
                password TEXT,
                role TEXT,
                created_at TEXT
            )
        ''')
        
        self.conn.commit()
    
    def hash_password(self, password):
        """Hash password for security"""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def add_user(self, username, password, role='staff'):
        """Add a new user to the system"""
        try:
            hashed_pw = self.hash_password(password)
            self.cursor.execute('''
                INSERT INTO users (username, password, role, created_at)
                VALUES (?, ?, ?, ?)
            ''', (username, hashed_pw, role, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def verify_user(self, username, password):
        """Verify user credentials"""
        hashed_pw = self.hash_password(password)
        self.cursor.execute('''
            SELECT username, role FROM users 
            WHERE username = ? AND password = ?
        ''', (username, hashed_pw))
        return self.cursor.fetchone()
    
    # Student operations
    def add_student(self, student_data):
        """Add a new student"""
        try:
            query = '''
                INSERT INTO students (
                    student_id, first_name, last_name, date_of_birth,
                    email, phone, address, enrollment_date, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            '''
            self.cursor.execute(query, student_data)
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_all_students(self):
        """Get all students"""
        query = "SELECT * FROM students ORDER BY student_id"
        return pd.read_sql_query(query, self.conn)
    
    def get_student(self, student_id):
        """Get a specific student"""
        query = "SELECT * FROM students WHERE student_id = ?"
        return pd.read_sql_query(query, self.conn, params=[student_id])
    
    def update_student(self, student_id, updates):
        """Update student information"""
        set_clause = ", ".join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values()) + [student_id]
        query = f"UPDATE students SET {set_clause} WHERE student_id = ?"
        self.cursor.execute(query, values)
        self.conn.commit()
    
    def delete_student(self, student_id):
        """Delete a student (cascade will handle enrollments)"""
        self.cursor.execute("DELETE FROM students WHERE student_id = ?", (student_id,))
        self.conn.commit()
    
    # Course operations
    def add_course(self, course_data):
        """Add a new course"""
        try:
            query = '''
                INSERT INTO courses (
                    course_id, course_name, credits, department,
                    instructor, semester, max_students
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
            '''
            self.cursor.execute(query, course_data)
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_all_courses(self):
        """Get all courses"""
        query = "SELECT * FROM courses ORDER BY course_id"
        return pd.read_sql_query(query, self.conn)
    
    def get_course(self, course_id):
        """Get a specific course"""
        query = "SELECT * FROM courses WHERE course_id = ?"
        return pd.read_sql_query(query, self.conn, params=[course_id])
    
    # Enrollment operations
    def enroll_student(self, student_id, course_id, semester):
        """Enroll a student in a course"""
        try:
            # Check if course has space
            self.cursor.execute('''
                SELECT COUNT(*) as enrolled, max_students 
                FROM enrollments e
                JOIN courses c ON e.course_id = c.course_id
                WHERE e.course_id = ? AND e.semester = ?
            ''', (course_id, semester))
            
            result = self.cursor.fetchone()
            if result and result[1] and result[0] >= result[1]:
                return False, "Course is full"
            
            enrollment_date = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute('''
                INSERT INTO enrollments (student_id, course_id, enrollment_date, semester)
                VALUES (?, ?, ?, ?)
            ''', (student_id, course_id, enrollment_date, semester))
            self.conn.commit()
            return True, "Enrollment successful"
        except sqlite3.IntegrityError:
            return False, "Student already enrolled in this course"
    
    def get_student_courses(self, student_id):
        """Get all courses for a student"""
        query = '''
            SELECT c.*, e.grade, e.status, e.enrollment_id
            FROM courses c
            JOIN enrollments e ON c.course_id = e.course_id
            WHERE e.student_id = ?
        '''
        return pd.read_sql_query(query, self.conn, params=[student_id])
    
    def get_course_students(self, course_id):
        """Get all students in a course"""
        query = '''
            SELECT s.*, e.grade, e.status
            FROM students s
            JOIN enrollments e ON s.student_id = e.student_id
            WHERE e.course_id = ?
        '''
        return pd.read_sql_query(query, self.conn, params=[course_id])
    
    # Grade operations
    def add_grade(self, enrollment_id, assignment_name, score, max_score, weight):
        """Add a grade for a student"""
        date_recorded = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute('''
            INSERT INTO grades (enrollment_id, assignment_name, score, max_score, weight, date_recorded)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (enrollment_id, assignment_name, score, max_score, weight, date_recorded))
        self.conn.commit()
        
        # Update final grade in enrollments
        self.calculate_final_grade(enrollment_id)
    
    def calculate_final_grade(self, enrollment_id):
        """Calculate and update final grade for an enrollment"""
        self.cursor.execute('''
            SELECT 
                SUM(score * weight / max_score) / SUM(weight) * 100 as final_grade
            FROM grades
            WHERE enrollment_id = ?
        ''', (enrollment_id,))
        
        result = self.cursor.fetchone()
        if result and result[0]:
            final_grade = result[0]
            
            # Convert to letter grade
            if final_grade >= 90:
                letter_grade = 'A'
            elif final_grade >= 80:
                letter_grade = 'B'
            elif final_grade >= 70:
                letter_grade = 'C'
            elif final_grade >= 60:
                letter_grade = 'D'
            else:
                letter_grade = 'F'
            
            self.cursor.execute('''
                UPDATE enrollments SET grade = ? WHERE enrollment_id = ?
            ''', (letter_grade, enrollment_id))
            self.conn.commit()
    
    def get_student_grades(self, student_id):
        """Get all grades for a student"""
        query = '''
            SELECT c.course_name, e.semester, g.assignment_name, 
                   g.score, g.max_score, g.weight, g.date_recorded, e.grade as final_grade
            FROM grades g
            JOIN enrollments e ON g.enrollment_id = e.enrollment_id
            JOIN courses c ON e.course_id = c.course_id
            WHERE e.student_id = ?
            ORDER BY g.date_recorded DESC
        '''
        return pd.read_sql_query(query, self.conn, params=[student_id])
    
    # Attendance operations
    def mark_attendance(self, student_id, course_id, date, status):
        """Mark attendance for a student"""
        try:
            self.cursor.execute('''
                INSERT INTO attendance (student_id, course_id, date, status)
                VALUES (?, ?, ?, ?)
            ''', (student_id, course_id, date, status))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            # Update existing record
            self.cursor.execute('''
                UPDATE attendance SET status = ?
                WHERE student_id = ? AND course_id = ? AND date = ?
            ''', (status, student_id, course_id, date))
            self.conn.commit()
            return True
    
    def get_attendance_report(self, course_id, date):
        """Get attendance report for a course on a specific date"""
        query = '''
            SELECT s.student_id, s.first_name, s.last_name, 
                   COALESCE(a.status, 'absent') as status
            FROM students s
            JOIN enrollments e ON s.student_id = e.student_id
            LEFT JOIN attendance a ON s.student_id = a.student_id 
                AND a.course_id = e.course_id AND a.date = ?
            WHERE e.course_id = ? AND e.status = 'enrolled'
        '''
        return pd.read_sql_query(query, self.conn, params=[date, course_id])
    
    def close(self):
        """Close database connection"""
        self.conn.close()
