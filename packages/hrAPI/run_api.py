from flask import Blueprint, redirect, request, make_response, jsonify, session, render_template
from flask_cors import CORS, cross_origin
from packages.database import CursorFromConnectionPool


hrapi = Blueprint('hrapi', __name__, url_prefix='/', template_folder='templates')
CORS(hrapi)



class Api:
	
	@classmethod
	def savevisareport(cls, date, info):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("INSERT INTO visaimmigration(date, details)VALUES(%s, %s)", (date, info))
			if cursor:
				return True


	@classmethod
	def updaterecord(cls, info, recordid):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("UPDATE visaimmigration SET details=%s WHERE id=%s", (info, recordid))
			if cursor:
				return True


	@classmethod
	def getreport(cls,):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM visaimmigration order by date desc")
			res = cursor.fetchall()
			if res:
				return res


	@classmethod
	def editreport(cls, reportid):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM visaimmigration WHERE id=%s LIMIT 1", (reportid, ))
			res = cursor.fetchone()
			if res:
				return res


	@classmethod
	def delrecord(cls, reportid):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("DELETE FROM visaimmigration WHERE id=%s", (reportid, ))
			if cursor:
				return True

		
   
@hrapi.route('/api/visaimmigration/', methods=['POST', 'GET'])
def saverecord():
	
	if request.method == 'POST':
		date = request.form.get('date')
		file_for_client = request.form.get('file_for_client')
		client_name = request.form.get('client_name')
		client_contact = request.form.get('client_contact')
		client_company_or_refer = request.form.get('client_company_or_refer')
		type_of_visa = request.form.get('type_of_visa')
		list_of_requirement = request.form.get('list_of_requirement')
		document_provided = request.form.get('document_provided')
		signed_process_document = request.form.get('signed_process_document')
		process_timeframe = request.form.get('process_timeframe')
		additional_service = request.form.get('additional_service')
		additional_service_list = request.form.get('additional_service_list')
		courier = request.form.get('courier')
		courier_cost = request.form.get('courier_cost')
		total_cost = request.form.get('total_cost')
		payment_received = request.form.get('payment_received')
		payment_received_date = request.form.get('payment_received_date')
		payment_receivedVia = request.form.get('payment_receivedVia')
		receipt_to_client = request.form.get('receipt_to_client')
		complete_document_received_from_client = request.form.get('complete_document_received_from_client')
		total_document_received = request.form.get('total_document_received')
		date_complete_document_received = request.form.get('date_complete_document_received')
		complete_document_received_by = request.form.get('complete_document_received_by')
		date_document_received_for_processing = request.form.get('date_document_received_for_processing')
		submission_delay_reason = request.form.get('submission_delay_reason')
		date_visa_returned_from_eci = request.form.get('date_visa_returned_from_eci')
		visa_status = request.form.get('visa_status')
		appeal_required = request.form.get('appeal_required')
		appeal_required_reason = request.form.get('appeal_required_reason')
		date_document_received_by_client = request.form.get('date_document_received_by_client')
		refund_required = request.form.get('refund_required')
		refund_required_amount = request.form.get('refund_required_amount')
		refund_required_reason = request.form.get('refund_required_reason')
		refund_required_date = request.form.get('refund_required_date')
		refund_required_via = request.form.get('refund_required_via')
		refund_required_receipt = request.form.get('refund_required_receipt')
		process_completed = request.form.get('process_completed')
		process_completed_no_reason = request.form.get('process_completed_no_reason')
		process_completed_yes_date = request.form.get('process_completed_yes_date')
		btm_officer_name = request.form.get('btm_officer_name')

		# info = {
		# 	'Date': date, 'File opened for client?': file_for_client, 'Client Name': client_name, 'Client Contact': client_contact, 
		# 	'Company/Walk in passenger, If walk in referred to BTM by whom?': client_company_or_refer, 'Type of visa/immigration service': type_of_visa,
		# 	'Client provided with list of requirements': list_of_requirement, 'Client provided with documented processes for service': document_provided, 
		# 	'Client signed documented processes for service': signed_process_document, 'Client informed of processing timeframe': process_timeframe, 
		# 	'Client requested additional service?': additional_service, 'Additional service selected by client': additional_service_list, 
		# 	'Courier service / document delivery fees applicable?': courier, 'Cost': courier_cost,
		# 	'Client provided with total cost in writing': total_cost, 'Payment received by client': payment_received, 'Date payment received': payment_received_date, 
		# 	'Payment via': payment_receivedVia, 'Receipt provided to client': receipt_to_client, 
		# 	'Complete documents received from client and signed for by BTM officer': complete_document_received_from_client, 
		# 	'Total number of documents received': total_document_received, 'Date complete documents received': date_complete_document_received, 
		# 	'Completed documents received by BTM officer': complete_document_received_by, 'Date documents submitted for processing': date_document_received_for_processing, 
		# 	'If submission delay insert reason': submission_delay_reason, 'Date Visa/immigration document returned from embassy/ consulate/ immigration': date_visa_returned_from_eci, 
		# 	'Visa/Immigration result & status': visa_status, 'Appeal/resubmission required?': appeal_required, 'Reason for appeal / resubmission': appeal_required_reason, 
		# 	'Date documents collected by client': date_document_received_by_client, 'Refund required?': refund_required, 'Refund Amount': refund_required_amount, 
		# 	'Reason for Refund': refund_required_reason, 'Date refund paid': refund_required_date, 'Refund via': refund_required_via, 
		# 	'Refund receipt/credit note provided to client': refund_required_receipt, 'Process completed': process_completed, 
		# 	'Date of process completion': process_completed_yes_date, 'Process not complete reason': process_completed_no_reason, 
		# 	'BTM Visa & Immigration officer Name': btm_officer_name
		# }

		details = [date, file_for_client, client_name, client_contact, client_company_or_refer, type_of_visa, list_of_requirement, document_provided, signed_process_document, 
					process_timeframe, additional_service, additional_service_list, courier, courier_cost, total_cost, payment_received, payment_received_date, 
					payment_receivedVia, receipt_to_client, complete_document_received_from_client, total_document_received, date_complete_document_received, 
					complete_document_received_by, date_document_received_for_processing, submission_delay_reason, date_visa_returned_from_eci, visa_status, appeal_required, 
					appeal_required_reason, date_document_received_by_client, refund_required, refund_required_amount, refund_required_reason, refund_required_date, 
					refund_required_via, refund_required_receipt, process_completed, process_completed_yes_date, process_completed_no_reason, btm_officer_name]

		saverecord = Api.savevisareport(date=date, info=details)
		if saverecord == True:
			return 'saved'


		

		
	
@hrapi.route('/api/visaimmigration/getrecord/', methods=['GET'])
def getreport():

	if request.method == 'GET':
		date = request.args.get('date')

		if date == 'month':
			report = Api.getreport()
			
			return make_response(jsonify(report))
		else:
			return make_response(jsonify(None))


@hrapi.route('/api/visaimmigration/editReport/', methods=['GET'])
def editReport():

	if request.method == 'GET':
		reportid = request.args.get('id')

		getDet = Api.editreport(reportid)

		return make_response(jsonify(getDet))



@hrapi.route('/api/visaimmigration/updaterecord/', methods=['POST', 'GET'])
def updaterecord():
	
	if request.method == 'POST':
		recordid = request.form.get('recordid')
		date = request.form.get('date')
		file_for_client = request.form.get('file_for_client')
		client_name = request.form.get('client_name')
		client_contact = request.form.get('client_contact')
		client_company_or_refer = request.form.get('client_company_or_refer')
		type_of_visa = request.form.get('type_of_visa')
		list_of_requirement = request.form.get('list_of_requirement')
		document_provided = request.form.get('document_provided')
		signed_process_document = request.form.get('signed_process_document')
		process_timeframe = request.form.get('process_timeframe')
		additional_service = request.form.get('additional_service')
		additional_service_list = request.form.get('additional_service_list')
		courier = request.form.get('courier')
		courier_cost = request.form.get('courier_cost')
		total_cost = request.form.get('total_cost')
		payment_received = request.form.get('payment_received')
		payment_received_date = request.form.get('payment_received_date')
		payment_receivedVia = request.form.get('payment_receivedVia')
		receipt_to_client = request.form.get('receipt_to_client')
		complete_document_received_from_client = request.form.get('complete_document_received_from_client')
		total_document_received = request.form.get('total_document_received')
		date_complete_document_received = request.form.get('date_complete_document_received')
		complete_document_received_by = request.form.get('complete_document_received_by')
		date_document_received_for_processing = request.form.get('date_document_received_for_processing')
		submission_delay_reason = request.form.get('submission_delay_reason')
		date_visa_returned_from_eci = request.form.get('date_visa_returned_from_eci')
		visa_status = request.form.get('visa_status')
		appeal_required = request.form.get('appeal_required')
		appeal_required_reason = request.form.get('appeal_required_reason')
		date_document_received_by_client = request.form.get('date_document_received_by_client')
		refund_required = request.form.get('refund_required')
		refund_required_amount = request.form.get('refund_required_amount')
		refund_required_reason = request.form.get('refund_required_reason')
		refund_required_date = request.form.get('refund_required_date')
		refund_required_via = request.form.get('refund_required_via')
		refund_required_receipt = request.form.get('refund_required_receipt')
		process_completed = request.form.get('process_completed')
		process_completed_no_reason = request.form.get('process_completed_no_reason')
		process_completed_yes_date = request.form.get('process_completed_yes_date')
		btm_officer_name = request.form.get('btm_officer_name')


		details = [date, file_for_client, client_name, client_contact, client_company_or_refer, type_of_visa, list_of_requirement, document_provided, signed_process_document, 
					process_timeframe, additional_service, additional_service_list, courier, courier_cost, total_cost, payment_received, payment_received_date, 
					payment_receivedVia, receipt_to_client, complete_document_received_from_client, total_document_received, date_complete_document_received, 
					complete_document_received_by, date_document_received_for_processing, submission_delay_reason, date_visa_returned_from_eci, visa_status, appeal_required, 
					appeal_required_reason, date_document_received_by_client, refund_required, refund_required_amount, refund_required_reason, refund_required_date, 
					refund_required_via, refund_required_receipt, process_completed, process_completed_yes_date, process_completed_no_reason, btm_officer_name]

		saverecord = Api.updaterecord(info=details, recordid=recordid)
		if saverecord == True:
			return 'saved'


@hrapi.route('/api/visaimmigration/deleterecord/', methods=['GET'])
def deleterecord():
	reportId = request.args.get('id')

	if reportId:
		delrcd = Api.delrecord(reportId)

		if delrcd == True:
			return make_response(jsonify('True'))



