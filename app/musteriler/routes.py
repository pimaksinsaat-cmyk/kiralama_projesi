from app.musteriler import musteriler_bp
from flask import render_template, url_for

@musteriler_bp.route('/')
@musteriler_bp.route('/index')
def index():
    """
    Ana Sayfa (Dashboard).
    """
    # Birazdan oluşturacağımız 'musteriler/index.html' şablonunu döndürür.
    return render_template('musteriler/index.html')