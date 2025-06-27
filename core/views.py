from django.shortcuts import render, get_object_or_404
from rest_framework import generics, permissions
from rest_framework.response import Response
from rest_framework import status
from .models import Job, Application, Feedback
from .serializers import (
    JobSerializer,
    ApplicationSerializer,
    FeedbackSerializer
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
        application = serializer.save(seeker=user.seeker_profile)
        
        # Create notifications for both seeker and recruiter
        try:
            from notifications.services import create_application_notification
            create_application_notification(application)
        except ImportError:
            # Handle case where notifications app is not available
            pass

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
        
        # Get all job seekers but filter out those without key profile data
        seekers = JobSeekerProfile.objects.filter(is_available=True)
        print(f"[DEBUG] Total available job seekers: {seekers.count()}")
        
        # Get job details for debugging
        print(f"[DEBUG] Job ID: {job.id}, Title: {job.title}")
        print(f"[DEBUG] Job Skills: {job.skills}")
        print(f"[DEBUG] Job Description Length: {len(job.description) if job.description else 0}")
        
        # Get recommendations
        recommended = get_candidate_recommendations_for_job(job, seekers)
        print(f"[DEBUG] Recommended candidates count: {len(recommended)}")
        print(f"[DEBUG] Recommended candidate IDs: {[seeker.id for seeker in recommended]}")
        
        # Enhance response with match scores
        serializer = self.get_serializer(recommended, many=True)
        data = serializer.data
        
        # Add match score to each candidate
        for i, candidate in enumerate(data):
            # Calculate a simple match score based on skills overlap
            job_skills = set(skill.lower() for skill in job.skills) if job.skills else set()
            candidate_skills = set(skill.lower() for skill in candidate.get('skills', []))
            
            if job_skills and candidate_skills:
                match_score = len(job_skills.intersection(candidate_skills)) / len(job_skills) * 100
                candidate['match_score'] = round(match_score, 1)
            else:
                candidate['match_score'] = 50.0  # Default score
        
        return Response(data)


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
            
            # Extract seeker details from the serializer
            seeker_details = app_data.pop('seeker_details', {})
            
            # Format the application data for the frontend
            formatted_app = {
                'application_id': app_data['id'],
                'status': app_data['status'],
                'applied_at': app_data['applied_at'],
                'cover_letter': app_data['cover_letter'],
                'selected_for_next_step': app_data.get('selected_for_next_step', False),
                'next_step_type': app_data.get('next_step_type', ''),
                'next_step_status': app_data.get('next_step_status', ''),
                'name': seeker_details.get('full_name', 'Unknown'),
                'email': seeker_details.get('email', ''),
                'phone': seeker_details.get('phone', ''),
                'skills': seeker_details.get('skills', []),
                'education': seeker_details.get('education', []),
                'experience': seeker_details.get('experience', []),
                'resume_url': seeker_details.get('resume_url'),
                'profile_picture': seeker_details.get('profile_picture'),
                'linkedin': seeker_details.get('linkedin', ''),
                'location': seeker_details.get('location', ''),
                'willing_to_relocate': seeker_details.get('willing_to_relocate', False),
                'salary_expectation': seeker_details.get('salary_expectation'),
                'profile_id': seeker_details.get('id'),
                'rating': seeker_details.get('average_rating', 0) or 0.0,  # Default to 0.0 if None
                'feedback_count': seeker_details.get('feedback_count', 0),
                'feedbacks': seeker_details.get('feedbacks', []),
            }
            
            serialized_applications.append(formatted_app)
            
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
        recruiter_notes = request.data.get('recruiter_notes')
        
        # Validate next_step_type
        if next_step_type not in dict(Application._meta.get_field('next_step_type').choices) and next_step_type != 'REJECTED':
            return Response({'detail': 'Invalid next_step_type.'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Handle rejection case
        if next_step_type == 'REJECTED':
            application.status = 'REJECTED'
            if recruiter_notes:
                application.recruiter_notes = recruiter_notes
            application.save()
            return Response(ApplicationSerializer(application).data, status=status.HTTP_200_OK)
        
        # Handle normal next step flow
        application.selected_for_next_step = True
        application.next_step_type = next_step_type
        application.next_step_status = 'APPROVED'
        
        # Update application status based on next_step_type
        if next_step_type == 'DIRECT_HIRE':
            application.status = 'HIRED'
        elif next_step_type == 'INTERVIEW':
            application.status = 'INTERVIEW'
            
        # Set job duration for direct hires
        if next_step_type == 'DIRECT_HIRE' and job_duration_days:
            application.job_duration_days = job_duration_days
            
        # Save recruiter notes if provided
        if recruiter_notes:
            application.recruiter_notes = recruiter_notes
            
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


class SeekerFeedbackView(APIView):
    """View to retrieve all feedback for a job seeker"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, profile_id):
        # Get all feedback for this seeker from both models
        from authentication.models import SeekerFeedback
        
        # Get the seeker profile
        from authentication.models import JobSeekerProfile
        seeker = get_object_or_404(JobSeekerProfile, id=profile_id)
        
        # Combine feedback from both models
        application_feedbacks = Feedback.objects.filter(profile=seeker)
        seeker_feedbacks = SeekerFeedback.objects.filter(seeker=seeker)
        
        # Serialize the feedback
        app_serializer = FeedbackSerializer(application_feedbacks, many=True)
        
        # Create a custom response for seeker feedbacks
        seeker_feedback_data = [{
            'id': feedback.id,
            'rating': float(feedback.rating),
            'comment': feedback.comment,
            'created_at': feedback.created_at.strftime('%Y-%m-%d'),
            'recruiter_name': feedback.recruiter.company_name if feedback.recruiter else 'Unknown',
            'source': 'general_feedback'
        } for feedback in seeker_feedbacks]
        
        # Add source to application feedbacks
        app_feedback_data = app_serializer.data
        for feedback in app_feedback_data:
            feedback['source'] = 'application_feedback'
        
        # Combine both types of feedback
        all_feedback = list(app_feedback_data) + seeker_feedback_data
        
        # Sort by created_at (most recent first)
        all_feedback.sort(key=lambda x: x['created_at'], reverse=True)
        
        return Response({
            'profile_id': profile_id,
            'feedbacks': all_feedback,
            'average_rating': seeker.average_rating or 0.0,
            'feedback_count': len(all_feedback)
        })


class ApplicationDetailView(APIView):
    """View to retrieve application details including approval status and notes"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, pk):
        # Get the application
        application = get_object_or_404(Application, pk=pk)
        
        # Check if the user is authorized to view this application
        user = request.user
        if (hasattr(user, 'recruiter_profile') and application.job.recruiter != user.recruiter_profile) and \
           (hasattr(user, 'seeker_profile') and application.seeker != user.seeker_profile):
            return Response(
                {'detail': 'You are not authorized to view this application.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Return application details including approval status and notes
        data = {
            'id': application.id,
            'job': application.job.id,
            'job_title': application.job.title,
            'seeker': application.seeker.id,
            'seeker_name': f"{application.seeker.user.first_name} {application.seeker.user.last_name}",
            'status': application.status,
            'applied_at': application.applied_at,
            'selected_for_next_step': application.selected_for_next_step,
            'next_step_type': application.next_step_type,
            'next_step_status': application.next_step_status,
            'applicant_approved': application.applicant_approved,
            'recruiter_notes': application.recruiter_notes
        }
        
        return Response(data)


class ApplicationFeedbackView(APIView):
    """View to create and retrieve feedback for an application"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, pk):
        # Check if user is a recruiter
        if not hasattr(request.user, 'recruiter_profile'):
            return Response(
                {'detail': 'Only recruiters can provide feedback.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get the application
        application = get_object_or_404(Application, pk=pk)
        
        # Check if the recruiter owns the job associated with this application
        if application.job.recruiter != request.user.recruiter_profile:
            return Response(
                {'detail': 'You can only provide feedback for applications to your own jobs.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if the application has been approved (selected for next step)
        if not application.selected_for_next_step or application.next_step_status != 'APPROVED':
            return Response(
                {'detail': 'You can only provide feedback for approved applications.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create feedback data
        feedback_data = {
            'application': application.id,
            'profile': request.data.get('profile_id'),
            'rating': request.data.get('rating'),
            'comment': request.data.get('comment', '')
        }
        
        # Validate and save feedback
        serializer = FeedbackSerializer(data=feedback_data, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request, pk):
        # Get the application
        application = get_object_or_404(Application, pk=pk)
        
        # Check if the user is authorized to view this feedback
        user = request.user
        if (hasattr(user, 'recruiter_profile') and application.job.recruiter != user.recruiter_profile) and \
           (hasattr(user, 'seeker_profile') and application.seeker != user.seeker_profile):
            return Response(
                {'detail': 'You are not authorized to view this feedback.'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all feedbacks for this application
        feedbacks = Feedback.objects.filter(application=application)
        serializer = FeedbackSerializer(feedbacks, many=True)
        return Response(serializer.data)
