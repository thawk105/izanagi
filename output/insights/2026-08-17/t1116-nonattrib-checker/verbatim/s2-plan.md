## 結論

(P3) を checker 単体の安全側強化として採用する。ただし、親 brief の「`flake` が land を通る」という前提は現行コードでは成立しない。

`check_acceptance_reds.py` が `flake` を rc=0 で返しても、待ち手は [tools/dev_wave_wait.py:2802-2812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/dev_wave_wait.py:2802) で各 node を次の形に exact 固定している。

```text
{"classification", "nodeid", "rerun_rc"}
classification == "non-attributable"
```

現行 `flake` は 5 field なので、受領証発行前に `acceptance-red-check` で拒否される。したがって、規律 2 と「受理集合を広げない」を守る推奨案は、checker の 2 file だけを純縮小する案である。R2 の「未接触 file の flake を実際に通す」まで求める場合は別の受理集合拡大になり、段 4 の明示裁定が必要となる。

以下の行番号は現 worktree HEAD `5a19b8ab` の実値である。テストは実走していない。

## 実装 hunk

### 1. 差分 path 集合の取得

[tools/check_acceptance_reds.py:734-747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/check_acceptance_reds.py:734)

変更前:

- `_git()` は汎用 wrapper のみ。
- 分類処理は commit 差分を一度も読まない。

変更後:

- `_wave_changed_paths(repo, tested_main, wave_tip, command_runner) -> frozenset[str]` を `_git()` の直後に新設する。
- 呼ぶ argv は次とする。

```text
git -C <wave repo> diff
  --name-only -z
  --no-renames
  --no-ext-diff
  --no-textconv
  --ignore-submodules=none
  <tested_main>..<wave_tip>
  --
```

- 非 0 rc、非文字列 stdout、非空なのに NUL 終端でない出力、重複 path、絶対 path、`..`、非 NFC、制御文字を含む path は `InvalidInput` とする。
- `-z` で quoting に依存せず、`--no-renames` により rename の旧名と新名の双方を直接接触として扱う。これは過剰拒否方向にしか動かない。

呼び出し場所は probe worktree ではなく、`_probe_nodes()` に渡される `repo`、すなわち wave working repo とする。SHA は immutable で両 commit が同じ object database にあり、node ごとの一時 worktreeで同じ diff を繰り返す理由がない。

### 2. `flake` 候補だけに接触条件を加える

[tools/check_acceptance_reds.py:1314-1406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/check_acceptance_reds.py:1314)

変更前:

- main rc=1: `non-attributable`
- main rc=0、wave rc=1: `attributable`
- main rc=0、wave rc=0: 無条件で `flakes` へ追加

変更後:

- diff は main rc=0、wave rc=0 になった最初の node でだけ遅延取得し、以後は同一集合を再利用する。
- `main_probe.collection.path in changed_paths` なら `attributable` に留める。
- 未接触のときだけ従来どおり `flakes` へ入れる。
- 接触により `attributable` へ留めた node について、`logged_nodeid -> test file path` の mapping を第 8 戻り値として返す。
- main 赤、wave 単独赤、rc が 0/1 外の経路では diff を呼ばない。既存分類へ不要な新しい失敗点を加えない。

### 3. nodeid からの test file 取得

新しい `reference.split("::", 1)` は追加しない。

既存処理は以下の流れで path を確定している。

- [tools/check_acceptance_reds.py:501-510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/check_acceptance_reds.py:501): log reference の先頭 path を検証
- [tools/check_acceptance_reds.py:1237-1253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/check_acceptance_reds.py:1237): collection 対象 path を取り出し、`_CollectionEvidence.path` に保持
- [tools/check_acceptance_reds.py:896-938](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/check_acceptance_reds.py:896): `_complete_collected_nodeids()` が `path` または `path::...` の exact 集合だけを採用
- [tools/check_acceptance_reds.py:514-556](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/check_acceptance_reds.py:514): group suffix を含む log 表記から exact selector を確定

したがって `_probe_nodes()` は [tools/check_acceptance_reds.py:1377-1378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/check_acceptance_reds.py:1377) の `main_probe.collection.path` をそのまま使う。これなら `@group`、parameter、log detail を再解析しない。

### 4. 戻り値の受け渡し

[tools/check_acceptance_reds.py:1527-1552](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/check_acceptance_reds.py:1527)

変更前:

- `_probe_nodes()` の 7 要素を unpack する。
- receipt 構築層には接触理由が届かない。

変更後:

- `wave_touched_paths: dict[str, str] = {}` を初期化し、第 8 戻り値を受け取る。
- green log では空 mapping のままとし、diff は実行しない。

### 5. node-local な受領証証拠

[tools/check_acceptance_reds.py:1561-1583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/check_acceptance_reds.py:1561)

変更前:

- main/wave の両 rc がある node は固定 5 field。
- test file 接触の根拠は記録されない。

変更後:

- 接触が理由で `flake` から `attributable` に留まった node にだけ、次を追加する。

```json
"wave_touched_path": "orchestrator/tests/test_example.py"
```

- 値は boolean ではなく、比較に使用した repo-relative path そのものとする。
- main 赤、wave 赤、未接触 flake の node shape は一切変えない。
- root field と [tools/check_acceptance_reds.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/check_acceptance_reds.py:22) の schema version は変えない。

## two-dot を選ぶ根拠

受入待ち手は main が進んでいれば [tools/dev_wave_wait.py:3038-3088](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/dev_wave_wait.py:3038) で main を wave に merge し、[tools/dev_wave_wait.py:3098-3099](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/dev_wave_wait.py:3098) で `HEAD..main == 0` を再確認してから受入を走らせる。land も [tools/dev_wave_land.py:1490-1501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/dev_wave_land.py:1490) で `tested_main` が `tested_tip` の ancestor であることと、`tested_main..tested_tip` の commit 閉包を検証する。

したがって受入時には merge base は `tested_main` 自身であり、merge-base/three-dot を別途求めても集合は変わらない。受入が実際に監査する A..T 閉包と同じ両端を使う two-dot を採用する。

## consumer と scope

### 推奨する 2 file 案

待ち手は checker rc が非 0 なら [tools/dev_wave_wait.py:2754-2756](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/dev_wave_wait.py:2754) で receipt を読む前に停止する。`wave_touched_path` を持つ node は必ず `attributable`、checker rc=1 なので、次の exact 検査には到達しない。

- root exact: [tools/dev_wave_wait.py:2762-2774](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/dev_wave_wait.py:2762)
- node exact: [tools/dev_wave_wait.py:2802-2812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/dev_wave_wait.py:2802)

land は checker receipt の `nodes[]` を直接消費しない。待ち手が作る外側 receipt の `red_nodeids` だけを [tools/dev_wave_land.py:607-625](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/dev_wave_land.py:607) で読み、checker blob の main/tip 一致を [tools/dev_wave_land.py:647-680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/dev_wave_land.py:647) で検証する。したがって land の更新は不要である。

### R2 を end-to-end で有効化する場合の scope 拡大

未接触 `flake` を本当に通すには、次を同時更新しなければならない。

- `tools/dev_wave_wait.py:2802-2815`: 現行 3-field `non-attributable` に加え、現行 5-field `flake` 形を exact に受理し、全 rc が 0 であることを検査する。
- `orchestrator/tests/test_dev_wave_wait.py:3296-3307` 周辺: flake node の受理、rc 不整合・未知 field の拒否を追加する。
- `tools/dev_wave_land.py`: 外側 receipt は不変なので更新不要。

これは production 2 file、test 2 file の計 4 file scopeになる。さらに現 HEAD の未接触 flake は現在「拒否」なので、この更新は下表のとおり受理集合を広げる。規律 2 の制約下では段 4 の明示裁定なしに採用できない。

## テスト計画

[orchestrator/tests/test_check_acceptance_reds.py:92-110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/orchestrator/tests/test_check_acceptance_reds.py:92) に、test file を main で追跡してから wave で変更し、両 SHA を返す小 helper を追加する。既存 `_advance_wave_tip()` は変えない。

[orchestrator/tests/test_check_acceptance_reds.py:571-670](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/orchestrator/tests/test_check_acceptance_reds.py:571) の後へ次を追加する。

1. `test_both_green_touched_test_file_is_attributable`

   両 probe rc=0、test file を wave が変更。rc=1、`classification=attributable`、`wave_touched_path` の exact path を要求する。これが無いと現行の無条件 `flake` 実装が通る。

2. `test_changed_paths_diff_is_once_from_wave_repo_with_two_dot`

   2 node を同じ touched file から出し、diff が wave repo で一度だけ、`tested_main..wave_tip` に対して呼ばれたことを検査する。これが無いと probe worktree 呼び出し、three-dot、node ごとの反復実装が通る。

3. `test_changed_paths_diff_failure_is_invalid_input`

   exact diff argv だけ rc=2 にし、checker rc=2、receipt 不在、probe 残骸なしを要求する。これが無いと diff 失敗を空集合として扱う fail-open 実装が通る。

4. `test_nearby_changed_path_does_not_match_test_file`

   `test_example.py.extra` のみを変更し、`test_example.py::...` は従来どおり `flake` とする。これが無いと prefix や basename 比較でも通る。

既存期待値は変更しない。

- `:468`, `:614`: main rc=1 なので差分判定へ入らず、3-field `non-attributable` のまま。
- `:496`, `:533`: wave rc=1 だけで `attributable` が確定し、diff を呼ばない。
- `:571`: wave が触るのは `tracked.txt` だけなので、5-field `flake` の exact 期待を維持する。この期待が「何か変更があれば全て attributable」という過剰拒否も検出する。
- `:649`: wave rc=2 は接触判定より先に `InvalidInput` のまま。
- `:1054`, `:1072`: wave tip identity と必須 CLI は diff より前の gate のまま。

## 規律 2 の before/after

推奨する checker 2 file 案の表である。

| 受入全走 | main 単独 | wave 単独 | test file 接触 | checker 変更前 | checker 変更後 | 現行 wait/land 前後 |
|---|---:|---:|---|---|---|---|
| 緑 | - | - | - | green、通す | 同じ | 通す → 通す |
| 赤 | 1 | 未実行 | 任意 | non-attributable、通す | 同じ | 通す → 通す |
| 赤 | 0 | 1 | 任意 | attributable、拒否 | 同じ | 拒否 → 拒否 |
| 赤 | 0 | 0 | なし | flake、checker は通す | 同じ | 拒否 → 拒否 |
| 赤 | 0 | 0 | あり | flake、checker は通す | attributable、拒否 | 拒否 → 拒否 |

checker 境界では最後の cell だけ縮小し、land 境界では変化ゼロである。広がる cell はない。

一方、待ち手も変更して未接触 flake を通す案は、現 HEAD に対して次の拡大を持つ。

| main 単独 | wave 単独 | 接触 | wait/land 変更前 | wait/land 変更後 |
|---:|---:|---|---|---|
| 0 | 0 | なし | 拒否 | 🔴 **通す。受理集合拡大** |

## 退けた案

- 単独再走を N 回繰り返す: 不採用。1 dispatch は最大 900 秒の queue 待ち、3600 秒の実行、300 秒 grace、60 秒 accounting を持つため `_DISPATCH_TIMEOUT_SECONDS=5100` である [tools/check_acceptance_reds.py:25-28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/check_acceptance_reds.py:25)。node 再走自体も [tools/check_acceptance_reds.py:956-994](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/check_acceptance_reds.py:956) で毎回 force-dispatch される。N 回とも単独なら、48 worker 文脈でだけ再現する順序・競合を観測できず、費用だけが N 倍になる。

- test file 全体を再走する: 不採用。現行の file 走は [tools/check_acceptance_reds.py:997-1045](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/check_acceptance_reds.py:997) の collect-only に限られ、判定本体は single node である。file 実行へ変えると同 file 内の別失敗を帰属へ混ぜ、なお cross-file の順序汚染や worker 間競合は再現しない。各 probe は [tools/check_acceptance_reds.py:1211-1235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1116-nonattrib-checker/tools/check_acceptance_reds.py:1211) で worktree 作成と submodule 初期化も行う。

- 差分到達可能性の完全な写像: 今回は不採用。現行が持つのは collection path と exact selector の写像だけで、`conftest.py`、fixture、plugin、動的 import、subprocess、共有 filesystem・port への依存は表現していない。完全写像は [T-389] 相当の別機構であり、両 revision の解析・動的依存採取・consumer 契約まで必要になる。

- `flake` を全面廃止する: 技術的には最も安全で、一般の差分起因 full-suite-only 赤も閉じる。しかし未接触 flake を救う R2 を正面から破るため、今回の裁定なしには採らない。

なお (P3) 自体も完全な因果判定ではない。wave が test file を直接触らず、共有 fixture や production code を介して full-suite-only 赤を作る場合は checker 単体では `flake` のままである。現行 wait が全 flake を拒否している間は land 穴にならないが、R2 を consumer まで開くならこの残余を明示的に受容する裁定が必要である。

## 検証予定

この段では一切実走していない。実装後に親が少なくとも次を実行する。

- `python3 tools/run_tests.py orchestrator/tests/test_check_acceptance_reds.py`
- consumer 拡張を採る場合のみ `orchestrator/tests/test_dev_wave_wait.py` と `orchestrator/tests/test_dev_wave_land.py`
- wave 前後へ同じ分類 matrix を通し、deny→allow が 0 件である反転検査
- 事前登録した差分判定 mutation、`tools/check_codex_agents.py`、`tools/check_docs.py`
- commit 後の `tools/check_ai_provenance.py`

## 総括

(P3) は checker 単体では「接触あり flake」だけを拒否へ縮める安全な変更として実装できる。  
最大の未解決点は、現行 waiter が既に全 `flake` を exact node 検査で拒否しており、親 brief の land 前提が成立しないことである。  
推奨は 2 file の checker 強化とし、`wave_touched_path` は新しく拒否される node にだけ記録する。  
段 4 では「現行受理集合を守って checker 強化だけ行う」か、「R2 を実効化するため 4 file scope と未接触 flake の受理拡大を明示承認する」かを裁定すべきである。