# [T-2419] 非負 BACKOFF_FIXED に production の意味宣言を渡す

2026-09-09 / branch `worktree-dev-wave-t2419-meaning-decl` / base main `cbcdb6c91`

## 何が問題だったか

意味判定器 `orchestrator/campaign/condition_meaning_gate.py` は前から実在していた。
`BACKOFF_FIXED = -1` (stock adaptive) には枝選択の witness が渡っており green になる。
しかし**非負値には宣言が渡っていなかった**。`backoff_sweep.py` の
`_require_backoff_condition_gate` は、宣言を作るのを `requested_value == -1` のときだけに
限っており、それ以外は `declaration=None` を渡していた。判定器はこれを
`unestablished` / `meaning-witness-undeclared` として第三の状態に落とし、admission は通る。

結果として、この helper を通る 6 driver (backoff_sweep / backoff_extended_sweep /
backoff_profile / backoff_repro / backoff_overthrottle / backoff_requested_us) の
**静的 backoff 要求はすべて「意味は未確立」のまま成果物へ持ち越されていた**。

これが実害を生んだ形が F718 である。B-10 拡張格子の上端 1000 µs が、合成枝の符号化
(商がモードを選び、剰余が振幅になる) の境界と一致していたため、実際には振幅 0 の乱択モード
= 実質 0 µs を測り、その値を成果物へ記録した。供給検査は通っている。供給され、適用され、
検査も通った。違ったのは**値の意味**だけである。

## 何を入れたか

`_require_backoff_condition_gate` に必須 keyword `backoff_fixed_physical_us: Mapping[int, int]`
を足した。生値から、その driver が意図した物理 µs への写像である。

- key の集合は、要求された非負 `BACKOFF_FIXED` の集合と**完全一致**しなければならない。
  欠けても余っても source capture の前に `RuntimeError` になる。
- 非負値の宣言 bits は `canonical_float64_bits(float(physical))` を 2 文脈へ複製する。
- **判定器側は符号の変換を一切しない。** codec (`encode/decode_static_backoff_us`) は
  `backoff_extended_sweep.py` に残したままで、gate からは呼ばない。
- `-1` の stock branch witness と他 macro の扱いは変えていない。

呼び出し面 6 箇所が写像を渡す。物理値が scope にある場所で作る。

| driver | 写像の出所 |
|---|---|
| `backoff_sweep.py` | `SWEEP_US` が物理格子そのもの (`{n: n}`) |
| `backoff_extended_sweep.py` | run kind の物理格子から `{encode(a): a}` |
| `backoff_profile.py` | `amounts` が物理量 (`{a: a}`) |
| `backoff_repro.py` | 点を組み立てた物理集合 (`{n: n}`) |
| `backoff_overthrottle.py` | 継承点しか持たないので driver 自身の `_point_backoff_us` (decode 由来) |
| `backoff_requested_us.py` | 非負要求が無いので空写像 |

## なぜこれが恒真ゲートではないか

期待値は Python 側の driver intent、観測値は捕捉した合成枝を独立 TU へ埋めて
**実 C++ compiler で評価した値**である。同じ式を二度読んでいるのではない。

段 2 の当初案は「生値を codec で逆算して期待値にする」だった。段 3 の 2 レンズが
**独立に同じ blocker へ収束**してこれを倒した。逆算では driver が何を要求したかを証明できず、
たとえば `SWEEP_US` へ「物理 3000 µs のつもりで 3000」を足すと、宣言も観測も 1000.0 になって
素通りする。F718 と同型の事故がそのまま通る。段 4 はこれを採り、driver に物理 µs を
渡させる設計へ変えた。

副産物として実装は当初案より**小さくなった**。wire domain の一律拒否 (新しい拒否面) が
不要になり、codec の移動も不要になって循環 import の論点ごと消えた。

## 受理・拒否の変化

| 生値 | intent | 変更前 | 変更後 |
|---:|---:|---|---|
| `-1` | 写像に無し | stock branch meaning green | 不変 |
| `5` | `5` | unestablished、受理 | green、受理 |
| `3000` | `1000` | unestablished、受理 | green、受理 |
| `1000` | `1000` | unestablished、受理 | **観測 0.0 と不一致で red、build 前に拒否** |
| `1000` | `0` | unestablished、受理 | 観測一致なら green、受理 |
| 任意の非負値 | 観測と不一致 | unestablished、受理 | red、拒否 |
| 任意の非負値 | key 欠け・余り | 契約なし | capture 前に `RuntimeError` |

受理集合は狭まる方向にだけ動いている。

## 実測

- 焦点走 **470 passed / 0 failed** — backoff 系 6 file、意味判定器、screening 2 file、
  compiler binding、site aware、s1 direct comparison の 12 file。
  実 C++ compiler と cmake を使う node を含み、skip は 0。
- 新規 test node 3 件。
  - `test_real_family_helper_observes_raw_3000_as_intended_static_1000` (符号化点の正例)
  - `test_real_family_helper_rejects_f718_intent_and_evaluator_records_red` (F718 の負例)
  - `test_family_helper_rejects_physical_intent_contract_before_source_capture` (写像契約の負例)
- 期待値を変えた既存 assert は 1 箇所だけ
  (`test_real_family_helper_admits_effective_define_and_recomputes_file_digest` の
  meaning が `unestablished` から `green` へ)。

## 変異

台帳は `mutation-final.json` (本走) と `mutation-probe.json` (probe)。
どちらも repo head `fe92c890f`、runner は `tools/run_tests.py --force-dispatch` の
dispatch 経路。**5/5 KILLED、期待 node 完全一致、SURVIVED 0、MISMATCH 0。**

段 4 の当初登録では M1 と M5 の期待集合が重なっており、段 6 レビュー A が
「変異の帰属が分離されていない」を must-fix にした。probe 走 (全件 SURVIVED 登録) で
実測 node を集め、M5 を別の位置へ再照準してから本登録した。

| ID | 変異 | 実測で死んだ node |
|---|---|---|
| M1 | 非負値の宣言を `None` に戻す | 正例 (生値 5)、正例 (生値 3000)、F718 負例 の 3 件 |
| M2 | 宣言 bits を物理 µs でなく生値から作る | 正例 (生値 3000) の 1 件だけ |
| M3 | 写像 key の完全一致検査を外す | 契約負例の 1 件だけ |
| M4 | extended の写像を生値=物理に変える | 正例 (生値 3000) の 1 件だけ |
| M5 | 2 文脈目の期待 bits を 0.0 にする (過剰拒否) | 正例 (生値 5)、正例 (生値 3000)、extended の実 gate node の 3 件 |

**M2 が本設計の核心を実証している。** 生値と物理が一致する点 (生値 5) は死なず、
符号化点 (生値 3000 が物理 1000) だけが死ぬ。つまりこのテストは
「宣言が driver の intent から来ているか、生値の逆算から来ているか」を実際に区別している。
段 3 の 2 レンズが倒した当初案は、まさにこの区別ができない設計だった。

M5 は受理集合を狭める wave に要る「承認外の過剰拒否の正例」である。M1 と違って
F718 負例は死なず (元から赤なので)、代わりに extended の実 gate node が死ぬ。
期待集合が分離していることが実測で確認できた。

anchor は 5 件とも注入箇所 1 件ずつで、単一理由である。

## この関門が守っていない範囲 (明記)

- **合成枝が実際に選ばれたことは観測していない。** 意味の節の proof kind は
  `compiler-evaluated-captured-applied-source-decoder-standalone-tu-finite-pointwise-witness`
  であり、捕捉した hole を独立 TU で評価するだけで、`#if BACKOFF_FIXED >= 0` の枝選択は見ない。
  `unestablished_meaning_macros` の契約も「その proof_kind の境界内で established」と述べている。
  この境界は本 wave でも変えていない。
  ただし 6 driver はいずれも同じ family 呼び出しに `-1` を含み、`-1` の供給の節は
  `stock-inert-preprocess-identical` を要求するので、条件式を反転させる改変は供給側で赤になる。
- **generic screening 経路は対象外。** `screening_driver.py` は今も宣言を常に `None` にしており、
  生値 1000 を `unestablished` のまま admit する。backoff sweep 自身は先行する family gate が
  支配するので止まる。
- **b10 shape driver は本 helper を通らない。** 乱択 shape の生値 1002〜1100 は正当な符号であり、
  独自の閉じた格子・式 pin・applied-tree 検査・物理残差検査を持つ。
- **凍結の再発行はしていない。** `output/s1-freeze/known_axes_freeze.json` は
  `backoff_sweep.py` の sha256 を記録しており、`verify_document()` は現行 file を
  live で再 hash して照合する。ただし記録値は本 wave の**前から**現行と乖離しており
  (generator hash の乖離が手前で先に止まる)、本 wave が作った赤ではない。

## 裁定へ返すもの

1. **generic screening にも意味宣言を入れるか。** 入れる場合、b10 の乱択帯を一律に
   static codec で解釈してはならないので、static scalar と randomized shape を別の宣言型
   または別 helper へ分ける設計が要る。
2. **T-2418 の `meaning_witness_status`。** `backoff_extended_sweep.py` の固定文字列
   `unestablished_for_positive_backoff_fixed_as_in_existing_sweep` は、本 wave 以後に
   同 driver を再走すると live の実態と食い違う。既存 artifact は不変でよいが、
   新規 run の metadata としては偽になる。直すには campaign identity と report schema の
   版上げが要り、T-2418 の事前登録に触れる。
3. **凍結 source hash の位置づけ。** `known_axes_freeze.json` の source sha を
   「歴史的出所」として保持するのか「live source 一致 gate」として使い続けるのか。
   前者なら live verifier から当該比較を外す版上げ、後者なら明示的な再凍結と
   trust root 更新が要る。
4. **`s1_direct_comparison.py` と `paper_story_a2_certification.py`** は正値を常に
   `float(raw)` と宣言する独自経路である。現行値は 999 以下なので正しいが、
   符号化上側へ広げると正しい生値 3000 まで誤って red にする。本 helper の scope 外。
