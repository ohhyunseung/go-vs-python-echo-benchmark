import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.gridspec as gridspec
import matplotlib.font_manager as fm
import glob
import os
import re

# ── 한글 폰트 등록 ─────────────────────────────────────────────────────────
def find_noto_cjk():
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/noto/NotoSansCJK-Regular.ttc",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path
    result = glob.glob("/usr/share/fonts/**/NotoSansCJK*.ttc", recursive=True)
    return result[0] if result else None

font_path = find_noto_cjk()
if font_path:
    fm.fontManager.addfont(font_path)
    plt.rcParams["font.family"] = "Noto Sans CJK JP"
else:
    # 시스템에 등록된 CJK 계열 폰트 자동 탐색
    cjk_names = ["Noto Sans CJK JP", "Noto Sans CJK KR", "NanumGothic",
                 "Malgun Gothic", "AppleGothic", "WenQuanYi Micro Hei"]
    available = {f.name for f in fm.fontManager.ttflist}
    found = next((n for n in cjk_names if n in available), None)
    if found:
        plt.rcParams["font.family"] = found
    else:
        print("경고: 한글 폰트를 찾지 못했습니다. 'apt install fonts-noto-cjk' 로 설치하세요.")

plt.rcParams["axes.unicode_minus"] = False

# ── 데이터 ─────────────────────────────────────────────────────────────────

def load_data_from_log(log_name, prefix, target_active=1000, target_total=1000, limit=50):
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(base_dir, log_name)
    if not os.path.exists(log_path):
        return None

    escaped_prefix = re.escape(prefix)
    pattern = re.compile(
        rf"^(?:.*?){escaped_prefix}\s+active=(\d+)\s+total=(\d+)\s+msg/s=(\d+)\s+MB/s=([0-9.]+)"
    )
    values = []

    with open(log_path, encoding="utf-8", errors="ignore") as f:
        for line in f:
            m = pattern.search(line)
            if not m:
                continue
            if int(m.group(1)) == target_active and int(m.group(2)) == target_total:
                values.append(int(m.group(3)))
                if len(values) >= limit:
                    break

    return values if values else None

py_data = load_data_from_log("py_svr.log", "[PY]")
print(f"Python 데이터 포인트 수: {len(py_data) if py_data else 0}")

go_data = load_data_from_log("go_svr.log", "[GO]")
print(f"Go 데이터 포인트 수: {len(go_data) if go_data else 0}")

PY_COLOR   = "#378ADD"
GO_COLOR   = "#1D9E75"
BG_COLOR   = "#FAFAFA"
GRID_COLOR = "#E8E8E8"

plt.rcParams.update({
    "axes.facecolor":     BG_COLOR,
    "figure.facecolor":   "white",
    "axes.grid":          True,
    "grid.color":         GRID_COLOR,
    "grid.linewidth":     0.8,
    "axes.spines.top":    False,
    "axes.spines.right":  False,
    "axes.spines.left":   False,
    "axes.spines.bottom": False,
    "xtick.color":        "#888",
    "ytick.color":        "#888",
    "axes.labelcolor":    "#555",
    "axes.titlesize":     13,
    "axes.titleweight":   "bold",
    "axes.titlepad":      10,
})

fig = plt.figure(figsize=(13, 14))
fig.suptitle(
    "Python (uvloop) vs Go — mTLS TLS 1.3 Echo Server\n1,000 동시 연결 기준",
    fontsize=15, fontweight="bold", color="#222", y=0.98,
)
gs = gridspec.GridSpec(3, 1, figure=fig, hspace=0.52)

py_patch = mpatches.Patch(color=PY_COLOR, label="Python (uvloop)")
go_patch = mpatches.Patch(color=GO_COLOR, label="Go")

# ── 1. 시계열 ─────────────────────────────────────────────────────────────
ax1 = fig.add_subplot(gs[0])
t_py = np.arange(1, len(py_data) + 1)
t_go = np.arange(1, len(go_data) + 1)

ax1.plot(t_py, py_data, color=PY_COLOR, linewidth=2, marker="o", markersize=4, zorder=3)
ax1.plot(t_go, go_data, color=GO_COLOR, linewidth=2, marker="s", markersize=3, linestyle="--", zorder=3)
ax1.fill_between(t_py, py_data, alpha=0.10, color=PY_COLOR)
ax1.fill_between(t_go, go_data, alpha=0.10, color=GO_COLOR)
ax1.axhline(np.mean(py_data), color=PY_COLOR, linewidth=1, linestyle=":", alpha=0.7)
ax1.axhline(np.mean(go_data), color=GO_COLOR, linewidth=1, linestyle=":", alpha=0.7)
ax1.set_title("① 시계열 — 초당 메시지 처리량 (msg/s)")
ax1.set_xlabel("측정 시각 (초)")
ax1.set_ylabel("msg/s")
ax1.set_xlim(0, max(len(go_data), len(py_data)) + 1)
ax1.set_ylim(0, 8500)
ax1.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax1.legend(handles=[py_patch, go_patch], fontsize=10, loc="upper right", framealpha=0.8)

# ── 2. 박스플롯 ───────────────────────────────────────────────────────────
ax2 = fig.add_subplot(gs[1])
bp = ax2.boxplot(
    [py_data, go_data], vert=True, patch_artist=True, widths=0.45, showfliers=True,
    medianprops=dict(linewidth=2.5), whiskerprops=dict(linewidth=1.5),
    capprops=dict(linewidth=1.5),
    flierprops=dict(marker="o", markersize=5, linestyle="none"),
    boxprops=dict(linewidth=1.5),
)
for patch, color in zip(bp["boxes"], [PY_COLOR, GO_COLOR]):
    patch.set_facecolor(color + "33")
    patch.set_edgecolor(color)
for median, color in zip(bp["medians"], [PY_COLOR, GO_COLOR]):
    median.set_color(color)
for i, color in enumerate([PY_COLOR, GO_COLOR]):
    bp["whiskers"][i*2].set_color(color)
    bp["whiskers"][i*2+1].set_color(color)
    bp["caps"][i*2].set_color(color)
    bp["caps"][i*2+1].set_color(color)
    bp["fliers"][i].set_markerfacecolor(color)
    bp["fliers"][i].set_markeredgecolor(color)

ax2.set_xticks([1, 2])
ax2.set_xticklabels(["Python (uvloop)", "Go"], fontsize=11)
ax2.set_title("② 박스플롯 — 분포 및 이상치")
ax2.set_ylabel("msg/s")
ax2.set_ylim(0, 8500)
ax2.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
stats_text = (
    f"Python  중앙값 {int(np.median(py_data)):,}  "
    f"IQR {int(np.percentile(py_data,75)-np.percentile(py_data,25)):,}\n"
    f"Go          중앙값 {int(np.median(go_data)):,}  "
    f"IQR {int(np.percentile(go_data,75)-np.percentile(go_data,25)):,}"
)
ax2.text(0.97, 0.04, stats_text, transform=ax2.transAxes,
         fontsize=9, color="#555", ha="right", va="bottom",
         bbox=dict(boxstyle="round,pad=0.4", fc="white", alpha=0.7, ec=GRID_COLOR))

# ── 3. 히스토그램 ─────────────────────────────────────────────────────────
ax3 = fig.add_subplot(gs[2])
bins = np.arange(1500, 8001, 500)
ax3.hist(py_data, bins=bins, color=PY_COLOR, alpha=0.75, edgecolor="white", linewidth=0.5)
ax3.hist(go_data, bins=bins, color=GO_COLOR, alpha=0.75, edgecolor="white", linewidth=0.5)
ax3.set_title("③ 히스토그램 — 구간별 빈도 분포")
ax3.set_xlabel("msg/s 구간")
ax3.set_ylabel("빈도 (회)")
ax3.set_xlim(1000, 8200)
ax3.xaxis.set_major_formatter(plt.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax3.legend(handles=[py_patch, go_patch], fontsize=10, loc="upper right", framealpha=0.8)
ax3.annotate("Python 집중\n(2,000~3,000)", xy=(2500, 9), xytext=(2500, 13),
             arrowprops=dict(arrowstyle="->", color=PY_COLOR, lw=1.3),
             fontsize=9, color=PY_COLOR, ha="center")
ax3.annotate("Go 집중\n(5,500~7,000)", xy=(6250, 14), xytext=(6250, 18),
             arrowprops=dict(arrowstyle="->", color=GO_COLOR, lw=1.3),
             fontsize=9, color=GO_COLOR, ha="center")

# ── 저장 ───────────────────────────────────────────────────────────────────
out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "performance_charts.png")
plt.savefig(out_path, dpi=150, bbox_inches="tight")
print(f"저장 완료: {out_path}")