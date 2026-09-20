## 方針と現物との差分

**MISATTR・RUNG1・TRIGGER_GATING の 3 件を登録し、REQUESTED_US は今回は未登録とする案を推奨します。** 配線変更は `s8a_trigger_coverage._require_condition_gate` に限定します。REQUESTED_US の TU 2 箇所だけを代表として登録する案は採りません。

HEAD は指定どおり `947fd160ab44e6ae82b6eab56ee8d70813fda31d`。必読 3 資料と指定実装を静的に確認しました。編集・pytest 実行はしていません。

以下の行番号は現物に合わせています。略記は次のファイルを指します。

| 略記 | ファイル |
|---|---|
| G | [condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-bc/orchestrator/campaign/condition_meaning_gate.py) |
| T | [test_condition_meaning_gate.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-bc/orchestrator/tests/test_condition_meaning_gate.py) |
| C | [s8a_trigger_coverage.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-bc/orchestrator/campaign/s8a_trigger_coverage.py) |
| S | [test_s8a_trigger_sweep.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-bc/orchestrator/tests/test_s8a_trigger_sweep.py) |

**brief の集合件数は現物と一致しません。** G:254–310 の枝選択登録簿は 18 件、G:314 の BACKOFF_FIXED を含む対応集合は 19 件です。MOCC_TEMP_PREDICATE と MOCC_HOT_UPDATE_UNLOCK も既存です。したがって本案の完了件数は **枝選択 18→21、対応集合 19→22**。I1 は brief にいう既存 17 件だけでなく、現物の既存全件へ適用します。

## 現行挙動

| 面 | 現物と問題 |
|---|---|
| 定義要求 | G:947–979 は `default=None` を許す。G:1005–1013 により MISATTR の `1/None` は inert ではない |
| factory | G:982–1002 は NOINLINE の特例以外を `1/0` に限定。MISATTR は登録するだけでは届かない |
| configure | G:1699–1708 は `None` なら対象の `-D` を足さず、CXX_FLAGS 自体は明示的に設定する |
| supply | G:2596 は default をそのまま control に使う。G:2261–2271 は値がある場合だけ検査し、非 stock の未定義対照に対象 macro が混入していてもここでは拒否しない |
| meaning | G:3177 は `default is None` を拒否。G:3310–3311 は `(int(value),1)` 固定 |
| 計装 | G:2958–2983 は逐語完全一致が一箇所の場合だけ計装する |
| 再検証 | G:3839 は完了数 1、G:3988–4012 は原則 `1/0` 固定。さらに G:4014–4028 は双方の `-D` を placeholder に置き換えるため、片腕に `-D` が無い比較には対応しない |
| 登録の副作用 | G:1907–1916 は登録済み CXX_FLAGS macro に共有 build root を使う。MISATTR と RUNG1 の追加は meaning だけでなく supply の configure 形も変える |

E 節の MISATTR `1/0` supply red、`1/None` supply green はこの実装と整合します。ただし E は親が取得した実測であり、本段で再実走した結果ではありません。

## 最小変更：未定義対照

1. **登録 directive を対照形の正本にする。**  
   G:254–310 に MISATTR の `("cc/silo/transaction.cc", "#ifdef IZANAGI_BREAK_TRIGGER_MISATTR")` を追加。G:990–997 では登録 directive が `#ifdef ` で始まる場合に限り、要求 `"1"`・既定 `None`・所有 path 一致を要求します。既存 `#if` の `1/0` と NOINLINE 特例は維持します。

2. **meaning の None 拒否だけを外す。**  
   G:3173–3180 の factory との完全一致検査を残し、末尾の一律 `default is None` 拒否を削除します。G:3186 の comparison は既存のままで MISATTR では `None` になります。NOINLINE の要求 0→対照 1 は変えません。

3. **値と選択期待を分ける。**  
   G:513、G:3101、G:3830 の型を `str | None` にする。G:3310–3311 は `None` の選択期待を 0 とし、定義済み腕は従来どおり数値化します。`None` を文字列 `"0"` や `"None"` へ変換しません。

4. **argv の不在検査。**  
   G:3115 の `observed_defines.get(macro) != define_value` は、そのまま未定義検査に使えます。G:2055–2075 の辞書値は常に文字列であり、`-DM` は `"1"`、`-DM=` は `""`。`None` を返すのは名前が無い場合だけです。  
   supply は G:2271 の直後に、`expected_value is None and not stock_identity` なら `macro not in observed_defines` を要求する分岐を追加。違反は既存語彙 `supply-value-mismatch`、expected は `None` とします。stock 対照を巻き込みません。

5. **実行時 comparable は変更不要。**  
   G:2121–2129 は allowed macro の `-D` を実行 argv に残し、comparable から除外します。要求側だけに `-D` がある場合も比較対象は自然に一致します。meaning の allowed は対象 macro 一つだけのままです（G:3130）。

6. **green record 再検証を追随。**  
   G:3988–4012 で登録 directive から default `None` と選択期待 0 を導出。G:3847 の `.get()` による不在検査は維持します。  
   **G:4014–4028 は追加修正が必須**です。`#ifdef` 経路だけ、対象 define の引数を両 argv から除去して比較します。`-DM=1` と `-D`, `M=1` の両形を扱い、他の引数は除去しません。既存 `#if` 経路の placeholder 比較はそのまま残します。

G:3614 の supply green 再検証には要求値・既定値そのものがなく、request digest しかありません。ここで macro 名だけから supply 全般に `1/None` を強制する拡張は避けます。今回の不在契約は supply 発行時と meaning observation 再検証で検査し、既存 supply schema を維持します。

CLI は G:4193 ですでに `--default-value` 省略が可能です。新しい CLI オプションは不要です。

## 最小変更：全箇所観測と宣言形

**P1 の別 mapping を採用します。ただし新しい dataclass／receipt field は設けない案が最小です。**

| 案 | 評価 |
|---|---|
| 既存 2-tuple を 3-tuple 化 | consumer の unpack・tuple pin を壊すため不採用 |
| 別 mapping、既定 1 | 採用。既存 tuple・宣言コンストラクタ・JSON schema を維持できる |
| 複数 path を持つ新宣言型 | REQUESTED_US には適するが、今回の 3 件には不要 |

G:310 付近へ `_CONDITIONAL_BRANCH_SITE_COUNTS` を追加し、RUNG1=2、TRIGGER_GATING=12 のみ宣言します。未掲載は 1。件数を取得する小さい helper を計装・評価・再検証で共用します。登録外キーや非正整数は test で拒否し、独立した期待表で件数を pin します。

G:662–681 の宣言は既存のままでも、macro と registry の束縛を介して N を一意に決められます。**新 field に default を付けるだけでは I1 を守れません。** G:789–795 は dataclass field を既定でも出力します。今回は field 自体を増やさず、既存の `selected_count`・`completed_count` と registry から N を再検証します。receipt に同じ N を重複保存する必要はありません。

G:2952–2984 の変更は次に限定します。

- 改行だけを除いた逐語一致をすべて集める。
- 件数が N と違えば拒否。N=1 の reason・detail は現行の `compile-time-branch-start-not-unique` を完全維持。
- N>1 の不一致は新規 `compile-time-branch-site-count-mismatch` とし、expected=N、observed=実測件数。
- marker 衝突検査を保つ。
- 全 index に、現行と同じ `directive / SELECTED / #endif / COMPLETED / directive` を挿入する。元の `#endif` を解析・探索しない。

G:3310–3329 は要求 `(N·v,N)`、対照 `(N·v,N)` を厳密比較します。MISATTR の未定義対照だけ v=0 と解釈します。G:3824 の validator に `completed_count=1` の既定引数を足し、G:4004–4012 から N を渡す形なら既存呼出しも保てます。

実 patch の独立アンカーは以下です。

| macro | 逐語箇所 |
|---|---|
| MISATTR | `patches/broken-silo-trigger-misattr.patch:9`、一箇所 |
| RUNG1 | `patches/silo_ladder_rung1.patch:9,31`、同じ transaction.cc に二箇所 |
| TRIGGER_GATING | `patches/silo-backoff-trigger-gating-variant.patch:41,79,101,107,119,133,143,153,163,173,183,193`、十二箇所 |

TRIGGER_GATING の `#ifndef` 番兵（同 patch:38）と診断用複合条件（`patches/instr-silo-backoff-trigger-gating-tally.patch:9`）は対象逐語ではありません。主張は **skeleton の十二箇所の枝選択**までです。診断 tally の複合枝まで観測したとは書きません。

## REQUESTED_US：今回は未登録を推奨

現物は `patches/silo-backoff-requested-us.patch:29,41` が header、`:60,178` が transaction.cc です。TU の二箇所だけ登録するのは部分観測です。

全四箇所を採る場合には、少なくとも以下が必要です。

| 面 | 必要な拡張 |
|---|---|
| 宣言 | 一つの macro に `(transaction.cc, directive,2)` と `(include/backoff.hh,directive,2)` を束縛する別 site-group mapping |
| capture | G:3182 の単一 capture を二 file にし、G:2892 の no-follow capture を両方へ適用 |
| shadow | G:2998 の owner 直接経路を使わず、G:3023 の全木 shadow を一度だけ構築。二 file とも symlink 対象から除外して計装本文を書く |
| 観測 | 二つの shadow を別々に観測せず、同じ shadow の owner TU 一回の前処理で合計 `(4,4)/(0,4)` を要求 |
| 証拠 | 両 source の digest・capture identity・宣言箇所数を保存し、G:3976 の単一 source 束縛を拡張 |
| test | header 未到達、二 file の片側欠落、重複観測、capture 差替えを検査 |

現行 G:2987 は単一 instrumented source を受け取り、shadow directory を新規作成します。二回呼べば済む形ではありません。owner 直接経路では include 先 directory が元木への symlink になり、header 計装を同時に載せられません。

header は `external/ccbench/include/backoff.hh:1` に `#pragma once`、`external/ccbench/cc/silo/include/transaction.hh:9` に include があります。これは複数 include に対する一回展開の根拠ですが、**実際に一回到達した証明は計装後の completed 数で取る**必要があります。採用するなら二重 include fixture と実 TU の双方で確認します。

複数 file の capture・shadow・証拠 schema まで変更する費用に対し、公開 requested-us driver は現状 admission を保存しません。P4 の許容する未登録案を推奨します。`DEFINE_SPECS.owner_tus` は変更しません。

## 配線の採否と所有 path

C:113 を `None if macro == MISATTR_DEFINE else 0`、C:119 を factory 呼出しへ変更します。TRIGGER_GATING の default は 0 のままです。

C:194–195 の実 build は MISATTR=1 を CXX_FLAGS で供給します。C:214–221 の gate 呼出しはその CXX_FLAGS 引数を取り除き、gate 自身に要求／対照を構築させています。この形は維持します。

| driver | admission の流れ | 採否 |
|---|---|---|
| `s8a_trigger_coverage` | C:130–134 で返却、C:150/160 で収集、C:347 に格納、C:424 で JSON 保存 | 配線する |
| `s8a_trigger_freq` | `:64` で coverage helper を再利用、`:134`→`:148`→`:204` で保存 | 編集不要で追随。回帰対象 |
| `silo_ladder_rung1` | `:2174` が RUNG1 `1/0`、`:2232` は factory 既配線。`:4139`・`:4635` に condition records を格納 | driver 編集不要 |
| `s8a_trigger_sweep` | `:340–344` は返却するが `:408` が捨てる。`:614–623` の provenance JSON にも載らない | 配線しない |
| `backoff_sweep` | `:228` は records/admission を返すが `:452–467` が捨てる。この caller の要求は FIXED のみ | 非 FIXED の `:209` は変更しない |
| `backoff_requested_us` | `:133–141` は helper の返り値を返すが `:1107–1111` が捨てる。FIXED 側も `:1089` で捨てる | 配線しない |

**condition admission と build admission は別物です。** C:247–248 の `build_admissions` は build receipt であり、C:207/214 の condition helper の返り値を保存しているわけではありません。condition 証拠が残る根拠は preflight の `condition_gates` です。

author の推奨所有 path は次の **5 file** です。

- `orchestrator/campaign/condition_meaning_gate.py`
- `orchestrator/campaign/s8a_trigger_coverage.py`
- `orchestrator/tests/test_condition_meaning_gate.py`
- `orchestrator/tests/test_s8a_trigger_sweep.py`
- `orchestrator/tests/test_silo_ladder_rung1_driver.py`

最後の一件は必須追加です。同 test の **:105 が `rung_declaration is None` を要求**しており、登録すると壊れます。型・macro・directive が正しい宣言を要求する assertion に更新します。brief の「test 2 file」では不足します。

## 不変条件と I1 の検証

- **D1491:** G:649–651、G:3428–3430、G:3884–3886、G:3903–3905、G:4217–4225 の BACKOFF_FIXED 固定を維持。T:1751 と T:2826 の旧宣言拒否を残す。
- **DEFINE_SPECS:** G:73–252 を変更しない。route・owner・target・inert・companion を保持する。
- **既存 `#if` 経路:** default 0、NOINLINE の対照反転、argv 再検証、N=1 の reason/detail/期待文字列を維持する。
- **新規 mapping:** 既存 macro の N はすべて 1。既存 tuple と順序も保持する。
- **companion を足さない:** G:919 は spec companion を補完し、G:1704–1707 は CXX_FLAGS route の companion を裸の `-D` として注入する。一方 gating patch:26 は CMake 側から同 macro を供給するため、MISATTR の companion にすると G:2069–2072 の二重 define 拒否に当たる。外側条件は C:146 の genome configure で供給する。

I1 の検査は二層に分けます。

1. **同一入力での canonical bytes・判定互換。**  
   実 submodule の既存 macro と既存 fixture から、変更前の実 compiler 観測・file identity・argv を取得する。その同じ観測入力を旧版／新版へ再生し、green/red の完全な canonical JSON、record digest、再検証結果を比較する。新規 field が既定値でも増えていないことも確認する。
2. **独立した実走の意味互換。**  
   同じ patch・configure・compiler で旧版／新版を実走し、前処理 bytes/digest、counts、reason を比較する。新規 MISATTR/RUNG1 は共有 build root 化の前後も比較する。

**独立二走の canonical JSON 全 bytes 一致を、そのまま必須にするのは不適切です。** G:3240 の一時 path、G:2943 の file identity 等が証拠に入ります。I1 の完全 bytes 比較は「同じ捕捉入力」で行い、実走比較で path 等を正規化した結果は完全 bytes 一致と呼ばないよう区別します。再生は互換 test 用であり production 認証には使いません。

規律 2 についても、**同じ要求に対する gate の弱体化禁止**と、MISATTR driver の要求を `1/0` から `1/None` に訂正することを分けます。後者まで含めて無条件に「従来受理集合の部分集合」とは主張しません。

## 具体的な正負例と既存 pin の波及

T:224 の fixture builder は新規 macro に限って独立期待表の N 個の枝を生成し、両腕に無条件の本文を残します。既定腕が空になって supply が先に落ちる F29 型を避けます。既存 fixture の本文は変更しません。

T:210 の request helper は、MISATTR 正例の呼出し側で `default=None` を明示するのが最小です。明示された `default=0` を helper が勝手に補正してはいけません。

| 正負例 | 検査すること |
|---|---|
| MISATTR `1/None`、外側条件有効 | supply green、meaning `(1,1)/(0,1)`、admitted、未確立なし |
| MISATTR `1/0` | factory は None。実 `#ifdef` fixture の supply は同一出力で red |
| 未定義対照に `-DM=0`／`-DM`／`-D`, `M=0` 混入 | supply 発行時の不在検査で red |
| RUNG1 二箇所、GATING 十二箇所 | `(N,N)/(0,N)`。既定腕でも全 completion を観測 |
| 一箇所を逐語等価な `#if (M)` に変更 | macro の意味は同じでも宣言箇所数不足で red |
| 一箇所を外側 `#if 0` に入れる | 静的件数 N は満たすが completed<N で red |
| 二箇所間で default 時だけ macro を再定義 | requested と default は異なっていても default 選択数が非ゼロなら red |
| owner prefix `#undef` | 既存 T:1581 と同様に非識別として red |
| 無関係 comment／枝本文のみ変更 | counts と判定は不変。source digest を含む record bytes は変わり得る |

既存 pin の更新・維持箇所は以下です。

- T:33 の列挙に三件追加。T:2814 の集合 pin は自動追随するが、独立件数・N pin も設ける。
- T:266–287 は MISATTR の `#ifdef` と新規 N を test 側で独立宣言。registry 自身から期待 N を作らない。
- T:993–1009 は fixture directive 列を N 個要求する。
- T:1316 の全 registry 正例は :1339–1342 の 1 固定と :1343–1351 の双方 `-D` 前提を更新する。
- T:1689 の未登録例は `SS2PL_LOCK_IMPL` 等、今回登録しない macro へ変更する。MISATTR を default 0 のまま残すと、未登録 test が非対値 test に化ける。
- T:1714 の既存非対値 test、T:1562 の N=1 重複拒否、T:1776 の schema 変異 test は維持。
- `test_mocc_mutation_proof.py:177`、`test_mocc_template_proof.py:267`、`test_mocc_proof_surface.py:569` は 2-tuple 維持により編集不要。
- S:91–94 は preflight の実行順しか検査しない。factory/default の配線検出には新 test が必要。
- `s1_expected_goldens.py:256,318,373` は backoff_sweep path を含む。今回はその driver を編集しないので、このための pin 更新を生じさせない。歴史記録の hash を現行値へ書き換えない。

## 変異候補と落ちる test node の予測

以下の新規 node 名は **author が実装する提案名**です。まだ存在・実走した test ではありません。T/S の略記は上記ファイルです。表は原因を切り分ける焦点 node を示し、全 suite の失敗集合一致を保証するものではありません。

| 変異 | 予測する焦点 node | 帰属 |
|---|---|---|
| coverage の MISATTR default を 0 に戻す | `S::test_coverage_condition_gate_passes_exact_factory_pair[misattr]` | 実 request の default と実 factory 宣言を観測する assertion |
| RUNG1 の宣言 N を 2→1 | `T::test_multisite_branch_selection_accepts_all_sites[rung1]` | 独立二箇所 fixture に対して `start-not-unique`。green 期待が落ちる |
| GATING の宣言 N を 12→11 | `T::test_multisite_branch_selection_accepts_all_sites[gating]` | `site-count-mismatch`。fixture を registry N から生成しないことが前提 |
| 正例 fixture 一箇所だけ `#if (M)` に変える | 同上の対応 parameter | 逐語件数不足。追加の `test_multisite_rejects_changed_directive` は、この red 自体を正常期待する負例 |
| 評価側の default 期待を観測値に合わせて緩める | `T::test_multisite_assert_rejects_default_partial_selection` | `_assert_compile_time_branch_selection` を直接呼び、`(2,2)/(1,2)` の拒否を要求 |
| schema 側の default 選択数検査を緩める | `T::test_multisite_green_schema_rejects_partial_default` | 正規 green 証拠の default count だけを変え、digest を再計算した公開 record の拒否 |
| G:2271 に追加する未定義検査を外す | `T::test_undefined_control_rejects_supplied_zero_in_supply` | control にだけ `-DM=0` を注入。数値値差も持つ fixture で supply 差分を保ち、不在検査単独を検出 |
| coverage の factory を None に戻す | `S::test_coverage_condition_gate_passes_exact_factory_pair[misattr]`、同 `[gating]` | evaluator に渡された宣言の型・内容 |
| MISATTR registry entry 削除 | `T::test_ifdef_factory_accepts_only_one_vs_undefined` | registry lookup に依存しない request から factory 宣言が消える |
| RUNG1 registry entry 削除 | `test_silo_ladder_rung1_driver.py::test_condition_gates_pass_real_factory_declarations_to_evaluator` | 更新後の RUNG1 宣言 assertion |
| 任意の新 entry 削除 | `T::test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches` | 集合 pin。意味観測による検出とは区別 |

default 期待の緩和は、family test だけでは発行時 validator が重ねて拒否して生き残り得ます。したがって評価層と再検証層の node を分離します。同様に未定義検査削除は meaning に拒否させず、supply 単独で検出します。

負の変異は registry 周辺の無関係 comment と、directive を保った枝本文変更です。前者は全証拠不変、後者は枝選択 counts・判定不変を期待します。本文変更後の source digest まで不変とは期待しません。

段 4 では置換 seam と選択 node を確定し、baseline の収集結果を得てから期待失敗集合を登録します。KeyError・fixture 不成立・宣言消失・意味観測拒否を一括して「witness が検出」と報告しません。

## 段 6 レビュー観点

1. **未定義対照:** configure、実 compile argv、observation、green record 再検証の全段で `None` が不在として扱われるか。特に G:4014 の argv 比較漏れを確認する。
2. **全箇所性:** 静的件数 N と両腕の completion=N の両方を要求するか。最初の一箇所だけの計装、外側条件による未観測を許さないか。
3. **I1:** 既存全件の tuple、N=1 の red 語彙、schema、同一入力 canonical bytes が保たれるか。新 field の default が勝手に出力されていないか。
4. **過剰決定:** 変異が意図した一つの seam で落ちるか。別 validator や supply の空出力で落ちていないか。
5. **実 TU:** MISATTR の外側 gating/no-wait、GATING の BACK_OFF/no-wait を official 同形 configure で有効にして全 completion を得るか。fixture の緑だけで登録を完了しない。
6. **共有 build root:** 新規 CXX_FLAGS 二件の登録前後 supply を比較し、cache 由来の差を meaning の改善と混同しない。
7. **成果物:** coverage/frequency の condition JSON と rung1 の成果物で未確立一覧が実際に縮むか。build receipt だけを根拠にしない。
8. **主張範囲:** 動的到達性、誤帰属発火、枝本文の正しさ、診断 tally 全体の意味まで主張しない。

author 後は焦点 test と上記 consumer 回帰を実行し、最終 production registry で login／計算ノードの official 同形 cell を取得する必要があります。本段はその実測を代替しません。

## 親 brief への反論

- **件数と既存集合が古い:** 17→20 ではなく、現物では対応集合 19→22。I1 の対象も現物全件へ広げる。
- **P1 の新 field は不要:** N は registry から導出でき、既存 count field で証拠を表現できる。default field を足すだけでは canonical bytes が変わる。
- **P2 は argv 再検証の修正を追加すべき:** 実観測の `.get()` は None に対応できるが、green schema の placeholder 比較はできない。
- **P4 は未登録を推奨:** 二 file の同時 shadow は既存 header 経路の単純な二回利用では済まない。部分登録はしない。
- **test 2 file では不足:** rung1 driver test:105 の None pin 更新が必須。
- **I5 の「MISATTR 対照を 0 に戻す→not-discriminating」は変異位置次第:** driver request を戻せば factory は未宣言になり、supply の同一出力で落ちる。意味観測の reason を期待する変異と区別する。
- **「枝本文変更で witness 不変」は判定に限定:** source digest を保存しているため record bytes まで不変ではない。
- **規律 2 の説明を限定すべき:** 誤った対照要求の訂正と gate の判定緩和は別。共有 build root 化も含め、無条件の受理集合包含を実証済みとは書かない。

## 総括

三件登録、別 N mapping、既存 schema 維持、coverage helper の最小配線を推奨します。REQUESTED_US は四箇所を同時観測できる変更単位へ残します。実装所有は 5 file。静的計画のみ完了しており、編集・pytest・実 TU 再実測は未実施です。