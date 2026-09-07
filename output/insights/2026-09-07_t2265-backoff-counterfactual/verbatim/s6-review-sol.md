## 赤 1 は patch C の token paste が直接原因

深刻度: blocker  
根拠: `patches/cicada-adaptive-counterfactual.patch:265-273`、`reds.md:9-23`  
成果物影響: T-148 により認証経路が停止し、親が実測した 23 件の赤を生む。

patch C 内で `##` または `%:%:` が現れるのは `value##ULL` の 1 箇所だけであり、親の帰属は正しい。`source_digest` の変更、走査除外、別 file への移設は防壁の迂回なので不可。

`#include` を増やさない正しい修正候補は次のとおり。

- CMake が既存の十進 seed 値を compile definition として出す時点で `ULL` を付け、C++ 側は `BACKOFF_STEP_POLICY_SEED` を直接初期化に使う。
- seed を CMake から引用符付き十進文字列として渡し、patch C 内の `constexpr` 十進 parser で `uint64_t` にする。追加 include は不要で、token paste も要らない。
- 二段 stringification と `constexpr` parser を同じ `include/backoff.hh` 内に置く。ただし新しい裸マクロを残さず、使用直後に `#undef` する。

単純に `static_cast<uint64_t>(BACKOFF_STEP_POLICY_SEED)` へ置換するだけでは不可。既定値 `11400714819323198485` は符号付き `long long` の上限を超えるため、無接尾辞の十進整数として解釈させると GCC の診断が `-Werror` で失敗し得る。

## 赤 2 は期待値ではなく負勾配生成器が壊れている

深刻度: blocker  
根拠: `orchestrator/tests/test_dynamic_backoff_transitions.py:524-536`、`patches/cicada-adaptive-dynamic.patch:399-420`  
成果物影響: 5 件の baseline failure により M4 と M6 の変異証拠も成立しない。

`force_gradient` は常に `time_diff=100`、`committed_diff=100`、`clocks_per_us=1` なので、今回の throughput は `1,000,000` になる。一方、負勾配用の前値は `2.0` にしか設定されていない。通常の入力では `backoff_diff>0` でもあるため、`sign=-1` を渡しても実勾配は正になる。

現状の意味から導かれる出力は次のとおり。

- `series` の B 単独と policy 0: `101,101,99,101`
- `safe` の policy 0: `101,101`
- `safe` の policy 1: `99,99`
- step adapt × dynamic ceiling の 4 組すべて: policy 1 は `99,99`
- dynamic shrink、policy 0: `after=201 gradient=1 recommended=1 assigned=0 realized=0 feasible=1 ceiling=400`
- dynamic shrink、policy 1: `after=199 gradient=1 recommended=1 assigned=1 realized=1 feasible=1 ceiling=400`
- fixed upper、policy 1: `after=998.5 gradient=1 recommended=1 assigned=1 realized=1 feasible=0 ceiling=1000`

意図した場面へ直す最小候補は `test_dynamic_backoff_transitions.py:529` の負勾配用前値を `2,000,000.0` にすること。その場合、意味から導かれる期待値は以下になる。

- B 単独と policy 0: 両者の実出力を直接比較し、結果は `101,99,99,101`
- `safe`: policy 0 は `101,99`、policy 1 は `99,101`
- 4 compile 組の policy 1: すべて `99,101`
- dynamic shrink: 両 policy とも `after=100 gradient=-1 recommended=-1 realized=0 feasible=0 ceiling=100`
- fixed upper、policy 1: `after=1000 gradient=-1 recommended=-1 assigned=1 realized=0 feasible=0 ceiling=1000`

`test_policy_zero_matches_patch_b_transitions_exactly` の固定 literal assertion は削除し、`policy_zero == b_only` だけを不変条件にすべきである。

## 反転本体は裁定どおりで、赤 2 に合わせて変更してはならない

深刻度: blocker  
根拠: `patches/cicada-adaptive-counterfactual.patch:470-577`、`ruling.md:22-28,56-60`  
成果物影響: patch C を現在の誤った期待値へ合わせると、正しい反転意味論を破壊する。

4 通りの `BACKOFF_STEP_ADAPT × BACKOFF_DYN_CEILING` すべてで、推奨更新は `patch:474-506` で完了し、その共通後段で反転される。

- origin は推奨更新前の `new_backoff` として `patch:470-472` で保存される。
- `recommended_delta_sign` は推奨更新後、割当前の差分から `patch:508-516` で算出される。
- `both_actions_feasible` は更新済み ceiling を用い、推奨値と厳密な逆候補の両方について `patch:522-529` で算出される。policy 1/2 の割当より前である。
- policy 1 は必ず反転、policy 2 は bit が 1 の場合だけ反転するため、R8 の対応も正しい。`patch:532-555`
- clamp は反転後の `patch:558-565`、`inversion_realized` は clamp 後の厳密な大きさ比較として `patch:568-576` にある。

したがって、実装側に符号や ceiling の変更を入れて赤 2 を消すのは逆修正になる。

## LCG の policy 0 消去は実装済みだが検査に歯がない

深刻度: must-fix  
根拠: `patches/cicada-adaptive-counterfactual.patch:265-274,540-555`、`orchestrator/tests/test_dynamic_backoff_transitions.py:1134-1150,1368-1403`  
成果物影響: policy 0 に LCG state を残す数値条件の退行がテストを通り得る。

現物では seed、state、更新式のすべてが `BACKOFF_STEP_POLICY == 2` の分岐にあり、policy 0 から LCG は消える。診断 4 項目と marker も `BACKOFF_TRACE` 内にあり、trace=0 の 3 policy でコンパイル時除去される構造になっている。

ただし preprocess テストの禁止集合は trace 名だけで、`kBackoffStepPolicySeed`、`backoff_step_policy_state_`、LCG 定数を検査していない。また numeric-if テストは許可された行が 1 本存在することしか見ない。例えば seed guard を `#if BACKOFF_STEP_POLICY >= 0` に広げても、既存 assertion を通過する。

policy 0 の preprocess 出力について LCG の 2 symbol と乗数・加数を明示的に禁止し、policy 2 では存在を要求する必要がある。

## `both_actions_feasible` の片腕を落とす変異が残る

深刻度: must-fix  
根拠: `orchestrator/tests/test_dynamic_backoff_transitions.py:632-666,1315-1365`、`patches/cicada-adaptive-counterfactual.patch:522-529`  
成果物影響: 推奨腕の境界検査を削除して逆腕だけを見る誤実装を検出できない。

赤 2 を正しく直した後の場面は、safe が両腕 feasible、partial-lower と fixed-upper が「推奨腕だけ feasible」、dynamic-shrink が両腕 infeasible になる。したがって、実装から推奨候補 `new_backoff` の境界検査を削除し、逆候補だけを検査する変異が全期待値を満たす。

上限近傍で正勾配を明示的に作り、推奨 `1000.5` は infeasible、逆候補 `998.5` は feasible、従って `both_actions_feasible=0` となる場面を追加すべきである。

`test_dynamic_ceiling_shrink_can_make_both_arms_equal` は clamp によって p0/p1 が必ず同じ 100 になる境界確認であり、反転そのものの主検査には数えられない。安全域の正負テストを主検査として緑に戻す必要がある。

## M8 は具体的な生存変異があり、M4/M6 はまだ評価不能

深刻度: must-fix  
根拠: `ruling.md:113-137`、`orchestrator/tests/test_dynamic_backoff_transitions.py:1237-1271,1281-1284`  
成果物影響: DW-M01 の「M1〜M24 は死亡」という完了主張を現状では出せない。

M8 の検査は LCG の先頭 16 bit しか見ない。加数を現在の `1442695040888963407` から `1442695040888972894`、つまり `+9487` へ変えても、同じ seed から先頭 16 bit は同じ `0111001000100110` になり、出力値列も同じになる。M8 を「加数を変える」という変異クラスとして扱うなら生存する。加数 literal 自体の静的 pin、または変更後の具体値を事前登録する必要がある。

現状で殺せない、または有効な死亡証拠を作れないものは次のとおり。

- M4、M6: 唯一の指定テストが赤 2 の baseline failure を持つため、修正前は死亡判定不能。
- M8: 上記 `+9487` の具体的 survivor がある。
- M25: 裁定どおり意図的 survivor。

M1〜M3、M5、M7、M9〜M24 には論理上の歯がある。ただし M13 の台帳上の指定 node は合成 parser 入力だけなので patch C の field 脱落を直接は見ず、実際の killer は `test_emitter_stdout_parses_with_the_real_parser` である。完全集合の記載を直す必要がある。

## 赤 3 の file 単位 allowlist はゲート緩和になる

深刻度: must-fix  
根拠: `reds.md:50-59`、`patches/cicada-adaptive-counterfactual.patch:317-357`  
成果物影響: 赤を消すため patch C 全体を免除すると、将来同 file に入る本物の裸マクロも見逃す。

赤 3 の帰属自体は正しい。seed helper 2 名は赤 1 の正修正で消せる。残る 2 名は trace marker の文字列である。

ただし `known_non_variant_patches` が file 単位なら、patch C の追加を「gate の弱体化ではない」とは言えない。既存慣行の踏襲でも受理集合は広がる。patch C 内の裸 `IZANAGI_` 集合を正確に `{IZANAGI_BACKOFF_TRACE, IZANAGI_BACKOFF_TRACE_SUMMARY}` に pin し、両者が文字列 literal にしか現れないことを検査した上で限定例外にすべきである。

着地済み 3 commit には認証の exact 2 cell 契約、A の SHA pin、既存 5/11-field literal、既存 PBS literalを緩める変更はない。赤 4 も新しい build sink と 2 define の追加に対する正当な ledger 赤であり、親の帰属は正しい。

## 総括

blocker は T-148 の token paste と、負勾配を作れていないテスト helper の 2 点。  
patch C の反転位置、割当、feasibility、realization の意味論自体は裁定どおり。  
M8 に具体的 survivor があり、LCG 消去と feasibility 片腕にも追加の歯が要る。  
pytest は実走せず、指定資料と 3 commit 差分の静的検査のみを行った。