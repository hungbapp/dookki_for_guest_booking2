from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db_connection

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        conn = get_db_connection()
        user = conn.execute('SELECT id, username, password_hash, full_name, role FROM users WHERE username = ?',
                            (username,)).fetchone()
        conn.close()
        if user and check_password_hash(user['password_hash'], password):
            session.clear()
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['full_name'] = user['full_name']
            session['role'] = user['role']
            flash('Đăng nhập thành công.', 'success')
            if user['role'] == 'admin':
                return redirect(url_for('admin.dashboard'))
            return redirect(url_for('customer.booking_form'))
        flash('Tên đăng nhập hoặc mật khẩu không đúng.', 'danger')
    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        if not full_name or not username or not password:
            flash('Vui lòng nhập đầy đủ thông tin.', 'warning')
        elif len(username) < 3:
            flash('Tên đăng nhập phải có ít nhất 3 ký tự.', 'warning')
        elif len(password) < 6:
            flash('Mật khẩu phải có ít nhất 6 ký tự.', 'warning')
        elif password != confirm_password:
            flash('Mật khẩu xác nhận không khớp.', 'danger')
        else:
            conn = get_db_connection()
            try:
                conn.execute('INSERT INTO users (username, password_hash, full_name, role) VALUES (?, ?, ?, ?)',
                             (username, generate_password_hash(password), full_name, 'customer'))
                conn.commit()
                flash('Đăng ký thành công. Hãy đăng nhập để đặt bàn.', 'success')
                return redirect(url_for('auth.login'))
            except Exception:
                flash('Tên đăng nhập đã tồn tại. Vui lòng chọn tên khác.', 'danger')
            finally:
                conn.close()
    return render_template('auth/register.html')


@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.clear()
    flash('Bạn đã đăng xuất.', 'success')
    return redirect(url_for('auth.login'))
