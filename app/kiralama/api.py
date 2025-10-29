from app.kiralama import kiralama_bp
from app.models import Ekipman
from flask import render_template, redirect, url_for, flash, jsonify, request
from sqlalchemy import and_

# ... (diğer route'larınız) ...

@kiralama_bp.route('/api/get-ekipman')
def get_ekipman():
  try:
    # 1. Filtre parametrelerini al
    tipi = request.args.get('tipi', '', type=str)
    yakit = request.args.get('yakit', '', type=str)
    min_yukseklik = request.args.get('min_yukseklik', 0, type=int)
    min_kapasite = request.args.get('min_kapasite', 0, type=int)
    
    # YENİ: Canvas'taki JavaScript'ten gelen 'include_id' parametresini al
    include_id = request.args.get('include_id', None, type=int)

    # 2. Ana sorgu: 'bosta' olan ve filtrelere uyanlar
    query = Ekipman.query.filter(
      and_(
        Ekipman.calisma_durumu == 'bosta',
        Ekipman.calisma_yuksekligi.isnot(None),
        Ekipman.kaldirma_kapasitesi.isnot(None),
        )
    )

    # 3. Filtreleri uygula
    if tipi:
      query = query.filter(Ekipman.tipi.ilike(f"%{tipi}%"))
    if yakit:
      query = query.filter(Ekipman.yakit.ilike(f"%{yakit}%"))
    if min_yukseklik > 0:
      query = query.filter(Ekipman.calisma_yuksekligi >= min_yukseklik)
    if min_kapasite > 0:
      query = query.filter(Ekipman.kaldirma_kapasitesi >= min_kapasite)

    # 'bosta' olanları al
    ekipmanlar = query.all()
    
    # 4. YENİ MANTIK: 'include_id'yi işle
    
    # 'bosta' listesindeki ID'leri bir sete al (hızlı kontrol için)
    bosta_id_seti = {e.id for e in ekipmanlar}

    if include_id and include_id not in bosta_id_seti:
      # Eğer 'include_id' gönderildiyse ve zaten 'bosta' listesinde değilse,
      # bu ekipmanı (filtrelere uymasa bile) bul ve listeye ekle.
      mevcut_ekipman = Ekipman.query.get(include_id)
      if mevcut_ekipman:
        # Kullanıcının 'mevcut' seçimi görmesi için listenin başına ekliyoruz.
        ekipmanlar.insert(0, mevcut_ekipman)
    
    # 5. Sonuçları JSON formatına çevir
    sonuc = [
      {
        "id": e.id, 
        # YENİ: Mevcut ekipmanın kodunun sonuna "(Mevcut)" ekleyebiliriz
        "kod": f"{e.kod} ({e.tipi} / {e.calisma_yuksekligi or 0}m / {e.kaldirma_kapasitesi or 0}kg)" + 
            (" (Mevcut)" if e.id == include_id else "") 
      } 
      for e in ekipmanlar
    ]
    
    return jsonify(sonuc)
    
  except Exception as e:
    # Hata ayıklama için print eklemek iyi bir fikir olabilir
    print(f"API Hatası (get_ekipman): {str(e)}")
    return jsonify({"error": str(e), "details": "Sunucu tarafında bir hata oluştu."}), 500
