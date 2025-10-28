from app.kiralama import kiralama_bp
from app.models import Kiralama, Ekipman, Musteri
from app.forms import KiralamaForm
from flask import render_template, redirect, url_for, flash
from sqlalchemy.exc import IntegrityError
from app import db
from datetime import datetime

# --- Index ---
@kiralama_bp.route('/index')
def index():
    kiralamalar = Kiralama.query.all()
    for k in kiralamalar:
        try:
            bas = datetime.strptime(k.kiralama_baslangıcı, "%Y-%m-%d")
            bit = datetime.strptime(k.kiralama_bitis, "%Y-%m-%d")
            k.gun_sayisi = (bit - bas).days + 1
        except:
            k.gun_sayisi = None
        try:
            brm = float(k.kiralama_brm_fiyat or 0)
            nak = float(k.nakliye_fiyat or 0)
            k.toplam_fiyat = (k.gun_sayisi or 0) * brm + nak
        except:
            k.toplam_fiyat = 0

    return render_template('kiralama/index.html', kiralamalar=kiralamalar)

# --- Ekle ---
@kiralama_bp.route('/', methods=['GET', 'POST'])
@kiralama_bp.route('/ekle', methods=['GET', 'POST'])
def ekle():
    form = KiralamaForm()

    # Dropdown seçeneklerini doldur
    form.ekipman_id.choices = [(e.id, e.kod) for e in Ekipman.query.filter_by(calisma_durumu='bosta').all()]
    form.musteri_id.choices = [(m.id, m.firma_adi) for m in Musteri.query.all()]

    if form.validate_on_submit():
        secilen_ekipman = Ekipman.query.get(form.ekipman_id.data)
        secilen_musteri = Musteri.query.get(form.musteri_id.data)

        if not (secilen_ekipman and secilen_musteri):
            flash("Geçersiz ekipman veya müşteri seçimi!", "danger")
            return redirect(url_for('kiralama.ekle'))

        yeni_kiralama = Kiralama(
            kiralama_form_no=form.kiralama_form_no.data,
            ekipman_id=secilen_ekipman.id,
            musteri_id=secilen_musteri.id,
            kiralama_baslangıcı=form.kiralama_baslangıcı.data.strftime("%Y-%m-%d"),
            kiralama_bitis=form.kiralama_bitis.data.strftime("%Y-%m-%d"),
            kiralama_brm_fiyat=str(form.kiralama_brm_fiyat.data),
            nakliye_fiyat=str(form.nakliye_fiyat.data)
        )

        try:
            db.session.add(yeni_kiralama)
            secilen_ekipman.calisma_durumu = "kirada"
            db.session.commit()
            flash("Kiralama başarıyla eklendi!", "success")
            return redirect(url_for('kiralama.index'))
        except IntegrityError:
            db.session.rollback()
            flash("Veritabanı hatası oluştu!", "danger")

    else:
        if form.errors:
            print(form.errors)

    return render_template('kiralama/ekle.html', form=form)
