from flask import current_app, render_template, url_for
from packages.database import CursorFromConnectionPool
from datetime import datetime
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from packages.functions import get_table_column


class Loan:
    def __init__(self, emp_id):
        self.id = emp_id

    def __repr__(self):
        return "<User {}>".format(self.id)


    def loan_action(self, action):
      with CursorFromConnectionPool() as cursor:
        cursor.execute("UPDATE loan SET status=%s WHERE emp_id=%s and outstanding > %s", (action, self.id, 0))
        if cursor:
          return True
        else:
          return False

    #
    @classmethod
    def loan_applicants(cls, category):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT employees.name, loan.loan_type, loan.amount, loan.outstanding, loan.percent, \
                           loan.installment, loan.deduction_rate, loan.emp_id, loan.id, loan.loan_category \
                           from loan \
                           left join employees \
                           on loan.emp_id = employees.id \
                           where loan.status=%s and loan.loan_category=%s and loan.outstanding > %s', (1, category.lower(), 0))
            res = cursor.fetchall()
            return res

    #
    @classmethod
    def loan_per_applicants(cls, emp_id, loan_type):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT employees.name, loan.loan_type, loan.amount, loan.outstanding, loan.percent, '
                           'loan.installment, loan.deduction_rate, loan.emp_id, loan.id '
                           'from loan '
                           'left join employees '
                           'on loan.emp_id = employees.id '
                           'WHERE loan.emp_id=%s and loan.loan_type=%s', (emp_id, loan_type))
            res = cursor.fetchone()
            return res


    @classmethod
    def requestlist(cls, loanid=None, emp_id=None, status=None):
        with CursorFromConnectionPool() as cursor:
            if loanid == None:
              cursor.execute('SELECT employees.staff_id, employees.name, employees.department, employees.email, \
                                    loanrequest.loantype, loanrequest.process_date, employees.id, loanrequest.id, \
                                    loanrequest.status \
                              FROM loanrequest\
                              LEFT JOIN employees ON loanrequest.emp_id = employees.id \
                              WHERE loanrequest.status = %s and employees.active=%s ORDER BY loanrequest.id Desc', (status.lower(), 1))
              res = cursor.fetchall()
              return res
            else:
              cursor.execute('SELECT * FROM loanrequest WHERE emp_id=%s and id=%s LIMIT 1', (emp_id, loanid))
              res = cursor.fetchone()
              return res

    @classmethod
    def getEMI(cls, emp_id, amount, rate, duration):
      getrate = int(rate)
      
      getPerc = getrate / 100

      getAmount = getPerc * float(amount)

      repayment = float(getAmount) + float(amount)
      # check if repayment is payable
      is_amount_payable = Process_loan(emp_id=emp_id).quarter_salary(repayment=repayment)
      
      if is_amount_payable == True:
        EMI = float(repayment) / int(duration)
        return format(repayment,'.2f'), format(EMI, '.2f'), rate, duration

      elif is_amount_payable == 'Tax profile has not been processed.':
        return 101
      else:
        return False

    
    def loanRecord(self, loanrequestid=None, active=None):
      with CursorFromConnectionPool() as cursor:
        if not active:
          cursor.execute("SELECT * FROM loan WHERE loanrequestid=%s and emp_id=%s LIMIT 1", (loanrequestid, self.id))
        else:
          cursor.execute("SELECT * FROM loan WHERE id=%s and emp_id=%s LIMIT 1", (active, self.id))
        
        res = cursor.fetchone()
        if res: return res

    
    def chkloanpaid(self, loanid, month, year):
      with CursorFromConnectionPool() as cursor:
        cursor.execute("SELECT * FROM loanrepay WHERE loan_id=%s and emp_id=%s and month=%s and year=%s", 
                        (loanid, self.id, month, year))
        res = cursor.fetchone()
        if res:
          return res            
            

    @classmethod
    def createloantype(cls, name, description):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('INSERT INTO loantype(loan_name, loan_description) VALUES(%s, %s) RETURNING ID',
                           (name, description))
            res = cursor.fetchone()
            if res:
                return 'New Loan Type Created Successfully'

    @classmethod
    def updateloantype(cls, name, description, get_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE loantype SET loan_name=%s, loan_description=%s WHERE id=%s',
                           (name, description, get_id))
            if cursor:
                return 'Updated Successfully'

    @classmethod
    def otherloan(cls, getsalary):
        debit_percentage_value = 0
        repayment = getsalary - debit_percentage_value
        return repayment

    # @classmethod
    # def save_loan(cls, emp_id, loan_type, amount, outstanding, percent, repay_perc):
    #     with CursorFromConnectionPool() as cursor:
    #         cursor.execute('INSERT INTO loan (emp_id, loan_type, amount, outstanding, percent, repayment_perc) '
    #                        'values(%s, %s, %s, %s, %s, %s) RETURNING id',
    #                        (emp_id, loan_type, amount, outstanding, percent, repay_perc))
    #         res = cursor.fetchone()
    #         return res

    @classmethod
    def get_loan_details(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM loan WHERE emp_id=%s and loan_category=%s', (emp_id, 'otherloan'))
            res = cursor.fetchall()
            return res

    #
    @classmethod
    def coop_loan_applicants(cls):
      category = 'cooperative'.lower()
      with CursorFromConnectionPool() as cursor:
        cursor.execute('SELECT employees.name, loan.loan_type, loan.amount, loan.outstanding, loan.percent, \
                        loan.installment, loan.deduction_rate, loan.emp_id, loan.id \
                        FROM loan \
                        LEFT JOIN employees \
                        ON loan.emp_id = employees.id \
                        WHERE loan.status=%s and loan.loan_category=%s', (1, category))
        res = cursor.fetchall()
        return res

    @classmethod
    def coop_per_applicants(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT employees.name, cooperative.loan, cooperative.outstanding, cooperative.emp_id '
                           'from cooperative '
                           'left join employees '
                           'on cooperative.emp_id = employees.id '
                           'WHERE cooperative.emp_id=%s', (emp_id,))
            res = cursor.fetchone()
            return res


    @classmethod
    def clearloan(cls, emp_id, loan_id):
      loanrecord = Loan(emp_id).loanRecord(active=loan_id)
      empid = loanrecord[1]
      loantype = loanrecord[2]
      loan_amount = loanrecord[3]
      outstandingLoan = int(0)
      repayment = loanrecord[4]
      category = loanrecord[9].lower()
      loanId = loanrecord[0]
      status = 'Loan cleared'

      saveRecord = loanpayment(empid=empid, loan_type=loantype, loan=loan_amount, repayment=repayment, 
                                outstanding=outstandingLoan, category=category, loan_id=loanId, status=status)
      if saveRecord:
        with CursorFromConnectionPool() as cursor:
          cursor.execute("UPDATE loan SET outstanding=%s, status=%s WHERE id=%s and emp_id=%s", (outstandingLoan, 0, loanId, empid))
          if cursor:
            return True


    @classmethod
    def getLoanType(cls):
      with CursorFromConnectionPool() as cursor:
        cursor.execute("SELECT * FROM loantype")
        _types = cursor.fetchall()
        return _types if _types else None


    @classmethod
    def getLoanReportFilter(cls, fType, fyear, mode, fStatus=None):
      
      if mode.lower() == 'loanrecord':
        with CursorFromConnectionPool() as cursor:
          if fType.lower() == 'all' and fStatus.lower() == 'all' and fyear.lower() == 'all':
            cursor.execute("SELECT * FROM loan")

          elif fType.lower() != 'all' and fStatus.lower() == 'all' and fyear.lower() == 'all':
            cursor.execute("SELECT * FROM loan WHERE loan_type=%s", (fType,))

          elif fType.lower() == 'all' and fStatus.lower() != 'all' and fyear.lower() == 'all':
            if fStatus.lower() == 'active':
              cursor.execute("SELECT * FROM loan WHERE outstanding > %s", (0, ))
            elif fStatus.lower() == 'pending':
              cursor.execute("SELECT * FROM loanrequest WHERE status is %s", (None,))
            elif fStatus.lower() == 'completed':
              cursor.execute("SELECT * FROM loan WHERE outstanding = %s", (0, ))

          elif fType.lower() == 'all' and fStatus.lower() != 'all' and fyear.lower() != 'all':
            if fStatus.lower() == 'active':
              cursor.execute("SELECT * FROM loan WHERE outstanding > %s and year=%s", (0, fyear))
            elif fStatus.lower() == 'pending':
              cursor.execute("SELECT * FROM loanrequest WHERE year=%s", (fyear, ))
            elif fstatus.lower() == 'completed':
              cursor.execute("SELECT * FROM loan WHERE outstanding = %s and year=%s", (0, fyear))

          elif fType.lower() != 'all' and fStatus.lower() != 'all' and fyear.lower() == 'all':
            if fStatus.lower() == 'active':
              cursor.execute("SELECT * FROM loan WHERE loan_type=%s and outstanding > %s", (fType, 0))
            elif fStatus.lower() == 'pending':
              cursor.execute("SELECT * FROM loanrequest WHERE loantype=%s and status is %s ", (fType, None))
            elif fStatus.lower() == 'completed':
              cursor.execute("SELECT * FROM loan WHERE loan_type=%s and outstanding=%s", (fType, 0))

          elif fType.lower() != 'all' and fStatus.lower() != 'all' and fyear.lower() != 'all':
            if fStatus.lower() == 'active':
              cursor.execute("SELECT * FROM loan WHERE loan_type=%s and outstanding > %s and year=%s", (fType, 0, fyear))
            elif fStatus.lower() == 'pending':
              cursor.execute("SELECT * FROM loanrequest WHERE loantype=%s and status is %s and year=%s", (fType, None, fyear))
            elif fStatus.lower() == 'completed':
              cursor.execute("SELECT * FROM loan WHERE loan_type=%s and outstanding=%s and year=%s", (fType, 0, fyear))

          result = cursor.fetchall()
          return result if result else None


      if mode.lower() == 'repaymentrecord':
        with CursorFromConnectionPool() as cursor:
          if fType.lower() == 'all' and fyear == 'all':
            cursor.execute("SELECT * FROM loanrepay")
          elif fType.lower() == 'all' and fyear != 'all':
            cursor.execute("SELECT * FROM loanrepay WHERE year=%s", (fyear, ))
          elif fType.lower() != 'all' and fyear != 'all':
            cursor.execute("SELECT * FROM loanrepay WHERE loan_type=%s and year=%s", (fType, fyear))
          
          result = cursor.fetchall()
          return result if result else None




def loanpayment(empid, loan_type, loan, repayment, outstanding, category, loan_id, status=None):
  month = datetime.today().strftime("%B")
  year = datetime.today().strftime("%Y")

  with CursorFromConnectionPool() as cursor:
    # check if record already exist
    cursor.execute("INSERT INTO loanrepay(emp_id, loan_type, month, year, loan, repayment, outstanding, category, \
                    loan_id, status) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", 
                    (empid, loan_type, month, year, loan, repayment, outstanding, category, loan_id, status))
    if cursor:
      return True


class Process_loan:
  """docstring for Process_loan"""
  def __init__(self, emp_id):
    self.id = emp_id

  def __repr__(self):
    pass

  def emp_loan_enabled(self):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("SELECT loan FROM permission WHERE emp_id=%s", (self.id,))
      res = cursor.fetchone()
      if res is not None:
        is_emp_enabled = res[0]
        if is_emp_enabled == 1:
          return True
        

  def on_loan(self):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("SELECT * FROM loan WHERE emp_id=%s and outstanding > %s", (self.id, 0))
      is_on_loan = cursor.fetchall()
      if is_on_loan:
        return is_on_loan


  def on_coop_loan(self):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("SELECT * FROM cooperative WHERE emp_id=%s and outstanding > %s", (self.id, 0))
      is_on_coop_loan = cursor.fetchone()
      if is_on_coop_loan is not None:
        return True
      else:
        return False


  def quarter_salary(self, repayment):
    info = Process_loan.fetch_gross(self.id)

    if info is not None and info[2] is not None:
      value = info[0] - info[1] - info[2]
      # get quarter value
      quarter_value = value / 3


      if quarter_value > repayment:
        return True
      else:
        return False
    else:
      return 'Tax profile has not been processed.'


  @classmethod
  def is_loan_enabled(cls):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("SELECT loan_request FROM oops")
      res = cursor.fetchone()
      if res is not None:
        is_enabled = res[0]
        if is_enabled == 1:
          return True
        else:
          return False
      else:
        None

  @classmethod
  def fetch_gross(cls, emp_id):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("SELECT gross, pension, total_tax "
                      "FROM account_info "
                      "LEFT JOIN tax "
                      "ON account_info.emp_id = tax.emp_id "
                      "WHERE account_info.emp_id = %s", (emp_id,))
      res = cursor.fetchone()
      if res is not None:
        return res
      else:
        return None

  @classmethod
  def repyament_amount(cls, repayment, installment):
    to_pay = repayment / installment
    return to_pay


  @classmethod
  def loan_type(cls, get_type):
    check_for = get_type.lower().find('cooperative')

    if check_for > 0:
      return 'coop'
    else:
      return 'others'


  def getLoanRecord(self, category):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("SELECT * FROM loan WHERE emp_id=%s and loan_category=%s ORDER BY id", (self.id, category))
      response = cursor.fetchall()
      if not None: return response 

  def getLoanRecordDetails(self, loan_id, category):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("SELECT * FROM loanrepay WHERE loan_id=%s and emp_id=%s and category=%s", (loan_id, self.id, category))
      result = cursor.fetchall()
      if not None: return result


  @classmethod
  def loanType(cls, loanTypeID):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("SELECT * FROM loantype WHERE id=%s LIMIT 1", (loanTypeID,))
      res = cursor.fetchone()
      if res: return res


  def submitRequest(self, loantype, amount, installment, requestDate, processDate, year):
    with CursorFromConnectionPool() as cursor:
      status = 'pending'.lower()
      cursor.execute("INSERT INTO loanrequest(emp_id, loantype, amount, installment, requesting_date, process_date, status, year)\
                      VALUES(%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id", 
                      (self.id, loantype, amount, installment, requestDate, processDate, status, year))
      getloanid = cursor.fetchone()
      if getloanid: return getloanid
        
        


  def pendingLoan(self, pendId=None):
    with CursorFromConnectionPool() as cursor:
        status = ['approved', 'processed']

        if pendId == None:
          cursor.execute("SELECT * FROM loanrequest WHERE emp_id=%s and status!=%s and status!=%s ", 
                          (self.id, status[0], status[1]))
          result = cursor.fetchall()
        else:
          cursor.execute("SELECT * FROM loanrequest WHERE id=%s and status != %s and status !=%s", (pendId, 
                                                                                                      status[0], status[1]))
          result = cursor.fetchone()
      
        if result:
          return result


  def updateLoanRequest(self, loantype, amount, installment, update, requestDate=None, emi=None, rate=None, \
                        repayment=None, note=None, status=None):
    with CursorFromConnectionPool() as cursor:
      if emi == None:
        cursor.execute("UPDATE loanrequest SET loantype=%s, amount=%s, installment=%s, requesting_date=%s WHERE id=%s", 
                        (loantype, amount, installment, requestDate, update))
      else:
        cursor.execute("UPDATE loanrequest SET loantype=%s, amount=%s, installment=%s, emi=%s, rate=%s, \
                        repayment=%s, note=%s, status=%s WHERE id=%s", 
                        (loantype, amount, installment, emi, rate, repayment, note, status, update))
      if cursor:
        # send email notification to admin on update
        return True


  def deleteLoan(self, loanid):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("UPDATE loanrequest SET status=%s WHERE id=%s and emp_id=%s", ('cancelled', loanid, self.id))
      if cursor:
        # send an email notification to admin.
        return True

  def loanreview(self, loanid, status):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("UPDATE loanrequest SET status=%s WHERE emp_id=%s and id=%s", (status, self.id, loanid))
      if cursor:
        return True

      
    
class Save_loan:
  """docstring for Save_loan"""
  def __init__(self, emp_id, loan_type, amount, outstanding, interest, installment, deduction):
    self.id = emp_id
    self.type = loan_type
    self.amount = outstanding #amount
    self.outstanding = outstanding
    self.interest = interest
    self.installment = installment
    self.deduction = deduction

  def __repr__(self):
    pass


  def save_loan(self, loan_category, requestID):
    month = datetime.today().strftime('%B')
    year = datetime.today().strftime('%Y')
    date = datetime.today().strftime('%d/%B/%Y')
    with CursorFromConnectionPool() as cursor:
      cursor.execute("INSERT INTO loan(emp_id, loan_type, amount, outstanding, percent, installment, deduction_rate, \
                                        loan_category, month, year, status, loanrequestid)\
                      VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id", 
                      (self.id, self.type, self.amount, self.outstanding, self.interest, 
                        self.installment, self.deduction, loan_category, month, year, 1, requestID))
      getid = cursor.fetchone()
      if getid:
        cursor.execute("UPDATE loanrequest SET amount=%s, installment=%s, emi=%s, rate=%s, repayment=%s,\
                        status=%s, loandate=%s WHERE id=%s and emp_id=%s", 
                      (self.amount, self.installment, self.deduction, self.interest, self.outstanding,\
                        'processed', date, requestID, self.id))
        loanid = 'Loan/'+year+'/00'+str(getid[0])
        cursor.execute("UPDATE loan SET loanid=%s WHERE id=%s", (loanid, getid))
        if cursor:
          return True
      else:
        return False


  def save_coop_loan(self):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("UPDATE cooperative SET loan=%s, outstanding=%s, loan_percent=%s, installment=%s, deduction_rate=%s WHERE emp_id=%s", 
                      (self.amount, self.outstanding, self.interest, self.installment, self.deduction, self.id) )
      if cursor:
        return True
      else:
        return False




class sendLoanNotification():
  """docstring for resetPass"""
  def __init__(self, empid, loanid, msg):
    self.id = empid
    self.loanid = loanid
    self.url = url_for('loans.requests', _external=True)
    self.details = sendLoanNotification.getLoanInfo(empid=self.id, loanid=self.loanid)
    self.msg = msg

  
  def sendMail(self):
    admin_email = sendLoanNotification.getAdminEmail()

    sendport = current_app.config['MAIL_PORT']
    smtp_server = 'smtp.gmail.com'
    sender_email = current_app.config['EMAIL_ADDRESS']
    password = current_app.config['SEND_MAIL_PASSWORD']
    
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Loan Application"
    message["From"] = 'BTM Loan Management System'
    message["To"] = admin_email
    text = """\
    
          BUSINESS TRAVEL MANAGEMENT
          Loan Application
          """
    html = render_template('userloan/loanmsg.html', details=self.details, message=self.msg, url=self.url)
    
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    message.attach(part1)
    message.attach(part2)

    context = ssl.create_default_context()
    try:
      with smtplib.SMTP_SSL(smtp_server, sendport, context=context) as server:
        server.login(sender_email, password)
        server.sendmail(sender_email, admin_email, message.as_string())

        return True
    except: 
      return True

   

  @classmethod
  def getAdminEmail(cls):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("SELECT leave_hr_email from oops limit 1")
      email = cursor.fetchone()
      if email:
        return email[0]


  @classmethod
  def getLoanInfo(cls, empid, loanid):
    with CursorFromConnectionPool() as cursor:
      # send a mail notification to the admin user of a new loan request.
      cursor.execute("SELECT employees.name, loanrequest.loantype, loanrequest.amount, loanrequest.installment \
                      from employees left join loanrequest on employees.id = loanrequest.emp_id\
                      where employees.id=%s and loanrequest.id=%s LIMIT 1", (empid, loanid))
      det = cursor.fetchone()
      if det: return det

