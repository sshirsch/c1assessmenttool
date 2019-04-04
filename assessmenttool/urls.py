from django.urls import path

from . import views

urlpatterns = [
    path('users/<user_id>', views.get_user),
    path('users', views.create_user),
    path('assessments/healthz', views.get_health),
    path('users/<int:user_id>/assessments', views.create_assessment),
    path('assessments/<assessment_id>', views.get_assessment),
    path('assessments/<assessment_id>/questions/<int:question_index>', views.get_question),
    path('assessments/<assessment_id>/questions/<int:question_index>/answers', views.submit_answer),
    path('assessments/<assessment_id>/start', views.start_assessment),
    path('assessments/<assessment_id>/end', views.end_assessment),
]
