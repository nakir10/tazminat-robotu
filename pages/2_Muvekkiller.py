import streamlit as st

from veritabani.muvekkiller import (
    muvekkil_ekle,
    muvekkilleri_listele,
    muvekkil_ara,
    muvekkil_getir,
)


st.set_page_config(
    page_title="Müvekkiller",
    page_icon="👤",
    layout="wide",
)


st.title("👤 Müvekkiller")
st.caption("Hukuk ofisi müvekkil yönetimi")


# ---------------------------------------------------------
# YARDIMCI FONKSİYON
# ---------------------------------------------------------

def form_degerlerini_temizle():
    """Yeni müvekkil formundaki alanları temizler."""
    for anahtar in [
        "yeni_ad",
        "yeni_soyad",
        "yeni_tc",
        "yeni_dogum",
        "yeni_cinsiyet",
        "yeni_telefon",
        "yeni_eposta",
        "yeni_adres",
        "yeni_meslek",
        "yeni_ucret",
        "yeni_tahsil",
        "yeni_not",
    ]:
        st.session_state.pop(anahtar, None)


# ---------------------------------------------------------
# ARAMA
# ---------------------------------------------------------

arama = st.text_input(
    "🔎 Müvekkil ara",
    placeholder="Ad, soyad veya telefon yazın...",
)


# ---------------------------------------------------------
# YENİ MÜVEKKİL
# ---------------------------------------------------------

with st.expander("➕ Yeni Müvekkil Ekle", expanded=False):

    with st.form("yeni_muvekkil_formu"):

        col1, col2 = st.columns(2)

        with col1:
            ad = st.text_input(
                "Ad *",
                key="yeni_ad",
            )

            tc = st.text_input(
                "T.C. Kimlik No",
                key="yeni_tc",
            )

            telefon = st.text_input(
                "Telefon",
                key="yeni_telefon",
            )

            adres = st.text_area(
                "Adres",
                key="yeni_adres",
            )

            ucret = st.number_input(
                "Ücret",
                min_value=0.0,
                step=1000.0,
                value=0.0,
                key="yeni_ucret",
            )

        with col2:
            soyad = st.text_input(
                "Soyad *",
                key="yeni_soyad",
            )

            dogum_tarihi = st.date_input(
                "Doğum Tarihi",
                value=None,
                key="yeni_dogum",
            )

            cinsiyet = st.selectbox(
                "Cinsiyet",
                ["", "Kadın", "Erkek"],
                key="yeni_cinsiyet",
            )

            e_posta = st.text_input(
                "E-posta",
                key="yeni_eposta",
            )

            meslek = st.text_input(
                "Meslek",
                key="yeni_meslek",
            )

            tahsil_edilen = st.number_input(
                "Tahsil Edilen",
                min_value=0.0,
                step=1000.0,
                value=0.0,
                key="yeni_tahsil",
            )

        notlar = st.text_area(
            "Müvekkil Notu",
            key="yeni_not",
        )

        kaydet = st.form_submit_button(
            "💾 Müvekkili Kaydet",
            use_container_width=True,
        )

        if kaydet:

            if not ad.strip() or not soyad.strip():
                st.error("Ad ve soyad zorunludur.")

            else:
                yeni_id = muvekkil_ekle(
                    ad=ad,
                    soyad=soyad,
                    tc_kimlik_no=tc or None,
                    dogum_tarihi=(
                        dogum_tarihi.isoformat()
                        if dogum_tarihi
                        else None
                    ),
                    cinsiyet=cinsiyet or None,
                    telefon=telefon or None,
                    e_posta=e_posta or None,
                    adres=adres or None,
                    meslek=meslek or None,
                    ucret=ucret,
                    tahsil_edilen=tahsil_edilen,
                    notlar=notlar or None,
                )

                st.success(
                    f"Müvekkil kaydedildi. ID: {yeni_id}"
                )

                st.rerun()


# ---------------------------------------------------------
# MÜVEKKİL LİSTESİ
# ---------------------------------------------------------

if arama.strip():
    muvekkiller = muvekkil_ara(arama)
else:
    muvekkiller = muvekkilleri_listele()


st.subheader("Müvekkil Listesi")

if not muvekkiller:

    st.info("Henüz kayıtlı müvekkil bulunmuyor.")

else:

    for muvekkil in muvekkiller:

        ad_soyad = (
            f"{muvekkil['ad']} {muvekkil['soyad']}"
        )

        telefon = muvekkil["telefon"] or "-"

        with st.expander(
            f"👤 {ad_soyad} — {telefon}"
        ):

            col1, col2 = st.columns(2)

            with col1:
                st.write(
                    f"**Ad Soyad:** {ad_soyad}"
                )

                st.write(
                    f"**Telefon:** {telefon}"
                )

                st.write(
                    f"**E-posta:** "
                    f"{muvekkil['e_posta'] or '-'}"
                )

                st.write(
                    f"**Meslek:** "
                    f"{muvekkil['meslek'] or '-'}"
                )

            with col2:
                st.write(
                    f"**T.C. Kimlik No:** "
                    f"{muvekkil['tc_kimlik_no'] or '-'}"
                )

                st.write(
                    f"**Doğum Tarihi:** "
                    f"{muvekkil['dogum_tarihi'] or '-'}"
                )

                st.write(
                    f"**Ücret:** "
                    f"{muvekkil['ucret']:,.2f} TL"
                )

                st.write(
                    f"**Tahsil Edilen:** "
                    f"{muvekkil['tahsil_edilen']:,.2f} TL"
                )

            st.write(
                f"**Adres:** "
                f"{muvekkil['adres'] or '-'}"
            )

            st.write(
                f"**Not:** "
                f"{muvekkil['notlar'] or '-'}"
            )