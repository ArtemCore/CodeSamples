## Auth submodule acceptance tests
### 1. Classic actor registration
1. Open /authorization/
2. Click sign up button 
3. Pass registration data
4. Click sing up button

### 2. Classic actor authorization
1. Open /authorization/
2. Pass authorization data
3. Click sing in button

### 3. Ecosystem actor registration
1. Open /authorization/
2. Click sign up button 
3. Click QR code button
4. Scan QR code by ecosystem54 mobile app
5. Pass registration data on mobile app

### 4. Ecosystem actor authorization
1. Open /authorization/
2. Click QR code button 
3. Scan QR code by ecosystem54 mobile app

### 5. Moving to standalone mode
1. On local_settings.py file, set AUTH_STANDALONE = True
2. Use python manage.py disconnect_biom
3. Restart your service

### 6. Connect to biome
1. On local_settings.py file, set AUTH_STANDALONE = False
2. Register your service on auth service
3. Setting necessary permissions for your service
4. Pass auth service credentials to local_settings.py
5. Use python manage.py connect_biom

### 7. Setting of permissions by auth service
1. Create necessary permissions on your service
2. Use python manage.py collect_perms
3. Setting permissions on auth service

### 8. Setting of permissions on standalone mode
1. Move to standalone mode
2. Create necessary permissions on your service
3. Use python manage.py collect_perms
4. Open /authorization/
5. Sign in as admin or root
6. Go to /auth_admin/actors/
7. Open any actor
8. Setting permissions
