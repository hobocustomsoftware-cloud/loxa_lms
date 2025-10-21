# ✅ Correct Google Authentication Endpoints

## 🎯 **Current Status Analysis**

Based on your test results:

### **✅ WORKING:**
1. **Google Web Login** - `GET /api/web-auth/google/login/`
   - Returns 302 redirect to Google OAuth
   - **Issue:** Redirect URI uses `http://` instead of `https://`

### **❌ NOT WORKING:**
1. **Google API Login** - `POST /api/auth/google/`
   - Expects registration fields (username, email, password1, password2)
   - This is NOT a Google OAuth endpoint

## 🔧 **SOLUTIONS**

### **1. Fix Google Web Login (redirect_uri_mismatch)**

**Problem:** Redirect URI uses `http://` instead of `https://`

**Solution:** Add this EXACT URI to Google Console:
```
http://lms.myanmarlink.online/api/web-auth/google/login/callback/
```

**Steps:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. APIs & Services → Credentials → Your OAuth Client
3. Add redirect URI: `http://lms.myanmarlink.online/api/web-auth/google/login/callback/`

### **2. Use Correct Google OAuth Endpoint**

The `/api/auth/google/` endpoint is for registration, not Google OAuth. 

**For Google OAuth, use:**
```bash
# This is the correct way to test Google OAuth
curl -I https://lms.myanmarlink.online/api/web-auth/google/login/
```

### **3. Test Complete Flow**

#### **Step 1: Test Google Web Login**
```bash
curl -I https://lms.myanmarlink.online/api/web-auth/google/login/
```
**Expected:** 302 redirect to Google OAuth

#### **Step 2: Test in Browser**
1. Visit: `https://lms.myanmarlink.online/api/web-auth/google/login/`
2. Should redirect to Google OAuth
3. Complete Google login
4. Should redirect back to your site

#### **Step 3: Test Regular Login (Alternative)**
```bash
curl -X POST https://lms.myanmarlink.online/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@gmail.com",
    "password": "testpassword"
  }'
```

## 🎯 **Working Test Commands**

### **1. Google Web Login (Primary Method)**
```bash
# Test redirect
curl -I https://lms.myanmarlink.online/api/web-auth/google/login/

# Test in browser
# Visit: https://lms.myanmarlink.online/api/web-auth/google/login/
```

### **2. Regular Login (Alternative)**
```bash
curl -X POST https://lms.myanmarlink.online/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@gmail.com",
    "password": "password123"
  }'
```

### **3. Check Available Endpoints**
```bash
# Check what auth endpoints are available
curl -X GET https://lms.myanmarlink.online/api/auth/ -H "Accept: application/json"
```

## 📋 **Summary**

1. **Google Web Login** - ✅ Working (needs Google Console redirect URI)
2. **Google API Login** - ❌ Not available (use web login instead)
3. **Regular Login** - ✅ Available as alternative

**Main Action:** Add redirect URI to Google Console to fix the third-party login failure! 🚀
