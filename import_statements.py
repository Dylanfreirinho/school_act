import json
from app import app
from app import db
from app import Statements

 
def import_statements():
    with open('actiontype_statements.json', 'r') as file:
        statements_data = json.load(file)
        
    with app.app_context():
        for statement_data in statements_data:
            statement_number = statement_data['statement_number']
            statement_choices = statement_data['statement_choices']
            
            for choice_data in statement_choices:
                choice_number = choice_data['choice_number']
                choice_text = choice_data['choice_text']
                choice_result = choice_data['choice_result']
                
                statement = Statements(
                    statement_number=statement_number,
                    choice_number=choice_number,
                    choice_text=choice_text,
                    choice_result=choice_result
                )
                db.session.add(statement)
        db.session.commit()

if __name__ == '__main__':
    import_statements()