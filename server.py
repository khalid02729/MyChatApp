import os
import logging
import json
from http import HTTPStatus
from http.server import HTTPServer, SimpleHTTPRequestHandler

# إعداد السجلات (Logging)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

class ProfessionalHandler(SimpleHTTPRequestHandler):
    
    # معالجة طلبات GET
    def do_GET(self):
        # مسار فحص حالة السيرفر
        if self.path == "/api/status":
            # جلب رقم البورت الحالي ديناميكياً
            current_port = int(os.environ.get("PORT", 8082))
            self.send_json_response(HTTPStatus.OK, {"status": "running", "port": current_port})
            return
        
        # السلوك الافتراضي لخدمة الملفات الثابتة
        return super().do_GET()

    # معالجة طلبات POST
    def do_POST(self):
        if self.path == "/api/data":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            logging.info(f"Received POST data: {post_data.decode('utf-8')}")
            
            self.send_json_response(HTTPStatus.CREATED, {"message": "Data received successfully"})
            return
            
        self.send_json_response(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found"})

    # دالة مساعدة لإرسال استجابات JSON
    def send_json_response(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        # السماح بطلب البيانات (CORS) وهو مهم جداً لاتصال تطبيق الموبايل
        self.send_header("Access-Control-Allow-Origin", "*") 
        self.end_headers()
        response_bytes = json.dumps(data).encode('utf-8')
        self.wfile.write(response_bytes)

    # توجيه سجلات السيرفر
    def log_message(self, format, *args):
        logging.info(f"{self.client_address[0]} - {format % args}")

def run():
    # قراءة المنفذ ديناميكياً من بيئة تشغيل Railway
    port = int(os.environ.get("PORT", 8082))
    
    # التعديل الأساسي هنا: ربط السيرفر بـ "0.0.0.0" لفتح الاتصال الخارجي
    server_address = ("0.0.0.0", port)
    
    httpd = HTTPServer(server_address, ProfessionalHandler)
    logging.info(f"🚀 Server is running publicly on port: {port}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("🛑 Server shutting down gracefully.")
        httpd.server_close()

if __name__ == "__main__":
    run()
