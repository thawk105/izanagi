---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2229-verify-cost-decomposition
seq: 1
title: [T-2229] 「直列性検査 1 回 23 分」を既存の記録だけで区間別に分解した — 当時の 120 秒 timeout 契約からベンチ process は各反復およそ 120 秒以下 (条件付き)、区間の約 91% が Python 側 (数え直し + 検査器) で検査器が主要項。検査器の値は試算 (71〜92%) にとどまり、反復の内側を計った保存資料は確認した範囲に無い (docs + insight、branch worktree-dev-wave-t2229-verify-cost-decomposition、実装面 0・実装変更がないため変異テスト対象外)
---
## 本文
- ユーザー依頼は「23 分は混合区間 (build・trace 取得・verifier) であって検査器単体の費用ではない
  点を、既存 receipt / log から区間別に切り分け、積み方を insight に構造化する。並列化や検査削減は
  処方しない。実装差分ゼロ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
  着手直前の local main `a0ccb8ad9` (起動時 snapshot `e2d4d9ce8` から 2 commit 進んでいた) から
  fresh worktree を作り、新規測定は投入していない。
- **着手前の済照合。** 1223 (2026-09-03) が帰属と積み方の是正 (D1554、A-6 insight 追記、1187 注記)
  を済ませており、残件は 1189 への in-file 注記 1 か所と「区間別の分解」そのもの。T-2261 (09-03)
  が pass 別 (build / legacy / performance 1〜5) まで、T-2191 (09-02) が検査器単体 (合成 trace)
  まで分けていたので、本 wave の純増は「pass の内側」に絞った。
- **反復の内側を計った保存資料は確認した範囲に無い ((P1) real、全称は判定不能)。** `ed8a676b` の
  WAL `verify_done` payload に時刻・所要の field は無く、driver の標準出力 (`log=print`) は job が
  SIGTERM で終わったため attempt dir の `driver.stdout` が 0 bytes (`driver.stderr` も 0 bytes)、
  `scheduler.stdout` (10,395 bytes) は gflags / glog の依存 build の出力だけ。当時の verifier
  capability / commit receipt の code にも段別所要の保存経路は無い (レビューの確認)。
- **記録と契約から言える上限が 1 つ見つかった (レビュー nit 5 を裏返した新事実、ただし条件付き)。**
  当時の code (`0a07481b8`) は trace 有効ベンチ process を `subprocess.run(timeout=120)`
  (`TRACE_TIMEOUT_S`) で `trace-timeout` として reject する契約で、22 反復に 1 件もその reject が
  無い。2 巡目の焦点レビューが「timeout は子の起動後 `communicate()` から計るので、起動直後の親の
  遅延分は保証外 = 厳密な上限ではない」と指摘 (must-fix、real)。その遅延が無視できるという条件の
  下で、ベンチ process (記録の読み込み + 3 秒走 + trace の書き出しと flush + 終了) は各反復およそ
  120 秒以下、**区間の約 1289 秒 (約 91%) が Python 側** (数え直し換算約 20 秒 + 検査器 + 台帳操作
  0.36 秒以下) で、検査器が主要項。trace 無し版の同じベンチは perf 相 `rep_walltime_s` 225 rep の
  実測で 3.35〜3.42 秒 (参考値、trace 有効版の下限ではない)。
- **段の順序から出た事実 2 つ。** (a) `shutil.rmtree(tdir)` は WAL 書き込みの後の `finally` に
  あり、(b) WAL の時刻 `.ts` は `append()` の前に採るので、前反復の WAL 行の書き込みと trace dir
  削除はどちらも次の反復の区間に入る。最後の反復の分だけが `verify_done` → `commit`
  (0.15〜0.36 秒) に入るので、17M commit 分の trace dir 削除 + WAL 行書き込みは 0.36 秒以下と分かる
  (最後の 1 回の観測)。
- **同一 4 変種の直列 / 並列差分が組めたが、帰属には使えない (レビュー must-fix、real)。**
  同じ read-heavy を並列化後の検査器 (source `2a338449b`、既定 `workers` 16、bnode088、09-05) で
  完走した `acf840c8` に `ed8a676b` の 4 変種がすべて含まれ、17M 級で直列 1408.8 秒 → 並列
  607.4 秒 (変種別の差 781〜823 秒、区間全体の所要比 2.29〜2.37)。初稿はここに等 R 模型と
  s ≤ 4 を暗黙に置いて「検査器 76〜98%」を記録からの上下限として書いていたが、レビューが
  「等 R は未実証 (node・trace・code が同一でなく、並列側は検証への追加引数と `proof_surfaces` の
  WAL 出力を持つ、`workers` 16 の発火も未確認)、s に上限を置く根拠も無い (s = 5 で 71%、
  s → ∞ で 57%)」と指摘。real と裁定し、条件付き試算 (§5.3) へ降格した。
- 結論の形: 条件付きの上限が「ベンチ process 約 120 秒以下、Python 側 約 91%」で、仮定なしの定量値は
  無い。検査器の値は
  合成単価の外挿 (71〜86%) と等 R 試算 (s = 2.6〜4 で 76〜92%) の 2 つの試算にとどまり、
  どちらかに決める記録は無い。点推定は書かない。記録は {{D:verify-cost-interval-attribution}}。
  幅を狭めるには計算ノードでの検査器単体の実測か反復内の計時が要るが、どちらも本 wave の
  scope 外なので起票していない。
- 積み方: 「23 分」は中央値 (1408.8 秒) の丸めで、10 回で 3.91 時間。上端 1465.6 秒で 4.07 時間
  (倍率 2.95、D1554 のとおり)、反復の外側 (build 2 × 52.8 秒 + legacy 2 × 28.9 秒 + job 前置 28 秒
  + 行間 2.3 秒) を足して 4.12 時間 (倍率 2.91)。walltime `12:00:00` は動かしていない。
  帯・中央値・差・積み方はいずれも欠測 attempt (`292d58f1dad8` の 3 反復) を含む母集団から出ており
  D1529 の但し書きを付けた。除いた 10 反復の中央値は 1398.7 秒で結論は変わらない。
- 1189 の [T-2191] 項の逐語 (「直列性検査が単一スレッドで … 1 回 22-24 分」) へ訂正注記 2 を
  純追記した (main 比 15 行追加・削除 0)。1223 で並行 wave が所有していた slot は空いていた
  ((P3) real、当時の所有状況は判定不能)。
- **段 6 レビュー (read-only codex、1 巡目 review + 2 巡目 focus + 3 巡目 focus = DW-O16 の上限)。**
  1 巡目 (レンズ = 算術の再計算・差分帰属の前提・断定の範囲・1189 追記・平易さ): 全数値を TSV と
  WAL 原本から再計算して丸めの範囲で一致、must-fix 1 (等 R 模型の結論化、real → 条件付き試算へ
  降格し timeout 契約の上限を主に据えた)、nit 6 (「構造上の下限 R ≥ 24」の転用、WAL 書き込みの
  区間帰属が 1 つずれる、D1529 の但し書きの射程、「どこにも無い」の全称、残差を flush へ集中帰属、
  平易さ 4 語) すべて real で反映。2 巡目 (焦点、対応表): closed 3 / partial 3 / regressed 1、
  新規 must-fix 1 = 「timeout を厳密な実時間上限に転用」(real → 条件付きへ改めた)、partial 3 =
  3.4 秒を trace 有効版の下端扱い・pooled D が欠測 3 反復を含む・派生値の丸め (1288.8 を ≥1289 と
  書いた) をいずれも real で反映。3 巡目 (焦点、最終): 対応表 closed 8 / partial 0 / regressed 0、
  派生値 5 項目一致、新しい所見なし。certified の変更・規律 2 の弱体化・D1554 との矛盾は 3 巡とも
  無し。逐語は insight の `verbatim/s6-review-A.md`、`s6-focus-A.md`、`s6-focus-B.md`。
  仮定付き模型を上下限として結論化した near miss (2 度同型) は {{F:model-assumption-written-as-bound}}
  に起票した (着地前に捕捉、成果物の値は不変)。
- 段 8 (自己改善候補 3 件): (i) `*.out` が `.gitignore` で insight の同梱 file が黙って落ちる
  (1 例、`.txt` へ改名で解決、docs 変更なし)、(ii) レビュー prompt の「算術の再計算」「模型の前提」
  レンズが過大主張を捕捉した (作法として有効、F の恒久対応に記載し docs 変更なし)、(iii) 焦点
  再レビューで派生値の前提 (模型の仮定・計時起点) も裏取りする → `DW-O16` へ 1 文を追記 (節は
  919 → 992 / 1000 bytes、exact pin なし、`check_docs` rc=0、専用 commit)。routing 先は F 1 本と
  reference 1 節、command 入口の編集なし。
- 工数: codex 子 3 本 (review 1、focus 2、`gpt-6-astra` / docs 権威の reasoning = medium)。親の実測: WAL 2 本の抽出
  (jq + 使い捨て script、job dir に留め repo へ入れていない)、block record 45 本の `rep_walltime_s`
  集計、当時の commit の `pipeline.py` / `wal.py` / `trace.hh` の段構成と timeout 契約の確認、
  両 run の受領証 (job ID・node・開始終了時刻) の照合、`check_docs.py`、三軸語走査、
  全史 provenance 監査 (11,256 commit、新規違反なし)。
## 次の一手差分
### 完了
- [T-2229] 「直列性検査 1 回 23 分」の帰属 (混合区間) と積み方 (帯の中央値 1408.8 秒、上端
  1465.6 秒 × 10 = 4.07 時間、`12:00:00` の倍率 2.95) を区間別に分解し
  `output/insights/2026-09-18/t2229-verify-cost-decomposition/README.md` に構造化した。
  timeout 契約からベンチ process は各反復およそ 120 秒以下 (条件付き)、区間の約 91% が Python 側で
  検査器が主要項、検査器の値は試算 (71〜92%) にとどまる。1189 の in-file 注記も追記した。
  並列化・検査削減は処方していない。
  remaining: none
  base: cbc22e3f24aafa03efcfffe4cf215652d5437995a51b6dce35bfd32c768da524
