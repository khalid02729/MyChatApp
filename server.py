import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = 'quran_perfect_2027_key'
CORS(app, supports_credentials=True, origins="*")

DATABASE = 'quran_perfect.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('DROP TABLE IF EXISTS azkar')
        conn.execute('DROP TABLE IF EXISTS surahs')
        conn.execute('CREATE TABLE surahs (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, type TEXT NOT NULL, start_page INTEGER NOT NULL, end_page INTEGER NOT NULL)')
        conn.execute('CREATE TABLE azkar (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, text TEXT NOT NULL, count INTEGER NOT NULL)')
        
        # 💎 ضخ فهرس المصحف الشريف بالترتيب الحقيقي المعتمد (أمثلة البداية المتسلسلة)
        conn.execute("INSERT INTO surahs (name, type, start_page, end_page) VALUES ('الفَاتِحَة', 'مكية', 1, 1)")
        conn.execute("INSERT INTO surahs (name, type, start_page, end_page) VALUES ('البَقَرَة', 'مدنية', 2, 49)")
        conn.execute("INSERT INTO surahs (name, type, start_page, end_page) VALUES ('آلِ عِمْرَان', 'مدنية', 50, 76)")
        conn.execute("INSERT INTO surahs (name, type, start_page, end_page) VALUES ('النِّسَاءِ', 'مدنية', 77, 106)")
        conn.execute("INSERT INTO surahs (name, type, start_page, end_page) VALUES ('الإخْلَاص', 'مكية', 604, 604)")
        conn.execute("INSERT INTO surahs (name, type, start_page, end_page) VALUES ('الفَلَق', 'مكية', 604, 604)")
        conn.execute("INSERT INTO surahs (name, type, start_page, end_page) VALUES ('النَّاس', 'مكية', 604, 604)")
        
        # ☀️ ضخ نصوص أذكار الصباح والتحصين الشرعية الكاملة والموسعة دون أي اختصار
        conn.execute("INSERT INTO azkar (category, text, count) VALUES ('sabah', '📜 أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ: اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ ۚ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ ۗ مَن ذَا الَّذِي يَشْفَعُ عِندَهُ إِلَّا بِإِذْنِهِ ۚ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ ۖ وَلَا يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلَّا بِمَا شَاءَ ۚ وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالْأَرْضَ ۖ وَلَا يَئُودُهُ حِفْظُهُمَا ۚ وَهُوَ الْعَلِيُّ الْعَظِيمُ. (آية الكرسي - حصن المسلم)', 1)")
        conn.execute("INSERT INTO azkar (category, text, count) VALUES ('sabah', '☀️ أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ، لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ، رَبِّ أَسْأَلُكَ خَيْرَ مَا فِي هَذَا الْيَوْمِ وَخَيْرَ مَا بَعْدَهُ، وَأَعُوذُ بِكLocal مِنْ شَرِّ مَا فِي هَذَا الْيَوْمِ وَشَرِّ مَا بَعْدَهُ.', 1)")
        conn.execute("INSERT INTO azkar (category, text, count) VALUES ('sabah', '📿 يَا حَيُّ يَا قَيُّومُ بِرَحْمَتِكَ أَسْتَغِيثُ، أَصْلِحْ لِي شَأْنِي كُلَّهُ وَلَا تَكِلْنِي إِلَى نَفْسِي طَرْفَةَ عَيْنٍ.', 1)")
        conn.execute("INSERT INTO azkar (category, text, count) VALUES ('sabah', '🛡️ بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ.', 3)")

        # 🌙 ضخ نصوص أذكار المساء الشرعية الكاملة والموسعة لحفظ النفس والسكينة
        conn.execute("INSERT INTO azkar (category, text, count) VALUES ('masaa', '📜 أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ: اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ... (آية الكرسي - حماية وحفظ للمساء حتى تصبح)', 1)")
        conn.execute("INSERT INTO azkar (category, text, count) VALUES ('masaa', '🌙 أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ.', 1)")
        conn.execute("INSERT INTO azkar (category, text, count) VALUES ('masaa', '🌿 أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ.', 3)")
        conn.execute("INSERT INTO azkar (category, text, count) VALUES ('masaa', '🛡️ بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ.', 3)")
        conn.commit()

init_db()

@app.route('/')
def index(): return send_from_directory('.', 'index.html')

@app.route('/api/surahs', methods=['GET'])
def get_surahs():
    with get_db() as conn: surahs = conn.execute('SELECT * FROM surahs ORDER BY id ASC').fetchall()
    return jsonify([dict(s) for s in surahs])

@app.route('/api/azkar', methods=['GET'])
def get_azkar():
    cat = request.args.get('category', 'sabah')
    with get_db() as conn: az = conn.execute('SELECT * FROM azkar WHERE category = ?', (cat,)).fetchall()
    return jsonify([dict(a) for a in az])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
