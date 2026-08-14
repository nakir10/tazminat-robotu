from pathlib import Path
import sqlite3


# ---------------------------------------------------------
# VERİTABANI KONUMU
# ---------------------------------------------------------

PROJE_KOKU = Path(__file__).resolve().parent.parent
VERI_KLASORU = PROJE_KOKU / "veri"
VERI_KLASORU.mkdir(exist_ok=True)

DB_PATH = VERI_KLASORU / "hukuk_ofisi.db"


# ---------------------------------------------------------
# VERİTABANI BAĞLANTISI
# ---------------------------------------------------------

def get_connection():
    """
    SQLite veritabanına bağlantı açar.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ---------------------------------------------------------
# TABLOLARI OLUŞTUR
# ---------------------------------------------------------

def init_db():
    """
    Hukuk ofisi otomasyonu için gerekli tabloları oluşturur.
    Tablolar zaten varsa yeniden oluşturmaz.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        # -------------------------------------------------
        # KULLANICILAR
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS kullanicilar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_adi TEXT NOT NULL UNIQUE,
                ad_soyad TEXT NOT NULL,
                rol TEXT NOT NULL DEFAULT 'Avukat',
                parola_hash TEXT NOT NULL,
                aktif INTEGER NOT NULL DEFAULT 1,
                olusturma_tarihi TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # -------------------------------------------------
        # MÜVEKKİLLER
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS muvekkiller (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ad TEXT NOT NULL,
                soyad TEXT NOT NULL,
                tc_kimlik_no TEXT,
                dogum_tarihi TEXT,
                cinsiyet TEXT,
                telefon TEXT,
                e_posta TEXT,
                adres TEXT,
                meslek TEXT,
                ucret REAL DEFAULT 0,
                tahsil_edilen REAL DEFAULT 0,
                notlar TEXT,
                olusturma_tarihi TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TEXT
            )
        """)

        # -------------------------------------------------
        # DOSYALAR
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dosyalar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                muvekkil_id INTEGER NOT NULL,
                dosya_no TEXT NOT NULL UNIQUE,
                dosya_adi TEXT NOT NULL,
                dosya_turu TEXT,
                karsi_taraf TEXT,
                mahkeme TEXT,
                esas_no TEXT,
                karar_no TEXT,
                durum TEXT NOT NULL DEFAULT 'Aktif',
                acilis_tarihi TEXT,
                kapanis_tarihi TEXT,
                genel_not TEXT,
                FOREIGN KEY (muvekkil_id)
                    REFERENCES muvekkiller(id)
                    ON DELETE CASCADE
            )
        """)

        # -------------------------------------------------
        # DOSYA NOTLARI
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dosya_notlari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dosya_id INTEGER NOT NULL,
                kullanici_id INTEGER,
                tarih_saat TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                metin TEXT NOT NULL,
                FOREIGN KEY (dosya_id)
                    REFERENCES dosyalar(id)
                    ON DELETE CASCADE,
                FOREIGN KEY (kullanici_id)
                    REFERENCES kullanicilar(id)
                    ON DELETE SET NULL
            )
        """)

        # -------------------------------------------------
        # GENEL NOT DEFTERİ
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS genel_notlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                kullanici_id INTEGER,
                baslik TEXT,
                metin TEXT NOT NULL,
                sabit INTEGER NOT NULL DEFAULT 0,
                olusturma_tarihi TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                guncelleme_tarihi TEXT,
                FOREIGN KEY (kullanici_id)
                    REFERENCES kullanicilar(id)
                    ON DELETE SET NULL
            )
        """)

        # -------------------------------------------------
        # İÇTİHAT BANKASI
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ictihatlar (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                mahkeme TEXT NOT NULL,
                daire TEXT,
                esas_no TEXT,
                karar_no TEXT,
                karar_tarihi TEXT,
                konu TEXT,
                ozet TEXT NOT NULL,
                etiketler TEXT,
                tam_metin_kunye TEXT,
                olusturma_tarihi TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # -------------------------------------------------
        # MUHASEBE KAYITLARI
        # -------------------------------------------------
        #
        # islem_turu:
        #   'tahsilat'
        #   'gider'
        #
        # İkisini ayrı tablo yapmak yerine tek tabloda
        # tutuyoruz.
        # -------------------------------------------------

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS muhasebe_kayitlari (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                islem_turu TEXT NOT NULL,
                tarih TEXT NOT NULL,
                kategori TEXT NOT NULL,
                aciklama TEXT,
                tutar REAL NOT NULL,
                notlar TEXT,
                olusturma_tarihi TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        conn.commit()

    finally:
        conn.close()


# ---------------------------------------------------------
# TEST
# ---------------------------------------------------------

if __name__ == "__main__":
    init_db()
    print(f"Veritabanı hazır: {DB_PATH}")