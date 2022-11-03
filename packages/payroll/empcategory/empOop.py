from packages.database import CursorFromConnectionPool


class Category:
    def __init__(self, name, basic, house_a, transport_a, other_a, total_a):
        self.name = name
        self.basic = basic
        self.house_a = house_a
        self.transport_a = transport_a
        self.other_a = other_a
        self.total_a = total_a

    def __repr__(self):
        return "<Class category: {}, {}>".format(self.basic_a, self.total_a)


    @classmethod
    def new_column(cls, column_name):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("ALTER TABLE emp_class ADD COLUMN IF NOT exists {} real ".format(column_name))
            


    @classmethod
    def create_new_class(cls, name, basic, house_a, transport_a, other_a, total_a):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('INSERT INTO emp_class(name, basic, house_a, transport_a, other_a, total_a) '
                           'VALUES(%s, %s, %s, %s, %s, %s) RETURNING id',
                           (name, basic, house_a, transport_a, other_a, total_a))
            res = cursor.fetchone()
            if res:
                last_inserted_id = res[0]
                return last_inserted_id
            else:
                return False

    @classmethod
    def update_column(cls, column_name, value, class_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute("UPDATE emp_class SET {}=%s WHERE id=%s".format(column_name), (value, class_id))

    @classmethod
    def get_class(cls, getID):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM emp_class WHERE id = %s', (getID,))
            class_data = cursor.fetchone()
            if class_data:
                return class_data

    @classmethod
    def update_class(cls, class_id, name, basic, house_a, transport_a, other_a, total_a, lsg, twofour, health):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('UPDATE emp_class SET name = %s, basic = %s, house_a= %s, transport_a = %s, '
                           'other_a = %s, total_a=%s, lasg_lunch_allowance=%s, twofourhrs_allowance=%s, health_allowance=%s\
                            WHERE id = %s RETURNING id', (name, basic, house_a, transport_a, other_a, total_a, lsg, twofour, health, class_id))
            get_update_id = cursor.fetchone()
            if get_update_id:
                last_id = get_update_id[0]
                return last_id

    @classmethod
    def class_list(cls):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('SELECT * FROM emp_class ORDER BY id DESC')
            all_list = cursor.fetchall()
            if all_list:
                return all_list

    @classmethod
    def delete_class(cls, class_id):
        with CursorFromConnectionPool() as cursor:
            cursor.execute('DELETE FROM emp_class WHERE id = %s', (class_id,))
            if cursor:
                return 'deleted'


def converttofloat(value):
    getvalue = value
    remove_str = getvalue.replace(',', '')
    return float(remove_str)






