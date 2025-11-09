# --- 1. GEREKLİ TÜM IMPORTLAR ---
import json
import traceback
from datetime import datetime, timezone, date
from decimal import Decimal

from flask import render_template, redirect, url_for, flash, jsonify, request
from sqlalchemy import and_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import joinedload 

from app import db
from app.kiralama import kiralama_bp
from app.models import Kiralama, Ekipman, Musteri, KiralamaKalemi
from app.forms import KiralamaForm, KiralamaKalemiForm 

# --- 2. JINJA2 FİLTRESİ (Tarih Formatlama) ---
@kiralama_bp.app_template_filter('tarihtr')
def tarihtr(value):
    """ Gelen tarih objesini veya string'i GG.AA.YYYY formatına çevirir. """
    if not value:
        return ""
    if isinstance(value, (datetime, date)):
         return value.strftime("%d.%m.%Y")
    if isinstance(value, str):
        try:
            value_dt = datetime.strptime(value, '%Y-%m-%d').date()
            return value_dt.strftime("%d.%m.%Y")
        except ValueError:
            return value
    return value


# --- 3. KİRALAMA LİSTELEME (ANA SAYFA) ---
@kiralama_bp.route('/index')
@kiralama_bp.route('/') 
def index():
    """ Tüm kiralama kayıtlarını listeler. """
    try:
        kiralamalar = Kiralama.query.options(
            joinedload(Kiralama.musteri),       
            joinedload(Kiralama.kalemler).joinedload(KiralamaKalemi.ekipman)
        ).order_by(Kiralama.id.desc()).all()
        
        return render_template('kiralama/index.html', kiralamalar=kiralamalar)

    except Exception as e:
        flash(f"Kiralamalar yüklenirken bir hata oluştu: {str(e)}", "danger")
        traceback.print_exc()
        return render_template('kiralama/index.html', kiralamalar=[])


# --- 4. YENİ KİRALAMA EKLEME ---
@kiralama_bp.route('/ekle', methods=['GET', 'POST'])
def ekle():
    """ Yeni kiralama kaydı oluşturur. """
    form = KiralamaForm()
    
    form.musteri_id.choices = [(m.id, m.firma_adi) for m in Musteri.query.all()]
    
    bosta_ekipmanlar = Ekipman.query.filter_by(calisma_durumu='bosta').order_by(Ekipman.kod).all()
    bosta_choices = [
        (e.id, f"{e.kod} ({e.tipi} / {e.calisma_yuksekligi or 0}m)") 
        for e in bosta_ekipmanlar
    ]
    bosta_choices.insert(0, ('', '--- Ekipman Seçiniz ---'))

    if request.method == 'GET':
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
            flash(f"Form numarası oluşturulurken hata: {e}", "warning")
            simdiki_yil = datetime.now(timezone.utc).year
            form.kiralama_form_no.data = f'PF-{simdiki_yil}/1'
        
        try:
            if form.kalemler:
                form.kalemler[0].form.ekipman_id.choices = bosta_choices
        except Exception as e:
            flash(f"Choices atanırken hata: {e}", "danger")

    if request.method == 'POST':
        for kalem_form_field in form.kalemler:
            kalem_form_field.form.ekipman_id.choices = bosta_choices

    if form.validate_on_submit():
        yeni_kiralama = Kiralama(
            kiralama_form_no=form.kiralama_form_no.data,
            musteri_id=form.musteri_id.data
        )
        db.session.add(yeni_kiralama) 

        try:
            secilen_ekipman_idler = set()
            
            for kalem_data in form.kalemler.data:
                try:
                    ekipman_id = int(kalem_data['ekipman_id'])
                except (ValueError, TypeError):
                    continue 
                
                if not ekipman_id:
                    continue 
                    
                if ekipman_id in secilen_ekipman_idler:
                    flash(f"Ekipmanı (ID: {ekipman_id}) aynı formda birden fazla seçemezsiniz. İşlem iptal.", "danger")
                    db.session.rollback()
                    return redirect(url_for('kiralama.ekle'))
                
                secilen_ekipman = Ekipman.query.get(ekipman_id)
                if not secilen_ekipman or secilen_ekipman.calisma_durumu != 'bosta':
                    flash(f"Ekipman (ID: {ekipman_id}) kiralanamaz veya bulunamadı. İşlem iptal.", "danger")
                    db.session.rollback()
                    return redirect(url_for('kiralama.ekle'))
                
                baslangic_str = kalem_data['kiralama_baslangıcı'].strftime("%Y-%m-%d") if kalem_data['kiralama_baslangıcı'] else None
                bitis_str = kalem_data['kiralama_bitis'].strftime("%Y-%m-%d") if kalem_data['kiralama_bitis'] else None
                
                yeni_kalem = KiralamaKalemi(
                    kiralama=yeni_kiralama,
                    ekipman=secilen_ekipman,
                    kiralama_baslangıcı=baslangic_str,
                    kiralama_bitis=bitis_str,
                    kiralama_brm_fiyat=str(kalem_data['kiralama_brm_fiyat'] or 0),
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
                return redirect(url_for('kiralama.index')) 

        except Exception as e:
            db.session.rollback()
            flash(f"Veritabanı hatası oluştu: {str(e)}", "danger")
            traceback.print_exc()

    else:
        if request.method == 'POST' and form.errors:
            flash("Formda hatalar var, lütfen kontrol edin.", "warning")
            for field, errors in form.errors.items():
                if field == 'kalemler':
                    for i, kalem_errors in enumerate(errors):
                        if kalem_errors:
                            for sub_field, sub_errors in kalem_errors.items():
                                flash(f"Satır {i+1} - {sub_field}: {', '.join(sub_errors)}", "danger")
                # else:
                #     flash(f"Form hatası - {field}: {', '.join(errors)}", "danger")

    bosta_choices_json = json.dumps(bosta_choices)

    return render_template(
        'kiralama/ekle.html', 
        form=form, 
        bosta_choices_json=bosta_choices_json
    )


# --- 5. KİRALAMA KAYDI DÜZENLEME ---
@kiralama_bp.route('/duzenle/<int:kiralama_id>', methods=['GET', 'POST'])
def duzenle(kiralama_id):
    """ Mevcut bir kiralama kaydını (ana form ve kalemleri) düzenler. """
    
    kiralama = Kiralama.query.options(
        joinedload(Kiralama.kalemler)
    ).get_or_404(kiralama_id)

    form = KiralamaForm(obj=kiralama)

    # --- DÜZELTME 1: "Choices cannot be None" HATASI İÇİN ---
    # 'musteri_id' SelectField'inin 'choices' listesi 'POST' isteğinde de dolu olmalı.
    form.musteri_id.choices = [(m.id, m.firma_adi) for m in Musteri.query.all()]

    # --- DÜZELTME 2: "Formda Hatalar Var (Müşteri)" HATASI İÇİN ---
    # 'musteri_id' alanı 'disabled' olduğu için forma gönderilmiyor.
    # 'DataRequired' doğrulamasını geçmesi için bu alandaki doğrulamaları kaldırıyoruz.
    form.musteri_id.validators = []

    # --- DÜZELTME 3: "Formda Hatalar Var (Ekipman)" HATASI İÇİN ---
    # 'ekipman_id' SelectField'lerinin 'choices' listesi 'POST' isteğinde de dolu olmalı.
    # Bu blok 'validate_on_submit'ten ÖNCE çalışmalı.
    
    # 3a. 'Bosta' olan tüm ekipmanları al
    bosta_ekipmanlar = Ekipman.query.filter_by(calisma_durumu='bosta').order_by(Ekipman.kod).all()
    bosta_choices = [
        (e.id, f"{e.kod} ({e.tipi} / {e.calisma_yuksekligi or 0}m)") 
        for e in bosta_ekipmanlar
    ]
    bosta_id_seti = {e.id for e in bosta_ekipmanlar}

    # 3b. 'Bosta' listesine bu formdaki mevcut seçili (kirada olan) ekipmanları ekle
    full_choices = list(bosta_choices) 
    for kalem in kiralama.kalemler:
        if kalem.ekipman_id not in bosta_id_seti:
            e = kalem.ekipman 
            if e:
                label = f"{e.kod} ({e.tipi} / {e.calisma_yuksekligi or 0}m) (MEVCUT SEÇİM)"
                full_choices.append((e.id, label))

    full_choices.insert(0, ('', '--- Ekipman Seçiniz ---'))

    # 3c. 'choices' listesini formdaki tüm kalemlere ata
    for kalem_form_field in form.kalemler:
        kalem_form_field.form.ekipman_id.choices = full_choices

    # 3d. JS için JSON listesini hazırla
    bosta_choices_json = json.dumps(full_choices)
    # --- DÜZELTME 3 SONU ---


    # --- DÜZELTME (GET ISTEGI - VERI DÖNÜŞTÜRME) ---
    # Form yüklenirken (GET) veritabanındaki 'String' verileri 
    # form alanlarının beklediği 'Date' ve 'Decimal' objelerine çeviriyoruz.
    if request.method == 'GET':
        for kalem_form in form.kalemler:
            try:
                # 1. TARİH ALANLARI
                data_str = kalem_form.kiralama_baslangıcı.data
                if isinstance(data_str, str) and data_str:
                    kalem_form.kiralama_baslangıcı.data = datetime.strptime(data_str, '%Y-%m-%d').date()
                else:
                    kalem_form.kiralama_baslangıcı.data = None

                data_str = kalem_form.kiralama_bitis.data
                if isinstance(data_str, str) and data_str:
                    kalem_form.kiralama_bitis.data = datetime.strptime(data_str, '%Y-%m-%d').date()
                else:
                    kalem_form.kiralama_bitis.data = None

                # 2. FİYAT ALANLARI
                data_str = kalem_form.kiralama_brm_fiyat.data
                if isinstance(data_str, str) and data_str:
                    kalem_form.kiralama_brm_fiyat.data = Decimal(data_str)
                else:
                    kalem_form.kiralama_brm_fiyat.data = None

                data_str = kalem_form.nakliye_fiyat.data
                if isinstance(data_str, str) and data_str:
                    kalem_form.nakliye_fiyat.data = Decimal(data_str)
                else:
                    kalem_form.nakliye_fiyat.data = None
            
            except Exception as e:
                print(f"Düzeltme formu GET veri dönüştürme hatası: {e}")
                kalem_form.kiralama_baslangıcı.data = None
                kalem_form.kiralama_bitis.data = None
                kalem_form.kiralama_brm_fiyat.data = None
                kalem_form.nakliye_fiyat.data = None
    # --- GET VERİ DÖNÜŞTÜRME KODU SONU ---


    # --- POST ISTEGI (Formu kaydetme) ---
    # 'choices' listeleri ve 'validators' Düzeltme 1, 2, 3 sayesinde 
    # artık 'validate_on_submit' için hazır.
    if form.validate_on_submit():
        
        original_ekipman_ids = {kalem.ekipman_id for kalem in kiralama.kalemler if kalem.ekipman_id}

        try:
            # Not: kiralama.musteri_id'yi GÜNCELLEMİYORUZ ('disabled' yaptık).
            
            new_ekipman_ids = set()
            new_kalemler_data = [] 
            
            for kalem_data in form.kalemler.data:
                try:
                    ekipman_id = int(kalem_data['ekipman_id'])
                    if ekipman_id:
                        new_ekipman_ids.add(ekipman_id)
                        new_kalemler_data.append(kalem_data)
                except (ValueError, TypeError):
                    continue 
            
            ids_to_make_bosta = original_ekipman_ids - new_ekipman_ids
            ids_to_make_kirada = new_ekipman_ids - original_ekipman_ids

            if ids_to_make_bosta:
                Ekipman.query.filter(Ekipman.id.in_(ids_to_make_bosta)).update(
                    {'calisma_durumu': 'bosta'}, synchronize_session=False
                )
                
            if ids_to_make_kirada:
                yeni_kiralananlar = Ekipman.query.filter(
                    Ekipman.id.in_(ids_to_make_kirada), 
                    Ekipman.calisma_durumu == 'bosta'
                ).all()
                
                if len(yeni_kiralananlar) != len(ids_to_make_kirada):
                    raise Exception(f"Seçilen ekipmanlardan bazıları 'bosta' değil. İşlem iptal.")
                
                for ekip in yeni_kiralananlar:
                    ekip.calisma_durumu = 'kirada'

            kiralama.kalemler.clear() 
            db.session.flush() 
            
            for kalem_data in new_kalemler_data:
                
                baslangic_str = kalem_data['kiralama_baslangıcı'].strftime("%Y-%m-%d") if kalem_data['kiralama_baslangıcı'] else None
                bitis_str = kalem_data['kiralama_bitis'].strftime("%Y-%m-%d") if kalem_data['kiralama_bitis'] else None
                brm_fiyat_str = str(kalem_data['kiralama_brm_fiyat'] or 0)
                nakliye_fiyat_str = str(kalem_data['nakliye_fiyat'] or 0)
                
                yeni_kalem = KiralamaKalemi(
                    ekipman_id=int(kalem_data['ekipman_id']),
                    kiralama_baslangıcı=baslangic_str,
                    kiralama_bitis=bitis_str,
                    kiralama_brm_fiyat=brm_fiyat_str,
                    nakliye_fiyat=nakliye_fiyat_str
                )
                kiralama.kalemler.append(yeni_kalem)

            db.session.commit()
            flash('Kiralama kaydı başarıyla güncellendi.', 'success')
            return redirect(url_for('kiralama.index'))

        except Exception as e:
            db.session.rollback()
            flash(f"Güncelleme sırasında bir veritabanı hatası oluştu: {str(e)}", "danger")
            traceback.print_exc()

    elif request.method == 'POST' and form.errors:
        flash("Formda hatalar var. Lütfen kontrol ediniz.", "danger")
        # Hataların detayını terminalde görmek için:
        print("Form Validasyon Hataları:", form.errors) 
        
    # --- GET ISTEGI (veya POST'ta hata varsa) ---
    return render_template(
        'kiralama/duzelt.html', 
        form=form, 
        kiralama=kiralama, 
        bosta_choices_json=bosta_choices_json
    )


# --- 6. KİRALAMA KAYDI SİLME ---
@kiralama_bp.route('/sil/<int:kiralama_id>', methods=['POST'])
def sil(kiralama_id):
    """
    Ana kiralama kaydını ve ona bağlı tüm kalemleri siler.
    İlişkili ekipmanların durumunu 'bosta' olarak günceller.
    """
    kiralama = Kiralama.query.get_or_404(kiralama_id)
    
    try:
        for kalem in kiralama.kalemler:
            if kalem.ekipman:
                kalem.ekipman.calisma_durumu = 'bosta'
        
        db.session.delete(kiralama)
        db.session.commit()
        
        flash('Kiralama kaydı ve bağlı kalemleri başarıyla silindi.', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Kiralama silinirken bir hata oluştu: {str(e)}', 'danger')
        traceback.print_exc() 

    return redirect(url_for('kiralama.index'))


# --- 7. EKİPMAN FİLTRELEME API (JS için) ---
@kiralama_bp.route('/api/get-ekipman')
def get_ekipman():
    """ Ekipmanları filtrelemek için JSON verisi sağlar. """
    try:
        tipi = request.args.get('tipi', '', type=str)
        yakit = request.args.get('yakit', '', type=str)
        min_yukseklik = request.args.get('min_yukseklik', 0, type=int) 
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
        if min_yukseklik > 0:
            query = query.filter(Ekipman.calisma_yuksekligi >= min_yukseklik)
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