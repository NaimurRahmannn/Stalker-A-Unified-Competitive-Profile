from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    email = models.EmailField("email address", unique=True)
    full_name = models.CharField(max_length=255, blank=True)
    avatar = models.URLField(max_length=500, blank=True)
    bio = models.TextField(blank=True)
    country = models.CharField(max_length=100, blank=True)
    institution = models.CharField(max_length=255, blank=True)
    github_url = models.URLField(max_length=500, blank=True)
    linkedin_url = models.URLField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.username
