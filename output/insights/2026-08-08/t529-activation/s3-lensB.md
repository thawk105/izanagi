静的レビューの結論は **NO-GO** です。must-fix は 6 件です。read-only で確認し、ファイル変更・pytest 実行はしていません。`MappingProxyType` についてのみ、project test ではない最小の Python 言語レベル確認を行いました。

### 1. activation head が reviewed commit に機械的に束縛されていない

深刻度: **must-fix**

根拠:

- 確定裁定は trust root を「レビュー済み commit」としていますが、これは現在プランでは運用上の説明だけです。[s1-brief.md:37](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s1-brief.md:37>)、[s2-plan.md:173](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:173>)
- loader は directory 内の chain を検証するだけで、期待する最終 serial/state hash や exact file set を、commit-bound な値へ照合しません。[s2-plan.md:63](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:63>)、[s2-plan.md:79](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:79>)
- hash chain は途中改変には効きますが、正当な serial 2 の未 commit 追加と、末尾 record 削除による正当な prefix への rollback を区別できません。計画中の gap/predecessor test も末尾切詰めを落としません。[s2-plan.md:226](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:226>)
- PBS source binder は `sys.modules` 上の Python module bytes だけを receipt の commit と比較します。JSON record は対象外です。[certified_writer_preflight.py:85](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/certified_writer_preflight.py:85>)、[certified_writer_preflight.py:120](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/certified_writer_preflight.py:120>)
- T126・silo・T419 の pin は一部 consumer を守るだけで、authority loader 自身の trust root にはなりません。[s2-plan.md:247](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:247>)

成果物影響: 未 commit の valid suffix で current が pegasus g1 `e576…` から g2 `1346…` へ変わり floor live admission が拒否され、逆に valid prefix rollback では g2 活性化後の certified 選択・台帳が再び g1 較正へ戻ります。

修正案:

- 安定した単一 path の activation manifest に、期待 head serial/state hash と全 record の `{path, sha256}` を記録する。
- loader は manifest と directory の集合・bytes を双方向 exact で照合し、extra/missing/tail truncation を拒否する。
- manifest 自身を source commit、T126 identity、silo binding、T419 dirty scopeへ束縛する。
- `valid suffix injection`、`valid prefix rollback`、manifest と record の別 commit 混在を専用 test にする。

### 2. receipt gate が最初の書込みへ届く層は一部だけである

深刻度: **must-fix**

根拠:

親 brief は「最初の書込み前」に receipt を assert するとしていますが、段2プランの変更先は `execution_guard.require_certified_writer_authorization()` だけです。[s1-brief.md:27](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s1-brief.md:27>)、[s2-plan.md:201](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:201>)

| 入口 | lazy authority 検証 | receipt assert / 漏れ |
|---|---|---|
| floor campaign | `_validate_protocol_against_current()` の `lookup()` で自動被覆。[s8b_floor_campaign.py:2840](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8b_floor_campaign.py:2840>) | claim `:2945`、run dir `:3006` より前の activation receipt assert はない。 |
| oracle driver | `_prepare_v2_execution()` の `lookup()` で自動被覆。[s8b_oracle_driver.py:770](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8b_oracle_driver.py:770>) | G12 claim `:1201`、campaign/session/budget `:1224-1242` は最初の `pipeline.evaluate()` より前で、計画の guard を通らない。 |
| scoping | Python 計測は `_assert_matches_calibration()` の `lookup()` で被覆。[pegasus_floor_scoping.py:201](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/pegasus_floor_scoping.py:201>) | Python out-dir 作成 `:104-123` と PBS の TMPDIR/out/provenance 作成は先行する。[floor_scoping.sh:37](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/tools/pegasus/floor_scoping.sh:37>) ただし現契約は certified consumer 非接続です。[pegasus_floor_scoping.py:2](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/pegasus_floor_scoping.py:2>) |
| T-126 | PBS preflight `lookup()` と driver `lookup()` は自動被覆。[certified_writer_admission.py:370](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/certified_writer_admission.py:370>)、[t126_driver.py:869](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/qualification/t126_driver.py:869>) | attestation child は `create_json()` で書くが activation receipt を再検証しない。[t126_driver.py:1125](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/qualification/t126_driver.py:1125>) member の guard は後段 `pipeline.evaluate()` 内。 |
| silo | driver の環境検査は `lookup()` で被覆。[silo_ladder_rung1.py:1933](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/silo_ladder_rung1.py:1933>) | PBS wrapper は lookup 前に staging を書く。[silo_ladder_rung1.sh:60](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/tools/pegasus/silo_ladder_rung1.sh:60>) 昇格入口未実装という確定裁定のため、これを promotion gate 実装済みとは扱えない。 |
| selector | direct import はないが、`seal()` → `_derive_protocol_bytes()` → `build_protocol_document()` → `lookup()` で間接的に current activation が効く。[s8b_prediction_runner.py:1457](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8b_prediction_runner.py:1457>)、[s8b_floor_campaign.py:491](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8b_floor_campaign.py:491>) | journal/prediction 作成前ではあるが activation receipt assert はない。[s8b_prediction_runner.py:1505](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/s8b_prediction_runner.py:1505>) |
| P3 | `run_campaign()` が guard を layout 作成前に通し、`pipeline.evaluate()` も再検査するため certified measurement は自動被覆。[loop.py:131](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/loop.py:131>)、[pipeline.py:595](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/pipeline.py:595>) | 被覆済み。前段の exploration reject/checkpoint は certified sink ではない。 |
| PBS wrapper | floor/T126 は static preflight の lookup が最初の shell mutation より前。[floor_campaign.sh:29](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/tools/pegasus/floor_campaign.sh:29>)、[t126_qualification.sh:63](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/tools/pegasus/t126_qualification.sh:63>) | receipt を持つ Python preflight process と実際に書く shell process は別。scoping/silo wrapper にはこの preflight 自体がない。 |

成果物影響: T126 の fork child は親 PID の snapshot を再検証せず attestation JSON を書け、floor/oracle/selector も新 receipt 条件を構造的に通らないため、台帳・budget・prediction の受理集合が「全入口で activation receipt 済み」という報告と一致しません。

修正案:

- floor・oracle・selector は current contract 解決直後、最初の副作用前に共通 activation receipt assertion を置く。
- T126 は controller の最初の成果物書込み前と、書込みを行う fork child の双方で PID-bound receipt を再取得・assertする。
- floor/T126 static admission では manifest/head 検証と receipt assertionを明示し、成功 exit を shell gate として固定する。
- scoping は現状どおり non-certified、silo は no-promotion と明示して scope 外にするかを裁定パッケージへ返す。
- 「receipt と writer が同一 process でなければならない」という解釈なら、現在の PBS subprocess 構造では実現不能なので、ここだけは**ユーザー再裁定が要る**。durable receipt をこの wave に入れる提案ではない。

### 3. PID 判定だけでは fork/thread cache が安全にならない

深刻度: **must-fix**

根拠:

- プランは mutex 内で PID mismatch を検出して再ロードする構想です。[s2-plan.md:139](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:139>)
- 別 thread が mutex を保持した瞬間に fork すると、child は解除できる thread のない locked mutex を継承します。PID を mutex 取得後に見る設計では永久待ちになります。
- T126 には lookup 後に fork する実経路があります。[t126_driver.py:496](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/qualification/t126_driver.py:496>)、[t126_driver.py:509](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/qualification/t126_driver.py:509>)
- test collection 時点で lookup する module が既に二つあります。[test_campaign.py:79](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_campaign.py:79>)、[test_screening_driver.py:37](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_screening_driver.py:37>)。conftest 自身も fixture より module import が先だと明記しています。[conftest.py:46](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/conftest.py:46>)

成果物影響: fork child の停止は T126 attempt ledger を未完にし、本来受理可能な trial を受理集合から脱落させ、collection 済み cache の汚染は誤った current/ever-active 実装を acceptance が見逃す原因になります。

修正案:

- `os.register_at_fork(after_in_child=...)` などで child の lock・PID・cache・receipt を、lock 取得前に再初期化する。
- snapshot は activation・current map・ever-active・receipt の全検証完了後に一括 publishする。
- 「別 thread が lock を保持した状態で fork」する決定的 test を追加する。
- authority state を差し替える fixture は cache を前後で clearし、`monkeypatch` teardown 後にも temp snapshot が残らない順序を明示する。
- import-I/O test は既に import 済みの test process ではなく fresh subprocess で行う。

### 4. identity pin は依存閉包が不足し、record を直接 path set に足す方式は履歴検証を壊す

深刻度: **must-fix**

根拠:

- プランが挙げた三箇所の行位置・構造は実在します。T126 は exact static set、silo は runtime module list、T419 は `git status -- ...related` です。[contract.py:38](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/qualification/contract.py:38>)、[silo_ladder_rung1.py:254](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/silo_ladder_rung1.py:254>)、[t419_probe_causality.py:3491](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/tools/pegasus/probes/t419_probe_causality.py:3491>)
- 現 T126 set は `env_contract.py` を含みますが、新たに意味を持つ `execution_guard.py`、`env_contract_activation.py`、`calibration_verify.py` とその `schema_v2.py` / `effective_clock_policy.py`、さらに `env_attestation.py` / `site_policy.py` / `tsc.py` を含みません。[contract.py:59](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/qualification/contract.py:59>)、[execution_guard.py:21](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/execution_guard.py:21>)
- preimage validator は key set を現在の `REQUIRED_CODE_IDENTITY_PATHS` と exact 比較します。[contract.py:518](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/qualification/contract.py:518>)
- historical verifier も、記録時 commit の set ではなく現在の定数を要求します。[identity.py:130](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/qualification/identity.py:130>)。したがって record 追加ごとに path set を増やすと、旧 series preimage はその時点で検証不能になります。
- 「calibration verification の実 dependency」とだけ書くのは実装可能な列挙になっていません。[s2-plan.md:247](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:247>)

成果物影響: pin 漏れでは activation/receipt 実装を変えても同じ `qualification_series_id` が出得る一方、record path の追加では既存 T126 ledger の series identity が将来 verifier から参照不能になります。

修正案:

- activation record を全て top-level identity key にせず、安定 path の manifest digest で閉包する。
- manifest は全 record hash と headを束縛し、historical verifier は記録 commit にある manifestと record blobs を検証する。
- activation追加時に source identityの**値が変わること自体は意図した正しい挙動**。変えるべきでないのは identity schemaの path集合です。
- T126 には少なくとも activation leaf/manifest、calibration verifier依存、変更される execution guard とその実行依存を追加する。
- silo の runtime list と T419 の directory dirty scope 追加は方向として正しい。

### 5. silo の「歴史 evidence」は将来の current g2 を参照して壊れる

深刻度: **must-fix**

根拠:

- test は historical runtime binding を current と一致させないことを明示しています。[test_silo_ladder_rung1_evidence.py:1249](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1249>)
- その直後に `env_contract.lookup("pegasus")` を呼び、歴史 evidence の calibration path/hash/contract hash が**現在値**と一致することを要求しています。[test_silo_ladder_rung1_evidence.py:1262](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1262>)
- プランは silo evidence を変更しないとしています。[s2-plan.md:251](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:251>)
- production の `validate_current_bindings()` は live/current 用なので、こちらを historical resolver に変えてはいけません。[silo_ladder_rung1.py:3512](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/silo_ladder_rung1.py:3512>)

成果物影響: serial 2 で g2 を活性化した瞬間、committed g1 silo evidence の calibration参照が不正扱いとなり、patch ledgerからの歴史参照が切れます。

修正案:

- historical evidence 側だけ、`binding["calibration"]["contract_sha256"]` を `resolve_by_contract_sha256(..., expected_env_tag="pegasus")` で解決する。
- path/hashも解決した歴史 contract と記録 binding に照合する。
- `validate_current_bindings()` は current gate のまま維持する。
- 成果物 bytes は変更せず、再検証ロジックと testだけを直す。

### 6. テスト表の一部は名前どおりの誤実装を落とさない

深刻度: **must-fix**

根拠:

[s2-plan.md:216-239](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:216>) の各 nodeid を静的に照合した結果です。

| nodeid（短縮） | 判定 |
|---|---|
| `generation_golden_has_exact...` | 有効。g1/g2 の exact tuple を固定する場合。 |
| `validate_generations_accepts_registered_g2` | suite-level では有効。fuse が残れば module import 自体が赤になり、nodeidまで到達しない。 |
| `registry_and_lookup_follow_activation...` | 条件付き有効。REGISTRY/cacheをpatchせず、実 initial record g1 と実 tail g2を比較する必要がある。 |
| `registered_g2_calibration...accepted` | 有効。実 bytesを読むことが条件。 |
| `resolver_rejects_registered_never_active_g2` | 条件付き有効。実 initial chainを使い、resolver/indexをpatchしないこと。 |
| `activation_leaf_is_stdlib_only...` | AST依存検査には有効。import時I/Oは検出しない。 |
| `initial_record_is_exact...` | 有効。 |
| `record_rejects_duplicate...` | 列挙ケースには有効。 |
| `chain_rejects_gap...symlink` | 不十分。正当 prefixへのtail rollbackとvalid suffix注入は落とさない。 |
| `transition_rejects_noop...` | 有効。 |
| `real_g2_serial2...switches_lookup` | 条件付き有効。既存のようにREGISTRYを直接patchすると永久 fuseを殺せない。 |
| `serial2_preserves_g1_as_ever_active` | 有効。 |
| `import_performs_no...io` | 同一test processでは無効。collection前lookup済みなのでfresh subprocess必須。 |
| `authority_validation_is_cached_once_per_pid` | 不十分。通常forkではlocked-mutex継承を検出しない。 |
| `forged_stale_cross_process_receipts...` | seal生成経路をpatchしないなら有効。 |
| `issue_cli_parses_before_load...` | parse順/O_EXCLには有効。reviewed-commit/head束縛は検出しない。 |
| `m0_activation_receipt_refusal...` | generic pipelineだけ。floor/oracle/T126/PBSの漏れは検出しない。 |
| `activation_receipt_check_precedes...` | 同上。guard内順序だけ。 |
| `public_reverify_rejects_never_active...` | 実 authority chainを通せば有効。resolver mockだけなら弱い。 |
| `public_reverify_accepts_g1...` | 実 serial2を通せば有効。 |
| `build_observations_rejects_never_active...` | 実 resolver/cacheを通せば有効。 |
| `build_observations_accepts_ever_active_g1...` | 実 serial2を通せば有効。 |

既存テスト置換にも検出力低下があります。

- bootstrap fuse 専用 testの削除自体は、新しい実 g2 import/serial2 testがproduction seamを通れば妥当です。[test_env_contract.py:541](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_env_contract.py:541>)
- module-level structural validation の順序検査は残す必要があります。[test_env_contract.py:558](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_env_contract.py:558>)
- 現 historical testの resolver call回数・contract object伝播・live refusal理由のassertは、単なる「g1を受理」に縮めてはいけません。[test_s8b_ratified_verify.py:725](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_s8b_ratified_verify.py:725>)
- 既存 synthetic fixture は `GENERATIONS`、`REGISTRY`、indexを同時patchしており、新loaderの誤りを迂回します。[test_s8b_floor_campaign.py:4395](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_s8b_floor_campaign.py:4395>)

成果物影響: この表のままではtail rollback、locked-fork、入口receipt欠落がacceptanceを通り、g2の誤選択やactivation未確認のfloor/oracle/T126台帳をland後に許します。

修正案:

- commit-bound head の suffix注入/tail rollback testを追加。
- import testをfresh subprocess化。
- mutex保持中fork testを追加。
- floor・oracle・T126・floor/T126 PBSそれぞれに「receipt refusal時は最初の書込みゼロ」を置く。
- activation integration testはdirectory/root/cacheだけを操作し、`REGISTRY`やresolver結果を直接patchしない。
- 既存 historical testの call-count、object伝播、no-fallback、reason検査を保持する。

### 7. repo root 解決の対応範囲が未定義

深刻度: **should-fix**

根拠:

- `calibration_verify` は明示された `repo_root` を strict resolveし、その配下だけを読む契約です。[calibration_verify.py:81](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/calibration_verify.py:81>)
- 既存の `Path(__file__).resolve().parents[2]` は cwd非依存で、通常worktreeとT126 source-stageには適合します。[pegasus_floor_scoping.py:70](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/pegasus_floor_scoping.py:70>)
- repo内に wheel/install copy用の packaging manifestはなく、installed copyでは `output/...calibration` とactivation directoryを同じ相対位置に期待できません。
- 段2プランはauthority cacheへ渡すrootの導出方法を固定していません。[s2-plan.md:137](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:137>)

成果物影響: installed copyでは初回lookupがfail-closedとなり、certified選択・report・ledgerが生成されない一方、worktree/cwd変更では正しく実装すれば値のdriftは起きません。

修正案:

- 本waveの対応対象を「source checkout/worktree/source-stageのみ」と明記する。
- rootはcwdから導出せず、`__file__`基準とsentinel検査で固定する。
- 任意cwd、別worktree、git-archive source-stage、shadow/installed copy拒否をテストする。
- installed copyを支援するなら、root注入またはmanifest/calibrationのbundle設計を別途定める。

### 8. lazy `MappingProxyType` 自体は成立するが、公開操作契約のtestが足りない

深刻度: **should-fix**

根拠:

- productionで `REGISTRY` を直接操作するのは `env_contract.py` 内の `sorted(REGISTRY)` と `.values()`だけです。[env_contract.py:383](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:383>)、[env_contract.py:393](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/campaign/env_contract.py:393>)
- repo全体検索では、production module直下で `REGISTRY` を触るconsumerはありません。module直下の `lookup()` は前述のtest 2本だけです。
- 現testは iteration/set/items とread-only性を使います。[test_env_contract.py:376](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_env_contract.py:376>)、[test_env_contract.py:666](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-activation/orchestrator/tests/test_env_contract.py:666>)
- `collections.abc.Mapping` 実装を `MappingProxyType` で包む最小言語probeでは iteration、`.values()`、`in`、`len`、`sorted`、`.items()`はいずれも委譲され、`isinstance(..., MappingProxyType)`も維持されました。project testの結果ではありません。

成果物影響: view実装がMapping契約を外すとrequired-attestation候補数やunknown-env一覧が変わり、正しいcertified入力まで拒否されます。

修正案:

- `_ActivationRegistryView` を正式に `collections.abc.Mapping` として実装する。
- 上記6操作、順序、同一snapshot、read-only、未知keyを一つの互換testで固定する。
- 各操作がauthority loadを一度だけ起動することも確認する。

### 9. 親A/B案もプランA〜D案も所有分割として成立していない

深刻度: **should-fix**

根拠:

- 親A/B案は形式上逐次ですが、Aがauthority全体とissuerを持ち、Bが全testを持つためA単体を受理できません。またfloor/oracle/T126/PBSの追加配線ファイルを所有していません。[s1-brief.md:92](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s1-brief.md:92>)
- プラン単位Aはissuerを所有しますが、issuerは単位Bが実装するauthority loaderを呼ぶため依存が逆流します。[s2-plan.md:169](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:169>)、[s2-plan.md:260](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:260>)
- `test_env_contract_activation.py` はAのleaf testとBのcache/serial2 integration、issuer testを同居させる計画で、所有が重なります。[s2-plan.md:224](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t529-activation/s2-plan.md:224>)
- BとDも `test_env_contract.py` とstatic closure検査を共有します。

成果物影響: 競合patchでhead manifest、entry receipt、identity pinのいずれかが脱落すると、g2誤選択または同一series IDへの意味論混入をland時に見逃します。

修正案:

第三案を推します。依存順は `1 → 2 → (3,5)`、`3 → 4` とします。

1. activation pure leaf専有: `env_contract_activation.py` と純粋leaf test。
2. authority専有: `env_contract.py`、manifest/records、issuer、authority integration test。
3. generic/floor/oracle/selector/PBS admission専有: `execution_guard.py`、各driver、`certified_writer_admission.py`、preflight/wrapper、対応test。
4. T126・identity専有: `t126_driver.py`、qualification contract/identity、T126 test。
5. silo/T419/historical専有: silo runtime binding、historical evidence test、T419 probe/test。

新test fileをleaf・authority・entryで分離し、既存test fileも各単位へ一意に割り当てます。

## 総括

1. **判定: NO-GO**
2. **must-fix: 6件**
   - reviewed commitへactivation headが束縛されず、suffix注入・tail rollbackが可能。
   - receipt assertionがfloor・oracle・T126・selector・PBSの全書込み境界へ届かない。
   - PID cacheがlocked mutex付きforkとtest collection汚染に耐えない。
   - identity依存閉包が不足し、recordごとのpath set追加が歴史T126検証を壊す。
   - silo historical evidenceが将来のcurrent g2を参照して旧g1を拒否する。
   - テスト表がtail rollback・held-lock fork・入口漏れを検出しない。
3. **実装単位: 第三案を推奨**。親A/B案はscope不足、プランA〜D案はissuer依存逆流とtest所有重複があるため、上記5単位の逐次・素集合分割が妥当です。