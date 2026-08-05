def arac_gruplari():
    return list(ARAC_KODU_MAP.keys())
    
ARAC_KODU_MAP = {
    "Otomobil": "A", "Taksi": "A",
    "Minibüs": "B", "Otobüs": "B",
    "Kamyonet": "C", "Kamyon": "C", "Çekici": "C", "Tanker": "C",
    "İş Makinesi": "D", "Traktör": "D", "Tarım Makinesi": "D",
    "Özel Amaçlı Araç": "Ç",
    "Römork": "E",
    "Motosiklet": "F",
}

def get_R_katsayisi(piyasa_degeri: float, arac_kodu: str) -> float:
    """Rayiç Değer Katsayısı — Ek-1 Madde 2, Tablo R.1 (A,F) / R.2 (B,C,Ç,D,E)."""
    if arac_kodu in ("A", "F"):
        sinirlar = [(50000,0.65),(100000,0.70),(200000,0.75),(300000,0.80),
                    (400000,0.85),(500000,0.90),(750000,0.95),(float("inf"),1.00)]
    else:
        sinirlar = [(250000,0.65),(350000,0.70),(500000,0.75),(750000,0.80),
                    (1000000,0.85),(1250000,0.90),(1500000,0.95),(float("inf"),1.00)]
    for esik, r in sinirlar:
        if piyasa_degeri < esik:
            return r
    return 1.00

def get_K_katsayisi(km_veya_saat: float, arac_kodu: str) -> float:
    """
    Kullanılmışlık Düzeyi Katsayısı — Ek-1 Madde 3
    K.1 (A,F) ve K.2 (B,C,Ç,E): kilometre
    K.3 (D): çalışma saati
    """
    if arac_kodu in ("A", "F"):
        sinirlar = [(20000,1.00),(50000,0.95),(100000,0.90),(150000,0.85),
                    (200000,0.80),(300000,0.75),(float("inf"),0.70)]
    elif arac_kodu == "D":
        sinirlar = [(500,1.00),(1000,0.95),(2000,0.90),(3000,0.85),
                    (4000,0.80),(5000,0.75),(float("inf"),0.70)]
    else:  # B, C, Ç, E
        sinirlar = [(50000,1.00),(150000,0.95),(300000,0.90),(500000,0.85),
                    (750000,0.80),(1000000,0.75),(float("inf"),0.70)]
    for esik, k in sinirlar:
        if km_veya_saat < esik:
            return k
    return 0.70

def _km_tablo_alt_siniri(km: float, arac_kodu: str) -> float:
    """G.3 kontrolü: ilgili tablodaki alt bant sınırını döndürür."""
    if arac_kodu in ("A", "F"):
        bantlar = [0, 20000, 50000, 100000, 150000, 200000, 300000]
    elif arac_kodu == "D":
        bantlar = [0, 500, 1000, 2000, 3000, 4000, 5000]
    else:
        bantlar = [0, 50000, 150000, 300000, 500000, 750000, 1000000]
    alt = 0
    for b in bantlar:
        if km >= b:
            alt = b
    return alt

def get_R_katsayisi(piyasa_degeri: float, arac_kodu: str) -> float:
    """Rayiç Değer Katsayısı — Ek-1 Madde 2, Tablo R.1 (A,F) / R.2 (B,C,Ç,D,E)."""
    if arac_kodu in ("A", "F"):
        sinirlar = [(50000,0.65),(100000,0.70),(200000,0.75),(300000,0.80),
                    (400000,0.85),(500000,0.90),(750000,0.95),(float("inf"),1.00)]
    else:
        sinirlar = [(250000,0.65),(350000,0.70),(500000,0.75),(750000,0.80),
                    (1000000,0.85),(1250000,0.90),(1500000,0.95),(float("inf"),1.00)]
    for esik, r in sinirlar:
        if piyasa_degeri < esik:
            return r
    return 1.00

def get_K_katsayisi(km_veya_saat: float, arac_kodu: str) -> float:
    """
    Kullanılmışlık Düzeyi Katsayısı — Ek-1 Madde 3
    K.1 (A,F) ve K.2 (B,C,Ç,E): kilometre
    K.3 (D): çalışma saati
    """
    if arac_kodu in ("A", "F"):
        sinirlar = [(20000,1.00),(50000,0.95),(100000,0.90),(150000,0.85),
                    (200000,0.80),(300000,0.75),(float("inf"),0.70)]
    elif arac_kodu == "D":
        sinirlar = [(500,1.00),(1000,0.95),(2000,0.90),(3000,0.85),
                    (4000,0.80),(5000,0.75),(float("inf"),0.70)]
    else:  # B, C, Ç, E
        sinirlar = [(50000,1.00),(150000,0.95),(300000,0.90),(500000,0.85),
                    (750000,0.80),(1000000,0.75),(float("inf"),0.70)]
    for esik, k in sinirlar:
        if km_veya_saat < esik:
            return k
    return 0.70

def _km_tablo_alt_siniri(km: float, arac_kodu: str) -> float:
    """G.3 kontrolü: ilgili tablodaki alt bant sınırını döndürür."""
    if arac_kodu in ("A", "F"):
        bantlar = [0, 20000, 50000, 100000, 150000, 200000, 300000]
    elif arac_kodu == "D":
        bantlar = [0, 500, 1000, 2000, 3000, 4000, 5000]
    else:
        bantlar = [0, 50000, 150000, 300000, 500000, 750000, 1000000]
    alt = 0
    for b in bantlar:
        if km >= b:
            alt = b
    return alt

def deger_kaybi_hesapla(
    arac_grubu: str,
    piyasa_degeri: float,
    km_veya_saat: float,
    hasarli_parcalar: list,      # [{"isim":str,"Pi":float,"Oi":float,"Yi":float}]
    toplam_hasar_tutari: float,  # KDV dahil, tenzilatsız
    ticari_kiralik: bool,
    sbm_kayit_sayisi: int,
    hurda_mi: bool,
) -> dict:
    """
    Değer Kaybı Tazminatı — Ek-1 Madde 6
    DK = Piyasa Değeri × R × K × H × G
    F kodu (Motosiklet): DK_nihai = DK × 2,5  [Madde 6/2]
    """
    # [DÜZ-7] G.3: km=0 kenar durumu — sıfır km bandın içindeyse (+0 fark) G3 uygulanmaz
    if hurda_mi:
        return {"hata": ("Hasar sebebiyle trafikten çekme veya hurdaya çıkarılma işlemi "
                         "görmüş araçlar değer kaybı tazminatı talebinde bulunamaz. "
                         "(Genel Şartlar A.6/ö)"), "sonuc": 0.0}

    arac_kodu = ARAC_KODU_MAP.get(arac_grubu, "A")
    R = get_R_katsayisi(piyasa_degeri, arac_kodu)
    K = get_K_katsayisi(km_veya_saat, arac_kodu)

    # HK — Hasar Katsayısı (Ek-1 Madde 4/1)
    HK = sum(p["Pi"] + p["Oi"] + p["Yi"] for p in hasarli_parcalar)

    # T — Hasar Tutarı Katsayısı (Ek-1 Madde 4/3)
    T = (toplam_hasar_tutari / piyasa_degeri * 100) * 0.10 if piyasa_degeri else 0.0

    # H — Hasara Uğrayan Parçalar Katsayısı (Ek-1 Madde 4/4)
    H = (HK + T) / 100

    # G — Genel Değerlendirme Katsayısı (Ek-1 Madde 5)
    G1 = -0.05 if ticari_kiralik else 0.0
    G2 = -0.03 * min(max(sbm_kayit_sayisi, 0), 5)

    # [DÜZ-7] G.3: km>0 VE km - alt_sinir ≤ 1000 ise tetiklenir
    alt_sinir = _km_tablo_alt_siniri(km_veya_saat, arac_kodu)
    fark = km_veya_saat - alt_sinir
    G3 = 0.05 if (km_veya_saat > 0 and 0 < fark <= 1000) else 0.0

    G = 1.0 + G1 + G2 + G3

    DK = piyasa_degeri * R * K * H * G
    carpan = 2.5 if arac_kodu == "F" else 1.0
    DK_nihai = DK * carpan

    return {
        "arac_kodu": arac_kodu, "R": R, "K": K,
        "HK": HK, "T": T, "H": H,
        "G1": G1, "G2": G2, "G3": G3, "G": G,
        "DK_ham": DK, "carpan": carpan, "DK_nihai": DK_nihai,
        "hata": None,
    }