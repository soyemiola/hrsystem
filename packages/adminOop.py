from packages.database import Database, CursorFromConnectionPool
from flask import session, g, redirect, render_template, url_for, current_app
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date, timedelta
import random
import datetime
import os

        

class Operations:
    def __init__(self, email, password=None):
        self.email = email
        self.password = password

    def __repr__(self):
        return '{}'.format(self.email)

    def checkuser(self):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM admin WHERE email=%s', (self.email,))
            get_record = cursor.fetchone()
            if get_record is not None:
                return get_record


    def existing_user(self):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM admin WHERE email=%s', (self.email,))
            get_record = cursor.fetchone()
            if get_record is not None:
                return get_record


    def adduser(self, firstname, lastname, created, role):
        adminId = random.randint(1000, 5000)

        with CursorFromConnectionPool() as cursor:
            cursor.execute('INSERT INTO admin(id, firstname, lastname, email, password, created, role) VALUES(%s, %s, %s, %s, %s, %s, %s) \
                            RETURNING id', (adminId, firstname, lastname, self.email, self.password, created, role))
            get_id = cursor.fetchone()
            return get_id


    @classmethod
    def fetch_record(cls, email, user_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM admin WHERE email=%s and id=%s', (email, user_id))
            res = cursor.fetchone()
            return res

    @classmethod
    def all_employees(cls):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT count(*) FROM employees')
            res = cursor.fetchone()
            return res

    @classmethod
    def active_employees(cls):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT count(*) FROM employees WHERE active=%s', (1,))
            res = cursor.fetchone()
            return res

    @classmethod
    def leave_request(cls):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT count(*) FROM leaverequest WHERE status=%s', ('Pending',))
            res = cursor.fetchone()
            return res

    @classmethod
    def onleave(cls, date):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT count(*) FROM leaverequest WHERE status=%s and resumeday > %s', ('Approved', date))
            res = cursor.fetchone()
            return res

    @classmethod
    def userlogin(cls, email, password):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM employees WHERE email=%s and password=%s LIMIT 1', (email, password))
            res = cursor.fetchone()
            if res:
                return res

    @classmethod
    def pre_reg(cls, name, state, address, city, mobile, bankname, account, taxnumber, pensioncomp, pensionnum):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("INSERT INTO pre_reg(name, state, address, city, mobile, bankname, account, taxnumber, pensioncomp, pensionnum)\
                            VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                            (name, state, address, city, mobile, bankname, account, taxnumber, pensioncomp, pensionnum))
            if cursor:
                return True
            else:
                return False

    @classmethod
    def update_pass(cls, new_password, getid):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("UPDATE admin SET password=%s WHERE id=%s", (new_password, getid))
            if cursor:
              return True

    @classmethod
    def performance_score(cls):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("select employees.name, target.department, target.name, target.target_uid, "
                           "target_score.average, target_score.emp_id, target_score.total "
                           "from target_score "
                           "left join target "
                           "on target_score.uniquecode = target.target_uid "
                           "left join employees "
                           "on target_score.emp_id = employees.id LIMIT 10")
            res = cursor.fetchall()
            if res is not None:
                return res

    @classmethod
    def adminusers(cls):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM admin")
            res = cursor.fetchall()
            return res

    @classmethod
    def updateadminuser(cls, columnname, columnvalue, adminid):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("UPDATE admin SET {}=%s WHERE id=%s ".format(columnname), (columnvalue, adminid))
            if cursor:
                return True


    @classmethod
    def users(cls):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT employees.id, employees.name, employees.department, employees.dob, employees.image, \
                            permission.active \
                            FROM employees \
                            LEFT JOIN permission \
                            ON employees.id = permission.emp_id \
                            WHERE permission.active = %s', (1,))
            result = cursor.fetchall()
            if result:
                return result

    @classmethod
    def getlist(cls, department, toplevel=None):
        with CursorFromConnectionPool() as cursor:
            if toplevel:
                cursor.execute("SELECT email FROM employees WHERE post=%s or post=%s", ('General Manager', 'Managing Director'))
            else:
                cursor.execute('SELECT email FROM employees WHERE department=%s and active=%s', (department, 1))
            
            res = cursor.fetchall()
            if res is not None:
              return res
            else:
              return None

    
class Report:
    """docstring for Report"""
    def __init__(self, info, category=None, subject=None, sendcopy=None):
        self.name = info[1]
        self.email = info[2]
        self.postdate = info[0]
        self.shift = info[3]
        self.category = category
        self.subject = subject
        self.info = info
        self.sendcopy = sendcopy        


    def process(self, html=None):
        sendmail = self.__sendmail(subject=self.subject, info=self.info, sendcopy=self.sendcopy, htmlpage=html)
        if sendmail == True:
            return True
        else:
            return False

    
    def savereport(self, pnr, details, clientname, status, future=None, ticket=None, draftID=None):
        with CursorFromConnectionPool() as cursor:
           
            if draftID:
                cursor.execute("UPDATE report SET name=%s, email=%s, postdate=%s, shift=%s, category=%s, pnr=%s, details=%s, \
                                ticket=%s, clientname=%s, future_date=%s, status=%s WHERE id=%s", 
                                (self.name, self.email, self.postdate, self.shift, self.category, pnr, details, ticket, 
                                    clientname, future, status, draftID))
                if cursor:
                    return True
            else:
                cursor.execute("INSERT INTO report(name, email, postdate, shift, category, pnr, details, ticket, clientname, future_date, status) \
                                VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id", 
                                (self.name, self.email, self.postdate, self.shift, self.category, pnr, details, ticket, 
                                    clientname, future, status))
                record_id = cursor.fetchone()
            
                return record_id[0]


    @classmethod
    def drafthandOver(cls, email, shift, postdate):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM report WHERE email=%s and shift=%s and postdate=%s", (email, shift, postdate))
            draft_msg = cursor.fetchall()
            return draft_msg


    @classmethod
    def saveqareport(cls, name, email, postdate, shift, resumetime, category, details, rsc_tab, status, draftID=None):
        with CursorFromConnectionPool() as cursor:
            if draftID:
                cursor.execute("UPDATE qareport SET name=%s, email=%s, postdate=%s, shift=%s, resumetime=%s, category=%s, \
                                details=%s, rsc_tab=%s, status=%s WHERE id=%s",
                                (name, email, postdate, shift, resumetime, category, details, rsc_tab, status, draftID))
                if cursor:
                    return True
            else:
                cursor.execute("INSERT INTO qareport(name, email, postdate, shift, resumetime, category, details, rsc_tab, status) \
                                VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id", (name, email, postdate, shift, resumetime, category, 
                                                                            details, rsc_tab, status))
                record_id = cursor.fetchone()
            
                return record_id[0]

    @classmethod
    def draftQA(cls, email, shift, postdate):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM qareport WHERE email=%s and shift=%s and postdate=%s", (email, shift, postdate))
            draft_msg = cursor.fetchall()
            return draft_msg


    def saveccreport(self, cust_name, cust_num, cust_reacable, cust_feedback):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("INSERT INTO ccreport(name, email, postdate, shift, category, cust_name, cust_num, cust_reacable, \
                            cust_feedback) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                            (self.name, self.email, self.postdate, self.shift, self.category, cust_name, cust_num, \
                                cust_reacable, cust_feedback))


    def __sendmail(self, subject, info, sendcopy=None, htmlpage=None):
        future_date = info[13]
        # get result from db where future day applies
        next_date = str(date.today() + timedelta(1))

        future_info = self.__future_fields()
        record = self.__future_record(next_date=next_date, future_det=future_info)
        
        if record is not None:
            next_request = record
        else:
            next_request = None

        to = ['olanrewaju.soyemi@btmlimited.net']
        
        if htmlpage is None:
            _24hour = ''
        else:
            _24hour = ''

        if sendcopy is not None:
            copymail = sendcopy
        else:
            copymail = ''

        cc = ['yusuf.busari@btmlimited.net']

        sendport = current_app.config['MAIL_PORT']
        smtp_server = current_app.config['SEND_MAIL_SERVER']
        sender_email = current_app.config['EMAIL_ADDRESS']
        password = current_app.config['SEND_MAIL_PASSWORD']
        #receiver_email = to

        
        message = MIMEMultipart("alternative")
        message["Subject"] = subject
        message["From"] = current_app.config['EMAIL_ADDRESS']
        message["To"] = ','.join(to)
        message["Cc"] =','.join(cc)

        toAddress = to + cc

        text = """\
        
                BUSINESS TRAVEL MANAGEMENT
                HR Report Notification
                """
        
        if htmlpage == 'QA':
            html = render_template('qareport.html', info=info)
        elif htmlpage == 'Call center':
            html = render_template('callcenterreport.html', info=info)
        else:
            html = render_template('report.html', info=info, next_request=next_request)
            
        
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        message.attach(part1)
        message.attach(part2)

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(smtp_server, sendport, context=context) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, toAddress, message.as_string())
                return True
        except:
            return False        



    @classmethod
    def operation(cls, date, category):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM report WHERE postdate = %s and category = %s", (date, category))
            res = cursor.fetchall()
            if res is not None:
                return res
            else:
                return None

    
    def __future_fields(self):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM report WHERE future_date is not null")
            res = cursor.fetchall()
            if res is not None:
                return res


    def __future_record(self, next_date, future_det):
        request = []
        for i in future_det:
            for ft in i[10]:
                position = i[10].index(ft)
                if ft == next_date:
                    clientname = i[9][position]
                    pnr = i[6][position]
                    details = i[7][position]

                    details_info = clientname, pnr, details

                    request.append(details_info)

        return request

    @classmethod
    def it_report(cls, date):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM weeklyreport WHERE startdate=%s and status=%s",(date, 'Complete'))
            res = cursor.fetchall()
            if res:
                return res


    @classmethod
    def commsReport(cls, info):
        sendreport = Report.__sendCommsEmail(info=info)

        if sendreport == True:
            with CursorFromConnectionPool() as cursor:
                cursor.execute("INSERT INTO commsreport(name, email, shift, sdate, actionpoint, description, duedate, comment)\
                                VALUES(%s, %s, %s, %s, %s, %s, %s, %s)", 
                                (info[0], info[1], info[2], info[3], info[4], info[5], info[6], info[7]))
                if cursor:
                    return True
        else:
            return False


    @classmethod
    def __sendCommsEmail(cls, info):
        sendport = current_app.config['MAIL_PORT']
        smtp_server = current_app.config['SEND_MAIL_SERVER']
        sender_email = current_app.config['EMAIL_ADDRESS']
        password = current_app.config['SEND_MAIL_PASSWORD']

        if info[8]:
            sendcopy = info[8]
        else:
            sendcopy = ''

        to = ['olanrewaju.soyemi@btmlimited.net']
        cc = ['yusuf.busari@btmlimited.net', sendcopy]
        
        message = MIMEMultipart("alternative")
        message["Subject"] = 'COMMS Report.'
        message["From"] = current_app.config['EMAIL_ADDRESS']
        message["To"] = ','.join(to)
        message["Cc"] =','.join(cc)        

        toAddress = to + cc

        text = """\
        
                BUSINESS TRAVEL MANAGEMENT
                Comms Department Report
                """

        html = render_template('commsemail.html', info=info)
        
        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        message.attach(part1)
        message.attach(part2)

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(smtp_server, sendport, context=context) as server:
                server.login(sender_email, password)
                server.sendmail(sender_email, toAddress, message.as_string())
                return True
        except:
            return False


    @classmethod
    def commsreport(cls, date):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM commsreport WHERE sdate=%s LIMIT 1", (date,))
            result = cursor.fetchone()
            if result:
                return result
          

class Birthday:
    """docstring for Birthday"""
    def __init__(self, stafflist):
        self.month = datetime.datetime.today().strftime('%m')
        self.list = stafflist

    def __repr__(self):
        pass

    def celebrants(self):
        celebrants = self.in_month()
        return celebrants


    def in_month(self):
        emp_in_month = []

        if self.list is not None:
            for x in range(len(self.list)):
                emp_month = datetime.datetime.strptime(self.list[x][3], '%Y-%m-%d').strftime('%m')
                if emp_month == self.month:
                    emp_in_month.append(self.list[x])

            if len(emp_in_month) != 0:
                return emp_in_month
            else:
                return None
        else:
            return None
