from flask import Blueprint, render_template, make_response, jsonify, request, redirect, url_for, flash, Markup, session
from flask_login import current_user, login_required
from packages.payroll.loan.loanOop import Loan, Process_loan, Save_loan
from packages.employees.userOop import Employee
from packages.employees.coop.cooperative import Cooperative
from packages.functions import fetch_table_record, fetch_table_per_record
from packages.payroll.taxable import convert_to_float
import datetime
from packages.run_admin import year_selector

loans = Blueprint('loans', __name__, url_prefix='/', template_folder='templates')


@loans.before_request
def chk_session():
    if not current_user.is_authenticated:
        return redirect(url_for('admin.login', next=request.url))



@loans.route('/admin/loan', methods=['POST', 'GET'])
def loan():
    emp_data = Employee.fetch_all_record()
    dept = fetch_table_record('department')
    loantype = fetch_table_record('loantype')
    
    if len(loantype) == 0:
        loantype = None
        msg = Markup("<b>No Loan Type has been Created yet! </b> <a href='"+url_for('loans.createloantype')+"'>click here to create</a>")
        flash(msg, 'warning')

    if request.method == 'POST' and request.form['type'] == 'department':
        deptname = request.form['deptname']
        dept_list = Employee.fetch_all_dept(dept=deptname)
        
        if len(dept_list) > 0:
            dept_list = dept_list
        else:
            dept_list = None

        return make_response(jsonify(dept_list))
    
    elif request.method == 'POST' and request.form['type'] == 'employee':
        empid = request.form['empid']
        on_loan = Process_loan(emp_id=empid).on_loan()
        loantype = fetch_table_record('loantype')
        
        if on_loan:
            on_loan = on_loan
        else:
            on_loan = None

        return make_response(jsonify(on_loan, loantype))

    elif request.method == 'POST' and request.form['type'] == 'checkloan':
        empid = request.form['empid']
        loantype = request.form['loantype']

        if 'cooperative' in loantype.lower():
            chk = Cooperative().chk_coop_emp(emp_id=empid)
            if chk:
                status = 'True'
            else:
                status = 'False'
        else:
            status = '0'

        return make_response(jsonify(status))
        

    return render_template('loans/loan.html', emp_list=emp_data, department=dept)


@loans.route('/admin/processloan', methods=['POST'])
def submitLoanApplication():
    empid = request.form['empid']
    loantype = request.form['loantype']
    amount = float(request.form['amount'].replace(',',''))
    installment = request.form['duration']
    requestDate = request.form['requestdate']
    processDate = datetime.datetime.today().strftime('%d/%m/%Y')
    year = datetime.datetime.today().strftime('%Y')

    
    saveLoan = Process_loan(emp_id=empid).submitRequest(loantype, amount, installment, requestDate, processDate, year)
    if saveLoan:
        # send email notification to loan applicant
        flash("Loan Submitted", 'success')
    else:
        flash("Error updatinig loan request", 'danger')
    
    return redirect(url_for('loans.loan'))



@loans.route('/admin/requests')
def requests():
    loanlist = Loan.requestlist(status='pending')
    return render_template('loans/requestlist.html', list=loanlist)


@loans.route('/admin/processrequest/<emp_id>/<loanid>', methods=['POST', 'GET'])
def processLoanRequest(emp_id, loanid):
    emp_record = Employee.emp_per_record(emp_id)
    loanrecord = Loan.requestlist(loanid=loanid, emp_id=emp_id)
    link_loan = None
    
    if not loanrecord:
        return redirect(url_for('loans.requests'))
    else:
        link_loan = Loan(emp_id).loanRecord(loanrequestid=loanrecord[0])
        if not link_loan:
            loanID = None
        else:
            loanID = link_loan[0]

    
    is_on_loan = Process_loan(emp_id=emp_id).on_loan()
    EMI = None
    note = session.get('loan_note')

    if 'cooperative' in loanrecord[2].lower():
        loan_category = 'cooperative'
    else:
        loan_category = 'otherloan'

    if request.method == 'POST':
        if request.form['submitbtn'] == 'calculate':
            loan_amount = request.form['amount']
            rate = request.form['rate']
            duration = request.form['duration']

            values = Loan.getEMI(emp_id=emp_id, amount=loan_amount, rate=rate, duration=duration)
            
            if values and values != 101:
                EMI = values
            elif values == 101:
                EMI = 101
            elif values == False:
                flash("Loan amount exceed salary strength", 'info')
                EMI = None

        if request.form['submitbtn'] == 'note':
            session['loan_note'] = request.form['loan_note']
            flash('Note Attached to loan successfully', 'success')
            return redirect(url_for('loans.processLoanRequest', emp_id=emp_id, loanid=loanid)) 

        if request.form['submitbtn'] == 'submit':
            loan_amount = request.form['repayment']
            rate = request.form['rate']
            duration = request.form['duration']
            note = request.form['loan_note']
            EMI = request.form['deduction']
            repayment = request.form['repayment']

            updateLoan = Process_loan(emp_id).updateLoanRequest(loantype=loanrecord[2], amount=loan_amount, installment=duration,\
                                                                update=loanrecord[0], emi=EMI, rate=rate, repayment=repayment, \
                                                                note=note, status='processing')
            if updateLoan:
                # send mail notification to user
                flash('Submitted', 'success')
            return redirect(url_for('loans.processLoanRequest', emp_id=emp_id, loanid=loanid))


        if request.form['submitbtn']  == 'processloan':
            _type = request.form['_type']
            _amount = request.form['_outstanding']
            _outstanding = request.form['_outstanding']
            _perc = request.form['rate']
            _installment = request.form['duration']
            _deduction = request.form['deduction']
            _category = request.form['_category']
            

            proc = Save_loan(emp_id, _type, _amount, _outstanding, _perc, _installment, _deduction).save_loan(loan_category, \
                                                                                                                loanrecord[0] )

            flash('Loan process successfully', 'success')
            return redirect(url_for('loans.processLoanRequest', emp_id=emp_id, loanid=loanid))


    return render_template('loans/processloan.html', user=emp_record, loanrecord=loanrecord, EMI=EMI, note=note, \
                            on_loan=is_on_loan, category=loan_category, loanID=loanID)
    

@loans.route('/admin/list', methods=['POST', 'GET'])
def list():
    loanlist = Loan.loan_applicants(category='otherloan')

    if request.method == 'POST':
        adjust = request.form['id']
        loan_type = request.form['loan_type']
        get_data = Loan.loan_per_applicants(emp_id=adjust, loan_type=loan_type)
        
        return make_response(jsonify(get_data))
    return render_template('loans/list.html', list=loanlist)


@loans.route('admin.list-details/<emp_id>/<loanID>/<category>')
def loanDetails(emp_id, loanID, category):
    emp_record = Employee.emp_per_record(emp_id)
    details = Loan(emp_id).loanRecord(active=int(loanID))
    if not details:
        return redirect(url_for('loans.list'))

    return render_template('loans/loaninfo.html', user=emp_record, loanrecord=details)


@loans.route('/admin/coop-list', methods=['POST', 'GET'])
def coop_loan_list():
    loanlist = Loan.coop_loan_applicants()

    if request.method == 'POST':
        adjust = request.form['id']
        get_data = Loan.coop_per_applicants(emp_id=adjust)
        
        return make_response(jsonify(get_data))
    return render_template('loans/cooploanlist.html', list=loanlist)


@loans.route('/admin/chk_emp_loan', methods=['POST'])
def chk_emp_loan():
    if request.method == 'POST':
        chk_emp_coop = request.form['emp_id']
        if chk_emp_coop:
            is_emp_active = Cooperative.chk_coop_emp(chk_emp_coop)
            if is_emp_active:
                if is_emp_active[5] is not None:
                    if float(is_emp_active[5]) > int(0):
                        return make_response(jsonify('on loan'))
                return make_response(jsonify('Active'))
            else:
                return make_response(jsonify('None'))


@loans.route('/admin/processloan', methods=['POST', 'GET'])
def processloan():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        loan = convert_to_float(request.form['amount'])
        repay = convert_to_float(request.form['repayment'])
        installment = int(request.form['installment'])
        loan_type = request.form['type']
        interest = request.form['loan_perc']

        # check if loan is enable
        is_enable = Process_loan.is_loan_enabled()
        if is_enable is not None:
            if is_enable == True:
                is_emp_enable = Process_loan(emp_id=emp_id).emp_loan_enabled()
                if is_emp_enable == True:
                    #check loan type
                    what_type = Process_loan.loan_type(get_type=loan_type)

                    if what_type == 'others':
                        # chk if emp is on loan
                        # is_on_loan = Process_loan(emp_id=emp_id).on_loan()
                        # if is_on_loan is not True:
                            is_amount_payable = Process_loan(emp_id=emp_id).quarter_salary(repayment=repay)
                            if is_amount_payable == True:
                                to_pay_monthly = Process_loan.repyament_amount(repayment=repay, installment=installment)

                                save_loan = Save_loan(emp_id=emp_id, loan_type=loan_type, amount=loan, outstanding=repay, 
                                                        interest=interest, installment=installment, deduction=to_pay_monthly).save_loan(loan_category=\
                                                                                                                                        'otherloan')
                                if save_loan is True:
                                    msg = Markup("<strong>"+ loan_type.upper() + " has been process successfully </strong>")
                                    flash(msg, 'success')
                                    return redirect(url_for('loans.list'))
                                else:
                                    flash('Error processing loan. Try Again', 'danger')
                                    return redirect(url_for('loans.loan'))
                            elif is_amount_payable == 'Tax profile has not been processed.':
                                flash(is_amount_payable, 'warning')
                                return redirect(url_for('loans.loan'))
                            else:
                                flash('No! Amount requested is not payable', 'warning')
                                return redirect(url_for('loans.loan'))
                        # else:
                        #     flash('Sorry! Employee is currently on loan', 'warning')
                        #     return redirect(url_for('loans.loan'))
                        #     flash('Other type of loan', 'info')
                        #     return redirect(url_for('loans.loan'))
                    elif what_type == 'coop':
                        # is_on_coop_loan = Process_loan(emp_id=emp_id).on_coop_loan()
                        # if is_on_coop_loan is not True:
                            # is_on_loan = Process_loan(emp_id=emp_id).on_loan()
                            # if is_on_loan is not True:
                                to_pay_monthly = Process_loan.repyament_amount(repayment=repay, installment=installment)

                                save_loan = Save_loan(emp_id=emp_id, loan_type=loan_type, amount=loan, outstanding=repay, 
                                                        interest=interest, installment=installment, deduction=to_pay_monthly).save_loan(loan_category=\
                                                                                                                                        'cooperative')
                                if save_loan is True:
                                    msg = Markup("<strong>"+ loan_type + " has been process successfully </strong>")
                                    flash(msg, 'success')
                                    return redirect(url_for('loans.coop_loan_list'))
                                else:
                                    flash('Error processing loan. Try Again', 'danger')
                                    return redirect(url_for('loans.loan'))
                            # else:
                            #     flash('Sorry! Employee is currently on loan', 'warning')
                            #     return redirect(url_for('loans.loan'))  
                        # else:
                        #     flash('Sorry! Employee is currently on cooperative loan', 'warning')
                        #     return redirect(url_for('loans.loan'))
                else:
                    flash('Employees loan request has been disabled', 'warning')
                    return redirect(url_for('loans.loan'))
                flash('Enabled', 'success')
                return redirect(url_for('loans.loan'))
            else:
                flash('Loan request has been disabled', 'info')
                return redirect(url_for('loans.loan'))
        else:
            flash('Loan setting has not be set!', 'warning')
            return redirect(url_for('loans.loan'))



@loans.route('/admin/clearloan', methods=['POST', 'GET'])
def clearloan():
    if request.method == 'POST':
        emp_id = request.form['id']
        loan_id = request.form['loan_id']
        url = request.form['url']
        clear = Loan.clearloan(emp_id=emp_id, loan_id=loan_id)
        
        if clear == True:
            flash('Loan has been cleared successfully', 'success')
            return redirect(url_for(url))
        elif clear == False:
            return redirect(url_for(url))
        else:
            flash('Process failed', 'warning')
            return redirect(url_for(url))




@loans.route('/admin/createloantype', methods=['POST', 'GET'])
def createloantype():
    alert = ''

    if request.method == 'POST':
        name = request.form['name']
        description = request.form['loandescription']
        new_type = Loan.createloantype(name, description)

        if new_type is not None:
            alert = new_type

    return render_template('loans/createloantype.html', alert=alert)


@loans.route('/admin/loantypes')
def loantypes():
    typelist = fetch_table_record('loantype')

    return render_template('loans/loantypes.html', typelist=typelist)


@loans.route('/admin/editloantype/<get_id>', methods=['POST','GET'])
def editloantype(get_id):
    alert = ''
    typedetails = fetch_table_per_record('loantype', get_id)

    if request.method == 'POST':
        type_id = request.form['id']
        name = request.form['name']
        description = request.form['loandescription']

        update = Loan.updateloantype(name, description, type_id)
        typedetails = fetch_table_per_record('loantype', get_id)
        alert = update

    return render_template('loans/editloantype.html', typedetails=typedetails, alert=alert)


@loans.route('/admin/activeloan', methods=['POST', 'GET'])
def activeloan():
    emp_id = request.form['id']
    # check if emp is currently on a particular loan
    chk = Loan.get_loan_details(emp_id)
    if chk is not None:
        return make_response(jsonify(chk))


@loans.route('/admin/loan/<action>/<get_id>')
def action(action, get_id):
    if action == 'approve':
        op = Loan(emp_id=get_id).loan_action(action=1)
        if op == True:
            flash('Loan approved', 'success')
            return redirect(url_for('loans.requests'))
        else:
            flash('Operation failed', 'danger')
            return redirect(url_for('loans.requests'))
    
    if action == 'decline':
        op = Loan(emp_id=get_id).loan_action(action=2)
        if op == True:
            flash('Loan Decline', 'danger')
            return redirect(url_for('loans.requests'))
        else:
            flash('Operation failed', 'danger')
            return redirect(url_for('loans.requests'))

    return redirect(url_for('loans.requests'))



@loans.route('/admin/deletetype')
def deleteloantype():
    pass


@loans.route('/admin/loans/report', methods=['POST', 'GET'])
def loanreport():
    _types = Loan.getLoanType()
    _years = year_selector()
    _status = ['Active', 'Pending', 'Completed']
    filterRecord, rtable, rfilter = None, 'loantable', 'loanreport'
    openFilter = None

    if request.method == 'POST':
        btnSubmit = request.form['submit'].lower()

        if btnSubmit == 'loan':
            fType = request.form['_type']
            fStatus = request.form['_status']
            fyear = request.form['_year']
            fmode = request.form['mode']

            filterRecord = Loan.getLoanReportFilter(fType=fType, fyear=fyear, mode=fmode, fStatus=fStatus)

        elif btnSubmit == 'repayment':        
            fmode = request.form['mode']
            fType = request.form['type']
            fyear = request.form['year']
            filterRecord = Loan.getLoanReportFilter(fType=fType, fyear=fyear, mode=fmode)


        openFilter = [fType, fStatus, fyear]

        
        if not filterRecord:
            flash('No Record found', 'info')
        else:
            if btnSubmit == 'loan':
                if fStatus.lower() == 'pending':
                    rtable = 'pendingtable'

        
        if fmode.lower() == 'repaymentrecord':
            rfilter = 'repayment'
            rtable = 'repaymenttable'
        else:
            rfilter = None

    
    return render_template('loans/reportloan.html', rfilter=rfilter, _types=_types, _years=_years, _status=_status, \
                            filterRecord=filterRecord, rtable=rtable, openFilter=openFilter)


@loans.add_app_template_filter
def emi_payment(duration, loanID, emp_id, emp_name, requestID=None):
    from dateutil import relativedelta
    
    if not loanID:
        return None

    details = []
    if requestID:
        loanrecord = Loan(emp_id).loanRecord(loanrequestid=int(requestID))
    else:  
        loanrecord = Loan(emp_id).loanRecord(active=int(loanID))
    
    if loanrecord:
        getdate = datetime.datetime.today().strptime('01/'+loanrecord[10]+'/'+loanrecord[11], '%d/%B/%Y')
    else:
        return None
    
    for i in range(int(duration)):
        next_month = getdate + relativedelta.relativedelta(months=i)
        getDate = datetime.datetime.today().strptime(str(next_month), '%Y-%m-%d %H:%M:%S').strftime('%B/%Y')
        month = datetime.datetime.today().strptime(str(getDate), '%B/%Y').strftime('%B')
        year = datetime.datetime.today().strptime(str(getDate), '%B/%Y').strftime('%Y')
        
        next_emi = month+'/'+year
        
        amount = loanrecord[4] / int(duration)

        status = Loan(emp_id).chkloanpaid(loanrecord[0], month, year) # check from loan table if loan has been paid for the month
        if status:
            loan_status = 'Paid'
        else:
            loan_status = 'Unpaid'
        
        emi_info = [loanrecord[12], emp_name, next_emi, amount, loan_status]
        details.append(emi_info)



    return details

