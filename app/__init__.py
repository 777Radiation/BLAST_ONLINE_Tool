from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config  # 引入配置

app = Flask(__name__)
app.config.from_object(Config)  # 使用配置
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

from app import routes, models  # 导入路由和模型