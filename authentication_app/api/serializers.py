from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

class RegistrationSerializer(serializers.ModelSerializer):
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
        if data['password'] != data['confirmed_password']:
            raise serializers.ValidationError(
                {'password': 'Passwords do not match.'}
            )
        return data

    def create(self, validated_data):
        email=validated_data['email'].lower()

        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data['password']
        )

        user.is_active = False
        user.save()
        return user