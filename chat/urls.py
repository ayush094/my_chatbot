from django.urls import path
from . import views
from .views import ChatAPIView

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path("api/chat/", ChatAPIView.as_view()),
]
