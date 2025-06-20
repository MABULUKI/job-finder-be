from django.urls import path
from .views import (
    RecruiterSignupView, 
    JobSeekerSignupView, 
    LoginView, 
    LogoutView,
    RecruiterProfileUpdateView, 
    JobSeekerProfileUpdateView,
    SeekerFeedbackCreateView,
    SeekerFeedbackListView,
    MarkRecruiterProfileUpdatedView,
    MarkJobSeekerProfileUpdatedView
)

urlpatterns = [
    path('recruiter/signup/', RecruiterSignupView.as_view(), name='recruiter-signup'),
    path('seeker/signup/', JobSeekerSignupView.as_view(), name='seeker-signup'),
    path('recruiter/profile/', RecruiterProfileUpdateView.as_view(), name='recruiter-profile-update'),
    path('seeker/profile/', JobSeekerProfileUpdateView.as_view(), name='jobseeker-profile-update'),
    path('seeker/<int:seeker_id>/feedbacks/', SeekerFeedbackListView.as_view(), name='seeker-feedback-list'),
    path('seeker/feedback/', SeekerFeedbackCreateView.as_view(), name='seeker-feedback-create'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('recruiter/mark-profile-updated/', MarkRecruiterProfileUpdatedView.as_view(), name='recruiter-mark-profile-updated'),
    path('seeker/mark-profile-updated/', MarkJobSeekerProfileUpdatedView.as_view(), name='seeker-mark-profile-updated'),
]
