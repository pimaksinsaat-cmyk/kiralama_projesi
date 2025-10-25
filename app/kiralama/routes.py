from app.kiralama import kiralama_bp
from flask import render_template, request
from app.models import Kiralama
from app.forms import KiralamaForm
# from app import db  # Eğer veritabanına kayıt yapacaksan, yorumu kaldır

@kiralama_bp.route('/', methods=['GET', 'POST'])
@kiralama_bp.route('/ekle', methods=['GET', 'POST'])
def ekle():
    """
    Kiralama ekleme sayfası.
    """
    form = KiralamaForm()  # Form nesnesi oluşturuluyor

    # Form POST edildiğinde ve doğrulama başarılıysa
    if form.validate_on_submit():
        yeni_kiralama = Kiralama(
            kod=form.kod.data,
            musteri_adi=form.musteri_adi.data,
            musteri_iletisim=form.musteri_iletisim.data,
            kiralama_baslangıcı=form.kiralama_baslangıcı.data,
            kiralama_bitis=form.kiralama_bitis.data,
            kiralama_brm_fiyat=form.kiralama_brm_fiyat.data,
            nakliye_fiyat=form.nakliye_fiyat.data
        )

        # Eğer veritabanına kaydetmek istiyorsan aşağıdakileri aç:
        # db.session.add(yeni_kiralama)
        # db.session.commit()

        return "Kiralama kaydedildi!"

    # Form ve sayfa şablonunu render et
    return render_template('kiralama/ekle.html', form=form)
