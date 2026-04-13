# Web Deployment Instructions

## 1. GitHub ga Yuklash

```bash
git init
git add .
git commit -m "Initial commit - Education Platform"
git branch -M main
git remote add origin https://github.com/USERNAME/REPO.git
git push -u origin main
```

## 2. Render.com da Deploy

1. **Yangi Web Service yarating**
   - Render.com ga kiring
   - "New +" -> "Web Service"
   - GitHub repo ulang

2. **Build Settings**
   - **Environment:** Python
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `gunicorn --bind 0.0.0.0:$PORT app:app`

3. **Environment Variables**
   - `SECRET_KEY`: `super-secret-key-for-sessions-to-work`

4. **Manual Deploy**
   - "Manual Deploy" tugmasini bosing
   - "Deploy Latest Commit" tanlang

## 3. Test Qilish

**URL:** `https://sizning-project.onrender.com`

**Login:**
- Username: `AkmalJaxonkulov`
- Password: `Akmal1221`

## 4. Agar Xatolik Bo'lsa

**Loglarni ko'ring:**
- Render.com -> Service -> Logs
- "All logs" tugmasini bosing

**Umumiy xatoliklar:**
- Database: SQLite avtomatik yaratiladi
- Session: SECRET_KEY tekshiring
- Dependencies: requirements.txt tekshiring

## 5. Muvaffaqiyat Alomatlari

- Build successful
- Login ishlaydi
- Admin dashboard ochiladi
- Statistika ko'rsatiladi

---

**Platform tayyor!** Endi foydalanishingiz mumkin.
