from flask import Blueprint

# 'kiralama' adında bir blueprint (departman tabelası) oluştur
kiralama_bp = Blueprint('kiralama', __name__)

# Bu departmana ait rotaları (URL'leri) bağla
# (Circular import'u önlemek için import en sonda yapılır)
from app.kiralama import routes