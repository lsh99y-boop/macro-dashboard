# -*- coding: utf-8 -*-
"""지표 계산.

1) 시총/M2 비율 + Z스코어 (밸류에이션 과열 신호등)
2) 선행지수 순환변동치 4국면 (확장·둔화·수축·회복) + 정점/저점 판정
3) 과열 × 사이클 2축 매트릭스
"""
from __future__ import annotations
from dataclasses import dataclass
import numpy as np
import pandas as pd

import config as C


# ─────────────────────────────────────────────────────────────────
# 1) 시총 / M2 비율 + Z스코어
# ─────────────────────────────────────────────────────────────────
@dataclass
class RatioResult:
    ratio: pd.Series          # 시총/M2 (%) 월간
    mean: float               # 기준구간 평균(%)
    std: float                # 기준구간 표준편차
    z: pd.Series              # 전구간 Z스코어 (기준구간 μ,σ 기준)
    z_detrended: pd.Series    # 추세제거 Z (5년 롤링 기준)
    latest: dict              # 최신 스냅샷


def _signal_from_z(z: float) -> tuple[str, str]:
    """Z스코어 → (신호등 이모지, 라벨)."""
    if z >= C.Z_EXTREME:
        return "🔴", "심각한 과열"
    if z >= C.Z_ELEVATED:
        return "🟡", "과열"
    if z <= -C.Z_EXTREME:
        return "🔵", "심각한 저평가"
    if z <= -C.Z_ELEVATED:
        return "🟢", "저평가"
    return "⚪", "정상 범위"


def compute_ratio_zscore(marcap_won: pd.Series, m2_won: pd.Series) -> RatioResult:
    """시총/M2 비율(%)과 Z스코어를 계산."""
    df = pd.concat({"cap": marcap_won, "m2": m2_won}, axis=1).dropna()
    ratio = (df["cap"] / df["m2"] * 100.0).rename("시총/M2(%)")

    base = ratio.loc[C.BASELINE_START:C.BASELINE_END]
    mean, std = float(base.mean()), float(base.std())
    z = ((ratio - mean) / std).rename("Z")

    # 추세제거 Z: M2가 꾸준히 커져 비율 평균이 우상향하는 편향을 보정.
    # 60개월 롤링 평균·표준편차 대비 편차 → "최근 추세 대비 얼마나 벗어났나".
    roll_mean = ratio.rolling(60, min_periods=36).mean()
    roll_std = ratio.rolling(60, min_periods=36).std()
    z_det = ((ratio - roll_mean) / roll_std).rename("Z_detrended")

    cur_z = float(z.iloc[-1])
    cur_zd = float(z_det.dropna().iloc[-1]) if z_det.notna().any() else np.nan
    # 신호등은 '추세보정 Z'(평균회귀 편향 제거) 기준 — 원시 Z는 M2 추세로 과대해짐.
    emoji, label = _signal_from_z(cur_zd if cur_zd == cur_zd else cur_z)
    pct = float((ratio <= ratio.iloc[-1]).mean() * 100)   # 역사적 백분위

    # 현재 추정: 최신 시총(확정) ÷ 최신 M2(시차로 이월). M2 전망 미반영이라 추정치.
    est_ratio = float(marcap_won.iloc[-1] / m2_won.iloc[-1] * 100)
    latest = {
        "date": ratio.index[-1],
        "ratio": float(ratio.iloc[-1]),
        "z": cur_z,
        "z_detrended": cur_zd,
        "percentile": pct,
        "emoji": emoji,
        "label": label,
        "peak_ratio": float(ratio.max()),
        "peak_date": ratio.idxmax(),
        "est_ratio": est_ratio,
        "est_cap_date": marcap_won.index[-1],
        "est_m2_date": m2_won.index[-1],
    }
    return RatioResult(ratio, mean, std, z, z_det, latest)


# ─────────────────────────────────────────────────────────────────
# 2) 선행지수 순환변동치 4국면
# ─────────────────────────────────────────────────────────────────
PHASES = {
    ("up", "above"): ("확장", "경기 확장 — 기준선 위에서 상승"),
    ("down", "above"): ("둔화", "경기 둔화 — 고점권에서 꺾임"),
    ("down", "below"): ("수축", "경기 수축 — 기준선 아래 하락"),
    ("up", "below"): ("회복", "경기 회복 — 바닥에서 반등"),
}


@dataclass
class CycleResult:
    series: pd.Series
    slope3: pd.Series         # 3개월 변화(모멘텀)
    phase: pd.Series          # 국면 라벨 시계열
    latest: dict


def compute_cycle_phase(cci: pd.Series) -> CycleResult:
    """100 기준 위/아래 × 3개월 방향 → 4국면 라벨링, 정점/저점 판정."""
    s = cci.dropna()
    slope3 = (s - s.shift(3)).rename("3개월변화")

    def _label(idx) -> str:
        val = s.loc[idx]
        sl = slope3.loc[idx]
        if pd.isna(sl):
            return ""
        d = "up" if sl >= 0 else "down"
        pos = "above" if val >= 100 else "below"
        return PHASES[(d, pos)][0]

    phase = pd.Series({idx: _label(idx) for idx in s.index}, name="국면")

    # 정점/저점 판정: 최근 N개월 연속 하락/상승 여부
    diff = s.diff()
    consec_down = 0
    for v in diff.iloc[::-1]:
        if v < 0:
            consec_down += 1
        else:
            break
    consec_up = 0
    for v in diff.iloc[::-1]:
        if v > 0:
            consec_up += 1
        else:
            break

    peak_flag = consec_down >= 3        # 3개월 연속 하락 = 정점 유력
    trough_flag = consec_up >= 3
    recent_peak_date = s.loc[:s.index[-1]].idxmax() if peak_flag else None

    latest = {
        "date": s.index[-1],
        "value": float(s.iloc[-1]),
        "slope3": float(slope3.iloc[-1]),
        "phase": phase.iloc[-1],
        "phase_desc": PHASES[("up" if slope3.iloc[-1] >= 0 else "down",
                              "above" if s.iloc[-1] >= 100 else "below")][1],
        "consec_down": consec_down,
        "consec_up": consec_up,
        "peak_flag": peak_flag,
        "trough_flag": trough_flag,
        "recent_peak_date": recent_peak_date,
        "recent_peak_value": float(s.max()) if peak_flag else None,
    }
    return CycleResult(s, slope3, phase, latest)


# ─────────────────────────────────────────────────────────────────
# 3) 과열 × 사이클 2축 매트릭스
# ─────────────────────────────────────────────────────────────────
QUADRANTS = {
    ("hot", "up"):   ("과열·확장", "🔥 밸류 과열 + 경기 상승 — 거품 지속, 가장 위험"),
    ("hot", "down"): ("과열해소·둔화", "⚠️ 과열 해소 중 + 경기 꺾임 — 경계/하락 구간"),
    ("cool", "down"):("정상·수축", "🧊 밸류 정상 + 경기 수축 — 침체/바닥 탐색"),
    ("cool", "up"):  ("정상·회복", "🌱 밸류 정상 + 경기 반등 — 매수 우호"),
}


@dataclass
class MatrixResult:
    x_z: float                # 밸류 과열 축 (Z스코어)
    y_slope: float            # 사이클 축 (순환변동치 3개월 변화)
    quadrant: str
    desc: str
    history: pd.DataFrame     # 월별 (z, slope) 궤적


def compute_matrix(ratio_res: RatioResult, cycle_res: CycleResult,
                   hot_threshold: float = C.Z_ELEVATED) -> MatrixResult:
    """밸류 Z스코어(X) × 순환변동치 모멘텀(Y)으로 4분면 판정."""
    # X축은 추세보정 Z(평균회귀 편향 제거). 원시 Z는 M2 추세로 +7σ까지 벌어져 왜곡.
    z = ratio_res.z_detrended
    slope = cycle_res.slope3
    hist = pd.concat({"z": z, "slope": slope}, axis=1).dropna()

    cur_z = float(hist["z"].iloc[-1])
    cur_sl = float(hist["slope"].iloc[-1])
    x = "hot" if cur_z >= hot_threshold else "cool"
    y = "up" if cur_sl >= 0 else "down"
    name, desc = QUADRANTS[(x, y)]
    return MatrixResult(cur_z, cur_sl, name, desc, hist)
