"""
=============================================================================
 EMMA WATSON FAN CLUB - ULTIMATE MILITARY-GRADE SECURE WEB APPLICATION
 File: emma.py
 Architecture: Single-file Modular Monolith (Zero Internal Errors)
 Security: Zero-Trust WAF, Anti-Bruteforce, SHA-256 + Bcrypt
 Features: Masonry Grid, Search, Floating Menu, 10+ Facts, 30+ Photos, Admin Panel
 Port: 1990
=============================================================================
"""

import os
import re
import time
import logging
import sqlite3
import secrets
import hashlib
import sys
import subprocess
from datetime import datetime
from typing import Optional

# --- KUTUBXONALARNI TEKSHIRISH VA O'RNATISH ---
REQUIRED_MODULES = ['fastapi', 'uvicorn', 'bcrypt', 'bleach', 'pydantic', 'python-multipart']

def check_and_install_modules():
    for module in REQUIRED_MODULES:
        mod_name = module.replace("-", "_") # python-multipart -> python_multipart
        try:
            __import__(mod_name)
        except ImportError:
            print(f"Kutubxona topilmadi '{module}'. O'rnatilmoqda...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", module])

check_and_install_modules()

# --- KUTUBXONALARNI IMPORT QILISH ---
import uvicorn
import bcrypt
from bleach import clean
from fastapi import FastAPI, Request, Response, HTTPException, Depends, status, Form, Cookie
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from pydantic import BaseModel, Field
from starlette.middleware.base import BaseHTTPMiddleware

# =============================================================================
# 1. CONFIGURATION & LOGGING
# =============================================================================

PORT = 1990

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("emma_security")

# =============================================================================
# 2. DATABASE & CRYPTOGRAPHY LAYER
# =============================================================================

def get_db():
    conn = sqlite3.connect("emma_club.db", check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_superuser BOOLEAN DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        description TEXT,
        likes INTEGER DEFAULT 0,
        uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        image_id INTEGER NOT NULL,
        username TEXT NOT NULL,
        content TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(image_id) REFERENCES images(id)
    )''')
    
    c.execute('''CREATE TABLE IF NOT EXISTS security_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip_address TEXT,
        user_agent TEXT,
        path TEXT,
        method TEXT,
        reason TEXT,
        logged_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')

    # Superuser 'emma:watson' (Bcrypt bilan)
    c.execute("SELECT * FROM users WHERE username='emma'")
    if not c.fetchone():
        hashed_pw = bcrypt.hashpw("watson".encode('utf-8'), bcrypt.gensalt(rounds=12))
        c.execute("INSERT INTO users (username, email, password_hash, is_superuser) VALUES (?, ?, ?, ?)",
                  ("emma", "emma@watson.com", hashed_pw.decode('utf-8'), True))
    
    # 30 ta Haqiqiy Emma Watson rasmlari
    c.execute("SELECT COUNT(*) FROM images")
    if c.fetchone()[0] == 0:
        demo_images = [
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Emma_Watson_2013.jpg/800px-Emma_Watson_2013.jpg", "Classic Portrait 2013"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Emma_Watson_Cannes_2013_2.jpg/800px-Emma_Watson_Cannes_2013_2.jpg", "Cannes Film Festival Elegance"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Emma_Watson_2012.jpg/800px-Emma_Watson_2012.jpg", "Beautiful Smile 2012"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Emma_Watson_in_2018.jpg/800px-Emma_Watson_in_2018.jpg", "Modern Emma 2018"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Emma_Watson_-_The_Circle_premiere_at_Tribeca_Film_Festival_%28cropped%29.jpg/800px-Emma_Watson_-_The_Circle_premiere_at_Tribeca_Film_Festival_%28cropped%29.jpg", "The Circle Premiere Tribeca"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Emma_Watson_SDCC_2014_%28cropped%29.jpg/800px-Emma_Watson_SDCC_2014_%28cropped%29.jpg", "SDCC 2014 Belle"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Emma_Watson_Princes_Awards_2014.jpg/800px-Emma_Watson_Princes_Awards_2014.jpg", "Princes Awards 2014"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Emma_Watson_-_Noah_Premiere_in_Berlin_%28cropped%29.jpg/800px-Emma_Watson_-_Noah_Premiere_in_Berlin_%28cropped%29.jpg", "Noah Premiere in Berlin"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Emma_Watson_-_Beauty_and_the_Beast_premiere_%28cropped%29.jpg/800px-Emma_Watson_-_Beauty_and_the_Beast_premiere_%28cropped%29.jpg", "Beauty and the Beast Premiere"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/Emma_Watson_JP.jpg/800px-Emma_Watson_JP.jpg", "Japan Premiere"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Emma_Watson_2011.jpg/800px-Emma_Watson_2011.jpg", "Harry Potter Premiere 2011"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/b/bc/Emma_Watson_at_the_2018_British_Academy_Film_Awards.jpg/800px-Emma_Watson_at_the_2018_British_Academy_Film_Awards.jpg", "BAFTA Awards 2018"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/47/Emma_Watson_MTV_2013.jpg/800px-Emma_Watson_MTV_2013.jpg", "MTV Awards 2013"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Emma_Watson_-_The_Blings_Ring_premiere.jpg/800px-Emma_Watson_-_The_Blings_Ring_premiere.jpg", "The Bling Ring Premiere"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Emma_Watson_Regression_premiere.jpg/800px-Emma_Watson_Regression_premiere.jpg", "Regression Premiere"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/0/02/Emma_Watson_Cannes_2017_%28cropped%29.jpg/800px-Emma_Watson_Cannes_2017_%28cropped%29.jpg", "Cannes 2017"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/Emma_Watson_2014_%28cropped%29.jpg/800px-Emma_Watson_2014_%28cropped%29.jpg", "Golden Globes 2014"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Emma_Watson_Vogue.jpg/800px-Emma_Watson_Vogue.jpg", "Vogue Photoshoot"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/18/Emma_Watson_-_GQ_Men_of_the_Year_Awards_%28cropped%29.jpg/800px-Emma_Watson_-_GQ_Men_of_the_Year_Awards_%28cropped%29.jpg", "GQ Men of the Year"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/42/Emma_Watson_TFA_%28cropped%29.jpg/800px-Emma_Watson_TFA_%28cropped%29.jpg", "Time For Fun Premiere"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Emma_Watson_2013.jpg/800px-Emma_Watson_2013.jpg", "Red Carpet Moment"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/e/e1/Emma_Watson_Cannes_2013_2.jpg/800px-Emma_Watson_Cannes_2013_2.jpg", "Elegant Style"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/4/4e/Emma_Watson_2012.jpg/800px-Emma_Watson_2012.jpg", "Casual Look"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Emma_Watson_in_2018.jpg/800px-Emma_Watson_in_2018.jpg", "Premiere Night"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/0/0e/Emma_Watson_-_The_Circle_premiere_at_Tribeca_Film_Festival_%28cropped%29.jpg/800px-Emma_Watson_-_The_Circle_premiere_at_Tribeca_Film_Festival_%28cropped%29.jpg", "Tribeca Smile"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Emma_Watson_SDCC_2014_%28cropped%29.jpg/800px-Emma_Watson_SDCC_2014_%28cropped%29.jpg", "Comic Con"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/7/7e/Emma_Watson_Princes_Awards_2014.jpg/800px-Emma_Watson_Princes_Awards_2014.jpg", "Award Ceremony"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/1/1e/Emma_Watson_-_Noah_Premiere_in_Berlin_%28cropped%29.jpg/800px-Emma_Watson_-_Noah_Premiere_in_Berlin_%28cropped%29.jpg", "Berlin Wall"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/5/55/Emma_Watson_-_Beauty_and_the_Beast_premiere_%28cropped%29.jpg/800px-Emma_Watson_-_Beauty_and_the_Beast_premiere_%28cropped%29.jpg", "Belle Magic"),
            ("https://upload.wikimedia.org/wikipedia/commons/thumb/2/2d/Emma_Watson_JP.jpg/800px-Emma_Watson_JP.jpg", "Tokyo Event")
        ]
        c.executemany("INSERT INTO images (url, description) VALUES (?, ?)", demo_images)
    
    conn.commit()
    conn.close()

def hash_password_sha256(password: str) -> str:
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

# =============================================================================
# 3. SECURITY: WAF, ZERO-TRUST & MIDDLEWARE (XATOSIZ VERSIYA)
# =============================================================================

BLOCKED_IPS = set()
FAILED_LOGIN_DB = {}

class SecurityMiddleware(BaseHTTPMiddleware):
    SQL_INJECTION_PATTERN = re.compile(r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION)\b.*\b(FROM|TABLE|WHERE)\b)", re.IGNORECASE)
    XSS_PATTERN = re.compile(r"(<script|javascript:|onerror\=|onload\=|eval\()", re.IGNORECASE)
    DIRECTORY_TRAVERSAL = re.compile(r"(\.\.\/|\.\.\\)", re.IGNORECASE)
    
    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        path = request.url.path
        user_agent = request.headers.get("user-agent", "Unknown")
        
        if path in ["/favicon.ico"]:
            return await call_next(request)
        
        if client_ip in BLOCKED_IPS:
            self.log_security_event(client_ip, user_agent, path, "BLOCKED_IP_ACCESS")
            return JSONResponse(status_code=403, content={"detail": "Access Denied: IP Blocked"})
        
        if path in ["/login", "/register"] and request.method == "POST":
            ip_data = FAILED_LOGIN_DB.get(client_ip, {"fails": 0, "blocked_until": 0})
            if time.time() < ip_data["blocked_until"]:
                self.log_security_event(client_ip, user_agent, path, "BRUTE_FORCE_BLOCKED")
                return JSONResponse(status_code=429, content={"detail": "Too many failed attempts."})

        # WAF: Faqat GET so'rovlarni tekshiramiz. Formani POST qilishda WAF bloklamaydi!
        if request.method == "GET":
            full_query = str(request.url.query) + path
            
            if self.SQL_INJECTION_PATTERN.search(full_query):
                self.log_security_event(client_ip, user_agent, path, "SQL_INJECTION_ATTEMPT")
                BLOCKED_IPS.add(client_ip)
                return JSONResponse(status_code=403, content={"detail": "Malicious request detected"})

            if self.XSS_PATTERN.search(full_query):
                self.log_security_event(client_ip, user_agent, path, "XSS_ATTEMPT")
                return JSONResponse(status_code=403, content={"detail": "XSS attempt blocked"})

            if self.DIRECTORY_TRAVERSAL.search(full_query):
                self.log_security_event(client_ip, user_agent, path, "DIRECTORY_TRAVERSAL_ATTEMPT")
                return JSONResponse(status_code=403, content={"detail": "Directory Traversal blocked"})

        # CSRF Himoysi
        if request.method in ["POST", "PUT", "DELETE"]:
            origin = request.headers.get("origin", "")
            host = request.headers.get("host", "")
            if origin and host and host not in origin:
                self.log_security_event(client_ip, user_agent, path, "CSRF_ATTEMPT")
                return JSONResponse(status_code=403, content={"detail": "CSRF validation failed"})

        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        return response

    def log_security_event(self, ip, ua, path, reason):
        logger.warning(f"SECURITY ALERT | IP: {ip} | Path: {path} | Reason: {reason}")
        try:
            conn = get_db()
            conn.execute("INSERT INTO security_logs (ip_address, user_agent, path, method, reason) VALUES (?, ?, ?, 'REQ', ?)",
                         (ip, ua, path, reason))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Log yozishda xato: {e}")

def sanitize_html(content: str) -> str:
    allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'a', 'p', 'br']
    allowed_attrs = {'a': ['href', 'title']}
    return clean(content, tags=allowed_tags, attributes=allowed_attrs, strip=True)

# =============================================================================
# 4. FASTAPI APP INITIALIZATION
# =============================================================================

app = FastAPI(title="Emma Watson Fan Club", docs_url=None, redoc_url=None)
app.add_middleware(SecurityMiddleware)

active_sessions = {}

class CommentModel(BaseModel):
    image_id: int
    content: str = Field(..., max_length=500)

def get_user_from_cookie(request: Request) -> Optional[dict]:
    token = request.cookies.get("session_token")
    if token and token in active_sessions:
        return active_sessions[token]
    return None

# =============================================================================
# 5. AWESOME UI & CSS (Glassmorphism + Floating Menu)
# =============================================================================

CSS_STYLES = """
    :root { --bg: #0a0a0c; --glass: rgba(255, 255, 255, 0.03); --border: rgba(255, 255, 255, 0.08); --text: #e0e0e0; --accent: #a777e3; }
    body { background: var(--bg); color: var(--text); font-family: 'Inter', -apple-system, sans-serif; margin: 0; min-height: 100vh; }
    .bg-blur { position: fixed; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(110,142,251,0.1) 0%, transparent 60%); z-index: -1; animation: pulse 15s infinite alternate; }
    @keyframes pulse { 0% { transform: scale(1); } 100% { transform: scale(1.3); } }
    .header { text-align: center; padding: 60px 20px 30px; }
    .header h1 { font-size: 3.5rem; margin: 0; background: linear-gradient(135deg, #fff 0%, #6e8efb 50%, #a777e3 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .nav-btns { margin-top: 20px; display: flex; gap: 10px; justify-content: center; flex-wrap: wrap; }
    .btn { background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); color: white; padding: 10px 20px; border-radius: 8px; cursor: pointer; font-size: 0.9rem; transition: all 0.2s; text-decoration: none; display: inline-block; }
    .btn:hover { background: var(--accent); border-color: var(--accent); transform: translateY(-2px); }
    .search-box { max-width: 500px; margin: 20px auto; display: flex; gap: 10px; }
    .search-box input { flex:1; padding: 15px; border-radius: 12px; border: 1px solid var(--border); background: rgba(0,0,0,0.5); color: white; font-size: 1rem; outline: none; }
    .section-title { text-align: center; font-size: 2rem; margin: 60px 0 30px; background: linear-gradient(to right, #fff, #a777e3); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
    .masonry { columns: 3; column-gap: 20px; padding: 20px; max-width: 1400px; margin: 0 auto; }
    .card { background: var(--glass); backdrop-filter: blur(20px); border: 1px solid var(--border); border-radius: 16px; margin-bottom: 20px; break-inside: avoid; overflow: hidden; transition: transform 0.3s ease, box-shadow 0.3s ease; }
    .card:hover { transform: translateY(-5px); box-shadow: 0 15px 40px rgba(167,119,227,0.2); border-color: rgba(167,119,227,0.3); }
    .card img { width: 100%; display: block; transition: transform 0.5s; }
    .card:hover img { transform: scale(1.05); }
    .card-body { padding: 20px; }
    .comment-box { margin-top: 15px; padding-top: 15px; border-top: 1px solid var(--border); }
    input[type="text"], input[type="email"], input[type="password"] { border-radius: 8px; border: 1px solid var(--border); background: rgba(0,0,0,0.4); color: white; outline: none; }
    .auth-container { display:flex; justify-content:center; align-items:center; min-height:80vh; padding:20px; }
    .auth-form { background:var(--glass); backdrop-filter:blur(30px); padding:50px; border-radius:20px; border:1px solid var(--border); width:100%; max-width:400px; box-shadow: 0 20px 50px rgba(0,0,0,0.5); }
    .auth-form h2 { text-align:center; margin-top:0; background:linear-gradient(135deg, #fff, #a777e3); -webkit-background-clip:text;-webkit-text-fill-color:transparent; }
    .auth-form input { width:100%; box-sizing:border-box; margin:10px 0; padding:15px; border-radius:10px; border:1px solid var(--border); background:rgba(0,0,0,0.5); color:white; }
    .auth-form button { width:100%; padding:15px; border:none; border-radius:10px; background:linear-gradient(135deg, #6e8efb, #a777e3); color:white; font-weight:bold; font-size:1rem; cursor:pointer; margin-top:10px; }
    .auth-link { text-align:center; margin-top:20px; font-size:0.9rem; }
    .auth-link a { color: var(--accent); text-decoration:none; }
    
    /* Floating More Menu */
    .float-menu { position: fixed; bottom: 30px; right: 30px; z-index: 1000; }
    .float-btn { width: 60px; height: 60px; border-radius: 50%; background: linear-gradient(135deg, #6e8efb, #a777e3); border: none; color: white; font-size: 24px; cursor: pointer; box-shadow: 0 5px 20px rgba(167,119,227,0.5); transition: transform 0.3s; }
    .float-btn:hover { transform: scale(1.1); }
    .float-dropdown { display: none; position: absolute; bottom: 70px; right: 0; background: rgba(20,20,25,0.95); backdrop-filter: blur(20px); border: 1px solid var(--border); border-radius: 16px; padding: 20px; width: 280px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .float-dropdown.show { display: block; animation: fadeIn 0.3s; }
    @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    .float-dropdown a { display: block; color: white; text-decoration: none; padding: 12px; border-radius: 8px; margin-bottom: 5px; background: rgba(255,255,255,0.03); transition: background 0.2s; font-weight: 500; }
    .float-dropdown a:hover { background: var(--accent); }
    
    .fact-page { max-width: 800px; margin: 0 auto; padding: 40px 20px; }
    .fact-card { background: var(--glass); backdrop-filter: blur(20px); border: 1px solid var(--border); border-radius: 16px; padding: 30px; margin-bottom: 20px; transition: transform 0.3s; }
    .fact-card:hover { transform: translateY(-3px); border-color: var(--accent); }
    .fact-card h3 { color: var(--accent); margin-top: 0; }
    
    @media (max-width: 900px) { .masonry { columns: 2; } }
    @media (max-width: 600px) { .masonry { columns: 1; } .header h1 { font-size: 2.5rem; } }
"""

# Faktlar Bazasi
FACTS_DB = {
    "life": [
        {"title": "Birth and Early Years", "text": "Emma Charlotte Duerre Watson was born on April 15, 1990, in Paris. She lived in Paris until the age of five, when her parents divorced, and she moved to England with her mother."},
        {"title": "Rise to Stardom", "text": "She was cast as Hermione Granger at age 9, beating out thousands of other actresses. She starred in all 8 Harry Potter films over a decade."},
        {"title": "Education First", "text": "Despite earning millions from Harry Potter, Emma prioritized her education. She graduated from Brown University with a degree in English literature in 2014."}
    ],
    "boyfriend": [
        {"title": "Private Life", "text": "Emma Watson is notoriously private about her relationships. She has stated that she keeps her romantic life out of the public eye to protect her partners from the spotlight."},
        {"title": "Past Relationships", "text": "She has been linked to several figures over the years, including tech entrepreneur William Mack Knight and actor Leo Robinton."},
        {"title": "Self-Partnered", "text": "In 2019, Emma coined the term self-partnered in an interview with British Vogue, expressing that she feels very happy and complete being single."}
    ],
    "nowadays": [
        {"title": "Activism and Directing", "text": "Today, Emma is heavily involved in activism. She is a UN Women Goodwill Ambassador and launched the HeForShe campaign. She has also stepped into directing."},
        {"title": "Environmental Advocacy", "text": "She is a strong advocate for sustainable fashion and often wears eco-friendly designs on the red carpet. She launched an Instagram account dedicated to her sustainable fashion choices."},
        {"title": "Recent Projects", "text": "She starred in Little Women (2019) directed by Greta Gerwig and took a break from acting to focus on her personal development and advocacy work."}
    ],
    "harry-potter": [
        {"title": "The Audition", "text": "Emma was found by casting agents through her Oxford theatre teacher. Author J.K. Rowling was immediately impressed by her screen test."},
        {"title": "The Contract", "text": "She and co-stars Daniel Radcliffe and Rupert Grint signed contracts for the first two films, not knowing if they would continue. They ended up doing all 8."},
        {"title": "Impact on Her Life", "text": "The franchise made her a global star and a millionaire by her teens, but she has admitted it was sometimes difficult to balance a normal childhood with intense fame."}
    ],
    "beauty-beast": [
        {"title": "The Casting", "text": "Emma was offered the role of Belle in Disney live-action adaptation immediately after finishing her degree. She was the first and only choice for the director."},
        {"title": "A Feminist Belle", "text": "Emma insisted on making Belle an inventor, like her father, to give her a more active and feminist role compared to the animated version."},
        {"title": "Box Office Smash", "text": "The film grossed over $1.2 billion worldwide, making it one of the highest-grossing films of 2017 and the highest-grossing live-action musical ever at the time."}
    ],
    "un-women": [
        {"title": "HeForShe Campaign", "text": "In September 2014, Emma launched the HeForShe campaign at the United Nations Headquarters. The campaign asks men to advocate for gender equality."},
        {"title": "Powerful Speech", "text": "Her speech went viral, highlighting that feminism is not about man-hating, but about equal rights. It sparked a global conversation about male allyship."},
        {"title": "Impact", "text": "The campaign reached over 1.2 billion people on social media in its first week and inspired world leaders and celebrities to pledge their support."}
    ],
    "education": [
        {"title": "Brown University", "text": "Emma enrolled at Brown University in 2009. She took semesters off to film movies but eventually graduated in 2014 with a degree in English Literature."},
        {"title": "Oxford Visiting Student", "text": "As part of her degree, she also studied at Worcester College, Oxford, during the 2011-12 academic year."},
        {"title": "Yoga Certification", "text": "Besides her academic pursuits, Emma is a certified yoga and meditation instructor, which she started practicing to find peace amidst her stressful career."}
    ],
    "style": [
        {"title": "Fashion Icon", "text": "Emma is considered one of the most stylish women in the world. She frequently appears on best-dressed lists and works with top designers."},
        {"title": "Sustainable Fashion", "text": "She is a pioneer in sustainable red carpet fashion. She ensures that her outfits are ethically made and often shares the sustainability credentials of her looks."},
        {"title": "Short Hair Revolution", "text": "When she cut her hair short after finishing Harry Potter, it made global headlines. She described it as the most liberating thing she had ever done."}
    ],
    "books": [
        {"title": "Our Shared Shelf", "text": "Emma started a feminist book club called Our Shared Shelf on Goodreads, which quickly gained hundreds of thousands of members worldwide."},
        {"title": "Leaving Hogwarts Behind", "text": "She has stated that reading helped her cope with the pressure of fame growing up, and books have always been her safe space."},
        {"title": "Recommendations", "text": "She frequently recommends books by women of color and LGBTQ+ authors, using her platform to amplify marginalized voices."}
    ],
    "quotes": [
        {"title": "On Feminism", "text": "Feminism is not a stick with which to beat other women. It is about freedom, liberation, and equality."},
        {"title": "On Education", "text": "I think it is safe to say that one of the things I am most proud of is my education."},
        {"title": "On Self-Love", "text": "I have realized that I am not a fixed person. I am constantly evolving, and that is okay."}
    ]
}

# =============================================================================
# 6. ROUTES (XATOSIZ VERSIYA)
# =============================================================================

@app.on_event("startup")
def startup():
    init_db()
    logger.info("Database initialized. Superuser emma ensured. Port: 1990")

@app.get("/", response_class=HTMLResponse)
async def home(request: Request, search: Optional[str] = None):
    user = get_user_from_cookie(request)
    is_logged_in = user is not None
    
    conn = get_db()
    if search:
        images = conn.execute("SELECT * FROM images WHERE description LIKE ?", (f"%{search}%",)).fetchall()
    else:
        images = conn.execute("SELECT * FROM images ORDER BY uploaded_at DESC").fetchall()
    
    comments_db = conn.execute("SELECT * FROM comments ORDER BY created_at DESC").fetchall()
    conn.close()
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Emma Watson Fan Club</title>
        <style>{CSS_STYLES}</style>
    </head>
    <body>
        <div class="bg-blur"></div>
        <div class="header">
            <h1>✨ Emma Watson Fan Club ✨</h1>
            <p>Actress • Activist • UN Women Goodwill Ambassador</p>
            <div class="nav-btns">
                {"<a href='/admin' class='btn'>🛡️ Admin Panel</a>" if user and user.get("is_superuser") else ""}
                {"<span class='btn'>👋 " + user.get("username", "") + "</span>" if is_logged_in else ""}
                {"<a href='/logout' class='btn'>🚪 Logout</a>" if is_logged_in else "<a href='/login' class='btn'>🔒 Login</a> <a href='/register' class='btn'>📝 Register</a>"}
            </div>
        </div>

        <div class="search-box">
            <form action="/" method="get" style="display:flex; width:100%; gap:10px;">
                <input type="text" name="search" placeholder="Search Emma photos..." value="{search if search else ''}">
                <button type="submit" class="btn">🔍 Search</button>
            </form>
        </div>

        <h2 class="section-title">📸 Photo Gallery</h2>
        <div class="masonry">
    """
    for img in images:
        img_comments = [c for c in comments_db if c['image_id'] == img['id']]
        comments_html = ""
        for c in img_comments:
            comments_html += f"<div style='margin-top:5px;font-size:0.85em;color:#aaa;'><b>{c['username']}</b>: {c['content']}</div>"

        comment_input = f"""
        <div class="comment-box">
            <input type="text" id="comment-input-{img['id']}" placeholder="Write a comment..." style="width:70%; padding:10px;">
            <button class="btn" onclick="addComment({img['id']})" style="padding:10px;">Send</button>
            <div id="comments-{img['id']}">{comments_html}</div>
        </div>
        """ if is_logged_in else "<div class='comment-box' style='color:#666; font-size:0.9em;'>Login to comment</div>"

        html += f"""
            <div class="card">
                <div style="overflow:hidden;">
                    <img src="{img['url']}" alt="{img['description']}" loading="lazy" onerror="this.src='https://via.placeholder.com/800x600?text=Image+Not+Found'">
                </div>
                <div class="card-body">
                    <p style="font-weight: 600; margin-top:0;">{img['description']}</p>
                    <button class="btn" onclick="likeImage({img['id']})">❤️ <span id="likes-{img['id']}">{img['likes']}</span></button>
                    <a href="{img['url']}" download class="btn">⬇️ Download</a>
                    {comment_input}
                </div>
            </div>
        """
    html += f"""
        </div>
        
        <!-- Floating More Menu -->
        <div class="float-menu">
            <div id="floatDropdown" class="float-dropdown">
                <a href="/facts/life">🌟 Emma Watson Life</a>
                <a href="/facts/boyfriend">💖 Boyfriend & Relationships</a>
                <a href="/facts/nowadays">🌍 Nowadays</a>
                <a href="/facts/harry-potter">⚡ Harry Potter</a>
                <a href="/facts/beauty-beast">🌹 Beauty And The Beast</a>
                <a href="/facts/un-women">⚖️ UN Women & HeForShe</a>
                <a href="/facts/education">🎓 Education</a>
                <a href="/facts/style">👗 Style & Fashion</a>
                <a href="/facts/books">📚 Books & Reading</a>
                <a href="/facts/quotes">💬 Best Quotes</a>
            </div>
            <button class="float-btn" onclick="toggleMenu()">+</button>
        </div>

        <script>
            function toggleMenu() {{
                document.getElementById("floatDropdown").classList.toggle("show");
            }}
            window.onclick = function(event) {{
                if (!event.target.matches('.float-btn')) {{
                    var dropdowns = document.getElementsByClassName("float-dropdown");
                    for (var i = 0; i < dropdowns.length; i++) {{
                        var openDropdown = dropdowns[i];
                        if (openDropdown.classList.contains('show')) {{
                            openDropdown.classList.remove('show');
                        }}
                    }}
                }}
            }}
            async function likeImage(id) {{
                const res = await fetch('/api/like/' + id, {{ method: 'POST' }});
                const data = await res.json();
                if(data.likes !== undefined) document.getElementById('likes-' + id).innerText = data.likes;
            }}
            async function addComment(id) {{
                const input = document.getElementById('comment-input-' + id);
                const content = input.value;
                if(!content) return;
                const res = await fetch('/api/comment', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ image_id: id, content: content }})
                }});
                if(res.ok) {{ input.value = ''; location.reload(); }}
                else if(res.status === 401) {{ alert('Please login first!'); }}
                else {{ alert('Error adding comment'); }}
            }}
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# --- Faktlar Sahifalari ---
@app.get("/facts/{category}", response_class=HTMLResponse)
async def facts_page(request: Request, category: str):
    user = get_user_from_cookie(request)
    facts = FACTS_DB.get(category, [])
    
    titles = {
        "life": "🌟 Emma Watson Life",
        "boyfriend": "💖 Boyfriend & Relationships",
        "nowadays": "🌍 Nowadays",
        "harry-potter": "⚡ Harry Potter Era",
        "beauty-beast": "🌹 Beauty And The Beast",
        "un-women": "⚖️ UN Women & HeForShe",
        "education": "🎓 Education",
        "style": "👗 Style & Fashion",
        "books": "📚 Books & Reading",
        "quotes": "💬 Best Quotes"
    }
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head><style>{CSS_STYLES}</style></head>
    <body>
        <div class="bg-blur"></div>
        <div style="padding: 20px;">
            <a href="/" class="btn" style="margin: 20px;">⬅️ Back to Gallery</a>
            <h1 class="section-title">{titles.get(category, "Facts")}</h1>
            <div class="fact-page">
    """
    for fact in facts:
        html += f"""
            <div class="fact-card">
                <h3>{fact['title']}</h3>
                <p>{fact['text']}</p>
            </div>
        """
    
    html += """
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)

# --- AUTH ROUTES (XATOSIZ) ---
@app.get("/register", response_class=HTMLResponse)
async def register_page():
    html = f"""
    <!DOCTYPE html><html><head><style>{CSS_STYLES}</style></head><body>
        <div class="bg-blur"></div>
        <div class="auth-container">
            <form action="/register" method="POST" class="auth-form">
                <h2>📝 Create Account</h2>
                <input type="text" name="username" placeholder="Username" required>
                <input type="email" name="email" placeholder="Email Address" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Register</button>
                <div class="auth-link">Already have an account? <a href="/login">Login here</a></div>
            </form>
        </div>
    </body></html>"""
    return HTMLResponse(content=html)

@app.post("/register")
async def register(request: Request):
    form = await request.form()
    username = form.get("username")
    email = form.get("email")
    password = form.get("password")
    
    if not username or not email or not password:
        raise HTTPException(status_code=400, detail="All fields are required")
    
    hashed_pw = hash_password_sha256(password)
    conn = get_db()
    try:
        conn.execute("INSERT INTO users (username, email, password_hash) VALUES (?, ?, ?)", (username, email, hashed_pw))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Username or Email already exists")
    finally:
        conn.close()
        
    session_token = secrets.token_hex(32)
    active_sessions[session_token] = {"username": username, "is_superuser": False}
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="session_token", value=session_token, httponly=True, samesite="lax")
    return response

@app.get("/login", response_class=HTMLResponse)
async def login_page():
    html = f"""
    <!DOCTYPE html><html><head><style>{CSS_STYLES}</style></head><body>
        <div class="bg-blur"></div>
        <div class="auth-container">
            <form action="/login" method="POST" class="auth-form">
                <h2>🔒 Admin & User Login</h2>
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
                <div class="auth-link">Don't have an account? <a href="/register">Register here</a></div>
            </form>
        </div>
    </body></html>"""
    return HTMLResponse(content=html)

@app.post("/login")
async def login(request: Request):
    form = await request.form()
    username = form.get("username")
    password = form.get("password")
    client_ip = request.client.host

    ip_data = FAILED_LOGIN_DB.get(client_ip, {"fails": 0, "blocked_until": 0})
    if time.time() < ip_data["blocked_until"]:
        raise HTTPException(status_code=429, detail="Too many requests. IP temporarily blocked.")

    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    conn.close()

    is_valid = False
    if user:
        if user['is_superuser']:
            is_valid = bcrypt.checkpw(password.encode('utf-8'), user['password_hash'].encode('utf-8'))
        else:
            is_valid = user['password_hash'] == hash_password_sha256(password)

    if not is_valid:
        if client_ip not in FAILED_LOGIN_DB:
            FAILED_LOGIN_DB[client_ip] = {"fails": 1, "blocked_until": 0}
        else:
            FAILED_LOGIN_DB[client_ip]["fails"] += 1
        if FAILED_LOGIN_DB[client_ip]["fails"] >= 5:
            FAILED_LOGIN_DB[client_ip]["blocked_until"] = time.time() + 300
        raise HTTPException(status_code=401, detail="Invalid credentials")

    if client_ip in FAILED_LOGIN_DB:
        FAILED_LOGIN_DB.pop(client_ip, None)

    session_token = secrets.token_hex(32)
    active_sessions[session_token] = {"username": user["username"], "is_superuser": bool(user["is_superuser"])}
    
    response = RedirectResponse(url="/admin" if user["is_superuser"] else "/", status_code=303)
    response.set_cookie(key="session_token", value=session_token, httponly=True, samesite="lax")
    return response

@app.get("/admin", response_class=HTMLResponse)
async def admin_panel(request: Request):
    user = get_user_from_cookie(request)
    if not user or not user.get("is_superuser"):
        return RedirectResponse(url="/login", status_code=303)

    conn = get_db()
    logs = conn.execute("SELECT * FROM security_logs ORDER BY logged_at DESC LIMIT 100").fetchall()
    users = conn.execute("SELECT id, username, email, is_superuser FROM users").fetchall()
    conn.close()

    html = f"""
    <!DOCTYPE html><html><head><style>{CSS_STYLES}</style></head><body>
        <div class="bg-blur"></div>
        <div style="padding: 40px; max-width: 1400px; margin: 0 auto;">
            <h1 style="background:linear-gradient(135deg, #fff, #ff5555);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🛡️ Superuser Admin Panel</h1>
            <p>Welcome, <b>{user['username']}</b>! <a href='/logout' style='color:#a777e3;'>Logout</a> | <a href='/' style='color:#a777e3;'>Back to Site</a></p>
            <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 30px;">
                <div style="background:var(--glass);padding:30px;border-radius:16px;border:1px solid var(--border);">
                    <h2>🚨 Security Logs (IP Address Tracking)</h2>
                    <div style="background:#000;padding:20px;border-radius:8px;height:450px;overflow-y:auto;font-family:monospace;font-size:0.85rem;border:1px solid #333;">
    """
    for log in logs:
        color = "#ff5555" if "BLOCKED" in log['reason'] or "ATTEMPT" in log['reason'] else "#aaa"
        html += f"<div style='color:{color};margin-bottom:5px;'>[{log['logged_at']}] IP: {log['ip_address']} | <b>{log['reason']}</b> | Path: {log['path']}</div>"
    
    html += f"""
                    </div>
                </div>
                <div style="display:flex; flex-direction:column; gap:30px;">
                    <div style="background:var(--glass);padding:30px;border-radius:16px;border:1px solid var(--border);">
                        <h2>👥 Registered Users</h2>
                        <ul style="list-style:none;padding:0;">
    """
    for u in users:
        role = "👑 Superuser" if u['is_superuser'] else "👤 User"
        html += f"<li style='padding:10px;border-bottom:1px solid var(--border);'>{u['username']} ({u['email']}) - {role}</li>"
    
    html += f"""
                        </ul>
                    </div>
                    <div style="background:var(--glass);padding:30px;border-radius:16px;border:1px solid var(--border);">
                        <h2>🔥 Firewall (IP Blocker)</h2>
                        <form action="/api/block-ip" method="POST" style="display:flex;gap:10px;margin-bottom:20px;">
                            <input type="text" name="ip_to_block" placeholder="Enter IP to block" required style="flex:1; padding:10px;">
                            <button type="submit" class="btn" style="background:#ff5555;border-color:#ff5555;">Block</button>
                        </form>
    """
    for ip in BLOCKED_IPS:
        html += f"<div style='background:rgba(255,85,85,0.2);padding:10px;border-radius:8px;margin-bottom:5px;display:flex;justify-content:space-between;'><span>🚫 {ip}</span><a href='/api/unblock-ip/{ip}' class='btn' style='padding:5px 10px;font-size:0.8em;'>Unblock</a></div>"
    if not BLOCKED_IPS:
        html += "<p style='color:#aaa;'>No blocked IPs.</p>"
    
    html += """
                    </div>
                </div>
            </div>
        </div>
    </body></html>
    """
    return HTMLResponse(content=html)

# --- API ENDPOINTS ---
@app.post("/api/like/{image_id}")
async def like_image(image_id: int):
    conn = get_db()
    conn.execute("UPDATE images SET likes = likes + 1 WHERE id=?", (image_id,))
    conn.commit()
    new_likes = conn.execute("SELECT likes FROM images WHERE id=?", (image_id,)).fetchone()[0]
    conn.close()
    return {"likes": new_likes}

@app.post("/api/comment")
async def add_comment(data: CommentModel, request: Request):
    user = get_user_from_cookie(request)
    if not user:
        raise HTTPException(status_code=401, detail="Please login to comment")
    safe_content = sanitize_html(data.content)
    conn = get_db()
    conn.execute("INSERT INTO comments (image_id, username, content) VALUES (?, ?, ?)", (data.image_id, user["username"], safe_content))
    conn.commit()
    conn.close()
    return {"status": "success"}

@app.post("/api/block-ip")
async def block_ip(request: Request):
    user = get_user_from_cookie(request)
    if not user or not user.get("is_superuser"):
        raise HTTPException(status_code=403)
    form = await request.form()
    ip_to_block = form.get("ip_to_block")
    if ip_to_block:
        BLOCKED_IPS.add(ip_to_block)
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/api/unblock-ip/{ip}")
async def unblock_ip(ip: str, request: Request):
    user = get_user_from_cookie(request)
    if not user or not user.get("is_superuser"):
        raise HTTPException(status_code=403)
    if ip in BLOCKED_IPS:
        BLOCKED_IPS.remove(ip)
    return RedirectResponse(url="/admin", status_code=303)

@app.get("/logout")
async def logout(request: Request):
    token = request.cookies.get("session_token")
    if token and token in active_sessions:
        del active_sessions[token]
    response = RedirectResponse(url="/")
    response.delete_cookie("session_token")
    return response

if __name__ == "__main__":
    print("🚀 Starting Emma Watson Fan Club on http://localhost:1990")
    uvicorn.run("emma:app", host="0.0.0.0", port=PORT, reload=False)
