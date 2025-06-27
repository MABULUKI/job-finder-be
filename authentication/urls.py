from django.urls import path
from .views import (
    RecruiterProfileView,
    RecruiterProfileUpdateView,
    JobSeekerProfileView,
    JobSeekerProfileUpdateView,
    LoginView,
    LogoutView,
    RecruiterSignupView,
    JobSeekerSignupView,
    SeekerFeedbackCreateView,  # Now uses FeedbackRating model
    SeekerFeedbackListView,    # Now uses FeedbackRating model
    MarkRecruiterProfileUpdatedView,
    MarkJobSeekerProfileUpdatedView,
    JobSeekerProfilePictureView,
    JobSeekerResumeView
)

urlpatterns = [
    path('recruiter/signup/', RecruiterSignupView.as_view(), name='recruiter-signup'),
    path('seeker/signup/', JobSeekerSignupView.as_view(), name='seeker-signup'),
    path('recruiter/profile/', RecruiterProfileView.as_view(), name='recruiter-profile'),
    path('recruiter/profile/update/', RecruiterProfileUpdateView.as_view(), name='recruiter-profile-update'),
    path('seeker/profile/', JobSeekerProfileView.as_view(), name='jobseeker-profile'),
    path('seeker/profile/update/', JobSeekerProfileUpdateView.as_view(), name='jobseeker-profile-update'),
    path('seeker/profile/picture/', JobSeekerProfilePictureView.as_view(), name='seeker-profile-picture'),
    path('seeker/resume/', JobSeekerResumeView.as_view(), name='seeker-resume'),
    path('seeker/<int:seeker_id>/feedbacks/', SeekerFeedbackListView.as_view(), name='seeker-feedback-list'),
    path('seeker/feedback/', SeekerFeedbackCreateView.as_view(), name='seeker-feedback-create'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('recruiter/mark-profile-updated/', MarkRecruiterProfileUpdatedView.as_view(), name='recruiter-mark-profile-updated'),
    path('seeker/mark-profile-updated/', MarkJobSeekerProfileUpdatedView.as_view(), name='seeker-mark-profile-updated'),
]
