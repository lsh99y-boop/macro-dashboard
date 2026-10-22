# -*- coding: utf-8 -*-
"""프로젝트 설정 및 상수.

ECOS(한국은행) 오픈API 키는 코드에 넣지 않습니다(공개 저장소 대비).
우선순위: 환경변수 ECOS_KEY  →  로컬 파일 .ecos_key(.gitignore됨).
- GitHub Actions: 저장소 Secret ECOS_KEY 로 주입.
- 로컬 실행: 프로젝트 폴더에 .ecos_key 파일로 키 한 줄 저장.
"""
import os
from pathlib import Path


def _load_ecos_key() -> str:
    key = os.environ.get("ECOS_KEY", "").strip()
    if key:
        return key
    f = Path(__file__).resolve().parent / ".ecos_key"
    if f.exists():
        return f.read_text(encoding="utf-8").strip()
    return ""


# 한국은행 ECOS 오픈API 인증키 (환경변수 또는 .ecos_key)
ECOS_KEY = _load_ecos_key()

# ─── ECOS 통계 코드 ────────────────────────────────────────────────
# M2(광의통화, 평잔, 원계열), 단위 십억원, 월간
M2_STAT, M2_ITEM, M2_UNIT_WON = "161Y006", "BBHA00", 1e9   # 십억원 → 원 환산계수
# 경기종합지수 중 선행지수 순환변동치, 2020=100, 월간
CCI_STAT, CCI_ITEM = "901Y067", "I16E"
# (참고) 동행지수 순환변동치
COIN_STAT, COIN_ITEM = "901Y067", "I16D"

# ─── marcap (코스피 시가총액) ──────────────────────────────────────
# FinanceData/marcap GitHub 저장소의 연도별 parquet (일별·전종목 시가총액)
MARCAP_YEAR_URL = (
    "https://raw.githubusercontent.com/FinanceData/marcap/master/data/marcap-{year}.parquet"
)

# ─── 분석 기간 ────────────────────────────────────────────────────
START_YEAR = 2005                 # 분석 시작 연도 (김영익 소장 기준과 동일)
BASELINE_START = "2005-01"        # Z스코어 기준선 시작
BASELINE_END = "2025-12"          # Z스코어 기준선 끝 (장기평균 산정 구간)

# ─── 경로 ─────────────────────────────────────────────────────────
ROOT = Path(__file__).resolve().parent
CACHE_DIR = ROOT / "data" / "cache"
OUT_DIR = ROOT / "output"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUT_DIR.mkdir(parents=True, exist_ok=True)

# ─── 신호 임계치 (Z스코어 기준) ───────────────────────────────────
# |Z| 밴드: 과열/정상/저평가 신호등
Z_EXTREME = 2.0    # 🔴 심각한 과열(또는 극단 저평가)
Z_ELEVATED = 1.0   # 🟡 과열(또는 저평가) 진입
