import base64
from io import BytesIO
import json
import seaborn as sns
from django.contrib import messages
from django.shortcuts import render
from matplotlib import pyplot as plt
from .forms import AttendancePredictionForm
from .utils import analyze_courses, predict_attendance
from .models import Department, PredictionRecord
import plotly.express as px
import pandas as pd
from django.http import JsonResponse, HttpResponse

def base(request):
    return render(request, 'base_content.html')


def predict_attendance_view(request):
    if request.method == 'POST':
        form = AttendancePredictionForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            course = data['course_id']           # instance of Course
            semester = data['semester_id'] 

            attendance_percentage = predict_attendance({
                'average_score': data['average_score'],
                'grade': data['grade'],
                'course_id': course.course_id,       # hanya ID-nya
                'semester_id': semester.semester_id  # hanya ID-nya
            }) 
            
            # Save to database
            record = PredictionRecord(
                name=data['name'],
                average_score=data['average_score'],
                grade=data['grade'],
                semester_id=semester.semester_id,
                course_id=course.course_id,
                predicted_attendance=attendance_percentage
            )
            record.save()
            
            # Create chart
            fig = px.bar(
                x=['Predicted Attendance'],
                y=[attendance_percentage],
                title='Attendance Prediction',
                labels={'y': 'Percentage (%)', 'x': ''},
                text=[f"{attendance_percentage:.1f}%"],
                range_y=[0, 100]
            )
            fig.update_traces(marker_color='#4e73df', textposition='outside')
            chart = fig.to_html()
            
            return render(request, 'attendance_prediction_dashboard.html', {
                'form': form,
                'prediction': attendance_percentage,
                'chart': chart,
                'name': data['name']
            })
    else:
        form = AttendancePredictionForm()
    
    return render(request, 'attendance_prediction_dashboard.html', {'form': form})

def course_recommendation(request):
    try:
        assessment_df = pd.read_csv('course_recommendation.csv')
        departments_qs = Department.objects.all()
        departments_list = list(departments_qs.values_list('dept_name', flat=True))  # FIXED

        initial_dept = request.session.get('selected_department')
        if initial_dept is None and departments_list:
            initial_dept = departments_list[0]  # default ke dept pertama

        if initial_dept:
            courses = sorted(assessment_df[assessment_df['dept_name'] == initial_dept]['course_name'].unique())
        else:
            courses = []

        context = {
            'departments': departments_list,
            'courses': courses,
            'selected_department': initial_dept
        }

        return render(request, 'course_recommendation.html', context)

    except FileNotFoundError:
        messages.error(request, "Data file not found. Please run the ETL command first.")
        context = {'departments': [], 'courses': []}
        return render(request, 'course_recommendation.html', context)


def get_courses(request):
    department = request.GET.get('department', '')

    try:
        assessment_df = pd.read_csv('course_recommendation.csv')
        courses = sorted(assessment_df[assessment_df['dept_name'] == department]['course_name'].unique())
        request.session['selected_department'] = department

        return HttpResponse(json.dumps(courses), content_type='application/json')

    except FileNotFoundError:
        return HttpResponse(json.dumps([]), content_type='application/json')


def analyze(request):
    if request.method != 'POST':
        return HttpResponse("Method not allowed", status=405)

    department = request.POST.get('department', '')
    course1 = request.POST.get('course1', '')
    course2 = request.POST.get('course2', '')

    if not department or not course1 or not course2:
        messages.error(request, "Please select a department and two courses")
        return render(request, 'course_recommendation.html')

    if course1 == course2:
        messages.error(request, "Please select two different courses")
        return render(request, 'course_recommendation.html')

    try:
        assessment_df = pd.read_csv('course_recommendation.csv')
        rules_df = pd.read_csv('course_apriori_rules.csv')

        result = analyze_courses(department, course1, course2, assessment_df, rules_df)

        if 'error' in result:
            messages.error(request, result['error'])
            return render(request, 'course_recommendation.html')

        img_data = create_visualization(result['rule_data'], course1, course2)

        departments_list = sorted(assessment_df['dept_name'].unique())
        courses = sorted(assessment_df[assessment_df['dept_name'] == department]['course_name'].unique())

        context = {
            'departments': departments_list,
            'courses': courses,
            'selected_department': department,
            'analysis_result': result,
            'visualization': img_data
        }

        return render(request,'course_analysis.html', context)

    except FileNotFoundError:
        messages.error(request, "Data files not found. Please run the ETL and Apriori commands first.")
        return render(request, 'course_recommendation.html')
    except Exception as e:
        messages.error(request, f"Error analyzing courses: {str(e)}")
        return render(request, 'course_recommendation.html')


def create_visualization(rule_data, course1, course2):
    """Create visualization of association rules metrics"""
    plt.figure(figsize=(10, 6))

    if rule_data is None or rule_data.empty:
        plt.text(0.5, 0.5, f"No association rule found between {course1} and {course2}",
                horizontalalignment='center', verticalalignment='center')
    else:
        metrics = ['support', 'confidence', 'lift']
        values = [rule_data[metric].values[0] for metric in metrics]

        colors = ['#5DA5DA', '#FAA43A', '#60BD68']
        ax = sns.barplot(x=metrics, y=values, palette=colors)

        for i, v in enumerate(values):
            ax.text(i, v + 0.02, f'{v:.3f}', ha='center')

        plt.title(f'Association Rule Metrics: {course1} and {course2}')
        plt.ylim(0, max(values) * 1.2)

    img_buffer = BytesIO()
    plt.savefig(img_buffer, format='png', bbox_inches='tight')
    img_buffer.seek(0)

    img_data = base64.b64encode(img_buffer.read()).decode('utf-8')
    plt.close()

    return img_data
