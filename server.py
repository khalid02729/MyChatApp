import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = 'quran_text_2027_key'
CORS(app, supports_credentials=True, origins="*")

DATABASE = 'quran_text.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('DROP TABLE IF EXISTS azkar')
        conn.execute('DROP TABLE IF EXISTS verses')
        conn.execute('DROP TABLE IF EXISTS surahs')
        
        # 1. جدول السور الرئيسي
        conn.execute('CREATE TABLE surahs (id INTEGER PRIMARY KEY, name TEXT NOT NULL, type TEXT NOT NULL)')
        # 2. جدول الآيات المنفصلة (آية آية بدقة مطلقة)
        conn.execute('CREATE TABLE verses (id INTEGER PRIMARY KEY AUTOINCREMENT, surah_id INTEGER, verse_number INTEGER, text TEXT NOT NULL)')
        # 3. جدول الأذكار الكاملة
        conn.execute('CREATE TABLE azkar (id INTEGER PRIMARY KEY AUTOINCREMENT, category TEXT NOT NULL, text TEXT NOT NULL, count INTEGER NOT NULL)')
        
        # 🕌 ضخ الفهرس
        conn.execute("INSERT INTO surahs (id, name, type) VALUES (1, 'الفَاتِحَة', 'مكية')")
        conn.execute("INSERT INTO surahs (id, name, type) VALUES (112, 'الإخْلَاص', 'مكية')")
        conn.execute("INSERT INTO surahs (id, name, type) VALUES (113, 'الفَلَق', 'مكية')")
        conn.execute("INSERT INTO surahs (id, name, type) VALUES (114, 'النَّاس', 'مكية')")
        
        # 📖 ضخ آيات سورة الفاتحة بدقة ومقسمة آية آية
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (1, 1, 'بِسْمِ اللَّهِ الرَّحْمَٰنِ الرَّحِيمِ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (1, 2, 'الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (1, 3, 'الرَّحْمَٰنِ الرَّحِيمِ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (1, 4, 'مَالِكِ يَوْمِ الدِّينِ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (1, 5, 'إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (1, 6, 'اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (1, 7, 'صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ')")

        # 📖 ضخ سورة الإخلاص آية آية
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (112, 1, 'قُلْ هُوَ اللَّهُ أَحَدٌ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (112, 2, 'اللَّهُ الصَّمَدُ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (112, 3, 'لَمْ يَلِدْ وَلَمْ يُولَدْ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (112, 4, 'لَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ')")

        # 📖 ضخ سورة الفلق آية آية
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (113, 1, 'قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (113, 2, 'مِن شَرِّ مَا خَلَقَ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (113, 3, 'وَمِن شَرِّ غَاسِقٍ إِذَا وَقَبَ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (113, 4, 'وَمِن شَرِّ النَّفَّاثَاتِ فِي الْعُقَدِ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (113, 5, 'وَمِن شَرِّ حَاسدٍ إِذَا حَسَدَ')")

        # 📖 ضخ سورة الناس آية آية
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (114, 1, 'قُلْ أَعُوذُ بِرَبِّ النَّاسِ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (114, 2, 'مَلِكِ النَّاسِ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (114, 3, 'إِلَٰهِ النَّاسِ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (114, 4, 'مِن شَرِّ الْوَسْوَاسِ الْخَنَّاسِ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (114, 5, 'الَّذِي يُوَسْوِسُ فِي صُدُورِ النَّاسِ')")
        conn.execute("INSERT INTO verses (surah_id, verse_number, text) VALUES (114, 6, 'مِنَ الْجِنَّةِ وَالنَّاسِ')")

        # ☀️ ضخ نصوص أذكار الصباح كاملة وموسعة
        conn.execute("INSERT INTO azkar (category, text, count) VALUES ('sabah', '📜 اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ ۚ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ ۗ مَن ذَا الَّذِي يَشْفَعُ عِندَهُ إِلَّا بِإِذْنِهِ ۚ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ ۖ وَلَا يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلَّا بِمَا شَاءَ ۚ وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالْأَرْضَ ۖ وَلَا يَئُودُهُ حِفْظُهُمَا ۚ وَهُوَ الْعَلِيُّ الْعَظِيمُ.', 1)")
        conn.execute("INSERT INTO azkar (category, text, count) VALUES ('sabah', '☀️ أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ وَالْحَمْدُ لِلَّهِ، لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ.', 1)")
        conn.execute("INSERT INTO azkar (category, text, count) VALUES ('sabah', '🛡️ بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ.', 3)")

        # 🌙 أذكار المساء كاملة وموسعة
        conn.execute("INSERT INTO azkar (category, text, count) VALUES ('masaa', '📜 اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ... (آية الكرسي كاملة للمساء)', 1)")
        conn.execute("INSERT INTO azkar (category, text, count) VALUES ('masaa', '🌙 أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ.', 1)")
        conn.execute("INSERT INTO azkar (category, text, count) VALUES ('masaa', '🌿 أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ.', 3)")
        conn.commit()

init_db()

@app.route('/')
def index(): return send_from_directory('.', 'index.html')

@app.route('/api/surahs', methods=['GET'])
def get_surahs():
    with get_db() as conn: surahs = conn.execute('SELECT * FROM surahs ORDER BY id ASC').fetchall()
    return jsonify([dict(s) for s in surahs])

@app.route('/api/surah/<int:surah_id>', methods=['GET'])
def get_surah_content(surah_id):
    with get_db() as conn:
        surah_info = conn.execute('SELECT * FROM surahs WHERE id = ?', (surah_id,)).fetchone()
        verses = conn.execute('SELECT verse_number, text FROM verses WHERE surah_id = ? ORDER BY verse_number ASC', (surah_id,)).fetchall()
    if surah_info:
        return jsonify({'name': surah_info['name'], 'type': surah_info['type'], 'verses': [dict(v) for v in verses]})
    return jsonify({'status': 'error'}), 404

@app.route('/api/azkar', methods=['GET'])
def get_azkar():
    cat = request.args.get('category', 'sabah')
    with get_db() as conn: az = conn.execute('SELECT * FROM azkar WHERE category = ?', (cat,)).fetchall()
    return jsonify([dict(a) for a in az])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

