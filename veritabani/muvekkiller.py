from datetime import date
from typing import Optional

from veritabani.database import get_connection


def muvekkil_ekle(
    ad: str,
    soyad: str,
    tc_kimlik_no: Optional[str] = None,
    dogum_tarihi: Optional[str] = None,
    cinsiyet: Optional[str] = None,
    telefon: Optional[str] = None,
    e_posta: Optional[str] = None,
    adres: Optional[str] = None,
    meslek: Optional[str] = None,
    ucret: float = 0.0,
    tahsil_edilen: float = 0.0,
    notlar: Optional[str] = None,
) -> int:
    """
    Yeni bir müvekkil kaydeder.

    Başarılı olursa oluşturulan müvekkilin ID'sini döndürür.
    """

    if not ad or not ad.strip():
        raise ValueError("Müvekkil adı boş bırakılamaz.")

    if not soyad or not soyad.strip():
        raise ValueError("Müvekkil soyadı boş bırakılamaz.")

    if ucret < 0:
        raise ValueError("Ücret negatif olamaz.")

    if tahsil_edilen < 0:
        raise ValueError("Tahsil edilen tutar negatif olamaz.")

    conn = get_connection()

    try:
        cursor = conn.execute(
            """
            INSERT INTO muvekkiller (
                ad,
                soyad,
                tc_kimlik_no,
                dogum_tarihi,
                cinsiyet,
                telefon,
                e_posta,
                adres,
                meslek,
                ucret,
                tahsil_edilen,
                notlar
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                ad.strip(),
                soyad.strip(),
                tc_kimlik_no,
                dogum_tarihi,
                cinsiyet,
                telefon,
                e_posta,
                adres,
                meslek,
                ucret,
                tahsil_edilen,
                notlar,
            ),
        )

        conn.commit()
        return cursor.lastrowid

    finally:
        conn.close()


def muvekkil_getir(muvekkil_id: int):
    """
    ID'si verilen tek bir müvekkili getirir.
    Bulunamazsa None döndürür.
    """

    conn = get_connection()

    try:
        row = conn.execute(
            """
            SELECT *
            FROM muvekkiller
            WHERE id = ?
            """,
            (muvekkil_id,),
        ).fetchone()

        return row

    finally:
        conn.close()


def muvekkilleri_listele():
    """
    Tüm müvekkilleri soyad ve ada göre sıralayarak getirir.
    """

    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT *
            FROM muvekkiller
            ORDER BY soyad COLLATE NOCASE, ad COLLATE NOCASE
            """
        ).fetchall()

        return rows

    finally:
        conn.close()


def muvekkil_ara(arama: str):
    """
    Ad, soyad veya telefon içinde arama yapar.
    """

    if not arama or not arama.strip():
        return muvekkilleri_listele()

    arama = arama.strip()
    desen = f"%{arama}%"

    conn = get_connection()

    try:
        rows = conn.execute(
            """
            SELECT *
            FROM muvekkiller
            WHERE ad LIKE ?
               OR soyad LIKE ?
               OR telefon LIKE ?
            ORDER BY soyad COLLATE NOCASE, ad COLLATE NOCASE
            """,
            (desen, desen, desen),
        ).fetchall()

        return rows

    finally:
        conn.close()


def muvekkil_guncelle(muvekkil_id: int, **alanlar) -> None:
    """
    Müvekkil bilgilerini günceller.

    Örnek:
        muvekkil_guncelle(
            1,
            telefon="05xx xxx xx xx",
            meslek="Avukat"
        )
    """

    izinli_alanlar = {
        "ad",
        "soyad",
        "tc_kimlik_no",
        "dogum_tarihi",
        "cinsiyet",
        "telefon",
        "e_posta",
        "adres",
        "meslek",
        "ucret",
        "tahsil_edilen",
        "notlar",
    }

    if not alanlar:
        return

    hatali_alanlar = set(alanlar) - izinli_alanlar

    if hatali_alanlar:
        raise ValueError(
            f"Güncellenmesine izin verilmeyen alanlar: "
            f"{', '.join(sorted(hatali_alanlar))}"
        )

    if "ucret" in alanlar and alanlar["ucret"] < 0:
        raise ValueError("Ücret negatif olamaz.")

    if "tahsil_edilen" in alanlar and alanlar["tahsil_edilen"] < 0:
        raise ValueError("Tahsil edilen tutar negatif olamaz.")

    alanlar["guncelleme_tarihi"] = date.today().isoformat()

    set_parcalari = []
    degerler = []

    for alan, deger in alanlar.items():
        set_parcalari.append(f"{alan} = ?")
        degerler.append(deger)

    degerler.append(muvekkil_id)

    conn = get_connection()

    try:
        conn.execute(
            f"""
            UPDATE muvekkiller
            SET {", ".join(set_parcalari)}
            WHERE id = ?
            """,
            degerler,
        )

        conn.commit()

    finally:
        conn.close()


def muvekkil_sil(muvekkil_id: int) -> None:
    """
    Müvekkili siler.

    Not:
    Dosyalar foreign key + ON DELETE CASCADE nedeniyle
    müvekkille ilişkili dosyaları da silebilir.
    Bu yüzden arayüzde gerçek silme işlemi için
    ayrıca onay isteyeceğiz.
    """

    conn = get_connection()

    try:
        conn.execute(
            """
            DELETE FROM muvekkiller
            WHERE id = ?
            """,
            (muvekkil_id,),
        )

        conn.commit()

    finally:
        conn.close()