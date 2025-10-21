# Fix redirect_uri_mismatch Error - Step by Step

## 🔍 Step 1: Check What Redirect URIs Your App is Actually Sending

### Test the Debug Endpoints

1. **Check Custom OAuth Flow Redirect URI:**
   ```bash
   curl https://lms.myanmarlink.online/api/auth/google/url/
   ```
   This will show you exactly what redirect URI is being sent to Google.

2. **Check Allauth Redirect URI:**
   ```bash
   curl https://lms.myanmarlink.online/api/debug/google-redirect/
   ```
   This will show you what allauth is generating.

## 🔧 Step 2: Common Redirect URI Issues

### Issue 1: Missing Trailing Slash
**Wrong:** `https://lms.myanmarlink.online/api/web-auth/google/login/callback`
**Correct:** `https://lms.myanmarlink.online/api/web-auth/google/login/callback/`

### Issue 2: HTTP vs HTTPS
**Wrong:** `http://lms.myanmarlink.online/api/web-auth/google/login/callback/`
**Correct:** `https://lms.myanmarlink.online/api/web-auth/google/login/callback/`

### Issue 3: Wrong Path
**Wrong:** `https://lms.myanmarlink.online/auth/google/callback/`
**Correct:** `https://lms.myanmarlink.online/api/web-auth/google/login/callback/`

## 🛠️ Step 3: Fix Google Console

1. **Go to Google Cloud Console**: https://console.cloud.google.com/
2. **Navigate to**: APIs & Services → Credentials
3. **Click on your OAuth 2.0 Client ID**
4. **In "Authorized redirect URIs" section, add ALL of these:**

```
https://lms.myanmarlink.online/api/web-auth/google/login/callback/
https://lms.myanmarlink.online/auth/google/callback
https://lms.myanmarlink.online/accounts/google/login/callback/
```

5. **Save the changes**

## 🧪 Step 4: Test Each Method

### Test 1: Custom OAuth Flow
```bash
# Get the auth URL
curl https://lms.myanmarlink.online/api/auth/google/url/

# Copy the auth_url from response and visit it in browser
# Complete the OAuth flow
# Check if you get redirected back successfully
```

### Test 2: Allauth Web Flow
```bash
# Visit this URL in browser
https://lms.myanmarlink.online/api/web-auth/google/login/
```

### Test 3: Check Debug Info
```bash
# Check what redirect URIs are being generated
curl https://lms.myanmarlink.online/api/debug/google-redirect/
```

## 🐛 Step 5: Common Solutions

### Solution 1: Update Django Settings
If the debug shows wrong redirect URIs, update your settings:

```python
# In settings.py
if not DEBUG:
    SITE_URL = "https://lms.myanmarlink.online"
    # Force HTTPS
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
```

### Solution 2: Update Nginx Headers
Make sure your nginx is passing the correct headers:

```nginx
location / {
    proxy_pass http://web:8000;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;  # This is important!
    proxy_set_header X-Forwarded-Host $host;
}
```

### Solution 3: Check Environment Variables
Make sure these are set in production:

```bash
GOOGLE_CLIENT_ID=your-actual-client-id
GOOGLE_CLIENT_SECRET=your-actual-client-secret
DJANGO_DEBUG=0
```

## 🔍 Step 6: Debug Commands

### Check What's Actually Being Sent
```bash
# Check the exact redirect URI being generated
curl -s https://lms.myanmarlink.online/api/auth/google/url/ | jq '.redirect_uri_used'

# Check allauth redirect URI
curl -s https://lms.myanmarlink.online/api/debug/google-redirect/ | jq '.allauth_redirect_uri'
```

### Check Google Console
1. Go to Google Console → Credentials
2. Click on your OAuth client
3. Check the "Authorized redirect URIs" section
4. Make sure it matches exactly what your app is sending

## ✅ Step 7: Verification

After making changes:

1. **Wait 5-10 minutes** for Google Console changes to propagate
2. **Test the OAuth flow**:
   - Visit: `https://lms.myanmarlink.online/api/web-auth/google/login/`
   - Complete Google OAuth
   - Check if you're redirected back successfully
3. **Check for errors** in browser console or server logs

## 🚨 If Still Not Working

### Check These Common Issues:

1. **Caching**: Clear browser cache and try incognito mode
2. **Google Console**: Make sure you're editing the correct OAuth client
3. **Domain**: Make sure `lms.myanmarlink.online` is exactly correct (no typos)
4. **HTTPS**: Make sure your site is accessible via HTTPS
5. **Environment**: Make sure production environment variables are set

### Debug Logs:
```bash
# Check Django logs
docker-compose logs web

# Check nginx logs
docker-compose logs nginx
```

The key is to match EXACTLY what your app sends with what's in Google Console! 🎯
