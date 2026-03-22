from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ParentProfile, StudentParentRelation, StudentProfile, TeacherProfile, User, UserRole

DATE_INPUT_STYLE = {'input_type': 'text', 'placeholder': 'YYYY-MM-DD'}


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'role', 'phone', 'is_active')


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = (
            'id',
            'password',
            'first_name',
            'last_name',
            'email',
            'role',
            'phone',
        )
        read_only_fields = ('id',)

    def validate_email(self, value):
        normalized = value.strip().lower()
        if User.objects.filter(email__iexact=normalized).exists():
            raise serializers.ValidationError('User with this email already exists.')
        return normalized

    def _build_username(self, email):
        candidate = email
        suffix = 1
        while User.objects.filter(username=candidate).exists():
            candidate = f'{email}_{suffix}'
            suffix += 1
        return candidate

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop('password')
        email = validated_data['email']
        user = User(username=self._build_username(email), **validated_data)
        user.set_password(password)
        user.save()

        if user.role == UserRole.STUDENT:
            StudentProfile.objects.create(user=user)
        elif user.role == UserRole.PARENT:
            ParentProfile.objects.create(user=user)
        elif user.role == UserRole.TEACHER:
            TeacherProfile.objects.create(user=user)

        return user


class EmailTokenObtainPairSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    default_error_messages = {
        'invalid_credentials': 'No active account found with the given credentials.',
    }

    def validate(self, attrs):
        email = attrs['email'].strip().lower()
        password = attrs['password']

        try:
            user = User.objects.get(email__iexact=email)
        except User.DoesNotExist:
            self.fail('invalid_credentials')

        if not user.check_password(password) or not user.is_active:
            self.fail('invalid_credentials')

        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }


class EmailTokenRefreshSerializer(TokenRefreshSerializer):
    pass


class StudentParentRelationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentParentRelation
        fields = ('id', 'parent', 'student', 'relationship', 'is_primary', 'is_financial_contact')


class StudentProfileSerializer(serializers.ModelSerializer):
    date_of_birth = serializers.DateField(required=False, allow_null=True, style=DATE_INPUT_STYLE)
    user_detail = UserSerializer(source='user', read_only=True)
    parent_links = StudentParentRelationSerializer(many=True, read_only=True)

    class Meta:
        model = StudentProfile
        fields = ('id', 'user', 'user_detail', 'date_of_birth', 'grade', 'notes', 'parent_links')


class ParentProfileSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = ParentProfile
        fields = ('id', 'user', 'user_detail', 'billing_notes')


class TeacherProfileSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = TeacherProfile
        fields = ('id', 'user', 'user_detail', 'hourly_rate', 'bio')
