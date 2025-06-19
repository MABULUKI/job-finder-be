from django.urls import path
from .views import (
    RecruiterSignupView, 
    JobSeekerSignupView, 
    LoginView, 
    RecruiterProfileUpdateView, 
    JobSeekerProfileUpdateView,
    SeekerFeedbackCreateView,
    SeekerFeedbackListView
)

urlpatterns = [
    path('recruiter/signup/', RecruiterSignupView.as_view(), name='recruiter-signup'),
    path('seeker/signup/', JobSeekerSignupView.as_view(), name='seeker-signup'),
    path('recruiter/profile/', RecruiterProfileUpdateView.as_view(), name='recruiter-profile-update'),
    path('seeker/profile/', JobSeekerProfileUpdateView.as_view(), name='jobseeker-profile-update'),
    path('seeker/<int:seeker_id>/feedbacks/', SeekerFeedbackListView.as_view(), name='seeker-feedback-list'),
    path('seeker/feedback/', SeekerFeedbackCreateView.as_view(), name='seeker-feedback-create'),
    path('login/', LoginView.as_view(), name='login'),
]
