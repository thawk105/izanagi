## 所見

必読6資料と適用済み現物を確認しました。所有5ファイルの `git diff` は `author-impl.patch` と byte 一致です。以下は静的レビューであり、pytest・変異・実TUの実走は行っていません。

略号：G＝`orchestrator/campaign/condition_meaning_gate.py`、T＝`orchestrator/tests/test_condition_meaning_gate.py`、S＝`orchestrator/tests/test_s8a_trigger_sweep.py`。

1. **real／must-fix — m4 の変異定義と期待する kill が整合していません。**  
   根拠：`ruling.md` の m4、G:3354・3366、T:1486・1509。対照の受理条件を `selected ≤ N·c` にしても、新規3 macro は `c=0` なので、非負の実測 count に対して元の `selected=0` と同じです。負例 `(2,2)/(1,2)` は依然として拒否され、指定の直接検査では kill できません。completion 検査を残す等、変異の exact な差分を確定して期待を訂正する必要があります。  
   **放置時の成果物変化：** 等価変異または意図と異なる変異を「評価側の緩和を検出した」と変異台帳へ誤記します。

2. **real／must-fix — m4 の直接検査が、独立した帰属点になっていません。**  
   根拠：[T:1497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-bc/orchestrator/tests/test_condition_meaning_gate.py:1497)、G:3441・1126。直接呼出しは公開 evaluator と red assertion の**後**です。対照 `(1,N)` を本当に通す評価側変異なら、evaluator 内の green record 発行時に schema が拒否し、T:1509 に到達しません。直接検査を独立 node に分離する必要があります。  
   **放置時の成果物変化：** schema による kill を評価側直接検査の成果として計上し、防壁ごとの検出能力を過大評価します。

3. **real／must-fix — baseline の既知失敗が残っています。**  
   根拠：T:3282、`test_s1_direct_comparison.py:697・794`、`focus-logs.md:5・10`。docstring pin は旧18件を要求し、S1 fixture はGATINGを1箇所しか生成しません。またGATINGを未確立例に使う期待も失効しています。N=12の本体判定を緩めず、fixture と未確立持越しの試験材料を更新すべきです。  
   **放置時の成果物変化：** 正常な認証経路の回帰確認が赤のままとなり、変異による追加失敗と baseline 失敗を混同します。B-4 の未commit状態による1件は別扱いです。

4. **real／must-fix — GATINGの裁定済み境界がコード上の説明へ十分反映されていません。**  
   根拠：[G:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2153-witness-bc/orchestrator/campaign/condition_meaning_gate.py:12)、G:316・322、T:1401。module docstring の “complete owner TU” と “guarded branches” は、直後の “declared conditional” により限定されていますが、**DefineSpec patchの逐語12箇所だけ**であり、instr複合枝・`#ifndef`番兵を除外するという裁定は明記されていません。author報告には限定があります。module説明と対応テストの説明にも残してください。  
   動的到達性・runtime anomaly・正しさを証明しないという文言は既に適切です。段4裁定を覆して複合枝の計装を要求する所見ではありません。  
   **放置時の成果物変化：** GATINGが未確立一覧から消えた記録を、重ね当て後の全条件箇所の確立として読み違えられます。

5. **refuted／nit — None対応による旧受理経路の拡大は確認できません。**  
   根拠：G:1015・2299・3471・4280。factory は `#ifdef` 登録だけ requested `"1"`／default `None`／owner条件を要求し、既存 `#if` の `1/None` は宣言しません。不在検査も `#ifdef` 登録かつ非stockに限定されます。NOINLINE・SORT・stock対照へは波及しません。旧宣言はBACKOFF_FIXED固定です。  
   `_effective_companions`、`_configure_defines`、`_preprocess_argv`、`_compile_defines`、`_cli_meaning_cases` の関数本文はHEADとbyte一致を確認しました。`--meaning-case` の制限にも差分はありません。factory=None は従来どおり **unestablishedであり、単独ではfamily拒否ではありません**。  
   **成果物への影響：** 同一要求に対する受理を広げる変更は見当たりません。MISATTRのdriver要求変更 `1/0 → 1/None` は別の要求として扱う必要があります。

6. **refuted／nit — 全箇所観測が欠落・不活性・自己入れ子を黙認する経路は確認できません。**  
   根拠：G:2993・3015・3352。一致した全indexへ挿入し、N=1のreason/detailは旧逐語のまま、N>1の件数違いは `site-count-mismatch` です。requested／contrast双方でcompletion=Nを要求します。自己入れ子では対照の内側completionが欠けて赤になります。  
   T:1475の4変異は、directive→件数、inactive→completion、partial-default→対照selected、undef→両腕同一、という最初の拒否へ帰属します。ただし「他の検査もすべて無関係」という意味での単一理由ではありません。自己入れ子そのものの追加負例は見当たりません。`comparison or "0"` は既存default `"0"`、NOINLINE requested=0のcontrast `"1"`を変えません。  
   **成果物への影響：** 宣言箇所の一部欠落をgreenとして認証する問題は確認できません。

7. **refuted／nit — 未定義対照のargv検査とcache消去は機能する構造です。**  
   根拠：G:2082・3156・1719・1949。`-DM` と `-D M` は値 `"1"` として辞書に入り、期待Noneに反するため拒否されます。`-UM` は定義として数えませんが、`-DM … -UM` でも辞書のMを消さないため、不在検査は保守的に拒否します。`-U` はargv比較からも除去しません。  
   CXX_FLAGS routeはNoneでも `-DCMAKE_CXX_FLAGS=<baseとcompanions>` を明示するので、共有cacheのrequested `=1`を残す実装ではありません。`focus-logs.md:28` の登録前後supply比較もこの読みと整合します。  
   **成果物への影響：** 対照に残った対象defineを見逃してgreen化する経路は確認できません。

8. **refuted／nit — schema変異はissuerに隠されていません。**  
   根拠：G:3879・4050・4060、T:1558。正常公開recordを `require_issuer=False` で先に受理し、count・None・argvを一つずつ改変しています。split `-D M=1` の正常例もあります。対象define以外と `-U` は除去せず、dangling `-D` の新規拒否は `#ifdef` 分岐内だけなので旧 `#if` 経路は不変です。  
   supply単独試験T:1441もmeaningを呼びません。CMake条件は対照だけに注入します。ただし裸 `-DM` は要求と同じ数値1なので、不在検査を外すと別理由 `preprocess-bytes-identical` でも赤になります。m6の防壁除去でgreenになる正例は、`=0` の2形です。  
   **成果物への影響：** schema変異の帰属は妥当です。裸defineケースまで「唯一の拒否防壁」と説明すると台帳が過大主張になります。

## 変異の帰属予測

以下は**静的予測**です。既知baseline失敗を除いた追加失敗を記録してください。T／Sは上記ファイルを表します。

| 変異 | 予測されるnode・最初の帰属 |
|---|---|
| m0 | **SURVIVED（等価）**。追加失敗なし。既知docstring pin赤をkillに数えない。 |
| m1 | **KILLED**：S::`test_coverage_condition_gate_passes_exact_factory_pair[misattr]`、request.default assertion（S:139）。declaration assertionより先。 |
| m2 | **KILLED**：同nodeの `[misattr]`／`[gating]`、declaration型（S:141）。 |
| m3 | **KILLED**：T::`test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches` のN比較（T:1049）。T::`test_new_branch_selection_supply_meaning_and_admission[BACKOFF_TRIGGER_GATING]` と `test_compile_time_branch_selection_accepts_each_registry_macro[BACKOFF_TRIGGER_GATING]` も件数不一致で落ちる。patchの `[pair]*N` 自体は独立期待12のままなので通る。 |
| m4 | **記載どおりの≤なら指定nodeによるkillは予測できない**。`partial-default` の1は依然拒否。実際に対照1を通す別変異ならT::`test_multisite_rejects_missing_or_wrong_selection[partial-default-IZANAGI_SILO_LADDER_RUNG1]`／`[partial-default-BACKOFF_TRIGGER_GATING]` がrecord発行時schemaで先に落ち、直接検査へ到達しない。 |
| m5 | **KILLED**：T::`test_new_branch_green_schema_rejects_count_value_and_argv_mutations` の新規3macro。default selected=1の最初の改変が受理され、`pytest.raises` が失敗。issuer・digestには隠されない。 |
| m6 | **KILLED**：T::`test_undefined_contrast_rejects_compile_define_in_supply[tokens0]`／`[tokens2]` はsupplyがgreenになり失敗。`[tokens1]` は別理由の赤になりreason assertionで失敗。 |
| m7 | **KILLED**：T::`test_ifdef_factory_and_supply_reject_one_vs_zero` のfactory型、registry束縛testの集合／順序比較、Sの `[misattr]` の型検査。MISATTRをfixtureから作る正例・schema例・supply例はT:253の **KeyError** が先なので別帰属。 |
| m8 | **KILLED**：T::`test_if_macro_none_contrast_keeps_cmake_default_supply_behavior`。SORT対照のCMake既定defineを新不在検査が拒否し、期待greenに反する。 |

## 判定

**NO-GO。** 本体の受理集合を不当に広げる具体経路は確認できませんが、受入と変異台帳を確定するには次が必要です。

- m4のexact変異と期待を訂正し、評価側直接検査を独立nodeにする。
- docstring pin、S1 fixture、未確立持越し例の既知失敗を解消する。
- GATINGのskeleton12箇所という境界をmodule／テスト説明へ明記する。
- 段4必須の計算ノード実TU cellと変異実測を確認する。提示された `focus-logs.md` の実TU結果はlogin分であり、計算ノードのpytest結果で代用できません。

## 総括

実装の中心である未定義対照・全箇所counts・green再検証は裁定と整合しています。主要な不足は、m4の定義と帰属、既知回帰失敗、主張範囲のコード上の明記です。I1の提示実測はSORT／REPORTの揮発差を除いた一致までであり、全既存recordのbyte一致や公開driver JSONの取得まで完了したとは扱えません。