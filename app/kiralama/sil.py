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