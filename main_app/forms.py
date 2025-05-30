from django import forms
from .models import Course, Semester

class AttendancePredictionForm(forms.Form):
    name = forms.CharField(
        label='Your Name',
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    average_score = forms.FloatField(
        label='Previous Average Assignment Score',
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'})
    )
    grade = forms.FloatField(
        label='Previous Average Semester Grade',
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={'step': '0.1', 'class': 'form-control'})
    )
    course_id = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        label='Course You Want to Take',
        empty_label="Select a course",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    semester_id = forms.ModelChoiceField(
        queryset=Semester.objects.all(),
        label='Semester You Want to Take',
        empty_label="Select a semester",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
