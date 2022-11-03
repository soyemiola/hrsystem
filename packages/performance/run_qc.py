import os
import random
from flask import Blueprint, render_template, url_for, redirect, flash, request, make_response, jsonify, current_app
from werkzeug.utils import secure_filename
from flask_login import current_user
from packages.performance.qcOop import QC
from packages.employees.userOop import Employee
from packages.functions import fetch_table_record
from datetime import datetime
import base64
import pdfkit
from packages.performance.performanceOop import Performance


qc = Blueprint('qc', __name__, static_folder='/static', template_folder='templates', url_prefix='/')

def getRecord(emp_id, startdate, enddate):
	return QC(emp_id=emp_id).get_report(start=startdate, end=enddate)

@qc.before_request
def chk_session():
    if not current_user.is_authenticated:
        return redirect(url_for('admin.login', next=request.url))


@qc.route('/admin/performance/QC-new', methods=['POST', 'GET'])
def addqc():
	dept_list = fetch_table_record(tablename='department')

	variance = Performance.computation()

	if request.method == 'POST':
		emp_id = request.form['employee']
		emp_det = Employee.emp_per_record(emp_id=emp_id)
	else:
		emp_det = None

	query = request.args.get('userid')
	if query:
		emp_det = Employee.emp_per_record(emp_id=query)

	return render_template('performance/addqc.html', department=dept_list, emp_det=emp_det, var=variance)


@qc.route('/admin/fetch-record', methods=['POST', 'GET'])
def fetchrecord():
	if request.method == 'POST':
		dept = request.form['dept']
		emp_list = QC.fetch_dept(dept=dept)
		if emp_list is not None:
			return make_response(jsonify(emp_list))
		else:
			return make_response(jsonify('None'))


@qc.route('/admin/performance/QC-report', methods=['POST', 'GET'])
def qcreport():
	record_list = QC.recordList()
	dept_list = fetch_table_record(tablename='department')
	variance = Performance.computation()
	reportComd = list()
	reportQry = list()

	if request.method == 'POST':
		emp_det = Employee.emp_per_record(emp_id=request.form['employee'])
		qclist = getRecord(emp_id=request.form['employee'], startdate=request.form['startdate'], \
							enddate=request.form['enddate'])

		for i in qclist:
			if i[2].lower() == 'commendation':
				reportComd.append(i)
			elif i[2].lower() == 'query':
				reportQry.append(i)

		#reports = reportComd, reportQry
		reports = qclist

		if len(reports) == 0:
			flash('No record found', 'info')
			return redirect(url_for('qc.qcreport'))

		start = request.form['startdate']
		end = request.form['enddate']
	else:
		emp_det = None
		reports = None
		start = None
		end = None


	userid = request.args.get('userid')
	q = request.args.get('q')
	
	if userid:
		startdate = request.args.get('startdate')
		enddate = request.args.get('enddate')
		emp_det = Employee.emp_per_record(emp_id=userid)
		reports = getRecord(emp_id=userid, startdate=startdate, enddate=enddate)
		
		if reports:
			flash('No record found', 'info')
			return redirect(url_for('qc.qcreport'))
		start = startdate
		end = enddate
	elif q:
		date = request.args.get('date')
		emp_det = Employee.emp_per_record(emp_id=q)
		qclist = QC(emp_id=q).get_report(start=date, end=date)

		for i in qclist:
			if i[2].lower() == 'commendation':
				reportComd.append(i)
			elif i[2].lower() == 'query':
				reportQry.append(i)

		#reports = reportComd, reportQry
		reports = qclist

	return render_template('performance/qcreport.html', department=dept_list, var=variance, emp_det=emp_det, reports=reports, start=start, \
							end=end, record_list=record_list)


@qc.route('/admin/performance/QC-report-item', methods=['POST', 'GET'])
def qcreport_item():
	if request.method == 'POST':
		reportid = request.form['id']
		items = QC.reportitem(reportid=reportid)
		return make_response(jsonify(items))




@qc.route('/admin/saveqc-report', methods=['POST', 'GET'])
def saveqc():
	try:
		if request.method == 'POST':
			emp_id = request.form['emp_id']
			emp_name = request.form['emp_name']
			department = request.form['department']
			mode = request.form['mode']
			receive_date = request.form['receive_date']
			subject = request.form['subject']
			summary = request.form['summary']
			attachment = request.files['attachment']
			save_by = current_user.firstname +' '+ current_user.lastname
			date = datetime.today().strftime('%Y-%m-%d')

			if attachment.filename is None or attachment.filename == '':
				attachment = ''
			else:
				# save file
				try:
					file_secure_name = secure_filename(attachment.filename)
					filename = emp_name + '_'+ mode + '_' + date + '_'+ str(random.randint(1, 5)) + '_' + file_secure_name 
					attachment.save(os.path.join(current_app.config['QC_FOLDER'], filename))

					attachment = filename
				except:
					flash("Error saving file, Try again!", 'danger')
					return redirect(url_for('qc.addqc', userid=emp_id))

			save_report = QC(emp_id=emp_id).new_qc_report(
				mode=mode, date_received=receive_date, date_saved=date, subject=subject, summary=summary, attachment=attachment, 
				submitby=save_by, department=department
				)
			if save_report is True:
				flash("Report submitted sucessfully", 'success')
				return redirect(url_for('qc.addqc', userid=emp_id))
	except:
		flash("Error saving report, Please try again !", 'danger')
		return redirect(url_for('qc.addqc'))


@qc.route('/admin/updateqc-report', methods=['POST', 'GET'])
def updateqc():
	try:
		if request.method == 'POST':
			emp_id = request.form['emp_id']
			emp_name = request.form['emp_name']
			mode = request.form['mode']
			receive_date = request.form['receive_date']
			subject = request.form['subject']
			summary = request.form['summary']
			attachment = request.files['attachment']
			update_by = current_user.firstname +' '+ current_user.lastname
			date = datetime.today().strftime('%Y-%m-%d')
			reportid = request.form['reportid']
			reportpdf = request.form['filename']

			startdate = request.form['start']
			enddate = request.form['end']


			if attachment.filename is None or attachment.filename == '':
				attachment = reportpdf
			else:
				# update file
				try:
					file_secure_name = secure_filename(attachment.filename)
					filename = emp_name + '_'+ mode + '_' + date + '_'+ str(random.randint(1, 5)) + '_' + file_secure_name 
					attachment.save(os.path.join(current_app.config['QC_FOLDER'], filename))

					attachment = filename
				except:
					flash("Error saving file, Try again!", 'danger')
					return redirect(url_for('qc.qcreport', userid=emp_id))

			update_report = QC.update_qc_report(reportid=reportid, mode=mode, date_received=receive_date, date_saved=date, 
												subject=subject, summary=summary, attachment=attachment, editby=update_by)
			if update_report is True:
				flash("Report updated sucessfully", 'success')
				return redirect(url_for('qc.qcreport', userid=emp_id, startdate=startdate, enddate=enddate))

			
	except:
		flash("Error updating report, Please try again !", 'danger')
		return redirect(url_for('qc.qcreport'))
	

@qc.route('/admin/deleteqc-report', methods=['POST', 'GET'])
def deleteqc():
	if request.method == 'POST':
		emp_id = request.form['emp_id']
		reportID = request.form['reportid']
		start = request.form['deletestart']
		end = request.form['deleteend']

		delete = QC.delete_qc_report(reportid=reportID)
		if delete is True:
			flash('Report deleted successfully', 'success')
			return redirect(url_for('qc.qcreport', userid=emp_id, startdate=start, enddate=end))
		else:
			flash('Error deleting report, Try again!', 'danger')
			return redirect(url_for('qc.qcreport', userid=emp_id, startdate=start, enddate=end))


@qc.route('/admin/qcreportPDF', methods=['POST', 'GET'])
def qcreportPDF():
	brandimage = get_image_file_as_base64_data(os.path.join(os.path.dirname(__file__), 'logo.png'))

	if request.method == 'GET':
		emp_id = request.args.get('employees')
		startdate = request.args.get('startdate')
		enddate = request.args.get('enddate')

		# fetch emp record
		emp_det = Employee.emp_per_record(emp_id=emp_id)
		# fetch emp report record
		reports = QC(emp_id=emp_id).get_report(start=startdate, end=enddate)

		filename = emp_det[1]+' QC Report.pdf'
		rendered = render_template('performance/qcPDF.html', emp_det=emp_det, reports=reports, logo=brandimage)

		# pdf = pdfkit.from_string(rendered, False)
		# response = make_response(pdf)
		# response.headers['Content-Type'] = 'application/pdf'
		# response.headers['Content-Disposition'] = 'inline; filename='+filename

		return rendered


def get_image_file_as_base64_data(filepath: str) -> str:
    with open(filepath, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode()
