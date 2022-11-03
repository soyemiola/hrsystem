from packages.database import CursorFromConnectionPool
from packages.payroll.taxable import Taxable, emptaxband, convert_to_float
from packages.employees.newuser import check_existing_user, new_user, create_user_account_details, \
        create_gcpt, pension_profile, user_permit
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import render_template, current_app


class Employee:
    def __init__(self, name, address, city, mobile, department, post, email, branch, employment_date, emp_class,
                 basic, house_a, transport_a, other_a, total_a, bank_name, bank_account, tax_number, pen_name,
                 pen_num, state, dob, jobtitle, title, gender, nokin, nokinnumber, nokinemail, nokinrel
                 ):
        self.name = name
        self.address = address
        self.city = city
        self.mobile = mobile
        self.department = department
        self.post = post
        self.email = email
        self.branch = branch
        self.employment_date = employment_date
        self.emp_class = emp_class
        self.basic = basic
        self.house_a = house_a
        self.transport_a = transport_a
        self.other_a = other_a
        self.total_a = total_a
        self.bank_name = bank_name
        self.bank_account = bank_account
        self.tax_number = tax_number
        self.pen_name = pen_name
        self.pen_num = pen_num
        self.state = state
        self.dob = dob
        self.jobtitle = jobtitle
        self.title = title
        self.gender = gender
        self.nokin = nokin
        self.nokinnumber = nokinnumber
        self.nokinemail = nokinemail
        self.nokinrel = nokinrel


    def __repr__(self):
        return "<Employee details: {}, {}, {}>".format(self.name, self.department, self.post)

    @classmethod
    def create_new_user(cls, name, address, city, mobile, department, post, email, branch, active_month, emp_class,
                        basic, house_a, transport_a, other_a, total_a, bank_name, bank_account, tax_number, pen_name,
                        pen_num, state, password, dob, staff_id, jobtitle, title, gender, nokin, nokinnumber, nokinemail, 
                        nokinrel):
        with CursorFromConnectionPool() as cursor:
            if check_existing_user(email) is None:
                get_user_id = new_user(name, address, city, mobile, department, post, email, branch, active_month, emp_class, 
                                        state, password, dob, staff_id, jobtitle, title, gender, nokin, nokinnumber, nokinemail, 
                                        nokinrel)
                if get_user_id is not None:
                    set_user_id = get_user_id[0]

                    get_acct_id = create_user_account_details(set_user_id, basic, house_a, transport_a, other_a,
                                                              total_a, bank_name, bank_account, name, tax_number)
                    try:
                        if get_acct_id is not None:
                            emp_acct_details = Taxable.get_taxable(basic, total_a)
                            gross = emp_acct_details['Gross']
                            cra = emp_acct_details['CRA']
                            pension = emp_acct_details['Pension']
                            totalrelief = emp_acct_details['Total Relief']

                            gcpt = create_gcpt(gross, cra, pension, totalrelief, get_acct_id)
                            if gcpt == 1:
                                user_pension = pension_profile(get_user_id, pen_name, pen_num)
                                if user_pension == 1:
                                    if user_permit(get_user_id) == 1:
                                        return get_user_id
                                    else:
                                        return 0
                                else:
                                    return 0
                            else:
                                return 0                       
                    except:
                        Employee.__remove_emp_record(empid=set_user_id)
                        return 210 # error creating user details
            else:
                return 101 # User Already Exist


    @classmethod
    def __remove_emp_record(cls, empid):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("DELETE FROM employees WHERE id=%s", (empid, ))


    def update_emp(self, update_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE employees SET name = %s, address = %s, city = %s, mobile = %s, department = %s, '
                           'post = %s, email = %s, branch = %s, emp_class = %s, state=%s, active_date=%s, dob=%s, jobtitle=%s, '
                           'gender=%s, title=%s WHERE id = %s', (self.name, self.address, self.city, self.mobile, 
                                                                    self.department, self.post, self.email, self.branch, 
                                                                    self.emp_class, self.state, self.employment_date, 
                                                                    self.dob, self.jobtitle, self.gender, self.title,
                                                                    update_id))
            get_id = update_id
            if get_id is not None:
                # get Taxable
                emp_acct_details = Taxable.get_taxable(self.basic, self.total_a)
                gross = emp_acct_details['Gross']
                cra = emp_acct_details['CRA']
                pension = emp_acct_details['Pension']
                totalrelief = emp_acct_details['Total Relief']

                emp_taxable = gross - totalrelief
                #get Taxbands
                emp_taxband = emptaxband(emp_id=get_id, gross=gross, relief=totalrelief)
                emp_band1 = convert_to_float(emp_taxband['Firstband'])
                emp_band2 = convert_to_float(emp_taxband['Secondband'])
                emp_band3 = convert_to_float(emp_taxband['Thirdband'])
                emp_band4 = convert_to_float(emp_taxband['Fourthband'])
                emp_band5 = convert_to_float(emp_taxband['Fifthband'])
                emp_band6 = convert_to_float(emp_taxband['Sixthband'])
                emp_total_band = emp_taxband['Total_tax']
                emp_min_tax = emp_taxband['Minimum_tax']
                emp_hm_tax = emp_taxband['HM_tax']
                emp_eff_tax = emp_taxband['Effective_tax']

                # update tax record
                emp_tax_record = Taxable.taxrecord(get_id, emp_taxable, emp_min_tax, emp_hm_tax, emp_eff_tax, emp_band1, emp_band2, emp_band3, 
                                                    emp_band4, emp_band5, emp_band6, emp_total_band)

                
                if emp_tax_record:
                    update_nextofkin = Employee.updateNOK(empid=get_id, nokin=self.nokin, noknumber=self.nokinnumber, nokemail=self.nokinemail, 
                                                            nokrel=self.nokinrel)
                    update_pen = Employee.update_pension(emp_id=get_id, pen_name=self.pen_name, pen_num=self.pen_num)
                    update_user_acct = self.update_acct_info(gross=gross, cra=cra, pension=pension, totalrelief=totalrelief, 
                                                                tax_number=self.tax_number, emp_id=get_id)

                    if update_user_acct is True:
                        return True

    

    def update_acct_info(self, gross, cra, pension, totalrelief, tax_number, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE account_info SET basic =%s, house_a=%s, transport_a=%s, other_a=%s, total_a=%s, bank_name=%s, bank_acct=%s, \
                            gross= %s, cra = %s, pension = %s, total_relief = %s, tax_number=%s WHERE emp_id = %s', 
                            (self.basic, self.house_a, self.transport_a, self.other_a, self.total_a, self.bank_name, 
                                self.bank_account, gross, cra, pension, totalrelief, tax_number, emp_id))
            if cursor:
                return True
            else:
                return False


    
    @classmethod
    def updatePass(cls, empId, newPass):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("UPDATE employees SET password=%s WHERE id=%s", (newPass, empId))
            if cursor:
                return True



    @classmethod
    def updateNOK(cls, empid, nokin, noknumber, nokemail, nokrel):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM nextofkin WHERE emp_id=%s LIMIT 1", (empid,))
            is_found = cursor.fetchone()
            if is_found:                
                cursor.execute("UPDATE nextofkin SET nokname=%s, noknumber=%s, nokemail=%s, nokrel=%s WHERE emp_id=%s", 
                                (nokin, noknumber, nokemail, nokrel, empid))
            else:
                cursor.execute("INSERT INTO nextofkin(emp_id, nokname, noknumber, nokemail, nokrel) VALUES(%s, %s, %s, %s, %s)", 
                            (empid, nokin, noknumber, nokemail, nokrel))
            
            return True if cursor else None


    
    @classmethod
    def update_pension(cls, emp_id, pen_name, pen_num):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE emppension SET pen_name=%s, pen_num=%s WHERE emp_id=%s', (pen_name, pen_num, emp_id))
            if cursor:
                return True

    
    @classmethod
    def fetch_all_record(cls, status=1):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT id, name, department, jobtitle, email, staff_id, mobile, post FROM employees \
                            WHERE active=%s ORDER BY staff_id ASC', (status,))
            fetch_all = cursor.fetchall()
            if fetch_all is not None:
                return fetch_all


    @classmethod
    def fetch_all_dept(cls, dept, status=1):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT employees.id, employees.name, employees.department, employees.post, '
                           'employees.email, permission.active, employees.staff_id '
                           'FROM employees '
                           'LEFT JOIN permission '
                           'ON employees.id = permission.emp_id '
                           'WHERE permission.active=%s and employees.department=%s '
                           'ORDER BY employees.staff_id ASC', (status, dept))
            fetch_all = cursor.fetchall()
            if fetch_all is not None:
                return fetch_all

    
    @classmethod
    def get_employee(cls):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM employees ORDER BY id DESC")
            get_data = cursor.fetchone()
            if get_data is not None:
              return get_data
            else:
              return None
            

    
    @classmethod
    def emp_per_record(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM employees WHERE id = %s', (emp_id, ))
            get_data = cursor.fetchone()
            return get_data

    

    @classmethod
    def  emp_account_record(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select account_info.emp_id, account_info.basic, account_info.house_a, '
                           'account_info.transport_a, account_info.other_a, account_info.pension, account_info.gross, '
                           'account_info.cra, account_info.total_relief, tax.taxable, account_info.bank_name, '
                           'account_info.bank_acct, account_info.total_a, account_info.salary, '
                           'account_info.bank_branch, account_info.tax_number, account_info.acct_name, '
                           'account_info.tax_number, account_info.daily_rate, account_info.weekly_rate, '
                           'account_info.percentage , emppension.pen_name, emppension.pen_num '
                           'from account_info '
                           'left join tax '
                           'on account_info.emp_id = tax.emp_id '
                           'left join emppension '
                           'on account_info.emp_id = emppension.emp_id '
                           'where account_info.emp_id = %s', (emp_id,))
            get_data = cursor.fetchone()
            return get_data

    

    @classmethod
    def emppension(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select * from emppension WHERE emp_id=%s', (emp_id,))
            res = cursor.fetchone()
            return res


    
    @classmethod
    def empnokin(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM nextofkin WHERE emp_id=%s LIMIT 1", (emp_id,))
            nokin = cursor.fetchone()
            return nokin if nokin else None


    

    @classmethod
    def emp_permission(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM permission WHERE emp_id=%s', (emp_id,))
            emp_permission = cursor.fetchone()
            if emp_permission:
                return emp_permission

   
    @classmethod
    def updateBasicTaxInfo(cls, emp_id, taxNumber, basicPay, acctNum, acctName, bankName, percent):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE account_info SET tax_number=%s, basic=%s, bank_acct=%s, acct_name=%s, '
                           'bank_name=%s, percentage=%s WHERE emp_id=%s', (taxNumber, basicPay, acctNum, acctName,
                                                                           bankName, percent, emp_id))
            if cursor:
                return 'Update Successful'

    
    @classmethod
    def updateAllowanceInfo(cls, emp_id, gettype, amount):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE account_info SET {}={} WHERE emp_id={}'.format(gettype, amount,
                                                                                  emp_id))
            if cursor:
                cursor.execute('SELECT basic, house_a, transport_a, other_a FROM account_info WHERE emp_id=%s',
                               (emp_id,))
                getData = cursor.fetchone()
                if getData:
                    getall = (getData[1], getData[2], getData[3])
                    total = sum(getall)
                    basic = getData[0]

                    cursor.execute('UPDATE account_info SET total_a={} WHERE emp_id={}'.format(total, emp_id))
                    if cursor:
                        emp_acct_details = Taxable.get_taxable(basic, total)
                        update_gross = emp_acct_details['Gross']
                        update_cra = emp_acct_details['CRA']
                        update_pension = emp_acct_details['Pension']
                        update_totalrelief = emp_acct_details['Total Relief']

                        cursor.execute('UPDATE account_info SET gross = %s, cra = %s, pension = %s, total_relief = %s '
                                       'WHERE emp_id = %s',
                                       (update_gross, update_cra, update_pension, update_totalrelief, emp_id))

                        emp_taxable = update_gross - update_totalrelief
                        emp_taxband = emptaxband(emp_id=emp_id, gross=update_gross, relief=update_totalrelief)
                        emp_band1 = convert_to_float(emp_taxband['Firstband'])
                        emp_band2 = convert_to_float(emp_taxband['Secondband'])
                        emp_band3 = convert_to_float(emp_taxband['Thirdband'])
                        emp_band4 = convert_to_float(emp_taxband['Fourthband'])
                        emp_band5 = convert_to_float(emp_taxband['Fifthband'])
                        emp_band6 = convert_to_float(emp_taxband['Sixthband'])
                        emp_total_band = emp_taxband['Total_tax']
                        emp_min_tax = emp_taxband['Minimum_tax']
                        emp_hm_tax = emp_taxband['HM_tax']
                        emp_eff_tax = emp_taxband['Effective_tax']

                        emp_tax_record = Taxable.taxrecord(emp_id, emp_taxable, emp_min_tax, emp_hm_tax,
                                                           emp_eff_tax, emp_band1,
                                                           emp_band2, emp_band3, emp_band4, emp_band5, emp_band6,
                                                           emp_total_band)

                        '''return emp_tax_record'''
                        return 'Update Successful'
                else:
                    print('Error getting data')

    

    @classmethod
    def permit_emp(cls, emp_id, cms, report, loan):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('Update permission set ghi_cms=%s, m_report=%s, loan=%s where emp_id=%s',
                           (cms, report, loan, emp_id))
            if cursor:
                return 'Permission Updated'

    

    @classmethod
    def updatepensionprofile(cls, emp_id, name, number):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE emppension SET pen_name=%s, pen_num=%s WHERE emp_id=%s', (name, number, emp_id))
            if cursor:
                return 'Profile Updated'

    

    @classmethod
    def save_tools(cls, emp_id, services, device, department, email):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('INSERT INTO work_tools(emp_id, services, device, department, email) \
                            VALUES(%s, %s, %s, %s, %s) RETURNING id', (emp_id, services, device, department, email))
            if cursor:
                return True
                
   
    
    @classmethod
    def get_tools(cls, emp):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM work_tools WHERE emp_id=%s', (emp,))
            res = cursor.fetchall()
            return res

    

    @classmethod
    def get_tools_per_dept(cls, emp, dept):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM work_tools WHERE emp_id=%s and department=%s', (emp, dept))
            res = cursor.fetchone()
            return res

    

    @classmethod
    def DA_account(cls, emp_id, status):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE employees SET active=%s WHERE id=%s', (status, emp_id))
            cursor.execute('UPDATE permission SET active=%s WHERE emp_id=%s', (status, emp_id))
            return True

    

    @classmethod
    def pre_reg_list(cls):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM pre_reg")
            reg_list = cursor.fetchall()
            if reg_list is not None:
                return reg_list
            else: 
                return None
    
    

    @classmethod
    def reg_list_info(cls, new_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM pre_reg WHERE id=%s", (new_id,))
            record = cursor.fetchone()
            if record is not None:
                return record
            else: 
                return None

    

    @classmethod
    def delete_list(cls, new_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("DELETE FROM pre_reg WHERE id=%s", (new_id,))


    
    @classmethod
    def offboardinglist(cls):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("select employees.id, employees.name, offboarding.department, offboarding.startdate, offboarding.enddate,\
                            offboarding.reason, offboarding.status\
                            from offboarding\
                            left join employees\
                            on offboarding.emp_id = employees.id\
                            where offboarding.status=%s\
                            ", ('In-process',))
            res = cursor.fetchall()
            return res
            
    

    @classmethod
    def offboarding(cls, emp_id, department, offboarddate, reason, comment):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("INSERT INTO offboarding(emp_id, department, offboarddate, reason, comment) VALUES(%s, %s, %s, %s, %s)", 
                            (emp_id, department, offboarddate, reason, comment))
            if cursor:
                return True

    

    @classmethod
    def emp_offboardinglist(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM offboarding WHERE emp_id=%s and status=%s", (emp_id, 'In-process'))
            res = cursor.fetchone()
            if res:
                return res

    

    @classmethod
    def update_offboarding(cls, enddate, actions, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("UPDATE offboarding SET enddate=%s, actions=%s, status=%s WHERE emp_id=%s ", 
                (enddate, actions, 'Completed', emp_id))
            if cursor:
                return True
    

    @classmethod
    def checkprocess(cls, emp_id):
      with CursorFromConnectionPool() as cursor:
        cursor.execute("SELECT * FROM offboarding where emp_id=%s and status=%s LIMIT 1", (emp_id, 'In-process'))
        result = cursor.fetchone()
        if result:
          return True
        else:
          return False

    

    @classmethod
    def updateOffice(cls, initial, new):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("UPDATE employees SET branch=%s WHERE branch=%s", (new, initial))
            if cursor:
                return True


    

    @classmethod
    def branch_emp_list(cls, branch, status=1):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT employees.id, employees.name, employees.jobtitle '
                           'FROM employees '
                           'LEFT JOIN permission '
                           'ON employees.id = permission.emp_id '
                           'WHERE permission.active=%s and employees.branch=%s '
                           'ORDER BY employees.staff_id ASC', (status, branch))
            fetch_all = cursor.fetchall()
            if fetch_all:
                return fetch_all

    

    @classmethod
    def branch_emp(cls, name):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT count(*) from employees WHERE branch=%s", (name,))
            num = cursor.fetchone()
            if num:
                return num[0]

    @classmethod
    def update_emp_pension_name(cls, initial, new):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("UPDATE emppension SET pen_name=%s WHERE pen_name=%s", (new, initial))
            if cursor:
                return True

    @classmethod
    def update_emp_bankname(cls, initial, new):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("UPDATE emppension SET pen_name=%s WHERE pen_name=%s", (new, initial))
            if cursor:
                return True


    #### Onboarding Process ##############
    @classmethod
    def offboardinglist_on(cls):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT employees.id, employees.name, offboarding.department, offboarding.offboarddate, \
                            offboarding.reason, offboarding.comment, offboarding.id\
                            from offboarding\
                            left join employees\
                            on offboarding.emp_id = employees.id ORDER BY offboarding.id DESC \
                            ")
            res = cursor.fetchall()
            return res

    @classmethod
    def update_onboarding(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("DELETE FROM offboarding WHERE emp_id=%s",(emp_id, ))
            if cursor:
                return True

    @classmethod
    def stafflist(cls):
      with CursorFromConnectionPool() as cursor:
        cursor.execute('SELECT employees.staff_id, employees.name, employees.dob, employees.department, employees.post,\
                        employees.emp_class, account_info.bank_name, account_info.bank_acct, employees.active_date, employees.jobtitle \
                        FROM employees \
                        LEFT JOIN account_info \
                        ON employees.id = account_info.emp_id \
                        LEFT JOIN permission \
                        ON employees.id = permission.emp_id \
                        WHERE permission.active=1 \
                        ORDER BY employees.staff_id ASC')
        result = cursor.fetchall()
        if result is not None:
          return result


    @classmethod
    def viewUserAccount(cls, userid):
        from hr_application.models import Employees

        # get user email address
        user_record = Employee.emp_per_record(emp_id=userid)
        user_login = Employees.query.filter_by(email=user_record[7]).first()
        

        return user_login if user_login else None




def convert_value(getAmount):
    val = '{:,.2f}'.format(getAmount)
    return val


class SendMailNotice:
    def __init__(self, emp_name, dept, email, device, services, training, new=None, existing=None, access=None):
        self.name = emp_name
        self.dept = dept
        self.email = email
        self.device = device
        self.services = services
        self.training = training
        self.new = new
        self.existing = existing
        self.access_email = access

    def __repr__(self):
        pass

    def sendmail(self):
        sendport = current_app.config['MAIL_PORT']
        smtp_server = current_app.config['SEND_MAIL_SERVER']
        sender_email = current_app.config['EMAIL_ADDRESS']
        password = current_app.config['SEND_MAIL_PASSWORD']

        message = MIMEMultipart("alternative")
        message["Subject"] = "New Staff Tool Requirement"
        message["From"] = 'HR Management System'
        message["To"] = self.email
        text = """\
                            BUSINESS TRAVEL MANAGEMENT
                            New Staff Tool Requirement
                            """

        html = render_template('users/sendmail.html', device=self.device, services=self.services,
                               training=self.training, empname=self.name, dept=self.dept, new=self.new, existing=self.existing, 
                               access=self.access_email)

        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        message.attach(part1)
        message.attach(part2)

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(smtp_server, sendport, context=context) as server:
                server.login(sender_email, password)
                server.sendmail(
                    sender_email, self.email, message.as_string()
                )

            return True
        except:
            return False


class Offboradingmail:
    def __init__(self, emp_name, dept, email, device, services):
        self.name = emp_name
        self.dept = dept
        self.email = email
        self.device = device
        self.services = services

    def __repr__(self):
        pass

    def sendmail(self):
        sendport = 465
        smtp_server = 'smtp.gmail.com'
        sender_email = 'btmcircle@gmail.com'
        password = current_app.config['SEND_MAIL_PASSWORD']

        message = MIMEMultipart("alternative")
        message["Subject"] = "Offboarding Staff Notification"
        message["From"] = 'HR Management System'
        message["To"] = self.email
        text = """\
                            BUSINESS TRAVEL MANAGEMENT
                            Offboarding Staff Notification
                            """

        html = render_template('users/offboardmail.html', device=self.device, services=self.services, empname=self.name, 
                                dept=self.dept)

        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        message.attach(part1)
        message.attach(part2)

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(smtp_server, sendport, context=context) as server:
                server.login(sender_email, password)
                server.sendmail(
                    sender_email, self.email, message.as_string()
                )

            return True
        except:
            return False


class Onboradingmail:
    def __init__(self, emp_name, dept, email, device, services, empmail):
        self.name = emp_name
        self.dept = dept
        self.email = email
        self.device = device
        self.services = services

    def __repr__(self):
        pass

    def sendmail(self):
        sendport = 465
        smtp_server = 'smtp.gmail.com'
        sender_email = 'btmcircle@gmail.com'
        password = current_app.config['SEND_MAIL_PASSWORD']

        message = MIMEMultipart("alternative")
        message["Subject"] = "Onboarding Staff Notification"
        message["From"] = 'HR Management System'
        message["To"] = self.email
        text = """\
                            BUSINESS TRAVEL MANAGEMENT
                            Onboarding Staff Notification
                            """

        html = render_template('users/onboardmail.html', device=self.device, services=self.services, empname=self.name, 
                                dept=self.dept, empmail=empmail)

        part1 = MIMEText(text, "plain")
        part2 = MIMEText(html, "html")

        message.attach(part1)
        message.attach(part2)

        context = ssl.create_default_context()
        try:
            with smtplib.SMTP_SSL(smtp_server, sendport, context=context) as server:
                server.login(sender_email, password)
                server.sendmail(
                    sender_email, self.email, message.as_string()
                )

            return True
        except:
            return False



class TFeedback():
    def __init__(self, ulink):
        self.ulink = ulink

    def __repr__(self):
        pass

    
    @classmethod
    def getlist(cls, ulink=None):
        with CursorFromConnectionPool() as cursor:
            if ulink:
                cursor.execute("SELECT * FROM trainingfeedback WHERE ulink=%s LIMIT 1", (ulink, ))
                result = cursor.fetchone()
            else:
                cursor.execute("SELECT * FROM trainingfeedback ORDER BY datepost ASC")
                result = cursor.fetchall()
            
            return result

    
    def nOU(self, ulink=None):
        with CursorFromConnectionPool() as cursor:
            if ulink:
                cursor.execute("SELECT * FROM feedbackform WHERE ulink=%s ORDER BY id ASC", (self.ulink,))
                res = cursor.fetchall()
                return res
            else:
                cursor.execute("SELECT count(*) FROM feedbackform WHERE ulink=%s", (self.ulink,))
                res = cursor.fetchone()
                return res[0]


    @classmethod
    def empDet(cls, empid):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM employees WHERE id=%s LIMIT 1", (empid, ))
            det = cursor.fetchone()
            return det

    @classmethod
    def trainingFDlist(cls, empid=None):
        with CursorFromConnectionPool() as cursor:
            if empid:
                cursor.execute("SELECT feedbackform.emp_id, trainingfeedback.title, feedbackform.submitdate, feedbackform.ulink\
                                FROM feedbackform \
                                LEFT JOIN trainingfeedback ON trainingfeedback.ulink = feedbackform.ulink \
                                WHERE feedbackform.emp_id=%s \
                                ", (empid, ))
                res = cursor.fetchall()
            else:
                cursor.execute('SELECT id, emp_id, count(*), ulink from feedbackform group by id')
                res = cursor.fetchall()
            
            return res



