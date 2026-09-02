import os
import logging
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
            self.send_json_response(HTTPStatus.OK, {"status": "running", "port": 8082})
            return
        
        # السلوك الافتراضي لخدمة الملفات الثابتة (مثل index.html إن وُجد)
        return super().do_GET()

    # معالجة طلبات POST (في حال أردت استقبال بيانات)
    def do_POST(self):
        if self.path == "/api/data":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            logging.info(f"Received POST data: {post_data.decode('utf-8')}")
            
            self.send_json_response(HTTPStatus.CREATED, {"message": "Data received successfully"})
            return
            
        self.send_json_response(HTTPStatus.NOT_FOUND, {"error": "Endpoint not found"})

    # دالة مساعدة لإرسال استجابات JSON بشكل منظم
    def send_json_response(self, status_code, data):
        import json
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        # السماح بطلب البيانات من جافا سكريبت (CORS)
        self.send_header("Access-Control-Allow-Origin", "*") 
        self.end_headers()
        response_bytes = json.dumps(data).encode('utf-8')
        self.wfile.write(response_bytes)

    # توجيه سجلات السيرفر إلى نظام الـ logging الأساسي
    def log_message(self, format, *args):
        logging.info(f"{self.client_address[0]} - {format % args}")

def run():
    # المنفذ الافتراضي أصبح 8082 الآن
    port = int(os.getenv("PORT", 8082))
    server_address = ("", port)
    
    httpd = HTTPServer(server_address, ProfessionalHandler)
    logging.info(f"🚀 Server is running on http://localhost:{port}")
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        logging.info("🛑 Server shutting down gracefully.")
        httpd.server_close()

if __name__ == "__main__":
    run()
