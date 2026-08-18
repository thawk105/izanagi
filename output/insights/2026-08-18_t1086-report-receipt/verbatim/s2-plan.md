# 段 2 実装プラン

静的検査のみ実施し、pytest は実走していない。P2 は採用、P3/P4 は exact 検査を加えて強化する。P1 の raw `Mapping` 渡しは、WAL 由来など別の mapping を authority として誤投入できるため採らない。`ReverifiedFreeze` 自体を report へ渡し、内部で `binaries_by_cell` を取り出す。

## 編集面

| file:line | 変更 | 理由 |
|---|---|---|
| `orchestrator/campaign/s8b_oracle_report.py:102-106` | `_STORE_REVERIFICATION_KEYS`、`_STORE_REVERIFICATION_CELL_KEYS`、閉じた state 集合を追加 | `_MEASUREMENT_RECORD_KEYS` と同じ module-local `frozenset` 方式で schema を固定する |
| `orchestrator/campaign/s8b_oracle_report.py:1814` 直前 | `def _resolve_store_path(*, output_root: Path, store_path: object) -> Path` を新設 | 絶対 path、`.`、`..`、制御文字、backslash、symlink 解決後の out_root 脱出を読込前に拒否する |
| 同上 | `def _build_store_reverification(*, schedule: Sequence[Mapping], binaries_by_cell: Mapping, output_root: Path) -> dict[str, object]` を新設 | trusted schedule と freeze authority を exact 照合し、store を最後に再読する単一 producer にする |
| `s8b_oracle_report.py:1814-1842` | `build_observations(..., reverified_freeze: s8b_ratified_freeze.ReverifiedFreeze \| None = None)` を追加。値がある場合は exact type、manifest の `freeze.sha256` との一致を確認 | raw mapping を authority API にしない。legacy に token が渡された場合も拒否する |
| `s8b_oracle_report.py:1951-1976` | WAL 評価完了後、observations 組立て直前に receipt を生成し、`store_reverification` を追加 | store 再読を可能な限り report 出力に近づける。WAL の binary 自己申告は一切参照しない |
| `s8b_oracle_report.py:1996-2016` | `reverified = None` で初期化し、official 分岐だけ `reverified_freeze=reverified` を `build_observations` へ渡す | 現在捨てている `ReverifiedFreeze` を authority token として消費する。legacy は `None` |
| `orchestrator/campaign/s8b_oracle_judge.py:29-34` | report と独立した同名 exact-key/state 定数を追加 | producer の定数を import せず、consumer が独立に schema を検査する |
| `s8b_oracle_judge.py:221` 直前 | `def _validate_store_reverification(value: object, *, expected_cell_ids: frozenset[str]) -> list[dict]` を新設 | receipt の exact schema、SHA、state 対応、重複、trusted schedule 全被覆を純関数で検査する |
| `s8b_oracle_judge.py:449-514` | `schedule_projection.expected_cells` から logical cell 集合を導き、official receipt を検査。receipt reasons を aggregation gate にも入れる | observations 自身の `expected_cells` を authority にしない。失敗時は構成集約も `unknown` にする |
| `s8b_oracle_judge.py:313-317` | `judge_oracle` の署名は変更しない | 確定裁定の位置引数 1 + keyword 3 を保存する |
| `orchestrator/tests/test_s8b_oracle_driver.py:4647` 付近 | 実 v2 fixture に正の対照と post-run A/B を追加 | 実走前 gate の既存テストでは新しい時間窓を殺せない |
| `orchestrator/tests/test_s8b_oracle_report.py:378-418,1456-1506,4405-4435` | judge helper の既定 fixture、CLI wiring、exact top-level key 検査、empty/out-of-root/coverage 負例を更新 | 既存検査を receipt 欠落による無関係な赤から分離しつつ production wiring を pin する |
| `orchestrator/tests/test_s8b_oracle_judge.py:45-117,552-590` | `_observations` と CLI fixture に独立な正しい receipt を追加し、receipt 欠落・malformed・extra-cell テストを追加 | judge の新しい受理境界を直接殺す |
| `orchestrator/tests/test_s8b_verdict.py:846-930` | `_oracle_verifier_case` に正しい receipt を追加 | verdict 再導出テストが新 gate 以外の意図を維持する |
| `orchestrator/tests/s8b_v2_freeze_fixture.py:220-282` | 編集せず再利用 | 実 store bytes、`store_path`、`binary_sha256` を既に持つ |
| `orchestrator/campaign/s8b_oracle_artifacts.py` | 変更なし | loader は marker/classifier のまま。`OFFICIAL_OBSERVATIONS_SCHEMA` も v1 据え置き |

official の direct `build_observations` 呼出しで token を省略した場合は、非 certifying な observations として key を出さない。production CLI は必ず token を渡し、judge は official receipt 欠落を拒否する。

## Receipt schema

`store_reverification` の exact schema は次のとおり。

| 階層 | exact key 集合 | 型と意味 |
|---|---|---|
| outer | `{"state", "cells"}` | `state: "verified" \| "unverified"`、`cells: non-empty list[object]` |
| cell | `{"cell_id", "store_path", "expected_sha256", "actual_sha256", "state"}` | P3 の形をそのまま固定 |
| `cell_id` | － | 非空 `str`。trusted schedule の `f"{holdout_id}::{configuration_id}"` と一致 |
| `store_path` | － | out_root 相対の portable POSIX path。report は resolve 後の containment も検査 |
| `expected_sha256` | － | lowercase hex 64 文字。`ReverifiedFreeze.binaries_by_cell[cell_id]["binary_sha256"]` のみから取得 |
| `actual_sha256` | － | lowercase hex 64 文字または `None` |
| cell `state` | － | `"match" \| "mismatch" \| "missing"` |

意味対応も exact にする。

- `match`: `actual_sha256 == expected_sha256`
- `mismatch`: actual は非 null かつ expected と不一致
- `missing`: actual は `None`
- outer `verified`: cells が非空で全件 `match`
- outer `unverified`: 少なくとも 1 件が `mismatch` または `missing`
- cells は `cell_id` 順、重複なし、schedule の unique logical cell 集合と完全一致

report は構築直後に両 exact key 集合を construction pin する。judge は独立した定数で全項目を再検査する。`state == "verified"` だけを見る P4 の単純形は採らない。

## Fail-closed 棚卸し

| ケース | report | `judge_oracle` |
|---|---|---|
| receipt が無い | official direct API で token 未指定なら key を省略。production `main()` では wiring テスト上発生不可 | official は `status="indeterminate"`、cell は `unknown`、理由 `store-reverification-absent` |
| `binaries_by_cell` が空 | `_build_store_reverification` が `ReportError`。CLI は rc=2、出力なし | forged empty receipt は non-empty/coverage 違反で indeterminate |
| legacy manifest | token なしで従来 observations を返し、receipt は出さない | pure judge は既存 `manifest-kind` で indeterminate。receipt 欠落理由は重ねない。judge CLI は legacy manifest を rc=2 で拒否 |
| `store_path` が out_root 外 | literal absolute、`..`、resolve 後の symlink escape を `ReportError`。読まない | 絶対 path や `..` は schema 違反で indeterminate。filesystem symlink escape は output-root API がないため report の責務 |
| schedule cell が authority に無い、または authority に schedule 外 cell がある | `set(binaries_by_cell) == scheduled_cell_ids` の exact equality が破れ `ReportError` | forged receipt の同様の不足・余剰は coverage 違反 |
| schedule 外 cell が receipt にある | legitimate report は生成不能 | `schedule_projection` 由来集合との exact 不一致で indeterminate |
| store bytes 不一致 | receipt cell=`mismatch`、outer=`unverified` を返す | `store-reverification-mismatch` で indeterminate |
| store 実体なし・読込不能 | receipt cell=`missing`, actual=`None`、outer=`unverified` | `store-reverification-store-missing` で indeterminate |

恒真化しやすい枝は明示的に塞ぐ。

- `all(cell["state"] == "match" for cell in [])` は恒真になるため、cells と authority の非空検査を先に置く。
- outer の自己申告 `state == "verified"` だけを見る枝も恒真化できるため、judge が cell state から再導出する。
- report が schedule だけを反復すると authority の余剰 cell は不可視になるため、両集合の equality を別に検査する。
- receipt 欠落枝は正常 producer だけでは発火しないため、正しい observations から key だけを削る C で発火させる。
- A/B/C は全て先に同一 fixture の determinate baseline を確認し、既に indeterminate な入力への恒真 assertion を禁止する。

## 既存テストの巻き添え全件

指定 3 ファイル全体について `set(...)`、`.keys()`、`len(...)`、dict 全体 equality を末尾まで検索した。該当は以下。

| file:line | pin | 対応 |
|---|---|---|
| `orchestrator/tests/test_s8b_oracle_report.py:4414` | legacy observations の exact top-level 9 keys | legacy は receipt なしなので変更しない |
| `orchestrator/tests/test_s8b_oracle_report.py:4430` | official observations の exact top-level 10 keys | token 付き fixture にし、`store_reverification` を加えた 11 keys に更新する。token なしの非 certifying 形は別テストへ分離 |
| `orchestrator/tests/test_s8b_oracle_artifacts.py:203` | loader の `loaded == document` | loader は key を合成しないため変更不要 |
| `orchestrator/tests/test_s8b_verdict.py` | 該当 0 件 | `:1734` の `set(result)` は combined verdict の pin であり observations ではない |

`len(observations["expected_cells"])` など nested collection の件数検査は top-level key 数ではなく、今回の巻き添えではない。top-level の `len(observations)` pin は 3 ファイルとも 0 件だった。

## A/B/C と正の対照

### 正の対照

`test_s8b_oracle_driver.py::test_v2_completed_driver_adapter_campaign_is_accepted_by_report` を拡張する。

- `_build_v2_repo` → `_run_v2` → `reverify_published_freeze` → `build_observations(reverified_freeze=...)` の順で実行。
- 全 receipt cell が `match`、outer が `verified`、exact key 集合、expected/actual SHA 一致を assert。
- E1 epoch を fixture で固定して `judge_oracle(...既存 keyword 3...)` が `determinate` を返すことを assert。
- report wiring や judge gate が過剰拒否になればこの assertion が赤になる。

### 負の対照 A

同じ実 v2 fixture で `_run_v2` 完了後、`_unique_store_victim` の store bytes だけを書き換える。

予定 nodeid:  
`orchestrator/tests/test_s8b_oracle_driver.py::test_v2_post_run_store_change_is_reported_and_refused[replaced]`

assertion:

- victim cell が `state == "mismatch"`
- `actual_sha256 != expected_sha256`
- outer が `unverified`
- judge が indeterminate
- reason に `store-reverification-mismatch`

report の post-run hash 再読、freeze SHA の権威利用、judge 伝播のいずれかを消すと赤になる。

### 負の対照 B

同じく実走完了後に victim store を unlink する。

予定 nodeid:  
`orchestrator/tests/test_s8b_oracle_driver.py::test_v2_post_run_store_change_is_reported_and_refused[removed]`

assertion:

- victim cell が `state == "missing"`
- `actual_sha256 is None`
- outer が `unverified`
- judge reason に `store-reverification-store-missing`

OSError を match に落とす、または store を再読しない変異を殺す。

### 負の対照 C

`test_s8b_oracle_judge.py` の determinate `_observations()` に正しい receipt を標準装備し、コピーから top-level key だけを削る。

予定 nodeid:  
`orchestrator/tests/test_s8b_oracle_judge.py::test_official_store_reverification_absence_is_indeterminate`

削除前 determinate、削除後 indeterminate、全 configuration `unknown`、exact reason が `store-reverification-absent` であることを assertする。missing receipt 検査を production から消すと削除後も determinate になり赤になる。

既存 `test_s8b_oracle_driver.py:4629,5025,5055` は実走前 gate の検査なので、新 A/B の代用にはしない。

## 追加する構造負例

- `test_store_reverification_rejects_empty_binary_authority`
- `test_store_reverification_rejects_binary_cell_coverage[missing]`
- `test_store_reverification_rejects_binary_cell_coverage[extra]`
- `test_store_reverification_rejects_out_of_root_store_path[absolute]`
- `test_store_reverification_rejects_out_of_root_store_path[parent]`
- `test_store_reverification_requires_exact_keys[outer-extra]`
- `test_store_reverification_requires_exact_keys[cell-extra]`
- `test_store_reverification_rejects_receipt_cell_outside_schedule`

report 側の token 改変負例は、実 `ReverifiedFreeze` を `dataclasses.replace` した test-only object で作る。production authority は常に loader が返した元 object のままとする。

## 変異事前登録候補

| # | 変異させる file:line と変異後 | 殺す nodeid |
|---|---|---|
| M1 | `s8b_oracle_report.py:2014-2016` で `reverified_freeze=reverified` を削除し、wave 前の「reverified を捨てる」呼出しへ戻す | `test_s8b_oracle_report.py::test_cli_official_resolves_ratified_freeze_and_verifies` |
| M2 | `s8b_oracle_report.py:1814` 直前の新 helper で `expected_sha256 = actual_sha256` にする | `test_v2_post_run_store_change_is_reported_and_refused[replaced]` |
| M3 | 同 helper で store を読まず `actual_sha256 = expected_sha256` にする | A `[replaced]` |
| M4 | 同 helper の OSError 分岐を `state="match", actual=expected` にする | B `[removed]` |
| M5 | outer 判定を `all(...)` から `any(...)` にする | A `[replaced]` と B `[removed]` |
| M6 | `s8b_oracle_judge.py:221` 直前の新 validator で receipt 欠落時に `[]` を返す | `test_official_store_reverification_absence_is_indeterminate` |
| M7 | `s8b_oracle_judge.py:494-513` で aggregation gate から store reasons を外し、measurement reasons だけに戻す | A/B、および C の全 configuration `unknown` assertion |
| M8 | judge の cell exact 検査を `set(entry) >= required_keys` に緩める | `test_store_reverification_requires_exact_keys[cell-extra]` |
| M9 | judge の receipt cell 集合 equality を subset 判定へ緩める | `test_store_reverification_rejects_receipt_cell_outside_schedule` |
| M10 | report の path resolver から resolve 後 `relative_to(output_root)` を削る | `test_store_reverification_rejects_out_of_root_store_path[absolute]` |

M1 が「wave 前の実コードが既に使っている形」の必須 1 件である。

## 静的受入条件

親が実測する対象は、少なくとも report、judge、driver の焦点 nodeid、`test_s8b_verdict.py`、`test_s8b_oracle_artifacts.py`。段 2 子としては pytest を実走せず、次を静的に確認済みとする。

- `judge_oracle` の位置引数 1 + keyword 3 は不変。
- judge CLI に `--output-root` を追加しない。
- expected SHA は WAL、row、run receipt から取らない。
- `OFFICIAL_OBSERVATIONS_SCHEMA` は据え置く。
- store は read-only で、report に書込経路を作らない。
- receipt は seal や偽造耐性を主張せず、単独 oracle 改ざんの検出に限定する。

## 総括

- P1 の raw Mapping は authority token を失うため、`ReverifiedFreeze` 自体を渡す形へ改める。
- expected SHA の唯一の源は `ReverifiedFreeze.binaries_by_cell` とする。
- receipt は exact outer 2 keys、exact cell 5 keys、非空かつ schedule 完全被覆とする。
- store 再読は WAL 評価後、observations 組立て直前に行う。
- mismatch と missing は report を失敗させず、構造化 receipt を出して judge が拒否する。
- empty authority、out-of-root path、schedule coverage 破れは report 自体を fail-closed に止める。
- legacy は receipt なしのまま、official receipt 欠落は judge で indeterminate にする。
- A/B/C は全て determinate baseline から分岐させ、恒真な拒否テストを避ける。
- 変異は wave 前の「reverified を捨てる」形を含む 10 件を事前登録できる。
- pytest は未実走であり、実測と緑判定は親に委ねる。