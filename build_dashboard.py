# -*- coding: utf-8 -*-
"""매크로 대시보드 생성.

데이터 수집 → 지표 계산 → 차트(PNG) → 자립형 HTML 리포트(output/macro_dashboard.html).
실행:  .venv\\Scripts\\python.exe build_dashboard.py
"""
from __future__ import annotations
import base64
import datetime as dt
import io
import sys

# 콘솔(cp949)에서 이모지 출력 시 깨지지 않도록 UTF-8 고정
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:  # noqa: BLE001
    pass

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import numpy as np

import config as C
import macro_fetch as F
import macro_indicators as I

# ─── 한글 폰트 ─────────────────────────────────────────────────────
for _f in ["Malgun Gothic", "맑은 고딕", "NanumGothic", "AppleGothic"]:
    try:
        plt.rcParams["font.family"] = _f
        break
    except Exception:  # noqa: BLE001
        continue
plt.rcParams["axes.unicode_minus"] = False

INK = "#1a2332"; MUTED = "#5b6b7f"; GRID = "#e3e8ef"
RED = "#e03131"; AMBER = "#f08c00"; GREEN = "#2f9e44"; BLUE = "#1971c2"
ACCENT = "#364fc7"


def _b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


# ─────────────────────────────────────────────────────────────────
# 차트
# ─────────────────────────────────────────────────────────────────
def chart_ratio(rr: I.RatioResult) -> str:
    fig, ax = plt.subplots(figsize=(9, 4.2))
    r = rr.ratio
    ax.plot(r.index, r.values, color=ACCENT, lw=1.6, zorder=5)
    m, s = rr.mean, rr.std
    ax.axhline(m, color=MUTED, lw=1, ls="--")
    ax.axhspan(m - s, m + s, color=GREEN, alpha=0.06)
    ax.axhspan(m + s, m + 2 * s, color=AMBER, alpha=0.08)
    ax.axhspan(m + 2 * s, r.max() * 1.05, color=RED, alpha=0.08)
    ax.text(r.index[0], m, f"  평균 {m:.1f}%", va="bottom", ha="left", color=MUTED, fontsize=9)
    # 최신·정점 표시
    ax.scatter([r.index[-1]], [r.iloc[-1]], color=RED, zorder=6, s=40)
    ax.annotate(f"{r.iloc[-1]:.1f}%", (r.index[-1], r.iloc[-1]),
                textcoords="offset points", xytext=(-6, 8), ha="right",
                color=RED, fontsize=10, fontweight="bold")
    pk = rr.latest["peak_date"]
    ax.annotate(f"사상최고 {rr.latest['peak_ratio']:.1f}%\n({pk:%Y-%m})",
                (pk, rr.latest["peak_ratio"]), textcoords="offset points",
                xytext=(6, -2), ha="left", color=MUTED, fontsize=8)
    # 10월 급락을 반영한 현재 추정치 (M2 이월) — 확정선과 구분해 별도 표시
    est_d = rr.latest["est_cap_date"]
    ax.scatter([est_d], [rr.latest["est_ratio"]], color=AMBER, zorder=6, s=38, marker="D")
    ax.annotate(f"급락반영 추정 {rr.latest['est_ratio']:.1f}%\n({est_d:%Y-%m})",
                (est_d, rr.latest["est_ratio"]), textcoords="offset points",
                xytext=(6, 4), ha="left", color=AMBER, fontsize=8, fontweight="bold")
    ax.set_title("① 코스피 시가총액 ÷ M2(광의통화) 비율", fontsize=12, color=INK, fontweight="bold", loc="left")
    ax.set_ylabel("%", color=MUTED)
    ax.grid(True, color=GRID, lw=0.6)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    for sp in ax.spines.values():
        sp.set_color(GRID)
    return _b64(fig)


def chart_cycle(cr: I.CycleResult) -> str:
    fig, ax = plt.subplots(figsize=(9, 4.2))
    s = cr.series
    ax.plot(s.index, s.values, color=GREEN, lw=1.6, zorder=5)
    ax.axhline(100, color=MUTED, lw=1, ls="--")
    ax.fill_between(s.index, 100, s.values, where=(s.values >= 100), color=GREEN, alpha=0.08)
    ax.fill_between(s.index, 100, s.values, where=(s.values < 100), color=RED, alpha=0.08)
    ax.scatter([s.index[-1]], [s.iloc[-1]], color=BLUE, zorder=6, s=40)
    ax.annotate(f"{s.iloc[-1]:.1f}", (s.index[-1], s.iloc[-1]),
                textcoords="offset points", xytext=(-6, 8), ha="right",
                color=BLUE, fontsize=10, fontweight="bold")
    if cr.latest["peak_flag"] and cr.latest["recent_peak_date"] is not None:
        pk = cr.latest["recent_peak_date"]
        ax.scatter([pk], [s.loc[pk]], color=RED, zorder=7, s=45, marker="v")
        ax.annotate(f"정점 유력\n({pk:%Y-%m})", (pk, s.loc[pk]),
                    textcoords="offset points", xytext=(6, 6), ha="left",
                    color=RED, fontsize=8, fontweight="bold")
    ax.set_title("② 선행지수 순환변동치 (100=장기추세)", fontsize=12, color=INK, fontweight="bold", loc="left")
    ax.grid(True, color=GRID, lw=0.6)
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    for sp in ax.spines.values():
        sp.set_color(GRID)
    return _b64(fig)


def chart_matrix(mx: I.MatrixResult) -> str:
    fig, ax = plt.subplots(figsize=(6.4, 6.0))
    h = mx.history.tail(24)
    # 사분면 배경
    ax.axhline(0, color=MUTED, lw=1)
    ax.axvline(C.Z_ELEVATED, color=MUTED, lw=1, ls="--")
    xlim = (min(-1.5, h["z"].min() - 0.5), max(3.0, h["z"].max() + 0.5))
    ylim_abs = max(5.0, abs(h["slope"]).max() * 1.2)
    ax.set_xlim(*xlim); ax.set_ylim(-ylim_abs, ylim_abs)
    # 분면 라벨
    ax.text(xlim[1] - 0.1, ylim_abs * 0.9, "과열·확장\n[위험]", ha="right", va="top", color=RED, fontsize=9, fontweight="bold")
    ax.text(xlim[1] - 0.1, -ylim_abs * 0.9, "과열해소·둔화\n[경계]", ha="right", va="bottom", color=AMBER, fontsize=9, fontweight="bold")
    ax.text(xlim[0] + 0.1, -ylim_abs * 0.9, "정상·수축\n[침체]", ha="left", va="bottom", color=BLUE, fontsize=9, fontweight="bold")
    ax.text(xlim[0] + 0.1, ylim_abs * 0.9, "정상·회복\n[우호]", ha="left", va="top", color=GREEN, fontsize=9, fontweight="bold")
    # 궤적
    ax.plot(h["z"], h["slope"], color=MUTED, lw=1, alpha=0.5, zorder=3)
    ax.scatter(h["z"], h["slope"], c=range(len(h)), cmap="viridis", s=18, zorder=4)
    ax.scatter([mx.x_z], [mx.y_slope], color=RED, s=120, zorder=6, edgecolor="white", linewidth=1.5)
    ax.annotate("현재", (mx.x_z, mx.y_slope), textcoords="offset points",
                xytext=(10, 6), color=RED, fontsize=11, fontweight="bold")
    ax.set_xlabel("밸류에이션 과열 (시총/M2 추세보정 Z) →", color=MUTED, fontsize=9)
    ax.set_ylabel("경기 모멘텀 (순환변동치 3개월변화) →", color=MUTED, fontsize=9)
    ax.set_title("③ 과열 × 사이클 2축 매트릭스 (최근 24개월)", fontsize=12, color=INK, fontweight="bold", loc="left")
    ax.grid(True, color=GRID, lw=0.5)
    for sp in ax.spines.values():
        sp.set_color(GRID)
    return _b64(fig)


# ─────────────────────────────────────────────────────────────────
# HTML
# ─────────────────────────────────────────────────────────────────
def build_html(rr, cr, mx, imgs: dict, m2_latest_date) -> str:
    L = rr.latest
    CY = cr.latest
    zd = L["z_detrended"]
    zd_txt = f"{zd:+.2f}σ" if zd == zd else "—"
    zcolor = RED if (zd == zd and zd >= C.Z_ELEVATED) else (GREEN if (zd == zd and zd <= -C.Z_ELEVATED) else MUTED)
    verdict = (
        f"현재 시장은 <b>{mx.quadrant}</b> 국면입니다. "
        f"밸류에이션(시총/M2)은 확정 최신 <b>{L['ratio']:.1f}%</b>({L['date']:%Y-%m}), "
        f"10월 급락을 반영한 추정은 <b>{L['est_ratio']:.1f}%</b> — "
        f"장기평균({rr.mean:.1f}%) 대비 추세보정 <b>{zd_txt}</b> "
        f"(역사적 상위 {100 - L['percentile']:.0f}%)로 {L['emoji']} <b>{L['label']}</b>. "
        f"경기 선행 사이클은 <b>{CY['phase']}</b> 국면"
        + (f"이며 <b>{CY['consec_down']}개월 연속 하락 → 정점(peak) 통과 유력</b>입니다."
           if CY["peak_flag"] else
           f"이며 {CY['consec_up']}개월 연속 상승으로 바닥 탈출이 진행 중입니다." if CY["trough_flag"]
           else f"로, 7월 고점({CY['value']:.1f} 부근) 뒤 모멘텀 둔화가 관찰됩니다.")
    )
    today = dt.date.today().strftime("%Y-%m-%d")

    def card(emoji, label, big, sub, color):
        return f"""<div class="card"><div class="ce" style="color:{color}">{emoji}</div>
<div class="cl">{label}</div><div class="cb" style="color:{color}">{big}</div>
<div class="cs">{sub}</div></div>"""

    cards = (
        card(L["emoji"], "밸류에이션(확정)", f"{L['ratio']:.1f}%",
             f"장기평균 {rr.mean:.1f}% 대비 · {L['date']:%Y-%m}", RED if zd == zd and zd >= 1 else GREEN)
        + card("📉", "현재 추정(급락반영)", f"{L['est_ratio']:.1f}%",
               f"시총 {L['est_cap_date']:%Y-%m}÷M2 {L['est_m2_date']:%Y-%m}", AMBER)
        + card("📏", "추세보정 Z", zd_txt,
               f"{L['label']} · 원시 {L['z']:+.1f}σ", zcolor)
        + card("🔻" if CY["peak_flag"] else "➡️", "경기 사이클", CY["phase"],
               f"순환변동치 {CY['value']:.1f} · 종합 {mx.quadrant}", BLUE)
    )

    return f"""<!doctype html><html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>매크로 밸류·사이클 대시보드</title>
<style>
:root{{--ink:{INK};--muted:{MUTED};--grid:{GRID};}}
*{{box-sizing:border-box}} body{{margin:0;background:#f5f7fa;color:var(--ink);
font-family:'Malgun Gothic','맑은 고딕',system-ui,sans-serif;line-height:1.6}}
.wrap{{max-width:980px;margin:0 auto;padding:28px 18px 60px}}
h1{{font-size:24px;margin:0 0 2px}} .sub{{color:var(--muted);font-size:13px;margin-bottom:20px}}
.verdict{{background:#fff;border:1px solid var(--grid);border-left:4px solid {ACCENT};
border-radius:10px;padding:16px 18px;margin-bottom:22px;font-size:15px}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin-bottom:26px}}
.card{{background:#fff;border:1px solid var(--grid);border-radius:12px;padding:14px;text-align:center}}
.ce{{font-size:22px}} .cl{{color:var(--muted);font-size:12px;margin:2px 0}}
.cb{{font-size:20px;font-weight:800}} .cs{{color:var(--muted);font-size:11px;margin-top:4px}}
.chart{{background:#fff;border:1px solid var(--grid);border-radius:12px;padding:12px;margin-bottom:18px}}
.chart img{{width:100%;display:block}}
.two{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}
.note{{font-size:12px;color:var(--muted);background:#fff;border:1px dashed var(--grid);
border-radius:10px;padding:14px 16px;margin-top:8px}}
.note b{{color:var(--ink)}}
@media(max-width:760px){{.cards{{grid-template-columns:repeat(2,1fr)}}.two{{grid-template-columns:1fr}}}}
</style></head><body><div class="wrap">
<h1>📊 매크로 밸류 · 사이클 대시보드</h1>
<div class="sub">코스피 시총/M2 과열도 × 경기 선행지수 순환변동치 · 생성일 {today}</div>
<div class="verdict">🧭 {verdict}</div>
<div class="cards">{cards}</div>
<div class="chart"><img src="data:image/png;base64,{imgs['ratio']}"></div>
<div class="chart"><img src="data:image/png;base64,{imgs['cycle']}"></div>
<div class="chart"><img src="data:image/png;base64,{imgs['matrix']}"></div>
<div class="note">
<b>데이터 출처</b> · M2(광의통화 평잔·원계열): 한국은행 ECOS 161Y006 — 최신 {m2_latest_date:%Y-%m}.
코스피 시가총액: KRX/marcap(일별 전종목 합산, 월말) — 최신 {L['est_cap_date']:%Y-%m-%d}.
선행지수 순환변동치: 한국은행 ECOS 901Y067 — 최신 {CY['date']:%Y-%m}.<br>
<b>유의</b> · ① M2·순환변동치는 월간이며 1~2개월 시차·사후개정이 있습니다(확정값 아님).
② M2 분모가 꾸준히 커져 비율의 장기평균선 자체가 우상향하므로, 단순 "평균회귀" 단정은 위험합니다 →
'추세보정 Z'(5년 롤링 기준)를 함께 보세요. ③ 정점/저점은 사후에만 확정됩니다
('{CY['consec_down']}개월 연속 하락=정점 유력'은 규칙 기반 잠정 판정).
④ 이 지표는 <b>중장기 국면 배경 필터</b>이지 단타 신호가 아닙니다 — 타이밍은 파동/피보나치 레이어가 담당.
</div>
</div></body></html>"""


def generate_html() -> str:
    """데이터 수집→계산→차트→HTML 문자열 생성 (파일 미기록)."""
    print("데이터 수집 중…")
    m2 = F.fetch_m2()
    cci = F.fetch_leading_cycle()
    cap = F.fetch_kospi_marketcap()
    print("지표 계산 중…")
    rr = I.compute_ratio_zscore(cap, m2)
    cr = I.compute_cycle_phase(cci)
    mx = I.compute_matrix(rr, cr)
    print("차트 생성 중…")
    imgs = {"ratio": chart_ratio(rr), "cycle": chart_cycle(cr), "matrix": chart_matrix(mx)}
    html = build_html(rr, cr, mx, imgs, m2.index[-1])
    # 콘솔 요약
    print(f"\n[밸류] 시총/M2 {rr.latest['ratio']:.1f}%  Z {rr.latest['z']:+.2f}σ  {rr.latest['emoji']} {rr.latest['label']}")
    print(f"[사이클] 순환변동치 {cr.latest['value']:.1f}  국면 {cr.latest['phase']}  (연속하락 {cr.latest['consec_down']}개월)")
    print(f"[종합] {mx.quadrant} — {mx.desc}")
    return html


def main():
    if not C.ECOS_KEY:
        raise SystemExit("ECOS_KEY가 없습니다. 환경변수 ECOS_KEY 또는 .ecos_key 파일을 설정하세요.")
    html = generate_html()
    out = C.OUT_DIR / "macro_dashboard.html"
    out.write_text(html, encoding="utf-8")
    print(f"완료 → {out}")
    # 콘솔 요약
    print(f"\n[밸류] 시총/M2 {rr.latest['ratio']:.1f}%  Z {rr.latest['z']:+.2f}σ  {rr.latest['emoji']} {rr.latest['label']}")
    print(f"[사이클] 순환변동치 {cr.latest['value']:.1f}  국면 {cr.latest['phase']}  (연속하락 {cr.latest['consec_down']}개월)")
    print(f"[종합] {mx.quadrant} — {mx.desc}")
    return out


if __name__ == "__main__":
    main()
