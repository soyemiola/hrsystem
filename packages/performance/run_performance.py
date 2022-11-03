from flask import Blueprint, render_template, redirect, url_for, request, flash, make_response, jsonify
from packages.performance.performanceOop import Performance, Appraisal, Review
from flask_login import current_user, login_required
from packages.functions import fetch_table_record
from datetime import datetime
from packages.run_admin import year_selector


performance = Blueprint('performance', __name__, static_folder='static', template_folder='templates', url_prefix='/')


current_year = datetime.today().strftime("%Y")

@performance.before_request
def chk_session():
    if not current_user.is_authenticated:
        return redirect(url_for('admin.login', next=request.url))


@performance.route('/admin/performance', methods=['POST', 'GET'])
def performance_overview():
    if request.method == 'POST':
        year = request.form['year']
        targets = Performance(status='shared').get_all_targets(year)
    else:
        targets = Performance(status='shared').get_all_targets(current_year)

    return render_template('performance/targetlist.html', targets=targets)


@performance.route('/admin/target-response', methods=['POST', 'GET'])
def target_response():
    if request.method == 'POST':
        year = request.form['year']
        info = Review.target_response_list(year)
    else:
        info = Review.target_response_list(current_year)
    return render_template('performance/target_response.html', info=info)


@performance.route('/admin/performance/<code>/details', methods=['POST', 'GET'])
def perform_details(code):
    target_info = Performance(code=code).get_target_code()
    if target_info is None:
        return redirect(url_for('performance.performance_overview'))

    target_supervisor = Performance(department=target_info[5]).target_supervisor('supervisor')
    tgt_emp = Performance(department=target_info[5], code=code).target_emp()
    rules = Performance(code=code).targetrules()
    compute = Performance.computation()
    targetrecord = None
    supID = target_info[12]
    targetdetails = list()

    user = request.args.get('team_member')
    if user:
        getTargetDetails = Review(user, code).chkstatus()
        emp_score = Performance.get_emp_response(emp_id=user, targetcode=code)
        sup_emp_score = Performance.get_emp_response(emp_id=supID, targetcode=code, ref=user)
        if emp_score and sup_emp_score:
            targetdetails = zip(emp_score, sup_emp_score)
            targetrecord = [targetdetails, getTargetDetails]
        else:
            targetrecord = None  
        
    
    return render_template('performance/targetinfo.html', suppy=target_supervisor, info=target_info,
                           tgt_emp=tgt_emp, compute=compute, targetinfo=targetrecord, rules=rules)


@performance.route('/admin/variance', methods=['POST', 'GET'])
def variance():
    var = Performance.computation()
    editform = ''
    # edit variance
    edit = request.args.get('edit')
    if edit:
        edit_var = Performance.edit_variance(edit)
        if edit_var is not None:
            editform = edit_var

    delete = request.args.get('delete')
    if delete:
        name = request.args.get('name')
        Performance.remove_variance(delete, name)
        flash('Variance deleted Successfully', 'success')
        return redirect(url_for('performance.variance'))

    # create new variance
    if request.method == 'POST':
        category = request.form['category']
        score = request.form['score']
        note = request.form['note']
        tag = request.form['tag']
        
        new_var = Performance.create_variance(category, score, note, tag)
        if new_var is True:
            flash('New variance created successfully', 'success')
            return redirect(url_for('performance.variance'))
    return render_template('performance/variance.html', var=var, edit=editform)


@performance.route('/admin/variance/update/<editid>', methods=['POST', 'GET'])
def update_var(editid):
    if request.method == 'POST':
        category = request.form['category']
        score = request.form['score']
        note = request.form['note']
        tag = request.form['tag']
        old_name = request.form['oldname']

        new_var = Performance.update_variance(category, score, note, tag, editid, old_name)
        if new_var is True:
            flash('Variance updated successfully', 'success')
            return redirect(url_for('performance.variance'))


@performance.route('/admin/performance/report', methods=['POST', 'GET'])
def report():
    department = fetch_table_record('department')
    label = []
    values = []
    dept = None
    info = None
    rep = None

    if request.method == 'POST':
        dept = request.form['department']
        start = request.form['from']
        end = request.form['to'] 
        
        rep = Performance(department=dept).report(dept=dept, start=start, end=end)
        if len(rep) == 0:
            flash('No Record Found!', 'info')
            return redirect(url_for('performance.report'))
        else:
            info = [start, end]

        for i in rep:
            label.append(i[0])
            values.append(i[3])



    if len(label) == 0:
        label = None

    if len(values) == 0:
        values = None

    return render_template('performance/report.html', department=department, label=label, values=values, dept=dept, info=info, 
                            result=rep)


@performance.route('/admin/performance/reset/<get_id>/<code>')
def reset_apprasial(get_id, code):
    reset = Performance(code=code).resetApprasial(emp_id=get_id)
    if reset:
        flash("Appraisal reset process successful", "success")
        return redirect(url_for('performance.perform_details', code=code, team_member=get_id))






@performance.route('/admin/performance/appraisal-tool', methods=['POST', 'GET'])
def appraisaltool():
    activeyear = year_selector()
    year = datetime.today().strftime("%Y")

    pmt = Appraisal(year=year).getpmt()

    if request.method == 'POST' and request.form['rulesubmit'] == 'create':
        codeid = request.form['codeid']
        phase = request.form['cphase']
        pmr = request.form['pmr']
        title = request.form.getlist('rules')
        desc = request.form.getlist('description')
        score = request.form.getlist('scores')

        setRule = Appraisal(year=current_year).set_rule(code=codeid, pmr=pmr, title=title, desc=desc, score=score, phase=phase)
        
        if setRule == True:
            flash('PMR Rule added', 'success')            
        elif setRule == 101:
            flash('Select PMR already exist', 'warning')
        else:
            flash('Error saving record, try again!', 'danger')

        return redirect(url_for('performance.appraisaltool'))


    if request.method == 'POST' and request.form['rulesubmit'] == 'filter':
        try:
            fil_year = request.form['year']
        except KeyError as e:
            flash('Select a valid year value', 'info')
            return redirect(url_for('performance.appraisaltool'))
        else:
            pmt = Appraisal(year=fil_year).getpmt()


    if request.method == 'POST' and request.form['rulesubmit'] == 'details':
        name = request.form['name']
        code = request.form['code']

        det = Appraisal.itemDetails(name=name, code=code)
        if det:
            return make_response(jsonify(det))
        
    return render_template('performance/appraisaltool.html', year=activeyear, pmt=pmt)


@performance.route('/admin/performance/addtool', methods=['POST'])
def addtool():
    if request.method == 'POST':
        name = request.form['pmt-name']
        score = request.form['pmt-score']
        year = datetime.today().strftime("%Y")
        phase = request.form['phase']

        newpmt = Appraisal(year=year).addpmt(name=name, score=score, phase=phase)
        if newpmt:
            flash("New Record created successfully", "success")
            return redirect(url_for('performance.appraisaltool'))
    else:
        return redirect(url_for('performance.appraisaltool'))



@performance.route('/admin/performance/edittool', methods=['POST'])
def edittool():
    if request.method == 'POST':
        name = request.form['pmt-name']
        i_name = request.form['i_name']
        score = request.form['pmt-score']
        pmtid = request.form['pmt-id']
        phase = request.form['phase']

        newpmt = Appraisal(year=None).updatepmt(name=name, score=score, pmtid=pmtid, i_name=i_name, phase=phase)
        if newpmt:
            flash("Record update successfully", "success")
            return redirect(url_for('performance.appraisaltool'))
    else:
        return redirect(url_for('performance.appraisaltool'))


@performance.route('/admin/performance/<pmtid>/<year>/deleteappraisal')
def deleteappraisal(pmtid, year):
    if pmtid:
        deletepmt = Appraisal(year=year).delete_pmt(pmtid=pmtid)
        if deletepmt:
            flash('Record deleted successfully', 'success')
            return redirect(url_for('performance.appraisaltool'))
    else:
        return redirect(url_for('performance.appraisaltool'))



@performance.add_app_template_filter
def get_target_score(code, emp_id):
    target_score = Performance(code=code).fetch_target_details(emp_id)
    return target_score


@performance.add_app_template_filter
def get_emp_name(emp_id):
    get_details = Performance.get_emp_details(emp_id)
    return get_details[1]


@performance.add_app_template_filter
def covert_percentage(value=0):
    if value is None:
        value = 0
        return int(value)
    else:
        res = int(value * 10)
        return int(res)


@performance.add_app_template_filter
def get_compute_value(name, emp_id, code):
    name = name.replace(' ', '_')
    value = Performance(code=code).compute_value(name, emp_id)
    if value:
        return float(value)


@performance.add_app_template_filter
def getqcValue(mode, emp_id, start, end):
    gtlist = Performance.getappraisalQC(mode, emp_id, start, end)
    if len(gtlist) > 0:
        return gtlist
    


@performance.add_app_template_filter
def replace_dash(get_value):
    var = get_value.replace(' ', '_')
    return var

@performance.add_app_template_filter
def perform_docx(tag, emp_id, targetid):
    getdocx = Performance.performance_docx(targetid, emp_id, tag)
    return getdocx



@performance.add_app_template_filter
def check_signed_status(code, emp_id):
    status = Performance(code=code).check_signed(emp_id=emp_id)
    if status:
        return status
    else:
        return None

@performance.add_app_template_filter
def assessmentUsers(code):
    return Appraisal.assessmentList(code)


@performance.add_app_template_filter
def get_getTragetrule(codeid, year):
    return Appraisal(year).getTragetrule(codeid)



@performance.route('/admin/performance/assessment', methods=['POST', 'GET'])
def assessment():
    get_assessments = Appraisal.getAssessment(current_year)

    if request.method == 'POST' and request.form['submit'] == 'filter':
        year = request.form['year']
        get_assessments = Appraisal.getAssessment(year)

    info, details, view_record, info  = None, None, 0, None

    wkcode = request.args.get('wkcode')
    wkempid = request.args.get('USERID')

    if wkcode and wkempid:
        info = UserAppraisal.appweeklyreportdet(code=wkcode, empid=wkempid)
        details = UserAppraisal.getusertargetrecord(code=wkcode, empid=wkempid)  
        view_record = 1

    if request.method == 'POST' and request.form['submit'] == 'supremark':
        remark = request.form['remark']
        code = request.form['code']
        empid = request.form['empid']


        stat = Appraisal.upWkTarget(remark, code, empid)
        if stat:
            flash('Remark added successfully', 'success')
            return redirect(url_for('performance.assessment', USERID=empid, wkcode=code))

    return render_template('performance/assessment.html', alist=get_assessments, view_record=view_record, info=info, details=details, year=year_selector())


@performance.route('/admin/performance/weeklyreport', methods=['POST', 'GET'])
def genWeeklyreport():
    if request.method == 'POST':
        sD = request.form['sD']
        eD = request.form['eD']
        year = datetime.today().strptime(sD, '%Y-%M-%d').strftime('%Y')

        pmt = Appraisal(year).getpmt()
        wkly = Appraisal.weekly_rpt(sD, eD, year)

    
    return render_template('performance/appweeklyreport.html', pmt=pmt, wkly=wkly)


@performance.add_app_template_filter
def empdet(empid):
    return Appraisal.getempdetails(empid)

@performance.add_app_template_filter
def get_total_wk_score(column, code):
    values = Appraisal.t_scores(column.replace(' ', '_').lower(), code)
    return sum(map(int, values[0][1]))
