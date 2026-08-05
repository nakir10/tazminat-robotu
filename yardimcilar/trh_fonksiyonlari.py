from datetime import date

from veriler.trh2010 import (
    TRH2010_ERKEK,
    TRH2010_KADIN,
)
def _trh_row(yas: int, cinsiyet: str) -> tuple:
    tablo = TRH2010_ERKEK if cinsiyet == "Erkek" else TRH2010_KADIN
    return tablo[max(0, min(99, int(yas)))]

def get_Dx(yas: int, cinsiyet: str) -> float:
    return _trh_row(yas, cinsiyet)[5]

def get_Nx(yas: int, cinsiyet: str) -> float:
    return _trh_row(yas, cinsiyet)[6]

def get_ex(yas: int, cinsiyet: str) -> float:
    """ex: x yaşında beklenen ek yaşam süresi (yıl)."""
    return _trh_row(yas, cinsiyet)[4]

def anuite_tam_hayat(yas: int, cinsiyet: str) -> float:
    """
    äx = Nx / Dx  (Dönem Başı Ödemeli Tam Hayat Anüitesi, yıllık birim)
    Ek-7 formülü. Aylık tazminata çevirmek için ×12 uygulayınız.
    """
    Dx = get_Dx(yas, cinsiyet)
    return get_Nx(yas, cinsiyet) / Dx if Dx else 0.0

def anuite_donemsel(yas: int, cinsiyet: str, n_yil: float) -> float:
    """
    äx:n = (Nx − Nx+n) / Dx  (Dönem Başı Ödemeli Dönemsel Hayat Anüitesi, yıllık birim)
    n_yil kesirli ise Nx+n lineer interpolasyonla bulunur.
    """
    if n_yil <= 0:
        return 0.0
    Dx = get_Dx(yas, cinsiyet)
    if not Dx:
        return 0.0
    bitis_tam = yas + int(n_yil)
    kesir = n_yil - int(n_yil)
    if kesir == 0 or bitis_tam >= 99:
        Nx_n = get_Nx(min(bitis_tam, 99), cinsiyet)
    else:
        Nx_a = get_Nx(min(bitis_tam, 99), cinsiyet)
        Nx_b = get_Nx(min(bitis_tam + 1, 99), cinsiyet)
        Nx_n = Nx_a + kesir * (Nx_b - Nx_a)
    return max(0.0, (get_Nx(yas, cinsiyet) - Nx_n) / Dx)

def yas_tam(dogum: date, referans: date) -> int:
    return relativedelta(referans, dogum).years

def yas_tam_ay(dogum: date, referans: date) -> float:
    """Tam yıl + kesirli ay (aktif dönem hesabında hassasiyet için)."""
    d = relativedelta(referans, dogum)
    return d.years + d.months / 12