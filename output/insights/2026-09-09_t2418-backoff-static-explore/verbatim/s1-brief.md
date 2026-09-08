# [T-2418] 段 1 brief — 静的 backoff 右側 3 点の探索走

基準: local main `2143a49c0c9037b303106eca4cfc346797d3f1b3` (着手直前)。
worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2418-static-backoff-explore`、
branch `worktree-dev-wave-t2418-static-backoff-explore`。

## 研究前進

backoff の tail 主張 (`docs/paper-story-backoff/2026-09-05.md`) は、静的 backoff を大きくしたとき
abort 抑制が飽和するかを右側で測れていない。既存の認証格子 `EXTENDED_SWEEP_US` は上端 1000 µs で
打ち切られており、これは凍結された事前登録格子なので触れない。D1813 は 2 段構成を裁定した —
第 1 段が本 wave の探索走 (2000 / 4000 / 9999 µs の 3 点)、第 2 段の本格格子と停止基準は
探索結果を見た後・本格 cohort 投入前に別途事前登録する。**完了判定:** 3 workload それぞれで
3 探索点 + 文脈 2 点が既存 sweep と同じ反復数 (REPS=5, EXTIME=3s) と同じ walltime 枠 (PBS 18000 秒)
で計測され、成果物が「探索であって正式系列ではない」ことを自ら開示していること。

## 確定済みユーザー裁定

- **D1813 (第 15 回、ユーザー委任裁定):** 2000 / 4000 / 9999 の 3 点を既存 sweep と同じ反復数・
  walltime 枠で測る。探索値は正式標本へ混ぜない。探索値・探索で選んだ格子・停止基準を開示する。
  本格格子と停止基準は本 wave では凍結しない。
- **引数:** 本題の実装と投入だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
  規律 2 を緩めない。Codex author = D95。

## brief 前の実測 (承認済み裁定・引数の前提の検算)

1. **引数の機構名は不正確 (real、覆さないが訂正が要る)。** 引数は機構を
   `orchestrator/campaign/backoff_sweep.py` と書くが、同 file の `SWEEP_US` は
   `[2,5,10,25,50,100]` で生の `BACKOFF_FIXED` を渡すため 1000 以上を表現できない。
   1000 超を表現する符号化 `encode_static_backoff_us` と格子 `EXTENDED_SWEEP_US` は
   `orchestrator/campaign/backoff_extended_sweep.py` にある。**本 wave の機構はこちら。**
   `backoff_sweep.py` からは `_BASE` / `_official_durable_root_policy` /
   `_require_backoff_condition_gate` を輸入して使う (現状のまま、編集しない)。
2. **3 点は現行 main の経路で構成できる (実測)。** worktree 上で
   `2000→4000→2000`、`4000→6000→4000`、`9999→11999→9999` の往復一致を確認した。
   `backoff_overthrottle._point_backoff_us` は同じ decoder を通す。
   `condition_meaning_gate` の `BACKOFF_FIXED` に 1000 上限は無く、非負の厳密整数だけを要求する。
3. **反復数は共有定数。** `p2_2.REPS=5`, `EXTIME=3`, `RECORDS=1_000_000`, `THREADS=48`。
   `PerfConfig` を既存経路で組む限り「同じ反復数」は自動的に満たす。
4. **walltime 枠は PBS 台本の側。** `tools/pegasus/b10_backoff_grid.sh` は
   `elapstim_req=05:00:00` / `EXPECTED_WALLTIME_S=18000` / `SWEEP_CAP_S=11700` を持ち、
   qstat の実測値が 18000 と一致しなければ job 本体が停止する。既存 t2266-tail は 8 genome を
   この枠で走らせた。本探索は 5 genome なので同じ枠に収まる。
5. **F660 は発火しない (実測)。** `tools/pegasus/admission_registry.json` の
   `tools/pegasus/b10_backoff_grid.sh` は `class=dispatch-required` で **既登録**、
   entry は sha256 を pin しない。新規 Pegasus 実行体を作らないので、機構と実測を別 wave へ
   割る必要はない。ただし job 本体は `$CURRENT_COMMIT:tools/pegasus/b10_backoff_grid.sh` の blob と
   実行 file の sha256 一致を要求するので、**投入前に wave branch へ commit 済みである必要がある。**
6. **投入経路は t810 dispatcher ではない。** `tools/pegasus/submit_b10_backoff_grid.sh`
   (`class=local-ok`) が login から workload ごとに 3 本 qsub する。orphan hold の問題圏外。
7. **編集面の重複 (起動時検査)。** 引数が名指しした 3 file
   (`t2187_adaptive_const_probe.py` / `backoff_policy_performance_analysis.py` /
   `b10_backoff_shape_sweep.py`) は本 wave の編集面に入らない。稼働中 worktree の未 commit 差分の
   走査結果は handoff に記す。

## scope (成果物影響つき)

放置すると: 右側の飽和位置が未知のまま本格格子を賭けることになり (規律 4 違反)、backoff tail の
主張が閉じない。D1813 の第 2 段の事前登録が着手できない。

**入れる:**
- (S1) `backoff_extended_sweep.py` に第 3 の RUN_KIND を足す。既存 `t2266-tail` と同型:
  専用の requested/realized タプル、専用 `spec_slug` / `trial` / `scale`、専用 report schema、
  `claim_scope`。**正式系列と campaign identity が別になることが「混ぜない」の実装である。**
- (S2) 成果物への探索開示。`claim_scope` と `run_kind` を search_config と report の両方へ載せ、
  「探索であり正式系列・本格格子ではない」ことを成果物自身が述べる (D1813 の開示要求)。
- (S3) PBS 台本と投入 script が新 RUN_KIND を受理する。genome 数の完了検査は 5 に対応させる。
- (S4) 既存テスト file への test 追加 (新規 test file は作らない = 受入台帳・自走 harness の
  追加を避ける)。
- (S5) 3 workload へ投入する。

**入れない (scope 外):**
- `EXTENDED_SWEEP_US` への点追加。凍結格子であり、`test_backoff_extended_sweep.py` が
  `EXTENDED_SWEEP_US[-1] == 1000` で上端を pin している。探索値を正式格子へ混ぜないという
  D1813 の要求そのものにも反する。
- 本格格子・停止基準 (飽和判定) の事前登録・凍結。D1813 が明示的に本 wave の後へ置いた。
- `T2266_*` の一般化・共通化。既存の凍結成果物名に触れる risk があり、族一般化の 2 例条件
  (DW-G03) を満たさない。
- 新しい gate・検査・台帳・互換層。引数が明示的に scope 外とした。

## 不変条件 (破ったら赤)

- `EXTENDED_SWEEP_US`、`T2266_*`、`encode_static_backoff_us` / `decode_static_backoff_us` の
  式、`patches/silo-backoff-fixed.patch`、`pin.CURRENT_PIN`、`EXPECTED_FREEZE_TREES_SHA256`、
  `output/s1-freeze` / `output/s8b-freeze` の bytes を変えない。
- **規律 2:** 新 RUN_KIND でも condition gate (`_require_condition_gate_before_measurement`) と
  静的 amount ごとの binary hash 相異検査 (`_require_distinct_static_binary_hashes`、
  t2266 は `require_all_binary_hashes=True`) を通す。探索だからと緩めない。
- `EXPECTED_WALLTIME_S=18000` と `REPS`/`EXTIME` を変えない (「同じ反復数・walltime 枠」の実体)。
- 探索の campaign identity は正式系列と別 (`spec_slug` / `trial` / `scale` が別文字列)。
- no-touch: `tools/pegasus/probes/t2187_adaptive_const_probe.py`、
  `orchestrator/campaign/backoff_policy_performance_analysis.py`、
  `orchestrator/campaign/b10_backoff_shape_sweep.py`。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1) 探索専用の report (.dat/.json) を出す。** 出さずに campaign 成果物だけでも計測は成立するが、
  D1813 の「成果物に開示する」を満たす場所と、第 2 段の事前登録が読む入口が要る。t2266 が同じ形を
  既に持つ。→ 攻撃点: 本当に必要か、campaign の search_config への開示だけで足りないか。
- **(P2) 文脈 2 点 (`none` / `adaptive`) を含めて 5 genome にする。** t2266 と同型。
  D1813 の「3 点」は静的点の数を指すと読んだ。→ 攻撃点: 3 genome に絞るべきか。
- **(P3) 投入は本 wave 内で、受入緑・commit 後に wave worktree から行う。** job 本体が HEAD の
  blob と実行 file の sha256 一致を求めるため、commit 前には投入できない。land 前でも
  wave branch の commit で条件は満たされる。→ 攻撃点: land 後に main checkout から投入すべきか
  (main は他 wave の land で動き続けるため、投入元としては wave worktree の方が安定)。
- **(P4) RUN_KIND 名を `t2418-explore` とする。** → 攻撃点: 既存の命名規約・登録簿と衝突しないか。

## 成果物の形

- コード: `orchestrator/campaign/backoff_extended_sweep.py` の新 RUN_KIND 一式。
- テスト: `orchestrator/tests/test_backoff_extended_sweep.py` への追加 (新規 file は作らない)。
- 投入経路: `tools/pegasus/b10_backoff_grid.sh` / `tools/pegasus/submit_b10_backoff_grid.sh`。
- 記録: `output/insights/2026-09-09_t2418-backoff-static-explore/`、worklog、投入 receipt。

## 並列分割方針 (軽量版)

設計択一が P1〜P4 で割れており、正しさ防壁 (condition gate・binary hash 相異) と
凍結格子に隣接するため、**段 2 プラン起草 + 段 3 敵対相談 2 本 + 段 6 レビュー 2 本を省かない。**
段 5 実装は 1 子 (編集面が 1 module + 1 test + 2 shell script で分割の利が小さい)。
