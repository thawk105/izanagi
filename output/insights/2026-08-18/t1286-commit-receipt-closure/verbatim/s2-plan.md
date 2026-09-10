## 総括

静的調査では campaign WAL の production COMMIT producer は 3 経路だが、同じ `STAGE_COMMIT` を使う qualification sink が別に 2 経路あり、`wal.append` だけでは裁定 1 全体を支配できない。  
campaign WAL の chokepoint は `wal.append` で正しいが、qualification には `QualificationEventSink.emit` 側の同等 gate が必要であり、親 P1/P2 は部分支持に留まる。  
[T-1252] の判定器 module 閉包は親候補ではなく S8C の core/evaluator/projection 3 module。T-1287 自身の保護面も加えると最終 closure は 14→20 path となる。  
批准は全実装後の closure digest に対する人間の別 commit が最後。親の段 5 分割と `762 → 1286 → 1287 → 1252` 順序はそのままでは不成立である。  
以下は read-only 静的検査結果であり、pytest の緑は主張しない。

## 1. COMMIT producer 全数

### 1.1 campaign WAL の production producer: 3 経路

`STAGE_COMMIT` は `orchestrator/campaign/model.py:23-36`、値 `"commit"` は同 `:28` に定義される。

| production callsite | 呼び出し閉包 | 分類 |
|---|---|---|
| `orchestrator/campaign/pipeline.py:1243-1250` | no-benchmark の `pipeline.evaluate` → `wal.log` → `wal.append` | campaign WAL |
| `orchestrator/campaign/pipeline.py:1305-1308` | benchmark 済み `pipeline.evaluate` → `wal.log` → `wal.append` | campaign WAL |
| `orchestrator/campaign/guided.py:131-141` | `_log_eval` → `wal.log` → `wal.append` | campaign WAL |

`wal.log` は `orchestrator/campaign/wal.py:621-628` の糖衣であり、最終的に `wal.append` (`:379-450`) を呼ぶ。production から `wal.append` を直接呼ぶ箇所はない。

`pipeline.evaluate` の production caller は既存の権威的 AST inventory `orchestrator/tests/test_campaign.py:4734-4743` と一致して次の 5 箇所である。

- `orchestrator/campaign/loop.py:306`
- `orchestrator/campaign/screening_driver.py:198`
- `orchestrator/campaign/s1_direct_comparison.py:980`。既定値は同 `:777-784`
- `orchestrator/campaign/s8b_oracle_driver.py:1577`。既定化は同 `:1310`
- `orchestrator/qualification/t126_driver.py:540`

このうち先頭 4 系統は campaign WAL を持ちうる。`t126_driver.py:540` は後述する qualification sink 専用である。

さらに `loop.run_campaign` の production caller は既存 gate `test_campaign.py:4718-4743` が固定する以下 15 箇所で、いずれも最終的には上記 `pipeline.py` の 2 callsite に収束する。

- `backoff_repro.py:113`
- `backoff_sweep.py:173`
- `demo.py:57,66`
- `p2_2.py:144`
- `p3_kickoff.py:111,118`
- `p3_s4_loop.py:958`
- `p3_s4_loop_sort.py:328`
- `p3_s4_loop_trigger_gating.py:640`
- `p3_s4_red.py:168,178`
- `s6_sort_sweep.py:367`
- `s8a_trigger_sweep.py:469`
- `sanity_silo.py:59`

guided 系統は次の独立した閉包である。

- `guided.py:163-193` の `cmd_start` → `guided.py:191` の `_log_eval`
- `guided.py:196-227` の `cmd_evaluate` → `guided.py:225` の `_log_eval`
- `_log_eval` の COMMIT は `guided.py:141`

### 1.2 campaign WAL ではない production producer: 2 経路

次も同じ `STAGE_COMMIT` を production で使うため、裁定の「全 `STAGE_COMMIT` producer」を字義どおり解釈すると除外できない。

- `pipeline.py:1252-1260`
- `pipeline.py:1310-1311`

両方とも `qualification_policy.event_sink.emit(...)` を呼び、実体は `orchestrator/qualification/artifacts.py:749-784` の `QualificationEventSink.emit` である。これは `append_jsonl` (`artifacts.py:517-538`) に qualification evaluation JSONL を書き、campaign WAL も `campaign.lock` も作らない。

したがって権威ある数え方は次のとおり。

- campaign WAL producer: 3
- qualification event producer: 2
- production の `STAGE_COMMIT` callsite 合計: 5

parent brief の「AST gate に emit も含める」は全数 census として必要だが、`wal.append` gate が emit を保護すると解釈してはならない。

### 1.3 低層・recovery・test-only

`wal.append` の直接 caller は現在 test のみで、少なくとも `test_campaign.py:1357,1759,2398` にある。production でない根拠は `orchestrator/tests/` 配下であり、production import closure に入らないこと。ただし公開 API として producer gate を迂回できるため、テスト専用だから検査不要とはできない。

`wal.py:1336-1367` の `_append_records_locked` は `append` を迂回する内部低層である。現在の production caller は `recover_interrupted_attempts` (`wal.py:1370-1517`, 呼出し `:1514`) だけで、投入する record は `_recovery_abort_record` (`:1320-1333`) が作る `STAGE_ABORT` のみである。

既存 COMMIT fixture は次の種類へ分離する。

- framing・I/O だけを検査する fixture: COMMIT を中立 stage に変更
- legacy WAL の互換性 fixture: tests 内の raw JSONL writer で過去 record を構築
- 新規の有効 COMMIT fixture: verifier evidence と receipt を作る test support helper を使用
- production に `allow_unreceipted_commit=True` のような bypass は作らない

## 2. chokepoint

### campaign WAL

親 P1 の「`wal.append` の record 検証側」は campaign WAL に限れば支持する。

producer 側だけでは、次の直接経路を塞げない。

```text
WalRecord(stage=STAGE_COMMIT, ...)
    → wal.append(...)
```

現在 production caller がなくても、API 自体が存在し test から利用されているため、`pipeline.evaluate` と `guided._log_eval` の検査だけでは支配点にならない。

挿入位置は `wal.py:398` の flock 取得後、既存 tail を読む `:399-405` の後、最初の `os.write` (`:413` 付近) より前とする。lock 外で receipt の未消費を検査すると、同じ receipt を持つ並行 writer が双方通過できる。

実装は次の二段にする。

1. `wal.append` が prospective COMMIT に receipt 必須・lock binding・verifier evidence・重複を検査する。
2. `_append_records_locked` (`wal.py:1336-1367`) は `STAGE_ABORT` 以外を明示的な例外で拒否する。

2 は「今は ABORT しか渡らない」という恒真 assert ではなく、将来 COMMIT を渡したとき実際に停止する runtime gate と負の対照を置く。

`parse_line` (`wal.py:268-310`) は歴史的 record の構文 parser のまま維持し、receipt を必須化しない。ここで必須化すると既存 v1 WAL の読取りまで破壊する。

### qualification

裁定全体については P1 を反証する。`QualificationEventSink.emit` は `wal.append` を通らないからである。

字義どおり全 producer を保護するなら、`artifacts.py:749-784` に第二の chokepoint を置く。source lock identity は qualification protocol の `source.campaign_lock_sha256` (`qualification/contract.py:163-166`) を用い、`t126_driver.py:504-507` で sink 構築時に渡す。既存の source artifact 照合は `artifacts.py:804-813` にある。

一回限りの検査には `append_jsonl` の単純追記では不足する。`emit` 専用に flock 下で既存 evaluation JSONL を読み、receipt ID 未出現を検査してから追記する必要がある。新しい外部 state file は作らず、既存 event ledger 自身を消費済み集合にする。

既存 AST gate は次のように整理する。

- `test_campaign.py:7024-7079`: `pipeline.evaluate` 内の WAL COMMIT 2 箇所のみを数える
- `test_t674_qualification_contract_lanes.py:277-329`: pipeline 内の WAL 2 + qualification 2、計 4 をすでに固定
- guided の 1 箇所と `wal.append` 直接逃げ道を加え、repo-wide の producer/sink 別 census に拡張する

## 3. receipt 設計

### 3.1 verifier verdict の権威

権威ある判定値は `orchestrator/verifier/model.py:170-220` の `VerifyResult` である。

- `verdict`: `model.py:203-215`
- certified pass の唯一の信号: `model.py:217-220` の `certified`
- 安定した report 表現: `orchestrator/verifier/report.py:42-76` の `result_to_dict`

COMMIT receipt は少なくとも `certified is True` かつ `verdict == "serializable"` に束縛する。`verify_tags` や「verify record が存在する」だけでは判定を表さない。

`pipeline.py:1094-1097` が verifier を実行し、`:1102-1118` が `STAGE_VERIFY_DONE` を書き、`:1121` が `not vr.certified` を拒否する。複数 pass は `pipeline.py:1196-1235` にあり、現在のローカル `res.verdict` は pass ごとに上書きされる。receipt は最後の verdict だけでなく、COMMIT の `verify_configs` と同順序の全 pass を保持する。

各新規 `STAGE_VERIFY_DONE` に次を追加する。

- `build_attempt_id`
- `build_admission_receipt_sha256`
- workload/config tag
- `verdict`
- `certified`
- `verifier_result_sha256`

`verifier_result_sha256` は `result_to_dict(vr)` から環境依存の `trace_dir` を除いた安定 projection の canonical JSON に対する domain-separated SHA-256 とする。

### 3.2 lock identity

campaign WAL では、raw `campaign.lock` bytes の SHA-256 を lock identity とする。これは既存 artifact admission の `orchestrator/campaign/artifact_admission.py:858-864` と同じ定義である。

`campaign_id` は不適切である。`ident.canonical_preimage` (`ident.py:151-178`) は v2 authority 全体を含まず、campaign ID も `:181-190` の短縮値だからである。v1 でも `DecodedCampaignLock.original_text` (`campaign_lock.py:76-98`) から exact raw digest を計算できる。

qualification は destination campaign lock を持たないため、protocol が固定し既存 admission が照合する source `campaign_lock_sha256` を lock identity とする。

### 3.3 receipt schema

共通 core を例えば次の strict schema にする。

- `schema = "campaign-commit-verification-receipt/v1"`
- `sink_kind = "campaign-wal" | "qualification-evaluation"`
- `lock_identity_sha256`
- `variant`
- operation/build-attempt identity
- ordered verifier evidence:
  `{workload_tag, verdict, certified, verifier_result_sha256}`
- `terminal_payload_sha256`
- guided の場合だけ replay provenance:
  `{source_campaign_lock_sha256, source_wal_sha256, source_commit_receipt_id, source_variant}`
- `receipt_id`

`terminal_payload_sha256` は receipt 自身を除いた COMMIT payload の canonical digest とし、receipt 発行後に fitness や verify configuration を差し替えられないようにする。

`receipt_id` は上記 core 全体を domain-separated SHA-256 した値とする。caller が任意 ID を選ぶ方式にはしない。

### 3.4 発行経路

- `pipeline.py:1196-1235`: pass ごとの exact verifier evidence を順序付きで蓄積
- `pipeline.py:1243-1250,1305-1308`: 全検証・benchmark 終了後、COMMIT 直前に campaign WAL receipt を発行
- `pipeline.py:1252-1260,1310-1311`: 同じ verifier evidence から qualification receipt を発行
- `guided.py:131-141`: replay が運んだ source proof を検証後、destination lock digest に結び直した receipt を発行

可能なら receipt issuer は一度しか seal できない in-memory `CommitReceipt` object を返し、`wal.log/append` はその object と payload の一致も検査する。ただし durable な一回限りの根拠は object ではなく、次項の既存 ledger 内 receipt ID 集合である。

### 3.5 一回限り・replay・recovery

campaign WAL について親 P2 は支持する。

- 消費済み集合: flock 下で読んだ既存 WAL の COMMIT receipt ID
- 新規 COMMIT の ID が集合にあれば拒否
- 追記成功後は COMMIT 自身が durable な消費記録
- 外部 state file は不要
- fsync 後に caller が失敗扱いして再試行しても、再 scan が既存 ID を検出する

ただし P2 は qualification まで覆わない。qualification は既存 evaluation JSONL 内の receipt ID 集合を同じ方法で使う。

replay (`wal.py:1520-1574`) は receipt を「再消費」せず、既存 1 record の妥当性と集合内重複を read-only に再計算する。recovery (`wal.py:1370-1517`) も同じ検査後に ABORT だけを追記する。recovery suffix は receipt ID を持たず、新しい消費を発生させない。

guided は現状のままでは不十分である。

- `replay.py:52-60` の `GenomeResult` は `certified: bool` しか保持しない
- `replay.py:162-197`、特に `:181-182` は VERIFY_DONE を最後の bool に潰す
- `guided.py:131-141` はその bool から合成 VERIFY/COMMIT を作る

修正案は次のとおり。

- `GenomeResult` に immutable `VerifiedReplayEvidence` を追加
- `load_landscape` が `CertifiedCampaignView` から source lock SHA、WAL SHA、source COMMIT receipt ID、variant、ordered verifier evidence を保持
- receipt 付き source COMMIT だけが新しい guided certified COMMIT を発行可能
- legacy receiptless source は引き続き閲覧できるが、新しい certified COMMIT へ laundering できない
- 手作りの `GenomeResult(certified=True)` は拒否する

## 4. v1 両立

静的再検証では live `output/campaigns/*/campaign.lock` は 30 件で、`authority` と `search_config.environment_contract_sha256` はともに 0 件だった。親の実測は正しい。

現行 `wal.py:1040-1085` は `decoded.is_v2` を `:1054-1057` で検査し、legacy key のない v1 は `:1059-1061` で return する。よって receipt gate をこの v2 branch 内へ置く案は不採用とする。

互換規則は次の二面に分ける。

- 過去: receipt 導入前の COMMIT は replay/recovery/read で許容
- 将来: v1/v2 を問わず、今回のコードで新たに append する COMMIT は receipt 必須

新規検査は lock version 分岐の外、`wal.append` の prospective-record admission に置く。v1 でも raw lock digest を算出できるため、要件を弱める必要はない。

formal admission では新 schema の receipt を完全検証する一方、legacy artifact は現在の epoch/compatibility policy に従って読み取る。既存 WAL を migration 書換えしてはならない。

負の対照は、代表 v1 campaign のコピーに対して次を同じ test で行う。

1. receiptless な既存 WAL を replay/recovery できる
2. replay/recovery を繰り返しても WAL bytes が変わらない
3. 同じ v1 lock へ新しい receiptless COMMIT を append すると拒否される

これにより「legacy が読めるから新規 COMMIT も通る」という恒真な互換 branch を防ぐ。

## 5. 批准台帳

### 5.1 批准単位

親 P3 の closure digest 1 本を支持する。批准単位は exact path→Git blob SHA-256 map 全体の canonical hash とする。

path ごとの批准は、個別には批准済みでも組合せとして未審査の Frankenstein closure を作れるため不採用。Git commit SHA は digest に含めず、同一 bytes が別 commit に移っただけで批准を失わないようにする。lock には従来どおり path map を残し、diagnostic に使う。

### 5.2 比較位置

現在の経路は次のとおり。

- exact closure: `campaign_lock.py:27-44`
- capture: `contract_loader_binding.py:324-337`
- live verify: `contract_loader_binding.py:340-359`
- new-lock adapter: `ident.py:248-258`
- new certified lock 全体: `ident.py:436-502`
- capture 呼出し: `ident.py:470`
- authority capture: `ident.py:471`
- encode/acquire: `ident.py:473-488`

批准比較は `_capture_current_loader_binding` (`ident.py:248-258`) で capture/live verify の直後、return の前に入れる。これにより `ensure_campaign_identity` は lock encode/acquire より前に未批准 closure を拒否する。

`_authority_source_for_new_certified_lock` (`ident.py:227-245`) は T-762 後の verified activation wrapper を使う。binding 批准と activation authority の両方を得てから v2 lock を encode する。

### 5.3 台帳と追記権限

新規 strict canonical JSONL を、例として次へ置く。

`hooks/enforcement-source-closure-ratifications.v1.jsonl`

row は exact schema のみにする。

```json
{"schema_version":1,"closure_digest_sha256":"<64-hex>"}
```

`hooks/guard_write.py:17-18` と `hooks/README.md:138-154` が `hooks/` を直接書換え保護面として扱うため、AI 用 append API・CLI・自動更新処理は作らない。production は read-only verifier だけを持つ。

台帳 verifier は `trial_registry.py:1698-1740` の履歴検証を参考に、committed history が strict prefix extension であることを確認する。削除、置換、並替え、複数行の無審査追加を拒否する。

ただし repository 内の trailer や author 名だけでは「人間」を暗号学的に証明できない。`docs/decisions.md:13151-13173` の D287、`:15565-15592`、`:17328-17363` とも整合する境界は次である。

- 実装担当 AI は台帳を追記しない
- 全 closure bytes を確定・commit 後、人間が map と digest をレビューする
- 人間が別 commit で 1 行だけ追記する
- 未批准の間は新 certified lock 生成を fail closed にする

署名による人間証明まで求めるなら、repo 外 trust root の追加裁定が必要であり、本プランでは謳わない。

### 5.4 T-1287 自身の self-protection

批准比較が closure 外なら、その比較処理を改変して批准を迂回できる。したがって T-1252 の 3 module だけでなく、次も closure に加える。

- `orchestrator/campaign/campaign_lock.py`
- `orchestrator/campaign/contract_loader_binding.py`
- 新規 `orchestrator/campaign/enforcement_source_ratification.py`

台帳データ自身は trust root なので closure から意図的に除外する。含めると批准 entry を足すたび digest が変わる自己参照になる。

## 6. 判定器閉包

親候補の `s8b_oracle_judge.py` は不採用。repo から導出される S8C 判定器 module の exact 集合は次の 3 個である。

1. `orchestrator/campaign/s8c_preregistration.py`
2. `orchestrator/campaign/s8c_preregistration_evidence.py`
3. `orchestrator/campaign/s8c_generation_projection.py`

閉じている根拠は次のとおり。

- `s8c_preregistration.py:40-50` が `CORE_MODULE_PATH`、`EVALUATOR_MODULE_PATH`、`PROJECTION_MODULE_PATH` を権威的に定義し、DECIDER_VERSION はこの三者を表す
- dynamic identity check は同 `:1540-1641`
- activation 時に三者を読み hash する処理は `:1661-1675`
- live core/evaluator/projection の照合は `:1698-1726`
- evidence/report へ三 hash を出す処理は `:1759-1773`
- `s8c_preregistration_evidence.py:18` の project-local import は core のみ
- `s8c_generation_projection.py:1-15` は stdlib のみを使う pure leaf
- core が動的に読む project-local evaluator/projection は上記 2 module だけ

`s8b_oracle_judge.py` は S8B の判定器で、`s8b_verdict.py:91,273,290` から使われる。S8C DECIDER_VERSION closure を構成しない。

evidence contract JSON は module ではなく、`s8c_preregistration.py:191-199` の `protected_sha256` と `:1272-1285` の record 照合で別に保護される。

したがって最終 exact closure は次となる。

- 現行 14
- T-1252 S8C 判定器 3
- T-1287 の self-protection 3
- 合計 20 path

### `CONTRACT_LOADER_RELATIVE_PATHS` の全 consumer

production は 3 file。

- `campaign_lock.py:29,176,185`
- `contract_loader_binding.py:15,73,78,329,348,372`
- `artifact_admission.py:177,743,747`

test/support は 9 file。

- `test_t671_source_binding.py:169,173,203,224,235,240,271,275,329,404`
- `campaign_lock_test_support.py:18`
- `test_campaign_lock_codec.py:45,167,257`
- `test_artifact_admission.py:1323,1329,1345,1411,1568,1590,1612,1625,1650-1654`
- `test_s6_sort_sweep.py:624,630`
- `test_s8a_trigger_sweep.py:834,840`
- `test_bench_first_real_wal.py:166,172`
- `test_layer3_report.py:65`
- `test_env_contract_activation.py:307`

全 12 file を audit 対象とする。tuple を動的に反復していて編集不要な consumer もあるが、epoch/golden hash が変わる可能性を確認しなければならない。

`test_t671_source_binding.py:166-256` の既存 12→14 先例を一般化し、old 14 は各追加 enforcement face の改変を見逃すが exact 20 は拒否することを個別に固定する。

## 7. 負の対照

| 裁定 | 現状で通る入力 | 修正後の期待 | テスト配置 |
|---|---|---|---|
| T-1286 | v1 lock、green VERIFY_DONE の後へ receiptless COMMIT を `wal.append` | append 前に拒否し WAL byte 不変 | 新規 `test_commit_receipt.py:1-`。既存 API fixture は `test_campaign.py:1357,1759,2398` を利用 |
| T-1287 | clean committed closure を capture するが digest は批准台帳にない | `ident.py:470` の lock capture 後、lock 作成前に拒否 | `test_t671_source_binding.py:256` 以降 |
| T-762 | activation prefix は構文上正しいが、registry intersection 又は calibration blob が不整合 | `ident` wrapper 内で拒否し lock を作らない | `test_env_contract_activation.py:1952-2004` 周辺 |
| T-1252 | 旧 14 path は不変のまま、三判定器の一つを改変 | old-14 model は通るが exact-20 binding は拒否 | `test_t671_source_binding.py:178-256` の parametric 拡張 |

T-1286 にはさらに以下を同じ land で置く。

- 同一 receipt ID の二回目を拒否
- lock SHA だけ変えた receipt を拒否
- `certified=false` 又は `verdict!="serializable"` を拒否
- COMMIT payload を receipt 発行後に変えると拒否
- verifier evidence の順序・tag が `verify_configs` と違えば拒否
- `_append_records_locked` に COMMIT を渡すと拒否
- qualification event JSONL で同一 ID の二回目を拒否
- guided の bare `GenomeResult(certified=True)` を拒否
- source receipt を別 source lock/destination lock に使い回すと拒否
- replay/recovery を二回実行しても durable receipt 数は増えない
- v1 の historical receiptless COMMIT は読めるが、新規 receiptless append は拒否

T-1287 には台帳 row の削除・置換・並替え、未批准 digest、批准済み digest と path map の不一致をそれぞれ負の対照にする。

T-762 には runtime 負対照に加え、`ident.py` が次を直接参照しない AST test を置く。

- `env_contract_activation.load_activation_state`
- `env_contract_activation.read_activation_record_files`
- `env_contract_activation.validate_activation_records`

ただし AST test だけで完了扱いせず、registry/calibration 不整合が実際に拒否される runtime test を必須にする。

## 8. 段 5 分割

親の A=T-762 / B=T-1286 / C=T-1287+T-1252 は編集 file が素集合にならない。

- A と C がともに `ident.py` を編集する
- B は `replay.py` を必要とするが親の production file 列挙から漏れている
- 字義どおり全 `STAGE_COMMIT` を保護するなら B は qualification files も編集する
- closure consumer の test ownership も A/C 間で衝突しうる

file ownership を優先して次へ分ける。

### A: activation provider

- `orchestrator/campaign/env_contract.py`
- `orchestrator/tests/test_env_contract_activation.py`

`env_contract.py:631-662` の共通検査を抽出し、current と historical の双方に fork-safe verified wrapper を提供する。cache/reset は `:665-709`、public current API は `:745-747` の隣に置く。

### B: COMMIT receipt

- `orchestrator/campaign/wal.py`
- `orchestrator/campaign/pipeline.py`
- `orchestrator/campaign/guided.py`
- `orchestrator/campaign/replay.py`
- `orchestrator/qualification/artifacts.py`
- `orchestrator/qualification/t126_driver.py`
- `orchestrator/tests/test_campaign.py`
- `orchestrator/tests/test_guided.py`
- `orchestrator/tests/test_t674_qualification_contract_lanes.py`
- 新規 receipt test/support
- receiptless raw COMMIT を持つ既存 test files の機械的 fixture 移行

### C: identity・closure integration

- `orchestrator/campaign/ident.py`
- `orchestrator/campaign/campaign_lock.py`
- `orchestrator/campaign/contract_loader_binding.py`
- 新規 `orchestrator/campaign/enforcement_source_ratification.py`
- `orchestrator/campaign/artifact_admission.py`
- `test_t671_source_binding.py`
- その他 closure consumer tests/support

C が `ident.py` で A の API へ T-762 call migration を行い、同じ file 内へ T-1287 比較を入れる。このため課題番号として T-762 は A/C にまたがるが、編集 file ownership は素集合になる。

A と B は並行可能。C は A の public API と、B を含む最終 enforcement bytes を受けて統合する。批准台帳の 1 行追記は C に自動割当せず、人間専用の最終単位 D とする。

## 9. 順序

親 P5 の `762 → 1286 → 1287 → 1252` は反証する。

現行 closure は `env_contract.py` / `ident.py` と `wal.py` / `pipeline.py` を含むため、T-762・T-1286 の編集は closure digest を変える。T-1252 で path set が増え、T-1287 自身の比較 module 追加でも再び digest が変わる。T-1287 の批准を T-1252 より先に確定すると、直後に批准対象が失効する。

推奨順序は次のとおり。

1. A: T-762 verified activation provider
2. B: T-1286 receipt を A と並行実装
3. C: `ident.py` の T-762 migration、T-1252 exact module 集合、T-1287 self-protection を統合
4. final exact 20 closure を固定し、未批准なら new lock が fail closed する状態で全 code/test を commit
5. 親が関連 test・repository checker を実測
6. committed tip の exact path→blob map と digest を算出
7. 人間がレビューし、批准台帳へ別 commit で 1 行追記
8. 親が再度 acceptance を実測

P5 を維持できるのは「T-1287」は verifier machinery の実装だけを意味し、実際の批准 entry は T-1252 を含む全変更後に行う、と再定義した場合だけである。

## 10. 親 brief への反証

親実測のうち、次は確認できた。

- live lock 30 件、authority 0、legacy environment-contract key 0
- `wal.py:1054-1061` の v2/v1 分岐により、v2 内だけの gate は live v1 で発火しない
- `test_campaign.py:7024-7079` の名前付き AST gate は pipeline の `wal.log(COMMIT)` 2 箇所だけを数える
- `ident.py` の direct activation route は wrapper の registry intersection、calibration、verified hash set、fork-safe lock/cache を迂回する

修正が必要な点は次のとおり。

1. 「COMMIT producer」は campaign WAL 3 箇所だけではない。qualification `emit` 2 箇所を含めると production `STAGE_COMMIT` callsite は 5。`wal.append` は前者だけの chokepointである。
2. qualification emit は完全に gate 無しではない。`test_t674_qualification_contract_lanes.py:277-329` が pipeline 内の WAL 2 + emit 2 をすでに数える。ただし guided と低層 append は依然漏れている。
3. P2 の「WAL 内の消費済み集合」は campaign WAL には正しいが、裁定を全 producer に適用するなら qualification event ledger も必要。
4. guided は `certified: bool` に verifier evidence を潰しており、単に receipt field を足すだけでは verifier 判定に束縛できない。`replay.py` の変更が必須。
5. T-1252 の候補集合は誤り。`s8b_oracle_judge.py` ではなく `s8c_preregistration_evidence.py` が exact 3 の一員。
6. `CONTRACT_LOADER_RELATIVE_PATHS` の test/support consumer は 6 file ではなく 9 file、production 3 file と合わせて 12 file。
7. T-1287 の比較器自身を closure に含めない 14→17 案は自己保護されない。最終集合は 14→20 が必要。
8. A/C は `ident.py` で競合し、親の段 5 ownership は素集合でない。
9. P5 は批准 digest の確定順として不正。批准は T-762、T-1286、T-1252、T-1287 enforcement bytes の全確定後でなければならない。
10. `ident.py:292` は概略位置で、現行 direct load は `:294`、raw file read は `:303`、direct validation は `:306-314`。
11. `hooks/README.md:138-140` と `hooks/guard_write.py:10-13,249-253` の「pipeline だけが COMMIT を書く」という説明は `guided.py:141` と矛盾しており、保護された人間編集面として別途更新が必要。
