from flask_wtf import FlaskForm
from wtforms import (
    StringField, 
    DecimalField, 
    SelectField, 
    DateField, 
    SubmitField, 
    FormField,  # Alt formları eklemek için
    FieldList   # Alt form listesi oluşturmak için
)
# DataRequired yerine InputRequired kullanmak,
# '' (boş metin) değerlerinin coerce=int veya Decimal()
# hatalarına yol açmasını engeller.
from wtforms.validators import Optional, InputRequired

# --- 1. Ekipman Ekleme Formu ---

class EkipmanForm(FlaskForm):
    """
    Yeni makine (ekipman) eklemek için kullanılacak form.
    """
    kod = StringField('Makine Kodu', validators=[InputRequired()])
    yakit = StringField('Yakıt Türü', validators=[InputRequired()])
    tipi = StringField('Makine Tipi', validators=[InputRequired()])
    marka = StringField('Makine Markası', validators=[InputRequired()])
    seri_no = StringField('Makine Seri No', validators=[InputRequired()])
    calisma_yuksekligi = StringField('Çalışma Yüksekliği (m)', validators=[InputRequired()]) 
    kaldirma_kapasitesi = StringField('Kaldırma Kapasitesi (kg)', validators=[InputRequired()])
    uretim_tarihi = StringField('Üretim Tarihi (Örn: 2023-10-31)', validators=[InputRequired()])
    submit = SubmitField('Kaydet')


# --- 2. Müşteri (Firma) Ekleme Formu ---

class FirmaForm(FlaskForm):
    """
    Yeni firma (müşteri) eklemek için kullanılacak form.
    """
    firma_adi = StringField('Firma Adı', validators=[InputRequired()])
    yetkili_adi = StringField('Yetkili Kişi', validators=[InputRequired()])
    iletisim_bilgileri = StringField('Adres / İletişim', validators=[InputRequired()])
    vergi_dairesi = StringField('Vergi Dairesi', validators=[InputRequired()])
    vergi_no = StringField('Vergi Numarası', validators=[InputRequired()])
    submit = SubmitField('Kaydet')


# --- 3. Kiralama Kalemi Alt Formu (DÜZELTİLDİ) ---

class KiralamaKalemiForm(FlaskForm):
    """
    Ana Kiralama formundaki her bir ekipman satırını temsil eder.
    """
    
    # WTForms alt formları için CSRF koruması ana formdan gelir.
    class Meta:
        csrf = False 

    # DÜZELTME: 'coerce=int' KALDIRILDI.
    # 'InputRequired' validatörü, 'value=""' olan 
    # "--- Ekipman Seçiniz ---" seçeneğinin gönderilmesini engelleyecektir.
    ekipman_id = SelectField('Ekipman Seç', validators=[InputRequired()])
    
    kiralama_baslangıcı = DateField('Başlangıç Tarihi', format='%Y-%m-%d', validators=[InputRequired()])
    kiralama_bitis = DateField('Bitiş Tarihi', format='%Y-%m-%d', validators=[InputRequired()])
    
    # DecimalField için de InputRequired önemlidir
    kiralama_brm_fiyat = DecimalField('Birim Fiyat', validators=[InputRequired()])
    nakliye_fiyat = DecimalField('Nakliye Fiyatı', validators=[Optional()], default=0.0)
    

# --- 4. Ana Kiralama Formu (DÜZELTİLDİ) ---

class KiralamaForm(FlaskForm):
    """
    Ana Kiralama Formu.
    """
    kiralama_form_no = StringField('Kiralama Form No', validators=[Optional()])
    
    # DÜZELTME: 'coerce=int' KALDIRILDI.
    musteri_id = SelectField('Müşteri Seç', validators=[InputRequired()])

    # 'kalemler' listesi, 'KiralamaKalemiForm' alt formlarını tutar
    kalemler = FieldList(FormField(KiralamaKalemiForm), min_entries=1)
    
    submit = SubmitField('Kaydet')