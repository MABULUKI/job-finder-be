from django.shortcuts import render
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from .models import Job, Application
from .serializers import (
    JobSerializer,
    ApplicationSerializer
)
from authentication.serializers import JobSeekerProfileSerializer
from .ai.job_recommendation import get_job_recommendations_for_seeker
from .ai.candidate_recommendation import get_candidate_recommendations_for_job
from rest_framework.views import APIView
from django.utils import timezone
from datetime import timedelta

# Create your views here.


class JobCreateView(generics.CreateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

class JobListView(generics.ListAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.AllowAny]

class ApplicationCreateView(generics.CreateAPIView):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, 'seeker_profile'):
            raise PermissionDenied('Only job seekers can apply for jobs.')
        serializer.save(seeker=user.seeker_profile)

class ApplicationListView(generics.ListAPIView):
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if hasattr(user, 'seeker_profile'):
            return Application.objects.filter(seeker=user.seeker_profile)
        elif hasattr(user, 'recruiter_profile'):
            return Application.objects.filter(job__recruiter=user.recruiter_profile)
        return Application.objects.none()

class JobRecommendationView(generics.GenericAPIView):
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        if not hasattr(user, 'seeker_profile'):
            return Response({'detail': 'Only job seekers can get recommendations.'}, status=403)
        jobs = Job.objects.all()
        recommended = get_job_recommendations_for_seeker(user.seeker_profile, jobs)
        print(f"[DEBUG] Recommended jobs count: {len(recommended)}")
        print(f"[DEBUG] Recommended job IDs: {[job.id for job in recommended]}")
        # Check if model is being used: print top scores
        import numpy as np
        from core.ai.job_recommendation import extract_job_features
        features = [extract_job_features(user.seeker_profile, job) for job in jobs]
        if features:
            X = np.stack(features)
            from catboost import CatBoostClassifier
            import os
            model_path = os.path.join(os.path.dirname(__file__), 'ai/models/job_recommendation_model.cbm')
            catboost_model = CatBoostClassifier()
            catboost_model.load_model(model_path)
            scores = catboost_model.predict_proba(X)[:, 1]
            print(f"[DEBUG] Top 10 CatBoost scores: {sorted(scores, reverse=True)[:10]}")
        serializer = self.get_serializer(recommended, many=True)
        return Response(serializer.data)

class CandidateRecommendationView(generics.GenericAPIView):
    serializer_class = JobSeekerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, job_id):
        user = request.user
        if not hasattr(user, 'recruiter_profile'):
            return Response({'detail': 'Only recruiters can get candidate recommendations.'}, status=403)
        try:
            job = Job.objects.get(id=job_id, recruiter=user.recruiter_profile)
        except Job.DoesNotExist:
            return Response({'detail': 'Job not found or not owned by recruiter.'}, status=404)
        from authentication.models import JobSeekerProfile
        seekers = JobSeekerProfile.objects.all()
        recommended = get_candidate_recommendations_for_job(job, seekers)
        serializer = self.get_serializer(recommended, many=True)
        return Response(serializer.data)

class JobUpdateNextStepView(generics.UpdateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        job = super().get_object()
        user = self.request.user
        if not hasattr(user, 'recruiter_profile') or job.recruiter != user.recruiter_profile:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied('You do not have permission to update this job.')
        return job

class ApplicationNextStepView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response({'detail': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not hasattr(user, 'recruiter_profile') or application.job.recruiter != user.recruiter_profile:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        next_step_type = request.data.get('next_step_type')
        job_duration_days = request.data.get('job_duration_days')
        if next_step_type not in dict(Application._meta.get_field('next_step_type').choices):
            return Response({'detail': 'Invalid next_step_type.'}, status=status.HTTP_400_BAD_REQUEST)
        application.selected_for_next_step = True
        application.next_step_type = next_step_type
        application.next_step_status = 'PENDING'
        if next_step_type == 'DIRECT_HIRE' and job_duration_days:
            application.job_duration_days = job_duration_days
        application.save()
        return Response(ApplicationSerializer(application).data, status=status.HTTP_200_OK)

class ApplicationApproveNextStepView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        try:
            application = Application.objects.get(pk=pk)
        except Application.DoesNotExist:
            return Response({'detail': 'Application not found.'}, status=status.HTTP_404_NOT_FOUND)
        user = request.user
        if not hasattr(user, 'seeker_profile') or application.seeker != user.seeker_profile:
            return Response({'detail': 'Permission denied.'}, status=status.HTTP_403_FORBIDDEN)
        approve = request.data.get('approve')
        if approve is True:
            application.applicant_approved = True
            application.next_step_status = 'APPROVED'
            application.save()
            # If direct hire, set is_available = False for duration
            if application.next_step_type == 'DIRECT_HIRE' and application.job_duration_days:
                seeker = application.seeker
                seeker.is_available = False
                seeker.save()
                # Optionally, you could schedule a task to re-enable availability after duration
        elif approve is False:
            application.applicant_approved = False
            application.next_step_status = 'DECLINED'
            application.save()
        else:
            return Response({'detail': 'Missing or invalid approve field.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response(ApplicationSerializer(application).data, status=status.HTTP_200_OK)

class ToggleAvailabilityView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        user = request.user
        if not hasattr(user, 'seeker_profile'):
            return Response({'detail': 'Not a seeker.'}, status=status.HTTP_403_FORBIDDEN)
        seeker = user.seeker_profile
        seeker.is_available = not seeker.is_available
        seeker.save()
        return Response({'is_available': seeker.is_available}, status=status.HTTP_200_OK)
