# Ta'lim Platformasi - Web Deployment Files

## To'liq Ishlaydigan Fayllar

Bu arxivda Render.com ga deploy qilish uchun barcha kerakli fayllar mavjud.

## Login Ma'lumotlari
- **Username:** `AkmalJaxonkulov`
- **Password:** `Akmal1221`

## Fayllar Tarkibi

### 1. `app.py` - Asosiy Flask ilovasi
- Session-based authentication
- SQLite database
- Admin user creation
- Debug logging

### 2. `requirements.txt` - Python dependentsiyalari
```
Flask==2.3.3
Flask-SQLAlchemy==2.5.1
Flask-Login==0.6.3
Flask-WTF==1.1.1
WTForms==3.0.1
Werkzeug==2.3.7
SQLAlchemy==1.4.53
bcrypt==4.0.1
python-dotenv==1.0.0
Jinja2==3.1.2
email-validator==2.0.0
gunicorn==20.1.0
```

### 3. `templates/` - HTML shablonlari
- `login.html` - Login sahifasi
- `simple_admin_dashboard.html` - Admin panel

### 4. `Procfile` - Gunicorn uchun
- Production WSGI server sozlamasi

### 5. `gunicorn_start.py` - Backup start skripti

## Deploy Qilish

1. GitHub ga yuklang
2. Render.com da yangi Web Service yarating
3. GitHub repo ulang
4. Manual Deploy qiling

## Xususiyatlar

- **Xavfsiz Login** - Admin ma'lumotlari ko'rinmaydi
- **Session Management** - To'g'ri ishlaydi
- **Database** - Auto creation
- **Debug Logging** - Barcha jarayon ko'rsatiladi
- **Production Ready** - Gunicorn bilan

## URL
Deploy qilingandan so'ng: `https://sizning-project.onrender.com`

---

Yaratilgan: 2026-04-14
Version: Final Working
