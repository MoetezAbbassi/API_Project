# Insomnia Testing Guide - Fitness API

## Quick Setup

### 1. Import Collection
1. Open Insomnia
2. Go to **File** → **Import** → **From File**
3. Select `insomnia_fitness_api.json`
4. Collection will appear in your workspace

### 2. Set Base Environment Variables

These are the environment variables you need to set in Insomnia's **Base Environment**:

```json
{
  "base_url": "http://localhost:5000",
  "token": "",
  "user_id": ""
}
```

**Steps to add:**
1. Click **Manage Environments** (gear icon)
2. Click **Base Environment**
3. Add the following variables:

| Variable | Value | Description |
|----------|-------|-------------|
| `base_url` | `http://localhost:5000` | API base URL |
| `token` | *(leave empty)* | JWT token (fill after login) |
| `user_id` | *(leave empty)* | User ID (fill after login) |

## Testing Workflow

### Step 1: Register User
**Request:** `🔐 Authentication` → `Register User`

**Request Body:**
```json
{
  "username": "testuser",
  "email": "test@example.com",
  "password": "Test1234!"
}
```

**Response** will contain `user_id` and `email`

---

### Step 2: Login (Step 1)
**Request:** `🔐 Authentication` → `Login (Step 1)`

**Request Body:**
```json
{
  "username": "testuser",
  "password": "Test1234!"
}
```

**Response** will contain `user_id`

**⚠️ Copy the `user_id` from response and paste into Insomnia environment variable `user_id`**

---

### Step 3: Verify Login (Step 2)
**Request:** `🔐 Authentication` → `Verify Login (Step 2)`

**Note:** Check your email for the 6-digit verification code (in development mode, check server logs)

**Request Body:**
```json
{
  "user_id": "{{ _.user_id }}",
  "code": "123456"
}
```

**Response** will contain JWT `access_token`

**⚠️ Copy the `access_token` from response and paste into Insomnia environment variable `token`**

---

### Step 4: Test Protected Endpoints
Once you have `token` set, all protected endpoints will work automatically using `{{ _.token }}`

**Test these endpoints in order:**
1. `👤 Users` → `Get User by ID` (uses `{{ _.user_id }}`)
2. `📊 Dashboard` → `Get Dashboard Summary` (uses `{{ _.user_id }}`)
3. `🍽️ Meals` → `Get My Meals`
4. `🏋️ Workouts` → `Get All Workouts`
5. `💪 Exercises` → `Get All Exercises` (no auth required)

---

## Quick Reference Variables

When copying from responses, update these in Insomnia:

| From Response | → Set as Environment Variable |
|---------------|-------------------------------|
| `user_id` | `user_id` |
| `access_token` | `token` |

---

## Example: Complete Login Flow

**Terminal/Console Testing (using curl):**

```bash
# 1. Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","email":"test@example.com","password":"Test1234!"}'

# 2. Login
curl -X POST http://localhost:5000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"testuser","password":"Test1234!"}'

# 3. Verify (replace USER_ID and CODE)
curl -X POST http://localhost:5000/api/auth/verify-login \
  -H "Content-Type: application/json" \
  -d '{"user_id":"USER_ID_HERE","code":"123456"}'

# 4. Use token for protected requests
curl -X GET http://localhost:5000/api/dashboard/USER_ID_HERE/summary \
  -H "Authorization: Bearer TOKEN_HERE"
```

---

## Folder Structure in Insomnia

```
Fitness API
├── 🔐 Authentication (10 endpoints)
│   ├── Register User
│   ├── Login (Step 1)
│   ├── Verify Login (Step 2)
│   ├── Google OAuth Login
│   ├── Get Profile
│   └── ... (more auth endpoints)
├── 👤 Users (6 endpoints)
│   ├── Get User by ID
│   ├── Update User
│   └── ... (more user endpoints)
├── 💪 Exercises (6 endpoints)
│   ├── Get All Exercises
│   ├── Get Exercise by ID
│   └── ... (more exercise endpoints)
├── 🏋️ Workouts (6 endpoints)
│   ├── Get All Workouts
│   ├── Create Workout
│   └── ... (more workout endpoints)
├── 🍽️ Meals (6 endpoints)
│   ├── Get My Meals
│   ├── Create Meal
│   └── ... (more meal endpoints)
├── 📊 Dashboard (2 endpoints)
│   ├── Get Dashboard Summary
│   └── Get Calories Graph
├── 🤖 ML Scanner (4 endpoints)
│   ├── Identify Equipment
│   ├── Equipment List
│   └── ... (more ML endpoints)
├── 🎯 Goals (4 endpoints)
│   ├── Get All Goals
│   ├── Create Goal
│   └── ... (more goal endpoints)
├── 🥗 Nutrition (2 endpoints)
│   ├── Get Daily Nutrition
│   └── Get Weekly Nutrition
└── ❤️ Health Check (1 endpoint)
    └── Health Check
```

---

## Notes

- All timestamps are in UTC
- JWT tokens expire after a period (check `.env` for `JWT_ACCESS_TOKEN_EXPIRE`)
- Use `{{ _.base_url }}` in any request to reference the base URL
- Use `{{ _.token }}` in `Authorization` header for protected routes
- Use `{{ _.user_id }}` in URLs that require user ID

---

## Troubleshooting

**"Invalid token" error?**
- Re-login and update the `token` environment variable

**"User not found" error?**
- Make sure `user_id` is set correctly in environment variables
- Use the exact `user_id` from login response

**"CORS error"?**
- Backend is running on `http://localhost:5000`
- Check server is started: `python run.py`

**Can't find verification code?**
- In development mode, check Flask server console output
- Or set `MAIL_SEND_IMMEDIATELY=True` in `.env` to send actual emails

---

## All 47 Endpoints Ready to Test! 🎉

Start with Register → Login → Verify, then test any endpoint in the collection.
