from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group
from .models import Role, GLOBAL_ROLE_SLUGS

@receiver(post_migrate)
def ensure_roles_and_groups(sender, **kwargs):
    for slug in GLOBAL_ROLE_SLUGS:
        Role.objects.get_or_create(slug=slug, defaults={"name": slug.replace("_", " ").title()})
        Group.objects.get_or_create(name=slug)