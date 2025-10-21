# Fix Google OAuth for Production Deployment

## 🚨 Common Production Issues

### 1. **Redirect URI Mismatch**
The most common issue is that Google Console redirect URIs don't match your production domain.

### 2. **HTTPS vs HTTP**
Google OAuth requires HTTPS in production (except localhost).

### 3. **Environment Variables**
Production environment variables might not be set correctly.

### 4. **Domain Configuration**
Django settings need to know the production domain.

## 🔧 Step-by-Step Fix

### Step 1: Update Google Cloud Console

1. **Go to Google Cloud Console** → APIs & Services → Credentials
2. **Edit your OAuth 2.0 Client ID**
3. **Add these Authorized Redirect URIs:**
   ```
   https://yourdomain.com/api/web-auth/google/login/callback/
   https://yourdomain.com/auth/google/callback
   https://yourdomain.com/accounts/google/login/callback/
   ```

### Step 2: Update Django Settings for Production

Add these settings to your `settings.py`:

```python
# Production Google OAuth Configuration
if not DEBUG:
    # Force HTTPS for OAuth
    SECURE_SSL_REDIRECT = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    
    # Update allowed hosts for production
    ALLOWED_HOSTS = [
        'yourdomain.com',
        'www.yourdomain.com',
        'api.yourdomain.com',
    ]
    
    # Update CORS for production
    CORS_ALLOWED_ORIGINS = [
        "https://yourdomain.com",
        "https://www.yourdomain.com",
        "https://api.yourdomain.com",
    ]
    
    # Update redirect URIs for production
    SOCIALACCOUNT_PROVIDERS = {
        'google': {
            'APP': {
                'client_id': os.getenv('GOOGLE_CLIENT_ID'),
                'secret': os.getenv('GOOGLE_CLIENT_SECRET'),
                'key': ''
            },
            'SCOPE': ['profile', 'email'],
            'AUTH_PARAMS': {'access_type': 'online'},
            'VERIFIED_EMAIL': True,
        }
    }
```

### Step 3: Update Docker Compose for Production

Create a production docker-compose file:

```yaml
# docker-compose.prod.yml
services:
  web:
    build:
      context: .
      dockerfile: deploy/Dockerfile
    image: loxa/web:latest
    environment:
      DJANGO_SETTINGS_MODULE: loxa.settings
      DJANGO_DEBUG: "0"  # Disable debug in production
      DJANGO_SECRET_KEY: ${DJANGO_SECRET_KEY}
      DJANGO_ALLOWED_HOSTS: ${DJANGO_ALLOWED_HOSTS}
      POSTGRES_DB: ${POSTGRES_DB}
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_HOST: postgres
      POSTGRES_PORT: "5432"
      GOOGLE_CLIENT_ID: ${GOOGLE_CLIENT_ID}
      GOOGLE_CLIENT_SECRET: ${GOOGLE_CLIENT_SECRET}
      # Add your production domain
      DJANGO_SITE_URL: https://yourdomain.com
    # ... rest of your config
```

### Step 4: Update Nginx Configuration

Update your `nginx.conf` to handle HTTPS and proper headers:

```nginx
server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL configuration (add your SSL certificates)
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    
    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    
    # Proxy to Django
    location / {
        proxy_pass         http://web:8000;
        proxy_set_header   Host $host;
        proxy_set_header   X-Real-IP $remote_addr;
        proxy_set_header   X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header   X-Forwarded-Proto $scheme;
        proxy_set_header   X-Forwarded-Host $host;
        proxy_set_header   X-Forwarded-Port $server_port;
    }
    
    # ... rest of your config
}
```

### Step 5: Update Social Views for Production

Update your `api/social_views.py` to handle production domains:

```python
def _default_redirect_uri(request):
    # Use production domain in production
    if settings.DEBUG:
        return request.build_absolute_uri("/auth/google/callback")
    else:
        # Use your production domain
        return f"https://yourdomain.com/auth/google/callback"
```

### Step 6: Environment Variables for Production

Create a production `.env` file:

```bash
# Production Environment Variables
DJANGO_DEBUG=0
DJANGO_SECRET_KEY=your-production-secret-key
DJANGO_ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,api.yourdomain.com

# Database
POSTGRES_DB=loxa_prod
POSTGRES_USER=loxa_user
POSTGRES_PASSWORD=your-secure-password

# Google OAuth (Production)
GOOGLE_CLIENT_ID=your-production-google-client-id
GOOGLE_CLIENT_SECRET=your-production-google-client-secret

# Site URL
DJANGO_SITE_URL=https://yourdomain.com
```

## 🧪 Testing Production Deployment

### 1. Test Google OAuth URLs

```bash
# Test auth URL generation
curl https://yourdomain.com/api/auth/google/url/

# Test web login redirect
curl -I https://yourdomain.com/api/web-auth/google/login/
```

### 2. Check Environment Variables

```bash
# Check if environment variables are loaded
docker-compose exec web python manage.py shell
>>> from django.conf import settings
>>> print(settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY)
>>> print(settings.ALLOWED_HOSTS)
```

### 3. Test OAuth Flow

1. Visit: `https://yourdomain.com/api/web-auth/google/login/`
2. Complete Google OAuth
3. Check if you're redirected back correctly
4. Verify JWT tokens are generated

## 🐛 Common Production Issues & Solutions

### Issue 1: "Redirect URI Mismatch"
**Solution**: Ensure Google Console has exact production URLs

### Issue 2: "Invalid Client"
**Solution**: Check `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` are set

### Issue 3: "HTTP not allowed"
**Solution**: Use HTTPS in production, add SSL certificate

### Issue 4: "CORS errors"
**Solution**: Update `CORS_ALLOWED_ORIGINS` with production domains

### Issue 5: "Domain not allowed"
**Solution**: Add production domain to `ALLOWED_HOSTS`

## 🚀 Deployment Commands

```bash
# Build and deploy
docker-compose -f docker-compose.prod.yml up --build -d

# Check logs
docker-compose logs web

# Run migrations
docker-compose exec web python manage.py migrate

# Collect static files
docker-compose exec web python manage.py collectstatic --noinput
```

## 📋 Checklist for Production

- [ ] Google Console redirect URIs updated
- [ ] HTTPS enabled with valid SSL certificate
- [ ] Environment variables set correctly
- [ ] Django settings updated for production
- [ ] Nginx configured for HTTPS
- [ ] CORS settings updated
- [ ] ALLOWED_HOSTS includes production domain
- [ ] Test OAuth flow end-to-end

## 🔍 Debug Commands

```bash
# Check if Google OAuth is working
curl -X POST https://yourdomain.com/api/auth/google/ \
  -H "Content-Type: application/json" \
  -d '{"access_token": "test-token"}'

# Check Django settings
docker-compose exec web python manage.py shell -c "
from django.conf import settings
print('Google Client ID:', settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY)
print('Allowed Hosts:', settings.ALLOWED_HOSTS)
print('Debug Mode:', settings.DEBUG)
"
```

Your Google OAuth should work in production after these fixes! 🎉
