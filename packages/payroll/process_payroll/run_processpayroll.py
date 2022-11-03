from flask import Blueprint, render_template, request, redirect, url_for, make_response, jsonify, flash, Markup, current_app
from packages.payroll.taxable import Taxable, get_bands
from packages.payroll.taxband import getband
from packages.employees.userOop import Employee
from packages.payroll.process_payroll.salary import Salary
from datetime import datetime
from packages.employees.coop.cooperative import Cooperative
from packages.functions import monthly_submission, all_sum, monthly_sum, resetperc, fetch_table_record, update_setting
import calendar
from flask_login import current_user, login_required
from packages.employees.newuser import create_gcpt
from packages.payroll.empcategory.empOop import Category, converttofloat
from packages.run_admin import year_selector



payroll = Blueprint('payroll', __name__, url_prefix='/', template_folder='templates')


@payroll.before_request
def chk_session():
    if not current_user.is_authenticated:
        return redirect(url_for('admin.login', next=request.url))

       

@payroll.route('/admin/payrun', methods=['POST', 'GET'])
def payrun():
    emp_tax_list = Taxable.taxlist()

    process_all_btn = 1

    if emp_tax_list is None:
        revrtbtn = None
        process_all_btn = None
    else:
        for chk in emp_tax_list:
            if chk[8] == None:
                process_all_btn = None
                break
        
        revrtbtn = 1

    status = request.args.get('status')

    if status == '0':
        flash('Number of work days is required!', 'danger')
    elif status == '1':
        flash('Not set yet!', 'warning')
    elif status == '2':
        flash('Process failed!', 'danger')
    else:
        pass    

    now = datetime.now()
    days = calendar.monthrange(now.year, now.month)[1]

    return render_template('payroll/payrun.html', emp_tax=emp_tax_list, process_all_btn=process_all_btn, revrtbtn=revrtbtn, days=days)


@payroll.route('/admin/processTax/<page>/<get_id>')
def processTax(get_id, page):
    # perform update on account_info 
    emp_tax = Taxable.processtax(get_id)
    if emp_tax[2] == 0:
        flash('Update User Payroll Class', 'danger')
        if page == 'profile':
            return redirect(url_for('users.emp_profile', get_id=get_id))
        else:
            return redirect(url_for('payroll.payrun')) 
    else:
        basic = Taxable.get_taxable(basic=emp_tax[2], OA=emp_tax[3])    
        create_gcpt(gross=basic['Gross'], cra=basic['CRA'], pension=basic['Pension'], totalrelief=basic['Total Relief'], 
                    get_acct_id=get_id)

        emp_gross = float(basic['Gross'])
        emp_relief = float(basic["Total Relief"])
        
        emp_taxable = emp_gross - emp_relief
        emp_process_tax = getband(emp_taxable, emp_gross)

        get_bands(emp_taxable, emp_process_tax, get_id)
        flash('Profile Tax process Successful', 'success')

        if page == 'profile':            
            return redirect(url_for('users.emp_profile', get_id=get_id))
        else:
            return redirect(url_for('payroll.payrun'))


@payroll.route('/admin/payslip', methods=['POST', 'GET'])
def payslip():
    if request.method == 'POST':
        month = datetime.today().strftime('%B')
        year = datetime.today().strftime('%Y')

        emp_id = request.form['parun_id']
        percentage = float(request.form['percentage'])

        try:
            days = request.form['days']
        except:
            flash('Please select number of working days', 'warning')
            return redirect(url_for('payroll.payrun'))

        
        info = Salary.process_salary(emp_id=emp_id, percentage=percentage, days=days, month=month, year=year)
        
        if info == 102:
            flash('Loan repayment process failed', 'danger')
            return redirect(url_for('payroll.payrun'))
        if info == 103:
            flash('Coop loan process failed', 'danger')
            return redirect(url_for('payroll.payrun'))

        return redirect(url_for('payroll.viewpayroll', getid=emp_id))
    return redirect(url_for('payroll.payrun'))


@payroll.route('/admin/payrun/revert/<get_id>/<month>/<year>')
def revert_payroll(get_id, month, year):
    emp_id = get_id
    month = month
    year = year

    revert = Salary.revert_det(emp_id=emp_id, month=month, year=year)

    if revert is True:
        flash('Payroll Record deleted', 'success')
    else:
        flash('Error Reverting Payslip', 'danger')

    return redirect(url_for('payroll.payrun'))


@payroll.route('/admin/revert_all')
def revertall():
    month = datetime.today().strftime('%B')
    year = datetime.today().strftime('%Y')

    all_revert = Salary.revertall(month=month, year=year) 
    if all_revert is True:
        flash('Revert process successful', 'success')
    else:
        flash('Error! Try Again', 'danger')
    return redirect(url_for('payroll.payrun'))


@payroll.route('/admin/processall')
def processall():
    month = datetime.today().strftime('%B')
    year = datetime.today().strftime('%Y')
    now = datetime.now()
    days = calendar.monthrange(now.year, now.month)[1]

    emp_list = Employee.fetch_all_record()

    for i in emp_list:
        get_acct_info = Employee.emp_account_record(emp_id=i[0])
        percentage = get_acct_info[20]

        chk = Salary.chk_process_salary_per_month(i[0], month, year)
        if chk is None:
            try:
                info = Salary.process_salary(emp_id=i[0], percentage=percentage, days=days, month=month, year=year)
            except:
                pass
        else:
            pass
            
    flash('Process completed successfully', 'success')

    return redirect(url_for('payroll.payrun'))

    

@payroll.add_app_template_filter
def two_decimal(value):
    return '{:,.2f}'.format(value)



@payroll.route('admin/viewpayroll/<getid>')
def viewpayroll(getid):
    emp_info = Employee.emp_per_record(getid)
    if emp_info:
        emp_acct = Employee.emp_account_record(getid)
    else:
        return redirect(url_for('payroll.payrun'))
    
    month = datetime.today().strftime('%B')
    year = datetime.today().strftime('%Y')

    details = Salary.get_salary_info(getid, month, year)
    if details:
        finalized = Salary.chk_salary_per_month(getid, month, year)
        return render_template('payroll/payslip.html', info=emp_info, acct=emp_acct, details=details, finalized=finalized)
    else:
        return redirect(url_for('payroll.payrun'))    



@payroll.route('/admin/payinfo/<get_id>')
def payinfo(get_id):
    emp_id = get_id
    emp_info = Employee.emp_per_record(emp_id)
    emp_pension = Employee.emppension(emp_id)
    emp_acct = Employee.emp_account_record(emp_id)
    emp_tax_info = Taxable.get_emp_tax(emp_id)
    emp_loan = 0
    emp_coop_loan = Cooperative.check_loan_details(emp_id)
    emp_coop_loan_deduction = Cooperative.loan_deduction(emp_id)

    return render_template('payroll/payinfo.html', info=emp_info, pension=emp_pension, acct=emp_acct,
                           tax=emp_tax_info, loan=emp_loan, cloan=emp_coop_loan,
                           coop_loan_deduction=emp_coop_loan_deduction)


@payroll.route('/admin/finalise/<get_id>/<month>/<year>/<page>')
def finalise(get_id, month, year, page):
    emp_id = get_id
    
    if page == 'payslip':
        finalize = Salary.finalise(emp_id, month, year)
        if finalize:
            flash('Process successful', 'success')
            page = 'payroll.'+str(page)
            return redirect(url_for(page))
    
    elif page == 'filling':
        finalize = Salary.finalise(emp_id, month, year)
        return redirect(url_for('payroll.filling', finalize='single', month=month, year=year))

    return redirect(url_for('payroll.viewpayroll', getid=emp_id))


@payroll.route('/admin/filling', methods=['POST', 'GET'])
def filling():
    month = datetime.today().strftime('%B')
    year = datetime.today().strftime('%Y')

    if request.method == 'POST':
        filter_month = request.form['month']
        filter_year = request.form['year']

        getDetails = monthly_submission(filter_month, filter_year)
        filters = filter_month, filter_year
    else:
        getDetails = monthly_submission(month, year)
        filters = month , year

    # finalize all
    finalize = request.args.get('finalize')
    finalize_month = request.args.get('month')
    finalize_year = request.args.get('year')
    
    if finalize == 'YES' and finalize_month != '' and finalize_year != '':
        proc = Salary.finalise_all(finalize_month, finalize_year)
        if proc:
            getDetails = monthly_submission(finalize_month, finalize_year)
    
    elif finalize == 'single' and finalize_month != '' and finalize_year != '':
        getDetails = monthly_submission(finalize_month, finalize_year)
    else:
        pass
    


    months = {v: k for k, v in enumerate(calendar.month_name)}
    year = []
    start_year = int(current_app.config['START_YEAR'])
    
    for i in range(3):
        yr = start_year + i
        year.append(yr)
    return render_template('payroll/filling.html', details=getDetails, month=months, year=year, filters=filters)


@payroll.route('/admin/adminreview', methods=['POST', 'GET'])
def review():
    month = datetime.today().strftime('%B')
    year = datetime.today().strftime('%Y')
    
    if request.method == 'POST':
        filter_month = request.form['month']
        filter_year = request.form['year']

        details = all_sum(filter_month, filter_year)
        filters = filter_month, filter_year
    else:
        details = all_sum(month, year)
        filters = month, year

    year_list = year_selector()
    month_list = {v: k for k, v in enumerate(calendar.month_name)}

    return render_template('payroll/review.html', review=details, filters=filters, month=month_list, year=year_list)



@payroll.route('/admin/reviewlist/<month>/<year>', methods=['POST', 'GET'])
def reviewlist(month, year):
    office = fetch_table_record(tablename='branch')

    if request.method == 'POST':
        filter_office = request.form['office']
        emp_list_month = Salary.listper_month(month, year, filter_office)  
        total = None 

    else:
        emp_list_month = Salary.listper_month(month, year)
        total = monthly_sum(month, year)
        filter_office = None


    return render_template('payroll/reviewlist.html', emp_list=emp_list_month, month=month, year=year, total=total, 
                            branch=office, office=filter_office)


@payroll.route('/admin/resetpercentage', methods=['POST', 'GET'])
def resetpercentage():
    perc = request.form['value']
    res = resetperc(perc)
    return make_response(jsonify(res))


@payroll.route('/admin/payroll-adjustment', methods=['POST', 'GET'])
def adjustment():
    if current_user.role != 'AD':
        return redirect(url_for('admin.dashboard'))

    emp = Employee.fetch_all_record()
    details = None

    if request.method == 'POST':
        
            emp_id = request.form['emp_id']
            a_month = request.form['emp_month']
            a_year = request.form['emp_year']

            emp_info = Employee.emp_per_record(emp_id)
            adjust_info = Salary.get_salary_info(emp_id, a_month, a_year)

            if adjust_info:
                details = emp_info, adjust_info
            else:
                msg = Markup("No record found for <b>SELECTED FIELDS</b>")
                flash(msg, 'info')
        

    month = {v: k for k, v in enumerate(calendar.month_name)}
    year = year_selector()
    return render_template('payroll/adjustment.html', emp=emp, year=year, month=month, info=details)


@payroll.route('/admin/process-adjustment', methods=['POST', 'GET'])
def process_adjustment():
    if request.method == 'POST':
        try:
            emp_id = request.form['emp_id']
            month = request.form['adj_month']
            year = request.form['adj_year']
            reason = request.form['reason']
            adj_type = request.form['adj_type']
            adj_salary = request.form['adj_salary']
            date = datetime.today().strftime('%c')

            try:
                proc_adj = Salary.adjustment(emp_id, month, year, reason, adj_type, adj_salary, date)
                if proc_adj:
                    flash(proc_adj, 'success')
                return redirect(url_for('payroll.adjustment_list'))
            except:
                msg = Markup("<b>Error processing request</b> Try Again")
                flash(msg, 'danger')
                return redirect(url_for('payroll.adjustment'))
        except:
            msg = Markup("<b>Error!</b> Please Fill out all fields to process payroll adjustment")
            flash(msg, 'danger')
            return redirect(url_for('payroll.adjustment'))

    else:
        return redirect(url_for('payroll.adjustment'))


@payroll.route('/admin/adjustment-list', methods=['POST', 'GET'])
def adjustment_list():
    adjust_lst = None
    if request.method == 'POST':
        filter_month = request.form['month']
        filter_year = request.form['year']

        adjustment = Salary.adjustment_list(month=filter_month, year=filter_year)
        if adjustment:
            adjust_lst = adjustment
        
        filters = filter_month, filter_year
    else:
        month = datetime.today().strftime('%B')
        year = datetime.today().strftime('%Y')
        adjustment = Salary.adjustment_list(month=month, year=year)
        
        if adjustment:
            adjust_lst = adjustment
        filters = month, year

    
    date = {v: k for k, v in enumerate(calendar.month_name)}
    year = year_selector()


    return render_template('payroll/adjustment-list.html', year=year, month=date, adjust=adjust_lst, filters=filters)


@payroll.route('/admin/edit-adjustment/<empid>/<month>/<year>', methods=['POST', 'GET'])
def edit_adjustment(empid, month, year):
    if not empid:
        return redirect(url_for('admin.dashboard'))
    else:
        info = Salary.adjustment_list(month=month, year=year, empid=empid)

        if request.method == 'POST':
            emp_id = request.form['emp_id']
            month = month
            year = year
            reason = request.form['reason']
            adj_type = request.form['adj_type']
            adj_salary = request.form['adj_salary']
            date = datetime.today().strftime('%c')
            proc_adj = Salary.adjustment(emp_id, month, year, reason, adj_type, adj_salary, date)

            flash('Updated', 'success')
            return redirect(url_for('payroll.adjustment_list'))

        return render_template('payroll/editadjustment.html', info=info)


@payroll.route('/admin/delete-adjust', methods=['POST', 'GET'])
def deleteAdjustment():
    if request.method == 'POST':
        deleteID = request.form['adj_id']
        del_action = Salary.deleteADJ(deleteID=deleteID)
        if del_action:
            flash('Adjustment Deleted Successfully', 'success')
            return redirect(url_for('payroll.adjustment_list'))
        else:
            flash('Error removing Adjustment. Try Again!', 'danger')
            return redirect(url_for('payroll.adjustment_list'))

            

@payroll.route('/admin/tax-information', methods=['POST', 'GET'])
def tax():
    tax = Salary.taxinformation()

    if request.method == 'POST':
        emp_id = request.form['emp_id']
        taxable = request.form['taxable']
        mintax = request.form['mintax']
        highertax = request.form['highertax']
        effective = request.form['effective']
        band1 = request.form['band1']
        band2 = request.form['band2']
        band3 = request.form['band3']
        band4 = request.form['band4']
        band5 = request.form['band5']
        band6 = request.form['band6']
        total = request.form['total']
        
        update_tax = Taxable.taxrecord(emp_id=emp_id, taxable=taxable, mintax=mintax, highertax=highertax, effective_tax=effective, 
                                        band1=band1, band2=band2, band3=band3, band4=band4, band5=band5, band6=band6, total_tax=total)
        if update_tax:
            flash(update_tax, 'success')
            return redirect(url_for('payroll.tax'))

    return render_template('payroll/tax.html', taxinfo=tax)


@payroll.route('/admin/generate_payclass', methods=['POST', 'GET'])
def payclass():
    if request.method == 'POST':
        basic_value = request.form['basic']
        house_allowance = request.form['housing']
        transport_allowance = request.form['transport']
        other_allowance = request.form['other']
        all_allowance = [float(house_allowance), float(transport_allowance), float(other_allowance)]
        total_allowance = sum(all_allowance)

        # generate pay class
        info = Taxable.get_taxable(basic=float(basic_value), OA=total_allowance)
        gross_value = float(info['Gross'])
        relief_value = float(info["Total Relief"])

        taxable_value = gross_value - relief_value
        process_tax = getband(taxable_value, gross_value)

        monthly_pay = ((gross_value/12) - (process_tax['Total_tax']/12) - (info['Pension']/12))
        annual_pay = gross_value - process_tax['Total_tax'] - info['Pension']

        values = info, basic_value, house_allowance, transport_allowance, other_allowance, taxable_value, \
                process_tax, relief_value, monthly_pay, annual_pay
        

        report = values
    else:
        report = None

    return render_template('payroll/payclass.html', report=report)


@payroll.route('/admin/create_class', methods=['POST', 'GET'])
def create_class():
    name = request.form['classname']
    basic = converttofloat(request.form['basic'])
    house = converttofloat(request.form['house_a'])
    transport = converttofloat(request.form['transport_a'])
    other = converttofloat(request.form['other_a'])

    total_allowance = house, transport, other

    new_class = Category.create_new_class(name=name, basic=basic, house_a=house, transport_a=transport, 
                                                other_a=other, total_a=sum(total_allowance))
    
    if new_class:
        flash('New PayClass Created Successfully', 'success')
    else:
        flash('Error creating PayClass. Try Again!', 'danger')


    return redirect(url_for('payroll.payclass'))



@payroll.route('/admin/remittance', methods=['POST', 'GET'])
def remittance():
    dept_list = fetch_table_record(tablename='department')
    return render_template('payroll/remittance.html', department=dept_list)
