from packages.database import CursorFromConnectionPool


def check_existing_user(email):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('SELECT * FROM employees WHERE email=%s', (email,))
        fetch_record = cursor.fetchone()
        if fetch_record is not None:
            return fetch_record
        else:
            return None


def new_user(name, address, city, mobile, department, post, email, branch, active_date, emp_class, state,
                    password, dob, staff_id, jobtitle, title, gender, nokin, nokinnumber, nokinemail, nokinrel):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('INSERT INTO employees(name, address, city, mobile, department, post, email, branch, '
                       'active_date, emp_class, state, password, dob, staff_id, jobtitle, title, gender) '
                       'VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id',
                       (name, address, city, mobile, department, post, email, branch, active_date, emp_class, state,
                        password, dob, staff_id, jobtitle, title, gender))
        get_last_id = cursor.fetchone()
        if get_last_id:
            # create next of kin info
            cursor.execute("INSERT INTO nextofkin(emp_id, nokname, noknumber, nokemail, nokrel) VALUES(%s, %s, %s, %s, %s)", 
                            (get_last_id, nokin, nokinnumber, nokinemail, nokinrel))
            if cursor:
                return get_last_id


def create_user_account_details(get_id, basic, house_a, transport_a, other_a, total_a, bank_name, bank_account, name,
                                tax_number):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('INSERT INTO account_info(emp_id, basic, house_a, transport_a, other_a, total_a, '
                       'bank_name, bank_acct, acct_name, tax_number, percentage) '
                       'VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id ',
                       (get_id, basic, house_a, transport_a, other_a, total_a, bank_name, bank_account, name,
                        tax_number, int(100)))
        get_acct_id = cursor.fetchone()
        return get_acct_id


def create_gcpt(gross, cra, pension, totalrelief, get_acct_id):
    d_rate = dailyrate(gross, 261)
    w_rate = dailyrate(gross, 52)
    with CursorFromConnectionPool() as cursor:
        cursor.execute('UPDATE account_info SET gross = %s, cra = %s, pension = %s, total_relief = %s, daily_rate=%s, weekly_rate=%s \
                        WHERE emp_id = %s',
                       (gross, cra, pension, totalrelief, d_rate, w_rate, get_acct_id))
        if cursor:            
            return 1
        else:
            return 0


def pension_profile(get_id, pen_name, pen_num):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('INSERT INTO emppension(emp_id, pen_name, pen_num) VALUES(%s, %s, %s)',
                       (get_id, pen_name, pen_num))
        if cursor:
            return 1
        else:
            return 0


def user_permit(get_id):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('INSERT INTO permission(emp_id, ghi_cms, m_report, loan, leave, active) '
                       'VALUES(%s, %s, %s, %s, %s, %s)', (get_id, 1, 1, 1, 1, 1))
        if cursor:
            return 1
        else:
            return 0


def dailyrate(annualpay, days):
    rate = annualpay / days
    return rate

