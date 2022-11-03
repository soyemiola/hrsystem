from flask import Blueprint, render_template, redirect, url_for, request, current_app, make_response, jsonify, flash
from flask_login import current_user
from packages.attendance.attendanceOop import attendance
import calendar
import datetime
from packages.run_admin import year_selector
from packages.functions import fetch_table_record
from packages.employees.userOop import Employee



register = Blueprint('register', __name__, url_prefix='/', template_folder='templates', static_folder='static')


@register.before_request
def chk_session():
    if not current_user.is_authenticated:
        return redirect(url_for('admin.login', next=request.url))


@register.route('/admin/attendance', methods=['POST', 'GET'])
def home():
	employees = attendance.active_employee()
	department = fetch_table_record('department')
	view = None

	month = {v: k for k, v in enumerate(calendar.month_name)}
	year = year_selector()

	att = attendance.current_month()
	#today = datetime.datetime.today().strftime("%d-%M-%Y")

	if request.method == 'POST' and request.form['getattendance'] == 'search':
		empid = request.form['employee']
		search_month = request.form['month']
		search_year = request.form['year']

		att = attendance.search_register_by_user(empid, search_month, search_year)

		if att == None:
			flash('No Record found', 'info')
		view = 1

	return render_template('attendance/attendance.html', users=employees, dept=department, month=month, year=year, att=att, view=view)



@register.route('/admin/getemp', methods=['POST'])
def getemp():
	if request.method == 'POST' :
		dept = request.form['dept']
		resp = attendance.get_department(dept=dept)
		return make_response(jsonify(resp))



@register.route('/admin/staffattendanceprofile/<userId>/<month>/<year>')
def staff_profile(userId, month, year):
	user_info = Employee.emp_per_record(emp_id=userId)
	att_info = attendance.get_login_details(emp_id=userId, month=month, year=year)
	return render_template('attendance/register.html', user_info=user_info, att=att_info)



@register.route('admin/attendance/settings', methods=['POST', 'GET'])
def att_settings():
	att_list = attendance.schedules()
	statusId = request.args.get('timeId')
	status = request.args.get('status')
	
	if statusId != None and status == 'edit':
		edit = attendance.schedules(record=statusId)
	else:
		edit = None

	if statusId != None and status == 'active':
		active = attendance.active_time(statusId=statusId)
		if active == True:
			flash('Attendance Time Schedule Activated', 'success')
			return redirect(url_for('register.att_settings'))

	# delete record
	if statusId != None and status == 'delete':
		remove = attendance.remove_time(statusId=statusId)
		if remove == True:
			flash('Time schedule deleted successfully', 'success')
			return redirect(url_for('register.att_settings'))


	if request.method == 'POST':
		name = request.form['name']
		resume = request.form['resume']
		close = request.form['close']
		shift = request.form['shift']
		isId = request.form.get('editid')

		if not isId:
			create_time = attendance.register_time(name=name, resume=resume, close=close, shift=shift)
			if create_time is True:
				flash('New Time schedule created successfully', 'success')
				return redirect(url_for('register.att_settings'))
			else:
				flash('Error creating time schedule', 'danger')
				return redirect(url_for('register.att_settings'))
		else:
			update_time = attendance.update_register_time(name=name, resume=resume, close=close, shift=shift, updateid=isId)
			if update_time is True:
				flash('Time schedule updated successfully', 'success')
				return redirect(url_for('register.att_settings'))
			else:
				flash('Error updating time schedule', 'danger')
				return redirect(url_for('register.att_settings'))

	
	return render_template('attendance/att_settings.html', att_list=att_list, edit=edit)


@register.route('admin/attendance/report', methods=['POST', 'GET'])
def attendance_reporting():
	dates = list()

	if request.method == 'POST':
		report_type = request.form['rtype'].lower()

		if report_type == 'daily':
			mode = 'daily'
			dD = request.form['Ddate']
			dD = datetime.datetime.today().strptime(dD, '%Y-%m-%d').strftime('%d-%m-%Y') # 2022-01-03
			dates.append(dD)

		elif report_type == 'weekly':
			mode = 'weekly'
			wkstart = datetime.datetime.today().strptime(request.form['wdate-start'], '%Y-%m-%d').strftime('%d-%m-%Y') 
			wkend = datetime.datetime.today().strptime(request.form['wdate-end'], '%Y-%m-%d').strftime('%d-%m-%Y') 

			dates.append(wkstart)
			dates.append(wkend)

		elif report_type == 'monthly':
			mode = 'monthly'
			mMonth = request.form['Mmonth']
			mYear = request.form['Myear']
			dates.append(mMonth)
			dates.append(mYear)

		result = attendance.filter_attendance_list(mode, dates), mode
		
		return render_template('attendance/reporting.html', info=result, dates=dates)

	else:
		return redirect(url_for('register.home'))



@register.add_app_template_filter
def get_register_name(emp_id, mode=None):
	name = attendance.reg_name(emp_id)
	if mode == None:
		return name[1]
	else:
		return name


@register.add_app_template_filter
def get_register_date(emp_id, month, year):
	result = attendance.get_login_details(emp_id, month, year)
	return result


@register.add_app_template_filter
def return_day_value(date):
	day = datetime.datetime.today().strptime(date, '%d-%M-%Y').strftime("%d")
	return int(day)


@register.add_app_template_filter
def get_overtime(closetime, resumetime):
	if cTime != None:
		cTime = datetime.datetime.today().strptime(closetime, '%H:%M')
		rTime = datetime.datetime.today().strptime(resumetime, '%H:%M')

		overTime = cTime - rTime
		return overTime
	else:
		return None


@register.add_app_template_filter
def time_diff(date1, date2):
	d1 = datetime.datetime.today().strptime(date1, '%d-%M-%Y')
	d2 = datetime.datetime.today().strptime(date2, '%d-%M-%Y')

	diff = d2 - d1 
	return diff.days + 1


@register.add_app_template_filter
def dates_list(sDate, eDate):
	days = attendance.days_in_date(sDate, eDate)
	return days


@register.add_app_template_filter
def get_date_record(date, empid, pA=None):
	return attendance.date_record(date, empid, pA)
		

