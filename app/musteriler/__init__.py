from flask import Blueprint

# 'musteriler' adında bir blueprint (departman tabelası) oluştur
musteriler_bp = Blueprint('musteriler', __name__)

# Bu departmana ait rotaları (URL'leri) bağla
# (Circular import'u önlemek için import en sonda yapılır)
from app.musteriler import routes