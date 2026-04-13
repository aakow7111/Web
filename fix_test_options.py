#!/usr/bin/env python
"""
Fix test options format in database
Convert JSON format to pipe-separated format
"""

import json
import re
from app import app, db, Question

def fix_all_test_options():
    """Convert all test options from JSON to pipe-separated format"""
    with app.app_context():
        questions = Question.query.all()
        fixed_count = 0
        
        for question in questions:
            try:
                # Check if options are in JSON format
                if question.options.startswith('{'):
                    # Parse JSON
                    options_dict = json.loads(question.options)
                    
                    # Convert to pipe-separated format
                    option_values = []
                    for key in ['A', 'B', 'C', 'D']:
                        if key in options_dict:
                            option_values.append(options_dict[key])
                        else:
                            option_values.append(f"Option {key}")
                    
                    # Update with pipe-separated format
                    question.options = '|'.join(option_values)
                    fixed_count += 1
                    print(f"Fixed question {question.id}: {question.options}")
                    
            except Exception as e:
                print(f"Error fixing question {question.id}: {e}")
                continue
        
        # Commit changes
        db.session.commit()
        print(f"Fixed {fixed_count} questions total")

if __name__ == "__main__":
    fix_all_test_options()
