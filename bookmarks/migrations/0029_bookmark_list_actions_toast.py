# Generated by Django 5.0.2 on 2024-03-29 21:25

from django.db import migrations
from django.contrib.auth import get_user_model

from bookmarks.models import Toast

User = get_user_model()


def forwards(apps, schema_editor):

    for user in User.objects.all():
        toast = Toast(
            key="bookmark_list_actions_hint",
            message="This version adds a new link to each bookmark to view details in a dialog. If you feel there is too much clutter you can now hide individual links in the settings.",
            owner=user,
        )
        toast.save()


def reverse(apps, schema_editor):
    Toast.objects.filter(key="bookmark_list_actions_hint").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("bookmarks", "0028_userprofile_display_archive_bookmark_action_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, reverse),
    ]
