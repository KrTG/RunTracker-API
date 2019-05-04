from datetime import datetime

from django.core import exceptions
from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core import validators

from .helpers import format_tempo, format_run_time

class UserManager(BaseUserManager):
    """Define a model manager for User model with no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Create and save a User with the given email and password."""
        if not email:
            raise ValueError('The given email must be set')
        if len(password) < 8:
            raise exceptions.ValidationError("Password too short(min 8 characters).")
        
        email = self.normalize_email(email)        
        try:
            user = self.model(email=email, **extra_fields)                    
            user.set_password(password)
            user.full_clean()
            user.save(using=self._db)   
        except exceptions.ValidationError as e:
            raise e        
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular User with the given email and password."""
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        try:
            return self._create_user(email, password, **extra_fields)
        except Exception:
            raise

    def create_superuser(self, email, password, **extra_fields):
        """Create and save a SuperUser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField('email address', unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    avatar = models.TextField(blank=True, default='')
    weight = models.PositiveIntegerField(default=70)    

    objects = UserManager()

    def serialize(self):
        return {
            'id': self.pk,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,      
            'weight': self.weight,
            'avatar': self.avatar,
        }

class Run(models.Model):
    ALL = 'all'
    FRIENDS = 'friends'
    ONLY_ME = 'only_me'
    PRIVACY_CHOICES = (
        (ALL, 'Public'),
        (FRIENDS, 'Friends only'),
        (ONLY_ME, 'Only me'),
    )

    creator = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        default=None,
        related_name="+"
    )

    start_datetime = models.DateTimeField()
    distance = models.PositiveIntegerField()
    privacy_level = models.CharField(
        max_length=10,
        choices=PRIVACY_CHOICES,
    )
    max_runners = models.PositiveIntegerField()
    runners = models.ManyToManyField(User, through='Participation')
    finished = models.BooleanField(default=False)    


    def serialize(self):
        return {
            'id': self.pk,
            'start': self.start_datetime.strftime("%Y-%m-%dT%H:%M"),
            'distance': self.distance,
            'privacy': self.privacy_level,
            'max_runners': self.max_runners,
            'finished': self.finished,
        }

    def get_likes(self):        
        return Like.objects.filter(run=self).count()

    def num_watching(self):        
        return Watching.objects.filter(run=self).count()

class Comment(models.Model):
    run = models.ForeignKey(
        Run,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    text = models.CharField(max_length=1500)
    datetime = models.DateTimeField(auto_now_add=True)

    def serialize(self):
        return {
            'text': self.text,
            'created': self.datetime.strftime("%Y-%m-%dT%H:%M"),
        }

class Like(models.Model):
    class Meta:
        unique_together = ("run", "user")

    run = models.ForeignKey(
        Run,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
    

class Watching(models.Model):
    class Meta:
        unique_together = ("run", "user")

    run = models.ForeignKey(
        Run,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )
        

class Participation(models.Model):
    
    class Meta:
        unique_together = ("run", "user")

    run = models.ForeignKey(
        Run,
        on_delete=models.CASCADE
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE
    )

    position = models.PositiveIntegerField(null=True, blank=True, default=None)
    time = models.DurationField(null=True, blank=True, default=None)
    avg_tempo = models.DurationField(null=True, blank=True, default=None)
    max_tempo = models.DurationField(null=True, blank=True, default=None)
    min_tempo = models.DurationField(null=True, blank=True, default=None)    

    def serialize(self):
        return {
            'position': self.position,
            'time': format_run_time(self.time),
            'avg_tempo': format_tempo(self.avg_tempo),
            'max_tempo': format_tempo(self.max_tempo),
            'min_tempo': format_tempo(self.min_tempo),
        }

    def splits(self):
        return Split.objects.filter(participation=self)

class Split(models.Model):
    participation = models.ForeignKey(
        Participation,
        on_delete=models.CASCADE
    )
    distance = models.PositiveIntegerField()
    timestamp = models.DateTimeField()

    def serialize(self):
        return {
            'distance': self.distance,
            'timestamp': self.timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
        }

    





