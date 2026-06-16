import streamlit as st

# Global Sayfa Ayarı
st.set_page_config(
    page_title="Av. Mahmut NAKİR - Hukuk Otomasyon Sistemi",
    page_icon="⚖️",
    layout="wide"
)

# Global Şifre Kontrolü (Giriş Şifresi: 771044)
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

if not st.session_state.giris_yapildi:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    
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

# Giriş Başarılıysa Gösterilecek Ortak Dashboard Başlığı
st.markdown("<h1 style='text-align: center; color: #1E3A8A;'>⚖️ Av. Mahmut NAKİR</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center; color: #555555;'>Hukuk Otomasyon ve Bilgi Bankası Platformu</h3>", unsafe_allow_html=True)
st.markdown("---")

st.info("👋 Platformumuza Hoş Geldiniz! Kullanmak istediğiniz araca sol taraftaki menüyü kullanarak bağımsız sayfalar halinde erişebilirsiniz.")
