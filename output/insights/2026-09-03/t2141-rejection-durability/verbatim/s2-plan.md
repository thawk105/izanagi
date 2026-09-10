## 相乗り可否の実測

- **issuer publication root の固定 artifact: 相乗り不可。ただし母数と path 束縛は再利用可。** `p3_b4_prerun_issuer.py:455-467` が `scheduled_attempt_count` と全 `planned_result_artifacts` を receipt の commitment に入れ、`:1100-1119` が再ロード時に復元するため、実験母数と候補 path は既に publication root から復元できる。一方、registry・manifest・receipt は `:621-623` で排他的に作られ、receipt は `:650-657` で最終確定される。さらに `:1056-1067` が registry/manifest bytes を receipt descriptor と照合するため、producer が後から固定 artifact へ追記すると publication 自体が失効する。

- **`p3_b4_admission_record.py`: 相乗り不可。** `p3_b4_admission_record.py:691-824` は repository 内の admission record と preregistration blob を読み、Git commit・hash・宣言値を検証して `VerifiedB4AdmissionRecord` を返す read-only verifier である。publication root、attempt result path、producer rejection を書く関数を持たず、記録対象も事前 admission であって実行後の候補棄却ではない。

- **`p3_b4_analysis_ledgers.py`: 相乗り不可。** `p3_b4_analysis_ledgers.py:595-639` の registry は scheduled-attempt 行の後に `protocol-violation` 行を hash chain で並べ、`:772-811` の `append_registry_violation` は新しい `B4ScheduledAttemptRegistry` 値をメモリ上で返すだけで file へ追記しない。理由語彙も `p3_b4_analysis_contract.py:59-67` の 5 種に閉じ、producer の 12 issue code や `artifact/field/detail` を保持できない。実 file は issuer が `p3_b4_prerun_issuer.py:621` で一度だけ書き、receipt が bytes を pin するため、事後更新は固定 publication を壊す。

- **campaign WAL: 相乗り不可。** 実 writer は `wal.py:933-1017` で record を検証し、`:1021-1123` で `CampaignLayout.wal_file` へ append・file fsync・directory fsync する。書き先は `layout.py:203-208` の各 campaign root 配下 `runs/wal.jsonl` であり、publication root だけを持つ consumer の入力ではない。また stage は `wal.py:406-427` と `model.py:28-36` の閉じた語彙で、producer rejection 専用 stage は存在しない。`publish_b4_attempt_result` は `p3_b4_raw_record_producer.py:1739-1741` で request の campaign root を確定する前にも棄却しうるため、WAL 自体を特定できない場合もある。

- **既存 attempt result leaf: 相乗り不可。** 成功時は `p3_b4_raw_record_producer.py:640-652` で issuer-planned path を選び、`:1750-1758` / `:1852-1878` で `_publish_exact` する。この leaf に rejection union を置く案では、まさに `PLANNED_PATH_CONFLICT` が発生する `:487-499` / `:526-532` や、leaf 側 IO error の `:541-550` を記録できない。さらに成功 artifact を期待する assembly の `:1917-1927` と同じ leaf に別 schema を混ぜることになる。成功 leaf は現状の bytes と意味を維持する。

結論は、既存 receipt から母数・attempt_id・planned path を再利用し、足りない「事後 rejection event」だけを publication root の新しい 1 leaf に置く案である。

## 変更プラン (file:line)

- `orchestrator/campaign/p3_b4_prerun_issuer.py:40-48`
  - 公開定数 `B4_RAW_RECORD_REJECTIONS_NAME = "raw-record-rejections.jsonl"` を追加する。
  - issuer は空 file を作らない。したがって現在の発行 bytes と「発行直後は固定 3 artifact」という既存期待は変えず、名前だけを予約する。

- `orchestrator/campaign/p3_b4_prerun_issuer.py:418-440`
  - `_reject_fixed_artifact_conflicts` の `fixed_artifact_paths` に上記名を加える。
  - 現行どおり planned path が固定 leaf と同一、またはその配下なら `PLANNED_RESULT_PATH_INVALID` にする。新 leaf は publication root 直下なので、その祖先になれる planned path は publication root 自身だけであり、`:434` の既存検査が拒否する。
  - この検査は発行時 `:737-740` と再ロード時 `:1106-1109` の双方から呼ばれるため、receipt を全再束縛した改変にも同じ制約を課す。

- `orchestrator/campaign/p3_b4_prerun_issuer.py:1178-1190`
  - artifact 名定数を `__all__` に追加し、producer と consumer が同じ定数を使う。

- `orchestrator/campaign/p3_b4_raw_record_producer.py:21-36`
  - `fcntl` と既存 `chained_event_row` を import する。新しい共通 framework は作らない。

- `orchestrator/campaign/p3_b4_raw_record_producer.py:52-55,120-161`
  - event schema `p3-b4-raw-record-rejection-event/v1` と、厳密に検証済みの event/ledger snapshot 用 dataclass を追加する。
  - 1 event は `issuer_commitment_sha256`、`attempt_id | null`、元の `B4RawRecordIssue` 全項目、`event_index`、`previous_event_sha256`、`event_sha256` だけを持つ。時刻や caller の任意 request 全体は入れない。
  - assembly の成功・失敗結果に、同一 snapshot から読んだ rejection event 群を付随させる。rejection 本体の既存 `schema_version/attempt_id/issues` は維持する。

- `orchestrator/campaign/p3_b4_raw_record_producer.py:267-307` の後
  - rejection core を canonical JSON へ変換する専用関数、strict JSONL loader、event-chain 再生成検査を追加する。
  - loader は publication commitment の一致、closed issue code、非空 issues、canonical bytes、連続 event index、previous/event hash、非 null attempt_id が issuer の planned 集合に属することを検査する。
  - file 不在は「event 0 件」として扱う。newline 終端済みの不正行や chain 不一致は fail-closed にし、未終端 tail は未完了 event として採用しない。

- `orchestrator/campaign/p3_b4_raw_record_producer.py:453-558` の後
  - `raw-record-rejections.jsonl` 専用 append writer を追加する。
  - `_ensure_real_parent` で publication root まで real directory であることを確認し、root directory fd と `O_APPEND|O_CREAT|O_NOFOLLOW` の file fd を開く。`flock(LOCK_EX)` 下で既存全行を strict reload してから次の chained row を追記し、file と root directory を `fsync` する。
  - 既存 `_publish_exact` は一行も変更せず、成功 leaf の no-replacement、同一 bytes の idempotence、real-parent 検査をそのまま残す。

- `orchestrator/campaign/p3_b4_raw_record_producer.py:1725-1771`
  - publication の検証に成功した後だけ、request 内の `attempt_id` が sealed planned 集合の一意な要素なら「記録用 candidate id」として先に控える。この値は成功判定へ渡さず、`_request` と `_derive_b4_attempt_data` の検査順・条件は変えない。
  - `_Reject` または予期しない例外から `B4RawRecordRejection` を作ったら、return 前に ledger へ耐久追記する。
  - ledger 記録失敗時は元 rejection に `IO_ERROR` issue を追加して rejection のまま返す。成功 publish へフォールバックしない。

- `orchestrator/campaign/p3_b4_raw_record_producer.py:1774-1891`
  - batch でも validated publication を得た後の全 rejection を同じ writer へ一件ずつ記録する。request collection 自体の不正や batch 前走査の rejection は `attempt_id=None` event として残す。
  - 各 item の成功・rejection・deferred の順序と tuple 長は維持する。
  - `B4RawRecordDeferred` を検出する `:1849-1851` は append を通さず、そのまま第 3 状態として返す。

- `orchestrator/campaign/p3_b4_raw_record_producer.py:1894-2058`
  - validated publication から rejection ledger を一度 snapshot し、その snapshot を assembly の結果へ付ける。
  - planned leaf 不在時の既存 `INCOMPLETE_SET` issue は維持しつつ、consumer が同じ結果から全 durable rejection event を取得できるようにする。assembly 自身の検査失敗は producer rejection ledger へ追記しない。
  - 成功 assembly でも過去に rejection 後の再試行が成功した履歴を失わないよう、ledger snapshot を返す。

- `orchestrator/campaign/p3_b4_raw_record_producer.py:2061-2076`
  - 新しい event/ledger 型と loader を export する。

- `orchestrator/campaign/p3_b4_material_report.py:38-43,89-97`
  - assembly に付随する rejection ledger snapshot を `B4MaterialReportInputs` に保持する。

- `orchestrator/campaign/p3_b4_material_report.py:183-239`
  - publication reload と assembly の結果から、issuer の scheduled count、planned count、ledger bytes、全 rejection event を同一 report input に固定する。

- `orchestrator/campaign/p3_b4_material_report.py:665-797`
  - `provenance.artifacts` に rejection ledger の path・availability・SHA-256・UTF-8 bytes を追加する。
  - top-level に `producer_rejections` を追加し、`scheduled_attempt_count`、`planned_result_artifact_count`、event count、unscoped count、全 event を出す。consumer は `attempt_id` を registry/manifest/planned mapping と join して候補と理由を復元できる。
  - `_HISTORICAL_REJECTION_NON_GUARANTEE` は無条件列挙をやめる。観測時に absent な planned leafのうち matching rejection event が無いものが一件でもあれば従来文字列を残し、すべて success leaf または durable rejection で説明できれば落とす。`:56-58` の観測時点非保証は残す。

- `orchestrator/campaign/p3_b4_material_report.py:800-828`
  - report に埋めた rejection ledger bytes/hash/events を assembly snapshot から独立再照合する。

- `orchestrator/campaign/p3_b4_material_report.py:849-921`
  - Markdown の provenance 表へ rejection ledger を追加し、producer rejection event count を表示する。完全な機械可読内容は JSON 側を正本とする。

## 新設する artifact とその名前衝突の閉じ方

新設する file 種は publication root 直下の `raw-record-rejections.jsonl` だけである。issuer 発行時には作らず、最初の rejection の return 前に producer が作る。

名前衝突は `p3_b4_prerun_issuer.py:418-440` の既存検査へこの名前を追加して閉じる。新規発行は `:737-740`、既存 publication の reload は `:1106-1109` で必ず同じ検査を通るため、planned result path が次のいずれでも拒否される。

- `<publication-root>/raw-record-rejections.jsonl`
- `<publication-root>/raw-record-rejections.jsonl/...`
- publication root 自身

ledger writer はこの一つの固定 path 以外を caller から受け取らない。成功 attempt leaf には引き続き issuer の `_planned_path` が返す path だけを書き、両 artifact の namespace を混ぜない。

## consumer 側の復元経路

復元順は次の一本に固定する。

1. `load_b4_prerun_publication` が registry、manifest、receipt、全 planned path、scheduled count を復元する。
2. rejection ledger loader が固定名の JSONL を一 snapshot で読み、chain と issuer commitment を再検証する。
3. `assemble_b4_raw_analysis` は成功 leaf 群を従来どおり再導出し、成否にかかわらず同じ結果へ durable rejection event 群を付ける。
4. material report は `attempt_id` で ledger event を registry・manifest・planned path に join し、候補、issue code、artifact、field、detail を JSON に出す。
5. ledger に `attempt_id=None` の event があれば unscoped rejection として別集計し、特定候補へ誤帰属させない。
6. planned leaf が absent で matching rejection が無い場合は `deferred` と決めつけず、未試行・記録失敗・deferred を区別不能な unresolved 状態として従来非保証を残す。

これにより `B4RawRecordDeferred` を rejection event に変換せず、成功後にも過去 rejection の履歴を保持できる。

## 受理集合を広げないことの論証

成功へ至る既存列は `p3_b4_raw_record_producer.py:1739-1758` と `:1841-1878` のまま、`_validated_publication`、`_request`、`_derive_b4_attempt_data`、`_publish_exact` をすべて通過した場合だけである。

追加処理は例外を既に捕捉した後の rejection return path にだけ置く。記録成功でも元の rejection を返し、記録失敗でも `IO_ERROR` を加えた rejection を返す。記録結果から `_publish_exact` へ戻る枝は作らない。

`_publish_exact` の `:487-499` と `:526-532` の different-bytes conflict、`:478` の real-parent 検査、`:501-537` の create/link/fsync 手順は変更しない。deferred の `:1665-1672`、`:1748-1749`、`:1849-1851` も ledger writer を呼ばない。

issuer 側では新しい固定名との衝突だけを追加拒否するため、受理集合を広げず、必要な範囲で狭めるだけである。

## 追加・変更するテスト

**正例**

- `orchestrator/tests/test_p3_b4_raw_record_producer.py:802-805` 付近に ledger 読取 assertion helper を追加する。
- `:1101-1115` の実 rejection 相当入力を用い、return された issue と ledger から再ロードした event の `attempt_id/artifact/field/code/detail` が一致し、event が issuer commitment に束縛されることを確認する。
- batch で異なる 2 candidate を拒否し、event index、previous hash、file 順、候補 ID が一致することを確認する。
- 一度 rejection、その後同 candidate を正常公開した場合に、成功 leaf bytes は従来 schema のまま、assembly には過去 rejection event が残ることを確認する。
- `orchestrator/tests/test_p3_b4_material_report.py:183-240` の後に、report JSON だけから scheduled count、planned count、候補 ID、全 issue が復元できる test を追加する。
- 全 absent candidate が success または durable rejection で説明できる fixture では、特定の historical-rejection non-guarantee が落ちることを確認する。

**負例**

- planned result leaf に異なる bytes を先置きして `PLANNED_PATH_CONFLICT` を起こし、その conflict 自体が別 ledger に残ることを確認する。現行実装では ledger が存在せず赤になる。
- ledger append の open/write/fsync failure を注入し、結果が必ず `B4RawRecordRejection` のまま、planned success leaf も不存在であることを確認する。
- rejection を一件記録した後に `B4RawRecordDeferred` を発生させ、event count が増えないことを確認する。
- ledger の canonical bytes、event index、previous hash、issuer commitment、issue code の各一箇所を改変し、loader・assembly・material report が fail-closed になることを確認する。
- `orchestrator/tests/test_p3_b4_prerun_issuer.py:534-571` の固定 artifact conflict 入力へ新しい名前を追加し、exact/descendant planned path が発行前に拒否されることを確認する。`:596-623` 相当の reload 改変負例も追加する。
- `orchestrator/tests/test_p3_b4_material_report.py:223-226` の既存 missing-leaf 期待は変更しない。matching durable rejection が無い破損例では従来非保証が残るため、そのまま緑になる。
- issuer 発行直後の root 内容を 3 file とする `test_p3_b4_prerun_issuer.py:218-223` も変更しない。ledger が rejection 時に初めて作られることを新規 test で確認する。

## 想定される反論と、それが real なら壊れる箇所

- **「registry violation 行へ足せばよい」**が real なら、`p3_b4_analysis_contract.py:59-67` の閉じた reason 語彙と `p3_b4_analysis_ledgers.py:546-592` の exact schema を壊す必要がある。さらに更新後 registry は issuer receipt の descriptor 検査 `p3_b4_prerun_issuer.py:1056-1061` と commitment/completeness 検査 `:1124-1158` に拒否される。

- **「成功 attempt leaf を union にすれば新 file は不要」**が real なら、既存 leaf を開けない `PLANNED_PATH_CONFLICT` と IO failure でも同じ leafへ記録できなければならない。実際には `_publish_exact` の `p3_b4_raw_record_producer.py:487-550` がそれを拒否するため、最重要の失敗理由ほど残らない。

- **「campaign WAL は既に durable」**が real なら、publication root から campaign WAL path を常に導出でき、専用 event が stage whitelist を通る必要がある。`layout.py:203-208` と `wal.py:406-427` の双方が成立を否定し、request validation 前 rejection では campaign root 自体も未確定である。

- **「deferred も一緒に記録すべき」**が real なら、`p3_b4_raw_record_producer.py:1665-1672` の retryable 第 3 状態と、`test_p3_b4_raw_record_producer.py:1183-1199,1330-1384` の no-publish 契約が壊れる。したがって記録対象にしない。

- **「非保証は常に削除できる」**が real なら、durable event のない absent leaf も rejection と断定できなければならない。既存 missing-leaf test `test_p3_b4_material_report.py:183-240` が示すとおり、それは未試行・削除・deferred と区別不能なので、非保証は coverage に応じて狭める。

- **「hash chain で悪意ある全面改変も防げる」**は本案の主張ではない。chain は破損・欠落・順序違反を検出するためのもので、issuer の coordinated rewrite 等の非保証 `p3_b4_prerun_issuer.py:52-64` は残す。

## 総括

- 採るべき案は publication root 直下の `raw-record-rejections.jsonl` 一種だけを追加する案である。
- issuer receipt の既存母数・attempt mapping を再利用し、事後 event の器だけを足す。
- 成功 leaf、admission record、analysis registry、campaign WAL は意味または配置が合わず、完全な相乗り先にはならない。
- rejection は return 前に append・file fsync・directory fsync し、記録失敗でも成功へ転じない。
- deferred は記録せず、matching event のない absent path は unresolved のまま扱う。
- `_publish_exact` と既存テスト期待を維持しつつ、material report の非保証を実際の coverage に応じて狭められる。