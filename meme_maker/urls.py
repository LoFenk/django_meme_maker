from django.urls import path
from . import views

app_name = 'meme_maker'

urlpatterns = [
    path('', views.home, name='home'),
    path('create/', views.create_meme, name='create'),
    path('meme/<int:pk>/', views.meme_detail, name='detail'),
    path('memes/', views.meme_list, name='list'),
]

