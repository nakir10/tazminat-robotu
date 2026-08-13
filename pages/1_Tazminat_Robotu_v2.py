"""
============================================================
ZORUNLU TRAFİK SİGORTASI TAZMİNAT HESAPLAMA ROBOTU v1.1
============================================================
Yasal Dayanak:
  - 2918 sayılı Karayolları Trafik Kanunu (KTK)
  - Karayolları Motorlu Araçlar Zorunlu Mali Sorumluluk
    Sigortası Genel Şartları (RG-4/12/2021-31679)
    Ek-1 : Değer Kaybı Tazminatı Hesaplaması
    Ek-2 : Sakatlık Tazminatları Hesaplaması
    Ek-3 : Destekten Yoksun Kalma Tazminatı Hesaplaması
    Ek-7 : Tazminat Hesaplamalarında Esas Alınacak Hayat Tabloları
  - TRH-2010 Yaşam Tablosu (%1,65 iskonto oranı)

Değişiklik Kaydı — v1.0 → v1.1:
  [DÜZ-1] Modül 2: Aktif dönem geliri oransal güncelleme ile hesaplanıyor
           (Ek-2 Md.6/a — kaza geliri / kaza dönemi AGİ × hesap dönemi AGİ)
  [DÜZ-2] Modül 2: Askerlik dönemi artık aktif anüite süresinden düşülüyor
           (Ek-2 Md.6/3 — belgeli muafiyet yoksa 18-22 yaş pasif dönem)
  [DÜZ-3] Modül 3: İşlemiş dönem gelirinden destek şahsının payı çıkarılıyor
           (Ek-3 Md.6 — yalnızca hak sahiplerine düşen kısım dağıtılır)
  [DÜZ-4] Modül 3: Eş işleyecek döneminde aktif+pasif geçişi uygulanıyor
  [DÜZ-5] Modül 3: Ölü kod (isleyecek_es) temizlendi, tek tutarlı hesap yolu
  [DÜZ-6] Modül 3: Çocuk cinsiyeti artık parametreden alınıyor (hardcode kaldırıldı)
  [DÜZ-7] Modül 1: G.3 sınır kontrolü — km=0 durumunda yanlış tetiklenme düzeltildi
  [DÜZ-8] Modül 2: ae_aktif/ae_pasif NameError riski giderildi (güvenli None başlatma)
  [DÜZ-9] Modül 3: İşlemiş dönem hesabında destek payı uyarısı netleştirildi

Teknik Notlar:
  - İskonto oranı   : %1,65 (sabit, mevzuat gereği — Ek-2 Md.4, Ek-3 Md.4)
  - Aktif dönem     : 18–65 yaş
  - Pasif dönem gel.: AGİ hariç net asgari ücret (Ek-2 Md.6/2, Ek-3 Md.7/2)
  - İşlemiş dönem  : iskontosuz, güncellemesiz (Ek-2 Md.7/1, Ek-3 Md.8/1)
  - İşleyecek dönem: äx = Nx/Dx veya äx:n = (Nx−Nx+n)/Dx
  - Anüite birimi  : yıllık; aylık gelirle çarpımda ×12 uygulanır
  - Askerlik       : Ek-2'de pasif sayılır; Ek-3'te tenzil YAPILMAZ
============================================================
"""

import streamlit as st

# Sayfa Yapılandırması

# --- ŞİFRE KORUMA BAŞLANGICI ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

if not st.session_state.giris_yapildi:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_s1, col_s2, col_s3 = st.columns([1, 2, 1]) # Ekranı ortalamak için
    
    with col_s2:
        st.error("🔒 BU ALANA ERİŞİM KISITLANMIŞTIR")
        st.subheader("Sistemi Kullanmak İçin Giriş Yapın")
        sifre = st.text_input("Giriş Şifresi:", type="password")
        
        # Güncellenmiş yeni şifreniz
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            if sifre == "771044":  
                st.session_state.giris_yapildi = True
                st.rerun()
            else:
                st.error("Girdiğiniz şifre hatalıdır. Lütfen tekrar deneyiniz.")
    st.stop() # Şifre doğru girilene kadar alt kodların çalışmasını engeller
# --- ŞİFRE KORUMA BİTİŞİ ---
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from veriler.trh2010 import TRH2010_ERKEK, TRH2010_KADIN
from yardimcilar.trh_fonksiyonlari import (
    _trh_row,
    get_Dx,
    get_Nx,
    get_ex,
    anuite_tam_hayat,
    anuite_donemsel,
    yas_tam,
    yas_tam_ay,
)
from hesaplamalar.deger_kaybi import (
    get_R_katsayisi,
    get_K_katsayisi,
    _km_tablo_alt_siniri,
    deger_kaybi_hesapla,
    arac_gruplari,
)
from hesaplamalar.bedensel_hasar import bedensel_hasar_hesapla
from hesaplamalar.destekten_yoksun import destekten_yoksun_kalma_hesapla

# ============================================================
# MODÜL 2: SAKATLIK TAZMİNATI
# Ek-2 (RG-4/12/2021-31679)
# ============================================================



# ============================================================
# MODÜL 3: DESTEKTEN YOKSUN KALMA TAZMİNATI
# Ek-3 (RG-4/12/2021-31679)
# ============================================================

# Yeniden evlenme olasılıkları — Ek-3 Madde 9
_YENIDEN_EVLENME = {
    "Kadın": [(17,20,0.52),(21,25,0.40),(26,30,0.27),(31,35,0.17),
              (36,40,0.09),(41,50,0.02),(51,55,0.01),(56,999,0.00)],
    "Erkek": [(17,20,0.90),(21,25,0.70),(26,30,0.48),(31,35,0.30),
              (36,40,0.15),(41,50,0.04),(51,55,0.02),(56,999,0.00)],
}

def get_yeniden_evlenme_olasiligi(yas: int, cinsiyet: str, velayetteki_cocuk: int = 0) -> float:
    """Ek-3 Madde 9: yeniden evlenme olasılığı; her velayet çocuğu için -5 puan."""
    oran = 0.0
    for alt, ust, p in _YENIDEN_EVLENME.get(cinsiyet, []):
        if alt <= yas <= ust:
            oran = p
            break
    return max(0.0, oran - velayetteki_cocuk * 0.05)




    def _isleyecek_gelir(n_yil: float, cinsiyet_k: str, yas_k: int) -> float:
        """
        [DÜZ-4] Hak sahibi için işleyecek dönem tazminatı:
        destek şahsının aktif → pasif dönem geçişini yansıtır.
        Aktif dönem: aktif_isleyecek_aylik × äx:n_aktif × 12
        Pasif dönem: pasif_aylik × äx+n_aktif:n_pasif × 12 (indirgenmis)
        """
        if donem_destek == "aktif" and yas_destek_hesap < 65:
            n_aktif_k = min(n_yil, 65 - yas_destek_hesap)  # aktif kalan
            n_pasif_k = max(0.0, n_yil - n_aktif_k)

            ae_a = _isleyecek_kisi(yas_k, cinsiyet_k, n_aktif_k)
            tutarA = aktif_isleyecek_aylik * ae_a * 12

            # Pasif kısım: hak sahibi yas_k + n_aktif_k yaşında başlar
            if n_pasif_k > 0:
                yas_k_pasif = yas_k + int(n_aktif_k)
                Dx_k = get_Dx(yas_k, cinsiyet_k)
                Dx_k_pasif = get_Dx(min(yas_k_pasif, 99), cinsiyet_k)
                ae_p_raw = _isleyecek_kisi(yas_k_pasif, cinsiyet_k, n_pasif_k)
                ae_p = ae_p_raw * (Dx_k_pasif / Dx_k) if Dx_k else 0.0
                tutarP = pasif_aylik * ae_p * 12
            else:
                tutarP = 0.0

            return tutarA + tutarP

        elif donem_destek == "aktif_2yil":
            n_aktif_k = min(n_yil, 2.0)
            n_pasif_k = max(0.0, n_yil - n_aktif_k)

            ae_a = _isleyecek_kisi(yas_k, cinsiyet_k, n_aktif_k)
            tutarA = aktif_isleyecek_aylik * ae_a * 12

            if n_pasif_k > 0:
                yas_k_pasif = yas_k + int(n_aktif_k)
                Dx_k = get_Dx(yas_k, cinsiyet_k)
                Dx_k_pasif = get_Dx(min(yas_k_pasif, 99), cinsiyet_k)
                ae_p_raw = _isleyecek_kisi(yas_k_pasif, cinsiyet_k, n_pasif_k)
                ae_p = ae_p_raw * (Dx_k_pasif / Dx_k) if Dx_k else 0.0
                tutarP = pasif_aylik * ae_p * 12
            else:
                tutarP = 0.0

            return tutarA + tutarP

        else:  # tamamen pasif
            ae = _isleyecek_kisi(yas_k, cinsiyet_k, n_yil)
            return pasif_aylik * ae * 12

    # ----------------------------------------------------------------
    # HAK SAHİBİ TAZMINATLARI
    # ----------------------------------------------------------------
    hak_sahibi_sonuclari = []

    # EŞ
    if es_dogum_tarihi is not None:
        yas_es = yas_tam(es_dogum_tarihi, hesap_tarihi)
        es_kisi_pay = es_pay_sayi / toplam_pay
        ex_es = get_ex(yas_es, es_cinsiyet)
        ev_ol = get_yeniden_evlenme_olasiligi(yas_es, es_cinsiyet, velayetteki_cocuk_sayisi)

        if es_yeniden_evlendi_mi and es_evlenme_tarihi:
            d_ev = relativedelta(es_evlenme_tarihi, hesap_tarihi)
            n_es = max(0.0, d_ev.years + d_ev.months / 12)
        else:
            n_es = min(ex_es, ex_destek)

        islemis_es = islemis_havuz * es_kisi_pay
        isleyecek_brut_es = _isleyecek_gelir(n_es, es_cinsiyet, yas_es) * es_kisi_pay
        isleyecek_net_es = isleyecek_brut_es * (1.0 - ev_ol)

        hak_sahibi_sonuclari.append({
            "tip": "Eş", "yas": yas_es, "pay_oran": es_kisi_pay,
            "ev_olasiligi": ev_ol, "n_desteklik": n_es,
            "islemis": islemis_es, "isleyecek": isleyecek_net_es,
            "toplam": islemis_es + isleyecek_net_es,
        })

    # ÇOCUKLAR
    for i, cocuk in enumerate(cocuklar):
        yas_cocuk = yas_tam(cocuk["dogum_tarihi"], hesap_tarihi)
        # [DÜZ-6] Cinsiyet parametreden alınıyor
        cocuk_cinsiyet = cocuk.get("cinsiyet", "Erkek")
        lisans_mi = cocuk.get("lisans_mi", False)
        desteklik_son = 25 if lisans_mi else 22
        n_cocuk = max(0.0, desteklik_son - yas_cocuk)
        cocuk_kisi_pay = 1 / toplam_pay

        islemis_cocuk = islemis_havuz * cocuk_kisi_pay
        isleyecek_cocuk = _isleyecek_gelir(n_cocuk, cocuk_cinsiyet, yas_cocuk) * cocuk_kisi_pay

        hak_sahibi_sonuclari.append({
            "tip": f"Çocuk {i+1} (Yaş: {yas_cocuk})", "yas": yas_cocuk,
            "pay_oran": cocuk_kisi_pay, "ev_olasiligi": 0.0,
            "n_desteklik": n_cocuk,
            "islemis": islemis_cocuk, "isleyecek": isleyecek_cocuk,
            "toplam": islemis_cocuk + isleyecek_cocuk,
        })

    # ANNE
    if anne_hayatta_mi and anne_dogum_tarihi:
        yas_anne = yas_tam(anne_dogum_tarihi, hesap_tarihi)
        ex_anne = get_ex(yas_anne, "Kadın")
        n_anne = min(ex_anne, ex_destek)
        anne_kisi_pay = anne_pay_sayi / toplam_pay

        islemis_anne = islemis_havuz * anne_kisi_pay
        isleyecek_anne = _isleyecek_gelir(n_anne, "Kadın", yas_anne) * anne_kisi_pay

        hak_sahibi_sonuclari.append({
            "tip": "Anne", "yas": yas_anne, "pay_oran": anne_kisi_pay,
            "ev_olasiligi": 0.0, "n_desteklik": n_anne,
            "islemis": islemis_anne, "isleyecek": isleyecek_anne,
            "toplam": islemis_anne + isleyecek_anne,
        })

    # BABA
    if baba_hayatta_mi and baba_dogum_tarihi:
        yas_baba = yas_tam(baba_dogum_tarihi, hesap_tarihi)
        ex_baba = get_ex(yas_baba, "Erkek")
        n_baba = min(ex_baba, ex_destek)
        baba_kisi_pay = baba_pay_sayi / toplam_pay

        islemis_baba = islemis_havuz * baba_kisi_pay
        isleyecek_baba = _isleyecek_gelir(n_baba, "Erkek", yas_baba) * baba_kisi_pay

        hak_sahibi_sonuclari.append({
            "tip": "Baba", "yas": yas_baba, "pay_oran": baba_kisi_pay,
            "ev_olasiligi": 0.0, "n_desteklik": n_baba,
            "islemis": islemis_baba, "isleyecek": isleyecek_baba,
            "toplam": islemis_baba + isleyecek_baba,
        })

    genel_brut = sum(h["toplam"] for h in hak_sahibi_sonuclari)
    kusur_indirimi = genel_brut * kusur_orani_destek
    genel_net = max(0.0, genel_brut - kusur_indirimi)

    return {
        "donem_tipi": donem_destek,
        "yas_destek_vefat": yas_destek_vefat,
        "yas_destek_hesap": yas_destek_hesap,
        "hak_sahibi_gelir_orani": hak_sahibi_gelir_orani,
        "toplam_pay": toplam_pay,
        "islemis_sure_ay": islemis_sure_ay,
        "hak_sahibi_sonuclari": hak_sahibi_sonuclari,
        "genel_toplam_brut": genel_brut,
        "kusur_indirimi": kusur_indirimi,
        "genel_toplam_net": genel_net,
        "hata": None,
    }


# ============================================================
# STREAMLIT ARAYÜZÜ
# ============================================================

def fmt(tutar: float) -> str:
    return f"₺{tutar:,.2f}"

def main():
    st.set_page_config(
        page_title="Tazminat Hesaplama Robotu v1.1",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
    html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;}
    .stApp{background:#F7F6F1;}
    [data-testid="stSidebar"]{background:#1A1A2E!important;border-right:3px solid #C9A84C;}
    [data-testid="stSidebar"] *{color:#E8E4D9!important;}
    [data-testid="stSidebar"] label{color:#C9A84C!important;font-size:0.73rem!important;font-weight:600!important;letter-spacing:.08em!important;text-transform:uppercase!important;}
    .rh{background:#1A1A2E;color:#F7F6F1;padding:1.8rem 2.5rem 1.4rem;border-radius:8px;margin-bottom:1.2rem;border-left:6px solid #C9A84C;font-family:'IBM Plex Serif',serif;}
    .rh h1{font-size:1.5rem;font-weight:600;color:#F7F6F1;margin:0 0 .3rem;}
    .rh .sub{font-size:.75rem;color:#C9A84C;letter-spacing:.12em;text-transform:uppercase;font-family:'IBM Plex Mono',monospace;}
    .sec{font-family:'IBM Plex Serif',serif;font-size:.95rem;font-weight:600;color:#1A1A2E;border-bottom:2px solid #C9A84C;padding-bottom:.35rem;margin:1.4rem 0 .8rem;}
    .card{background:#fff;border:1px solid #DDD9CE;border-radius:6px;padding:1rem 1.4rem;margin:.4rem 0;border-left:4px solid #C9A84C;}
    .card .lbl{font-size:.7rem;font-weight:600;color:#888;text-transform:uppercase;letter-spacing:.1em;font-family:'IBM Plex Mono',monospace;}
    .card .val{font-size:1.4rem;font-weight:600;color:#1A1A2E;font-family:'IBM Plex Mono',monospace;margin-top:.15rem;}
    .card.grn{border-left-color:#2E7D32;} .card.blu{border-left-color:#1565C0;} .card.red{border-left-color:#C62828;}
    .grand{background:#1A1A2E;color:#F7F6F1;padding:1.4rem 2rem;border-radius:8px;margin-top:1.2rem;display:flex;justify-content:space-between;align-items:center;border:2px solid #C9A84C;}
    .grand .gl{font-family:'IBM Plex Serif',serif;font-size:.95rem;color:#C9A84C;letter-spacing:.05em;}
    .grand .gv{font-family:'IBM Plex Mono',monospace;font-size:1.7rem;font-weight:600;color:#F7F6F1;}
    .warn{background:#FFF8E1;border:1px solid #F9A825;border-left:4px solid #F9A825;border-radius:4px;padding:.75rem 1rem;margin:.4rem 0;font-size:.81rem;color:#5D4037;}
    .err{background:#FFEBEE;border:1px solid #C62828;border-left:4px solid #C62828;border-radius:4px;padding:.75rem 1rem;margin:.4rem 0;font-size:.84rem;color:#C62828;font-weight:500;}
    .ptbl{width:100%;border-collapse:collapse;font-size:.82rem;margin:.4rem 0;}
    .ptbl th{background:#F0EDE8;color:#1A1A2E;font-weight:600;padding:.45rem .7rem;text-align:left;font-family:'IBM Plex Mono',monospace;font-size:.72rem;letter-spacing:.06em;text-transform:uppercase;}
    .ptbl td{padding:.38rem .7rem;border-bottom:1px solid #E8E4DC;color:#333;}
    .ptbl tr:hover td{background:#FAF8F3;}
    .stButton>button{background:#1A1A2E!important;color:#C9A84C!important;border:2px solid #C9A84C!important;border-radius:4px!important;font-family:'IBM Plex Mono',monospace!important;font-weight:600!important;font-size:.83rem!important;letter-spacing:.1em!important;text-transform:uppercase!important;padding:.55rem 2rem!important;width:100%;}
    .stButton>button:hover{background:#C9A84C!important;color:#1A1A2E!important;}
    .foot{font-size:.7rem;color:#999;font-style:italic;margin-top:1.8rem;padding-top:.9rem;border-top:1px solid #DDD;font-family:'IBM Plex Serif',serif;}
    </style>
    """, unsafe_allow_html=True)

    # ── SIDEBAR ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚖️ Tazminat Robotu v1.1")
        st.caption("Zorunlu Trafik Sigortası · RG-4/12/2021-31679")
        st.markdown("---")
        modul = st.radio("HESAPLAMA MODÜLÜ", [
            "Değer Kaybı (Ek-1)",
            "Sakatlık Tazminatı (Ek-2)",
            "Destekten Yoksun Kalma (Ek-3)",
        ])
        st.markdown("---")

        # ── EK-1 GİRDİLERİ ──
        if modul == "Değer Kaybı (Ek-1)":
            arac_grubu = st.selectbox("Araç Grubu", arac_gruplari())
            piyasa_degeri = st.number_input("Piyasa Değeri (TL)", 0.0, value=500000.0, step=1000.0)
            arac_kodu_prv = "A"
            km_label = "Çalışma Saati" if arac_kodu_prv == "D" else "Kilometre"
            km = st.number_input(km_label, 0.0, value=45000.0, step=500.0)
            toplam_hasar = st.number_input("Toplam Hasar (KDV dahil, TL)", 0.0, value=80000.0, step=500.0)
            ticari_kiralik = st.checkbox("Ticari / Kiralık (G.1: −0,05)")
            sbm_kayit = st.number_input("SBM Hasar Kaydı Sayısı", 0, 10, 0,
                                         help="Her kayıt −0,03 | max −0,15")
            hurda_mi = st.checkbox("⚠️ Hurda / Trafikten Çekme Var")
            st.markdown("**HASARLI PARÇALAR**")
            n_parca = st.number_input("Parça Sayısı", 1, 15, 3, step=1)
            parcalar = []
            for i in range(int(n_parca)):
                with st.expander(f"Parça {i+1}", expanded=(i == 0)):
                    isim = st.text_input("Parça Adı", f"Parça {i+1}", key=f"p_isim_{i}")
                    Pi = st.number_input("Pi (Değişim Katsayısı)", 0.0, value=1.0, step=0.25, key=f"pi_{i}",
                                          help="Ek-1 Madde 4 tablosundan ilgili satır Pi değeri")
                    Oi = st.number_input("Oi (Onarım Katsayısı)", 0.0, value=0.0, step=0.25, key=f"oi_{i}",
                                          help="Hafif=0.50 | Orta=0.75 | Yüksek=1.00 | Değişimse 0")
                    Yi = st.number_input("Yi (Boya Katsayısı)", 0.0, value=0.0, step=0.25, key=f"yi_{i}",
                                          help="Boya yok=0 | Lokal=tablo lokal Yi | Tam=tablo tam Yi")
                    parcalar.append({"isim": isim, "Pi": Pi, "Oi": Oi, "Yi": Yi})

        # ── EK-2 GİRDİLERİ ──
        elif modul == "Sakatlık Tazminatı (Ek-2)":
            st.markdown("**MAĞDUR**")
            m_dogum = st.date_input("Doğum Tarihi", date(1985, 6, 15))
            m_cinsiyet = st.radio("Cinsiyet", ["Erkek", "Kadın"], horizontal=True)
            kaza_t = st.date_input("Kaza Tarihi", date(2024, 3, 10))
            hesap_t = st.date_input("Hesap Tarihi", date.today())
            st.markdown("**KURUL RAPORU**")
            gig_gun = st.number_input("GİG Süresi (Gün)", 0, value=90, step=1)
            sakatlik_oran = st.slider("Sürekli Sakatlık Oranı (%)", 0, 100, 30) / 100
            st.markdown("**GELİR**")
            resmi_gelir = st.checkbox("Resmî Belgeli Gelir Var", True)
            aylik_kaza = st.number_input("Kaza Tarihi Aylık Net Gelir (TL)", 0.0, value=25000.0, step=500.0)
            kaza_agi = st.number_input("Kaza Dönemi AGİ Dahil Net ASÜ (TL)", 0.0, value=20002.50, step=100.0,
                                        help="Kaza tarihindeki asgari ücret — oransal güncelleme için gerekli")
            hesap_agi_dahil = st.number_input("Hesap Dönemi AGİ Dahil Net ASÜ (TL)", 0.0, value=22104.67, step=100.0)
            agi_haric = st.number_input("AGİ Hariç Net ASÜ (TL)", 0.0, value=20903.0, step=100.0,
                                         help="Pasif dönem baz geliri")
            st.markdown("**ÇALIŞMA**")
            calisiyor_s = st.checkbox("Hesap Tarihinde Çalışıyor", True)
            emekli_s = st.checkbox("Emekli", False)
            ask_muaf = st.checkbox("Askerlik Muafiyeti Belgeli", False)
            st.markdown("**BAKICI**")
            bakici = st.selectbox("Bakıcı İhtiyacı", ["Yok", "Kısmi (%50)", "Tam (%100)"])
            bakici_bel = st.checkbox("Bakıcı Belgelenmiş (Brüt ASÜ baz)")
            brut_asu = st.number_input("Brüt ASÜ (TL)", 0.0, value=26005.50, step=100.0,
                                        disabled=not bakici_bel)
            st.markdown("**KUSUR**")
            kusur_m = st.slider("Mağdurun Kusur Oranı (%)", 0, 100, 0) / 100

        # ── EK-3 GİRDİLERİ ──
        else:
            st.markdown("**DESTEK ŞAHSI**")
            d_dogum = st.date_input("Doğum Tarihi", date(1975, 4, 20))
            d_cinsiyet = st.radio("Cinsiyet", ["Erkek", "Kadın"], horizontal=True)
            vefat_t = st.date_input("Vefat/Kaza Tarihi", date(2024, 1, 15))
            hesap_t_d = st.date_input("Hesap Tarihi", date.today())
            st.markdown("**GELİR**")
            resmi_gelir_d = st.checkbox("Resmî Belgeli Gelir Var", True)
            d_aylik = st.number_input("Aylık Net Gelir (TL)", 0.0, value=35000.0, step=500.0)
            vefat_agi = st.number_input("Vefat Dönemi AGİ Dahil Net ASÜ (TL)", 0.0, value=20002.50, step=100.0)
            hesap_agi_d = st.number_input("Hesap Dönemi AGİ Dahil Net ASÜ (TL)", 0.0, value=22104.67, step=100.0)
            agi_haric_d = st.number_input("AGİ Hariç Net ASÜ (TL)", 0.0, value=20903.0, step=100.0)
            d_cal = st.checkbox("Vefat Tarihinde Çalışıyordu", True)
            d_em = st.checkbox("Emekli", False)
            st.markdown("**HAK SAHİPLERİ**")
            es_var = st.checkbox("Eş", True)
            es_dogum_s = es_cinsiyet_s = ev_yeniden_s = ev_tar_s = velayet_s = None
            if es_var:
                es_dogum_s = st.date_input("Eşin Doğum Tarihi", date(1978, 9, 5))
                es_cinsiyet_s = st.radio("Eşin Cinsiyeti", ["Kadın", "Erkek"], horizontal=True)
                velayet_s = st.number_input("Velayetteki Çocuk Sayısı", 0, 10, 0)
                ev_yeniden_s = st.checkbox("Eş Yeniden Evlendi (Bilinen)")
                ev_tar_s = st.date_input("Yeniden Evlenme Tarihi", date(2025, 6, 1)) if ev_yeniden_s else None
            n_cocuk = st.number_input("Çocuk Sayısı", 0, 8, 1, step=1)
            cocuklar_list = []
            for i in range(int(n_cocuk)):
                with st.expander(f"Çocuk {i+1}"):
                    c_dog = st.date_input("Doğum Tarihi", date(2010, 3, 1), key=f"cd_{i}")
                    # [DÜZ-6] Cinsiyet artık alınıyor
                    c_cin = st.radio("Cinsiyet", ["Erkek", "Kadın"], horizontal=True, key=f"cc_{i}")
                    c_lis = st.checkbox("Lisans/Lisansüstü (25 yaş)", key=f"cl_{i}")
                    cocuklar_list.append({"dogum_tarihi": c_dog, "cinsiyet": c_cin, "lisans_mi": c_lis})
            anne_var = st.checkbox("Anne (Hak Sahibi)", False)
            anne_dog_s = st.date_input("Anne Doğum Tarihi", date(1950, 1, 1)) if anne_var else None
            baba_var = st.checkbox("Baba (Hak Sahibi)", False)
            baba_dog_s = st.date_input("Baba Doğum Tarihi", date(1948, 1, 1)) if baba_var else None
            st.markdown("**KUSUR**")
            kusur_d = st.slider("Destek Şahsının Kusur Oranı (%)", 0, 100, 0) / 100

    # ── ANA EKRAN ────────────────────────────────────────────
    st.markdown("""
    <div class="rh">
        <div class="sub">Adli Bilirkişi & Aktüer Standardında</div>
        <h1>⚖️ Zorunlu Trafik Sigortası Tazminat Hesaplama Robotu</h1>
        <div class="sub">RG-4/12/2021-31679 · TRH-2010 Hayat Tablosu · İskonto %1,65 · v1.1</div>
    </div>
    """, unsafe_allow_html=True)

    col_btn, col_warn = st.columns([1, 3])
    with col_btn:
        hesapla = st.button("▶  HESAPLA")
    with col_warn:
        st.markdown('<div class="warn"><strong>Hukuki Uyarı:</strong> Bu robot mevzuata uygun aktüeryal hesaplama yapar. Sonuçlar yargı kararının veya resmî bilirkişi raporunun yerini tutmaz.</div>', unsafe_allow_html=True)

    if not hesapla:
        st.markdown("""
        <div style="text-align:center;padding:3rem 2rem;">
            <div style="font-size:3rem;margin-bottom:1rem;">⚖️</div>
            <div style="font-family:'IBM Plex Serif',serif;font-size:1.05rem;color:#555;">
                Sol panelden modülü ve parametreleri seçin, ardından <strong>HESAPLA</strong>'ya basın.
            </div>
            <div style="margin-top:1rem;font-size:.78rem;color:#aaa;font-family:'IBM Plex Mono',monospace;">
                EK-1: Değer Kaybı · EK-2: Sakatlık Tazminatı · EK-3: Destekten Yoksun Kalma
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown("---")

    # ── EK-1 SONUÇLARI ───────────────────────────────────────
    if modul == "Değer Kaybı (Ek-1)":
        s = deger_kaybi_hesapla(arac_grubu, piyasa_degeri, km, parcalar,
                                toplam_hasar, ticari_kiralik, sbm_kayit, hurda_mi)
        if s["hata"]:
            st.markdown(f'<div class="err">🚫 {s["hata"]}</div>', unsafe_allow_html=True)
            return

        st.markdown('<div class="sec">DEĞER KAYBI TAZMİNATI — Ek-1</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="card"><div class="lbl">Araç Kodu</div><div class="val">{s["arac_kodu"]}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="card"><div class="lbl">Piyasa Değeri</div><div class="val">{fmt(piyasa_degeri)}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="card grn"><div class="lbl">Toplam Hasar</div><div class="val">{fmt(toplam_hasar)}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="sec">KATSAYI ZİNCİRİ</div>', unsafe_allow_html=True)
        rows = [
            ["R — Rayiç Değer Katsayısı", f"{s['R']:.2f}", f"Tablo R.1/R.2 · Piyasa Değeri {fmt(piyasa_degeri)}"],
            ["K — Kullanılmışlık Katsayısı", f"{s['K']:.2f}", f"Tablo K.1/K.2/K.3 · {km:,.0f} km/saat"],
            ["HK — Hasar Katsayısı (Σ Pi+Oi+Yi)", f"{s['HK']:.4f}", f"{len(parcalar)} parça toplamı"],
            ["T — Hasar Tutarı Katsayısı", f"{s['T']:.4f}", f"({fmt(toplam_hasar)} / {fmt(piyasa_degeri)} × 100) × 0,10"],
            ["H — Hasara Uğrayan Parçalar Katsayısı", f"{s['H']:.4f}", f"(HK + T) / 100"],
            ["G.1 — Ticari/Kiralık", f"{s['G1']:+.2f}", "Ticari/Kiralık: −0,05 | Diğer: 0,00"],
            ["G.2 — SBM Hasar Geçmişi", f"{s['G2']:+.2f}", f"{sbm_kayit} kayıt × (−0,03) | max −0,15"],
            ["G.3 — Km Alt Sınır Yakınlığı (≤1000 km)", f"{s['G3']:+.2f}", "0 < fark ≤ 1000 km ise +0,05 | Diğer: 0,00"],
            ["G — Genel Değerlendirme Katsayısı", f"{s['G']:.4f}", f"1 + ({s['G1']:.2f} + {s['G2']:.2f} + {s['G3']:.2f})"],
        ]
        df = pd.DataFrame(rows, columns=["Parametre", "Değer", "Açıklama / Mevzuat Dayanağı"])
        st.markdown(df.to_html(index=False, classes="ptbl"), unsafe_allow_html=True)

        st.markdown('<div class="sec">NİHAİ FORMÜL</div>', unsafe_allow_html=True)
        carpan_not = " × 2,5 (Motosiklet — Ek-1 Madde 6/2)" if s["carpan"] == 2.5 else ""
        st.markdown(f"""
        <div style="background:#F0EDE8;padding:.9rem 1.4rem;border-radius:6px;font-family:'IBM Plex Mono',monospace;font-size:.85rem;color:#1A1A2E;margin:.4rem 0;">
        DK = Piyasa Değeri × R × K × H × G{carpan_not}<br>
        DK = {fmt(piyasa_degeri)} × {s['R']:.2f} × {s['K']:.2f} × {s['H']:.4f} × {s['G']:.4f} = {fmt(s['DK_ham'])}
        {"<br><strong>DK_nihai = " + fmt(s['DK_ham']) + " × 2,5 = " + fmt(s['DK_nihai']) + "</strong>" if s['carpan'] == 2.5 else ""}
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f'<div class="grand"><div class="gl">ARAÇ DEĞER KAYBI TAZMİNATI (Ek-1)</div><div class="gv">{fmt(s["DK_nihai"])}</div></div>', unsafe_allow_html=True)

    # ── EK-2 SONUÇLARI ───────────────────────────────────────
    elif modul == "Sakatlık Tazminatı (Ek-2)":
        s = bedensel_hasar_hesapla(
            dogum_tarihi=m_dogum, cinsiyet=m_cinsiyet,
            kaza_tarihi=kaza_t, hesap_tarihi=hesap_t,
            gig_sure_gun=gig_gun, sakatlik_orani=sakatlik_oran,
            aylik_net_gelir_kaza=aylik_kaza,
            kaza_donemi_agi_dahil_net=kaza_agi,
            hesap_donemi_agi_dahil_net=hesap_agi_dahil,
            agi_haric_net_asgari=agi_haric,
            resmi_belgeli_gelir=resmi_gelir,
            calisiyor_mu=calisiyor_s, emekli_mi=emekli_s,
            askerlik_belgeli_muafiyet=ask_muaf,
            bakici_ihtiyaci=bakici, bakici_belgeli=bakici_bel,
            brut_asgari_ucret=brut_asu,
            kusur_orani_mazdur=kusur_m,
        )
        if s.get("hata"):
            st.markdown(f'<div class="err">🚫 {s["hata"]}</div>', unsafe_allow_html=True)
            return

        donem_txt = {"aktif":"Aktif (18–65 yaş)","pasif":"Pasif","aktif_2yil":"Aktif +2 Yıl (65+)"}
        st.markdown('<div class="sec">SAKATLIK TAZMİNATI — Ek-2</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="card"><div class="lbl">Hesap Tarihi Yaşı</div><div class="val">{s["yas_hesap"]}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="card"><div class="lbl">Dönem</div><div class="val" style="font-size:1rem;">{donem_txt.get(s["donem_tipi"],"")}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="card"><div class="lbl">Sakatlık Oranı</div><div class="val">{sakatlik_oran*100:.0f}%</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="sec">HESAPLAMA DETAYI</div>', unsafe_allow_html=True)
        rows2 = [
            ["GİG Süresi", f"{s['gig_sure_gun']} gün ({s['gig_sure_ay']:.2f} ay)", "Kurul Raporu — GİG döneminde sakatlık %100 varsayılır (Ek-2 Md.1/2)"],
            ["GİG Aylık Geliri", fmt(aylik_kaza if resmi_gelir else hesap_agi_dahil), "İşlemiş dönem — iskontosuz, güncellemesiz"],
            ["GİG Tazminatı", fmt(s["gig_tazminat"]), "Aylık Gelir × Süre (ay)"],
            ["İşleyecek Aktif Aylık Gelir [DÜZ-1]", fmt(s["aktif_isleyecek_aylik"]), "Ek-2 Md.6/a: kaza geliri / kaza AGİ × hesap AGİ (oransal)"],
            ["äx Aktif (yıllık, ×12→aylık)", f"{s['ae_aktif_yillik']:.5f}", f"äx:n = (Nx−Nx+n)/Dx · TRH-2010 · %1,65 iskonto"],
            ["äx Pasif (65+ indirgenmis, yıllık, ×12→aylık)", f"{s['ae_pasif_yillik']:.5f}", "Nx(65)/Dx(hesap_yaş) · pasif baz: AGİ hariç net ASÜ"],
            ["Askerlik Tenzili [DÜZ-2]", f"{s['askerlik_tenzil_yil']:.1f} yıl" if s['askerlik_tenzil_yil'] else "Yok/Muaf", "Ek-2 Md.6/3 — 18-22 yaş pasif dönem; belgeli muafiyet yoksa"],
            ["Sürekli Sakatlık Tazminatı", fmt(s["surekkli_sakatlik"]), f"Aktif+Pasif anüite × %{sakatlik_oran*100:.0f}"],
            ["Bakıcı Gideri", fmt(s["bakici_gideri"]), f"{'Brüt ASÜ' if bakici_bel else 'AGİ dahil net ASÜ'} × {bakici} × äx"],
        ]
        df2 = pd.DataFrame(rows2, columns=["Kalem", "Değer", "Açıklama / Mevzuat Dayanağı"])
        st.markdown(df2.to_html(index=False, classes="ptbl"), unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="card blu"><div class="lbl">GİG Tazminatı</div><div class="val">{fmt(s["gig_tazminat"])}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="card blu"><div class="lbl">Sürekli Sakatlık</div><div class="val">{fmt(s["surekkli_sakatlik"])}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="card blu"><div class="lbl">Bakıcı Gideri</div><div class="val">{fmt(s["bakici_gideri"])}</div></div>', unsafe_allow_html=True)

        if kusur_m > 0:
            st.markdown(f'<div class="warn"><strong>Kusur Tenzili (A.6/b):</strong> Mağdurun %{kusur_m*100:.0f} kusuruna karşılık {fmt(s["kusur_indirimi"])} düşülmüştür.</div>', unsafe_allow_html=True)

        label = "NET (Kusur Tenzilli)" if kusur_m > 0 else "TOPLAM"
        st.markdown(f'<div class="grand"><div class="gl">SAKATLIK TAZMİNATI {label} (Ek-2)</div><div class="gv">{fmt(s["toplam_net"])}</div></div>', unsafe_allow_html=True)

    # ── EK-3 SONUÇLARI ───────────────────────────────────────
    else:
        s = destekten_yoksun_kalma_hesapla(
            destek_dogum_tarihi=d_dogum, destek_cinsiyet=d_cinsiyet,
            vefat_tarihi=vefat_t, hesap_tarihi=hesap_t_d,
            destek_aylik_net_gelir=d_aylik,
            vefat_donemi_agi_dahil_net=vefat_agi,
            hesap_donemi_agi_dahil_net=hesap_agi_d,
            agi_haric_net_asgari=agi_haric_d,
            resmi_belgeli_gelir=resmi_gelir_d,
            destek_calisiyor_mu=d_cal, destek_emekli_mi=d_em,
            es_dogum_tarihi=es_dogum_s if es_var else None,
            es_cinsiyet=es_cinsiyet_s if es_var else "Kadın",
            es_yeniden_evlendi_mi=ev_yeniden_s if es_var else False,
            es_evlenme_tarihi=ev_tar_s if (es_var and ev_yeniden_s) else None,
            velayetteki_cocuk_sayisi=int(velayet_s) if es_var else 0,
            cocuklar=cocuklar_list,
            anne_dogum_tarihi=anne_dog_s, anne_hayatta_mi=anne_var,
            baba_dogum_tarihi=baba_dog_s, baba_hayatta_mi=baba_var,
            kusur_orani_destek=kusur_d,
        )
        if s.get("hata"):
            st.markdown(f'<div class="err">🚫 {s["hata"]}</div>', unsafe_allow_html=True)
            return

        donem_txt = {"aktif":"Aktif (18–65)","pasif":"Pasif","aktif_2yil":"Aktif +2 Yıl"}
        st.markdown('<div class="sec">DESTEKTEN YOKSUN KALMA TAZMİNATI — Ek-3</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="card"><div class="lbl">Vefat Yaşı</div><div class="val">{s["yas_destek_vefat"]}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="card"><div class="lbl">Dönem</div><div class="val" style="font-size:1rem;">{donem_txt.get(s["donem_tipi"],"")}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="card"><div class="lbl">İşlemiş Dönem</div><div class="val" style="font-size:1rem;">{s["islemis_sure_ay"]:.1f} Ay</div></div>', unsafe_allow_html=True)

        hs_orani_pct = s["hak_sahibi_gelir_orani"] * 100
        st.markdown(f'<div class="warn"><strong>[DÜZ-3] Pay Düzeltmesi (Ek-3 Md.6):</strong> Toplam {s["toplam_pay"]} payın 2\'si destek şahsına ayrılmış; hak sahiplerine düşen gelir oranı <strong>%{hs_orani_pct:.1f}</strong> olarak uygulanmıştır.</div>', unsafe_allow_html=True)

        st.markdown('<div class="sec">HAK SAHİBİ BAZLI TAZMİNAT</div>', unsafe_allow_html=True)
        if s["hak_sahibi_sonuclari"]:
            df3 = pd.DataFrame([{
                "Hak Sahibi": h["tip"],
                "Yaş": h["yas"],
                "Pay Oranı": f"{h['pay_oran']:.4f}",
                "Desteklik (yıl)": f"{h['n_desteklik']:.1f}",
                "Yeniden Evl.": f"%{h['ev_olasiligi']*100:.0f}" if h["ev_olasiligi"] > 0 else "—",
                "İşlemiş Dönem": fmt(h["islemis"]),
                "İşleyecek Dönem": fmt(h["isleyecek"]),
                "KİŞİ TOPLAMI": fmt(h["toplam"]),
            } for h in s["hak_sahibi_sonuclari"]])
            st.markdown(df3.to_html(index=False, classes="ptbl"), unsafe_allow_html=True)
        else:
            st.warning("Hak sahibi girilmedi.")

        if kusur_d > 0:
            st.markdown(f'<div class="warn"><strong>Kusur Tenzili (A.6/d):</strong> Destek şahsının %{kusur_d*100:.0f} kusuruna karşılık {fmt(s["kusur_indirimi"])} düşülmüştür.</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="grand"><div class="gl">DESTEKTEN YOKSUN KALMA TAZMİNATI NET (Ek-3)</div><div class="gv">{fmt(s["genel_toplam_net"])}</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="warn"><strong>Not (Ek-3 Md.9/3):</strong> Destekten yoksun kalma hesabında askerlik dönemi tenzili YAPILMAMAKTADIR (Ek-2\'den farklı).</div>', unsafe_allow_html=True)

    # Footer
    st.markdown(f"""
    <div class="foot">
        Hesaplama Tarihi: {date.today().strftime('%d.%m.%Y')} &nbsp;|&nbsp;
        Mevzuat: RG-4/12/2021-31679 &nbsp;|&nbsp;
        TRH-2010 · %1,65 İskonto &nbsp;|&nbsp;
        v1.1 — Bu rapor yargısal bilirkişi raporu niteliği taşımaz.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
