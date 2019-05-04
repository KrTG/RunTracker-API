from django.urls import path

from . import views, views_user

urlpatterns = [    
    path('test', views.test_view, name='test_view'),
    path('version', views.version, name='version'),
    path('time', views.time, name='time'),
    path('register', views_user.register, name='register'),
    path('login', views_user.login, name='login'),
    path('logout', views_user.logout, name='logout'),
    path('login-status', views_user.check_login, name='check_login'),
    path('profile', views_user.my_profile, name='my_profile'),
    path('profile/<int:user_id>/', views_user.profile, name='profile'),
    path('profile/stats', views_user.my_stats, name='my_stats'),
    path('profile/<int:user_id>/stats', views_user.stats, name='stats'),
    path('profile/avatar', views_user.change_avatar, name='change_avatar'),
    path('runs', views.runs_get, name='runs_get'),
    path('runs/create', views.run_create, name='run_create'),    
    path('runs/<int:run_id>/', views.run_get, name='run_get'),
    path('runs/<int:run_id>/join', views.run_join, name='run_join'),
    path('runs/<int:run_id>/quit', views.run_quit, name='run_quit'),
    path('runs/<int:run_id>/splits', views.splits, name='splits'),
    path('runs/<int:run_id>/splits/submit', views.split_create, name='split_create'),
    path('runs/<int:run_id>/results', views.run_results, name='run_results'),
    path('runs/<int:run_id>/comments', views.comments_get, name='comments_get'),
    path('runs/<int:run_id>/comments/add', views.add_comment, name='add_comment'),    
    path('runs/<int:run_id>/watch', views.start_watching, name='start_watching'),
    path('runs/<int:run_id>/stop-watching', views.stop_watching, name='start_watching'),
    path('runs/<int:run_id>/like', views.add_like, name='add_like'),
    path('runs/<int:run_id>/unlike', views.remove_like, name='remove_like'),
]