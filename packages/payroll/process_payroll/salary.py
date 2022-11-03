from flask import flash, redirect, url_for
from packages.database import CursorFromConnectionPool
from datetime import datetime
import calendar
from packages.functions import fetch_perc
from packages.payroll.process_payroll.salaryOop import Basic, Loan, Coop, Adjustment, Save_salary, Salary_ops, socialcontrib
from packages.employees.coop.cooperative import Cooperative


class Salary:
    def __init__(self, emp_name=None):
        self.name = emp_name

    def __repr__(self):
        return "<{}>".format(self.name)


    @classmethod
    def process_salary(cls, emp_id, percentage, days, month, year):
      
      if int(days) != 0:
        basic = Basic(get_id=emp_id).salary_info(percentage=percentage)
        amount_worked_for = Basic(get_id=emp_id).rate_worked_for(days=days, percentage=percentage)
        if amount_worked_for is False:
            return 101 # days invalid

        salary = amount_worked_for['workedfor'] 
          
        # loan deduction
        to_deduct_loan = Salary_ops().deduct(column_name='loan_deduction')
        if to_deduct_loan == int(1):
            loan_deduction = Loan(get_id=emp_id).deduct_loan(salary=salary, month=month, year=year)
            if loan_deduction is False:
                return 102  # loan payment process failed
            else:
                if loan_deduction is None:
                    loan = 0 
                    #rtn_salary = salary       
                else:
                    loan = loan_deduction['loan']
                    salary = loan_deduction['salary']
        else:
            #print('Loan not process')
            loan = 0
              
        #coop loan deduction
        to_deduct_coop_loan = Salary_ops().deduct(column_name='coop_loan_deduction')
        if to_deduct_coop_loan == int(1):
            coop_loan = Coop(get_id=emp_id).coop_loan_deduct(salary=salary, month=month, year=year)
            if coop_loan is False:
                return 103  # coop loan process failed
            else:
                if coop_loan is None:
                    coop = 0
                    outstanding = 0
                    #rtn_coop_salary = rtn_salary
                else:
                    coop = coop_loan['coop_loan']
                    salary = coop_loan['salary']
                    outstanding = coop_loan['outstanding']
        else:
            #print('Coop loan not processed')
            coop = 0
            #rtn_coop_salary = rtn_salary

        # coop deduction
        to_contribute = Salary_ops().deduct(column_name='coop_contribution')
        if to_contribute == int(1):
            coop_contribution = Coop(get_id=emp_id).coop_contribution(salary=salary)
            if coop_contribution is not None:
                salary = coop_contribution['salary']
                contribution = coop_contribution['contribution']
                
                # sum all coop deduction 
                all_coop_dedcutions = (coop, contribution)
                coop_deductions = sum(all_coop_dedcutions)
            else:
                contribution = 0             


            cooperative = {
                'coop_loan': coop,
                'contribution':contribution
            }

        else:
            #print('No monthly coop contribution performed')
            #rtn_coop_contribution_salary = rtn_coop_salary
            cooperative = {
                'coop_loan': 0,
                'contribution':0
            }

            contribution = 0

        
        # monthly social contribution
        s_contrib = socialcontrib(salary=salary).deduct_social()
        salary = s_contrib['salary']
        social__contrib = s_contrib['contribution']

        

        # adjustment
        now = datetime.today().now()
        previous_month = calendar.month_name[now.month - 1 if now.month > 1 else 12]

        adjustment = Adjustment(get_id=emp_id, month=previous_month, year=year).make_adjustment(salary=salary)
        if adjustment is not None:
            operation = adjustment['operation']
            salary = adjustment['salary']
            adj_amount = adjustment['amount']
        else:
            operation = None
            #rtn_adj_salary = rtn_coop_contribution_salary
            adj_amount = 0


        if operation == 'deduct':
            adj_deduct = adj_amount
        else:
            adj_deduct = 0

        deductions = (basic['tax'], basic['pension'], loan, coop, contribution, social__contrib, adj_deduct)
        month_deduction = sum(deductions)

        coop_savings = contribution
        coop_deduction = sum((coop, contribution))


        #salary = rtn_adj_salary

        net_pay = salary

        date_process = datetime.today().strftime('%c')

        info = {
          'basic': basic,
          'workedfor': amount_worked_for,
          'loan': loan,
          'coop': coop,
          'cooperative': cooperative,
          'coop_deduction': coop_deduction,
          'deduction': month_deduction,
          'monthly_social': social__contrib,
          'adjustment': adjustment,
          'netpay': net_pay,
          'bankname': basic['bankname'],
          'accountnum': basic['accountnum']
        }

        # save cooperative details
        is_member = Cooperative.chk_coop_emp(emp_id=emp_id)
        if is_member is not None:
          total = sum((info['cooperative']['contribution'], info['coop']))
          save_coop = Save_salary.save_coop_record(emp_id=emp_id, month=month, year=year, contribution=info['cooperative']['contribution'],
                                                    loan=info['coop'], total=total)

        
      else:
        basic = {
          'basic': 0,
          'allowances': 0,
          'gross': 0,
          'cra': 0,
          'tax': 0,
          'pension': 0,
          'salary': 0,
          'employer_savings': 0,
          'relief': 0,
          'bankname': 0,
          'accountnum': 0
        }

        amount_worked_for = {
          'days': 0,
          'workedfor': 0,
          'absent': 0
        }

        loan, coop, coop_savings, coop_deduction, month_deduction, adj_amount, net_pay = 0, 0, 0, 0, 0, 0, 0
        date_process = datetime.today().strftime('%c')
        social__contrib = 0

        info = {
          'basic': 0,
          'workedfor': 0,
          'loan': 0,
          'coop': 0,
          'cooperative': 0,
          'coop_deduction': 0,
          'deduction': 0,
          'monthly_social': 0,
          'adjustment': 0,
          'netpay': 0,
          'bankname': None,
          'accountnum': None
        }

      save_info = Save_salary(emp_id=emp_id, month=month, year=year, percentage=percentage, basic=basic['basic'], allowances=basic['allowances'], gross=basic['gross'], 
                              pension=basic['pension'], employer_savings=basic['employer_savings'], relief=basic['relief'], tax=basic['tax'], 
                              workedfor=amount_worked_for['workedfor'] , loan_deduction=loan, coop_loan_deduction=coop, coop_savings=coop_savings, 
                              coop_total_deduction=coop_deduction, total_deduction=month_deduction, adjustment=adj_amount, 
                              present=amount_worked_for['days'], absent=amount_worked_for['absent'], netpay=net_pay, 
                              date_process=date_process, monthly_social=social__contrib, 
                              bankname=info['bankname'], accountnum=info['accountnum']).save_record()

      
      if save_info is True:
          return info


    @classmethod
    def revert_det(cls, emp_id, month, year):
      with CursorFromConnectionPool() as cursor:
        revert_loan = Loan.loan_revert(empid=emp_id, month=month, year=year)
        if revert_loan is True or revert_loan == 0:
          coop_revert = Coop(get_id = emp_id).revert()
          if coop_revert is True or coop_revert == 0:
            cursor.execute("DELETE FROM salary WHERE emp_id=%s and month=%s and year=%s", (emp_id, month, year))
            cursor.execute("DELETE FROM attendance WHERE emp_id=%s and month=%s and year=%s", (emp_id, month, year))
            if cursor:
              return True


    @classmethod
    def revertall(cls, month, year):
      with CursorFromConnectionPool() as cursor:
        cursor.execute("SELECT * FROM salary WHERE month=%s and year=%s", (month, year))
        response = cursor.fetchall()
        if response:
          for i in range(len(response)):
            revert_loan = Loan.loan_revert(empid=response[i][1], month=month, year=year)
            if revert_loan is True or revert_loan == 0:
              coop_revert = Coop(get_id = response[i][1]).revert()
              if coop_revert is True or coop_revert == 0:
                cursor.execute("DELETE FROM salary WHERE emp_id=%s and month=%s and year=%s", (response[i][1], month, year))
                cursor.execute("DELETE FROM attendance WHERE emp_id=%s and month=%s and year=%s", (response[i][1], month, year))
              else:
                # error revertin coop record
                print('Error reverting coop record')

            else:
              # error reverting loan
              print('Error reverting loan record')

          return True
        else:
          return None


    @classmethod
    def chk_salary_per_month(cls, emp_id, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT emp_id, month, year, finalized FROM salary WHERE  emp_id=%s and month=%s and '
                           'year=%s and finalized=%s '
                           'LIMIT 1', (emp_id, month, year, 'Yes'))
            res = cursor.fetchone()
            return res

    @classmethod
    def chk_process_salary_per_month(cls, emp_id, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT emp_id, month, year FROM salary WHERE emp_id=%s and month=%s and year=%s '
                           'LIMIT 1', (emp_id, month, year))
            res = cursor.fetchone()
            return res

    @classmethod
    def chk_processed_salary(cls, month):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * from salary WHERE month=%s', (month,))
            res = cursor.fetchall()
            return res

    @classmethod
    def get_salary_info(cls, emp_id, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM salary WHERE emp_id=%s and month=%s and year=%s',
                           (emp_id, month, year))
            res = cursor.fetchone()
            if res:
              info = {
                  'slip_no': 'SLIP/00'+str(res[0]),
                  'emp_id': res[1],
                  'month': res[2],
                  'year': res[3],
                  'percentage': res[4],
                  'basic': res[5],
                  'allowance': res[6],
                  'gross': res[7],
                  'pension': res[8],
                  'employer': res[9],
                  'relief': res[10],
                  'tax': res[11],
                  'workedfor': res[12],
                  'loan': res[13],
                  'coop_loan': res[14],
                  'coop_savings': res[15],
                  'coop_deduction': res[16],
                  'adjustment': res[17],
                  'deduction': res[18],
                  'present': res[19],
                  'absent': res[20],
                  'netpay': res[21],
                  'monthly_social': res[24],
              }
              return info

    @classmethod
    def finalise(cls, emp_id, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE salary SET finalized=%s WHERE emp_id=%s and month=%s and year=%s',
                           ('Yes', emp_id, month, year))
            if cursor:
              return True

    @classmethod
    def finalise_all(cls, month, year):
        with CursorFromConnectionPool() as cursor:
          cursor.execute('UPDATE salary SET finalized=%s WHERE month=%s and year=%s',
                          ('Yes', month, year))

    @classmethod
    def listper_month(cls, month, year, office=None):
        with CursorFromConnectionPool() as cursor:
          if office:
            cursor.execute('select employees.name, salary.month, salary.year, salary.perc, salary.basic, '
                           'salary.allowance, salary.gross, salary.pension, salary.employer_savings, salary.relief, '
                           'salary.tax, salary.workedfor, salary.loan, salary.coop_loan, salary.coop_savings, '
                           'salary.coop_deduction, salary.adjustment, salary.deductions, attendance.present, attendance.absent, '
                           'salary.netpay, salary.socialcontrib, employees.staff_id '                           
                           'from employees '
                           'left join salary '
                           'on salary.emp_id = employees.id '
                           'left join attendance '
                           'on employees.id = attendance.emp_id '
                           'where salary.month = %s and salary.year = %s and attendance.month = %s and '
                           'attendance.year= %s and employees.branch=%s order by employees.staff_id ', 
                           (month, year, month, year, office))
            res = cursor.fetchall()
          else:
            cursor.execute('select employees.name, salary.month, salary.year, salary.perc, salary.basic, '
                           'salary.allowance, salary.gross, salary.pension, salary.employer_savings, salary.relief, '
                           'salary.tax, salary.workedfor, salary.loan, salary.coop_loan, salary.coop_savings, '
                           'salary.coop_deduction, salary.adjustment, salary.deductions, attendance.present, attendance.absent, '
                           'salary.netpay, salary.socialcontrib, employees.staff_id '                           
                           'from employees '
                           'left join salary '
                           'on salary.emp_id = employees.id '
                           'left join attendance '
                           'on employees.id = attendance.emp_id '
                           'where salary.month = %s and salary.year = %s and attendance.month = %s and '
                           'attendance.year= %s order by employees.staff_id ', (month, year, month, year))
            res = cursor.fetchall()

          if res:
            return res
          

    @classmethod
    def emp_month_report(cls, emp_id, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select employees.name, salary.month, salary.year, salary.perc, salary.basic, '
                           'salary.allowance, salary.gross, salary.pension, salary.employer_savings, salary.relief, '
                           'salary.tax, salary.workedfor, salary.loan, salary.coop_loan, salary.coop_savings, '
                           'salary.coop_deduction, salary.adjustment, salary.deductions, attendance.present, attendance.absent, '
                           'salary.netpay, employees.id, salary.socialcontrib, employees.staff_id, salary.bankname, salary.bankacct '                           
                           'from employees '
                           'left join salary '
                           'on employees.id = salary.emp_id '
                           'left join attendance '
                           'on employees.id = attendance.emp_id '
                           'where salary.emp_id = %s and salary.month=%s and salary.year=%s and salary.finalized =%s',
                           (emp_id, month, year, 'Yes'))
            res = cursor.fetchone()
            return res

    @classmethod
    def emp_year_report(cls, emp_id, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select employees.name, salary.month, salary.year, salary.perc, salary.basic, '
                           'salary.allowance, salary.gross, salary.pension, salary.employer_savings, salary.relief, '
                           'salary.tax, salary.workedfor, salary.loan, salary.coop_loan, salary.coop_savings, '
                           'salary.coop_deduction, salary.adjustment, salary.deductions, '
                           'salary.netpay, employees.id, salary.socialcontrib, salary.bankname, salary.bankacct '                           
                           'from employees '
                           'left join salary '
                           'on employees.id = salary.emp_id '
                           'where salary.emp_id = %s and salary.year=%s and salary.finalized =%s order by salary.id asc',
                           (emp_id, year, 'Yes'))
            res = cursor.fetchall()
            if res:
                return res

    @classmethod
    def emp_year_sum(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('CREATE OR REPLACE VIEW total_sum AS '
                           'select coalesce(sum(basic), 0) as basic, '
                           'coalesce(sum(allowance), 0) as allowance, coalesce(sum(gross), 0) as gross, coalesce(sum(pension), 0) as pension, '
                           'coalesce(sum(employer_savings), 0) as Esavings, coalesce(sum(relief), 0) as relief, coalesce(sum(tax), 0) as tax, '
                           'coalesce(sum(workedfor), 0) as workedfor, coalesce(sum(loan), 0) as loan, coalesce(sum(coop_loan), 0) as coop_loan, '
                           'coalesce(sum(coop_savings), 0) as coop_savings, coalesce(sum(coop_deduction), 0) as cd, '
                           'coalesce(sum(adjustment), 0) as ad, coalesce(sum(deductions), 0) as ded, '
                           'coalesce(sum(netpay), 0) as netpay, coalesce(sum(socialcontrib), 0) as social '
                           'FROM salary '
                           'WHERE salary.emp_id=%s and finalized=%s '
                           'GROUP BY salary.emp_id', (emp_id, "Yes"))
            if cursor:
                cursor.execute('SELECT * FROM total_sum')
                res = cursor.fetchone()
                result = {
                    'basic': res[0], 'workedfor': res[7],
                    'gross': res[2], 'pension': res[3],
                    'tax': res[6], 'netpay': res[14],
                    'loan': res[8], 'cloan': res[9], 'csw': res[10], 'deduction': res[13], 'social': res[15]
                }
                return result

    @classmethod
    def bankreport(cls, bank_name, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select employees.name, salary.month, salary.year, salary.netpay, account_info.bank_name, '
                           'account_info.bank_acct, employees.staff_id '
                           'from salary '
                           'inner join account_info '
                           'on salary.emp_id = account_info.emp_id '
                           'inner join employees '
                           'on salary.emp_id = employees.id '
                           'where account_info.bank_name = %s and salary.month = %s and salary.year = %s',
                           (bank_name, month, year))
            res = cursor.fetchall()
            return res

    @classmethod
    def all_bankreport(cls, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select employees.name, salary.month, salary.year, salary.netpay, account_info.bank_name, '
                           'account_info.bank_acct, employees.staff_id '
                           'from salary '
                           'inner join account_info '
                           'on salary.emp_id = account_info.emp_id '
                           'inner join employees '
                           'on salary.emp_id = employees.id '
                           'where salary.month = %s and salary.year = %s',
                           (month, year))
            res = cursor.fetchall()
            return res

    @classmethod
    def sum_bank_report(cls, bank_name, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('CREATE OR REPLACE VIEW Bank_sum AS '
                           'select employees.name, salary.month, salary.year, salary.netpay, account_info.bank_name, '
                           'account_info.bank_acct, employees.staff_id '
                           'from salary '
                           'inner join account_info '
                           'on salary.emp_id = account_info.emp_id '
                           'inner join employees '
                           'on salary.emp_id = employees.id '
                           'where account_info.bank_name = %s and salary.month = %s and salary.year = %s',
                           (bank_name, month, year))
            if cursor:
                cursor.execute('select count(*), coalesce(sum(netpay), 0) as total_salary from Bank_sum')
                res = cursor.fetchone()
                return res

    @classmethod
    def sum_all_bank_report(cls, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('CREATE OR REPLACE VIEW all_Bank_sum AS '
                           'select employees.name, salary.month, salary.year, salary.netpay, account_info.bank_name, '
                           'account_info.bank_acct, employees.staff_id '
                           'from salary '
                           'inner join account_info '
                           'on salary.emp_id = account_info.emp_id '
                           'inner join employees '
                           'on salary.emp_id = employees.id '
                           'where salary.month = %s and salary.year = %s',
                           (month, year))
            if cursor:
                cursor.execute('select count(*), coalesce(sum(netpay), 0) as total_salary from all_Bank_sum')
                res = cursor.fetchone()
                return res

    @classmethod
    def pfareport(cls, pfa_name, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select employees.name, salary.month, salary.year, salary.pension, emppension.pen_name, '
                           'emppension.pen_num, salary.employer_savings, employees.staff_id '
                           'from salary '
                           'inner join emppension '
                           'on salary.emp_id = emppension.emp_id '
                           'inner join employees '
                           'on salary.emp_id = employees.id '
                           'where emppension.pen_name = %s and salary.month = %s and salary.year = %s',
                           (pfa_name, month, year))
            res = cursor.fetchall()
            return res

    @classmethod
    def all_pfareport(cls, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select employees.name, salary.month, salary.year, salary.pension, emppension.pen_name, '
                           'emppension.pen_num, salary.employer_savings, employees.staff_id '
                           'from salary '
                           'inner join emppension '
                           'on salary.emp_id = emppension.emp_id '
                           'inner join employees '
                           'on salary.emp_id = employees.id '
                           'where salary.month = %s and salary.year = %s',
                           (month, year))
            res = cursor.fetchall()
            return res

    @classmethod
    def sum_pfa_report(cls, pfa_name, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('CREATE OR REPLACE VIEW pension_sum AS '
                           'select employees.name, salary.month, salary.year, salary.pension, emppension.pen_name, '
                           'emppension.pen_num, salary.employer_savings, employees.staff_id '
                           'from salary '
                           'inner join emppension '
                           'on salary.emp_id = emppension.emp_id '
                           'inner join employees '
                           'on salary.emp_id = employees.id '
                           'where emppension.pen_name = %s and salary.month = %s and salary.year = %s',
                           (pfa_name, month, year))
            if cursor:
                cursor.execute('select count(*), coalesce(sum(pension), 0) as employee_savings, '
                               'coalesce(sum(employer_savings), 0) as employer_savings '
                               'from pension_sum')
                res = cursor.fetchone()
                return res

    @classmethod
    def sum_all_pfa_report(cls, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('CREATE OR REPLACE VIEW all_pension_sum AS '
                           'select employees.name, salary.month, salary.year, salary.pension, emppension.pen_name, '
                           'emppension.pen_num, salary.employer_savings, employees.staff_id '
                           'from salary '
                           'inner join emppension '
                           'on salary.emp_id = emppension.emp_id '
                           'inner join employees '
                           'on salary.emp_id = employees.id '
                           'where salary.month = %s and salary.year = %s',
                           (month, year))
            if cursor:
                cursor.execute('select count(*), coalesce(sum(pension), 0) as employee_savings, '
                               'coalesce(sum(employer_savings), 0) as employer_savings '
                               'from all_pension_sum')
                res = cursor.fetchone()
                return res

    @classmethod
    def payereport(cls, state, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select employees.name, employees.state, account_info.tax_number, salary.month, '
                           'salary.year, salary.tax, employees.staff_id '
                           'from employees '
                           'inner join account_info '
                           'on employees.id = account_info.emp_id '
                           'inner join salary '
                           'on account_info.emp_id = salary.emp_id '
                           'where employees.state = %s and salary.month= %s and salary.year=%s',
                           (state, month, year))
            res = cursor.fetchall()
            return res

    @classmethod
    def payereport_all(cls, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select employees.name, employees.state, account_info.tax_number, salary.month, '
                           'salary.year, salary.tax, employees.staff_id '
                           'from employees '
                           'inner join account_info '
                           'on employees.id = account_info.emp_id '
                           'inner join salary '
                           'on account_info.emp_id = salary.emp_id '
                           'where salary.month= %s and salary.year=%s',
                           (month, year))
            res = cursor.fetchall()
            return res

    @classmethod
    def sum_tax_report(cls, state, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('CREATE OR REPLACE VIEW tax_sum AS '
                           'select employees.name, employees.state, account_info.tax_number, salary.month, '
                           'salary.year, salary.tax '
                           'from employees '
                           'inner join account_info '
                           'on employees.id = account_info.emp_id '
                           'inner join salary '
                           'on account_info.emp_id = salary.emp_id '
                           'where employees.state = %s and salary.month= %s and salary.year=%s',
                           (state, month, year))
            if cursor:
                cursor.execute('select count(*), coalesce(sum(tax), 0) as total_tax from tax_sum')
                res = cursor.fetchone()
                return res

    @classmethod
    def sum_all_tax_report(cls, month, year):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('CREATE OR REPLACE VIEW all_tax_sum AS '
                           'select employees.name, employees.state, account_info.tax_number, salary.month, '
                           'salary.year, salary.tax '
                           'from employees '
                           'inner join account_info '
                           'on employees.id = account_info.emp_id '
                           'inner join salary '
                           'on account_info.emp_id = salary.emp_id '
                           'where salary.month= %s and salary.year=%s',
                           (month, year))
            if cursor:
                cursor.execute('select count(*), coalesce(sum(tax), 0) as total_tax from all_tax_sum')
                res = cursor.fetchone()
                return res

    @classmethod
    def adjustment(cls, emp_id, month, year, reason, adj_type, amount, date):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT month, year FROM adjustment WHERE emp_id=%s and month=%s and year=%s',
                           (emp_id, month, year))
            response = cursor.fetchone()
            if response:
                cursor.execute('UPDATE adjustment SET reason=%s, adj_type=%s, amount=%s, date=%s '
                               'WHERE emp_id=%s and month=%s and year=%s', (reason, adj_type, amount, date, emp_id,
                                                                            month, year))
                if cursor:
                    return 'Adjustment Modified'
                else:
                    return 'Error Modifying Adjustment'
            else:
                cursor.execute('INSERT INTO adjustment(emp_id, month, year, reason, adj_type, amount, date) '
                               'VALUES(%s, %s, %s, %s, %s, %s, %s)RETURNING id', (emp_id, month, year, reason,
                                                                                  adj_type, amount, date))
                res = cursor.fetchone()
                if res:
                    return 'Adjustment created successfully'
                else:
                    return 'Error creating Adjustment'

    @classmethod
    def adjustment_list(cls, month, year, empid=None):
      with CursorFromConnectionPool() as cursor:
        cursor.execute("select employees.name, adjustment.month, adjustment.year, adjustment.reason, "
                        "adjustment.adj_type, adjustment.amount, adjustment.emp_id, adjustment.id "
                        "from adjustment "
                        "left join employees " 
                        "on adjustment.emp_id = employees.id " 
                        "where adjustment.year = %s and adjustment.month= %s", (year, month))
        if empid:
          res = cursor.fetchone()
        else:
          res = cursor.fetchall()
        
        return res


    @classmethod
    def deleteADJ(cls, deleteID):
      with CursorFromConnectionPool() as cursor:
        cursor.execute("DELETE FROM adjustment WHERE id=%s", (deleteID, ))
        if cursor:
          return True

          

    @classmethod
    def salary_list(cls):
      with CursorFromConnectionPool() as cursor:
        cursor.execute("SELECT * FROM salary")
        res = cursor.fetchall()
        if res is not None:
          return res
        else:
          return None

    ###########
    @classmethod
    def taxinformation(cls):
      with CursorFromConnectionPool() as cursor:
        cursor.execute("select employees.staff_id, employees.name, tax.taxable, tax.mintax, tax.highertax, tax.effective_tax, tax.band1,\
                tax.band2, tax.band3, tax.band4, tax.band5, tax.band6, tax.total_tax, tax.emp_id\
                from tax \
                left join employees\
                on tax.emp_id = employees.id \
                order by employees.staff_id asc")
        result = cursor.fetchall()
        if result is not None:
          return result


    @classmethod
    def emp_taxinfo(cls, emp_id):
      with CursorFromConnectionPool() as cursor:
        cursor.execute("select employees.staff_id, employees.name, tax.taxable, tax.mintax, tax.highertax, tax.effective_tax, tax.band1,\
                tax.band2, tax.band3, tax.band4, tax.band5, tax.band6, tax.total_tax, tax.emp_id\
                from tax \
                left join employees\
                on tax.emp_id = employees.id \
                where tax.emp_id=%s\
                order by employees.staff_id asc", (emp_id,))
        result = cursor.fetchall()
        if result is not None:
          return result

    ##########


def check_tax_profile(emp_tax_id):
    with CursorFromConnectionPool() as cursor:
        cursor.execute('SELECT * FROM tax WHERE emp_id = %s', (emp_tax_id,))
        res = cursor.fetchone()
        return res


def convert(getAmount):
    return '{:,.2f}'.format(getAmount)



