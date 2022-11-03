from flask import Blueprint, render_template, request, make_response, jsonify
from packages.functions import insert_into_table, fetch_table_record, edit_table_record, fetch_table_per_record
from flask_login import current_user, login_required


dept = Blueprint('dept', __name__, template_folder='templates', url_prefix='/')


@dept.before_request
def chk_session():
    if not current_user.is_authenticated:
        return redirect(url_for('admin.login', next=request.url))
        

@dept.route('/department')
def department():
    dept = 'department'
    dept_info = fetch_table_record(dept)
    render = render_template('department/department.html', all_dept=dept_info)
    return render


@dept.route('/addepartment', methods=['POST', 'GET'])
def addepartment():
    if request.method == 'POST':
        table_name = request.form['type']
        _name = request.form['name']

        if table_name == 'department':
            new_dept = insert_into_table(_name, table_name)
            if new_dept:
                return make_response(jsonify(new_dept))

    render = render_template('department/add_department.html')
    return render


@dept.route('/editdepartment/<edit>', methods=['POST', 'GET'])
def editdepartment(edit):
    get_info = fetch_table_per_record('department', edit)
    render = render_template('department/editdepartment.html', edit=get_info)
    return render


@dept.route('/updatedepartment', methods=['POST'])
def updatedepartment():
    if request.method == 'POST':
        tablename = 'department'
        name = str(request.form['name'])
        table_id = int(request.form['id'])

        edit_alert = edit_table_record(tablename, name, table_id)
        return make_response(jsonify(edit_alert))

