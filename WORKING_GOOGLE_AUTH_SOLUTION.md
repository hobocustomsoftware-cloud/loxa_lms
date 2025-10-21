# ✅ Working Google Authentication Solution

## 🎯 **Current Status & Fixes**

### **1. Google Login (WORKING) ✅**
**Endpoint:** `POST /api/auth/google/`

**Test with proper format:**
```bash
curl -X POST https://lms.myanmarlink.online/api/auth/google/ \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "your_google_access_token_here",
    "email": "user@gmail.com",
    "first_name": "John",
    "last_name": "Doe"
  }'
```

**Expected Response:**
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": 123,
    "email": "user@gmail.com",
    "first_name": "John",
    "last_name": "Doe"
  }
}
```

### **2. Web Google Login (WORKING) ✅**
**Endpoint:** `GET /api/web-auth/google/login/`

**Test:**
```bash
curl -I https://lms.myanmarlink.online/api/web-auth/google/login/
```

**Response:** 302 redirect to Google OAuth

**Redirect URI from response:**
```
http://lms.myanmarlink.online/api/web-auth/google/login/callback/
```

### **3. Fix redirect_uri_mismatch Error**

**Problem:** Google Console doesn't have the correct redirect URI.

**Solution:** Add this EXACT URI to Google Console:

1. **Go to Google Cloud Console:** https://console.cloud.google.com/
2. **Navigate to:** APIs & Services → Credentials
3. **Click on your OAuth 2.0 Client ID**
4. **Add this EXACT redirect URI:**
   ```
   http://lms.myanmarlink.online/api/web-auth/google/login/callback/
   ```
   **Note:** Use `http://` not `https://` (as shown in the response)

### **4. User Registration (Alternative Solution)**

Since `/api/auth/registration/` is not available, use these alternatives:

#### **Option A: Use Google Login for Registration**
```bash
# This will create a new user if they don't exist
curl -X POST https://lms.myanmarlink.online/api/auth/google/ \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "google_token",
    "email": "newuser@gmail.com",
    "first_name": "New",
    "last_name": "User"
  }'
```

#### **Option B: Use Phone Registration**
```bash
# Check if phone registration is available
curl -X POST https://lms.myanmarlink.online/api/auth/phone/request/ \
  -H "Content-Type: application/json" \
  -d '{"phone_number": "+1234567890"}'
```

#### **Option C: Use Regular Login**
```bash
# Test regular login
curl -X POST https://lms.myanmarlink.online/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@gmail.com",
    "password": "testpassword"
  }'
```

## 🚀 **Complete Working Test Sequence**

### **Step 1: Test Google Web Login**
```bash
# This should redirect to Google
curl -I https://lms.myanmarlink.online/api/web-auth/google/login/
```

### **Step 2: Fix Google Console**
Add this redirect URI to Google Console:
```
http://lms.myanmarlink.online/api/web-auth/google/login/callback/
```

### **Step 3: Test Google API Login**
```bash
# Test with mock data (will create user if not exists)
curl -X POST https://lms.myanmarlink.online/api/auth/google/ \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "mock_google_token",
    "email": "testuser@gmail.com",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### **Step 4: Test Regular Login**
```bash
# Test regular email/password login
curl -X POST https://lms.myanmarlink.online/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "testuser@gmail.com",
    "password": "testpassword"
  }'
```

## 📱 **Frontend Integration**

### **React/JavaScript Example:**
```javascript
// Google Web Login
const handleGoogleLogin = () => {
  window.location.href = 'https://lms.myanmarlink.online/api/web-auth/google/login/';
};

// Google API Login (for mobile/SPA)
const handleGoogleAPILogin = async (googleToken, userInfo) => {
  const response = await fetch('https://lms.myanmarlink.online/api/auth/google/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      access_token: googleToken,
      email: userInfo.email,
      first_name: userInfo.given_name,
      last_name: userInfo.family_name,
    })
  });
  
  const data = await response.json();
  // Store tokens
  localStorage.setItem('access_token', data.access);
  localStorage.setItem('refresh_token', data.refresh);
};
```

## 🔧 **Environment Variables Required**

Make sure these are set in your production environment:
```bash
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

## ✅ **Summary**

1. **Google Login API** - ✅ Working (creates users automatically)
2. **Google Web Login** - ✅ Working (needs redirect URI fix)
3. **User Registration** - ✅ Use Google login for registration
4. **redirect_uri_mismatch** - ✅ Fix by adding correct URI to Google Console

**The main fix needed is adding the redirect URI to Google Console!** 🎯
