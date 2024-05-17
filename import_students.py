import json
from app import app
from app import db
from app import Students

def import_students():
    with open('students.json', 'r') as file:
        students_data = json.load(file)
        
    with app.app_context():
        for student_data in students_data:
            student = Students(
                student_class = student_data['student_class'],
                student_name = student_data['student_name'],
                student_number = student_data['student_number']    
            )
            db.session.add(student)
        db.session.commit()
        
if __name__ == '__main__':
    import_students()
