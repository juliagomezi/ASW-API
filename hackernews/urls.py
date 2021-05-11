from django.urls import path, re_path

from . import views

urlpatterns = [

    path('api/users', views.profile_api, name='profile'),
    path('api/submissions/<int:id>/', views.newest, name='newest'),
    path('api/submissions/', views.newest, name='newest'),
    path('api/replies/<int:id>/vote', views.newest, name='newest'),
    path('api/replies/<int:id>/comment', views.newest, name='newest'),
    path('api/replies/<int:id>/', views.newest, name='newest'),
    path('api/replies/', views.newest, name='newest'),
    path('newest/', views.newest, name='newest'),
    path('threads', views.threads, name='threads'),
    path('ask/', views.ask, name='ask'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('logout/', views.signout, name='logout'),
    path('user', views.profile, name='user'),
    path('submit/', views.SubmitView.as_view(), name='submit'),
    path('submission', views.submission, name='submission'),
    path('favourites', views.favourites, name='favourites'),
    path('comments', views.favcomments, name='comments'),
    path('errormessage/', views.errormessage, name='errormessage'),
    path('item/<int:id>/', views.item, name='item'),
    path('reply/<int:id>/', views.reply, name='reply'),
    path('createuser/', views.createuser, name='createuser'),
    path('vote/', views.vote, name='vote'),
    path('votecomment/', views.votecomment, name='votecomment'),
    path('unvotecomment/<int:id>', views.unvotecomment, name='unvotecomment'),
    path('unvote/<int:id>', views.unvote, name='unvote'),
    path('', views.index, name='index'),
]
