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

# --- 1. Index (Liste) Sayfası ---
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

# --- 3. Kiralama Silme İşlemi ---
@kiralama_bp.route('/sil/<int:id>', methods=['POST'])
def sil(id):
    # CSRF koruması Flask-WTF tarafından otomatik yönetilir (eğer formda token varsa)
    # Token, index.html'deki formda manuel olarak eklendi.
    
    kiralama = Kiralama.query.get_or_404(id)
    ekipman = kiralama.ekipman # Silmeden önce ekipmanı al
    
    try:
        db.session.delete(kiralama)
        
        # Eğer bu kiralama ekipmanın son durumuysa, ekipmanı 'bosta' yap
        # Daha karmaşık bir mantık (örn: başka kiralaması var mı) gerekebilir
        # Şimdilik basitçe 'bosta' yapıyoruz:
        if ekipman and ekipman.calisma_durumu == 'kirada':
            # Bu ekipmanın başka aktif kiralaması olup olmadığını kontrol et
            baska_kiralama = Kiralama.query.filter(
                Kiralama.ekipman_id == ekipman.id,
                Kiralama.id != id # Kendisi hariç
            ).first() # (Daha karmaşık bir tarih kontrolü gerekebilir)
            
            if not baska_kiralama:
                ekipman.calisma_durumu = 'bosta'
        
        db.session.commit()
        flash("Kiralama kaydı başarıyla silindi.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Silme sırasında hata oluştu: {str(e)}", "danger")
        
    return redirect(url_for('kiralama.index'))

# --- 4. API (Ekipman Filtreleme) ---
@kiralama_bp.route('/api/get-ekipman')
def get_ekipman():
    try:
        tipi = request.args.get('ekipman_tipi', '', type=str)
        yakit = request.args.get('ekipman_yakit', '', type=str)
        min_yukseklik = request.args.get('min_yukseklik', 0, type=int)
        min_kapasite = request.args.get('min_kapasite', 0, type=int)

        query = Ekipman.query.filter(
            and_(
                Ekipman.calisma_durumu == 'bosta',
                Ekipman.calisma_yuksekligi.isnot(None),
                Ekipman.kaldirma_kapasitesi.isnot(None)
            )
        )

        if tipi:
            query = query.filter(Ekipman.tipi.ilike(f"%{tipi}%"))
        if yakit:
            query = query.filter(Ekipman.yakit.ilike(f"%{yakit}%"))
        if min_yukseklik > 0:
            query = query.filter(Ekipman.calisma_yuksekligi >= min_yukseklik)
        if min_kapasite > 0:
            query = query.filter(Ekipman.kaldirma_kapasitesi >= min_kapasite)

        ekipmanlar = query.all()

        sonuc = [
            {
                "id": e.id, 
                "kod": f"{e.kod} ({e.tipi} / {e.calisma_yuksekligi or 0}m / {e.kaldirma_kapasitesi or 0}kg)"
            } 
            for e in ekipmanlar
        ]
        
        return jsonify(sonuc)
        
    except Exception as e:
        return jsonify({"error": str(e), "details": "Sunucu tarafında bir hata oluştu."}), 500
# --- 5. Kiralama Bilgi Sayfası ---
@kiralama_bp.route('/bilgi/<int:id>', methods=['GET', 'POST'])
def bilgi(id):
    """
    ID'si verilen müşterinin detaylı bilgilerini gösterir.
    """
    kiralama = Kiralama.query.get_or_404(id)
   
    
    return render_template('kiralama/bilgi.html', kiralama=kiralama)

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

