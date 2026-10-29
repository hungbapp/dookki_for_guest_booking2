from flask import Flask
from database import init_db
from routes.customer_routes import customer_bp
from routes.admin_routes import admin_bp
from routes.auth_routes import auth_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object('config')

    # Khởi tạo cơ sở dữ liệu SQLite tự động
    init_db()

    # Đăng ký Blueprints (Gắn kết các module route vào ứng dụng)
    app.register_blueprint(customer_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(auth_bp)

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)