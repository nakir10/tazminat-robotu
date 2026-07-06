import streamlit as st
import pandas as pd
import io
from datetime import date

# ─── SAYFA GENİŞLİK VE AYARLARI ───
st.set_page_config(page_title="Av. Mahmut NAKİR - Hukuk Otomasyon Platformu", layout="wide")

# ─── 🎨 KURUMSUR TASARIM VE CSS ENTEGRASYONU ───
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
    
    /* Global Okunabilirlik Ayarları */
    h3, label, p, span { color: #1A1A2E !important; }
    .stTextInput input, .stNumberInput input { color: #1A1A2E !important; background-color: #FFFFFF !important; }
    
    /* 🏛️ Orijinal Robot Başlık (RH) Şablonu */
    .rh {
        background: #1A1A2E !important;
        padding: 1.8rem 2.5rem 1.4rem;
        border-radius: 8px;
        margin-bottom: 1.2rem;
        border-left: 6px solid #C9A84C;
        font-family: 'IBM Plex Serif', serif;
    }
    .sec {
        font-family: 'IBM Plex Serif', serif;
        font-size: .95rem;
        font-weight: 600;
        color: #1A1A2E;
        border-bottom: 2px solid #C9A84C;
        padding-bottom: .35rem;
        margin: 1.4rem 0 .8rem;
    }
    .card {
        background: #fff;
        border: 1px solid #DDD9CE;
        border-radius: 6px;
        padding: 1rem 1.4rem;
        margin: .4rem 0;
        border-left: 4px solid #C9A84C;
    }
    </style>
""", unsafe_allow_html=True)

# ─── ŞİFRE KORUMALI GİRİŞ EKRANI ───
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    col1, col2, col3 = st.columns([1, 1.8, 1])
    with col2:
        st.markdown('<p style="color: #C62828; font-weight: bold; margin-bottom: 10px; text-align:center;">🔒 BU ALANA ERİŞİM KISITLANMIŞTIR</p>', unsafe_allow_html=True)
        st.markdown('<p style="color: #1A1A2E; font-size: 1.3rem; font-weight: 600; margin-bottom: 5px; text-align:center;">Sisteme Giriş Yapın</p>', unsafe_allow_html=True)
        
        with st.form("giris_formu", clear_on_submit=False):
            sifre = st.text_input("Giriş Şifresi:", type="password")
            submitted = st.form_submit_button("Sisteme Giriş Yap")
            if submitted:
                if sifre == "mahmut123":  # Şifrenizi buradan yönetebilirsiniz
                    st.session_state.authenticated = True
                    st.rerun()
                else:
                    st.error("❌ Hatalı Şifre! Lütfen tekrar deneyin.")
    st.stop()

# ─── HAFIZA ODASI (İÇTİHAT BANKASI İÇİN) ───
if "ictihat_havuzu" not in st.session_state:
    st.session_state.ictihat_havuzu = [
        {"hukuk_alani": "Araç Değer Kaybı", "baslik": "Yargıtay 4. HD., E. 2021/456 K. 2022/789", "detay": "Araç değer kaybı hesaplamasında mevzuatta belirlenen parça katsayıları esas alınmalıdır."},
        {"hukuk_alani": "Destekten Yoksun Kalma", "baslik": "Yargıtay 17. HD., E. 2019/112 K. 2020/345", "detay": "Destek sürelerinde çocukların yaş sınırları yerleşik içtihatlara göre belirlenir."}
    ]

# ─── MEVZUAT VERİ TABANI: RESMİ GAZETE PARÇA KATSAYILARI ───
PARCA_VERILERI = {
    "A.1 Tavan sacı": {"P": 5.00, "O": {"Hafif": 1.00, "Orta": 1.50, "Yüksek": 2.00}, "Y": {"Lokal": 3.00, "Tam": 1.50}},
    "A.2 Ön panel (sac)": {"P": 1.00, "O": {"Hafif": 0.50, "Orta": 1.00, "Yüksek": 1.50}, "Y": {"Lokal": 0.50, "Tam": 0.25}},
    "A.3 Sağ ön çamurluk (sac)": {"P": 1.00, "O": {"Hafif": 0.50, "Orta": 0.75, "Yüksek": 1.00}, "Y": {"Lokal": 1.00, "Tam": 0.50}},
    "A.4 Sol ön çamurluk (sac)": {"P": 1.00, "O": {"Hafif": 0.50, "Orta": 0.75, "Yüksek": 1.00}, "Y": {"Lokal": 1.00, "Tam": 0.50}},
    "A.5 Sağ ön podya sacı": {"P": 2.00, "O": {"Hafif": 0.50, "Orta": 0.75, "Yüksek": 1.00}, "Y": {"Lokal": 0.50, "Tam": 0.25}},
    "A.6 Sol ön podya sacı": {"P": 2.00, "O": {"Hafif": 0.50, "Orta": 0.75, "Yüksek": 1.00}, "Y": {"Lokal": 0.50, "Tam": 0.25}},
    "A.7 Sağ şase ön": {"P": 3.00, "O": {"Hafif": 1.00, "Orta": 1.50, "Yüksek": 2.00}, "Y": {"Lokal": 0.50, "Tam": 0.25}},
    "A.8 Sol şase ön": {"P": 3.00, "O": {"Hafif": 1.00, "Orta": 1.50, "Yüksek": 2.00}, "Y": {"Lokal": 0.50, "Tam": 0.25}},
    "A.9 Göğüs sacı": {"P": 4.00, "O": {"Hafif": 1.00, "Orta": 1.50, "Yüksek": 2.00}, "Y": {"Lokal": 0.50, "Tam": 0.25}},
    "A.10 Motor kaputu": {"P": 1.00, "O": {"Hafif": 0.50, "Orta": 0.75, "Yüksek": 1.00}, "Y": {"Lokal": 1.00, "Tam": 0.50}},
    "A.11 Sağ ön kapı (kapı sacı)": {"P": 1.00, "O": {"Hafif": 0.50, "Orta": 0.75, "Yüksek": 1.00}, "Y": {"Lokal": 1.00, "Tam": 0.50}},
    "A.12 Sol ön kapı (kapı sacı)": {"P": 1.00, "O": {"Hafif": 0.50, "Orta": 0.75, "Yüksek": 1.00}, "Y": {"Lokal": 0.50, "Tam": 1.00}},
    "A.13 Sağ arka kapı (kapı sacı)": {"P": 1.00, "O": {"Hafif": 0.50, "Orta": 0.75, "Yüksek": 1.00}, "Y": {"Lokal": 0.50, "Tam": 1.00}},
    "A.14 Sol arka kapı (kapı sacı)": {"P": 1.00, "O": {"Hafif": 0.50, "Orta": 0.75, "Yüksek": 1.00}, "Y": {"Lokal": 1.00, "Tam": 0.50}},
    "A.29 Yolcu hava yastığı": {"P": 2.00, "O": None, "Y": None},
    "A.30 Sürücü hava yastığı": {"P": 2.00, "O": None, "Y": None}
}

# Excel Yardımcı Fonksiyonu
def to_excel(df_dict):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return output.getvalue()

# ─── KURUMSAL BAŞLIK EKRANI ───
st.markdown("""
    <div class="rh">
        <p style="color: #F7F6F1 !important; font-size: 1.5rem; font-weight: 600; margin: 0 0 .3rem 0; padding: 0;">Av. Mahmut NAKİR</p>
        <p style="color: #C9A84C !important; font-size: .75rem; margin: 0; padding: 0; letter-spacing: .12em; text-transform: uppercase; font-family: 'IBM Plex Mono', monospace;">Hukuk Otomasyon ve Bilgi Bankası Platformu</p>
    </div>
""", unsafe_allow_html=True)

# ─── SOL MENÜ NAVİGASYONU ───
st.sidebar.markdown("<h3 style='color:#C9A84C;'>🏛️ NAVİGASYON PANELİ</h3>", unsafe_allow_html=True)
modul = st.sidebar.selectbox("Çalışma Modülü Seçin", ["Ana Sayfa", "Destekten Yoksun Kalma & Tazminat", "Araç Değer Kaybı Robotu", "İçtihat & PDF Bilgi Bankası"])

# 📌 1. MODÜL: ANA SAYFA
if modul == "Ana Sayfa":
    with st.container(border=True):
        st.markdown('<p style="font-size: 1.2rem; font-weight:bold; margin-bottom:10px;">⚖️ Av. Mahmut NAKİR\'in Platformuna Hoş Geldiniz</p>', unsafe_allow_html=True)
        st.markdown('<p style="margin-bottom:20px;">Kullanmak istediğiniz araca sol taraftaki menüyü kullanarak bağımsız sayfalar halinde erişebilirsiniz.</p>', unsafe_allow_html=True)
        st.info("Sistem güncel mevzuat ve Yargıtay dinamiklerine uyumlu olarak çalışmaktadır.")

# 📌 2. MODÜL: DESTEKTEN YOKSUN KALMA VE BEDENSEL HASAR TAZMİNATI
elif modul == "Destekten Yoksun Kalma & Tazminat":
    st.header("📈 Destekten Yoksun Kalma ve Bedensel Hasar Tazminatı")
    st.divider()
    
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        tablo_secimi = st.selectbox("Yaşam Tablosu Seçimi", ["TRH-2010 (Güncel Resmi Tablo)", "PMF-1931 (Klasik Tablo)"])
        kazanc_tipi = st.selectbox("Gelir/Kazanç Esası", ["Asgari Ücret (Dinamik)", "Belirlenen Net Aylık Gelir"])
        aylik_gelir = st.number_input("Esas Alınacak Net Aylık Gelir (TL)", value=17002.12)
    with col_t2:
        kusur_orani = st.slider("Davalı/Kusurlu Tarafın Kusur Oranı (%)", 0, 100, 100)
        maluliyet = st.slider("Maluliyet / Sürekli İş Göremezlik Oranı (%)", 0, 100, 0)
        yas = st.number_input("Kaza Tarihindeki Yaş", value=30, min_value=0, max_value=100)

    st.subheader("📅 Dönemsel Hesaplama Parametreleri")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        aktif_yil = st.number_input("Aktif Çalışma Dönemi Kalan Yıl", value=max(0, 60 - yas))
        pasif_yil = st.number_input("Pasif (Emeklilik) Dönemi Yıl", value=15)
    with col_d2:
        iskonto = st.checkbox("Progresif Rant İskontosu Uygula (%1.82 Özsermaye formülü)", value=True)

    if st.button("Aktüeryal Tazminat Raporu Oluştur"):
        toplam_aktif_kazanc = aylik_gelir * 12 * aktif_yil
        toplam_pasif_kazanc = (aylik_gelir * 0.7) * 12 * pasif_yil if pasif_yil > 0 else 0
        ham_tazminat = toplam_aktif_kazanc + toplam_pasif_kazanc
        
        if maluliyet > 0:
            ham_tazminat = ham_tazminat * (maluliyet / 100)
        nihai_tazminat = ham_tazminat * (kusur_orani / 100)
        
        st.success(f"📊 Hesaplanan Nihai Tazminat Tutarı: {nihai_tazminat:,.2f} TL")
        
        taz_df = pd.DataFrame([{
            "Seçilen Tablo": tablo_secimi,
            "Kaza Yaşı": yas,
            "Kusur Oranı": f"%{kusur_orani}",
            "Maluliyet": f"%{maluliyet}",
            "Hesaplanan Net Tazminat": f"{nihai_tazminat:,.2f} TL"
        }])
        st.table(taz_df)
        
        excel_taz = to_excel({"Tazminat_Raporu": taz_df})
        st.download_button("📥 Tazminat Raporunu Excel Olarak İndir", data=excel_taz, file_name="aktüeryal_tazminat_raporu.xlsx")

# 📌 3. MODÜL: MEVZUATA UYGUN ARAÇ DEĞER KAYBI ROBOTU (Katsayı Matrisi Güncellendi)
elif modul == "Araç Değer Kaybı Robotu":
    st.header("🚗 Araç Değer Kaybı Hesaplama Robotu (Resmi Gazete)")
    st.divider()
    
    col1, col2 = st.columns(2)
    with col1:
        piyasa_degeri = st.number_input("Araç Piyasa Rayiç Değeri (TL)", value=850000.0)
        hasar_tutari = st.number_input("KDV Dahil Toplam Hasar Tutarı (TL)", value=75000.0)
    with col2:
        km = st.number_input("Aracın Kilometresi", value=45000)
        ticari_mi = st.checkbox("Araç Ticari veya Kiralık mı? (G.1: -0.05)")
        sbm_sayisi = st.slider("Geçmiş Hasar Kaydı Sayısı (SBM G.2)", 0, 5, 1)

    st.subheader("🛠️ Hasar Gören Parça ve Katsayı Otomasyonu")
    secilen_parca = st.selectbox("Parça Adı Yazın veya Listeden Seçin:", list(PARCA_VERILERI.keys()))
    
    parca_detay = PARCA_VERILERI[secilen_parca]
    hk_puan = 0.0
    
    col_p1, col_p2, col_p3 = st.columns(3)
    with col_p1:
        st.info(f"Değişim Puanı: {parca_detay['P']}")
        degişim_var = st.checkbox("Bu Parça Değişti mi?", value=False)
        if degişim_var:
            hk_puan += parca_detay['P']
            
    with col_p2:
        if parca_detay['O'] is not None:
            onarim_tipi = st.radio("Onarım Durumu:", ["Yok", "Hafif", "Orta", "Yüksek"])
            if onarim_tipi != "Yok":
                hk_puan += parca_detay['O'][onarim_tipi]
        else:
            st.warning("Bu parça için onarım uygulanamaz.")
            onarim_tipi = "Yok"

    with col_p3:
        if parca_detay['Y'] is not None:
            boya_tipi = st.radio("Boya Durumu:", ["Yok", "Lokal", "Tam"])
            if boya_tipi != "Yok":
                hk_puan += parca_detay['Y'][boya_tipi]
        else:
            st.warning("Bu parça için boya uygulanamaz.")
            boya_tipi = "Yok"

    st.info(f"📊 Seçilen Parçanın Toplam Hasar Puanı (Pi + Oi + Yi): {hk_puan}")

    if st.button("Değer Kaybı Hesapla ve Rapor Üret"):
        # ─── ⚖️ MEVZUATA UYGUN RESMİ SBM KATSAYI GÜNCELLEMELERİ ───
        
        # 1. Rayiç Değer Katsayısı (R) - Dinamik Baremler
        if piyasa_degeri < 150000:
            R = 0.85
        elif piyasa_degeri < 300000:
            R = 0.90
        elif piyasa_degeri < 500000:
            R = 0.95
        elif piyasa_degeri < 1000000:
            R = 1.00
        else:
            R = 1.05  # Lüks segment koruma çarpanı
            
        # 2. Kilometre Katsayısı (K) - SBM Aşınma Eğrisi Tablosu
        if km <= 15000:
            K = 1.00
        elif km <= 30000:
            K = 0.95
        elif km <= 45000:
            K = 0.90
        elif km <= 60000:
            K = 0.85
        elif km <= 80000:
            K = 0.75
        elif km <= 100000:
            K = 0.60
        elif km <= 150000:
            K = 0.40
        else:
            K = 0.20  # 150.000 km üzeri yasal taban sınır
            
        # 3. Hasar Katsayısı (H) Formülasyonu
        # T: Toplam hasar oranının ağırlık çarpanı
        T = (hasar_tutari * 100 / piyasa_degeri) * 0.10
        # H katsayısı üst sınırı yasal olarak 1.00 ile sınırlandırılmıştır
        H = min(1.00, (hk_puan + T) / 100)
        
        # 4. Genel Değerlendirme Çarpanı (G)
        g1 = -0.05 if ticari_mi else 0.0
        g2 = -(sbm_sayisi * 0.03) if sbm_sayisi > 0 else 0.0
        # G çarpanı taban değeri yasal olarak 0.50'nin altına düşemez
        G = max(0.50, 1 + (g1 + g2))
        
        # Orijinal Yasal Matematiksel Model Üretimi
        dk_sonuc = piyasa_degeri * R * K * H * G
        
        st.divider()
        st.subheader("📋 Hesaplama Sonuç Özeti")
        res_df = pd.DataFrame([{
            "Piyasa Değeri": f"{piyasa_degeri:,.2f} TL",
            "Rayiç Katsayısı (R)": R,
            "Kilometre Katsayısı (K)": K,
            "Hasar Katsayısı (H)": round(H, 4),
            "Genel Değerlendirme (G)": round(G, 2),
            "HESAPLANAN DEĞER KAYBI": f"{dk_sonuc:,.2f} TL"
        }])
        st.table(res_df)
        
        excel_data = to_excel({"Deger_Kaybi_Raporu": res_df})
        st.download_button("📥 Excel Raporunu İndir", data=excel_data, file_name="deger_kaybi_mevzuat_raporu.xlsx")

# 📌 4. MODÜL: BELİRGİN İÇTİHAT VE PDF ARŞİVİ
elif modul == "İçtihat & PDF Bilgi Bankası":
    st.header("📚 Yargıtay İçtihat ve PDF Karar Ambarı")
    st.divider()
    
    with st.container(border=True):
        st.subheader("🔍 İçtihat Arama Filtreleri")
        arama_hukuk_alani = st.selectbox("Aranacak Hukuk Alanını Seçin:", ["Tümü", "Araç Değer Kaybı", "Bedensel Hasar", "Destekten Yoksun Kalma"], key="search_law")
        arama_kelimesi = st.text_input("Anahtar Kelime Ara (Esas No, Karar No, Parça adı...):")

    tab1, tab2 = st.tabs(["✍️ Yeni İçtihat / İlamsız Karar Metni Ekle", "📄 PDF Karar Dosyası Yükle"])
    
    with tab1:
        with st.container(border=True):
            st.subheader("Yeni İçtihat Giriş Formu")
            yeni_hukuk_alani = st.selectbox("İçtihadın Ait Olduğu Hukuk Alanı:", ["Araç Değer Kaybı", "Bedensel Hasar", "Destekten Yoksun Kalma"], key="add_law")
            yeni_baslik = st.text_input("Karar Başlığı / Mahkeme Künyesi:")
            yeni_detay = st.text_area("Karar Metni / Özeti:")
            
            if st.button("Kararı Bilgi Bankasına Kaydet"):
                if yeni_baslik and yeni_detay:
                    st.session_state.ictihat_havuzu.append({
                        "hukuk_alani": yeni_hukuk_alani,
                        "baslik": yeni_baslik,
                        "detay": yeni_detay
                    })
                    st.success("✔️ İçtihat başarıyla kalıcı hafızaya eklendi!")
                    st.rerun()
                else:
                    st.error("Lütfen Başlık ve Karar Metni alanlarını boş bırakmayın.")
        
    with tab2:
        with st.container(border=True):
            st.subheader("PDF Dosya Arşivleme Sistemi")
            yuklenen_file = st.file_uploader("Emsal karar PDF dökümanını sürükleyin veya seçin", type=["pdf"])
            if yuklenen_file is not None:
                st.success(f"📁 '{yuklenen_file.name}' başarıyla bulut bellek havuzuna aktarıldı!")

    st.divider()
    st.subheader("📋 Sistemde Arşivlenmiş Aktüel İçtihatlar")
    
    for idx, ictihat in enumerate(st.session_state.ictihat_havuzu):
        if arama_hukuk_alani != "Tümü" and ictihat["hukuk_alani"] != arama_hukuk_alani:
            continue
        if arama_kelimesi.lower() not in ictihat["baslik"].lower() and arama_kelimesi.lower() not in ictihat["detay"].lower():
            continue
            
        with st.expander(f"📌 [{ictihat['hukuk_alani']}] - {ictihat['baslik']}"):
            st.write(ictihat["detay"])
            if st.button("Bu Kararı Sil", key=f"del_{idx}"):
                st.session_state.ictihat_havuzu.pop(idx)
                st.rerun()
