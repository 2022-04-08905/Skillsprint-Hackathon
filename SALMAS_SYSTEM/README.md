# SmartTuition System

## Overview
SmartTuition System is a simple school management web application for managing students, tuition payments, and announcements. It is built with Python, SQLite, and a minimal HTTP server. The system supports admin login, student management, tuition tracking, and public announcements.

## Features
- Admin login and dashboard
- Add, edit, and delete students
- Record and view tuition payments
- Post and view announcements
- Responsive web UI (HTML/CSS/JS)
- Docker support for easy deployment

## Project Structure
```
database.db                # SQLite database file
server.py                  # Main Python server
static/                    # Static JS/CSS files
    reports.js
    students.js
    style.css
    tuition.js
templates/                 # HTML templates
    add_announcement.html
    add_student.html
    add_tuition.html
    announcements.html
    edit_form.html
    index.html
    login.html
    reports.html
    students.html
    tuition.html
```

## Setup & Running
### Requirements
- Python 3.8+
- (Optional) Docker

### Local Run
1. Install Python 3.8 or higher.
2. Install dependencies (if any):
   - No external dependencies required.
3. Run the server:
   ```
   python server.py
   ```
4. Open your browser and go to `http://localhost:8000`

### Docker Run
1. Build the Docker image:
   ```
   docker build -t smarttuition .
   ```
2. Run the container:
   ```
   docker run -p 8000:8000 smarttuition
   ```
3. Visit `http://localhost:8000` in your browser.

## Admin Login
- **Username:** salma
- **Password:** pass123

## Student Login (if enabled)
- **Registration Number:** (see student list)
- **Password:** Surname (last name, case-insensitive)

## User Manual
### Admin
- Log in with your admin credentials.
- Use the dashboard to add/edit/delete students, record tuition, and post announcements.
- Announcements are visible to all users on the landing page.

### Students
- If student login is enabled, use your registration number and surname to log in.
- View your tuition receipts and announcements after login.

### Public
- Announcements are visible on the landing page without login.

## Troubleshooting
- If you have issues with student login, check that the surname field is set for each student in the database.
- To reset the admin password, edit the `USERNAME` and `PASSWORD` variables in `server.py`.

## License
MIT
