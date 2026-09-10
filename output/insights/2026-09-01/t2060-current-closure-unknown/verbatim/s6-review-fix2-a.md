静的検査の結論は次のとおりです。

- 22 node の主たる検査性質は維持されています。重点指定された `test_m3_*` と submodule recursive に、portable 化で新たに恒真化した node は見つかりませんでした。
- ただし保証は完全には同一ではありません。全 22 node から「実 rollout 由来 POS bytes が production の既定 hash / numstat pin を満たすこと」という共通の統合前提が失われました。
- supervisor / replay 系 8 node はさらに、production の既定 POS spec を通す代わりに test-local spec を注入しています。対象 assertion は維持されていますが、統合保証は弱くなっています。
- skip / duplicate / SHA 不一致の三分岐は、想定された canonical 入力では正しく分離されています。
- test resolver と production `_find_rollout` には具体的な不一致があります。
- pytest は実行していません。

以下では略号を使います。

- `T`: `orchestrator/tests/test_codex_reasoning_ab.py`
- `P`: `tools/codex_reasoning_ab.py`
- `D`: `s6-fix2-diff.patch`
- `B`: `blocker-adjudication.md`

## 22 node の保証の同一性 (全件表)

旧入力の共通形は、現在 `historical_benchmark_snapshots` として残る `T:922-971` です。POS は実 rollout 3 本から独立 2 route の golden を導出し、NEG は integrated diff の内容を使い、両 case の prompt も実 rollout から作っていました。

新入力の共通形は `T:975-1036` です。POS / NEG とも `_build_snapshot_base` の integrated 内容をコピーし、POS の `PATCH_PATHS` hash と numstat だけを NEG 値へ変えた test-local spec で受理します。

表中の「共通損失」は、旧 fixture setup が持っていた実 rollout 存在、独立 golden、production POS pin 受理という付随保証が失われたことを指します。

| # | node | 変更前の入力と検査 | 変更後の入力と検査 | 失われた性質 |
|---:|---|---|---|---|
| 1 | `test_forbidden_commits_are_unreachable_in_both_cases` | 実 rollout 由来 POS と実 NEG snapshot。禁止 commit が object store から到達不能で ref が 1 本だけか検査、`T:2283-2299` | portable POS / NEG に対し同じ `cat-file` と ref 検査 | 対象性質は保持。object store は両 fixture とも `_build_snapshot_base` 由来。共通損失のみ |
| 2 | `test_cleaned_snapshot_records_absent_commit_graph_and_keeps_closure` | 旧 snapshot を production default spec で検証し、commit-graph 不在、object-info 清掃、禁止 commit と focus 履歴不在を検査 | `_verify_benchmark_snapshot` で portable spec を渡し、同じ closure assertion、`T:2448-2485` | closure 性質は保持。POS が production default spec を通る統合保証は喪失 |
| 3 | `test_stale_commit_graph_referencing_pruned_commit_is_rejected_and_manifested` | 実 POS をコピーし stale graph を注入。直接の closure reason と default verifier の拒否を検査 | portable POS と portable spec で同じ注入と拒否を検査、`T:2765-2789` | stale graph 検出は保持。default POS hash / numstat との統合保証は喪失 |
| 4 | `test_m1_snapshot_head_pin_is_independent` | production POS spec を複製し head だけゼロ化、実 POS が `HEAD mismatch` になることを検査 | portable POS spec を複製して同じ head 変異、`T:3438-3449` | head 独立性は保持。変異箇所以外の POS hash / numstat が production 値である保証は喪失 |
| 5 | `test_m3_snapshot_mode_change` | 実 POS / NEG の `TRACKED_PATHS[0]` を `0600` にし default verifier の mode 拒否を検査 | portable POS / NEG と portable spec で同じ変異、`T:3472-3483` | 保持。対象ファイル、期待 mode、検出処理は不変。POS content pin の付随保証だけ喪失 |
| 6 | `test_m3_symbolic_head_is_required` | 実 POS の `.git/HEAD` を detached にして symbolic HEAD 拒否を検査 | portable POS へ同じ変異、`T:3486-3495` | 保持。branch / HEAD は portable spec でも production と同一。共通損失のみ |
| 7 | `test_m3_ignored_extra_and_missing` | 実 POS / NEG に ignore 済み extra を追加し、case ごとの既存 artifact を削除。extra と missing を検査 | portable POS / NEG に同じ操作、`T:3498-3522` | 保持。untracked / forbidden / artifact 集合は変更されていない。共通損失のみ |
| 8 | `test_m3_focus_artifact_directions[POS-focus1.md]` | POS で禁止されている focus1 を実 POS に追加し拒否を検査 | portable POS に同じ追加、`T:3525-3543` | 保持。POS の artifact direction は不変 |
| 9 | `test_m3_focus_artifact_directions[POS-focus2.md]` | POS で禁止されている focus2 を追加 | portable POS に同じ追加 | 保持。focus2 は新旧とも POS artifact 集合に存在しない |
| 10 | `test_m3_focus_artifact_directions[NEG-focus2.md]` | NEG で禁止されている focus2 を実 NEG に追加 | portable NEG に同じ追加 | 保持。NEG snapshot と NEG spec は実質不変 |
| 11 | `test_snapshot_submodule_object_store_is_recursive` | 旧 base 非変異、POS / NEG index 同一、実 POS の recursive submodule、grafts 注入拒否を検査 | 同じ `_build_snapshot_base` と submodule tree に対して同じ assertion、`T:3546-3579` | submodule 性質は保持。submodule は rollout-derived `PATCH_PATHS` と独立。POS default spec 受理のみ喪失 |
| 12 | `test_pos_neg_submodule_initialization_state_mismatch_is_rejected` | 実 snapshot oracle から schedule を作り、NEG の submodule manifest SHA を変更して POS / NEG mismatch を検査 | portable oracle から同じ schedule を作り同じ変異、`T:6443-6454` | 保持。submodule manifest は同じ base から得られる。共通損失のみ |
| 13 | `test_validate_schedule_legacy_different_arm_same_model_pair_remains_valid` | 実 prompt / oracle digest を持つ legacy schedule を normalize | portable prompt / oracle digest の schedule を normalize、`T:7395-7404` | legacy normalization 性質は保持。実 prompt / snapshot digest を入力とする統合保証は喪失 |
| 14 | `test_git_answer_object_reinjection_is_rejected` | 実 NEG へ artifact commit を fetch し default verifier が forbidden object を拒否 | portable NEG へ同じ fetch、portable helper で拒否、`T:7478-7492` | 保持。NEG content と NEG spec は変更されていない |
| 15 | `test_supervisor_launches_pair_and_scrubs_git_environment` | 実 POS snapshot と実 render prompt、production default verifier を通して supervisor を起動し、順序、環境、sandbox receipt を検査 | portable POS、literal prompt、verifier wrapper を使い同じ assertion、`T:8974-9002`、wrapper は `T:1421-1448` | 主たる supervisor / sandbox 性質は保持。実 prompt と production default POS spec の統合保証は喪失 |
| 16 | `test_agent_sandbox_binds_exclude_attempt_receipt_directory` | 同じ旧 supervisor 入力で bind 集合を検査 | portable 入力と wrapper で同じ bind assertion、`T:9005-9026` | bind 性質は保持。前行と同じ統合保証を喪失 |
| 17 | `test_verify_replays_complete_fake_codex_experiment` | 実 POS / NEG snapshot と prompt から fake experiment を構築し、production replay、ledger、decision、追加 rollout tamper を検査 | portable fixture と wrapper から同じ manifest を構築し同じ assertion、`T:9143-9199` | replay 集計と tamper 検出は保持。production default spec と実 prompt の end-to-end 保証は喪失 |
| 18 | `test_material_replay_rejects_task_manifest_exchange_at_digest_consumers` | 旧 full manifest へ alternate task manifest を渡し digest mismatch を検査 | portable full manifest へ同じ交換、`T:9202-9224` | digest binding は保持。fixture の実 provenance 統合のみ喪失 |
| 19 | `test_replay_forwards_only_successful_snapshot_evidence_to_adjudication` | 旧 full manifest を使い、NEG replay 結果だけ意図的に変えて verified run ID の伝播を検査 | portable full manifest と wrapper の上で同じ強制 mismatch、`T:9601-9719` | 保持。成功 / 失敗集合はテスト内で明示的に構成され、実 POS / NEG bytes 差に依存していない |
| 20 | `test_verify_checks_pre_post_snapshot_for_every_shared_oracle_run` | 旧 manifest の共有 oracle と post snapshot tamper で replay 回数と拒否理由を検査 | portable manifest で同じ共有化と tamper、`T:9722-9835` | 保持。pre/post mismatch は明示的 JSON 変異で成立。実 rollout 内容には依存しない |
| 21 | `test_attempt_four_is_rejected_before_launch` | 実 POS snapshot / prompt と production verifier を通る状況で attempt 4 を拒否 | portable POS / prompt に verifier wrapper を明示導入、`T:12308-12330` | attempt bound は保持。attempt 判定前後の production default snapshot 検証との統合保証は喪失 |
| 22 | `test_f3_4_prelaunch_exception_completes_pair_and_allows_next_generation` | 実 POS snapshot / prompt で prelaunch 例外、pair completion、attempt 2 retry を検査 | portable POS / prompt と wrapper で同じ例外、ledger、retry assertion、`T:12333-12438` | pair lifecycle は保持。production default POS spec と実 prompt の統合保証は喪失 |

## 恒真化の検出

### snapshot の構造差

| 面 | 変更前 | 変更後 | 判定 |
|---|---|---|---|
| base repository | `BASE_COMMIT` object closure を作り integrated diff を working tree へ適用、`P:3292-3315` | 同じ | 同一 |
| POS `PATCH_PATHS` | author + fix1 と integrated - fix2 の独立 2 route が一致した bytes で上書き、`P:925-978`, `P:3321-3347` | 上書きしない。base にある integrated、すなわち NEG 内容のまま、`T:987-1018` | 差が消失 |
| POS hash | `bc3f...` と `ed3f...`、`P:263-272` | `0bc5...` と `c4f5...` に対応する NEG bytes、`P:273-281`, `T:1010-1017` | POS / NEG 差が消失 |
| POS numstat | 主要 2 行が `[693,0]` と `[123,10]`、`P:283-291` | NEG の `[764,0]` と `[126,10]` を spec に設定、`P:292-299`, `T:1015-1017` | POS / NEG 差が消失 |
| artifact 集合 | POS / NEG ごとの `CASE_ARTIFACTS` を artifact commit から配置 | 同じ、`T:997-1008` | 同一 |
| forbidden focus 方向 | POS は focus1 / focus2、NEG は focus2 | 同じ `_snapshot_spec`、`P:1002-1010` | 同一 |
| Git object closure / submodule | `_build_snapshot_base` 由来 | 同じ | 同一 |
| prompt | real rollout から `render_prompt`、receipt あり、`T:959-970` | `portable POS/NEG benchmark prompt`、receipt は `None`、`T:1020-1031` | 実 prompt 性質を喪失 |
| verifier spec | production default `_snapshot_spec` | POS の hash / numstat を NEG に変えた test-local spec、`T:1009-1018` | production POS pin 統合を喪失 |

### 重点 node の判定

- `test_m3_snapshot_mode_change`: mode だけを `0644` から `0600` へ変えます。portable 化で変更されたのは content hash と numstat で、期待 mode は同一です。恒真化は refuted。
- `test_m3_symbolic_head_is_required`: `.git/HEAD` の symbolic 性だけを変えます。head / branch spec は変更されていません。恒真化は refuted。
- `test_m3_ignored_extra_and_missing`: extra filesystem entry と artifact 欠落を作ります。untracked / artifact 集合は新旧同じです。恒真化は refuted。
- `test_m3_focus_artifact_directions` 3 node: case ごとの forbidden 集合は変更されていません。恒真化は refuted。
- `test_snapshot_submodule_object_store_is_recursive`: submodule と grafts は同じ base builder が作る構造です。rollout-derived 2 ファイルは submodule 検査に関与しません。恒真化は refuted。

したがって、「実 rollout 由来の差が消えたことにより、これらの named assertion が恒真になった」という重大所見はありません。ただし「実 POS 内容と production pin の整合」という別の保証自体は全 22 node から消えています。

## skip / 赤 の区別の正しさ

### 指定された三分岐

1. 不在

   `matches[label]` と `named_candidates[label]` がともに空なら missing へ入り、`_require_historical_rollouts` が label 付きで skip します。`T:876-912`。追加 test は `T:1089-1100`。

2. 重複

   identity match が 2 件なら `len(candidates) != 1` で `RC_SESSION` を送出し、skip 層は捕捉しません。`T:879-888`。追加 test は `T:1103-1123`。

3. SHA 不一致

   identity match が 1 件なら `_verify_rollout_sha` へ進み、`RC_SNAPSHOT` が伝播します。`T:889-895`、`P:640-655`。追加 test は `T:1126-1145`。

### 「名前は在るが中身が一致しない」場合

`if not candidates and not named_candidates[label]` は偽になります。その直後の `len(candidates) != 1` が真になるため、結果は skip ではなく `RC_SESSION` の赤です。`T:879-888`。

これは parent の fail-closed 要求 `B:52-54` と一致します。

### 精度上の問題

`historical_rollouts` は、各 consumer が必要とする label の部分集合ではなく常に 5 label 全部を要求します。`T:782-800`, `T:916-918`。

例えば:

- `test_m2_production_golden_requires_both_routes` が実際に必要なのは author / fix1 / fix2 ですが、POS または NEG rollout が欠けても skip します。
- prompt replacement 3 node と collector golden は POS だけを使いますが、他の 4 label が欠けても skip します。
- `test_parent_numstat_controls_remain_pinned` は numstat assertion 自体には rendered prompt を使いませんが、historical fixture は POS / NEG prompt まで生成します。

従って、6 node への限定はできていますが、label 単位の依存判定は過大です。現在の「5 本すべて欠落」環境では結果は同じですが、部分復旧時には不要な skip または不要な赤を発生させます。

また、session ID を含まない名前へ rename され、同時に session metadata が読めないほど破損したファイルは required rollout と関連付けられないため「不在」扱いです。canonical filename が残る破損は `named_candidates` により赤になります。

## resolver 二重実装の食い違い

`_matching_required_session_ids` 単体の identity 規則 `T:803-848` は、production `_rollout_matches_session` `P:534-569` と実質同じです。

しかし resolver 全体は一致しません。production `_find_rollout` には exact filename の高速経路があります。session ID suffix に一致する候補が 1 件なら、その 1 件だけを検査して返し、別名の identity match を数えません。`P:596-626`。

具体的な食い違い入力:

```text
sessions/
  a/rollout-2026-xx-<SID>.jsonl
  b/rollout-alias.jsonl
```

両ファイルの内容を同一の正しい session metadata とし、SHA pin もその bytes に一致させます。

- test resolver: 両方を identity match と数え、`len(candidates) == 2` で `RC_SESSION`。
- production `_find_rollout`: suffix が `<SID>` の候補は `a` の 1 件だけなので、高速経路で SHA を確認して `a` を返す。`b` は無視。

つまり precondition が赤なのに本体 resolver は解決する入力を具体的に構成できます。影響は false-green ではなく false-red、すなわち不要な wave 停止です。

逆方向、すなわち precondition が 1 件を SHA 一致で解決したのに、同じ静止 filesystem と一意な session ID に対する production `_find_rollout` が失敗する入力は見つかりませんでした。precondition の 1 件集合は production fallback の 1 件集合にもなるためです。

別件として、`labels_by_session = {session_id: label ...}` は同じ session ID を複数 label が共有する manifest で最後の label だけを残します。`T:863-866`。default manifest は 5 ID が一意なので現状には発火しませんが、汎用 resolver としては production の label ごとの個別解決と一致しません。

## scope 逸脱の判定

「fixture 作り替え自体が scope 逸脱」という主張は refuted です。

parent の要求は:

- 外部証拠依存 node だけを限定する
- 非依存 node を skip しない
- module fixture 全体を落とさない

です。`B:49-58`。

実装は旧 fixture の生成処理を `historical_benchmark_snapshots` として残し、6 node だけに `historical_rollouts` または historical snapshot を要求させています。22 node 用には別の module-scope portable fixture を残しています。したがって構造上は案 5 の範囲内です。

ただし実装範囲は最小ではありません。

- 良い点: 22 node の signature を大量変更せず、共通 builder、artifact、submodule closure を再利用できる。
- 悪い点: POS / NEG の本来の content 差を fixture 全体で消し、supervisor / replay に test-local verifier monkeypatch を導入した。`T:1039-1076`, `T:1421-1425`, `T:1823-1831`。
- より狭い形: closure、M3、schedule、supervisor 各 consumer 群へ必要フィールドだけの小さい fixture を分け、production default spec を通す検査と synthetic spec を使う検査を明示的に別名にする。この形なら統合保証の喪失が見えやすい反面、fixture 重複は増える。

よって「scope 逸脱」ではありませんが、test seam が広くなったことはレビュー上の実在する弱化です。

## 既存期待値と pin の保全

削除 28 行を物理行ごとに確認しました。

| # | 削除行 | 内容 | 判定 |
|---:|---|---|---|
| 1 | `D:9` | `_REAL_ROLLOUT = (` | path locator pin の削除 |
| 2 | `D:10` | `_HISTORICAL_SESSIONS` | 同上。manifest resolver へ置換 |
| 3 | `D:11` | 固定日付 directory | 同上 |
| 4 | `D:12` | 固定 rollout filename / session ID | 同上。session ID pin 自体は manifest に残る |
| 5 | `D:13` | 定数終端 | assertion ではない |
| 6 | `D:156` | 旧 `benchmark_snapshots` 定義行 | historical fixture への rename / split |
| 7 | `D:157` | root `is_dir()` 判定 | 5 rollout 判定へ置換 |
| 8 | `D:158` | root 不在 skip | label 付き skip へ置換 |
| 9 | `D:372` | numstat test の旧 fixture 引数 | historical fixture へ置換 |
| 10 | `D:375` | POS default verify 1 行 | historical POS の同じ default verify へ置換 |
| 11 | `D:376` | NEG default verify 1 行 | historical NEG の同じ default verify へ置換 |
| 12 | `D:390` | cleaned snapshot の default verify | portable helper へ変更。暗黙の POS pin 保証を変更 |
| 13 | `D:401` | stale graph の default verify | portable helper へ変更 |
| 14 | `D:412` | M1 の production POS spec | portable POS spec へ変更。暗黙期待値の実変更 |
| 15 | `D:416` | M1 の直接 verify | helper へ変更 |
| 16 | `D:434` | mode test の default verify | helper へ変更 |
| 17 | `D:445` | symbolic HEAD の default verify | helper へ変更 |
| 18 | `D:456` | ignored extra の default verify | helper へ変更 |
| 19 | `D:467` | missing artifact の default verify | helper へ変更 |
| 20 | `D:478` | focus direction の default verify | helper へ変更 |
| 21 | `D:489` | submodule clean verify | helper へ変更 |
| 22 | `D:500` | submodule graft verify | helper へ変更 |
| 23 | `D:511` | NEG reinjection default verify | helperへ変更。ただし NEG spec は同一 |
| 24 | `D:526` | prompt test の固定 rollout path | manifest-resolved POS path へ変更 |
| 25 | `D:535` | collector test の引数なし定義 | historical fixture 引数付きへ変更 |
| 26 | `D:541` | hash assertion の固定 path 読取 | resolved POS path 読取へ変更。assert と hash pin は保持 |
| 27 | `D:545` | token slice の固定 path 読取 | resolved POS path 読取へ変更。slice assert は保持 |
| 28 | `D:556` | attempt-four の 1 行 signature | monkeypatch 引数追加のため再整形 |

結論:

- 既存の `assert` 行は 1 行も削除されていません。
- session ID、rollout SHA、golden SHA、numstat の literal pin 値自体は変更されていません。
- 固定 rollout filesystem path という locator pin は削除されています。これは identity + SHA resolver への置換であり、証拠 pin の弱化ではありません。
- 一方、12から22の default verifier 呼び出しと14の spec source 変更により、POS hash / numstat の暗黙期待値は実質的に変更されています。従って「既存期待値に一切変更なし」という完了報告は、literal assert に限れば正しいものの、検証意味論まで含めると不正確です。

## 所見一覧

| ID | 判定 | 実体 | 影響 |
|---|---|---|---|
| A-01 | real | `T:975-1018`, `P:263-299` | portable POS は `PATCH_PATHS` と numstat が NEG と同一になり、実 rollout 由来 POS 内容の保証を失う |
| A-02 | refuted | `T:3472-3579`, `P:997-1010` | M3 mode / HEAD / extra / missing / focus と recursive submodule の named 性質は、消失した content 差に依存せず恒真化していない |
| A-03 | real | `T:1039-1076`, `T:1421-1425`, `T:1823-1831` | supervisor / replay 系は production default POS spec ではなく test-local spec を通すため統合保証が弱い |
| S-01 | refuted | `T:879-895`, `T:899-912` | canonical な不在、重複、SHA 不一致は skip、RC_SESSION、RC_SNAPSHOT に正しく分離される |
| S-02 | real | `T:782-800`, `T:916-924` | 5 label 一括 gate のため、各 node が不要な label の欠落や破損でも skip または赤になる |
| R-01 | real | `T:867-894`, `P:596-637` | canonical 名 1 件と別名 identity duplicate 1 件で test resolver は赤、production resolver は受理する |
| R-02 | real | `T:863-866` | 複数 label が同一 session ID を持つ manifest では label mapping が上書きされる |
| C-01 | refuted | `B:49-58`, `T:916-1036` | fixture split は案 5 の範囲内であり、module fixture 全体を skip していない |
| P-01 | real | `D:9-13`, `D:390-500` | literal hash pin は保持されたが、固定 path pin の削除と default POS spec から portable spec への意味変更がある |

## 総括

22 node の主たる assertion は全件静的に追跡でき、重点 node を含め新たな恒真化は確認されませんでした。その意味では portable 化は成立しています。

ただし「同じ保証を完全に維持」は成立しません。実 POS rollout bytes、独立 golden、real prompt、production default POS spec との統合保証が除かれています。特に supervisor / replay 系では test-local verifier 注入がこの差を隠します。

修正を差し戻すほどの重大な target-property 喪失は見つかりませんでしたが、次の 2 点は修正候補です。

1. historical gate を node ごとの必要 label 集合へ細分化する。
2. preflight resolver を再実装せず production resolver と同じ候補選択 primitive へ一本化する。

pytest 緑、skip 数、実行時挙動は本 review では確認していません。