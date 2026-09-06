import os
import sqlite3

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS


app = Flask(__name__, static_folder=".", static_url_path="")
CORS(app)

DATABASE = "quran_text.db"


# =========================================================
# قاعدة البيانات
# =========================================================

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():

    with get_db() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS surahs (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                type TEXT NOT NULL,
                number_of_ayahs INTEGER NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS verses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                surah_id INTEGER NOT NULL,
                verse_number INTEGER NOT NULL,
                text TEXT NOT NULL,
                UNIQUE(surah_id, verse_number)
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS azkar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                text TEXT NOT NULL,
                count INTEGER NOT NULL
            )
        """)

        conn.commit()


# =========================================================
# التحقق من وجود القرآن محليًا
# =========================================================

def quran_is_ready():

    with get_db() as conn:

        surah_count = conn.execute(
            "SELECT COUNT(*) FROM surahs"
        ).fetchone()[0]

        verse_count = conn.execute(
            "SELECT COUNT(*) FROM verses"
        ).fetchone()[0]

    return (
        surah_count == 114
        and verse_count > 6000
    )


# =========================================================
# الأذكار
# =========================================================

def insert_default_azkar():

    with get_db() as conn:

        count = conn.execute(
            "SELECT COUNT(*) FROM azkar"
        ).fetchone()[0]

        if count > 0:
            return

        azkar = [

            # ================= أذكار الصباح =================

            (
                "sabah",
                "أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ. اللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ، لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ، لَهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ، مَنْ ذَا الَّذِي يَشْفَعُ عِنْدَهُ إِلَّا بِإِذْنِهِ، يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ، وَلَا يُحِيطُونَ بِشَيْءٍ مِنْ عِلْمِهِ إِلَّا بِمَا شَاءَ، وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالْأَرْضَ، وَلَا يَئُودُهُ حِفْظُهُمَا، وَهُوَ الْعَلِيُّ الْعَظِيمُ.",
                1
            ),

            (
                "sabah",
                "قُلْ هُوَ اللَّهُ أَحَدٌ، اللَّهُ الصَّمَدُ، لَمْ يَلِدْ وَلَمْ يُولَدْ، وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ.",
                3
            ),

            (
                "sabah",
                "قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ، مِن شَرِّ مَا خَلَقَ، وَمِن شَرِّ غَاسِقٍ إِذَا وَقَبَ، وَمِن شَرِّ النَّفَّاثَاتِ فِي الْعُقَدِ، وَمِن شَرِّ حَاسِدٍ إِذَا حَسَدَ.",
                3
            ),

            (
                "sabah",
                "قُلْ أَعُوذُ بِرَبِّ النَّاسِ، مَلِكِ النَّاسِ، إِلَهِ النَّاسِ، مِن شَرِّ الْوَسْوَاسِ الْخَنَّاسِ، الَّذِي يُوَسْوِسُ فِي صُدُورِ النَّاسِ، مِنَ الْجِنَّةِ وَالنَّاسِ.",
                3
            ),

            (
                "sabah",
                "أَصْبَحْنَا وَأَصْبَحَ الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ، لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ.",
                1
            ),

            (
                "sabah",
                "اللَّهُمَّ بِكَ أَصْبَحْنَا، وَبِكَ أَمْسَيْنَا، وَبِكَ نَحْيَا، وَبِكَ نَمُوتُ، وَإِلَيْكَ النُّشُورُ.",
                1
            ),

            (
                "sabah",
                "رَضِيتُ بِاللَّهِ رَبًّا، وَبِالإِسْلَامِ دِينًا، وَبِمُحَمَّدٍ ﷺ نَبِيًّا.",
                3
            ),

            (
                "sabah",
                "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْعَفْوَ وَالْعَافِيَةَ فِي الدُّنْيَا وَالْآخِرَةِ.",
                1
            ),

            (
                "sabah",
                "بِسْمِ اللَّهِ الَّذِي لَا يَضُرُّ مَعَ اسْمِهِ شَيْءٌ فِي الْأَرْضِ وَلَا فِي السَّمَاءِ وَهُوَ السَّمِيعُ الْعَلِيمُ.",
                3
            ),


            # ================= أذكار المساء =================

            (
                "masaa",
                "أَعُوذُ بِاللَّهِ مِنَ الشَّيْطَانِ الرَّجِيمِ. اللَّهُ لَا إِلَهَ إِلَّا هُوَ الْحَيُّ الْقَيُّومُ، لَا تَأْخُذُهُ سِنَةٌ وَلَا نَوْمٌ، لَهُ مَا فِي السَّمَاوَاتِ وَمَا فِي الْأَرْضِ، مَنْ ذَا الَّذِي يَشْفَعُ عِنْدَهُ إِلَّا بِإِذْنِهِ، يَعْلَمُ مَا بَيْنَ أَيْدِيهِمْ وَمَا خَلْفَهُمْ، وَلَا يُحِيطُونَ بِشَيْءٍ مِنْ عِلْمِهِ إِلَّا بِمَا شَاءَ، وَسِعَ كُرْسِيُّهُ السَّمَاوَاتِ وَالْأَرْضَ، وَلَا يَئُودُهُ حِفْظُهُمَا، وَهُوَ الْعَلِيُّ الْعَظِيمُ.",
                1
            ),

            (
                "masaa",
                "قُلْ هُوَ اللَّهُ أَحَدٌ، اللَّهُ الصَّمَدُ، لَمْ يَلِدْ وَلَمْ يُولَدْ، وَلَمْ يَكُن لَّهُ كُفُوًا أَحَدٌ.",
                3
            ),

            (
                "masaa",
                "قُلْ أَعُوذُ بِرَبِّ الْفَلَقِ، مِن شَرِّ مَا خَلَقَ، وَمِن شَرِّ غَاسِقٍ إِذَا وَقَبَ، وَمِن شَرِّ النَّفَّاثَاتِ فِي الْعُقَدِ، وَمِن شَرِّ حَاسِدٍ إِذَا حَسَدَ.",
                3
            ),

            (
                "masaa",
                "قُلْ أَعُوذُ بِرَبِّ النَّاسِ، مَلِكِ النَّاسِ، إِلَهِ النَّاسِ، مِن شَرِّ الْوَسْوَاسِ الْخَنَّاسِ، الَّذِي يُوَسْوِسُ فِي صُدُورِ النَّاسِ، مِنَ الْجِنَّةِ وَالنَّاسِ.",
                3
            ),

            (
                "masaa",
                "أَمْسَيْنَا وَأَمْسَى الْمُلْكُ لِلَّهِ، وَالْحَمْدُ لِلَّهِ، لَا إِلَهَ إِلَّا اللَّهُ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ.",
                1
            ),

            (
                "masaa",
                "اللَّهُمَّ بِكَ أَمْسَيْنَا، وَبِكَ أَصْبَحْنَا، وَبِكَ نَحْيَا، وَبِكَ نَمُوتُ، وَإِلَيْكَ الْمَصِيرُ.",
                1
            ),

            (
                "masaa",
                "رَضِيتُ بِاللَّهِ رَبًّا، وَبِالإِسْلَامِ دِينًا، وَبِمُحَمَّدٍ ﷺ نَبِيًّا.",
                3
            ),

            (
                "masaa",
                "أَعُوذُ بِكَلِمَاتِ اللَّهِ التَّامَّاتِ مِنْ شَرِّ مَا خَلَقَ.",
                3
            ),

            (
                "masaa",
                "اللَّهُمَّ إِنِّي أَسْأَلُكَ الْعَفْوَ وَالْعَافِيَةَ فِي الدُّنْيَا وَالْآخِرَةِ.",
                1
            )
        ]


        conn.executemany(
            """
            INSERT INTO azkar
            (category, text, count)
            VALUES (?, ?, ?)
            """,
            azkar
        )

        conn.commit()


# =========================================================
# تهيئة المشروع - Offline
# =========================================================

def initialize():

    create_tables()

    if quran_is_ready():

        print("📖 القرآن الكريم موجود محليًا.")
        print("✅ تم العثور على 114 سورة.")

    else:

        print("⚠️ تحذير:")
        print("قاعدة بيانات القرآن غير مكتملة.")
        print("تأكد أن quran_text.db هي قاعدة البيانات الأصلية.")

    insert_default_azkar()

    print("========================================")
    print("🔒 وضع Offline مفعل")
    print("🌐 لا يوجد اتصال بالإنترنت")
    print("========================================")


initialize()


# =========================================================
# الصفحة الرئيسية
# =========================================================

@app.route("/")
def index():

    return send_from_directory(
        ".",
        "index.html"
    )


# =========================================================
# API السور
# =========================================================

@app.route("/api/surahs", methods=["GET"])
def get_surahs():

    with get_db() as conn:

        rows = conn.execute(
            """
            SELECT id, name, type, number_of_ayahs
            FROM surahs
            ORDER BY id
            """
        ).fetchall()

    return jsonify([
        dict(row)
        for row in rows
    ])


# =========================================================
# API سورة واحدة
# =========================================================

@app.route("/api/surah/<int:surah_id>", methods=["GET"])
def get_surah(surah_id):

    if not 1 <= surah_id <= 114:

        return jsonify({
            "error": "رقم السورة غير صحيح"
        }), 400


    with get_db() as conn:

        surah = conn.execute(
            """
            SELECT *
            FROM surahs
            WHERE id = ?
            """,
            (surah_id,)
        ).fetchone()


        verses = conn.execute(
            """
            SELECT verse_number, text
            FROM verses
            WHERE surah_id = ?
            ORDER BY verse_number
            """,
            (surah_id,)
        ).fetchall()


    if not surah:

        return jsonify({
            "error": "السورة غير موجودة"
        }), 404


    return jsonify({
        "id": surah["id"],
        "name": surah["name"],
        "type": surah["type"],
        "number_of_ayahs": surah["number_of_ayahs"],
        "verses": [
            dict(verse)
            for verse in verses
        ]
    })


# =========================================================
# البحث في القرآن
# =========================================================

@app.route("/api/search", methods=["GET"])
def search_quran():

    query = request.args.get(
        "q",
        ""
    ).strip()


    if len(query) < 2:

        return jsonify([])


    with get_db() as conn:

        rows = conn.execute(
            """
            SELECT
                verses.surah_id,
                surahs.name AS surah_name,
                verses.verse_number,
                verses.text
            FROM verses
            INNER JOIN surahs
                ON surahs.id = verses.surah_id
            WHERE verses.text LIKE ?
            ORDER BY verses.surah_id, verses.verse_number
            LIMIT 100
            """,
            (f"%{query}%",)
        ).fetchall()


    return jsonify([
        dict(row)
        for row in rows
    ])


# =========================================================
# الأذكار
# =========================================================

@app.route("/api/azkar", methods=["GET"])
def get_azkar():

    category = request.args.get(
        "category",
        "sabah"
    )


    if category not in ["sabah", "masaa"]:

        return jsonify({
            "error": "قسم الأذكار غير صحيح"
        }), 400


    with get_db() as conn:

        rows = conn.execute(
            """
            SELECT id, text, count
            FROM azkar
            WHERE category = ?
            ORDER BY id
            """,
            (category,)
        ).fetchall()


    return jsonify([
        dict(row)
        for row in rows
    ])


# =========================================================
# Health Check
# =========================================================

@app.route("/api/health", methods=["GET"])
def health():

    with get_db() as conn:

        surahs = conn.execute(
            "SELECT COUNT(*) FROM surahs"
        ).fetchone()[0]

        verses = conn.execute(
            "SELECT COUNT(*) FROM verses"
        ).fetchone()[0]

        azkar = conn.execute(
            "SELECT COUNT(*) FROM azkar"
        ).fetchone()[0]


    return jsonify({
        "status": "offline",
        "internet_required": False,
        "surahs": surahs,
        "verses": verses,
        "azkar": azkar
    })


# =========================================================
# تشغيل السيرفر
# =========================================================

if __name__ == "__main__":

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    print("")
    print("========================================")
    print("📖 المصحف الشريف والأذكار")
    print("🔒 وضع Offline")
    print("🌐 لا يحتاج إلى إنترنت")
    print("========================================")
    print("")

    app.run(
        host="127.0.0.1",
        port=port,
        debug=False
    )
