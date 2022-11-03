from flask import Blueprint, render_template, make_response, jsonify, request, flash, redirect, url_for, current_app
from packages.functions import monthly_sum, fetch_table_record
from packages.payroll.process_payroll.salary import Salary
import base64
import pdfkit
import os
from packages.employees.userOop import Employee
import calendar
from datetime import datetime
import datetime
from flask_login import current_user, login_required
from packages.adminOop import Report
from packages.run_admin import year_selector


report = Blueprint('report', __name__, url_prefix='/', template_folder='templates', static_folder='static')



@report.before_request
def chk_session():
    if not current_user.is_authenticated:
        return redirect(url_for('admin.login', next=request.url))
        

@report.route('/pdf_template/<month>/<year>')
def pdf_template(month, year):
    total = monthly_sum(month, year)
    filename = month+'_payroll_review.pdf'
    
    return render_template('reports/report-pdf.html', month=month, year=year, info=total)
    
    


@report.route('/admin/reports', methods=['POST', 'GET'])
def reports():
    info = None
    if request.method == 'POST':
        try:
            emp_id = request.form['emp_name']
            month = request.form['month']
            year = request.form['year']
        except KeyError as e:
            flash('Invalid query selection. Try Again', 'warning')
            return redirect(url_for('report.reports'))
        


        details = Salary.emp_month_report(emp_id, month, year)
        if details:
            info = details
        else:
            flash('No Record Found', 'danger')
    emp_list = Employee.fetch_all_record()
    
    month = {v: k for k, v in enumerate(calendar.month_name)}
    year = year_selector()
    
        
    return render_template('reports/report.html', emp_list=emp_list, year=year, month=month, details=info)
   

@report.route('/admin/payrollyearreport', methods=['POST'])
def payrollyearreport():
    emp_id = request.form['id']
    year = request.form['year']

    user_report = Salary.emp_year_report(emp_id, year)
    if user_report is None:
        report_ = ''
        return make_response(jsonify(report_))
    else:
        report_ = user_report
        get_sum = Salary.emp_year_sum(emp_id)
        if get_sum is None:
            get_sum = ''

        return make_response(jsonify(report_, get_sum))


@report.route('/empReport/<getid>/<month>/<year>')
def empReport(getid, month, year):
    _month = month
    user_info = Employee.emp_per_record(getid)
    user_acct_info = Employee.emp_account_record(getid)
    salary_info = Salary.emp_month_report(getid, month, year)
    
    return render_template('reports/empReport.html', info=user_info, acct_info=user_acct_info, salary=salary_info)


@report.route('/admin/yearreport', methods=['POST', 'GET'])
def yearreport():
    info = None
    if request.method == 'POST':
        try:
            emp_id = request.form['id']
            year = request.form['year']
        except KeyError as e:
            flash('Invalid query selection. Try Again', 'warning')
            return redirect(url_for('report.yearreport'))
       

        user_report = Salary.emp_year_report(emp_id, year)
        if user_report == None:
            flash('No record found', 'info')
        else:
            report = user_report
            get_sum = Salary.emp_year_sum(emp_id)
            if get_sum == None:
                get_sum = None
            info = {'info': report, 'sum': get_sum }

    emp_list = Employee.fetch_all_record()
    year = year_selector()
    
    return render_template('reports/yearreport.html', emp_list=emp_list, year=year, details=info)


@report.route('/admin/empYearreport', methods=['POST', 'GET'])
def empYearreport():
    emp_id = request.args.get('id')
    year = request.args.get('year')
    empDetails = Employee.emp_per_record(emp_id)
    user_acct_info = Employee.emp_account_record(emp_id)
    reportDetails = Salary.emp_year_report(emp_id, year)
    emp_sum = Salary.emp_year_sum(emp_id)
    
    return render_template('reports/empYearreport.html', empDetails=empDetails, acct_info=user_acct_info,
                               record=reportDetails, total=emp_sum, year=year)

    


@report.route('/admin/bankreport', methods=['POST', 'GET'])
def bankreport():
    banks = fetch_table_record('bank_name')
    year = year_selector()

    dsp_report = ''
    alertmsg = ''
    dsp_summary = ''

    if request.method == 'POST':
        try:
            bank_selected = request.form['bankname']
            month_selected = request.form['month']
            year_selected = request.form['year']

            if bank_selected == 'All Banks':
                summary = Salary.sum_all_bank_report(month_selected, year_selected)
                fetch_report = Salary.all_bankreport(month_selected, year_selected)
                
            else:
                summary = Salary.sum_bank_report(bank_selected, month_selected, year_selected)
                fetch_report = Salary.bankreport(bank_selected, month_selected, year_selected)

            
            if len(fetch_report) != 0:
                if len(summary) != 0:
                    dsp_report = fetch_report
                    dsp_summary = {
                        'summary': summary,
                        'bankname': bank_selected,
                        'month': month_selected,
                        'year': year_selected
                    }
            else:
                flash('No Record found', 'info')
        except KeyError as e:
            tab = request.args.get('schedule')
            if tab == 'A':
                schedule = tab
            elif tab == 'B':
                schedule = tab 
            else:
                schedule = None

            flash('Invalid query selection. Try Again', 'warning')
            return redirect(url_for('report.bankreport', schedule=tab))

    tab = request.args.get('schedule')

    month = {v: k for k, v in enumerate(calendar.month_name)}
    
    if tab == 'A':
        return render_template('reports/bankreportA.html', banks=banks, months=month, years=year, dsp=dsp_report,
                           alert=alertmsg, Tsummary=dsp_summary)

    elif tab == 'B':
        return render_template('reports/bankreportB.html', banks=banks, months=month, years=year, dsp=dsp_report,
                           alert=alertmsg, Tsummary=dsp_summary)
    else:
        return render_template('reports/bankreport.html', banks=banks, months=month, years=year, dsp=dsp_report,
                                alert=alertmsg, Tsummary=dsp_summary)


@report.route('/admin/pfareport', methods=['POST', 'GET'])
def pfareport():
    pfa = fetch_table_record('pensioncomp')
    month = {v: k for k, v in enumerate(calendar.month_name)}
    year = year_selector()

    dsp_report = ''
    alertmsg = ''
    dsp_summary = ''
    total = 0

    if request.method == 'POST':
        try:
            pfa_selected = request.form['pfaname']
            month_selected = request.form['month']
            year_selected = request.form['year']

            if pfa_selected == 'All PFA':
                summary = Salary.sum_all_pfa_report(month_selected, year_selected)
                fetch_report = Salary.all_pfareport(month_selected, year_selected)
            else:
                summary = Salary.sum_pfa_report(pfa_selected, month_selected, year_selected)
                fetch_report = Salary.pfareport(pfa_selected, month_selected, year_selected)

            if len(fetch_report) != 0:
                if len(summary) != 0:
                    dsp_report = fetch_report
                    dsp_summary = {
                        'summary': summary,
                        'pfaname': pfa_selected,
                        'month': month_selected,
                        'year': year_selected
                    }
                    total = float(dsp_summary['summary'][1]) + float(dsp_summary['summary'][2])
                    
            else:
                flash('No record found', 'info')
        except KeyError as e:
            flash('Invalid query selection. Try Again', 'warning')
            return redirect(url_for('report.pfareport'))



    return render_template('reports/pfareport.html', pfas=pfa, months=month, years=year, dsp=dsp_report,
                           alert=alertmsg, Tsummary=dsp_summary, total=total)


@report.route('/admin/paye', methods=['POST', 'GET'])
def paye():
    paye = None
    if request.method == 'POST':
        try:
            get_state = request.form['state']
            get_month = request.form['month']
            get_year = request.form['year']

            if get_state == 'All state':
                paye_record = Salary.payereport_all(get_month, get_year)
                sum_paye_record = Salary.sum_all_tax_report(get_month, get_year)
            else:
                paye_record = Salary.payereport(get_state, get_month, get_year)
                sum_paye_record = Salary.sum_tax_report(get_state, get_month, get_year)
            

            if len(paye_record) == 0:
                flash('No Redcord found', 'info')
            else:
                paye = {
                    'eachrecord': paye_record,
                    'sum': sum_paye_record,
                    'state': get_state,
                    'month': get_month,
                    'year': get_year
                }
        except KeyError as e:
            flash('All fileds required', 'warning')
            return redirect(url_for('report.paye'))


    states = ('Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa', 'Benue', 'Borno', 'Cross', 'Delta', 'Ebonyi',
              'Edo', 'Ekiti', 'Enugu', 'FCT', 'Gombe', 'Imo', 'Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Kogi',
              'Kwara', 'Lagos', 'Nassarawa', 'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo', 'Plateau', 'Rivers', 'Sokoto',
              'Taraba', 'Yobe', 'Zamfara')

    month = {v: k for k, v in enumerate(calendar.month_name)}
    year = year_selector() 


    return render_template('reports/paye.html', state=states, months=month, years=year, payeinfo=paye)


@report.route('/paye-pdf/<state>/<month>/<year>')
def paye_pdf(state, month, year):
    if state == 'All state':
        paye_record = Salary.payereport_all(month, year)
        sum_paye_record = Salary.sum_all_tax_report(month, year)
    else:
        paye_record = Salary.payereport(state, month, year)
        sum_paye_record = Salary.sum_tax_report(state, month, year)    

    filename = state + '_paye_' + month + '_' + year + '.pdf'
    
    return render_template('reports/paye-pdf.html', list=paye_record, sum_list=sum_paye_record)
    


@report.route('/bankreport-pdf/<bank>/<month>/<year>')
def bank_report_pdf(bank, month, year):
    if bank == 'All Banks':
        total = Salary.sum_all_bank_report(month, year)
        each_list = Salary.all_bankreport(month, year)
    else:
        total = Salary.sum_bank_report(bank, month, year)
        each_list = Salary.bankreport(bank, month, year)

    schedule = request.args.get('schedule')
    if schedule == 'A':
        schedule25 = 1
        schedule75 = None
    elif schedule == 'B':
        schedule25 = None
        schedule75 = 1
    else:
        schedule25 = None
        schedule75 = None

    filename = bank + '_Report_' + month + '_' + year + '.pdf'
    
    return render_template('reports/bankreport-pdf.html', list=each_list, sum_list=total, 
                                schedule25=schedule25, schedule75=schedule75)
    


@report.route('/pfareport-pdf/<name>/<month>/<year>')
def pfa_report_pdf(name, month, year):
    if name == 'All PFA':
        pfa_total = Salary.sum_all_pfa_report(month, year)
        pfa_list = Salary.all_pfareport(month, year)
    else:
        pfa_total = Salary.sum_pfa_report(name, month, year)
        pfa_list = Salary.pfareport(name, month, year)
    

    total = float(pfa_total[1]) + float(pfa_total[2])
    filename = name + '_Report_' + month + '_' + year + '.pdf'
    
    return render_template('reports/pfareport-pdf.html', list=pfa_list, sum_list=pfa_total,
                             total=total)
    
    


@report.add_app_template_filter
def schedule(value, percent):
    amount = float(value) / 100
    sch = amount * int(percent)
    return sch


@report.route('/staff-info-pdf')
def staffpdf():
    stafflist = Employee.stafflist()
    filename = 'staff information.pdf'
    
    return render_template('reports/staffpdf.html', staff=stafflist)



@report.route('/operation-report/<mode>/<date>')
def operation_pdf(mode, date):
    filename = mode+' '+date+'.pdf'
    
    opx = Report.operation(date=date, category=mode)

    info = [opx]

    return render_template('reports/operation-pdf.html', info=info, mode=mode)
    

@report.route('/admin/payroll-graph-view', methods=['POST', 'GET'])
def payrollgraph():
    return render_template('reports/payrollgraph.html')




def get_image_file_as_base64_data(filepath: str) -> str:
    with open(filepath, 'rb') as image_file:
        return base64.b64encode(image_file.read()).decode()