import os


class Config:
	SECRET_KEY = os.environ.get('SECRET_KEY')
	SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
	SECURITY_PASSWORD_SALT = os.environ.get('SECURITY_PASSWORD_SALT')
	LEAVE_URL_LINK = os.environ.get('LEAVE_URL_LINK')
	EMAIL_ADDRESS = os.environ.get('EMAIL_USER') #'btmhris@yahoo.com'
	SEND_MAIL_PASSWORD = os.environ.get('EMAIL_PASS') #'yhsxefbqrjlipvqj'
	SEND_MAIL_SERVER = os.environ.get('SEND_MAIL_SERVER')
	MAIL_PORT = os.environ.get('MAIL_PORT')
	START_YEAR = os.environ.get('START_YEAR')
	UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__)+'\\static\\admin\\handover\\')
	SOP_FOLDER = os.path.join(os.path.dirname(__file__)+'\\static\\admin\\SOPs\\')
	JD_FOLDER = os.path.join(os.path.dirname(__file__)+'\\static\\admin\\JD\\')
	WEEKLY_FOLDER = os.path.join(os.path.dirname(__file__)+'\\static\\admin\\weekly\\')
	LOGIN_LOG = os.path.join(os.path.dirname(__file__)+'\\static\\admin\\login_log\\')
	DOC_FOLDER = os.path.join(os.path.dirname(__file__)+'\\static\\admin\\documents\\')
	QC_FOLDER = os.path.join(os.path.dirname(__file__)+'\\static\\admin\\QC\\')
	DB_USER = 'postgres'
	DB_NAME = 'BTM_DB'
	DB_PASS = '1234'


