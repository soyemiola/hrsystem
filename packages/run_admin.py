from flask import Blueprint, render_template, flash, redirect, url_for, request, current_app, make_response, jsonify, session
from packages import bcrypt
from flask_login import login_user, current_user, logout_user, login_required
from packages.adminOop import Operations, Report, Birthday
from packages.models import Admin
from packages.forms import Login, Newuser, New_staff
from datetime import date, timedelta
import datetime
import calendar
from packages.functions import salary, System_settings, update_setting
from packages.leave.sendleave import SendLeave, ConfirmLeave
from packages.leave.token import generate_token, confirm_token
from packages.graph import servingterm, getterm, graphy, engaging_emp
from dateutil.relativedelta import relativedelta
from packages.attendance.attendanceOop import attendance
import socket


admin = Blueprint('admin', __name__, url_prefix='/', template_folder='templates')


    
def loginTime(email):
    hostname = socket.gethostname()
    ipaddress = socket.gethostbyname(hostname)
    access_time = datetime.datetime.today().strftime('%d-%B-%Y %H:%M:%S')
    path = current_app.config['LOGIN_LOG']

    try:
        with open(path+'adminlog.csv', 'a') as f:
            f.write(f'{email},{hostname},{ipaddress},{access_time}\n') 
    except FileNotFoundError as e:
        print('This is it')
    else:
        pass
    finally:
        pass   
    


def year_selector():
    year_list = list()
    current_year = datetime.datetime.today().strftime("%Y")
    start_year = int(current_app.config['START_YEAR'])

    year_range = (int(current_year) - int(start_year)) + 1

    for i in range(int(year_range)):
        yr = start_year + i
        year_list.append(yr)

    return year_list


@admin.route("/admin/login", methods=['POST', 'GET'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('admin.dashboard'))

    login = Login()

    return render_template('admin/login.html', form=login)



@admin.route('/admin/loginprocess', methods=['POST', 'GET'])
def admin_login_proc():
    if request.method == 'POST':
        login = Login()
        if login.validate_on_submit():
            user = Admin.query.filter_by(email=login.email.data).first()
            if user:
                if user.status == 0:
                    flash('Access Denied', 'danger')
                    return redirect(url_for('admin.login'))
                else:
                    if user and bcrypt.check_password_hash(user.password, login.password.data):
                        login_user(user, remember=login.remember.data)
                        next_page = request.args.get('next')
                        loginTime(email=login.email.data)

                        session['admin_user'] = True
                        return redirect(next_page) if next_page else redirect(url_for('admin.dashboard'))
                    else:
                        flash('Login Unsuccessful. Please check email and password and Try Again!', 'danger')
                        return redirect(url_for('admin.login'))

            else:
                flash('No Login Details Found', 'danger')
                return redirect(url_for('admin.login'))
    else:
        return redirect(url_for('admin.login'))




@admin.route("/admin/logout")
@login_required
def logout():
    logout_user()
    session.pop('admin_user')
    return redirect(url_for('admin.login'))



@admin.route('/admin/viewprofile/<emp_user_id>')
def viewUserProfile(emp_user_id):
    from flask_login import login_user, logout_user
    from hr_application.admin.employees.userOop import Employee 

    if emp_user_id:
        openProfile = Employee.viewUserAccount(userid=emp_user_id)
        if openProfile:
            logout_user()
            try:
                session.pop('admin_user')
            except:
                pass

            login_user(openProfile)
            session['user'] = True
            return redirect(url_for('user_in.home'))
        else:
            session['user'] = False
            flash('No User found', 'danger')

    return render_template('users/viewprofile.html')


@admin.route("/admin/adduser", methods=['POST', 'GET'])
def adduser():
    newuser = Newuser()
    if newuser.validate_on_submit():
        exist = Newuser().validate_email(newuser.email.data)
        if exist == True:
            flash('Sorry email already exist', 'danger')
        else:
            hashed_password = bcrypt.generate_password_hash(newuser.password.data).decode('utf-8')
            created = datetime.datetime.today().strftime('%c')
            if newuser.role.data == 'Administrator':
                role = 'AD'
            elif newuser.role.data == 'Managing Director':
                role = 'MD'
            else:
                role = 'OB'

            add_user = Operations(email=newuser.email.data, password=hashed_password).adduser(newuser.firstname.data,
                                                                                              newuser.lastname.data,
                                                                                              created,
                                                                                              role)
            if add_user:
                flash('New Admin User Created', 'success')
    return render_template('adduseradmin.html', form=newuser)


@admin.route("/admin/emoloyment-form/new-intake", methods=['POST', 'GET'])
def newstaff():
    staff = New_staff()
    is_complete = False
    if staff.validate_on_submit():
        new_input = Operations.pre_reg(name=staff.name.data, state=staff.state.data, address=staff.address.data,
                                       city=staff.city.data,
                                       mobile=staff.mobile.data, bankname=staff.bank_name.data,
                                       account=staff.acct_num.data,
                                       taxnumber=staff.tax.data, pensioncomp=staff.pension.data,
                                       pensionnum=staff.pension_num.data)
        if new_input is True:
            is_complete = True
            flash('Registration Succesful', 'success')
        else:
            is_complete = False
            flash('Submission failed. Try Again!', 'danger')
    return render_template('newintake.html', form=staff, is_complete=is_complete)



@admin.route('/admin/dashboard')
@login_required
def dashboard():
    year = datetime.datetime.today().strftime('%Y')

    employees = Operations.all_employees()
    active = Operations.active_employees()
    leave_request = Operations.leave_request()
    onleave = Operations.onleave(date=datetime.datetime.today().strftime('%Y-%m-%d'))

    info = {
        'employees': employees[0],
        'active': active[0],
        'leave': leave_request[0],
        'onleave': onleave[0]
    }

    
    workedfor = salary(column_name='workedfor', year=year)
    
    # Payroll graphical representation
    legend = 'Monthly Payroll Data'
    workedfor_labels = []
    workedfor_values = []

    if workedfor:
        for det in workedfor:
            workedfor_labels.append(det[0])
            workedfor_values.append(det[1])

    labels = workedfor_labels
    values = workedfor_values

    if len(labels) == 0:
        labels = None
        values = None
    else:
        labels = labels
        values = values


    # Performance graphical representation
    performance = Operations.performance_score()
    perform_label = []
    peform_values = []

    for i in performance:
        name = i[0].split(' ', 1)[0]
        perform_label.append(name)
        peform_values.append(i[6])
    

    performance = [perform_label, peform_values]

    if len(performance[1]) == 0:
        performance = None
    else:
        performance = performance


    # demograph
    gender = graphy(parameter='gender')
    if len(gender) == 0:
        gender = None
    else:
        gender = gender

    geolocation = graphy(parameter='state')
    if len(geolocation) == 0:
        geolocation == None
    else:
        geolocation = geolocation

    # turnover
    terms = servingterm.staff_turnover()
    if terms:
        terms = terms
    else:
        terms = None


    # birthday notice
    emplist = Operations.users()
    birthday = Birthday(stafflist=emplist).celebrants()

    if birthday is None or len(birthday) == 0:
        birthday = None 

    return render_template('admin/dashboard.html', info=info, labels=labels, values=values, legend=legend, year=year,
                           performance=performance, gender=gender, geolocation=geolocation, terms=terms, birthday=birthday)



@admin.route('/confirm/<leave_id>/<email>/<level>/<mode>/<auth>')
def confirm(leave_id, email, level, mode, auth):
    process = ConfirmLeave(leaveid=leave_id, email=email, leave_level=level, leave_mode=mode, auth=auth).process()
    if process == 'decline':
        return redirect(
            url_for('admin.leavedeclined', authorization=generate_token('leave_decline_comment'), getlevel=level,
                    getid=leave_id))
    if process == True:
        return render_template('leave/successpage.html')


@admin.route('/leaveprocess/<authorization>/<getlevel>/<getid>', methods=['POST', 'GET'])
def leavedeclined(authorization, getlevel, getid):
    code = confirm_token(authorization)
    level = confirm_token(getlevel)
    leaveid = confirm_token(getid)

    if bcrypt.check_password_hash(current_app.config['LEAVE_URL_LINK'], code) is not True:
        return render_template('empUser/authorized.html')
    else:
        return render_template('empuser/decline.html', authorization=authorization, level=level, leaveid=leaveid)


@admin.route('/leaveprocess/response/<authorization>', methods=['POST', 'GET'])
def leaveresponse(authorization):
    if request.method == 'POST':
        comment = request.form['comment']
        level = request.form['level']
        leaveid = request.form['leaveid']

        # update leavenotify table
        decline = ConfirmLeave.decline(leaveid=leaveid, level=level, comment=comment)
        if decline == 1:
            flash('Response Already Taken', 'info')
        elif decline == True:
            flash('Comment Received', 'success')
        else:
            flash('Process Failed! Try Again', 'danger')

        return redirect(url_for('admin.leavedeclined', authorization=authorization,
                                getlevel=generate_token(level), getid=generate_token(leaveid)))


@admin.route('/admin/updatepassword', methods=['POST', 'GET'])
def password():
    if request.method == 'POST':
        current_pass = request.form['password']
        new_pass = str(request.form['newpassword'])
        confirm_new_pass = str(request.form['cnewpassword'])

        active_pass = bcrypt.check_password_hash(current_user.password, current_pass)
        if active_pass is False:
            flash('Current password Incorrect! Try Again', 'warning')
            return redirect(url_for('admin.password', user_id=current_user.id))

        if new_pass != confirm_new_pass:
            flash('New password does not Match', 'danger')
            return redirect(url_for('admin.password', user_id=current_user.id))
        else:
            password = bcrypt.generate_password_hash(new_pass).decode('utf-8')
            update = Operations.update_pass(new_password=password, getid=current_user.id)
            if update is True:
                flash('Password updated successfully', 'success')
                return redirect(url_for('admin.password', user_id=current_user.id))

    return render_template('admin/pass.html')


@admin.route('/admin/adminusers', methods=['POST', 'GET'])
def adminusers():
    users = Operations.adminusers()

    if request.method == 'POST':
        admin_id = request.form['id']
        status = request.form['status']
        update = Operations.updateadminuser(columnname='status', columnvalue=status, adminid=admin_id)
        if update:
            return make_response(jsonify(update))

    return render_template('admin/adminuser.html', users=users, reset_code=generate_token('yes_reset#password'))


@admin.route('/admin/adminrole', methods=['POST', 'GET'])
def adminopz():
    reset = request.args.get('resetpass')
    empid = request.args.get('adminid')

    if reset:
        if confirm_token(reset) == 'yes_reset#password':
            password = bcrypt.generate_password_hash('Passw0rd1').decode('utf-8')
            update = Operations.updateadminuser(columnname='password', columnvalue=password, adminid=empid)
            if update == True:
                flash('Password Updated', 'success')
                return redirect(url_for('admin.adminusers'))
        else:
            flash('Authentication failed', 'danger')
            return redirect(url_for('admin.adminusers'))

    if request.method == 'POST':
        adminid = request.form['adminId']
        role = request.form['role']

        update = Operations.updateadminuser(columnname='role', columnvalue=role, adminid=adminid)
        if update == True:
            flash('Role Update', 'success')
            return redirect(url_for('admin.adminusers'))
        else:
            flash('Error Updating', 'danger')
            return redirect(url_for('admin.adminusers'))


@admin.route('/handoverreport', methods=['POST', 'GET'])
def handover_report():   
    
        year = datetime.datetime.today().strftime('%Y')
        today = datetime.datetime.today().strftime('%d-%m-%Y')

        draft_info = None

        # fetch record
        if request.method == 'POST' and request.form['submit'].lower() == 'fetch':
            email = request.form['email']
            shift = request.form['shift']
            date = request.form.get('date')

            if date == '':
                date = datetime.datetime.today().strftime('%Y-%m-%d')

            draft_info = Report.drafthandOver(email, shift, date)
            

            if not draft_info:
                flash("No Record found", "info")
                return redirect(url_for('admin.handover_report'))

        
        if request.method == 'POST':
            date = request.form.get('date')
            name = request.form['name']
            email = request.form['email'].lower()
            shift = request.form['shift']

            item = request.form.getlist('item')
            pnr = request.form.getlist('pnr')
            clientname = request.form.getlist('clientname')
            future_date = request.form.getlist('future')
            details = request.form.getlist('details')
            category = 'Handover'
            h_draft_id = request.form.get('h_draft_id')

            a_item = request.form.getlist('a_item')
            a_pnr = request.form.getlist('a_pnr')
            a_ticket = request.form.getlist('a_ticket')
            a_clientname = request.form.getlist('a_clientname')
            a_details = request.form.getlist('a_details')
            a_category = 'Activity'
            a_draft_id = request.form.get('a_draft_id')

            mailcopy = request.form.get('mailcopy')

            send_status = request.form['submit']

            info = [date, name, email, shift, pnr, details, a_pnr, a_ticket, a_details, item, 
                        a_item, clientname, a_clientname, future_date]



            if send_status.lower() == 'draft':
                handover_process = Report(info=info, category=category).savereport(pnr=pnr, details=details, clientname=clientname, 
                                                                                    status='draft', future=future_date, draftID=h_draft_id)

                activity_process = Report(info=info, category=a_category).savereport(pnr=a_pnr, details=a_details, 
                                                                                        clientname=a_clientname, status='draft',
                                                                                        ticket=a_ticket, draftID=a_draft_id)

                flash('Saved as Draft', 'success')
                draft_info = Report.drafthandOver(email, shift, date)
                
            
            elif send_status.lower() == 'send':                
                
                if mailcopy == 'Yes':
                    send_copy = email
                else:
                    send_copy = None           
            

                sendmail = Report(info=info, subject='Handover Report', sendcopy=send_copy).process()
                if sendmail == True:
                    handover_process = Report(info=info, category=category).savereport(pnr=pnr, details=details, clientname=clientname, 
                                                                                        status='Send', future=future_date, draftID=h_draft_id)

                    activity_process = Report(info=info, category=a_category).savereport(pnr=a_pnr, details=a_details, clientname=a_clientname,
                                                                                            status='Send', ticket=a_ticket, draftID=a_draft_id)

                    flash('Report submitted successfully', 'success')
                    return redirect(url_for('admin.handover_report'))
                else:
                    flash('Error Sending report', 'danger')
                    return redirect(url_for('admin.handover_report'))

        return render_template('handover_report.html', today=today, year=year, info=draft_info)



@admin.route('/monitoryreport/', methods=['POST', 'GET'])
def qa_report():
        year = datetime.datetime.today().strftime('%Y')
        today = datetime.datetime.today().strftime('%d-%m-%Y')

        draft_info = None

        # fetch record
        if request.method == 'POST' and request.form['submit'].lower() == 'fetch':
            email = request.form['email']
            shift = request.form['shift']
            date = datetime.datetime.today().strftime('%Y-%m-%d')

            draft_info = Report.draftQA(email, shift, date)

            if not draft_info:
                flash("No Record found", "info")

        if request.method == 'POST':
            # try:
                date = datetime.datetime.today().strftime('%Y-%m-%d')
                name = request.form['name']
                email = request.form['email']
                time = request.form['time']
                shift = request.form['shift']

                item = request.form.getlist('item')
                details = request.form.getlist('details')
                resolution = request.form.getlist('resolution')
                category = 'Issues'
                i_draft_id = request.form.get('i_draft_id')

                e_item = request.form.getlist('e_item')
                e_details = request.form.getlist('e_details')
                escalation = request.form.getlist('escalation')
                e_category = 'Escalation'
                e_draft_id = request.form.get('e_draft_id')

                c_item = request.form.getlist('c_item')
                c_details = request.form.getlist('c_details')
                consultant = request.form.getlist('consultant')
                c_category = 'Compliment'
                c_draft_id = request.form.get('c_draft_id')
                

                mailcopy = request.form.get('mailcopy')
                send_status = request.form['submit']
                

                info = [date, name, email, shift, time, details, resolution, e_details, escalation, c_details, consultant, item, e_item, c_item]

                
                if send_status.lower() == 'draft':
                    issues = Report(info=info, category=category).saveqareport(name=name, email=email, postdate=date, shift=shift, 
                                                                                resumetime=time, category=category, 
                                                                                details=details, rsc_tab=resolution, status='draft',
                                                                                draftID=i_draft_id)

                    escalation = Report(info=info, category=e_category).saveqareport(name=name, email=email, postdate=date, 
                                                                                        shift=shift, resumetime=time, 
                                                                                        category=e_category, details=e_details, 
                                                                                        rsc_tab=escalation, status='draft',
                                                                                        draftID=e_draft_id)

                    compliment = Report(info=info, category=c_category).saveqareport(name=name, email=email, postdate=date, 
                                                                                        shift=shift, resumetime=time, 
                                                                                        category=c_category, details=c_details, 
                                                                                        rsc_tab=consultant, status='draft',
                                                                                        draftID=c_draft_id)
                    flash('Saved as Draft', 'success')
                    draft_info = Report.draftQA(email, shift, date)

                elif send_status.lower() == 'send': 
                    if mailcopy == 'Yes':
                        send_copy = email
                    else:
                        send_copy = None

                    sendmail = Report(info=info, subject='Quality Assurance Report', sendcopy=send_copy).process(html='QA')
                    if sendmail == True:
                        issues = Report(info=info, category=category).saveqareport(name=name, email=email, postdate=date, shift=shift, 
                                                                                    resumetime=time, category=category, 
                                                                                    details=details, rsc_tab=resolution, status='Send', 
                                                                                    draftID=i_draft_id)

                        escalation = Report(info=info, category=e_category).saveqareport(name=name, email=email, postdate=date, 
                                                                                            shift=shift, resumetime=time, 
                                                                                            category=e_category, details=e_details, 
                                                                                            rsc_tab=escalation, status='Send', 
                                                                                            draftID=e_draft_id)

                        compliment = Report(info=info, category=c_category).saveqareport(name=name, email=email, postdate=date, 
                                                                                            shift=shift, resumetime=time, 
                                                                                            category=c_category, details=c_details, 
                                                                                            rsc_tab=consultant, status='Send', 
                                                                                            draftID=c_draft_id)

                        flash('Report submitted successfully', 'success')
                        return redirect(url_for('admin.qa_report'))
                    else:
                        flash('Error Sending report', 'danger')
                        return redirect(url_for('admin.qa_report'))


            # except:
            #     return redirect(url_for('admin.qa_report'))
           
                

        return render_template('qa_report.html', today=today, year=year, info=draft_info)


@admin.route('/callcenterreport', methods=['POST', 'GET'])
def callcenterreport():
        year = datetime.datetime.today().strftime('%Y')
        today = datetime.datetime.today().strftime('%d-%m-%Y')

        if request.method == 'POST':
            try:
                date = datetime.datetime.today().strftime('%Y-%m-%d')
                name = request.form['name']
                email = request.form['email']
                shift = request.form['shift']
                time = request.form['time']
                category = 'Call Center Handover'

                c_item = request.form.getlist('c_item')
                c_cust_name = request.form.getlist('c_cust_name')
                c_cust_num = request.form.getlist('c_cust_num')
                c_cust_reachable = request.form.getlist('c_cust_reachable')
                c_cust_feedback = request.form.getlist('c_cust_feedback')

                mailcopy = request.form.get('mailcopy')
                if mailcopy == 'Yes':
                    send_copy = email
                else:
                    send_copy = None

                info = [date, name, email, shift, time, c_item, c_cust_name, c_cust_num, c_cust_reachable, c_cust_feedback]

                sendmail = Report(info=info, subject=category, sendcopy=send_copy).process(html='Call center')
                if sendmail == True:
                    handover_process = Report(info=info, category=category).saveccreport(cust_name=c_cust_name, cust_num=c_cust_num, \
                                                                                            cust_reacable=c_cust_reachable, \
                                                                                            cust_feedback=c_cust_feedback)

                    flash('Report submitted successfully', 'success')
                    return redirect(url_for('admin.callcenterreport'))
                else:
                    flash('Error Sending report', 'danger')
                    return redirect(url_for('admin.callcenterreport'))
            except:
                flash('Error! Try Again', 'danger')
                return redirect(url_for('admin.callcenterreport'))
                

        return render_template('callcenter.html', today=today, year=year)


@admin.route('/admin/<department>/report', methods=['POST', 'GET'])
@login_required
def operation(department):
    dept = department.lower()
    today = datetime.datetime.today().strftime('%Y-%m-%d')
    
    if dept == 'operation':
        handover = Report.operation(date=today, category='Handover')
        activity = Report.operation(date=today, category='Activity')

        info = [handover, activity]
        filter_date = None

        if request.method == 'POST' :
            date = request.form['date']
            handover = Report.operation(date=date, category='Handover')
            activity = Report.operation(date=date, category='Activity')

            info = [handover, activity]
            filter_date = date

        return render_template('admin/operation.html', info=info, today=today, filter_date=filter_date, department=department)

    elif dept == 'it':
        info = Report.it_report(date=today)

        if request.method == 'POST':
            date = request.form['date']
            info = Report.it_report(date=date)

        return render_template('admin/operation.html', department=department, info=info)
    
    elif dept == 'comms':
        info = Report.commsreport(today)

        if request.method == 'POST':
            date = request.form['date']
            info = Report.commsreport(date=date)

        return render_template('admin/commsreport.html', department=department, info=info, today=today)


@admin.route('/visareport')
def visareport():
    today = datetime.datetime.today().strftime('%d-%m-%Y')
    return render_template('visareport.html', today=today)

    


@admin.add_app_template_filter
def year_duration(date):
    try:
        now = datetime.datetime.today()
        date = datetime.datetime.strptime(date, "%Y-%m-%d")
        rdelta = relativedelta(now, date)

        if rdelta.years < 1:
            label = 'year'
        else:
            label = 'years'

        if rdelta.days > 1:
            days = 'days'
        else:
            days = 'day'

        return '{} {} and {} month {} {}'.format(rdelta.years, label, rdelta.months, rdelta.days, days)

    except:
        pass



@admin.add_app_template_filter
def honours_year(size_range):
    emp_engage = engaging_emp(size_range=size_range)
    return emp_engage


# //- S Y S T E M  S E T T I N G S --// #

@admin.route('/admin/settings')
@login_required
def settings():
    setting_stat = System_settings.settings()
    hr_list = Operations.getlist(department='Human Resources & Admin')
    toplevel = Operations.getlist(department=None, toplevel=True)

    return render_template('admin/settings.html', setting=setting_stat, hr_list=hr_list, toplevel=toplevel)



@admin.route('/admin/updatesetting', methods=['POST', 'GET'])
def updatesetting():
    name = request.form['name']
    value = request.form['value']
    update = update_setting(name, value)
    return make_response(jsonify(update))



@admin.route('/admin/backupnow', methods=['POST'])
def backupnow():
    import gzip
    import subprocess

    if request.method == 'POST':        
        
        with gzip.open('backup.gz', 'wb') as f:
          popen = subprocess.Popen(cmd, stdout=subprocess.PIPE, universal_newlines=True)
          
          for stdout_line in iter(popen.stdout.readline, ""):
            f.write(stdout_line.encode('utf-8'))
          
          popen.stdout.close()
          popen.wait()
        
        return make_response(jsonify(1))


# //-- END SYSTEM SETTINGS --// #


# @leaves.route('/admin/leavesetting', methods=['POST', 'GET'])
# def setting():
#     fetchsetting = fetch_table_record('oops')
    
#     if len(fetchsetting) == 0 or fetchsetting[0][7] is None:
#         fetchsetting = None

#     hr_list = Leave.hr_list()
    
#     if request.method == 'POST':
#         name = request.form['name']
#         value = request.form['value']
#         update = update_setting(name, value)
        
#         return make_response(jsonify(update))
#     return render_template('leave/settings.html', action=fetchsetting, hr=hr_list)



# A T T E N D A N C E

@admin.route('/attendance/check-info', methods=['POST', 'GET'])
@login_required
def check_info():
    today = datetime.datetime.today().strftime('%d-%m-%Y')
    if request.method == 'POST':
        empid = request.form['empid']
        # get emp attendance information
        status = attendance(empid=empid).attendance_info(date=today)
        if status:
            login_time = status[3]
            logout_time = status[4]

            register_status = True

            if login_time is None or login_time == '':
                return 'signin'
            if login_time is not None and logout_time == None :
                return 'signout'
            if login_time != None and logout_time != None:
                return 'Completed'
        else:
            return 'No record'





@admin.route('/commsreport', methods=['POST', 'GET'])
def comms_report():
    today = datetime.datetime.today().strftime('%d-%m-%Y');
    year = datetime.datetime.today().strftime('%Y')

    if request.method == 'POST' and request.form['submit'].lower() == 'send':
        name = request.form['name']
        email = request.form['email']
        shift = request.form['shift']
        date = request.form['date']

        ap = request.form.getlist('action_point')
        desc = request.form.getlist('description')
        duedate = request.form.getlist('duedate')
        commentbox = request.form.getlist('commentBox')
        mailcopy = request.form.get('mailcopy')

        if mailcopy.lower() == 'yes':
            send_copy = email
        else:
            send_copy = None


        info = name, email, shift, date, ap, desc, duedate, commentbox, send_copy

        submit_report = Report.commsReport(info=info)

        if submit_report == True:
            flash('Report submitted successfully', 'success')
        else:
            flash('Error submitting report. Try Again!', 'danger')

        return redirect(url_for('admin.comms_report'))


    
    return render_template('coomsreport.html', today=today, year=year)




@admin.route('/visaimmigration', methods=['POST', 'GET'])
def visaimmg():

    if request.method == 'POST':
        date = request.form.get('date')
        file_for_client = request.form.get('file_for_client')
        client_name = request.form.get('client_name')
        client_contact = request.form.get('client_contact')
        client_company_or_refer = request.form.get('client_company_or_refer')
        type_of_visa = request.form.get('type_of_visa')
        list_of_requirement = request.form.get('list_of_requirement')
        document_provided = request.form.get('document_provided')
        signed_process_document = request.form.get('signed_process_document')
        process_timeframe = request.form.get('process_timeframe')
        additional_service = request.form.get('additional_service')
        additional_service_list = request.form.get('additional_service_list')
        courier = request.form.get('courier')
        courier_cost = request.form.get('courier_cost')
        total_cost = request.form.get('total_cost')
        payment_received = request.form.get('payment_received')
        payment_received_date = request.form.get('payment_received_date')
        payment_receivedVia = request.form.get('payment_receivedVia')
        receipt_to_client = request.form.get('receipt_to_client')
        complete_document_received_from_client = request.form.get('complete_document_received_from_client')
        total_document_received = request.form.get('total_document_received')
        date_complete_document_received = request.form.get('date_complete_document_received')
        complete_document_received_by = request.form.get('complete_document_received_by')
        date_document_received_for_processing = request.form.get('date_document_received_for_processing')
        submission_delay_reason = request.form.get('submission_delay_reason')
        date_visa_returned_from_eci = request.form.get('date_visa_returned_from_eci')
        visa_status = request.form.get('visa_status')
        appeal_required = request.form.get('appeal_required')
        appeal_required_reason = request.form.get('appeal_required_reason')
        date_document_received_by_client = request.form.get('date_document_received_by_client')
        refund_required = request.form.get('refund_required')
        refund_required_amount = request.form.get('refund_required_amount')
        refund_required_reason = request.form.get('refund_required_reason')
        refund_required_date = request.form.get('refund_required_date')
        refund_required_via = request.form.get('refund_required_via')
        refund_required_receipt = request.form.get('refund_required_receipt')
        process_completed = request.form.get('process_completed')
        process_completed_no_reason = request.form.get('process_completed_no_reason')
        process_completed_yes_date = request.form.get('process_completed_yes_date')
        btm_officer_name = request.form.get('btm_officer_name')


        details = [date, file_for_client, client_name, client_contact, client_company_or_refer, type_of_visa, list_of_requirement, document_provided, signed_process_document, 
                    process_timeframe, additional_service, additional_service_list, courier, courier_cost, total_cost, payment_received, payment_received_date, 
                    payment_receivedVia, receipt_to_client, complete_document_received_from_client, total_document_received, date_complete_document_received, 
                    complete_document_received_by, date_document_received_for_processing, submission_delay_reason, date_visa_returned_from_eci, visa_status, appeal_required, 
                    appeal_required_reason, date_document_received_by_client, refund_required, refund_required_amount, refund_required_reason, refund_required_date, 
                    refund_required_via, refund_required_receipt, process_completed, process_completed_yes_date, process_completed_no_reason, btm_officer_name]

        saverecord = Api.savevisareport(date=date, info=details)
        if saverecord == True:
            return 'saved' 


    return render_template('visareport.html')



@admin.route('/visaimmigration/recordlist', methods=['POST', 'GET'])
def visaimmgrecordlist(): 
    from hr_application.hrAPI.run_api import Api 

    getid = request.args.get('editrecord')
    record, editrecord = None, None

    if getid:
        editrecord = Api.editreport(reportid=getid)
    else:           
        record = Api.getreport()


    return render_template('visarecordlist.html', recordlist=record, editrecord=editrecord)

