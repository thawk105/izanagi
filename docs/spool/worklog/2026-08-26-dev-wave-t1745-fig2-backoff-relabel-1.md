---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1745-fig2-backoff-relabel
seq: 1
title: [T-1745] fig2 の後継図を tracked 生成器つきで作り、図と provenance の label 対応を機械束縛する (コード + docs、branch worktree-dev-wave-t1745-fig2-backoff-relabel)
---

## 本文

- **段 3 が親の段 1 裁定を覆した。** 親は根拠 insight が `authority: none` を自称することを根拠に、
  同 insight の「図・キャプション・見出しのいずれにも `adaptive` を残さない」を
  権威ある禁止ではないと読んだ。これは誤りだった。`output/README.md` は
  「`authority: none` は可変状態の正本でないことを示すだけ」と定め、`docs/decisions.md` は
  「`authority: none` は発効の否定ではない」と明記している。親が両方を実測で確認して覆した。
  加えて、正しい値でも 3 本線を併置すると read-heavy が「no backoff 比 -6.9%」と
  「adaptive 比 +312%」を同時に見せてしまい、旧事故の本質 (どの線が分母か図から決まらない) を
  再生産する。よって後継図は **no-backoff 対照 1 本だけ**を基準線にすると裁定した。
- **親の段 1 の成果物影響主張が偽だったため取り下げた。** 「入力 hash を束縛する検査を足せば
  T-1745 同型の再発を防げる」と書いたが、旧事故は「入力値は正しいのに線の label が別物を
  指していた」ことであり、入力 hash では捕まらない。段 6 レビュー A がこれを実測で示した。
  代わりに provenance へ「実際に描いた線の label・値・95% CI 半幅・genome」を記録し、
  その記録経路を描画関数の返り値に一本化して、記録と描画が構造的に乖離しないようにした。
- **段 6 レビュー A が偽緑を実測で暴いた (親が 3 件を独立に裏取り)。**
  (1) 新設 gate は合成 fixture だけを検査し、着地する実 provenance を開く test が 0 件だった
  (`grep` で 0 hit)。(2) 段 5 が入れた測定条件抽出が `int('false')` を呼ぶため、
  `-ycsb_rmw=false` を持つ 4 campaign で例外になった (`=0` 形式は 22 件)。
  (3) 既定 baseline の test が production 定数と定数を比べる恒真だった。
  他に、PNG/PDF を無関係な図へ差し替えて digest も更新すると通る、`facts` が無検査で
  `best_M=999` が通る、`campaign.lock` が hash 閉包外、といった穴も示された。
- **段 6 レビュー B が図とキャプションを数値レベルで独立検算した。** 平均比
  `+38.111185129 / +11.422593028 / -6.852026348%`、median 比
  `+38.328803879 / +11.268232226 / -6.642987663%` を再計算し、キャプションの表示値と
  丸めの向きが負値を含めて正しいことを確認。生成 PDF の全文検索で `adaptive` / `適応` / `stock`
  が 0 件、peak 注釈が read-heavy にだけ付かないのが正しい (単調減少で最大が左端) ことも確認した。
  insight の「言わないこと」9 項目すべてに適合。
- **キャプションの意味誤記 2 件を一次資料で訂正した。** `external/ccbench` の引数ドキュメントにより
  `-clocks_per_us` は CPU cycle でなく **TSC tick / µs**、`-ycsb_rmw` は boolean なので
  「率 0%」でなく「**無効**」。また「read 比率だけが workload ごとに異なる」は
  「記録された実行フラグの上では」と限定した (測定日は write/balanced が 2026-06-22、
  read-heavy が 2026-06-28 で異なる)。
- **再計測は一切していない。** 入力 WAL 3 件の SHA-256 が根拠 insight の source ledger と
  完全一致することを親が確認した。lock file の SHA-256 も同台帳と一致する。
- **編集面重複検査を 2 回実測した。** wave 中に worktree が 38 → 43 へ増えたため再走し、
  `docs/paper-story/` と `tools/plotting/` の生きた衝突はどちらも 0 件だった
  (2 回目は SCANNED=43 HITS=0)。引数が言う「複数の停止中 worktree に差分が見えている」は
  この wave の期間中は成立しなかった。
- **既存の凍結 PNG 3 枚は 1 byte も触っていない** (`git status` で untracked 4 件のみ)。
  凍結スナップショット 2 本の誤キャプションは運用ルール上訂正できないため、
  入口 README の erratum を強化するに留めた。
- codex 子の異常: 段 6 レビュー B の初回が `metering_status: incomplete` により
  `outcome: not_accepted` で戻った (内容の失敗ではない)。job-id を変えて再投入した。
  また `--reasoning` を review 段へ渡して rc=2 になった (effort は docs 権威から自動導出される)。
- **変異 matrix は 7 件すべて KILLED、baseline PASSED。** 中でも
  「図に書く文字だけを `stock adaptive` に変え、記録側は正しいまま」という旧事故そのものの変異が
  `test_actual_panel_artists_match_serialized_baseline_records` で赤になった。
- **変異の erratum (DW-M02)。** 初回走行では 2 件が MISMATCH だった。実装の欠陥ではなく
  期待 node 集合の登録漏れである。生成器のバイト列を変える変異は、実成果物 gate も
  「generator SHA256 mismatch」で正しく赤にするため、狙った node に加えて 1〜2 件が落ちていた。
  束縛が意図どおり効いている証拠なので、初回を probe として残し、完全な期待集合へ再登録して
  再走した (attempt 2 で全件一致)。初回結果は消していない。
- 工数: codex 子 7 本 (plan 1 / consult 2 / author 1 / review 3 (うち 1 本は不採用) / fix 1)。
  変異本走 2 回 (初回は expected_nodes の probe)。

## 次の一手差分

### 完了

- [T-1745] 後継図 `docs/paper-story/figures/fig2b_backoff_sweep_3workload.{png,pdf,provenance.json}` を
  tracked 生成器 `tools/plotting/plot_backoff.py` で作った。基準線は無 backoff 対照 1 本のみ。
  provenance schema を v2 へ上げ、入力 (WAL / dat / lock) と生成器と出力の full SHA-256、
  描いた線の label↔値↔genome↔95% CI 半幅、WAL 由来の測定条件を記録する。
  `orchestrator/tests/test_backoff_figure_provenance.py` が着地物を検査し、
  `orchestrator/tests/test_plot_backoff_ci.py` が図中 label と provenance の一致を検査する。
  再現手順とキャプション正文は `docs/paper-story/figures/README.md`。
  remaining: none
  base: b41fb31b646da75492124a26837637de5c661bbf8996999c0ab5a35b387d7298

### 新規

- {{T:dev-wave-background-waiting-discipline}} **P2・新規**: 背景 job の待機作法を dev-wave docs へ
  入れる余地を作る。本 wave の段 8 は候補を 2 件出し、DW-O03 の射程是正 (prompt だけでなく
  brief・裁定・runner script・spec・`python3 -c` も guard に拒否される) は実装できたが、
  待機の作法は入れる場所が無かった。DW-C00 は L1 予算が満杯 (追記すると 10,749 > 10,625 bytes)、
  DW-C01 は節全体が exact 契約かつ単節予算 1,000 bytes も満杯 (追記すると 1,136 bytes)。
  自己改善契約は「予算のために安全義務を削除・弱化してはならない」「予算値を上げる変更は
  理由付きの独立審査対象」と定めるため実装せず返す。実測の根拠: 本 wave は子の完了待ちで
  背景待ち手を通知のたびに積み、待機だけで 100 turn 以上を消費した。
  入れたい規範は「背景へ待ち手を 1 本張ったら完了通知まで足さない」の 1 文である。
- {{T:fig2b-scope-out-package}} **P3・新規**: [T-1745] で scope 外に置いた 5 件をユーザー裁定へ返す。
  (1) 凍結スナップショット 2 本の誤キャプションをどう扱うか (運用ルール改訂が要る)、
  (2) 図の byte 決定的な再生成 (`SOURCE_DATE_EPOCH`・依存版 pin・font pin)、
  (3) `_overlap_check` を警告から拒否へ昇格し結果を provenance へ残す、
  (4) パネル間 y 軸の共有または正規化、(5) read-heavy の CI 帯の視認性 (縦軸比 0.40%)。
