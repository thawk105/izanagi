# 段 1 brief (2026-09-04、軽量版・docs-only・子ゼロ) — 逐語

- scope: (1) tools/plotting/ の 6 図種を「実寸 (production 入力の形) vs 検査用 fixture の形」で棚卸しし、結果を insight へ凍結する。(2) FIGURE_CONVENTIONS.md へ「検査用 fixture は実寸へ揃える」規約を純増で足し、§9 の雛形指定 (warn-only の plot_backoff._overlap_check) を fail-closed 側へ正す。(3) 棚卸しで見つかった不揃いは新規 T として次の一手へ登録する (本 wave では直さない)。
- 確定済みユーザー裁定: D1546 (棚卸し + 規約追記、新機構なし)。F812 が恒久対応文言 (実寸と同じ格子形状・軸点数、producer 必須セルを fixture に含める、実データ実走で閉じる) を持つ。command 引数: 仮想リスク向け gate・検査・台帳・一般化の追加は scope 外。
- 不変条件: 規律 2 を緩めない (fixture 拡大は検査を厳しくする方向のみ)。実装面 (test / generator) は本 wave で編集しない (Codex author = D95 が要る別 wave へ)。凍結図の bytes・provenance に触れない。可変状態 (棚卸し結果の snapshot) は規約書へ再掲せず insight + worklog fragment に置く。
- 成果物: FIGURE_CONVENTIONS.md (§9 訂正 + 新節「10. 検査用 fixture は実寸へ揃える」+「新しい図種を足すとき」への 1 手順追加)、output/insights/2026-09-04_t2216-figure-fixture-real-size/README.md (棚卸し表・裏取り・限界)、docs/spool/worklog fragment (T-2216 完了、新規 T 4 件)。
- 分割方針: docs-only、子ゼロ。棚卸しは Explore 子 (read-only) 1 本で済み、親が要所を裏取りした。
- 受入・実測環境: login node での受入全走 (tools/dev_wave_wait.py acceptance)。作図・計測は行わない。
- (P1) 「実寸」の定義は「production 入力が生む panel 数・格子形状・軸点数・系列数・反復数・注記密度」とし、値の実数一致までは要求しない (値は provenance が束縛する)。
- (P2) plot_backoff の warn-only 検査と ss2pl の描画テスト皆無は、実図が既に fail-closed 検査 (ss2pl) または人手 (backoff) で生成済みなので、実在の欠陥でなく被覆漏れ (P3) とする。
- 模擬/実の差: 棚卸しは source 読取のみで模擬なし。実寸の点数は fig2b の dat (6 点)・provenance (n_reps 5) の実物から数えた。
