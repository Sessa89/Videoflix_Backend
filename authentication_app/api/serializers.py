"""
Serializers for user-facing authentication endpoints.

Currently includes:
- `RegistrationSerializer` for creating inactive users from an email+password
  pair, enforcing email uniqueness and simple password confirmation.
"""

from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

class RegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Validates that:
    - The `email` is unique among all users.
    - `password` and `confirmed_password` match.
    """

    email = serializers.EmailField(
        validators=[
            UniqueValidator(
                queryset=User.objects.all(),
                message="This email is already taken."
            )
        ]
    )
    password = serializers.CharField(write_only=True, min_length=8)
    confirmed_password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['email', 'password', 'confirmed_password']

    def validate(self, data):
        """
        Ensure both password fields match.

        Returns:
            The validated data.

        Raises:
            serializers.ValidationError: if passwords do not match.
        """

        if data['password'] != data['confirmed_password']:
            raise serializers.ValidationError(
                {'password': 'Passwords do not match.'}
            )
        return data

    def create(self, validated_data):
        """
        Create a new inactive user.

        Behavior:
            - Uses the email as both `username` and `email`.
            - Sets `is_active=False` (user must activate via email token).
        """

        email=validated_data['email'].lower()

        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data['password']
        )

        user.is_active = False
        user.save()
        return user