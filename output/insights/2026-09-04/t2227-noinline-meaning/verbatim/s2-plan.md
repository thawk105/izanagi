## 現行の経路と欠陥の再確認

- `orchestrator/campaign/condition_meaning_gate.py:180-210` の registry に `BACKOFF_NOINLINE` がなく、`MEANING_SUPPORTED_MACROS` にも入らない。

- factory は `orchestrator/campaign/condition_meaning_gate.py:873-888` で要求値 1、既定値 0、かつ `source_rel in spec.owner_tus` の場合だけ宣言する。このため次の両方を拒否する。

  - A-2 の要求値 0、既定値 0。
  - `include/backoff.hh` 所有の witness。DefineSpec の owner TU は `cc/silo/transaction.cc` だからである。

- source capture と計装自体は任意の registry source に使える。`_capture_compile_time_branch_source` は `orchestrator/campaign/condition_meaning_gate.py:2621-2678`、指令への marker 挿入は `:2681-2713` にある。欠陥は、その後の shadow と compile input の選び方にある。

- 現行 `_write_shadow_owner_source` `:2716-2749` は対象 file の祖先だけを実 directory にし、兄弟 directory を symlink にする。header を対象にすると shadow の `cc` が directory symlink になり、owner TU の相対 include が実木へ戻る。

- `_replace_owner_compile_input` `:2752-2784` は compile operand を `instrumented_owner`、実際には計装した `source_rel` へ置換する。header witness では compile operand に header を置くことになり、D1490 の「所有 TU 全体」にもならない。

- `_preprocess_argv` はすでに `-MD -MF` を付ける `:1939-1992` が、`_compile_time_observation` `:2787-2850` は依存 file を読まない。計装 header が本当に owner TU の依存閉包へ入ったかを確かめていない。

- `_assert_compile_time_branch_selection` `:2857-3035` と green record validator `:3566-3655` は、名前だけでなく期待値も requested=1、default=0 に固定されている。要求 0、対照 1 は現行のままでは green record を自己検証できない。

- owner entry の解決は `_select_owner_entry` `:1654-1684` が実 source root と実 compile database に対して先に行う。shadow はその後だけに使うので、この関数を変える必要はない。

- A-2 は `paper_story_a2_certification.py:630-654` で `BACKOFF_FIXED` 以外を `declaration=None` のまま渡す。s1 も `s1_direct_comparison.py:229-246,280-292` の legacy helper が `BACKOFF_FIXED` 以外を常に None にする。

- fixture header `orchestrator/tests/fixtures/condition_meaning_gate/supplied/include/backoff.hh:1-7` に noinline 指令がなく、実 patch の `patches/silo-backoff-fixed.patch:52-58` と不一致である。

## P1〜P6 の採否と根拠

- (P1) 採る。ただし既存 8 macro の経路を条件分岐で逐語的に残す。

  header witness の場合だけ全 directory を実体化し、通常 file を symlink にする深い鏡像を使う。compile operand は計装 header ではなく `instrumented_root / request.owner_tu` へ差し替える。依存 file に計装 header がなければ red にする。既存 8 macro は `source_rel == owner_tu` の現行 shadow 分岐を維持し、追加の依存検査も通さない。これが挙動と evidence bytes を変えない最も狭い実装である。

- (P2) 変える。

  inert 宣言を registry 全体へ一般化すると、`test_condition_meaning_gate.py:1096-1109` が固定している既存 macro の要求 0、既定値 0 の挙動を変える。factory の拡張は `BACKOFF_NOINLINE` に限り、`default == "0"` かつ `requested in {"0", "1"}` の場合だけ行う。既存 8 macro は要求 1、既定値 0 のままにする。要求 0、既定値 1 のような patch の既定値と逆の申告も受理しない。

  field は追加しない。`CompileTimeBranchSelectionObservation.define_value` `condition_meaning_gate.py:405-411` が値を保持するので、`requested` slot に実要求 0、互換名である `default` slot に対照 1 を格納できる。`default_configure_argv` も対照側 argv と定義する。既存 8 macro では対照値が実際の default 0 と一致するため canonical evidence は従来と同じになる。

- (P3) A-2 と s1 の配線は採る。

  A-2 は対象を要求し、`paper` admission を receipt に載せる `paper_story_a2_certification.py:613-690` ので必須。s1 も対象を要求し、`floor` または `certified-selection` の admission に入るため D1492 の条件を満たす。

  raw-only を配線しないという結論は維持するが、「raw だから」だけを根拠にはしない。D1492 の第二条件である、promotion 成果物へ admission が載らないことを理由として driver ごとに記録する。raw admission 自体も D1492 の「成果物」に含める解釈なら、これらも配線対象になるため、親の段 4 で境界を明記する必要がある。

- (P4) 変更する。

  `output/` 内の既受理成果物への影響が空集合であることは `brief.md:29-36` の実測どおり採る。一方、repo 外の Pegasus attempt root や durable base は未走査なので、「全保存先で空集合」とは書かない。現時点では migration なし、repo 内の訂正なしとする。

- (P5) 採る。

  fixture header の現行 1 行目より前へ、patch `:55-57` と同じ 3 行を置く。これは EVOLVE block の外なので、`test_condition_meaning_gate.py:1924-1935` の block 抽出と conditional/hole 比較は変わらない。

- (P6) 採る。

  supply arm、D1523 の inert 比較、`RELATED_DEFINE_DECODE_MACROS` `condition_meaning_gate.py:212-216`、CLI、`MeaningWitnessDeclaration` `:533-549` は変更しない。特に legacy 宣言の `macro != MACRO` 拒否を維持する。

## 変更 plan (file:line)

- `orchestrator/campaign/condition_meaning_gate.py:180-205`

  `_CONDITIONAL_BRANCH_WITNESSES` に次を追加する。

  ```python
  "BACKOFF_NOINLINE": (
      "include/backoff.hh", "#if BACKOFF_NOINLINE",
  ),
  ```

  `MEANING_SUPPORTED_MACROS` は `:209-211` の導出をそのまま使う。直接編集しない。

- `orchestrator/campaign/condition_meaning_gate.py:873-888`

  factory を macro 別に分ける。

  - 既存 8 macro: 現行どおり requested=1、default=0、source が owner TU。
  - `BACKOFF_NOINLINE`: requested は 0 または 1、default は必ず 0、registry tuple は header の確定値と完全一致。
  - header 所有の許可は `BACKOFF_NOINLINE` の確定 tuple だけに閉じる。単に `source_rel not in owner_tus` の拒否を全 macro から外さない。

- `orchestrator/campaign/condition_meaning_gate.py:2716-2749`

  `_write_shadow_owner_source` に owner TU の相対 path を渡す。

  - `source_rel == owner_tu` なら現行アルゴリズムを残す。
  - header 所有なら `.git` を除く source tree の directory を shadow 側に実 directory として作り、file を symlink にする。計装対象 header だけは symlink を作らず、計装 bytes を通常 file として書く。
  - 戻り値は少なくとも計装 source path と shadow owner path を区別できる形にする。

- `orchestrator/campaign/condition_meaning_gate.py:2752-2784`

  `_replace_owner_compile_input` の差し替え先を shadow owner TU にする。`BACKOFF_NOINLINE` なら `instrumented_root/cc/silo/transaction.cc` であり、`instrumented_root/include/backoff.hh` ではない。

  `-ffile-prefix-map={instrumented_root}={source_root}` `:2779-2782` は維持する。これにより shadow 経由の `__FILE__` と `__BASE_FILE__` が一時 directory に依存しない。既存 8 macro では差し替え path と argv が従来と同じになる。

- `orchestrator/campaign/condition_meaning_gate.py:2787-2850`

  header 所有時だけ、preprocess 成功直後に dependency file を読む。既存 parser `:1995-2017` を使い、各 path を compile cwd 基準で解決して、計装 header の実 path が 1 件含まれることを要求する。

  - dependency file が読めない、解析できない場合は既存 `dependency-closure-invalid`。
  - 解析できるが計装 header がない場合は新しい局所 reason code `compile-time-branch-instrumented-source-unobserved`。
  - この検査結果は evidence field に追加しない。header witness の発行可否を fail-closed にするだけで、既存 schema と bytes を変えない。

- `orchestrator/campaign/condition_meaning_gate.py:2857-3035`

  requested が 0 なら comparison を 1、それ以外は default 0 と導出する。configure と observation の順序は常に「実 requested、comparison」とする。

  期待式 `:2996-3018` は各 observation の `define_value` から選択期待値を計算する。

  - 値 1 は `(1, 1)`。
  - 値 0 は `(0, 1)`。
  - 両 observation が同じなら従来どおり `compile-time-branch-selection-not-discriminating`。
  - 個別期待と違えば `compile-time-branch-selection-mismatch`。

  既存 8 macro の expected 文字列は従来の `requested=(1,1),default=(0,1)` と同じにする。

- `orchestrator/campaign/condition_meaning_gate.py:3566-3655`

  green evidence validator を macro 別にする。

  - 既存 8 macro は requested value 1、default slot value 0 を引き続き必須とする。
  - `BACKOFF_NOINLINE` は requested value 0 または 1、default slot は反対値を必須とする。
  - `selected_count` は observation の値に対応して 0 または 1、`completed_count` は常に 1。
  - argv 正規化 `:3633-3648` は hard-coded 1/0 ではなく各 observation の `define_value` を使う。

- `orchestrator/tests/fixtures/condition_meaning_gate/supplied/include/backoff.hh:1`

  現行 EVOLVE block の直前へ次を追加する。

  ```cpp
  #if BACKOFF_NOINLINE
  __attribute__((noinline))
  #endif
  ```

- `orchestrator/campaign/paper_story_a2_certification.py:630-654`

  `declaration` の初期値を `declare_define_runtime_meaning(request)` の返値にする。その後の `BACKOFF_FIXED` 用 legacy declaration だけを現行どおり上書きする。これにより `ConditionalBranchMeaningDeclaration` は factory からだけ得られる。

- `orchestrator/campaign/s1_direct_comparison.py:280-292`

  各 request についてまず `declare_define_runtime_meaning(request)` を呼び、None の場合だけ `_condition_meaning_declaration` `:229-246` の legacy BACKOFF_FIXED 宣言へ fallback する。helper の legacy 型と内容は広げない。

## テスト plan (正例・負例、file:line)

- `orchestrator/tests/test_condition_meaning_gate.py:30-39`

  `_COMPILE_TIME_BRANCH_MACROS` に `BACKOFF_NOINLINE` を追加する。

- `orchestrator/tests/test_condition_meaning_gate.py:196-220`

  `_compile_time_source_root` は registry の `source_rel` を使う。

  - 既存 8 macro は従来どおり transaction.cc を生成する。
  - `BACKOFF_NOINLINE` は supplied fixture を複製し、`include/backoff.hh` に試験 directive を置く。owner TU は fixture `transaction.cc:13` の include を利用する。
  - 既存 8 macro 向けの test support Options を変更しない。

- `orchestrator/tests/test_condition_meaning_gate.py:223-236,708-724`

  `_patch_added_branch_declaration` 自体は header patch をすでに扱えるため変更不要。registry binding test の fixture 読み先を固定 `cc/silo/transaction.cc` から `fixture / patch_declaration[0]` へ変える。noinline について次を assert する。

  ```python
  assert patch_declaration == (
      "include/backoff.hh", "#if BACKOFF_NOINLINE"
  )
  assert G.CONDITIONAL_BRANCH_WITNESSES[macro] == patch_declaration
  ```

- `orchestrator/tests/test_condition_meaning_gate.py:727-823` 付近に `test_backoff_noinline_header_owned_inert_meaning_observes_zero_and_one` を追加する。

  - factory が `ConditionalBranchMeaningDeclaration` を返す。
  - `source_rel == "include/backoff.hh"`。
  - record は green。
  - `requested.define_value == "0"`、count は `(0, 1)`。
  - `default.define_value == "1"`、count は `(1, 1)`。
  - `_validate_arm_record_integrity` が通る。
  - requested/default argv の define 以外が一致する。

- 同位置に `test_backoff_noinline_header_owned_requested_one_is_green` を追加し、診断要求 1、既定値 0 が従来形 `(1,1)/(0,1)` で green になることを固定する。

- `orchestrator/tests/test_condition_meaning_gate.py:879-1075` の負例群に `test_header_owned_branch_requires_instrumented_header_dependency` を追加する。

  owner TU は header を include せず、owner 内から marker macro を呼んで count だけを偽装する。assert は次のとおり。

  ```python
  assert meaning.terminal_status == "red"
  assert meaning.reason_code == (
      "compile-time-branch-instrumented-source-unobserved"
  )
  ```

- `orchestrator/tests/test_condition_meaning_gate.py:1096-1109`

  既存 macro の `(0, 0)` が None のままである parametrized test を変更しない。別 test で `BACKOFF_NOINLINE` の `(0,0)` と `(1,0)` だけが宣言され、`(0,1)`、`(1,1)`、default None は None になることを pin する。

- `orchestrator/tests/test_condition_meaning_gate.py:1112-1132,1938-1966`

  legacy declaration と CLI が `BACKOFF_FIXED` 固定である既存 assert を維持する。domain expectation には noinline が registry 経由で入るが、`MeaningWitnessDeclaration("BACKOFF_NOINLINE", ())` は引き続き ValueError とする。

- `orchestrator/tests/test_condition_meaning_gate.py:1135-1180`

  noinline の逆順 observation を使った green record も schema validator が受理し、同値 observation、wrong count、define が 0/1 以外、argv drift は拒否するケースを追加する。

- `orchestrator/tests/test_condition_meaning_gate.py:1924-1935`

  EVOLVE block 比較は変更しない。追加 3 行が block 外であるため、patch、supplied、F707 の conditional/hole 束縛が維持されることを既存 assert で確認する。

- `orchestrator/tests/test_paper_story_a2_certification.py:62-79`

  helper source に `declare_define_runtime_meaning` が含まれることを assert する。

- `orchestrator/tests/test_paper_story_a2_certification.py:500-562`

  noinline factory を sentinel declaration を返す stub にし、runtime evaluator が noinline request でその sentinel を受け取った場合だけ green を返す。期待値を次へ変更する。

  - factory call は `BACKOFF_NOINLINE`, requested 0, default 0 の 1 回。
  - rejection message には既存の BACKOFF_FIXED supply red が残る。
  - `BACKOFF_NOINLINE:runtime-meaning:meaning-witness-undeclared` は含まれない。

- `orchestrator/tests/test_s1_direct_comparison.py:62-66,393-429` 付近

  production record helper が factory を呼ぶことを source assert し、noinline request 0 に対する declaration が factory 由来で green、`unestablished_meaning_macros` に noinline が残らない正例を追加する。

静的計画のみであり、pytest は実行していない。

## 変異事前登録の候補

- 「計装 header の実読検査を外す」

  `test_header_owned_branch_requires_instrumented_header_dependency` が marker 偽装を green にしてしまう変異を殺す。期待は red と `compile-time-branch-instrumented-source-unobserved`。

- 「deep mirror を旧 ancestor-directory-symlink 方式へ戻す」または「compile operand を計装 header へ置く」

  `test_backoff_noinline_header_owned_inert_meaning_observes_zero_and_one` が green にならず、requested `(0,1)`、contrast `(1,1)` の assert で殺す。

- 「対照値 1 の configure または observation を外す」

  同じ inert 正例で `default.define_value == "1"` と `(1,1)` を要求し、値 0 だけの恒真検査を殺す。

- 「factory の registry 束縛を外す」

  registry から noinline を一時的に除いた状態で factory が None を返す test と、発行済み宣言が evaluation 時の factory 再照合で unestablished になる testを置く。既存 `test_compile_time_factory_keeps_unregistered_macro_unestablished` `:1078-1093` も維持する。

- 「既存 8 macro に inert factory を広げる」

  `test_compile_time_factory_rejects_nonpaired_values` `:1096-1109` の既存 macro `(0,0)` が None という assert で殺す。

- 「legacy declaration または CLI を noinline へ広げる」

  `test_legacy_meaning_declaration_and_cli_stay_backoff_fixed_only` `:1112-1132` と domain test `:1964-1966` で殺す。

- 「A-2 の factory 配線を外す」

  A-2 rejection test の sentinel identity、factory call 一覧、noinline undeclared message 不在の 3 assert で殺す。

- 「s1 の factory 配線を外す」

  noinline record が green であり、`unestablished_meaning_macros` に noinline がない assert で殺す。

## 配線しない driver と理由

- `paper_story_a1_paired.py`: `brief.md:63` のとおり要求対象が `BACKOFF_FIXED` だけで、`BACKOFF_NOINLINE` を要求しない。D1492 の第一条件を満たさない。

- `backoff_profile.py`: `brief.md:64` のとおり診断 build は行うが condition family を呼ばず、`admission=None`。D1492 の第二条件を満たさない。

- `backoff_sweep.py:82,125-150`: `raw-measurement` のみに閉じ、promotion 成果物へ admission を載せない前提で配線しない。

- `screening_driver.py:53,101`: `raw` のみに閉じ、同じ理由で配線しない。

- `silo_ladder_rung1.py:2213`: `raw-measurement` のみに閉じ、同じ理由で配線しない。

- `tools/pegasus/probes/t1683_rr5_cost_probe.py:152-209`: probe の raw measurement であり、promotion admission を作らないため配線しない。

- `backoff_repro`: `brief.md:121-123` では raw 系として挙がる一方、実測列挙 `brief.md:58-64` には個別 anchor がない。親が実在する gate 呼び出しと artifact carriage を確認できるまでは変更面へ入れない。

## 残る懸念

- D1492 の「成果物」が raw receipt まで含むなら、raw-only という理由は不十分である。その解釈では上記 raw driver も配線対象となる。親の段 4 では「promotion 成果物だけ」を指すのかを明記すべきである。

- `-ffile-prefix-map` は `__FILE__` と `__BASE_FILE__` の一時 root を畳めるが、dependency file の path 表記まで変換するとは仮定しない。依存 token は compile cwd 基準で実 path 化して比較する。

- fixture の直接 include は `transaction.cc:13`、実木は `external/ccbench/cc/silo/include/transaction.hh:9` を経由する。深い鏡像が両方で効くことは、親の実 fixture、実 patch 木 dogfood で確認が必要である。

- repo 外の Pegasus attempt root と durable base は未走査なので、「既受理成果物への影響が全保存先で空集合」とはまだ断定できない。

- inert noinline で optional `configured_commands` を渡す経路は、supply 用 control と meaning 用 contrast が異なる。A-2 と s1 はこの共有 seam を使わないため本変更では触らず、渡された場合は値不一致で fail-closed とする。

## 総括

実装の芯は、`BACKOFF_NOINLINE` だけを registry factory に追加し、header を計装した深い shadow treeの owner TU 全体を値 0 と値 1 で前処理することにある。計装 header の依存実読を必須にし、要求 0 は `(0,1)`、対照 1 は `(1,1)` の場合だけ green とする。

既存 8 macro は factory 条件、shadow 分岐、evidence field、canonical schemaを変えない。A-2 と s1 のみを確実に配線し、supply arm、D1523、CLI、legacy declaration、台帳には触れない。