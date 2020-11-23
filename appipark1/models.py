from django.db import models


class Tag(models.Model):
    name = models.CharField(max_length=40, null=False)
    comment = models.CharField(max_length=400, default='')
    isdelete = models.BooleanField(default=False)


class Equipment(models.Model):
    name = models.CharField(max_length=40, null=False)
    type = models.CharField(max_length=40, null=False)
    location = models.CharField(max_length=400, default='')
    state = models.CharField(max_length=10, default='')
    isdelete = models.BooleanField(default=False)


class Blacklist(models.Model):
    photo = models.CharField(max_length=100, null=False)
    comment = models.CharField(max_length=400, default='')
    tag = models.CharField(max_length=40, null=False)
    face_id = models.CharField(max_length=32, null=False)
    face_token = models.CharField(max_length=32, null=False)
    isdelete = models.BooleanField(default=False)


class Record(models.Model):
    img = models.CharField(max_length=100, null=False)
    photo = models.CharField(max_length=100, null=False)
    tag = models.CharField(max_length=40, null=False)
    face_id = models.CharField(max_length=32, null=False)
    score = models.FloatField(null=False)
    record_time = models.DateTimeField(null=False)
    equipment = models.CharField(max_length=40, null=False)
    isdelete = models.BooleanField(default=False)


class Task(models.Model):
    pass
