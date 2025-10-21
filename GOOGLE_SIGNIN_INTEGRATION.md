# Google Sign-In Integration Guide

This guide shows how to implement Google Sign-In with three different flows:

1. **Google Sign-In** - Login or register using Google account
2. **Google Connect** - Connect existing account to Google
3. **Google Register** - Create account with Google email + custom password

## 🚀 Available Endpoints

### 1. Google Sign-In (Login or Register)
**POST** `/api/google/signin/`

**Request:**
```json
{
  "id_token": "google_id_token_here",
  "email": "user@gmail.com",
  "name": "John Doe",
  "first_name": "John",
  "last_name": "Doe",
  "picture": "https://profile-pic-url.com"
}
```

**Response:**
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user_id": 123,
  "email": "user@gmail.com",
  "first_name": "John",
  "last_name": "Doe",
  "is_new_user": true,
  "message": "Account created successfully with Google"
}
```

### 2. Connect Existing Account to Google
**POST** `/api/google/connect/`

**Request:**
```json
{
  "email": "existing@example.com",
  "password": "existing_password",
  "id_token": "google_id_token_here"
}
```

### 3. Register with Google Email + Password
**POST** `/api/google/register/`

**Request:**
```json
{
  "email": "user@gmail.com",
  "password": "custom_password",
  "first_name": "John",
  "last_name": "Doe"
}
```

### 4. Check Google Connection Status
**GET** `/api/google/status/` (Requires authentication)

## 📱 Frontend Implementation Examples

### React/JavaScript Implementation

```jsx
import React, { useState } from 'react';

const GoogleSignIn = () => {
  const [loading, setLoading] = useState(false);
  const [user, setUser] = useState(null);

  // Initialize Google Sign-In
  useEffect(() => {
    const initializeGoogleSignIn = () => {
      if (window.google) {
        window.google.accounts.id.initialize({
          client_id: 'YOUR_GOOGLE_CLIENT_ID',
          callback: handleGoogleSignIn,
          auto_select: false,
          cancel_on_tap_outside: true
        });
      }
    };

    // Load Google Sign-In script
    const script = document.createElement('script');
    script.src = 'https://accounts.google.com/gsi/client';
    script.onload = initializeGoogleSignIn;
    document.head.appendChild(script);

    return () => {
      document.head.removeChild(script);
    };
  }, []);

  // Handle Google Sign-In response
  const handleGoogleSignIn = async (response) => {
    setLoading(true);
    try {
      const result = await fetch('/api/google/signin/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          id_token: response.credential
        })
      });

      const data = await result.json();
      
      if (result.ok) {
        // Store tokens
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        setUser(data);
        
        if (data.is_new_user) {
          alert('Welcome! Your account has been created.');
        } else {
          alert('Welcome back!');
        }
      } else {
        alert('Sign-in failed: ' + data.detail);
      }
    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Connect existing account to Google
  const connectToGoogle = async (email, password) => {
    setLoading(true);
    try {
      // First get Google ID token
      const googleResponse = await new Promise((resolve) => {
        window.google.accounts.id.prompt((response) => {
          resolve(response);
        });
      });

      const result = await fetch('/api/google/connect/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email,
          password: password,
          id_token: googleResponse.credential
        })
      });

      const data = await result.json();
      
      if (result.ok) {
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        setUser(data);
        alert('Account successfully connected to Google!');
      } else {
        alert('Connection failed: ' + data.detail);
      }
    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // Register with Google email + custom password
  const registerWithGoogleEmail = async (formData) => {
    setLoading(true);
    try {
      const result = await fetch('/api/google/register/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData)
      });

      const data = await result.json();
      
      if (result.ok) {
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        setUser(data);
        alert('Account created successfully!');
      } else {
        alert('Registration failed: ' + data.detail);
      }
    } catch (error) {
      alert('Error: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="google-signin">
      <h2>Sign In with Google</h2>
      
      {/* Google Sign-In Button */}
      <div id="google-signin-button"></div>
      
      {/* Connect Existing Account */}
      <div className="connect-existing">
        <h3>Connect Existing Account</h3>
        <form onSubmit={(e) => {
          e.preventDefault();
          const formData = new FormData(e.target);
          connectToGoogle(formData.get('email'), formData.get('password'));
        }}>
          <input type="email" name="email" placeholder="Email" required />
          <input type="password" name="password" placeholder="Password" required />
          <button type="submit" disabled={loading}>
            {loading ? 'Connecting...' : 'Connect to Google'}
          </button>
        </form>
      </div>

      {/* Register with Google Email */}
      <div className="register-google-email">
        <h3>Register with Google Email</h3>
        <form onSubmit={(e) => {
          e.preventDefault();
          const formData = new FormData(e.target);
          registerWithGoogleEmail({
            email: formData.get('email'),
            password: formData.get('password'),
            first_name: formData.get('first_name'),
            last_name: formData.get('last_name')
          });
        }}>
          <input type="email" name="email" placeholder="Google Email" required />
          <input type="password" name="password" placeholder="Password" required />
          <input type="text" name="first_name" placeholder="First Name" />
          <input type="text" name="last_name" placeholder="Last Name" />
          <button type="submit" disabled={loading}>
            {loading ? 'Creating...' : 'Create Account'}
          </button>
        </form>
      </div>

      {user && (
        <div className="user-info">
          <h3>Welcome, {user.first_name}!</h3>
          <p>Email: {user.email}</p>
          <p>User ID: {user.user_id}</p>
        </div>
      )}
    </div>
  );
};

export default GoogleSignIn;
```

### Flutter/Dart Implementation

```dart
import 'package:google_sign_in/google_sign_in.dart';
import 'package:http/http.dart' as http;
import 'dart:convert';

class GoogleAuthService {
  final GoogleSignIn _googleSignIn = GoogleSignIn(
    clientId: 'YOUR_GOOGLE_CLIENT_ID',
  );

  // Google Sign-In (Login or Register)
  Future<Map<String, dynamic>?> signInWithGoogle() async {
    try {
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      if (googleUser == null) return null;

      final GoogleSignInAuthentication googleAuth = 
          await googleUser.authentication;

      final response = await http.post(
        Uri.parse('https://lms.myanmarlink.online/api/google/signin/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'id_token': googleAuth.idToken,
          'email': googleUser.email,
          'name': googleUser.displayName,
          'first_name': googleUser.displayName?.split(' ').first ?? '',
          'last_name': googleUser.displayName?.split(' ').last ?? '',
          'picture': googleUser.photoUrl,
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

  // Connect existing account to Google
  Future<Map<String, dynamic>?> connectToGoogle(
    String email, 
    String password
  ) async {
    try {
      final GoogleSignInAccount? googleUser = await _googleSignIn.signIn();
      if (googleUser == null) return null;

      final GoogleSignInAuthentication googleAuth = 
          await googleUser.authentication;

      final response = await http.post(
        Uri.parse('https://lms.myanmarlink.online/api/google/connect/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'password': password,
          'id_token': googleAuth.idToken,
        }),
      );

      if (response.statusCode == 200) {
        return jsonDecode(response.body);
      }
      return null;
    } catch (error) {
      print('Google Connect Error: $error');
      return null;
    }
  }

  // Register with Google email + custom password
  Future<Map<String, dynamic>?> registerWithGoogleEmail(
    String email,
    String password,
    String firstName,
    String lastName,
  ) async {
    try {
      final response = await http.post(
        Uri.parse('https://lms.myanmarlink.online/api/google/register/'),
        headers: {'Content-Type': 'application/json'},
        body: jsonEncode({
          'email': email,
          'password': password,
          'first_name': firstName,
          'last_name': lastName,
        }),
      );

      if (response.statusCode == 201) {
        return jsonDecode(response.body);
      }
      return null;
    } catch (error) {
      print('Google Register Error: $error');
      return null;
    }
  }
}
```

## 🧪 Testing the Implementation

### Test Google Sign-In
```bash
# Test with a real Google ID token
curl -X POST https://lms.myanmarlink.online/api/google/signin/ \
  -H "Content-Type: application/json" \
  -d '{
    "id_token": "your_google_id_token_here",
    "email": "test@gmail.com",
    "name": "Test User"
  }'
```

### Test Google Connect
```bash
curl -X POST https://lms.myanmarlink.online/api/google/connect/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "existing@example.com",
    "password": "existing_password",
    "id_token": "your_google_id_token_here"
  }'
```

### Test Google Register
```bash
curl -X POST https://lms.myanmarlink.online/api/google/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "newuser@gmail.com",
    "password": "new_password",
    "first_name": "New",
    "last_name": "User"
  }'
```

## 🔧 Configuration

### 1. Google Cloud Console Setup
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create OAuth 2.0 credentials
3. Add authorized origins:
   - `https://lms.myanmarlink.online`
   - `http://localhost:3000` (for development)
4. Add authorized redirect URIs:
   - `https://lms.myanmarlink.online/api/web-auth/google/login/callback/`

### 2. Environment Variables
```bash
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

## 🎯 User Flow Options

### Option 1: Direct Google Sign-In
- User clicks "Sign in with Google"
- Gets redirected to Google
- Returns with account created/logged in

### Option 2: Connect Existing Account
- User has existing account
- Wants to link it with Google
- Provides email/password + Google auth

### Option 3: Register with Google Email
- User wants to use Google email
- But create custom password
- More control over account

Your Google Sign-In system is now ready! 🚀
