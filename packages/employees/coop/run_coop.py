from flask import Blueprint, request, redirect, url_for, render_template, flash, make_response, jsonify
from flask_login import current_user, login_required
from packages.employees.coop.cooperative import Cooperative


cms_coop = Blueprint('cms_coop', __name__, url_prefix='/', template_folder='templates', static_folder='static')



@cms_coop.before_request
def chk_session():
    if not current_user.is_authenticated:
        return redirect(url_for('admin.login', next=request.url))



@cms_coop.route('/admin/cooperative-members', methods=['POST', 'GET'])
def cooperative():
    fetch_data = Cooperative().get_users()
    add_member = request.args.get('add_emp')
    delete_member = request.args.get('delete_emp')

    if add_member:
        add = Cooperative.add_coop_member(add_member)
        if add:
            flash('Employee has been added successfully', 'success')
            return redirect(url_for('cms_coop.cooperative'))

    if delete_member:
        delete = Cooperative.delete_coop_member(delete_member)
        if delete:
            flash('Employee has been removed successfully', 'success')
            return redirect(url_for('cms_coop.cooperative'))

    return render_template('cooperative/cooperative.html', emp_details=fetch_data)


@cms_coop.route('/admin/update-contribution', methods=['POST'])
def update_contribution():
    if request.method == 'POST':
    	emp_id = request.form['emp_id']
    	amount = request.form['amount']

    	update_amount = Cooperative(emp_id=emp_id).update_contribution(amount=amount)
    	if update_amount is True:
    		return make_response(jsonify('success'))


@cms_coop.add_app_template_filter
def getContribution(emp_id):
	return Cooperative(emp_id=emp_id).getAmount()


