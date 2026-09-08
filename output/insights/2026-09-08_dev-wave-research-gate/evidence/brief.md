# 段 1 brief — dev-wave の過剰実装・過剰ガードレール抑止を強化する (wave: dev-wave-research-gate)

## 研究前進 (この wave 自身への P1 適用)
この wave は論文を直接進めない。土台側の正当化は実測: 直近 4 日 (2026-09-05〜08) の wave 61 本のうち
研究前進 ≈27 / 土台・工程 ≈34 (うち新規 gate・binding・enforcement ≈9、insight 名による粗分類)。
直近 1 週間 (09-01→09-08、main) で製品 +67,219/−2,230 行、テスト +73,174/−1,942 行、削除された .py は
2 週間で 2 file。decisions は 1 日 25〜111 件 (D1791 まで)、failures F902、worklog 持ち越し T 345 件。
ユーザーは 2026-09-08 に「研究開発の遅滞」「土台にゴミを入れたら掃除が要る」を明示した。

## scope
docs-only。`docs/dev-wave/core.md` の `DW-S01` に P1 を収容する。P3 / P5 は本相談後に親が統合判断する。
実装面 (コード・テスト・tool・`tools/check_docs.py` の定数を含む) は触らない。増枠が不可避なら別途報告する。

## 確定済みユーザー裁定 (2026-09-08)
- P1 採用: 段 1 brief に「研究前進の 1 行」を必須化。論文の主張・図表・実験節の何を進めるか、土台なら
  「今止まっている研究の実測」を書く。どちらも書けない wave は開始しない (fail-closed)。
- P3 (段 7 記録に wave の純増 1 行: 製品行 / テスト行 / 新規 tool / 新規 gate) と
  P5 (実装面差分が削除だけの wave は変異免除、`DW-G05` を逆向きに適用: 削除で失われる成果物影響を
  1 行で書けなければ消してよい) は「codex に相談して統合判断」。
- P2 (段 3/6 に過剰・削除レンズ) / P4 (変異 matrix を防壁・台帳・受入判定の実装面に限定) /
  P6 (所見→T 起票の出口) は今回未選択。実装せず裁定候補として記録する。
- 予算は D782 の手順を親が回す: 既存記述の削減 (D227: 同一読点で読まれる上位互換節との重複だけが原資)
  → 無理なら層ごと最小増枠して報告。

## 不変条件
- 絶対規律 1〜7 は不変。安全義務を予算のために削除・弱化しない (`docs/skill-self-improvement.md`)。
- 層予算: L1 ≤ 10,625 bytes (現在 10,594、残 31)、L1.5 ≤ 9,696 (現在 9,694、残 2)、L2 節 ≤ 1,000。
  節 bytes 実測: core.md preamble 108 / C00 1060 / C01 996 / STOP 577 / S01 1360 / G01 256 / G02 251 /
  G03 256 / G04 227 / G05 821 / S04 1025 / S07 1244 / S08 226 / S09 410 / CTX 875。
  L1 = core の U 節 + mutation preamble 109 + M01 523 + operations preamble 205 + O23 1061。
- `tools/check_docs.py` の逐語 pin (1 byte も動かせない): DW-C01 の見出し〜先頭 2 行、DW-C00 の
  「待ち手は 1 条件 1 本とし、通知ごとに作り直さず `tools/dev_wave_wait.py` を使う。」、
  「実装面があれば段 5 の Codex 実装子と fix 子は」「親は直接編集しない」、DW-S09 の
  「`tools/dev_wave_land.py` は local main を変更する唯一の通常 land 経路」と
  「全 commit・受入結果を固定し、tested main/tip と監査 commit 列を実測して 」「`DW-O23` を行う。」。
  workers.md: 「codex は `reasoning=xhigh`、`sandbox=workspace-write` とする。」
  「実装 wave は異なるレンズの敵対レビューを `reasoning=xhigh` で必ず 2 本並列で行う。」
  「並列 fix の統合後、焦点再レビューは全体へ `reasoning=xhigh` で 1 本でよい。」
  「実装面に Codex `role=author` のないハンク」「親が直接直さない」。
- 入口 `.claude/commands/dev-wave.md` は触らない (節全体 exact / regex 構造 pin が多数)。

## 成果物の形
- `docs/dev-wave/core.md` の差分 (DW-S01 への P1 文。P3 を採るなら DW-S07、P5 を採るなら DW-S04/DW-M01)
- decisions fragment (P1 採用と P3/P5 の判断、P2/P4/P6 の記録)、worklog fragment、insight (逐語)
- `python3 tools/check_docs.py` rc=0

## 分割方針
docs-only のため実装子なし。read-only consult 2 本 (レンズ A = 実効性、レンズ B = 整合・予算)。

## 変更面 (実アンカー)
| file | 節 | 現 bytes | 役割 |
|---|---|---|---|
| docs/dev-wave/core.md | `## DW-S01 — 段 1 brief` | 1360 | P1 の収容先 (第一候補) |
| docs/dev-wave/core.md | `## DW-G05 — 成果物影響` | 821 | 第二候補 (過剰実装の既存規範がある) |
| docs/dev-wave/core.md | `## DW-S07 — 段 7 記録` | 1244 | P3 を採る場合 |
| docs/dev-wave/core.md | `## DW-S04 — 段 4 裁定` | 1025 | P5 を採る場合 (変異免除の条件文) |
| docs/dev-wave/core.md | `## DW-CTX` | 875 | 削減候補 (入口と重複する文があるか) |

## 親の provisional 裁定 (攻撃対象)
- (P1) 段 1 に「研究前進 1 行」を必須化すれば、親の自己申告でも土台 wave の流入が減る。
  疑い: 何でも「研究のため」と書けて恒真化する / `DW-C00`「command 引数は worklog 候補より優先」と
  無人 supervisor 経路 (`DW-CTX`) が逃げ道になる / 書けない wave を「開始しない」ことと、ユーザーが
  明示起動した wave の扱いが衝突する。
- (P2) 収容先は DW-S01 で、必要 bytes (約 120〜160) は L1 内の D227 準拠の重複削減で捻出できる。
- (P3) P3 (純増 1 行) は可視化のみで抑止にならず見送りが妥当。反論: 観測が無ければ P1 の効果も測れない。
- (P4) P5 は規律 2 / `DW-M01` と衝突しない (削除だけの差分は受理集合を広げない) が、既存
  `DW-S04`「実装面の差分ゼロの wave だけ変異 matrix を免除」との関係で二義化しないか。
- (P5) 既存正本 (D205 / `DW-G05` 第 2 段落 / next-tasks「常設の前提」) と P1 は重複でなく純増である
  (dev-wave は引数を優先するので next-tasks の篩を通らない wave が存在する)。

## 模擬 / 実の差
節 bytes と pin は `tools/check_docs.py` の関数で実測した値。wave 分類 (研究 / 土台) は insight 名による
粗分類で、1 件ずつの読解はしていない。
