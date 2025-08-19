# IkekoHub - Multi-Tenant School Management System

> A comprehensive multi-tenant Django REST API platform for school management with role-based access control

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Usage Examples](#usage-examples)
- [Contributing](#contributing)
- [License](#license)

## Overview

IkekoHub is a multi-tenant school management system built with Django that allows multiple schools to operate independently within the same application infrastructure. Each school operates in its own isolated database schema while sharing the same codebase, ensuring data security and scalability.

The system supports four main user roles:
- **Admin**: School administrators with full access
- **Teacher**: Teaching staff with classroom management capabilities
- **Student**: Students with access to their academic information
- **Parent**: Parents with access to their children's information

## Features

- ✨ **Multi-tenancy**: Complete data isolation between schools
- 🔐 **JWT Authentication**: Secure token-based authentication
- 👥 **Role-based Access Control**: Admin, Teacher, Student, and Parent roles
- 🏫 **School Management**: Create and manage multiple schools
- 👨‍🎓 **Student Management**: Comprehensive student profiles and enrollment
- 👨‍🏫 **Teacher Management**: Teacher profiles and subject assignment
- 👨‍👩‍👧‍👦 **Parent Integration**: Automatic parent account creation and linking
- 📊 **Bulk Operations**: Mass student creation support
- 🔄 **Automatic Workflows**: Parent accounts auto-created when students are enrolled
- 📱 **RESTful API**: Complete REST API with Swagger documentation

## Tech Stack

### Backend
- **Language**: Python 3.8+
- **Framework**: Django 5.2.3
- **REST Framework**: Django REST Framework 3.16.0
- **Database**: PostgreSQL with django-tenants
- **Authentication**: 
  - JWT (Simple JWT 5.5.0)
  - Django Allauth 65.9.0
  - dj-rest-auth 7.0.1
- **Multi-tenancy**: django-tenants 3.8.0
- **Task Queue**: Celery 5.5.3 with Redis 6.2.0
- **Documentation**: drf-yasg 1.21.10 (Swagger/OpenAPI)

### Infrastructure
- **Database**: PostgreSQL
- **Cache/Message Broker**: Redis
- **Static Files**: WhiteNoise
- **Container**: Docker & Docker Compose

## Architecture

### Multi-Tenant Architecture
- **Public Schema**: Contains shared data (schools, domains, users)
- **Tenant Schemas**: Each school has its own isolated schema
- **Dynamic Schema Routing**: Automatic tenant detection via subdomain

### Role-Based Access Control
```
Admin (School-wide access)
├── Create/manage teachers
├── Create/manage students
├── View all data within school
└── Bulk operations

Teacher (Classroom access)
├── View assigned students
├── Access teaching materials
└── Classroom management

Student (Personal access)
├── View own academic information
├── Access learning materials
└── Communication with teachers

Parent (Child-related access)
├── View children's information
├── Communication with teachers
└── Academic progress tracking
```

## Installation

### Prerequisites

- Python 3.8 or higher
- PostgreSQL 12+
- Redis (for Celery tasks)
- Docker and Docker Compose (optional)

### Local Development Setup

1. **Clone the repository**
   ```bash
   git clone https://github.com/Olokor/main-ikekohub.git
   cd main-ikekohub
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Database setup with Docker**
   ```bash
   # Start PostgreSQL container
   docker-compose up db -d
   ```

5. **Configure environment variables**
   ```bash
   # Create .env file with your configuration
   cp .env.example .env
   ```

6. **Run migrations**
   ```bash
   # Create and migrate public schema
   python manage.py migrate_schemas --shared
   
   # Create and migrate tenant schemas
   python manage.py migrate_schemas
   ```

7. **Create a public schema tenant**
   ```bash
   python manage.py shell
   ```
   ```python
   from public_app.models import School, Domain
   
   # Create public tenant
   public_tenant = School(schema_name='public', name='Public')
   public_tenant.save()
   
   # Create domain
   domain = Domain(domain='localhost', tenant=public_tenant, is_primary=True)
   domain.save()
   ```

8. **Start the development server**
   ```bash
   python manage.py runserver
   ```

### Docker Setup

```bash
# Build and run with Docker Compose
docker-compose up --build

# Run in detached mode
docker-compose up -d
```

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Database Configuration
DATABASE_NAME=main-ikekohub
DATABASE_USER=postgres
DATABASE_PASSWORD=passwd
DATABASE_HOST=localhost
DATABASE_PORT=1649

# Django Configuration
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,*.localhost

# JWT Configuration
JWT_ACCESS_TOKEN_LIFETIME=30  # minutes
JWT_REFRESH_TOKEN_LIFETIME=60  # hours

# Email Configuration (for development)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend

# Redis Configuration (for Celery)
REDIS_URL=redis://localhost:6379

# File Upload Configuration
MEDIA_URL=/media/
MEDIA_ROOT=./media
```

### Database Configuration

The application uses PostgreSQL with django-tenants for multi-tenancy:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': 'main-ikekohub',
        'USER': 'postgres',
        'PASSWORD': 'passwd',
        'HOST': 'localhost',
        'PORT': 1649,
    }
}
```

## API Documentation

### Base URLs
- **Public API**: `http://localhost:8000/api/public/`
- **Tenant API**: `http://{school}.localhost:8000/api-tenant/`
- **Authentication**: `http://localhost:8000/api/auth/`

### Authentication

The API uses JWT tokens for authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

### Public Endpoints (No Authentication Required)

#### School Management
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/public/create-school/` | Create a new school tenant |
| POST | `/api/auth/login/` | User login |
| POST | `/api/auth/registration/` | User registration |
| POST | `/api/auth/password/reset/` | Password reset |

### Tenant Endpoints (Authentication Required)

**Note**: These endpoints are accessed via school-specific subdomains (e.g., `schoolname.localhost:8000`)

#### Admin Endpoints (`/api-tenant/admin/`)
| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| POST | `/create-admin/` | Create new admin user | Admin |
| POST | `/create-teacher/` | Create new teacher | Admin |
| POST | `/create-student/` | Create new student | Admin |
| POST | `/create-students/` | Bulk create students | Admin |
| GET | `/get-teacher/<username>` | Get teacher by username | Admin |
| GET | `/get-all-teachers` | List all teachers | Admin |
| GET | `/get-student/<admission_number>` | Get student by admission number | Admin |
| GET | `/get-all-student/` | List all students | Admin |

#### Teacher Endpoints (`/api-tenant/teacher/`)
| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/teacher-dashboard/` | Teacher dashboard | Teacher |

#### Student Endpoints (`/api-tenant/student/`)
| Method | Endpoint | Description | Permission |
|--------|----------|-------------|------------|
| GET | `/student-dashboard/` | Student dashboard | Student |

#### Authentication Endpoints (`/api-tenant/`)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/token/` | Obtain JWT token pair |
| POST | `/token/refresh/` | Refresh JWT token |

### Request/Response Examples

#### 1. Create a School
```bash
curl -X POST http://localhost:8000/api/public/create-school/ \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Springfield Elementary",
    "admin_email": "admin@springfield.edu",
    "admin_first_name": "John",
    "admin_last_name": "Doe"
  }'
```

**Response:**
```json
{
  "school": {
    "id": 1,
    "name": "Springfield Elementary",
    "schema_name": "springfieldelementary",
    "created_at": "2025-08-19T10:30:00Z",
    "admin_email": "admin@springfield.edu",
    "admin_first_name": "John",
    "admin_last_name": "Doe"
  },
  "domain": {
    "id": 1,
    "domain": "SpringfieldElementary.localhost",
    "is_primary": true,
    "tenant": 1
  }
}
```

#### 2. Admin Login (Tenant-specific)
```bash
curl -X POST http://springfieldelementary.localhost:8000/api-tenant/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin@springfield.edu",
    "password": "Default_password12345!"
  }'
```

**Response:**
```json
{
  "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

#### 3. Create a Teacher
```bash
curl -X POST http://springfieldelementary.localhost:8000/api-tenant/admin/create-teacher/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{
    "username": "jane.smith",
    "email": "jane.smith@springfield.edu",
    "password": "SecurePass123!",
    "school": "Springfield Elementary"
  }'
```

**Response:**
```json
{
  "id": 1,
  "username": "jane.smith",
  "email": "jane.smith@springfield.edu",
  "school": "Springfield Elementary"
}
```

#### 4. Create a Student
```bash
curl -X POST http://springfieldelementary.localhost:8000/api-tenant/admin/create-student/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '{
    "username": "bart.simpson",
    "first_name": "Bart",
    "last_name": "Simpson",
    "email": "bart.simpson@student.springfield.edu",
    "password": "StudentPass123!",
    "school": "Springfield Elementary",
    "admission_number": "SE2025001",
    "date_of_birth": "2010-04-01",
    "parent_name": "Homer Simpson",
    "parent_email": "homer.simpson@email.com",
    "parent_contact": "+1234567890",
    "address": "742 Evergreen Terrace, Springfield",
    "class_level": "4th Grade",
    "academic_year": "2024-2025"
  }'
```

**Response:**
```json
{
  "id": 1,
  "username": "bart.simpson",
  "email": "bart.simpson@student.springfield.edu",
  "school": "Springfield Elementary",
  "admission_number": "SE2025001",
  "date_of_birth": "2010-04-01",
  "parent_name": "Homer Simpson",
  "parent_email": "homer.simpson@email.com",
  "parent_contact": "+1234567890",
  "address": "742 Evergreen Terrace, Springfield",
  "class_level": "4th Grade",
  "academic_year": "2024-2025",
  "parent_username": "parent_homer.simpson"
}
```

#### 5. Bulk Create Students
```bash
curl -X POST http://springfieldelementary.localhost:8000/api-tenant/admin/create-students/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <admin_token>" \
  -d '[
    {
      "username": "lisa.simpson",
      "first_name": "Lisa",
      "last_name": "Simpson",
      "email": "lisa.simpson@student.springfield.edu",
      "password": "StudentPass123!",
      "school": "Springfield Elementary",
      "admission_number": "SE2025002",
      "date_of_birth": "2012-05-09",
      "parent_name": "Homer Simpson",
      "parent_email": "homer.simpson@email.com",
      "parent_contact": "+1234567890",
      "address": "742 Evergreen Terrace, Springfield",
      "class_level": "2nd Grade",
      "academic_year": "2024-2025"
    }
  ]'
```

### Error Responses

All error responses follow this format:

```json
{
  "error": "Error message",
  "details": {
    "field_name": ["Specific field error message"]
  }
}
```

**Common HTTP Status Codes:**
- `200` - Success
- `201` - Created
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `500` - Internal Server Error

## Project Structure

```
main-ikekohub/
├── admin_app/              # Admin functionality
│   ├── models.py          # AdminProfile model
│   ├── views.py           # Admin CRUD operations
│   ├── serializers.py     # Admin serializers
│   ├── permissions.py     # IsSchoolAdmin permission
│   ├── signals.py         # Parent auto-creation signals
│   └── urls.py            # Admin endpoints
├── teacher_app/           # Teacher functionality
│   ├── models.py          # TeacherProfile model
│   ├── views.py           # Teacher views
│   ├── serializers.py     # Teacher serializers
│   ├── permissions.py     # IsTeacher permission
│   └── urls.py            # Teacher endpoints
├── student_app/           # Student functionality
│   ├── models.py          # StudentProfile model
│   ├── views.py           # Student views
│   ├── serializers.py     # Student serializers
│   ├── permissions.py     # IsStudent permission
│   └── urls.py            # Student endpoints
├── parent_app/            # Parent functionality
│   ├── models.py          # ParentProfile model
│   └── urls.py            # Parent endpoints (empty)
├── public_app/            # Multi-tenant models
│   ├── models.py          # School, Domain, TenantUser
│   ├── views.py           # School creation
│   ├── serializers.py     # Public serializers
│   └── urls.py            # Public endpoints
├── ikekohub/              # Django project configuration
│   ├── settings.py        # Django settings
│   ├── public_urls.py     # Public URL configuration
│   ├── tenant_urls.py     # Tenant URL configuration
│   └── wsgi.py            # WSGI configuration
├── requirements.txt       # Python dependencies
├── docker-compose.yaml    # Docker configuration
├── manage.py             # Django management script
└── README.md             # This file
```

### Key Models

#### Public Schema Models
- **School (TenantMixin)**: Represents each school tenant
- **Domain (DomainMixin)**: Maps subdomains to schools
- **TenantUser (AbstractUser)**: Custom user model with school relationship

#### Tenant Schema Models
- **AdminProfile**: Admin-specific profile and permissions
- **TeacherProfile**: Teacher profile with subjects taught
- **StudentProfile**: Student profile with academic information
- **ParentProfile**: Parent profile linked to students

## Usage Examples

### Setting Up a New School

1. **Create the school**:
   ```bash
   POST /api/public/create-school/
   ```

2. **Access via subdomain**:
   ```
   http://schoolname.localhost:8000
   ```

3. **Admin login with default credentials**:
   - Username: admin email provided
   - Password: `Default_password12345!`

4. **Create teachers and students** using admin endpoints

### Automatic Parent Account Creation

When a student is created, the system automatically:
1. Creates a parent user account using the parent email
2. Sets a default password: `Parent{admission_number}!`
3. Creates a ParentProfile linked to the student
4. Links the parent to the student through many-to-many relationship

### Working with Multi-Tenancy

Each school operates on its own subdomain:
- `school1.localhost:8000` - School 1's interface
- `school2.localhost:8000` - School 2's interface
- `localhost:8000` - Public interface for school creation

Data is completely isolated between tenants at the database level.

## API Documentation URLs

- **Public API Swagger**: `http://localhost:8000/swagger/public/`
- **Tenant API Swagger**: `http://{school}.localhost:8000/swagger/tenant/`

## Development

### Running Tests

```bash
# Run all tests
python manage.py test

# Run specific app tests
python manage.py test admin_app
python manage.py test student_app
```

### Database Management

```bash
# Create migrations
python manage.py makemigrations

# Apply migrations to public schema
python manage.py migrate_schemas --shared

# Apply migrations to all tenant schemas
python manage.py migrate_schemas

# Create a superuser for public schema
python manage.py createsuperuser
```

### Celery Tasks (if implemented)

```bash
# Start Celery worker
celery -A ikekohub worker -l info

# Start Celery beat (for scheduled tasks)
celery -A ikekohub beat -l info
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines

- Follow PEP 8 style guidelines
- Write tests for new features
- Update documentation for API changes
- Use meaningful commit messages
- Ensure multi-tenant compatibility

## Troubleshooting

### Common Issues

1. **Schema not found errors**
   - Ensure you've run `migrate_schemas` for tenant schemas
   - Check that the subdomain matches the school's schema name

2. **Permission denied errors**
   - Verify JWT token is valid and not expired
   - Check user has the correct role for the endpoint

3. **Database connection errors**
   - Ensure PostgreSQL is running on port 1649
   - Check database credentials in settings

4. **Parent creation failures**
   - Check the signals are properly configured
   - Verify parent email is unique across the tenant

## License

This project is licensed under the Olokor-Dev_0 License - see the LICENSE file for details.

## Support

For support, please create an issue in the GitHub repository or contact the development team.

---

**Built with ❤️ by the IkekoHub Team**
