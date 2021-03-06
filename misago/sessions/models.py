from django.db import models
       
class Session(models.Model):
    id = models.CharField(max_length=42, primary_key=True)
    data = models.TextField(db_column="session_data")
    user = models.ForeignKey('users.User', related_name='+', null=True, on_delete=models.SET_NULL)
    crawler = models.CharField(max_length=255, blank=True, null=True)
    ip = models.GenericIPAddressField()
    agent = models.CharField(max_length=255)
    start = models.DateTimeField()
    last = models.DateTimeField()
    staff = models.BooleanField(default=False)
    admin = models.BooleanField(default=False)
    matched = models.BooleanField(default=False)
    hidden = models.BooleanField(default=False)

class Token(models.Model):
    id = models.CharField(max_length=42, primary_key=True)
    user = models.ForeignKey('users.User', related_name='+')
    created = models.DateTimeField()
    accessed = models.DateTimeField()
    hidden = models.BooleanField(default=False)