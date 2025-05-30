from django.core.management.base import BaseCommand
import pandas as pd
from main_app.models import (
    CourseDifficulty, CourseInstructor, 
    Enrollment, Attendance, Assessment
)
import os
import django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")
django.setup()

class Command(BaseCommand):
    help = 'Extract and join all tables into one CSV file (grade as student average)'

    def handle(self, *args, **kwargs):
        data = []

        # Hitung rata-rata grade per student
        enrollments = Enrollment.objects.all()
        student_grades = {}
        for enrollment in enrollments:
            stu_id = enrollment.stu_id
            student_grades.setdefault(stu_id, []).append(enrollment.grade)
        
        # Buat dict rata-rata grade
        avg_grade_per_student = {stu_id: sum(grades)/len(grades) 
                                 for stu_id, grades in student_grades.items()}
        
        # Loop ke semua enrollment lagi untuk membuat dataframe
        for enrollment in enrollments:
            student = enrollment.stu_id
            course = enrollment.course_id
            semester = enrollment.semester_id
            
            department = student.dept_id
            instructor_link = CourseInstructor.objects.filter(course_id=course, semester_id=semester).first()
            instructor = instructor_link.instructor_id if instructor_link else None
            course_difficulty = CourseDifficulty.objects.filter(course_id=course).first()
            
            assessments = Assessment.objects.filter(enroll_id=enrollment)
            avg_score = assessments.aggregate(django.db.models.Avg('score'))['score__avg'] or 0
            
            attendance = Attendance.objects.filter(enroll_id=enrollment).first()
            attendance_pct = attendance.attendance_percentage if attendance else 0
            
            data.append({
                "student_id": student.stu_id,
                "gender": student.gender,
                "age": (pd.Timestamp.now() - pd.Timestamp(student.dob)).days // 365,
                "department_id": department.dept_id if department else None,
                
                "course_id": course.course_id,
                "difficulty_level": course_difficulty.difficulty_level if course_difficulty else 'Medium',
                
                "semester_id": semester.semester_id,
                
                "instructor_id": instructor.instructor_id if instructor else None,
                
                "attendance_percentage": attendance_pct,
                "average_score": avg_score,
                "grade": avg_grade_per_student[student]
            })
        
        df = pd.DataFrame(data)
        df.to_csv('all_data_joined.csv', index=False)
        self.stdout.write(self.style.SUCCESS('All data joined and exported to all_data_joined.csv with averaged grade.'))
