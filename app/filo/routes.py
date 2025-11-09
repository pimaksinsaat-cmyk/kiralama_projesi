from app.filo import filo_bp
from app import db 
# YENİ MODELLER: Artık KiralamaKalemi'ni de sorgulamamız gerekiyor
from app.models import Ekipman, Musteri, Kiralama, KiralamaKalemi
from app.forms import EkipmanForm 
from flask import render_template, redirect, url_for, flash, request
from datetime import datetime
# YENİ IMPORT: 'index' rotasındaki sorguları hızlandırmak için
from sqlalchemy.orm import joinedload, subqueryload

# --- 1. Makine Parkı Listeleme Sayfası (DÜZELTİLDİ) ---
@filo_bp.route('/')
@filo_bp.route('/index')
def index():
    """
    Tüm makine parkını listeler.
    Yeni 'KiralamaKalemi' modeline göre sorgulama yapar.
    """
    try:
        # Ekipmanları çekerken, ilişkili 'kalemleri', 
        # kalemlerin 'kiralama' başlığını ve kiralama başlığının 'musteri'sini
        # önceden yükle (Eager Loading) -> Sayfayı aşırı hızlandırır.
        ekipmanlar = Ekipman.query.options(
            subqueryload(Ekipman.kiralama_kalemleri).options(
                joinedload(KiralamaKalemi.kiralama).joinedload(Kiralama.musteri)
            )
        ).order_by(Ekipman.kod).all()
        
        # Kirada olan ekipmanların bilgilerini bul
        for ekipman in ekipmanlar:
            ekipman.aktif_kiralama_bilgisi = None # Varsayılan değer
            if ekipman.calisma_durumu == 'kirada':
                # Ekipmana ait son (aktif) kiralama kalemini bul
                # (KiralamaKalemi.id'ye göre sıralıyoruz)
                aktif_kalem = KiralamaKalemi.query.filter_by(
                    ekipman_id=ekipman.id
                ).order_by(KiralamaKalemi.id.desc()).first()
                
                if aktif_kalem:
                    # ekipman nesnesine geçici bir özellik olarak ekle
                    ekipman.aktif_kiralama_bilgisi = aktif_kalem
                # else: Veri tutarsızlığı var (kirada ama kalem yok)
    
    except Exception as e:
        flash(f"Ekipmanlar yüklenirken bir hata oluştu: {str(e)}", "danger")
        ekipmanlar = []

    return render_template('filo/index.html', ekipmanlar=ekipmanlar)

# --- 2. Yeni Makine Ekleme Sayfası (Form) (DÜZELTİLDİ) ---
@filo_bp.route('/ekle', methods=['GET', 'POST'])
def ekle():
    form = EkipmanForm()
    
    # 'son_kod' mantığı, yeni kayıt yoksa hata verir.
    # Düzeltilmiş hali:
    try:
        son_ekipman = Ekipman.query.order_by(Ekipman.id.desc()).first()
        son_kod = son_ekipman.kod if son_ekipman else 'Henüz kayıt yok'
    except Exception:
        son_kod = 'Veritabanı hatası'

    if form.validate_on_submit():
        try:
            # DÜZELTME: Formdan gelen String verileri Integer'a çevir
            # (models.py'da bu alanlar Integer)
            yeni_ekipman = Ekipman(
                kod=form.kod.data,
                yakit=form.yakit.data,
                tipi=form.tipi.data,
                marka=form.marka.data,
                seri_no=form.seri_no.data,
                calisma_yuksekligi=int(form.calisma_yuksekligi.data),
                kaldirma_kapasitesi=int(form.kaldirma_kapasitesi.data), 
                uretim_tarihi=form.uretim_tarihi.data
            )
            
            db.session.add(yeni_ekipman)
            db.session.commit()
            flash('Yeni makine başarıyla eklendi!', 'success')
            return redirect(url_for('filo.index'))
            
        except ValueError:
            # int() çevrimi başarısız olursa (örn: "abc" veya "10.5" girilirse)
            flash("Hata: Yükseklik ve Kapasite alanları sayısal (tamsayı) olmalıdır.", "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Kaydederken bir hata oluştu: {str(e)}", "danger")
    
    return render_template('filo/ekle.html', form=form, son_kod=son_kod)

# --- 3. Makine Silme İşlemi (Bu kod doğru, değişiklik yok) ---
@filo_bp.route('/sil/<int:id>', methods=['POST'])
def sil(id):
    ekipman = Ekipman.query.get_or_404(id)
    if ekipman.calisma_durumu == 'kirada':
        flash('Kirada olan bir ekipman silinemez! Önce kirayı sonlandırın.', 'danger')
        return redirect(url_for('filo.index'))
    try:
        db.session.delete(ekipman)
        db.session.commit()
        flash('Makine başarıyla silindi.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ekipman silinirken bir hata oluştu: {str(e)}', 'danger')
    
    return redirect(url_for('filo.index'))

# --- 4. Makine Düzeltme Sayfası (DÜZELTİLDİ) ---
@filo_bp.route('/duzelt/<int:id>', methods=['GET', 'POST'])
def duzelt(id):
    ekipman = Ekipman.query.get_or_404(id)
    form = EkipmanForm(obj=ekipman)
    
    if form.validate_on_submit():
        try:
            ekipman.marka = form.marka.data
            ekipman.yakit = form.yakit.data
            ekipman.tipi = form.tipi.data
            ekipman.kod = form.kod.data
            ekipman.seri_no = form.seri_no.data
            
            # DÜZELTME: Formdan gelen String verileri Integer'a çevir
            ekipman.calisma_yuksekligi = int(form.calisma_yuksekligi.data)
            ekipman.kaldirma_kapasitesi = int(form.kaldirma_kapasitesi.data)
            ekipman.uretim_tarihi = form.uretim_tarihi.data
            
            db.session.commit()
            flash('Makine bilgileri başarıyla güncellendi!', 'success')
            return redirect(url_for('filo.index'))
            
        except ValueError:
            flash("Hata: Yükseklik ve Kapasite alanları sayısal (tamsayı) olmalıdır.", "danger")
        except Exception as e:
            db.session.rollback()
            flash(f"Güncellerken bir hata oluştu: {str(e)}", "danger")
    
    return render_template('filo/duzelt.html', form=form, ekipman=ekipman)

# --- 5. Makine Bilgi Sayfası (Bilgi ekleyelim) ---
@filo_bp.route('/bilgi/<int:id>', methods=['GET'])
def bilgi(id):
    # Ekipmanı ve ilişkili tüm kiralama kalemlerini çek
    ekipman = Ekipman.query.options(
        subqueryload(Ekipman.kiralama_kalemleri).options(
            joinedload(KiralamaKalemi.kiralama).joinedload(Kiralama.musteri)
        )
    ).get_or_404(id)
    
    # Kalemleri tarihe göre sıralayalım (en yeni en üstte)
    kalemler = sorted(ekipman.kiralama_kalemleri, key=lambda k: k.id, reverse=True)
    
    return render_template('filo/bilgi.html', ekipman=ekipman, kalemler=kalemler)

# --- 6. KİRALAMA SONLANDIRMA (GÜNCELLENDİ) ---
@filo_bp.route('/sonlandir', methods=['POST'])
def sonlandir():
    try:
        ekipman_id = request.form.get('ekipman_id', type=int)
        bitis_tarihi_str = request.form.get('bitis_tarihi') 

        if not (ekipman_id and bitis_tarihi_str):
            flash('Eksik bilgi! Ekipman ID veya Bitiş Tarihi gelmedi.', 'danger')
            return redirect(url_for('filo.index'))

        ekipman = Ekipman.query.get_or_404(ekipman_id)

        if ekipman.calisma_durumu == 'kirada':
            
            # Ekipmana ait 'sonlandırılmamış' aktif kalemi bul
            aktif_kalem = KiralamaKalemi.query.filter_by(
                ekipman_id=ekipman.id,
                sonlandirildi=False  # Sadece henüz kapatılmamış olanı bul
            ).order_by(KiralamaKalemi.id.desc()).first()
            
            if aktif_kalem:
                # Sunucu Tarafı Tarih Kontrolü
                try:
                    # kiralama_baslangıcı 'String' olduğu için strptime kullanıyoruz
                    baslangic_dt = datetime.strptime(aktif_kalem.kiralama_baslangıcı, "%Y-%m-%d").date()
                    bitis_dt = datetime.strptime(bitis_tarihi_str, "%Y-%m-%d").date()
                    
                    if bitis_dt < baslangic_dt:
                        flash(f"Hata: Bitiş tarihi ({bitis_tarihi_str}), başlangıç tarihinden ({aktif_kalem.kiralama_baslangıcı}) önce olamaz!", 'danger')
                        return redirect(url_for('filo.index'))
                        
                except ValueError:
                    flash("Tarih formatı geçersiz.", 'danger')
                    return redirect(url_for('filo.index'))

                # --- ASIL İŞLEM BURADA ---
                
                # 1. Kiralama Bitiş Tarihini (String olarak) ayarla
                aktif_kalem.kiralama_bitis = bitis_tarihi_str
                
                # 2. Ekipman durumunu 'bosta' yap
                ekipman.calisma_durumu = 'bosta'
                
                # 3. (EN ÖNEMLİSİ) Bu kalemi 'sonlandirildi' olarak işaretle.
                #    Bu, 'duzenle' sayfasının bu kalemi kilitlemesini sağlayacak.
                aktif_kalem.sonlandirildi = True 
                
                db.session.commit()
                flash(f"{ekipman.kod} kodlu ekipman kiralaması başarıyla sonlandırıldı.", 'success')
            else:
                # Veri tutarsızlığı: 'kirada' ama 'sonlandırılmamış' kalem yok.
                ekipman.calisma_durumu = 'bosta'
                db.session.commit()
                flash(f"{ekipman.kod} 'kirada' görünüyordu ama aktif kiralama kalemi bulunamadı! Ekipman 'boşa' alındı.", 'warning')
        else:
            flash(f"{ekipman.kod} kodlu ekipman zaten 'Boşta'.", 'info')
    
    except Exception as e:
        db.session.rollback()
        flash(f"Kiralama sonlandırılırken bir hata oluştu: {str(e)}", 'danger')
        traceback.print_exc() # Hatayı terminale yazdır
        
    return redirect(url_for('filo.index'))