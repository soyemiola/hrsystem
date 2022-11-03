import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from datetime import datetime
from packages.config import Config
from packages.database import Database



db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.blueprint_login_views = {'admin': '/admin/login'}
login_manager.login_message_category = 'warning'



def create_app(config_class=Config):
	app = Flask(__name__)
	app.config.from_object(Config)

	db.init_app(app)
	bcrypt.init_app(app)
	login_manager.init_app(app)
	

	Database.initialise(host='localhost', database=app.config['DB_NAME'], 
						user=app.config['DB_USER'], password=app.config['DB_PASS'])

	from packages.run_admin import admin
	from packages.employees.coop.run_coop import cms_coop
	from packages.employees.department.run_dept import dept
	from packages.employees.run_employee import users
	from packages.employees.userOop import Employee
	from packages.leave.run_leave import leaves
	from packages.payroll.empcategory.run_class import empclass
	from packages.payroll.loan.run_loan import loans
	from packages.payroll.process_payroll.run_processpayroll import payroll
	from packages.payroll.process_payroll.salary import Salary
	from packages.payroll.reports.report import report
	from packages.settings.run_settings import settings
	from packages.performance.run_performance import performance
	from packages.performance.run_qc import qc
	from packages.attendance.run_attendance import register
	


	from packages.hrAPI.run_api import hrapi

	# Blueprint Registration
	app.register_blueprint(admin, url_prefix='/')
	app.register_blueprint(cms_coop, url_prefix='/')
	app.register_blueprint(dept, url_prefix='/')
	app.register_blueprint(users, url_prefix='/')
	app.register_blueprint(leaves, url_prefix='/')
	app.register_blueprint(empclass, url_prefix='/')
	app.register_blueprint(loans, url_prefix='/')
	app.register_blueprint(payroll, url_prefix='/')
	app.register_blueprint(report, url_prefix='/')
	app.register_blueprint(settings, url_prefix='/')
	app.register_blueprint(performance, url_prefix='/')
	app.register_blueprint(qc, url_prefix='/')
	app.register_blueprint(register, url_prefix='/')


	app.register_blueprint(hrapi, url_prefix='/')

	return app

