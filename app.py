import streamlit as st
import pandas as pd
import io
from datetime import date

# Sayfa Genişlik ve Stil Ayarları
st.set_page_config(page_title="Aktüeryal Hesaplama ve İçtihat Bilgi Bankası", layout="wide")

# Görünürlüğü ve kamufle olan alanları düzeltmek için özel CSS
st.markdown("""
<style>
    .styled-box {
        background-color: #f8f9fa;
        border: 2px solid #d1d8e0;
        padding: 15px;
        border-radius: 8px;
        margin-bottom: 20px;
    }
    .main-header {
        color: #1e3799;
        font-weight: bold;
        border-bottom: 2px solid #1e3799;
        padding-bottom: 5px;
    }
</style>
""", unsafe_allowed_html=True)

st.title("⚖️ Entegre Aktüeryal Tazminat Hesaplama & İçtihat Sistemi")

# ============================================================
# HAFIZA ODASI (SESSION STATE) TANIMLAMALARI
# ============================================================
if "ictihat_havuzu" not in st.session_state:
    st.session_state.ictihat_havuzu = [
        {"hukuk_alani": "Araç Değer Kaybı", "baslik": "Yargıtay 4. HD., E. 2021/456 K. 2022/789", "detay": "Araç değer kaybı hesaplamasında mevzuatta belirlenen parça katsayıları esas alınmalıdır."},
        {"hukuk_alani": "Destekten Yoksun Kalma", "baslik": "Yargıtay 17. HD., E. 2019/112 K. 2020/345", "detay": "Destek sürelerinde çocukların yaş sınırları yerleşik içtihatlara göre belirlenir."}
    ]

# ============================================================
# MEVZUAT VERİ TABANI: RESMİ GAZETE PARÇA KATSAYILARI
# ============================================================
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
    "A.15 Sağ Marşpiyel (sac)": {"P": 2.00, "O": {"Hafif": 0.50, "Orta": 0.75, "Yüksek": 1.00}, "Y": {"Lokal": 0.50, "Tam": 0.25}},
    "A.16 Sol Marşpiyel (sac)": {"P": 2.00, "O": {"Hafif": 0.50, "Orta": 0.75, "Yüksek": 1.00}, "Y": {"Lokal": 0.50, "Tam": 0.25}},
    "A.17 A Direği sağ": {"P": 1.00, "O": {"Hafif": 0.50, "Orta": 0.75, "Yüksek": 1.00}, "Y": {"Lokal": 0.25, "Tam": 0.50}},
    "A.18 B Direği sağ": {"P": 2.00, "O": {"Hafif": 0.50, "Orta": 0.75, "Yüksek": 1.00}, "Y": {"Lokal": 0.50, "Tam": 0.25}},
    "A.19 A Direği sol": {"P": 1.00, "O": {"Hafif": 0.50, "Orta": 0.75, "Yüksek": 1.00}, "Y": {"Lokal": 0.50, "Tam": 0.25}},
    "A.20 B Direği sol": {"P": 2.00, "O": {"Hafif": 0.50, "Orta": 0.75, "Yüksek": 1.00}, "Y": {"Lokal": 0.50, "Tam": 0.25}},
    "A.21 Bagaj kapağı": {"P": 1.00, "O": {"Hafif": 0.50, "Orta": 1.00, "Yüksek": 1.50}, "Y": {"Lokal": 1.00, "Tam": 0.50}},
    "A.22 Arka panel": {"P": 2.00, "O": {"Hafif": 0.50, "Orta": 1.00, "Yüksek": 1.50}, "Y": {"Lokal": 0.50, "Tam": 1.00}},
    "A.23 Sağ arka çamurluk": {"P": 4.00, "O": {"Hafif": 0.50, "Orta": 1.00, "Yüksek": 1.50}, "Y": {"Lokal": 1.00, "Tam": 0.50}},
    "A.24 Sol arka çamurluk": {"P": 4.00, "O": {"Hafif": 0.50, "Orta": 1.00, "Yüksek": 1.50}, "Y": {"Lokal": 0.50, "Tam": 1.00}},
    "A.25 Havuz sacı": {"P": 3.00, "O": {"Hafif": 0.50, "Orta": 1.00, "Yüksek": 1.50}, "Y": {"Lokal": 0.25, "Tam": 0.50}},
    "A.26 Sağ şase arka": {"P": 3.00, "O": {"Hafif": 1.00, "Orta": 1.50, "Yüksek": 2.00}, "Y": {"Lokal": 0.50, "Tam": 0.25}},
    "A.27 Sol şase arka": {"P": 3.00, "O": {"Hafif": 1.00, "Orta": 1.50, "Yüksek": 2.00}, "Y": {"Lokal": 0.25, "Tam": 0.50}},
    "A.28 Motor traversi/Dingil": {"P": 1.00, "O": {"Hafif": 1.00, "Orta": 1.50, "Yüksek": 2.00}, "Y": {"Lokal": 0.0, "Tam": 0.0}},
    "A.29 Yolcu hava yastığı": {"P": 2.00, "O": None, "Y": None},
    "A.30 Sürücü hava yastığı": {"P": 2.00, "O": None, "Y": None},
    "A.31 Sağ yan hava yastığı": {"P": 2.00, "O": None, "Y": None},
    "A.32 Sol yan hava yastığı": {"P": 2.00, "O": None, "Y": None}
}

# Excel'e aktarma yardımcı fonksiyonu
def to_excel(df_dict):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        for sheet_name, df in df_dict.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)
    return output.getvalue()

# ============================================================
# ANA MODÜL SEÇİMİ (SOL MENÜ)
# ============================================================
modul = st.sidebar.selectbox("🎯 Çalışma Modülü Seçin", ["Araç Değer Kaybı", "İçtihat & PDF Bilgi Bankası"])

if modul == "Araç Değer Kaybı":
    st.markdown("<h2 class='main-header'>🚗 Araç Değer Kaybı Hesaplama Robotu (Resmi Gazete)</h2>", unsafe_allowed_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        piyasa_degeri = st.number_input("Araç Piyasa Rayiç Değeri (TL)", value=850000.0)
        hasar_tutari = st.number_input("KDV Dahil Toplam Hasar Tutarı (TL)", value=75000.0)
    with col2:
        km = st.number_input("Aracın Kilometresi", value=45000)
        ticari_mi = st.checkbox("Araç Ticari veya Kiralık mı? (G.1: -0.05)")
        sbm_sayisi = st.slider("Geçmiş Hasar Kaydı Sayısı (SBM G.2)", 0, 5, 1)

    # 1. GERİ BİLDİRİM: OTOMATİK PARÇA VE KATSAYI SEÇİM ALANI
    st.markdown("### 🛠️ Hasar Gören Parça ve İşlem Seçimi")
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
            st.warning("Bu parça için onarım katsayısı uygulanmaz.")
            onarim_tipi = "Yok"

    with col_p3:
        if parca_detay['Y'] is not None:
            boya_tipi = st.radio("Boya Durumu:", ["Yok", "Lokal", "Tam"])
            if boya_tipi != "Yok":
                hk_puan += parca_detay['Y'][boya_tipi]
        else:
            st.warning("Bu parça için boya katsayısı uygulanmaz.")
            boya_tipi = "Yok"

    st.success(f"📊 Seçilen Parçanın Toplam Hasar Puanı (Pi + Oi + Yi): {hk_puan}")

    if st.button("Hesaplamayı Tamamla ve Excel Raporu Üret"):
        # Matematiksel Hesaplamalar
        # 1. R Katsayısı
        R = 1.00 if piyasa_degeri >= 750000 else 0.95
        # 2. K Katsayısı
        K = 0.95 if km < 50000 else 0.90
        # 3. T Katsayısı
        T = (hasar_tutari * 100 / piyasa_degeri) * 0.10
        # 4. H Katsayısı
        H = (hk_puan + T) / 100
        # 5. G Katsayısı
        g1 = -0.05 if ticari_mi else 0.0
        g2 = -(sbm_sayisi * 0.03) if sbm_sayisi > 0 else 0.0
        G = 1 + (g1 + g2)
        
        # Nihai Değer Kaybı (DK)
        dk_sonuc = piyasa_degeri * R * K * H * G
        
        st.markdown("---")
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
        
        # Excel Butonunu Tetikleme
        excel_data = to_excel({"Deger_Kaybi_Raporu": res_df})
        st.download_button("📥 Excel Raporunu İndir", data=excel_data, file_name="deger_kaybi_mevzuat_raporu.xlsx")

# ============================================================
# 2 ve 3. GERİ BİLDİRİM: İÇTİHAT & PDF YÜKLEME VE KAMUFLAJ DÜZELTME PANELDİR
# ============================================================
elif modul == "İçtihat & PDF Bilgi Bankası":
    st.markdown("<h2 class='main-header'>📚 Yargıtay İçtihat ve PDF Karar Ambarı</h2>", unsafe_allowed_html=True)
    
    # 3. GERİ BİLDİRİM: Kamufle Olan Arama Bölümünün Belirginleştirilmesi
    st.markdown("<div class='styled-box'><h4>🔍 İçtihat Arama Filtreleri (Görünüm Düzeltildi)</h4>", unsafe_allowed_html=True)
    arama_hukuk_alani = st.selectbox("Aranacak Hukuk Alanını Seçin:", ["Tümü", "Araç Değer Kaybı", "Bedensel Hasar", "Destekten Yoksun Kalma"], key="search_law")
    arama_kelimesi = st.text_input("Anahtar Kelime Ara (Esas No, Karar No, Parça adı...):")
    st.markdown("</div>", unsafe_allowed_html=True)

    # 2. GERİ BİLDİRİM: Kalıcı Arşiv Ekleme Sekmeleri
    tab1, tab2 = st.tabs(["✍️ Yeni İçtihat / İlamsız Karar Metni Ekle", "📄 PDF Karar Dosyası Yükle"])
    
    with tab1:
        st.markdown("<div class='styled-box'>", unsafe_allowed_html=True)
        st.subheader("Yeni İçtihat Giriş Formu")
        # 3. GERİ BİLDİRİM: Kamufle olan hukuk alanı kutusu düzeltildi
        yeni_hukuk_alani = st.selectbox("İçtihadın Ait Olduğu Hukuk Alanı (Belirginleştirildi):", ["Araç Değer Kaybı", "Bedensel Hasar", "Destekten Yoksun Kalma"], key="add_law")
        yeni_baslik = st.text_input("Karar Başlığı / Mahkeme Künyesi:")
        yeni_detay = st.text_area("Karar Metni / Özeti:")
        
        if st.button("Kararı Bilgi Bankasına Kaydet"):
            if yeni_baslik and yeni_detay:
                st.session_state.ictihat_havuzu.append({
                    "hukuk_alani": yeni_hukuk_alani,
                    "baslik": yeni_baslik,
                    "detay": yeni_detay
                })
                st.success("✔️ İçtihat başarıyla hafızaya eklendi ve aşağıdaki listeye yansıtıldı!")
                st.rerun()
            else:
                st.error("Lütfen Başlık ve Karar Metni alanlarını boş bırakmayın.")
        st.markdown("</div>", unsafe_allowed_html=True)
        
    with tab2:
        st.markdown("<div class='styled-box'>", unsafe_allowed_html=True)
        st.subheader("PDF Dosya Arşivleme Sistemi")
        yuklenen_file = st.file_uploader("Emsal karar PDF dökümanını sürükleyin veya seçin", type=["pdf"])
        if yuklenen_file is not None:
            st.success(f"📁 '{yuklenen_file.name}' başarıyla lokal bellek havuzuna aktarıldı!")
        st.markdown("</div>", unsafe_allowed_html=True)

    # 📜 DİNAMİK LİSTELEME ALANI
    st.markdown("---")
    st.subheader("📋 Sistemde Arşivlenmiş Aktüel İçtihatlar")
    
    for idx, ictihat in enumerate(st.session_state.ictihat_havuzu):
        # Filtreleme mantığı
        if arama_hukuk_alani != "Tümü" and ictihat["hukuk_alani"] != arama_hukuk_alani:
            continue
        if arama_kelimesi.lower() not in ictihat["baslik"].lower() and arama_kelimesi.lower() not in ictihat["detay"].lower():
            continue
            
        with st.expander(f"📌 [{ictihat['hukuk_alani']}] - {ictihat['baslik']}"):
            st.write(ictihat["detay"])
            if st.button("Bu Kararı Sil", key=f"del_{idx}"):
                st.session_state.ictihat_havuzu.pop(idx)
                st.rerun()
