# Google Authentication Testing Guide

## 🧪 Testing All Google Auth Endpoints

### 1. Google Register (Create Account with Google Email + Password)

**Endpoint:** `POST /api/google/register/`

**Correct curl command:**
```bash
curl -X POST https://lms.myanmarlink.online/api/google/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@gmail.com",
    "password": "testpassword123",
    "first_name": "Test",
    "last_name": "User"
  }'
```

**Expected Response (201 Created):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user_id": 123,
  "email": "testuser@gmail.com",
  "first_name": "Test",
  "last_name": "User",
  "is_new_user": true,
  "message": "Account created successfully"
}
```

**Test with minimal data:**
```bash
curl -X POST https://lms.myanmarlink.online/api/google/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "minimal@gmail.com",
    "password": "password123"
  }'
```

### 2. Google Sign-In (Login or Auto-Register with Google ID Token)

**Endpoint:** `POST /api/google/signin/`

**Note:** This requires a real Google ID token. For testing, you can use a mock token structure.

```bash
curl -X POST https://lms.myanmarlink.online/api/google/signin/ \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "mock_google_id_token",
    "email": "googletest@gmail.com",
    "name": "Google Test User",
    "first_name": "Google",
    "last_name": "Test"
  }'
```

**Expected Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user_id": 124,
  "email": "googletest@gmail.com",
  "first_name": "Google",
  "last_name": "Test",
  "is_new_user": true,
  "message": "Account created successfully with Google"
}
```

### 3. Google Connect (Link Existing Account to Google)

**Endpoint:** `POST /api/google/connect/`

**Prerequisites:** 
- User must already exist (created via register endpoint)
- Need a Google ID token

```bash
curl -X POST https://lms.myanmarlink.online/api/google/connect/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@gmail.com",
    "password": "testpassword123",
    "id_token": "mock_google_id_token"
  }'
```

**Expected Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user_id": 123,
  "email": "testuser@gmail.com",
  "first_name": "Test",
  "last_name": "User",
  "is_new_user": false,
  "message": "Account successfully connected to Google"
}
```

### 4. Google Status (Check if User has Google Connected)

**Endpoint:** `GET /api/google/status/`

**Prerequisites:** Must be authenticated (need access token from previous calls)

```bash
# First get an access token from register/signin
ACCESS_TOKEN="your_access_token_here"

curl -X GET https://lms.myanmarlink.online/api/google/status/ \
  -H "Authorization: Bearer $ACCESS_TOKEN"
```

**Expected Response (200 OK):**
```json
{
  "has_google_connected": false,
  "email": "testuser@gmail.com",
  "can_connect_google": true
}
```

## 🔍 Testing Error Cases

### Test 1: Duplicate Email Registration
```bash
# First registration
curl -X POST https://lms.myanmarlink.online/api/google/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "duplicate@gmail.com", "password": "password123"}'

# Try to register again with same email
curl -X POST https://lms.myanmarlink.online/api/google/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "duplicate@gmail.com", "password": "password456"}'
```

**Expected Error Response (400 Bad Request):**
```json
{
  "detail": "Account with this email already exists"
}
```

### Test 2: Missing Required Fields
```bash
curl -X POST https://lms.myanmarlink.online/api/google/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "incomplete@gmail.com"}'
```

**Expected Error Response (400 Bad Request):**
```json
{
  "detail": "Email and password are required"
}
```

### Test 3: Invalid Google Connect (Wrong Password)
```bash
curl -X POST https://lms.myanmarlink.online/api/google/connect/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@gmail.com",
    "password": "wrongpassword",
    "id_token": "mock_google_id_token"
  }'
```

**Expected Error Response (401 Unauthorized):**
```json
{
  "detail": "Invalid email or password"
}
```

## 🚀 Complete Test Sequence

### Step 1: Test Google Register
```bash
echo "=== Testing Google Register ==="
curl -X POST https://lms.myanmarlink.online/api/google/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@gmail.com",
    "password": "testpassword123",
    "first_name": "Test",
    "last_name": "User"
  }' | jq
```

### Step 2: Test Google Sign-In (Auto-register)
```bash
echo "=== Testing Google Sign-In ==="
curl -X POST https://lms.myanmarlink.online/api/google/signin/ \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "mock_token",
    "email": "googletest@gmail.com",
    "name": "Google Test"
  }' | jq
```

### Step 3: Test Google Connect
```bash
echo "=== Testing Google Connect ==="
curl -X POST https://lms.myanmarlink.online/api/google/connect/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@gmail.com",
    "password": "testpassword123",
    "id_token": "mock_token"
  }' | jq
```

### Step 4: Test Status Check
```bash
echo "=== Testing Status Check ==="
# Extract access token from previous response
ACCESS_TOKEN="eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."

curl -X GET https://lms.myanmarlink.online/api/google/status/ \
  -H "Authorization: Bearer $ACCESS_TOKEN" | jq
```

## 🐛 Debugging Tips

### Check if endpoints are accessible:
```bash
# Test if the server is running
curl -I https://lms.myanmarlink.online/api/google/register/

# Should return: HTTP/1.1 405 Method Not Allowed (expected for GET on POST endpoint)
```

### Check server logs:
```bash
# If using Docker
docker-compose logs web

# Look for any error messages
```

### Test with verbose curl:
```bash
curl -v -X POST https://lms.myanmarlink.online/api/google/register/ \
  -H "Content-Type: application/json" \
  -d '{"email": "test@gmail.com", "password": "test123"}'
```

## ✅ Expected Results

1. **Google Register** should create new users and return JWT tokens
2. **Google Sign-In** should login existing users or create new ones
3. **Google Connect** should link existing accounts to Google
4. **Google Status** should show connection status for authenticated users

All endpoints should return proper JSON responses with appropriate HTTP status codes! 🎯
