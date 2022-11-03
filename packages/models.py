from flask import session, current_app
from packages import db, login_manager
from flask_login import UserMixin

	

@login_manager.user_loader
def load_user(user_id):
    user = Employees.query.get(int(user_id))
    if user == None:
        user = Admin.query.get(int(user_id))
    return user


class Superadmin(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.Text)
	email = db.Column(db.String(255))
	password = db.Column(db.Text)
	status = db.Column(db.Integer)


	def __repr__(self):
		return f"Super_Admin('{self.name}', '{self.email}', '{self.password}, '{self.status})"
		
    





class Employees(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255))
	address = db.Column(db.String(255))
	city = db.Column(db.String(100))
	mobile = db.Column(db.String(200))
	department = db.Column(db.String(200))
	post = db.Column(db.String(200))
	email = db.Column(db.String(100))
	branch = db.Column(db.String(100))
	active_date = db.Column(db.String(50))
	emp_class = db.Column(db.String(100))
	coop = db.Column(db.String(100))
	active = db.Column(db.Integer, default=1)
	state = db.Column(db.String(100))
	password = db.Column(db.String(100))
	dob = db.Column(db.String(100))
	staff_id = db.Column(db.String(100))
	role = db.Column(db.String(100))
	jobtitle = db.Column(db.String(200))
	aboutme = db.Column(db.Text)
	image = db.Column(db.Text)
	color = db.Column(db.Text)
	title = db.Column(db.Text)
	gender = db.Column(db.Text)

	# Relationship
	account_info = db.relationship('Account_info', backref='user', lazy=True)
	adjustment = db.relationship('Adjustment', backref='user', lazy=True)
	attendance = db.relationship('Attendance', backref='user', lazy=True)
	coopdetails = db.relationship('Coopdetails', backref='user', lazy=True)
	cooperative = db.relationship('Cooperative', backref='user', lazy=True)
	emppension = db.relationship('Emppension', backref='user', lazy=True)
	leaveaction = db.relationship('Leave_action', backref='user', lazy=True)
	leavemessage = db.relationship('Leave_message', backref='user', lazy=True)
	leavedays = db.relationship('Leavedays', backref='user', lazy=True)
	# leavenotify = db.relationship('Leavenotify', backref='user', lazy=True)
	leaverequest = db.relationship('Leaverequest', backref='user', lazy=True)
	loan = db.relationship('Loan', backref='user', lazy=True)
	loanrepay = db.relationship('Loanrepay', backref='user', lazy=True)
	salary = db.relationship('Salary', backref='user', lazy=True)
	tax = db.relationship('Tax', backref='user', lazy=True)


	def __repr__(self):
		return f"Employees('{self.id}', '{self.name}', '{self.department}', '{self.post}', '{self.email}', '{self.role}', \
							'{self.color}', '{self.image}', '{self.jobtitle}')"

# nullable=False

####################################################################
class Account_info(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
	basic = db.Column(db.Float)
	house_a = db.Column(db.Float)
	transport_a = db.Column(db.Float)
	other_a = db.Column(db.Float)
	total_a = db.Column(db.Float)
	salary = db.Column(db.Float)
	gross = db.Column(db.Float)
	cra = db.Column(db.Float)
	pension = db.Column(db.Float)
	total_relief = db.Column(db.Float)
	bank_name = db.Column(db.String(100))
	bank_acct = db.Column(db.String(100))
	acct_name = db.Column(db.String(100))
	bank_branch = db.Column(db.String(100))
	tax_number = db.Column(db.String(100))
	daily_rate = db.Column(db.Float)
	weekly_rate = db.Column(db.Float)
	percentage = db.Column(db.Float)


	def __repr__(self):
		return f"Account_info('{self.emp_id}', '{self.gross}', '{self.pension}', '{self.bank_name}')"



class Adjustment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer, db.ForeignKey('employees.id'), nullable=False)
	month = db.Column(db.String(100), nullable=False)
	year = db.Column(db.String(100), nullable=False)
	reason = db.Column(db.String(255), nullable=False)
	adj_type = db.Column(db.String(100), nullable=False)
	amount = db.Column(db.Float, nullable=False)
	date = db.Column(db.String(100), nullable=False)


	def __repr__(self):
		return f"Adjustment('{self.emp_id}', '{self.month}', '{self.year}', '{self.amount}')"



class Admin(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	email = db.Column(db.String(100))
	password = db.Column(db.String(255))
	firstname = db.Column(db.String(255))
	lastname = db.Column(db.String(255))
	created = db.Column(db.String(100))
	role = db.Column(db.String(100))
	status = db.Column(db.Integer)


	def __repr__(self):
		return f"Admin('{self.id}', '{self.email}', '{self.firstname}', '{self.lastname}', '{self.status}')"


class Appraisal_pmt(db.Model, UserMixin):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.Text)
	score = db.Column(db.Float)
	year = db.Column(db.String(255))
	phase = db.Column(db.Text)	


class Attendance(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
	month = db.Column(db.String(100), nullable=False)
	present = db.Column(db.Integer, nullable=False)
	absent = db.Column(db.Integer, nullable=False)
	year = db.Column(db.Integer, nullable=False)
	

class Bank_name(db.Model):
	name = db.Column(db.String(150),  nullable=False)
	id = db.Column(db.Integer, primary_key=True)


class Branch(db.Model):
	name = db.Column(db.String(150),  nullable=False)
	id = db.Column(db.Integer, primary_key=True)


class Department(db.Model):
	name = db.Column(db.String(150),  nullable=False)
	id = db.Column(db.Integer, primary_key=True)
	supervisor = db.Column(db.String(255))
	sop = db.Column(db.Text)


class Post(db.Model):
	name = db.Column(db.String(150),  nullable=False)
	id = db.Column(db.Integer, primary_key=True)
	jd = db.Column(db.String(255))
	department = db.Column(db.String(255))



class Pensioncomp(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(150),  nullable=False)



class Coopdetails(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
	month = db.Column(db.String(100))
	year = db.Column(db.String(100))
	contribution = db.Column(db.Float)
	socialwelfare = db.Column(db.Float)
	loan = db.Column(db.Float)
	total = db.Column(db.Float)


class Cooperative(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
	contribution = db.Column(db.Float)
	socialwelfare = db.Column(db.Float)
	loan = db.Column(db.Float)
	outstanding = db.Column(db.Float)
	loan_percent = db.Column(db.Integer)
	status = db.Column(db.String(100))
	total = db.Column(db.Float)
	installment = db.Column(db.Integer)
	deduction_rate = db.Column(db.Float)


class Coop_set(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer)
	contribution = db.Column(db.Integer)


class Emp_class(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100))
	basic = db.Column(db.Float)
	house_a = db.Column(db.Float)
	transport_a = db.Column(db.Float)
	other_a = db.Column(db.Float)
	total_a = db.Column(db.Float)
	lasg_lunch_allowance = db.Column(db.Float)
	twofourhrs_allowance = db.Column(db.Float)
	health_allowance = db.Column(db.Float)



class Emppension(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
	pen_name = db.Column(db.String(150))
	pen_num = db.Column(db.String(150))


class Leave_action(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	leave_request = db.Column(db.Integer, db.ForeignKey('employees.id'))
	hr_user = db.Column(db.String(150))
	email = db.Column(db.String(150))


class Leave_message(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	leave_id = db.Column(db.Integer, db.ForeignKey('leaverequest.id'))
	emp_leave_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
	receiving_emp_id = db.Column(db.Integer)
	leave_mode = db.Column(db.String(150))
	msg_date = db.Column(db.String(255))
	status = db.Column(db.Integer)


class Leavecomment(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	leaveid = db.Column(db.Integer, nullable=False)
	relief1 = db.Column(db.String(200))
	relief2 = db.Column(db.String(200))
	relief3 = db.Column(db.String(200))
	supervisor = db.Column(db.String(200))
	hr_action = db.Column(db.String(200))
	final = db.Column(db.String(200))


class Leavedays(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
	total_days = db.Column(db.Integer)
	used_days = db.Column(db.Integer)
	remain_days = db.Column(db.Integer)
	status = db.Column(db.Integer)


class Leavenotify(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	leave_id = db.Column(db.Integer, db.ForeignKey('leaverequest.id'))
	email = db.Column(db.String(200))
	relief1_id = db.Column(db.Integer)
	relief1_name = db.Column(db.String(200))
	relief1_email = db.Column(db.String(200))
	relief2_id = db.Column(db.Integer)
	relief2_name = db.Column(db.String(200))
	relief2_email = db.Column(db.String(200))
	relief3_id = db.Column(db.Integer)
	relief3_name = db.Column(db.String(200))
	relief3_email = db.Column(db.String(200))
	super_id = db.Column(db.Integer)
	super_name = db.Column(db.String(200))
	super_email = db.Column(db.String(200))
	hr_email = db.Column(db.String(200))
	approve_email = db.Column(db.String(200))
	relief1_action = db.Column(db.String(200))
	relief2_action = db.Column(db.String(200))
	relief3_action = db.Column(db.String(200))
	super_action = db.Column(db.String(200))
	hr_action = db.Column(db.String(200))
	final_action = db.Column(db.String(200))
	status = db.Column(db.String(60))
	auth = db.Column(db.String(255))



class Leaverequest(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
	leavetype = db.Column(db.String(150))
	startdate = db.Column(db.String(150))
	enddate = db.Column(db.String(150))
	duration = db.Column(db.Integer)
	resumeday = db.Column(db.String(50))
	address = db.Column(db.String(200))
	contact = db.Column(db.String(50))
	department = db.Column(db.String(50))
	handover = db.Column(db.String(100))
	requestdate = db.Column(db.String(50))
	status = db.Column(db.String(50))
	year = db.Column(db.String(100))
	allowance = db.Column(db.String(100))
	allowancereceive = db.Column(db.String(50), default='pending')

	

class Leavetype(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(100))
	description = db.Column(db.String(255))
	duration = db.Column(db.Integer)



class Otherleave(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer)
	leave_name = db.Column(db.String(100))
	total_days = db.Column(db.Integer)
	used_days = db.Column(db.Integer)
	remain_days = db.Column(db.Integer)


class leavededuction(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer)
	leavetype = db.Column(db.String(100))
	days = db.Column(db.Integer)
	reason = db.Column(db.Text)
	sdate = db.Column(db.String(100))
	year = db.Column(db.String(100))



class Loan(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
	loan_type = db.Column(db.String(200))
	amount = db.Column(db.Float)
	outstanding = db.Column(db.Float)
	percent = db.Column(db.Float)
	installment = db.Column(db.Integer)
	deduction_rate = db.Column(db.Float)
	status = db.Column(db.Integer)
	loan_category = db.Column(db.String(200))
	month = db.Column(db.String(100))
	year = db.Column(db.String(100))
	loanid = db.Column(db.String(100))
	loanrequestid = db.Column(db.Integer)



class Loanrepay(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
	loan_type = db.Column(db.String(200))
	month = db.Column(db.String(100))
	year = db.Column(db.String(100))
	loan = db.Column(db.Float)
	repayment = db.Column(db.Float, nullable=True)
	outstanding = db.Column(db.Float, nullable=True)
	category = db.Column(db.String(100))
	loan_id = db.Column(db.Integer)
	status = db.Column(db.String(100))


class Loanrequest(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer)
	loantype = db.Column(db.String(255))
	amount = db.Column(db.Float)
	installment = db.Column(db.Integer)
	requesting_date = db.Column(db.String(100))
	process_date = db.Column(db.String(100))
	status = db.Column(db.String(100))
	emi = db.Column(db.Float)
	rate = db.Column(db.Integer)
	repayment = db.Column(db.Float)
	note = db.Column(db.String(100))
	loandate = db.Column(db.String(100))
	year = db.Column(db.Text)



class Loantype(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	loan_name = db.Column(db.String(100))
	loan_description = db.Column(db.String(255))
	

class Oops(db.Model):
	salary_perc = db.Column(db.Integer, nullable=True)
	payroll_report = db.Column(db.Integer, nullable=True)
	monthly_deduction = db.Column(db.Integer, nullable=True)
	loan_deduction = db.Column(db.Integer, nullable=True)
	coop_loan_deduction = db.Column(db.Integer, nullable=True)
	coop_contribution = db.Column(db.Integer, nullable=True)
	loan_request = db.Column(db.Integer, nullable=True)
	leave_request = db.Column(db.Integer, nullable=True)
	leave_hr_email = db.Column(db.String(200), nullable=True)
	leave_final_email = db.Column(db.String(200), nullable=True)
	id = db.Column(db.Integer, primary_key=True)
	leave_year = db.Column(db.String(100), nullable=True)

	# start update
class Offboarding(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer)
	department = db.Column(db.String(100))
	startdate = db.Column(db.String(100))
	enddate = db.Column(db.String(100))
	reason = db.Column(db.String(255))
	status = db.Column(db.String(100))
	actions = db.Column(db.String(100)) # update
	onboard_date = db.Column(db.String(150))
	# end-update

class Permission(db.Model):
	emp_id = db.Column(db.Integer)
	ghi_cms = db.Column(db.Integer)
	m_report = db.Column(db.Integer)
	loan = db.Column(db.Integer)
	active = db.Column(db.Integer)
	leave = db.Column(db.Integer)
	id = db.Column(db.Integer, primary_key=True)
	


class Salary(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
	month = db.Column(db.String(50), nullable=True)
	year = db.Column(db.String(100), nullable=True)
	perc = db.Column(db.Float)
	basic = db.Column(db.Float)
	allowance = db.Column(db.Float)
	gross = db.Column(db.Float)
	pension = db.Column(db.Float)
	employer_savings = db.Column(db.Float)
	relief = db.Column(db.Float)
	tax = db.Column(db.Float)
	workedfor = db.Column(db.Float)
	loan = db.Column(db.Float)
	coop_loan = db.Column(db.Float)
	coop_savings = db.Column(db.Float)
	coop_deduction = db.Column(db.Float)
	adjustment = db.Column(db.Float)
	deductions = db.Column(db.Float)
	present = db.Column(db.Integer)
	absent = db.Column(db.Integer)
	netpay = db.Column(db.Float)
	finalized = db.Column(db.String(50))
	date_process = db.Column(db.String(100))
	socialcontrib = db.Column(db.Float)
	bankname = db.Column(db.String(200))
	bankacct = db.Column(db.String(100))


class Tax(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
	taxable = db.Column(db.Float)
	mintax = db.Column(db.Float)
	highertax = db.Column(db.Float)
	effective_tax = db.Column(db.Float, nullable=True)
	band1 = db.Column(db.Float, nullable=True)
	band2 = db.Column(db.Float, nullable=True)
	band3 = db.Column(db.Float, nullable=True)
	band4 = db.Column(db.Float, nullable=True)
	band5 = db.Column(db.Float, nullable=True)
	band6 = db.Column(db.Float, nullable=True)
	total_tax = db.Column(db.Float, nullable=True)


class Pre_reg(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255))
	state = db.Column(db.String(255))
	address = db.Column(db.String(255))
	city = db.Column(db.String(255))
	mobile = db.Column(db.String(60))
	bankname = db.Column(db.String(255))
	account = db.Column(db.Integer)
	taxnumber = db.Column(db.String(100))
	pensioncomp = db.Column(db.String(100))
	pensionnum = db.Column(db.String(100))


class Work_tools(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer)
	services = db.Column(db.Text)
	device = db.Column(db.Text)
	department = db.Column(db.String(100))
	email = db.Column(db.String(100))


class Review_compute(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	category = db.Column(db.String(255))
	score = db.Column(db.Integer)
	note = db.Column(db.String(255))
	tag = db.Column(db.Integer)


class Review_docx(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	targetid = db.Column(db.String(100))
	emp_id = db.Column(db.Integer)
	department = db.Column(db.String(100))
	tag = db.Column(db.String(100))
	report = db.Column(db.Text)


class Review_response(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	uniquecode = db.Column(db.String(100))
	emp_id = db.Column(db.Integer)
	rule_id = db.Column(db.Integer)
	rule_score = db.Column(db.Float)
	rule_feedback = db.Column(db.String(255))
	rule_type = db.Column(db.String(100))
	status = db.Column(db.String(100))
	res_emp_id = db.Column(db.Integer)
	department = db.Column(db.String(100))


class Rules(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	text = db.Column(db.Text)
	score = db.Column(db.Float)
	percentage = db.Column(db.Float)
	targetid = db.Column(db.String(100))


class Target(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(200))
	start_date = db.Column(db.String(200))
	end_date = db.Column(db.String(200))
	num_emp = db.Column(db.Integer)
	department = db.Column(db.String(100))
	target_uid = db.Column(db.String(100))
	num_rules = db.Column(db.Integer)
	total_perc = db.Column(db.Float)
	out_perc = db.Column(db.Float)
	status = db.Column(db.String(100))
	setby = db.Column(db.String(100))
	setbyid = db.Column(db.Integer)
	year = db.Column(db.Text)


class Target_score(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	uniquecode = db.Column(db.String(100))
	emp_id = db.Column(db.Integer)
	reviewer_id = db.Column(db.Integer)
	total = db.Column(db.Float)
	average = db.Column(db.Float)


class Targetemp(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	unique_code = db.Column(db.String(100))
	emp_id = db.Column(db.Integer)
	status = db.Column(db.String(100))
	targetuid = db.Column(db.Integer)
	super_action = db.Column(db.String(100))
	department = db.Column(db.String(100))
	emp_signed = db.Column(db.String(100))
	complete_review = db.Column(db.String(100))
	active = db.Column(db.String(100))
	process = db.Column(db.String(100))
	accept = db.Column(db.Integer)
	reason = db.Column(db.Text)


class Qcreport(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer)
	mode = db.Column(db.String(200))
	date_received = db.Column(db.String(100))
	date_saved = db.Column(db.String(100))
	subject = db.Column(db.Text)
	summary = db.Column(db.Text)
	attachment = db.Column(db.Text)
	submitby = db.Column(db.String(255))
	editby = db.Column(db.String(255))
	department = db.Column(db.String(255))


class Notification(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer)
	label = db.Column(db.Text)
	link = db.Column(db.Text)
	dateposted = db.Column(db.String(100))
	status = db.Column(db.String(100))
	target = db.Column(db.String(100))


class Ccreport(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255))
	email = db.Column(db.String(255))
	postdate = db.Column(db.String(255))
	shift = db.Column(db.String(255))
	category = db.Column(db.String(255))
	cust_name = db.Column(db.Text)
	cust_num = db.Column(db.Text)
	cust_reachable = db.Column(db.Text)
	cust_feedback = db.Column(db.Text)

class Empdocument(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
	docx_name = db.Column(db.Text)
	document = db.Column(db.Text)
	uploadby = db.Column(db.Integer)
	month = db.Column(db.String(200))
	year = db.Column(db.String(200))
	uploadtime = db.Column(db.Text)
	category = db.Column(db.String(125))
	docdate = db.Column(db.Text)


class Feedbackform(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer)
	setbyid = db.Column(db.Integer)
	submitdate = db.Column(db.Text)
	department = db.Column(db.Text)
	questions = db.Column(db.Text)
	answers = db.Column(db.Text)
	ulink = db.Column(db.Text)


class Nextofkin(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer)
	nokname = db.Column(db.Text)
	noknumber = db.Column(db.Text)
	nokemail = db.Column(db.Text)
	nokrel = db.Column(db.Text)


class Qareport(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(200))
	email = db.Column(db.String(200))
	postdate = db.Column(db.String(200))
	shift = db.Column(db.String(100))
	resumetime = db.Column(db.String(100))
	category = db.Column(db.String(100))
	details = db.Column(db.Text)
	rsc_tab = db.Column(db.Text)
	status = db.Column(db.Text)


class Register(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer)
	date = db.Column(db.Text)
	login_time = db.Column(db.Text)
	logout_time = db.Column(db.Text)
	ip_address = db.Column(db.Text)
	hostname = db.Column(db.Text)
	month = db.Column(db.String(150))
	year = db.Column(db.String(100))
	shift = db.Column(db.Text)
	status = db.Column(db.String(255))
	shiftid = db.Column(db.Integer)
	ulocation = db.Column(db.Text)
	accessfrom = db.Column(db.Text)


class Register_time(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.Text)
	resume = db.Column(db.Text)
	close = db.Column(db.Text)
	shift = db.Column(db.Text)


class Report(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	name = db.Column(db.String(255))
	email = db.Column(db.String(255))
	postdate = db.Column(db.String(255))
	shift = db.Column(db.String(255))
	category = db.Column(db.String(255))
	pnr = db.Column(db.Text)
	details = db.Column(db.Text)
	ticket = db.Column(db.Text)
	clientname = db.Column(db.Text)
	future_date = db.Column(db.Text)
	status = db.Column(db.Text)


class Targetreport(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	targetcode = db.Column(db.Text)
	emp_id = db.Column(db.Integer)
	startdate = db.Column(db.Text)
	enddate = db.Column(db.Text)
	year = db.Column(db.Text)


class Targetrule(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	targetcode = db.Column(db.Integer)
	pmr = db.Column(db.String(255))
	title = db.Column(db.Text)
	description = db.Column(db.Text)
	score = db.Column(db.Text)
	phase = db.Column(db.Text)
	year = db.Column(db.Text)


class Trainingfeedback(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	setby_id = db.Column(db.Integer)
	title = db.Column(db.Text)
	datepost = db.Column(db.Text)
	checklist = db.Column(db.Text)
	ulink = db.Column(db.Text)
	department = db.Column(db.Text)
	description = db.Column(db.Text)
	time = db.Column(db.Text)
	year = db.Column(db.Text)
	venue = db.Column(db.Text)


class Usertarget(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	targetcode = db.Column(db.Text)
	name = db.Column(db.Text)
	startdate = db.Column(db.Text)
	enddate = db.Column(db.Text)
	year = db.Column(db.Text)
	num_emp = db.Column(db.Integer)
	department = db.Column(db.String(100))
	status = db.Column(db.Text)
	setby = db.Column(db.String(255))
	setbyid = db.Column(db.Integer)
	phase = db.Column(db.Text)


class Usertargetemp(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	targetid = db.Column(db.Text)
	targetcode = db.Column(db.Text)
	emp_id = db.Column(db.Integer)
	status = db.Column(db.Text)
	department = db.Column(db.Text)
	review_status = db.Column(db.Text)
	year = db.Column(db.Text)
	overallscore = db.Column(db.Float)
	sup_remark = db.Column(db.Text)
	sup_score = db.Column(db.Float)
	mng_remark = db.Column(db.Text)
	mng_score = db.Column(db.Float)
	hr_remark = db.Column(db.Text)


class Weeklyreport(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	emp_id = db.Column(db.Integer)
	task = db.Column(db.Text)
	startdate = db.Column(db.String(100))
	enddate = db.Column(db.String(100))
	status = db.Column(db.String(100))
	days = db.Column(db.Text)
	taskstatus = db.Column(db.Text)
	files = db.Column(db.Text)

	
# set employees active default value to 1
# set account_info percentage default to 100
# set permission active default to 1