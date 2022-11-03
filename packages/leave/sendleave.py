import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import url_for, render_template, current_app, redirect
from packages.database import CursorFromConnectionPool
from packages.leave.token import generate_token, confirm_token
from packages.leave.leaveOop import Leave
import datetime


class SendLeave:
	"""docstring for SendLeave"""
	def __init__(self, getid , emp_email, leavetype , startdate , enddate , duration , resumptiondate , relief_staffs , 
					address , contactperson , supervisor_id , supervisor_name , supervisor_email, department, hr_email, approver_email, 
					handover, requestdate, allowance):
		
		relief = self.__get_relief(reliefing_staff=relief_staffs)

		self.getid = getid
		self.leavetype = leavetype
		self.startdate = startdate
		self.enddate = enddate
		self.duration = duration
		self.resumptiondate = resumptiondate
		self.address = address
		self.contactperson = contactperson
		self.department = department
		self.handover = handover
		self.date = requestdate
		self.allowance = allowance
		self.year = datetime.datetime.today().strftime("%Y");

		# leave notify variable
		self.emp_email = emp_email
		self.relief1_id = relief[0]
		self.relief1_name = relief[1]
		self.relief1_email = relief[2]
		self.relief2_id = relief[3]
		self.relief2_name = relief[4]
		self.relief2_email = relief[5]
		self.relief3_id = relief[6]
		self.relief3_name = relief[7]
		self.relief3_email = relief[8]
		self.supervisor_id = supervisor_id
		self.supervisor_name = supervisor_name
		self.supervisor_email = supervisor_email
		self.hr_email = hr_email
		self.approver_email = approver_email

	def __get_relief(self, reliefing_staff):
		relief1_id = reliefing_staff['id'][0]
		relief1_name = reliefing_staff['name'][0]
		relief1_email = reliefing_staff['email'][0]

		if len(reliefing_staff['id']) >= 2:
			relief2_id = reliefing_staff['id'][1]
			relief2_name = reliefing_staff['name'][1]
			relief2_email = reliefing_staff['email'][1]
		else:
			relief2_id = None
			relief2_name = None
			relief2_email = None

		if len(reliefing_staff['id']) >= 3:
			relief3_id = reliefing_staff['id'][2]
			relief3_name = reliefing_staff['name'][2]
			relief3_email = reliefing_staff['email'][2]
		else:
			relief3_id = None
			relief3_name = None
			relief3_email = None

		relief = [relief1_id, relief1_name, relief1_email, relief2_id, relief2_name, relief2_email, relief3_id, relief3_name, relief3_email]
		return relief


	def save_leave(self, status, update):
		leave_info = self.__save_leave_info(status, update)
		
		if leave_info and status == 'Pending':
			get_id = leave_info
			save = self.__save_notification(leaveid=get_id)
			comment = self.__create_comment(leaveid=get_id)
						
			btn = SendLeave.send_mail_btn(getid=get_id, email=self.emp_email, leave_level='relief1')

			send_mail = SendLeave.send_mail(leaveid=get_id, receiving_email=self.relief1_email, acceptbtn=btn['accept'],
														declinebtn=btn['decline'])
			if send_mail is True:
								
				# in_msg = SendLeave.__leave_in_app_message(leave_id=get_id, emp_leave_id=self.getid, receiving_emp_id=self.relief1_id, 
				# 													leave_mode='relief1', msg_date=self.date, status=0)
				# if in_msg is True:
				# 	return True
				# else:
				# 	return False
				return True
			else:
				return False
		
		elif leave_info and status == 'Draft':
			return True
		else:
			return False		
			

	@classmethod
	def hr_approver(cls, empid, getid, email, column, comment, action, mode):
		if mode == 1:
			hr_comment = SendLeave.__comment(column_name=column, comment=comment, leaveid=getid, action=action)
			if hr_comment is True:
				apprv = SendLeave.final_approve(emp_id=empid, leaveid=getid, email=email)
				if apprv:
					return True

		elif mode == 0:
			hr_comment = SendLeave.__comment(column_name=column, comment=comment, leaveid=getid, action='decline')
			with CursorFromConnectionPool() as cursor:
				cursor.execute("UPDATE leaverequest SET status=%s WHERE id=%s", ('Declined', leaveid))
				cursor.execute("UPDATE leavenotify SET status=%s WHERE leave_id=%s", ('Declined', leaveid))
				
			mail_notice = SendLeave.send_mail(leaveid=getid, receiving_email=email, user='notifyuser', mode='decline')
			if mail_notice is True:
				return True

	@classmethod
	def final_approve(cls, emp_id, leaveid, email):
		get_days = SendLeave.__leavedays(emp_id=emp_id)
		leavedays = get_days[0]
		usedDays = get_days[1]

		info = Leave.get_leave_details(leave_id=leaveid)
		leavename = info[1]
		request_days = info[5]
		outstanding_days = int(leavedays) - int(request_days)
		uDays = usedDays + request_days

		# update final record
		ConfirmLeave.final_update(name='final_action', val='accept', leaveid=leaveid)
		ConfirmLeave.final_update(name='status', val='Approved', leaveid=leaveid)

		if leavename.lower() != 'annual leave':
			# check if the user once apply for the leave
			__isFound = Leave.checkOtherLeave(name=info[1], empid=emp_id)
			if __isFound:
				total_days = __isFound[3]
				remain_days = __isFound[5]
				used_days = request_days

				remain_days = int(remain_days) - int(used_days)
				Leave.OtherLeave(empid=emp_id, name=leavename, totalDays=total_days, usedDays=used_days, 
									remainDays=remain_days)
			else:
				getLeaveInfo = Leave.leavelist(name=leavename)
				total_days = getLeaveInfo[3]
				used_days = request_days

				remain_days = int(total_days) - int(request_days)
				Leave.OtherLeave(empid=emp_id, name=leavename, totalDays=total_days, usedDays=used_days, 
									remainDays=remain_days)
		else:
			SendLeave.__updateleavedays(emp_id=emp_id, days=outstanding_days, useddays=uDays)
		
		SendLeave.__finalstatus(status='Approved', leaveid=leaveid)

		mail_notice = SendLeave.send_mail(leaveid=leaveid, receiving_email=email, user='notifyuser', mode='accept')
		
		return True

	@classmethod
	def __leavedays(cls, emp_id):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT remain_days, used_days FROM leavedays WHERE emp_id=%s LIMIT 1", (emp_id,))
			res = cursor.fetchone()
			return res

	@classmethod
	def getdays(cls, emp_id): #update on live server
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT remain_days FROM leavedays WHERE emp_id=%s LIMIT 1", (emp_id,))
			res = cursor.fetchone()
			if res:
				return res[0]

	@classmethod
	def __updateleavedays(cls, emp_id, days, useddays):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("UPDATE leavedays SET remain_days=%s, used_days=%s WHERE emp_id=%s", (days, useddays, emp_id))


	@classmethod
	def __finalstatus(cls, status, leaveid):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("UPDATE leaverequest SET status=%s WHERE id=%s", (status, leaveid))


	@classmethod
	def __comment(cls, column_name, comment, leaveid, action):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("UPDATE leavecomment SET {}=%s WHERE leaveid=%s".format(column_name), (comment, leaveid))
			cursor.execute("UPDATE leavenotify SET hr_action=%s WHERE leave_id=%s", (action, leaveid))
			if cursor:
				return True


	def __save_leave_info(self, status, update=None):
		with CursorFromConnectionPool() as cursor:
			if update == None:
				cursor.execute("INSERT INTO leaverequest(emp_id, leavetype, startdate, enddate, duration, resumeday, address, \
										contact, department, handover, requestdate, status, allowance, year) \
										VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id", 
										(self.getid, self.leavetype, self.startdate, self.enddate, self.duration, self.resumptiondate, 
											self.address, self.contactperson, self.department,  self.handover, self.date, status, 
											self.allowance, self.year))
				res = cursor.fetchone()
				if res is not None:
					return res[0]
				else:
					return None
			else:
				cursor.execute("UPDATE leaverequest SET leavetype=%s, startdate=%s, enddate=%s, duration=%s, resumeday=%s, \
										address=%s, contact=%s, department=%s, handover=%s, requestdate=%s, status=%s, \
										allowance=%s, year=%s WHERE emp_id=%s and id=%s", (self.leavetype, self.startdate, self.enddate, self.duration, self.resumptiondate, 
											self.address, self.contactperson, self.department,  self.handover, self.date, status, 
											self.allowance, self.year, self.getid, update))
				if cursor:
					return update


			


	def __save_notification(self, leaveid):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("INSERT INTO leavenotify(leave_id, email, relief1_id, relief1_name, relief1_email, relief2_id, relief2_name, \
							relief2_email, relief3_id, relief3_name, relief3_email, super_id, super_name, super_email, hr_email, \
							approve_email, relief1_action) \
							VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
							(leaveid, self.emp_email, self.relief1_id, self.relief1_name, self.relief1_email, self.relief2_id, self.relief2_name, 
								self.relief2_email, self.relief3_id, self.relief3_name, self.relief3_email, self.supervisor_id, self.supervisor_name, 
								self.supervisor_email, self.hr_email, self.approver_email, 'pending'))
			if cursor:
				return True
			else:
				return False


	def __create_comment(self, leaveid):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("INSERT INTO leavecomment(leaveid) VALUES(%s)", (leaveid,))
			if cursor:
				return True



	@classmethod
	def send_mail_btn(cls, getid, email, leave_level):
	    leave_id_token = generate_token(getid)
	    leave_email = generate_token(email)
	    level = generate_token(leave_level)
	    code_auth = generate_token('T1xe4y2v@..?') # generate a 16 random number for dynamic purpose

	    accept_url = url_for('admin.confirm', leave_id=leave_id_token, email=leave_email, level=level, mode='accept',
	                         auth=code_auth, _external=True)
	    decline_url = url_for('admin.confirm', leave_id=leave_id_token, email=leave_email, level=level, mode='decline',
	                          auth=code_auth, _external=True)

	    with CursorFromConnectionPool() as cursor:
	        cursor.execute('UPDATE leavenotify SET auth=%s WHERE leave_id=%s', (code_auth, getid))

	    btn = {
	        'accept': accept_url,
	        'decline': decline_url
	    }
	    return btn


	@classmethod
	def send_mail(cls, leaveid=None, receiving_email=None, acceptbtn=None, declinebtn=None, hr=None, user=None, mode=None, 
					remind=None):

		sendport = current_app.config['MAIL_PORT']
		smtp_server = current_app.config['SEND_MAIL_SERVER']
		sender_email = current_app.config['EMAIL_ADDRESS']
		password = current_app.config['SEND_MAIL_PASSWORD']
		receiver_email = receiving_email
		leave_info = Leave.get_leave_details(leaveid)		
	    
		message = MIMEMultipart("alternative")
		message["Subject"] = "Leave Management System"
		message["From"] = current_app.config['EMAIL_ADDRESS']
		message["To"] = receiver_email
		text = """\
		
	    		BUSINESS TRAVEL MANAGEMENT
	    		Leave Application Request
	    		"""
		if hr is not None:
			html = render_template('leave/notice_email.html')
		elif user is not None:
			url = url_for('empleave.leaveprogress', leave_id=leaveid, _external=True)
			html = render_template('userleave/noticemail.html', url=url, mode=mode)
		else:
			html = render_template('userleave/leaveDetails.html', res=leave_info, accept=acceptbtn,  decline=declinebtn, remind=remind)
		
		part1 = MIMEText(text, "plain")
		part2 = MIMEText(html, "html")

		message.attach(part1)
		message.attach(part2)

		context = ssl.create_default_context()
		try:
			with smtplib.SMTP_SSL(smtp_server, sendport, context=context) as server:
				server.login(sender_email, password)
				server.sendmail(sender_email, receiver_email, message.as_string())

				return True
		except:
			return True


	# @classmethod
	# def __leave_in_app_message(cls, leave_id, emp_leave_id, receiving_emp_id, leave_mode, msg_date, status):
	# 	with CursorFromConnectionPool() as cursor:
	# 		cursor.execute("INSERT INTO leave_message(leave_id, emp_leave_id, receiving_emp_id, leave_mode, msg_date, status) \
	# 						VALUES(%s, %s, %s, %s, %s, %s)", (leave_id, emp_leave_id, receiving_emp_id, leave_mode, msg_date, status ))
	# 		if cursor:
	# 			return True
	# 		else:
	# 			return False


	@classmethod				
	def notify(cls, get_id, email, level, receiving_email, emp_id, receiving_id, date):
		if level == 'hr':
			send_mail = SendLeave.send_mail(hr=level, receiving_email=receiving_email)
			if send_mail is True:
				return True
			else:
				False

		btn = SendLeave.send_mail_btn(getid=get_id, email=email, leave_level=level)

		send_mail = SendLeave.send_mail(leaveid=get_id, receiving_email=receiving_email, acceptbtn=btn['accept'], declinebtn=btn['decline'])
		if send_mail is True:
						
			# in_msg = SendLeave.__leave_in_app_message(leave_id=get_id, emp_leave_id=emp_id, receiving_emp_id=receiving_id, 
			# 											leave_mode=level, msg_date=date, status=0)
			# if in_msg is True:
			# 	return True
			# else:
			# 	return False
			return True
		else:
			return False


	@classmethod
	def send_reminder(cls, leaveid, leave_email, leave_level, receiving_email):
		btn = SendLeave.send_mail_btn(getid=leaveid, email=leave_email, leave_level=leave_level)
		send_mail = SendLeave.send_mail(leaveid=leaveid, receiving_email=receiving_email, acceptbtn=btn['accept'], 
										declinebtn=btn['decline'], remind='reminder')
		if send_mail:
			return True


class ConfirmLeave:
	"""docstring for ConfirmLeave"""
	def __init__(self, leaveid, email=None, leave_level=None, leave_mode=None, auth=None):
		self.id = confirm_token(leaveid)
		self.email = confirm_token(email)
		self.level = confirm_token(leave_level)
		self.mode = leave_mode
		self.auth = confirm_token(auth)
		self.date = datetime.datetime.today()

	def __repr__(self):
		pass

	def __leave_info(self):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM leaverequest WHERE id=%s LIMIT 1", (self.id,))
			res = cursor.fetchone()
			return res


	def __get_email(self):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT super_email, super_id, hr_email, approve_email FROM leavenotify WHERE leave_id=%s LIMIT 1", 
							(self.id,))
			res = cursor.fetchone()
			return res


	def process(self):
		if self.__authenticate_link() is True:
			if self.__check_paramater() is True:
				det = self.__what_level()
				details = self.__leave_info()
				email_notify = self.__get_email()
				# check if response has been made.......if made
				# redirect to a page saying your response has been processed already.
				if self.mode == 'accept':					
					if self.level == 'final':
						final = SendLeave.final_approve(emp_id=details[1], leaveid=details[0], email=self.email)
						if final is True:
							# update notification for leave user
							return True
					
					if self.level == 'supervisor':
						self.__update_notify(column_name='super_action', column_val='accept')
						self.__update_notify(column_name='hr_action', column_val='pending')
						# notify hr
						send_msg = SendLeave.notify(get_id=self.id, email=self.email, level='hr', receiving_email=email_notify[2], 
													emp_id=None, receiving_id=None, date=self.date)
						if send_msg is True:
							# update notification for leave user
							return True
					
					#update leave notify db
					self.__update_notify(column_name=det[1], column_val='accept')
					#check if next relief exist...
					next_info = ConfirmLeave.__relief_list(leaveid=self.id, column_name=det[2], column_email=det[3], column_id=det[4])
					if next_info is not None:
						# if next relief exist update relief status to 'pending'
						action = det[2].replace('name', 'action')
						notice_level = det[2].replace('_name', '')
						self.__update_notify(column_name=action, column_val='pending')
						# notify the next relief
						emp_id = details[1]

						if notice_level != 'super':
							send_msg = SendLeave.notify(get_id=self.id, email=self.email, level=notice_level, receiving_email=next_info[1], 
														emp_id=emp_id, receiving_id=next_info[2], date=self.date)
							if send_msg is True:
								# update notification for next user 
								# update notification for leave user
								return True
						# else:
						# 	send_msg = SendLeave.notify(get_id=self.id, email=self.email, level='supervisor', receiving_email=email_notify[0], 
						# 								emp_id=emp_id, receiving_id=email_notify[1], date=self.date)
						# 	if send_msg is True:
						# 		return True

					else:
						#print('Notify the supervisor')
						self.__update_notify(column_name='super_action', column_val='pending')
						emp_id = details[1]
						send_msg = SendLeave.notify(get_id=self.id, email=self.email, level='supervisor', receiving_email=email_notify[0], 
														emp_id=emp_id, receiving_id=email_notify[1], date=self.date)
						if send_msg is True:
							return True

					
				if self.mode == 'decline':
					return 'decline'
					# redirect to a form page to fill why they are declining.
			else:
				print('Invalid credentials')
				return False # invalid credentials
		else:
			print('Invalid Auth')
			return False # invalid credentials

	def __authenticate_link(self):
		auth = ConfirmLeave.__fetch_auth(leaveid=self.id)
		reverse = confirm_token(auth[1])

		if reverse == self.auth:
			return True
		else:
			return False

	def __check_paramater(self):
		value = ConfirmLeave.__fetch_auth(leaveid=self.id)
		leave_id = value[0]
		email = value[2]

		getid = int(self.id)
		if leave_id == getid and email == self.email:
			return True
		else:
			return False

	def __what_level(self):
		mode = self.level
		next_level = None
		next_email = None
		next_id = None

		if mode == 'relief1':
			level = 'relief1'
			tag = 'relief1_action'
			next_level = 'relief2_name'
			next_email = 'relief2_email'
			next_id = 'relief2_id'
		elif mode == 'relief2':
			level = 'relief2'
			tag = 'relief2_action'
			next_level = 'relief3_name'
			next_email = 'relief3_email'
			next_id = 'relief3_id'
		elif mode == 'relief3':
			level = 'relief3'
			tag = 'relief3_action'
			next_level = 'super_name'
			next_email = 'super_email'
			next_id = 'super_id'
		elif mode == 'supervisor':
			level = 'supervisor'
			tag = 'super_action'
		elif mode == 'approver':
			level = 'approver'
			tag = 'final_action'
		else:
			level = None
			tag = None


		det = [level, tag, next_level, next_email, next_id]
		return det

		
	def __update_notify(self, column_name, column_val):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("UPDATE leavenotify SET {}=%s WHERE leave_id=%s".format(column_name), (column_val, self.id))
			if cursor:
				return True


	@classmethod
	def final_update(cls, name, val, leaveid):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("UPDATE leavenotify SET {}=%s WHERE leave_id=%s".format(name), (val, leaveid))
			if cursor:
				return True


	@classmethod
	def __fetch_auth(cls, leaveid):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT leave_id, auth, email FROM leavenotify WHERE leave_id=%s LIMIT 1", (leaveid,))
			res = cursor.fetchone()
			if res is not None:
				return res
			else:
				return None

	@classmethod
	def __relief_list(cls, leaveid, column_name, column_email, column_id):
		if column_name is not None:
			with CursorFromConnectionPool() as cursor:
				cursor.execute("SELECT {}, {}, {} FROM leavenotify WHERE leave_id=%s LIMIT 1".format(column_name, column_email, column_id), 
								(leaveid,))
				res = cursor.fetchone()
				if res[0] is not None:
					return res
				else:
					return None
		else:
			return None

	
	@classmethod
	def decline(cls, leaveid, level, comment):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT {} FROM leavecomment WHERE leaveid=%s".format(level), (leaveid,))
			res = cursor.fetchone()
			if res[0] is not None:
				return 1
			else:
				cursor.execute("UPDATE leavecomment set {}=%s WHERE leaveid=%s".format(level), (comment, leaveid))
				if cursor:
					if level == 'final':
						level = 'final_action'
						
					elif level == 'supervisor':
						level = level.replace('visor', '')
						level = level+'_action'
					else:
						level = level+'_action'


					cng_name = level
					
					cursor.execute("UPDATE leavenotify SET {}=%s WHERE leave_id=%s".format(cng_name), ('decline', leaveid))
					cursor.execute("SELECT email FROM leavenotify WHERE leave_id=%s", (leaveid,))
					email = cursor.fetchone()
					cursor.execute("UPDATE leaverequest SET status=%s WHERE id=%s", ('Declined', leaveid))
					if cursor:
						mail_notice = SendLeave.send_mail(leaveid=leaveid, receiving_email=email[0], user='notifyuser', 
															mode='decline')
						return True
					
					else:
						return False



