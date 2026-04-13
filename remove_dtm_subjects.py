#!/usr/bin/env python
"""
Remove DTM and DTM Umumiy subjects from database
"""

from app import app, db, Subject

def remove_dtm_subjects():
    """Remove DTM and DTM Umumiy subjects"""
    with app.app_context():
        # Find DTM subjects
        dtm_subjects = Subject.query.filter(
            Subject.name.in_(['DTM', 'DTM Umumiy'])
        ).all()
        
        removed_count = 0
        for subject in dtm_subjects:
            print(f"Removing subject: {subject.name}")
            db.session.delete(subject)
            removed_count += 1
        
        # Commit changes
        db.session.commit()
        print(f"Removed {removed_count} DTM subjects")

if __name__ == "__main__":
    remove_dtm_subjects()
