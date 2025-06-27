from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.hashers import check_password
from rest_framework import generics, permissions
from rest_framework.exceptions import NotFound
from .models import User, RecruiterProfile, JobSeekerProfile
from core.models import FeedbackRating
from .serializers import RecruiterProfileSerializer, JobSeekerProfileSerializer, FeedbackRatingSerializer
from rest_framework.permissions import IsAuthenticated

# Create your views here.

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

class RecruiterProfileView(generics.RetrieveAPIView):
    """
    GET /auth/recruiter/profile/
    Retrieves the authenticated recruiter's profile.
    """
    serializer_class = RecruiterProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        if hasattr(user, 'recruiter_profile'):
            return user.recruiter_profile
        raise NotFound('Recruiter profile does not exist for this user.')

class RecruiterProfileUpdateView(generics.UpdateAPIView):
    """
    PUT/PATCH /auth/recruiter/profile/update/
    Updates the authenticated recruiter's profile.
    """
    queryset = RecruiterProfile.objects.all()
    serializer_class = RecruiterProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

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

class JobSeekerProfileView(generics.RetrieveAPIView):
    """
    GET /auth/seeker/profile/
    Retrieves the authenticated job seeker's profile.
    """
    serializer_class = JobSeekerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        if hasattr(user, 'seeker_profile'):
            return user.seeker_profile
        raise NotFound('Job seeker profile does not exist for this user.')

class JobSeekerProfileUpdateView(generics.UpdateAPIView):
    """
    PUT/PATCH /auth/seeker/profile/update/
    Updates the authenticated job seeker's profile.
    """
    queryset = JobSeekerProfile.objects.all()
    serializer_class = JobSeekerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        user = self.request.user
        if hasattr(user, 'seeker_profile'):
            return user.seeker_profile
        raise NotFound('Job seeker profile does not exist for this user.')

    def update(self, request, *args, **kwargs):
        response = super().update(request, *args, **kwargs)
        # Get the updated profile
        profile = self.get_object()
        
        # Set profile_updated to True if education or skills are not empty
        should_mark_updated = False
        
        # Check if education or skills are populated
        if profile.education and len(profile.education) > 0:
            should_mark_updated = True
        elif profile.skills and len(profile.skills) > 0:
            should_mark_updated = True
        
        # Always update the flag if conditions are met
        if should_mark_updated:
            profile.profile_updated = True
            profile.save(update_fields=["profile_updated"])
            
        return response

class SeekerFeedbackCreateView(generics.CreateAPIView):
    serializer_class = FeedbackRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        user = self.request.user
        if not hasattr(user, 'recruiter_profile'):
            raise NotFound('Only recruiters can provide feedback.')
        
        # Get the profile ID from the request data
        profile_id = self.request.data.get('profile')
        if not profile_id:
            raise serializers.ValidationError({'profile': 'Profile ID is required'})
            
        try:
            profile = JobSeekerProfile.objects.get(id=profile_id)
            serializer.save(
                recruiter=user.recruiter_profile,
                profile=profile,
                feedback_type='PROFILE',
                application=None
            )
        except JobSeekerProfile.DoesNotExist:
            raise NotFound(f'Job seeker profile with ID {profile_id} not found')

class SeekerFeedbackListView(generics.ListAPIView):
    serializer_class = FeedbackRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        seeker_id = self.kwargs.get('seeker_id')
        return FeedbackRating.objects.filter(profile_id=seeker_id, feedback_type='PROFILE').order_by('-created_at')

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
        from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
        
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            # Allow logout even without refresh token
            return Response({'detail': 'Logged out without token blacklisting.'}, status=200)
        
        try:
            # Try the newer method first
            token = RefreshToken(refresh_token)
            try:
                # For newer versions of djangorestframework-simplejwt
                token.blacklist()
            except AttributeError:
                # For older versions, manually blacklist the token
                try:
                    jti = token.get('jti')
                    if jti:
                        # Get or create the outstanding token
                        outstanding_token, _ = OutstandingToken.objects.get_or_create(
                            jti=jti,
                            user=request.user,
                            token=refresh_token
                        )
                        # Blacklist the token
                        BlacklistedToken.objects.get_or_create(token=outstanding_token)
                except Exception as inner_e:
                    # Log the error but still allow logout
                    print(f"Error blacklisting token: {str(inner_e)}")
                
            return Response({'detail': 'Logout successful.'}, status=200)
        except TokenError:
            # Still allow logout even with invalid token
            return Response({'detail': 'Logged out. Token was invalid or expired.'}, status=200)
        except Exception as e:
            print(f"Logout error: {str(e)}")
            # Still allow logout even if blacklisting fails
            return Response({'detail': 'Logged out, but token blacklisting failed.'}, status=200)

class JobSeekerProfilePictureView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if not hasattr(request.user, 'seeker_profile'):
            return Response({'detail': 'Not a job seeker.'}, status=status.HTTP_403_FORBIDDEN)
        
        profile = request.user.seeker_profile
        profile.profile_picture = request.FILES.get('profile_picture')
        profile.save()
        
        serializer = JobSeekerProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)

class JobSeekerResumeView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if not hasattr(request.user, 'seeker_profile'):
            return Response({'detail': 'Not a job seeker.'}, status=status.HTTP_403_FORBIDDEN)
        
        profile = request.user.seeker_profile
        profile.resume = request.FILES.get('resume')
        profile.save()
        
        serializer = JobSeekerProfileSerializer(profile)
        return Response(serializer.data, status=status.HTTP_200_OK)
