from app.kiralama import kiralama_bp
from app.models import Kiralama, Ekipman, Musteri, KiralamaKalemi
from app.forms import KiralamaForm, KiralamaKalemiForm
from flask import render_template, redirect, url_for, flash, jsonify, request
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_
# YENİ IMPORT: 'index' rotasındaki sorguyu hızlandırmak için
from sqlalchemy.orm import joinedload 
from app import db
from datetime import datetime, timezone
from decimal import Decimal
import traceback
import json



@kiralama_bp.app_template_filter('tarihtr')
def tarihtr(value):
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime("%d.%m.%Y")

# --- 1. Kiralama Listeleme Sayfası (YENİ EKLENDİ) ---
# 'Kaydet' butonuna bastıktan sonra buraya yönlendiriliyorsunuz.
@kiralama_bp.route('/index')
@kiralama_bp.route('/') # Blueprint'in ana sayfasını da burası yapalım
def index():
    """
    Tüm kiralama kayıtlarını listeler.
    """
    try:
        # Tüm Kiralama kayıtlarını (ana formları) veritabanından çek.
        # 'joinedload' kullanmak, N+1 sorgu problemini çözer ve sayfayı hızlandırır.
        kiralamalar = Kiralama.query.options(
            joinedload(Kiralama.musteri),       # Müşteri bilgilerini önceden çek
            joinedload(Kiralama.kalemler).joinedload(KiralamaKalemi.ekipman) # Kalemleri ve kalemlerin ekipmanlarını çek
        ).order_by(Kiralama.id.desc()).all()
        
        return render_template('kiralama/index.html', kiralamalar=kiralamalar)

    except Exception as e:
        flash(f"Kiralamalar yüklenirken bir hata oluştu: {str(e)}", "danger")
        traceback.print_exc()
        # Hata olsa bile sayfa yüklensin (boş listeyle)
        return render_template('kiralama/index.html', kiralamalar=[])


# --- 2. Kiralama Ekleme Sayfası (MEVCUT KODUNUZ) ---
    
@kiralama_bp.route('/ekle', methods=['GET', 'POST'])
def ekle():
    form = KiralamaForm()
    
    # 1. Müşteri listesini her zaman doldur
    form.musteri_id.choices = [(m.id, m.firma_adi) for m in Musteri.query.all()]
    
    # 2. 'Bosta' olan tüm ekipmanların listesi
    bosta_ekipmanlar = Ekipman.query.filter_by(calisma_durumu='bosta').order_by(Ekipman.kod).all()
    bosta_choices = [
        (e.id, f"{e.kod} ({e.tipi} / {e.calisma_yuksekligi or 0}m)") 
        for e in bosta_ekipmanlar
    ]
    bosta_choices.insert(0, ('', '--- Ekipman Seçiniz ---'))

    # --- GET ISTEGI (Formu ilk kez gösterme) ---
    if request.method == 'GET':
        
        # --- BLOK 1: FORM NO (TRY...EXCEPT İÇİNDE) ---
        try:
            simdiki_yil = datetime.now(timezone.utc).year
            form_prefix = f'PF-{simdiki_yil}/'
            
            son_kiralama = Kiralama.query.filter(
                Kiralama.kiralama_form_no.like(f"{form_prefix}%")
            ).order_by(Kiralama.id.desc()).first()
            
            yeni_numara = 1
            if son_kiralama and son_kiralama.kiralama_form_no:
                son_numara_parcalari = son_kiralama.kiralama_form_no.split('/')
                if len(son_numara_parcalari) > 1 and son_numara_parcalari[-1].isdigit():
                    son_numara_str = son_numara_parcalari[-1]
                    if son_numara_str: 
                        yeni_numara = int(son_numara_str) + 1
                
            form.kiralama_form_no.data = f'{form_prefix}{yeni_numara}'
        except Exception as e:
            flash(f"Form numarası oluşturulurken hata (kod 1): {e}", "warning")
            simdiki_yil = datetime.now(timezone.utc).year
            form.kiralama_form_no.data = f'PF-{simdiki_yil}/1'
        
        # --- BLOK 2: CHOICES ATAMASI (TRY...EXCEPT DIŞINDA) ---
        try:
            if form.kalemler:
                form.kalemler[0].form.ekipman_id.choices = bosta_choices
        except Exception as e:
            flash(f"Choices atanırken hata (kod 2): {e}", "danger")

    # --- POST ISTEGI (Formu doğrulama/kaydetme) ---
    
    # POST ise (validasyon hatası olsa bile) tüm kalemlerin listesini doldur
    if request.method == 'POST':
        for kalem_form_field in form.kalemler:
            kalem_form_field.form.ekipman_id.choices = bosta_choices

    if form.validate_on_submit():
        # 1. Ana Kiralama formunu oluştur
        yeni_kiralama = Kiralama(
            kiralama_form_no=form.kiralama_form_no.data,
            musteri_id=form.musteri_id.data
        )
        db.session.add(yeni_kiralama) 

        try:
            # 2. Formdan gelen 'kalemler' listesini dolaş
            secilen_ekipman_idler = set()
            
            for kalem_data in form.kalemler.data:
                # coerce=int'i kaldırdığımız için, ID'yi manuel olarak alalım
                try:
                    ekipman_id = int(kalem_data['ekipman_id'])
                except (ValueError, TypeError):
                    continue # Boş ('') veya geçersiz ID'leri atla
                
                if not ekipman_id:
                    continue 
                    
                if ekipman_id in secilen_ekipman_idler:
                    flash(f"Bir ekipmanı (ID: {ekipman_id}) aynı formda birden fazla seçemezsiniz. İşlem iptal edildi.", "danger")
                    db.session.rollback()
                    return redirect(url_for('kiralama.ekle'))
                
                secilen_ekipman = Ekipman.query.get(ekipman_id)
                if not secilen_ekipman or secilen_ekipman.calisma_durumu != 'bosta':
                    flash(f"Seçilen ekipman (ID: {ekipman_id}) kiralanamaz veya bulunamadı. İşlem iptal edildi.", "danger")
                    db.session.rollback()
                    return redirect(url_for('kiralama.ekle'))
                
                # 3. Yeni KiralamaKalemi nesnesini oluştur
                yeni_kalem = KiralamaKalemi(
                    kiralama=yeni_kiralama,
                    ekipman=secilen_ekipman,
                    kiralama_baslangıcı=kalem_data['kiralama_baslangıcı'].strftime("%Y-%m-%d"),
                    kiralama_bitis=kalem_data['kiralama_bitis'].strftime("%Y-%m-%d"),
                    kiralama_brm_fiyat=str(kalem_data['kiralama_brm_fiyat']),
                    nakliye_fiyat=str(kalem_data['nakliye_fiyat'] or 0)
                )
                
                secilen_ekipman.calisma_durumu = "kirada"
                secilen_ekipman_idler.add(ekipman_id)
                db.session.add(yeni_kalem)

            if not secilen_ekipman_idler:
                flash("En az bir geçerli kiralama kalemi eklemelisiniz.", "danger")
                db.session.rollback()
            else:
                db.session.commit()
                flash(f"{len(secilen_ekipman_idler)} kalem başarıyla kiralandı!", "success")
                # BAŞARILI KAYIT SONRASI LİSTELEME SAYFASINA YÖNLENDİR
                return redirect(url_for('kiralama.index')) 

        except Exception as e:
            db.session.rollback()
            flash(f"Veritabanı hatası oluştu: {str(e)}", "danger")
            traceback.print_exc()

    else:
        # Form validasyonu BAŞARISIZ olduysa
        if form.errors:
            for field, errors in form.errors.items():
                if field == 'kalemler':
                    for i, kalem_errors in enumerate(errors):
                        if kalem_errors:
                            for sub_field, sub_errors in kalem_errors.items():
                                flash(f"Satır {i+1} - {sub_field}: {', '.join(sub_errors)}", "danger")
                else:
                    flash(f"Form hatası - {field}: {', '.join(errors)}", "danger")

    # Validasyon hatası durumunda (veya GET isteğinde) 
    # 'choices' listesini (her ihtimale karşı) TEKRAR doldur
    for kalem_form_field in form.kalemler:
        kalem_form_field.form.ekipman_id.choices = bosta_choices
    
    bosta_choices_json = json.dumps(bosta_choices)

    # GET isteği veya Validasyon HATASI durumunda 'ekle.html'yi render et
    return render_template(
        'kiralama/ekle.html', 
        form=form, 
        bosta_choices_json=bosta_choices_json
    )


# --- 3. Ekipman Filtreleme API (MEVCUT KODUNUZ) ---
# (Güncelleme sayfası için saklıyoruz)

@kiralama_bp.route('/api/get-ekipman')
def get_ekipman():
    try:
        tipi = request.args.get('tipi', '', type=str)
        yakit = request.args.get('yakit', '', type=str)
        min_yuksekl = request.args.get('min_yuksekl', 0, type=int) # Hata olmasın diye 'min_yukseklik' olmalı
        min_kapasite = request.args.get('min_kapasite', 0, type=int)
        include_id = request.args.get('include_id', None, type=int)

        query = Ekipman.query.filter(
            and_(
                Ekipman.calisma_durumu == 'bosta',
                Ekipman.calisma_yuksekligi.isnot(None),
                Ekipman.kaldirma_kapasitesi.isnot(None),
                )
        )

        if tipi:
            query = query.filter(Ekipman.tipi.ilike(f"%{tipi}%"))
        if yakit:
            query = query.filter(Ekipman.yakit.ilike(f"%{yakit}%"))
        # ÖNEMLİ: Parametre adını 'min_yukseklik' olarak düzelttim
        if min_yuksekl > 0:
            query = query.filter(Ekipman.calisma_yuksekligi >= min_yuksekl)
        if min_kapasite > 0:
            query = query.filter(Ekipman.kaldirma_kapasitesi >= min_kapasite)

        ekipmanlar = query.all()
        
        bosta_id_seti = {e.id for e in ekipmanlar}

        if include_id and include_id not in bosta_id_seti:
            mevcut_ekipman = Ekipman.query.get(include_id)
            if mevcut_ekipman:
                ekipmanlar.insert(0, mevcut_ekipman)
        
        sonuc = [
            {
                "id": e.id, 
                "kod": f"{e.kod} ({e.tipi} / {e.calisma_yuksekligi or 0}m / {e.kaldirma_kapasitesi or 0}kg)" + 
                       (" (Mevcut Seçim)" if e.id == include_id and e.id not in bosta_id_seti else "") 
            } 
            for e in ekipmanlar
        ]
        
        return jsonify(sonuc)
        
    except Exception as e:
        print(f"API Hatası (get_ekipman): {str(e)}")
        traceback.print_exc()
        return jsonify({"error": str(e), "details": "Sunucu tarafında bir hata oluştu."}), 500
    # app/kiralama/routes.py (veya ekle.py) dosyanıza ekleyin

# ... (diğer import'larınız) ...
# 'traceback' import edilmemişse ekleyin:
import traceback 

# ... (index, ekle, get_ekipman fonksiyonlarınız) ...


# --- 4. KİRALAMA KAYDI SİLME ROTASI (YENİ) ---
@kiralama_bp.route('/sil/<int:kiralama_id>', methods=['POST'])
def sil(kiralama_id):
    """
    Ana kiralama kaydını ve ona bağlı tüm kalemleri siler.
    İlişkili ekipmanların durumunu 'bosta' olarak günceller.
    """
    
    # Not: 'index.html' içinde CSRF token'ı <form> içine eklediğinizden
    # emin olun, yoksa bu rota '400 Bad Request' hatası verir.
    
    # 1. Silinecek ana kiralama kaydını bul
    kiralama = Kiralama.query.get_or_404(kiralama_id)
    
    try:
        # 2. Adım: Bu kiralamaya bağlı TÜM ekipmanları bul
        # ve durumlarını 'bosta' olarak güncelle.
        for kalem in kiralama.kalemler:
            if kalem.ekipman:
                # Ekipmanın durumunu 'bosta' yap
                kalem.ekipman.calisma_durumu = 'bosta'
        
        # 3. Adım: Ana kiralama kaydını sil.
        # models.py'daki 'cascade="all, delete-orphan"' ayarı sayesinde,
        # bu kiralama silindiğinde, ona bağlı TÜM KiralamaKalemi
        # kayıtları da veritabanından otomatik olarak silinecektir.
        db.session.delete(kiralama)
        
        # 4. Adım: Hem ekipman durumlarını hem de silme işlemini onayla.
        db.session.commit()
        
        flash('Kiralama kaydı ve bağlı kalemleri başarıyla silindi.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Kiralama silinirken bir hata oluştu: {str(e)}', 'danger')
        traceback.print_exc() # Hatayı terminale yazdır

    # İşlem başarılı da olsa, hatalı da olsa listeleme sayfasına dön
    return redirect(url_for('kiralama.index'))