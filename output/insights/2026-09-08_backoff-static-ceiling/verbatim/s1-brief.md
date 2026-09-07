## 段 1 brief

**scope:** 静的 backoff の表現可能上限を閉じる設計判断 1 件と、その実装。二択は
(A) 符号化を直して 1000 µs 以上の静的点を表現可能にする、(B) 静的域の上限を 999 と明示的に固定する。
仮想リスク向けの gate・検査・台帳・一般化の新設は scope 外 (依頼文の明示)。

**確定済みユーザー裁定:** 規律 2 を緩めない。実装面は Codex `role=author` (D95)。F718 を先に読む
(読了済み)。上限の設計判断と実装だけ。着手直前の local main から fresh worktree (実施済み)。

**不変条件:**
1. `BACKOFF_FIXED=-1` の stock 枝と inert 性 (preprocess 後ソースが原本と同一) を 1 bit も変えない。
2. 既に測り終えた値の意味を変えない — 0..999 の定数域、1000..1999 の symmetric-modulo、
   2000..2999 の binary は数値的に不変。`test_p03_legacy_zero_through_999_is_numerically_identical`
   と `test_exact_finite_models_distinguish_registered_shapes_and_dormant_code2` が既にこれを pin する。
3. B-10 の凍結束縛を黙って破らない。`docs/b10-backoff-shape-preregistration.md` (schema v4) は
   `artifacts.patch_sha256` と `artifacts.formula_sha256` と `grid.encoding` を pin しており、
   完了済み official 系列 (write-heavy 45 record digest、balanced 系列) が同じ束縛の下にある。
4. C++ の hole line と Python の写し (`exact_model`) は常に同じ関数を表す。

**成果物:** 裁定した案の実装 (patch の hole line か格子定数)、既存 `condition_meaning_gate` の
runtime-meaning witness による正例・負例、影響テストの更新、insight + worklog/decisions fragment。

**分割方針:** 実装面あり → 段 5 Codex author 必須。設計択一が割れ、凍結束縛と受理集合に触るので
段 2・3 の敵対検証子と段 6 review を省かない (軽量版ではあるが子ゼロにはしない)。

**DW-G05 成果物影響:** 放置すると B-10 待ち方 campaign は静的 backoff を 999 µs までしか張れず、
abort 抑制が飽和する領域を欠いたまま「待ち方の形」の材料レポートが確定する。

**DW-G01 生死実験先行:** 新符号化の生死は既存 `condition_meaning_gate` の runtime-meaning witness
(hole を評価 TU へ materialize し `#define BACKOFF_FIXED <値>` で `now_backoff` の double bits を読む)
で確認できる。専用機構・新規 driver は作らない。

### 割れうる前提 (親の provisional 裁定・攻撃対象)

- **(P1)** (B) 単独では依頼の目的を満たさない。entry 1314 が受領した実測は「999 でも abort 抑制が
  飽和していない」であり、上限を 999 に固定しても測れない領域は測れないままである。
- **(P2)** (A) は既存 3 モードの数値を保ったまま実現できる。現行 decoder の `code >= 3` は
  `Fraction(mean_us)` (= 定数 r) へ落ちる未使用域であり、ここを静的高値へ割り当てれば
  0..2999 の意味は不変にできる。ただし hole line の bytes が変わるので (3) の束縛は必ず動く。
- **(P3)** (A) を採る場合、B-10 prereg は版を立て直す必要がある。既存 official 系列の値は
  無効化しない (規律 7: 記録された測定は現行コードとの差だけでは無効にならない) が、
  新しい静的高値の点は新しい登録の下で測る。
- **(P4)** `EXTENDED_SWEEP_US` は依然 1000 を末尾に持ち、`test_backoff_extended_sweep.py:280` の
  `assert M.EXTENDED_SWEEP_US[-1] == 1000` が汚染点を pin している。どちらの案でもここは触る。

### 変更面 (実アンカー表)

| path:anchor | 現物 | 役割 |
|---|---|---|
| `patches/silo-backoff-fixed.patch` (合成枝 1 行) | `#if BACKOFF_FIXED >= 0` の `double now_backoff = ...` | 符号化の正本 (C++)。sha256 `36cd974c56c6f103d894a53048ac734d9859def266c05898d3794d2c48470832` |
| `orchestrator/campaign/b10_backoff_shape_sweep.py:263` | `EXPECTED_HOLE_LINE` | hole line の逐語 byte pin |
| 同 `:264` | `FORMULA_SHA256` | 上記から導く hash |
| 同 `:648-653` | `encode()` = `SHAPE_CODES[shape] * 1000 + mean_us` | 送信側の符号化 |
| 同 `:722-742` | `exact_model()` | 受信側の decoder の Python 写し |
| 同 `:1048` | `grid["encoding"] != "BACKOFF_FIXED=shape_code*1000+mu"` | prereg spec との照合 |
| `docs/b10-backoff-shape-preregistration.md:286,320` | `artifacts.patch_sha256` / `grid.encoding` | 凍結 prereg の束縛 |
| `orchestrator/campaign/backoff_extended_sweep.py:55-70` | `EXTENDED_SWEEP_US` (末尾 1000) / `T2266_REQUESTED_US` / `T2266_REALIZED_US` / `T2266_UNREALIZED` | 格子定数 |
| `tools/t2216_backoff_walk_model.py:53` | `TAIL_BACKOFFS = (150,200,300,500,750,999)` | model 側の tail 格子 |
| `orchestrator/tests/test_backoff_extended_sweep.py:280` | `assert M.EXTENDED_SWEEP_US[-1] == 1000` | 汚染点の pin |
| `orchestrator/tests/test_b10_backoff_shape_sweep.py:2564,2583` | 0..999 恒等 / code2 休眠 | 数値不変の pin |
| `orchestrator/campaign/condition_meaning_gate.py` | `BACKOFF_FIXED` の runtime-meaning witness | F718 型の検出器 (既存) |
| `orchestrator/campaign/p3_s4_red.py:171` | `BACKOFF_FIXED=999` | 赤系 genome の literal |

### 実測した新事実 (依頼文の前提との差)

1. **「格子の上端が 999 に固定されている」は T-2266 の tail 格子については既に main に着地済み。**
   `backoff_extended_sweep.py:64-70` に requested (…,1000) と realized (…,999) の分離と
   `T2266_UNREALIZED = {1000: "F718 — 現符号化では商 1・振幅 0 となり固定 0 へ復号される"}` があり、
   `t2216_backoff_walk_model.py:53` も 999。依頼文が「固定するか」と問う案 (B) の一部は実施済みである。
2. **`EXTENDED_SWEEP_US` は 1000 を持ったまま。** 上の分離は t2266-tail 系列にだけ入っており、
   29 点の拡張格子は汚染点を含んだまま test で pin されている。
3. **符号化の実体 (現物読解 + Python 写しで裏取り):** q = V/1000、r = V%1000。
   q=0 → 定数 V、q=1 → symmetric-modulo 振幅 r、q=2 → binary 振幅 r、q>=3 → 定数 r。
   binary (code 2) は prereg v4 の R1 で登録外だが hole line には残る「byte-pinned dormant」。
4. **F718 型の検出器は既に実在する。** `condition_meaning_gate` の runtime-meaning witness が
   hole を評価 TU へ materialize して `now_backoff` の double bits を読む。よって
   新設 gate は不要の見込み (DW-O13 非成立)。子はこの前提を攻撃してよい。
