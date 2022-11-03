from packages.database import CursorFromConnectionPool
from datetime import datetime
import calendar
from packages.payroll.loan.loanOop import loanpayment


class Basic:
	"""docstring for ClassName"""
	def __init__(self, get_id, percentage=None):
		self.id = get_id

	def __repr__():
		return "User Id: {}".format(self.id)

	def basic_info(self):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT basic, total_a, gross, cra, bank_name, bank_acct FROM account_info WHERE emp_id=%s", (self.id,))
			info = cursor.fetchone()
			if info is not None:
				return info
			else:
				return None

	def tax_info(self):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT total_tax FROM tax WHERE emp_id=%s", (self.id,))
			taxable = cursor.fetchone()
			if taxable is not None:
				return taxable[0]
			else:
				return None


	def pension_info(self):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT pension from account_info WHERE emp_id=%s", (self.id,))
			pension = cursor.fetchone()
			if pension is not None:
				return pension[0]

	def employer_savings(self, grosspay):
		percentage = int(10)
		savings = (percentage / 100) * grosspay
		return savings

	


	def salary_info(self, percentage=100):
		perc = percentage
		months = 12
		data = Basic(self.id).basic_info();
		tax =  Basic(self.id).tax_info();
		pension =  Basic(self.id).pension_info();
			
		basic = get_perc(amount=(data[0] / months), percent=perc)
		allowances = get_perc(amount=(data[1] / months), percent=perc)
		gross = get_perc(amount=(data[2] / months), percent=perc)
		cra = get_perc(amount=(data[3] / months), percent=perc)
		tax = get_perc(amount=(tax / months), percent=perc)
		pension = get_perc(amount=(pension / months), percent=perc)
		salary = gross - tax - pension
		employer_savings = Basic(self.id).employer_savings(grosspay=gross)
		relief = cra + pension

		baisc_details = {
			'basic': basic,
			'allowances': allowances,
			'gross': gross,
			'cra': cra,
			'tax': tax,
			'pension': pension,
			'salary': salary,
			'employer_savings': employer_savings,
			'relief': relief,
			'bankname': data[4],
			'accountnum': data[5]
		}
		
		return baisc_details

	def rate_worked_for(self, days, percentage):
		now = datetime.now()
		info = Basic(self.id).salary_info(percentage)
		calendar_days = calendar.monthrange(now.year, now.month)[1]
		
		working_days = int(days)

		salary = info['salary']
		daily_rate = salary / calendar_days
		absent = calendar_days - int(days)

		salary_worked_for = daily_rate * int(days)
		details = {
		    'days': days,
		    'workedfor': salary_worked_for,
		    'absent': absent
		}
		return details
		    


def get_perc(amount, percent):
	per = percent / 100
	value =per * float(amount)
	return value


class Loan:
	"""docstring for Loan"""
	def __init__(self, get_id):
		self.id = get_id

	def __repr__(self):
		return 'Loan user id: {}'.format(self.id)


	def loan_info(self):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM loan WHERE emp_id=%s and loan_category=%s and status=%s and outstanding != %s", 
							(self.id, 'otherloan', 1, 0))
			info = cursor.fetchall()
			if info:
				return info
			

	def updaterecord(self, loan_type, month, year, loan, repayment, outstanding, category, loan_id):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("UPDATE loan SET outstanding=%s WHERE emp_id=%s and id=%s", (outstanding, self.id, loan_id))
			# cursor.execute("INSERT INTO loanrepay(emp_id, loan_type, month, year, loan, repayment, outstanding, category, \
			# 										loan_id) \
			# 				VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)", (self.id, loan_type, month, year, loan, repayment, 
			# 															outstanding, category, loan_id))
			if cursor:
				saveloanrecord = loanpayment(self.id, loan_type, loan, repayment, outstanding, category, loan_id)
				if saveloanrecord:
					return True
				else:
					return False
			else:
				return False


	def deduct_loan(self, salary, month, year):
		loan_info = Loan(self.id).loan_info()
		
		if loan_info and len(loan_info) != 0:
			# loop tru to deduct loan
			get_salary = salary
			loanPAID = 0

			for i in loan_info:
				proc_salary = get_salary

				if i[4] is not None and i[7] is not None:
					outstanding = i[4]
					deduction_rate = i[7]
					
					# check if outstanding is lower to deduction rate
					if outstanding < deduction_rate:
						proc_salary = proc_salary - outstanding
						loan_outstanding = 0
						loan_paid = outstanding
					else:
						proc_salary = proc_salary - deduction_rate
						loan_outstanding = outstanding - deduction_rate
						loan_paid = deduction_rate

					# update loan record
					update_loan = Loan(self.id).updaterecord(loan_type=i[2], month=month, year=year, loan=i[3],
																repayment=loan_paid, outstanding=loan_outstanding,
																category=i[9], loan_id=i[0])
					if update_loan is True:
						get_salary = proc_salary
						loanPAID = loanPAID + loan_paid
					else:
						return False
				else:
				    return None	

			current_salary = get_salary

			info = {
				'salary': current_salary,
				'loan': loanPAID
			}
			return info
			
		else:
			return None	

	
	@classmethod
	def loan_revert(cls, empid, month, year):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM loanrepay WHERE emp_id=%s and month=%s and year=%s", (empid, month, year))
			res = cursor.fetchall()
			process = None
			
			if res:
				for i in range(len(res)):
					if res[i][8] == 'otherloan':
						loan_type = res[i][2]
						loan_cat = res[i][8]
						amount_paid = res[i][6]
						loan_id = res[i][9]
						
						cursor.execute("SELECT outstanding, id FROM loan WHERE emp_id=%s and year=%s and loan_type=%s",
										(empid, year, loan_type))
						result = cursor.fetchone()

						outstanding_val = result[0] + amount_paid

						cursor.execute("UPDATE loan set outstanding=%s WHERE emp_id=%s and month=%s and year=%s and loan_type=%s",
										(outstanding_val, empid, month, year, loan_type))
						cursor.execute("DELETE FROM loanrepay WHERE emp_id=%s and month=%s and year=%s and category=%s and loan_id=%s", 
										(empid, month, year, loan_cat, loan_id))

						if cursor:
							process = True
						else:
							process = False

					elif res[i][8] == 'cooperative':
						cursor.execute("SELECT * FROM loan WHERE emp_id=%s and year=%s", (empid, year))
						result = cursor.fetchall()

						if result:
							for i in range(len(result)):
								deduction_value = result[i][7]
								outstanding_value = result[i][4]
								loan_id = result[i][0]

								new_outstanding_value = outstanding_value + deduction_value

								# update loan table
								cursor.execute("UPDATE loan SET outstanding=%s WHERE emp_id=%s and id=%s",
												(new_outstanding_value, empid, loan_id))

							# revert monthly contribution
							cursor.execute("SELECT * FROM coopdetails WHERE emp_id=%s and month=%s and year=%s", 
											(empid, month, year))
							res = cursor.fetchone()
							if res:
								contrib = res[4]

								cursor.execute("SELECT * FROM cooperative WHERE emp_id=%s", (empid,))
								proc = cursor.fetchone()

								if proc:
									contrib_value = proc[2]

									revert_contrib = contrib_value - contrib

									cursor.execute("UPDATE cooperative SET contribution=%s WHERE emp_id=%s", (revert_contrib, empid))
									if cursor:
										cursor.execute("DELETE FROM coopdetails WHERE emp_id=%s and month=%s and year=%s", 
														(empid, month, year))
										if cursor:
											cursor.execute("DELETE FROM loanrepay WHERE emp_id=%s and month=%s and year=%s", 
															(empid, month, year))
											if cursor:
												return True
											else:
												# print('unabale to delete loanrepay record')
												return 100 # unabale to delete loanrepay record
										else:
											# print('unable to delete coopdetails record')
											return 101 # unable to delete coopdetails record
									else:
										# print('unable to update cooperative record')
										return 102 # unable to update cooperative record
								else:
									# print('No record found')
									pass
							else:
								# print('no coopdetails found')
								return 103 # no coopdetails found
						else:
							# print('no loan record found')
							return None # no loan record found
						

				if process == True:
					return True
			else:
				return 0 # no loan record found


	


class Coop:
	"""docstring for Loan"""
	def __init__(self, get_id):
		self.id = get_id

	def __repr__(self):
		return 'Coop user id: {}'.format(self.id)


	def loan_details(self):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM loan WHERE emp_id=%s and loan_category=%s and status=%s", 
							(self.id, 'cooperative', 1))
			loan_info = cursor.fetchall()
			if loan_info is not None:
				return loan_info
			else:
				return None

	def loanrecord(self, outstanding):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("UPDATE cooperative SET outstanding=%s WHERE emp_id=%s", (outstanding, self.id))
			if cursor:
				return True
			else: return False

	def coop_list(self):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM cooperative WHERE emp_id=%s and status=%s", (self.id, 'Active'))
			is_member = cursor.fetchone()
			if is_member is not None:
				return is_member
			else:
				return None

	def update_coop_record(self, contribution):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM cooperative WHERE emp_id=%s", (self.id,))
			coop_det = cursor.fetchone()
			if coop_det[2] is None:
				initial_contr = 0
			else:
				initial_contr = coop_det[2]

			contr = initial_contr + contribution			

			cursor.execute("UPDATE cooperative SET contribution=%s WHERE emp_id=%s", (contr, self.id))
			if cursor:
				return True
			else:
				return False



	def contribution_value(self):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT contribution FROM coop_set WHERE emp_id=%s", (self.id,))
			value = cursor.fetchone()
			if value is not None:
				return value
			else:
				return None


	@classmethod
	def save_contribution(cls, emp_id, month, year, contribute, socialwelfare, loan, outstanding, total):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("INSERT INTO coopdetails(emp_id, month, year, contribution, socialwelfare, loan, outstanding, total) VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", 
							(emp_id, month, year, contribute, socialwelfare, loan, outstanding, total))
			if cursor:
				cursor.execute("UPDATE cooperative SET contribution=%s, socialwelfare=%s WHERE emp_id=%s", (contribute, socialwelfare, emp_id))
				if cursor:
					return True
			else:
				return False


	def coop_loan_deduct(self, salary, month, year):
		loan_details = Coop(self.id).loan_details()

		if len(loan_details) != 0:
			# loop tru to deduct loan
			get_salary = salary
			loanPAID = 0

			for i in loan_details:
				proc_salary = get_salary

				if i[4] is not None and i[7] is not None:
					outstanding = i[4]
					deduction_rate = i[7]

					if outstanding < deduction_rate:
						proc_salary = proc_salary - outstanding
						loan_outstanding = 0
						loan_paid = outstanding
					else:
						proc_salary = proc_salary - deduction_rate
						loan_outstanding = outstanding - deduction_rate
						loan_paid = deduction_rate

					# save_record = Coop(self.id).loanrecord(outstanding=loan_outstanding)
					# update loan record
					save_record = Loan(self.id).updaterecord(loan_type=i[2], month=month, year=year, loan=i[3],
																repayment=loan_paid, outstanding=loan_outstanding, 
																category= i[9], loan_id=i[0])
					
					if save_record is True:
						get_salary = proc_salary
						loanPAID = loanPAID + loan_paid
					else:
						return False
				else:
					return None

			rtn_details = {
				'salary': get_salary,
				'coop_loan': loanPAID,
				'outstanding': loan_outstanding,
			}
			
			return rtn_details
		else:
			return None



	def coop_contribution(self, salary):
		is_member = Coop(self.id).coop_list()
		if is_member is not None:
			value = Coop(self.id).contribution_value()
			if value is not None:
				contribution = value[0]
				
				deduct = salary - contribution

				details = {
					'salary': deduct,
					'contribution': contribution
				}

				return details
			else:
				return None

		else:
			return None

	def revert(self):
		coop_info = Coop(self.id).coop_list()
		if coop_info:
			contribution = coop_info[2]
			value = Coop(self.id).contribution_value()

			if value:
				revert_val = contribution - value[0]

				with CursorFromConnectionPool() as cursor:
					cursor.execute("UPDATE cooperative set contribution=%s WHERE emp_id=%s", (revert_val, self.id))
					if cursor:
						return True
			
		else:
			return 0

		


class socialcontrib:
	"""docstring for socialcontrib"""
	def __init__(self, salary):
		self.salary = salary
		self.social_contrib = int(500)

	def deduct_social(self):
		cont = self.salary - self.social_contrib
		resp = {
			'contribution': self.social_contrib,
			'salary': cont
		}
		return resp
		

class Adjustment:
	"""docstring for Adjustment"""
	def __init__(self, get_id, month, year):
		self.id = get_id
		self.month = month
		self.year = year

	def get_adjustment(self):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM adjustment WHERE emp_id=%s and month=%s and year=%s", (self.id, self.month, self.year))
			is_found = cursor.fetchone()
			if is_found is not None:
				return is_found
			else:
				return None

	def make_adjustment(self, salary):
		details = Adjustment(self.id, self.month, self.year).get_adjustment()
		if details is not None:
			operation = details[5]
			amount = details[6]

			if operation == 'add':
				adj_salary = salary + amount
			elif operation == 'deduct':
				adj_salary = salary - amount

			info = {
				'operation': operation,
				'salary': adj_salary,
				'amount': amount
			}

			return info
		else:
			return None


class Salary_ops:
	"""docstring for Salary_ops"""
	def __init__(self):
		pass

	def deduct(self, column_name):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT {} FROM oops".format(column_name))
			res = cursor.fetchone()
			if res is not None:
				return res[0]
			elif res is None:
				return 0
			else:
				return 0


class Save_salary:
	"""docstring for Save_salary"""
	def __init__(self, emp_id, month, year, percentage, basic, allowances, gross, pension, employer_savings, relief, tax, workedfor, 
				    loan_deduction, coop_loan_deduction, coop_savings, coop_total_deduction, total_deduction, adjustment, present, absent, 
				    netpay, date_process, monthly_social, bankname, accountnum):
		self.id = emp_id
		self.month = month
		self.year = year
		self.percentage = percentage
		self.basic = basic
		self.allowances = allowances
		self.gross = gross
		self.pension = pension
		self.employer = employer_savings
		self.relief = relief
		self.tax = tax
		self.workedfor = workedfor
		self.loan = loan_deduction
		self.coop_loan = coop_loan_deduction
		self.coop_savings = coop_savings
		self.coop_deduction = coop_total_deduction
		self.adjustment = adjustment
		self.deductions = total_deduction
		self.present = present
		self.absent = absent
		self.netpay = netpay
		self.date = date_process
		self.monthly_social = monthly_social
		self.bankname = bankname
		self.accountnum = accountnum


	def __repr__(self):
		pass


	def save_record(self):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("INSERT INTO salary(emp_id, month, year, perc, basic, allowance, gross, pension, employer_savings, relief, tax, \
				                                workedfor, loan, coop_loan, coop_savings, coop_deduction, adjustment, deductions, present, \
				                                absent, netpay, finalized, date_process, socialcontrib, bankname, bankacct) \
				                                VALUES(%s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, \
														%s, %s, %s,%s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s)", 
														(self.id, self.month, self.year, self.percentage, self.basic, 
															self.allowances, self.gross, self.pension, self.employer, 
															self.relief, self.tax, self.workedfor,	self.loan, self.coop_loan, 
															self.coop_savings, self.coop_deduction, self.adjustment, 
															self.deductions, self.present, self.absent, self.netpay, 'No', 
															self.date, self.monthly_social, self.bankname, self.accountnum))
			if cursor:
				cursor.execute("INSERT INTO attendance(emp_id, month, present, absent, year) VALUES(%s, %s, %s, %s, %s)", 
								(self.id, self.month, self.present, self.absent, self.year))
				if cursor:
				    return True
				else:
					return False
			else:
				return False


	@classmethod
	def save_coop_record(cls, emp_id, month, year, contribution, loan, total):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("INSERT INTO coopdetails(emp_id, month, year, contribution, loan, total) \
							VALUES(%s, %s, %s, %s, %s, %s)", (emp_id, month, year, contribution, loan, total))
			if cursor:
				save_coop_det = Coop(get_id=emp_id).update_coop_record(contribution=contribution)
				if save_coop_det is True:
					return True
				else:
					return False
			else:
				return False


	