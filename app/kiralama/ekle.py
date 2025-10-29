from app.kiralama import kiralama_bp
from app.models import Kiralama, Ekipman, Musteri
from app.forms import KiralamaForm
from flask import render_template, redirect, url_for, flash, jsonify, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
from app import db
from datetime import datetime, timezone
from decimal import Decimal
import traceback

# --- 2. Kiralama Ekleme Sayfası ---

    
@kiralama_bp.route('/', methods=['GET', 'POST'])
@kiralama_bp.route('/ekle', methods=['GET', 'POST'])
def ekle():
    form = KiralamaForm()

    form.musteri_id.choices = [(m.id, m.firma_adi) for m in Musteri.query.all()]
    
    # Otomatik Form Numarası Oluşturma
    if request.method == 'GET':
        try:
            # O yıla ait son kaydı bul
            simdiki_yil = datetime.now(timezone.utc).year
            form_prefix = f'PF-{simdiki_yil}/'
            
            son_kiralama = Kiralama.query.filter(
                Kiralama.kiralama_form_no.like(f"{form_prefix}%")
            ).order_by(Kiralama.id.desc()).first()
            
            yeni_numara = 1
            if son_kiralama:
                son_numara_str = son_kiralama.kiralama_form_no.split('/')[-1]
                yeni_numara = int(son_numara_str) + 1
                
            form.kiralama_form_no.data = f'{form_prefix}{yeni_numara}'
        except Exception as e:
            flash(f"Form numarası oluşturulurken hata: {e}", "warning")
            form.kiralama_form_no.data = f'PF-{simdiki_yil}/1' # Hata olursa başa dön

    if request.method == 'POST':
        # Validasyonun "Not a valid choice" hatası vermemesi için
        # tüm 'bosta' ekipmanları choices'e ekliyoruz.
        form.ekipman_id.choices = [(e.id, e.kod) for e in Ekipman.query.filter_by(calisma_durumu='bosta').all()]
    else:
        # GET isteğinde liste boş başlasın, JS dolduracak
        form.ekipman_id.choices = []

    if form.validate_on_submit():
        secilen_ekipman = Ekipman.query.get(form.ekipman_id.data)
        secilen_musteri = Musteri.query.get(form.musteri_id.data)

        if not (secilen_ekipman and secilen_musteri):
            flash("Geçersiz ekipman veya müşteri seçimi!", "danger")
            return redirect(url_for('kiralama.ekle'))
            
        if secilen_ekipman.calisma_durumu != 'bosta':
            flash(f"{secilen_ekipman.kod} kodlu ekipman şu anda kirada!", "danger")
            return redirect(url_for('kiralama.ekle'))

        yeni_kiralama = Kiralama(
            kiralama_form_no=form.kiralama_form_no.data,
            ekipman_id=secilen_ekipman.id,
            musteri_id=secilen_musteri.id,
            kiralama_baslangıcı=form.kiralama_baslangıcı.data.strftime("%Y-%m-%d"),
            kiralama_bitis=form.kiralama_bitis.data.strftime("%Y-%m-%d"),
            kiralama_brm_fiyat=str(form.kiralama_brm_fiyat.data),
            nakliye_fiyat=str(form.nakliye_fiyat.data or 0)
        )

        try:
            db.session.add(yeni_kiralama)
            secilen_ekipman.calisma_durumu = "kirada"
            db.session.commit()
            flash("Kiralama başarıyla eklendi!", "success")
            return redirect(url_for('kiralama.index'))
        except Exception as e:
            db.session.rollback()
            flash(f"Veritabanı hatası oluştu: {str(e)}", "danger")

    else:
        if form.errors:
            # Form hatalarını daha detaylı yazdır
            for field, errors in form.errors.items():
                for error in errors:
                    print(f"Hata Alanı: {field}, Hata: {error}")
                    flash(f"Form hatası - {field}: {error}", "danger")

    return render_template('kiralama/ekle.html', form=form)

