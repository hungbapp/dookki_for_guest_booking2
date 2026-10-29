from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from datetime import datetime, timedelta
# Import hàm lấy kết nối SQLite từ file database.py
from database import get_db_connection

customer_bp = Blueprint('customer', __name__)

@customer_bp.route('/', methods=['GET'])
def index():
    return redirect(url_for('customer.booking_form'))

@customer_bp.route('/booking', methods=['GET'])
def booking_form():
    return render_template('booking/index.html')

import random
import string

@customer_bp.route('/book', methods=['POST'])
def book_table():
    customer_name = request.form.get('customer_name')
    phone = request.form.get('phone')
    booking_date = request.form.get('booking_date')
    booking_time = request.form.get('booking_time')
    num_people = request.form.get('num_people')
    table_id = request.form.get('table_id')
    note = request.form.get('note')

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. KIỂM TRA ĐIỀU KIỆN: 1 SĐT CHỈ ĐƯỢC ĐẶT 1 BÀN 1 NGÀY
    cursor.execute('SELECT id FROM bookings WHERE phone = ? AND booking_date = ? AND status != "cancelled"', (phone, booking_date))
    if cursor.fetchone():
        conn.close()
        return jsonify({'success': False, 'message': f'Số điện thoại {phone} đã đặt bàn trong ngày {booking_date}. Mỗi SĐT chỉ được đặt 1 lần/ngày!'})

    # 2. TẠO MÃ CODE 6 SỐ
    booking_code = ''.join(random.choices(string.digits, k=6))

    # 3. LẤY THÔNG TIN BÀN
    cursor.execute('SELECT area, table_number FROM tables WHERE id = ?', (table_id,))
    table_data = cursor.fetchone()
    area = table_data['area'] if table_data else "Không xác định"
    table_number = table_data['table_number'] if table_data else ""

    # 4. LƯU VÀO DATABASE
    cursor.execute('''
        INSERT INTO bookings (customer_name, phone, booking_date, booking_time, num_people, area, table_id, note, status, booking_code)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (customer_name, phone, booking_date, booking_time, num_people, area, table_id, note, 'confirmed', booking_code))
    
    conn.commit()
    conn.close()

    # Trả kết quả về cho Frontend tạo QR
    return jsonify({'success': True, 'code': booking_code, 'name': customer_name, 'table': table_number})


@customer_bp.route('/api/lookup', methods=['GET'])
def lookup_booking():
    query = request.args.get('query', '').strip()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Tìm kiếm theo SĐT hoặc Mã CODE 6 số
    cursor.execute('''
        SELECT b.*, t.table_number 
        FROM bookings b 
        LEFT JOIN tables t ON b.table_id = t.id 
        WHERE b.phone = ? OR b.booking_code = ? 
        ORDER BY b.id DESC LIMIT 1
    ''', (query, query))
    row = cursor.fetchone()
    conn.close()

    if row:
        return jsonify({
            'success': True, 
            'data': {
                'code': row['booking_code'],
                'name': row['customer_name'],
                'date': row['booking_date'],
                'time': row['booking_time'],
                'table': row['table_number'],
                'status': row['status']
            }
        })
    return jsonify({'success': False, 'message': 'Không tìm thấy lịch sử đặt bàn với thông tin này!'})

    # 1. Tự động lấy thông tin "Khu vực" (area) từ Database dựa trên bàn khách đã chọn
    cursor.execute('SELECT area FROM tables WHERE id = ?', (table_id,))
    table_data = cursor.fetchone()
    
    # Nếu tìm thấy bàn, lấy đúng khu vực của bàn đó, ngược lại để "Không xác định"
    area = table_data['area'] if table_data else "Không xác định"

    # 2. Tiến hành lưu vào bảng bookings
    cursor.execute('''
        INSERT INTO bookings (customer_name, phone, booking_date, booking_time, num_people, area, table_id, note, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (customer_name, phone, booking_date, booking_time, num_people, area, table_id, note, 'confirmed'))
    
    conn.commit()
    conn.close()

    flash("Đặt bàn thành công! Nhân viên sẽ sớm liên hệ xác nhận.", "success")
    return redirect(url_for('customer.booking_form'))

@customer_bp.route('/api/get-tables', methods=['GET'])
def get_tables():
    date_str = request.args.get('date')
    time_str = request.args.get('time')
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Truy vấn toàn bộ danh sách bàn
    cursor.execute('SELECT * FROM tables')
    tables = cursor.fetchall()
    
    # 2. Truy vấn danh sách đã đặt trong ngày
    cursor.execute('SELECT * FROM bookings WHERE booking_date = ? AND status != "cancelled"', (date_str,))
    bookings = cursor.fetchall()
    conn.close()
    
    # Chuyển bookings thành dictionary theo table_id để tra cứu nhanh
    booking_dict = {b['table_id']: b for b in bookings if b['table_id']}
    
    now = datetime.now()
    result = []
    
    for table in tables:
        table_id = table['id']
        table_status = "available"
        remaining_seconds = 0
        booked_by = ""
        booking_time_str = ""
        
        if table_id in booking_dict:
            booking = booking_dict[table_id]
            
            try:
                # Ghép ngày giờ đặt bàn
                booking_datetime = datetime.strptime(f"{booking['booking_date']} {booking['booking_time']}", "%Y-%m-%d %H:%M")
                grace_period_end = booking_datetime + timedelta(minutes=15)
                
                # Kiểm tra trạng thái thời gian
                if booking_datetime <= now <= grace_period_end:
                    table_status = "waiting" # Giữ bàn 15 phút
                    remaining_seconds = int((grace_period_end - now).total_seconds())
                    booked_by = booking['customer_name']
                    booking_time_str = booking['booking_time']
                elif now < booking_datetime:
                    table_status = "booked" # Đã đặt
                    booked_by = booking['customer_name']
                    booking_time_str = booking['booking_time']
            except Exception as e:
                pass

        result.append({
            "id": table['id'],
            "table_number": table['table_number'],
            "capacity": table['capacity'],
            "area": table['area'],
            "status": table_status,
            "remaining_seconds": remaining_seconds,
            "booked_by": booked_by,
            "booking_time": booking_time_str
        })
        
    return jsonify(result)