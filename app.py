 layout="wide"
)

# 🎨 TAZMİNAT ROBOTU İMZA TASARIMI VE KUSURSUZ OKUNABİLİRLİK GÜNCELLEMESİ
# 🎨 TAZMİNAT ROBOTU İMZA TASARIMI VE ARINDIRILMIŞ RENK AYARLARI
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Serif:ital,wght@0,400;0,600;1,400&family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@300;400;500;600&display=swap');
@@ -18,7 +18,7 @@
    [data-testid="stSidebar"] label{color:#C9A84C!important;font-size:0.73rem!important;font-weight:600!important;letter-spacing:.08em!important;text-transform:uppercase!important;}
    
    /* 🏛️ ORİJİNAL ROBOT BAŞLIK (RH) ŞABLONU */
    .rh{background:#1A1A2E !important;color:#F7F6F1 !important;padding:1.8rem 2.5rem 1.4rem;border-radius:8px;margin-bottom:1.2rem;border-left:6px solid #C9A84C;font-family:'IBM Plex Serif',serif;}
    .rh{background:#1A1A2E !important;padding:1.8rem 2.5rem 1.4rem;border-radius:8px;margin-bottom:1.2rem;border-left:6px solid #C9A84C;font-family:'IBM Plex Serif',serif;}
    
    .sec{font-family:'IBM Plex Serif',serif;font-size:.95rem;font-weight:600;color:#1A1A2E;border-bottom:2px solid #C9A84C;padding-bottom:.35rem;margin:1.4rem 0 .8rem;}
    .card{background:#fff;border:1px solid #DDD9CE;border-radius:6px;padding:1rem 1.4rem;margin:.4rem 0;border-left:4px solid #C9A84C;}
@@ -71,10 +71,7 @@
    
    .foot{font-size:.7rem;color:#999;font-style:italic;margin-top:1.8rem;padding-top:.9rem;border-top:1px solid #DDD;font-family:'IBM Plex Serif',serif;}
    
    /* GİRİŞ EKRANI OKUNABİLİRLİK AYARLARI */
    h3, label, p, span {
        color: #1A1A2E; 
    }
    /* GİRİŞ EKRANI GİRDİ ALANI NETLEŞTİRME */
    .stTextInput input {
        color: #1A1A2E !important;
        background-color: #FFFFFF !important;
@@ -91,8 +88,9 @@
    col1, col2, col3 = st.columns([1, 1.8, 1])

    with col2:
        st.error("🔒 BU ALANA ERİŞİM KISITLANMIŞTIR")
        st.subheader("Sisteme Giriş Yapın")
        # Başlık çakışmalarını engellemek için satır içi p etiketleri kullanıldı
        st.markdown('<p style="color: #C62828; font-weight: bold; margin-bottom: 10px;">🔒 BU ALANA ERİŞİM KISITLANMIŞTIR</p>', unsafe_allow_html=True)
        st.markdown('<p style="color: #1A1A2E; font-size: 1.3rem; font-weight: 600; margin-bottom: 5px;">Sisteme Giriş Yapın</p>', unsafe_allow_html=True)

        with st.form("giris_formu", clear_on_submit=False):
            sifre = st.text_input("Giriş Şifresi:", type="password")
@@ -107,18 +105,18 @@
    st.stop()


# ─── KURUMSAL BAŞLIK EKRANI (DOĞRUDAN SATIR İÇİ RENK SABİTLEME YAPILDI) ───
# ─── KURUMSAL BAŞLIK EKRANI (MÜDAHALE EDİLEMEZ PARAGRAF TASARIMI) ───
st.markdown("""
    <div class="rh">
        <h1 style="color: #F7F6F1 !important; font-size: 1.5rem; font-weight: 600; margin: 0 0 .3rem;">Av. Mahmut NAKİR</h1>
        <div class="sub" style="color: #C9A84C !important; font-size: .75rem; letter-spacing: .12em; text-transform: uppercase; font-family: 'IBM Plex Mono',monospace;">Hukuk Otomasyon ve Bilgi Bankası Platformu</div>
        <p style="color: #F7F6F1 !important; font-size: 1.5rem; font-weight: 600; margin: 0 0 .3rem 0; padding: 0; font-family: 'IBM Plex Serif', serif;">Av. Mahmut NAKİR</p>
        <p style="color: #C9A84C !important; font-size: .75rem; margin: 0; padding: 0; letter-spacing: .12em; text-transform: uppercase; font-family: 'IBM Plex Mono', monospace;">Hukuk Otomasyon ve Bilgi Bankası Platformu</p>
    </div>
""", unsafe_allow_html=True)

# İki Satır Boşluklu Terazi Emojili Karşılama Alanı
st.markdown("""
    <div class="warn" style="font-size: 1rem; padding: 1.5rem; background: #fff; border-left-color: #C9A84C; color: #1A1A2E;">
        <span style="color: #1A1A2E !important;">⚖️ Av. Mahmut NAKİR'in Platformuna Hoş Geldiniz</span><br><br><br>
        <span style="color: #1A1A2E !important;">Kullanmak istediğiniz araca sol taraftaki menüyü kullanarak bağımsız sayfalar halinde erişebilirsiniz.</span>
    <div class="warn" style="font-size: 1rem; padding: 1.5rem; background: #fff; border-left-color: #C9A84C;">
        <p style="color: #1A1A2E !important; margin: 0 0 25px 0; padding: 0;">⚖️ Av. Mahmut NAKİR'in Platformuna Hoş Geldiniz</p>
        <p style="color: #1A1A2E !important; margin: 0; padding: 0;">Kullanmak istediğiniz araca sol taraftaki menüyü kullanarak bağımsız sayfalar halinde erişebilirsiniz.</p>
    </div>
""", unsafe_allow_html=True)
