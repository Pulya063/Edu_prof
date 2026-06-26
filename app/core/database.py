import os
from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Створюємо глобальний об'єкт бази даних
db = SQLAlchemy(app)


@app.route('/status')
def check_status():
    # db.session — це готова синхронна сесія.
    # Вона доступна у будь-якому маршруті автоматично.
    result = db.session.execute(text("SELECT 1")).scalar()

    return jsonify({
        "status": "healthy",
        "db_response": result
    })


if __name__ == '__main__':
    app.run(debug=True)
