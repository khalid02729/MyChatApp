import os
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3

app = Flask(__name__, static_folder='.', static_url_path='')
app.config['SECRET_KEY'] = 'quran_azkar_2027_secret_key'

# فتح الحماية بأعلى صلاحيات مطلقة لمنع رسائل خطأ الاتصال للأبد
CORS(app, supports_credentials=True, origins="*")

DATABASE = 'quran_azkar.db'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# تأسيس جداول السور والآيات والأذكار على نظافة تامة
def init_db():
    with get_db() as conn:
        conn.execute('DROP TABLE IF EXISTS azkar')
        conn.execute('DROP TABLE IF EXISTS surahs')
        
        # جدول السور
        conn.execute('''
            CREATE TABLE surahs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                type TEXT NOT NULL, -- مكية / مدنية
                verses_count INTEGER NOT NULL,
                content TEXT NOT NULL 
            )
        ''')
        
        # جدول الأذكار
        conn.execute('''
            CREATE TABLE azkar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL, -- sabah / masaa
                text TEXT NOT NULL,
                count INTEGER NOT NULL 
            )
        ''')
        conn.commit()
        
        # 🚀 ضخ المحتوى الإسلامي الكامل والكامل بالآيات والأذكار الصحيحة
        check = conn.execute('SELECT COUNT(*) FROM surahs').fetchone()
        if check == 0:
            # 💎 ضخ السور كاملة بحروفها وآياتها المنسقة
            conn.execute('''
                INSERT INTO surahs (name, type, verses_count, content) 
                VALUES ('الفَاتِحَة', 'مكية', 7, 'الْحَمْدُ لِلَّهِ رَبِّ الْعَالَمِينَ ﴿٢﴾ الرَّحْمَٰنِ الرَّحِيمِ ﴿٣﴾ مَالِكِ يَوْمِ الدِّينِ ﴿٤﴾ إِيَّاكَ نَعْبُدُ وَإِيَّاكَ نَسْتَعِينُ ﴿٥﴾ اهْدِنَا الصِّرَاطَ الْمُسْتَقِيمَ ﴿٦﴾ صِرَاطَ الَّذِينَ أَنْعَمْتَ عَلَيْهِمْ غَيْرِ الْمَغْضُوبِ عَلَيْهِمْ وَلَا الضَّالِّينَ ﴿٧﴾')
            ''')
            conn.execute('''
                INSERT INTO surahs (name, type, verses_count, content) 
                VALUES ('الإخْلَاص', 'مكية', 4, 'قُلْ هُوَ اللَّهُ أَحَدٌ ﴿١﴾ اللَّهُ الصَّمَدُ ﴿٢﴾ لَمْ يَلِدْ وَلَمْ يُولَدْ ﴿٣﴾ وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ ﴿٤﴾')
            ''')
            conn.execute('''
                INSERT INTO surahs (name, type, verses_count, content) 
                VALUES ('الفَلَق', 'مكية', 5, 'قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ ﴿١﴾ مِن شَرِّ مَا خَلَقَ ﴿٢﴾ وَمِن شَرِّ غَاسِقٍ إِذَا وَقَبَ ﴿٣﴾ وَمِن شَرِّ النَّفَّاثَاتِ فِي الْعُقَدِ ﴿٤﴾ وَمِن شَرِّ حَاسِدٍ إِذَا حَسَدَ ﴿٥﴾')
            ''')
            conn.execute('''
                INSERT INTO surahs (name, type, verses_count, content) 
                VALUES ('النَّاس', 'مكية', 6, 'قُلْ أَعُوذُ بِرَبِّ النَّاسِ ﴿١﴾ مَلِكِ النَّاسِ ﴿٢﴾ إِلَٰهِ النَّاسِ ﴿٣﴾ مِن شَرِّ الْوَسْوَاسِ الْخَنَّاسِ ﴿٤﴾ الَّذِي يُوَسْوِسُ فِي صُدُورِ النَّاسِ ﴿٥﴾ مِنَ الْجِنَّةِ وَالنَّاسِ ﴿٦﴾')
            ''')
            
            # ☀️ ضخ باقة أذكار الصباح كاملة بالعدادات والتحصين
            conn.execute("INSERT INTO azkar (category, text, count) VALUES ('sabah', '📜 أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ: اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ ۚ لَّهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ ۗ مَن ذَا الَّذِي يَشْفَعُ عِندَهُ إِلَّا بِإِذْنِهِ ۚ يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ ۖ وَلَا يُحِيطُونَ بِشَيْءٍ مِّنْ عِلْمِهِ إِلَّا بِمَا شَاءَ ۚ وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالْأَرْضَ ۖ وَلَا يَئُودُهُ حِفْظُهُمَا ۚ وَهُوَ الْعَلِيُّ الْعَظِيمُ. (آية الكرسي - حماية وراحة للقلب)', 1)")
            conn.execute("INSERT INTO azkar (category, text, count) VALUES ('sabah', '☀️ أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ.', 1)")
            conn.execute("INSERT INTO azkar (category, text, count) VALUES ('sabah', '📿 يَا حَيُّ يَا قَيُّومُ بِرَحْمَتِكَ أَسْتَغِيثُ، أَصْلِحْ لِي شَأْنِي كُلَّهُ وَلَا تَكِلْنِي إِلَى نَفْسِي طَرْفَةَ عَيْنٍ.', 1)")
            conn.execute("INSERT INTO azkar (category, text, count) VALUES ('sabah', '🛡️ بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ.', 3)")
            conn.execute("INSERT INTO azkar (category, text, count) VALUES ('sabah', '🤍 رَضِيتُ بِاللَّهِ رَبًّا، وَبِالْإِسْلَامِ دِينًا، وَبِمُحَمَّدٍ صَلَّى اللَّهُ عَلَيْهِ وَسَلَّمَ نَبِيًّا.', 3)")

            # 🌙 ضخ باقة أذكار المساء كاملة للحفظ والسكينة
            conn.execute("INSERT INTO azkar (category, text, count) VALUES ('masaa', '📜 أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ: اللَّهُ لَا إِلَٰهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ ۚ لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ... (آية الكرسي سَكينة وحفظ للمساء)', 1)")
            conn.execute("INSERT INTO azkar (category, text, count) VALUES ('masaa', '🌙 أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ.', 1)")
            conn.execute("INSERT INTO azkar (category, text, count) VALUES ('masaa', '🌿 أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ.', 3)")
            conn.execute("INSERT INTO azkar (category, text, count) VALUES ('masaa', '🛡️ بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ.', 3)")
            conn.execute("INSERT INTO azkar (category, text, count) VALUES ('masaa', '📿 اللَّهُمَّ بِكَ أَمْسَيْنَا، وَبِكَ أَصْبَحْنَا، وَبِكَ نَحْيَا، وَبِكَ نَمُوتُ، وَإِلَيْكَ الْمَصِيرُ.', 1)")
            
            conn.commit()

init_db()

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/api/surahs', methods=['GET'])
def get_surahs():
    with get_db() as conn:
        surahs = conn.execute('SELECT id, name, type, verses_count FROM surahs').fetchall()
    return jsonify([dict(s) for s in surahs])

@app.route('/api/surah/<int:surah_id>', methods=['GET'])
def get_surah_content(surah_id):
    with get_db() as conn:
        surah = conn.execute('SELECT * FROM surahs WHERE id = ?', (surah_id,)).fetchone()
    if surah:
        return jsonify(dict(surah))
    return jsonify({'status': 'error', 'message': 'السورة غير موجودة'}), 404

@app.route('/api/azkar', methods=['GET'])
def get_azkar():
    category = request.args.get('category', 'sabah')
    with get_db() as conn:
        azkar_list = conn.execute('SELECT * FROM azkar WHERE category = ?', (category,)).fetchall()
    return jsonify([dict(a) for a in azkar_list])

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)

