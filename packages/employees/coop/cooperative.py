from packages.database import CursorFromConnectionPool
from datetime import datetime


class Cooperative:
    def __init__(self, emp_id=None):
        self.id = emp_id

    def __repr__(self):
        pass

    def get_users(self, status=1):
         with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT employees.id, employees.name, employees.department, employees.post, '
                           'employees.email, permission.active, employees.staff_id, employees.coop '
                           'FROM employees '
                           'LEFT JOIN permission '
                           'ON employees.id = permission.emp_id '
                           'WHERE permission.active=%s '
                           'ORDER BY employees.staff_id ASC', (status,))
            fetch_all = cursor.fetchall()
            if fetch_all is not None:
                return fetch_all

    @classmethod
    def add_coop_member(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM cooperative WHERE emp_id=%s', (emp_id,))
            chk_exist = cursor.fetchone()
            if not chk_exist:
                cursor.execute('INSERT INTO cooperative (emp_id, status) VALUES(%s, %s)', (emp_id, 'Active'))
            else:
                cursor.execute('UPDATE cooperative SET status=%s WHERE emp_id=%s', ('Active', emp_id))
            
            
            cursor.execute('UPDATE employees SET coop=%s WHERE id=%s', ('Yes', emp_id))
            if Cooperative(emp_id=emp_id).__amount_to_save() is True:
                return True


    @classmethod
    def delete_coop_member(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE cooperative SET status=%s WHERE emp_id=%s', ('Deactivate', emp_id))
            if cursor:
                cursor.execute('UPDATE employees SET coop=%s WHERE id=%s', (None, emp_id))
                return True

    @classmethod
    def chk_coop_emp(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM cooperative WHERE status=%s and emp_id=%s', ('Active', emp_id))
            coop_exist = cursor.fetchone()
            if coop_exist:
                return coop_exist

    @classmethod
    def coop_emp(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM cooperative WHERE emp_id=%s', (emp_id,))
            coop_exist = cursor.fetchone()
            if coop_exist:
                return coop_exist

    
    def __amount_to_save(self):
        # minimum amount to save
        amount_save = 5000
        with CursorFromConnectionPool() as cursor:
            cursor.execute("INSERT INTO coop_set(emp_id, contribution) VALUES(%s, %s)", (self.id, amount_save))
            if cursor:
                return True

    def update_contribution(self, amount):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT * FROM coop_set WHERE emp_id=%s", (self.id,))
            is_added = cursor.fetchone()

            if is_added is None:
                Cooperative(emp_id=self.id).__amount_to_save()

            cursor.execute("UPDATE coop_set SET contribution=%s WHERE emp_id=%s", (amount, self.id))
            if cursor:
                return True

    def getAmount(self):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("SELECT contribution FROM coop_set WHERE emp_id=%s", (self.id, ))
            result = cursor.fetchone()
            if result:
                return result[0]
            else:
                return 0


    # Not used
    # @classmethod
    # def month_report(cls, emp_id, month):
    #     with CursorFromConnectionPool() as cursor:
    #         cursor.execute('SELECT * FROM coopdetails WHERE month=%s and emp_id=%s', (month, emp_id))
    #         res = cursor.fetchone()
    #         return res


    @classmethod
    def check_loan_details(cls, emp_id, category):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM loan WHERE emp_id=%s and loan_category=%s', (emp_id, category))
            pd = cursor.fetchall()
            return pd

    # not in use
    # @classmethod
    # def perform_coop_deduction(cls, emp_id):
    #     with CursorFromConnectionPool() as cursor:
    #         cursor.execute('SELECT GHI_CMS FROM permission WHERE emp_id=%s', (emp_id,))
    #         deduct = cursor.fetchone()
    #         return deduct

    @classmethod
    def lastdeduction(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM coopdetails WHERE emp_id=%s ORDER BY id DESC LIMIT 1', (emp_id,))
            res = cursor.fetchone()
            if res:
                return res

    @classmethod
    def deduction(cls, emp_id, salary):
        get_record = Cooperative.chk_coop_emp(emp_id)
        get_last_deduction = Cooperative.lastdeduction(get_record[1])
        
        # perform monthly contribution
        mcont = m_contribution(salary)
        msocial = m_social_welfare(mcont['salary'])
        salary = msocial['salary']

        # perform loan deduction if any
        if get_last_deduction is None:
            loan_outstanding = get_record[5]
        else:
            loan_outstanding = get_last_deduction[6]

        if loan_outstanding is not 0:
            rtn_details = payback_loan(emp_id, salary, get_record[9])
            final_salary = rtn_details['salary']
            emp_loan = rtn_details['loan']
            amountpay = rtn_details['amountpay']
            get_loan_outstanding = rtn_details['outstanding']
            if get_loan_outstanding < 0:
                get_loan_outstanding = 0
        else:
            final_salary = salary
            emp_loan = get_record[4]
            amountpay = 0
            get_loan_outstanding = get_record[5]

        emp_contribution = mcont['contribution']
        emp_social = msocial['contribution']
        emp_salary = final_salary
        all_contribution = (emp_contribution, emp_social)
        total_contribution = sum(all_contribution)
        emp_loan_outstanding = '{:.2f}'.format(get_loan_outstanding)
        emp_amountpay = '{:.2f}'.format(amountpay)

        # save record to db
        save_monthly_deduction(emp_id, emp_contribution, emp_social, emp_loan, emp_loan_outstanding, emp_amountpay,
                               total_contribution)

        value = {
            'contribution': emp_contribution,
            'social': emp_social,
            'loan': emp_amountpay,
            'salary': emp_salary
        }
        return value

    @classmethod
    def new_loan(cls, emp_id, loan, repay, percrate, repayment_perc):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE cooperative SET loan=%s, outstanding=%s, loan_percent=%s, repayment_perc=%s '
                           'WHERE emp_id=%s',
                           (loan, repay, percrate, repayment_perc, emp_id))
            if cursor:
                return 'Loan Record Successfully saved'

    @classmethod
    def loan_deduction(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM coopdetails WHERE emp_id=%s', (emp_id,))
            res = cursor.fetchall()
            return res


# def m_contribution(get_salary):
#     mc_value = 500  # could be changed
#     rtn_salary = get_salary - mc_value
#     get_mnth_pay = mc_value
#     mcon = {
#         'salary': rtn_salary,
#         'contribution': get_mnth_pay
#     }
#     return mcon


# def m_social_welfare(get_salary):
#     sw_value = 200  # could be changed
#     rtn_salary = get_salary - sw_value
#     get_mnth_social = sw_value
#     sw_con = {
#         'salary': rtn_salary,
#         'contribution': get_mnth_social
#     }
#     return sw_con


# def payback_loan(emp_id, get_salary, repayment_perc):
#     with CursorFromConnectionPool() as cursor:
#         cursor.execute('SELECT loan, outstanding, loan_percent FROM cooperative WHERE emp_id=%s', (emp_id,))
#         emp_loan_record = cursor.fetchone()
#         emp_loan = emp_loan_record[0]
#         emp_loan_outstanding = emp_loan_record[1]
#         emp_loan_percentage = emp_loan_record[2]

#         # deduct 10% of emp salary for loan payback
#         if emp_loan_outstanding is not None:
#             loan_repayment = _get_percentage(repayment_perc, get_salary)
#             if loan_repayment > emp_loan_outstanding:
#                 rtn_emp_salary = get_salary - emp_loan_outstanding
#                 amountpay = emp_loan_outstanding
#                 new_emp_loan_outstanding = 0
#             else:
#                 rtn_emp_salary = get_salary - loan_repayment
#                 new_emp_loan_outstanding = emp_loan_outstanding - loan_repayment
#                 amountpay = loan_repayment

#             # rtn_emp_salary = get_salary - loan_repayment

#             loan_details = {
#                 'salary': rtn_emp_salary,
#                 'loan': emp_loan,
#                 'outstanding': new_emp_loan_outstanding,
#                 'amountpay': amountpay
#             }
#             return loan_details
#         else:
#             no_loan = {
#                 'salary': get_salary,
#                 'loan': 0,
#                 'outstanding': 0,
#                 'amountpay': 0
#             }
#             return no_loan


# def save_monthly_deduction(emp_id, contribution, socialwelfare, loan, outstanding, amountpay, total):
#     month = datetime.today().strftime('%B')
#     year = datetime.today().strftime('%Y')
#     with CursorFromConnectionPool() as cursor:
#         cursor.execute('SELECT emp_id, month from coopdetails WHERE emp_id=%s and month=%s and year=%s',
#                        (emp_id, month, year))
#         chk_record = cursor.fetchone()
#         if not chk_record:
#             cursor.execute(
#                 'INSERT INTO coopdetails(emp_id, month, year, contribution, socialwelfare, loan, outstanding, '
#                 'repayment, total) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id',
#                 (emp_id, month, year, contribution, socialwelfare, loan, outstanding, amountpay, total))
#             save_record = cursor.fetchone()
#             if save_record:
#                 cursor.execute('SELECT coalesce(sum(contribution), 0) as contribution, coalesce(sum(socialwelfare), 0) '
#                                'as socialwelfare, coalesce(sum(outstanding), 0) as outstanding '
#                                'FROM coopdetails '
#                                'WHERE emp_id=%s', (emp_id,))
#                 res = cursor.fetchone()
#                 cont = res[0]
#                 sw = res[1]
#                 coop_emp = (cont, sw)
#                 total_cont = sum(coop_emp)

#                 cursor.execute('UPDATE cooperative SET contribution=%s, socialwelfare=%s, total=%s, loan=%s, '
#                                'outstanding=%s '
#                                'WHERE emp_id=%s',
#                                (cont, sw, total_cont, loan, outstanding, emp_id))
#         else:
#             cursor.execute(
#                 'UPDATE coopdetails SET month=%s, year=%s, contribution=%s, socialwelfare=%s, loan=%s, outstanding=%s, '
#                 'repayment=%s, total=%s WHERE emp_id=%s',
#                 (month, year, contribution, socialwelfare, loan, outstanding, amountpay, total, emp_id))
#             if cursor:
#                 cursor.execute('SELECT coalesce(sum(contribution), 0) as contribution, coalesce(sum(socialwelfare), 0) '
#                                'as socialwelfare, coalesce(sum(outstanding), 0) as outstanding '
#                                'FROM coopdetails '
#                                'WHERE emp_id=%s', (emp_id,))
#                 res = cursor.fetchone()
#                 cont = res[0]
#                 sw = res[1]
#                 coop_emp = (cont, sw)
#                 total_cont = sum(coop_emp)

#                 cursor.execute('UPDATE cooperative SET contribution=%s, socialwelfare=%s, total=%s, loan=%s, '
#                                'outstanding=%s '
#                                'WHERE emp_id=%s',
#                                (cont, sw, total_cont, loan, outstanding, emp_id))


def _get_percentage(get_percentage, get_amount):
    if get_percentage is not None:
        stp1 = get_percentage / 100
        stp2 = stp1 * get_amount
        return stp2
    else:
        return 0
