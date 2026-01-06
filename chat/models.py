from django.db import models
from pgvector.django import VectorField

class MetadataVector(models.Model):
    content = models.TextField()
    metadata_key = models.CharField(max_length=255) # table_name or table_name.col_name
    embedding = VectorField(dimensions=384)

    def __str__(self):
        return self.metadata_key


class ChatMessage(models.Model):
    user_message = models.TextField()
    ai_response = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.timestamp}: {self.user_message[:20]}..."


class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Employee(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, related_name='employees')
    position = models.CharField(max_length=100)
    hire_date = models.DateField()
    manager = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='subordinates')

    def __str__(self):
        return f"{self.first_name} {self.last_name}"


class Salary(models.Model):
    employee = models.OneToOneField(Employee, on_delete=models.CASCADE, related_name='salary')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    effective_date = models.DateField()

    def __str__(self):
        return f"{self.employee}: {self.amount}"


class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='attendance_records')
    date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        return f"{self.employee} - {self.date}: {self.status}"


class Leave(models.Model):
    LEAVE_TYPES = [
        ('Sick', 'Sick'),
        ('Vacation', 'Vacation'),
        ('Personal', 'Personal'),
    ]
    STATUS_CHOICES = [
        ('Approved', 'Approved'),
        ('Pending', 'Pending'),
        ('Denied', 'Denied'),
    ]
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='leaves')
    start_date = models.DateField()
    end_date = models.DateField()
    leave_type = models.CharField(max_length=20, choices=LEAVE_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)

    def __str__(self):
        return f"{self.employee} - {self.leave_type}: {self.start_date} to {self.end_date}"


