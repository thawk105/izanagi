## 調査前提

指定された親 brief、production、対象テスト、T-663 の一次資料をすべて読了しました。作業木は clean で、コード編集・テスト実走は行っていません。以下は段 2 契約に従う静的プランであり、緑は主張しません。

## 1. 再評価点の設計択一

| 案 | 裁定 | 理由 |
|---|---|---|
| P1 | 原文のままは不採用。後述の P1′へ置換 | `_stage_receipt_write` 後に gate を置くだけでは、`_atomic_create_json_reserved` が同じ JSON をもう一度 temp write/fsync するため、その二度目だけが停滞する穴が残る。 |
| P2 | 採用 | `wall_clock_scope` は引き続き `actuals.wall_clock_s` の終点、すなわち receipt field 確定時点を表せる。schema 変更は不要。 |
| P3 | 条件付き採用 | flip 時の output unlink・flag 復元・receipt 再構築は正しい。ただし unlink 後の親 directory fsync と、古い staged temp の破棄を手順へ加える。 |
| P4 | 採用 | 1 回制限は便宜的な打切りではなく、`accepted=True → False` だけの単調遷移だから十分。flip 後は再び accepted にならない。 |

### 採用案 P1′

現在の `tools/codex_worker_launch.py:445-472,1625-1628` を変え、`_stage_receipt_write` が fsync 済み temp を削除せず返し、`_atomic_create_json_reserved` がその同一 temp を `link` / `replace` するようにします。

最終 gate は次をすべて終えた後に置きます。

1. output の create-only 公開と hash 再照合 (`tools/codex_worker_launch.py:1730-1738`)
2. published output を含む `_audit_receipt_value`
3. 最終 receipt と同じ bytes の serialize・temp write・file fsync
4. `_latch_final_job_limit`

その時点でまだ accepted なら、保持した temp をそのまま receipt final path へ公開します。これにより、gate 後の二度目の JSON write/fsync を除去できます。

### create-only 制約下での「publication 完了後」

receipt の最終 path が公開された後に再評価し、超過なら取り消す、という文字どおりの要求は満たせません。`os.link` / `os.replace` が成功した瞬間から別 consumer が accepted receipt を読めるためです。

したがって満たせるのは、次の意味です。

> output publication と receipt の全可逆な prepublication 作業を完了した後、最後の取消可能点で wall gate を再評価する。

残る測定不能区間は次です。

- `os.link` または invalid partial に対する `os.replace` (`tools/codex_worker_launch.py:452-457`)
- final directory entry の `_fsync_parent` (`:458`)
- temp cleanup、receipt lock の unlock/close、関数 return (`:468-472,438-442,1762`)

この区間が 10〜20 秒停滞するケースは create-only のままでは完全には塞げません。ただし staged temp の再利用により、現在そこに含まれる JSON serialize・file write・file fsync は gate の前へ移せます。

## 2. `_run_supervised` の改修プラン

### helper 面

- `tools/codex_worker_launch.py:445-472`
  - `_atomic_create_json_reserved` を「value から temp を作る関数」から「呼出側が用意した fsync 済み temp を公開する関数」へ変更する。
  - `replace_invalid=False` は staged temp を `os.link`、`True` は `os.replace`。
  - 例外時の final path rollback と temp cleanup は現行どおり維持する。

- `tools/codex_worker_launch.py:475-484`
  - 汎用 `_atomic_create_json` は `_write_json_temp` を自分で呼び、その temp を変更後の `_atomic_create_json_reserved` へ渡す。
  - これにより早期 launcher-error 経路の外部挙動は変えない。

- `tools/codex_worker_launch.py:1625-1628`
  - `_stage_receipt_write(...) -> Path` とし、`_write_json_temp` が返した temp を削除せず返す。
  - 呼出側は必ず atomic publication に渡すか、`finally` で unlink するという所有契約を docstring に固定する。

- `tools/codex_worker_launch.py:1795-1798`
  - `_publish_launcher_error_receipt` も新しい helper 契約に合わせて temp を明示的に作って渡す。
  - outcome や rc は変更しない。

### before

`tools/codex_worker_launch.py:1727-1762` の現行順序は次です。

1. receipt slot 予約
2. accepted なら output 公開
3. wall gate
4. flip なら output unlink
5. receipt audit
6. `_stage_receipt_write` が temp write/fsync 後に削除
7. `_atomic_create_json_reserved` が再度 temp write/fsyncして公開
8. receipt の `launcher_rc` を返す

したがって 5〜7 の費用は最後の gate に入っていません。

### after

同範囲を次の制御フローへ変更します。

1. `_reserve_receipt_slot` は現在どおり output 公開より前に取得し、receipt 公開まで保持する。
2. candidate `receipt["outcome"] != "accepted"` なら、audit → stage → staged temp の atomic create とする。wall 再評価はしない。
3. candidate accepted なら output を公開し、直後に `args.output_published_by_run=True`。
4. output hash を照合し、`_audit_receipt_value(..., check_published_output=True)` を実行。
5. accepted receipt を `_stage_receipt_write` し、fsync 済み temp を保持。
6. その後に `_latch_final_job_limit` を実行する。
7. `attempts[-1]["accepted"]` がまだ真なら、保持した temp を `_atomic_create_json_reserved` へ渡し、rc=0。
8. 偽へ flip した場合:
   - staged accepted temp を unlink
   - published output を unlink
   - output directory を `_fsync_parent`
   - durable な削除完了後に `args.output_published_by_run=False`
   - `_receipt` を再実行
   - `_audit_receipt_value(..., check_published_output=False)` を再実行
   - not-accepted receipt を再 staging
   - その temp を atomic create
   - rc=1
9. 途中例外では `args.output_published_by_run` が真の間、既存の `_publish_launcher_error_receipt` (`:1765-1798`) が最後の cleanup を担う。

`_receipt` は渡された `attempts` を深いコピーにしていないため (`:1437-1443`)、latch 後の in-memory `receipt["attempts"]` は変化します。一方 staged bytes は latch 前の snapshot です。したがって flip 判定には古い top-level `receipt["outcome"]` を使わず、`attempts[-1]["accepted"]` を使い、flip 時は staged bytes を必ず破棄して `_receipt` から再構築します。

### `outcome != "accepted"` の再評価

不要です。

- `not_accepted` は既に受理集合外であり、再評価しても安全性は増えません。
- 再評価すると、例えば既存の `stop_reason=max_attempts` が publication 遅延だけで `max_wall_clock_s` に変わり、T-678 と無関係な拒否理由の分類を変更します。
- `launcher_error` の早期経路 (`:1640-1654,1669-1682`) と fallback (`:1765-1798`) も既に rc=2、output 非公開です。

再評価対象を accepted candidate に限定することで、受理集合だけを縮め、既存の拒否集合内の分類を保ちます。

## 3. 不変条件の維持

### `_writer_truth` の真理値表

`tools/codex_worker_launch.py:1328-1343` は変更しません。

| 条件 | `outcome` | `stop_reason` | `launcher_rc` |
|---|---|---|---:|
| 最終 attempt が accepted、全 attempt に trigger なし | `accepted` | `completed` | 0 |
| いずれかの attempt に trigger あり | `not_accepted` | 最初の trigger | 1 |
| trigger なし、attempt 上限消化 | `not_accepted` | `max_attempts` | 1 |
| 上記以外 | `launcher_error` | `launcher_error` | 2 |
| `_receipt(..., force_launcher_error=True)` | `launcher_error` | `launcher_error` | 2 |

今回の flip は最終 attempt に `limit_trigger=max_wall_clock_s` を設定し、`accepted=False` にする (`:1594-1617`) ため、第2行へ移るだけです。逆方向の遷移はありません。

同時に `_receipt` (`:1374-1444`) は次を自動的に再導出します。

- `output_sha256=None`
- `outcome=not_accepted`
- `stop_reason=max_wall_clock_s`
- `launcher_rc=1`
- `possible_unobserved_overshoot=True`

### schema v2

次は一切変更しません。

- `_RECEIPT_FIELDS_V2` (`tools/codex_worker_launch.py:110-144`)
- `_RECEIPT_V2_ONLY_FIELDS` (`:145-153`)
- `schema_version=2` (`:1402`)
- `_validate_receipt` の closed field 検査 (`:1951-1973`)
- accepted/not-accepted/launcher-error の checker-side truth table (`:2098-2139`)

### `wall_clock_scope`

`"launcher_start_to_receipt_fields_finalized"` を維持します。

この文字列は `actuals.wall_clock_s` の終点を表します。accepted の最終 admission check はそれより後ろへ移りますが、receipt に記録された wall 値自体の意味は変えません。atomic publication 完了までを記録したとは主張しません。

文字列を変更すると次が影響を受けます。

- v2 exact literal validator: `tools/codex_worker_launch.py:2032-2039`
- positive fixture: `orchestrator/tests/test_codex_worker_launch.py:1640-1645`
- diagnostic receipt fixture: `:1169-1195`
- v1 compatibility test: `:2384-2424`
- 既存実 receipt: `/work/1/SFC/tanab/dev-wave-jobs/task-inventory/review-a/receipt.json:1`

実 receipt は静的確認上 `schema_version=2`、現行 literal、closed field 集合を持っています。literal を変えるなら schema v3 と consumer migration が必要ですが、今回それを行う理由はありません。

## 4. 追加するテスト

配置は `orchestrator/tests/test_codex_worker_launch.py:2035-2104` 付近の finalization failure 群が適切です。

### 新規 node 1

`test_receipt_staging_wall_overrun_flips_to_not_accepted_and_removes_output`

- `_write_fake_codex`、`_base_command`、`_run_main_in_process`、`monkeypatch` を使用する。
- `_run_case` は launcher を別 process で起動するため monkeypatch が届かず、このテストには使わない。
- production の clock seam は追加しない。
- test 内で元の `LAUNCHER.time.monotonic_ns` を保存し、offset を加える wrapper を monkeypatch する。
- `_stage_receipt_write` の one-shot wrapper は:
  1. 元関数を実行
  2. `paths["output"].exists()` を確認して output が実際に公開済みだったことを記録
  3. monotonic offset を 4 秒進める
  4. staged temp をそのまま返す
- `max_wall="3"` とし、実 sleep は使わない。
- 期待値:
  - rc=1
  - `outcome=not_accepted`
  - `stop_reason=max_wall_clock_s`
  - `launcher_rc=1`
  - 最終 attempt の `accepted is False`
  - `limit_trigger=max_wall_clock_s`
  - output 不在
  - receipt temp の残骸なし
  - `args.output_published_by_run` の cleanup が働いたこと

変更前は stage 後に latch がないため rc=0・accepted・output 残存となり赤、変更後は上記 flip で緑になります。

### 新規 node 2

`test_accepted_receipt_publication_reuses_prepublication_staged_temp`

- 同じ in-process helper 群を使う。
- `LAUNCHER._write_json_temp` を wrapper 化し、`path == paths["receipt"]` の呼出回数だけ数える。manifest 書込みは除外する。
- 通常 fake、`max_wall="3"` で outcome accepted、output 存在、receipt temp write がちょうど1回であることを固定する。

変更前は `_stage_receipt_write` と `_atomic_create_json_reserved` が各1回、計2回書くため赤です。変更後は staged temp の再利用により1回となり緑です。このテストがなければ「二度目の write だけが停滞する」P1 の残存穴を再導入できます。

### 維持する正の対照

新規テストではありませんが、`test_positive_p1_normal_job_is_accepted` (`:1630-1669`) を正常経路の必須対照とします。期待値は変更せず、予算内なら accepted / completed / rc=0 / output 存在を保ちます。

併せて次の既存 node を関連回帰として走らせます。

- `test_receipt_publication_failure_removes_output_and_writes_error_receipt` (`:2077-2104`)
- `test_complete_receipt_publication_is_atomic_create_only_at_run_callsite` (`:2235-2309`)
- `test_check_receipt_reads_v1_field_sets_with_explicit_skip_diagnostics` (`:2384-2424`)
- `test_check_receipt_rejects_unknown_and_duplicate_fields` (`:2928-2953`)

### 外側 timeout

`_run_launcher_subprocess` と direct `Popen` helper の timeout は10秒です (`:528-552,555-575,610-632`)。新規2 test は in-process かつ fake clock offset なので、この timeout は発火しません。timeout を20秒へ広げる案は出しません。

実 sleep を使った親の追試では、既存 brief と同じ4秒遅延なら通常所要込みでも10秒未満が見込まれますが、これは親が実測すべき事項です。12秒の subprocess delay は外側 timeout が先に発火するため、inner gate の証拠には使えません。

## 5. 波及する consumer

repo 内で launcher receipt の当該 field を実行時に読む Python 面を検索した結果、`tools/codex_worker_launch.py` と対象 test file 以外の executable consumer はありません。ほかのファイルにある一般名 `outcome` / `accepted` は別 schema です。

### production

- attempt の accepted 構築: `tools/codex_worker_launch.py:994-1075`
- writer truth table: `:1328-1343`
- receipt 組立て: `:1374-1444`
- final wall latch: `:1594-1617`
- publication と rc 返却: `:1631-1762`
- exception cleanup: `:1765-1798`
- attempt semantic binding: `:1832-1948`
- schema/literal/truth-table validator: `:1951-2148`
- sealed artifact auditと outcome→checker rc: `:2288-2417`
- `check-receipt` CLI rc: `:2420-2452,2532-2574`

挙動が変わるのは、従来 accepted だった「output/audit/staging 後に wall 超過した job」だけです。`run` と `check-receipt` は0から1へ、output は存在から不在へ変わります。既存の accepted 正常 job、既存の not-accepted job、launcher-error jobは変えません。

### テスト

- 診断 consumer: `orchestrator/tests/test_codex_worker_launch.py:169-219,291-337`
- schema v2 の合成 receipt: `:1097-1216`
- 診断契約 tests: `:1219-1627`
- accepted/limit truth-table tests: `:1630-1991`
- launcher-error finalization tests: `:2008-2104`
- create-only race: `:2235-2309`
- v1/v2 compatibility・closed schema: `:2384-2424,2928-2972`
- 後半の rejected/accepted consumers: `:2618-2706,2777-2885,2991-3004,3042-3058`

既存期待値は変更しません。新しい遅延注入 node だけが新しい rejected 行を観測します。

### docs・記録

実行時 parser ではありませんが、意味契約として次が影響範囲です。

- wall hard-cap と非採用契約: `docs/decisions.md:4422-4457` (D100)
- 予算を広げない裁定: `docs/decisions.md:11524-11545` (D249)
- Phase 3 の launcher 概要: `docs/phase3.md:696-708`
- F57 の受理 conjunct 診断: `docs/failures.md:1477-1492`
- T-678 起票: `docs/archive/worklog-phase3-0809-324-325.md:465-467`
- 出処: `output/insights/2026-08-09_t663-launcher-flake-diagnostic/s3-lensA.md:43-51`
- 裁定候補 S2: 同 `s4-adjudication.md:69-75`

歴史資料は書き換えません。親が段 7 で新 insight と worklog fragment に、P1′、create-only の残余、実測結果を記録すべきです。

## 6. 親が実測すべき項目

- 新規2 node が変更前赤・変更後緑になること。
- `test_positive_p1_normal_job_is_accepted` が引き続き accepted になること。
- 4秒の実 sleep を `_stage_receipt_write` に一時注入した実時間対照で rc=1、output 不在になること。
- accepted 正常経路で receipt 向け `_write_json_temp` が本当に1回だけであること。
- flip、atomic-create 例外、race の全経路で temp/output 残骸がないこと。
- create-only race が引き続き `[0,2]` となり、敗者の output が残らないこと。
- target file の直列走と親の標準受入全走。必ず `python3 tools/run_tests.py` 経由で実施すること。
- 実 receipt `review-a/receipt.json` を現行 `check-receipt` で検査し、schema v2 互換を実測すること。
- `python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py`、commit 後の provenance 検査。
- 最終 `link/replace + directory fsync` の残余時間は gate に入らないため、その限界を記録で欠落させないこと。

## 総括

- P1 はそのまま採らず、fsync 済み staged temp を最終 publication に再利用する P1′へ置換する。
- 最後の可逆 gate は output 公開・audit・exact receipt staging の後、receipt final path 公開の直前に置く。
- flip は `not_accepted / max_wall_clock_s / rc=1` とし、output を durable に削除してから receipt を再構築する。
- schema v2、closed fields、`wall_clock_scope` literal、既存 receipt 互換は変更しない。
- 最大の残余は create-only atomic link/replace と directory fsync 自体を publication 後に再評価できない点である。
- テストは未実走であり、新規2 node・関連回帰・実 receipt 互換の実測を親へ申し送る。