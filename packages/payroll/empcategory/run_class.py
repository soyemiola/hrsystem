from flask import Blueprint, render_template, request, url_for, redirect, flash
from packages.payroll.empcategory.empOop import Category, converttofloat
from packages.functions import delete_table_record
from flask_login import current_user, login_required


empclass = Blueprint('empclass', __name__, url_prefix='/', template_folder='templates')


@empclass.before_request
def chk_session():
    if not current_user.is_authenticated:
        return redirect(url_for('admin.login', next=request.url))


@empclass.route('/admin/classlist')
def classlist():
    fetch_list = Category.class_list()
    return render_template('empcategory/classlist.html', all__=fetch_list, alert='')


@empclass.route('/admin/addclass', methods=['POST', 'GET'])
def addclass():
    if request.method == 'POST':
        name_ = str(request.form['name'])
        basic_ = converttofloat(request.form['basic'])
        house_a = converttofloat(request.form['house_allow'])
        transport_a = converttofloat(request.form['transport_allow'])
        others = request.form.getlist('other_allowance')
        label = request.form.getlist('label')

        other_allowance = []
        details = []

        size = len(others)

        for i in range(size):
            value = (label[i], others[i])
            details.append(value)
            # create new column if not exist
            new_column = Category.new_column(column_name=label[i].replace(' ','_'))

        
        for i in others:
            other_allowance.append(converttofloat(i))

        
        total_allowance = (house_a, transport_a, sum(other_allowance))
        # create new emp_class
        new_class = Category.create_new_class(name=name_, basic=basic_, house_a=house_a, transport_a=transport_a, 
                                                other_a=sum(other_allowance), total_a=sum(total_allowance))
        if new_class is not False:
            # update the table
            for i in range(size):
                update = Category.update_column(column_name=label[i].replace(' ', '_'), value=converttofloat(others[i]), 
                                                class_id=new_class)

            flash('New class categpry created', 'success')
            return redirect(url_for('empclass.classlist'))

    return render_template('empcategory/addclass.html')


@empclass.route('/editclass/<int:get_id>')
def editclass(get_id):
    class_record = Category.get_class(get_id)
    return render_template('empcategory/editclass.html', edit_data=class_record)
    


@empclass.route('/updateclass/<int:get_id>', methods=['POST', 'GET'])
def updateclass(get_id):
    if request.method == 'POST':
        class_id = get_id
        name_ = str(request.form['name'])
        basic_ = converttofloat(request.form['basic'])
        house_a = converttofloat(request.form['house_allow'])
        transport_a = converttofloat(request.form['transport_allow'])
        lasg = converttofloat(request.form['lasg_allowance'])
        twofour = converttofloat(request.form['twofour_allowance'])
        health = converttofloat(request.form['health_allowance'])
        
        other_allowance = (lasg, twofour, health)
        total_allowance = (house_a, transport_a, sum(other_allowance))

        update_class = Category.update_class(class_id=class_id, name=name_, basic=basic_, house_a=house_a, transport_a=transport_a, 
                                            other_a=sum(other_allowance), total_a=sum(total_allowance), lsg=lasg, twofour=twofour, health=health)

        if update_class is not False:
            flash('Class Updated', 'success')
            return redirect(url_for('empclass.classlist'))
       

    return redirect(url_for('empclass.classlist'))


@empclass.route('/admin/delete/<getid>')
def delete(getid):
    delete = delete_table_record('emp_class', getid)
    if delete:
        return redirect(url_for('empclass.classlist'))
     
