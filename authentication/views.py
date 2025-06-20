from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from .models import User, RecruiterProfile, JobSeekerProfile, SeekerFeedback
from .serializers import RecruiterProfileSerializer, JobSeekerProfileSerializer, SeekerFeedbackSerializer

# Create your views here.

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import RecruiterProfile, JobSeekerProfile

class MarkRecruiterProfileUpdatedView(APIView):
    """
    POST /auth/recruiter/mark-profile-updated/
    Marks the authenticated recruiter's profile as updated (profile_updated=True).
    """
    permission_classes = [IsAuthenticated]
    def post(self, request):
        if hasattr(request.user, 'recruiter_profile'):
            profile = request.user.recruiter_profile
            profile.profile_updated = True
            profile.save()
            return Response({'profile_updated': True})
        return Response({'error': 'No recruiter profile'}, status=400)

class MarkJobSeekerProfileUpdatedView(APIView):
    """
    POST /auth/seeker/mark-profile-updated/
    Marks the authenticated job seeker's profile as updated (profile_updated=True).
    """
    permission_classes = [IsAuthenticated]
    def post(self, request):
        if hasattr(request.user, 'seeker_profile'):
            profile = request.user.seeker_profile
            profile.profile_updated = True
            profile.save()
            return Response({'profile_updated': True})
        return Response({'error': 'No job seeker profile'}, status=400)

class RecruiterSignupView(APIView):
    def post(self, request):
        data = request.data
        email = data.get('email')
        password = data.get('password')
        company_name = data.get('company_name')
        if not all([email, password, company_name]):
            return Response({'error': 'email, password, and company_name are required'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=email, email=email, password=password)
        recruiter = RecruiterProfile.objects.create(user=user, company_name=company_name)
        return Response({'id': user.id, 'email': user.email}, status=status.HTTP_201_CREATED)

class JobSeekerSignupView(APIView):
    def post(self, request):
        data = request.data
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        if not all([email, password, full_name]):
            return Response({'error': 'email, password, and full_name are required'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=email, email=email, password=password)
        seeker = JobSeekerProfile.objects.create(user=user, full_name=full_name)
        return Response({'id': user.id, 'email': user.email}, status=status.HTTP_201_CREATED)

class RecruiterProfileUpdateView(generics.UpdateAPIView):
    queryset = RecruiterProfile.objects.all()
    serializer_class = RecruiterProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_object(self):
        user = self.request.user
        if hasattr(user, 'recruiter_profile'):
            return user.recruiter_profile
        raise NotFound('Recruiter profile does not exist for this user.')

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        # Mark profile_updated True on any update
        profile = self.get_object()
        if not profile.profile_updated:
            profile.profile_updated = True
            profile.save(update_fields=["profile_updated"])
        return response

class JobSeekerProfileUpdateView(generics.UpdateAPIView):
    queryset = JobSeekerProfile.objects.all()
    serializer_class = JobSeekerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_object(self):
        user = self.request.user
        if hasattr(user, 'seeker_profile'):
            return user.seeker_profile
        raise NotFound('Job seeker profile does not exist for this user.')

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        # Mark profile_updated True on any update
        profile = self.get_object()
        if not profile.profile_updated:
            profile.profile_updated = True
            profile.save(update_fields=["profile_updated"])
        return response

class SeekerFeedbackCreateView(generics.CreateAPIView):
    serializer_class = SeekerFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        recruiter = self.request.user.recruiter_profile
        seeker_id = self.request.data.get('seeker')
        seeker = JobSeekerProfile.objects.get(id=seeker_id)
        serializer.save(recruiter=recruiter, seeker=seeker)

class SeekerFeedbackListView(generics.ListAPIView):
    serializer_class = SeekerFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        seeker_id = self.kwargs['seeker_id']
        return SeekerFeedback.objects.filter(seeker_id=seeker_id).order_by('-created_at')

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        if not user.check_password(password):
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        # Determine user type by profile existence
        if hasattr(user, 'recruiter_profile'):
            user_type = 'recruiter'
        elif hasattr(user, 'seeker_profile'):
            user_type = 'seeker'
        else:
            return Response({'error': 'User profile not found'}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'id': user.id,
            'email': user.email,
            'user_type': user_type
        }, status=status.HTTP_200_OK)

class LogoutView(APIView):
    """
    POST /auth/logout/
    Blacklists the refresh token (if provided) and logs out the user.
    """
    permission_classes = [IsAuthenticated]
    def post(self, request):
        from rest_framework_simplejwt.tokens import RefreshToken, TokenError
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token required.'}, status=400)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response({'error': 'Invalid or expired token.'}, status=400)
        return Response({'detail': 'Logout successful.'}, status=200)
