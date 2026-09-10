## 読んだもの

全文を読んだ一次資料:

- `s1-brief.md`
- `s2-plan-out.md`
- `orchestrator/campaign/backoff_sweep.py`
- `orchestrator/campaign/condition_meaning_gate.py`
- `patches/silo-backoff-fixed.patch`
- `orchestrator/tests/test_condition_meaning_gate.py`
- `orchestrator/tests/test_backoff_sweep.py`

追加で該当範囲を読んだもの:

- codec と consumer: `backoff_extended_sweep.py`、`backoff_profile.py`、`backoff_requested_us.py`、`backoff_repro.py`、`backoff_overthrottle.py`
- codec test: `test_backoff_extended_sweep.py`
- freeze producer・consumer・test: `s1_known_axes_freeze.py`、`s1_measurement_freeze.py`、`s1_verify_extime_calibration.py`、`s8b_oracle_driver.py`、`freeze_verification_hold.py`、`test_s1_known_axes_freeze.py`、`test_frozen_artifacts.py`
- `test_reflux_ir.py` の freeze 参照部

pytest は実走していない。書込みも行っていない。

## 所見

**所見 1: 非負値の witness は実 conditional を通らず、選択枝が逆でも green になり得る**

- 根拠:
  - 実 source の枝選択は `patches/silo-backoff-fixed.patch:69-73`、式本体は `:70`。
  - `MeaningCase` が枝選択を宣言できるのは `-1` と `STOCK_ADAPTIVE_BRANCH` の組だけである。非負値へ `SYNTHESIZED_BACKOFF_BRANCH` を指定すると constructor が拒否する。`condition_meaning_gate.py:413-425`
  - 非負 case は `evaluate_define_runtime_meaning()` から `assert_backoff_fixed_meaning()` へ入る。`condition_meaning_gate.py:3374-3395`
  - 後者が実 source から取り出すのは conditional 全体ではなく `block.hole` だけであり、それを独立 TU に直接挿入する。`condition_meaning_gate.py:4235-4246`、`:1387-1415`
  - compile・実行結果との bits 比較自体は実 compiler 経由である。`condition_meaning_gate.py:4267-4304`
  - supply arm は requested と default の preprocess bytes が「違う」ことしか要求せず、どちらが合成枝かは見ない。`condition_meaning_gate.py:2590-2627`
  - 両 arm が green なら admission は green になる。`condition_meaning_gate.py:4063-4068`

- 具体的な失敗シナリオ:
  - 実 source の `#if BACKOFF_FIXED >= 0` を `#if BACKOFF_FIXED < 0` に変える。
  - requested `5` は誤って stock 枝、control `-1` は合成枝になるため、preprocess bytes は異なり supply は green。
  - meaning arm は predicate を捨てて hole だけを `BACKOFF_FIXED=5` で compile し、5.0 を観測して green。
  - family は admitted だが、実 target は stock adaptive で走る。規律 2 と「実 source で要求 µs を確認」の両方を破る。
  - repository patch の一行だけを変える変異は `test_condition_meaning_gate.py:2394-2405` の fixture anchor が落とす。しかしこれは静的な patch-fixture 同一性であり、production gate が捕捉した live source の枝方向を証明してはいない。

- `MeaningCase` の非負値検証が要求するのは、exact `int` かつ 0 以上、二要素 tuple、有限 binary64 bits だけである。上限、static wire domain、両 context の同値、raw と期待 bits の関係、合成枝選択は要求しない。`condition_meaning_gate.py:413-433`
  - `MeaningCase(1000, ("0000000000000000", "0000000000000000"))` は構築でき、現行 hole では pointwise green になる。
  - `MeaningCase(12000, ("40c3880000000000", "40c3880000000000"))` も構築でき、現行 hole の 10000.0 と一致して green になる。
  - `MeaningCase(5, ("c014000000000000", "c014000000000000"))` すら constructor は受ける。現行 source では mismatch red になるが、非負物理量という宣言規則は型に存在しない。

深刻度: **blocker**

**所見 2: Python と C++ は別経路だが、driver の要求意味は独立に宣言されていない [恒真ゲート]**

- 根拠:
  - プランは期待値を raw から `decode_static_backoff_us(raw)` で作る。`s2-plan-out.md:14-16`、`:42-47`
  - Python codec は `0..999 -> raw`、`3000..11999 -> raw-2000`。`backoff_extended_sweep.py:64-79`
  - C++ の静的枝も同じ二式を持つ。`silo-backoff-fixed.patch:69-70`
  - compile 観測は Python decoder を呼ばないため、C++ 式だけを壊せば mismatch になる。この意味では文字どおり同一関数を二度読む恒真化ではない。`condition_meaning_gate.py:4235-4304`
  - しかし helper の引数は raw macro 値だけで、caller が要求した物理 µs を持たない。`backoff_sweep.py:88-93`
  - `backoff_sweep` 自身は `SWEEP_US` を raw flag へ直接入れ、表示も raw を `fixed={bf}us` と扱う。`backoff_sweep.py:193-202`、`:425-429`
  - 一方 extended driver は物理量を encode して raw にし、表示時は decode する。`backoff_extended_sweep.py:438-445`、`:890-897`

- 具体的な失敗シナリオ:
  - `backoff_sweep` 規約で「3000 µs」のつもりで raw 3000 を渡す。
  - プランの helper は同じ raw を 1000 µs と自己解釈し、C++ hole も 1000.0 を返すので green。
  - driver 表示は `fixed=3000us`、実行意味は 1000 µsとなる。F718 と同じ「要求意味と wire 値の混同」を別の値で再生できる。
  - プランの raw 3000 正例は、caller がどこで 1000 µs を要求したかを示さず、decoder が出した 1000 を期待値に採用している。

期待値は driver が保持する物理量から渡す必要がある。少なくとも raw 値だけから「driver の要求意味」を復元したことにはできない。

深刻度: **blocker**

**所見 3: 負例が新しい production wiring の mismatch 経路を通らない**

- 根拠:
  - プランの production 負例は raw 1000 を static domain 外として早期拒否する。compiler mismatch は別に手製 `MeaningWitnessDeclaration` を直接 evaluator へ渡して確認する。`s2-plan-out.md:49-53`、`:125`
  - 後半と同じ generic evaluator 検査は既に存在する。`test_condition_meaning_gate.py:414-428`、`:447-462`
  - production helper は supply、meaning、family admission を順に作り、red record を `RuntimeError` にする。`backoff_sweep.py:127-168`

- 具体的な失敗シナリオ:
  - 新しい raw-to-declaration wiring を削除、または一部の値だけ `declaration=None` に戻す。
  - raw 1000 の production test は domain reject のまま通る。
  - compiler mismatch test は手製 declaration を使うため通る。
  - 従って負例は新しい wiring が mismatch を family red、さらに helper の build 前拒否へ運ぶことを検査しない。

許可域の raw 5 または 3000について fixture の hole を改変し、production helper 自体が `decoded-meaning-mismatch` 由来で拒否する負例が必要である。

深刻度: **must-fix**

**所見 4: freeze に current-source consumer が無いという親 brief の推論は反証される**

- 根拠:
  - freeze は `backoff_sweep.py` を三箇所で `4e7fa96e...` と記録する。`known_axes_freeze.json:152-154`、`:378-380`、`:604-606`
  - 静的実測した現行 hash は `1b64f897309d9104aa089353dfd7474ca50bc349fcb410d5f9807aa55b7b8773` で、親の記載どおり不一致。
  - `s1_known_axes_freeze.verify_document()` は全 `sources` の現行 file hash を再計算し、不一致を拒否する。`s1_known_axes_freeze.py:877-892`
  - さらに canonical freeze の generator 記録は `1d4d45a3...`。`known_axes_freeze.json:5-7`。現行 generator は静的実測で `8fea2bf2...` なので、実際には source loop より先の `s1_known_axes_freeze.py:872-875` で止まる。backoff mismatch が早期の別 mismatch にマスクされているだけである。
  - current-source を要求する直接 consumer は存在する:
    - measurement freeze: `s1_measurement_freeze.py:160-167`
    - extime calibration: `s1_verify_extime_calibration.py:230-268`
    - oracle driver: `s8b_oracle_driver.py:509-522`
  - 一方、freeze JSON 自体の bytes 検査は hold 中に対象から外れる。`test_frozen_artifacts.py:162-195`、`freeze_verification_hold.py:14-38`
  - acceptance test は canonical artifact ではなく fresh `build_document()` を検証し、「現状ドリフトに非依存」と明記している。`test_s1_known_axes_freeze.py:650-662`

- 具体的な失敗シナリオ:
  - この変更後も freeze bytes test は held または unchanged で通る。
  - 同時に production の canonical `verify_document()` は generator mismatch、そこを直せば backoff source mismatch で赤になる。
  - 従って「consumer があれば既に acceptance が赤」という背理法は成立しない。検査の hold、fresh-document test、早期 mismatch のマスクを区別していない。

freeze を再発行しない方針自体とは別に、「current file 一致を要求する consumer は無い」という記述は削除または訂正が必要である。

深刻度: **must-fix**

## 親 brief への攻撃

- `s1-brief.md:33-34` の恒真化禁止は、コード経路の分離だけなら満たす。Python expected と compiled C++ observed は別物であり、C++ hole の一方的変更は既存 test が落とす。
- ただし driver intent の出所は独立していない。raw を同じ static codec で解釈して期待値に戻すため、「driver が要求した意味」ではなく「wire decoder が述べる意味」を自己宣言している。
- `s1-brief.md:26-27` の規律 2 は、meaning arm が観測できる mismatch については `condition_meaning_gate.py:4063-4068` と `backoff_sweep.py:159-168` が守る。しかし conditional の枝方向は観測対象外なので、誤った target branch を green にできる。
- stock `-1` の主張は裏づけられる。`MeaningCase` は `(-1, None, STOCK_ADAPTIVE_BRANCH)` 以外の branch declaration を拒否し、実 conditional の branch と stock body の双方を検査する。`condition_meaning_gate.py:416-424`、`:2712-2826`。既存 helper test も `test_backoff_sweep.py:169-194` で守る。
- raw 3000 -> 1000.0、raw 1000 -> 0.0 という現行 hole の説明は正しい。問題は、その body が actual target で選択されたことと、1000.0 が caller intent だったことを同時に証明していない点である。
- freeze hash の実測値は正しいが、consumer 不在への一般化は誤りである。

## 守られていない行

- `s2-plan-out.md:69-71` の「全 0..999 と 3000..11999 に宣言を作る」一般性:
  - 実 helper 正例は raw 5 と raw 3000だけである。
  - 実装条件を `value in {5, 3000}` に狭めても計画中の二正例は通る。raw 0、999、11999などは `unestablished` のまま admitted になり、落ちる計画 test が無い。

- `s2-plan-out.md:71` の「-2 以下は不変」:
  - `value == -1` を `value < 0` に壊し、-2 を stock declaration 構築へ流すと早期 `ValueError` になるが、既存・計画 test に -2 の helper 回帰が無い。`-1` test は通る。

- `s2-plan-out.md:71,120-122` の production domain 境界:
  - helper で試す拒否値は 1000だけで、1001、2999、12000 の helper 到達テストが無い。
  - `test_backoff_extended_sweep.py:400-418` は codec 単体の境界を守るが、helper が decoder 例外を `unestablished` に変換しないことまでは守らない。

- `s2-plan-out.md:38-40,73-75` の単一 codec 所有:
  - extended 側の旧定義 `backoff_extended_sweep.py:60-79` を残しても、既存の値ベース codec test は通る。
  - `backoff_extended_sweep.decode_static_backoff_us is backoff_sweep.decode_static_backoff_us` のような再輸出 identity test が無く、二重正本化を検出できない。

- `condition_meaning_gate.py:4235-4246` の hole-only 評価:
  - copied fixture の predicate を反転して production helper を呼ぶ test が無い。
  - patch 一行変異は `test_condition_meaning_gate.py:2394-2405` の静的 anchor が落とすが、live gate の枝選択能力は守っていない。

- `test_backoff_extended_sweep.py:919-933`:
  - extended wrapper の実 test は supply と admission だけを確認する。meaning が `unestablished` でも admission は true なので、encoded point の meaning green 化を直接守らない。

一方、次の行は現行 test で守られている。

- C++ hole の低域式: `test_condition_meaning_gate.py:268-300`
- C++ hole の raw 3000 上域式: `test_condition_meaning_gate.py:302-310`
- static codec の全 0..9999 round-trip と境界: `test_backoff_extended_sweep.py:400-418`
- stock `-1` の branch と body: `test_backoff_sweep.py:169-194`、`test_condition_meaning_gate.py:906-961`
- family が meaning red を拒否すること: `test_condition_meaning_gate.py:1814-1831`

## 裁定候補

- driver intent の渡し方を裁定する必要がある。推奨は、6 consumer が raw と独立した物理 µs を helper へ渡す案である。codec の再呼出しだけを caller 側へ移す案では独立性は増えない。
- 非負 witness は「hole の pointwise 値」だけでよいのか、「実 conditional が synthesized branch を選び、その値になる」まで要求するのか。親 brief の完了判定を維持するなら後者が必要で、現行 `MeaningCase` では表現できない。
- generic `MeaningCase` 全体を static domain に狭めるかは scope 外の API 裁定である。T-2419 内では専用 declaration 型または production builder の厳格検査に閉じる方が影響が小さい。
- legacy freeze の current-source 検証を復旧するか、frozen-head blob 検証へ変えるか、再発行するかは別 wave の裁定対象である。本変更で「consumer 不在」と扱うのは不可。

## 総括

blocker は、非負 witness が実 conditional の選択枝を観測しないことと、caller intent を独立に宣言しないことの 2 件。  
計画中の F718 負例は evaluator 自体には到達するが、新しい production wiring の red 経路を守らない。  
stock `-1` と C++ hole の代表値は既存 test で守られている。  
freeze consumer 不在という親 brief の推論は反証された。