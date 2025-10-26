from app import db # __init__.py'de oluşturduğumuz 'db' objesi

class Ekipman(db.Model):
    """
    Makine Parkındaki (Filo) iş makinelerini temsil eden model.
    """
    id = db.Column(db.Integer, primary_key=True)
    kod = db.Column(db.String(100), unique=True, nullable=False, index=True)
    yakit = db.Column(db.String(50), nullable=False, default='')  # 'Elektrikli', 'Dizel', 'Hybrid' vb.
    tipi= db.Column(db.String(100), nullable=False, default='')  # Örneğin: 'Forklift', 'Vinç' vb.
    marka = db.Column(db.String(100), nullable=False)
    seri_no = db.Column(db.String(100), unique=True, nullable=False, index=True)
    calisma_yuksekligi = db.Column(db.String(100), nullable=False)
    kaldirma_kapasitesi = db.Column(db.String(100), nullable=False) 
    uretim_tarihi = db.Column(db.String(100), nullable=False)  # Üretim tarihi
    calısma_durumu = db.Column(db.String(50), nullable=False, default='')  # 'bosta' veya 'kirada' gibi değerler alabilir

    def __repr__(self):
        # Bu, terminalde objeyi print ettiğimizde nasıl görüneceğini belirler
        return f'<Ekipman {self.marka} - {self.kod}>'
class Musteri(db.Model):
    """
    Müşteri bilgilerini temsil eden model.
    """
    id = db.Column(db.Integer, primary_key=True)
    firma_adi = db.Column(db.String(150), nullable=False)
    yetkili_adi = db.Column(db.String(100), nullable=False)
    iletisim_bilgileri = db.Column(db.String(200), nullable=False) 
    vergi_dairesi = db.Column(db.String(100), nullable=False)
    vergi_no = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):

        return f'<Musteri {self.firma_adi} - {self.yetkili_adi}>'
class Kiralama(db.Model):
    """
    Makine kiralama işlemlerini temsil eden model.
    """
    id = db.Column(db.Integer, primary_key=True)
    kod = db.Column(db.String(100), nullable=False)  # Kiralanan makinenin kodu
    musteri_adi = db.Column(db.String(150), nullable=False)  # Müşteri adı
    musteri_iletisim = db.Column(db.String(200), nullable=False)  # Müşteri iletişim bilgileri
    kiralama_baslangıcı = db.Column(db.String(50), nullable=False)  # Kira başlangıç tarihi
    kiralama_bitis = db.Column(db.String(50), nullable=False)  # Kira bitiş tarihi
    kiralama_brm_fiyat = db.Column(db.String(50), nullable=False)  # Kira birim fiyatı
    nakliye_fiyat = db.Column(db.String(50), nullable=False)  # Nakliye fiyatı

    def __repr__(self):
        return f'<Kiralama {self.kod} - {self.musteri_adi}>'    
    
