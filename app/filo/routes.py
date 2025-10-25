from app.filo import filo_bp
from app import db 
from app.models import Ekipman, Musteri
from app.forms import EkipmanForm 
from flask import render_template, redirect, url_for, flash
from datetime import datetime  # --- DEĞİŞİKLİK 1: datetime import edildi ---

# --- 1. Makine Parkı Listeleme Sayfası ---
@filo_bp.route('/')
def index():
    """
    Tüm makine parkını listeler.
    """
    ekipmanlar = Ekipman.query.all()
    return render_template('filo/index.html', ekipmanlar=ekipmanlar)

# --- 2. Yeni Makine Ekleme Sayfası (Form) ---
@filo_bp.route('/ekle', methods=['GET', 'POST'])
def ekle():
    """
    Yeni makine ekleme formunu gösterir (GET) ve işler (POST).
    """
    form = EkipmanForm()
    
    if form.validate_on_submit():
        
        # --- DEĞİŞİKLİK 2: String'i date objesine çevirme ---
        uretim_tarihi_obj = None # Varsayılan olarak boş
        uretim_tarihi_str = form.uretim_tarihi.data
        
        # Eğer formdan bir tarih geldiyse (boş değilse)
        if uretim_tarihi_str:
            # Gelen 'YYYY-MM-DD' formatındaki string'i date objesine çevir
            # Not: .data'yı str() içine almak, bazen date objesi gelirse diye
            # hatayı önler, ama sizin durumunuzda hep string geliyor.
            uretim_tarihi_obj = datetime.strptime(str(uretim_tarihi_str), '%Y-%m-%d').date()
        # --- DEĞİŞİKLİK SONU ---

        yeni_ekipman = Ekipman(
            kod=form.kod.data,
            yakit=form.yakit.data,
            tipi=form.tipi.data,
            marka=form.marka.data,
            seri_no=form.seri_no.data,
            calisma_yuksekligi=form.calisma_yuksekligi.data,
            kaldirma_kapasitesi=form.kaldirma_kapasitesi.data, 
            uretim_tarihi=uretim_tarihi_obj  # Buraya artık string değil, date objesi atanıyor
        )
        
        db.session.add(yeni_ekipman)
        db.session.commit()
        
        flash('Yeni makine başarıyla eklendi!', 'success')
        
        return redirect(url_for('filo.index'))
    
    return render_template('filo/ekle.html', form=form)

# --- 3. Makine Silme İşlemi ---
@filo_bp.route('/sil/<int:id>', methods=['POST'])
def sil(id):
    """
    ID'si verilen makineyi siler.
    """
    ekipman = Ekipman.query.get_or_404(id)
    
    db.session.delete(ekipman)
    db.session.commit()
    
    flash('Makine başarıyla silindi.', 'success')
    
    return redirect(url_for('filo.index'))

# --- 4. Makine Düzeltme Sayfası (YENİ FONKSİYON) ---
@filo_bp.route('/duzelt/<int:id>', methods=['GET', 'POST'])
def duzelt(id):
    """
    ID'si verilen makineyi bulur ve form ile bilgilerini günceller.
    """
    ekipman = Ekipman.query.get_or_404(id)
    form = EkipmanForm(obj=ekipman)
    
    if form.validate_on_submit():
        
        # --- DEĞİŞİKLİK 3: String'i date objesine çevirme ---
        uretim_tarihi_obj = None # Varsayılan olarak boş
        uretim_tarihi_str = form.uretim_tarihi.data
        
        if uretim_tarihi_str:
            uretim_tarihi_obj = datetime.strptime(str(uretim_tarihi_str), '%Y-%m-%d').date()
        # --- DEĞİŞİKLİK SONU ---
        
        ekipman.marka = form.marka.data
        ekipman.yakit = form.yakit.data
        ekipman.tipi = form.tipi.data
        ekipman.kod = form.kod.data
        ekipman.seri_no = form.seri_no.data
        ekipman.calisma_yuksekligi = form.calisma_yuksekligi.data
        ekipman.kaldirma_kapasitesi = form.kaldirma_kapasitesi.data
        ekipman.uretim_tarihi = uretim_tarihi_obj # Buraya da date objesi atanıyor

        db.session.commit()
        
        flash('Makine bilgileri başarıyla güncellendi!', 'success')
        
        return redirect(url_for('filo.index'))
    
    return render_template('filo/duzelt.html', form=form, ekipman=ekipman)