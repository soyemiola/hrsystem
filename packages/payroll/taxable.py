from packages.database import CursorFromConnectionPool
from packages.payroll.taxband import getband


class Taxable:
    def __init__(self, basic, OA):
        self.basic = basic
        self.HA = OA

    @classmethod
    def get_taxable(cls, basic, OA):
        _basic = float(basic)
        _OA = float(OA)
        get_gross = sum((_basic, _OA)) 
        get_pension = pension(8, get_gross)
        get_grosspay_cra = get_gross - get_pension
        get_cra = _consolidated_relief_allowance(get_grosspay_cra, 12) # new added function.
        # get_cra = _consolidated_relief_allowance(get_gross, 12)
        get_total_relief = total_relief(get_cra, get_pension)

        res = {
            "Gross": get_gross,
            "CRA": get_cra,
            "Pension": get_pension,
            "Total Relief": get_total_relief
        }
        return res

    @classmethod
    def processtax(cls, emp_id):
        # get account info n deduct ross from total relief to get taxable value
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select employees.id, employees.name, account_info.basic, account_info.total_a, '
                           'account_info.gross, account_info.cra, account_info.pension, account_info.total_relief '
                           'from account_info '
                           'left join employees '
                           'on employees.id = account_info.emp_id '
                           'where account_info.emp_id = %s', (emp_id,))
            res = cursor.fetchone()
            if res:                
                return res

    @classmethod
    def taxrecord(cls, emp_id, taxable, mintax, highertax, effective_tax, band1, band2, band3, band4, band5, band6,
                  total_tax):
        # check if tax has been calculated
        chk_emp = Taxable.tax_per_emp(emp_id)
        if not chk_emp:
            with CursorFromConnectionPool() as cursor:
                cursor.execute('INSERT INTO tax(emp_id, taxable, mintax, highertax, effective_tax, band1, band2, '
                               'band3, band4, band5, band6, total_tax) '
                               'VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ',
                               (emp_id, taxable, mintax, highertax, effective_tax, band1, band2, band3, band4,
                                band5, band6, total_tax))
                if cursor:
                    return 'New Tax Record Created'
        else:
            with CursorFromConnectionPool() as cursor:
                cursor.execute('UPDATE tax SET taxable=%s, mintax=%s, highertax=%s, effective_tax=%s, band1=%s, '
                               'band2=%s, band3=%s, band4=%s, band5=%s, band6=%s, total_tax=%s WHERE emp_id=%s',
                               (taxable, mintax, highertax, effective_tax, band1, band2, band3, band4,
                                band5, band6, total_tax, emp_id))
                if cursor:
                    return 'Record Updated Successfully'

    @classmethod
    def taxlist(cls, status=1):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select employees.id, employees.name, account_info.basic, account_info.total_a, '
                           'account_info.gross, account_info.cra, account_info.pension, account_info.total_relief, '
                           'tax.taxable, tax.mintax, tax.highertax, tax.effective_tax, tax.band1, tax.band2, '
                           'tax.band3, tax.band4, tax.band5, tax.band6, tax.total_tax, account_info.percentage, employees.staff_id '
                           'from employees '
                           'inner join account_info on employees.id = account_info.emp_id '
                           'left outer join tax on employees.id = tax.emp_id '
                           'left join permission on permission.emp_id = employees.id '
                           'where permission.active = %s order by employees.staff_id asc', (status,))
            res = cursor.fetchall()
            if res:
                return res
            else:
                return None
                

    @classmethod
    def tax_per_emp(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select * from tax where emp_id = %s', (emp_id,))
            res = cursor.fetchone()
            if res:
                return res

    @classmethod
    def get_emp_tax(cls, emp_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('select employees.id, employees.name, account_info.basic, account_info.total_a, '
                           'account_info.gross, account_info.cra, account_info.pension, account_info.total_relief, '
                           'tax.taxable, tax.mintax, tax.highertax, tax.effective_tax, tax.band1, tax.band2, '
                           'tax.band3, tax.band4, tax.band5, tax.band6, tax.total_tax '
                           'from employees '
                           'inner join account_info on employees.id = account_info.emp_id '
                           'left outer join tax on employees.id = tax.emp_id '
                           'where employees.id = %s', (emp_id,))
            res = cursor.fetchone()
            if res:
                return res


def _get_percentage(get_percentage, get_amount):
    stp1 = get_percentage / 100
    stp2 = stp1 * get_amount
    return stp2


def _consolidated_relief_allowance(get_gross_pay, get_month_spent):
    _cra = _get_percentage(20, get_gross_pay) + max(_get_percentage(1, get_gross_pay),
                                                    200000 * get_month_spent / 12)

    return _cra


def pension(get_percentage_value, gross_value):
    get_amount = gross_value
    rate = get_percentage_value
    perc = rate / 100
    get_value = perc * get_amount

    return get_value


def total_relief(get_cra, get_pension):
    sum_of_relief = get_cra + get_pension

    return sum_of_relief


def convert_to_float(getvalue):
    get_num = getvalue
    remove_str = get_num.replace(',', '')
    return float(remove_str)


def emptaxband(emp_id, gross, relief):
    emp_taxable = gross - relief
    emp_tax_details = getband(emp_taxable, gross)

    return emp_tax_details


def get_bands(taxable, getbands, get_id):
    emp_band1 = convert_to_float(getbands['Firstband'])
    emp_band2 = convert_to_float(getbands['Secondband'])
    emp_band3 = convert_to_float(getbands['Thirdband'])
    emp_band4 = convert_to_float(getbands['Fourthband'])
    emp_band5 = convert_to_float(getbands['Fifthband'])
    emp_band6 = convert_to_float(getbands['Sixthband'])
    emp_total_band = getbands['Total_tax']
    emp_min_tax = getbands['Minimum_tax']
    emp_hm_tax = getbands['HM_tax']
    emp_eff_tax = getbands['Effective_tax']

    Taxable.taxrecord(get_id, taxable, emp_min_tax, emp_hm_tax, emp_eff_tax, emp_band1, emp_band2, emp_band3,
                      emp_band4, emp_band5, emp_band6, emp_total_band)