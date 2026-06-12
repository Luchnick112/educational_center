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

    def validate_telegram_username(self, value):
        normalized = (value or '').strip().lower()
        if not normalized:
            return None
        if not normalized.startswith('@'):
            normalized = f'@{normalized}'

        if not re.fullmatch(TELEGRAM_USERNAME_RE, normalized):
            raise serializers.ValidationError(
                'Invalid Telegram username. Use 5-32 characters: letters, numbers, underscore.'
            )

        legacy_without_at = normalized[1:]
        queryset = User.objects.filter(telegram_username__iexact=normalized) | User.objects.filter(
            telegram_username__iexact=legacy_without_at
        )
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('User with this Telegram username already exists.')

        return normalized

    def validate_email(self, value):
        email = (value or '').strip().lower()
        if not email:
            return ''

        queryset = User.objects.filter(email__iexact=email)
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.exists():
            raise serializers.ValidationError('User with this email already exists.')

        return email


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8, required=False, allow_blank=False)
    telegram_username = serializers.CharField(required=False, allow_blank=True, max_length=33)
    email = serializers.EmailField(required=False, allow_blank=True)

    class Meta:
        model = User
        fields = (
            'id',
            'password',
            'first_name',
            'last_name',
            'telegram_username',
            'email',
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
            return ''

        if not re.fullmatch(TELEGRAM_USERNAME_RE, normalized):
            raise serializers.ValidationError(
                'Invalid Telegram username. Use 5-32 characters: letters, numbers, underscore.'
            )

        return normalized

    def validate_email(self, value):
        return value.strip().lower()

    def _is_staff_request(self) -> bool:
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        return bool(user and user.is_authenticated and (user.is_staff or user.role == UserRole.ADMIN))

    def _existing_user_for_identity(self, *, telegram_username: str = '', email: str = '') -> User | None:
        matches = []

        if telegram_username:
            legacy_without_at = telegram_username[1:] if telegram_username.startswith('@') else telegram_username
            matches.extend(
                User.objects.filter(telegram_username__iexact=telegram_username)
                | User.objects.filter(telegram_username__iexact=legacy_without_at)
                | User.objects.filter(username__iexact=telegram_username)
                | User.objects.filter(username__iexact=legacy_without_at)
            )

        if email:
            matches.extend(User.objects.filter(email__iexact=email) | User.objects.filter(username__iexact=email))

        unique_matches = {user.pk: user for user in matches}
        if len(unique_matches) > 1:
            raise serializers.ValidationError(
                'Telegram username and email belong to different existing users.'
            )

        return next(iter(unique_matches.values()), None)

    def validate(self, attrs):
        role = attrs.get('role')
        password = attrs.get('password', '')
        telegram_username = attrs.get('telegram_username', '')
        email = attrs.get('email', '')

        if not telegram_username and not email:
            raise serializers.ValidationError('Telegram username or email is required.')

        staff_creating_user = self._is_staff_request()
        if not password and not staff_creating_user:
            raise serializers.ValidationError({'password': 'Password is required.'})

        existing_user = self._existing_user_for_identity(telegram_username=telegram_username, email=email)
        if existing_user:
            can_claim_user = (
                bool(password)
                and role == existing_user.role
                and not existing_user.has_usable_password()
            )
            if not can_claim_user:
                raise serializers.ValidationError('User with this Telegram username or email already exists.')

            attrs['_claim_user'] = existing_user

        return attrs

    @transaction.atomic
    def create(self, validated_data):
        password = validated_data.pop('password', '')
        claim_user = validated_data.pop('_claim_user', None)

        if claim_user:
            user = claim_user
            for field in ('first_name', 'last_name', 'telegram_username', 'email', 'phone'):
                value = validated_data.get(field)
                if value:
                    setattr(user, field, value)
            user.set_password(password)
            user.save()
        else:
            telegram_username = validated_data.get('telegram_username', '')
            email = validated_data.get('email', '')
            username = telegram_username or email

            # Keep a stable identifier for Django auth/admin.
            user = User(username=username, **validated_data)
            if password:
                user.set_password(password)
            else:
                user.set_unusable_password()
            user.save()

        if user.role == UserRole.STUDENT and not hasattr(user, 'student_profile'):
            StudentProfile.objects.create(user=user)
        elif user.role == UserRole.PARENT and not hasattr(user, 'parent_profile'):
            ParentProfile.objects.create(user=user)
        elif user.role == UserRole.TEACHER and not hasattr(user, 'teacher_profile'):
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
        # relationship is stored in the model for optional metadata, but the API only needs the link itself.
        fields = ('id', 'parent', 'student', 'is_primary', 'is_financial_contact')


class StudentProfileSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)
    parent_links = StudentParentRelationSerializer(many=True, read_only=True)

    def validate(self, attrs):
        if 'lesson_price' in attrs:
            request = self.context.get('request')
            user = getattr(request, 'user', None)
            is_admin = bool(user and user.is_authenticated and (user.is_staff or user.role == UserRole.ADMIN))
            if not is_admin:
                raise serializers.ValidationError({'lesson_price': 'Only admins can update lesson price.'})
        return attrs

    class Meta:
        model = StudentProfile
        fields = ('id', 'user', 'user_detail', 'lesson_price', 'notes', 'parent_links')


class ParentProfileSerializer(serializers.ModelSerializer):
    user_detail = serializers.SerializerMethodField()

    def get_user_detail(self, obj: ParentProfile):
        data = UserSerializer(obj.user).data
        relationship: list[dict] = []
        for rel in obj.student_links.all():
            # Defensive: data may contain orphaned links/profiles in dev DB.
            student = getattr(rel, 'student', None)
            if not student:
                continue
            try:
                student_user = student.user
            except User.DoesNotExist:
                continue
            relationship.append(
                {
                    'first_name': student_user.first_name,
                    'last_name': student_user.last_name,
                    'telegram_username': student_user.telegram_username,
                }
            )

        data['relationship'] = relationship
        return data

    class Meta:
        model = ParentProfile
        fields = ('id', 'user', 'user_detail', 'billing_notes')


class TeacherProfileSerializer(serializers.ModelSerializer):
    user_detail = UserSerializer(source='user', read_only=True)

    class Meta:
        model = TeacherProfile
        fields = ('id', 'user', 'user_detail', 'hourly_rate', 'bio')
