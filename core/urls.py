from django.urls import path
from .views import (
    JobCreateView,
    JobListView,
    ApplicationCreateView,
    ApplicationListView,
    JobRecommendationView,
    CandidateRecommendationView,
    JobUpdateNextStepView,
    ApplicationNextStepView,
    ApplicationApproveNextStepView,
    ToggleAvailabilityView
)

urlpatterns = [
    path('jobs/', JobListView.as_view(), name='job-list'),
    path('jobs/create/', JobCreateView.as_view(), name='job-create'),
    path('jobs/<int:pk>/update-next-step/', JobUpdateNextStepView.as_view(), name='job-update-next-step'),
    path('applications/', ApplicationListView.as_view(), name='application-list'),
    path('applications/create/', ApplicationCreateView.as_view(), name='application-create'),
    path('jobs/recommended/', JobRecommendationView.as_view(), name='job-recommendation'),
    path('jobs/<int:job_id>/candidates/', CandidateRecommendationView.as_view(), name='candidate-recommendation'),
    path('applications/<int:pk>/next-step/', ApplicationNextStepView.as_view(), name='application-next-step'),
    path('applications/<int:pk>/approve-next-step/', ApplicationApproveNextStepView.as_view(), name='application-approve-next-step'),
    path('seeker/toggle-availability/', ToggleAvailabilityView.as_view(), name='toggle-availability'),
]
