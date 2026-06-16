import streamlit as st

# Global Sayfa Ayarı
st.set_page_config(
    page_title="Av. Mahmut NAKİR - Hukuk Otomasyon Sistemi",
    page_icon="⚖️",
    layout="wide"
)

# 🎨 PROFESYONEL VE CANLI RENK PALETİ (CSS MAKYAJI)
st.markdown("""
    <style>
        /* 1. Tüm Sayfa Arka Planı ve Yazı Tipi */
        html, body, [data-testid="stAppViewContainer"] {
            font-family: 'Inter', 'Segoe UI', system-ui, sans-serif !important;
            background-color: #F8FAFC !important; /* Okunabilirliği yüksek temiz dijital arka plan */
        }
        
        /* 2. Sol Menü (Sidebar) Kurumsal Tasarımı */
        [data-testid="stSidebar"] {
            background-color: #0F172A !important; /* Ağır ve profesyonel gece mavisi */
        }
        [data-testid="stSidebar"] * {
            color: #F8FAFC !important; /* Sol menü yazıları net beyaz/gri tonu */
        }
        
        /* Active sayfa vurgusu */
        [data-testid="stSidebarNav"] ul li div a span {
            font-weight: 500 !important;
        }
        
        /* 3. Canlı Başlık Stilleri */
        .ana-baslik {
            font-family: 'Georgia', serif;
            color: #0F172A !important; /* Güçlü kurumsal ton */
            font-size: 40px !important;
            font-weight: 800;
            text-align: center;
            margin-top: -10px;
            margin-bottom: 5px;
            letter-spacing: 0.5px;
        }
        
        .alt-baslik {
            color: #D97706 !important; /* Canlı Amber/Altın tonu */
            font-size: 16px !important;
            font-weight: 700;
            text-align: center;
            letter-spacing: 2px;
            margin-bottom: 30px;
        }
        
        /* 4. Canlı ve Profesyonel Butonlar */
        .stButton>button {
            background-color: #2563EB !important; /* Canlı Safir Mavisi */
            color: white !important;
            font-size: 16px !important;
            font-weight: 600 !important;
            border-radius: 8px !important;
            border: none !important;
            padding: 10px 20px !important;
            box-shadow: 0px 4px 6px rgba(37, 99, 235, 0.2); /* Hafif mavi gölge */
            transition: all 0.2s ease-in-out;
        }
        .stButton>button:hover {
            background-color: #1D4ED8 !important; /* Üzerine gelince biraz koyulaşır */
            box-shadow: 0px 6px 12px rgba(37, 99, 235, 0.3);
            transform: translateY(-1px); /* Hafif yukarı kalkma efekti */
        }
        
        /* 5. Maksimum Okunabilirlik İçin Metin Ayarları */
        p, span, label, li {
            font-size: 16px !important; /* Okumayı kolaylaştıran ideal boyut */
            color: #1E293B !important; /* Koyu karbon rengi (Gözü yormaz, çok nettir) */
            line-height: 1.6 !important; /* Satır arası boşluğu düzenler */
        }
        
        /* Bilgi kutuları (st.info vb.) için canlandırma */
        .stAlert {
            background-color: #EFF6FF !important;
            border-left: 5px solid #2563EB !important;
            border-radius: 8px !important;
        }
    </style>
""", unsafe_allow_html=True)


# Global Şifre Kontrolü (Giriş Şifresi: 771044)
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

if not st.session_state.giris_yapildi:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 1.8, 1])
    
    with col2:
        st.error("🔒 BU ALANA ERİŞİM KISITLANMIŞTIR")
        st.subheader("Sisteme Giriş Yapın")
        sifre = st.text_input("Giriş Şifresi:", type="password")
        
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            if sifre == "771044":  
                st.session_state.giris_yapildi = True
                st.rerun()
            else:
                st.error("Girdiğiniz şifre hatalıdır. Lütfen tekrar deneyiniz.")
    st.stop()


# ─── KURUMSAL BAŞLIK EKRANI ───
st.markdown('<div class="ana-baslik">Av. Mahmut NAKİR</div>', unsafe_allow_html=True)
st.markdown('<div class="alt-baslik">HUKUK OTOMASYON VE BİLGİ BANKASI PLATFORMU</div>', unsafe_allow_html=True)
st.markdown("---")

# Yenilenen Karşılama Metni ve İki Satır Boşluklu Yapı
st.info(
    "⚖️ Av. Mahmut NAKİR'in Platformuna Hoş Geldiniz\n\n"
    "\n\n"
    "Kullanmak istediğiniz araca sol taraftaki menüyü kullanarak bağımsız sayfalar halinde erişebilirsiniz."
)
