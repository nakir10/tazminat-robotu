from yardimcilar.trh_fonksiyonlari import (
    yas_tam,
    _aktif_pasif_donem,
    anuite_donemsel,
    anuite_tam_hayat,
    get_ex,
    get_Dx,
    get_Nx,
)
def bedensel_hasar_hesapla(
    dogum_tarihi: date,
    cinsiyet: str,
    kaza_tarihi: date,
    hesap_tarihi: date,
    gig_sure_gun: int,
    sakatlik_orani: float,           # 0.0 – 1.0
    aylik_net_gelir_kaza: float,     # kaza tarihindeki net gelir
    kaza_donemi_agi_dahil_net: float,# kaza tarihindeki AGİ dahil net ASÜ
    hesap_donemi_agi_dahil_net: float,# hesap tarihindeki AGİ dahil net ASÜ
    agi_haric_net_asgari: float,     # pasif dönem baz ücreti
    resmi_belgeli_gelir: bool,
    calisiyor_mu: bool = True,
    emekli_mi: bool = False,
    askerlik_belgeli_muafiyet: bool = False,
    bakici_ihtiyaci: str = "Yok",    # "Yok" | "Kısmi (%50)" | "Tam (%100)"
    bakici_belgeli: bool = False,
    brut_asgari_ucret: float = 0.0,
    kusur_orani_mazdur: float = 0.0,
) -> dict:
    """
    Sakatlık Tazminatı (Ek-2):
      GİG Tazminatı + Sürekli Sakatlık Tazminatı + Bakıcı Gideri
    """
    yas_hesap = yas_tam(dogum_tarihi, hesap_tarihi)
    donem_tipi = _aktif_pasif_donem(yas_hesap, calisiyor_mu, emekli_mi)

    # ----------------------------------------------------------------
    # [DÜZ-1] GELİR TESPİTİ — Ek-2 Madde 6(a)
    # Resmî belgeli gelir varsa ve AGİ dahil net ASÜ'den fazlaysa
    # işleyecek dönem geliri = hesap dönemi AGİ dahil net ASÜ × oran
    # oran = kaza geliri / kaza dönemi AGİ dahil net ASÜ
    # ----------------------------------------------------------------
    if resmi_belgeli_gelir and kaza_donemi_agi_dahil_net > 0:
        oran_katsayisi = aylik_net_gelir_kaza / kaza_donemi_agi_dahil_net
        if aylik_net_gelir_kaza > kaza_donemi_agi_dahil_net:
            # Oransal güncelleme
            aktif_isleyecek_aylik = hesap_donemi_agi_dahil_net * oran_katsayisi
        else:
            # Gelir ≤ AGİ → asgari ücret baz alınır
            aktif_isleyecek_aylik = hesap_donemi_agi_dahil_net
    else:
        aktif_isleyecek_aylik = hesap_donemi_agi_dahil_net

    pasif_aylik_gelir = agi_haric_net_asgari

    # GİG dönemi geliri: kaza tarihi geliri veya kaza dönemi asgari ücreti
    if resmi_belgeli_gelir:
        gig_aylik_gelir = aylik_net_gelir_kaza
    else:
        gig_aylik_gelir = kaza_donemi_agi_dahil_net

    # ----------------------------------------------------------------
    # GİG TAZMİNATI — İşlemiş dönem (Ek-2 Madde 1/2 + Madde 7/1)
    # GİG döneminde sakatlık oranı %100 varsayılır
    # İskontosuz, güncellemesiz
    # ----------------------------------------------------------------
    gig_sure_ay = gig_sure_gun / 30.4375  # ortalama gün/ay
    gig_tazminat = gig_aylik_gelir * gig_sure_ay  # × 1.0 (%100 GİG varsayımı)

    # ----------------------------------------------------------------
    # [DÜZ-2] ASKERLİK DÖNEMİ — Ek-2 Madde 6(3)
    # Belgeli muafiyet yoksa erkeklerde 18–22 yaş arası aktif dönem değil,
    # pasif dönem sayılır. Aktif anüite başlangıcı buna göre ayarlanır.
    # ----------------------------------------------------------------
    askerlik_baslangic_yas = None
    askerlik_bitis_yas = None
    askerlik_tenzil_yil = 0.0
    if cinsiyet == "Erkek" and not askerlik_belgeli_muafiyet:
        ask_bas = max(yas_hesap, 18)
        ask_bit = min(22, 65)
        if ask_bas < ask_bit:
            askerlik_baslangic_yas = ask_bas
            askerlik_bitis_yas = ask_bit
            askerlik_tenzil_yil = ask_bit - ask_bas

    # ----------------------------------------------------------------
    # SÜREKLİ SAKATLIK TAZMİNATI — İşleyecek dönem (Ek-2 Madde 7/2)
    # Formül: äx = Nx/Dx  (Dönem Başı Ödemeli Tam Hayat Anüitesi)
    # Aktif (18–65) + Pasif (65+) bileşik anüite
    # ----------------------------------------------------------------
    ae_aktif_yillik = 0.0
    ae_pasif_yillik = 0.0

    if donem_tipi == "aktif" and yas_hesap < 65:
        aktif_bitis = 65

        # [DÜZ-2] Askerlik varsa aktif anüiteyi iki parçada hesapla:
        #   yas_hesap → askerlik_bas  (aktif)
        #   askerlik_bas → askerlik_bit  (pasif ücret, ama anüite süre içinde)
        #   askerlik_bit → 65  (aktif)
        if askerlik_tenzil_yil > 0 and askerlik_baslangic_yas < aktif_bitis:
            # Askerlik öncesi aktif parça
            n_once = askerlik_baslangic_yas - yas_hesap
            ae_once = anuite_donemsel(yas_hesap, cinsiyet, n_once) if n_once > 0 else 0.0

            # Askerlik dönemi (pasif ücretle hesaplanır, ayrı tutulur)
            ae_ask_raw = anuite_donemsel(askerlik_baslangic_yas, cinsiyet, askerlik_tenzil_yil)
            Dx_x = get_Dx(yas_hesap, cinsiyet)
            Dx_ask = get_Dx(askerlik_baslangic_yas, cinsiyet)
            ae_ask = ae_ask_raw * (Dx_ask / Dx_x) if Dx_x else 0.0  # hesap tarihine indirgeme

            # Askerlik sonrası aktif parça
            n_sonra = aktif_bitis - askerlik_bitis_yas
            ae_sonra_raw = anuite_donemsel(askerlik_bitis_yas, cinsiyet, n_sonra) if n_sonra > 0 else 0.0
            Dx_ask_bit = get_Dx(askerlik_bitis_yas, cinsiyet)
            ae_sonra = ae_sonra_raw * (Dx_ask_bit / Dx_x) if Dx_x else 0.0

            ae_aktif_yillik = ae_once + ae_sonra
            # Askerlik dönemi için pasif ücret anüitesi eklenecek
            ae_ask_pasif = ae_ask  # pasif dönem geliriyle çarpılacak, aşağıda birleştirilir
        else:
            n_aktif = aktif_bitis - yas_hesap
            ae_aktif_yillik = anuite_donemsel(yas_hesap, cinsiyet, n_aktif)
            ae_ask_pasif = 0.0

        # Pasif dönem anüitesi (65 yaşından sonra): äx:∞ @ 65 indirgenmesi
        Dx_hesap = get_Dx(yas_hesap, cinsiyet)
        Dx_65 = get_Dx(65, cinsiyet)
        ae_65_raw = anuite_tam_hayat(65, cinsiyet)
        ae_pasif_yillik = ae_65_raw * (Dx_65 / Dx_hesap) if Dx_hesap else 0.0

        surekkli_sakatlik = (
            aktif_isleyecek_aylik * sakatlik_orani * ae_aktif_yillik * 12
            + (pasif_aylik_gelir * sakatlik_orani * ae_ask_pasif * 12 if askerlik_tenzil_yil > 0 else 0.0)
            + pasif_aylik_gelir * sakatlik_orani * ae_pasif_yillik * 12
        )

    elif donem_tipi == "aktif_2yil":
        ae_aktif_yillik = anuite_donemsel(yas_hesap, cinsiyet, 2.0)
        Dx_hesap = get_Dx(yas_hesap, cinsiyet)
        Dx_yeni = get_Dx(min(yas_hesap + 2, 99), cinsiyet)
        ae_65_raw = anuite_tam_hayat(min(yas_hesap + 2, 99), cinsiyet)
        ae_pasif_yillik = ae_65_raw * (Dx_yeni / Dx_hesap) if Dx_hesap else 0.0
        ae_ask_pasif = 0.0

        surekkli_sakatlik = (
            aktif_isleyecek_aylik * sakatlik_orani * ae_aktif_yillik * 12
            + pasif_aylik_gelir * sakatlik_orani * ae_pasif_yillik * 12
        )

    else:  # tamamen pasif
        ae_pasif_yillik = anuite_tam_hayat(yas_hesap, cinsiyet)
        ae_aktif_yillik = 0.0
        ae_ask_pasif = 0.0

        surekkli_sakatlik = pasif_aylik_gelir * sakatlik_orani * ae_pasif_yillik * 12

    # ----------------------------------------------------------------
    # BAKICI GİDERİ — Ek-2 Madde 8
    # ----------------------------------------------------------------
    bakici_gideri = 0.0
    if bakici_ihtiyaci != "Yok":
        bakici_baz = brut_asgari_ucret if bakici_belgeli else hesap_donemi_agi_dahil_net
        oran_bakici = 0.50 if bakici_ihtiyaci == "Kısmi (%50)" else 1.00
        ae_bakici = anuite_tam_hayat(yas_hesap, cinsiyet)
        bakici_gideri = bakici_baz * oran_bakici * ae_bakici * 12

    toplam_brut = gig_tazminat + surekkli_sakatlik + bakici_gideri
    kusur_indirimi = toplam_brut * kusur_orani_mazdur
    toplam_net = max(0.0, toplam_brut - kusur_indirimi)

    # [DÜZ-8] Güvenli döndürme — tanımsız değişken riski yok
    return {
        "donem_tipi": donem_tipi,
        "yas_hesap": yas_hesap,
        "aktif_isleyecek_aylik": aktif_isleyecek_aylik,
        "gig_sure_gun": gig_sure_gun,
        "gig_sure_ay": gig_sure_ay,
        "gig_tazminat": gig_tazminat,
        "ae_aktif_yillik": ae_aktif_yillik,
        "ae_pasif_yillik": ae_pasif_yillik,
        "askerlik_tenzil_yil": askerlik_tenzil_yil,
        "surekkli_sakatlik": surekkli_sakatlik,
        "bakici_gideri": bakici_gideri,
        "toplam_brut": toplam_brut,
        "kusur_indirimi": kusur_indirimi,
        "toplam_net": toplam_net,
        "hata": None,
    }