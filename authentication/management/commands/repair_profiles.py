from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from authentication.models import RecruiterProfile, JobSeekerProfile

class Command(BaseCommand):
    help = 'Ensure every user has an associated recruiter or job seeker profile.'

    def handle(self, *args, **options):
        User = get_user_model()
        created_recruiters = 0
        created_seekers = 0
        for user in User.objects.all():
            if not hasattr(user, 'recruiter_profile') and not hasattr(user, 'seeker_profile'):
                # Decide default profile type for orphaned users (default: job seeker)
                JobSeekerProfile.objects.create(user=user, full_name=user.email)
                created_seekers += 1
            # Optionally, log users with both profiles or print summary
        self.stdout.write(self.style.SUCCESS(f'Created {created_seekers} job seeker profiles for users without any profile.'))
