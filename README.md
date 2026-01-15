# Fitness Trainer API

A comprehensive personal fitness tracking REST API built with Flask and SQLite. Track workouts, monitor nutrition, manage fitness goals, and analyze progress with a complete suite of analytics features.

## 🎯 Project Overview

The Fitness Trainer API is a full-featured backend system designed to support fitness and wellness applications. It provides 48 endpoints across 12 modules covering:

- **Authentication & Authorization**: User registration, login, JWT token management, Google OAuth 2.0
- **User Management**: Profile management, fitness statistics, progress tracking
- **Workout Tracking**: Create, log, and analyze workouts with exercise-level detail
- **Nutrition Logging**: Track meals, monitor macros, calculate daily nutrition
- **Goal Management**: Set fitness goals, track progress, monitor completion
- **Exercise Reference**: Browse 50+ pre-loaded exercises with difficulty levels
- **Training Programs**: Generate personalized weekly workout programs
- **Calendar Planning**: Plan workouts and events across your calendar
- **Dashboard Analytics**: Comprehensive metrics and visualizations
- **ML Equipment Recognition**: AI-powered equipment identification from images
- **Email Verification**: Secure 2FA with email-based verification codes
- **Comprehensive Testing**: Full test suite with 15+ test cases

## 🚀 Quick Start

### Installation

```bash
# Clone repository (or download files)
cd fitness-api-project

# Install dependencies
pip install -r requirements.txt

# Initialize database with exercise data
python scripts/seed_exercises.py

# Start the server
python run.py
```

Server runs on `http://localhost:5000`

### Verification

```bash
# Check server health
curl http://localhost:5000/api/health

# Expected response:
# {"status": "healthy"}
```

## 📋 API Documentation

### 46 Total Endpoints

#### Authentication (7 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | User login with 2FA verification |
| POST | `/api/auth/verify-login` | Verify 2FA code and get token |
| POST | `/api/auth/logout` | Logout (invalidate token) |
| GET | `/api/auth/verify` | Verify token validity |
| POST | `/api/auth/refresh-token` | Refresh JWT token (24h expiry) |
| POST | `/api/auth/google/login` | Login with Google OAuth 2.0 |

#### Users (5 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users/{user_id}` | Get user profile |
| PUT | `/api/users/{user_id}` | Update profile (age, weight, height) |
| GET | `/api/users/{user_id}/stats` | Get fitness statistics |
| DELETE | `/api/users/{user_id}` | Delete account |
| GET | `/api/users/{user_id}/progress` | Get date-range progress |

#### Goals (5 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/goals` | Create fitness goal |
| GET | `/api/goals/{user_id}` | List user's goals |
| GET | `/api/goals/{goal_id}` | Get goal detail |
| PUT | `/api/goals/{goal_id}` | Update goal |
| DELETE | `/api/goals/{goal_id}` | Delete goal |

#### Exercises (5 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/exercises` | List all exercises (paginated) |
| GET | `/api/exercises/{exercise_id}` | Get exercise detail |
| GET | `/api/exercises/muscle/{muscle_group}` | Filter by muscle group |
| POST | `/api/exercises` | Create exercise (admin) |
| GET | `/api/exercises/difficulty/{level}` | Filter by difficulty |

#### Workouts (10 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/workouts` | Create new workout |
| GET | `/api/workouts/{user_id}` | List user's workouts |
| GET | `/api/workouts/{workout_id}` | Get workout detail |
| POST | `/api/workouts/{id}/exercises` | Add exercise to workout |
| PUT | `/api/workouts/{id}/exercises/{exercise_id}` | Update exercise in workout |
| PUT | `/api/workouts/{workout_id}` | Update/complete workout |
| DELETE | `/api/workouts/{workout_id}` | Delete workout |
| DELETE | `/api/workouts/{id}/exercises/{ex_id}` | Remove exercise from workout |
| GET | `/api/workouts/{user_id}/recent` | Get recent workouts |
| GET | `/api/workouts/{user_id}/by-date/{date}` | Get workouts by date |

#### Meals (5 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/meals` | Log meal with macros |
| GET | `/api/meals/{user_id}` | List meals (paginated) |
| GET | `/api/meals/{user_id}/daily` | Daily nutrition summary |
| PUT | `/api/meals/{meal_id}` | Update meal |
| DELETE | `/api/meals/{meal_id}` | Delete meal |

#### Calendar (3 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/calendar/{user_id}` | Month-view calendar with events |
| POST | `/api/calendar/events` | Create calendar event |
| DELETE | `/api/calendar/events/{event_id}` | Delete calendar event |

#### Programs (3 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/programs` | Create training program |
| GET | `/api/programs/{user_id}` | List user's programs |
| GET | `/api/programs/{program_id}` | Get program with schedule |

#### Dashboard (1 endpoint)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/dashboard/{user_id}` | Comprehensive fitness dashboard |

#### ML (2 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/ml/identify-equipment` | ML equipment identification |
| GET | `/api/ml/predictions/{user_id}` | List ML predictions |

#### Nutrition (2 endpoints)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/nutrition/daily/{user_id}` | Daily nutrition summary |
| GET | `/api/nutrition/weekly/{user_id}` | Weekly nutrition analysis |

#### Health (1 endpoint)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Server health check |

## 🔐 Authentication

The API supports both traditional and OAuth authentication:

### JWT Authentication
```bash
# Register new user
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_fitness",
    "email": "john@example.com",
    "password": "SecurePass123"
  }'

# Login to get 2FA verification
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_fitness",
    "password": "SecurePass123"
  }'

# Verify 2FA code to get token
curl -X POST http://localhost:5000/api/auth/verify-login \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "uuid",
    "verification_code": "123456"
  }'

# Use token in subsequent requests
curl -X GET http://localhost:5000/api/users/{user_id} \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIs..."
```

### Google OAuth 2.0
```bash
# Frontend sends Google ID token (handled automatically by Google Sign-In button)
curl -X POST http://localhost:5000/api/auth/google/login \
  -H "Content-Type: application/json" \
  -d '{
    "credential": "google_id_token_from_signin_button"
  }'

# Returns JWT token directly - no 2FA needed for OAuth
```

**Authentication Features:**
- **JWT Tokens**: HS256 signed, 24-hour expiry
- **2FA via Email**: 6-digit verification codes sent to email
- **Google OAuth 2.0**: One-click sign-in with automatic account creation
- **Password Security**: Bcrypt hashing with 12-round salt
- **Refresh Tokens**: Extend sessions without re-authenticating

## 🗄️ Database Schema

**12 Core Models:**
1. **User** - User accounts with profile data, Google OAuth support
2. **Goal** - Fitness goals with progress tracking
3. **Exercise** - Exercise reference library (50+ pre-loaded)
4. **Workout** - Workout sessions
5. **WorkoutExercise** - Exercise details within workouts
6. **Meal** - Meal logs with nutrition data
7. **MealItem** - Individual food items in meals
8. **FitnessProgram** - Personalized training programs
9. **ProgramWorkout** - Weekly schedule for programs
10. **CalendarEvent** - Calendar entries for planning
11. **MLPrediction** - ML model predictions
12. **EmailVerificationCode** - 2FA verification codes

**Recent Schema Updates:**
- Added `google_id` field to User model for Google OAuth support
- Added `profile_picture` field for storing user profile images
- Added `EmailVerificationCode` model for secure email-based 2FA

**Data Relationships:**
- User → Many Goals, Workouts, Meals, Programs
- Workout → Many WorkoutExercises
- Exercise → Pre-loaded reference data
- Goal → Target tracking with dates
- Meal → Multiple MealItems
- FitnessProgram → Weekly schedule

## ⚙️ Environment Configuration

Create `.env` file in project root:

```env
# Flask Configuration
FLASK_ENV=development
FLASK_APP=app/main.py
FLASK_PORT=5000

# Database
DATABASE_URL=sqlite:///fitness_app.db

# Security
SECRET_KEY=your-secret-key-change-in-production
JWT_SECRET_KEY=your-jwt-secret-key-change-in-production

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:5000

# Email Configuration (for 2FA verification codes)
SMTP_SERVER=smtp.mailersend.net
SMTP_PORT=587
SMTP_USERNAME=your_mailersend_username
SMTP_PASSWORD=your_mailersend_password
SENDER_EMAIL=noreply@yourdomain.com
SENDER_NAME=Fitness Tracker

# Google OAuth 2.0 Configuration
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret
```

**Google OAuth Setup:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing
3. Enable Google+ API and Google Identity Services API
4. Create OAuth 2.0 credentials (Web application)
5. Add Authorized JavaScript origins:
   - `http://localhost:5000`
   - `http://127.0.0.1:5000`
6. Add Authorized redirect URIs:
   - `http://localhost:5000/api/auth/google/callback`
   - `http://localhost:5000/app`
7. Copy Client ID and Client Secret to `.env`

## 📁 Project Structure

```
fitness-api-project/
├── app/
│   ├── __init__.py              # Flask app factory
│   ├── main.py                  # Blueprint registration
│   ├── config.py                # Configuration
│   ├── database.py              # SQLAlchemy setup
│   ├── models.py                # 11 ORM models
│   ├── routes/                  # 11 Blueprint modules
│   │   ├── auth.py              # Authentication
│   │   ├── users.py             # User management
│   │   ├── goals.py             # Goal tracking
│   │   ├── exercises.py         # Exercise reference
│   │   ├── workouts.py          # Workout logging
│   │   ├── meals.py             # Nutrition logging
│   │   ├── calendar.py          # Calendar events
│   │   ├── programs.py          # Training programs
│   │   ├── dashboard.py         # Analytics
│   │   ├── ml.py                # ML predictions
│   │   └── nutrition.py         # Nutrition analytics
│   ├── services/                # Business logic
│   │   ├── auth_service.py      # JWT & bcrypt
│   │   ├── workout_service.py   # Calorie calculations
│   │   ├── nutrition_service.py # Macro tracking
│   │   ├── dashboard_service.py # Analytics
│   │   ├── program_service.py   # Program generation
│   │   └── ml_service.py        # ML operations
│   └── utils/                   # Helper functions
│       ├── constants.py         # Constants
│       ├── validators.py        # Input validation
│       ├── responses.py         # Response formatting
│       └── decorators.py        # Custom decorators
├── scripts/
│   └── seed_exercises.py        # Database seeding
├── tests/
│   ├── conftest.py              # Pytest fixtures
│   ├── test_auth.py             # Auth tests (8 cases)
│   └── test_workouts.py         # Workout tests (7 cases)
├── fitness_app.db               # SQLite database
├── requirements.txt             # Python dependencies
├── .env                         # Environment variables
├── .gitignore                   # Git ignore rules
├── run.py                       # Application entry point
├── config.py                    # Top-level config
└── README.md                    # This file
```

## 🧪 Testing

Comprehensive test suite with 15+ test cases:

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v

# Run specific test class
pytest tests/test_auth.py::TestAuthRegister -v

# Run with detailed output
pytest tests/ -vv --tb=short
```

**Test Coverage:**
- ✅ Authentication (8 test cases)
- ✅ Workouts (7 test cases)
- ✅ Calorie calculations
- ✅ Authorization/ownership verification
- ✅ Error handling

**Fixtures:**
- `test_app`: In-memory SQLite database
- `test_client`: Flask test client
- `sample_user`: Pre-created test user
- `test_user_token`: Valid JWT token
- `auth_headers`: Authorization headers

## 🔑 Key Features

✅ **48 API Endpoints** across 12 modules
✅ **JWT Authentication** with 24-hour tokens
✅ **Google OAuth 2.0** with one-click sign-in
✅ **Email-based 2FA** with 6-digit verification codes
✅ **SQLite Database** with 12 models
✅ **Password Security** with bcrypt (12-round salt)
✅ **Calorie Tracking** with formula-based calculations
✅ **Goal Progress** with percentage tracking
✅ **Calendar Planning** with event management
✅ **Nutrition Analytics** with macro percentages
✅ **ML Integration** with equipment recognition
✅ **Service Layer** with reusable business logic
✅ **Comprehensive Tests** with 15+ test cases
✅ **Error Handling** with meaningful messages
✅ **Pagination Support** on list endpoints
✅ **Input Validation** on all endpoints
✅ **CORS Support** for frontend integration
✅ **Profile Pictures** for Google OAuth users

## 📊 Example API Usage

### Register User
```bash
POST /api/auth/register
{
  "username": "john_fitness",
  "email": "john@example.com",
  "password": "SecurePass123"
}
```

### Create Workout
```bash
POST /api/workouts
Headers: Authorization: Bearer <token>
{
  "workout_type": "strength",
  "notes": "Upper body day"
}
```

### Add Exercise to Workout
```bash
POST /api/workouts/{workout_id}/exercises
{
  "exercise_id": "uuid",
  "sets": 3,
  "reps": 10,
  "weight_used": 185,
  "weight_unit": "lbs"
}
```

### Complete Workout
```bash
PUT /api/workouts/{workout_id}
{
  "status": "completed",
  "notes": "Great session!"
}
```

### Log Meal
```bash
POST /api/meals
{
  "meal_type": "lunch",
  "meal_date": "2026-01-11",
  "total_calories": 650,
  "protein_g": 35,
  "carbs_g": 75,
  "fats_g": 20
}
```

### Get Dashboard
```bash
GET /api/dashboard/{user_id}?period=week
```

## 🛠️ Development

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Seed Database
```bash
python scripts/seed_exercises.py
```

### Run Development Server
```bash
python run.py
```

### Run Tests
```bash
pytest tests/ -v
```

## 📦 Dependencies

- **Flask 3.0.0** - Web framework
- **Flask-CORS 4.0.0** - CORS support
- **Flask-JWT-Extended 4.5.3** - JWT authentication
- **SQLAlchemy 2.0.23** - ORM
- **python-dotenv** - Environment variables
- **bcrypt** - Password hashing
- **google-auth** - Google OAuth 2.0 verification
- **google-auth-oauthlib** - Google OAuth library
- **google-auth-httplib2** - Google OAuth HTTP client
- **pytest** - Testing framework
- **pytest-cov** - Code coverage
- **requests** - HTTP client for OAuth token exchange

## 🔒 Security Features

- ✅ JWT token-based authentication
- ✅ Bcrypt password hashing (12 rounds)
- ✅ User ownership verification on protected endpoints
- ✅ Input validation on all routes
- ✅ SQL injection prevention (ORM)
- ✅ CORS configuration for safe frontend requests
- ✅ Secure error messages without exposing internals

## 📈 Performance

- ✅ Indexed database queries
- ✅ Pagination for large datasets
- ✅ Efficient relationship loading
- ✅ Caching-ready architecture
- ✅ Connection pooling via SQLAlchemy

## 🚀 Deployment

### Production Checklist
- [ ] Set `FLASK_ENV=production`
- [ ] Use strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Configure database for production (PostgreSQL recommended)
- [ ] Enable HTTPS
- [ ] Set proper CORS origins
- [ ] Configure file upload limits
- [ ] Enable request logging
- [ ] Set up monitoring/alerting

### Example Production Commands
```bash
# Install production dependencies
pip install -r requirements.txt gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 "app:create_app()"
```

## 📝 API Response Format

All responses follow a standard JSON format:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": {
    "user_id": "uuid",
    "username": "john_fitness"
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "validation_error",
  "message": "Username must be 3-20 characters",
  "code": "INVALID_USERNAME"
}
```

**Paginated Response:**
```json
{
  "success": true,
  "message": "Success",
  "data": [...],
  "total": 50,
  "page": 1,
  "per_page": 10
}
```

## 🤝 Contributing

For development contributions:

1. Create a feature branch
2. Make your changes
3. Run tests: `pytest tests/ -v`
4. Ensure coverage > 80%
5. Commit with clear messages
6. Create pull request

## 📄 License

This project is provided as-is for educational and commercial use.

## 🆘 Troubleshooting

### Database Issues
```bash
# Reset database
rm fitness_app.db
python scripts/seed_exercises.py

# Check database status
sqlite3 fitness_app.db ".tables"
```

### Port Already in Use
```bash
# Use different port
FLASK_PORT=5001 python run.py
```

### Import Errors
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

### Test Failures
```bash
# Run with verbose output
pytest tests/ -vv --tb=long

# Run single test
pytest tests/test_auth.py::TestAuthRegister::test_register_success -vv
```

## 📞 Support

For issues, questions, or suggestions, check:
- Test files in `tests/` directory
- Service examples in `app/services/`
- Route implementations in `app/routes/`

## 🎓 Learning Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/)
- [JWT Authentication](https://tools.ietf.org/html/rfc7519)
- [RESTful API Design](https://restfulapi.net/)
- [Pytest Documentation](https://docs.pytest.org/)

---

**API Version**: 1.0.1  
**Last Updated**: January 15, 2026  
**Status**: Production-Ready with OAuth 2.0 ✅

## 📝 Recent Updates (January 2026)

- ✅ Added Google OAuth 2.0 authentication
- ✅ Implemented email-based 2FA for login security
- ✅ Extended User model with `google_id` and `profile_picture` fields
- ✅ Created `/api/auth/google/login` endpoint
- ✅ Integrated Google Sign-In button in frontend
- ✅ Added email verification service with SMTP support
- ✅ Fixed frontend form visibility (login/register/verify separation)
- ✅ Updated meal item positioning in meal log (z-index fix)
- ✅ Removed unnecessary test files and cleaned up project structure
- ✅ Added venv311 to .gitignore
- ✅ Installed and verified all Google authentication dependencies
