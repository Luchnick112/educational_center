from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("users", "0002_user_telegram_username"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="telegram_chat_id",
            field=models.BigIntegerField(blank=True, null=True, unique=True),
        ),
        migrations.AddField(
            model_name="user",
            name="telegram_user_id",
            field=models.BigIntegerField(blank=True, null=True, unique=True),
        ),
        migrations.CreateModel(
            name="TelegramLinkToken",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("token", models.CharField(max_length=64, unique=True)),
                ("expires_at", models.DateTimeField()),
                ("used_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("linked_chat_id", models.BigIntegerField(blank=True, null=True)),
                ("linked_user_id", models.BigIntegerField(blank=True, null=True)),
                ("linked_username", models.CharField(blank=True, max_length=64)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="telegram_link_tokens",
                        to="users.user",
                    ),
                ),
            ],
            options={
                "indexes": [
                    models.Index(fields=["token"], name="users_teleg_token_9d2b2b_idx"),
                    models.Index(fields=["expires_at"], name="users_teleg_expires_4f1e2e_idx"),
                ],
            },
        ),
    ]

