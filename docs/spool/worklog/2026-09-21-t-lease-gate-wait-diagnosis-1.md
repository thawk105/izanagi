---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: t-lease-gate-wait-diagnosis
seq: 1
title: 受入門番 (leaders ≤ 1 ∧ load ≤ 60 + jitter) で wave が待った時間を門番 log から実測した — 直近 20 wave の待ちは 1 回中央値 152.5 秒 (構造下限に近い)、30 分以上の観測待ちは 1 区間、9/19 以降 79 wave では 30 分以上が 39 区間・飢餓候補 5 件。閉門の大半は leaders 条件で、その推定分の約半分 (1003.0 / 2049.3 分) は記録上の走行中受入が 1 本以下だった。緩和 4 択 + 別枠をユーザー裁定へ返す (診断のみ・実装 0 行、insight、branch worktree-t-lease-gate-wait-diagnosis、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「受入 lease の門番 (leaders ≤ 1 ∧ load ≤ 60 + jitter) で wave が待った時間を、直近 20 wave の acceptance-*.wait-receipt.json / wait.log (job dir) と lease directory の記録から実測する (診断のみ、着手直前の local main から fresh worktree)。待ち時間の分布、同時に待った wave 数、開いた瞬間の leaders / load、飢餓 (同条件で 3 本以上が待つと開かない、2026-09-20 [T-2610]) の発生回数を出す。門番の閾値・周期・lease TTL の変更はユーザー裁定 (memory 正本) なので、緩和案 (閾値、jitter、周期の位相、優先順) を効果見積り付きの裁定パッケージにして実装しない。lease の primitive と待ち手の正本は変えない。規律 2 を緩めない。診断だけ。gate・台帳・一般化の追加は scope 外」。
- **閉じた (数表と裁定パッケージを insight に置いた。repo の実装面差分 0 行、段 4 → 5 (probe の author) → 6 (fix 4 巡 + レビュー + 焦点) → 7)。** 一次資料は `output/insights/2026-09-21/acceptance-gate-wait-diagnosis/README.md` (段 1〜6 の逐語、probe の逐語と sha256、最終走の出力と生 stdout を同 dir に凍結)。decisions fragment 0 (裁定パッケージは提案であり採用済み判断ではない)、failures fragment 0。
- **依頼の前提 2 つが成立しなかった (brief 前の実測、07:39 JST)。** lease dir (`dev-wave-jobs/land-lease/`) は stale ticket 1 件だけで履歴を持たず、`tools/wave_land_window.py` も単一 lease の作成・更新・削除しか書かない。`acceptance-*.wait-receipt.json` (producer receipt、key は artifact / done の mtime_ns) と `acceptance-receipt-*.json` (待ち手発行、24 key) にも待ちの開始・終了時刻が無い。待ち時間を復元できる一次資料は各 wave が job dir に手書きした門番 log (chain 型 / loop 型の 2 形式) だけだった。
- 主判定 (probe の最終走、`--until 2026-09-21T07:37:00+09:00` で着手時刻に締め、本 wave を除外、門番 log 126 file / 79 wave / 467 区間、self-check 4/4 passed): **直近 20 wave** (選択キー 9/20 21:20:32〜9/21 04:57:50、集合は brief 時点の記録と一致) の観測待ちは n=34 で中央値 152.5 秒 / p90 642 秒 / 最大 4838 秒、wave あたりの和は中央値 316 秒 / 合計 12,507 秒。中央値は門番の構造下限 (周期 100〜140 秒 1 回 + 乱数 0〜45 秒) に近く、模型の開門候補から実投入までの差は中央値 20 秒・最大 44 秒。30 分以上の観測待ちは 1 区間、飢餓候補 0。**9/19 以降の 79 wave** では n=147 で中央値 261 秒 / p90 3157 秒 / 最大 9317 秒、30 分以上が 39 区間 (打切り 3)、飢餓候補 (30 分以上 ∧ 同区間の再カウント拒否 ≥ 2) が 5 件 (打切り 2)。
- **閉門の大半は leaders 条件だった** (9/19 以降: leaders-only 973 tick / 推定 1938.4 分、both 55 / 110.9、load-only 22 / 45.0、unknown 87 / 154.8、open 503 / 768.1)。**新事実:** leaders 起因閉門 1028 tick のうち 502 tick (推定 1003.0 分 = 2049.3 分の約 48.9%) は、その時刻に started→finished の走行が 1 本以下だった。maxl=1 で閉じるには記録 leaders ≥ 2 が要るので、記録どうしが合っていない。候補は (a) 部分文字列一致の数え方による偽 leader、(b) 記録の残らない走行、(c) started/finished の欠落で、断定しない (部分文字列一致の門番で 945 tick 中 470、argv 先頭一致でも 83 tick 中 32 が不一致)。
- 開いた瞬間は、直近 20 で GO 直前 leaders が 0 本 17 回 / 1 本 16 回 / 2 本 1 回 (maxl=2 の門番)、load1 は中央値 4.47・最大 38.55 で条件 60 を大きく下回る。同時待ちは直近 20 で 0 本 28 回 / 1 本 5 / 2 本 1。9/19 以降では他に 3 本以上の記録上の待ちがあっても投入に至った例が 51 回あり、依頼の「同条件で 3 本以上が待つと開かない」はこの資料の範囲では文字どおりには成り立たない (条件変種を含む集計で、「同条件で 3 本」を抽出した件数ではない)。
- **[T-2610] は 233 分の連続飢餓ではなかった。** 50 分 21 秒の打切り区間 (再カウント拒否 2 回、飢餓候補) + 168 分 27 秒の記録の空白 (門番 loop の kill と再起動が分類器に拒否された期間) + 再起動後 14 分 13 秒 (8 tick 中 6 tick が load1 60.62〜102.89 で閉門) に分かれる。§2 の定義で wave の待ちに入るのは 853 秒だけである。
- 感度分析 (記録 tick 列へ条件だけを差し替えた仮定付き参考模型。効果見積りではなく上下限にもしない): 一律 (maxl=2, load 60) で直近 20 は 8 区間が早まり合計 −7,375 秒 (うち 1 区間が 64%)、9/19 以降は −132,794 秒。一律 (1, 80) は直近 20 で −932 秒、9/19 以降で −5,728 秒 (同集合での 60→80 は −5,126 秒)。他 wave の応答・同時走行増による遅延と赤・pigz・再カウント時の load 再評価は模型に入っていない。
- **裁定パッケージ (README §7、ユーザー裁定待ち):** 択 A = leaders の数え方を argv 先頭一致へ統一し写し元を 1 つに決める (効果は数値化不可、採用前に実 leader の argv との照合が要る)、択 B = maxl ≤ 2 の期間限定試行 (模型値あり、同時走行増の危険と検証条件つき)、択 C = maxload 80 (効果小)、択 D = 乱数幅・周期の位相 (数値効果なし)、別枠 = FIFO / slot 機構 (D2148 項 12 が現時点で採らないとした設計判断)。親の推奨は A を先に、B は検証条件つきの期間限定、C・D・別枠は採らない。lease primitive・待ち手・TTL は択に含めない。
- 段 3 相談 1 本 (read-only) が親の初案を 12 件で修正・却下した (全件 real・採用): 停止と再起動をまたぐ log を連続待ちにしない (区間分割 600 秒)、飢餓の定義を「同時待ち ≥ 3」から「長時間待ち ∧ 再カウント拒否 ≥ 2」へ、効果見積りを感度分析へ縮小、leaders 値で同時待ち数を補正しない、日付復元と条件の出所を明示、母集合の選択キーと観測区間を別掲。裁定は README §6 と job dir の `s4-ruling.md`。
- 段 5 author 1 本が probe (`tools/gate_wait_probe.py`、repo へ land しない) を書き、親の本走監査で 4 巡の fix: (1) 投入行の変種 `attempt N: tip=… main=…` (39 件) を認識せず直近 20 の 12 区間を打切り扱い、(2) 走行数の照合を追加、(3) 観測の締め `--until` と門番 log の無い dir の走行と自 wave 除外 (母集合が走らせるたびに動き、待機中の並走 wave を拾っていた)、(4) leaders の数え方との交差表・感度寄与上位・飢餓候補の説明列。
- 段 6 レビュー 1 本は照合表 50 行超で数表と派生値を全部再計算し (転記は全一致)、NO-GO で must-fix 7 / should 7 / nit 2 を出した。全件採用して是正: 感度上位 5 件は全件走行 0 (4 件と書いていた)、同時待ちの母集合は since で絞られる (全門番 log ではない)、日付復元の説明が実装と逆、感度の行は「一律置換」であって単独条件の変更ではない、推奨理由の「約半分」の分母のすり替えと「記録と実態」→「記録どうし」、択 B の「同時走行最大 3 本」は保証されない、`~/.claude/jobs/` の不在主張の範囲限定。焦点再レビューで対応表を取った。
- 工数: codex 子 8 本 (consult 1、author 1、fix 4、review 1、focus 1、全段 `gpt-6-astra` / medium、受理 8/8)。親の実走: probe 4 走 (login、read-only)、開始 gate 1、midflight gate 4。計算ノード job 0。
- 受入全走と land の結果は本 entry には書けない (fold 後に確定するため insight に追記)。

## 次の一手差分

### 新規

- {{T:acceptance-gate-relax-ruling}} **P2・ユーザー裁定待ち**: 受入門番の緩和 4 択 + 別枠 (`output/insights/2026-09-21/acceptance-gate-wait-diagnosis/README.md` §7) を裁定する。択 A = leaders の数え方を argv 先頭一致へ統一し写し元を決める (親の推奨、採用前に実 leader の argv 照合)、択 B = maxl ≤ 2 の期間限定試行 (検証条件つき)、択 C = maxload 80、択 D = 乱数幅・周期の位相、別枠 = FIFO / slot 機構 (D2148 項 12 の scope 外)。門番の閾値・周期・lease TTL の変更はユーザー裁定で、AI は実装しない。
