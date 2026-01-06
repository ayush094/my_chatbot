from django.contrib import admin
from .models import Employee, Department, Salary, Attendance, Leave

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('id', 'first_name', 'last_name', 'email', 'department', 'position', 'hire_date', 'manager')
    list_filter = ('department', 'position', 'hire_date')
    search_fields = ('first_name', 'last_name', 'email')
    raw_id_fields = ('manager',)

@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    list_display = ('employee', 'amount', 'effective_date')
    list_filter = ('effective_date',)
    search_fields = ('employee__first_name', 'employee__last_name')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'status')
    list_filter = ('date', 'status')
    search_fields = ('employee__first_name', 'employee__last_name')

@admin.register(Leave)
class LeaveAdmin(admin.ModelAdmin):
    list_display = ('employee', 'leave_type', 'start_date', 'end_date', 'status')
    list_filter = ('leave_type', 'status', 'start_date')
    search_fields = ('employee__first_name', 'employee__last_name')
