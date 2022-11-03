import os
import random
import datetime
from werkzeug.utils import secure_filename
from flask import Blueprint, render_template, request, make_response, jsonify, redirect, url_for, current_app, flash, session
from packages.functions import getTotal, fetch_table_record, insert_into_table, fetch_table_per_record, \
    edit_table_record, delete_table_record, update_supervisor
from flask_login import current_user, login_required
from packages.employees.userOop import Employee
from packages.settings.settingsOops import Department, Designation, Documents



settings = Blueprint('settings', __name__, url_prefix='/', template_folder='templates')


ALLOWED_EXTENSIONS = {'pdf'}

def allowed_extension(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@settings.before_request
def chk_session():
    if not current_user.is_authenticated:
        return redirect(url_for('admin.login', next=request.url))

   

@settings.route('/admin/setting/create-department', methods=['POST', 'GET'])
def createDepartment():
    if request.method == 'POST':
        deptname = request.form['department']
        sopDocx = request.files['sop']

        # upload file
        if sopDocx.filename is None or sopDocx.filename == '':
            flash('Department SOP is required', 'danger')
            return redirect(url_for('settings.createDepartment'))
        else:
            file_secure_name = secure_filename(sopDocx.filename)
            filename = deptname+'_SOP.pdf'
            sopDocx.save(os.path.join(current_app.config['SOP_FOLDER'], filename))
            sopDocx = filename

            save_record = Department.new_record(name=deptname, sop_file=sopDocx)
            if save_record == True:
                flash('New Department created', 'success')
                return redirect(url_for('settings.departmentList'))
            else:
                flash('Error creating department', 'danger')
                return redirect(url_for('settings.createDepartment'))
    return render_template('setting/add_department.html')


@settings.route('/admin/setting/department-list')
def departmentList():
    deptList = fetch_table_record('department')
    return render_template('setting/department.html', deptList=deptList)


@settings.route('/admin/setting/<dept_id>/edit-department', methods=['POST', 'GET'])
def editDepartment(dept_id):
    dept = fetch_table_per_record('department', dept_id)
    dept_emps = Employee.fetch_all_dept(dept=dept[0])
    dept_sop = dept[3]

    if dept_sop:
        sop_docx = current_app.config['SOP_FOLDER']+dept_sop
    else:
        sop_docx = None
    
    if not dept:
        return redirect(url_for('settings.departmentList'))

    if request.method == 'POST':
        dept_id = request.form['deptid']
        deptname = request.form['department']
        sopDocx = request.files['sop']
        current_sop = request.form['current_sop']
        supervisor = request.form.get('supervisor')

        # upload file
        if sopDocx.filename is None or sopDocx.filename == '':
            sopDocx = current_sop            
            if sopDocx == 'None':
                sopDocx = None
        else:
            # delete the previous document
            try:
                if current_sop:
                    os.remove(current_app.config['SOP_FOLDER']+current_sop)
            except:
                pass

            file_secure_name = secure_filename(sopDocx.filename)
            filename = deptname+'_SOP.pdf'
            sopDocx.save(os.path.join(current_app.config['SOP_FOLDER'], filename))
            sopDocx = filename

        update_record = Department(dept_id=dept[1]).update_department(oldname=dept[0], new_name=deptname, sop=sopDocx, 
                                                                        supervisor=supervisor)
        if update_record == True:
            flash('Record updated successfully', 'success')
            return redirect(url_for('settings.departmentList'))
        else:
            flash('Error updating record', 'danger')
            return redirect(url_for('settings.departmentList'))

    return render_template('setting/editdepartment.html', dept=dept, sop_docx=sop_docx, dept_emps=dept_emps)


@settings.route('/admin/delete-department/<dept_id>')
def delete_department(dept_id):
    record = fetch_table_per_record('department', dept_id)
    if record[3]:
        path = current_app.config['SOP_FOLDER']+'/'+record[3]
        try:
            os.remove(path)
        except:
            pass
    
    delete = delete_table_record('department', dept_id)
    if delete:
        flash(delete, 'success')

        return redirect(url_for('settings.departmentList'))



@settings.route('/admin/setting/designation')
def designation():
    desg = fetch_table_record('post')
    return render_template('setting/post.html', desg=desg)


@settings.route('/admin/setting/add-designation', methods=['POST', 'GET'])
def add_designation():
    dept = fetch_table_record('department')

    if request.method == 'POST':
        postname = request.form['designation']
        department = request.form.get('department')
        jd = request.files['jd']

        if not department or department == 0:
            flash('Select a valid department name', 'danger')
            return redirect(url_for('settings.add_designation'))

        # upload file
        if jd.filename is None or jd.filename == '':
            flash('Job Description document is required', 'danger')
            return redirect(url_for('settings.add_designation'))
        else:
            file_secure_name = secure_filename(jd.filename)
            filename = postname+'_JD.pdf'
            jd.save(os.path.join(current_app.config['JD_FOLDER'], filename))
            jd = filename

            save_record = Designation.create_new_record(name=postname, jd=jd, department=department)
            if save_record == True:
                flash('Record created successfully', 'success')
                return redirect(url_for('settings.designation'))
            else:
                flash('Error creating record', 'danger')
                return redirect(url_for('settings.add_designation'))

    return render_template('setting/addpost.html', dept=dept)


@settings.route('/admin/<pid>/edit-designation',methods=['POST', 'GET'])
def editdesignation(pid):
    post = fetch_table_per_record('post', pid)
    dept = fetch_table_record('department')

    if request.method == 'POST':
        post_id = pid
        postname = request.form['designation']
        jd = request.files['jd']
        current_jd = request.form['current_jd']
        department = request.form['department']

        
        if jd.filename is None or jd.filename == '':
            jd = current_jd            
            if jd == 'None':
                jd = None
        else:
            try:
                if current_jd:
                    os.remove(current_app.config['JD_FOLDER']+current_jd)
            except:
                pass

            file_secure_name = secure_filename(jd.filename)
            filename = postname+'_JD.pdf'
            jd.save(os.path.join(current_app.config['JD_FOLDER'], filename))
            jd = filename

        update_record = Designation(designation_id=pid).update_designation(name=postname, jd=jd, department=department, 
                                                                            oldname=post[0])
        if update_record == True:
            flash('Record updated successfully', 'success')
            return redirect(url_for('settings.designation'))
        else:
            flash('Error updating record', 'danger')
            return redirect(url_for('settings.editdesignation', pid=pid))

    return render_template('setting/editpost.html', edit=post, dept=dept)



@settings.route('/admin/setting/<pid>/delete-designation/')
def deleteDesignation(pid):
    delete = delete_table_record('post', pid)
    if delete:
        flash(delete, 'success')

        return redirect(url_for('settings.designation'))



@settings.route('/admin/setting/officebranch', methods=['POST', 'GET'])
def officebranch():
    branch = fetch_table_record('branch')

    if request.method == 'POST':
        branchname = request.form['name']
        branch_emp = Employee.branch_emp_list(branch=branchname)
        return make_response(jsonify(branch_emp))
    return render_template('setting/branch.html', all_branch=branch)


@settings.add_app_template_filter
def branchNum(name):
    num = Employee.branch_emp(name=name)
    return num


@settings.route('/admin/setting/add-office-branch', methods=['POST', 'GET'])
def addbranch():
    if request.method == 'POST':
        branchname = request.form['name']
        create = insert_into_table(_name=branchname, table_name='branch')
        if create:
                flash('New Office branch created successfully', 'success')
                return redirect(url_for('settings.officebranch'))

    return render_template('setting/addbranch.html')


@settings.route('/admin/<pid>/setting/editbranch', methods=['POST', 'GET'])
def editbranch(pid):
    branch = fetch_table_per_record('branch', pid)
    initial_name = branch[0]

    if request.method == 'POST':
        name = request.form['name']
        update_record = edit_table_record(tablename='branch', fieldname=name, table_id=pid)
        if update_record:
            # update employees branch record
            update_emp_office = Employee.updateOffice(initial=initial_name, new=name)
            if update_emp_office:
                flash('Update Successful', 'success')
                return redirect(url_for('settings.officebranch'))

    return render_template('setting/editbranch.html', data=branch)


@settings.route('/admin/<pid>/deletebranch')
def deletebranch(pid):
    delete = delete_table_record('branch', pid)
    if delete:
        flash('Record Deleted', 'success')
        return redirect(url_for('settings.officebranch'))



@settings.route('/admin/setting/PFA')
def pfa():
    pfa = fetch_table_record('pensioncomp')
    return render_template('setting/pfa.html', all_pfa=pfa)


@settings.route('/admin/setting/addPFA', methods=['POST', 'GET'])
def addpfa():
    if request.method == 'POST':
        name = request.form['name']
        create = insert_into_table(_name=name, table_name='pensioncomp')
        if create:
            flash('New PFA created successfully', 'success')
            return redirect(url_for('settings.pfa'))
    return render_template('setting/add_pfa.html')


@settings.route('/admin/<pid>/setting/editpfa', methods=['POST', 'GET'])
def editpfa(pid):
    all_pfa = fetch_table_per_record('pensioncomp', pid)
    pfaname = all_pfa[1]

    if request.method == 'POST':
        name = request.form['name']
        update = edit_table_record(tablename='pensioncomp', fieldname=name, table_id=pid)
        if update:
            emp_pension = Employee.update_emp_pension_name(initial=pfaname, new=name)
            if emp_pension:
                flash('Record updated', 'success')
                return redirect(url_for('settings.pfa'))

    return render_template('setting/editpfa.html', data=all_pfa)


@settings.route('/admin/<pid>/deletepfa')
def deletepfa(pid):
    delete = delete_table_record('pensioncomp', pid)
    if delete:
        flash('Record Deleted', 'success')
        return redirect(url_for('settings.pfa'))



@settings.route('/admin/setting/banklist')
def banklist():
    banklist = fetch_table_record('bank_name')
    return render_template('setting/banks.html', all_banks=banklist)


@settings.route('/admin/setting/addbanklist', methods=['POST', 'GET'])
def addbanklist():
    if request.method == 'POST':
        name = request.form['name']
        create = insert_into_table(_name=name, table_name='bank_name')
        if create:
            flash('New Bank created successfully', 'success')
            return redirect(url_for('settings.banklist'))
    return render_template('setting/add_bank.html')


@settings.route('/admin/<pid>/setting/editbanklist', methods=['POST', 'GET'])
def editbanklist(pid):
    all_bank = fetch_table_per_record('bank_name', pid)
    bankname = all_bank[0]

    if request.method == 'POST':
        name = request.form['name']
        update = edit_table_record(tablename='bank_name', fieldname=name, table_id=pid)
        if update:
            emp_bank = Employee.update_emp_bankname(initial=bankname, new=name)
            if emp_bank:
                flash('Record updated', 'success')
                return redirect(url_for('settings.banklist'))

    return render_template('setting/editbank.html', data=all_bank)


@settings.route('/admin/<pid>/deletebanklist')
def deletebanklist(pid):
    delete = delete_table_record('bank_name', pid)
    if delete:
        flash('Record Deleted', 'success')
        return redirect(url_for('settings.banklist'))



@settings.route('/admin/documentation', methods=['POST', 'GET'])
def document():
    emplist = Employee.fetch_all_record()
    has_docx = Documents.emp_document()

    if request.method == 'POST' and request.form['submit'] == 'addnewdocument':
        emp_id = request.form['empid']
        docxname = request.form['doc_name']
        docx_file = request.files['file']
        date = request.form['docxdate']
        category = request.form['category']

        month = datetime.datetime.today().strptime(date, '%Y-%m-%d').strftime('%B')
        year = datetime.datetime.today().strptime(date, '%Y-%m-%d').strftime('%Y')

        uploadtime = datetime.datetime.today()

        if docx_file.filename is None or docx_file.filename == '':
            flash('Please valid document to save record. Try Again!', 'warning')
            return redirect(url_for('settings.document'))
        else:
            if docx_file and allowed_extension(docx_file.filename):
                docx_secure_name = secure_filename(docx_file.filename)
                filename = str(random.randint(1, 1000))+'_'+docx_secure_name
                docx_file.save(os.path.join(current_app.config['DOC_FOLDER'], filename))

                docx_file = filename
            else:
                flash('Select a valid document note', 'danger')
                return redirect(url_for('settings.document'))


        savedocx = Documents.save_docx(empid=emp_id, name=docxname, docx=docx_file, uploadby=current_user.id, month=month, 
                                        year=year, uploadtime=uploadtime, category=category)

        if savedocx:
            flash("Document Uploaded successfully.", "success")
            return redirect(url_for('settings.document'))

        else:
            flash("Error uploading document, Try Again!", "danger")
            return redirect(url_for('settings.document'))


    
    if request.method == 'POST' and request.form['submit'] == 'fetchdocx':
        empid = request.form['empid']

        docx = Documents(empid=empid).getdocx()
        if docx:
            return make_response(jsonify(docx))

    return render_template('setting/document.html', has_docx=has_docx, emplist=emplist)


@settings.route('/admin/deletedocx', methods=['POST', 'GET'])
def deletedocx():
    del_docx = request.args.get('DEL')
    del_docx_name = request.args.get('docx')
    docx_id = request.args.get('ID')
    emp_id = request.args.get('empid')
    docx_name = 1

    filepath = current_app.config['DOC_FOLDER']+'/'+del_docx_name

    if docx_id and emp_id and del_docx == 'TRUE':
        delete_emp_docx = Documents(empid=emp_id).remove_docx(docxid=docx_id)
        if delete_emp_docx == True:
           if os.path.exists(filepath):
                os.remove(filepath)

        flash('Document removed successfully', 'success')
        return redirect(url_for('settings.document'))
    else:
        return redirect(url_for('settings.document'))



@settings.add_app_template_filter
def getdocxInfo(empid):
    return Documents(empid=empid).empdet()