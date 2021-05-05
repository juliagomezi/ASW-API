from django.contrib import admin

# Register your models here.

from .models import Contribution, Comment, UserDetail, CommentVote, ContributionVote

admin.site.register(Contribution)
admin.site.register(Comment)
admin.site.register(UserDetail)
admin.site.register(CommentVote)
admin.site.register(ContributionVote)
