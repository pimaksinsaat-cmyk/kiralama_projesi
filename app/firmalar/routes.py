from app.firmalar import firmalar_bp
from app import db
from flask import render_template, url_for
from app.models import Ekipman,Musteri
from app.forms import EkipmanForm,FirmaForm
from flask import render_template, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError
# --- 1. Müşteri Listeleme Sayfası ---
@firmalar_bp.route('/')
@firmalar_bp.route('/index')
def index():
    """
    Ana Sayfa (Dashboard).
    
    Müşteri listesini gösterir.
    """
   
    musteriler = Musteri.query.all()
    return render_template('firmalar/index.html', musteriler=musteriler)
# --- 2. Yeni MakMüşteri Ekleme Sayfası (Form) --- 
@firmalar_bp.route('/ekle', methods=['GET', 'POST'])
def ekle():
    """
    Yeni müşteri ekleme formunu gösterir (GET) ve işler (POST).
    """
    form = FirmaForm()
    
    if form.validate_on_submit():
        try:
            yeni_musteri = Musteri(
            firma_adi=form.firma_adi.data,
            yetkili_adi=form.yetkili_adi.data,
            iletisim_bilgileri=form.iletisim_bilgileri.data,
            vergi_dairesi=form.vergi_dairesi.data,
            vergi_no=form.vergi_no.data
            )
        
            db.session.add(yeni_musteri)
            db.session.commit()
        
            flash('Yeni müşteri başarıyla eklendi!', 'success')
            return redirect(url_for('firmalar.index'))
        except IntegrityError as e:

            db.session.rollback()   

            flash(f'HATA: Girdiğiniz vergi numarası {form.vergi_no.data} zaten sistemde kayıtlı. Lütfen kontrol edin.', 'danger')

    return render_template('firmalar/ekle.html', form=form)
# --- 3.Müşteri silme işlermi ---
@firmalar_bp.route('/sil/<int:id>', methods=['POST'])
def sil(id):
    """
    ID'si verilen müşteriyi siler.
    """
    musteri = Musteri.query.get_or_404(id)
    
    db.session.delete(musteri)
    db.session.commit()
    
    flash('Müşteri başarıyla silindi!', 'success')
    
    return redirect(url_for('firmalar.index'))  
# --- 4. Müşteri Düzenleme Sayfası (Form) ---
@firmalar_bp.route('/duzelt/<int:id>', methods=['GET', 'POST'])
def duzelt(id):
    """
    Mevcut müşteriyi düzenleme formunu gösterir (GET) ve işler (POST).
    """
    musteri = Musteri.query.get_or_404(id)
    form = FirmaForm(obj=musteri)
    
    if form.validate_on_submit():
        musteri.firma_adi = form.firma_adi.data
        musteri.yetkili_adi = form.yetkili_adi.data
        musteri.iletisim_bilgileri = form.iletisim_bilgileri.data
        musteri.vergi_dairesi = form.vergi_dairesi.data
        musteri.vergi_no = form.vergi_no.data
        
        db.session.commit()
        
        flash('Müşteri bilgileri başarıyla güncellendi!', 'success')
        
        return redirect(url_for('firmalar.index'))
    
    return render_template('firmalar/duzelt.html', form=form, musteri=musteri) 