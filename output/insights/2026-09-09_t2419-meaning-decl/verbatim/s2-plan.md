## 前提の確認

必読の親 brief、`backoff_sweep.py`、`condition_meaning_gate.py`、`backoff_extended_sweep.py`、実 patch、両 test file を確認した。補助資料として 6 driver、`b10_backoff_shape_sweep.py`、関連 test、`acceptance_duration_ledger.json` の該当箇所も確認した。pytest は実走していない。

親 brief の主要なコード認識に誤りはない。ただし次の補足が要る。

- helper consumer は 6 module で正しい。直接の helper 呼び出し式は 7 個あり、そのうち `BACKOFF_FIXED` を渡す面が 6 個、`backoff_requested_us.py:126-139` の `BACKOFF_REQUESTED_US` 専用面が 1 個である。
- 現行に生値 1000〜2999 を使う driver は存在する。`b10_backoff_shape_sweep.py:100-103,782-817` が `symmetric-modulo` を 1002、1005、1010、1025、1050、1100 に符号化する。ただし同 file を grep した結果 `_require_backoff_condition_gate` の呼び出しはなく、今回の static helper consumer ではない。
- 「新 test file でなければ台帳不要」という結論は妥当だが、理由は file 単位ではない。台帳は `acceptance_duration_ledger.json:2` の nodeid 単位であり、既存 file の nodeid も `:256-257,3392-3398` に登録されている。一方、受入側は `:15` が示す 90% coverage 契約なので、未計測の新規 2 nodeid を推測値で追加する必要はない。
- `backoff_extended_sweep_report.py` と `test_screening_driver.py` は射影対象外なので直接読んでいない。前者の consumer 存在、後者の別経路という判断は親 brief に基づく。freeze hash の記述も射影外成果物では再検証していない。

## 決定

1. P1 は親の provisional 案に同意し、production 宣言値を静的 codec から導く。

   - 選択案では `backoff_sweep.py:55-60` 付近へ bounded static codec を移し、`backoff_sweep.py:107-155` が `decode_static_backoff_us(raw)` と `canonical_float64_bits(float(physical_us))` から宣言を作る。6 個の `BACKOFF_FIXED` 呼び出し面は変更しない。
   - driver 明示案では `_require_backoff_condition_gate` の引数へ `raw -> physical_us` 宣言を追加し、次の 6 面を変更する必要がある。

     - `backoff_sweep.py:378-392`
     - `backoff_extended_sweep.py:527-544`
     - `backoff_profile.py:344-361`
     - `backoff_requested_us.py:110-123`
     - `backoff_repro.py:63-83`
     - `backoff_overthrottle.py:61-78`

     extended と overthrottle は encoded `Genome` しか保持しないため、真に明示化するなら `backoff_extended_sweep.py:432-524,1402` などから物理値を追加で運ぶ必要もある。codec をその場で呼ぶだけなら選択案と同じで、呼び出し面だけ増える。
   - 恒真化にはならない。期待値は Python の static codec、観測値は `condition_meaning_gate.py:1154-1243` が捕捉した `include/backoff.hh` から `:4235-4246` が hole を抽出し、`:1387-1415` の TU を `:4267-4289` で実 C++ compiler に通した結果である。実式は `silo-backoff-fixed.patch:69-73` にあり、Python decoder は compiler 側から呼ばれない。source 式だけが変われば `:4291-4304` で赤になる。

2. P1 の生値 1000〜2999 は static helper では拒否する。

   - `unestablished` 据え置きは F718 型を残すため不可。
   - 乱択意味の宣言は、static driver の単一物理値契約ではなく `start` 依存の別契約になるため今回の scope 外。
   - 6 個の static helper consumer を grep・読解した範囲では、この帯を helper へ渡す現行実走経路はない。extended は `backoff_extended_sweep.py:64-79,432-488` の codec を使い、物理 1000 は生値 3000になる。profile は `backoff_profile.py:74,330-361` の -1、2〜100、repro は `backoff_repro.py:50-55,87-94` の -1、5、10、requested-us の実 gate は `backoff_requested_us.py:1052-1092` で -1 のみである。
   - B10 の乱択生値は存在するが、独自 shape driver であり今回の helper 拒否の影響を受けない。

3. P2 は codec 全体を `backoff_sweep.py` へ移す。

   - `backoff_extended_sweep.py:37-41` の既存 `from .backoff_sweep import ...` に `STATIC_BACKOFF_MAX_US`、`STATIC_BACKOFF_RAW_MAX`、`encode_static_backoff_us`、`decode_static_backoff_us` を追加する。
   - `backoff_extended_sweep.py:60-79` のローカル定義を除く。
   - import された名前は同 module の属性として残るため、`backoff_overthrottle.py:24-35` と親 brief が示す `backoff_extended_sweep_report.py` の既存 import を変更しない。循環 import も生じない。

4. P3 は両文脈で同じ bits とする。

   - `condition_meaning_gate.canonical_float64_bits(float(decode_static_backoff_us(raw)))` で 1 個の bits を作り、`CONTEXT_STARTS` の 2 要素へ複製する。
   - 生値 3000 の宣言は `("408f400000000000", "408f400000000000")`。
   - `CONTEXT_STARTS = (1, 2)` は `condition_meaning_gate.py:301`。静的域の patch 式は生値 0〜999 なら生値そのもの、生値 3000〜11999 なら生値 minus 2000 であり、`start` を参照する q==1、q==2 の枝を通らない。
   - 負例の宣言 bits も上記 2 個だが、実観測は 0.0 の `0000000000000000` になる。

5. 正例・負例は `test_backoff_sweep.py:145-194` の近傍へ追加する。

   - 正例は production helper を生値 3000 で実行し、meaning が `green/declared-meaning-observed`、2 観測がともに 1000.0、`unestablished_meaning_macros == ()` であることを確認する。
   - 負例は production helper が生値 1000 を static wire domain 外として拒否することに加え、手製の `MeaningWitnessDeclaration` で 1000.0 を宣言し、実体の `capture_define_inputs`、`make_define_request`、`evaluate_define_runtime_meaning`、実 C++ compiler を通して `red/decoded-meaning-mismatch` を確認する。compiler/evaluator/source capture は stub しない。
   - fixture は既存 `fixtures/condition_meaning_gate/supplied` を使う。`test_condition_meaning_gate.py:2394-2405` がその conditional を実 patch target に固定しているため、別途 external tree へ patch を materialize する必要はない。

6. 既存 assertion の変更は `test_backoff_sweep.py:166` の 1 箇所である。生値 5 の meaning を `unestablished` ではなく `green/declared-meaning-observed` と期待させる。

   - `test_backoff_extended_sweep.py:919-933` の実 wrapper は挙動上 green へ変わるが、現在は meaning status を assert していない。
   - `test_screening_driver.py:200` の `("BACKOFF_FIXED", "unestablished")` は別経路なので変更しない。backoff sweep の事前 family gate が green になることとは独立である。
   - `test_condition_meaning_gate.py` の明示宣言テストは evaluator 自体の契約であり変更不要。

7. 新規 test file は作らず、受入台帳も変更しない。新 nodeid の実時間が未計測であり、台帳へ推測値を入れない。

## 変更プラン

- `orchestrator/campaign/backoff_sweep.py:55-60`
  - 変更前: static codec は extended module にだけ存在する。
  - 変更後: bounded static codec と上限定数をここで定義し、production helper と extended の双方が同じ wire-domain 定義を使う。

- `orchestrator/campaign/backoff_sweep.py:107-155`
  - 変更前: `BACKOFF_FIXED=-1` だけ宣言を作り、全非負値は `declaration=None`。
  - 変更後: request と declaration を同時に構築し、-1 は既存 branch case、0〜999・3000〜11999 は static pointwise case、1000〜2999・12000 以上は supply compile 前に明示的な `RuntimeError` とする。他 macro と -2 以下の挙動は変えない。

- `orchestrator/campaign/backoff_extended_sweep.py:37-41,60-79`
  - 変更前: codec をローカル所有し、backoff_sweep は逆 import できない。
  - 変更後: backoff_sweep から import・再輸出し、既存 API と consumer import を保ったまま循環を避ける。

- `orchestrator/tests/test_backoff_sweep.py:145-166`
  - 変更前: 生値 5 の meaning を `unestablished` と期待する。
  - 変更後: `green/declared-meaning-observed`、一致する 2 観測、空の unestablished 集合を期待する。

- `orchestrator/tests/test_backoff_sweep.py:169-194` 近傍
  - 変更前: production の非負 wiring と F718 型を直接覆うテストがない。
  - 変更後: 生値 3000 の production green と、生値 1000を1000.0と誤宣言した実 compiler red の 2 test を追加する。

- `condition_meaning_gate.py`、patch、台帳、screening driver、B10 shape driver、freeze 成果物は変更しない。

## テストプラン

新 nodeid 案:

- `orchestrator/tests/test_backoff_sweep.py::test_real_family_helper_declares_raw_3000_as_static_1000_and_observes_green`
- `orchestrator/tests/test_backoff_sweep.py::test_real_runtime_meaning_marks_raw_1000_declared_as_static_1000_red`

実走すべき回帰 nodeid:

- `orchestrator/tests/test_backoff_sweep.py::test_real_family_helper_admits_effective_define_and_recomputes_file_digest`
- `orchestrator/tests/test_backoff_sweep.py::test_real_family_helper_treats_minus_one_as_stock_identity`
- `orchestrator/tests/test_backoff_sweep.py::test_real_family_helper_rejects_ignored_define_before_any_driver_build`
- `orchestrator/tests/test_backoff_sweep.py::test_sweep_condition_gate_dominates_screened_and_direct_campaign_paths`
- `orchestrator/tests/test_backoff_extended_sweep.py::test_static_codec_is_bijective_on_its_exact_bounded_domain`
- `orchestrator/tests/test_backoff_extended_sweep.py::test_real_extended_driver_gate_recomputes_preprocessed_file_digest`
- `orchestrator/tests/test_backoff_extended_sweep.py::test_extended_gate_wrapper_forwards_configure_args`
- `orchestrator/tests/test_condition_meaning_gate.py::test_backoff_fixed_raw_3000_is_observed_as_static_1000`
- `orchestrator/tests/test_condition_meaning_gate.py::test_f718_1000_decodes_to_zero`
- `orchestrator/tests/test_condition_meaning_gate.py::test_generic_f718_is_supply_green_and_meaning_red`
- `orchestrator/tests/test_condition_meaning_gate.py::test_patch_target_decoder_and_fixture_holes_are_independently_anchored`
- `orchestrator/tests/test_condition_meaning_gate.py::test_established_meaning_uses_examined_empty_carryover_not_unset`
- `orchestrator/tests/test_condition_meaning_gate.py::test_promotion_rejects_red_runtime_meaning`
- `orchestrator/tests/test_backoff_consumers.py::test_backoff_repro_condition_gate_dominates_campaign_build_and_measurement`

## 受理集合の変化

supply arm が green で、現行 patch source を前提とする。

| `BACKOFF_FIXED` | 変更前 | 変更後 |
|---|---|---|
| `-1` | stock branch meaning green | green のまま |
| `-2` 以下 | unestablished、admitted | 今回の scope では不変 |
| `0..999` | unestablished、admitted | compiled observation 一致により green、admitted |
| `1000..2999` | unestablished、admitted | static helper が wire-domain 外として事前拒否 |
| `3000..11999` | unestablished、admitted | compiled observation 一致により green、admitted |
| `12000` 以上 | unestablished、admitted | bounded static domain 外として事前拒否 |
| valid static 値だが source 観測が不一致 | unestablished、admitted | meaning red、family 不受理、helper が `RuntimeError` |

生値 1000 は production では事前拒否されるため、通常の meaning record にはならない。負例では明示的な誤宣言を evaluator へ渡し、期待 `408f400000000000`、観測 `0000000000000000` の red を確認する。

## 裁定候補

`backoff_extended_sweep.py:99-101` の `T2418_MEANING_WITNESS_STATUS` は、`:647,1168,1275` で現在も `unestablished_for_positive_backoff_fixed_as_in_existing_sweep` を出力し、`test_backoff_extended_sweep.py:517-519,578-580,716-718` が固定している。

これは既存 T-2418 測定時点の歴史的 disclosure なら変更すべきでない。一方、新規 rerun の live gate 状態を表すなら変更後は不正確になる。campaign identity と report provenance に波及するため、本プランには混ぜず、歴史的固定値か live 状態かを別途裁定する。

## 総括

production 宣言は中央の bounded static codec から作り、実 C++ source の compile 観測と比較する。  
0〜999 と 3000〜11999 は green、乱択帯と上限外は事前拒否する。  
循環 import は codec を backoff_sweep へ移し、extended で再輸出して解消する。  
既存 assertion の変更は raw 5 の `unestablished` 1 箇所で、台帳と freeze は変更しない。