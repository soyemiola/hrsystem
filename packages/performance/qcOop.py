from packages.database import CursorFromConnectionPool


class QC:
	"""docstring for QC"""
	def __init__(self, emp_id):
		self.id = emp_id


	def new_qc_report(self, mode, date_received, date_saved, subject, summary, attachment, submitby, department):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("INSERT INTO qcreport(emp_id, mode, date_received, date_saved, subject, summary, attachment, \
												submitby, department) \
							VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id", 
							(self.id, mode, date_received, date_saved, subject, summary, attachment, submitby, department))
			qc_id = cursor.fetchone()
			if qc_id:
				return True
			else:
				return False
				

	@classmethod
	def update_qc_report(cls, reportid, mode, date_received, date_saved, subject, summary, attachment, editby):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("UPDATE qcreport SET mode=%s, date_received=%s, date_saved=%s, subject=%s, summary=%s, \
								attachment=%s, editby=%s WHERE id=%s", 
								(mode, date_received, date_saved, subject, summary, attachment, editby, reportid))
			if cursor:
				return True
			else:
				return False

	@classmethod
	def delete_qc_report(cls, reportid):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("DELETE FROM qcreport WHERE id=%s", (reportid,))
			if cursor:
				return True


	def get_report(self, start, end):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM qcreport WHERE emp_id=%s AND date_received BETWEEN %s AND %s ORDER BY id", 
							(self.id, start, end))
			result = cursor.fetchall()
			if result:
				return result
			else:
				return None

	@classmethod
	def fetch_dept(cls, dept):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM employees WHERE department=%s and active=%s ORDER BY name", (dept, 1))
			record_list = cursor.fetchall()
			if record_list:
				return record_list
			else:
				return None

	@classmethod
	def reportitem(cls, reportid):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT qcreport.id, qcreport.emp_id, qcreport.mode, qcreport.date_received, qcreport.date_saved, \
								qcreport.subject, qcreport.summary, qcreport.attachment, qcreport.submitby,  employees.name \
							FROM qcreport \
							LEFT JOIN employees \
							ON qcreport.emp_id = employees.id \
							WHERE qcreport.id = %s", (reportid,))
			result = cursor.fetchone()
			if result:
				return result


	@classmethod
	def recordList(cls,):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT employees.id, employees.name, employees.staff_id, employees.department, qcreport.id,\
							qcreport.mode, qcreport.date_received, qcreport.date_saved, qcreport.subject, qcreport.summary,\
							qcreport.attachment\
							FROM qcreport\
							LEFT JOIN employees\
							ON employees.id = qcreport.emp_id\
							WHERE employees.active=%s\
							ORDER BY qcreport.date_received desc", (1,))
			result = cursor.fetchall()
			if result:
				return result


	def variancelist(self, start, end):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM qcreport WHERE emp_id=%s and date_received BETWEEN %s and %s order by date_received desc", 
							(self.id, start, end))
			vlist = cursor.fetchall()
			return vlist


	def variancepoint(self, mode, start, end):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT count(*) from qcreport WHERE mode=%s and emp_id=%s and date_received between %s and %s",
							(mode, self.id, start, end))
			vpoint = cursor.fetchone()
			return vpoint[0]




