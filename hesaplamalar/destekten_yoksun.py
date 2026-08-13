from dateutil.relativedelta import relativedelta
from datetime import date

from yardimcilar.trh_fonksiyonlari import (
    yas_tam,
    anuite_donemsel,
    anuite_tam_hayat,
    get_Dx,
    get_Nx,
    get_ex,
    _aktif_pasif_donem,
)

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


def destekten_yoksun_kalma_hesapla(
    destek_dogum_tarihi: date,
    destek_cinsiyet: str,
    vefat_tarihi: date,
    hesap_tarihi: date,
    destek_aylik_net_gelir: float,
    vefat_donemi_agi_dahil_net: float,   # vefat tarihindeki AGİ dahil net ASÜ
    hesap_donemi_agi_dahil_net: float,   # hesap tarihindeki AGİ dahil net ASÜ
    agi_haric_net_asgari: float,
    resmi_belgeli_gelir: bool,
    destek_calisiyor_mu: bool,
    destek_emekli_mi: bool,
    es_dogum_tarihi: date = None,
    es_cinsiyet: str = "Kadın",
    es_yeniden_evlendi_mi: bool = False,
    es_evlenme_tarihi: date = None,
    velayetteki_cocuk_sayisi: int = 0,
    cocuklar: list = None,  # [{"dogum_tarihi":date,"cinsiyet":str,"lisans_mi":bool}]
    anne_dogum_tarihi: date = None,
    baba_dogum_tarihi: date = None,
    anne_hayatta_mi: bool = False,
    baba_hayatta_mi: bool = False,
    kusur_orani_destek: float = 0.0,
) -> dict:
    """
    Destekten Yoksun Kalma Tazminatı — Ek-3
    Askerlik tenzili YAPILMAZ (Madde 9/3).
    İşlemiş dönem: destek şahsının payı çıkarılarak hak sahiplerine dağıtılır.
    """
    if cocuklar is None:
        cocuklar = []

    yas_destek_vefat = yas_tam(destek_dogum_tarihi, vefat_tarihi)
    yas_destek_hesap = yas_tam(destek_dogum_tarihi, hesap_tarihi)
    ex_destek = get_ex(yas_destek_hesap, destek_cinsiyet)

    # Aktif/pasif dönem — Ek-3 Madde 5 (vefat tarihindeki yaş esas)
    donem_destek = _aktif_pasif_donem(yas_destek_vefat, destek_calisiyor_mu, destek_emekli_mi)

    # ----------------------------------------------------------------
    # [DÜZ-1] GELİR TESPİTİ — Ek-3 Madde 7(a)
    # ----------------------------------------------------------------
    if resmi_belgeli_gelir and vefat_donemi_agi_dahil_net > 0:
        oran_k = destek_aylik_net_gelir / vefat_donemi_agi_dahil_net
        if destek_aylik_net_gelir > vefat_donemi_agi_dahil_net:
            aktif_isleyecek_aylik = hesap_donemi_agi_dahil_net * oran_k
        else:
            aktif_isleyecek_aylik = hesap_donemi_agi_dahil_net
    else:
        aktif_isleyecek_aylik = hesap_donemi_agi_dahil_net

    pasif_aylik = agi_haric_net_asgari

    # İşlemiş dönem geliri (gelir tespitinde vefat tarihi verileri)
    if resmi_belgeli_gelir:
        islemis_aylik = destek_aylik_net_gelir
    else:
        islemis_aylik = vefat_donemi_agi_dahil_net

    # ----------------------------------------------------------------
    # PAY YAPISI — Ek-3 Madde 6
    # ----------------------------------------------------------------
    destek_pay = 2
    es_pay_sayi = 2 if es_dogum_tarihi is not None else 0
    cocuk_pay_sayi = len(cocuklar)
    anne_pay_sayi = 0
    baba_pay_sayi = 0
    if anne_hayatta_mi and anne_dogum_tarihi:
        anne_pay_sayi = 2 if (not baba_hayatta_mi or not baba_dogum_tarihi) else 1
    if baba_hayatta_mi and baba_dogum_tarihi:
        baba_pay_sayi = 2 if (not anne_hayatta_mi or not anne_dogum_tarihi) else 1

    toplam_pay = destek_pay + es_pay_sayi + cocuk_pay_sayi + anne_pay_sayi + baba_pay_sayi
    if toplam_pay == 0:
        toplam_pay = 1  # sıfır bölme koruması

    # [DÜZ-3] Hak sahiplerine dağıtılacak gelir oranı = 1 - destek_pay/toplam_pay
    # Destek şahsının kendi payı çıkarılır; yalnızca kalan pay hak sahiplerine verilir.
    hak_sahibi_gelir_orani = 1.0 - (destek_pay / toplam_pay)

    # ----------------------------------------------------------------
    # İŞLEMİŞ DÖNEM (iskontosuz, güncellemesiz — Ek-3 Madde 8/1)
    # ----------------------------------------------------------------
    delta = relativedelta(hesap_tarihi, vefat_tarihi)
    islemis_sure_ay = delta.years * 12 + delta.months + delta.days / 30.4375
    islemis_sure_ay = max(0.0, islemis_sure_ay)

    # Hak sahiplerine düşen toplam işlemiş dönem havuzu
    islemis_havuz = islemis_aylik * islemis_sure_ay * hak_sahibi_gelir_orani

    # ----------------------------------------------------------------
    # İŞLEYECEK DÖNEM ANÜİTELERİ (destek şahsına ait)
    # ----------------------------------------------------------------
    if donem_destek == "aktif" and yas_destek_hesap < 65:
        n_aktif = 65 - yas_destek_hesap
        Dx_d = get_Dx(yas_destek_hesap, destek_cinsiyet)
        Dx_65 = get_Dx(65, destek_cinsiyet)
        ae_aktif_d = anuite_donemsel(yas_destek_hesap, destek_cinsiyet, n_aktif)
        ae_pasif_d = anuite_tam_hayat(65, destek_cinsiyet) * (Dx_65 / Dx_d) if Dx_d else 0.0
    elif donem_destek == "aktif_2yil":
        Dx_d = get_Dx(yas_destek_hesap, destek_cinsiyet)
        Dx_yeni = get_Dx(min(yas_destek_hesap + 2, 99), destek_cinsiyet)
        ae_aktif_d = anuite_donemsel(yas_destek_hesap, destek_cinsiyet, 2.0)
        ae_pasif_d = anuite_tam_hayat(min(yas_destek_hesap + 2, 99), destek_cinsiyet) * (Dx_yeni / Dx_d) if Dx_d else 0.0
    else:
        ae_aktif_d = 0.0
        ae_pasif_d = anuite_tam_hayat(yas_destek_hesap, destek_cinsiyet)

    def _isleyecek_kisi(yas_k: int, cinsiyet_k: str, n_desteklik: float) -> float:
        """
        Hak sahibi x yaşında, n_desteklik yıl süre için äx:n.
        Üst limit: destek şahsının ex beklenen ömrüne göre kısıtlanır.
        """
        n_efektif = min(max(n_desteklik, 0.0), ex_destek)
        if n_efektif <= 0:
            return 0.0
        return anuite_donemsel(yas_k, cinsiyet_k, n_efektif)

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