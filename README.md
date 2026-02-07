# OhTaskMe

An intelligent Django-based productivity platform that automatically generates preparation tasks for your events using AI-powered NLP analysis. Manage tasks and events with JWT authentication, REST APIs, and smart workload distribution.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [AI Task Suggestion System](#ai-task-suggestion-system)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Features

### Core Functionality
- **Event Management**: Create and manage events with automatic task generation
- **Task Management**: Organize tasks with scheduling, completion tracking, and event associations
- **AI-Powered Task Suggestions**: Intelligent NLP-based task recommendations for event preparation
- **Smart Workload Distribution**: Automatically balance tasks across available time slots
- **Statistics Dashboard**: Track productivity metrics, completion rates, and trends
- **User Authentication**: Secure JWT-based authentication with custom user model

### Advanced Features
- **Event-Task Relationships**: Link tasks to events for automated preparation workflows
- **NLP Analysis**: Context-aware event classification using spaCy and NLTK
- **ML Training Pipeline**: Adaptive learning from user feedback and historical data
- **REST API**: Full-featured API for all operations with filtering, ordering, and pagination
- **Responsive Frontend**: Django templates with Bootstrap for clean, mobile-friendly UI
- **Password Reset**: Secure password recovery workflow

## Technology Stack

### Backend
- **Framework**: Django 5.2.5
- **API**: Django REST Framework 3.16.1
- **Authentication**: djangorestframework-simplejwt 5.5.1
- **Database**: PostgreSQL (via psycopg2-binary 2.9.10)
- **API Documentation**: drf-yasg 1.21.10

### AI & Machine Learning
- **NLP**: spaCy 3.8.7 with en_core_web_sm model
- **Text Processing**: NLTK 3.9.1
- **Machine Learning**: scikit-learn 1.7.1, scipy 1.16.1
- **Data Processing**: numpy 2.3.2

### Frontend
- **Templates**: Django template system
- **Styling**: Bootstrap (CSS framework)
- **JavaScript**: Vanilla JS for interactivity

### Additional Libraries
- **Filtering**: django-filter 25.1
- **Task Queue Support**: Python standard library
- **Date/Time**: pytz 2025.2

## Project Structure

```
ohtaskme/
├── ohtaskme/              # Main project configuration
│   ├── settings.py        # Django settings
│   ├── urls.py            # Root URL configuration
│   └── wsgi.py            # WSGI configuration
├── users/                 # User authentication app
│   ├── models.py          # Custom User model
│   ├── serializers.py     # User serializers
│   ├── views.py           # Auth views (registration, profile, password reset)
│   └── urls.py            # User endpoints
├── tasks/                 # Task management app
│   ├── models.py          # Task model
│   ├── serializers.py     # Task serializers
│   ├── views.py           # Task CRUD operations
│   ├── filters.py         # Task filtering logic
│   └── urls.py            # Task endpoints
├── events/                # Event management app
│   ├── models.py          # Event and ActiveEvent models
│   ├── serializers.py     # Event serializers
│   ├── views.py           # Event CRUD operations
│   ├── task_suggestions.py # AI task suggestion engine
│   ├── training_pipeline.py # ML model training
│   ├── signals.py         # Auto task generation signals
│   └── urls.py            # Event endpoints
├── stats/                 # Statistics and analytics app
│   ├── models.py          # Statistics models
│   ├── analytics.py       # Analytics calculations
│   ├── views.py           # Stats views
│   └── urls.py            # Stats endpoints
├── templates/             # Django HTML templates
│   ├── base.html          # Base template
│   ├── users/             # User templates
│   ├── tasks/             # Task templates
│   ├── events/            # Event templates
│   └── stats/             # Statistics templates
├── static/                # Static files (CSS, JS, images)
├── ml_models/             # Trained ML models (gitignored)
├── manage.py              # Django management script
├── requirements.txt       # Python dependencies
└── devplan.md             # Development roadmap
```

## Installation

### Prerequisites
- Python 3.8 or higher
- PostgreSQL 12 or higher
- pip (Python package manager)
- virtualenv (recommended)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/ohtaskme.git
cd ohtaskme
```

### Step 2: Create Virtual Environment

```bash
python -m venv devvenv
```

Activate the virtual environment:
- **Windows**: `devvenv\Scripts\activate`
- **Linux/Mac**: `source devvenv/bin/activate`

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Download NLP Models

```bash
python -m spacy download en_core_web_sm
python -m nltk.downloader stopwords punkt
```

### Step 5: Set Up PostgreSQL Database

Create a PostgreSQL database:
```sql
CREATE DATABASE ohtaskme_db;
CREATE USER ohtaskme_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE ohtaskme_db TO ohtaskme_user;
```

### Step 6: Configure Environment

Update `ohtaskme/settings.py` with your database credentials:
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'ohtaskme_db',
        'USER': 'ohtaskme_user',
        'PASSWORD': 'your_password',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
```

### Step 7: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 8: Create Superuser

```bash
python manage.py createsuperuser
```

### Step 9: Initialize AI Model (Optional)

```bash
python initialize_task_model.py
```

Or use the management command:
```bash
python manage.py train_task_model
```

### Step 10: Collect Static Files

```bash
python manage.py collectstatic
```

### Step 11: Run Development Server

```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## Configuration

### JWT Settings

JWT token lifetimes can be configured in `settings.py`:
```python
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    # ... other settings
}
```

### Static Files

Configure static file directories in `settings.py`:
```python
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
```

### AI Task Suggestion

Model settings can be adjusted in `events/task_suggestions.py`:
- Event classification patterns
- Confidence thresholds
- Task templates
- Timing calculations

## Usage

### Web Interface

1. **Register**: Create a new account at `/users/register/`
2. **Login**: Sign in at `/users/login/`
3. **Dashboard**: View overview at `/`
4. **Tasks**: Manage tasks at `/tasks/`
5. **Events**: Manage events at `/events/`
6. **Statistics**: View analytics at `/stats/`

### API Endpoints

Base URL: `http://localhost:8000/api/`

#### Authentication
- `POST /api/users/register/` - Register new user
- `POST /api/users/token/` - Obtain JWT token
- `POST /api/users/token/refresh/` - Refresh JWT token
- `GET /api/users/profile/` - Get user profile
- `PUT /api/users/profile/` - Update user profile

#### Tasks
- `GET /api/tasks/` - List all tasks
- `POST /api/tasks/` - Create new task
- `GET /api/tasks/{id}/` - Retrieve task details
- `PUT /api/tasks/{id}/` - Update task
- `DELETE /api/tasks/{id}/` - Delete task

#### Events
- `GET /api/events/` - List all events
- `POST /api/events/` - Create new event
- `GET /api/events/{id}/` - Retrieve event details
- `PUT /api/events/{id}/` - Update event
- `DELETE /api/events/{id}/` - Delete event
- `GET /api/events/{id}/suggest-tasks/` - Get AI task suggestions

#### Statistics
- `GET /api/stats/dashboard/` - Get statistics overview
- `GET /api/stats/productivity/` - Get productivity metrics

### API Authentication

Include JWT token in request headers:
```bash
Authorization: Bearer <your_access_token>
```

Example using curl:
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8000/api/tasks/
```

## API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/swagger/`
- **ReDoc**: `http://localhost:8000/redoc/`

## AI Task Suggestion System

The AI task suggestion system uses NLP and machine learning to generate intelligent task recommendations.

### How It Works

1. **Event Analysis**: Analyzes event title, description, duration, and location
2. **Classification**: Categorizes events (meeting, presentation, travel, etc.)
3. **Task Generation**: Generates context-appropriate preparation tasks
4. **Confidence Scoring**: Assigns confidence scores to suggestions
5. **Timing Optimization**: Schedules tasks based on workload and deadlines

### Training the Model

Train the model with historical data:
```bash
python manage.py train_task_model
```

The model learns from:
- Previously created tasks
- User acceptance/rejection patterns
- Event-task associations
- Completion rates

### Customization

Modify event patterns in `events/task_suggestions.py`:
```python
EVENT_PATTERNS = {
    'meeting': {
        'keywords': ['meeting', 'discussion', 'sync'],
        'tasks': ['prepare agenda', 'book room', 'send invites']
    },
    # Add your own patterns
}
```

## Testing

### Run All Tests

```bash
python manage.py test
```

### Run Specific App Tests

```bash
python manage.py test users
python manage.py test tasks
python manage.py test events
python manage.py test stats
```

### Test Coverage

Run tests with coverage:
```bash
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Helper Scripts

- `run_all_tests.py` - Python script to run all tests
- `run_all_tests.ps1` - PowerShell script for Windows
- `run_all_tests.bat` - Batch script for Windows

## Project Highlights

### Modular Architecture
- Separation of concerns with distinct apps for users, tasks, events, and statistics
- Reusable components and clear interfaces
- Easy to extend and maintain

### Intelligent Automation
- Automatic task generation based on event details
- Smart workload distribution to avoid overloading users
- Adaptive learning from user behavior

### Developer-Friendly
- Comprehensive API documentation
- Clear project structure
- Extensive test coverage
- Type hints and docstrings

### Production-Ready
- JWT authentication for security
- PostgreSQL for scalability
- REST API for integration
- Configurable settings

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Guidelines
- Follow PEP 8 style guide
- Write tests for new features
- Update documentation as needed
- Keep commits atomic and descriptive

## Acknowledgments

- Built with Django and Django REST Framework
- NLP powered by spaCy and NLTK
- UI styled with Bootstrap
- Inspired by productivity methodologies and task management best practices

## Support

For issues, questions, or suggestions:
- Open an issue on GitHub
- Contact the maintainer

## Roadmap

Future enhancements planned:
- User profile customization and preferences
- Advanced ML models for task success prediction
- Google Calendar integration
- Mobile app (Android/iOS)
- Team collaboration features
- Gamification and achievement system
- Export/import functionality (CSV, iCal)
- Real-time notifications

---

Built with care for productive people.
