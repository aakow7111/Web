#!/usr/bin/env python
"""
Update admin login from admin/admin123 to AkmalJaxonkulov/Akmal1221
"""

from app import app, db, User, generate_password_hash

def update_admin():
    """Update admin user credentials"""
    with app.app_context():
        # Find old admin user
        old_admin = User.query.filter_by(username='admin').first()
        
        if old_admin:
            print("Eski admin user topildi: 'admin'")
            # Delete old admin
            db.session.delete(old_admin)
            db.session.commit()
            print("Eski admin user o'chirildi")
        
        # Create new admin user
        new_admin = User.query.filter_by(username='AkmalJaxonkulov').first()
        if not new_admin:
            new_admin = User(
                username='AkmalJaxonkulov',
                password_hash=generate_password_hash('Akmal1221'),
                first_name='Akmal',
                last_name='Jaxonkulov',
                group_id=1,
                is_admin=True
            )
            db.session.add(new_admin)
            db.session.commit()
            print("Yangi admin user yaratildi: AkmalJaxonkulov/Akmal1221")
        else:
            print("Yangi admin user allaqachon mavjud")
        
        print("Admin login muvaffaqiyatli yangilandi!")

if __name__ == "__main__":
    update_admin()
