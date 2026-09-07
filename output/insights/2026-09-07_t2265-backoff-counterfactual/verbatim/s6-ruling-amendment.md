# 段 6 裁定の補正 (段 6 レビュー 2 本を受けて。`ruling.md` と `reds.md` を上書きする)

## A. 赤 4 の帰属を訂正する (レビュー luna の blocker、採用)

`reds.md` の「新 define が build sink を増やした」は**誤り**。正体は
**単位 B が driver に行を足したせいで deferred gate 台帳の行番号 pin が失効した**ことである。
13 件は新 sink ではなく、同一 sink が移動しただけ。件数 31→33 は新 define 2 本が
同じ S1 sink で到達不能になった分である。

正しい追随 (現物を数えて確かめてから当てること):

- `orchestrator/tests/test_ccbench_spawn_sites.py:922` の `2718` → `2919`
- 同 `:934` の `3074` → `3275`
- 同 `:915-930` の理由文 `A+B stack` → `A+B+C stack`
- 同 `:2679` / `:2683` / `:2694-2704` の exact ledger の写しも同じ line と理由へ
- 同 `:2920` S1 sink: `covered=4, proven-unreachable=33`
- 同 `:2923` S8B sink: `covered=37`

## B. 赤 3 の直し方を訂正する (両レビューの must-fix、採用)

`reds.md` は「patch C を `known_non_variant_patches` へ載せるのは慣行の踏襲」と書いたが、
`test_p3_s4_loop.py:7368` の allowlist は **path 単位で全 token を免除する**ため、これは
**受理集合の拡大であり gate の弱体化**である。

**採る形:** path ごとの**許容 token exact 集合**にする。patch B / patch C では
`{IZANAGI_BACKOFF_TRACE, IZANAGI_BACKOFF_TRACE_SUMMARY}` だけを差し引き、
それ以外の裸 `IZANAGI_` が 1 件でもあれば赤にする。両 token が**文字列 literal の中にしか
現れない**ことも検査する。**赤 1 を直す前に path を免除するのは明確な弱体化なので順序を守る。**

## C. 変異事前登録の補正 (両レビューの blocker / must-fix、採用)

- **M1 の「冗長 gate」分類は誤り。** patch C の policy 条件は 4 箇所あり 1-site が特定されていない。
  `:265` の guard を `#ifdef` にしても policy 0 の遷移値は変わらず、遷移テストは赤にならない。
  **M1 の完全集合は静的 `#if` 検査 1 本だけ**とし、冗長 gate から外す。
- **M8 には具体的な生存変異がある。** 加数を `1442695040888963407` → `1442695040888972894` に
  しても先頭 16 bit は同じ `0111001000100110` になる。**加数と乗数の literal を静的に pin する
  歯を足す** (M8 の完全集合を「16 bit 系列 + literal 静的 pin」にする)。
- **M4 / M6 は baseline が赤なので現状では kill 判定不能。** 場面設定を直して baseline を緑に
  戻してから走らせる。
- **M13 の完全集合を訂正:** 台帳指定の合成 parser テストは patch C の field 脱落を直接見ない。
  実際の killer は `test_emitter_stdout_parses_with_the_real_parser` である。
- **M20 の歯は指定文字列の変異に限定される。** PBS の分類挙動 (`HAS_EXTENDED_CELL` /
  `NEEDS_DYNAMIC_OUT`) を 0 に壊しても現テストは緑なので、**挙動を実行して見る歯を足す**。

## D. 旧 v2 artifact 互換の範囲を確定する (レビュー luna の must-fix、採用)

図生成器の A+B / A+B+C 受理は正しい。しかし driver の certification / group reader は v3 のみを
受理し、legacy 定数は使われていない。**「旧 A+B artifact 全般が読める」とは主張しない。**

**採る形:** 図入力の v2 互換は維持し (テスト済み)、certification / group については
**未使用の legacy 定数を残して互換を装わない**。v2 の certification / group artifact は
**明示的な理由付きで拒否**されることをテストで固定し、境界を README と insight に書く。
**互換を実装せずに主張するのが最悪であり、それを避けるのが本項の目的である。**

## E. patch C の反転意味論は変更しない (レビュー sol の blocker、採用)

反転点・割当・`both_actions_feasible`・`inversion_realized` の位置と定義は裁定どおりであることが
現物の行単位で確認された。**赤 2 を消すために実装側の符号や ceiling を触るのは逆修正であり禁止。**
直すのはテストの場面設定と期待値の側だけである。

## F. 追加で歯を作る箇所 (両レビューの must-fix、採用)

1. **policy 0 の preprocess 検査**に LCG の symbol (`kBackoffStepPolicySeed`,
   `backoff_step_policy_state_`) と乗数・加数の literal を**禁止集合として**足し、policy 2 では
   **存在を要求**する。
2. **`both_actions_feasible` の推奨腕側の歯**: 上限近傍で正勾配を作り、推奨 `1000.5` が infeasible、
   逆候補 `998.5` が feasible ゆえ `both_actions_feasible=0` になる場面を足す
   (推奨腕の境界検査を削除する変異を殺す)。
3. **numeric-if テスト**が guard の緩和 (`#if BACKOFF_STEP_POLICY >= 0`) を素通りしないようにする。
4. **PBS の 11/12 field 分類**を、文字列一致ではなく**実際に分類を走らせて**検査する。

## G. 期待値の導出 (レビュー sol が意味から導いた値。実装ではなくテスト側を直す)

`test_dynamic_backoff_transitions.py:529` の負勾配用前値 `2.0` → `2000000.0` に直すと、
意味から導かれる期待値は次になる。**この値をそのまま焼き込まず、直した場面で実際にそうなることを
確かめてから書くこと。**

- B 単独と policy 0: 両者の**実出力どうしを直接比較**する (固定 literal の assertion は削除)。値は `101,99,99,101`
- `safe`: policy 0 は `101,99`、policy 1 は `99,101`
- 4 compile 組の policy 1: すべて `99,101`
- dynamic shrink: 両 policy とも `after=100 gradient=-1 recommended=-1 realized=0 feasible=0 ceiling=100`
- fixed upper、policy 1: `after=1000 gradient=-1 recommended=-1 assigned=1 realized=0 feasible=0 ceiling=1000`
