from rest_framework import serializers
from apps.main.models import School


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['id', 'name', 'slug', 'domain', 'description', 'short_description', 
                 'founded_year', 'capacity', 'student_count', 'teacher_count', 
                 'direction_count', 'class_count', 'email', 'phone_number', 
                 'address', 'latitude', 'longitude', 'instagram_link', 
                 'telegram_link', 'facebook_link', 'youtube_link', 'logo'] 