from django.urls import path
from . import views, admin_view

urlpatterns = [
    path("", views.base, name="base"),
    path("retrain-model/<int:model_id>/", admin_view.retrain_model_view, name="retrain_model"),
    path("attendance_prediction_dashboard/", views.predict_attendance_view, name="attendance_prediction_dashboard"),
    path("course_recommendation/", views.course_recommendation, name="course_recommendation"),
    path("course_analysis/", views.analyze, name="course_analysis"),
    path('get-courses/', views.get_courses, name='get_courses'),
]