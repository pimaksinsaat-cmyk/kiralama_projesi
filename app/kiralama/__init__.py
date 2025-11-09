from flask import Blueprint

# kiralama Blueprint'ini tanımlıyoruz
kiralama_bp = Blueprint('kiralama', __name__, template_folder='templates')

# Alttaki satırlar, rotaların uygulamaya dahil edilmesini sağlar.

from . import index
from . import ekle
from . import sil
from . import bilgi
from . import api