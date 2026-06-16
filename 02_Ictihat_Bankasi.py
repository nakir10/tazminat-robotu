import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="İçtihat Otomasyonu ve Bilgi Bankası",
    page_icon="⚖️",
    layout="wide"
)

# ──────────────────────────────────────────────
# VERİ KATMANI
# ──────────────────────────────────────────────
if "ictihat_df" not in st.session_state:
    data = [
        {
            "ALAN": "İŞ HUKUKU",
            "KONU / İÇERİK": (
                "MOBİNG İSPATI / Özel hukuk ve iş hukuku yargılamasında vicdani kanaatin oluşmasına "
                "yetecek kadar bir ispatın yeterli olduğu, taraflarca ileri sürülen delillerin sıhhat "
                "ve kuvvetinde tereddüt edilmesi halinde işçi lehine yorum ilkesinin uygulanması gerektiği"
            ),
            "SAYI / TARİH": "9. Hukuk Dairesi – 2016/36185 E., 2020/18583 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "BORÇLAR HUKUKU",
            "KONU / İÇERİK": (
                "SÖZLEŞMEYİ HAKSIZ OLARAK FESHEDEN KARŞI TARAFIN HEM MÜSPET HEM DE MENFİ ZARARLARINI TAZMİN EDER"
            ),
            "SAYI / TARİH": "6. Hukuk Dairesi – 2024/813 E., 2024/3080 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "HMK",
            "KONU / İÇERİK": (
                "Medeni usul hukukunda hukukî yarar, mahkemede bir davanın açılabilmesi için, davacının "
                "bu davayı açmakta ve mahkemeden hukuksal korunma istemekte bir çıkarının bulunması "
                "gerektiğine ilişkin ilke anlamına gelir. Davacının davayı açtığı tarih itibariyle dava "
                "açmakta hukuk kuralları tarafından haklı bulunan (korunan) bir yararı olmalı, hakkını "
                "elde edebilmesi için mahkeme kararına ihtiyacı bulunmalıdır."
            ),
            "SAYI / TARİH": "HGK – 2019/592 E., 2022/706 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "HMK",
            "KONU / İÇERİK": (
                "Davanın belirsiz alacak davası olarak açılmasına rağmen tazminatın belirli olduğu sonucuna "
                "ulaşılsa da davacının mevcut yasal düzenlemeler karşısında dava açmaktan başka bir yolla "
                "alacağına kavuşma imkânı olmayıp bir mahkeme kararına ihtiyaç bulunması karşısında "
                "eldeki eda davasını açmakta hukukî yararının bulunmadığını söylemek mümkün değildir."
            ),
            "SAYI / TARİH": "HGK – 2019/592 E., 2022/706 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "BORÇLAR HUKUKU",
            "KONU / İÇERİK": (
                "Havale ödeme vasıtası olup var olan bir borcun ödendiğini gösterir. Bu karinenin aksini "
                "havaleyi gönderen şahsın ispat etmesi gerekir. (Açıklamasız gönderilen paranın "
                "değerlendirmesi: Sanki borcun var da borcunu ödüyorsun; aksini parayı gönderen "
                "ispatlamalıdır.)"
            ),
            "SAYI / TARİH": "13. Hukuk Dairesi – 2015/42470 E., 2018/3508 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "BORÇLAR HUKUKU",
            "KONU / İÇERİK": (
                "Havale bir borç ödeme aracıdır. Eğer havaleyle borç verilmişse açıklamaya yazılmalıdır; "
                "aksi hâlde verilen paranın borç ödendiğine karine oluşur ve bu karineyi havaleyi "
                "gönderen çürütmelidir."
            ),
            "SAYI / TARİH": "13. Hukuk Dairesi – 2015/39062 E., 2017/12750 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "HMK",
            "KONU / İÇERİK": (
                "Bu düzenleme dikkate alındığında WhatsApp yazışmaları belge niteliğindedir."
            ),
            "SAYI / TARİH": "6. Hukuk Dairesi – 2023/1984 E., 2024/4323 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "İŞ HUKUKU",
            "KONU / İÇERİK": "MOBİNG TANIMI VE SOMUT OLAYA YANSIMASI",
            "SAYI / TARİH": "22. Hukuk Dairesi – 2015/11958 E., 2016/15623 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "İŞ HUKUKU",
            "KONU / İÇERİK": (
                "YILLIK İZNE ÇIKAN İŞÇİYE PEŞİN ÜCRET ÖDEMESİNİN YAPILMAMASI İŞÇİ TARAFINDAN "
                "HAKLI FESİH SEBEBİDİR"
            ),
            "SAYI / TARİH": "9. Hukuk Dairesi – 2025/2024 E., 2025/2487 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "İŞ HUKUKU",
            "KONU / İÇERİK": (
                "İşverenin işçiye kullandırdığı yıllık ücretli iznin hak edilenden fazla olduğu öne "
                "sürülerek karşılığında parasal iade talep etmenin yasal bir dayanağı yoktur."
            ),
            "SAYI / TARİH": "9. Hukuk Dairesi – 2016/26145 E., 2020/11957 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "İŞ HUKUKU",
            "KONU / İÇERİK": (
                "Yıllık izinlerin kullandırıldığı noktasında ispat yükü işverene aittir. İşveren yıllık "
                "izinlerin kullandırıldığını imzalı izin defteri veya eşdeğer bir belge ile "
                "kanıtlamalıdır. Bu nedenle yıllık iznin zamanaşımı iş sözleşmesinin feshinden "
                "itibaren işlemeye başlar."
            ),
            "SAYI / TARİH": "9. Hukuk Dairesi – 2020/9573 E., 2024/15629 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "İŞ HUKUKU",
            "KONU / İÇERİK": (
                "FAZLA ÇALIŞMANIN ŞEKLİ, İSPATI VE USULÜ ÜZERİNE KAPSAMLI İÇTİHAT"
            ),
            "SAYI / TARİH": "7. Hukuk Dairesi – 2013/15259 E., 2014/415 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "İŞ HUKUKU",
            "KONU / İÇERİK": (
                "İŞÇİ FESİH SEBEBİNE BAĞLIDIR. SUNMUŞ OLDUĞU FESİH SEBEBİ HAKSIZ ÇIKMASI HALİNDE "
                "HAKLI OLDUĞU ANCAK TALEPTE BULUNMADIĞI FESİH SEBEBİYLE HAKLI DURUMA GELEMEZ."
            ),
            "SAYI / TARİH": "9. Hukuk Dairesi – 2016/33833 E., 2020/17837 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "İŞ HUKUKU",
            "KONU / İÇERİK": (
                "Fazla çalışma yaptığını iddia eden işçi bu iddiasını ispatla yükümlüdür. Fazla "
                "çalışmanın ispatı konusunda iş yeri kayıtları, özellikle işyerine giriş çıkışı "
                "gösteren belgeler, iş yeri iç yazışmaları delil niteliğindedir. Ancak, yazılı "
                "belgelerle ispatlanamaması durumunda tarafların dinletmiş oldukları tanık beyanları "
                "ile sonuca gidilmesi gerekir. İşçinin fiilen yaptığı işin niteliği ve yoğunluğuna "
                "göre de fazla çalışma olup olmadığı araştırılmalıdır."
            ),
            "SAYI / TARİH": "9. Hukuk Dairesi – 2021/8477 E., 2021/14490 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "İŞ HUKUKU",
            "KONU / İÇERİK": (
                "Fazla çalışmanın yazılı delil ya da tanıkla ispatı imkân dahilindedir. İşyerinde "
                "çalışma düzenini bilmeyen ve bilmesi mümkün olmayan tanıkların anlatımlarına değer "
                "verilemez. Aynı ispat kuralları hafta tatili ve ulusal bayram ile genel tatil ücret "
                "alacakları için de geçerlidir."
            ),
            "SAYI / TARİH": "9. Hukuk Dairesi – 2021/8477 E., 2021/14490 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "İŞ HUKUKU",
            "KONU / İÇERİK": (
                "Davacının yaptığı işin niteliği ve çalıştığı işyerinin özelliği ile kesinleşmiş "
                "mahkeme kararları gözetilmeden, salt husumetli oldukları gerekçesiyle tanık beyanları "
                "hiç dikkate alınmadan fazla çalışma, hafta tatili ile ulusal bayram ve genel tatil "
                "alacaklarının reddine hükmedilmesi hatalı olup bozmayı gerektirmiştir."
            ),
            "SAYI / TARİH": "9. Hukuk Dairesi – 2021/8477 E., 2021/14490 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "İŞ HUKUKU",
            "KONU / İÇERİK": (
                "Bir işyerinde aralıklı çalışmanın varlığı halinde talep edilecek olan ihbar "
                "tazminatı bir bütün olarak değil ayrı ayrı talep edilmelidir. (Detayları karardan "
                "okunmalıdır)"
            ),
            "SAYI / TARİH": "9. Hukuk Dairesi – 2025/6398 E., 2025/7870 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "İŞ HUKUKU",
            "KONU / İÇERİK": (
                "Aynı fesih sebebine bağlı olarak hem kötüniyet tazminatına hem de eşit davranma "
                "borcuna aykırılık tazminatına hükmedilmiştir. Aynı olay sebebiyle iki ayrı tazminata "
                "hükmedilebilmesi ancak kanunun açıkça cevaz verdiği hallerde mümkündür; bu nedenle "
                "işçi lehine olan tazminata hükmedilmesi gerekirken iki tazminata birden hükmedilmesi "
                "usul ve kanuna aykırı olup bozmayı gerektirmiştir."
            ),
            "SAYI / TARİH": "22. Hukuk Dairesi – 2014/31113 E., 2015/12206 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "SİGORTA HUKUKU",
            "KONU / İÇERİK": (
                "Trafik kazalarında irdelenmesi gereken husus trafik kazasının meydana gelmesinde "
                "tarafların olaya etkileri ve dolayısıyla sürüş kusurlarıdır. Kaza sırasında "
                "davacının geçerli bir sürücü belgesinin olmaması idari yaptırım uygulanmasını "
                "gerektiren bir hal olup sürüş kusuru olarak veya illiyet bağını kesen bir hal "
                "olarak nitelendirilemez."
            ),
            "SAYI / TARİH": "4. Hukuk Dairesi – 2025/8636 E., 2025/14492 K.",
            "PDF_LINK": "#",
        },
        {
            "ALAN": "İŞ HUKUKU",
            "KONU / İÇERİK": (
                "24 Saatlik çalışma esası varsa işçinin uyku ihtiyacını gidereceği yatak/kanepe vb. "
                "bulunuyorsa 10 saat, yoksa 4 saat ara dinlenme yaptığı kabul edilir. "
                "\"Nitekim, ilke olarak, işçinin uyku ihtiyacını gideremediği 24 saat esaslı "
                "çalışmada yemek ve sair ihtiyaçları nedeniyle 4 saat ara dinlenme yaptığı "
                "kabul edilmelidir.\""
            ),
            "SAYI / TARİH": "HGK – 2014/22-2460 E., 2017/230 K.",
            "PDF_LINK": "#",
        },
    ]
    st.session_state.ictihat_df = pd.DataFrame(data)

# ──────────────────────────────────────────────
# BAŞLIK
# ──────────────────────────────────────────────
st.markdown(
    """
    <h1 style='text-align:center; color:#1a3c6e;'>⚖️ İçtihat Otomasyonu ve Bilgi Bankası</h1>
    <p style='text-align:center; color:#555; font-size:15px;'>
        Emsal kararlarınızı kolayca arayın, filtreleyin ve yeni içtihatlar ekleyin.
    </p>
    <hr>
    """,
    unsafe_allow_html=True,
)

sekme1, sekme2 = st.tabs(["🔍 İçtihat Takip & Arama", "➕ Yeni İçtihat & PDF Yükle"])

# ──────────────────────────────────────────────
# SEKME 1 – ARAMA & KART TASARIMI
# ──────────────────────────────────────────────
with sekme1:
    df = st.session_state.ictihat_df.copy()

    col_filtre, col_arama = st.columns([1, 3])

    with col_filtre:
        alanlar = ["Hepsi"] + sorted(df["ALAN"].dropna().unique().tolist())
        secili_alan = st.selectbox("📂 Hukuk Alanı", alanlar)

    with col_arama:
        arama_metni = st.text_input(
            "🔎 Arama (Konu / İçerik veya Künye içinde arar)",
            placeholder="Anahtar kelime giriniz…",
        )

    # Filtreleme
    if secili_alan != "Hepsi":
        df = df[df["ALAN"] == secili_alan]

    if arama_metni.strip():
        maske = (
            df["KONU / İÇERİK"].str.contains(arama_metni, case=False, na=False)
            | df["SAYI / TARİH"].str.contains(arama_metni, case=False, na=False)
        )
        df = df[maske]

    st.markdown(f"**{len(df)}** içtihat bulundu.")
    st.divider()

    if df.empty:
        st.warning("Arama kriterlerinize uygun içtihat bulunamadı.")
    else:
        for _, row in df.iterrows():
            with st.container():
                st.info(
                    f"**🏛️ Alan:** {row['ALAN']}   |   **📌 Künye:** {row['SAYI / TARİH']}\n\n"
                    f"{row['KONU / İÇERİK']}"
                )
                if row["PDF_LINK"] and row["PDF_LINK"] != "#":
                    st.link_button("📄 Emsal Karar PDF'ini Gör", row["PDF_LINK"])
                else:
                    st.caption("⚠️ Bu karara ait yüklenmiş PDF bulunmuyor.")
                st.write("")

# ──────────────────────────────────────────────
# SEKME 2 – YENİ İÇTİHAT & PDF YÜKLE
# ──────────────────────────────────────────────
with sekme2:
    st.subheader("Yeni İçtihat Ekle")
    st.markdown("Aşağıdaki formu doldurarak bilgi bankasına yeni bir emsal karar ekleyin.")

    mevcut_alanlar = sorted(st.session_state.ictihat_df["ALAN"].dropna().unique().tolist())
    alan_secenekleri = mevcut_alanlar + ["Diğer / Yeni Alan"]

    with st.form("yeni_ictihat_formu", clear_on_submit=True):
        secilen_alan = st.selectbox("Hukuk Alanı *", alan_secenekleri)
        yeni_alan_adi = st.text_input(
            "Yeni Alan Adı (yalnızca 'Diğer / Yeni Alan' seçildiğinde doldurun)"
        )
        kunye = st.text_input("Karar Künyesi *", placeholder="ör. 9. Hukuk Dairesi – 2025/1234 E., 2025/5678 K.")
        ozet = st.text_area("İçtihat Özeti *", height=180, placeholder="Kararın özeti veya önemli hüküm…")
        pdf_dosya = st.file_uploader("PDF Yükle (isteğe bağlı)", type=["pdf"])
        gonder = st.form_submit_button("💾 İçtihadı Kaydet")

    if gonder:
        eksik = []
        if not kunye.strip():
            eksik.append("Karar Künyesi")
        if not ozet.strip():
            eksik.append("İçtihat Özeti")
        if eksik:
            st.error(f"Lütfen zorunlu alanları doldurun: {', '.join(eksik)}")
        else:
            alan_adi = yeni_alan_adi.strip() if secilen_alan == "Diğer / Yeni Alan" and yeni_alan_adi.strip() else secilen_alan
            pdf_link = "#"
            if pdf_dosya is not None:
                pdf_link = f"[Yüklendi: {pdf_dosya.name}]"

            yeni_satir = pd.DataFrame(
                [
                    {
                        "ALAN": alan_adi,
                        "KONU / İÇERİK": ozet.strip(),
                        "SAYI / TARİH": kunye.strip(),
                        "PDF_LINK": pdf_link,
                    }
                ]
            )
            st.session_state.ictihat_df = pd.concat(
                [st.session_state.ictihat_df, yeni_satir], ignore_index=True
            )
            st.success(
                f"✅ İçtihat başarıyla eklendi! "
                f"Toplam kayıt sayısı: **{len(st.session_state.ictihat_df)}**"
            )
            st.balloons()
