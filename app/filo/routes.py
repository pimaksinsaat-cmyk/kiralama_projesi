from app.filo import filo_bp
from app import db 
from app.models import Ekipman, Musteri, Kiralama
from app.forms import EkipmanForm 
from flask import render_template, redirect, url_for, flash, request
from datetime import datetime

# --- 1. Makine Parkı Listeleme Sayfası (GÜNCELLENDİ) ---
@filo_bp.route('/')
def index():
    """
    Tüm makine parkını listeler.
    Kirada olanlara aktif kiralama başlangıç tarihini ekler.
    """
    ekipmanlar = Ekipman.query.all()
    
    # YENİ: Kirada olan ekipmanların başlangıç tarihini bul
    for ekipman in ekipmanlar:
        ekipman.aktif_kiralama_baslangici = None # Varsayılan değer
        if ekipman.calisma_durumu == 'kirada':
            # Ekipmana ait son (aktif) kiralama kaydını bul
            aktif_kiralama = Kiralama.query.filter_by(
                ekipman_id=ekipman.id
            ).order_by(Kiralama.id.desc()).first()
            
            if aktif_kiralama:
                # ekipman nesnesine geçici bir özellik olarak ekle
                ekipman.aktif_kiralama_baslangici = aktif_kiralama.kiralama_baslangıcı
            # else: Veri tutarsızlığı var (kirada ama kayıt yok), None olarak kalacak
    
    return render_template('filo/index.html', ekipmanlar=ekipmanlar)

# --- 2. Yeni Makine Ekleme Sayfası (Form) ---
@filo_bp.route('/ekle', methods=['GET', 'POST'])
def ekle():
# ... (Mevcut kodunuz aynı kalıyor) ...
    form = EkipmanForm()
    son_ekipman = Ekipman.query.order_by(Ekipman.id.desc()).first()
    son_kod = son_ekipman.kod if son_ekipman else 'Kayıtlı makine yok'
    
    if form.validate_on_submit():
        
        yeni_ekipman = Ekipman(
            kod=form.kod.data,
            yakit=form.yakit.data,
            tipi=form.tipi.data,
            marka=form.marka.data,
            seri_no=form.seri_no.data,
            calisma_yuksekligi=form.calisma_yuksekligi.data,
            kaldirma_kapasitesi=form.kaldirma_kapasitesi.data, 
            uretim_tarihi=form.uretim_tarihi.data
        )
        
        db.session.add(yeni_ekipman)
        db.session.commit()
        flash('Yeni makine başarıyla eklendi!', 'success')
        return redirect(url_for('filo.index'))
    
    return render_template('filo/ekle.html', form=form, son_kod=son_kod)

# --- 3. Makine Silme İşlemi ---
@filo_bp.route('/sil/<int:id>', methods=['POST'])
def sil(id):
# ... (Mevcut kodunuz aynı kalıyor) ...
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

# --- 4. Makine Düzeltme Sayfası ---
@filo_bp.route('/duzelt/<int:id>', methods=['GET', 'POST'])
def duzelt(id):
# ... (Mevcut kodunuz aynı kalıyor) ...
    ekipman = Ekipman.query.get_or_404(id)
    form = EkipmanForm(obj=ekipman)
    
    if form.validate_on_submit():
        ekipman.marka = form.marka.data
        ekipman.yakit = form.yakit.data
        ekipman.tipi = form.tipi.data
        ekipman.kod = form.kod.data
        ekipman.seri_no = form.seri_no.data
        ekipman.calisma_yuksekligi = form.calisma_yuksekligi.data
        ekipman.kaldirma_kapasitesi = form.kaldirma_kapasitesi.data
        ekipman.uretim_tarihi = form.uretim_tarihi.data
        db.session.commit()
        flash('Makine bilgileri başarıyla güncellendi!', 'success')
        return redirect(url_for('filo.index'))
    
    return render_template('filo/duzelt.html', form=form, ekipman=ekipman)

# --- 5. Makine Bilgi Sayfası ---
@filo_bp.route('/bilgi/<int:id>', methods=['GET'])
def bilgi(id):
# ... (Mevcut kodunuz aynı kalıyor) ...
    ekipman = Ekipman.query.get_or_404(id)
    return render_template('filo/bilgi.html', ekipman=ekipman)

# --- 6. KİRALAMA SONLANDIRMA ---
@filo_bp.route('/sonlandir', methods=['POST'])
def sonlandir():
# ... (Mevcut kodunuz aynı kalıyor) ...
    try:
        ekipman_id = request.form.get('ekipman_id', type=int)
        bitis_tarihi_str = request.form.get('bitis_tarihi') 

        if not (ekipman_id and bitis_tarihi_str):
            flash('Eksik bilgi! Ekipman ID veya Bitiş Tarihi gelmedi.', 'danger')
            return redirect(url_for('filo.index'))

        ekipman = Ekipman.query.get_or_404(ekipman_id)

        if ekipman.calisma_durumu == 'kirada':
            ekipman.calisma_durumu = 'bosta'
            
            aktif_kiralama = Kiralama.query.filter_by(ekipman_id=ekipman.id).order_by(Kiralama.id.desc()).first()
            
            if aktif_kiralama:
                # YENİ KONTROL (Sunucu Tarafı)
                # Kiralama bitiş tarihi, başlangıç tarihinden önce olamaz
                try:
                    baslangic_dt = datetime.strptime(aktif_kiralama.kiralama_baslangıcı, "%Y-%m-%d").date()
                    bitis_dt = datetime.strptime(bitis_tarihi_str, "%Y-%m-%d").date()
                    
                    if bitis_dt < baslangic_dt:
                        flash(f"Hata: Bitiş tarihi ({bitis_tarihi_str}), başlangıç tarihinden ({aktif_kiralama.kiralama_baslangıcı}) önce olamaz!", 'danger')
                        return redirect(url_for('filo.index'))
                except ValueError:
                    flash("Tarih formatı geçersiz.", 'danger')
                    return redirect(url_for('filo.index'))

                aktif_kiralama.kiralama_bitis = bitis_tarihi_str
            else:
                flash(f"{ekipman.kod} boşa alındı ancak aktif kiralama kaydı bulunamadı!", 'warning')
            
            db.session.commit()
            flash(f"{ekipman.kod} kodlu ekipman 'Boşa' alındı. Bitiş tarihi: {bitis_tarihi_str}", 'success')
        
        else:
            flash(f"{ekipman.kod} kodlu ekipman zaten 'Boşta'.", 'info')
    
    except Exception as e:
        db.session.rollback()
        flash(f"Kiralama sonlandırılırken bir hata oluştu: {str(e)}", 'danger')
        
    return redirect(url_for('filo.index'))

