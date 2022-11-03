from flask import request, render_template, session
import os.path
import datetime
from urllib.parse import urlparse
from packages import create_app
from packages.database import Database, CursorFromConnectionPool
from packages.payroll.process_payroll.salary import Salary


app = create_app()


if __name__ == '__main__': 
	app.run(debug=True)



@app.before_request
def before_request():
    session.permanent = True
    create_app.permanent_session_lifetime = datetime.timedelta(minutes=15)
    session.modified = True


@app.template_filter()
def numberFormat(value):
    if value is None:
        return 0
    else:
        return format(float(value), ',.2f')


@app.template_filter()
def check_process_salary(get_emp_id):
    month = datetime.datetime.today().strftime('%B')
    year = datetime.datetime.today().strftime('%Y')
    chk = Salary.chk_process_salary_per_month(get_emp_id, month, year)
    if chk:
        return chk
    else:
        return None


@app.template_filter()
def process_btn(check):
    month = datetime.datetime.today().strftime('%B')
    year = datetime.datetime.today().strftime('%Y')
    
    emp_list = Employee.fetch_all_record()
    for i in emp_list:
        chk = Salary.chk_process_salary_per_month(i[0], month, year)
        if chk is None:
            return 'unlock'
        else:
            pass


@app.template_filter()
def check_finalized_salary(get_emp_id):
    month = datetime.datetime.today().strftime('%B')
    year = datetime.datetime.today().strftime('%Y')
    chk = Salary.chk_salary_per_month(get_emp_id, month, year)
    if chk:
        return 'Finalized'


@app.template_filter()
def changeDateFormat(getDate):
    if getDate != 0:
        month = datetime.datetime.strptime(getDate, '%b').strftime('%B')
        return month
    else:
        return ''


@app.errorhandler(404)
def page_not_found(e):
    last_url = request.base_url
    path_domain = getPath(last_url)

    return render_template('404.html', error_msg=e, path=path_domain)


@app.errorhandler(500)
def internal_server_error(e):
    last_url = request.base_url
    path_domain = getPath(last_url)
    return render_template('server_error.html', error_msg=e, path=path_domain)


@app.errorhandler(405)
def method_not_allowed(e):
    last_url = request.base_url
    path_domain = getPath(last_url)
    return render_template('server_error.html', error_msg=e, path=path_domain)


@app.template_filter()
def getName(emp_id):
    emp_name = WeeklyTask.empname(emp_id=emp_id)
    if emp_name:
        return emp_name[0]



def getPath(last_url):
    path = urlparse(last_url).path
    sections = []; 
    temp = "";
    path_domain = 'admin.dashboard'
    # path_domain =  None

    # while path != '/':
    #     temp = os.path.split(path)
    #     path =  temp[0]
    #     sections.append(temp[1])
    
    # if 'admin' in sections:
    #     path_domain = 'admin.dashboard'
    # else:
    #      path_domain = 'user_in.home'

    return path_domain



@app.before_first_request
def leave_reload():
    with CursorFromConnectionPool() as cursor:
        cursor.execute("SELECT leave_year FROM oops ")
        year = cursor.fetchone()
        if year is not None:
            app.config['LEAVE_YEAR'] = year[0]
        else:
            app.config['LEAVE_YEAR'] = 2020

    leave_year = app.config['LEAVE_YEAR']
    current_year = datetime.datetime.today().strftime('%Y')
    
    if leave_year != current_year:
        app.config['LEAVE_YEAR'] = current_year
        with CursorFromConnectionPool() as cursor:
            cursor.execute("UPDATE oops SET leave_year=%s", (current_year,))
            cursor.execute("UPDATE leavedays SET used_days=%s, remain_days=%s", (0, 21))
    else:
        pass
