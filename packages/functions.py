from packages.database import CursorFromConnectionPool
import datetime


def fetch_table_record(tablename):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('SELECT * FROM {}'.format(tablename))
        get_all = cursor.fetchall()
        return get_all


def fetch_table_per_record(tablename, table_id):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('SELECT * FROM {} WHERE id={}'.format(tablename, table_id))
        get_one = cursor.fetchone()
        return get_one


def insert_into_table(_name, table_name):
    with CursorFromConnectionPool() as cursor:
        name = table_name
        cursor.execute('INSERT INTO {}(name) VALUES(%s) RETURNING id'.format(table_name), (_name,))
        res = cursor.fetchone()
        return res


def edit_table_record(tablename, fieldname, table_id):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('UPDATE {} SET name=%s WHERE id = {}'.format(tablename, table_id), (fieldname,))
        if cursor:
            return 'Record Updated'


def delete_table_record(tablename, table_id):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('DELETE FROM {} WHERE id = {}'.format(tablename, table_id))
        if cursor:
            return 'Record Deleted'


def monthly_submission(month, year):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('select employees.id, employees.name, salary.date_process, salary.finalized, salary.month, employees.staff_id '
                       'from employees '
                       'left join salary '
                       'on employees.id = salary.emp_id '
                       'where salary.month = %s and salary.year=%s order by employees.staff_id asc', (month, year))
        res = cursor.fetchall()
        if res:
            return res


def all_sum(month, year):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('select coalesce(sum(gross), 0) as total_gross, coalesce(sum(pension), 0) as total_pension, '
                       'coalesce(sum(tax), 0) as total_tax, coalesce(sum(employer_savings), 0) as employer_pension, '
                       'count(*) as total_emp, month '
                       'from salary '
                       'where salary.month = %s and salary.year=%s '
                       'group by salary.month '
                       'order by salary.month asc', (month, str(year)))
        res = cursor.fetchall()
        if res:
            return res


def getTotal(getTablename):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('SELECT count(*) from {}'.format(getTablename))
        res = cursor.fetchone()
        return res


def monthly_sum(month, year, office=None):
    with CursorFromConnectionPool() as cursor:
        if office is None:
            cursor.execute('select coalesce(sum(basic), 0) as basic, '
                           'coalesce(sum(allowance), 0) as allowance, coalesce(sum(gross), 0) as gross, coalesce(sum(pension), 0) as pension, '
                           'coalesce(sum(employer_savings), 0) as Esavings, coalesce(sum(relief), 0) as relief, coalesce(sum(tax), 0) as tax, '
                           'coalesce(sum(workedfor), 0) as workedfor, coalesce(sum(loan), 0) as loan, coalesce(sum(coop_loan), 0) as coop_loan, '
                           'coalesce(sum(coop_savings), 0) as coop_savings, coalesce(sum(coop_deduction), 0) as cd, '
                           'coalesce(sum(adjustment), 0) as ad, coalesce(sum(deductions), 0) as ded, coalesce(sum(netpay), 0) as netpay, '
                           'count(*) as num, coalesce(sum(socialcontrib), 0) as social '
                           'from salary '
                           'where month = %s and year =%s', (month, year))
            res = cursor.fetchone()
            if res:
                return res
        else:
            cursor.execute('select coalesce(sum(basic), 0) as basic, '
                           'coalesce(sum(allowance), 0) as allowance, coalesce(sum(gross), 0) as gross, coalesce(sum(pension), 0) as pension, '
                           'coalesce(sum(employer_savings), 0) as Esavings, coalesce(sum(relief), 0) as relief, coalesce(sum(tax), 0) as tax, '
                           'coalesce(sum(workedfor), 0) as workedfor, coalesce(sum(loan), 0) as loan, coalesce(sum(coop_loan), 0) as coop_loan, '
                           'coalesce(sum(coop_savings), 0) as coop_savings, coalesce(sum(coop_deduction), 0) as cd, '
                           'coalesce(sum(adjustment), 0) as ad, coalesce(sum(deductions), 0) as ded, coalesce(sum(netpay), 0) as netpay, '
                           'count(*) as num, coalesce(sum(socialcontrib), 0) as social '
                           'from salary '
                           'left join employees '
                           'on salary.emp_id = employees.id '
                           'where month = %s and year =%s and employees.branch=%s group by employees.branch', (month, year, office))
            res = cursor.fetchone()
            if res:
                return res


def changeMonth(getMonth):
    month = datetime.datetime.strptime(getMonth, '%B').strftime('%b')
    return month


def fetch_perc(emp_id):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('SELECT percentage FROM account_info WHERE emp_id={}'.format(emp_id))
        res = cursor.fetchone()
        return res[0]


def update_setting(column_name, value):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('SELECT {} FROM oops'.format(column_name))
        res = cursor.fetchone()
        if res is None:
            cursor.execute('INSERT INTO oops({}) VALUES(%s)'.format(column_name), (value,))
            if cursor:
                return 'New Success'
        else:
            cursor.execute('UPDATE oops SET {}=%s'.format(column_name), (value,))
            if cursor:
                return 'Successful'


def get_table_column(tablename, column):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('SELECT {} FROM {}'.format(column, tablename))
        res = cursor.fetchone()
        if res is not None:
            return res[0]
        else:
            return None



def resetperc(value):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('SELECT salary_perc FROM oops')
        res = cursor.fetchone()
        if res is None:
            cursor.execute('INSERT INTO oops(salary_perc) VALUES(%s)', (value,)) 
        else:
            cursor.execute('UPDATE oops SET salary_perc=%s', (value,))
        cursor.execute('UPDATE account_info SET percentage=%s', (value,))
        if cursor:
            return 'Percentage reset'

def salary(column_name, year):
    with CursorFromConnectionPool() as cursor:
      cursor.execute("SELECT month, coalesce(sum({}), 0) FROM salary WHERE year=%s GROUP BY month ORDER BY \
                      to_date(month, 'Month')".format(column_name), (year, ))
      res = cursor.fetchall()
      if res:
        return res


def update_supervisor(name, deptid, emp_id, department):
    with CursorFromConnectionPool() as cursor:
        cursor.execute("UPDATE department SET supervisor=%s WHERE id=%s", (name, deptid))
        cursor.execute("UPDATE employees SET role=%s WHERE department=%s", (' ', department))
        cursor.execute("UPDATE employees SET role=%s WHERE id=%s and department=%s", ('supervisor', emp_id, department))


def take_charge(name, department, emp_id):
    with CursorFromConnectionPool() as cursor:
        cursor.execute("UPDATE department SET supervisor=%s WHERE name=%s", (name, department))
        cursor.execute("UPDATE employees SET role=%s WHERE department=%s and role != 'supervisor' ", (' ', department))
        cursor.execute("UPDATE employees SET role=%s WHERE id=%s and role != 'supervisor' and department=%s", ('taking-charge', emp_id, department))


def in_charge(department):
    with CursorFromConnectionPool() as cursor:
        cursor.execute("SELECT supervisor FROM department WHERE name=%s", (department,))
        res = cursor.fetchone()
        if res is not None:
          return res[0]


class System_settings(object):
    """docstring for System_settings"""
    def __init__(self, arg):
        self.arg = arg

    def __repr__(self):
        pass

    @classmethod
    def settings(cls):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM oops')
            res = cursor.fetchone()
            if res:
                return res
        