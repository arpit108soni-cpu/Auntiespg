# Aunties PG

A modern Flask web application for a PG (Paying Guest) guesthouse facility. This platform provides an interactive interface for showcasing accommodations, managing resident profiles, displaying gallery images, and handling customer inquiries.

## Features Overview

### Public Features

#### 1. **Home Page** (`/`)
- Landing page with welcoming introduction to the guesthouse
- Navigation to all public sections of the site

#### 2. **Gallery** (`/gallery`)
- Browse accommodation images organized by categories:
  - Private Suites
  - Shared Rooms
  - Common Areas
  - Amenities
- Images display with:
  - Title and description
  - Category classification
  - Availability status (Available/Booked)
- Filter and view images by category
- Admin interface visible to logged-in admins for quick management

#### 3. **Residents** (`/residents`)
- View profiles of current residents
- Each resident card displays:
  - Name
  - College/Institution
  - Major/Field of Study
  - Profile Photo
  - Resident Category (Medical, Engineering, Arts, General)
- Categorized resident listings
- New residents can be added from admin panel

#### 4. **Contact Form** (`/contact`)
- Submit inquiries and booking requests
- Form fields:
  - Full Name
  - Contact Number
  - Email Address
  - Inquiry Message
- CSRF-protected submission
- Email validation
- Responses stored in database for admin review

### Admin Features

#### 5. **Admin Dashboard** (`/admin`)
- Secure authentication required
- Tab-based management interface:

##### **Gallery Management**
- Upload new accommodation images
  - Supports: PNG, JPG, JPEG, GIF, WebP
  - Maximum file size: 8 MB
  - Automatic filename sanitization to prevent security issues
- Set image properties:
  - Title
  - Category (room type)
  - Availability Status
- Delete images with automatic file cleanup
- View all uploaded images in chronological order

##### **Residents Management**
- Add new resident profiles with:
  - Full Name
  - College/Institution Name
  - Major/Field of Study
  - Photo Upload (optional; defaults to avatar)
  - Resident Category
- Delete resident profiles (removes associated photos)
- View all residents in the system

##### **Inquiries Management**
- View all contact form submissions
- Display inquiry details:
  - Visitor Name
  - Contact Number
  - Email Address
  - Inquiry Message
  - Submission Timestamp
- Delete old inquiries to maintain database
- Track potential bookings and customer interest

### Security Features

#### **Authentication & Authorization**
- Secure admin login with username and password
- Password hashing using SHA-256
- Session management with secure tokens
- Admin-only route protection

#### **CSRF Protection**
- Cross-Site Request Forgery token generation and validation
- Token injection in all forms
- Token verification on POST/DELETE operations

#### **File Security**
- File type validation (images only)
- Secure filename sanitization
- File size limits (8 MB maximum)
- Uploaded files stored in protected directory
- Timestamp-based filename prefixes to prevent collisions

#### **Security Headers**
- X-Content-Type-Options: nosniff
- X-XSS-Protection: 1; mode=block
- Referrer-Policy: strict-origin-when-cross-origin
- Permissions-Policy: Disables geolocation, camera, microphone
- X-Frame-Options: SAMEORIGIN

### Database Structure

The application uses SQLite with four main tables:

**Contacts Table** - Stores visitor inquiries
- Full name, contact number, email
- Inquiry message
- Timestamp of submission

**Residents Table** - Stores resident profiles
- Name, college, major field of study
- Profile photo URL
- Resident category (medical, engineering, arts, general)
- Profile creation timestamp

**Gallery Images Table** - Stores accommodation photos
- Image title and category
- Filename and URL reference
- Availability status
- Upload timestamp

**Admin Users Table** - Stores admin credentials
- Username
- Password hash (SHA-256)
- Account creation timestamp

## Local setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set a secret key for session security:
   - `export SECRET_KEY="your-secret-key"` on macOS/Linux
   - `set SECRET_KEY=your-secret-key` on Windows PowerShell
3. Run the app:
   ```bash
   python app.py
   ```
4. Open `http://127.0.0.1:5001`

## Deploy to a free host

### Render

1. Push this repo to GitHub.
2. Create a new Web Service on Render.
3. Connect your GitHub repo and choose the branch.
4. Set the build command:
   ```bash
   pip install -r requirements.txt
   ```
5. Set the start command:
   ```bash
   gunicorn app:app
   ```
6. Add an environment variable:
   - `SECRET_KEY` = a strong random value
7. Deploy.

Render will provide a public URL that you can share.

### Replit

1. Create a new Python Repl.
2. Upload the project files.
3. Add `requirements.txt`.
4. Set the run command to:
   ```bash
   python app.py
   ```
5. Start the Repl and use the generated public link.

## Notes

- The app uses `database.db` and `static/uploads/` for local storage.
- On free hosting, file storage may be temporary or reset after restart.
- For production, use a dedicated database and cloud storage solution.
