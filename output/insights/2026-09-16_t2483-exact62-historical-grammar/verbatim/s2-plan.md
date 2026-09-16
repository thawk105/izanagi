## 方針と確認結果

**exact-24 の先例に沿って、既存 2 module の歴史閲覧分岐に exact-62 を追加する。** 通常 decoder・encode・resume・certified admission の受理条件は変更しない。

必読 7 ファイルは読み取り成功。ファイル変更、pytest、commit・branch 操作は行っていない。以下の行番号は変更前の worktree を指す。

`git show 2a9ba783f^:orchestrator/campaign/campaign_lock.py` から tuple を取得し、AST による静的比較で次を確認した。

- 62 path の宣言順は親の `measured-facts.md:32–93` と完全一致。
- 現行 63 の末尾 `orchestrator/campaign/verify_fanout_worker.py` を除いた列とも一致。ただし実装には slice を使わない。
- sorted path を**末尾 LF 付き**で連結した SHA-256 は、親の値 `ea217fefb2565a3f7d8f811bed864aedab0b5a461a4947ac0d1abaad9cb6ff59` と一致。

追加探索で指定した `docs/insights*` は存在しなかった。必読対象ではないため続行し、scope の根拠は記録 commit の実コードと `docs/decisions.md` から確認した。

## 1. campaign_lock.py の変更計画

対象は [campaign_lock.py][codec]。

| 位置 | 変更 |
|---|---|
| `:143` の exact-24 literal 直後 | `T733_EXACT62_CONTRACT_LOADER_RELATIVE_PATHS` を新設。記録 commit の 62 行を宣言順の独立 tuple literal として置く。 |
| `HistoricalCampaignLockAuthority.__post_init__:211` | whitelist に上記 tuple を追加。exact tuple 型、tuple 全体の一致、blob map の宣言順一致を維持する。 |
| `_validate_pre_t733_historical_authority:382` の直後 | 同型の兄弟関数 `_validate_t733_exact62_historical_authority` を追加する。 |
| `decode_historical_campaign_lock:568` | 現行・exact-62・exact-24 の識別へ拡張。docstring も収載済み 3 grammar に合わせる。 |

**validator は一般化せず、兄弟関数を採る。** 今回は歴史 grammar 1 件だけの追加であり、exact-24 の検証順・エラー文・返却値をそのまま残せる利点が大きい。任意の tuple を渡す検証器や registry を導入する必要もない。

兄弟関数は既存関数の検査をすべて踏襲する。

- authority の exact keys、正の exact int serial。
- `tuple(blob_sha256s) == tuple(sorted(T733_EXACT62_...))`。
- 62 path **全件**の digest 形式検査。
- environment / activation hash、記録 commit の形式検査。
- blob map を **62 path の宣言順**で再構成し、`HistoricalCampaignLockAuthority` を返す。

decoder の分岐は次の形にする。

1. `:593–595` の現行 wire tuple 一致は既存どおり通常 decoder を呼び、歴史専用型へ投影。
2. それ以外では既存の inner identity 検証を維持。
3. `:603` で exact-62 wire tuple と一致すれば兄弟関数。それ以外は既存 exact-24 validator に渡す。
4. exact-24 でもない入力は既存 validator の exact tuple 検査で拒否。
5. outer canonical 検査と `DecodedHistoricalCampaignLock` の構築は共有する。

これにより、未知入力を exact-24 として受理する fallback にはならない。wire 順序は sorted tuple、返却 authority と epoch の順序は記録時の宣言 tuple、という既存の区別を維持する。

## 2. artifact_admission.py の変更計画

対象は [artifact_admission.py][admission]。**追加が必要なのは分岐 2 箇所だけではなく、epoch の構築時検査も含む。**

| 位置 | 変更 |
|---|---|
| scope 定数群 `:84–92` の後 | `T733_EXACT62_CAMPAIGN_VERIFIER_EPOCH_SCOPE` と対応する `EXCLUDED_SCOPE` を独立文字列として追加。 |
| `HistoricalCampaignVerifierEpoch:217–238` | exact-24 の既定値を保持。許可する `(identity_scope, excluded_scope)` の組に exact-62 の組を追加する。各 field を独立に許可して混成を通さない。 |
| `_RecordedCampaignVerifierEpoch.__post_init__:275–282` | 歴史型を無条件に exact-24 とする処理を変更。歴史 scope の組に対応する exact-24／exact-62 tuple と blob map 順序を照合する。通常型は現行 tuple のまま。 |
| `_verify_committed_loader_binding:1009–1017` | 歴史専用型、かつ記録 tuple が exact-24 **または exact-62** の場合に、明示 path 版の検証関数へ渡す。 |
| `_recorded_campaign_verifier_epoch:1067–1079` | exact-24 分岐を保持し、exact-62 の `elif` を追加。新 scope を明示指定して `HistoricalCampaignVerifierEpoch` を構築する。 |
| docstring `:1036–1038`、`:1132` | exact-62 も歴史 scope で返す旨に更新。 |

経路は次のとおり。

`HISTORICAL_RAW` → 専用 decoder → exact-62 authority → 記録 commit の全 62 blob 照合 → 記録順による epoch → `HistoricalCampaignVerifierEpoch` → `HistoricalCampaignView`。

`_decode_campaign_lock_for_purpose:986` の exact enum 判定、`_require_verifier_epoch_for_purpose:1103` の歴史型拒否、`CertifiedCampaignView.__post_init__:427` の exact 通常 epoch 型要求は維持する。

epoch digest は既存 `:1061–1065` の式を変えない。

`SHA256(domain || Σ(path UTF-8 || NUL || digest bytes))`

scope は対応する診断 field に固定する。**scope 文字列を hash preimage に追加する変更はしない**。それは exact-24 の既存 epoch bytes を変えてしまう。

## 3. exact-62 scope 文面の根拠

一次資料は以下。

- `a94ba713b:orchestrator/campaign/artifact_admission.py:73–83`：62 path 導入時の scope / excluded scope の実コード。
- [docs/decisions.md:50607][decisions]、D1650：既存 24＋明示 import 先 36＋package 初期化 2 の収載。
- 同 `:50633`、D1651：推移閉包ではないこと、未収載数、非 import 委譲の除外、完全性を主張しないことを明記する裁定。

新定数は記録時の文面を独立 literal として保存する。

**identity_scope**

> enforcement source closure (curated exact 62 path; 2026-09-01 の静的 import 発見集合 131 module のうち、既存 24、明示 import 先 36、実行時 package 初期化 2 を収載; source-import 推移閉包ではない)

**excluded_scope**

> 同発見集合の未収載 69 module、orchestrator/verifier/__main__.py、orchestrator/verifier/cli.py、package 外の orchestrator/verify.py、および data/schema、生成物、subprocess、外部 command/Git、toolchain、binary、動的 import を含む非 import 委譲は本 map の外であり、完全性を主張しない

現行 scope 定数も現在はこの文面だが、そこへの alias にはしない。T-2482 で現行文面が変わっても歴史 scope が変化しないようにする。現行定数そのものは本件で訂正しない。

## 4. committed blob 検証関数の確認

[contract_loader_binding.py:577][binding] の `verify_committed_contract_loader_blobs` は、引数 `relative_paths` をそのまま `_iter_blobs` に渡し、返された各 blob の SHA-256 と記録 map を照合する。**現行 63 path 固定ではなく、exact-62 にそのまま使える。変更不要。**

一方、`ContractLoaderBinding.__post_init__:67` → `_validate_blob_sha256s:81` は現行閉包に固定されている。exact-62 を `binding_from_authority:597` に流してはいけない。

grammar の whitelist は codec が担い、ここには検証済みの記録 tuple を渡す。62 path の一部だけを渡す処理にはしない。

## 5. 既存の否定側テスト棚卸し

対象は [test_campaign_lock_codec.py][codec-tests] と [test_artifact_admission.py][admission-tests]。

| テスト・位置 | 使用 grammar | exact-62 追加後 |
|---|---|---|
| `test_historical_decoder_rejects_unknown_blob_map_grammars:182` `[subset]` | exact-24 から末尾を削除した 23 | 未知のまま |
| 同 `[superset]` | exact-24＋worker の 25 | 未知のまま |
| 同 `[same-count-replacement]` | exact-24 の末尾を worker に置換した 24 | 未知のまま |
| `test_historical_decoder_rejects_reordered_blob_map_wire_keys:202` | exact-24 の wire 先頭 2 key を交換 | 未知のまま |
| `test_unknown_pre_t733_grammar_is_rejected_for_both_read_purposes:1815` | 上記と同じ subset／superset／置換／順序交換 | 全 parameter が未知のまま |

通常 decoder の閉包拒否テストも確認した。

| テスト・位置 | 判定 |
|---|---|
| `test_pre_t733_exact_24_remains_rejected_by_normal_decoder:168` | 歴史側では既知。通常側の拒否を維持。 |
| `test_v2_rejects_extra_authority_and_blob_keys:264` | blob 側は現行 63＋`extra.py` の 64。未知のまま。 |
| `test_v2_rejects_each_missing_enforcement_source_blob_key:278` | 現行 63 から各 1 path を削除。**worker 削除 parameter だけは exact-62 になる。** |
| `test_v2_rejects_legacy_exact_two_source_blob_keys:290` | 2 path。未知のまま。 |
| `test_v2_rejects_pre_wave_exact_twelve_source_blob_keys:307` | 12 path。未知のまま。 |
| admission の `test_p4_same_pre_t733_exact_24_bytes_are_rejected_for_certified_use:1789` | 既知の歴史 grammar に対する certified 拒否。維持。 |

**差し替え必須の既存テストはない。** `test_v2_rejects_each_missing_enforcement_source_blob_key[verify_fanout_worker.py]` は「歴史側でも未知」とは主張しておらず、通常 decoder の exact-62 拒否を守る重要な parameter なので残す。

新しい歴史側 superset テストでは、exact-62 に worker を足すと既知の現行 63 になるため使わない。代わりに `unknown.py` を追加し、各候補が既知 3 wire tuple のいずれとも異なることをテスト内で確認する。

## 6. 合成 fixture と追加テスト

codec fixture は `test_campaign_lock_codec.py:59` の `_pre_t733_v2_value()` と同型の `_t733_exact62_v2_value()` を追加する。現行 fixture の blob map を独立 exact-62 tuple で投影し、canonical JSON にする。

admission fixture は `test_artifact_admission.py:474` の committed fixture repo と、`:526` の書換 helper の形を踏襲する。新 helper は **テスト内だけで** exact-62 の合成 lock を作る。

[campaign_lock_test_support.py:23][support] は現行 v2 の土台作成に利用できる。ただし `ContractLoaderBinding` と encoder は現行固定なので、62 map を渡すようには変更しない。現行 fixture 作成後の JSON 投影を用いる。実 3 本のコピー・書換えは行わない。

追加する node 候補は以下。

| 配置 | 新設 node | 主張 |
|---|---|---|
| codec `:149` 付近 | `test_t733_exact62_uses_dedicated_historical_decoder_type` | text／bytes 入口、専用返却型、記録 tuple・map 順序、original text、通常 activation validator との型境界 |
| codec 同所 | `test_t733_exact62_remains_rejected_by_normal_decoder` | 同じ canonical bytes を通常 decoder が拒否 |
| codec `:178` 付近 | `test_t733_exact62_rejects_unknown_grammars` | subset 61、未知 path 追加 63、同数置換 62、wire 順序交換を拒否 |
| codec 同所 | `test_t733_exact62_authority_requires_exact_declared_order` | authority 直接構築でも未知 tuple・順序違い・map 順序違いを拒否 |
| admission `:1751` 付近 | `test_t733_exact62_is_readable_only_as_recorded_historical_epoch` | 専用 epoch 型、記録順の期待 digest、固定 scope 文面、unknown、lock/WAL bytes 不変、live closure 非依存 |
| admission 同所 | `test_t733_exact62_is_rejected_for_certified_use` | `require_admitted_campaign`、lock-only epoch API、`classify_campaign` が codec 段で拒否 |
| admission `:1815` 付近 | `test_unknown_t733_exact62_grammar_is_rejected_for_both_read_purposes` | 未知 4 種を両目的で拒否。後段の blob 不一致を grammar 拒否の代用にしない |
| admission `:1854` 付近 | `test_t733_exact62_rejects_each_recorded_commit_blob_mismatch` | **62 path 全件を parameter 化**し、各 digest を 1 桁変えて committed mismatch を要求 |
| admission epoch テスト付近 | `test_t733_exact62_epoch_requires_matching_scope_and_paths` | 歴史 scope 混成、exact-24 scope＋62 map、62 scope＋24 map を拒否 |

期待 tuple・期待 epoch は production の新定数だけから生成せず、記録 commit 由来の独立した期待列で固定する。既存 exact-24 テストの期待値は変更しない。

これらは**実装後に実行する候補**であり、本段で実走した結果ではない。

## 7. repo 内 consumer と影響

実行コードの直接参照は次の全件。文書・過去の変異ログ中の引用は実行 consumer に含めない。

| consumer | exact-62 が来た場合 |
|---|---|
| `campaign_lock.py:753–763` bytes wrapper | 新しい text decoder 分岐へ委譲し、専用型を返す。 |
| `campaign_lock.py:368–379` current authority 投影 | 現行 grammar の処理は不変。 |
| `campaign_lock.py:382–424` exact-24 authority 構築、および `:232` 型参照 | 既存経路は不変。62 は兄弟関数が構築する。 |
| `artifact_admission.py:976–995` decoder wrapper／目的別 dispatch | 歴史目的だけ新たに decode 成功する。 |
| `artifact_admission.py:1054` authority 型による記録 tuple 選択 | exact-62 の記録 tuple が epoch 計算へ流れる。上述の scope・map 検査変更が必要。 |
| [b10_backoff_shape_sweep.py:3131][shape] `_assert_report_lock_binding` | decoder は成功するようになるが、`:3135–3139` の **exact-24 専用条件で拒否を維持**。先行する campaign ID／lock digest 条件も維持。 |
| [b10_backoff_static_tail_formal.py:351][static] `load_explore_correctness_mode` | 中央歴史 admission を通過した 62 lock は `:354` の `run_kind == "t2418-explore"`、続く workload 条件まで進む。grammar による一律拒否から、既存の用途条件による判定へ変わる箇所。 |

直接 decoder を呼ぶテスト consumer は以下。

- `test_campaign_lock_codec.py:152,199,217`。
- `test_b10_backoff_shape_sweep.py:2537`。

B10 のコード変更は不要。既存 exact-24 snapshot の回帰確認対象は `test_report_lock_identity_accepts_exact_pre_t733_real_snapshots:2532`、`test_run_formal_report_reaches_locked_collection_and_writer_without_live_inputs:2875`。static-tail は `test_probe_5_explore_mode_and_formal_report_comparison:394`。

なお、shape の仮想 exact-62 入力は、拒否理由が「歴史 schema 不正」から「pre-T733 v2 が必要」へ進み得る。既存 exact-24 入力の挙動は変えない。

「bytes 不変」は既存 lock/WAL・歴史 epoch・B10 の既存成果物について守る。一方、admission の `validator_sha256` は `artifact_admission.py:1252` 付近で自身のファイル bytes から計算されるため、**変更後に新しく生成する admission receipt 全体まで旧 bytes と一致するとは主張できない**。この既存 provenance 機構は変更しない。

## 8. 変異事前登録候補

以下は変異と落ちるべき node の対。新設 node は前節の名前を使う。

| 何を変異させるか | 落ちるべきテスト |
|---|---|
| exact-62 decoder 分岐または authority whitelist 追加を削除 | codec の `test_t733_exact62_uses_dedicated_historical_decoder_type` |
| 62 literal の 1 path を置換、または宣言順を交換 | 同正例の独立期待 tuple、および admission 正例の期待 epoch |
| wire tuple 一致を同数判定／subset 判定に緩和 | `test_t733_exact62_rejects_unknown_grammars[same-count-replacement]`／`[superset]` |
| authority の tuple 順序検査を集合比較に変更 | `test_t733_exact62_authority_requires_exact_declared_order` |
| 62 の committed 検証を省略、または末尾 path を除外 | `test_t733_exact62_rejects_each_recorded_commit_blob_mismatch` の該当 path parameter |
| 62 epoch を通常 `CampaignVerifierEpoch` で返す | admission の `test_t733_exact62_is_readable_only_as_recorded_historical_epoch` |
| epoch の入力順を sorted wire 順へ変更 | 同正例の独立期待 epoch |
| 62 scope に exact-24 scope を指定、または scope と map の対応検査を緩和 | 同正例、および `test_t733_exact62_epoch_requires_matching_scope_and_paths` |
| certified decode 失敗時に歴史 decoder へ fallback | `test_t733_exact62_is_rejected_for_certified_use`。codec 段の拒否を要求するため、後段拒否でも検出 |
| 通常 decoder を exact-62 受理へ緩和 | `test_t733_exact62_remains_rejected_by_normal_decoder`、既存 `test_v2_rejects_each_missing_enforcement_source_blob_key[verify_fanout_worker.py]` |
| exact-24 の scope／epoch 順序を変更 | 既存 `test_p3_pre_t733_exact_24_is_readable_only_as_recorded_historical_epoch` |

wire 順序検査を集合比較へ変える**単独変異**は、後段の canonical JSON 検査でも拒否されるため、生存する可能性がある。順序拒否の end-to-end テストと、authority 直接構築の順序テストを分け、冗長検査による生存を成功と取り違えない。

## 総括

独立 exact-62 literal と兄弟 validator を追加し、既存 2 module 内で歴史専用型・scope・全 62 blob 検証を接続する。  
通常 decoder／encode／resume／certified の受理条件と、exact-24 の既存期待値は維持する。  
最大の risk は epoch 側の exact-24 固定検査を見落とし、decode 成功後に拒否または scope 誤表示を起こすこと。  
静的調査のみ完了。実 3 本の読取り確認と新設テスト実走は、実装後の親側検証に残る。

[codec]: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2483-exact62-historical-grammar/orchestrator/campaign/campaign_lock.py:118
[admission]: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2483-exact62-historical-grammar/orchestrator/campaign/artifact_admission.py:217
[binding]: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2483-exact62-historical-grammar/orchestrator/campaign/contract_loader_binding.py:577
[decisions]: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2483-exact62-historical-grammar/docs/decisions.md:50607
[codec-tests]: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2483-exact62-historical-grammar/orchestrator/tests/test_campaign_lock_codec.py:149
[admission-tests]: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2483-exact62-historical-grammar/orchestrator/tests/test_artifact_admission.py:1751
[support]: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2483-exact62-historical-grammar/orchestrator/tests/campaign_lock_test_support.py:23
[shape]: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2483-exact62-historical-grammar/orchestrator/campaign/b10_backoff_shape_sweep.py:3131
[static]: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2483-exact62-historical-grammar/orchestrator/campaign/b10_backoff_static_tail_formal.py:351