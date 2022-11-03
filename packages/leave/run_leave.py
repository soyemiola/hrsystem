import os
from flask import Blueprint, render_template, request, make_response, jsonify, url_for, redirect, flash
from packages.payroll.reports.report import get_image_file_as_base64_data
from packages.leave.leaveOop import Leave
from packages.functions import fetch_table_record, update_setting, get_table_column
from packages.leave.token import confirm_token, generate_token
import datetime
import pdfkit
from flask_login import current_user, login_required
from packages.leave.sendleave import SendLeave, ConfirmLeave
from packages.employees.userOop import Employee
from packages.leave.leaveOop import leave_status
from packages.run_admin import year_selector


leaves = Blueprint('leaves', __name__, url_prefix='/', template_folder='templates')



@leaves.before_request
def chk_session():
    if not current_user.is_authenticated:
        return redirect(url_for('admin.login', next=request.url))


@leaves.route('/admin/staff-leave', methods=['POST', 'GET'])
def staffleave():
    department_list = fetch_table_record('department')
    years = year_selector()
    get_list = Leave.leavelist()
    stafflist = Employee.fetch_all_record()


    if request.method == 'POST':
        emp_id = request.form['emp_id']
        leavetype = request.form['leavetype']
        days = request.form['days']
        reason = request.form['reason']

        submit_date = datetime.datetime.today().strftime('%Y-%m-%d')
        leave_year = datetime.datetime.today().strftime('%Y')

        proc = Leave.modifyleave(emp_id, leavetype, days, reason, submit_date, leave_year)
        
        if proc == True:
            flash('Leave record updated successfully', 'success')
        else:
            flash('Erorr updating record', 'danger')

        return redirect(url_for('leaves.staffleave'))
    return render_template('leave/staffleave.html', department=department_list, years=years, leave=get_list,
                            emp=stafflist)


@leaves.route('/admin/leaverecord/<emp_id>')
def leaverecord(emp_id):
    lst = Leave.leavestafflist(emp_id=emp_id)
    return render_template('leave/leaverecord.html', details=lst)


@leaves.route('/admin/leavededuction')
def ldeduction():
    deductinfo = Leave.leaveDeduction()
    return render_template('leave/deduction.html', details=deductinfo)



@leaves.route('/admin/leave-request', methods=['POST', 'GET'])
def leave_request():
    year = datetime.datetime.today().strftime('%Y')
    leave_list = Leave.fetch_all_leave(year=year)
    if request.method == 'POST':
        
        try:
            if request.form.get('comment') is not None:
                comment = request.form.get('comment')
            else:
                comment = ''

            emp_id = request.form['inputid']
            mode = int(request.form['mode'])
            leaveid = request.form['leaveid']
            leaveemail = request.form['email'] 

            send = SendLeave.hr_approver(empid=emp_id, getid=leaveid, email=leaveemail, column='hr_action', 
                                            comment=comment, action='accept', mode=mode)
            if send is True:
                flash('Leave Process Successful', 'success')
        except:
            flash('Error processing request', 'danger')
    return render_template('leave/leaverequest.html', leave_list=leave_list)



@leaves.route('/admin/addleave', methods=['POST', 'GET'])
def addleave():
    if request.method == 'POST':
        name = request.form['leavename']
        desc = request.form['leavedescription']
        duration = int(request.form['duration'])
        add_new_type = Leave(name, desc, duration)
        res = add_new_type.createleavetype()

        if res:
            flash(res, 'success')
    return render_template('leave/addleave.html')


@leaves.route('/admin/leavelist')
def leavelist():
    get_list = Leave.leavelist()
    return render_template('leave/leavelist.html', leave_list=get_list)


@leaves.route('/admin/editleave/<get_id>', methods=['POST', 'GET'])
def editleave(get_id):
    leaveinfo = Leave.fetch_leave_type(get_id)
    return render_template('leave/editleave.html', leavelist=leaveinfo)


@leaves.route('/admin/deleteleave/<get_id>', methods=['POST', 'GET'])
def deleteleave(get_id):
    delete_lv = Leave.delete_leave_type(get_id)
    if delete_lv:
        flash('Record Deleted', 'success')
        return redirect(url_for('leaves.leavelist'))


@leaves.route('/admin/updateleave', methods=['POST'])
def updateleave():
    if request.method == 'POST':
        id = int(request.form['id'])
        name = request.form['leavename']
        desc = request.form['leavedescription']
        duration = int(request.form['duration'])

        update_leave = Leave.update(id, name, desc, duration)
        if update_leave:
            flash('Record updated', 'success')
            return redirect(url_for('leaves.leavelist'))

 
@leaves.route('/admin/activelist')
def activeleave():
    chk = datetime.datetime.today().strftime('%Y-%m-%d')
    active = Leave.active('Approved', rdate=chk)
    return render_template('leave/active.html', active=active)


@leaves.app_template_filter()
def days_left(startdate, enddate):
    today = datetime.datetime.today() # today's date
    s_date = datetime.datetime.strptime(startdate, '%Y-%m-%d') # start of leave  date
    if today >= s_date:
        e_date = datetime.datetime.strptime(enddate, '%Y-%m-%d') # end of leave  date
        daysleft = (e_date - today).days
        return daysleft
    else:
       return None
    

@leaves.app_template_filter()
def check(leaveid):
    status = Leave.check_action(leaveid=leaveid)
    if status == 'pending':
        return 1
    elif status == 'accept':
        return 2
    else:
        return None

@leaves.app_template_filter()
def getleavedays(emp_id, leave_name):
    if leave_name.lower() == 'annual leave':
        det = Leave.getLeaverecord(name=leave_name, emp_id=emp_id, mode='annual')
    else:
        det = Leave.getLeaverecord(name=leave_name, emp_id=emp_id, mode='otherleave')
    if det:
        return det


@leaves.route('/admin/requestlist', methods=['POST', 'GET'])
def requestlist():
    if request.method == 'POST':
        leaveid = request.form['id']
        res = Leave.fetch_emp_leave(leaveid)
        return make_response(jsonify(res))
    status = Leave.leavestatus()
    return render_template('leave/status.html', status=status)


@leaves.route('/admin/leaverequestpdf/<leaveid>')
def leaverequestpdf(leaveid):
    res = Leave.fetch_emp_leave(leaveid)
    brandlogo = get_image_file_as_base64_data(os.path.join(os.path.dirname(__file__)+"\\static\\image", "logo.png"))

    render = render_template('leave/leaverequest_pdf.html', emp=res, logo=brandlogo)
    pdf = pdfkit.from_string(render, False)

    response = make_response(pdf)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = 'inline; filename=leave_request_report.pdf'

    return response


@leaves.route('/admin/calendar')
def calendar():
    return render_template('leave/calendar.html')


@leaves.route('/admin/leavecalendar', methods=['POST', 'GET'])
def leavecalendar():
    if request.method == 'GET':
        #print(request.args.get('dept'))
        active_leave = Leave.calendar_leave()
        all_ = []
        for i in active_leave:
            if i[9] == 'Approved':
                bg = '#3c8dbc'
                bc = '#3c8dbc'
            elif i[9] == 'Pending':
                bg = '#2b542c'
                bc = '#2b542c'
            elif i[9] == 'Declined':
                bg = '#dd4b39'
                bc = '#dd4b39'
            elif i[9] == 'Completed':
                bg = '#00a65a'
                bc = '#00a65a'
            else:
                bg = ''
                bc = ''

            leave_event = {
                'id': i[0],
                'title': i[8] + ' on ' + i[2] + ' | ' + i[6] + ' department',
                'start': i[3] + ' 00:00:00',
                'end': i[4] + ' 23:00:00',
                'backgroundColor': bg,
                'borderColor': bc
            }
            all_.append(leave_event)
        return make_response(jsonify(all_))



@leaves.route('/admin/populate-leave', methods=['POST', 'GET'])
def populateleave():
    emp_details = Employee.fetch_all_record()

    for i in emp_details:
        proc = Leave.createleave(emp_id=i[0])

    return make_response(jsonify('Process Successful'))


@leaves.route('/admin/leave-allowance', methods=['POST', 'GET'])
def leaveallowance():
    year = datetime.datetime.today().strftime('%Y')
    allowanceList = Leave.leaveallowance(year=str(year))

    if request.method == 'POST':
        leaveid = request.form['leaveid']
        process = Leave.actionAllowance(value='Yes', leaveid=leaveid, tablename='allowancereceive')
        if process is True:
            return redirect(url_for('leaves.leaveallowance'))

    return render_template('leave/leaveallowance.html', alist=allowanceList)


@leaves.route('/admin/allowance_update', methods=['POST'])
def allowance_update():
    if request.method == 'POST':
        leaveid = request.form['Aleaveid']
        allowanceStat = request.form['allowanceStat']
        status = Leave.actionAllowance(value=allowanceStat, leaveid=leaveid, tablename='allowance')
        if status is True:
            flash('Leave Allowance updated', 'success')
            return redirect(url_for('leaves.requestlist'))

