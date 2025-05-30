from django.core.management.base import BaseCommand
import pandas as pd
import os
from main_app.models import Assessment

class Command(BaseCommand):
    help = "ETL: Export assessment data with course, difficulty, student, and department info to CSV"

    def handle(self, *args, **kwargs):
        # Buat folder output
        output_dir = 'output'
        os.makedirs(output_dir, exist_ok=True)

        # Ambil semua data assessment dengan select_related
        assessments = Assessment.objects.select_related(
            'enroll_id__stu_id__dept_id',
            'enroll_id__course_id__coursedifficulty'
        ).all()

        data = []
        for a in assessments:
            enroll = a.enroll_id
            student = getattr(enroll, 'stu_id', None)
            department = getattr(student, 'dept_id', None)
            course = getattr(enroll, 'course_id', None)
            difficulty = getattr(course, 'coursedifficulty', None)

            data.append({
                'assessment_id': a.assessment_id,
                'assessment_type': a.assessment_type,
                'score': a.score,
                'enroll_id': enroll.enroll_id if enroll else None,
                'course_id': course.course_id if course else None,
                'course_name': course.course_name if course else None,
                'difficulty_level': difficulty.difficulty_level if difficulty else None,
                'stu_id': student.stu_id if student else None,
                'student_name': student.name if student else None,
                'dept_name': department.dept_name if department else None
            })

        # Buat DataFrame dengan urutan kolom yang diinginkan
        df = pd.DataFrame(data, columns=[
            'assessment_id', 'assessment_type', 'score',
            'enroll_id', 'course_id', 'course_name',
            'difficulty_level', 'stu_id', 'student_name', 'dept_name'
        ])

        # Simpan ke CSV
        df.to_csv('course_recommendation.csv', index=False)

        self.stdout.write(self.style.SUCCESS(f'CSV successfully exported!'))
