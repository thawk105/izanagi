結論として、S1〜S3 は scope を広げず実装可能である。S1 は既存 `Wal*` 型を `wal.py` に残す「薄い委譲」、S2 は準備と commit を分離した原子的置換、S3 は typestate API と hard-link locator を採る。既存 WAL の bytes・公開 API・proof consumer の受理集合は変えない。

以下の `new:Lx-Ly` は新規ファイル内の予定配置であり、既存ファイルの行番号は現状の anchor である。

## 所有 file の分割と固定依存

| 単位 | 排他的な所有 file |
|---|---|
| S1 | `orchestrator/durable/__init__.py`、`orchestrator/durable/io.py`、`orchestrator/durable/jsonl.py`、`orchestrator/campaign/wal.py`、`orchestrator/tests/test_durable_jsonl.py` |
| S2 | `orchestrator/durable/atomic_replace.py`、`orchestrator/tests/test_atomic_replace.py` |
| S3 | `orchestrator/durable/process_identity.py`、`orchestrator/durable/mutation_journal.py`、`orchestrator/tests/test_mutation_journal.py` |

したがって `O(S1) ∩ O(S2) = O(S1) ∩ O(S3) = O(S2) ∩ O(S3) = ∅` とする。S1 だけが `orchestrator/durable/__init__.py` を所有し、S2/S3 は package root を編集せず、各 submodule を直接 import する。

実装後の設計状態タグ、worklog、必要なら decisions fragment は親の統合作業とし、3 実装子の所有外に置く。

### S3 が依存する S1 の固定公開 signature

`orchestrator/durable/io.py:new:L20-L150`:

- `write_all(fd: int, data: bytes) -> None`
- `pread_exact(fd: int, offset: int, size: int) -> bytes`
- `fsync_directory_fd(fd: int) -> None`
- `publish_create_only_at(parent_fd: int, name: str, data: bytes, *, mode: int) -> CreatedFile`
- `replace_name_at(parent_fd: int, source_name: str, target_name: str) -> None`

`replace_name_at` は `os.replace(..., src_dir_fd=..., dst_dir_fd=...)` と同じ parent fd の `fsync` を不可分な API 契約にする。

`orchestrator/durable/jsonl.py:new:L20-L350`:

- `strict_json_loads(text: str, *, subject: str) -> object`
- `validate_json_value(value: object, *, path: str, subject: str) -> None`
- `canonical_json_bytes(value: object) -> bytes`
- `iter_binary_frames(path: str | os.PathLike[str]) -> Iterator[BinaryFrame]`
- `append_frame_at(parent_fd: int, name: str, frame: bytes, *, display_path: str, mode: int) -> None`
- `append_bytes_locked(fd: int, data: bytes, *, parent_fd: int, display_path: str) -> None`
- `repair_truncated_tail_at(parent_fd: int, name: str, *, display_path: str, validate_prefix: PrefixValidator | None, write_receipt: ReceiptWriter) -> TailRepairResult`

S3 はこのうち `canonical_json_bytes`、`strict_json_loads`、`iter_binary_frames`、`append_frame_at`、`repair_truncated_tail_at`、`fsync_directory_fd`、`publish_create_only_at`、`replace_name_at` のみに依存する。

## S1 durable primitive の抽出

### 移動・委譲する範囲

| 現行 anchor | 新しい所有先 | 方針 |
|---|---|---|
| `orchestrator/campaign/wal.py:160-244` | `jsonl.py:new:L70-L160` | duplicate key、非 finite、lone surrogate、cycle、非 JSON-native 型、共有 DAG 許容を generic 化する。`wal.py` 側に同名 private wrapper を残し、既存の文言と `WalPayloadTypeError.path` を復元する |
| `wal.py:320-332` | `jsonl.py:new:L162-L195` | byte framing iterator を移す |
| `wal.py:335-346` | `wal.py` に残す | 公開 `iter_lines` は委譲し、generic framing error を `WalFramingError` へ写す |
| `wal.py:358-453` | `jsonl.py:new:L197-L285` | open、`flock(LOCK_EX)`、regular-file gate、tail-gate、完全 write、file fsync、lock 中の親 dir fsync、close-error precedence を移す |
| `wal.py:456-484` | `io.py:new:L75-L125` / `jsonl.py:new:L287-L315` | range digest、128-byte preview、後方 newline boundary scan を移す |
| `wal.py:487-523` | `io.py:new:L127-L150` | create-only完全 write、file/dir fsync を移す。receipt の key、JSON bytes、prefix、時刻/PID/試行番号は campaign policy なので `wal.py` に残す |
| `wal.py:526-592` | `jsonl.py:new:L317-L350` | lock、tail scan、receipt-before-truncate、`ftruncate`、file fsync を移す。active-attempt 判定は callback のまま `wal.py` に残す |
| `wal.py:1060-1078` | `io.py:new:L55-L73` | locked fd の完全 `pread` を移す。UTF-8 decode と `WalRecord` parse は残す |
| `wal.py:1185-1216` | `jsonl.py:new:L255-L285` | lock 取得済み複数-frame write/fsync/dir-fsync を共通 primitive へ委譲する |

`wal.py:247-313` の `WalRecord` schema、既知 stage 白名簿、`_record_to_line` は移さない。特に `wal.py:309-313` の dict 挿入順、`ensure_ascii=False`、`separators=(",", ":")`、`sort_keys` なしを維持しないと WAL bytes が変わる。

`wal.py:595-1520` の campaign topology、replay、lock、recovery policy は durable 層へ持ち込まない。

### 定数

現在 inline の以下だけを private 定数として新層へ集約する。

- `wal.py:369-370` の append open flags
- `wal.py:492-493` の create-only flags
- `wal.py:533` の repair flags
- `wal.py:412-415,516-518,1207-1210` の directory flags
- `wal.py:462,476,1064` の read chunk `65536`
- `wal.py:466-467` の preview limit `128`

`wal.py:52-76` の campaign stage・payload・attempt 定数は移さない。receipt の最大再試行 `100` と名前規則 `wal-tail-repair-*` も `wal.py:494-505` に残す。

### 例外と facade

既存例外の「定義」は一つも移さない。

- `WalLineError`、`WalDuplicateKeyError`、`WalFramingError`、`WalPayloadTypeError`、`WalAppendError`: `wal.py:81-116`
- `WalTailRepairResult`: `wal.py:149-157`
- campaign semantic 例外: `wal.py:119-146`

新層には `JsonlLineError`、`JsonlDuplicateKeyError`、`JsonlFramingError`、`JsonlPayloadTypeError`、`JsonlAppendError`、generic `TailRepairResult` を追加するが、`wal.py` から外へ漏らさない。薄い wrapper が既存 `Wal*` 型・属性・文言へ変換する。

re-export を採らない理由は次の通り。

- `read_records_collected` は `type(exc).__name__` を理由文字列へ埋め込む (`wal.py:645-651`)。
- `WalAppendError.cause` が `WalFramingError` であることを consumer/test が検査する。
- re-export では class の `__module__` が変わる。薄い委譲なら型定義位置も保てる。
- `WalTailRepairResult` を generic dataclass の alias にすると annotation、repr、型 identity が変わりうる。

### import 互換

現行は `campaign.wal` と `orchestrator.campaign.wal` の両方が実在する。例として `orchestrator/campaign/replay.py:25-29`、`orchestrator/campaign/s8b_oracle_report.py:25-33`、`orchestrator/tests/test_campaign.py:28-33` は `orchestrator/` 自体を `sys.path` に入れて `campaign.wal` を読む。

そのため `wal.py:30` 付近では package 名を判定し、

- `__package__ == "campaign"` なら `durable.io/jsonl`
- `__package__ == "orchestrator.campaign"` なら `..durable.io/jsonl`

を読む。全 importer を `orchestrator.campaign` へ一括変更する案は公開 import 面を変えるので却下する。

### 移動で壊れうる consumer の全 inventory

import 元。これらはすべて `wal` facade のままとし、編集しない。

- `orchestrator/campaign/artifact_admission.py:24`
- `backoff_repro.py:26`
- `backoff_sweep.py:37`
- `guided.py:34`
- `ident.py:22`
- `layer3_report.py:50`
- `p2_2_report.py:22`
- `p3_kickoff.py:31`
- `p3_s4_loop.py:54`
- `p3_s4_loop_sort.py:66`
- `p3_s4_loop_trigger_gating.py:50`
- `p3_s4_red.py:40`
- `pipeline.py:36`
- `replay.py:29`
- `s1_direct_comparison.py:30`
- `s1_report.py:30`
- `s6_sort_sweep.py:55-56`
- `s8a_trigger_sweep.py:74-75`
- `s8b_oracle_driver.py:26`
- `s8b_oracle_report.py:33`
- `screening_driver.py:14`
- `loop.py:20-21`
- `orchestrator/critic/digest.py:27`
- `tools/plotting/plot_backoff.py:28`

例外 catch、`isinstance`、型 annotation の感応点:

- `screening_driver.py:62,182`
- `loop.py:275`
- `s1_direct_comparison.py:249,810,817`
- `ident.py:188`
- `guided.py:107`
- `s6_sort_sweep.py:288`
- `s8a_trigger_sweep.py:391`
- `s8b_oracle_driver.py:1381,1407`
- `layer3_report.py:99,114,413,418`

framing/parse を直接使う箇所:

- `tools/plotting/plot_backoff.py:121-122`
- `layer3_report.py:96-114,411-418`
- `s8b_oracle_report.py:1249-1293`
- `artifact_admission.py:577,600`
- `s1_direct_comparison.py:272,578`
- `s1_report.py:341`

テストは `wal.os`、`wal.fcntl`、`wal.hashlib` を monkeypatch している。

- `test_campaign.py:1671-1710,1719-1745,1751-1791,1797-1819,1834-1856`
- `test_s1_direct_comparison.py:1143-1164`
- `test_s6_sort_sweep.py:467-483`
- `test_s8a_trigger_sweep.py:535-549`
- `test_s8b_oracle_driver.py:3405-3457`
- `test_p3_s4_loop.py:383`

新層も `import os` / `import fcntl` / `import hashlib` と module object を参照し、関数を直接 import しない。これにより既存 `wal.os.write` 等への monkeypatch が同じ module object に届く。

## S2 原子的 target 置換

### 既存実装の再利用判定

| 既存実装 | 再利用可否 |
|---|---|
| `orchestrator/qualification/atomic_publish.py:24-123` | 不可。`os.link` による create-only publish であり上書きしない (`:100-120`)。live target hash CAS、metadata 保存、事前登録がない。さらに `contract.py:38-50` の pin 対象で brief `:51-52` の no-touch に抵触する |
| `tools/dev_waves/ledger.py:125-174,256-322` | private `_write_all`、dirfd/no-follow open、replace+dir-fsync の考え方は S1 公開 primitive へ取り込む。直接 import は不可。temp 名が PID/thread 依存 (`:274-288`)、対象が固定 cache 名だけで、hash/metadata/preregistration がない |
| `tools/mutation_harness.py:1790-1811` | ledger 用 `mkstemp → fsync → replace → dir fsync` であり、target identity の再検査がない。実 target は現在も in-place `write_text` (`:767-788,1251-1332`) なので再利用不可・本 wave では no-touch |
| `tools/dev_wave_land.py:1272-1285` | bytes/mode の temp restore だが dir fsync、uid/gid、live hash がない |
| `tools/spool_fold.py:1908-1925` | replace+dir fsync はあるが、random temp、事前登録、live hash、metadata がない |

S2 はこれらを複製せず、S1 の `write_all`、`fsync_directory_fd`、`replace_name_at` を使用する。

### module と API

`orchestrator/durable/atomic_replace.py:new:L1-L450`:

- `prepare_atomic_replace(parent_fd: int, target_name: str, replacement: bytes, *, expected_live_sha256: str, attempt_id: str, target_index: int, role: Literal["mutation", "restore"]) -> PreparedReplacement`
- `commit_atomic_replace(parent_fd: int, prepared: PreparedReplacement) -> ReplacementReceipt`
- `discard_atomic_replace(parent_fd: int, prepared: PreparedReplacement) -> DiscardResult`

予定配置:

- `new:L20-L95`: 例外、`LstatMetadata`、`TempRegistration`、`PreparedReplacement`、receipt
- `new:L96-L190`: safe component、target open、hash、metadata preflight
- `new:L191-L305`: temp 作成と durable registration
- `new:L306-L405`: live recheck、replace、postcheck
- `new:L406-L450`: exact temp cleanup

temp 名は

`.{target_name}.izanagi-{attempt_id}-{target_index:04d}-{role}.tmp`

とする。`attempt_id` は lowercase 32-hex、target index は armed target の path-sort 順。`PC_NAME_MAX` 超過、同名存在、名前の再利用は retry せず fail-closed とする。random `mkstemp` は、journal が事前に名前を束縛できないため使わない。

`TempRegistration` は最低限次を返す。

- `name: str`
- `st_dev: int`
- `st_ino: int`
- `sha256: str`
- `size: int`
- `parent_dev: int`
- `parent_ino: int`

### metadata

`lstat` から次を armed 用に記録する。

- `st_dev`, `st_ino`, `st_mode`, `st_uid`, `st_gid`
- `st_nlink`, `st_size`
- `st_atime_ns`, `st_mtime_ns`, `st_ctime_ns`

分類は次の通り。

- 保存対象: `stat.S_IMODE(st_mode)`、`st_uid`、`st_gid`、`st_atime_ns`、`st_mtime_ns`
- identity/race 検出対象: `st_dev`、`st_ino`、`st_nlink`、`st_size`、`st_ctime_ns`
- 置換により意図的に変わるもの: inode、ctime、replacement の size

拒否条件:

- symlink、非 regular、`st_nlink != 1`
- target と parent/temp の device 不一致
- `O_NOATIME` で target を読めず、preflight 自身が atime を変えうる場合
- temp に `fchown → fchmod → futimens` を適用後、`fstat` が記録値と一致しない
- target または temp の xattr/ACL/capability が非空、列挙不能
- inode flags を検査不能、または保存対象外の flag がある
- target hash、inode、mode、uid/gid、times が prepare 中に変わる

xattr/ACL/flags は本 wave ではコピーしないため、黙って落とさず拒否する。`st_blocks`、Lustre stripe/layout の物理配置は論理 metadata 保存契約に含めず、耐久性も主張しない。

### 順序

`atomic_replace.py:new:L191-L405` は次を固定する。

1. parent fd、target basename、lstat/open/fstat identity を検査
2. target を読み、`expected_live_sha256` と一致確認
3. 同一 parent に `O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC` で temp 作成
4. 完全 write
5. `fchown → fchmod → futimens`
6. temp の metadata/hash/inode を再検査
7. `fsync(temp fd)`、close
8. temp 名自体を耐久化するため target directory を fsync
9. `PreparedReplacement` を返す。呼出側はここで armed へ登録する
10. commit 時に parent、target、temp の inode/hash/metadata をすべて再検査
11. `os.replace`
12. target directory fsync
13. target を reopen し、inode が登録 temp、hash/metadata が予定値と一致することを検査

`os.replace` 後の dir fsync が失敗した場合は成功扱いせず、`target_may_have_changed=True` の indeterminate error を返す。journal は non-clean のまま残る。

S3 は mutation 用と restore 用の temp を双方 prepare してから armed を書く。prepare 中に crash すると「未登録 temp だけ」が残りうるが target は変わらない。この残骸は journal がないため自動削除せず、将来の quarantine が fail-stop する。これを消すには Lustre 上の `O_TMPFILE` 実測か pre-arm protocol の追加が必要で、現 scope へ無理に入れない。

また、live hash 再検査と rename の間に非協調 writer が割り込む kernel-level CAS はない。使い捨て worktree・consumer lease が有効化条件であり、S2 単体で TOCTOU 解消を主張しない。

## S3 変異 journal の記録層

### schema と hash-chain

`orchestrator/durable/mutation_journal.py:new:L20-L280` に次の exact top-level schema を置く。

| field | 型 |
|---|---|
| `schema_version` | exact `"izanagi-mutation-journal-event/v1"` |
| `attempt_id` | lowercase 32-hex `str` |
| `seq` | 0 始まりの非負 `int`、`bool` 不可 |
| `state` | `armed|mutated|restoring|recovering|clean` |
| `previous_record_sha256` | lowercase 64-hex |
| `payload` | state ごとの exact-key object |
| `record_sha256` | lowercase 64-hex |

hash は repo の既存方式 `orchestrator/campaign/reflux_origin_ledger.py:2250-2301,2328-2365` と `orchestrator/qualification/attempt_ledger.py:21-28,193-207,348-358` に揃える。

1. `record_sha256` を除いた上記 core object を作る。
2. S1 `canonical_json_bytes` で `ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False` の UTF-8 bytes にする。
3. `record_sha256 = sha256(core_bytes).hexdigest()`。
4. `seq == 0` の `previous_record_sha256` は `"0" * 64`。
5. `seq > 0` は直前 record の `record_sha256` と exact 一致。
6. full record を同じ canonical encoder で再 encoding し、末尾に一つだけ `b"\n"` を付ける。LF は hash 対象外。
7. reader は元 frame が再 encoding bytes と byte 一致しなければ拒否する。

hash-chain は破損・部分的差替えの検出であり、書込権限を持つ攻撃者に対する署名・真正性ではない。

### armed payload

`mutation_journal.py:new:L80-L170` の `armed.payload` exact keys は `repo`、`writer`、`targets` とする。

`repo`:

- `path: str`
- `root_dev: int`
- `root_ino: int`
- `head_oid: str`
- `worktree_incarnation_nonce: str`

`writer`:

- `hostname: str`
- `boot_id: str`
- `scheduler: {"kind": "pbs", "job_id_raw": str}`
- `pid: int`
- `pgid: int`
- `start_ticks: int`
- `cgroup: list[{"hierarchy_id": int, "controllers": list[str], "path": str}]`

各 `targets[]`:

- `path: str`
- `original: {"bytes_b64": str, "sha256": str, "size": int}`
- `mutated: {"bytes_b64": str, "sha256": str, "size": int}`
- S2 の `metadata`
- `mutation_temp: TempRegistration`
- `restore_temp: TempRegistration`

target は path 昇順、一意、repo-relative、symlink component 不可。base64 は strict decode 後に size/hash を再計算する。original と mutated の hash が同じなら拒否する。

他 state の payload:

- `mutated`: 全 target の post-replace `path/dev/ino/size/hash/mode/uid/gid`
- `restoring`: normal owner の quiescence evidence ref と全 target の復元直前 snapshot
- `recovering`: recovery writer identity、quiescence evidence ref、retry index、全 target の `ORIGINAL|MUTATED` 分類と prewrite hash
- `clean`: `normal|recovery`、最終 repo/HEAD、全 original hash/metadata、cleanliness evidence hash、quiescence evidence hash

evidence の意味検証は repair/harness 側の後続 scope とし、S3 は exact schema/hash と順序だけを検査する。

### 状態機械

`mutation_journal.py:new:L281-L390`:

| 現 state | 許可する次 state | 条件 |
|---|---|---|
| なし | `armed` | 唯一の genesis、`seq=0` |
| `armed` | `mutated` | 全 mutation commit と hash 検証済み |
| `mutated` | `restoring` | normal restore の最初の書込より前 |
| `restoring` | `clean` | 全 restore/fsync/検証済み |
| `armed` | `recovering` | 全 target preflight と quiescence authorization 済み |
| `mutated` | `recovering` | 同上 |
| `restoring` | `recovering` | 同上 |
| `recovering` | `recovering` | repair 途中 crash 後の再試行 |
| `recovering` | `clean` | 全 restore/fsync/検証済み |
| `clean` | なし | 唯一の terminal |

probe は `recovering` を current state として受け付けない (`t503_restore_durability_probe.py:326-328`) ため、README `:128-129` の過剰拒否を本番 FSM では繰り返さない。

### 順序を強制する API

`mutation_journal.py:new:L520-L940`:

- `MutationJournal.arm(root: TrustedRoot, plan: ArmedPlan) -> ArmedAttempt`
- `ArmedAttempt.apply_mutation(executor: MutationExecutor) -> MutatedAttempt`
- `MutatedAttempt.restore(executor: RestoreExecutor, verifier: CleanVerifier) -> CleanAttempt`
- `MutationJournal.recover(authorization: RecoveryAuthorization, executor: RestoreExecutor, verifier: CleanVerifier) -> CleanAttempt`
- arbitrary な `append(state)` は公開しない。

`docs/mutation-restore-durability-design.md:136-148` との対応:

1. `ArmedPlan` constructor が HEAD、path、bytes/hash、metadata、両 temp registration を全検証
2. `arm` が armed append + journal fsync
3. attempt dir fsync後、journal inodeへの `active` hard linkを `os.link` で no-overwrite publishし、親fsync
4. ここまで完了後にだけ `MutationExecutor` callback を呼ぶ
5. callback 内で S2 commit
6. 全 target postimage 検証後だけ `mutated`
7. restore callback 前に `restoring`、recovery callback 前に `recovering` を append+fsync
8. restore callback と verifier が全 file/dir fsync、HEAD、bytes、mode、cleanliness、quiescence evidence を返す
9. その後だけ `clean`
10. journal への staging hard linkを `last-clean.<attempt_id>` として作り親fsyncし、S1 `replace_name_at` で `last-clean` を更新。その後 `active` unlink + 親fsync
11. `CleanAttempt` が返るまで結果 ledger 用 capability は発行しない。実 ledger 配線自体は scope 外

append/fsync 失敗後は state object を poison し、同 object から後続 state、特に `clean` を発行できなくする。

`active` と attempt journal は hard link なので同じ `st_dev/st_ino` になる。clean append 後、locator cleanup 前に crash した場合は record を追加せず、既存 clean inodeから `last-clean` 更新と `active` unlinkだけを再開する。

### trusted root までの directory fsync

`mutation_journal.py:new:L391-L519`:

- canonical root の path 値ではなく、将来の resolver が開いた `TrustedRoot(fd, st_dev, st_ino, display_path)` を受け取る。
- root 自体は既存・provision 済みでなければならない。S3 は root より上の耐久性を主張しない。
- `repos/<sha256(repo-path)>/<incarnation>/attempts/<attempt-id>/` を safe component ごとに `mkdirat(0700)`。
- 各新規 mkdir 直後に親 fd を fsync。
- child は `O_DIRECTORY|O_NOFOLLOW|O_CLOEXEC` で openし、root と `st_dev` が違えば拒否。
- hierarchy 完成後も leaf から trusted root まで各 directory fd を順に fsync。
- symlink、`..`、slash/NUL、非 directory、root 外 escape、mount/device crossing をすべて無書込拒否。

これにより P2 は「自由な root path を渡す API」ではなく「canonical resolver が発行した fd capability を受ける API」として成立する。

### identity field の実在確認

`orchestrator/durable/process_identity.py:new:L1-L230` に取得・検証を集約する。

| field | 取得元 | この環境での確認 |
|---|---|---|
| repo path | resolved cwd と `git rev-parse --show-toplevel` の一致 | `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t503-restore-durability` |
| HEAD | hardened Git `rev-parse --verify HEAD` | 取得可能。将来 verifier は設計 `:265-271` に従い replace/lazy fetch を無効化 |
| worktree nonce | provisioner が作る immutable receipt | **取得不能**。現 `.git:1` は admin dir を指すだけで、その dir に `HEAD/index/gitdir/commondir/locked` 等はあるが nonce はない。admin path の再利用問題は設計 `:167-169` |
| hostname | `socket.gethostname()` | login は `pegasus02`。実測 writer は `evidence/legA-writer-info:1` の `bnode004` |
| boot ID | `/proc/sys/kernel/random/boot_id` | login で取得可能。今回 `2ccce62e-d29e-4c2e-81cc-49f5a9866b52` |
| scheduler job ID | exact env `PBS_JOBID` | login shellでは **取得不能/unset**。PBS script は `t503_restore_durability_probe.pbs:7-8,52-54` で必須。実測は `evidence/legA-writer-info:1` の `0:892334.nqsv` |
| PID | `os.getpid()` と `/proc/<pid>/stat` field 1 | 取得可能 |
| PGID | `/proc/<pid>/stat` field 5、`os.getpgid(pid)` と照合 | 取得可能。既存 parser は `tools/dev_waves/worker.py:104-121` |
| process start token | `/proc/<pid>/stat` field 22 | 取得可能。既存 strict parser は `campaign_claim.py:70-95`。実測 writer token も `evidence/legA-writer-info:1` に存在 |
| cgroup | `/proc/<pid>/cgroup` | login は `0::/user.slice/user-31609.slice/session-1909.scope` を確認。compute-job の cgroup は既存 probe 成果物に記録がなく、**実機値は未計測** |
| scheduler terminal ID | NQSV accounting の `Request ID:` | `evidence/legB2-scheduler-terminal.txt:5` は `892338.nqsv`。raw `PBS_JOBID` の先頭 `0:` だけを比較時に除く (`docs/pegasus-runbook.md:619-620`, probe `:296-318`) |

nonce、PBS job ID、boot/stat/cgroup のいずれかが取得不能・不正なら `armed` を書かない。`"unit-test"`、PIDだけ、空 cgroup等の代替値は作らない。

## テスト node の計画

テスト本体はすべて新規 test file に置き、既存テストの期待値は変更しない。

### S1 新規 nodes

- `orchestrator/tests/test_durable_jsonl.py::test_wal_facade_preserves_public_classes_signatures_and_import_modes`
- `...::test_wal_facade_emits_byte_identical_record_and_repair_receipt`
- `...::test_append_frame_uses_exact_flags_flock_tail_gate_and_parent_fsync_under_lock`
- `...::test_append_frame_completes_short_writes_and_zero_progress_fails_closed`
- `...::test_append_frame_maps_write_fsync_and_close_failures_without_masking`
- `...::test_strict_json_preserves_duplicate_nonfinite_cycle_surrogate_and_shared_dag_contract`
- `...::test_iter_binary_frames_does_not_decode_unterminated_multibyte_tail`
- `...::test_tail_repair_fsyncs_receipt_before_truncate_and_validates_complete_prefix`
- `...::test_tail_repair_missing_empty_and_framed_are_byte_stable_noops`
- `...::test_locked_multi_append_uses_the_shared_write_and_fsync_primitive`

既存必須 regression nodes:

- `test_campaign.py::test_wal_tolerates_truncated_last_line`
- `::test_wal_complete_invalid_final_line_is_not_treated_as_crash_prefix`
- `::test_wal_parse_line_rejects_nested_duplicate_and_unknown_top_level_key`
- `::test_wal_parse_line_rejects_invalid_basic_types_and_nonfinite_ts`
- `::test_wal_parse_line_requires_object_payload_and_checks_nested_duplicates_first`
- `::test_wal_log_rejects_falsy_nonobject_payload_but_none_means_empty_object`
- `::test_wal_blank_line_is_rejected_but_collected_reader_keeps_valid_records`
- `::test_wal_writer_rejects_nonstring_json_key_before_writing`
- `::test_wal_unterminated_complete_json_is_always_truncated_tail`
- `::test_wal_multibyte_partial_tail_is_not_decoded`
- `::test_wal_terminated_invalid_utf8_is_line_issue_not_tail`
- `::test_wal_terminated_invalid_json_is_line_issue_not_tail`
- `::test_wal_append_rejects_every_unterminated_tail_without_changing_bytes`
- `::test_wal_repair_tail_then_append_restores_independent_frames`
- `::test_wal_repair_without_any_newline_truncates_to_zero`
- `::test_wal_repair_missing_empty_and_framed_are_noops`
- `::test_wal_repair_receipt_is_durable_and_complete_before_truncate`
- `::test_wal_append_completes_short_writes_and_rejects_zero_progress`
- `::test_wal_append_fsyncs_directory_under_flock_on_every_append`
- `::test_wal_append_maps_wal_close_failure_to_structured_error`
- `::test_wal_repair_hashes_large_removed_tail_incrementally`
- `::test_wal_reader_stage_contract_is_exact_and_unknown_stage_fails_closed`
- `::test_wal_writer_stage_contract_is_exact_and_unknown_stage_fails_closed`
- `::test_wal_payload_deep_type_rejections_happen_before_open`
- `::test_wal_payload_accepts_ordered_dict_native_tree_and_shared_dag`
- `::test_wal_reader_rejects_raw_nonfinite_payload_constants_and_overflow`
- `::test_wal_exception_hierarchy_and_append_attributes_are_separate`
- `::test_wal_append_and_repair_wait_for_exclusive_flock`
- `::test_wal_records_by_stage_last_wins_per_stage`

### S2 nodes

- `orchestrator/tests/test_atomic_replace.py::test_prepare_returns_durable_registered_name_inode_and_hash_before_commit`
- `...::test_temp_name_is_deterministic_same_directory_and_collision_fails_closed`
- `...::test_prepare_rejects_symlink_nonregular_hardlink_and_path_escape_before_target_change`
- `...::test_prepare_rejects_unpreservable_mode_uid_gid_times_xattrs_and_inode_flags`
- `...::test_prepare_short_or_zero_write_leaves_target_unchanged_and_cleans_exact_temp`
- `...::test_commit_rechecks_live_target_inode_hash_and_metadata_before_replace`
- `...::test_commit_rejects_temp_name_inode_hash_or_parent_identity_mismatch`
- `...::test_temp_file_and_temp_directory_entry_are_fsynced_before_prepare_returns`
- `...::test_commit_fsyncs_target_directory_after_replace`
- `...::test_commit_preserves_mode_uid_gid_atime_mtime_and_registered_temp_inode`
- `...::test_post_replace_directory_fsync_failure_is_indeterminate_not_success`
- `...::test_discard_only_unlinks_the_exact_registered_temp_and_fsyncs_parent`
- `...::test_pre_registration_failure_never_changes_live_target`

### S3 nodes

- `orchestrator/tests/test_mutation_journal.py::test_record_hash_is_sha256_of_canonical_core_and_chains_previous_hash`
- `...::test_reader_rejects_noncanonical_json_duplicate_key_truncated_tail_seq_gap_and_hash_tamper`
- `...::test_reader_rejects_unknown_schema_extra_fields_and_illegal_transition`
- `...::test_clean_is_the_only_terminal_and_rejects_every_suffix`
- `...::test_transition_table_accepts_normal_and_each_recovery_edge`
- `...::test_recovering_can_repeat_after_repair_crash`
- `...::test_armed_binds_repo_nonce_scheduler_pid_pgid_start_cgroup_original_bytes_metadata_and_both_temps`
- `...::test_armed_rejects_bad_base64_hash_temp_identity_and_duplicate_target_path`
- `...::test_capture_identity_reads_boot_pid_pgid_start_cgroup_and_raw_pbs_jobid`
- `...::test_capture_identity_rejects_missing_pbs_nonce_boot_stat_or_cgroup`
- `...::test_capture_identity_never_synthesizes_a_worktree_nonce`
- `...::test_arm_fsyncs_record_attempt_directory_and_active_parent_before_first_mutation_callback`
- `...::test_active_is_a_no_overwrite_hardlink_to_attempt_journal`
- `...::test_mutated_is_appended_only_after_all_target_hashes_verify`
- `...::test_restoring_or_recovering_is_fsynced_before_first_restore_callback`
- `...::test_any_other_target_preflight_prevents_every_restore_callback`
- `...::test_clean_requires_file_directory_head_bytes_mode_cleanliness_and_quiescence_verification`
- `...::test_last_clean_is_fsynced_before_active_unlink`
- `...::test_clean_locator_cleanup_resumes_without_appending_after_crash`
- `...::test_append_failure_poisons_attempt_and_prevents_clean`
- `...::test_hierarchy_fsyncs_each_created_parent_through_trusted_root`
- `...::test_hierarchy_rejects_symlink_non_directory_device_crossing_and_path_escape`
- `...::test_unterminated_tail_requires_explicit_repair_and_never_rounds_unknown_to_clean`

probe の既存 `test_writer_fsyncs_armed_before_first_target_write`、`test_repair_refuses_when_any_target_is_other`、`test_clean_is_recorded_only_after_restore_verification`、`test_writer_fsyncs_temp_before_replace` (`orchestrator/tests/test_t503_restore_durability_probe.py:67-132`) は production tests の代用にせず、そのまま残す。

## proof-chain consumer の受理集合

このプランでは受理集合を変えない。ただし「`wal.py` が byte pin されていない」ことだけでは十分な根拠ではない。

- `s8b_oracle_report.py:1264-1293` は `wal.read_records_collected` の record、line issue、truncated-tail を受理判定へ直接使う。したがって例外名・framing・parse のわずかな drift でも受理集合は変わる。S1 facade regression が必要である。
- `s8b_ratified_freeze.py` は campaign WAL を import せず、独自 `_strict_load` (`:381-415`) と `_strict_jsonl` (`:1450-1468`) を使い、`:2870-2875` から別の floor journal を検証する。S1〜S3 はここへ接続しない。
- oracle manifest の `_GENERATOR_SOURCES` は `s8b_oracle_manifest.py:44-52` の exact 5 source であり、validation は `:411-450`。`wal.py` は含まれない。
- `test_s8b_oracle_manifest.py:428-465` はむしろ `wal.py` を extra/unrelated generator として拒否している。
- qualification pin は `orchestrator/qualification/contract.py:38-66`。`atomic_publish.py` は含むが `wal.py` と新 durable 層は含まない。
- `FROZEN_MANIFEST` は `orchestrator/tests/test_frozen_artifacts.py:38-85` の成果物 bytes だけである。

新 durable module をこの wave で `_GENERATOR_SOURCES` や frozen key-setへ追加すると exact key 集合と receipt bytesが変わるため行わない。これは既存の transitive source-closure の盲点を強化しないという意味であり、別 wave の proof-chain hardening 候補である。

proof consumer regression nodes:

- `test_layer3_report.py::test_unknown_stage_fails_closed`
- `::test_nested_duplicate_wal_key_fails_closed_for_one_reason`
- `::test_wal_wrapper_preserves_specific_parser_diagnosis`
- `::test_wal_blank_between_records_uses_shared_strict_contract`
- `::test_unframed_wal_tail_is_translated_with_framing_cause`
- `test_backoff_consumers.py::test_plot_backoff_rejects_duplicate_tps_before_it_reaches_plot_data`
- `::test_plot_backoff_rejects_blank_line_between_records`
- `::test_plot_backoff_rejects_unframed_tail_without_returning_partial_data`
- `test_s8b_oracle_report.py::test_complete_invalid_raw_final_line_is_rejected`
- `::test_invalid_line_after_terminal_cannot_hide_its_physical_position`
- `::test_invalid_line_does_not_mask_definitive_correctness_red`
- `::test_truncated_tail_does_not_mask_definitive_correctness_red`
- `::test_blank_line_between_valid_records_is_unconditional_violation`
- `::test_truncated_raw_tail_after_completed_terminal_is_one_protocol_reason`

## provisional 裁定 P1〜P4

- P1: 成り立つ。ただし「pin がないから不変」という根拠だけは不十分。oracle report が runtime で WAL semantics に依存するため、薄い facade と上記 regression を成立条件に追加する。
- P2: 条件付きで成り立つ。自由な `Path root` を公開引数にすると設計 `:162-169` の split-brain を作るので不可。canonical resolver が発行する `TrustedRoot` fd capability を受ける形なら後続 root 実装で API を壊さない。
- P3: 成り立つ。`tools/mutation_harness.py`、producer entrypoint、consumer gateから新 moduleを importしない。
- P4: 成り立つ。`tools/mutation_harness.py:767-788,1251-1332,1790-1811` を編集しない。ただし現行 in-place writer の危険は残る。

コード読解で全面的に成り立たない P はない。親の追加裁定が必要なのは、P2 の capability 解釈と、xattr/ACL/inode flags を「非対応なら拒否」に固定する metadata policy である。

## scope 外依存と完成範囲

S1、S2、S3 の codec/FSM/順序 API/祖先 fsync は、repair CLI、canonical root、consumer lease、harness 配線なしで実装・単体検証できる。

一方、以下は scope 外機構なしには production で完了しない。

- 現 worktreeには incarnation nonce がなく、login shellには `PBS_JOBID` もないため、実 identity で `armed` を作れない。
- `recovering → clean` の安全な authorization は scheduler terminal、orphan child、cgroup の quiescence verifier が必要。
- pre-arm crash の未登録 temp を consumer が無視しないため quarantine/admission gate が必要。
- non-cooperative writer との live-hash/replace TOCTOU は専有 worktreeまたはleaseが必要。
- canonical rootがなければ `TrustedRoot` capabilityの発行者がいない。
- `CleanAttempt` 後の ledger 配線がないため、結果公開順序はまだ producer に適用されない。

したがって brief `:31-37` の repair CLI、canonical root、consumer lease、harness 配線を本 waveへ引き込まない一方、これらなしに「転換完了」「自動修復可能」「consumer安全」とは呼ばない。

物理ノード死、client eviction、OST/MDT failover、電源断後の fsync bytes 永続性は引き続き未計測である (`design:397-408`, liveness README `:52-59`)。本計画は成功した syscall の順序だけを契約し、その後の物理永続性を前提にしない。

pytest は実走しておらず、緑は主張しない。既存テストの期待値変更、受理集合の拡大・縮小、ファイル編集はいずれも提案していない。

## 総括

骨子は、S1 の薄い facade で WAL の型・bytes・受理集合を固定し、S2 を「durable temp準備」と「再検査付きcommit」に分け、S3 が typestate API で armed-before-write と clean-after-verification を強制する構成である。

最大のリスクは、非協調 writer との TOCTOU、pre-arm temp crash、実在しない worktree nonce、未実装の quiescence/consumer quarantine である。親は `TrustedRoot` capability 方式、metadata 非対応時の全面拒否、pre-arm残骸を今 waveでは quarantine 前提の未解消 liveness とする点を裁定すべきである。