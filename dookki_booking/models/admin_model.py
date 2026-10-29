from database import get_db_connection


def get_all_bookings(phone_search=None):
    conn = get_db_connection()
    cur = conn.cursor()
    query = '''SELECT bookings.*, tables.table_number
               FROM bookings LEFT JOIN tables ON bookings.table_id = tables.id'''
    params = []
    if phone_search:
        query += ' WHERE bookings.phone LIKE ?'
        params.append(f'%{phone_search}%')
    query += ' ORDER BY bookings.id DESC'
    cur.execute(query, params)
    bookings = cur.fetchall()
    conn.close()
    return bookings


def update_booking_status(booking_id, status):
    allowed_statuses = {'Chờ xác nhận', 'Đã xếp bàn', 'Đã đến', 'Đã hủy'}
    if status not in allowed_statuses:
        return False
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('UPDATE bookings SET status = ? WHERE id = ?', (status, booking_id))
    conn.commit()
    changed = cur.rowcount > 0
    conn.close()
    return changed


def delete_booking(booking_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('DELETE FROM bookings WHERE id = ?', (booking_id,))
    conn.commit()
    changed = cur.rowcount > 0
    conn.close()
    return changed


def get_all_users(search_text=None):
    """Return account details without exposing password hashes."""
    conn = get_db_connection()
    query = '''SELECT id, username, full_name, role, created_at
               FROM users'''
    params = []
    if search_text:
        query += ' WHERE username LIKE ? OR full_name LIKE ?'
        keyword = f'%{search_text}%'
        params.extend([keyword, keyword])
    query += " ORDER BY CASE WHEN role = 'admin' THEN 0 ELSE 1 END, id DESC"
    users = conn.execute(query, params).fetchall()
    conn.close()
    return users


def update_user_role(user_id, new_role, current_admin_id):
    """Update a user's role with safeguards against self-lockout."""
    if new_role not in {'customer', 'admin'}:
        return False, 'Vai trò không hợp lệ.'
    if user_id == current_admin_id:
        return False, 'Không thể tự thay đổi quyền của tài khoản đang đăng nhập.'

    conn = get_db_connection()
    try:
        target = conn.execute('SELECT id, role FROM users WHERE id = ?', (user_id,)).fetchone()
        if target is None:
            return False, 'Không tìm thấy tài khoản.'
        if target['role'] == new_role:
            return True, 'Vai trò tài khoản không thay đổi.'
        if target['role'] == 'admin' and new_role != 'admin':
            admin_count = conn.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'").fetchone()[0]
            if admin_count <= 1:
                return False, 'Không thể hạ quyền quản trị viên cuối cùng của hệ thống.'
        conn.execute('UPDATE users SET role = ? WHERE id = ?', (new_role, user_id))
        conn.commit()
        return True, 'Đã cập nhật quyền tài khoản.'
    finally:
        conn.close()