from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from .models import User, Leave, Employee

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Add custom claims
        token['email'] = user.email
        token['role'] = user.role
        return token

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'role')

class LeaveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Leave
        fields = ('id', 'start_date', 'end_date', 'leave_type', 'status')
        read_only_fields = ('status',)

    def create(self, validated_data):
        # The employee will be assigned in the view to ensure it matches request.user
        return super().create(validated_data)
