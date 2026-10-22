# -*- coding: utf-8 -*-
"""GitHub Pages용 사이트 빌드.

build_dashboard.generate_html() 로 대시보드 HTML을 만들고,
PWA(홈 화면 설치) 태그를 주입한 뒤 web/ 정적자산과 함께 site/ 로 묶는다.
GitHub Actions 가 site/ 를 Pages 아티팩트로 업로드한다.

실행:  python build_site.py   (환경변수 ECOS_KEY 또는 .ecos_key 필요)
"""
from __future__ import annotations
import shutil
from pathlib import Path

import config as C
import build_dashboard as B

ROOT = Path(__file__).resolve().parent
WEB = ROOT / "web"
SITE = ROOT / "site"

PWA_HEAD = """<title>매크로 밸류·사이클 대시보드</title>
<link rel="manifest" href="manifest.webmanifest">
<meta name="theme-color" content="#364fc7">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<meta name="apple-mobile-web-app-title" content="매크로지표">
<link rel="apple-touch-icon" href="icon-192.png">
<link rel="icon" type="image/png" href="icon-192.png">"""

SW_SCRIPT = """<script>
if ('serviceWorker' in navigator) {
  window.addEventListener('load', function () {
    navigator.serviceWorker.register('sw.js').catch(function () {});
  });
}
</script>
</body></html>"""


def inject_pwa(html: str) -> str:
    html = html.replace("<title>매크로 밸류·사이클 대시보드</title>", PWA_HEAD, 1)
    html = html.replace("</div></body></html>", "</div>" + SW_SCRIPT, 1)
    return html


def main():
    if not C.ECOS_KEY:
        raise SystemExit("ECOS_KEY가 없습니다. 환경변수 ECOS_KEY 또는 .ecos_key 를 설정하세요.")
    html = inject_pwa(B.generate_html())

    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)
    # 정적 PWA 자산 복사
    for name in ("manifest.webmanifest", "sw.js", "icon-192.png", "icon-512.png"):
        shutil.copy2(WEB / name, SITE / name)
    (SITE / "index.html").write_text(html, encoding="utf-8")
    # Jekyll 비활성화(밑줄 폴더 등 그대로 서빙)
    (SITE / ".nojekyll").write_text("", encoding="utf-8")
    print(f"사이트 완료 → {SITE}  (파일 {len(list(SITE.iterdir()))}개)")


if __name__ == "__main__":
    main()
