import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import url_for, render_template
from packages.database import CursorFromConnectionPool
from packages.leave.token import generate_token


class Leave:
    def __init__(self, name, desc, duration):
        self.name = name
        self.desc = desc
        self.duration = duration

    def __repr__(self):
        pass

    def createleavetype(self):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('INSERT INTO leavetype(name, description, duration) VALUES(%s, %s, %s)',
                           (self.name, self.desc, self.duration))
            if cursor:
                return "New Leave category created"

    @classmethod
    def leavelist(cls, name=None):
        with CursorFromConnectionPool() as cursor:
          if name is None:
            cursor.execute('SELECT * FROM leavetype ORDER BY name ASC')
            res = cursor.fetchall()
          else:
            cursor.execute('SELECT * FROM leavetype WHERE name=%s', (name,))
            res = cursor.fetchone()
          
          return res


    @classmethod
    def fetch_leave_type(cls, getId):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM leavetype WHERE id=%s', (getId,))
            res = cursor.fetchone()
            if res:
                return res

    @classmethod
    def update(cls, leave_id, name, description, duration):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE leavetype SET name=%s, description=%s, duration=%s WHERE id=%s',
                           (name, description, duration, leave_id))
            if cursor:
                return 'Update Successfully'

    @classmethod
    def delete_leave_type(cls, getId):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('DELETE FROM leavetype WHERE id=%s', (getId,))
            if cursor:
              return True

    @classmethod
    def get_emps_by_dept(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM employees WHERE id !=%s and active=%s order by name asc', (emp_id, 1))
            res = cursor.fetchall()
            return res

    @classmethod
    def leave_supervisor(cls):
        with CursorFromConnectionPool() as cursor:
          cursor.execute('SELECT id, name, email FROM employees WHERE active=%s and role=%s or jobtitle=%s', 
                          (1, 'supervisor', 'Supervisor'))
          res = cursor.fetchall()
          return res
          

    @classmethod
    def notice(cls, leaveid, emp_leave_id, receiving_emp_id, leave_mode, msg_date):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('INSERT INTO leave_message(leave_id, emp_leave_id, receiving_emp_id, leave_mode, msg_date)'
                           'VALUES(%s, %s, %s, %s, %s) RETURNING id',
                           (leaveid, emp_leave_id, receiving_emp_id, leave_mode, msg_date))
            res = cursor.fetchone()
            return res

    
    @classmethod
    def fetch_emp_leave(cls, leaveid):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT employees.name, leaverequest.leavetype, leaverequest.duration, '
                           'leaverequest.startdate, leaverequest.enddate,  '
                           'leaverequest.address, leaverequest.contact, leavenotify.relief1_name, '
                           'leavenotify.super_name, leaverequest.requestdate, leaverequest.emp_id, '
                           'leaverequest.department, leaverequest.status, leaverequest.id, '
                           'leavenotify.email, leaverequest.resumeday, leavenotify.super_action, '
                           'leavenotify.relief1_action, leavenotify.relief2_name, leavenotify.relief2_action, '
                           'leavenotify.relief3_name, leavenotify.relief3_action, leaverequest.allowance, leaverequest.allowancereceive, '
                           'leaverequest.handover '
                           'FROM leaverequest '
                           'LEFT JOIN employees '
                           'ON leaverequest.emp_id = employees.id '
                           'LEFT JOIN leavenotify '
                           'ON leaverequest.id = leavenotify.leave_id '
                           'WHERE leaverequest.id = %s ORDER BY leaverequest.id DESC', (leaveid,))
            res = cursor.fetchone()
            if res is not None:
                return res

    @classmethod
    def fetch_all_leave(cls, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT leaverequest.emp_id, employees.name, leaverequest.department, '
                           'leaverequest.leavetype, leaverequest.duration, leaverequest.id '
                           'FROM leaverequest '
                           'LEFT JOIN employees '
                           'ON leaverequest.emp_id = employees.id '
                           'WHERE leaverequest.status=%s and leaverequest.year=%s ORDER BY ', ('Pending', year))
            res = cursor.fetchall()
            if res is not None:
                return res

    @classmethod
    def get_leave_details(cls, leave_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select leaverequest.id, leaverequest.leavetype, leaverequest.startdate, '
                           'leaverequest.enddate, '
                           'leaverequest.address, leaverequest.duration, '
                           'leavenotify.super_name, leavenotify.relief1_name, '
                           'leavenotify.relief1_action, leavenotify.super_action, leavenotify.hr_action, '
                           'leavenotify.final_action, leavenotify.status, leavenotify.email, '
                           'employees.name, leaverequest.department, leaverequest.requestdate, '
                           'leavenotify.super_email, leaverequest.resumeday, '
                           'leaverequest.handover, leavecomment.hr_action, leavenotify.relief2_name, '
                           'leavenotify.relief2_action, leavenotify.relief3_name, '
                           'leavenotify.relief3_action, leaverequest.contact, leaverequest.allowance '
                           'from leaverequest '
                           'left join leavenotify '
                           'on leaverequest.id = leavenotify.leave_id '
                           'left join employees '
                           'on leaverequest.emp_id = employees.id '
                           'left join leavecomment '
                           'on leaverequest.id = leavecomment.leaveid '
                           'where leaverequest.id = %s', (leave_id,))
            res = cursor.fetchone()
            return res

    @classmethod 
    def active(cls, status, rdate):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT leaverequest.id, leaverequest.emp_id, leaverequest.leavetype, '
                           'leaverequest.startdate, leaverequest.enddate, leaverequest.duration, '
                           'leaverequest.department, leaverequest.resumeday, employees.name '
                           'FROM leaverequest '
                           'LEFT JOIN employees '
                           'ON leaverequest.emp_id = employees.id '
                           'WHERE leaverequest.status=%s and leaverequest.resumeday > %s', (status, rdate))
            res = cursor.fetchall()
            return res

    @classmethod
    def calendar_leave(cls):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT leaverequest.id, leaverequest.emp_id, leaverequest.leavetype, '
                           'leaverequest.startdate, leaverequest.enddate, leaverequest.duration, '
                           'leaverequest.department, leaverequest.resumeday, employees.name, '
                           'leaverequest.status '
                           'FROM leaverequest '
                           'LEFT JOIN employees '
                           'ON leaverequest.emp_id = employees.id '
                           'WHERE leaverequest.status != %s and leaverequest.status != %s', ('Deleted', 'Declined')
                           )
            res = cursor.fetchall()
            if res is not None:
                return res

    @classmethod
    def calendar_leave_dept(cls, department):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT leaverequest.id, leaverequest.emp_id, leaverequest.leavetype, '
                           'leaverequest.startdate, leaverequest.enddate, leaverequest.duration, '
                           'leaverequest.department, leaverequest.resumeday, employees.name, '
                           'leaverequest.status '
                           'FROM leaverequest '
                           'LEFT JOIN employees '
                           'ON leaverequest.emp_id = employees.id '
                           'WHERE leaverequest.department=%s and leaverequest.status != %s', (department, 'Deleted'))
            res = cursor.fetchall()
            if res is not None:
                return res

    @classmethod
    def leavestatus(cls):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select employees.name, leaverequest.department, leaverequest.leavetype, '
                           'leaverequest.status, leavecomment.hr_action, leaverequest.id, leaverequest.requestdate '
                           'from leaverequest '
                           'left join employees '
                           'on leaverequest.emp_id = employees.id '
                           'left join leavenotify '
                           'on leaverequest.id = leavenotify.leave_id '
                           'left join leavecomment '
                           'on leaverequest.id = leavecomment.leaveid '
                           'where leaverequest.status != %s', ('Deleted',))
            res = cursor.fetchall()
            return res

    @classmethod
    def active_leave(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT leave FROM permission WHERE emp_id=%s', (emp_id,))
            res = cursor.fetchone()
            return res[0]

    @classmethod
    def leavedet(cls, emp_id):
      with CursorFromConnectionPool() as cursor:
        cursor.execute("SELECT * FROM leavedays WHERE emp_id=%s LIMIT 1", (emp_id,))
        res = cursor.fetchone()
        if res is not None:
          return res

    @classmethod
    def createleave(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM leavedays WHERE emp_id=%s", (emp_id,))
            active = cursor.fetchone()
            if active is None:
                cursor.execute('INSERT INTO leavedays(emp_id, total_days, used_days, remain_days, status) '
                               'VALUES(%s, %s, %s, %s, %s) RETURNING id', (emp_id, 21, 0, 21, 1))
                res = cursor.fetchone()
                return res


    @classmethod
    def updateleave(cls, emp_id, columnname, column_value):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE leavedays SET {}=%s WHERE emp_id=%s'.format(columnname), (column_value, emp_id))
            if columnname == 'status':
              cursor.execute("UPDATE permission SET leave=%s WHERE emp_id=%s", (column_value, emp_id))
            return True
                

    @classmethod
    def get_request_id(cls, tablename, columnn, ref_column, leaveid):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT {} FROM {} WHERE {}=%s'.format(columnn, tablename, ref_column), (leaveid,))
            res = cursor.fetchone()
            return res

    @classmethod
    def leave_deduct(cls, emp_id, get_leave_days, leave_duration):
        deduction = get_leave_days - leave_duration
        Leave.updateleave(emp_id, 'remain_days', deduction)
        Leave.updateleave(emp_id, 'used_days', leave_duration)


    @classmethod
    def check_action(cls, leaveid):
      with CursorFromConnectionPool() as cursor:
        cursor.execute("SELECT hr_action FROM leavenotify WHERE leave_id=%s", (leaveid,))
        res = cursor.fetchone()
        if res[0] is not None:
          return res[0]
        else:
          return False

    @classmethod
    def pendingList(cls, status):
      with CursorFromConnectionPool() as cursor:
        cursor.execute('SELECT employees.staff_id, employees.name, employees.department, leaverequest.leavetype, \
                        leaverequest.id \
                        FROM employees\
                        LEFT JOIN leaverequest\
                        ON employees.id = leaverequest.emp_id\
                        LEFT JOIN leavenotify\
                        ON leaverequest.id = leavenotify.leave_id\
                        WHERE leavenotify.final_action = %s\
                        ', (status,))
        result = cursor.fetchall()
        if result:
          return result


    @classmethod
    def finalPendingUser(cls, leaveid):
      with CursorFromConnectionPool() as cursor:
        cursor.execute('SELECT employees.name, employees.department, employees.post, leaverequest.id, \
                        leaverequest.emp_id, leaverequest.leavetype, leaverequest.startdate, \
                        leaverequest.enddate, leaverequest.duration, leaverequest.resumeday,\
                        leaverequest.handover, leaverequest.requestdate, leaverequest.allowance,\
                        leavenotify.email\
                        FROM leaverequest\
                        LEFT JOIN leavenotify\
                        ON leaverequest.id = leavenotify.leave_id\
                        LEFT JOIN employees\
                        ON employees.id = leaverequest.emp_id\
                        WHERE leaverequest.id=%s\
                        ', (leaveid,))
        result = cursor.fetchone()
        if result:
          return result

    @classmethod
    def leaveallowance(cls, year):
      with CursorFromConnectionPool() as cursor:
        cursor.execute("SELECT employees.name, employees.department, leaverequest.leavetype, leaverequest.status, \
                        leaverequest.allowance, leaverequest.allowancereceive, leaverequest.id, leaverequest.year\
                        FROM leaverequest \
                        LEFT JOIN employees \
                        ON leaverequest.emp_id=employees.id \
                        WHERE leaverequest.status != %s AND leaverequest.status != %s AND leaverequest.year = %s \
                        AND leaverequest.allowance=%s ", ('Deleted', 'Declined', year, 'Yes'))
        res = cursor.fetchall()
        if res:
          return res

    @classmethod
    def actionAllowance(cls, value, leaveid, tablename):
      with CursorFromConnectionPool() as cursor:
        cursor.execute('UPDATE leaverequest set {}=%s WHERE id=%s'.format(tablename), (value, leaveid))
        if cursor:
          return True

    @classmethod
    def checkOtherLeave(cls, name, empid):
      with CursorFromConnectionPool() as cursor:
        cursor.execute("SELECT * FROM otherleave WHERE leave_name=%s and emp_id=%s", (name, empid))
        res = cursor.fetchone()
        if res:
          return res

    @classmethod
    def OtherLeave(empid, name, totalDays, usedDays, remainDays):
      with CursorFromConnectionPool() as cursor:
        status = Leave.checkOtherLeave(name, empid)
        if status:
          cursor.execute("UPDATE otherleave SET used_days=%s, remain_days=%s WHERE emp_id=%s and leave_name=%s", 
                          (usedDays, remainDays, empid, name))
        else:
          cursor.execute("INSERT INTO otherleave(emp_id, leave_name, total_days, used_days, remain_days) \
                          VALUES(empid, name, totalDays, usedDays, remainDays)")

    @classmethod
    def fetchOtherLeaveInfo(cls, empid, name):
      with CursorFromConnectionPool() as cursor:
        cursor.execute("SELECT * FROM otherleave WHERE emp_id=%s and leave_name=%s", (empid, name))
        result = cursor.fetchone()
        if result:
          return result
        else:
          cursor.execute("SELECT * FROM leavetype WHERE name=%s", (name,))
          result = cursor.fetchone()
          if result:
            return result
          else:
            return None


    @classmethod
    def draftedLeave(cls, emp_id, status):
      with CursorFromConnectionPool() as cursor:
        cursor.execute("SELECT * FROM leaverequest WHERE emp_id=%s and status=%s", (emp_id, status))
        res = cursor.fetchall()
        if res:
          return res


    @classmethod
    def getLeaverecord(cls, name, emp_id, mode):
        with CursorFromConnectionPool() as cursor:
            if mode == 'annual':
                cursor.execute("SELECT * FROM leavedays WHERE emp_id=%s LIMIT 1", (emp_id, ))
            else:
                cursor.execute("SELECT * FROM otherleave WHERE leave_name=%s and emp_id=%s", (name, emp_id))

            result = cursor.fetchone()
            if result:
                return result

    @classmethod
    def modifyleave(cls, emp_id, leavetype, days, reason, submit_date, leave_year):
        status = None

        if leavetype.lower() == 'annual leave':
            dets = Leave.leavedet(emp_id=emp_id)
            outstandingDays = dets[4]
            UsedDays = dets[3]

            rdays = outstandingDays - int(days)
            udays = UsedDays + int(days)
            with CursorFromConnectionPool() as cursor:
                cursor.execute("UPDATE leavedays set remain_days=%s, used_days=%s WHERE emp_id=%s", 
                    (rdays, udays, emp_id))
                if cursor:
                    status = 1
        else:
            dets = Leave.checkOtherLeave(name=leavetype, empid=emp_id)
            if dets:
                outstandingDays = dets[5]
                UsedDays = dets[4]

                rdays = outstandingDays - int(days)
                udays = UsedDays + int(days)

                with CursorFromConnectionPool() as cursor:
                    cursor.execute("UPDATE otherleave SET remain_days=%s, used_days=%s WHERE emp_id=%s and name=%s", 
                                    (rdays, udays, emp_id, leavetype))
                    if cursor:
                        status = 1
            else:
                dets = Leave.leavelist(name=leavetype)
                assign_days = dets[3]
                
                rdays = assign_days - int(days)
                udays = int(days)

                with CursorFromConnectionPool() as cursor:
                    cursor.execute("INSERT into otherleave(emp_id, leave_name, total_days, used_days, remain_days)\
                                    VALUES(%s, %s, %s, %s, %s)", (emp_id, leavetype, assign_days, udays, rdays))
                    if cursor:
                        status = 1


        if status == 1:
            with CursorFromConnectionPool() as cursor:
                cursor.execute("INSERT INTO leavededuction(emp_id, leavetype, days, reason, sdate, year)\
                                VALUES(%s, %s, %s, %s, %s, %s)", (emp_id, leavetype, days, reason, submit_date, leave_year))
                if cursor:
                    return True
        else:
            return False

    @classmethod
    def leavestafflist(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM leaverequest WHERE emp_id=%s and status !=%s and status !=%s", 
                            (emp_id, 'Deleted', 'Declined'))
            lst = cursor.fetchall()
            if lst:
                return lst

    @classmethod
    def leaveDeduction(cls):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM leavededuction")
            details = cursor.fetchall()
            if details:
                return details



def fetch_emp():
    with CursorFromConnectionPool() as cursor:
        cursor.execute('SELECT * FROM employees WHERE post=%s or post=%s', ("HR Manager", "Managing Director"))
        res = cursor.fetchall()
        if res:
            return res


def leave_status(leave_id):
  with CursorFromConnectionPool() as cursor:
    cursor.execute("UPDATE leaverequest SET status=%s, WHERE id=%s", ('Completed', leave_id))
    



class empLeaveOpz:
  def __init__(self, emp_id):
    self.id = emp_id

  def __repr__(self):
    pass

  def getrequestlist(self, year):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("SELECT employees.name, leaverequest.id, leavenotify.email, leaverequest.department, leaverequest.leavetype, \
                      leaverequest.handover, leavenotify.auth, leaverequest.status, leaverequest.year \
                      from leaverequest left join leavenotify \
                      on leaverequest.id =leavenotify.leave_id \
                      left join employees \
                      on leaverequest.emp_id = employees.id \
                      where leaverequest.status != %s and leavenotify.relief1_id=%s or \
                      leavenotify.relief2_id=%s or leavenotify.relief3_id=%s or leavenotify.super_id=%s and leaverequest.year=%s", 
                      ('Deleted', self.id, self.id, self.id, self.id, year ))
      response = cursor.fetchall()
      if response:
        return response


  @classmethod
  def leaveNotifyDet(cls, leave_id):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("SELECT * FROM leavenotify WHERE leave_id=%s", (leave_id, ))
      res = cursor.fetchone()
      if res:
        return res


  @classmethod
  def leave_information(cls, leave_id):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("SELECT leaverequest.id, employees.name, employees.email, employees.department, \
                      leaverequest.leavetype, leaverequest.handover, leaverequest.startdate, leaverequest.enddate, \
                      leaverequest.resumeday, leaverequest.leavetype, leaverequest.contact, leaverequest.duration, \
                      leavenotify.relief1_id, leavenotify.relief2_id, leavenotify.relief3_id, leavenotify.super_id, \
                      leavenotify.auth, leavenotify.relief1_action, leavenotify.relief2_action, leavenotify.relief3_action,\
                      leavenotify.super_action\
                      FROM leaverequest\
                      LEFT JOIN employees\
                      ON leaverequest.emp_id = employees.id\
                      LEFT JOIN leavenotify\
                      ON leaverequest.id = leavenotify.leave_id\
                      WHERE leaverequest.id = %s", (leave_id,))

      value = cursor.fetchone()
      if value:
        return value

  @classmethod
  def declineReason(cls, reason, leaveid, columnname):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("UPDATE leavecomment SET {}=%s WHERE leaveid=%s", (columnname, reason, leaveid))
      if cursor:
        return True

  @classmethod
  def comment(cls, leaveid, columnname):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("SELECT {} FROM leavecomment WHERE leaveid=%s".format(columnname), (leaveid,))
      result = cursor.fetchone()
      if result:
        return result

        
