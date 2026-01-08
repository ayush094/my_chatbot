from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from .models import Leave, Employee, User
from .serializers import LeaveSerializer

class IsEmployee(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'employee'

class IsManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and getattr(request.user, 'role', None) == 'manager'

class LeaveListCreateView(generics.ListCreateAPIView):
    serializer_class = LeaveSerializer
    permission_classes = [IsEmployee]

    def get_queryset(self):
        # View only their own leave
        try:
            employee = Employee.objects.get(user=self.request.user)
            return Leave.objects.filter(employee=employee)
        except Employee.DoesNotExist:
            return Leave.objects.none()

    def perform_create(self, serializer):
        try:
            employee = Employee.objects.get(user=self.request.user)
            serializer.save(employee=employee, status='Pending')
        except Employee.DoesNotExist:
            # This should ideally be handled by a more robust profile check
            pass

class ManagerLeaveListView(generics.ListAPIView):
    serializer_class = LeaveSerializer
    permission_classes = [IsManager]

    def get_queryset(self):
        # View pending leaves ONLY for employees who report to this manager
        try:
            manager_profile = Employee.objects.get(user=self.request.user)
            return Leave.objects.filter(status='Pending', employee__manager=manager_profile)
        except Employee.DoesNotExist:
            return Leave.objects.none()

class LeaveActionView(APIView):
    permission_classes = [IsManager]

    def post(self, request):
        command = request.data.get('command', '') # e.g. "approve leave id 3"
        action = None
        leave_id = None
        
        lower_command = command.lower()
        if 'approve leave id' in lower_command:
            action = 'Approved'
            try:
                leave_id = int(lower_command.split('approve leave id')[-1].strip())
            except ValueError:
                pass
        elif 'reject leave id' in lower_command:
            action = 'Denied'
            try:
                leave_id = int(lower_command.split('reject leave id')[-1].strip())
            except ValueError:
                pass
        
        if not action or not leave_id:
            return Response({"error": "Invalid command format. Use 'approve leave id X' or 'reject leave id X'"}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            leave = Leave.objects.get(id=leave_id)
            manager_profile = Employee.objects.get(user=request.user)
            
            # Security checks
            if leave.employee.manager != manager_profile:
                return Response({"error": "You can only act upon leave requests from your direct reports"}, status=status.HTTP_403_FORBIDDEN)
            
            if leave.employee.user == request.user:
                return Response({"error": "Managers cannot approve their own leave"}, status=status.HTTP_403_FORBIDDEN)
            
            leave.status = action
            leave.save()
            return Response({"message": f"Leave {leave_id} has been {action.lower()}"})
        except Leave.DoesNotExist:
            return Response({"error": f"Leave request with ID {leave_id} not found"}, status=status.HTTP_404_NOT_FOUND)
