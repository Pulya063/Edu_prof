from flask_sqlalchemy import SQLAlchemy

# db не прив'язаний до конкретного Flask-застосунку тут.
# Ініціалізація відбувається через db.init_app(flask_app) у create_app() в main.py
db = SQLAlchemy()
