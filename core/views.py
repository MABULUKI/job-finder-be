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
from rest_framework.exceptions import PermissionDenied

# Create your views here.


class JobCreateView(generics.CreateAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, 'recruiter_profile'):
            raise permissions.exceptions.PermissionDenied('Only recruiters can post jobs.')
        serializer.save(recruiter=user.recruiter_profile)

class JobListView(generics.ListAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.AllowAny]


class JobDetailView(generics.RetrieveAPIView):
    """View to retrieve job details by ID, accessible by anyone"""
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [permissions.AllowAny]

class ApplicationCreateView(generics.CreateAPIView):
    queryset = Application.objects.all()
    serializer_class = ApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def create(self, request, *args, **kwargs):
        user = self.request.user
        if not hasattr(user, 'seeker_profile'):
            return Response(
                {'detail': 'Only job seekers can apply for jobs.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if job_id is in the request data
        job_id = request.data.get('job')
        if not job_id:
            return Response(
                {'detail': 'Job ID is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Check if the user has already applied for this job
        existing_application = Application.objects.filter(
            job_id=job_id,
            seeker=user.seeker_profile
        ).exists()
        
        if existing_application:
            return Response(
                {'detail': 'You have already applied for this job.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # If no existing application, proceed with creating a new one
        return super().create(request, *args, **kwargs)
    
    def perform_create(self, serializer):
        user = self.request.user
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


class JobApplicantsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, job_id):
        user = request.user
        if not hasattr(user, 'recruiter_profile'):
            return Response({'detail': 'Only recruiters can view job applicants.'}, status=status.HTTP_403_FORBIDDEN)
            
        try:
            job = Job.objects.get(id=job_id, recruiter=user.recruiter_profile)
        except Job.DoesNotExist:
            return Response({'detail': 'Job not found or not owned by recruiter.'}, status=status.HTTP_404_NOT_FOUND)
            
        # Get all applications for this job
        applications = Application.objects.filter(job=job)
        
        # Serialize the applications with detailed user information
        serialized_applications = []
        for application in applications:
            app_data = ApplicationSerializer(application).data
            # Add additional user details if needed
            app_data['user'] = {
                'id': application.seeker.user.id,
                'name': f"{application.seeker.user.first_name} {application.seeker.user.last_name}",
                'email': application.seeker.user.email,
                'phone': application.seeker.phone,  # Fixed: changed from phone_number to phone
                'skills': application.seeker.skills,
                'education': application.seeker.education,
            }
            # Calculate match score (placeholder - in production this would use AI model)
            app_data['match_score'] = 4.0  # Placeholder score between 0-5
            serialized_applications.append(app_data)
            
        return Response({
            'job_id': job.id,
            'job_title': job.title,
            'applicants': serialized_applications,
            'total_count': len(serialized_applications)
        }, status=status.HTTP_200_OK)

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

class DashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        if not hasattr(user, 'seeker_profile'):
            return Response({'detail': 'Not a seeker.'}, status=status.HTTP_403_FORBIDDEN)
        
        seeker = user.seeker_profile
        
        # Get all applications for this seeker
        applications = Application.objects.filter(seeker=seeker)
        
        # Calculate statistics
        stats = {
            'applications_count': applications.count(),
            'matches_count': applications.filter(status='ACCEPTED').count(),
            'interviews_count': applications.filter(
                next_step_type='INTERVIEW',
                selected_for_next_step=True
            ).count(),
            'direct_hires_count': applications.filter(
                next_step_type='DIRECT_HIRE',
                selected_for_next_step=True
            ).count(),
        }
        
        return Response(stats, status=status.HTTP_200_OK)


class RecruiterDashboardStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        if not hasattr(user, 'recruiter_profile'):
            return Response({'detail': 'Not a recruiter.'}, status=status.HTTP_403_FORBIDDEN)
        
        recruiter = user.recruiter_profile
        
        # Get all jobs posted by this recruiter
        jobs = Job.objects.filter(recruiter=recruiter)
        
        # Get all applications for jobs posted by this recruiter
        applications = Application.objects.filter(job__recruiter=recruiter)
        
        # Get recent applications (last 30 days)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_applications = applications.filter(applied_at__gte=thirty_days_ago)
        
        # Calculate statistics
        active_jobs_count = jobs.filter(application_deadline__gte=timezone.now().date()).count()
        
        # Get trend data (compare to previous 30 days)
        sixty_days_ago = timezone.now() - timedelta(days=60)
        previous_period_applications = applications.filter(
            applied_at__gte=sixty_days_ago,
            applied_at__lt=thirty_days_ago
        ).count()
        
        current_period_applications = recent_applications.count()
        applications_trend = current_period_applications - previous_period_applications
        
        stats = {
            'total_jobs': jobs.count(),
            'active_jobs': active_jobs_count,
            'total_applicants': applications.count(),
            'new_applications': recent_applications.count(),
            'trends': {
                'applications': applications_trend,
                'applications_percentage': calculate_percentage_change(previous_period_applications, current_period_applications),
            },
            # Get recent job postings with applicant counts
            'recent_jobs': [
                {
                    'id': job.id,
                    'title': job.title,
                    'date': job.posted_at.strftime('%Y-%m-%d'),
                    'status': 'Active' if job.application_deadline >= timezone.now().date() else 'Closed',
                    'applicants': Application.objects.filter(job=job).count(),
                }
                for job in jobs.order_by('-posted_at')[:5]  # Get 5 most recent jobs
            ]
        }
        
        return Response(stats, status=status.HTTP_200_OK)


def calculate_percentage_change(old_value, new_value):
    """Calculate percentage change between two values"""
    if old_value == 0:
        return 100 if new_value > 0 else 0
    return round(((new_value - old_value) / old_value) * 100)


class EmployerJobsView(generics.ListAPIView):
    """View to list all jobs posted by the authenticated employer/recruiter"""
    serializer_class = JobSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        if not hasattr(user, 'recruiter_profile'):
            raise PermissionDenied('Only recruiters can access their posted jobs.')
        
        # Return all jobs posted by this recruiter
        return Job.objects.filter(recruiter=user.recruiter_profile).order_by('-posted_at')
