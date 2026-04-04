from .employees_routes import hr_employees_bp
from .departments_routes import hr_departments_bp
from .job_titles_routes import hr_job_titles_bp
from .movements_routes import hr_movements_bp
from .leave_routes import hr_leave_bp
from .attendance_routes import hr_attendance_bp

__all__ = [
    "hr_employees_bp",
    "hr_departments_bp",
    "hr_job_titles_bp",
    "hr_movements_bp",
    "hr_leave_bp",
    "hr_attendance_bp",
]