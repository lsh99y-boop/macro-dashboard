# -*- coding: utf-8 -*-
"""데이터 수집: M2(ECOS), 선행지수 순환변동치(ECOS), 코스피 시가총액(marcap).

모든 함수는 월간 pandas.Series(index=월말 Timestamp)를 돌려준다.
marcap 연도별 parquet(약 20MB/년)은 월말 집계만 추려 data/cache 에 저장하므로
재실행 시 과거 연도는 다시 받지 않고 당해 연도만 갱신한다.
"""
from __future__ import annotations
import io
import datetime as dt
import requests
import pandas as pd

import config as C

_SESSION = requests.Session()
_SESSION.headers.update({"User-Agent": "Mozilla/5.0 (macro-indicator-tool)"})


# ─────────────────────────────────────────────────────────────────
# ECOS 공통
# ─────────────────────────────────────────────────────────────────
def _ecos_monthly(stat: str, item: str, start: str = "200501", end: str | None = None) -> pd.Series:
    """ECOS StatisticSearch 월간 조회 → Series(index=월말, value=float)."""
    if end is None:
        end = dt.date.today().strftime("%Y%m")
    url = (
        f"https://ecos.bok.or.kr/api/StatisticSearch/{C.ECOS_KEY}"
        f"/json/kr/1/1000/{stat}/M/{start}/{end}/{item}"
    )
    r = _SESSION.get(url, timeout=30).json()
    block = r.get("StatisticSearch")
    if not block:
        raise RuntimeError(f"ECOS 조회 실패 {stat}/{item}: {r.get('RESULT')}")
    df = pd.DataFrame(block["row"])
    df = df[df["DATA_VALUE"].notna()]
    idx = pd.to_datetime(df["TIME"], format="%Y%m") + pd.offsets.MonthEnd(0)
    s = pd.Series(df["DATA_VALUE"].astype(float).values, index=idx).sort_index()
    s.name = f"{stat}/{item}"
    return s


def fetch_m2() -> pd.Series:
    """M2(광의통화, 평잔, 원계열) 월간. 단위: 원."""
    s = _ecos_monthly(C.M2_STAT, C.M2_ITEM)
    return (s * C.M2_UNIT_WON).rename("M2_won")   # 십억원 → 원


def fetch_leading_cycle() -> pd.Series:
    """선행지수 순환변동치 월간. 기준 100."""
    return _ecos_monthly(C.CCI_STAT, C.CCI_ITEM).rename("선행지수순환변동치")


def fetch_coincident_cycle() -> pd.Series:
    """동행지수 순환변동치 월간. 기준 100."""
    return _ecos_monthly(C.COIN_STAT, C.COIN_ITEM).rename("동행지수순환변동치")


# ─────────────────────────────────────────────────────────────────
# marcap: 코스피 월말 시가총액
# ─────────────────────────────────────────────────────────────────
def _marcap_year_monthly(year: int) -> pd.Series:
    """한 해 parquet를 받아 KOSPI 월말 시가총액(원) Series로 집계."""
    url = C.MARCAP_YEAR_URL.format(year=year)
    r = _SESSION.get(url, timeout=120)
    r.raise_for_status()
    df = pd.read_parquet(io.BytesIO(r.content), columns=["Date", "Market", "Marcap"])
    k = df[df["Market"] == "KOSPI"]
    daily = k.groupby("Date")["Marcap"].sum()
    daily.index = pd.to_datetime(daily.index)
    monthly = daily.resample("ME").last()          # 각 월 마지막 거래일
    monthly.name = "KOSPI_marcap_won"
    return monthly


def fetch_kospi_marketcap(force_refresh_current: bool = True) -> pd.Series:
    """코스피 월말 시가총액(원) 월간 시계열. 연도별 집계를 캐시한다."""
    this_year = dt.date.today().year
    parts = []
    for year in range(C.START_YEAR, this_year + 1):
        cache = C.CACHE_DIR / f"marcap_kospi_{year}.csv"
        # 과거 연도는 캐시 사용, 당해 연도는 매번 갱신
        if cache.exists() and not (year == this_year and force_refresh_current):
            s = pd.read_csv(cache, index_col=0, parse_dates=True).iloc[:, 0]
        else:
            try:
                s = _marcap_year_monthly(year)
                s.to_frame().to_csv(cache)
            except Exception as e:  # noqa: BLE001
                # 아직 없는 연도 등은 건너뜀
                print(f"  [marcap] {year} 건너뜀: {e}")
                continue
        parts.append(s)
    out = pd.concat(parts).sort_index()
    out = out[~out.index.duplicated(keep="last")]
    out.name = "KOSPI_marcap_won"
    return out


if __name__ == "__main__":
    m2 = fetch_m2()
    cci = fetch_leading_cycle()
    cap = fetch_kospi_marketcap()
    print("M2  :", m2.index.min().date(), "~", m2.index.max().date(), "| 최신", round(m2.iloc[-1] / 1e12, 1), "조원")
    print("순환:", cci.index.min().date(), "~", cci.index.max().date(), "| 최신", cci.iloc[-1])
    print("시총:", cap.index.min().date(), "~", cap.index.max().date(), "| 최신", round(cap.iloc[-1] / 1e12, 1), "조원")
