import re

from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.tokens import RefreshToken

from .models import ParentProfile, StudentParentRelation, StudentProfile, TeacherProfile, TelegramLinkToken, User, UserRole

DATE_INPUT_STYLE = {'input_type': 'text', 'placeholder': 'YYYY-MM-DD'}
# Accept both "username" and "@username" at input time.
TELEGRAM_USERNAME_RE = r'^@?[A-Za-z0-9_]{5,32}$'


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'id',
            'first_name',
            'last_name',
            'telegram_username',
            'telegram_chat_id',
            'telegram_user_id',
            'email',
            'role',
            'phone',
            'is_active',
        )


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    telegram_username = serializers.CharField(required=True, max_length=33)

    class Meta:
        model = User
        fields = (
            'id',
            'password',
            'first_name',
            'last_name',
            'telegram_username',
            'role',
            'phone',
        )
        read_only_fields = ('id',)

    def validate_telegram_username(self, value):
        normalized = value.strip()
        normalized = normalized.lower()
        if normalized and not normalized.startswith('@'):
            normalized = f'@{normalized}'

        if not normalized:
            raise serializers.ValidationError('Telegram username is required.')

        if not re.fullmatch(TELEGRAM_USERNAME_RE, normalized):
            raise serializers.ValidationError(
                'Invalid Telegram username. Use 5-32 characters: letters, numbers, underscore.'
            )

        legacy_without_at = normalized[1:] if normalized.startswith('@') else normalized

        if User.objects.filter(telegram_username__iexact=normalized).exists() or User.objects.filter(
            telegram_username__iexact=legacy_without_at
        ).exists():
            raise serializers.ValidationError('User with this Telegram username already exists.')

        # Ensure we can also safely use it as Django "username" for admin/browsable auth if needed.
        if User.objects.filter(username__iexact=normalized).exists() or User.objects.filter(
            username__iexact=legacy_without_at
        ).exists():
            raise serializers.ValidationError('User with this username already exists.')

        return normalized

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop('password')
        telegram_username = validated_data['telegram_username']

        # Keep a stable identifier for Django auth/admin. We enforce uniqueness in validate_telegram_username.
        user = User(username=telegram_username, **validated_data)
        user.set_password(password)
        user.save()

        if user.role == UserRole.STUDENT:
            StudentProfile.objects.create(user=user)
        elif user.role == UserRole.PARENT:
            ParentProfile.objects.create(user=user)
        elif user.role == UserRole.TEACHER:
            TeacherProfile.objects.create(user=user)

        return user


class TelegramUsernameTokenObtainPairSerializer(serializers.Serializer):
    telegram_username = serializers.CharField(required=False, allow_blank=True)
    # Backwards compatibility: allow existing users to authenticate by email too.
    email = serializers.EmailField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)

    default_error_messages = {
        'invalid_credentials': 'No active account found with the given credentials.',
    }

    def validate(self, attrs):
        telegram_username = (attrs.get('telegram_username') or '').strip()
        email = (attrs.get('email') or '').strip().lower()
        password = attrs['password']

        user = None

        if telegram_username:
            telegram_username = telegram_username.lower()
            if telegram_username and not telegram_username.startswith('@'):
                telegram_username_with_at = f'@{telegram_username}'
            else:
                telegram_username_with_at = telegram_username
            telegram_username_without_at = telegram_username_with_at[1:] if telegram_username_with_at.startswith('@') else telegram_username_with_at
            user = (
                User.objects.filter(telegram_username__iexact=telegram_username_with_at).first()
                or User.objects.filter(telegram_username__iexact=telegram_username_without_at).first()
                or User.objects.filter(username__iexact=telegram_username_with_at).first()
                or User.objects.filter(username__iexact=telegram_username_without_at).first()
            )
        elif email:
            user = User.objects.filter(email__iexact=email).first()
        else:
            self.fail('invalid_credentials')

        if not user:
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


class TelegramLinkTokenResponseSerializer(serializers.Serializer):
    token = serializers.CharField()
    expires_at = serializers.DateTimeField()
    deep_link_url = serializers.URLField(allow_blank=True)


class TelegramWebhookSerializer(serializers.Serializer):
    update_id = serializers.IntegerField(required=False)
    message = serializers.DictField(required=False)
    edited_message = serializers.DictField(required=False)

    def validate(self, attrs):
        if not attrs.get('message') and not attrs.get('edited_message'):
            # Telegram sends many update types; we accept them but do nothing.
            return attrs
        return attrs


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
