from packages.database import CursorFromConnectionPool


class Performance:

    def __init__(self, code=None, department=None, status=None):
        self.code = code
        self.department = department
        self.status = status

    def __repr__(self):
        pass

    def get_all_targets(self, current_year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM target WHERE status =%s and year=%s', (self.status, current_year))
            res = cursor.fetchall()
            if res:
                return res

    def get_target_code(self):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM target WHERE target_uid =%s', (self.code,))
            res = cursor.fetchone()
            if res:
                return res

    def target_supervisor(self, post):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM employees WHERE department =%s and post=%s', (self.department, post))
            res = cursor.fetchone()
            if res:
                return res

    def target_emp(self):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT targetemp.id, targetemp.unique_code, targetemp.emp_id, targetemp.status,\
                            targetemp.targetuid, targetemp.super_action, targetemp.department, targetemp.emp_signed,\
                            targetemp.complete_review, targetemp.active, targetemp.process, targetemp.accept,\
                            targetemp.reason, employees.active\
                            FROM targetemp\
                            LEFT JOIN employees\
                            ON targetemp.emp_id = employees.id\
                            WHERE employees.active = %s and targetemp.unique_code = %s and targetemp.department=%s',
                           (1, self.code, self.department))
            res = cursor.fetchall()
            if res:
                return res

    def fetch_target_details(self, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM target_score WHERE uniquecode =%s and emp_id=%s',
                           (self.code, emp_id))
            res = cursor.fetchone()
            if res:
                return res

    def compute_value(self, name, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT {} FROM target_score WHERE uniquecode =%s and emp_id=%s '.
                           format(name),
                           (self.code, emp_id))
            res = cursor.fetchone()
            if res:
                if res[0] is not None:
                    return res[0]
                else:
                    return 0

    @classmethod
    def get_emp_details(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM employees WHERE id=%s',
                           (emp_id,))
            res = cursor.fetchone()
            if res:
                return res

    @classmethod
    def computation(cls):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM review_compute')
            res = cursor.fetchall()
            if res:
                return res

    @classmethod
    def create_variance(cls, category, score, note, tag):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('INSERT INTO review_compute(category, score, note, tag) '
                           'VALUES(%s, %s, %s, %s) RETURNING id', (category, score, note, tag))
            res = cursor.fetchone()
            if res:
                column = category.replace(' ', '_')
                cursor.execute('ALTER TABLE target_score ADD COLUMN IF NOT EXISTS {} real'.format(column))
                return True

    @classmethod
    def update_variance(cls, category, score, note, tag, v_id, old_name):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE review_compute SET category=%s, score=%s, note=%s, tag=%s WHERE id=%s',
                           (category, score, note, tag, v_id))
            if cursor:
                return True

    @classmethod
    def remove_variance(cls, v_id, name):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('DELETE FROM review_compute WHERE id=%s', (v_id,))
            column = name.replace(' ', '_')
            cursor.execute("ALTER TABLE target_score DROP COLUMN {}".format(column))
            


    @classmethod
    def edit_variance(cls, v_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM review_compute WHERE id=%s', (v_id,))
            res = cursor.fetchone()
            return res

    @classmethod
    def performance_docx(cls, targetid, emp_id, tag):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM review_docx WHERE targetid=%s and emp_id=%s and tag=%s', 
                            (targetid, int(emp_id), tag))
            res = cursor.fetchall()
            return res

    @classmethod
    def getappraisalQC(cls, mode, emp_id, start, end):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM qcreport WHERE mode=%s and emp_id=%s and date_received between %s and %s", 
                            (mode, emp_id, start, end))
            result = cursor.fetchall()
            return result
            

    def report(self, dept, start, end):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("select employees.name, target_score.uniquecode, target_score.average, target_score.total, \
                            target.start_date, target.end_date \
                            from target_score \
                            left join employees \
                            on target_score.emp_id = employees.id\
                            left join target \
                            on target_score.uniquecode = target.target_uid \
                            where target.department = %s and target.start_date between %s and %s", (dept, start, end))
            res = cursor.fetchall()
            if res is not None:
                return res
            else:
                return None


    def targetrules(self):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM rules WHERE targetid=%s ORDER BY id DESC", (self.code,))
            rules = cursor.fetchall()
            if rules:
                return rules


    def resetApprasial(self, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("DELETE FROM review_response WHERE emp_id=%s and uniquecode=%s", (emp_id, self.code))
            cursor.execute("DELETE FROM review_response WHERE res_emp_id=%s and uniquecode=%s", (emp_id, self.code))
            cursor.execute("DELETE FROM target_score WHERE emp_id=%s and uniquecode=%s", (emp_id, self.code))
            cursor.execute("UPDATE targetemp SET status=%s, super_action=%s, emp_signed=%s, complete_review=%s, \
                            process=%s WHERE unique_code=%s and emp_id=%s", 
                            ('Pending', 'Pending', '', '', '', self.code, emp_id))

            if cursor:
                return True

    def check_signed(self, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT emp_signed FROM targetemp WHERE unique_code=%s and emp_id=%s", (self.code, emp_id))
            res = cursor.fetchone()
            if res:
                return res[0]



    @classmethod
    def get_emp_response(cls, emp_id, targetcode, ref=None):
        with CursorFromConnectionPool() as cursor:
            if ref:
                cursor.execute('select review_response.emp_id, review_response.uniquecode, rules.text, rules.score, '
                           'review_response.rule_score, review_response.rule_feedback, review_response.rule_type, '
                           'review_response.rule_id '
                           'from review_response '
                           'left join rules '
                           'on review_response.rule_id = rules.id '
                           'where review_response.emp_id = %s and rules.targetid = %s and res_emp_id=%s order by rule_id desc',
                           (emp_id, targetcode, ref))
            else:

                cursor.execute('select review_response.emp_id, review_response.uniquecode, rules.text, rules.score, '
                               'review_response.rule_score, review_response.rule_feedback, review_response.rule_type, '
                               'review_response.rule_id '
                               'from review_response '
                               'left join rules '
                               'on review_response.rule_id = rules.id '
                               'where review_response.emp_id = %s and rules.targetid = %s order by rule_id desc',
                               (emp_id, targetcode))
            res = cursor.fetchall()
            if res:
                return res



class Appraisal:
    """docstring for Appraisal"""
    def __init__(self, year):
        self.year = year

    def __repr__(self):
        pass


    def addpmt(self, name, score, phase):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("INSERT INTO appraisal_pmt(name, score, year, phase) VALUES(%s, %s, %s, %s)", 
                            (name, score, self.year, phase))
            if cursor:
                pmr_name = name.replace(' ', '_').lower()
                cursor.execute("ALTER TABLE targetreport ADD COLUMN IF NOT exists {} TEXT[][]".format(pmr_name))
                if cursor:
                    return True


    def getpmt(self):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM appraisal_pmt WHERE year=%s", (self.year, ))
            result = cursor.fetchall()
            if result:
                return result


    def updatepmt(self, name, score, pmtid, i_name, phase):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("UPDATE appraisal_pmt SET name=%s, score=%s, phase=%s WHERE id=%s", (name, score, phase, pmtid))
            if cursor:
                cursor.execute("ALTER TABLE targetreport RENAME COLUMN {} TO {}".format(i_name.replace(' ', '_').lower(), 
                                                                                        name.replace(' ', '_').lower()))
                if cursor:
                    # chceck if rule has been created
                    cursor.execute("UPDATE targetrule set pmr=%s WHERE pmr=%s", (name, i_name))
                
                    return True


    def delete_pmt(self, pmtid):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT name FROM appraisal_pmt WHERE id=%s", (pmtid, ))
            pmt_name = cursor.fetchone()

            cursor.execute("DELETE FROM appraisal_pmt WHERE id=%s and year=%s", (pmtid, self.year))
            if cursor:
                cursor.execute("ALTER TABLE targetreport DROP COLUMN {}".format(pmt_name[0].replace(' ', '_').lower()))
                
                if cursor:
                    return True
                    

    def set_rule(self, code, pmr, title, desc, score, phase):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT targetcode, pmr FROM targetrule WHERE targetcode=%s and pmr=%s LIMIT 1", (code, pmr))
            get_res = cursor.fetchone()
            if get_res:
                return 101
            else:
                cursor.execute("INSERT INTO targetrule(targetcode, pmr, title, description, score, phase) \
                                VALUES(%s, %s, %s, %s, %s, %s)", (code, pmr, title, desc, score, phase))
                if cursor:
                    return True


    def getTragetrule(self, codeid):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM targetrule WHERE targetcode=%s LIMIT 1", (codeid,))
            result = cursor.fetchone()
            return result


    @classmethod
    def getAssessment(cls, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM usertarget WHERE year=%s ORDER BY startdate DESC", (year,))
            values = cursor.fetchall()
            return values


    @classmethod
    def assessmentList(cls, code):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM usertargetemp WHERE targetcode=%s", (code, ))
            res = cursor.fetchall()
            return res


    @classmethod
    def upWkTarget(cls, remark, code, empid):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("UPDATE usertargetemp set hr_remark=%s WHERE targetcode=%s and emp_id=%s", (remark, code, empid))
            if cursor:
                return True


    @classmethod
    def itemDetails(cls, name, code):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM targetrule WHERE pmr=%s and targetcode=%s LIMIT 1", (name, code))
            res = cursor.fetchone()
            return res


    @classmethod
    def weekly_rpt(cls, sD, eD, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM targetreport WHERE startdate=%s and enddate=%s and year=%s", (sD, eD, year))
            res = cursor.fetchall()
            return res


    @classmethod
    def getempdetails(cls, empid):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT staff_id, name, department FROM employees WHERE id=%s", (empid, ))
            res = cursor.fetchone()
            return res

    @classmethod
    def t_scores(cls, column, code):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT {} from targetreport WHERE targetcode=%s".format(column), (code, ))
            res = cursor.fetchone()
            return res




class Review:
    def __init__(self, get_emp_id, uniquecode=None):
        self.emp_id = get_emp_id
        self.code = uniquecode

    def __repr__(self):
        pass

    def chkstatus(self):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM targetemp WHERE unique_code=%s and emp_id=%s',
                           (self.code, self.emp_id))
            res = cursor.fetchone()
            if res:
                return res

    @classmethod
    def target_response_list(self, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select employees.name, employees.department, target.name, target.target_uid, '
                            'target_score.average, targetemp.emp_signed, targetemp.emp_id, target_score.total, target.year, employees.staff_id ' 
                            'from employees '
                            'left join targetemp on employees.id = targetemp.emp_id '
                            'left join target_score on targetemp.emp_id = target_score.emp_id '
                            'left join target on target_score.uniquecode = target.target_uid '
                            'where employees.active = %s and target.name != %s and target_score.uniquecode = targetemp.unique_code and target.year=%s', 
                            (1, '', year)
                           )
            res = cursor.fetchall()
            if res:
                return res

   
    