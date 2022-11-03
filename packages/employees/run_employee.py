from flask import Blueprint, render_template, redirect, request, url_for, make_response, jsonify, flash, current_app, session
from datetime import datetime
import bcrypt
from packages.models import Employees
from packages.employees.userOop import Employee, SendMailNotice, Offboradingmail, Onboradingmail, TFeedback
from packages.functions import fetch_table_record
from packages.payroll.empcategory.empOop import Category
from packages.employees.coop.cooperative import Cooperative
from packages.payroll.taxable import convert_to_float
import calendar
from packages.leave.leaveOop import Leave
from packages import login_manager
from flask_login import current_user, login_required
from packages.run_admin import year_selector


users = Blueprint('users', __name__, url_prefix='/', template_folder='templates', static_folder='static')


@users.before_request
def chk_session():
    if not current_user.is_authenticated:
        return redirect(url_for('admin.login', next=request.url))



@users.route('/admin/employees', methods=['POST', 'GET'])
def employees():
    emp_details = Employee.fetch_all_record()

    if request.method == 'POST':
        emp_details = Employee.fetch_all_record()
        return make_response(jsonify(emp_details))
    return render_template('users/employee.html', emp_details=emp_details)



@users.route('/admin/addemployees', methods=['POST', 'GET'])
def addemployee():
    last_record = Employee.get_employee()
    department = fetch_table_record('department')
    post = fetch_table_record('post')
    branch = fetch_table_record('branch')
    get_class = Category.class_list()
    bank = fetch_table_record('bank_name')
    pension = fetch_table_record('pensioncomp')
    states = (
    'Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa', 'Benue', 'Borno', 'Cross', 'Delta', 'Ebonyi',
    'Edo', 'Ekiti', 'Enugu', 'FCT', 'Gombe', 'Imo', 'Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Kogi',
    'Kwara', 'Lagos', 'Nassarawa', 'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo', 'Plateau', 'Rivers', 'Sokoto',
    'Taraba', 'Yobe', 'Zamfara')
    record = None

    # check new staff record
    reg_list = Employee.pre_reg_list()

    #populate fileds
    if request.method == 'POST':
        list_id = request.form['list']
        record = Employee.reg_list_info(new_id=list_id)

    try:
        if last_record is not None:
            staff_id = int(last_record[16].replace('BTM-', ' '))
        else:
            staff_id = 0
    except:
        staff_id = 0


    return render_template('users/addemployee.html', department=department, posts=post, branch=branch,
                           cat=get_class, bank=bank, pensions=pension, states=states, reg_list=reg_list, record=record,
                           last_record=staff_id)


@users.route('/admin/add/record', methods=['POST', 'GET'])
def addnewrecord():
    if request.method == 'POST':
        new_em_name = str(request.form['name'])
        new_em_state = str(request.form['state'])
        new_em_address = str(request.form['address'])
        new_em_city = str(request.form['city'])
        new_em_mobile = str(request.form['mobile'])
        new_em_department = str(request.form['department'])
        new_em_post = str(request.form['level'])
        new_em_email = str(request.form['email'])
        new_em_branch = str(request.form['branch'])
        new_em_category = str(request.form['category'])
        new_em_basic = float(request.form['basic'])
        new_em_ha = float(request.form['ha'])
        new_em_ta = float(request.form['ta'])
        new_em_oa = float(request.form['oa'])
        new_em_account = request.form['account']
        new_em_bankname = str(request.form['bankname'])
        new_em_date = request.form['activedate'] 
        new_em_tax_num = request.form['taxnumber']
        new_em_pen_name = request.form['pensioncompany']
        new_em_pen_num = request.form['pensionnumber']
        new_em_password = bcrypt.generate_password_hash('passw0rd1').decode('utf-8')
        new_em_staff_id = request.form['staff_id']
        new_em_dob = request.form.get('dob')
        new_em_jobtitle = request.form.get('jobtitle')
        new_em_title = request.form.get('title')
        new_em_gender = request.form.get('gender')

        # next of kin
        nokin = request.form.get('nokin')
        nokinnumber = request.form.get('nokinnumber')
        nokinemail = request.form.get('nokinemail')
        nokinrel = request.form.get('nokinrel')

        get_allowance = (new_em_ha, new_em_ta, new_em_oa)
        new_em_total_a = sum(get_allowance)

        from_list = request.form['frmlist']

        save_new_employee = Employee.create_new_user(new_em_name, new_em_address, new_em_city, new_em_mobile,
                                                        new_em_department, new_em_post, new_em_email, new_em_branch,
                                                        new_em_date, new_em_category, new_em_basic, new_em_ha, new_em_ta,
                                                        new_em_oa, new_em_total_a, new_em_bankname, new_em_account,
                                                        new_em_tax_num, new_em_pen_name, new_em_pen_num, new_em_state,
                                                        new_em_password, new_em_dob, new_em_staff_id, new_em_jobtitle, new_em_title, 
                                                        new_em_gender, nokin, nokinnumber, nokinemail, nokinrel)

        if save_new_employee == 101:
            flash('Email Already Exist, Try another', 'danger')
            return redirect(url_for('users.addemployee'))
        elif save_new_employee == 0:
            response = 0
        elif save_new_employee == 210:
            flash('Error creating user profile, Try Again', 'danger')
        else:
            new_emp_id = save_new_employee
            # remove data from staff list 
            # if from_list is not 'no':
            #     Employee.delete_list(new_id=int(from_list))
            return redirect(url_for('users.emp_requirement', get_emp_id=new_emp_id[0]))
            


@users.route('/admin/employees/requirements/<get_emp_id>', methods=['POST', 'GET'])
def emp_requirement(get_emp_id):
    emp_record = Employee.emp_per_record(get_emp_id)
    if request.method == 'POST':
        device = request.form.getlist('device')
        services = request.form.getlist('services')
        new_email = request.form.getlist('new_email_value')
        existing_email = request.form.getlist('exisiting_email_value')
        access_email = request.form.getlist('access_email_value')
        training = request.form.getlist('training')
        email = request.form['email']

        # send email address
        SendMailNotice(emp_name=emp_record[1], dept=emp_record[5], email=email, device=device, 
                        services=services, training=training, new=new_email, existing=existing_email, 
                        access=access_email).sendmail()
 
        # save tools to db
        save_tools = Employee.save_tools(emp_id=emp_record[0], services=services, device=device, 
                                            department=emp_record[5], email=email)
        if save_tools is True:
            flash('Request Send', 'success')

    process_done = request.args.get('action')
    if process_done == 'completed':
        flash('New User Created', 'success')
        return redirect(url_for('users.employees'))
    return render_template('users/requirement.html', emp_details=emp_record)



@users.route('/admin/editemployee/<editemp>', methods=['POST', 'GET'])
def editemployee(editemp):
    department = fetch_table_record('department')
    post = fetch_table_record('post')
    branch = fetch_table_record('branch')
    cat_ = fetch_table_record('emp_class')
    bank = fetch_table_record('bank_name')
    pension = fetch_table_record('pensioncomp')
    states = (
        'Abia', 'Adamawa', 'Akwa Ibom', 'Anambra', 'Bauchi', 'Bayelsa', 'Benue', 'Borno', 'Cross', 'Delta', 'Ebonyi',
        'Edo', 'Ekiti', 'Enugu', 'FCT', 'Gombe', 'Imo', 'Jigawa', 'Kaduna', 'Kano', 'Katsina', 'Kebbi', 'Kogi',
        'Kwara', 'Lagos', 'Nassarawa', 'Niger', 'Ogun', 'Ondo', 'Osun', 'Oyo', 'Plateau', 'Rivers', 'Sokoto',
        'Taraba', 'Yobe', 'Zamfara')

    emp_details = Employee.emp_per_record(editemp)
    emp_acct_details = Employee.emp_account_record(editemp)
    emp_pension = Employee.emppension(editemp)
    emp_nokin = Employee.empnokin(editemp)

    dates = {v: k for k, v in enumerate(calendar.month_abbr)}
    status = ''

    if editemp is None:
        return redirect('/users.employees')

    return render_template('users/editemployee.html', edit_data=emp_details, emp_acct=emp_acct_details,
                           dept=department, post=post, branch=branch, cat=cat_, bank=bank, date=dates,
                           pension=emp_pension, pensioncomp=pension, state=states, status=status, emp_nokin=emp_nokin)


@users.route('/admin/updateemployee', methods=['POST', 'GET'])
def updateemployee():
    if request.method == 'POST':
        em_id = request.form['emp_id']
        em_name = request.form['name']
        em_state = request.form['state']
        em_address = request.form['address']
        em_city = request.form['city']
        em_mobile = request.form['mobile']
        em_dept = request.form['department']
        em_post = request.form['level']
        em_email = request.form['email']
        em_branch = request.form['branch']
        em_category = request.form['category']
        em_basic = request.form['basic']
        em_total_a = request.form['ToA']
        em_ha = request.form['ha']
        em_ta = request.form['ta']
        em_oa = request.form['oa']
        em_acct = request.form['bank_acct']
        em_bank_name = request.form['bank_name']
        employment_date = request.form['employment_date']
        em_tax_num = request.form['taxnumber']
        em_pen_name = request.form['pensioncompany']
        em_pen_num = request.form['pensionnumber']
        em_dob = request.form['dob']
        em_jobtitle = request.form['jobtitle']
        em_title = request.form.get('title')
        em_gender = request.form.get('gender')

        nokin = request.form.get('nokin')
        nokinnumber = request.form.get('nokinnumber')
        nokinemail = request.form.get('nokinemail')
        nokinrel = request.form.get('nokinrel')
        

        if em_basic == 0:
            flash('Class value can not be 0', 'danger')
            return redirect(url_for('users.editemployee', editemp=em_id))

        emp_record = Employee(em_name, em_address, em_city, em_mobile, em_dept, em_post, em_email, em_branch, employment_date,
                              em_category, em_basic, em_ha, em_ta, em_oa, em_total_a, em_bank_name, em_acct, em_tax_num,
                              em_pen_name, em_pen_num, em_state, em_dob, em_jobtitle, em_title, em_gender, nokin, nokinnumber, 
                              nokinemail, nokinrel)

        update_emp_record = emp_record.update_emp(em_id)
        
        if update_emp_record != False:
            flash('Profile update Successfully', 'success')
        else:
            flash('Profile update failed', 'danger')

        return redirect(url_for('users.editemployee', editemp=em_id))


@users.route('/admin/unboard_employee/<unbound_emp>/<status>')
def unboard_employee(unbound_emp, status):
    pass



@users.route('/admin/emp_profile/<get_id>', methods=['POST', 'GET'])
def emp_profile(get_id):
    emp_record = Employee.emp_per_record(get_id)
    emp_account_record = Employee.emp_account_record(get_id)
    emp_coop = Cooperative.coop_emp(get_id)
    emp_pension = Employee.emppension(get_id)
    pension = fetch_table_record('pensioncomp')
    banklist = fetch_table_record('bank_name')

    emp_permission = Employee.emp_permission(get_id)
    # check profile taxable
    #try:
    chk_emp = emp_account_record[9]
    if chk_emp is None:
        tax_alert = 'Employee Tax Profile is not set yet!'
    else:
        tax_alert = ''

    return render_template('users/profile.html', emp_details=emp_record, emp_acct=emp_account_record,
                            alert=tax_alert, coop=emp_coop, pension=pension, emp_pension=emp_pension, bank=banklist)
    #except:
        #return redirect(url_for('users.employees', error=1))


@users.route('/admin/updateprofile', methods=['POST', 'GET'])
def updateprofile():
    emp_id = request.form['emp_id']
    taxnumber = request.form['taxnumber']
    basicpay = convert_to_float(request.form['basicpay'])
    percent = request.form['percent']
    acctnumber = request.form['acctnumber']
    acctname = request.form['acctname']
    bankname = request.form['bankname']

    updateInfo = Employee.updateBasicTaxInfo(emp_id, taxnumber, basicpay, acctnumber, acctname, bankname, percent)
    if updateInfo:
        flash('Profile Updated', 'success')
        return redirect(url_for('users.emp_profile', get_id=emp_id))


@users.route('/admin/updateprofileallowance', methods=['POST', 'GET'])
def updateprofileallowance():
    emp_id = request.form['emp_id']
    get_type = request.form['type']
    amount = convert_to_float(request.form['allowancepay'])

    try:
        updateInfo = Employee.updateAllowanceInfo(emp_id, get_type, amount)
        if updateInfo:
            flash('Profile Allowance Updated', 'success')
    except:
        flash('Error updating Allowance', 'danger')

    return redirect(url_for('users.emp_profile', get_id=emp_id))


@users.route('/admin/updatepensionprofile', methods=['POST'])
def updatepensionprofile():
    emp_id = request.form['emp_id']
    comp_name = request.form['name']
    pen_num = request.form['number']

    update = Employee.updatepensionprofile(emp_id, comp_name, pen_num)
    if update:
        flash('Profile pension updated', 'success')
        return redirect(url_for('users.emp_profile', get_id=emp_id))


@users.route('/admin/emppermission/<get_id>')
def emppermission(get_id):
    emp_record = Employee.emp_per_record(get_id)
    emp_permission = Employee.emp_permission(get_id)
    return render_template('users/profile-action.html', emp_details=emp_record, permission=emp_permission)


@users.route('/admin/permit', methods=['POST'])
def permit():
    emp_id = request.form['id']
    cms = request.form['cms']
    report = request.form['report']
    loan = request.form['loan']

    permitEmp = Employee.permit_emp(emp_id, cms, report, loan)
    flash('Profile setting updated successfully!', 'success')
    return redirect(url_for('users.emppermission', get_id=emp_id))



@users.route('/admin/leave-profile/<get_id>', methods=['POST', 'GET'])
def leave_profile(get_id):
    user = Employee.emp_per_record(get_id)
    leave = Leave.leavedet(user[0])

    if request.method == 'POST':
        try:
            emp_id = int(request.form['emp_id_leave'])
            days = int(request.form['leavedays'])

            res = Leave.createleave(emp_id, days)
            if res == 1:
                return redirect(url_for('users.leave_profile', get_id=emp_id))
        except:
            return redirect(url_for('users.employees'))

    return render_template('users/leave-profile.html', emp_details=user, leave=leave)

 
@users.route('/admin/createdays', methods=['POST', 'GET'])
def createdays():
    if request.method == 'POST':
        emp_id = request.form['id']
        res = Leave.createleave(emp_id)
        return make_response(jsonify(res))


@users.route('/admin/updateleavedays', methods=['POST', 'GET'])
def updateleavedays():
    emp_id = request.form['id']
    days = request.form['days']

    res = Leave.updateleave(emp_id, 'remain_days', days)
    return make_response(jsonify(res))


@users.route('/admin/activeleave', methods=['POST', 'GET'])
def activeleave():
    emp_id = request.form['id']
    status = request.form['status']

    res = Leave.updateleave(emp_id, 'status', status)
    return make_response(jsonify(res))


@users.route('/admin/user/offboard/', methods=['POST', 'GET'])
def offboard():
    emps = Employee.fetch_all_record()
    user_details, user_tools = None, None

    if request.method == 'POST' and request.form['submit'] == 'fetch':
        try:
            emp_id = request.form['emp_id']
        except:
            flash('Please select a user', 'warning')
            return redirect(url_for('users.offboard'))

        user_details = Employee.emp_per_record(emp_id=emp_id)
        user_tools = Employee.get_tools(emp=emp_id)

    elif request.method == 'POST' and request.form['submit'] == 'Offboard User':
        emp_id = request.form['empid']
        department = request.form['department']
        reason = request.form['reason']
        comment = request.form.get('comment')

        submitdate = datetime.today()#datetime.today().strftime("%Y-%m-%d")

        offboard_user = Employee.offboarding(emp_id=emp_id, department=department, offboarddate=submitdate, reason=reason, comment=comment)
        if offboard_user:
            DA_action = Employee.DA_account(emp_id=emp_id, status=int(0))
            if DA_action:
                flash('User Offboard', 'success')
                return redirect(url_for('users.offboard'))
    

    return render_template('users/offboard.html', emps=emps, u_details=user_details, u_tools=user_tools)


@users.route('/admin/mailoffboarding', methods=['POST', 'GET'])
def offboarding_mail():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        dept = request.form['dept']

        emp_det = Employee.emp_per_record(emp_id=emp_id)
        tools = Employee.get_tools_per_dept(emp=emp_id, dept=dept)
        #tools[5]
        Offboradingmail(emp_name=emp_det[1], dept=dept, email='intern2@btmlimited.net', device=tools[3], services=tools[2]).sendmail()

        return make_response(jsonify('success'))


@users.route('/admin/user/onboard', methods=['POST', 'GET'])
def onboard():
    offbound_emps = Employee.offboardinglist_on()
    open_process, status = None, None

    if len(offbound_emps) == 0:
        flash('No Record found', 'info')

    if request.method == 'POST':
        emp_id = request.form['emp_id']
        offboardId = request.form['offboardId']

        emp_details = Employee.emp_per_record(emp_id=emp_id)
        tools = Employee.get_tools(emp=emp_id)
        onboard_info = [emp_details, tools, offboardId]

        open_process = onboard_info
        offbound_emps = None

        if request.form.get('status') and request.form.get('status').lower() == 'activate':
            
            update_onboard = Employee.update_onboarding(emp_id=emp_id)
            if update_onboard is True:
                action = Employee.DA_account(emp_id=emp_id, status=int(1))
                if action is True:
                    flash("Profile Activated", "success")
                    return redirect(url_for('users.onboard'))
    
    return render_template('users/onboarding.html', offboard=offbound_emps, open_process=open_process)



@users.route('/admin/mailonboarding', methods=['POST', 'GET'])
def onboarding_mail():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        dept = request.form['dept']

        emp_det = Employee.emp_per_record(emp_id=emp_id)
        tools = Employee.get_tools_per_dept(emp=emp_id, dept=dept)

        Onboradingmail(emp_name=emp_det[1], dept=dept, email=tools[5], device=tools[3], services=tools[2], 
                        empmail=emp_det[7]).sendmail()

        return make_response(jsonify('success'))


@users.route('/admin/staff information')
def staff():
    stafflist = Employee.stafflist()
    return render_template('users/staffinfo.html', staff=stafflist)


@users.route('admin/getuserrecord', methods=['POST', 'GET'])
def resetpass():

    emp_id = request.args.get('resetpass')
    if emp_id:
        password = bcrypt.generate_password_hash('passw0rd1').decode('utf-8')
        setDefault = Employee.updatePass(id=emp_id, newpass=password)
        if setDefault:
            flash('Password Reset Successfully', 'success')
            return redirect(url_for('users.employees'))
        else:
            flash('Process Failed! Try Again', 'danger')
            return redirect(url_for('users.employees'))

    if request.method == 'POST':
        emp_id = request.form['emp_id'];
        emp_det = Employee.emp_per_record(emp_id=emp_id)

        return make_response(jsonify(emp_det))



@users.route('admin/inactivelist')
def inactiveusers():
    inactive = Employee.fetch_all_record(status=0)

    return render_template('users/inactivelist.html', inactive=inactive)



# FEEDBACK TRAINING
@users.add_app_template_filter
def nOU(ulink):
    return TFeedback(ulink).nOU()


@users.add_app_template_filter
def FBempDet(empid):
    return TFeedback.empDet(empid)


@users.route('/admin/feedbacktraining', methods=['POST', 'GET'])
def feedbacktraining():
    if request.method == 'POST':
        tflist = TFeedback.getlist(year=request.form['year'])
    tflist = TFeedback.getlist()

    return render_template('users/feedbacktraining.html', tflist=tflist, year=year_selector() )


@users.route('/admin/feedbacktraining/display/<ulink>')
def displayfb(ulink):
    if ulink:
        fbDet = TFeedback.getlist(ulink)
        reslist = TFeedback(ulink).nOU(ulink='yes')
        
        return render_template('users/displayfb.html', fbDet=fbDet, reslist=reslist) 




@users.route('/admin/feedbacktraining/list', methods=['POST', 'GET'])
def traininglist():
    tlist = TFeedback.trainingFDlist()

    if request.method == 'POST':
        empTList = TFeedback.trainingFDlist(request.form['emp_id'])
        return make_response(jsonify(empTList))
    return render_template('users/traininglist.html', tlist=tlist)
        