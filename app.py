import streamlit as st

# Global Sayfa Ayarı
st.set_page_config(
    page_title="Av. Mahmut NAKİR - Hukuk Otomasyon Sistemi",
    page_icon="⚖️",
    layout="wide"
)

# 🎨 TAZMİNAT ROBOTU İMZA TASARIMI (CSS MAKYAJI)
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
    
    /* Ana sayfa başlıkları için ek asil uyarlama */
    .custom-main-header {
        background: #1A1A2E;
        color: #F7F6F1;
        padding: 2.5rem;
        border-radius: 8px;
        text-align: center;
        border-bottom: 4px solid #C9A84C;
        font-family: 'IBM Plex Serif', serif;
        margin-bottom: 2rem;
    }
    .custom-main-header h1 {
        font-size: 2.5rem;
        font-weight: 600;
        margin: 0;
        color: #F7F6F1;
    }
    .custom-main-header p {
        font-size: 0.9rem;
        color: #C9A84C;
        margin-top: 0.5rem;
        letter-spacing: 0.15em;
        text-transform: uppercase;
        font-family: 'IBM Plex Mono', monospace;
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
st.markdown("""
    <div class="custom-main-header">
        <h1>Av. Mahmut NAKİR</h1>
        <p>Hukuk Otomasyon ve Bilgi Bankası Platformu</p>
    </div>
""", unsafe_allow_html=True)

# İki Satır Boşluklu Terazi Emojili Karşılama Alanı (Sizin Tasarımınızdaki Bilgi Kutusu Yapısıyla)
st.markdown("""
    <div class="warn" style="font-size: 1rem; padding: 1.5rem; background: #fff; border-left-color: #C9A84C; color: #1A1A2E;">
        ⚖️ Av. Mahmut NAKİR'in Platformuna Hoş Geldiniz<br><br><br>
        Kullanmak istediğiniz araca sol taraftaki menüyü kullanarak bağımsız sayfalar halinde erişebilirsiniz.
    </div>
""", unsafe_allow_html=True)
