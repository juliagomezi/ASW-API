import math
from datetime import datetime
from django.utils import timezone
from django.db import models

from django.core.exceptions import ValidationError
# Create your models here.
from django.forms import ModelForm, Textarea, TextInput, URLInput
from django.contrib.auth.models import User
from django import forms


class Contribution(models.Model):
    URL = 'url'
    ASK = 'ask'
    CHOICES = [
        (URL, 'url'),
        (ASK, 'ask')
    ]
    type = models.CharField(
        max_length=3,
        choices=CHOICES,
        default='url')
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=200)
    url = models.CharField(max_length=200, blank=True)
    text = models.CharField(max_length=200, blank=True)
    date = models.DateTimeField(default=datetime.now, blank=True)
    points = models.IntegerField(default=1)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True)

    def __str__(self):
        return self.title

    def get_date(self):
        time = self.date
        now = timezone.now()
        if type(time) is int:
            diff = now - datetime.fromtimestamp(time)
        elif isinstance(time, datetime):
            diff = now - time
        elif not time:
            diff = now - now
        else:
            raise ValueError('invalid date %s of type %s' % (time, type(time)))
        second_diff = diff.seconds
        day_diff = diff.days
        return get_date_text(day_diff, second_diff)


class Comment(models.Model):
    id = models.AutoField(primary_key=True)
    level = models.IntegerField(default=0)
    author = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    date = models.DateTimeField(default=datetime.now, blank=True)
    contribution = models.ForeignKey(Contribution, on_delete=models.CASCADE, related_name="comments")
    father = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.text

    def get_date(self):
        time = self.date
        now = timezone.now()
        if type(time) is int:
            diff = now - datetime.fromtimestamp(time)
        elif isinstance(time, datetime):
            diff = now - time
        elif not time:
            diff = now - now
        else:
            raise ValueError('invalid date %s of type %s' % (time, type(time)))
        second_diff = diff.seconds
        day_diff = diff.days
        return get_date_text(day_diff, second_diff)


class ContributionVote(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    contribution = models.ForeignKey(Contribution, on_delete=models.CASCADE)


class CommentVote(models.Model):
    user = models.ForeignKey(User, null=True, on_delete=models.SET_NULL)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)


class SubmitForm(ModelForm):
    class Meta:
        model = Contribution
        fields = ['url', 'title', 'text']
        widgets = {
            'url': URLInput(attrs={'size': 50}),
            'title': TextInput(attrs={'size': 50, 'required': False}),
            'text': Textarea(attrs={'cols': 49, 'rows': 4, 'required': False}),
        }

    def clean(self):
        super(SubmitForm, self).clean()
        cd = self.cleaned_data

        url = cd.get('url')
        text = cd.get('text')

        if not url and not text:
            raise ValidationError("FORMINCOMPLET")

        return cd


class DetailForm(forms.Form):
    about = forms.CharField(required=False, widget=forms.Textarea(attrs={'cols': '60', 'rows': '5'}))
    show_dead = forms.BooleanField(required=False)
    no_procrast = forms.BooleanField(required=False)
    max_visit = forms.IntegerField(min_value=0)
    min_away = forms.IntegerField(min_value=0)
    delay = forms.IntegerField(min_value=0)


class UserDetail(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_detail")
    karma = models.IntegerField(default=0)
    about = models.CharField(max_length=200, default="", blank=True)
    created = models.DateTimeField(default=datetime.now)
    show_dead = models.BooleanField(default=False)
    no_procrast = models.BooleanField(default=False)
    max_visit = models.PositiveIntegerField(default=20)
    min_away = models.PositiveIntegerField(default=180)
    delay = models.PositiveIntegerField(default=0)

    def set_data(self, detail_form: DetailForm):
        self.about = detail_form.cleaned_data['about']
        self.show_dead = detail_form.cleaned_data['show_dead']
        self.no_procrast = detail_form.cleaned_data['no_procrast']
        self.max_visit = detail_form.cleaned_data['max_visit']
        self.min_away = detail_form.cleaned_data['min_away']
        self.delay = detail_form.cleaned_data['delay']

    def get_date(self):
        time = self.created
        now = timezone.now()
        if type(time) is int:
            diff = now - datetime.fromtimestamp(time)
        elif isinstance(time, datetime):
            diff = now - time
        elif not time:
            diff = now - now
        else:
            raise ValueError('invalid date %s of type %s' % (time, type(time)))
        second_diff = diff.seconds
        day_diff = diff.days
        return get_date_text(day_diff, second_diff)


def get_date_text(day_diff, second_diff):
    if day_diff < 0:
        return ''

    if day_diff == 0:
        if second_diff < 10:
            return "just now"
        if second_diff < 60:
            return str(math.trunc(second_diff)) + " seconds ago"
        if second_diff < 120:
            return "a minute ago"
        if second_diff < 3600:
            return str(math.trunc(second_diff / 60)) + " minutes ago"
        if second_diff < 7200:
            return "1 hour ago"
        if second_diff < 86400:
            return str(math.trunc(second_diff / 3600)) + " hours ago"
    if day_diff == 1:
        return "1 day ago"
    if day_diff < 7:
        return str(day_diff) + " days ago"
    if day_diff < 31:
        return str(math.trunc(day_diff / 7)) + " weeks ago"
    if day_diff < 365:
        return str(math.trunc(day_diff / 30)) + " months ago"
    return str(math.trunc(day_diff / 365)) + " years ago"


class UserDTO(models.Model):
    username = models.CharField(max_length=200)
    email = models.CharField(max_length=200)
    karma = models.IntegerField(default=0)
    about = models.CharField(max_length=200, default="", blank=True)
    created = models.DateTimeField(default=datetime.now)

    def __init__(self, username, email, karma, about, created, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username = username
        self.email = email
        self.karma = karma
        self.about = about
        self.created = created


class ContributionCreationDTO(models.Model):
    title = models.CharField(max_length=200)
    url = models.CharField(max_length=200, blank=True)
    text = models.CharField(max_length=200, blank=True)

    def __init__(self, title, url, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = title
        self.url = url
        self.text = text


class ContributionDTO(models.Model):
    URL = 'url'
    ASK = 'ask'
    CHOICES = [
        (URL, 'url'),
        (ASK, 'ask')
    ]
    type = models.CharField(
        max_length=3,
        choices=CHOICES,
        default='url')
    id = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=200)
    url = models.CharField(max_length=200, blank=True)
    text = models.CharField(max_length=200, blank=True)
    date = models.DateTimeField(default=datetime.now, blank=True)
    points = models.IntegerField(default=1)
    author = models.CharField(max_length=200)

    def __init__(self, id, type, points, author, url, text, date, title, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.type = type
        self.id = id
        self.url = url
        self.text = text
        self.date = date
        self.points = points
        self.author = author
        self.title = title




class CommentDTO(models.Model):
    id = models.IntegerField(primary_key=True)
    level = models.IntegerField(default=0)
    author = models.CharField(max_length=200)
    text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    date = models.DateTimeField(default=datetime.now, blank=True)
    contributionId = models.IntegerField(default=0)
    fatherId = models.IntegerField(default=0)
    #replies = CommentDTO[]

    def __init__(self, id, level, author, text, votes, date, contributionId, fatherId, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.id = id
        self.level = level
        self.author = author
        self.text = text
        self.votes = votes
        self.date = date
        self.contributionId = contributionId
        self.fatherId = fatherId


class CommentCreationDTO(models.Model):
    text = models.CharField(max_length=200)

    def __init__(self, text, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.text = text