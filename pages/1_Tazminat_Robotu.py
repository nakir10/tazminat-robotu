"""
============================================================
ZORUNLU TRAFİK SİGORTASI TAZMİNAT HESAPLAMA ROBOTU v1.1
============================================================
Yasal Dayanak:
  - 2918 sayılı Karayolları Trafik Kanunu (KTK)
  - Karayolları Motorlu Araçlar Zorunlu Mali Sorumluluk
    Sigortası Genel Şartları (RG-4/12/2021-31679)
    Ek-1 : Değer Kaybı Tazminatı Hesaplaması
    Ek-2 : Sakatlık Tazminatları Hesaplaması
    Ek-3 : Destekten Yoksun Kalma Tazminatı Hesaplaması
    Ek-7 : Tazminat Hesaplamalarında Esas Alınacak Hayat Tabloları
  - TRH-2010 Yaşam Tablosu (%1,65 iskonto oranı)

Değişiklik Kaydı — v1.0 → v1.1:
  [DÜZ-1] Modül 2: Aktif dönem geliri oransal güncelleme ile hesaplanıyor
           (Ek-2 Md.6/a — kaza geliri / kaza dönemi AGİ × hesap dönemi AGİ)
  [DÜZ-2] Modül 2: Askerlik dönemi artık aktif anüite süresinden düşülüyor
           (Ek-2 Md.6/3 — belgeli muafiyet yoksa 18-22 yaş pasif dönem)
  [DÜZ-3] Modül 3: İşlemiş dönem gelirinden destek şahsının payı çıkarılıyor
           (Ek-3 Md.6 — yalnızca hak sahiplerine düşen kısım dağıtılır)
  [DÜZ-4] Modül 3: Eş işleyecek döneminde aktif+pasif geçişi uygulanıyor
  [DÜZ-5] Modül 3: Ölü kod (isleyecek_es) temizlendi, tek tutarlı hesap yolu
  [DÜZ-6] Modül 3: Çocuk cinsiyeti artık parametreden alınıyor (hardcode kaldırıldı)
  [DÜZ-7] Modül 1: G.3 sınır kontrolü — km=0 durumunda yanlış tetiklenme düzeltildi
  [DÜZ-8] Modül 2: ae_aktif/ae_pasif NameError riski giderildi (güvenli None başlatma)
  [DÜZ-9] Modül 3: İşlemiş dönem hesabında destek payı uyarısı netleştirildi

Teknik Notlar:
  - İskonto oranı   : %1,65 (sabit, mevzuat gereği — Ek-2 Md.4, Ek-3 Md.4)
  - Aktif dönem     : 18–65 yaş
  - Pasif dönem gel.: AGİ hariç net asgari ücret (Ek-2 Md.6/2, Ek-3 Md.7/2)
  - İşlemiş dönem  : iskontosuz, güncellemesiz (Ek-2 Md.7/1, Ek-3 Md.8/1)
  - İşleyecek dönem: äx = Nx/Dx veya äx:n = (Nx−Nx+n)/Dx
  - Anüite birimi  : yıllık; aylık gelirle çarpımda ×12 uygulanır
  - Askerlik       : Ek-2'de pasif sayılır; Ek-3'te tenzil YAPILMAZ
============================================================
"""

import streamlit as st

# Sayfa Yapılandırması

# --- ŞİFRE KORUMA BAŞLANGICI ---
if "giris_yapildi" not in st.session_state:
    st.session_state.giris_yapildi = False

if not st.session_state.giris_yapildi:
    st.markdown("<br><br>", unsafe_allow_html=True)
    col_s1, col_s2, col_s3 = st.columns([1, 2, 1]) # Ekranı ortalamak için
    
    with col_s2:
        st.error("🔒 BU ALANA ERİŞİM KISITLANMIŞTIR")
        st.subheader("Sistemi Kullanmak İçin Giriş Yapın")
        sifre = st.text_input("Giriş Şifresi:", type="password")
        
        # Güncellenmiş yeni şifreniz
        if st.button("Sisteme Giriş Yap", use_container_width=True):
            if sifre == "771044":  
                st.session_state.giris_yapildi = True
                st.rerun()
            else:
                st.error("Girdiğiniz şifre hatalıdır. Lütfen tekrar deneyiniz.")
    st.stop() # Şifre doğru girilene kadar alt kodların çalışmasını engeller
# --- ŞİFRE KORUMA BİTİŞİ ---
import pandas as pd
from datetime import date
from dateutil.relativedelta import relativedelta

# ============================================================
# VERİ TABANI: TRH-2010 ERKEK (%1,65 İskonto)
# Tuple yapısı: (qx, px, lx, dx, ex, Dx, Nx)
# İndeks       :  0    1   2   3   4   5   6
# ============================================================
TRH2010_ERKEK = {
    0:  (0.019533, 0.980467, 100000, 1953, 71.93, 100000.00, 4181488.73),
    1:  (0.000888, 0.999112, 98047,  87,   72.35, 96455.18,  4081488.73),
    2:  (0.000776, 0.999224, 97960,  76,   71.42, 94805.23,  3985033.55),
    3:  (0.000686, 0.999314, 97884,  67,   70.47, 93193.94,  3890228.33),
    4:  (0.000642, 0.999358, 97816,  63,   69.52, 91618.29,  3797034.38),
    5:  (0.000552, 0.999448, 97754,  54,   68.57, 90073.23,  3705416.09),
    6:  (0.000430, 0.999570, 97700,  42,   67.60, 88562.19,  3615342.86),
    7:  (0.000355, 0.999645, 97658,  35,   66.63, 87087.18,  3526780.66),
    8:  (0.000327, 0.999673, 97623,  32,   65.66, 85643.17,  3439693.48),
    9:  (0.000347, 0.999653, 97591,  34,   64.68, 84225.45,  3354050.31),
    10: (0.000335, 0.999665, 97557,  33,   63.70, 82829.55,  3269824.87),
    11: (0.000291, 0.999709, 97525,  28,   62.72, 81457.77,  3186995.31),
    12: (0.000295, 0.999705, 97496,  29,   61.74, 80112.20,  3105537.54),
    13: (0.000347, 0.999653, 97467,  34,   60.76, 78788.55,  3025425.35),
    14: (0.000446, 0.999554, 97434,  43,   59.78, 77482.78,  2946636.80),
    15: (0.000551, 0.999449, 97390,  54,   58.80, 76191.09,  2869154.02),
    16: (0.000626, 0.999374, 97336,  61,   57.84, 74913.01,  2792962.92),
    17: (0.000690, 0.999310, 97276,  67,   56.87, 73650.90,  2718049.92),
    18: (0.000745, 0.999255, 97208,  72,   55.91, 72405.38,  2644399.02),
    19: (0.000790, 0.999210, 97136,  77,   54.95, 71177.01,  2571993.64),
    20: (0.000858, 0.999142, 97059,  83,   53.99, 69966.32,  2500816.63),
    21: (0.000932, 0.999068, 96976,  90,   53.04, 68771.59,  2430850.30),
    22: (0.000973, 0.999027, 96886,  94,   52.09, 67592.24,  2362078.72),
    23: (0.000981, 0.999019, 96791,  95,   51.14, 66430.37,  2294486.48),
    24: (0.000955, 0.999045, 96696,  92,   50.19, 65287.98,  2228056.11),
    25: (0.000919, 0.999081, 96604,  89,   49.24, 64166.88,  2162768.13),
    26: (0.000905, 0.999095, 96515,  87,   48.28, 63067.33,  2098601.24),
    27: (0.000906, 0.999094, 96428,  87,   47.33, 61987.48,  2035533.92),
    28: (0.000924, 0.999076, 96341,  89,   46.37, 60926.01,  1973546.44),
    29: (0.000957, 0.999043, 96252,  92,   45.41, 59881.69,  1912620.43),
    30: (0.000973, 0.999027, 96160,  94,   44.45, 58853.30,  1852738.74),
    31: (0.000978, 0.999022, 96066,  94,   43.50, 57841.65,  1793885.44),
    32: (0.001010, 0.998990, 95972,  97,   42.54, 56847.08,  1736043.79),
    33: (0.001068, 0.998932, 95875,  102,  41.58, 55867.84,  1679196.72),
    34: (0.001152, 0.998848, 95773,  110,  40.62, 54902.30,  1623328.88),
    35: (0.001202, 0.998798, 95662,  115,  39.67, 53948.90,  1568426.58),
    36: (0.001236, 0.998764, 95547,  118,  38.72, 53009.37,  1514477.68),
    37: (0.001320, 0.998680, 95429,  126,  37.77, 52084.49,  1461468.30),
    38: (0.001456, 0.998544, 95303,  139,  36.81, 51171.42,  1409383.82),
    39: (0.001643, 0.998357, 95165,  156,  35.87, 50267.52,  1358212.40),
    40: (0.001769, 0.998231, 95008,  168,  34.93, 49370.31,  1307944.88),
    41: (0.001861, 0.998139, 94840,  176,  33.99, 48483.02,  1258574.57),
    42: (0.002048, 0.997952, 94664,  194,  33.05, 47607.27,  1210091.56),
    43: (0.002331, 0.997669, 94470,  220,  32.12, 46738.59,  1162484.29),
    44: (0.002710, 0.997290, 94250,  255,  31.19, 45872.75,  1115745.70),
    45: (0.003020, 0.996980, 93994,  284,  30.27, 45005.84,  1069872.95),
    46: (0.003269, 0.996731, 93710,  306,  29.36, 44141.58,  1024867.11),
    47: (0.003630, 0.996370, 93404,  339,  28.46, 43283.10,   980725.53),
    48: (0.004104, 0.995896, 93065,  382,  27.56, 42425.96,   937442.43),
    49: (0.004693, 0.995307, 92683,  435,  26.67, 41566.01,   895016.46),
    50: (0.005159, 0.994841, 92248,  476,  25.79, 40699.39,   853450.45),
    51: (0.005558, 0.994442, 91772,  510,  24.93, 39832.17,   812751.06),
    52: (0.006163, 0.993837, 91262,  562,  24.06, 38967.81,   772918.89),
    53: (0.006979, 0.993021, 90700,  633,  23.21, 38099.02,   733951.08),
    54: (0.008014, 0.991986, 90067,  722,  22.37, 37219.01,   695852.06),
    55: (0.008968, 0.991032, 89345,  801,  21.54, 36321.45,   658633.05),
    56: (0.009810, 0.990190, 88544,  869,  20.74, 35411.42,   622311.60),
    57: (0.010834, 0.989166, 87675,  950,  19.94, 34494.85,   586900.19),
    58: (0.012050, 0.987950, 86725,  1045, 19.15, 33567.26,   552405.33),
    59: (0.013470, 0.986530, 85680,  1154, 18.38, 32624.46,   518838.07),
    60: (0.014781, 0.985219, 84526,  1249, 17.62, 31662.56,   486213.61),
    61: (0.016036, 0.983964, 83276,  1335, 16.88, 30688.19,   454551.05),
    62: (0.017600, 0.982400, 81941,  1442, 16.14, 29705.93,   423862.86),
    63: (0.019498, 0.980502, 80499,  1570, 15.42, 28709.41,   394156.93),
    64: (0.021763, 0.978237, 78929,  1718, 14.72, 27692.71,   365447.53),
    65: (0.024068, 0.975932, 77212,  1858, 14.04, 26650.31,   337754.82),
    66: (0.026344, 0.973656, 75353,  1985, 13.37, 25586.72,   311104.51),
    67: (0.028939, 0.971061, 73368,  2123, 12.72, 24508.28,   285517.79),
    68: (0.031899, 0.968101, 71245,  2273, 12.08, 23412.72,   261009.51),
    69: (0.035280, 0.964720, 68972,  2433, 11.47, 22297.97,   237596.79),
    70: (0.039232, 0.960768, 66539,  2610, 10.87, 21162.12,   215298.82),
    71: (0.043486, 0.956514, 63929,  2780, 10.29, 20001.87,   194136.69),
    72: (0.047834, 0.952166, 61149,  2925,  9.73, 18821.51,   174134.83),
    73: (0.052306, 0.947694, 58224,  3045,  9.20, 17630.30,   155313.31),
    74: (0.056931, 0.943069, 55178,  3141,  8.68, 16436.92,   137683.02),
    75: (0.063283, 0.936717, 52037,  3293,  8.17, 15249.53,   121246.10),
    76: (0.071007, 0.928993, 48744,  3461,  7.69, 14052.63,   105996.56),
    77: (0.078297, 0.921703, 45283,  3545,  7.24, 12842.89,    91943.94),
    78: (0.084963, 0.915037, 41737,  3546,  6.81, 11645.18,    79101.05),
    79: (0.090677, 0.909323, 38191,  3463,  6.40, 10482.80,    67455.87),
    80: (0.099237, 0.900763, 34728,  3446,  5.99,  9377.52,    56973.07),
    81: (0.111418, 0.888582, 31282,  3485,  5.59,  8309.81,    47595.55),
    82: (0.123215, 0.876785, 27796,  3425,  5.23,  7264.09,    39285.74),
    83: (0.133970, 0.866030, 24371,  3265,  4.90,  6265.66,    32021.65),
    84: (0.142406, 0.857594, 21106,  3006,  4.57,  5338.17,    25755.99),
    85: (0.153331, 0.846669, 18101,  2775,  4.25,  4503.67,    20417.83),
    86: (0.170400, 0.829600, 15325,  2611,  3.93,  3751.22,    15914.16),
    87: (0.189071, 0.810929, 12714,  2404,  3.64,  3061.50,    12162.94),
    88: (0.208788, 0.791212, 10310,  2153,  3.37,  2442.36,     9101.44),
    89: (0.227740, 0.772260,  8157,  1858,  3.12,  1901.06,     6659.08),
    90: (0.241418, 0.758582,  6300,  1521,  2.90,  1444.28,     4758.02),
    91: (0.253833, 0.746167,  4779,  1213,  2.66,  1077.82,     3313.74),
    92: (0.271552, 0.728448,  3566,   968,  2.39,   791.18,     2235.92),
    93: (0.302863, 0.697137,  2597,   787,  2.10,   566.98,     1444.74),
    94: (0.368996, 0.631004,  1811,   668,  1.80,   388.84,      877.76),
    95: (0.444244, 0.555756,  1143,   508,  1.55,   241.38,      488.92),
    96: (0.480228, 0.519772,   635,   305,  1.40,   131.97,      247.54),
    97: (0.501158, 0.498842,   330,   165,  1.23,    67.48,       115.57),
    98: (0.540448, 0.459552,   165,    89,  0.96,    33.12,        48.09),
    99: (1.000000, 0.000000,    76,    76,  0.50,    14.97,        14.97),
}

# ============================================================
# VERİ TABANI: TRH-2010 KADIN (%1,65 İskonto)
# ============================================================
TRH2010_KADIN = {
    0:  (0.008161, 0.991839, 100000,  816, 78.02, 100000.00, 4402977.37),
    1:  (0.000278, 0.999722,  99184,   28, 77.66,  97573.92, 4302977.37),
    2:  (0.000235, 0.999765,  99156,   23, 76.68,  95963.39, 4205403.45),
    3:  (0.000202, 0.999798,  99133,   20, 75.70,  94383.50, 4109440.06),
    4:  (0.000187, 0.999813,  99113,   19, 74.72,  92832.65, 4015056.56),
    5:  (0.000143, 0.999857,  99094,   14, 73.73,  91308.72, 3922223.92),
    6:  (0.000116, 0.999884,  99080,   12, 72.74,  89813.74, 3830915.20),
    7:  (0.000100, 0.999900,  99069,   10, 71.75,  88345.59, 3741101.46),
    8:  (0.000093, 0.999907,  99059,    9, 70.76,  86902.86, 3652755.87),
    9:  (0.000097, 0.999903,  99050,   10, 69.76,  85484.26, 3565853.00),
    10: (0.000094, 0.999906,  99040,    9, 68.77,  84088.50, 3480368.75),
    11: (0.000084, 0.999916,  99031,    8, 67.78,  82715.78, 3396280.25),
    12: (0.000084, 0.999916,  99022,    8, 66.78,  81366.27, 3313564.47),
    13: (0.000095, 0.999905,  99014,    9, 65.79,  80038.76, 3232198.20),
    14: (0.000115, 0.999885,  99005,   11, 64.79,  78732.09, 3152159.44),
    15: (0.000135, 0.999865,  98993,   13, 63.80,  77445.17, 3073427.34),
    16: (0.000148, 0.999852,  98980,   15, 62.81,  76177.77, 2995982.18),
    17: (0.000162, 0.999838,  98965,   16, 61.82,  74930.15, 2919804.41),
    18: (0.000177, 0.999823,  98949,   18, 60.83,  73701.92, 2844874.26),
    19: (0.000193, 0.999807,  98932,   19, 59.84,  72492.71, 2771172.34),
    20: (0.000210, 0.999790,  98912,   21, 58.85,  71302.20, 2698679.63),
    21: (0.000226, 0.999774,  98892,   22, 57.86,  70130.10, 2627377.42),
    22: (0.000241, 0.999759,  98869,   24, 56.88,  68976.16, 2557247.32),
    23: (0.000256, 0.999744,  98845,   25, 55.89,  67840.18, 2488271.16),
    24: (0.000271, 0.999729,  98820,   27, 54.90,  66721.91, 2420430.98),
    25: (0.000282, 0.999718,  98793,   28, 53.92,  65621.11, 2353709.07),
    26: (0.000295, 0.999705,  98766,   29, 52.93,  64537.71, 2288087.96),
    27: (0.000311, 0.999689,  98736,   31, 51.95,  63471.42, 2223550.25),
    28: (0.000331, 0.999669,  98706,   33, 50.97,  62421.73, 2160078.83),
    29: (0.000356, 0.999644,  98673,   35, 49.98,  61388.16, 2097657.10),
    30: (0.000372, 0.999628,  98638,   37, 49.00,  60370.22, 2036268.94),
    31: (0.000385, 0.999615,  98601,   38, 48.02,  59368.20, 1975898.72),
    32: (0.000411, 0.999589,  98563,   41, 47.04,  58382.03, 1916530.52),
    33: (0.000450, 0.999550,  98523,   44, 46.06,  57410.75, 1858148.49),
    34: (0.000501, 0.999499,  98479,   49, 45.08,  56453.44, 1800737.74),
    35: (0.000536, 0.999464,  98429,   53, 44.10,  55509.25, 1744284.30),
    36: (0.000562, 0.999438,  98376,   55, 43.12,  54578.97, 1688775.05),
    37: (0.000613, 0.999387,  98321,   60, 42.15,  53662.88, 1634196.09),
    38: (0.000690, 0.999310,  98261,   68, 41.17,  52759.45, 1580533.21),
    39: (0.000793, 0.999207,  98193,   78, 40.20,  51867.22, 1527773.76),
    40: (0.000860, 0.999140,  98115,   84, 39.23,  50984.82, 1475906.55),
    41: (0.000911, 0.999089,  98031,   89, 38.26,  50114.08, 1424921.72),
    42: (0.001015, 0.998985,  97942,   99, 37.30,  49255.72, 1374807.64),
    43: (0.001174, 0.998826,  97842,  115, 36.34,  48407.01, 1325551.92),
    44: (0.001387, 0.998613,  97727,  136, 35.38,  47565.37, 1277144.90),
    45: (0.001574, 0.998426,  97592,  154, 34.43,  46728.39, 1229579.53),
    46: (0.001725, 0.998275,  97438,  168, 33.48,  45897.55, 1182851.14),
    47: (0.001918, 0.998082,  97270,  187, 32.54,  45074.65, 1136953.60),
    48: (0.002154, 0.997846,  97083,  209, 31.60,  44257.92, 1091878.95),
    49: (0.002433, 0.997567,  96874,  236, 30.67,  43445.73, 1047621.03),
    50: (0.002650, 0.997350,  96639,  256, 29.74,  42636.53, 1004175.30),
    51: (0.002840, 0.997160,  96383,  274, 28.82,  41833.31,  961538.78),
    52: (0.003129, 0.996871,  96109,  301, 27.90,  41037.37,  919705.47),
    53: (0.003517, 0.996483,  95808,  337, 26.98,  40244.93,  878668.10),
    54: (0.004006, 0.995994,  95471,  382, 26.08,  39452.43,  838423.16),
    55: (0.004401, 0.995599,  95089,  418, 25.18,  38656.56,  798970.73),
    56: (0.004735, 0.995265,  94670,  448, 24.29,  37861.73,  760314.18),
    57: (0.005225, 0.994775,  94222,  492, 23.40,  37070.78,  722452.45),
    58: (0.005875, 0.994125,  93730,  551, 22.52,  36278.47,  685381.68),
    59: (0.006688, 0.993312,  93179,  623, 21.65,  35479.93,  649103.20),
    60: (0.007251, 0.992749,  92556,  671, 20.79,  34670.60,  613623.27),
    61: (0.007724, 0.992276,  91885,  710, 19.94,  33860.49,  578952.67),
    62: (0.008609, 0.991391,  91175,  785, 19.09,  33053.57,  545092.19),
    63: (0.009923, 0.990077,  90390,  897, 18.26,  32237.09,  512038.61),
    64: (0.011685, 0.988315,  89493, 1046, 17.43,  31399.10,  479801.53),
    65: (0.013220, 0.986780,  88447, 1169, 16.63,  30528.50,  448402.42),
    66: (0.014533, 0.985467,  87278, 1268, 15.85,  29635.92,  417873.93),
    67: (0.016337, 0.983663,  86010, 1405, 15.08,  28731.17,  388238.01),
    68: (0.018672, 0.981328,  84605, 1580, 14.32,  27803.02,  359506.84),
    69: (0.021583, 0.978417,  83025, 1792, 13.58,  26841.02,  331703.81),
    70: (0.024463, 0.975537,  81233, 1987, 12.87,  25835.43,  304862.79),
    71: (0.027224, 0.972776,  79246, 2157, 12.18,  24794.30,  279027.37),
    72: (0.030523, 0.969477,  77088, 2353, 11.51,  23727.78,  254233.07),
    73: (0.034440, 0.965560,  74735, 2574, 10.85,  22630.14,  230505.29),
    74: (0.039082, 0.960918,  72162, 2820, 10.22,  21496.08,  207875.15),
    75: (0.044930, 0.955070,  69341, 3116,  9.62,  20320.68,  186379.07),
    76: (0.051247, 0.948753,  66226, 3394,  9.05,  19092.65,  166058.39),
    77: (0.057276, 0.942724,  62832, 3599,  8.51,  17820.17,  146965.74),
    78: (0.062975, 0.937025,  59233, 3730,  8.00,  16526.81,  129145.57),
    79: (0.068250, 0.931750,  55503, 3788,  7.50,  15234.67,  112618.76),
    80: (0.075940, 0.924060,  51715, 3927,  7.01,  13964.48,   97384.09),
    81: (0.086117, 0.913883,  47788, 4115,  6.55,  12694.57,   83419.60),
    82: (0.095750, 0.904250,  43672, 4182,  6.12,  11413.04,   70725.04),
    83: (0.104485, 0.895515,  39491, 4126,  5.71,  10152.72,   59312.00),
    84: (0.111664, 0.888336,  35365, 3949,  5.32,   8944.34,   49159.28),
    85: (0.122720, 0.877280,  31416, 3855,  4.93,   7816.60,   40214.95),
    86: (0.139435, 0.860565,  27560, 3843,  4.54,   6746.04,   32398.34),
    87: (0.156215, 0.843785,  23717, 3705,  4.20,   5711.17,   25652.30),
    88: (0.171981, 0.828019,  20012, 3442,  3.88,   4740.78,   19941.13),
    89: (0.184245, 0.815755,  16571, 3053,  3.59,   3861.74,   15200.35),
    90: (0.196392, 0.803608,  13518, 2655,  3.29,   3099.10,   11338.61),
    91: (0.215417, 0.784583,  10863, 2340,  2.97,   2450.03,    8239.51),
    92: (0.239333, 0.760667,   8523, 2040,  2.64,   1891.05,    5789.48),
    93: (0.270550, 0.729450,   6483, 1754,  2.32,   1415.11,    3898.42),
    94: (0.313514, 0.686486,   4729, 1483,  1.99,   1015.50,    2483.31),
    95: (0.370141, 0.629859,   3246, 1202,  1.67,    685.81,    1467.81),
    96: (0.445527, 0.554473,   2045,  911,  1.36,    424.95,     782.00),
    97: (0.559928, 0.440072,   1134,  635,  1.05,    231.80,     357.05),
    98: (0.747798, 0.252202,    499,  373,  0.75,    100.35,     125.25),
    99: (1.000000, 0.000000,    126,  126,  0.50,     24.90,      24.90),
}

# ============================================================
# YARDIMCI FONKSİYONLAR: TRH-2010
# ============================================================

def _trh_row(yas: int, cinsiyet: str) -> tuple:
    tablo = TRH2010_ERKEK if cinsiyet == "Erkek" else TRH2010_KADIN
    return tablo[max(0, min(99, int(yas)))]

def get_Dx(yas: int, cinsiyet: str) -> float:
    return _trh_row(yas, cinsiyet)[5]

def get_Nx(yas: int, cinsiyet: str) -> float:
    return _trh_row(yas, cinsiyet)[6]

def get_ex(yas: int, cinsiyet: str) -> float:
    """ex: x yaşında beklenen ek yaşam süresi (yıl)."""
    return _trh_row(yas, cinsiyet)[4]

def anuite_tam_hayat(yas: int, cinsiyet: str) -> float:
    """
    äx = Nx / Dx  (Dönem Başı Ödemeli Tam Hayat Anüitesi, yıllık birim)
    Ek-7 formülü. Aylık tazminata çevirmek için ×12 uygulayınız.
    """
    Dx = get_Dx(yas, cinsiyet)
    return get_Nx(yas, cinsiyet) / Dx if Dx else 0.0

def anuite_donemsel(yas: int, cinsiyet: str, n_yil: float) -> float:
    """
    äx:n = (Nx − Nx+n) / Dx  (Dönem Başı Ödemeli Dönemsel Hayat Anüitesi, yıllık birim)
    n_yil kesirli ise Nx+n lineer interpolasyonla bulunur.
    """
    if n_yil <= 0:
        return 0.0
    Dx = get_Dx(yas, cinsiyet)
    if not Dx:
        return 0.0
    bitis_tam = yas + int(n_yil)
    kesir = n_yil - int(n_yil)
    if kesir == 0 or bitis_tam >= 99:
        Nx_n = get_Nx(min(bitis_tam, 99), cinsiyet)
    else:
        Nx_a = get_Nx(min(bitis_tam, 99), cinsiyet)
        Nx_b = get_Nx(min(bitis_tam + 1, 99), cinsiyet)
        Nx_n = Nx_a + kesir * (Nx_b - Nx_a)
    return max(0.0, (get_Nx(yas, cinsiyet) - Nx_n) / Dx)

def yas_tam(dogum: date, referans: date) -> int:
    return relativedelta(referans, dogum).years

def yas_tam_ay(dogum: date, referans: date) -> float:
    """Tam yıl + kesirli ay (aktif dönem hesabında hassasiyet için)."""
    d = relativedelta(referans, dogum)
    return d.years + d.months / 12


# ============================================================
# MODÜL 1: DEĞER KAYBI TAZMİNATI
# Ek-1 (RG-4/12/2021-31679)
# ============================================================

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


# ============================================================
# MODÜL 2: SAKATLIK TAZMİNATI
# Ek-2 (RG-4/12/2021-31679)
# ============================================================

def _aktif_pasif_donem(yas: int, calisiyor_mu: bool, emekli_mi: bool) -> str:
    """
    Ek-2 Madde 5: aktif/pasif dönem tespiti.
    Döndürür: "aktif" | "aktif_2yil" | "pasif"
    """
    if yas < 18:
        return "pasif"
    if yas < 65:
        return "pasif" if (emekli_mi and not calisiyor_mu) else "aktif"
    return "aktif_2yil" if calisiyor_mu else "pasif"


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


# ============================================================
# MODÜL 3: DESTEKTEN YOKSUN KALMA TAZMİNATI
# Ek-3 (RG-4/12/2021-31679)
# ============================================================

# Yeniden evlenme olasılıkları — Ek-3 Madde 9
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


# ============================================================
# STREAMLIT ARAYÜZÜ
# ============================================================

def fmt(tutar: float) -> str:
    return f"₺{tutar:,.2f}"

def main():
    st.set_page_config(
        page_title="Tazminat Hesaplama Robotu v1.1",
        page_icon="⚖️",
        layout="wide",
        initial_sidebar_state="expanded",
    )

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
    </style>
    """, unsafe_allow_html=True)

    # ── SIDEBAR ──────────────────────────────────────────────
    with st.sidebar:
        st.markdown("### ⚖️ Tazminat Robotu v1.1")
        st.caption("Zorunlu Trafik Sigortası · RG-4/12/2021-31679")
        st.markdown("---")
        modul = st.radio("HESAPLAMA MODÜLÜ", [
            "Değer Kaybı (Ek-1)",
            "Sakatlık Tazminatı (Ek-2)",
            "Destekten Yoksun Kalma (Ek-3)",
        ])
        st.markdown("---")

        # ── EK-1 GİRDİLERİ ──
        if modul == "Değer Kaybı (Ek-1)":
            arac_grubu = st.selectbox("Araç Grubu", list(ARAC_KODU_MAP.keys()))
            piyasa_degeri = st.number_input("Piyasa Değeri (TL)", 0.0, value=500000.0, step=1000.0)
            arac_kodu_prv = ARAC_KODU_MAP.get(arac_grubu, "A")
            km_label = "Çalışma Saati" if arac_kodu_prv == "D" else "Kilometre"
            km = st.number_input(km_label, 0.0, value=45000.0, step=500.0)
            toplam_hasar = st.number_input("Toplam Hasar (KDV dahil, TL)", 0.0, value=80000.0, step=500.0)
            ticari_kiralik = st.checkbox("Ticari / Kiralık (G.1: −0,05)")
            sbm_kayit = st.number_input("SBM Hasar Kaydı Sayısı", 0, 10, 0,
                                         help="Her kayıt −0,03 | max −0,15")
            hurda_mi = st.checkbox("⚠️ Hurda / Trafikten Çekme Var")
            st.markdown("**HASARLI PARÇALAR**")
            n_parca = st.number_input("Parça Sayısı", 1, 15, 3, step=1)
            parcalar = []
            for i in range(int(n_parca)):
                with st.expander(f"Parça {i+1}", expanded=(i == 0)):
                    isim = st.text_input("Parça Adı", f"Parça {i+1}", key=f"p_isim_{i}")
                    Pi = st.number_input("Pi (Değişim Katsayısı)", 0.0, value=1.0, step=0.25, key=f"pi_{i}",
                                          help="Ek-1 Madde 4 tablosundan ilgili satır Pi değeri")
                    Oi = st.number_input("Oi (Onarım Katsayısı)", 0.0, value=0.0, step=0.25, key=f"oi_{i}",
                                          help="Hafif=0.50 | Orta=0.75 | Yüksek=1.00 | Değişimse 0")
                    Yi = st.number_input("Yi (Boya Katsayısı)", 0.0, value=0.0, step=0.25, key=f"yi_{i}",
                                          help="Boya yok=0 | Lokal=tablo lokal Yi | Tam=tablo tam Yi")
                    parcalar.append({"isim": isim, "Pi": Pi, "Oi": Oi, "Yi": Yi})

        # ── EK-2 GİRDİLERİ ──
        elif modul == "Sakatlık Tazminatı (Ek-2)":
            st.markdown("**MAĞDUR**")
            m_dogum = st.date_input("Doğum Tarihi", date(1985, 6, 15))
            m_cinsiyet = st.radio("Cinsiyet", ["Erkek", "Kadın"], horizontal=True)
            kaza_t = st.date_input("Kaza Tarihi", date(2024, 3, 10))
            hesap_t = st.date_input("Hesap Tarihi", date.today())
            st.markdown("**KURUL RAPORU**")
            gig_gun = st.number_input("GİG Süresi (Gün)", 0, value=90, step=1)
            sakatlik_oran = st.slider("Sürekli Sakatlık Oranı (%)", 0, 100, 30) / 100
            st.markdown("**GELİR**")
            resmi_gelir = st.checkbox("Resmî Belgeli Gelir Var", True)
            aylik_kaza = st.number_input("Kaza Tarihi Aylık Net Gelir (TL)", 0.0, value=25000.0, step=500.0)
            kaza_agi = st.number_input("Kaza Dönemi AGİ Dahil Net ASÜ (TL)", 0.0, value=20002.50, step=100.0,
                                        help="Kaza tarihindeki asgari ücret — oransal güncelleme için gerekli")
            hesap_agi_dahil = st.number_input("Hesap Dönemi AGİ Dahil Net ASÜ (TL)", 0.0, value=22104.67, step=100.0)
            agi_haric = st.number_input("AGİ Hariç Net ASÜ (TL)", 0.0, value=20903.0, step=100.0,
                                         help="Pasif dönem baz geliri")
            st.markdown("**ÇALIŞMA**")
            calisiyor_s = st.checkbox("Hesap Tarihinde Çalışıyor", True)
            emekli_s = st.checkbox("Emekli", False)
            ask_muaf = st.checkbox("Askerlik Muafiyeti Belgeli", False)
            st.markdown("**BAKICI**")
            bakici = st.selectbox("Bakıcı İhtiyacı", ["Yok", "Kısmi (%50)", "Tam (%100)"])
            bakici_bel = st.checkbox("Bakıcı Belgelenmiş (Brüt ASÜ baz)")
            brut_asu = st.number_input("Brüt ASÜ (TL)", 0.0, value=26005.50, step=100.0,
                                        disabled=not bakici_bel)
            st.markdown("**KUSUR**")
            kusur_m = st.slider("Mağdurun Kusur Oranı (%)", 0, 100, 0) / 100

        # ── EK-3 GİRDİLERİ ──
        else:
            st.markdown("**DESTEK ŞAHSI**")
            d_dogum = st.date_input("Doğum Tarihi", date(1975, 4, 20))
            d_cinsiyet = st.radio("Cinsiyet", ["Erkek", "Kadın"], horizontal=True)
            vefat_t = st.date_input("Vefat/Kaza Tarihi", date(2024, 1, 15))
            hesap_t_d = st.date_input("Hesap Tarihi", date.today())
            st.markdown("**GELİR**")
            resmi_gelir_d = st.checkbox("Resmî Belgeli Gelir Var", True)
            d_aylik = st.number_input("Aylık Net Gelir (TL)", 0.0, value=35000.0, step=500.0)
            vefat_agi = st.number_input("Vefat Dönemi AGİ Dahil Net ASÜ (TL)", 0.0, value=20002.50, step=100.0)
            hesap_agi_d = st.number_input("Hesap Dönemi AGİ Dahil Net ASÜ (TL)", 0.0, value=22104.67, step=100.0)
            agi_haric_d = st.number_input("AGİ Hariç Net ASÜ (TL)", 0.0, value=20903.0, step=100.0)
            d_cal = st.checkbox("Vefat Tarihinde Çalışıyordu", True)
            d_em = st.checkbox("Emekli", False)
            st.markdown("**HAK SAHİPLERİ**")
            es_var = st.checkbox("Eş", True)
            es_dogum_s = es_cinsiyet_s = ev_yeniden_s = ev_tar_s = velayet_s = None
            if es_var:
                es_dogum_s = st.date_input("Eşin Doğum Tarihi", date(1978, 9, 5))
                es_cinsiyet_s = st.radio("Eşin Cinsiyeti", ["Kadın", "Erkek"], horizontal=True)
                velayet_s = st.number_input("Velayetteki Çocuk Sayısı", 0, 10, 0)
                ev_yeniden_s = st.checkbox("Eş Yeniden Evlendi (Bilinen)")
                ev_tar_s = st.date_input("Yeniden Evlenme Tarihi", date(2025, 6, 1)) if ev_yeniden_s else None
            n_cocuk = st.number_input("Çocuk Sayısı", 0, 8, 1, step=1)
            cocuklar_list = []
            for i in range(int(n_cocuk)):
                with st.expander(f"Çocuk {i+1}"):
                    c_dog = st.date_input("Doğum Tarihi", date(2010, 3, 1), key=f"cd_{i}")
                    # [DÜZ-6] Cinsiyet artık alınıyor
                    c_cin = st.radio("Cinsiyet", ["Erkek", "Kadın"], horizontal=True, key=f"cc_{i}")
                    c_lis = st.checkbox("Lisans/Lisansüstü (25 yaş)", key=f"cl_{i}")
                    cocuklar_list.append({"dogum_tarihi": c_dog, "cinsiyet": c_cin, "lisans_mi": c_lis})
            anne_var = st.checkbox("Anne (Hak Sahibi)", False)
            anne_dog_s = st.date_input("Anne Doğum Tarihi", date(1950, 1, 1)) if anne_var else None
            baba_var = st.checkbox("Baba (Hak Sahibi)", False)
            baba_dog_s = st.date_input("Baba Doğum Tarihi", date(1948, 1, 1)) if baba_var else None
            st.markdown("**KUSUR**")
            kusur_d = st.slider("Destek Şahsının Kusur Oranı (%)", 0, 100, 0) / 100

    # ── ANA EKRAN ────────────────────────────────────────────
    st.markdown("""
    <div class="rh">
        <div class="sub">Adli Bilirkişi & Aktüer Standardında</div>
        <h1>⚖️ Zorunlu Trafik Sigortası Tazminat Hesaplama Robotu</h1>
        <div class="sub">RG-4/12/2021-31679 · TRH-2010 Hayat Tablosu · İskonto %1,65 · v1.1</div>
    </div>
    """, unsafe_allow_html=True)

    col_btn, col_warn = st.columns([1, 3])
    with col_btn:
        hesapla = st.button("▶  HESAPLA")
    with col_warn:
        st.markdown('<div class="warn"><strong>Hukuki Uyarı:</strong> Bu robot mevzuata uygun aktüeryal hesaplama yapar. Sonuçlar yargı kararının veya resmî bilirkişi raporunun yerini tutmaz.</div>', unsafe_allow_html=True)

    if not hesapla:
        st.markdown("""
        <div style="text-align:center;padding:3rem 2rem;">
            <div style="font-size:3rem;margin-bottom:1rem;">⚖️</div>
            <div style="font-family:'IBM Plex Serif',serif;font-size:1.05rem;color:#555;">
                Sol panelden modülü ve parametreleri seçin, ardından <strong>HESAPLA</strong>'ya basın.
            </div>
            <div style="margin-top:1rem;font-size:.78rem;color:#aaa;font-family:'IBM Plex Mono',monospace;">
                EK-1: Değer Kaybı · EK-2: Sakatlık Tazminatı · EK-3: Destekten Yoksun Kalma
            </div>
        </div>
        """, unsafe_allow_html=True)
        return

    st.markdown("---")

    # ── EK-1 SONUÇLARI ───────────────────────────────────────
    if modul == "Değer Kaybı (Ek-1)":
        s = deger_kaybi_hesapla(arac_grubu, piyasa_degeri, km, parcalar,
                                toplam_hasar, ticari_kiralik, sbm_kayit, hurda_mi)
        if s["hata"]:
            st.markdown(f'<div class="err">🚫 {s["hata"]}</div>', unsafe_allow_html=True)
            return

        st.markdown('<div class="sec">DEĞER KAYBI TAZMİNATI — Ek-1</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="card"><div class="lbl">Araç Kodu</div><div class="val">{s["arac_kodu"]}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="card"><div class="lbl">Piyasa Değeri</div><div class="val">{fmt(piyasa_degeri)}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="card grn"><div class="lbl">Toplam Hasar</div><div class="val">{fmt(toplam_hasar)}</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="sec">KATSAYI ZİNCİRİ</div>', unsafe_allow_html=True)
        rows = [
            ["R — Rayiç Değer Katsayısı", f"{s['R']:.2f}", f"Tablo R.1/R.2 · Piyasa Değeri {fmt(piyasa_degeri)}"],
            ["K — Kullanılmışlık Katsayısı", f"{s['K']:.2f}", f"Tablo K.1/K.2/K.3 · {km:,.0f} km/saat"],
            ["HK — Hasar Katsayısı (Σ Pi+Oi+Yi)", f"{s['HK']:.4f}", f"{len(parcalar)} parça toplamı"],
            ["T — Hasar Tutarı Katsayısı", f"{s['T']:.4f}", f"({fmt(toplam_hasar)} / {fmt(piyasa_degeri)} × 100) × 0,10"],
            ["H — Hasara Uğrayan Parçalar Katsayısı", f"{s['H']:.4f}", f"(HK + T) / 100"],
            ["G.1 — Ticari/Kiralık", f"{s['G1']:+.2f}", "Ticari/Kiralık: −0,05 | Diğer: 0,00"],
            ["G.2 — SBM Hasar Geçmişi", f"{s['G2']:+.2f}", f"{sbm_kayit} kayıt × (−0,03) | max −0,15"],
            ["G.3 — Km Alt Sınır Yakınlığı (≤1000 km)", f"{s['G3']:+.2f}", "0 < fark ≤ 1000 km ise +0,05 | Diğer: 0,00"],
            ["G — Genel Değerlendirme Katsayısı", f"{s['G']:.4f}", f"1 + ({s['G1']:.2f} + {s['G2']:.2f} + {s['G3']:.2f})"],
        ]
        df = pd.DataFrame(rows, columns=["Parametre", "Değer", "Açıklama / Mevzuat Dayanağı"])
        st.markdown(df.to_html(index=False, classes="ptbl"), unsafe_allow_html=True)

        st.markdown('<div class="sec">NİHAİ FORMÜL</div>', unsafe_allow_html=True)
        carpan_not = " × 2,5 (Motosiklet — Ek-1 Madde 6/2)" if s["carpan"] == 2.5 else ""
        st.markdown(f"""
        <div style="background:#F0EDE8;padding:.9rem 1.4rem;border-radius:6px;font-family:'IBM Plex Mono',monospace;font-size:.85rem;color:#1A1A2E;margin:.4rem 0;">
        DK = Piyasa Değeri × R × K × H × G{carpan_not}<br>
        DK = {fmt(piyasa_degeri)} × {s['R']:.2f} × {s['K']:.2f} × {s['H']:.4f} × {s['G']:.4f} = {fmt(s['DK_ham'])}
        {"<br><strong>DK_nihai = " + fmt(s['DK_ham']) + " × 2,5 = " + fmt(s['DK_nihai']) + "</strong>" if s['carpan'] == 2.5 else ""}
        </div>
        """, unsafe_allow_html=True)
        st.markdown(f'<div class="grand"><div class="gl">ARAÇ DEĞER KAYBI TAZMİNATI (Ek-1)</div><div class="gv">{fmt(s["DK_nihai"])}</div></div>', unsafe_allow_html=True)

    # ── EK-2 SONUÇLARI ───────────────────────────────────────
    elif modul == "Sakatlık Tazminatı (Ek-2)":
        s = bedensel_hasar_hesapla(
            dogum_tarihi=m_dogum, cinsiyet=m_cinsiyet,
            kaza_tarihi=kaza_t, hesap_tarihi=hesap_t,
            gig_sure_gun=gig_gun, sakatlik_orani=sakatlik_oran,
            aylik_net_gelir_kaza=aylik_kaza,
            kaza_donemi_agi_dahil_net=kaza_agi,
            hesap_donemi_agi_dahil_net=hesap_agi_dahil,
            agi_haric_net_asgari=agi_haric,
            resmi_belgeli_gelir=resmi_gelir,
            calisiyor_mu=calisiyor_s, emekli_mi=emekli_s,
            askerlik_belgeli_muafiyet=ask_muaf,
            bakici_ihtiyaci=bakici, bakici_belgeli=bakici_bel,
            brut_asgari_ucret=brut_asu,
            kusur_orani_mazdur=kusur_m,
        )
        if s.get("hata"):
            st.markdown(f'<div class="err">🚫 {s["hata"]}</div>', unsafe_allow_html=True)
            return

        donem_txt = {"aktif":"Aktif (18–65 yaş)","pasif":"Pasif","aktif_2yil":"Aktif +2 Yıl (65+)"}
        st.markdown('<div class="sec">SAKATLIK TAZMİNATI — Ek-2</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="card"><div class="lbl">Hesap Tarihi Yaşı</div><div class="val">{s["yas_hesap"]}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="card"><div class="lbl">Dönem</div><div class="val" style="font-size:1rem;">{donem_txt.get(s["donem_tipi"],"")}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="card"><div class="lbl">Sakatlık Oranı</div><div class="val">{sakatlik_oran*100:.0f}%</div></div>', unsafe_allow_html=True)

        st.markdown('<div class="sec">HESAPLAMA DETAYI</div>', unsafe_allow_html=True)
        rows2 = [
            ["GİG Süresi", f"{s['gig_sure_gun']} gün ({s['gig_sure_ay']:.2f} ay)", "Kurul Raporu — GİG döneminde sakatlık %100 varsayılır (Ek-2 Md.1/2)"],
            ["GİG Aylık Geliri", fmt(aylik_kaza if resmi_gelir else hesap_agi_dahil), "İşlemiş dönem — iskontosuz, güncellemesiz"],
            ["GİG Tazminatı", fmt(s["gig_tazminat"]), "Aylık Gelir × Süre (ay)"],
            ["İşleyecek Aktif Aylık Gelir [DÜZ-1]", fmt(s["aktif_isleyecek_aylik"]), "Ek-2 Md.6/a: kaza geliri / kaza AGİ × hesap AGİ (oransal)"],
            ["äx Aktif (yıllık, ×12→aylık)", f"{s['ae_aktif_yillik']:.5f}", f"äx:n = (Nx−Nx+n)/Dx · TRH-2010 · %1,65 iskonto"],
            ["äx Pasif (65+ indirgenmis, yıllık, ×12→aylık)", f"{s['ae_pasif_yillik']:.5f}", "Nx(65)/Dx(hesap_yaş) · pasif baz: AGİ hariç net ASÜ"],
            ["Askerlik Tenzili [DÜZ-2]", f"{s['askerlik_tenzil_yil']:.1f} yıl" if s['askerlik_tenzil_yil'] else "Yok/Muaf", "Ek-2 Md.6/3 — 18-22 yaş pasif dönem; belgeli muafiyet yoksa"],
            ["Sürekli Sakatlık Tazminatı", fmt(s["surekkli_sakatlik"]), f"Aktif+Pasif anüite × %{sakatlik_oran*100:.0f}"],
            ["Bakıcı Gideri", fmt(s["bakici_gideri"]), f"{'Brüt ASÜ' if bakici_bel else 'AGİ dahil net ASÜ'} × {bakici} × äx"],
        ]
        df2 = pd.DataFrame(rows2, columns=["Kalem", "Değer", "Açıklama / Mevzuat Dayanağı"])
        st.markdown(df2.to_html(index=False, classes="ptbl"), unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="card blu"><div class="lbl">GİG Tazminatı</div><div class="val">{fmt(s["gig_tazminat"])}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="card blu"><div class="lbl">Sürekli Sakatlık</div><div class="val">{fmt(s["surekkli_sakatlik"])}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="card blu"><div class="lbl">Bakıcı Gideri</div><div class="val">{fmt(s["bakici_gideri"])}</div></div>', unsafe_allow_html=True)

        if kusur_m > 0:
            st.markdown(f'<div class="warn"><strong>Kusur Tenzili (A.6/b):</strong> Mağdurun %{kusur_m*100:.0f} kusuruna karşılık {fmt(s["kusur_indirimi"])} düşülmüştür.</div>', unsafe_allow_html=True)

        label = "NET (Kusur Tenzilli)" if kusur_m > 0 else "TOPLAM"
        st.markdown(f'<div class="grand"><div class="gl">SAKATLIK TAZMİNATI {label} (Ek-2)</div><div class="gv">{fmt(s["toplam_net"])}</div></div>', unsafe_allow_html=True)

    # ── EK-3 SONUÇLARI ───────────────────────────────────────
    else:
        s = destekten_yoksun_kalma_hesapla(
            destek_dogum_tarihi=d_dogum, destek_cinsiyet=d_cinsiyet,
            vefat_tarihi=vefat_t, hesap_tarihi=hesap_t_d,
            destek_aylik_net_gelir=d_aylik,
            vefat_donemi_agi_dahil_net=vefat_agi,
            hesap_donemi_agi_dahil_net=hesap_agi_d,
            agi_haric_net_asgari=agi_haric_d,
            resmi_belgeli_gelir=resmi_gelir_d,
            destek_calisiyor_mu=d_cal, destek_emekli_mi=d_em,
            es_dogum_tarihi=es_dogum_s if es_var else None,
            es_cinsiyet=es_cinsiyet_s if es_var else "Kadın",
            es_yeniden_evlendi_mi=ev_yeniden_s if es_var else False,
            es_evlenme_tarihi=ev_tar_s if (es_var and ev_yeniden_s) else None,
            velayetteki_cocuk_sayisi=int(velayet_s) if es_var else 0,
            cocuklar=cocuklar_list,
            anne_dogum_tarihi=anne_dog_s, anne_hayatta_mi=anne_var,
            baba_dogum_tarihi=baba_dog_s, baba_hayatta_mi=baba_var,
            kusur_orani_destek=kusur_d,
        )
        if s.get("hata"):
            st.markdown(f'<div class="err">🚫 {s["hata"]}</div>', unsafe_allow_html=True)
            return

        donem_txt = {"aktif":"Aktif (18–65)","pasif":"Pasif","aktif_2yil":"Aktif +2 Yıl"}
        st.markdown('<div class="sec">DESTEKTEN YOKSUN KALMA TAZMİNATI — Ek-3</div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        with c1: st.markdown(f'<div class="card"><div class="lbl">Vefat Yaşı</div><div class="val">{s["yas_destek_vefat"]}</div></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="card"><div class="lbl">Dönem</div><div class="val" style="font-size:1rem;">{donem_txt.get(s["donem_tipi"],"")}</div></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="card"><div class="lbl">İşlemiş Dönem</div><div class="val" style="font-size:1rem;">{s["islemis_sure_ay"]:.1f} Ay</div></div>', unsafe_allow_html=True)

        hs_orani_pct = s["hak_sahibi_gelir_orani"] * 100
        st.markdown(f'<div class="warn"><strong>[DÜZ-3] Pay Düzeltmesi (Ek-3 Md.6):</strong> Toplam {s["toplam_pay"]} payın 2\'si destek şahsına ayrılmış; hak sahiplerine düşen gelir oranı <strong>%{hs_orani_pct:.1f}</strong> olarak uygulanmıştır.</div>', unsafe_allow_html=True)

        st.markdown('<div class="sec">HAK SAHİBİ BAZLI TAZMİNAT</div>', unsafe_allow_html=True)
        if s["hak_sahibi_sonuclari"]:
            df3 = pd.DataFrame([{
                "Hak Sahibi": h["tip"],
                "Yaş": h["yas"],
                "Pay Oranı": f"{h['pay_oran']:.4f}",
                "Desteklik (yıl)": f"{h['n_desteklik']:.1f}",
                "Yeniden Evl.": f"%{h['ev_olasiligi']*100:.0f}" if h["ev_olasiligi"] > 0 else "—",
                "İşlemiş Dönem": fmt(h["islemis"]),
                "İşleyecek Dönem": fmt(h["isleyecek"]),
                "KİŞİ TOPLAMI": fmt(h["toplam"]),
            } for h in s["hak_sahibi_sonuclari"]])
            st.markdown(df3.to_html(index=False, classes="ptbl"), unsafe_allow_html=True)
        else:
            st.warning("Hak sahibi girilmedi.")

        if kusur_d > 0:
            st.markdown(f'<div class="warn"><strong>Kusur Tenzili (A.6/d):</strong> Destek şahsının %{kusur_d*100:.0f} kusuruna karşılık {fmt(s["kusur_indirimi"])} düşülmüştür.</div>', unsafe_allow_html=True)

        st.markdown(f'<div class="grand"><div class="gl">DESTEKTEN YOKSUN KALMA TAZMİNATI NET (Ek-3)</div><div class="gv">{fmt(s["genel_toplam_net"])}</div></div>', unsafe_allow_html=True)
        st.markdown('<div class="warn"><strong>Not (Ek-3 Md.9/3):</strong> Destekten yoksun kalma hesabında askerlik dönemi tenzili YAPILMAMAKTADIR (Ek-2\'den farklı).</div>', unsafe_allow_html=True)

    # Footer
    st.markdown(f"""
    <div class="foot">
        Hesaplama Tarihi: {date.today().strftime('%d.%m.%Y')} &nbsp;|&nbsp;
        Mevzuat: RG-4/12/2021-31679 &nbsp;|&nbsp;
        TRH-2010 · %1,65 İskonto &nbsp;|&nbsp;
        v1.1 — Bu rapor yargısal bilirkişi raporu niteliği taşımaz.
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
