# 段 2 実装プラン

結論として、exact 14 への末尾追加は実装可能で、`campaign_lock.py` から verifier package への import 循環も生じない。暫定表外の主な面は、独立 E1 fixture、旧 exact-12 wire の明示拒否、Silo ladder の別系統 hash pin である。

本調査は read-only の静的検査のみ。`git status --short` は空だった。pytest、build、受入は実行しておらず、緑とは報告しない。

## 実装順序

1. DW-M01 に従い、下記の変異と期待 node を段 4 で先に登録する。
2. 単位 Aとして production 3 fileを exact 14 と新 scope 文言へ変更する。
3. 単位 Bとして独立 tuple、fixture、発火実証、wire、epoch 順序テストを更新する。
4. worklog、D442 を supersede する新 D、F357 の supersede 追記を spool fragment に記録する。
5. 統合 commit 後に関連テスト、全受入、docs/Codex/provenance 検査を親が実測する。`artifact_admission.py` は閉包内なので、commit 前の広域赤は F357 の偽赤と切り分ける。

## 完全な編集面

### 実際に編集する file

| file:line | 変更 |
|---|---|
| [campaign_lock.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/campaign/campaign_lock.py:27) | comment を exact 14 にし、行 41 の後へ `orchestrator/verifier/__init__.py`、`orchestrator/verifier/report.py` の順で追加する。既存 12 行は変更しない。 |
| [contract_loader_binding.py:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/campaign/contract_loader_binding.py:2) | 行 2、49–52 の exact 12 / 12 path を exact 14 / 14 path にする。検査コードは変更しない。 |
| [artifact_admission.py:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/campaign/artifact_admission.py:65) | scope と excluded scope を更新する。推奨 scope は `exact 14 path; pipeline.py、verifier dispatch __init__.py、verifier 実装 core/dsg/model/parse/report.py を含む`。excluded は `{__main__,cli}.py` と package 外 `orchestrator/verify.py` だけにする。 |
| [artifact_admission.py:100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/campaign/artifact_admission.py:100) | 行 100–105、717–725、800–810 の docstring を同じ exact 14 境界へそろえる。domain 行 63 は不変。 |
| [test_t671_source_binding.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/tests/test_t671_source_binding.py:22) | 旧実コードを表す独立 `_PRE_WAVE_ENFORCEMENT_SOURCE_PATHS` exact 12 を残し、期待 tuple はそこへ新 2 path を append した独立 exact 14 にする。 |
| [test_t671_source_binding.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/tests/test_t671_source_binding.py:123) | test 名を `exact_fourteen_paths` へ変更し、その直後に §5 の対照テストと clean 正例を追加する。 |
| [test_artifact_admission.py:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/tests/test_artifact_admission.py:44) | `_EXPECTED_E1_CLOSURE_PATHS` へ新 2 path を末尾追加。これにより行 349–360 の独立 epoch golden も 14 path になる。 |
| [test_artifact_admission.py:327](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/tests/test_artifact_admission.py:327) | fixture docstring を exact 14 にする。行 954–960 の逐語 scope、行 1077 の件数を 14 に変更する。 |
| [test_artifact_admission.py:1127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/tests/test_artifact_admission.py:1127) | verifier drift param を 4 file から `__init__.py` / `report.py` を含む 6 file に拡大する。現状でも赤にはならないが、exact 14 の path 単位検出を欠くため必要。 |
| [test_campaign_lock_codec.py:182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/tests/test_campaign_lock_codec.py:182) | legacy exact-2 test の直後へ、独立 literal の旧 exact-12 map が拒否される test を追加する。既存 missing-key param は自動的に 14 case へ増える。 |
| [test_s6_sort_sweep.py:619](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/tests/test_s6_sort_sweep.py:619) | fixture docstring を exact 14 にする。実体は production tuple を動的参照するためロジック変更なし。 |
| [test_s8a_trigger_sweep.py:829](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/tests/test_s8a_trigger_sweep.py:829) | 同じく fixture docstring を exact 14 にする。 |
| `docs/spool/worklog/2026-08-17-dev-wave-t1207-closure-exact14-1.md:1` | T-1207 完了、実測、変異、受入を記録。`remaining: none` と現 item の base digest が必要。 |
| `docs/spool/decisions/2026-08-17-dev-wave-t1207-closure-exact14-2.md:1` | 新 D を立て、D442 決定 1・3と dispatch/report 未閉包という制限を supersede。D442 決定 2 と D268 の残る制限は継承する。 |
| `docs/spool/failures/2026-08-17-dev-wave-t1207-closure-exact14-3.md:1` | `## supersede 追記` で F357 の「12 path」を「14 path」へ読み替える。commit 後切分け規律は維持する。 |

`orchestrator/verifier/__init__.py` と `report.py` 自体は編集しない。発火テストでは一時 repo のコピーだけを変える。

### `CONTRACT_LOADER_RELATIVE_PATHS` 全参照

source/test/tools/hooks の全件検索で、識別子を持つのは次の 12 fileだけだった。

- Production: `campaign_lock.py:29,174,183`、`contract_loader_binding.py:15,73,78,329,348,372`、`artifact_admission.py:175,740,744`。
- Test: `campaign_lock_test_support.py:18`、`test_artifact_admission.py:1280–1611`、`test_bench_first_real_wal.py:166–172`、`test_campaign_lock_codec.py:45,167,229`、`test_env_contract_activation.py:307`、`test_layer3_report.py:62`、`test_s6_sort_sweep.py:624–630`、`test_s8a_trigger_sweep.py:834–840`、`test_t671_source_binding.py:126–221`。
- 定数を直接 import するのは [contract_loader_binding.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/campaign/contract_loader_binding.py:15) だけ。他は `campaign_lock` 経由である。

このうち `campaign_lock_test_support.py`、bench、env activation、layer3 report は production tuple から動的生成するため編集不要。ただし受入対象である。

scope 定数の参照は production 定義に加え、`s8b_oracle_report.py:390,393` と `test_s8b_oracle_report.py:795,796` の動的参照だけである。逐語を二重管理する test は `test_artifact_admission.py:954–960` のみ。

closure 関連の逐語「12」は上表の production docstring/comment、T671 test 名、artifact fixture/scope/count、S6/S8a fixture に限られる。`test_s8b_oracle_driver.py` の `exact 12/51` と T080 の 63/12/51 は別の S1 closure なので変更しない。D442、F357、archive worklog は歴史記録なので in-place 書換えせず、新 D と supersede 追記で更新する。

### 他 wave 由来の hash pin

暫定表外では Silo ladder が新 2 fileをすでに別閉包で束縛している。

- [silo_ladder_rung1.py:262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/campaign/silo_ladder_rung1.py:262) は `verifier.rglob("*.py")` により `__init__.py` と `report.py` の両方を `runtime_modules_sha256` に含める。
- `report.py` はさらに同 file の 2452–2456、3551–3563、4460–4475、4593–4599 と [submit_silo_ladder_rung1.sh:287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/tools/pegasus/submit_silo_ladder_rung1.sh:287) の `verifier_module_sha256` で個別束縛される。
- [test_silo_ladder_rung1_driver.py:927](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/tests/test_silo_ladder_rung1_driver.py:927) が verifier tree 全体を pin する。
- [test_silo_ladder_rung1_evidence.py:80](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/tests/test_silo_ladder_rung1_evidence.py:80) の `e604...` は歴史的 report hash で、現行 bytes と異なること自体が期待値である。

識別子 key と現行 SHA-256 の双方で検索したが、現行 `__init__.py` の `9f7f4b...4602`、`report.py` の `59b1e8...fd5e` を逐語固定する別 pin は無かった。今回は両 fileの実 bytes を変更しないため、Silo pin や歴史 golden は更新しない。最終 diff に両 fileが入っていたら事故として止める。

## 末尾追加の順序と epoch / wire / golden

epoch preimage は [artifact_admission.py:742](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/campaign/artifact_admission.py:742) の次の順序になる。

`domain || old-path-1 || NUL || digest-1 || ... || old-path-12 || NUL || digest-12 || __init__.py || NUL || digest-13 || report.py || NUL || digest-14`

したがって既存 12 segment の綴りと順序は完全な prefix として保存される。新 digest は必ず再計算され、表示 prefix は `E1:`、domain は `campaign-verifier-epoch/v1` のままである。

wire は別で、[campaign_lock.py:127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/campaign/campaign_lock.py:127) が `sort_keys=True` を使う。このため canonical JSON 上では `__init__.py` は verifier key の先頭側、`report.py` は `parse.py` の後へ並び、tuple の「末尾追加」はそのまま wire の末尾順にはならない。意味上の既存 12 key/value は不変だが、wire bytes は旧 wire の byte prefix ではない。

[ campaign_lock.py:171–184 ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/campaign/campaign_lock.py:171) の exact key 比較により、受理言語は exact 12 から exact 14 へ置換される。旧 12、13、15 key map は拒否される。

独立 golden は `test_artifact_admission.py:349–360` が tuple 順と fixture index を再構成する。append なら index 1–12 の bytes は不変、13 が `__init__.py`、14 が `report.py` になる。現行 source/test に固定された完全な `E1:<64hex>` は無く、動的 golden の更新だけでよい。

## import 循環の判定

循環は生じない。

- [campaign_lock.py:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/campaign/campaign_lock.py:9) の import は `dataclasses/json/re/typing` だけで、追加するのは path 文字列である。
- [contract_loader_binding.py:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/campaign/contract_loader_binding.py:319) は文字列を `git cat-file` と disk reader に渡すだけで、`orchestrator.verifier` を import しない。
- [pipeline.py:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/campaign/pipeline.py:31) から verifier package を importする向きは従来どおり campaign → verifier。
- [verifier/__init__.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/verifier/__init__.py:16) は verifier 内部だけを importし、[report.py:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/verifier/report.py:12) も `.model` にしか依存しない。
- campaign package の `__init__.py` に子 module import はない。
- [test_campaign_lock_codec.py:277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/tests/test_campaign_lock_codec.py:277) の import-first sentinel を受入で維持する。

つまり依存は `campaign_lock <- contract_loader_binding` のままであり、閉包 member の path 文字列が package import edge になることはない。

## §5 発火実証テスト

追加先は `test_t671_source_binding.py:123–133` の直後とする。

### fixture 構成

- `_PRE_WAVE_ENFORCEMENT_SOURCE_PATHS`: wave 前に実在した 12 path を独立 literal で保持する。
- `_EXPECTED_ENFORCEMENT_SOURCE_PATHS`: 上の 12 に `__init__.py`、`report.py` を appendした独立 14。
- `_committed_loader_repo(..., copy_current_loaders=True)` は既存の `_git` と Git fixture を再利用できる。期待 tuple を 14 にすれば、新 2 fileも実 bytes のまま一時 repo に commitされる。
- mutation table は次の exact byte 対を持ち、旧 bytes がちょうど 1 箇所、新 bytes が 0 箇所であることを変更前に assertする。
  - `__init__.py`: `from .core import verify_trace_dir` → `from .parse import parse_trace_dir as verify_trace_dir`
  - `report.py`: `"certified": res.certified,` → `"certified": True,`

### 対テスト

提案 node:

`test_pre_wave_exact_twelve_misses_but_exact_fourteen_rejects_new_enforcement_face[verifier-init-dispatch]`

`test_pre_wave_exact_twelve_misses_but_exact_fourteen_rejects_new_enforcement_face[verifier-report-payload]`

各 case で次を行う。

1. exact 14 の一時 repoを作り、production tuple の状態で clean binding を captureし、live verify が通る binding を保存する。
2. 対象 fileの disk bytes を exact replacement で実際に変更する。Git commit/blob は変更しない。
3. `contract_loader_binding.CONTRACT_LOADER_RELATIVE_PATHS` だけを独立 exact 12 に差し替える。この module は行 15 で定数を直接 importしているため、ここが wave 前の実検査になる。
4. exact 12 では変更した新 path を巡回しないため、`capture_contract_loader_binding()` が binding を返し、その binding の `verify_live_contract_loader_binding()` も例外なしになることを negative control とする。
5. module 定数を production tuple へ戻す。同じ disk bytes に対し、`capture_contract_loader_binding()` と、手順 1 の clean binding に対する `verify_live_contract_loader_binding()` の双方が `ContractLoaderBindingError`、`contract-loader-drift`、対象 path で停止することを assertする。
6. exact-12 binding を exact-14 mode で再利用しない。`ContractLoaderBinding.__post_init__` の期待 key 集合が mode に依存するため、それぞれの mode で別 binding を作る。

これは「tuple に path がある」だけの assert ではなく、同じ実 disk mutation を旧検査が見逃し、新検査が捕捉する対照になっている。

clean 正例は別 node `test_exact_fourteen_clean_closure_capture_and_live_verify` とし、未変更の一時 repoで capture → live verify、key 集合と tuple 順が独立 exact 14 に一致することを確認する。

## M1 / M2 / M3 の再現と未測定範囲

### M1

base commit と post-wave commit の双方で、物理的な `output/**/campaign.lock` だけを列挙し、全件を v1/v2 に decodeして、件数・path・schemaを保存する。親の `32 / v2=0` は [test_artifact_admission.py:785](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/tests/test_artifact_admission.py:785) の corpus pin とも突き合わせる。

この測定が一般化できるのは「その checkout の `output` に存在した 32 本」までである。外部保存、別 worktree、別 branch、削除済み artifact、測定後に作られた v2、旧 E1 を転記した report は測っていない。「世界中に v2 がない」根拠にはしない。

### M2

base `5a19b8ab` の clean な使い捨て worktreeで、DW-O19 に従う。

1. 変更前 raw bytes と SHA-256 を保存し、binding を captureする。
2. `verifier/__init__.py:16` の旧行が 1 箇所だけであることを確認して exact replacement。
3. fresh interpreter で path 数、保存 binding の live verify、`pipeline.verify_trace_dir` と `core/parse` の object identityを測る。
4. 保存 raw bytesへ exact 復元し、SHA、diff、statusを確認する。
5. post-wave は一時 repoの発火実証により、同じ disk mutation が capture/live verify の双方で止まることを測る。

M2 が測っていないのは、実 `pipeline.evaluate` の end-to-end 結果、既ロード済み process の alias、弱化を commitしてから作る fresh lock、別 sink、CLI/wrapper、T1208/T1209 である。

### M3

同じく base の使い捨て worktreeで `report.py:46` の exact replacement を行い、fresh interpreter で `VerifyResult.certified=False` と `result_to_dict(...)[certified]=True` の乖離、旧 binding の非発火を測り、raw bytesを復元する。

[ pipeline.py:1133 ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/campaign/pipeline.py:1133) の棄却判定は `vr.certified`、行 1140 の report は rejection payload である。したがって M3 は診断偽装を実証するが、判定反転、実 WAL abort、CLI text、`render_text`、全 consumer を測っていない。

### 親の 3 測定が未確認の帰結

- exact-12 wire 拒否と exact-14 wire 受理。
- epoch preimage の append 順と新 digest。
- 新 2 pathそれぞれの capture/live 双方の fail-closed。
- clean exact-14 正例。
- 独立 fixture、Layer3、S1、S8b consumer の追随。
- import-first sentinel。
- Silo ladder の別 pin が不変であること。
- in-process state、TOCTOU、fresh malicious lock、cross-version epoch。
- 性能・I/O 増分。今回の子は性能測定を行っていない。

## DW-M01 変異事前登録候補

広域 suite を target にすると F358 の共通 `contract-loader-drift` だけで KILLED に見える。各 spec は一時 repoを使う単一 nodeを target set とし、記録 failed node の完全一致を要求する。

| 変異 | 位置 | 期待 node 完全集合 |
|---|---|---|
| `__init__.py` を tuple から除く | `campaign_lock.py:29–42` | 新 paired node `[verifier-init-dispatch]` だけ |
| `report.py` を tuple から除く | 同上 | 新 paired node `[verifier-report-payload]` だけ |
| live 検査を残したまま `disk = _read_regular_file_no_follow(...)` を `disk = blob` にする | `contract_loader_binding.py:355–356` | paired node `[verifier-init-dispatch]` だけ。`if disk != blob` は残るが発火不能になる変異。 |
| capture 側も `disk = blob` にする | `contract_loader_binding.py:331–332` | paired node `[verifier-report-payload]` だけ |
| epoch payload の tuple を `[:-1]` にして report digest を落とす | `artifact_admission.py:742–745` | `test_artifact_admission.py::test_certified_acceptance_admits_exact_e1_fixture` だけ |
| append した 2 path の順を交換する | `campaign_lock.py` の新 2 行 | 同じ exact-E1 fixture node だけ。wire は sortされるため epoch 順序 testが killerになる。 |
| exact key 検査と checked map 構築を同時に弱め、旧 exact-12 mapを受理させる | `campaign_lock.py:171–184` | 新 `test_v2_rejects_pre_wave_exact_twelve_source_blob_keys` だけ。複合置換として DW-M04 の一意性を各置換後に確認する。 |

過剰拒否を防ぐ正例は次を登録する。

- `test_exact_fourteen_clean_closure_capture_and_live_verify`
- `test_campaign_lock_codec.py::test_v2_exact_shape_and_canonical_encoding`
- `test_artifact_admission.py::test_certified_acceptance_admits_exact_e1_fixture`

scope 文字列だけを旧文言へ戻す変異は受理集合を変えないため、DW-M08 に従い kill ではなく diagnostic sensitivity pin として別枠にする。

## 既存受入への影響

production tuple だけを先に 14 にした場合の静的な赤見積りは次のとおり。

- [test_t671_source_binding.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/tests/test_t671_source_binding.py:123) は独立 tuple 不一致。
- 同 fileの行 139、187、215 の既存 12 parameter、行 283、316 は、tuple assert または一時 repoに新 2 fileが無いことで赤になる。期待 tuple 更新後は各 path param が 14 caseへ増える。
- [test_artifact_admission.py:939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1207-closure-exact14/orchestrator/tests/test_artifact_admission.py:939) は旧 scope 逐語不一致。
- 同 fileの行 1070 は `len(...) == 12` で赤。
- `_committed_closure_repo` を使う行 1081、1100、1137、1181、1200、1222、1244 の node は、新 2 file欠落で E1 fixture 構築前後に赤になる。tuple 更新後、独立 epoch golden も 14 pathへ変わる。
- 行 1137 の verifier drift testは現状の 4 caseだけでも緑になり得るが、新 2 faceを検査しない偽の十分性なので 6 caseへ広げる。
- codec、共有 helper、bench、env activation、layer3、S6/S8a は production tupleを動的参照するため、統合後の意味上の赤は予想しない。ただし S6/S8a のコメントは stale になるため編集する。
- `artifact_admission.py` 自体が閉包 member なので、commit 前の実 worktreeを使う campaign testには F357 の偽 `contract-loader-drift` が広く出得る。過去の「26件」を今回へ一般化せず、統合 commit 後の同範囲再走で帰属する。

親の最終受入は brief 指定どおり lease 後に `python3 tools/run_tests.py` を引数なしで実測する。あわせて `python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py`、spool fold dry-runを行い、commit 後に `python3 tools/check_ai_provenance.py` を実行する。Silo の `test_runtime_binding_covers_all_execution_semantics_modules` と committed evidence rebind testも sentinel に含める。

## P1–P5 への判断

- **P1: 賛成。** ただし package 内と package 外を文法上分離し、excluded を `{__main__,cli}.py` と `orchestrator/verify.py` に限定する。`__init__.py` と `report.py` は identity scope 側へ明記する。
- **P2: 賛成。ただし制限を新 D に明記。** 拘束された wave 境界、v2 corpus 0、既存 downstream への波及から domain 据置きは妥当。一方、同じ `/v1` が過去の 12-path grammar と新 14-path grammar を歴史上指すため、cross-version 認証ができたとは名乗らない。T-1208 は未解決のまま。
- **P3: 賛成。** `__init__.py`、`report.py` の末尾順は既存 12 の epoch prefixを保存し、dispatch face、diagnostic faceの順としても自然。wire は sortされる点を新 D に書く。
- **P4: 賛成。** D442 の既存 bytes は保持し、新 D で決定 1・3と「dispatch/report は未閉包」という制限だけを supersedeする。domain、歴史名、D268 の TOCTOU・fresh lock・bootstrap 等の制限は継承する。
- **P5: 限定付き賛成。** §5 の新発火テストは既存 `_git` と一時 repoを再利用できるため T671 に置く。だが旧 exact-12 wire 拒否は codec、epoch 順序と scope/drift は artifact admission の各正本 testに置くべきで、全追加 testを T671 へ集中させない。

## 総括

変更: 既存 12 の順序を保ち、`__init__.py`、`report.py` を末尾追加して exact 14 とし、scope・fixture・wire・記録を追随させる。  
最大の危険: 恒真な tuple assert、F357/F358 の共通 drift、同じ `/v1` に残る cross-version 非認証である。  
親が裁定すべき点: P1 の推奨逐語を採るか、および P5 を「発火テストだけ T671」と限定して確定するか。