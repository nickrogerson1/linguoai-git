from django.apps import AppConfig


# Changes the name in the admin from Members to Databases
class AuthConfig(AppConfig):
    name = 'members'
    verbose_name = 'Databases'
