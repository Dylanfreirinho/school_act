import datetime
import io
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, Response, flash
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash
import json
import csv


# de flask app object
app = Flask(__name__)
# creeert een app context
#push zorgt ervoor dat de context actief is
app.app_context().push()

#database instellingen
app.config['SECRET_KEY'] = 'hgrijiw23fddgfgj@hdbg21lehjg'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///act1.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
# variabele db die de SWLAlchemy object creeert
db = SQLAlchemy()
# de database wordt geinitialiseerd met de app
db.init_app(app)

#tabel voor statements met de keuzes
class Students(db.Model):
    student_number = db.Column(db.Integer, primary_key=True)
    student_name = db.Column(db.String(100), nullable=False)
    student_class = db.Column(db.String(2), nullable=False)
    team = db.Column(db.String(50))
    action_type = db.Column(db.String(50))
    
    def __repr__(self):
        return f"<Response {self.student_number}"
    
    def serialize(self):
        return {
            'student_number': self.student_number,
            'student_name': self.student_name,
            'student_class': self.student_class,
            'team': self.team,
            'action_type': self.action_type
        }

class Statements(db.Model):
    statement_number = db.Column(db.Integer, nullable=False, primary_key=True)
    choice_number = db.Column(db.Integer, nullable=False, primary_key=True)
    choice_text = db.Column(db.String, nullable=False)
    choice_result = db.Column(db.String, nullable=False)
    
    def __repr__(self):
        return f"<Statement ({self.statement_number}, {self.choice_number})>"
    
    # __table_args__ = (
    #     db.PrimaryKeyConstraint('statement_number', 'choice_number'),
    #     )
    
class StudentAnswer(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_number = db.Column(db.Integer, db.ForeignKey('students.student_number'))
    statement_number = db.Column(db.Integer, db.ForeignKey('statements.statement_number'))
    choice_result = db.Column(db.String)
    
#tabel voor de docenten    
class Teacher(db.Model):
    id_teacher = db.Column(db.Integer, primary_key=True, autoincrement=True)
    teacher_name = db.Column(db.String(100), nullable=False)
    user_name = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(50), nullable=False)
    
    def __repr__(self):
        return f"<Teacher {self.user_name}>"

# een route voor de begin pagina
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/student_login')
def student_login():
    return render_template('student_login.html')
    

@app.route('/act_form')
def act_form():
    return render_template('act_forms.html')

@app.route('/check_student', methods=['POST'])
def student_check():
    student_number = request.form.get('student_number')
    student = Students.query.filter_by(student_number=student_number).first()
    if not student:
        flash('studentnummer bestaat niet', 'error')
        return redirect(url_for('student_login'))
    
    student_answers = StudentAnswer.query.filter_by(student_number=student_number).all()
    if student_answers:
        flash('Je hebt de test al gedaan', 'info')
        return redirect(url_for('index'))
    
    total_statements = Statements.query.count()
    first_statement = Statements.query.filter_by(statement_number=1).first()
    return render_template('act_forms.html', student=student, statement=first_statement)


@app.route('/api/student/<int:student_number>/statement', methods=['GET'])
def get_student_statement(student_number):
    statements = db.session.query(Statements).filter(
        ~Statements.statement_number.in_(
            db.session.query(StudentAnswer.statement_number).filter_by(student_number=student_number)
        )
    ).order_by(Statements.statement_number).all()

    if statements:
        first_choice = statements[0]
        second_choice = statements[1]
        statement_data = {
            'statement_number': first_choice.statement_number,
            'statement_choices': [
                {
                    'choice_number': first_choice.choice_number,
                    "choice_text": first_choice.choice_text
                },     {
                    'choice_number': second_choice.choice_number,
                    "choice_text": second_choice.choice_text
                } 
            ]
        }
        return jsonify(statement_data), 200
    else:
        return jsonify({'message': 'No more statements'}), 404
    
@app.route('/api/student/<int:student_number>/statement/<int:statement_number>/<int:choice_number>', methods=['POST'])
def save_student_choice(student_number, statement_number, choice_number):
    statement_choice = choice_number
    
    if not statement_choice:
        return jsonify({'message': 'no tsatement choice provided'}), 400
    
    statement = Statements.query.filter_by(statement_number=statement_number, choice_number=choice_number).first()
    if not statement:
        return jsonify({'message': 'statement does not exist'}), 404
    
    if statement_choice not in [1, 2]:
        return jsonify({'message': 'invalid statement choice'}), 400
    
    student_choice = StudentAnswer(
        student_number=student_number,
        statement_number=statement.statement_number,
        choice_result=statement.choice_result
    )
    db.session.add(student_choice)
    db.session.commit()
    
    answered_statements_count = StudentAnswer.query.filter_by(student_number=student_number).count()
    action_type = None
    
    if answered_statements_count >= 20:
        action_type = calculate_action_type(student_number)
        student = Students.query.get(student_number)
        if student:
            student.action_type = action_type
            db.session.commit()
    
    return jsonify({'result': 'ok', 'action_type': action_type}), 200

def calculate_action_type(student_number):
    action_type_counts = {'E': 0, 'I': 0, 'S': 0, 'N': 0, 'T': 0, 'F': 0, 'J': 0, 'P': 0}
    
    student_choices = StudentAnswer.query.filter_by(student_number=student_number).all()
    
    for choice in student_choices:
        statement = Statements.query.filter_by(statement_number=choice.statement_number, choice_result=choice.choice_result).first()
        if statement:
            choice_result = statement.choice_result
            if choice_result in action_type_counts:
                action_type_counts[choice_result] +=1
    
    action_type_result = ''
    action_type_result += 'E' if action_type_counts['E'] > action_type_counts['I'] else 'I'
    action_type_result += 'S' if action_type_counts['S'] > action_type_counts['N'] else 'N'
    action_type_result += 'T' if action_type_counts['T'] > action_type_counts['F'] else 'F'
    action_type_result += 'J' if action_type_counts['J'] > action_type_counts['P'] else 'P'
    
    return action_type_result

@app.route('/docent_login', methods=['POST', 'GET'])
def teacher_login():
    if request.method == 'POST':
        user_name = request.form['user_name']
        password = request.form['password']
        teacher = Teacher.query.filter_by(user_name=user_name).first()
        if teacher:
            if check_password_hash(teacher.password, password):
                flash('Je bent ingelogd', 'success')
                return redirect(url_for('student_table'))
            else:
                flash('wachtwoord is onjuist', 'error')
        else:
            flash('Deze naam ' + user_name + ' bestaat niet', 'error')
    return render_template('login_docent.html')


@app.route('/docent_logout')
def teacher_logout():
    session.clear()
    return redirect(url_for('index'))


# een route voor de docent om de tabel met de studentgegevns te bekijken
@app.route('/student_table', methods=['GET'])
def student_table():
    # een query om alle gegevens van de studenten te weergeven
    # students = Students.query.all()
    name_search = request.args.get('zoek_naam')
    if name_search:
        students = Students.query.filter(Students.student_name.contains(name_search)).all()
    else:
        students = Students.query.all()
    return render_template('student_table.html', students=students)


# een route met daarin een form om een student toe te voegen
@app.route('/add_student', methods=['POST', 'GET'])
def add_student():
    # als de aanvraag een POST is, dan worden de gegevens opgehaald
    # en worden de gegevens toegevoegd aan de database 
    if request.method == 'POST':
        student_number = request.form['student_number']
        student_name = request.form['student_name']
        student_class = request.form['student_class']
        team = request.form['team']
        action_type = request.form['action_type']
        new_student = Students(student_number=student_number, student_name=student_name,
                               student_class=student_class, team=team, action_type=action_type)
        db.session.add(new_student)
        db.session.commit()
        return redirect(url_for('student_table'))
    return render_template('add_student.html')

# een route dat de csv bestand met de studentgegevens download
@app.route('/ex_csv')
def ex_csv():
    students = Students.query.all()
    
    # een lijst met de kolommen voor het csv bestand
    data = [['Studentnummer', 'Naam', 'Klas', 'Team', 'Actiontype']]
    for student in students:
        data.append([student.student_number, student.student_name, student.student_class, 
                     student.team, student.action_type])
    
    # hier wordt de data in het bestand opgeschreven
    output = io.StringIO()
    write = csv.writer(output)
    write.writerows(data)
    
    # hier wordt de data in het bestand opgeslagen
    res = Response(
        output.getvalue(),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filname=studenten.csv'}
    )
    return res
    

@app.route('/student_update/<int:student_number>', methods=['GET','POST'])
def student_update(student_number):
    student = Students.query.get_or_404(student_number)
    if request.method == 'POST':
        student.student_name = request.form['student_name']
        student.student_class = request.form['student_class']
        student.team = request.form['team']
        student.action_type = request.form['action_type']
        db.session.commit()
        return redirect(url_for('student_table'))
    return render_template('student_update.html', student=student)


# een route om de studenten te verwijderen
@app.route('/student_delete/<int:student_number>', methods=['POST'])
def student_delete(student_number):
    # een query om de student te verwijderen door de studentmummer te selecteren
    student_for_delete = Students.query.get_or_404(student_number)
    db.session.delete(student_for_delete)
    db.session.commit()
    return redirect(url_for('student_table'))
        

# als de flask app wordt uitgevoerd, dan wordt de database gecreeerd
# en de debug mode aangezet        
if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)