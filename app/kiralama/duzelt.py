from app.kiralama import kiralama_bp
from app.models import Kiralama, Ekipman, Musteri
from app.forms import KiralamaForm
from flask import render_template, redirect, url_for, flash,  request
from app import db
from datetime import datetime
from decimal import Decimal


# --- 6. Kiralama Düzenleme Sayfası (YENİ) ---
@kiralama_bp.route('/duzelt/<int:id>', methods=['GET', 'POST'])
def duzelt(id):
    kiralama = Kiralama.query.get_or_404(id)
    form = KiralamaForm(obj=kiralama)
    
    # Mevcut (eski) ekipman kimliğini sakla
    eski_ekipman_id = kiralama.ekipman_id
    mevcut_ekipman = Ekipman.query.get(eski_ekipman_id)

    # --- Müşteri ve Ekipman Listelerini Doldurma ---
    form.musteri_id.choices = [(m.id, m.firma_adi) for m in Musteri.query.all()]

    # Ekipman listesi (choices) 'ekle' fonksiyonundan farklı yönetilmeli
    # JavaScript'in düzgün çalışması için, 'bosta' olanlar + MEVCUT ekipman listelenmeli
    
    bosta_ekipmanlar = Ekipman.query.filter_by(calisma_durumu='bosta').all()
    choices = [(e.id, e.kod) for e in bosta_ekipmanlar]
    
    # Mevcut kiralanan ekipmanı listeye ekle (eğer 'bosta' listesinde değilse)
    if mevcut_ekipman and mevcut_ekipman.calisma_durumu != 'bosta':
        # (id, text) formatında
        choices.insert(0, (mevcut_ekipman.id, f"{mevcut_ekipman.kod} (Mevcut)"))
    
    # Hem POST hem GET için bu liste geçerli olmalı
    form.ekipman_id.choices = choices
    # --- Bitti ---

    if form.validate_on_submit():
        yeni_ekipman_id = form.ekipman_id.data
        
        # Ekipman değişikliği oldu mu?
        if yeni_ekipman_id != eski_ekipman_id:
            # Eski ekipmanı 'bosta' yap
            eski_ekipman = Ekipman.query.get(eski_ekipman_id)
            if eski_ekipman:
                eski_ekipman.calisma_durumu = 'bosta'
            
            # Yeni ekipmanı 'kirada' yap
            yeni_ekipman = Ekipman.query.get(yeni_ekipman_id)
            if yeni_ekipman:
                yeni_ekipman.calisma_durumu = 'kirada'
            
            kiralama.ekipman_id = yeni_ekipman_id
        
        # Diğer alanları güncelle
        kiralama.musteri_id = form.musteri_id.data
        # kiralama_form_no (readonly) güncellenmez
        
        kiralama.kiralama_baslangıcı = form.kiralama_baslangıcı.data.strftime("%Y-%m-%d")
        kiralama.kiralama_bitis = form.kiralama_bitis.data.strftime("%Y-%m-%d")
        kiralama.kiralama_brm_fiyat = str(form.kiralama_brm_fiyat.data)
        kiralama.nakliye_fiyat = str(form.nakliye_fiyat.data or 0)
        
        try:
            db.session.commit()
            flash('Kiralama bilgileri başarıyla güncellendi!', 'success')
            return redirect(url_for('kiralama.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Güncelleme sırasında hata oluştu: {str(e)}', 'danger')

    elif request.method == 'GET':
        # Formu 'obj' ile doldurmak çoğu alanı doldurur,
        # ancak String (model) -> Date/Decimal (form) dönüşümleri için manuel atama gerekir
        
        try:
            form.kiralama_baslangıcı.data = datetime.strptime(kiralama.kiralama_baslangıcı, "%Y-%m-%d")
            form.kiralama_bitis.data = datetime.strptime(kiralama.kiralama_bitis, "%Y-%m-%d")
            form.kiralama_brm_fiyat.data = Decimal(kiralama.kiralama_brm_fiyat or 0)
            form.nakliye_fiyat.data = Decimal(kiralama.nakliye_fiyat or 0)
        except Exception as e:
             flash(f"Form verileri yüklenirken hata (örn: bozuk tarih): {e}", "warning")

        # Seçili olan değerleri ata (form.ekipman_id.choices'i yukarıda doldurduk)
        form.musteri_id.data = kiralama.musteri_id
        form.ekipman_id.data = kiralama.ekipman_id
        
        # Filtre alanlarını mevcut ekipmanın özellikleriyle doldur
        if mevcut_ekipman:
            form.ekipman_tipi.data = mevcut_ekipman.tipi
            form.ekipman_yakit.data = mevcut_ekipman.yakit
            form.min_yukseklik.data = mevcut_ekipman.calisma_yuksekligi
            form.min_kapasite.data = mevcut_ekipman.kaldirma_kapasitesi

    # Formda hata varsa (hem GET'te yüklenirken hem POST'ta validasyon)
    if form.errors:
        for field, errors in form.errors.items():
            for error in errors:
                print(f"Hata Alanı: {field}, Hata: {error}")
                flash(f"Form hatası - {field}: {error}", "danger")

    return render_template('kiralama/duzelt.html', form=form, kiralama=kiralama)