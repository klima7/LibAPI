# Library Management API

Library management system based on Django REST Framework, providing comprehensive API for managing books, readers, and checkouts. The API supports filtering by various parameters and pagination for handling large datasets. Includes comprehensive unit tests.

## Running the Project

### Production Environment
To run the application in production mode, execute:

```bash
docker compose up
```

### Development Environment
For development mode with hot-reloading functionality, use:

```bash
docker compose -f docker-compose.dev.yml up
```

### Running Tests
To run unit tests, execute:

```bash
docker compose exec -it web python manage.py test
```

### Generating fake data
The application provides Django management commands for generating fake data to play with API:

#### Generate fake data
```bash
docker compose exec -it web python manage.py add_fake_data
```
This command generates sample data with default values (10 readers, 20 books, 15 checkouts). You can customize the amounts:
```bash
docker compose exec -it web python manage.py add_fake_data --readers 5 --books 10 --checkouts 8
```

#### Clear all data
```bash
docker compose exec -it web python manage.py clear_data
```
This command removes all data from the database (books, readers, and checkouts).

## Available URLs

Once the application is running, the following addresses will be available:

- **http://localhost:8000/** - Django REST Framework browsable API
- **http://localhost:8000/admin/** - Django admin panel (login: `admin`, password: `password`)
- **http://localhost:8000/swagger/** - Interactive API documentation (Swagger UI)
- **http://localhost:8000/redoc/** - Alternative API documentation (ReDoc)

## Available API Endpoints

The system provides the following REST resources:

- `/books/` - book management
- `/readers/` - reader management
- `/checkouts/` - checkout handling

Each resource supports standard CRUD operations (Create, Read, Update, Delete) according to REST conventions.

## Technologies

### Core Technologies
- **Python 3.10+** - programming language
- **Django 5.2** - web framework
- **Django REST Framework** - framework for building REST APIs
- **PostgreSQL** - relational database
- **Docker & Docker Compose** - application containerization

### Key Libraries
- **drf-yasg** - automatic API documentation generation (Swagger/ReDoc)
- **django-filter** - advanced data filtering in API
- **psycopg2-binary** - PostgreSQL adapter for Python
- **Gunicorn** - WSGI server for production application