import sqlite3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
import os
import http.cookies
from datetime import datetime
import json

PORT = 8000

# Authentication credentials
USERNAME = "salma"
PASSWORD = "pass123"

class SimpleTeacherSystem(BaseHTTPRequestHandler):
    
    def is_authenticated(self):
        """Check if user is logged in via cookies"""
        if "Cookie" in self.headers:
            cookie = http.cookies.SimpleCookie(self.headers["Cookie"])
            return cookie.get("logged_in") and cookie["logged_in"].value == "yes"
        return False
    
    def do_GET(self):
        # Parse the URL path and query parameters
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        query = parse_qs(parsed_path.query)
        
        # Public routes (no authentication required)
        if path == '/login':
            self.render_login()
            return
        elif path == '/logout':
            self.logout()
            return
        elif path.startswith('/static/'):
            self.serve_static()
            return
        elif path == '/api/students' and self.is_authenticated():
            self.api_get_students()
            return
            
        # Protected routes (authentication required)
        if not self.is_authenticated():
            self.redirect("/login")
            return
            
        # Main routes
        if path == '/':
            self.render_template("index.html")
        elif path == '/students':
            self.show_students()
        elif path == '/add_student':
            self.render_template("add_student.html")
        elif path == '/edit_student':
            self.edit_student(query.get('id', [None])[0])
        elif path == '/tuition':
            self.render_template("tuition.html")
        elif path == '/add_tuition':
            self.render_template("add_tuition.html")
        elif path == '/announcements':
            self.show_announcements()
        elif path == '/add_announcement':
            self.render_template("add_announcement.html")
        elif path == '/reports':
            self.show_reports("reports.html")
        else:
            self.send_error(404, "Page Not Found")

    def do_POST(self):
        # Public POST routes
        if self.path == '/login':
            self.handle_login()
            return
            
        # Protected POST routes
        if not self.is_authenticated():
            self.redirect("/login")
            return
            
        if self.path == '/save_student':
            self.save_student()
        elif self.path == '/update_student':
            self.update_student()
        elif self.path == '/delete_student':
            self.delete_student()
        elif self.path == '/save_tuition':
            self.save_tuition()
        elif self.path == '/save_announcement':
            self.save_announcement()
        else:
            self.send_error(404, "Page Not Found")

    # Authentication methods
    def handle_login(self):
        """Handle login form submission"""
        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length).decode()
        params = parse_qs(data)
        
        username = params.get('username', [''])[0].strip()
        password = params.get('password', [''])[0].strip()
        
        if username == USERNAME and password == PASSWORD:
            # Set login cookie and redirect to home
            self.send_response(302)
            self.send_header("Set-Cookie", "logged_in=yes; Max-Age=3600; Path=/")
            self.send_header("Location", "/")
            self.end_headers()
        else:
            self.render_login(error="❌ Invalid username or password!")

    def logout(self):
        """Handle logout"""
        self.send_response(302)
        self.send_header("Set-Cookie", "logged_in=no; Max-Age=0; Path=/")
        self.send_header("Location", "/login")
        self.end_headers()

    # Student management methods
    def show_students(self):
        """Display all enrolled students"""
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("SELECT id, student_id, name, parent_name, phone FROM students")
        students = cur.fetchall()
        conn.close()

        rows = ""
        if students:
            for s in students:
                rows += f"""
                <tr>
                    <td>{s[1]}</td>
                    <td>{s[2]}</td>
                    <td>{s[3]}</td>
                    <td>{s[4]}</td>
                    <td class="actions">
                        <a href="/edit_student?id={s[0]}" class="edit-btn">✏️</a>
                        <a href="#" onclick="deleteStudent({s[0]})" class="delete-btn">🗑️</a>
                    </td>
                </tr>
                """
        else:
            rows = "<tr><td colspan='5'>No students enrolled yet.</td></tr>"
            
        html = self.render_template("students.html", 
                                 content=rows,
                                 scripts="<script src='/static/students.js'></script>",
                                 return_html=True)
        self.respond(html)

    def api_get_students(self):
        """API endpoint for getting students (JSON)"""
        conn = sqlite3.connect("database.db")
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT id, student_id, name, parent_name, phone FROM students")
        students = cur.fetchall()
        conn.close()
        
        students_list = [dict(row) for row in students]
        self.send_json(students_list)

    def edit_student(self, student_id):
        """Show student edit form"""
        if not student_id:
            self.redirect("/students")
            return
            
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("SELECT id, student_id, name, parent_name, phone FROM students WHERE id = ?", (student_id,))
        student = cur.fetchone()
        conn.close()
        
        if not student:
            self.redirect("/students")
            return
            
        form_html = f"""
        <form method="POST" action="/update_student">
            <input type="hidden" name="id" value="{student[0]}">
            <input type="text" name="student_id" placeholder="Student ID" value="{student[1]}" required>
            <input type="text" name="name" placeholder="Student Name" value="{student[2]}" required>
            <input type="text" name="parent_name" placeholder="Parent Name" value="{student[3]}" required>
            <input type="text" name="phone" placeholder="Phone Number" value="{student[4]}" required>
            <button type="submit">Update Student</button>
            <a href="/students" class="cancel-btn">Cancel</a>
        </form>
        """
        
        html = self.render_template("edit_form.html", 
                                 title="Edit Student",
                                 content=form_html,
                                 return_html=True)
        self.respond(html)

    def save_student(self):
        """Save new student to database"""
        params = self.get_post_params()
        
        student_id = params.get("student_id", "").strip().upper()
        name = params.get("name", "").strip()
        parent_name = params.get("parent_name", "").strip()
        phone = params.get("phone", "").strip()

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        try:
            cur.execute("""
                INSERT INTO students (student_id, name, parent_name, phone)
                VALUES (?, ?, ?, ?)
            """, (student_id, name, parent_name, phone))
            conn.commit()
            conn.close()
            self.redirect("/students")
        except sqlite3.IntegrityError:
            conn.close()
            self.respond("""
                <h1>❌ Student ID already exists!</h1>
                <p><a href='/students'>← Back to Students</a></p>
            """)

    def update_student(self):
        """Update existing student"""
        params = self.get_post_params()
        
        student_id = params.get("student_id", "").strip().upper()
        name = params.get("name", "").strip()
        parent_name = params.get("parent_name", "").strip()
        phone = params.get("phone", "").strip()
        id = params.get("id", "")

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        try:
            cur.execute("""
                UPDATE students 
                SET student_id = ?, name = ?, parent_name = ?, phone = ?
                WHERE id = ?
            """, (student_id, name, parent_name, phone, id))
            conn.commit()
            conn.close()
            self.redirect("/students")
        except sqlite3.Error as e:
            conn.close()
            self.respond(f"""
                <h1>❌ Error updating student!</h1>
                <p>{str(e)}</p>
                <p><a href='/students'>← Back to Students</a></p>
            """)

    def delete_student(self):
        """Delete a student"""
        params = self.get_post_params()
        student_id = params.get("id", "")
        
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        try:
            cur.execute("DELETE FROM students WHERE id = ?", (student_id,))
            conn.commit()
            conn.close()
            self.send_json({"success": True})
        except sqlite3.Error as e:
            conn.close()
            self.send_json({"success": False, "error": str(e)})

    # Tuition management methods
    def show_tuition(self):
        """Display tuition payment records"""
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("""
            SELECT t.id, t.student_name, t.amount, t.date, t.notes 
            FROM tuition t 
            ORDER BY t.date DESC
        """)
        tuition_records = cur.fetchall()
        conn.close()

        rows = ""
        total_amount = 0
        if tuition_records:
            for t in tuition_records:
                rows += f"""
                <tr>
                    <td>{t[1]}</td>
                    <td>TSh {t[2]:,}</td>
                    <td>{t[3]}</td>
                    <td>{t[4] or ''}</td>
                    <td class="actions">
                        <a href="#" onclick="deleteTuition({t[0]})" class="delete-btn">🗑️</a>
                    </td>
                </tr>
                """
                total_amount += t[2]
        else:
            rows = "<tr><td colspan='5'>No tuition payments recorded yet.</td></tr>"
            
        html = self.render_template("tuition.html", 
                                 content=rows, 
                                 total=f"TSh {total_amount:,}",
                                 scripts="<script src='/static/tuition.js'></script>",
                                 return_html=True)
        self.respond(html)

    def save_tuition(self):
        """Save tuition payment to database"""
        params = self.get_post_params()
        
        student_name = params.get("student_name", "").strip()
        amount = float(params.get("amount", "0"))
        notes = params.get("notes", "").strip()
        date = datetime.now().strftime("%Y-%m-%d")

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO tuition (student_name, amount, date, notes)
            VALUES (?, ?, ?, ?)
        """, (student_name, amount, date, notes))
        conn.commit()
        conn.close()
        self.redirect("/tuition")

    # Announcement methods
    def show_announcements(self):
        """Display announcements"""
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("SELECT id, title, content, date, priority FROM announcements ORDER BY date DESC")
        announcements = cur.fetchall()
        conn.close()

        rows = ""
        if announcements:
            for a in announcements:
                priority_icon = {"High": "🔴", "Normal": "🟡", "Low": "🟢"}.get(a[4], "🟡")
                rows += f"""
                <tr>
                    <td>{priority_icon} {a[1]}</td>
                    <td>{a[2]}</td>
                    <td>{a[3]}</td>
                    <td>{a[4]}</td>
                    <td class="actions">
                        <a href="#" onclick="deleteAnnouncement({a[0]})" class="delete-btn">🗑️</a>
                    </td>
                </tr>
                """
        else:
            rows = "<tr><td colspan='5'>No announcements yet.</td></tr>"
            
        html = self.render_template("announcements.html", 
                                 content=rows,
                                 scripts="<script src='/static/announcements.js'></script>",
                                 return_html=True)
        self.respond(html)

    def save_announcement(self):
        """Save announcement to database"""
        params = self.get_post_params()
        
        title = params.get("title", "").strip()
        content = params.get("content", "").strip()
        priority = params.get("priority", "Normal")
        date = datetime.now().strftime("%Y-%m-%d %H:%M")

        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO announcements (title, content, date, priority)
            VALUES (?, ?, ?, ?)
        """, (title, content, date, priority))
        conn.commit()
        conn.close()
        self.redirect("/announcements")

    # Report methods
    def show_reports(self):
        """Display summary reports"""
        conn = sqlite3.connect("database.db")
        cur = conn.cursor()
        
        # Get statistics
        cur.execute("SELECT COUNT(*) FROM students")
        total_students = cur.fetchone()[0]
        
        cur.execute("SELECT SUM(amount) FROM tuition")
        total_tuition = cur.fetchone()[0] or 0
        
        cur.execute("SELECT COUNT(*) FROM announcements")
        total_announcements = cur.fetchone()[0]
        
        cur.execute("SELECT student_name, SUM(amount) FROM tuition GROUP BY student_name ORDER BY SUM(amount) DESC")
        top_payers = cur.fetchall()
        
        conn.close()

        # Generate top payers list
        top_payers_html = ""
        for payer in top_payers[:5]:  # Top 5
            top_payers_html += f"<li>{payer[0]}: TSh {payer[1]:,}</li>"
        
        if not top_payers_html:
            top_payers_html = "<li>No payments recorded yet</li>"

        report_content = f"""
        <div class="stats-grid">
            <div class="stat-card">
                <h3>👥 Students</h3>
                <p class="stat-number">{total_students}</p>
            </div>
            <div class="stat-card">
                <h3>💰 Total Tuition</h3>
                <p class="stat-number">TSh {total_tuition:,}</p>
            </div>
            <div class="stat-card">
                <h3>📢 Announcements</h3>
                <p class="stat-number">{total_announcements}</p>
            </div>
        </div>
        
        <h3>Top Paying Students</h3>
        <ul class="top-payers">
            {top_payers_html}
        </ul>
        
        <div class="chart-container">
            <canvas id="tuitionChart"></canvas>
        </div>
        """
        
        html = self.render_template("reports.html", 
                                 content=report_content,
                                 scripts="""
                                 <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                                 <script src="/static/reports.js"></script>
                                 """,
                                 return_html=True)
        self.respond(html)

    # Utility methods
    def serve_static(self):
        """Serve static files (CSS, JS, images)"""
        try:
            path = self.path.lstrip('/')
            if not os.path.exists(path):
                self.send_error(404)
                return
                
            with open(path, 'rb') as f:
                self.send_response(200)
                if path.endswith('.css'):
                    self.send_header('Content-type', 'text/css')
                elif path.endswith('.js'):
                    self.send_header('Content-type', 'application/javascript')
                elif path.endswith('.png'):
                    self.send_header('Content-type', 'image/png')
                elif path.endswith('.jpg') or path.endswith('.jpeg'):
                    self.send_header('Content-type', 'image/jpeg')
                else:
                    self.send_header('Content-type', 'application/octet-stream')
                self.end_headers()
                self.wfile.write(f.read())
        except Exception as e:
            self.send_error(500, f"Error serving static file: {str(e)}")

    def render_template(self, filename, content="", total="", scripts="", return_html=False):
        """Render HTML template with content replacement"""
        try:
            with open(f"templates/{filename}", "r", encoding="utf-8") as f:
                html = f.read()
                html = html.replace("{{content}}", content)
                html = html.replace("{{total}}", total)
                html = html.replace("{{scripts}}", scripts)
                if return_html:
                    return html
                self.respond(html)
        except FileNotFoundError:
            self.send_error(404, f"Template not found: {filename}")

    def render_login(self, error=""):
        """Render login page"""
        try:
            with open("templates/login.html", "r", encoding="utf-8") as f:
                html = f.read().replace("{{error}}", error)
                self.respond(html)
        except FileNotFoundError:
            # Create a basic login form if template doesn't exist
            login_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Login - SmartTuition System</title>
                <link rel="stylesheet" href="/static/style.css">
            </head>
            <body class="login-body">
                <div class="login-container">
                    <h2>🏫 SmartTuition System</h2>
                    <h3>Login</h3>
                    <form method="POST" action="/login" class="login-form">
                        <input type="text" name="username" placeholder="Username" required>
                        <input type="password" name="password" placeholder="Password" required>
                        <button type="submit">Login</button>
                    </form>
                    <p class="error">{error}</p>
                    <p class="info">Default: salma / pass123</p>
                </div>
            </body>
            </html>
            """
            self.respond(login_html)

    def get_post_params(self):
        """Get POST parameters from request"""
        length = int(self.headers['Content-Length'])
        data = self.rfile.read(length).decode()
        return parse_qs(data)

    def respond(self, html, content_type="text/html; charset=utf-8"):
        """Send HTML response"""
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.end_headers()
        self.wfile.write(html.encode("utf-8"))

    def send_json(self, data):
        """Send JSON response"""
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def redirect(self, location):
        """Redirect to another page"""
        self.send_response(302)
        self.send_header("Location", location)
        self.end_headers()

def init_db():
    """Initialize SQLite database with all required tables"""
    conn = sqlite3.connect("database.db")
    cur = conn.cursor()
    
    # Students table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT UNIQUE,
            name TEXT,
            parent_name TEXT,
            phone TEXT
        )
    """)
    
    # Tuition payments table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tuition (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_name TEXT,
            amount REAL,
            date TEXT,
            notes TEXT
        )
    """)
    
    # Announcements table
    cur.execute("""
        CREATE TABLE IF NOT EXISTS announcements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT,
            date TEXT,
            priority TEXT DEFAULT 'Normal'
        )
    """)
    
    # Insert some sample data if tables are empty
    try:
        cur.execute("SELECT COUNT(*) FROM students")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO students (student_id, name, parent_name, phone) VALUES (?, ?, ?, ?)",
                       ("STU001", "Ahmed Mwalimu", "John Mwalimu", "+255713456789"))
            cur.execute("INSERT INTO students (student_id, name, parent_name, phone) VALUES (?, ?, ?, ?)",
                       ("STU002", "Fatima Kibwana", "Mary Kibwana", "+255714567890"))
        
        cur.execute("SELECT COUNT(*) FROM tuition")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO tuition (student_name, amount, date, notes) VALUES (?, ?, ?, ?)",
                       ("Ahmed Mwalimu", 50000, "2025-07-20", "Monthly tuition"))
        
        cur.execute("SELECT COUNT(*) FROM announcements")
        if cur.fetchone()[0] == 0:
            cur.execute("INSERT INTO announcements (title, content, date, priority) VALUES (?, ?, ?, ?)",
                       ("Welcome to SmartTuition", "This system helps track student progress and payments.", "2025-07-24 10:00", "High"))
    except sqlite3.Error as e:
        print(f"Error initializing sample data: {e}")
    
    conn.commit()
    conn.close()

def create_static_files():
    """Create static files (CSS, JS) if they don't exist"""
    if not os.path.exists("static"):
        os.makedirs("static")
    
    # CSS file
    if not os.path.exists("static/style.css"):
        css_content = """
        /* CSS content from previous example */
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body { 
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
            background: #f5f5f5; 
            line-height: 1.6;
        }
        
        /* ... (rest of the CSS from previous example) ... */
        
        .actions {
            white-space: nowrap;
        }
        
        .edit-btn, .delete-btn {
            text-decoration: none;
            padding: 0.3rem 0.5rem;
            border-radius: 4px;
            margin: 0 0.2rem;
            display: inline-block;
        }
        
        .edit-btn {
            background: #3498db;
            color: white;
        }
        
        .delete-btn {
            background: #e74c3c;
            color: white;
        }
        
        .chart-container {
            background: white;
            padding: 2rem;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            margin-top: 2rem;
        }
        """
        with open("static/style.css", "w", encoding="utf-8") as f:
            f.write(css_content)
    
    # JavaScript files
    if not os.path.exists("static/students.js"):
        js_content = """
        function deleteStudent(id) {
            if (confirm('Are you sure you want to delete this student?')) {
                fetch('/delete_student', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `id=${id}`
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Error deleting student: ' + data.error);
                    }
                });
            }
        }
        """
        with open("static/students.js", "w", encoding="utf-8") as f:
            f.write(js_content)
    
    if not os.path.exists("static/tuition.js"):
        js_content = """
        function deleteTuition(id) {
            if (confirm('Are you sure you want to delete this tuition record?')) {
                fetch('/delete_tuition', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: `id=${id}`
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('Error deleting tuition record: ' + data.error);
                    }
                });
            }
        }
        """
        with open("static/tuition.js", "w", encoding="utf-8") as f:
            f.write(js_content)
    
    if not os.path.exists("static/reports.js"):
        js_content = """
        document.addEventListener('DOMContentLoaded', function() {
            fetch('/api/tuition_stats')
                .then(response => response.json())
                .then(data => {
                    renderChart(data);
                });
        });

        function renderChart(data) {
            const ctx = document.getElementById('tuitionChart').getContext('2d');
            new Chart(ctx, {
                type: 'bar',
                data: {
                    labels: data.labels,
                    datasets: [{
                        label: 'Tuition Payments (TSh)',
                        data: data.amounts,
                        backgroundColor: 'rgba(54, 162, 235, 0.5)',
                        borderColor: 'rgba(54, 162, 235, 1)',
                        borderWidth: 1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        """
        with open("static/reports.js", "w", encoding="utf-8") as f:
            f.write(js_content)

if __name__ == "__main__":
    print("🚀 Initializing SmartTuition System...")
    
    # Create directories if they don't exist
    if not os.path.exists("templates"):
        os.makedirs("templates")
    
    # Initialize database and create static files
    init_db()
    create_static_files()
    
    # Start server
    server = HTTPServer(("", PORT), SimpleTeacherSystem)
    print(f"📡 SmartTuition Server running at http://localhost:{PORT}")
    print(f"👤 Login with: {USERNAME} / {PASSWORD}")
    print("🔄 Press Ctrl+C to stop the server")
    
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n✅ Server stopped safely. Goodbye!")
        server.server_close()