from django.db import models

class Account(models.Model):
    id_account = models.AutoField(primary_key=True)
    status = models.IntegerField()
    user = models.CharField(max_length=45)
    password = models.CharField(max_length=100)
    subscription = models.CharField(max_length=45)
    
    email = models.EmailField(max_length=100, null=True, blank=True)
    google_id = models.CharField(max_length=255, null=True, blank=True)
    facebook_id = models.CharField(max_length=255, null=True, blank=True)

    subscription_expires_at = models.DateTimeField(null=True, blank=True)
    subscription_started_at = models.DateTimeField(null=True, blank=True)
    observations_admin = models.TextField(null=True, blank=True)  

    class Meta:
        managed = False
        db_table = 'account'  # nombre exacto de tu tabla en MySQL

    def __str__(self):
        return self.user

    @property
    def is_authenticated(self):
        """Compatibilidad con el sistema de autenticación de Django"""
        return True
