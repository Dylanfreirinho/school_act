from app import app, db
from app import Teacher
from werkzeug.security import generate_password_hash

def insert_user():
    password_hash = generate_password_hash('')
    
    teacher1 = Teacher(teacher_name='', user_name='', password=password_hash)
    # teacher2 = Teacher(teacher_name='', user_name='', password=password_hash)
    db.session.add(teacher1)
    
    db.session.commit()


if __name__ == '__main__':
    insert_user()