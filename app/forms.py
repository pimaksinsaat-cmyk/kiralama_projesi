from flask_wtf import FlaskForm
from wtforms import StringField, DecimalField, SelectField, DateField, SubmitField
from wtforms.validators import DataRequired, Optional

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

class FirmaForm(FlaskForm):
    """
    Yeni firma eklemek için kullanılacak form.
    """
    firma_adi = StringField('Firma Adı', validators=[DataRequired()])
    yetkili_adi = StringField('Yetkili Kişi', validators=[DataRequired()])
    iletisim_bilgileri = StringField('Adres', validators=[DataRequired()])
    vergi_dairesi = StringField('Vergi Dairesi', validators=[DataRequired()])
    vergi_no = StringField('Vergi Numarası', validators=[DataRequired()])  
    submit = SubmitField('Kaydet')



class KiralamaForm(FlaskForm):
    kiralama_form_no = StringField('Kiralama Form No', validators=[Optional()])
    
    # ForeignKey alanları
    ekipman_id = SelectField('Ekipman Seç', coerce=int, validators=[DataRequired()])
    musteri_id = SelectField('Müşteri Seç', coerce=int, validators=[DataRequired()])

    kiralama_baslangıcı = DateField('Kiralama Başlangıç Tarihi', format='%Y-%m-%d', validators=[DataRequired()])
    kiralama_bitis = DateField('Kiralama Bitiş Tarihi', format='%Y-%m-%d', validators=[DataRequired()])
    kiralama_brm_fiyat = DecimalField('Kira Birim Fiyatı', validators=[DataRequired()])
    nakliye_fiyat = DecimalField('Nakliye Fiyatı', validators=[Optional()])

    submit = SubmitField('Kaydet')
