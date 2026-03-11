import streamlit as st
import pandas as pd
from datetime import datetime
import plotly.express as px
from database import Database
from models import Student, Course
from utils import generate_student_id, generate_course_id, calculate_gpa, create_grade_distribution_chart

# Page configuration
st.set_page_config(
    page_title="Student Management System",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
@st.cache_resource
def init_database():
    return Database()

db = init_database()

# Session state initialization
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'username' not in st.session_state:
    st.session_state.username = None
if 'role' not in st.session_state:
    st.session_state.role = None
if 'current_page' not in st.session_state:
    st.session_state.current_page = "Dashboard"

# Authentication function
def login():
    st.title("🔐 Login to Student Management System")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login", use_container_width=True)
            
            if submitted:
                user = db.verify_user(username, password)
                if user:
                    st.session_state.authenticated = True
                    st.session_state.username = user[0]
                    st.session_state.role = user[1]
                    st.rerun()
                else:
                    st.error("Invalid username or password")
        
        st.markdown("---")
        st.markdown("### Demo Credentials")
        st.info("Username: admin\nPassword: admin123")

# Main app
def main():
    # Sidebar navigation
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000000/student-registration.png")
        st.title("🎓 Student Management")
        st.markdown(f"Welcome, **{st.session_state.username}**!")
        st.markdown(f"Role: **{st.session_state.role}**")
        st.markdown("---")
        
        # Navigation
        pages = ["Dashboard", "Student Management", "Course Management", 
                "Enrollments", "Grades", "Attendance", "Reports", "Settings"]
        
        for page in pages:
            if st.button(page, use_container_width=True):
                st.session_state.current_page = page
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.session_state.role = None
            st.rerun()
    
    # Main content area
    st.title(f"📚 {st.session_state.current_page}")
    
    if st.session_state.current_page == "Dashboard":
        show_dashboard()
    elif st.session_state.current_page == "Student Management":
        show_student_management()
    elif st.session_state.current_page == "Course Management":
        show_course_management()
    elif st.session_state.current_page == "Enrollments":
        show_enrollments()
    elif st.session_state.current_page == "Grades":
        show_grades()
    elif st.session_state.current_page == "Attendance":
        show_attendance()
    elif st.session_state.current_page == "Reports":
        show_reports()
    elif st.session_state.current_page == "Settings":
        show_settings()

def show_dashboard():
    col1, col2, col3, col4 = st.columns(4)
    
    # Get data
    students_df = db.get_all_students()
    courses_df = db.get_all_courses()
    
    with col1:
        st.metric("Total Students", len(students_df))
    with col2:
        st.metric("Total Courses", len(courses_df))
    with col3:
        active_students = len(students_df[students_df['status'] == 'active']) if not students_df.empty else 0
        st.metric("Active Students", active_students)
    with col4:
        # You can add more metrics here
        st.metric("System Status", "Online")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Recent Students")
        if not students_df.empty:
            st.dataframe(students_df[['student_id', 'first_name', 'last_name', 'email']].head(5), 
                        use_container_width=True)
        else:
            st.info("No students found")
    
    with col2:
        st.subheader("📋 Available Courses")
        if not courses_df.empty:
            st.dataframe(courses_df[['course_id', 'course_name', 'instructor', 'credits']].head(5),
                        use_container_width=True)
        else:
            st.info("No courses found")
    
    # Quick actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ Add Student", use_container_width=True):
            st.session_state.current_page = "Student Management"
            st.rerun()
    
    with col2:
        if st.button("📚 Add Course", use_container_width=True):
            st.session_state.current_page = "Course Management"
            st.rerun()
    
    with col3:
        if st.button("📝 Enroll Student", use_container_width=True):
            st.session_state.current_page = "Enrollments"
            st.rerun()
    
    with col4:
        if st.button("📊 View Reports", use_container_width=True):
            st.session_state.current_page = "Reports"
            st.rerun()

def show_student_management():
    tab1, tab2, tab3 = st.tabs(["View Students", "Add Student", "Manage Students"])
    
    with tab1:
        st.subheader("📋 All Students")
        students_df = db.get_all_students()
        
        if not students_df.empty:
            # Search filter
            search = st.text_input("🔍 Search students", placeholder="Enter name or ID...")
            if search:
                mask = (students_df['first_name'].str.contains(search, case=False) | 
                       students_df['last_name'].str.contains(search, case=False) |
                       students_df['student_id'].str.contains(search, case=False))
                filtered_df = students_df[mask]
            else:
                filtered_df = students_df
            
            st.dataframe(filtered_df, use_container_width=True)
            
            # Export option
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="📥 Download as CSV",
                data=csv,
                file_name=f"students_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No students found. Add a student to get started.")
    
    with tab2:
        st.subheader("➕ Add New Student")
        
        with st.form("add_student_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                student_id = st.text_input("Student ID", value=generate_student_id())
                first_name = st.text_input("First Name *")
                last_name = st.text_input("Last Name *")
                email = st.text_input("Email")
                phone = st.text_input("Phone")
            
            with col2:
                date_of_birth = st.date_input("Date of Birth")
                address = st.text_area("Address", height=100)
                enrollment_date = st.date_input("Enrollment Date", value=datetime.now())
                status = st.selectbox("Status", ["active", "inactive", "graduated", "suspended"])
            
            submitted = st.form_submit_button("Add Student", use_container_width=True)
            
            if submitted:
                if not first_name or not last_name:
                    st.error("First name and last name are required!")
                else:
                    student_data = (
                        student_id, first_name, last_name, 
                        date_of_birth.strftime("%Y-%m-%d") if date_of_birth else None,
                        email, phone, address, 
                        enrollment_date.strftime("%Y-%m-%d"), status
                    )
                    
                    if db.add_student(student_data):
                        st.success(f"Student {first_name} {last_name} added successfully!")
                        st.balloons()
                    else:
                        st.error("Student ID or Email already exists!")
    
    with tab3:
        st.subheader("✏️ Update or Delete Student")
        
        students_df = db.get_all_students()
        if not students_df.empty:
            student_options = students_df.apply(
                lambda x: f"{x['student_id']} - {x['first_name']} {x['last_name']}", axis=1
            ).tolist()
            
            selected_student = st.selectbox("Select Student", student_options)
            
            if selected_student:
                student_id = selected_student.split(" - ")[0]
                student_data = db.get_student(student_id)
                
                if not student_data.empty:
                    student = student_data.iloc[0]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Current Information:**")
                        st.write(f"ID: {student['student_id']}")
                        st.write(f"Name: {student['first_name']} {student['last_name']}")
                        st.write(f"Email: {student['email']}")
                        st.write(f"Phone: {student['phone']}")
                        st.write(f"Status: {student['status']}")
                    
                    with col2:
                        st.write("**Update Information:**")
                        
                        # Update form
                        with st.form("update_student_form"):
                            new_status = st.selectbox(
                                "Update Status", 
                                ["active", "inactive", "graduated", "suspended"],
                                index=["active", "inactive", "graduated", "suspended"].index(student['status'])
                            )
                            new_email = st.text_input("Update Email", value=student['email'] or "")
                            new_phone = st.text_input("Update Phone", value=student['phone'] or "")
                            
                            update_col1, update_col2 = st.columns(2)
                            with update_col1:
                                update_submitted = st.form_submit_button("Update Student")
                            with update_col2:
                                delete_submitted = st.form_submit_button("Delete Student", type="secondary")
                            
                            if update_submitted:
                                updates = {
                                    'status': new_status,
                                    'email': new_email,
                                    'phone': new_phone
                                }
                                db.update_student(student_id, updates)
                                st.success("Student updated successfully!")
                                st.rerun()
                            
                            if delete_submitted:
                                if st.checkbox("Confirm deletion"):
                                    db.delete_student(student_id)
                                    st.success("Student deleted successfully!")
                                    st.rerun()
        else:
            st.info("No students to manage")

def show_course_management():
    tab1, tab2, tab3 = st.tabs(["View Courses", "Add Course", "Manage Courses"])
    
    with tab1:
        st.subheader("📚 All Courses")
        courses_df = db.get_all_courses()
        
        if not courses_df.empty:
            search = st.text_input("🔍 Search courses", placeholder="Enter course name, ID, or instructor...")
            if search:
                mask = (courses_df['course_name'].str.contains(search, case=False) | 
                       courses_df['course_id'].str.contains(search, case=False) |
                       courses_df['instructor'].str.contains(search, case=False))
                filtered_df = courses_df[mask]
            else:
                filtered_df = courses_df
            
            st.dataframe(filtered_df, use_container_width=True)
        else:
            st.info("No courses found. Add a course to get started.")
    
    with tab2:
        st.subheader("➕ Add New Course")
        
        with st.form("add_course_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                course_id = st.text_input("Course ID", value=generate_course_id())
                course_name = st.text_input("Course Name *")
                credits = st.number_input("Credits", min_value=1, max_value=6, value=3)
                department = st.text_input("Department")
            
            with col2:
                instructor = st.text_input("Instructor")
                semester = st.selectbox(
                    "Semester", 
                    ["Fall 2024", "Spring 2024", "Summer 2024", "Fall 2025"]
                )
                max_students = st.number_input("Maximum Students", min_value=1, max_value=200, value=30)
            
            submitted = st.form_submit_button("Add Course", use_container_width=True)
            
            if submitted:
                if not course_name:
                    st.error("Course name is required!")
                else:
                    course_data = (course_id, course_name, credits, department, 
                                 instructor, semester, max_students)
                    
                    if db.add_course(course_data):
                        st.success(f"Course {course_name} added successfully!")
                        st.balloons()
                    else:
                        st.error("Course ID already exists!")

def show_enrollments():
    st.subheader("📝 Student Enrollment")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Select Student")
        students_df = db.get_all_students()
        if not students_df.empty:
            student_options = students_df[students_df['status'] == 'active'].apply(
                lambda x: f"{x['student_id']} - {x['first_name']} {x['last_name']}", axis=1
            ).tolist()
            
            selected_student = st.selectbox("Choose student", student_options, key="enroll_student")
            
            if selected_student:
                student_id = selected_student.split(" - ")[0]
                
                # Show enrolled courses
                st.write("### Currently Enrolled Courses")
                enrolled_df = db.get_student_courses(student_id)
                if not enrolled_df.empty:
                    st.dataframe(enrolled_df[['course_id', 'course_name', 'semester', 'grade']])
                else:
                    st.info("No courses enrolled")
    
    with col2:
        st.write("### Available Courses")
        courses_df = db.get_all_courses()
        
        if not courses_df.empty and selected_student:
            semester = st.selectbox(
                "Select Semester",
                ["Fall 2024", "Spring 2024", "Summer 2024", "Fall 2025"]
            )
            
            # Filter out already enrolled courses
            enrolled_courses = set()
            if not enrolled_df.empty:
                enrolled_courses = set(enrolled_df[enrolled_df['semester'] == semester]['course_id'])
            
            available_courses = courses_df[~courses_df['course_id'].isin(enrolled_courses)]
            
            if not available_courses.empty:
                course_options = available_courses.apply(
                    lambda x: f"{x['course_id']} - {x['course_name']} ({x['instructor']})", axis=1
                ).tolist()
                
                selected_course = st.selectbox("Choose course", course_options)
                
                if st.button("Enroll Student", use_container_width=True, type="primary"):
                    course_id = selected_course.split(" - ")[0]
                    success, message = db.enroll_student(student_id, course_id, semester)
                    
                    if success:
                        st.success(message)
                        st.balloons()
                        st.rerun()
                    else:
                        st.error(message)
            else:
                st.info("No available courses for this semester")

def show_grades():
    st.subheader("📊 Grade Management")
    
    tab1, tab2 = st.tabs(["Enter Grades", "View Grades"])
    
    with tab1:
        st.write("### Enter Grades for Students")
        
        courses_df = db.get_all_courses()
        if not courses_df.empty:
            selected_course = st.selectbox(
                "Select Course",
                courses_df.apply(lambda x: f"{x['course_id']} - {x['course_name']}", axis=1).tolist()
            )
            
            if selected_course:
                course_id = selected_course.split(" - ")[0]
                
                # Get enrolled students
                students_df = db.get_course_students(course_id)
                
                if not students_df.empty:
                    st.write(f"**Enrolled Students:** {len(students_df)}")
                    
                    assignment_name = st.text_input("Assignment Name")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        max_score = st.number_input("Max Score", value=100, min_value=1)
                    with col2:
                        weight = st.number_input("Weight", value=1.0, min_value=0.1, max_value=10.0)
                    
                    st.write("### Enter Grades")
                    
                    for idx, student in students_df.iterrows():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        
                        with col1:
                            st.write(f"{student['first_name']} {student['last_name']} ({student['student_id']})")
                        
                        with col2:
                            score = st.number_input(
                                f"Score for {student['student_id']}",
                                min_value=0.0,
                                max_value=float(max_score),
                                step=0.1,
                                key=f"score_{student['student_id']}_{idx}"
                            )
                        
                        with col3:
                            if st.button(f"Save", key=f"save_{student['student_id']}_{idx}"):
                                # Get enrollment_id
                                enrollment_query = '''
                                    SELECT enrollment_id FROM enrollments 
                                    WHERE student_id = ? AND course_id = ?
                                '''
                                enrollment_df = pd.read_sql_query(
                                    enrollment_query, 
                                    db.conn, 
                                    params=[student['student_id'], course_id]
                                )
                                
                                if not enrollment_df.empty:
                                    enrollment_id = enrollment_df.iloc[0]['enrollment_id']
                                    db.add_grade(enrollment_id, assignment_name, score, max_score, weight)
                                    st.success(f"Grade saved for {student['first_name']}")
                                else:
                                    st.error("Enrollment not found")
                else:
                    st.info("No students enrolled in this course")
    
    with tab2:
        st.write("### View Student Grades")
        
        students_df = db.get_all_students()
        if not students_df.empty:
            selected_student = st.selectbox(
                "Select Student",
                students_df.apply(lambda x: f"{x['student_id']} - {x['first_name']} {x['last_name']}", axis=1).tolist()
            )
            
            if selected_student:
                student_id = selected_student.split(" - ")[0]
                
                # Get grades
                grades_df = db.get_student_grades(student_id)
                
                if not grades_df.empty:
                    st.dataframe(grades_df)
                    
                    # Calculate GPA
                    gpa = calculate_gpa(grades_df)
                    st.metric("Current GPA", f"{gpa:.2f}")
                    
                    # Grade distribution chart
                    fig = create_grade_distribution_chart(grades_df)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No grades recorded for this student")

def show_attendance():
    st.subheader("📋 Attendance Management")
    
    courses_df = db.get_all_courses()
    if not courses_df.empty:
        selected_course = st.selectbox(
            "Select Course",
            courses_df.apply(lambda x: f"{x['course_id']} - {x['course_name']}", axis=1).tolist()
        )
        
        if selected_course:
            course_id = selected_course.split(" - ")[0]
            
            col1, col2 = st.columns([2, 1])
            
            with col1:
                attendance_date = st.date_input("Date", value=datetime.now())
            
            with col2:
                st.write("")
                st.write("")
                if st.button("Load Attendance Sheet", use_container_width=True):
                    st.session_state.attendance_date = attendance_date.strftime("%Y-%m-%d")
            
            if 'attendance_date' in st.session_state:
                date_str = st.session_state.attendance_date
                
                # Get attendance report
                attendance_df = db.get_attendance_report(course_id, date_str)
                
                if not attendance_df.empty:
                    st.write(f"**Attendance for {date_str}**")
                    
                    # Bulk actions
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("Mark All Present", use_container_width=True):
                            for _, student in attendance_df.iterrows():
                                db.mark_attendance(student['student_id'], course_id, date_str, 'present')
                            st.success("All marked present!")
                            st.rerun()
                    
                    with col2:
                        if st.button("Mark All Absent", use_container_width=True):
                            for _, student in attendance_df.iterrows():
                                db.mark_attendance(student['student_id'], course_id, date_str, 'absent')
                            st.success("All marked absent!")
                            st.rerun()
                    
                    # Individual attendance marking
                    for idx, student in attendance_df.iterrows():
                        col1, col2, col3 = st.columns([3, 2, 1])
                        
                        with col1:
                            st.write(f"{student['first_name']} {student['last_name']}")
                        
                        with col2:
                            current_status = student['status']
                            new_status = st.selectbox(
                                f"Status for {student['student_id']}",
                                ['present', 'absent', 'late', 'excused'],
                                index=['present', 'absent', 'late', 'excused'].index(current_status),
                                key=f"status_{student['student_id']}_{idx}"
                            )
                        
                        with col3:
                            if st.button(f"Update", key=f"update_{student['student_id']}_{idx}"):
                                db.mark_attendance(student['student_id'], course_id, date_str, new_status)
                                st.success(f"Attendance updated for {student['first_name']}")
                                st.rerun()
                else:
                    st.info("No students enrolled in this course")

def show_reports():
    st.subheader("📈 Academic Reports")
    
    report_type = st.selectbox(
        "Select Report Type",
        ["Student Performance", "Course Analytics", "Attendance Summary", "Grade Distribution"]
    )
    
    if report_type == "Student Performance":
        students_df = db.get_all_students()
        if not students_df.empty:
            selected_student = st.selectbox(
                "Select Student",
                students_df.apply(lambda x: f"{x['student_id']} - {x['first_name']} {x['last_name']}", axis=1).tolist()
            )
            
            if selected_student:
                student_id = selected_student.split(" - ")[0]
                
                # Get student details
                student_data = db.get_student(student_id)
                
                if not student_data.empty:
                    student = student_data.iloc[0]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Name", f"{student['first_name']} {student['last_name']}")
                    with col2:
                        st.metric("Student ID", student['student_id'])
                    with col3:
                        st.metric("Status", student['status'])
                    
                    # Get grades
                    grades_df = db.get_student_grades(student_id)
                    
                    if not grades_df.empty:
                        # Calculate statistics
                        gpa = calculate_gpa(grades_df)
                        st.metric("GPA", f"{gpa:.2f}")
                        
                        # Show grades by course
                        st.write("### Grades by Course")
                        st.dataframe(grades_df)
                        
                        # Grade distribution
                        fig = create_grade_distribution_chart(grades_df)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("No grades recorded for this student")
    
    elif report_type == "Course Analytics":
        courses_df = db.get_all_courses()
        if not courses_df.empty:
            selected_course = st.selectbox(
                "Select Course",
                courses_df.apply(lambda x: f"{x['course_id']} - {x['course_name']}", axis=1).tolist()
            )
            
            if selected_course:
                course_id = selected_course.split(" - ")[0]
                
                # Get course details
                course_data = db.get_course(course_id)
                
                if not course_data.empty:
                    course = course_data.iloc[0]
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Course Name", course['course_name'])
                    with col2:
                        st.metric("Instructor", course['instructor'] or "TBD")
                    with col3:
                        st.metric("Credits", course['credits'])
                    
                    # Get enrolled students
                    students_df = db.get_course_students(course_id)
                    
                    st.write(f"### Enrolled Students: {len(students_df)}")
                    
                    if not students_df.empty:
                        st.dataframe(students_df[['student_id', 'first_name', 'last_name', 'grade']])
                        
                        # Grade distribution for this course
                        grade_counts = students_df['grade'].value_counts()
                        fig = px.pie(
                            values=grade_counts.values,
                            names=grade_counts.index,
                            title="Grade Distribution"
                        )
                        st.plotly_chart(fig, use_container_width=True)

def show_settings():
    st.subheader("⚙️ System Settings")
    
    tab1, tab2 = st.tabs(["User Management", "System Info"])
    
    with tab1:
        st.write("### Add New User")
        
        with st.form("add_user_form"):
            new_username = st.text_input("Username")
            new_password = st.text_input("Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            role = st.selectbox("Role", ["admin", "staff", "teacher"])
            
            if st.form_submit_button("Create User", use_container_width=True):
                if not new_username or not new_password:
                    st.error("Username and password are required!")
                elif new_password != confirm_password:
                    st.error("Passwords do not match!")
                elif len(new_password) < 6:
                    st.error("Password must be at least 6 characters long!")
                else:
                    if db.add_user(new_username, new_password, role):
                        st.success(f"User {new_username} created successfully!")
                        st.balloons()
                    else:
                        st.error("Username already exists!")
    
    with tab2:
        st.write("### System Information")
        
        # Database stats
        students_df = db.get_all_students()
        courses_df = db.get_all_courses()
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total Students", len(students_df))
            st.metric("Active Students", len(students_df[students_df['status'] == 'active']) if not students_df.empty else 0)
        
        with col2:
            st.metric("Total Courses", len(courses_df))
            st.metric("Total Enrollments", "Calculate from DB")
        
        st.write("### Database Backup")
        if st.button("Create Backup", use_container_width=True):
            # Create backup logic here
            st.success("Backup created successfully!")

# Run the app
if __name__ == "__main__":
    if not st.session_state.authenticated:
        login()
    else:
        main()
