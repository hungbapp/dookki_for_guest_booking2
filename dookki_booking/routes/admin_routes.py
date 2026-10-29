from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from database import get_db_connection
from models.admin_model import (
    get_all_bookings, update_booking_status, delete_booking,
    get_all_users, update_user_role,
)

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(view_func):
    @wraps(view_func)
    def wrapped(*args, **kwargs):
        if not session.get('user_id'):
            flash('Vui lòng đăng nhập để tiếp tục.', 'warning')
            return redirect(url_for('auth.login'))
        
        # Đọc quyền hiện tại từ database để cập nhật ngay lập tức nếu có thay đổi
        conn = get_db_connection()
        user = conn.execute('SELECT role FROM users WHERE id = ?', (session.get('user_id'),)).fetchone()
        conn.close()
        
        if user is None:
            session.clear()
            flash('Tài khoản không còn tồn tại. Vui lòng đăng nhập lại.', 'warning')
            return redirect(url_for('auth.login'))
            
        session['role'] = user['role']
        if user['role'] != 'admin':
            flash('Bạn không có quyền truy cập trang quản trị.', 'danger')
            return redirect(url_for('customer.booking_form'))
            
        return view_func(*args, **kwargs)
    return wrapped


@admin_bp.route('/')
def dashboard_home():
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    search_phone = request.args.get('phone', '').strip()
    bookings = get_all_bookings(phone_search=search_phone or None)
    return render_template('admin/dashboard.html', bookings=bookings, search_phone=search_phone)


@admin_bp.route('/update_status/<int:id>', methods=['POST'])
@admin_required
def update_status(id):
    new_status = request.form.get('status', '')
    if update_booking_status(id, new_status):
        flash('Đã cập nhật trạng thái đơn đặt bàn.', 'success')
    else:
        flash('Trạng thái không hợp lệ hoặc đơn đặt bàn không tồn tại.', 'danger')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/delete/<int:id>', methods=['POST'])
@admin_required
def delete(id):
    delete_booking(id)
    flash('Đã xóa đơn đặt bàn.', 'success')
    return redirect(url_for('admin.dashboard'))


@admin_bp.route('/accounts')
@admin_required
def accounts():
    search_text = request.args.get('q', '').strip()
    users = get_all_users(search_text or None)
    return render_template('admin/accounts.html', users=users, search_text=search_text)


@admin_bp.route('/accounts/<int:user_id>/role', methods=['POST'])
@admin_required
def update_account_role(user_id):
    new_role = request.form.get('role', '').strip()
    success, message = update_user_role(user_id, new_role, session.get('user_id'))
    flash(message, 'success' if success else 'danger')
    return redirect(url_for('admin.accounts', q=request.args.get('q', '').strip()))
