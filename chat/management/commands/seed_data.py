from django.core.management.base import BaseCommand
from chat.models import User, Employee, Department, Salary, Attendance, Leave
from django.utils import timezone
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Seeds the database with sample HR data'

    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding data...')

        # 1. Departments
        hr_dept, _ = Department.objects.get_or_create(name='HR')
        eng_dept, _ = Department.objects.get_or_create(name='Engineering')
        sales_dept, _ = Department.objects.get_or_create(name='Sales')

        # 2. Managers
        def create_manager(email, first_name, last_name, dept, pos):
            user, created = User.objects.get_or_create(
                email=email,
                defaults={'role': 'manager', 'is_staff': True}
            )
            if created:
                user.set_password('manager123')
                user.save()

            profile, _ = Employee.objects.get_or_create(
                email=email,
                defaults={
                    'user': user,
                    'first_name': first_name,
                    'last_name': last_name,
                    'department': dept,
                    'position': pos,
                    'hire_date': date(2020, 1, 1)
                }
            )
            return profile

        hr_manager = create_manager('hr_manager@company.com', 'John', 'HR-Mgr', hr_dept, 'HR Manager')
        eng_manager = create_manager('manager@company.com', 'Sarah', 'Eng-Mgr', eng_dept, 'Engineering Manager')

        # 3. Employees
        emp_data = [
            {
                'email': 'alice@company.com',
                'first_name': 'Alice',
                'last_name': 'Smith',
                'dept': eng_dept,
                'pos': 'Software Engineer',
                'salary': 80000,
                'manager': eng_manager
            },
            {
                'email': 'bob@company.com',
                'first_name': 'Bob',
                'last_name': 'Jones',
                'dept': eng_dept,
                'pos': 'DevOps Engineer',
                'salary': 85000,
                'manager': eng_manager
            },
            {
                'email': 'charlie@company.com',
                'first_name': 'Charlie',
                'last_name': 'Brown',
                'dept': hr_dept,
                'pos': 'HR Assistant',
                'salary': 50000,
                'manager': hr_manager
            }
        ]

        for data in emp_data:
            user, created = User.objects.get_or_create(
                email=data['email'],
                defaults={'role': 'employee'}
            )
            
            emp, created = Employee.objects.get_or_create(
                email=data['email'],
                defaults={
                    'user': user,
                    'first_name': data['first_name'],
                    'last_name': data['last_name'],
                    'department': data['dept'],
                    'position': data['pos'],
                    'hire_date': date(2022, 6, 15),
                    'manager': data['manager']
                }
            )

            Salary.objects.get_or_create(
                employee=emp,
                defaults={'amount': data['salary'], 'effective_date': date(2023, 1, 1)}
            )

            # Sample Attendance
            for i in range(5):
                Attendance.objects.get_or_create(
                    employee=emp,
                    date=date.today() - timedelta(days=i),
                    defaults={'status': 'Present'}
                )

            # Sample Leaves
            Leave.objects.get_or_create(
                employee=emp,
                start_date=date.today() + timedelta(days=10),
                end_date=date.today() + timedelta(days=12),
                defaults={'leave_type': 'Vacation', 'status': 'Pending'}
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded sample HR data'))
