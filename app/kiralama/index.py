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