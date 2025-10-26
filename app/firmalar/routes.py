from app.firmalar import firmalar_bp
from app import db
from flask import render_template, url_for
from app.models import Ekipman,Musteri
from app.forms import EkipmanForm,FirmaForm
from flask import render_template, redirect, url_for, flash

@firmalar_bp.route('/')
@firmalar_bp.route('/index')
def index():
    """
    Ana Sayfa (Dashboard).
    
    Müşteri listesini gösterir.
    """
    
    musteriler = Musteri.query.all()
    return render_template('firmalar/index.html', musteriler=musteriler)

@firmalar_bp.route('/ekle', methods=['GET', 'POST'])
def ekle():
    """
    Yeni müşteri ekleme formunu gösterir (GET) ve işler (POST).
    """
    form = FirmaForm()
    
    if form.validate_on_submit():
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
    
    return render_template('firmalar/ekle.html', form=form)