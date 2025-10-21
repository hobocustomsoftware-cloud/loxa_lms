# 🔧 Fix Third-Party Login Failure

## 🚨 **Root Cause**
The "Third-Party Login Failure" error is caused by:
1. **HTTPS/HTTP mismatch** - Google OAuth requires HTTPS in production
2. **Incorrect redirect URI** - Google Console doesn't have the right redirect URI
3. **Missing environment variables** - Google OAuth credentials not set

## ✅ **Step-by-Step Fix**

### **Step 1: Update Google Console Redirect URIs**

Go to [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials → Your OAuth Client

**Add these EXACT redirect URIs:**
```
https://lms.myanmarlink.online/api/web-auth/google/login/callback/
https://lms.myanmarlink.online/auth/google/callback
```

**Important:** Use `https://` not `http://`

### **Step 2: Verify Environment Variables**

Make sure these are set in your production environment:
```bash
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
DJANGO_DEBUG=0
```

### **Step 3: Restart Services**

```bash
docker compose restart web
```

### **Step 4: Test the Fix**

```bash
# Test Google Web Login
curl -I https://lms.myanmarlink.online/api/web-auth/google/login/

# Should now redirect to HTTPS Google OAuth
```

## 🔍 **Debug Commands**

### **Check Current Redirect URI:**
```bash
curl -I https://lms.myanmarlink.online/api/web-auth/google/login/ 2>&1 | grep -i location
```

### **Check Environment Variables:**
```bash
docker compose exec web python manage.py shell -c "
from django.conf import settings
print('Google Client ID:', settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY)
print('Debug Mode:', settings.DEBUG)
print('Site URL:', getattr(settings, 'SITE_URL', 'Not set'))
"
```

### **Check Server Logs:**
```bash
docker compose logs web --tail=50
```

## 🎯 **Expected Results After Fix**

### **Before Fix:**
```
Location: https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=http%3A%2F%2Flms.myanmarlink.online%2Fapi%2Fweb-auth%2Fgoogle%2Flogin%2Fcallback%2F&...
```
❌ **Problem:** `http://` in redirect URI

### **After Fix:**
```
Location: https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=https%3A%2F%2Flms.myanmarlink.online%2Fapi%2Fweb-auth%2Fgoogle%2Flogin%2Fcallback%2F&...
```
✅ **Fixed:** `https://` in redirect URI

## 🚀 **Complete Test Sequence**

### **1. Test Google Web Login:**
```bash
curl -I https://lms.myanmarlink.online/api/web-auth/google/login/
```

### **2. Test Google API Login:**
```bash
curl -X POST https://lms.myanmarlink.online/api/auth/google/ \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "mock_token",
    "email": "test@gmail.com",
    "first_name": "Test",
    "last_name": "User"
  }'
```

### **3. Test in Browser:**
Visit: `https://lms.myanmarlink.online/api/web-auth/google/login/`

Should redirect to Google OAuth without errors.

## 🔧 **Additional Fixes Applied**

1. **Updated Django settings** to force HTTPS in production
2. **Fixed redirect URI generation** to use HTTPS
3. **Added proper security headers** for production

## 📋 **Checklist**

- [ ] Google Console has correct HTTPS redirect URIs
- [ ] Environment variables are set correctly
- [ ] Services restarted after changes
- [ ] Test commands show HTTPS redirect URIs
- [ ] Browser test works without errors

## 🎯 **Main Action Required**

**Add this redirect URI to Google Console:**
```
https://lms.myanmarlink.online/api/web-auth/google/login/callback/
```

The third-party login failure should be fixed after updating Google Console! 🚀
