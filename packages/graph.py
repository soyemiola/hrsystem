from packages.database import CursorFromConnectionPool
from datetime import date, timedelta
import datetime



class servingterm:
    """docstring for servingterm"""
    def __init__(self, condition, value, value2=None):
        self.condition = condition
        self.value = value
        self.value2 = value2

    def term(self):
        return self.__servingterm()

    
    def __servingterm(self):
        with CursorFromConnectionPool() as cursor:
            if self.value2 is None:
                cursor.execute("CREATE or REPLACE VIEW longterm AS\
                                SELECT employees.active_date, count(*) FROM employees\
                                WHERE {}\
                                GROUP BY employees.active_date".format(self.condition), (self.value,))
            else:
                cursor.execute("CREATE or REPLACE VIEW longterm AS\
                                SELECT employees.active_date, count(*) FROM employees\
                                WHERE {}\
                                GROUP BY employees.active_date".format(self.condition), (self.value, self.value2))
            if cursor:
                cursor.execute("SELECT count(*) FROM longterm")
                res = cursor.fetchone()
                return res

	
    @classmethod
    def inactive_staff(cls):
    	with CursorFromConnectionPool() as cursor:
    		cursor.execute('SELECT * FROM offboarding');
    		result = cursor.fetchall()
    		if result:
    			return result

    @classmethod
    def active_staff(cls):
    	with CursorFromConnectionPool() as cursor:
    		cursor.execute('SELECT count(*) FROM employees');
    		result = cursor.fetchone()
    		if result:
    			return result

    @classmethod
    def getEmployementDate(cls, emp_id):
    	with CursorFromConnectionPool() as cursor:
	    	cursor.execute('SELECT active_date FROM employees WHERE id=%s LIMIT 1', (emp_id,))
	    	res = cursor.fetchone()
	    	return res[0]


    @classmethod
    def staff_turnover(cls):
        all_emp = servingterm.active_staff()
        all_inactive_emp = servingterm.inactive_staff()
        current_year = datetime.datetime.today().strftime('%Y')

        inactive_emp = []

        if all_inactive_emp:
            for i in range(len(all_inactive_emp)):
                emp_inactive_year = datetime.datetime.strptime(all_inactive_emp[i][3], '%Y-%m-%d %H:%M:%S.%f').strftime('%Y')

                if emp_inactive_year == current_year:
                    inactive_emp.append(all_inactive_emp[i])

            total_inactive = len(inactive_emp)
            percentage = (total_inactive / all_emp[0]) * 100
            
            if len(inactive_emp) > 0:
                lt_5 = 0
                gt_5_lt_10 = 0
                gt_10_lt_15 = 0
                gt_15 = 0

                for x in range(len(inactive_emp)):
                    get_emp_date = servingterm.getEmployementDate(emp_id=inactive_emp[x][1])
                    employement_date = datetime.datetime.strptime(get_emp_date, '%Y-%m-%d').strftime('%Y')

                    worked_duration = int(current_year) - int(employement_date)
                	
                    if worked_duration <= 5:
                        lt_5 = lt_5 + 1
                    elif worked_duration > 5 and worked_duration <= 10:
                        gt_5_lt_10 = gt_5_lt_10 + 1
                    elif worked_duration > 10 and worked_duration <= 15:
                        gt_10_lt_15 = gt_10_lt_15 + 1
                    elif worked_duration > 15:
                        gt_15 = gt_15 + 1

                lt_5_perc = (lt_5 / len(inactive_emp)) * 100
                gt_5_lt_10_perc = (gt_5_lt_10 / len(inactive_emp)) * 100
                gt_10_lt_15_perc = (gt_10_lt_15 / len(inactive_emp)) * 100
                gt_15_perc = (gt_15 / len(inactive_emp)) * 100
                
                terms = {
				    'lt_5':lt_5_perc,
				    'gt5lt10': gt_5_lt_10_perc,
				    'gt10lt15': gt_10_lt_15_perc,
				    'gt15': gt_15_perc,
				    'perc': percentage,
				    'lt_5_val': lt_5,
				    'gt_5_lt_10_val': gt_5_lt_10,
				    'gt_10_lt_15_val': gt_10_lt_15,
				    'gt_15_val': gt_15,
				}

                return terms
        else:
            return None	


def graphy(parameter):
	with CursorFromConnectionPool() as cursor:
		cursor.execute('SELECT employees.{}, count(*) FROM employees\
						WHERE employees.active = %s\
						GROUP BY employees.{}\
						'.format(parameter, parameter), (1,))
		res = cursor.fetchall()
		if res is not None:
			return res 


def getterm(): 
	current_date = date.today()
	_15_year = format(current_date - timedelta(days=15*365), "%Y-%m-%d")
	_10_year = format(current_date - timedelta(days=10*365), "%Y-%m-%d")
	_5_year = format(current_date - timedelta(days=5*365), "%Y-%m-%d")

	lt_5_longterm = servingterm(condition='employees.active_date >= %s', value=_5_year).term()
	gt_5_lt_10_longterm = servingterm(condition='employees.active_date <= %s and employees.active_date >= %s', value=_5_year, value2=_10_year).term()
	gt_10_lt_15_longterm = servingterm(condition='employees.active_date <= %s and employees.active_date >= %s', value=_10_year, value2=_15_year).term()
	gt_15_longterm = servingterm(condition='employees.active_date <= %s', value=_15_year).term()
	
	terms = {
	    'lt_5': lt_5_longterm[0],
	    'gt5lt10': gt_5_lt_10_longterm[0],
	    'gt10lt15': gt_10_lt_15_longterm[0],
	    'gt15': gt_15_longterm[0]
	}

	if terms['lt_5'] == 0 and terms['gt5lt10'] == 0 and terms['gt10lt15'] == 0 and terms['gt15'] == 0:
		return None
	else:
		return terms


def engaging_emp(size_range):
	with CursorFromConnectionPool() as cursor:
		if size_range == 'all':
			cursor.execute("SELECT * FROM employees WHERE active=%s ORDER BY active_date ASC", (int(1),))
		else:
			cursor.execute("SELECT * FROM employees WHERE active=%s ORDER BY active_date ASC LIMIT %s", (int(1), size_range))
		
		res = cursor.fetchall()
		return res


