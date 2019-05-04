from django.core.management.base import BaseCommand
from REST.models import User

class Command(BaseCommand):

    def handle(self, *args, **options):
        if not User.objects.filter(email="admin@admin.pl").exists():
            User.objects.create_superuser("admin@admin.pl", "22abc22admin")