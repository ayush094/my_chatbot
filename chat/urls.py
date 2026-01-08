from django.urls import path
from . import views
from .views import ChatAPIView
from .views_auth import EmployeeLoginView, ManagerLoginView
from .views_leave import LeaveListCreateView, ManagerLeaveListView, LeaveActionView

urlpatterns = [
    path('', views.chat_home, name='chat_home'),
    path("api/chat/", ChatAPIView.as_view()),
    
    # Authentication
    path('api/auth/employee/login/', EmployeeLoginView.as_view(), name='employee_login'),
    path('api/auth/manager/login/', ManagerLoginView.as_view(), name='manager_login'),
    
    # Leave Management (API endpoints)
    path('api/leaves/', LeaveListCreateView.as_view(), name='leave_list_create'),
    path('api/leaves/pending/', ManagerLeaveListView.as_view(), name='manager_leave_list'),
    path('api/leaves/action/', LeaveActionView.as_view(), name='leave_action'),
]
