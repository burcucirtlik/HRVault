---
name: panel
description: Kişisel paneli güncelleyip tarayıcıda açar — son tarama, başvurular, uyum yüzdeleri, kaynaklar. Kişi "/panel", "paneli aç", "dashboard", "özeti göster" dediğinde kullan.
---
<!-- durum: çalışır -->
# panel

```bash
python3 engine/pipeline/dashboard.py --open
```
- Panel yalnızca kişinin bilgisayarındadır (`me/dashboard.html`); hiçbir yere yüklenmez. İlk açılışta bunu bir cümleyle söyle.
- `me/` yoksa betik panel üretmez: `/başla` öner.
- Açtıktan sonra panelde ne olduğunu iki satırda söyle; içeriği sohbete kopyalama.
