from app.kiralama import kiralama_bp
from app.models import Kiralama, Ekipman, Musteri
from app.forms import KiralamaForm, EkipmanForm, FirmaForm
from flask import render_template, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError
from app import db 
from datetime import datetime
# 1.index route
@kiralama_bp.route('/index')
def index():
    """
    Ana Sayfa (Dashboard).
    
    Kiralama listesini gösterir.
    """
   
    kiralamalar = Kiralama.query.all()
    for kiralama in kiralamalar:
        try:
            # Tarihleri datetime'a çevir
            baslangic = datetime.strptime(kiralama.kiralama_baslangıcı, "%Y-%m-%d")
            bitis = datetime.strptime(kiralama.kiralama_bitis, "%Y-%m-%d")

            # Gün farkını hesapla
            kiralama.gun_sayisi = (bitis - baslangic).days+1

        except Exception:
            kiralama.gun_sayisi = None  # Eksik veya hatalı tarih varsa

        try:
            # Fiyatları güvenli şekilde float’a dönüştür
            brm_fiyat = float(kiralama.kiralama_brm_fiyat or 0)
            nakliye = float(kiralama.nakliye_fiyat or 0)

            # Toplam fiyat = (gün sayısı * birim fiyat) + nakliye
            kiralama.toplam_fiyat = kiralama.gun_sayisi * brm_fiyat + nakliye

        except Exception:
            kiralama.toplam_fiyat = 0 


    return render_template('kiralama/index.html', kiralamalar=kiralamalar)

# 2. Kiralama Ekleme Sayfası (Form)
@kiralama_bp.route('/', methods=['GET', 'POST'])
@kiralama_bp.route('/ekle', methods=['GET', 'POST'])
def ekle():
    """
    Kiralama ekleme sayfası.
    """
    form = KiralamaForm()  # Form nesnesi oluşturuluyor

    # Form POST edildiğinde ve doğrulama başarılıysa
    if form.validate_on_submit():
        yeni_kiralama = Kiralama(
            kiralama_form_no=form.kiralama_form_no.data,
            kod=form.kod.data,
            musteri_adi=form.musteri_adi.data,
            musteri_iletisim=form.musteri_iletisim.data,
            kiralama_baslangıcı=form.kiralama_baslangıcı.data,
            kiralama_bitis=form.kiralama_bitis.data,
            kiralama_brm_fiyat=form.kiralama_brm_fiyat.data,
            nakliye_fiyat=form.nakliye_fiyat.data
        )

        db.session.add(yeni_kiralama)
        db.session.commit()

       
        flash('Kiralama işlemi başarıyla eklendi!', 'success')
    
        return redirect(url_for('kiralama.index'))
         
    return render_template('kiralama/ekle.html', form=form)
