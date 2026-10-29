import sqlite3
from config import DB_NAME

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Bảng quản lý bàn ăn
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tables (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            table_number TEXT NOT NULL UNIQUE,
            capacity INTEGER NOT NULL,
            area TEXT NOT NULL
        )
    ''')
    
    # 2. Bảng quản lý đơn đặt bàn
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_name TEXT NOT NULL,
            phone TEXT NOT NULL,
            booking_date TEXT NOT NULL,
            booking_time TEXT NOT NULL,
            num_people INTEGER NOT NULL,
            area TEXT NOT NULL,
            table_id INTEGER,
            note TEXT,
            status TEXT DEFAULT 'Chờ xác nhận',
            booking_code TEXT,
            FOREIGN KEY (table_id) REFERENCES tables (id)
        )
    ''')

    # 3. Bảng quản lý tài khoản người dùng / Admin (Cần thiết cho phần quản trị vừa tích hợp)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            role TEXT DEFAULT 'user'
        )
    ''')

    # Tạo sẵn một tài khoản Admin mặc định (Username: admin, Password: admin123) nếu chưa có
    cursor.execute('SELECT COUNT(*) FROM users WHERE role = "admin"')
    if cursor.fetchone()[0] == 0:
        cursor.execute('INSERT INTO users (username, password, role) VALUES (?, ?, ?)', ('admin', 'admin123', 'admin'))

    # Đảm bảo thêm cột booking_code nếu database cũ chưa có
    try:
        cursor.execute('ALTER TABLE bookings ADD COLUMN booking_code TEXT')
    except sqlite3.OperationalError:
        pass

    # Thêm dữ liệu mẫu các bàn ăn nếu bảng đang trống
    cursor.execute('SELECT COUNT(*) FROM tables')
    if cursor.fetchone()[0] == 0:
        sample_tables = [
            # Gần cửa sổ
            ('W-01', 2, 'Gần cửa sổ'), ('W-02', 2, 'Gần cửa sổ'),
            ('W-03', 4, 'Gần cửa sổ'), ('W-04', 4, 'Gần cửa sổ'),
            ('W-05', 8, 'Gần cửa sổ'), ('W-06', 8, 'Gần cửa sổ'),

            # Khu vực tiêu chuẩn
            ('S-01', 8, 'Khu vực tiêu chuẩn'), ('S-02', 8, 'Khu vực tiêu chuẩn'),
            ('S-09', 8, 'Khu vực tiêu chuẩn'), ('S-10', 8, 'Khu vực tiêu chuẩn'),
            ('S-03', 4, 'Khu vực tiêu chuẩn'), ('S-04', 4, 'Khu vực tiêu chuẩn'), ('S-05', 4, 'Khu vực tiêu chuẩn'),
            ('S-06', 2, 'Khu vực tiêu chuẩn'), ('S-07', 2, 'Khu vực tiêu chuẩn'), ('S-08', 2, 'Khu vực tiêu chuẩn'),

            # Gần quầy buffet
            ('T-01', 4, 'Gần quầy buffet'), ('T-02', 4, 'Gần quầy buffet'), ('T-03', 4, 'Gần quầy buffet'), ('T-10', 4, 'Gần quầy buffet'),
            ('T-04', 8, 'Gần quầy buffet'), ('T-05', 8, 'Gần quầy buffet'),
            ('T-06', 2, 'Gần quầy buffet'), ('T-07', 2, 'Gần quầy buffet'), ('T-08', 2, 'Gần quầy buffet'), ('T-09', 2, 'Gần quầy buffet'),

            # Phòng VIP
            ('VIP-01', 16, 'Phòng VIP'),
            ('VIP-02', 16, 'Phòng VIP')
        ]
        cursor.executemany('INSERT INTO tables (table_number, capacity, area) VALUES (?, ?, ?)', sample_tables)
    
    conn.commit()
    conn.close()