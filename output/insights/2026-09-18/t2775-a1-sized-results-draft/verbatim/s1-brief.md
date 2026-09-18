# 段 1 brief — A-1 balanced5 sized 本走 attempt-0001 の単独 results 稿と fig9 (台帳 ID 未起票、entry 1653 [T-2775] の続き)

- 起点: local main `c8e8dc06f` (2026-09-18 14:5x JST)、fresh worktree `worktree-dev-wave-t2775-a1-sized-results-draft`。
  slug の `t2775` は系譜ラベル (entry 1653 の README 注記の続き)。本 wave の台帳 ID は未起票のまま worklog 表題にそう書く。
- **研究前進:** 論文の結果節に「A-1 (D1262 の estimand で揃えた 3 workload の対測定) の attempt-0001 の descriptive 出力」を
  1 attempt の一次資料全体から落とした統制稿 1 本と、3 workload の対差平均 ± 登録済み区間を床 ±B と並べて見せる記述図 fig9 が
  加わる。完了判定 = 稿 1 file (append-only 系列) + fig9 3 成果物 + 生成器 + 対応検査 test + figures/README fig9 節 +
  paper-story README の results 表 1 行と stale 注記 1 行、受入緑、land。
- **scope:** 上記だけ。A-1 の充足・formal 化・再認可・再投入の判定は含めない (ユーザー手番、D2044 項 8)。
  gate・台帳・一般化の追加は scope 外。凍結物 (事前登録・policy・公開 leaf・既存稿・既存図) は 1 byte も変えない。

## 確定済みユーザー裁定 (前提実測済み)

- D2120 項 3 (2026-09-17): 既存 submit 経路で 1 attempt を認可、落ちたら再投入せず止める。→ attempt-0001 は落ちておらず完走 (insight §1)。
- D2044 項 8 (2026-09-16): 本番測定の認可は据え置き、認可はユーザー手番。→ 本稿は判定しない。
- D2120 項 15: paper-story の単独 results 稿は T-2611 / T-2674 の型。→ 同型で書く。
- 事前登録 §7.2: workload をまたぐ結論を作らない、`formal=false` / `promotion_prohibited=true` は文書編集で反転させない。
- D1637 (2 本目の論文と数値・図を共用しない)、D1993 / L23 (C1 との再現判定にしない)、D12 (protocol status を研究の成否へ拡張しない)。

## 一次資料の実測 (段 1 で親が現物を読んだ)

- 公開 leaf `output/insights/2026-09-13/paper-story-a1-balanced5-sized/`: README.md `880919db…` / receipt.json `a2039dc1…` /
  result.json `372f199e…` = `.complete.json` の `files` と insight §4 に一致 (`authority-recheck-1.tsv`)。
- repo 外 (耐久 base `…/measurement/attempt-0001/`): campaign.lock ×3・wal.jsonl ×3・balanced-schedule-receipt.json ×3 の sha256 と
  bytes は result.json の `campaign_binding` / `wal_evidence` / `schedule_receipt` と一致。raw/results/{result,receipt}.json は
  公開 leaf と bytes が違う (raw `b080d755…` / `7de00bf5…`; leaf は materializer が `materialization_evidence`・limitation 1 件・
  `materialization` を足した派生) が、`workloads[].statistics` と `arms` は構造比較で同一 (`raw-vs-leaf-diff-1.txt`)。
  receipt.json の `result.sha256` は raw を指す (leaf ではない)。
- 30 対 × 3 の再計算 (`arms-and-recheck-1.txt`): `signed_difference = variant − baseline` 全対一致、pairs[i] が arms.raw_tps[i] と
  一致、mean / sd / h / B / 分類が記録値と全桁一致 (sd は最終桁の float 丸め差のみ)。派生比 +0.694 / +0.116 / −0.056。
- WAL 10 record × 3 (build_start/build_done/verify_done/bench_done/commit × 2 arm)、verify_done は 6 本とも `certified=true` /
  `anomalies=0` / `verdict=serializable` / workload tag `legacy`、bench_done は `rounds=1` / `unstable=false` / `settled=true` /
  tps 30 点、`perf_observation.use_perf=false`。commits/aborts: write-heavy fixed10 459238/107049・no-backoff 544423/209963、
  balanced fixed5 466561/130497・no-backoff 483318/185235、read-heavy fixed2 516607/181083・no-backoff 515988/196776。
- **新事実 (覆さないが記録する):** t1505 insight §4 の表は balanced と read-heavy の commit 数が入れ替わっている
  (WAL と同 insight の `receipts/job-stdout-*.txt` が正)。他文書へは波及していない (`grep 516607|466561` は insight 表と stdout だけ)。
  → 稿は WAL の値を使い、本 wave の insight README に観察として書き、failures fragment で F1 へ「再発 (他 wave の凍結記録、本 wave が検出)」を追記する。
- 分類の述語は v3 では policy JSON に無く (`classification_rules` key 不在)、実装 `paper_story_a1_paired.py` の `_classify_difference`
  (`abs(mean) − h > B` → resolved-above-floor / `abs(mean) + h ≤ B` → bounded-below-floor / otherwise unresolved) と
  `_statistics_from_signed_differences` (floor_fraction は v3 で定数 0.03、policy `sizing.floor_fraction` 3/100 と検証で一致) にある。
  k・df・planned_sigma は policy `workloads[]`。事前登録 §5.2 の語 (`resolved-beyond-floor` 等) と実装の語は違うが述語は同値 (insight §5 の観察と同じ)。
- figures/ に A-1 は 0 件。results/ に A-1 は 0 件。fig 番号の最大は 8 → 新図は fig9。

## 不変条件

- 規律 2: verifier の判定 (6 arm とも 0 anomalies) は既存 verifier のままで、性能の判定ではない。稿・図・caption は正しさと性能を 1 文へ畳まない。
- 凍結物の bytes 不変: 事前登録 README、policy v3-sized.json、公開 leaf 4 file、既存 results 稿 8 本、既存図 fig1〜fig8。
- 数値の出所は公開 leaf の result.json (sha256 `372f199e…`) と WAL だけ。版・claim-evidence・insight の記述を数値の出所にしない。
- 限定を明記: `formal=false` / `promotion_prohibited=true` / `result_authority=sized-preregistered-descriptive-only` の非認証 lane、
  符号 +/+/−、descriptive で headline 値・横断結論・C1 再現判定にしない、単一 attempt を反復間の安定性へ一般化しない。
- hash 自己参照禁止 (F36): fig9 provenance は本稿を `caption_source` として sha256 束縛するので、稿は provenance の sha256 を持たない。
  provenance sha256 の正本は figures/README.md の fig9 節 (腐らない入口)。稿は「図の値と表の値が同じ生値から同じ計算で出ること」を
  test (入力と表示値の対応検査) に委ねると明記する。
- 実装面 (生成器・test) は Codex author が書く (D95)。親は docs だけ編集する。
- `test_official_perf_closure.py` は tools/ 配下の .py を走査し `perf` 名の分岐を検出する → 生成器は perf 名の変数で分岐しない。

## 成果物の形

1. `docs/paper-story/results/2026-09-18-a1-balanced5-sized-attempt1-descriptive.md` (親、A-6 稿 §0〜§5 の型)。
2. `tools/plotting/plot_a1_sized_paired.py` (Codex): 入力 = 公開 leaf 3 file (tracked、pin 表で sha256 照合)、値は `pairs[]` から
   mean / sd / h を再計算して `statistics` と fail-closed 照合、分類は記録値をコピーし述語で検算、`formal=false` /
   `promotion_prohibited=true` / `valid=true` / `errors=[]` / n=30 / `variance_plan_breach=false` を拒否条件に、
   3 panel (workload-local y、対差平均 ± h、床 ±B の破線、0 の実線、30 対の差の strip)、caption 英文固定、`fig<N>_` prefix、
   renderer-backed layout check、3 成果物、provenance に `caption_source` (本稿 path + sha256)。
3. `orchestrator/tests/test_plot_a1_sized_paired.py` (Codex): 実寸 fixture (3 workload × 30 対)、本物 Figure の layout check、
   pin 表と稿 §5 の sha256 一致、入力→表示値の対応 (provenance cells == result.json statistics、artist_series == cells)、
   着地 fig9 の closure (PNG/PDF sha・caption・caption_source sha == 現 file) when present、拒否系。
4. `docs/paper-story/figures/fig9_a1_balanced5_sized_attempt1.{png,pdf,provenance.json}` (親が生成、login node)。
5. `docs/paper-story/figures/README.md` fig9 節 + 一覧行、`tools/plotting/README.md` command example (親)。
6. `docs/paper-story/README.md`: results 表 1 行 + stale 注記 A-1 項へ 1 行 (親)。
7. insight `output/insights/2026-09-18/<slug>/` (README + verbatim)、spool fragment (worklog 1、failures 1)。

## 割れうる前提 (親の provisional 裁定・段 6 の攻撃対象)

- (P1) 図の形: 3 panel・絶対 tps・対差平均 ± h・床 ±B・30 対 strip。正規化 (比) は登録量でないので描かない。
- (P2) README の編集は results 表 1 行 + stale 注記 1 行の 2 行 (依頼の「1 行だけ」は stale 注記の話と読む。表の行は系列の索引で先例 2 本と同じ)。
- (P3) 分類の出所は実装の述語 + policy の k / sigma と書く (insight の「policy の classification_rules」は v3 では不正確)。
- (P4) file 名 `2026-09-18-a1-balanced5-sized-attempt1-descriptive.md` (status 語は無い: outer status を持たない lane)。
- (P5) 段 2・3 は省略 (変更面は fig8 の兄弟で file:line が親から書ける)、段 6 の敵対レビュー 2 本 (A: 稿の数値・逐語・識別子、
  B: 生成器・test・図・限定・裁定整合) と焦点再レビューは省かない。

## 並列分割

- 親: 稿 → (Codex author 1 本: 生成器 + test) → 親: 図生成・README 群 → 段 6 レビュー 2 本 (並列、read-only) → fix (Codex/親) →
  焦点再レビュー → 図の再生成 (稿の最終 bytes で) → 変異 matrix (生成器の検査の負例) → 記録 → land。
