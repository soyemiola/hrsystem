from packages.database import CursorFromConnectionPool
from packages import bcrypt
import datetime
from datetime import timedelta
import socket


class attendance():
	"""docstring for attendance"""
	def __init__(self, empid):
		self.id = empid


	def __repr__(self):
		pass


	@classmethod
	def get_active_time(cls, shiftid):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM register_time WHERE id = %s LIMIT 1", (shiftid,))
			res = cursor.fetchone()
			if res:
				return res


	@classmethod
	def register_time(cls, name, resume, close, shift):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("INSERT INTO register_time(name, resume, close, shift ) \
							VALUES(%s, %s, %s, %s)",(name, resume, close, shift))
			if cursor:
				return True


	@classmethod
	def update_register_time(cls, name, resume, close, shift, updateid):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("UPDATE register_time SET name=%s, resume=%s, close=%s, shift=%s WHERE id=%s", 
							(name, resume, close, shift, updateid))
			if cursor:
				return True

	@classmethod
	def is_register_time_created(cls):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM register_time ")
			result = cursor.fetchall()
			return result


	@classmethod
	def schedules(cls, record=None):
		with CursorFromConnectionPool() as cursor:
			if record:
				cursor.execute("SELECT * FROM register_time WHERE id=%s", (record,))
				res = cursor.fetchone()
			else:
				cursor.execute("SELECT * FROM register_time ORDER BY id DESC")
				res = cursor.fetchall()

			if res:
				return res

	@classmethod
	def active_time(cls, statusId):
		with CursorFromConnectionPool() as cursor:
			reset = None
			cursor.execute("UPDATE register_time SET status=%s", (reset,))
			cursor.execute("UPDATE register_time SET status=%s WHERE id=%s", ('active',statusId))
			if cursor:
				return True

	@classmethod
	def remove_time(cls, statusId):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("DELETE FROM register_time WHERE id=%s", (statusId,))
			if cursor:
				return True


	@classmethod
	def active_employee(cls):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM employees WHERE active=%s ORDER BY name ASC", (1, ))
			emp = cursor.fetchall()
			if emp:
				return emp

	def attendance_info(self, date):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM register WHERE emp_id=%s AND date=%s LIMIT 1", (self.id, date))
			status = cursor.fetchone()
			if status:
				return status
				
	def validatepass(self, password):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT password FROM employees WHERE id=%s LIMIT 1", (self.id,))
			saved_password = cursor.fetchone()
			if bcrypt.check_password_hash(saved_password[0], password):
				return True
			else:
				return False


	def get_att_Details(self, date):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM register WHERE date=%s and emp_id=%s LIMIT 1", (date, self.id))
			getinfo = cursor.fetchone()
			if getinfo:
				return getinfo


	def register_user(self, date, login_time, ip_address, hostname, shift, shiftid, ulocation, access):
		month = datetime.datetime.today().strftime('%B')
		year = datetime.datetime.today().strftime('%Y')

		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM register WHERE emp_id=%s and date=%s LIMIT 1", (self.id, date))
			exist = cursor.fetchone()
			if exist:
				return False
			else:
				cursor.execute("INSERT INTO register(emp_id, date, login_time, ip_address, hostname, month, year, shift, shiftid, ulocation, accessfrom)\
								VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (self.id, date, login_time, ip_address, hostname, 
																					month, year, shift, shiftid, ulocation, access))

				if cursor:
					return True


	def signout_user(self, date, logout_time):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM register WHERE emp_id=%s and date=%s LIMIT 1", (self.id, date))
			check = cursor.fetchone()
			check_login_time = check[3]
			check_logout_time = check[4]
			check_login_ip = check[5]

			if check_logout_time is None:
				cursor.execute("UPDATE register SET logout_time=%s WHERE emp_id=%s and date=%s", (logout_time, self.id, date))
				if cursor:
					return True
			else:
				return False


	def login_status(self, date):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("UPDATE register SET status=%s WHERE emp_id=%s and date=%s", ('Log In', self.id, date))
			if cursor:
				return True


	@classmethod
	def att_status_chk(cls, empid, get_ip, user_login_time, user_logout_time, date, shiftid):
		status = attendance(empid).attendance_status(get_ip, user_login_time, user_logout_time, date, shiftid)

	
	
	def attendance_status(self, get_ip, user_login_time, user_logout_time, date, shiftid):
		getTime = attendance.get_active_time(shiftid)

		resume_time = datetime.datetime.today().strptime(getTime[2], '%H:%M').strftime('%H:%M')
		close_time = datetime.datetime.today().strptime(getTime[3], '%H:%M').strftime('%H:%M')

		
		login_status = attendance.__check_attendance_time(resume_time, user_login_time, 'login')
		logout_status = attendance.__check_attendance_time(close_time, user_logout_time, 'logout')

		if login_status == 1 and logout_status == 1:
			status = 'Attendance is Accurate'
		elif login_status == 1 and logout_status == 0:
			status = 'Left before closing hour'
		elif login_status == 0 and logout_status == 1:
			status = 'Resume late'
		elif login_status == 0 and logout_status == 0:
			status = 'Resume late and left before close hour'
		else:
			status = 'No Action taken'	


		self.__setTimeStatus(status=status, date=date)
		


	@classmethod
	def __check_attendance_time(cls, setTime, time, mode):
		
		user_time = datetime.datetime.today().strptime(time, '%H:%M').strftime('%H:%M')

		if mode == 'login':		
			if setTime >= user_time:
				login_time_status = 1
			else:
				login_time_status = 0

			return login_time_status

		elif mode == 'logout':
			if setTime <= user_time:
				login_time_status = 1
			else:
				login_time_status = 0

			return login_time_status



	def __setTimeStatus(self, status, date):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("UPDATE register SET status=%s WHERE emp_id=%s and date=%s", (status, self.id, date))
			if cursor:
				return True



	@classmethod
	def current_month(cls, month=None, year=None):
		if month == None and year == None:
			month = datetime.datetime.today().strftime('%B')
			year = datetime.datetime.today().strftime('%Y')

		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT emp_id, month, year FROM register where month=%s and year=%s \
							GROUP BY emp_id, month, year ", (month, year))
			att_list = cursor.fetchall()
			if att_list:
				return att_list


	@classmethod
	def reg_name(cls, emp_id):
		with CursorFromConnectionPool() as cursor:
			cursor.execute('SELECT * from employees WHERE id=%s LIMIT 1', (emp_id, ))
			name = cursor.fetchone()
			return name
				

	@classmethod
	def get_login_details(cls, emp_id, month, year):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM register WHERE emp_id=%s and month=%s and year=%s ORDER BY id DESC", (emp_id, month, year))
			res = cursor.fetchall()

			if res:
				return res


	@classmethod
	def get_department(cls, dept):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM employees WHERE department=%s", (dept,))
			res = cursor.fetchall()
			return res


	@classmethod
	def search_register_by_user(cls, empid, month, year):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT emp_id, month, year FROM register WHERE emp_id=%s and month=%s and year=%s\
							GROUP BY emp_id, month, year ", (empid, month, year))
			att_list = cursor.fetchall()
			if att_list:
				return att_list



	@classmethod
	def filter_attendance_list(cls, mode, dates):
		mode = mode.lower()
		with CursorFromConnectionPool() as cursor:
			if mode == 'daily':
				daily_date = dates[0]
				cursor.execute("SELECT * FROM register WHERE date=%s", (daily_date, ))

			elif mode == 'weekly':
				startdate = dates[0]
				enddate = dates[1]
				cursor.execute("SELECT id, emp_id, month, year, date from register where TO_DATE(register.date, 'DD_MM_YYYY') \
								>= TO_DATE(%s, 'DD-MM-YYYY') and TO_DATE(register.date, 'DD-MM-YYYY') \
								<= TO_DATE(%s, 'DD-MM-YYYY') order by id asc;", (startdate, enddate))

			elif mode == 'monthly':
				month = dates[0]
				year = dates[1]
				cursor.execute("SELECT * FROM register WHERE month=%s and year=%s", (month, year))

			result = cursor.fetchall()

			return result


	@classmethod
	def days_in_date(cls, sDate, eDate):
		date_list = list()
		sDate = datetime.datetime.today().strptime(sDate, '%d-%M-%Y')
		eDate = datetime.datetime.today().strptime(eDate, '%d-%M-%Y')

		for i in daterange(sDate, eDate):
			date_list.append(i.strftime('%d-%M-%Y'))

		return date_list


	@classmethod
	def date_record(cls, date=None, empid=None, pA=None):
		with CursorFromConnectionPool() as cursor:
			if pA == None:
				cursor.execute("SELECT * FROM register WHERE date=%s and emp_id=%s", (date, empid))
				result = cursor.fetchone()
				return result
			else:
				present, absent = 0, 0
				for i in pA:
					cursor.execute("SELECT * FROM register WHERE date=%s and emp_id=%s", (i, empid))
					result = cursor.fetchone()

					if result != None:
						present += 1
					else:
						absent += 1
				return present, absent


	@classmethod
	def getlocation(cls):
		import urllib.request
		import json

		with urllib.request.urlopen("http://geolocation-db.com/json") as url:
		    data = json.loads(url.read().decode())
		    return data
		    


	@classmethod
	def check_user_ip(cls, userip):
		if listed_ip_address('192.168.83.', 254, 1, userip):
			return True
		elif listed_ip_address('155.93.123.', 5, 11, userip):
			return True
		elif listed_ip_address('197.255.61.', 5, 202, userip):
			return True
		elif listed_ip_address('41.216.164.', 5, 202, userip):
			return True
		else:
			return None




def listed_ip_address(ipaddress, looprange, start, userip):
	
	ip_chk = ipaddress + str(start)

	for a in range(looprange + 1):
		if userip == ip_chk:
			return 'Matched'
		else:
			ip_chk = ipaddress + str(start + a)
			



def daterange(date1, date2):
    for n in range(int ((date2 - date1).days)+1):
        yield date1 + timedelta(n)