from app import db

class Ekipman(db.Model):
    __tablename__ = 'ekipman'

    id = db.Column(db.Integer, primary_key=True)
    kod = db.Column(db.String(100), unique=True, nullable=False, index=True)
    yakit = db.Column(db.String(50), nullable=False, default='')
    tipi = db.Column(db.String(100), nullable=False, default='')
    marka = db.Column(db.String(100), nullable=False)
    seri_no = db.Column(db.String(100), unique=True, nullable=False, index=True)
    calisma_yuksekligi = db.Column(db.Integer, nullable=False)
    kaldirma_kapasitesi = db.Column(db.Integer, nullable=False)
    uretim_tarihi = db.Column(db.String(100), nullable=False)
    calisma_durumu = db.Column(db.String(50), nullable=False, default='bosta')

    # Kiralama ile ilişki
    kiralamalar = db.relationship('Kiralama', back_populates='ekipman', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Ekipman {self.kod}>'


class Musteri(db.Model):
    __tablename__ = 'musteri'

    id = db.Column(db.Integer, primary_key=True)
    firma_adi = db.Column(db.String(150), nullable=False)
    yetkili_adi = db.Column(db.String(100), nullable=False)
    iletisim_bilgileri = db.Column(db.String(200), nullable=False)
    vergi_dairesi = db.Column(db.String(100), nullable=False)
    vergi_no = db.Column(db.String(50), unique=True, nullable=False)

    # Kiralama ile ilişki
    kiralamalar = db.relationship('Kiralama', back_populates='musteri', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Musteri {self.firma_adi}>'


class Kiralama(db.Model):
    __tablename__ = 'kiralama'

    id = db.Column(db.Integer, primary_key=True)
    kiralama_form_no = db.Column(db.String(100), nullable=True)

    # 🔗 ForeignKey alanları
    ekipman_id = db.Column(db.Integer, db.ForeignKey('ekipman.id'), nullable=False)
    musteri_id = db.Column(db.Integer, db.ForeignKey('musteri.id'), nullable=False)

    # İlişkiler
    ekipman = db.relationship('Ekipman', back_populates='kiralamalar')
    musteri = db.relationship('Musteri', back_populates='kiralamalar')

    kiralama_baslangıcı = db.Column(db.String(50), nullable=False)
    kiralama_bitis = db.Column(db.String(50), nullable=False)
    kiralama_brm_fiyat = db.Column(db.String(50), nullable=False)
    nakliye_fiyat = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        return f'<Kiralama {self.kiralama_form_no or ""} - {self.musteri.firma_adi}>'
