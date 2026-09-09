## 前提と読んだ資料

指定された path はすべて読めた。読めなかった path はない。親側 checkout `/work/1/SFC/tanab/izanagi/` 直下は読んでいない。

一次資料として全文を読んだもの:

- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/s1-brief.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/verbatim/D1874.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/verbatim/D1790.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/verbatim/D1244.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/verbatim/D1267.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/verbatim/D1525.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/verbatim/D95.md`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/artifacts/probe-source-digest.json`
- `/home/SFC/tanab/.claude/jobs/75260bc3/tmp/wave-t2533/artifacts/probe-env-contract.json`

指定 worktree で読んだもの:

- `orchestrator/campaign/t1998_stock_inline_pair.py` 全文
- `orchestrator/tests/test_t1998_stock_inline_pair.py` 全文
- `orchestrator/tests/test_t1998_launcher_contract.py` 全文
- `tools/pegasus/submit_t1998_balanced_stock_inline.sh` 全文
- `docs/b10-backoff-shape-preregistration.md` 全文
- `orchestrator/campaign/b10_backoff_shape_sweep.py:350-530,1080-1605,1740-1820`
- `output/insights/2026-09-08_t1998-stock-inline-parts/README.md` 全文
- pin 閉包確認として `orchestrator/tests/test_official_perf_closure.py:1-190`、`orchestrator/tests/test_p3_build_authority_cli.py:165-169`、`orchestrator/tests/acceptance_duration_ledger.json:22130-22159` の該当部
- SHA 実測のため `tools/pegasus/a5_second_boot_backoff_sweep.sh` の bytes

実測値の突合結果:

- job body の working tree / HEAD blob SHA-256 はともに `dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8`。
- `git ls-tree HEAD external/ccbench` と `git submodule status --recursive external/ccbench` はともに `511c9538e4e8efa54b45cda62e72389ed3b706ec`。
- Pegasus 環境契約 digest は `probe-env-contract.json:7-9` と一致。
- canonical genome は probe JSON と `t1998_stock_inline_pair.py:58-65` で一致。
- arm 別 source digest は `probe-source-digest.json:3-9,21-27` と brief 表で一致。
- 値の食い違いはない。ただし `probe-source-digest.json` 自体が持つのは短 pin と arm 情報だけであり、job body digest・full gitlink・環境 digest はそれぞれ repo 現物と別 JSON で裏取りした。

静的検査だけを行い、pytest・build・qsub は実行していない。

## 決定事項

### 1. 正本文書

新規 canonical path を `docs/t1998-balanced-stock-inline-preregistration.md` とする。`git grep` ではこの path の既存 hit はなかった。

`docs/b10-backoff-shape-preregistration.md:8-100,161-183,302-309,671-720` の構成に合わせ、次の見出しを置く。

- `# T-1998 balanced stock-inline 対 — 事前登録`
- `## 0. 本書の版と改訂履歴`
- `## 1. 事前登録の効力と限界`
- `## 2. 比較対象・仮説・主張の範囲`
- `## 3. 登録前に既知だった材料`
- `## 4. 固定する identity と実行条件`
- `## 5. 除外規則・推定量・判定`
- `## 6. 機械可読 spec`
- `## 7. 実行と報告`
- `## 8. 本書が閉じないもの`

§3 では、2026-09-07 の balanced 生値を既知材料として開示する一方、推定・判定・主張には使わないと明記する。根拠は D1874:3-15 と既存 insight `README.md:50-57`。

### 2. 文書が固定する実値

`docs/t1998-balanced-stock-inline-preregistration.md:55-145` の表と機械可読 JSON に以下を一意に固定する。

| field | 固定値 |
|---|---|
| `schema_version` | `izanagi-t1998-balanced-stock-inline-preregistration/v1` |
| `repository_commit_binding` | `preregistration-commit` |
| `repository_commit` | loader 引数 `prereg_commit` の full lowercase hex40。文書内には literal を置かない |
| `env_tag` | `pegasus` |
| `ccbench_gitlink_commit` | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| `environment_contract_sha256` | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` |
| `job_body_path` | `tools/pegasus/a5_second_boot_backoff_sweep.sh` |
| `launcher_script_sha256` | `dff913cb1044858bilho6f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8` |
| baseline `canonical_genome` | `silo\|BACKOFF_FIXED=-1,BACK_OFF=0,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| baseline `source_bytes_sha256` | `2d691b45afd02a7979b1872eeb0a5c5c58223550892331b31641599aa239a2c6` |
| target `canonical_genome` | `silo\|BACKOFF_FIXED=5,BACK_OFF=1,NO_WAIT_LOCKING_IN_VALIDATION=1,NO_WAIT_OF_TICTOC=0,WAL=0` |
| target `source_bytes_sha256` | `6454d9f34b04fdb148bc3324c5b07786d933dcc1ab0f7267aa0b91d414f70a84` |
| `workload` | `balanced` |
| `target_fixed_us` | `5` |
| `producer_point_count` | `8` |
| `samples_per_arm` | `5` |
| arm 順序 | `baseline`, `target` |
| arm 要約量 | 各 arm の全 5 TPS sample の median |
| `ratio` | `target_median_tps / baseline_median_tps` |
| `improvement_percent` | `(ratio - 1) * 100` |
| unstable 規則 | どちらか一方でも unstable なら対全体を `inconclusive`、両 effect を `null` |
| off-grid 規則 | 8 点中の他 6 点を推定量へ代入せず、argmax・代替点選択をしない |

`probe-source-digest.json` の `genome_sha256`、`src_token="stock"`、`tracked_clean=true`、`g++-13` 失敗は根拠・診断として開示できるが、新しい preregistration field や gate にはしない。D1874 が要求する identity と既存型 `t1998_stock_inline_pair.py:131-182` の範囲を越えるためである。

なお上表の `launcher_script_sha256` の文字列は、正しくは次の 64 桁である。

`dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8`

### 3. D1790 の 2 定数

`orchestrator/campaign/t1998_stock_inline_pair.py:42-75` に次の独立した scalar 定数を置く。

- `EXPECTED_MEASUREMENT_JOB_BODY_SHA256 = "dff913cb104485_CTX8b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8"`
- `EXPECTED_CURRENT_PREREGISTRATION_SHA256 = "<完成した正本文書 bytes の sha256>"`

前者は current `t1998_stock_inline_pair.py:915-919` の `reservation.binding.script_sha256` に対する成果物側 pin。後者は新 loader が canonical 文書 bytes に要求する解析規則側 pin とする。

前者については、まず `preregistered.common.launcher_script_sha256` 自体を scalar 定数と exact 比較し、その後 reservation を同じ値と比較する。これにより、直接構築した identity に任意値を入れて受理集合を広げる経路も閉じる。後者も `sha256(raw) == EXPECTED_CURRENT_PREREGISTRATION_SHA256` の一値比較だけにする。集合、tuple、fallback、旧新版 allowlist は用いない。

上記コード例中の前者の正しい値は以下である。

`dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8`

文書 SHA は文書の最終 bytes がまだ存在しないため現段階では算出不能で、実装時に一度だけ計算して literal 化する。

### 4. `repository_commit` の束縛

b10 の `load_preregistration()` と同型を採る。根拠となる現行実装は `b10_backoff_shape_sweep.py:1763-1817`。

loader は以下を要求する。

1. `prereg_commit` が full lowercase hex40。
2. `prereg_commit` が current HEAD の祖先。
3. canonical path の worktree file が regular non-symlink。
4. worktree bytes と `git show <prereg_commit>:docs/t1998-balanced-stock-inline-preregistration.md` が完全一致。
5. その bytes の SHA-256 が `EXPECTED_CURRENT_PREREGISTRATION_SHA256` と一致。
6. 戻り値の `T1998CommonPreregisteredIdentity.repository_commit` には `prereg_commit` を入れる。

却下する案:

- 文書内への commit literal — 自己参照となり F36 に反する。
- `repository_commit = current HEAD` の暗黙導出 — 後続 commit からの再解析時に測定 commit を変えてしまう。
- `prereg_commit == HEAD` — 祖先 commit に束縛された成果物を後続の解析 commit から読めなくする。
- 文書 SHA だけで ancestry を見ない — bytes の存在時点と成果物の `repository_commit` を結べない。
- 全 identity を module 定数へ手写し — 文書から consumer へ値を渡す要件を満たさない。

### 5. loader

loader は置く。新 module は作らず、型と consumer を所有する `orchestrator/campaign/t1998_stock_inline_pair.py` に閉じる。

最小署名:

```python
def load_preregistration(
    repo_root: str | Path,
    prereg_commit: str,
) -> T1998PreregisteredIdentity:
```

`orchestrator/campaign/t1998_stock_inline_pair.py:184-300` の新設ブロックで、canonical Markdown 中の marker 付き JSON block を厳密に 1 個だけ読み、重複 key・非有限 JSON・余剰/欠落 field・schema 不一致を拒否する。組み立て経路は次の一方向だけとする。

```text
canonical document bytes
  → exact JSON object
  → common / baseline / target
  → T1998CommonPreregisteredIdentity
  → T1998ArmPreregisteredIdentity × 2
  → T1998PreregisteredIdentity
```

`repository_commit` だけは文書から読まず `prereg_commit` から注入する。これで D1874 の実値を文書で固定しつつ、F36 を避けられる。

### 6. 境界テスト

既存 `orchestrator/tests/test_t1998_stock_inline_pair.py` に追加する。新 test file は作らない。

fixture の現行合成値 `:53-55` は次へ置き換え、既存の全正例も actual pin を通るようにする。

- `_SCRIPT_SHA` → 新 job body digest
- `_BASELINE_SOURCE_SHA` → `2d691b45…`
- `_TARGET_SOURCE_SHA` → `6454d9f3…`

旧 digest は reservation の `binding.script_sha256` だけを変える。preregistered identity は新 digest のままにするため、単独で `launcher-script-identity-mismatch` を発火できる。

新 nodeid は下節に列挙する。

duration ledger は test file 単位ではなく nodeid 単位で現行 30 node を列挙している (`acceptance_duration_ledger.json:22130-22159`)。したがって同じ test file への追加でも、新 nodeid は親の JUnit 実測後に次の正本 producer で登録する。

```bash
python3 tools/update_acceptance_duration_ledger.py --add-only /absolute/path/to/parent-acceptance.junit.xml
```

### 7. 凍結 bytes の pin 閉包

`git grep` を path、basename、既存/予定識別子、実値、whole-file SHA、`path:line` 形式で実施した。

- 新 path `docs/t1998-balanced-stock-inline-preregistration.md`: hit なし。
- 予定識別子 `EXPECTED_MEASUREMENT_JOB_BODY_SHA256`、`EXPECTED_CURRENT_PREREGISTRATION_SHA256`、`T1998_PREREGISTRATION_REL`: hit なし。
- 現行 whole-file SHA:
  - consumer `097eb447a457555e9ede71c46979102c2a372cbadc558ca7ffcddba7da25b052`: hit なし。
  - consumer test `16086adbcf921c25b4e1afcfcc80a1b08eb99d0377d26aa516c1d1232dc11b6f`: hit なし。
  - duration ledger `1558b64d31c232117bc91b363255eee4c2388505b6cab8305692f2cf8a6fac16`: hit なし。
- consumer path の live pin:
  - `orchestrator/tests/test_official_perf_closure.py:77` の reviewed-file membership。
  - `orchestrator/tests/test_p3_build_authority_cli.py:168` の basename membership。
  - `test_t1998_stock_inline_pair.py:760-767` の禁止 import / `argmax` 全文走査。
  いずれも今回の loader 追加では値を変える必要がない。
- test path の live pin:
  - `acceptance_duration_ledger.json:22130-22159`。新 nodeid のみ producer で追記する。
- consumer/test の行番号 pin:
  - `output/insights/2026-09-08_t1998-stock-inline-parts/` の mutation spec/report と verbatim、
    `output/insights/2026-09-09_t2354-a5-prune-removal/` の verbatim に存在する。
  - これらは過去版を説明する凍結済み歴史成果物であり、現行行番号へ書き換えない。
- 旧 digest の exact hit は過去の reservation / submit 記録と歴史 insight に限られた。live T-1998 preregistration はない。
- 新 digest の現行 exact hit は `docs/worklog.md:682` と
  `output/insights/2026-09-09_t2354-a5-prune-removal/README.md:33`。コード literal pin はまだない。
- full gitlink、環境 digest、両 source digest、canonical genome は既存の成果物・他実験にも hit するが、
  いずれも当該 path の whole-file/line pin ではない。今回の値と一致する既存証拠であり、更新対象ではない。

## 実装プラン

### `docs/t1998-balanced-stock-inline-preregistration.md`（新規）

- `:1-7` — 文書の目的、D1874 による認可、正式測定前の prospective 文書であること。
- `:8-20` — v1、発効条件、改訂時に旧 commit/blob を上書きしない規則。
- `:21-36` — ancestry と bytes が証明する範囲、手動実行を封じるものではないという限界。
- `:37-54` — fixed 5 µs 対 no-backoff の仮説、記述的 estimand、一般化しない主張範囲。
- `:55-70` — 2026-09-07 生値を既知材料として開示し、主張へ転用しない規則。
- `:71-104` — repository commit、gitlink、環境、job body、arm 別 genome/source digest、実行条件の実値表。
- `:105-128` — rejection / inconclusive / median / ratio / improvement の添字域を同じ pair に固定。
- `:129-185` — marker 付き機械可読 JSON。`repository_commit` literal は置かず、binding rule だけを書く。
- `:186-205` — formal run は事前登録 commit の checkout からのみ行い、成果物 repository commit と一致させる。
- `:206-220` — 全値、拒否、inconclusive を報告し、事前登録前の値を混ぜない。
- `:221-235` — A-5、他 workload、最適点探索、機序一般化を閉じない旨。

### `orchestrator/campaign/t1998_stock_inline_pair.py`

- `:10-20` — loader に必要な標準ライブラリ import を追加。
- `:42-75` — canonical path、spec marker/schema、D1790 の scalar 2 定数を追加。
- `:131-182` — 既存 3 dataclass は変更しない。
- `:184-300` — strict Markdown/JSON parser、Git ancestor/blob 検査、`load_preregistration()` を追加。
- 現行 `:821-823` — `common.launcher_script_sha256` が
  `EXPECTED_MEASUREMENT_JOB_BODY_SHA256` と exact 一致する事前条件を追加。
- 現行 `:915-919` — reservation の `script_sha256` と preregistered 値の exact 比較は維持する。
- 現行 `:522-533` — arm 別 source digest 比較は無変更。
- 現行 `:707-712` — consumer の既存署名は無変更。loader を明示的に呼んだ側だけが identity を渡す。
- その他の rejection、inconclusive、推定量計算は一切緩めない。

### `orchestrator/tests/test_t1998_stock_inline_pair.py`

- `:51-55` — fixture の job body/source digest を actual 値へ置換。
- 現行 `:391-408` — dataclass 組み立て構造は維持。
- 現行 `:434-476` 周辺 — actual pin の正例・arm 別負例を追加。
- 現行 `:502-515` 周辺 — 旧 digest の artifact-side 負例を追加。
- 現行 `:768` の直前 — temporary Git repository helper と loader の commit/blob/hash 境界テストを追加。
- 既存拒否テストは削除・緩和しない。

### `orchestrator/tests/acceptance_duration_ledger.json`

- 現行 `:22130-22159` の T-1998 nodeid 群へ、親が取得した JUnit の実測 duration を `--add-only` で追加する。
- 手編集値、推定値、既存 nodeid の更新は行わない。

変更しないもの:

- `tools/pegasus/submit_t1998_balanced_stock_inline.sh:43-45,89-92,172-180`
- `orchestrator/tests/test_t1998_launcher_contract.py`
- `tools/pegasus/a5_second_boot_backoff_sweep.sh`
- `tools/pegasus/admission_registry.json`
- 既存 `output/insights/**`

## 追加するテスト

- `orchestrator/tests/test_t1998_stock_inline_pair.py::test_current_job_body_digest_is_accepted`
  — 新 digest を旧値へ戻す変異を正例で殺す。

- `orchestrator/tests/test_t1998_stock_inline_pair.py::test_old_job_body_digest_is_rejected_as_launcher_script_identity_mismatch`
  — artifact の旧 digest `0ef4d41ee1ddf8ecd7a86a32a3b9dbaf128279125ef4820c54421973ee281d84` を受理する変異を、code/field/expected/actual の完全検査で殺す。

- `orchestrator/tests/test_t1998_stock_inline_pair.py::test_current_arm_source_digests_are_accepted`
  — baseline/target の probe 実値を取り違える変異を正例で殺す。

- `orchestrator/tests/test_t1998_stock_inline_pair.py::test_each_arm_source_digest_drift_is_rejected[baseline]`
  — baseline の `source-identity-unbound` 比較だけを外す変異を殺す。

- `orchestrator/tests/test_t1998_stock_inline_pair.py::test_each_arm_source_digest_drift_is_rejected[target]`
  — target の `source-identity-unbound` 比較だけを外す変異を殺す。

- `orchestrator/tests/test_t1998_stock_inline_pair.py::test_load_preregistration_returns_document_identity_with_ancestor_commit`
  — 文書を parse せず module 手写し値を返す実装、または `repository_commit` を current HEAD に置換する実装を殺す。

- `orchestrator/tests/test_t1998_stock_inline_pair.py::test_load_preregistration_rejects_nonancestor_commit`
  — ancestry 検査を削る変異を殺す。

- `orchestrator/tests/test_t1998_stock_inline_pair.py::test_load_preregistration_rejects_worktree_blob_drift`
  — worktree bytes と指定 commit blob の一致検査を削る変異を殺す。

- `orchestrator/tests/test_t1998_stock_inline_pair.py::test_load_preregistration_rejects_current_document_sha_drift`
  — 現行解析文書 SHA の exact 一値比較を削る、任意値化する変異を殺す。

- `orchestrator/tests/test_t1998_stock_inline_pair.py::test_d1790_pins_are_distinct_exact_scalar_strings`
  — 2 pin の同一視、`None` 化、tuple/set/allowlist 化を殺す。

- 既存
  `orchestrator/tests/test_t1998_stock_inline_pair.py::test_launcher_script_digest_is_bound_to_preregistration`
  — preregistered 側の任意 digest を artifact に追随させる変異への既存負例として維持する。

## 親 brief への反論

(P1-1)〜(P1-4) を覆すべきものはない。以下の限定だけ加える。

- **P1-1 は採用。** canonical Markdown 1 本、commit blob、worktree bytes の一致を使う。さらに D1790 の解析規則側 pin として whole-file SHA-256 の scalar 定数を要求する。JSON 単独成果物を別に増やす理由はない。
- **P1-2 は採用。** 文書だけでは `T1998PreregisteredIdentity` へ到達せず、現行テストのような手組み `test_t1998_stock_inline_pair.py:391-407` が正式経路にも残るため、loader は必要。
- **P1-3 は採用。** b10 の ancestry/blob 方式が F36 を避けつつ最も単純である。HEAD exact 案は後続解析を不必要に拒否する。
- **P1-4 は採用。** `submit_t1998_balanced_stock_inline.sh:91-92,178-180` が job body の実 file digest を成果物へ運び、consumer `:915-919` が読む。README `:41-48` のとおり成果物から復元できるのは submitter ではなく job body までである。

ただし P1-4 の成果物側値を「事前登録文書 SHA」と呼んではならない。T-1998 producer schema が実際に記録するのは job body SHA であり、D1790 の考え方をこの利用可能な測定時点 identity に割り当てたもの、と明記する必要がある。

また brief `:47-58` の「artifacts に生の JSON」は値の provenance 全体を一つの JSON が持つという意味では正確でない。source JSON、environment JSON、repo の job body bytes、Git tree の四者に分かれている。ただし値そのものの不一致はなかった。

## 残る不確実性

- 正本文書の最終 bytes が未作成なので `EXPECTED_CURRENT_PREREGISTRATION_SHA256` は未確定。
- `repository_commit` は実装を含む着地 commit の full ID なので未確定。
- 新 nodeid の実測 duration と ledger の追記値は、親の JUnit 実走まで未確定。
- pytest、docs checker、provenance checker は本段では走らせておらず、緑とは報告できない。
- login node の `g++` と過去 A-5 の GNU 11.4.0 は版が一致するが、compute node と同一 header closure であることは未証明。正式測定時に source digest が違えば既存 `source-identity-unbound` で fail-closed になる。
- loader を呼ぶ最終利用者側の具体的な CLI は本 scope にない。今回は文書から identity を得る最小 callable 経路までとする。

## 総括

新規正本は `docs/t1998-balanced-stock-inline-preregistration.md` とし、実値を marker 付き JSON に一意固定する。  
consumer 同一 module に commit/blob/文書 SHA を検証する loader を置き、`repository_commit` は `prereg_commit` から導く。  
成果物側 job body SHA と現行文書 SHA は独立した scalar 定数にし、旧新版 allowlist は作らない。  
旧 job body digest、新 digest、両 arm source digest、commit/blob/hash の境界を既存 test file で固定する。  
歴史成果物の path/line pin は変更せず、新 nodeid だけ duration ledger の正本 producer で登録する。  
本段では実装・編集・commit・pytest・qsub を行っていない。