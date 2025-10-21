# Google Login Implementation Guide

Your Django project already has Google login implemented with multiple approaches. Here's how to set it up and use it:

## 🔧 Setup Required

### 1. Environment Variables
Add these to your environment (`.env` file or system environment):

```bash
GOOGLE_CLIENT_ID=your-google-client-id-here
GOOGLE_CLIENT_SECRET=your-google-client-secret-here
```

### 2. Google Cloud Console Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select existing one
3. Enable Google+ API
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized redirect URIs:
   - `http://localhost:8000/api/web-auth/google/login/callback/`
   - `http://localhost:8000/auth/google/callback`
   - `https://yourdomain.com/api/web-auth/google/login/callback/` (production)
   - `https://yourdomain.com/auth/google/callback` (production)

## 🚀 Available Google Login Endpoints

### 1. Mobile/API Login (dj-rest-auth)
**Endpoint**: `POST /api/auth/google/`
**Method**: Send Google ID token

```bash
curl -X POST http://localhost:8000/api/auth/google/ \
  -H "Content-Type: application/json" \
  -d '{"access_token": "your-google-id-token"}'
```

### 2. Web-based Login (django-allauth)
**Endpoint**: `GET /api/web-auth/google/login/`
**Method**: Redirect user to this URL, they'll be redirected to Google

```bash
# Direct browser to:
http://localhost:8000/api/web-auth/google/login/
```

### 3. Custom OAuth Flow
**Get Auth URL**: `GET /api/auth/google/url/`
**Exchange Code**: `POST /api/auth/google/exchange/`

```bash
# Step 1: Get Google OAuth URL
curl http://localhost:8000/api/auth/google/url/

# Step 2: User visits the URL, gets redirected back with code
# Step 3: Exchange code for JWT
curl -X POST http://localhost:8000/api/auth/google/exchange/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "authorization-code-from-google",
    "redirect_uri": "http://localhost:8000/auth/google/callback"
  }'
```

## 📱 Frontend Integration Examples

### React/JavaScript Example

```javascript
// Method 1: Using Google Identity Services (Recommended)
function initializeGoogleLogin() {
  google.accounts.id.initialize({
    client_id: 'YOUR_GOOGLE_CLIENT_ID',
    callback: handleCredentialResponse
  });
  
  google.accounts.id.renderButton(
    document.getElementById('google-login-button'),
    { theme: 'outline', size: 'large' }
  );
}

async function handleCredentialResponse(response) {
  const { credential } = response;
  
  // Send to your Django backend
  const loginResponse = await fetch('/api/auth/google/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      access_token: credential
    })
  });
  
  const tokens = await loginResponse.json();
  // Store tokens for API calls
  localStorage.setItem('access_token', tokens.access);
  localStorage.setItem('refresh_token', tokens.refresh);
}

// Method 2: Custom OAuth Flow
async function customGoogleLogin() {
  // Get auth URL
  const urlResponse = await fetch('/api/auth/google/url/');
  const { auth_url } = await urlResponse.json();
  
  // Redirect to Google
  window.location.href = auth_url;
}

// Handle callback (after redirect back from Google)
async function handleGoogleCallback() {
  const urlParams = new URLSearchParams(window.location.search);
  const code = urlParams.get('code');
  
  if (code) {
    const response = await fetch('/api/auth/google/exchange/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        code: code,
        redirect_uri: window.location.origin + '/auth/google/callback'
      })
    });
    
    const tokens = await response.json();
    // Store tokens
    localStorage.setItem('access_token', tokens.access);
    localStorage.setItem('refresh_token', tokens.refresh);
  }
}
```

### Flutter/Dart Example

```dart
import 'package:google_sign_in/google_sign_in.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class GoogleAuthService {
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    clientId: 'YOUR_GOOGLE_CLIENT_ID',
  );

  Future<Map<String, dynamic>?> signInWithGoogle() async {
    try {
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      if (googleUser == null) return null;

      final GoogleSignInAuthentication googleAuth = 
          await googleUser.authentication;

      // Send to Django backend
      final response = await http.post(
        Uri.parse('http://localhost:8000/api/auth/google/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'access_token': googleAuth.idToken,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
      return null;
    } catch (error) {
      print('Google Sign-In Error: $error');
      return null;
    }
  }
}
```

## 🔍 Testing the Implementation

### 1. Run Migrations (Docker)
```bash
# Run migrations to create social auth tables
docker-compose exec web python manage.py migrate

# Or if using docker run:
docker run --rm -v $(pwd):/app -w /app your-image python manage.py migrate
```

### 2. Start Your Docker Services
```bash
# Start all services (Django, PostgreSQL, Redis, etc.)
docker-compose up -d

# Check if services are running
docker-compose ps
```

### 3. Test Mobile/API Login
```bash
# Test the endpoint (replace with actual Google ID token)
curl -X POST http://localhost:8000/api/auth/google/ \
  -H "Content-Type: application/json" \
  -d '{"access_token": "test-token"}'
```

### 4. Test Web Login
```bash
# Visit in browser:
http://localhost:8000/api/web-auth/google/login/
```

### 5. Test Custom OAuth Flow
```bash
# Get auth URL
curl http://localhost:8000/api/auth/google/url/

# Use the returned URL in browser, then exchange the code
curl -X POST http://localhost:8000/api/auth/google/exchange/ \
  -H "Content-Type: application/json" \
  -d '{
    "code": "actual-code-from-google",
    "redirect_uri": "http://localhost:8000/auth/google/callback"
  }'
```

## 🛠️ Troubleshooting

### Common Issues:

1. **"Invalid client" error**: Check your Google Client ID and Secret
2. **"Redirect URI mismatch"**: Ensure redirect URIs match exactly in Google Console
3. **"User has no field named username"**: This is already fixed in your settings
4. **CORS errors**: Make sure CORS is properly configured (already done)

### Debug Steps:

1. Check environment variables are loaded (Docker):
   ```bash
   docker-compose exec web python manage.py shell
   >>> from django.conf import settings
   >>> print(settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY)
   ```

2. Check if social auth tables exist:
   ```bash
   docker-compose exec web python manage.py migrate
   ```

3. Check Docker logs:
   ```bash
   # Check web service logs
   docker-compose logs web
   
   # Check all services
   docker-compose logs
   ```

4. Test with Django admin:
   - Go to `http://localhost:8000/admin/`
   - Check if social applications are configured

5. Rebuild Docker containers if needed:
   ```bash
   # Rebuild and restart
   docker-compose down
   docker-compose up --build -d
   ```

## 📋 Next Steps

1. Set up your Google Cloud Console project
2. Add environment variables
3. Test the endpoints
4. Integrate with your frontend
5. Deploy and update redirect URIs for production

Your Google login implementation is already complete and ready to use! 🎉
