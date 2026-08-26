## 総括

- `_FLAKY_TEST_HOLD_ROWS` を空にすると、静的には `test_flaky_test_holds_contract.py` の 3 test が落ちる。
- 背景と異なり、契約テストは 3 row を逐語 pin していない。逐語に近い pin は hold#1 だけで、`failure_signature` も非空確認のみ。
- (D-a) は「規則から得た literal directory 候補を `git check-ignore` で検証し、既存 `git ls-files` 結果と和集合」にする。
- (D-b) の timestamp 漏れは 2 個の `_t080_output_snapshot` にだけ存在する。floor helper は既に root と timestamp を記録しない。
- before/after の状態 snapshot だけでは、git-visible path の一時作成後削除と ignored child 作成を完全には識別できない。
- 推奨は全 directory の `st_size` / `st_mtime_ns` / `st_ctime_ns` を外し、docstring を永続的な Git-visible 状態の検出へ狭めること。
- P1 は decorator と関数本体の正規化 AST digest を必須 field にする。コメント・整形・行移動では変えない。
- 最大の risk は、未検査だった一時作成後削除の検出力を明示的に捨てる点と、P1 追加時に D697 の「6 条件」が古くなる点である。

## A. pin 閉包

静的に落ちる箇所は次の 3 test に閉じる。

| file:line | 落ち方 | 追随 |
|---|---|---|
| `orchestrator/tests/test_flaky_test_holds_contract.py:291-312` | `REG.FLAKY_TEST_HOLDS[_NEW_HELD_NODE]` が line 300 で `KeyError` | `test_live_registry_is_empty_and_exports_empty_digest` 相当へ書き換え、rows / mapping / node IDs が空、digest が `_EMPTY_REGISTRY_SHA256` と一致することを pin する |
| `orchestrator/tests/test_flaky_test_holds_contract.py:902-945` | synthetic mapping の第 2 row を line 913 で live registry から読むため `KeyError` | live row への依存を除き、`_synthetic_valid_hold()` だけで summary の非空契約を検査する。count と digest golden を再計算する |
| `orchestrator/tests/test_flaky_test_holds_contract.py:988-1025` | conftest は空 registry との積集合を取り matched/skipped=0 を出すが、lines 1012-1013 は 1 を期待する | live empty registry の `0/0/0` と empty digest を期待する test に変える |

背景にある「3 row の node ID、`evidence_id`、`reintroduction_task_id`、`failure_signature` を逐語 pin」は現行コードとは一致しない。

- `test_flaky_test_holds_contract.py:32-35,300-312` が pin するのは hold#1 のみ。
- node ID、`evidence_id == "F480"`、reintroduction slug は exact だが、`failure_signature` は line 306 の truthiness だけ。
- hold#2 と hold#3 の node ID、F 番号、slug、signature は同ファイルに存在しない。
- したがって、3 row の逐語 pin を撤去する修正は存在せず、上記 live-row 依存だけを外せばよい。

各 hit の分類は次のとおり。

**撤去に追随して直す**

- `orchestrator/tests/flaky_test_holds.py:200-291` — 3 row 全体を `()` にする。
- `orchestrator/tests/test_flaky_test_holds_contract.py:32-35,291-312,902-945,988-1025` — 上記 3 test と `_NEW_HELD_NODE` の live-row 用途を撤去する。
- `orchestrator/tests/test_flaky_test_holds_contract.py:942-944` — `9a31...` は live hold#1 と synthetic F57 を組み合わせた digest golden。非空 synthetic test の構成変更と P1 field 追加の両方で更新が必要。
- `docs/decisions.md:27516-27525` — 空 registry 自体では壊れないが、P1 を採用すると「受理条件は 6 つ」が不正確になる。D697 への dated 追補か supersession を追加し、source digest を第 7 条件として明記する。

**そのままでよい**

- `orchestrator/tests/flaky_test_holds.py:294-303` — validator、空 `MappingProxyType`、空 node set、空 digest を既に正しく導出する。
- `orchestrator/tests/test_flaky_test_holds_contract.py:52-54,315-325,951-985` — `_EMPTY_REGISTRY_SHA256` と空 summary の契約が既にある。空 digest `4f53...` は変わらない。
- `orchestrator/tests/test_flaky_test_holds_contract.py:28-31,57-77` — `_HELD_NODE` は既に撤去済みの F57 を使う test-only synthetic row で、今回の 3 row ではない。P1 field の追随だけ必要。
- `orchestrator/tests/conftest.py:116-154` — import alias と lazy binding は空 mapping を `None` と混同しない。
- `orchestrator/tests/conftest.py:1417-1465,1621-1629,1703-1773,1868-1893` — empty registry なら literal match、skip、stale-key 検査が自然に no-op になる。
- `orchestrator/tests/conftest.py:1988-2030` — lines 2010-2016 が空 registry でも summary を出す。D923 の所要どおり。
- `tools/mutation_harness.py:1266-1307` — `getattr(module, "FLAKY_TEST_HOLD_NODE_IDS", None)` という動的参照も確認対象。空 `frozenset` を正しく受理し、交差も空になる。
- `tools/task_runs/pytest_stats.py:17-20,55-84,147-200`、`tools/task_runs/schema.py:328-330,443-456`、`tools/run_tests.py:1177-1218` — receipt は generic な collected/passed/failed/skipped を記録するだけ。再導入後の passed +3 / skipped -3 を値として受けられ、schema 変更は不要。
- `IZANAGI_FLAKY_HOLD_SUMMARY_V1` の consumer は `test_flaky_test_holds_contract.py:273-288,392-596,902-1025` だけ。`tools/` 配下には prefix または JSON key の専用 consumer はない。
- `orchestrator/tests/conftest.py:1734-1738` の user property JSON keys に repository 内 consumer はない。空なら property 自体が付かない。
- `docs/decisions.md:27509-27531,33297-33310` — D697 の機構と D923 の empty summary は存続させる。
- `docs/dev-wave/operations.md:128-132` と鏡像 `tools/check_docs.py:604-610`、`orchestrator/tests/test_check_docs.py:170` — registry path と一般運用を要求するだけで、3 node は要求しない。
- `orchestrator/tests/test_check_docs.py:1246-1250` — synthetic docs fixture が registry file の存在だけを要求する。ファイルは残る。
- `docs/failures.md:2779,5084-5101,13265-13327,15440-15464` — F136/F480 の履歴証拠。row 撤去後も削除しない。
- `docs/spool/FOLDED.md:2574,2618` — T-1773/T-1803 の allocation 履歴。削除しない。
- `docs/archive/worklog-phase3-0825-916.md:57`、`...917-918.md:120`、`...940.md:82`、`...949.md:84`、`...0826-968.md:792`、`...978-979.md:826` —履歴として残す。
- `orchestrator/tests/acceptance_duration_ledger.json:7663,8365,10819` —対象 test は削除せず受入へ戻すため、duration entry も残す。
- `orchestrator/tests/test_s8b_oracle_driver.py:818,1192-1207`、`test_pegasus_dispatch_compute.py:5430-5495`、`test_real_repo_serialization.py:3746-3836` — reintroduce する test 本体またはその consumer inventory なので残す。

live 3-row registry digest を literal に持つ golden は見つからない。存在する literal は empty digest と、`test_flaky_test_holds_contract.py:942-944` の synthetic digest だけである。

## B. (D-a) の設計

`output_snapshot_ignores.py:9-43` は次の三案を組み合わせる。

| 案 | 採否 | 理由 |
|---|---|---|
| `git check-ignore` 単独 | 判定器として採用、列挙器としては不採用 | nonexistent path に答えられるが、候補名を自分では列挙できず、glob の prefix 畳み込みも行わない |
| `.gitignore` を直接解釈 | ignore 判定器として不採用 | negation、escape、anchoring、nested `.gitignore`、global exclude を再実装すると Git と drift する |
| `git ls-files` と規則候補の和 | 採用 | wildcard や ambient rule による実在 path は現行 Git 列挙で保ち、literal directory rule は存在前から加えられる |

実装は次の形にする。

1. `output_snapshot_ignores.py:9` の前に、standard ignore source から「正の literal directory rule」だけを候補化する helper を置く。少なくとも repository root の `.gitignore:18-28` を読み、`output/runs/` から `output/runs/` を得る。negation、glob、escaped/曖昧な規則は真偽判定せず候補化をスキップする。
2. 候補は ignore 規則の bytes と規則ファイルの基準 directory から作る。`output/` の実在 entry、`rglob`、`os.listdir` は候補生成に使わない。
3. 各候補を `git check-ignore --no-index --stdin -z` に渡す。実際に Git が ignored と判定した候補だけを `output/` 相対 prefix にする。直接 parser は候補の over-approximation にしか使わない。
4. 現行 `git ls-files -o -i --exclude-standard --directory -- output/` の結果も残し、check-ignore 済み rule 候補との集合和を返す。
5. `output/` 自体がどちらかの経路で ignored なら、現行 lines 31-34 と同じ assertion で fail-closed にする。
6. `.gitignore:19` の `output/variants/*/bin/` のような wildcard は、存在前の有限 prefix へ無理に展開しない。実在後は `git ls-files` 側が exact path を返す。

状態依存を持ち込まないことは `test_s8b_oracle_driver.py:617-624` 周辺に一時 Git repo の contract test を追加して示す。

```python
absent = git_ignored_output_prefixes(repo)
(repo / "output/runs").mkdir(parents=True)
present = git_ignored_output_prefixes(repo)
assert absent == present == ("runs",)
```

さらに `output/runs/` の rule を消す、または negation で無効化した repo では `"runs"` が返らないことも pin する。これにより候補の根拠が directory の存在ではなく rule bytes と Git の判定であることを分離できる。

既存 3 test の要求は弱めない。

- `test_s8b_oracle_driver.py:601-614`
- `test_real_repo_serialization.py:587-603`
- `test_s8b_floor_campaign.py:1573-1588`

それぞれの `"runs" in ignored_prefixes` はそのまま残る。また ignored subtree の snapshot 不変も残す。現行は ignored parent を baseline より前に作っているため、(D-b) の「ignored parent 自体の新規作成」は検査していない。C の修理と同時に baseline を `ignored_parent.mkdir()` より前へ移す。

## C. (D-b) の設計

まず背景の補正が必要である。

- `test_s8b_oracle_driver.py:558-580` と `test_real_repo_serialization.py:541-563` は bit 単位で同一の `_t080_output_snapshot` で、root、directory size、mtime、ctime を記録する。
- `test_s8b_floor_campaign.py:1484-1510` は別実装である。root を row に入れず、directory は `("dir", rel)` のみ、file は内容 digest、symlink は link target を記録する。この helper には (D-b) の timestamp 漏れはない。

### 1. 現在の positive control

一時作成後削除を独立に検査する positive control は存在しない。

- `test_s8b_oracle_driver.py:583-598`
- `test_real_repo_serialization.py:566-582`
- `test_s8b_floor_campaign.py:1551-1570`

これらは visible directory と payload を `after` まで残すため、追加 row だけで `after != before` になる。ancestor timestamp の寄与を除いていない。

`test_s8b_oracle_driver.py:1192-1207` は実 operation が output を変えなかったことを検査する negative test であり、一時 visible path を意図的に作る positive control ではない。したがって lines 559 / 542 の docstring は「恒真な assertion」というより、実行可能な独立証拠を持たない未検査の主張である。

### 2. 検出力を完全に保つ代替

通常の before/after state snapshot の範囲には、完全な代替はない。

visible path を作成して削除した列と、ignored child の作成で ancestor metadata だけが変わった列は、最終的な Git-visible entry 集合が同じになりうる。ignored 由来の ancestor timestamp を捨てながら前者だけを残すには、inotify/fanotify/audit のような区間中の event provenance が必要になる。

inotify を採るなら `_t080_output_snapshot` の API を context manager 型へ変え、baseline 前に全 visible directory を watch し、create/delete/move event の path を Git ignore 判定へ通す必要がある。しかし subprocess の短命 event、動的 directory watch、Linux 固有 API、全 call site の変更まで入り、本 wave の小修理としては推奨しない。

推奨案は次のとおり。

- `test_s8b_oracle_driver.py:558-580` と `test_real_repo_serialization.py:541-563` で、`stat.S_ISDIR(info.st_mode)` の row は安定情報だけにする。
- directory は `st_mode` を残し、`st_size`、`st_mtime_ns`、`st_ctime_ns` を `None` に正規化する。mtime/ctime だけでなく `st_size` も child entry 作成で変化しうるため外す。
- regular file と symlink の size/mtime/ctime は現行どおり残す。
- root を含む永続的な visible directory/file の追加・削除は row 集合差で、file mutation は file metadata で検出する。
- docstring を「観測時点に存在する Git-visible entry と非-directory metadata を捉える snapshot」へ変更し、一時作成後削除を謳わない。
- 「ignored descendant を持ちうる directory」だけを動的に判定する案は採らない。before では候補がなく after では候補が増える場合、正規化対象自体が変化して新しい state dependency になる。全 directory を同じ row schema にする方が決定的である。

### 3. 対になる positive / negative control

3 個の negative control は、baseline を ignored parent の作成前へ移す。

- `test_s8b_oracle_driver.py:601-614`
- `test_real_repo_serialization.py:587-603`
- `test_s8b_floor_campaign.py:1573-1588`

すなわち次の順序にする。

```python
before = snapshot(tmp_path)
ignored_parent = tmp_path / "runs"
ignored_parent.mkdir()
# nested ignored payload を作る
assert snapshot(tmp_path) == before
```

除外を `"runs"` へ広げたときの positive control は、3 file の既存 visible test で control 名を `"runs-visible"` にし、prefix 境界を検査する。

```python
assert not is_git_ignored_output_path("runs-visible", ignored_prefixes)
before = snapshot(tmp_path)
# runs-visible/nested/payload.bin を作る
after = snapshot(tmp_path)
assert after != before, (
    "rule-derived ignore prefix 'runs' must not hide Git-visible "
    "'runs-visible'"
)
```

`is_git_ignored_output_path()` を誤って単純 `startswith("runs")` にした場合、この assertion が `after == before` で赤になる。これが exclusion 拡張と対になる具体的な detection-side positive control である。

一時作成後削除の主張を維持する裁定を選ぶ場合は、別途次の control を先に追加し、現在の helper で赤にならないことを確認した後に event observer を設計する必要がある。

```python
before = snapshot(tmp_path)
visible = tmp_path / "visible-transient"
visible.mkdir()
(visible / "payload").write_bytes(b"visible transient")
shutil.rmtree(visible)
after = snapshot(tmp_path)
assert after != before, (
    "Git-visible create-and-delete must remain observable"
)
```

推奨する directory metadata 正規化とは両立しないため、この transient control と正規化を同時には land させない。

## D. helper 共通化の可否

静的 diff の結果は次のとおり。

- `test_s8b_oracle_driver.py:558-580` と `test_real_repo_serialization.py:541-563` は 23 行が bit 一致し、source slice SHA-256 も両方 `c1a21b81...` だった。
- 直後の positive/negative tests は分岐している。`test_real_repo_serialization.py:566-603` は cleanup の `try/finally` を持つが、oracle 側 `:583-614` は持たない。
- `test_s8b_floor_campaign.py:1484-1510` は walker、row schema、file digest、root の扱いがすべて異なる。独立 reference helper `:1513-1529` も持つ。

推奨は共通化しない。

- (D-a) の規則導出は既に `output_snapshot_ignores.py:9-52` に共通化されており、ここは一度だけ修理できる。
- (D-b) は bit 一致する 2 helper に同じ小変更を適用する。
- floor helper を同じ API へ寄せると、内容 digest と独立 oracle を失うか、共通 helper が複数 mode を持つことになり、編集面と恒真化 risk が増える。
- 今回新しい共通 module や import 辺を増やす利益は、2 箇所の機械的同期より小さい。

## E. (P1) 機構の設計と推奨

P1 は採用を推奨する。ただし raw source bytes ではなく、decorator と関数本体の正規化 AST digest にする。

### validator への追加

`orchestrator/tests/flaky_test_holds.py` を次のように拡張する。

1. `:8-23` に `ast` import、repository root 定数、lowercase SHA-256 regex を追加する。
2. `FlakyTestHold:26-40` に `test_source_sha256: str` を追加する。
3. `_test_function_name():80-81` 周辺に、node ID の file と scope を解決して対象 `FunctionDef` / `AsyncFunctionDef` を一意に取る helper を追加する。
4. decorator、arguments、関数 body を `ast.dump(..., include_attributes=False)` 相当の安定 projection にし、先頭 docstring は除外する。行番号、列、コメント、空白は digest に入れない。
5. unreadable file、syntax error、対象なし、同 scope で複数候補、digest format 不正は `ValueError` にする。
6. `_validate_flaky_test_hold_rows():100-166` で field format と現在の AST digest の exact 一致を検査する。registry import 時点で失敗させるため、contract test だけでなく通常 collection も fail-fast になる。
7. `_hold_payload():170-183` に field を含め、registry digest 自体も再正当化へ束縛する。
8. registration 用に `flaky_test_hold_source_sha256(node_id)` を公開し、作者が literal を生成できるようにする。ただし row には関数呼び出しでなく 64 hex literal を置く。

`test_flaky_test_holds_contract.py` の追随は次のとおり。

- `_synthetic_valid_hold():57-77` に valid digest を追加する。
- `_hold_constructor_fields():84-97` と injection plugin constructor `:193-205` に field を追加する。
- negative-control table `:733-773` に malformed digest と現在 source と異なる valid-format digest を加える。
- temp registry import tests `:328-389` は target test source も temp root に複製し、validator が同じ checkout boundary を読むことを保証する。
- `:804-824` 周辺に、コメント・整形だけの変更では digest が同じ、assertion/decorator の変更では `ValueError` になる control を追加する。
- synthetic digest golden `:942-944` を新 payload で再計算する。empty digest `:52-54,982-984` は `[]` の hash なので変更しない。

### AST と行範囲の比較

- raw 行範囲は decorator 先頭から `end_lineno` までをそのまま hash するため実装は単純だが、整形、コメント、改行、隣接移動でも全 hold の再正当化を要求する。
- AST は今回の `join(10) -> join(60)`、`hookwrapper=True`、`yield` の追加をすべて検出する一方、コメント、空白、行移動では変わらない。
- AST は helper/fixture の変更を追わないが、transitive closure まで hash すると偽陽性と実装量が急増する。本機構は「held test 関数自身が編集された」という実例に scope を限定する。
- Python minor versionで AST schema が変わる可能性は残る。runner の Python 更新時に hold を再確認するコストとして受け入れる。

### 既存 field との関係

二重ではない。

- `green_observation` / `red_observation` / `green_run_count` は登録時の履歴証拠。
- `failure_signature` は F 節との過去 failure の結合。
- `reintroduction_task_id` は所有先。
- source digest だけが「その証拠が対象にした test 実装と現在の実装が同じか」を検査する。

### 代替との比較

- 登録から N 日を summary に出す案は、修理直後でも期限前なら黙って残り、未修理でも期限で警告する。登録日 field、wall-clock、summary schema まで増える割に因果が弱い。
- land 時に diff を調べる案は base range と merge topology に依存し、通常 collection では発火しない。
- hold を定期的に実走する案は、現行の無条件 skip と別の実行面・権限を新設する必要がある。

したがって、低偽陽性の AST digest を import-time validator に置く案を推奨する。

## F. 段 5 の所有分割

編集面を重ねない 2 子分割は可能である。

1. **registry / P1 子**

   - `orchestrator/tests/flaky_test_holds.py`
   - `orchestrator/tests/test_flaky_test_holds_contract.py`
   - `docs/decisions.md` の D697 追補
   - 3 row 撤去、empty live contract、AST digest 機構、synthetic golden を所有する。

2. **snapshot 子**

   - `orchestrator/tests/output_snapshot_ignores.py`
   - `orchestrator/tests/test_s8b_oracle_driver.py`
   - `orchestrator/tests/test_real_repo_serialization.py`
   - `orchestrator/tests/test_s8b_floor_campaign.py`
   - rule-derived prefix、directory metadata 正規化、3 negative control の順序修正、`runs-visible` positive control を所有する。

file の直接重複はない。ただし論理依存がある。registry 子だけを先に受入全走すると未修理の hold#2 が既に reintroduce される。段 5 は並列起草できるが、統合と実測は snapshot 子を先に取り込み、その後 registry 子を重ねる順序にする。

registry 子は `test_real_repo_serialization.py` を source digest の対象として読むだけで編集しない。また production rows は空になるため、snapshot 子の変更で P1 の live digest literal が変わることもない。

## 未確認事項

- pytest、焦点走、受入全走は実行していない。緑は主張しない。
- rule extractor と `git check-ignore` の引数・NUL 出力処理は、temp Git repo の新 contract test で親が実測する必要がある。
- directory `st_size` / timestamp 正規化後に、fresh ignored-parent 作成の 3 negative control と `runs-visible` positive control が両立するか実走が必要。
- 新しい AST projection の digest literal と synthetic registry digest golden は、実装後の exact bytes から再計算が必要。
- 撤去した 3 node、T-1856 の 3 node、`test_flaky_test_holds_contract.py`、関連 3 file の焦点走が必要。
- 最終的に受入全走で summary が `registered=0 / matched=0 / skipped=0 / empty digest` となり、3 node が passed 側へ移ることは親の実走で確認する必要がある。