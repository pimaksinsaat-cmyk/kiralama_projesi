from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class EkipmanForm(FlaskForm):
    """
    Yeni makine (ekipman) eklemek için kullanılacak form.
    """
    kod = StringField('Makine Kodu', validators=[DataRequired()])
    yakit = StringField('Yakıt Türü', validators=[DataRequired()])
    tipi = StringField('Makine Tipi', validators=[DataRequired()])
    marka = StringField('Makine Markası', validators=[DataRequired()])
    seri_no = StringField('Makine Seri No', validators=[DataRequired()])
    calisma_yuksekligi = StringField('Çalışma Yüksekliği', validators=[DataRequired()]) 
    kaldirma_kapasitesi = StringField('Kaldırma Kapasitesi', validators=[DataRequired()])
    uretim_tarihi = StringField('Üretim Tarihi', validators=[DataRequired()])   
    submit = SubmitField('Kaydet')

class KiralamaForm(FlaskForm):
    """
    Makine kiralama işlemi için kullanılacak form.
    """
    kod = StringField('Makine Kodu', validators=[DataRequired()])
    musteri_adi = StringField('Müşteri Adı', validators=[DataRequired()])
    musteri_iletisim = StringField('Müşteri İletişim Bilgileri', validators=[DataRequired()])
    kiralama_baslangıcı = StringField('Kira Başlangıç Tarihi', validators=[DataRequired()])
    kiralama_bitis = StringField('Kira Bitiş Tarihi', validators=[DataRequired()])
    kiralama_brm_fiyat = StringField('Kira Birim Fiyatı', validators=[DataRequired()])  
    nakliye_fiyat = StringField('Nakliye Fiyatı', validators=[DataRequired()])  
    submit = SubmitField('Kirala')  