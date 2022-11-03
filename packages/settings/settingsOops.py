from packages.database import CursorFromConnectionPool


class Department(object):
	"""docstring for Department"""
	def __init__(self, dept_id):
		self.id = dept_id

	def __repr__(self):
		pass

	@classmethod
	def new_record(cls, name, sop_file):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("INSERT INTO department(name, sop) VALUES(%s, %s)", (name, sop_file))
			if cursor:
				return True

	def update_department(self, oldname, new_name, sop, supervisor):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("UPDATE department SET name=%s, sop=%s, supervisor=%s WHERE id=%s", (new_name, sop, supervisor,
																								 self.id))
			if cursor:
				cursor.execute("UPDATE employees SET department=%s WHERE department=%s", (new_name, oldname))
				if cursor:
					return True
				else:
					pass
			else:
				pass


class Designation():
	"""docstring for Designation"""
	def __init__(self, designation_id):
		self.id = designation_id

	def __repr__(self):
		pass


	@classmethod
	def create_new_record(cls, name, jd, department):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("INSERT INTO post(name, jd, department) VALUES(%s, %s, %s)", (name, jd, department))
			if cursor:
				return True

	def update_designation(self, name, jd, department, oldname):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("UPDATE post SET name=%s, jd=%s, department=%s WHERE id=%s", (name, jd, department, self.id))
			if cursor:
				cursor.execute("UPDATE employees SET post=%s WHERE post=%s", (name, oldname))
				if cursor:
					return True



class Documents:
	"""docstring for Documents"""
	def __init__(self, empid):
		self.empid = empid

	def __repr__(self):
		pass


	@classmethod
	def save_docx(cls, empid, name, docx, uploadby, month, year, uploadtime, category):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("INSERT INTO empdocument(emp_id, docx_name, document, uploadby, month, year, uploadtime, category) \
							VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", 
							(empid, name, docx, uploadby, month, year, uploadtime, category))
			if cursor:
				return True

	def getdocx(self):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT * FROM empdocument WHERE emp_id=%s ORDER BY ID ASC", (self.empid, ))
			docx = cursor.fetchall()
			if docx:
				return docx


	def empdet(self):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT id, name, department, jobtitle, post FROM employees WHERE id=%s", (self.empid, ))
			res = cursor.fetchone()
			if res:
				return res


	@classmethod
	def emp_document(cls):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("SELECT empdocument.emp_id, count(empdocument.emp_id) FROM empdocument \
							left join employees on employees.id = empdocument.emp_id \
							group by empdocument.emp_id")
			has_docx = cursor.fetchall()
			if has_docx:
				return has_docx


	def remove_docx(self, docxid):		
		with CursorFromConnectionPool() as cursor:
			cursor.execute("DELETE FROM empdocument WHERE emp_id=%s and id=%s", (self.empid, docxid))
			if cursor:
				return True


	def userDocumentUpdate(self, docx_name, document, uploadby, docxid, month, year):
		with CursorFromConnectionPool() as cursor:
			cursor.execute("UPDATE empdocument SET docx_name=%s, document=%s, uploadby=%s, month=%s, year=%s WHERE emp_id=%s and id=%s", 
							(docx_name, document, uploadby, month, year, self.empid, docxid))
			if cursor:
				return True



		