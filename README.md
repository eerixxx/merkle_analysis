# Hierarchy Viewer

A full-stack application for viewing user hierarchies for Limitless and BoostyFi projects.

## Tech Stack

### Frontend
- React 18 + TypeScript
- Vite (build tool)
- shadcn/ui + Tailwind CSS
- TanStack Query (data fetching)
- React Router v6
- Axios

### Backend
- Django 5.0
- Django REST Framework
- djangorestframework-simplejwt (JWT auth)
- django-mptt (tree structures)
- Celery + Redis (background tasks)
- PostgreSQL 15
- Gunicorn + WhiteNoise

### Infrastructure
- Docker + Docker Compose
- Prometheus (metrics)
- Grafana (dashboards)
- Loki (logs)

## Project Structure

```
├── frontend/           # React application
│   ├── src/
│   │   ├── components/ # UI components
│   │   ├── pages/      # Page components
│   │   ├── lib/        # Utilities & API
│   │   └── types/      # TypeScript types
│
├── backend/            # Django application
│   ├── apps/
│   │   ├── core/       # Shared models & utils
│   │   ├── users/      # Auth user model
│   │   ├── limitless/  # Limitless models & API
│   │   └── boostyfi/   # BoostyFi models & API
│   ├── config/         # Django settings
│   └── requirements/   # Python dependencies
│
├── docker/             # Dockerfiles
├── monitoring/         # Prometheus, Grafana, Loki configs
├── sheets/             # Original CSV data
└── docker-compose.yml
```

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Node.js 20+ (for local frontend development)
- Python 3.11+ (for local backend development)

### Development Setup

1. **Clone the repository**
```bash
git clone <repo-url>
cd jggl_limitless_old
```

2. **Create environment file**
```bash
cp .env.example .env
# Edit .env with your settings
```

3. **Start services with Docker Compose**
```bash
docker-compose up -d
```

4. **Run database migrations**
```bash
docker-compose exec backend python manage.py migrate
```

5. **Create superuser**
```bash
docker-compose exec backend python manage.py createsuperuser
```

6. **Import CSV data**
```bash
docker-compose exec backend python manage.py import_csv --sheets-dir /app/../sheets
```

7. **Access the application**
- Frontend: http://localhost
- Backend API: http://localhost:8000/api/v1/
- Django Admin: http://localhost:8000/admin/
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

### Local Development (without Docker)

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements/local.txt

# Set environment variables
export DEBUG=true
export SECRET_KEY=dev-secret-key
export POSTGRES_HOST=localhost
export REDIS_URL=redis://localhost:6379/0

# Run migrations
python manage.py migrate

# Start development server
python manage.py runserver
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/token/` - Get JWT token
- `POST /api/v1/auth/token/refresh/` - Refresh token

### Limitless
- `GET /api/v1/limitless/users/` - List users
- `GET /api/v1/limitless/users/{id}/` - User details
- `GET /api/v1/limitless/users/{id}/tree/` - User subtree
- `GET /api/v1/limitless/users/roots/` - Root users
- `GET /api/v1/limitless/users/stats/` - Statistics

### BoostyFi
- `GET /api/v1/boostyfi/users/` - List users
- `GET /api/v1/boostyfi/users/{id}/` - User details
- `GET /api/v1/boostyfi/users/{id}/tree/` - User subtree
- `GET /api/v1/boostyfi/users/roots/` - Root users
- `GET /api/v1/boostyfi/users/stats/` - Statistics

## Management Commands

### Import CSV Data
```bash
python manage.py import_csv --app all --sheets-dir ../sheets
python manage.py import_csv --app limitless --clear  # Clear and reimport
python manage.py import_csv --app boostyfi
```

## Docker Commands

```bash
# Build and start
docker-compose up -d --build

# View logs
docker-compose logs -f backend

# Stop services
docker-compose down

# Reset database
docker-compose down -v
docker-compose up -d
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| DEBUG | Debug mode | false |
| SECRET_KEY | Django secret key | - |
| ALLOWED_HOSTS | Comma-separated hosts | localhost |
| POSTGRES_DB | Database name | hierarchy_db |
| POSTGRES_USER | Database user | postgres |
| POSTGRES_PASSWORD | Database password | postgres |
| REDIS_URL | Redis connection URL | redis://localhost:6379/0 |
| CORS_ALLOWED_ORIGINS | Allowed CORS origins | - |

## License

Private - All rights reserved
