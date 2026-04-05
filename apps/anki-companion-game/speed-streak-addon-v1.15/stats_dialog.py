from __future__ import annotations

import json
from datetime import datetime
from typing import Any, Optional

from aqt import mw
from aqt.qt import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
    Qt,
    QVBoxLayout,
)
from aqt.webview import AnkiWebView

from .game_state import CompanionGameEngine
from .stats_store import StatsStore


_dialog: Optional["StatsDialog"] = None


class StatsDialog(QDialog):
    def __init__(self, engine: CompanionGameEngine, store: StatsStore) -> None:
        super().__init__(mw)
        self.engine = engine
        self.store = store

        self.setModal(True)
        self.setWindowTitle("Speed Streak Stats")
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setObjectName("speedStreakStatsDialog")
        self.setStyleSheet(
            """
            QDialog#speedStreakStatsDialog {
              background: rgba(4, 8, 20, 180);
            }
            QFrame#speedStreakStatsCard {
              background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                stop:0 rgba(7, 16, 34, 248),
                stop:1 rgba(8, 18, 39, 240));
              border: 1px solid rgba(140, 180, 255, 0.18);
              border-radius: 28px;
            }
            QPushButton#speedStreakStatsClose {
              background: rgba(255, 255, 255, 0.08);
              color: #eef3ff;
              border: 1px solid rgba(255, 255, 255, 0.12);
              border-radius: 18px;
              padding: 8px 12px;
              font-size: 18px;
              font-weight: 800;
            }
            QPushButton#speedStreakStatsClose:hover {
              background: rgba(255, 255, 255, 0.14);
            }
            """
        )

        outer = QVBoxLayout(self)
        outer.setContentsMargins(28, 28, 28, 28)

        card = QFrame(self)
        card.setObjectName("speedStreakStatsCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 20, 20, 20)
        card_layout.setSpacing(14)

        header = QHBoxLayout()
        header.addStretch(1)
        close_button = QPushButton("×", card)
        close_button.setObjectName("speedStreakStatsClose")
        close_button.setCursor(Qt.CursorShape.PointingHandCursor)
        close_button.clicked.connect(self.close)
        header.addWidget(close_button, 0, Qt.AlignmentFlag.AlignRight)
        card_layout.addLayout(header)

        self.web = AnkiWebView(card)
        self.web.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card_layout.addWidget(self.web, 1)

        outer.addWidget(card, 1)
        self.refresh()

        if mw is not None:
            self.resize(max(940, int(mw.width() * 0.92)), max(700, int(mw.height() * 0.9)))

    def refresh(self) -> None:
        payload = {
            "generatedAt": datetime.now().isoformat(timespec="seconds"),
            "currentRoundPauseMs": self.engine.current_round_pause_ms(),
            "pauseActive": self.engine.pause_counts_toward_stats(),
            "today": self.store.today_summary(),
            "overall": self.store.overall_summary(),
            "history": self.store.historical_daily_stats(),
        }
        self.web.setHtml(self._html(payload))

    def _html(self, payload: dict[str, Any]) -> str:
        data = json.dumps(payload)
        return f"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    :root {{
      --bg: #081126;
      --bg-2: #0d1933;
      --card: rgba(255,255,255,0.045);
      --line: rgba(255,255,255,0.12);
      --text: #edf3ff;
      --muted: #96a7cf;
      --blue: #7fb0ff;
      --green: #63f2c1;
      --red: #ff6f96;
      --yellow: #ffd978;
    }}
    * {{
      box-sizing: border-box;
    }}
    html, body {{
      margin: 0;
      min-height: 100%;
      background:
        radial-gradient(circle at top left, rgba(127,176,255,0.16), transparent 22%),
        radial-gradient(circle at top right, rgba(99,242,193,0.1), transparent 20%),
        linear-gradient(180deg, #071020 0%, #0a1630 100%);
      color: var(--text);
      font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      overflow: auto;
    }}
    body {{
      padding: 8px 10px 22px;
    }}
    .shell {{
      display: grid;
      gap: 16px;
    }}
    .hero {{
      display: flex;
      justify-content: space-between;
      gap: 16px;
      align-items: end;
      padding: 4px 2px 0;
    }}
    .title {{
      font-size: 34px;
      font-weight: 900;
      letter-spacing: -0.04em;
    }}
    .subtitle {{
      margin-top: 6px;
      color: var(--muted);
      font-size: 14px;
    }}
    .range-row {{
      display: inline-flex;
      gap: 8px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }}
    .range-btn {{
      border: 1px solid rgba(255,255,255,0.1);
      background: rgba(255,255,255,0.05);
      color: var(--text);
      border-radius: 999px;
      padding: 10px 14px;
      font-weight: 800;
      letter-spacing: 0.04em;
      cursor: pointer;
      transition: transform 160ms ease, background 160ms ease, border-color 160ms ease;
    }}
    .range-btn:hover {{
      transform: translateY(-1px);
      background: rgba(255,255,255,0.08);
    }}
    .range-btn.active {{
      background: linear-gradient(180deg, rgba(127,176,255,0.28), rgba(77,126,214,0.28));
      border-color: rgba(127,176,255,0.35);
      box-shadow: 0 10px 22px rgba(0,0,0,0.18);
    }}
    .summary-grid {{
      display: grid;
      gap: 14px;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }}
    .summary-card, .chart-card {{
      border: 1px solid var(--line);
      border-radius: 24px;
      background: var(--card);
      box-shadow: 0 20px 40px rgba(0,0,0,0.18);
      backdrop-filter: blur(10px);
    }}
    .summary-card {{
      padding: 18px 18px 16px;
    }}
    .summary-label {{
      color: var(--muted);
      text-transform: uppercase;
      font-size: 12px;
      letter-spacing: 0.12em;
      font-weight: 800;
    }}
    .summary-value {{
      margin-top: 10px;
      font-size: 32px;
      font-weight: 900;
      letter-spacing: -0.05em;
    }}
    .summary-sub {{
      margin-top: 8px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.4;
    }}
    .chart-grid {{
      display: grid;
      gap: 16px;
      grid-template-columns: 1.2fr 1fr;
    }}
    .chart-card {{
      padding: 18px;
      display: grid;
      gap: 16px;
      align-content: start;
    }}
    .chart-head {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: start;
    }}
    .chart-title {{
      font-size: 22px;
      font-weight: 900;
      letter-spacing: -0.03em;
    }}
    .chart-copy {{
      margin-top: 6px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.5;
    }}
    .chart-legend {{
      display: inline-flex;
      gap: 14px;
      flex-wrap: wrap;
      color: var(--muted);
      font-size: 13px;
      font-weight: 700;
    }}
    .legend-item {{
      display: inline-flex;
      gap: 8px;
      align-items: center;
    }}
    .legend-dot {{
      width: 10px;
      height: 10px;
      border-radius: 999px;
    }}
    .chart-surface {{
      min-height: 320px;
      border-radius: 20px;
      border: 1px solid rgba(255,255,255,0.08);
      background: linear-gradient(180deg, rgba(255,255,255,0.03), rgba(255,255,255,0.02));
      padding: 12px;
    }}
    .empty {{
      min-height: 320px;
      display: grid;
      place-items: center;
      color: var(--muted);
      text-align: center;
      padding: 24px;
      line-height: 1.6;
    }}
    .footer {{
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      color: var(--muted);
      font-size: 13px;
    }}
    .footer strong {{
      color: var(--text);
    }}
    svg {{
      width: 100%;
      height: 100%;
      overflow: visible;
    }}
    .tick {{
      fill: var(--muted);
      font-size: 12px;
      font-weight: 700;
    }}
    .grid-line {{
      stroke: rgba(255,255,255,0.08);
      stroke-width: 1;
    }}
    .axis-line {{
      stroke: rgba(255,255,255,0.14);
      stroke-width: 1.2;
    }}
    @media (max-width: 1080px) {{
      .summary-grid, .chart-grid {{
        grid-template-columns: 1fr;
      }}
      .hero {{
        flex-direction: column;
        align-items: start;
      }}
    }}
  </style>
</head>
<body>
  <div class="shell">
    <div class="hero">
      <div>
        <div class="title">Speed Streak Stats</div>
        <div class="subtitle">Pause time for this round, today's pacing, and long-term review trends.</div>
      </div>
      <div id="rangeRow" class="range-row"></div>
    </div>
    <div class="summary-grid">
      <div class="summary-card">
        <div class="summary-label">Current Round Paused</div>
        <div id="pauseValue" class="summary-value">0s</div>
        <div class="summary-sub">This resets when you reset the game. It includes the current pause if Speed Streak is paused right now.</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">Average Time / Card Today</div>
        <div id="todayAvg" class="summary-value">0.0s</div>
        <div id="todayAvgSub" class="summary-sub">No answered cards recorded today yet.</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">Today Correct</div>
        <div id="todayCorrect" class="summary-value">0%</div>
        <div id="todayCorrectSub" class="summary-sub">0 correct / 0 incorrect.</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">Recorded Reviews</div>
        <div id="overallCards" class="summary-value">0</div>
        <div id="overallCardsSub" class="summary-sub">Historical answered-card events tracked by Speed Streak.</div>
      </div>
      <div class="summary-card">
        <div class="summary-label">Longest Streak</div>
        <div id="longestStreak" class="summary-value">0</div>
        <div id="longestStreakSub" class="summary-sub">Today's best: 0. Build your first recorded streak.</div>
      </div>
    </div>
    <div class="chart-grid">
      <div class="chart-card">
        <div class="chart-head">
          <div>
            <div class="chart-title">Average Time Per Card</div>
            <div class="chart-copy">Daily average response time based on answered cards. The range controls above let you zoom the chart in or out.</div>
          </div>
        </div>
        <div id="timeChart" class="chart-surface"></div>
        <div id="timeFooter" class="footer"></div>
      </div>
      <div class="chart-card">
        <div class="chart-head">
          <div>
            <div class="chart-title">Correct vs Incorrect</div>
            <div class="chart-copy">Daily accuracy split. Again counts as incorrect. Hard, Good, and Easy count as correct.</div>
          </div>
          <div class="chart-legend">
            <span class="legend-item"><span class="legend-dot" style="background: var(--green);"></span>Correct</span>
            <span class="legend-item"><span class="legend-dot" style="background: var(--red);"></span>Incorrect</span>
          </div>
        </div>
        <div id="accuracyChart" class="chart-surface"></div>
        <div id="accuracyFooter" class="footer"></div>
      </div>
    </div>
  </div>
  <script>
    const payload = {data};
    const RANGE_OPTIONS = [
      {{ id: "7", label: "7D", days: 7 }},
      {{ id: "30", label: "30D", days: 30 }},
      {{ id: "90", label: "90D", days: 90 }},
      {{ id: "all", label: "All", days: 0 }},
    ];
    let activeRange = payload.history.length > 90 ? "90" : (payload.history.length > 30 ? "30" : "7");

    function formatSeconds(ms) {{
      return `${{(Number(ms || 0) / 1000).toFixed(1)}}s`;
    }}

    function formatPercent(value) {{
      return `${{Number(value || 0).toFixed(0)}}%`;
    }}

    function currentPauseMs() {{
      const base = Number(payload.currentRoundPauseMs || 0);
      if (!payload.pauseActive) {{
        return base;
      }}
      const openedAt = new Date(payload.generatedAt).getTime();
      return base + Math.max(0, Date.now() - openedAt);
    }}

    function visibleSeries() {{
      const all = Array.isArray(payload.history) ? payload.history.slice() : [];
      const option = RANGE_OPTIONS.find((item) => item.id === activeRange) || RANGE_OPTIONS[0];
      if (!option.days || all.length <= option.days) {{
        return all;
      }}
      return all.slice(-option.days);
    }}

    function renderRangeButtons() {{
      const row = document.getElementById("rangeRow");
      row.innerHTML = RANGE_OPTIONS.map((option) =>
        `<button class="range-btn${{option.id === activeRange ? " active" : ""}}" data-range="${{option.id}}">${{option.label}}</button>`
      ).join("");
      row.querySelectorAll(".range-btn").forEach((button) => {{
        button.addEventListener("click", () => {{
          activeRange = button.dataset.range;
          render();
        }});
      }});
    }}

    function buildTimeChart(series) {{
      if (!series.length) {{
        return '<div class="empty">No answered-card history yet.<br>Once you review cards with Speed Streak on, this chart will appear here.</div>';
      }}
      const width = 680;
      const height = 320;
      const pad = {{ top: 18, right: 18, bottom: 42, left: 48 }};
      const innerW = width - pad.left - pad.right;
      const innerH = height - pad.top - pad.bottom;
      const values = series.map((row) => Number(row.avgActiveMs || 0) / 1000);
      const maxValue = Math.max(5, ...values.map((value) => Math.ceil(value)));
      const points = values.map((value, index) => {{
        const x = pad.left + (series.length === 1 ? innerW / 2 : (innerW * index) / (series.length - 1));
        const y = pad.top + innerH - ((value / maxValue) * innerH);
        return `${{x.toFixed(1)}},${{y.toFixed(1)}}`;
      }});
      const areaPoints = [`${{pad.left}},${{pad.top + innerH}}`, ...points, `${{pad.left + innerW}},${{pad.top + innerH}}`].join(" ");
      const grid = [0, 0.25, 0.5, 0.75, 1].map((ratio) => {{
        const y = pad.top + innerH - (innerH * ratio);
        const value = (maxValue * ratio).toFixed(1);
        return `
          <line class="grid-line" x1="${{pad.left}}" y1="${{y}}" x2="${{pad.left + innerW}}" y2="${{y}}"></line>
          <text class="tick" x="${{pad.left - 10}}" y="${{y + 4}}" text-anchor="end">${{value}}s</text>
        `;
      }}).join("");
      const labels = series.map((row, index) => {{
        const show = series.length <= 7 || index === 0 || index === series.length - 1 || index === Math.floor(series.length / 2);
        if (!show) {{
          return "";
        }}
        const x = pad.left + (series.length === 1 ? innerW / 2 : (innerW * index) / (series.length - 1));
        return `<text class="tick" x="${{x}}" y="${{height - 12}}" text-anchor="middle">${{row.day.slice(5)}}</text>`;
      }}).join("");
      const pointDots = points.map((point, index) => {{
        const [x, y] = point.split(",");
        const row = series[index];
        return `<circle cx="${{x}}" cy="${{y}}" r="4" fill="var(--blue)"><title>${{row.day}}: ${{(Number(row.avgActiveMs || 0) / 1000).toFixed(1)}}s average over ${{row.cards}} cards</title></circle>`;
      }}).join("");
      return `
        <svg viewBox="0 0 ${{width}} ${{height}}" role="img" aria-label="Average time per card chart">
          ${{grid}}
          <line class="axis-line" x1="${{pad.left}}" y1="${{pad.top + innerH}}" x2="${{pad.left + innerW}}" y2="${{pad.top + innerH}}"></line>
          <polygon points="${{areaPoints}}" fill="rgba(127,176,255,0.16)"></polygon>
          <polyline points="${{points.join(" ")}}" fill="none" stroke="var(--blue)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></polyline>
          ${{pointDots}}
          ${{labels}}
        </svg>
      `;
    }}

    function buildAccuracyChart(series) {{
      if (!series.length) {{
        return '<div class="empty">No accuracy history yet.<br>Once you answer cards, your historical correctness will show here.</div>';
      }}
      const width = 620;
      const height = 320;
      const pad = {{ top: 18, right: 18, bottom: 42, left: 48 }};
      const innerW = width - pad.left - pad.right;
      const innerH = height - pad.top - pad.bottom;
      const correctPoints = series.map((row, index) => {{
        const value = Number(row.correctPct || 0);
        const x = pad.left + (series.length === 1 ? innerW / 2 : (innerW * index) / (series.length - 1));
        const y = pad.top + innerH - ((value / 100) * innerH);
        return `${{x.toFixed(1)}},${{y.toFixed(1)}}`;
      }});
      const incorrectPoints = series.map((row, index) => {{
        const value = Number(row.incorrectPct || 0);
        const x = pad.left + (series.length === 1 ? innerW / 2 : (innerW * index) / (series.length - 1));
        const y = pad.top + innerH - ((value / 100) * innerH);
        return `${{x.toFixed(1)}},${{y.toFixed(1)}}`;
      }});
      const grid = [0, 25, 50, 75, 100].map((value) => {{
        const y = pad.top + innerH - ((value / 100) * innerH);
        return `
          <line class="grid-line" x1="${{pad.left}}" y1="${{y}}" x2="${{pad.left + innerW}}" y2="${{y}}"></line>
          <text class="tick" x="${{pad.left - 10}}" y="${{y + 4}}" text-anchor="end">${{value}}%</text>
        `;
      }}).join("");
      const labels = series.map((row, index) => {{
        const show = series.length <= 7 || index === 0 || index === series.length - 1 || index === Math.floor(series.length / 2);
        if (!show) {{
          return "";
        }}
        const x = pad.left + (series.length === 1 ? innerW / 2 : (innerW * index) / (series.length - 1));
        return `<text class="tick" x="${{x}}" y="${{height - 12}}" text-anchor="middle">${{row.day.slice(5)}}</text>`;
      }}).join("");
      const dots = series.map((row, index) => {{
        const [cx, cy] = correctPoints[index].split(",");
        const [ix, iy] = incorrectPoints[index].split(",");
        return `
          <circle cx="${{cx}}" cy="${{cy}}" r="3.6" fill="var(--green)">
            <title>${{row.day}}: ${{Number(row.correctPct || 0).toFixed(0)}}% correct (${{row.correctCards}} / ${{row.cards}})</title>
          </circle>
          <circle cx="${{ix}}" cy="${{iy}}" r="3.6" fill="var(--red)">
            <title>${{row.day}}: ${{Number(row.incorrectPct || 0).toFixed(0)}}% incorrect (${{row.incorrectCards}} / ${{row.cards}})</title>
          </circle>
        `;
      }}).join("");
      return `
        <svg viewBox="0 0 ${{width}} ${{height}}" role="img" aria-label="Correct versus incorrect chart">
          ${{grid}}
          <line class="axis-line" x1="${{pad.left}}" y1="${{pad.top + innerH}}" x2="${{pad.left + innerW}}" y2="${{pad.top + innerH}}"></line>
          <polyline points="${{correctPoints.join(" ")}}" fill="none" stroke="var(--green)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></polyline>
          <polyline points="${{incorrectPoints.join(" ")}}" fill="none" stroke="var(--red)" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"></polyline>
          ${{dots}}
          ${{labels}}
        </svg>
      `;
    }}

    function renderSummaries(series) {{
      const today = payload.today || {{}};
      const overall = payload.overall || {{}};
      document.getElementById("pauseValue").textContent = formatSeconds(currentPauseMs());
      document.getElementById("todayAvg").textContent = formatSeconds(today.avgActiveMs || 0);
      document.getElementById("todayAvgSub").textContent = today.cards
        ? `${{today.cards}} answered cards recorded today.`
        : "No answered cards recorded today yet.";
      document.getElementById("todayCorrect").textContent = formatPercent(today.correctPct || 0);
      document.getElementById("todayCorrectSub").textContent = `${{today.correctCards || 0}} correct / ${{today.incorrectCards || 0}} incorrect.`;
      document.getElementById("overallCards").textContent = String(overall.cards || 0);
      document.getElementById("overallCardsSub").textContent = overall.cards
        ? `${{formatSeconds(overall.avgActiveMs || 0)}} avg time, ${{formatPercent(overall.correctPct || 0)}} correct overall.`
        : "Historical answered-card events tracked by Speed Streak.";
      const overallLongestStreak = Number(overall.longestStreak || 0);
      const todayLongestStreak = Number(today.longestStreak || 0);
      document.getElementById("longestStreak").textContent = String(overallLongestStreak);
      document.getElementById("longestStreakSub").textContent = overallLongestStreak
        ? `Today's best: ${{todayLongestStreak}}. Best recorded run so far.`
        : `Today's best: ${{todayLongestStreak}}. Build your first recorded streak.`;

      const totalCards = series.reduce((sum, row) => sum + Number(row.cards || 0), 0);
      const avgMs = totalCards
        ? series.reduce((sum, row) => sum + (Number(row.avgActiveMs || 0) * Number(row.cards || 0)), 0) / totalCards
        : 0;
      const correct = series.reduce((sum, row) => sum + Number(row.correctCards || 0), 0);
      const incorrect = series.reduce((sum, row) => sum + Number(row.incorrectCards || 0), 0);

      document.getElementById("timeFooter").innerHTML = totalCards
        ? `<span><strong>${{series.length}}</strong> day${{series.length === 1 ? "" : "s"}} visible</span><span><strong>${{formatSeconds(avgMs)}}</strong> weighted average</span>`
        : `<span>No visible data yet.</span><span></span>`;
      document.getElementById("accuracyFooter").innerHTML = totalCards
        ? `<span><strong>${{correct}}</strong> correct</span><span><strong>${{incorrect}}</strong> incorrect</span>`
        : `<span>No visible data yet.</span><span></span>`;
    }}

    function render() {{
      renderRangeButtons();
      const series = visibleSeries();
      document.getElementById("timeChart").innerHTML = buildTimeChart(series);
      document.getElementById("accuracyChart").innerHTML = buildAccuracyChart(series);
      renderSummaries(series);
    }}

    render();
    if (payload.pauseActive) {{
      window.setInterval(() => {{
        document.getElementById("pauseValue").textContent = formatSeconds(currentPauseMs());
      }}, 250);
    }}
    window.addEventListener("resize", render);
  </script>
</body>
</html>
"""


def open_stats_dialog(engine: CompanionGameEngine, store: StatsStore) -> None:
    global _dialog
    if _dialog is None:
        _dialog = StatsDialog(engine, store)
    else:
        _dialog.engine = engine
        _dialog.store = store
        _dialog.refresh()

    _dialog.show()
    _dialog.raise_()
    _dialog.activateWindow()
