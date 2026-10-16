"""GTÜ sitesinin (Next.js) sayfalarından başlık ve gövde metni çıkarır.

İki tür sayfa var (olcumler §8):

- Duyuru detayı (/icerik/…): gövde gömülü veride. `self.__next_f.push`
  çağrılarındaki JS dizeleri birleştirilince RSC verisi çıkıyor; gövde bir
  öğenin `"content"` alanında HTML, başlığı hemen önündeki `"h1"`'de. Aynı
  veride "Sayfa bulunamadı" şablonunun h1'i de var; bu yüzden gövdeye en
  yakın h1 alınıyor.
- Kategori sayfası (/kategori/…/0/): gövde sunucunun ürettiği HTML'de,
  `<div class="rich-text-content">` içinde. Başlık <title>'dan.
"""

import html
import json
import re
from html.parser import HTMLParser

_PUSH = re.compile(r'self\.__next_f\.push\(\[1,"((?:[^"\\]|\\.)*)"\]\)')
_H1 = re.compile(r'\["\$","h1",null,\{"className":"[^"]*","children":"((?:[^"\\]|\\.)*)"\}\]')
_CONTENT = re.compile(r'"content":"((?:[^"\\]|\\.)*)"')
_BLOK = re.compile(r"</?(p|div|br|li|tr|h[1-6]|ul|ol|table)\b[^>]*>", re.IGNORECASE)
_BLOK_ETIKET = {"p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "table"}


def rsc(sayfa: str) -> str:
    """Gömülü RSC verisini düz metin olarak birleştirir."""
    parcalar = []
    for s in _PUSH.findall(sayfa):
        try:
            parcalar.append(json.loads(f'"{s}"'))
        except json.JSONDecodeError:
            continue
    return "".join(parcalar)


def _duzenle(t: str) -> str:
    """Satırları sadeleştirir, ardışık boş satırları teke indirir."""
    out, bos = [], False
    for s in (" ".join(x.split()) for x in t.splitlines()):
        if s:
            out.append(s)
            bos = False
        elif not bos and out:
            out.append("")
            bos = True
    return "\n".join(out).strip()


def html_metne(icerik: str) -> str:
    """Gövde HTML'ini paragrafları koruyarak düz metne çevirir."""
    t = _BLOK.sub("\n", icerik)
    return _duzenle(html.unescape(re.sub(r"<[^>]+>", " ", t)))


class _ZenginMetin(HTMLParser):
    """`rich-text-content` sınıflı div'lerin içindeki metni toplar."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.derinlik = 0  # 0: kapsayıcının dışında
        self.parcalar: list[str] = []

    def handle_starttag(self, etiket, nitelikler):
        if self.derinlik:
            if etiket == "div":
                self.derinlik += 1
            if etiket in _BLOK_ETIKET:
                self.parcalar.append("\n")
        elif etiket == "div" and "rich-text-content" in (dict(nitelikler).get("class") or ""):
            self.derinlik = 1
            self.parcalar.append("\n\n")

    def handle_endtag(self, etiket):
        if self.derinlik:
            if etiket in _BLOK_ETIKET:
                self.parcalar.append("\n")
            if etiket == "div":
                self.derinlik -= 1

    def handle_data(self, veri):
        if self.derinlik:
            self.parcalar.append(veri)


def zengin_metin(sayfa: str) -> str:
    p = _ZenginMetin()
    p.feed(re.sub(r"<script.*?</script>", "", sayfa, flags=re.DOTALL))
    return _duzenle("".join(p.parcalar))


def sayfa_basligi(sayfa: str) -> str:
    m = re.search(r"<title>(.*?)</title>", sayfa, re.DOTALL)
    return " ".join(html.unescape(m.group(1)).split()) if m else ""


def duyuru(sayfa: str) -> tuple[str, str, str]:
    """Duyuru detayı: (başlık, gövde metni, gövde HTML'i)."""
    r = rsc(sayfa)
    for m in _CONTENT.finditer(r):
        try:
            govde = json.loads(f'"{m.group(1)}"')
        except json.JSONDecodeError:
            continue
        if "<" not in govde:  # meta etiketlerinin content'i (site doğrulama kodu vb.)
            continue
        h1 = [x for x in _H1.finditer(r, 0, m.start())]
        baslik = json.loads(f'"{h1[-1].group(1)}"').strip() if h1 else ""
        return baslik, html_metne(govde), govde
    return "", "", ""


def dosya_baglantilari(govde_html: str) -> list[str]:
    return re.findall(r'href="([^"]+\.(?:pdf|docx?|xlsx?))"', govde_html, re.IGNORECASE)
