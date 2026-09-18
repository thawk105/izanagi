## 方針と読解範囲

P1〜P7 の局所修正方針を採用する。変更対象は `tools/dev_wave_cleanup.py` と `orchestrator/tests/test_dev_wave_cleanup.py`。T-2778、汎用 allowlist、他 tool への展開は含めない。撤去対象を自 wave の admin gitdir に限定する境界は維持する（D2119 項8、DW-O28）。

指定された必読資料はすべて読めた。以下の行番号は変更前の現物を指す。ファイル編集・pytest・実環境への操作は行っていない。テスト結果、変異結果、所要時間は未実測である。

親 brief への修正点は主に次の3点。

- P2 の「他5箇所」は **6呼出し**。
- P6 の M1 は、記載どおりの CLI 負例 A だけでは KILL できない。後述の snapshot 層の検証を同じ負例へ加える。
- brief 冒頭の「初期化済み worktree の全数で rc=20」は、F1026 と insight §1.3 が明示する条件付きの表現へ戻す。

## P1/P2：述語と呼出し変更

[tools/dev_wave_cleanup.py:752](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2777-cleanup-hardlink-fix/tools/dev_wave_cleanup.py:752) の直前に、次の最小述語を追加する。

```python
def _is_admin_object(prefix: str, name: str) -> bool:
    parts = (prefix + name).split("/")
    return parts[0] == "modules" and "objects" in parts[1:-1]
```

これは **path の分類だけ**を行う。regular file の確認は `_read_admin_file` に残す。`prefix` は admin root からの相対パス、空文字または末尾 `/`、`name` はディレクトリエントリ1個という既存の走査契約を使う（779〜805行）。

受理例は loose、pack、`.idx`、`.rev`、入れ子 submodule の object。`gitdir`、`modules/sub/config`、`modules/sub/HEAD`、root の `objects/...`、basename 自体が `objects` のファイルは該当しない。Git object の内容や拡張子を検証する機構は追加しない。

752〜762行の diff 案は次のとおり。

```diff
-def _read_admin_file(fd: int, name: str) -> bytes:
+def _read_admin_file(fd: int, name: str, *, allow_shared_object: bool = False) -> bytes:
     child = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
     try:
         metadata = os.fstat(child)
-        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
+        if (not stat.S_ISREG(metadata.st_mode)
+                or (metadata.st_nlink != 1
+                    and not (allow_shared_object and metadata.st_nlink > 1))):
             raise ValueError("admin entry is not a single regular file")
         with os.fdopen(os.dup(child), "rb") as stream:
             raw = stream.read()
         def stable(st):
+            if allow_shared_object:
+                return (st.st_dev, st.st_ino, st.st_mode, st.st_size,
+                        st.st_mtime_ns)
             return (st.st_dev, st.st_ino, st.st_mode, st.st_nlink, st.st_size,
                     st.st_mtime_ns, st.st_ctime_ns)
```

`nlink != 1` を無条件に免除せず、追加受理を `nlink > 1` に限定する。symlink、特殊 file、操作 marker の拒否は現行のまま（753、782〜803行）。

798〜800行は次へ置換する。

```python
            content = _admin_content(
                _read_admin_file(
                    fd, name, allow_shared_object=_is_admin_object(prefix, name)),
                semantic=prefix + name in {
                    "gitdir", "commondir", "HEAD", "logs/HEAD"})
```

956、966、971、1027行は次の diff とする。

```diff
-def _remove_admin_entries(fd: int, snapshot: dict, recheck) -> None:
+def _remove_admin_entries(fd: int, snapshot: dict, recheck, *, prefix: str = "") -> None:
```

```diff
-                _remove_admin_entries(child, content, recheck)
+                _remove_admin_entries(child, content, recheck, prefix=prefix + name + "/")
```

```diff
-            if _admin_content(_read_admin_file(fd, name), semantic="raw" in content) != content:
+            raw = _read_admin_file(
+                fd, name, allow_shared_object=_is_admin_object(prefix, name))
+            if _admin_content(raw, semantic="raw" in content) != content:
```

```diff
-        _remove_admin_entries(admin.admin_fd, snapshot, recheck_remaining)
+        _remove_admin_entries(admin.admin_fd, snapshot, recheck_remaining, prefix="")
```

既定拒否を残す呼出しは **631、831、832、880、1013、1034行の6件**。resolver の `gitdir`、binding の `gitdir` / `commondir`、journal の読取には keyword を渡さない。

## P3/P4：安定性、同一性、recovery

object file に限り、`stable()` から `st_nlink` と `st_ctime_ns` を外す案を推奨する。registry file の比較タプルは逐語のまま残す。

親 brief P3 が前提とする `link` の性質は、同一 inode の link count と ctime が更新されることである。他 worktree の local clone が読取の前後に hardlink を追加すると、bytes が不変でも現行764〜766行は `admin entry changed while reading` を出す。preflight 中なら1359〜1360行により rc=20、mutation 中なら1322〜1323行により rc=30 になる。

DW-O13 の nlink 275 / 285 / 288 は共有と変動を裏付ける資料値として使う。ただし、今回読んだ資料だけでは **同一 inode の値の時系列と、読取区間に重なった clone の発生は直接確認できない**。race の発生頻度と実際の重なりは未実測とする。

同一性の検証は次を維持する。

| 検証箇所 | 維持する検査 |
|---|---|
| 753〜765行 | no-follow、regular file、dev / ino / mode / size / mtime、FD と名前の照合 |
| 772〜775、804行 | length + sha256 と inode identity |
| 913〜920行 | recovery の残存項目が元 snapshot の部分集合で、inode と bytes が一致 |
| 958〜960行 | 各削除対象の inode が snapshot と一致 |
| 971〜973行 | 再読した length + sha256 が一致してから unlink |

この既存の同一性モデルを維持するには十分と判断する。任意の同時書換えに対する完全な原子性まで証明するものではなく、その一般化は本件に含めない。nlink は他 worktree の clone・削除で変動するため、snapshot に追加しない（P4、772〜775行）。

973行の `os.unlink` は当該ディレクトリエントリ1本を除去する。外部 alias が残れば inode と bytes は残る。この効果は正例で alias の bytes と nlink=1 を確認する。

recovery の prefix は次のように復元できる。

1. `_load_admin_recovery` が journal を既定拒否で読み、`_bind_admin(..., recovery=data)` に渡す（880、893行）。
2. `_bind_admin` は階層を保った `recovery["snapshot"]` を採用する（837、855〜856行）。
3. `_recheck_admin` は現在の root snapshot を取り、保存済み snapshot と部分集合照合する（931、941〜942行）。
4. `_remove_admin_entries` は root の `prefix=""` から入り、ディレクトリ階層ごとに `name + "/"` を足す。途中撤去後も残存 snapshot の階層から正しい prefix が付く。

931 / 951行の `_admin_snapshot` は、いずれも root から795行の再帰を通り、同じ述語を使う。830、1019、1025、1287行の snapshot も同様である。journal の形式変更や prefix の永続化は不要。

## P5/P7：fixture と正負例

追加位置は [orchestrator/tests/test_dev_wave_cleanup.py:1089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2777-cleanup-hardlink-fix/orchestrator/tests/test_dev_wave_cleanup.py:1089) の helper 周辺を推奨する。既存 `_make_repo`（57〜88行）、`_run`（111〜114行）、`_assert_removed`（177〜185行）を再利用する。

helper は `_add_synthetic_admin_objects(repo, tmp_path)` とし、次を作る。

```text
main/.git/worktrees/wave/
  modules/sub/config
  modules/sub/HEAD
  modules/sub/objects/ab/<38hex>
  modules/sub/objects/pack/pack-<40hex>.pack

tmp_path/
  loose-object-alias
  pack-object-alias
```

- config / HEAD は通常ファイル、nlink=1。
- loose / pack の bytes は固定した任意値でよい。
- object 2件から `tmp_path` 直下へ `os.link` し、両方 nlink=2 を確認する。
- helper は alias と期待 bytes の組を返す。
- real submodule、`.gitmodules`、submodule update は作らない。

新規 Git 操作は既存 fixture と結果確認に必要なものに限定する。synthetic file の追加自体は Git subprocess を増やさない。

正例 node：

```text
orchestrator/tests/test_dev_wave_cleanup.py::test_admin_shared_objects_are_removed
```

`_make_repo` → `_stub_unoccupied` → helper → `_run` の順とし、次を確認する。

```python
_assert_success_output(
    _run(repo, capsys),
    "removed",
    occupancy_phases=("preflight", "recheck"),
)
_assert_removed(repo)
assert not admin.exists()
```

各 alias の bytes が期待値と一致し、nlink=1 に戻ることも確認する。occupancy の形式は既存199〜207行に合わせる。

負例 A/B は1関数の2 parameter とする。

```text
orchestrator/tests/test_dev_wave_cleanup.py::test_admin_nonobject_hardlink_is_rejected[gitdir]
orchestrator/tests/test_dev_wave_cleanup.py::test_admin_nonobject_hardlink_is_rejected[submodule-config]
```

A は `admin/gitdir`、B は `admin/modules/sub/config` から `tmp_path` 直下へ alias を作る。B の config / HEAD は synthetic な通常ファイルとして作る。両方とも次を確認する。

- `(rc, out) == (20, "")`
- stderr に `admin entry is not a single regular file`
- link 作成後に採った `_admin_tree_state(admin)` が不変
- `refs/heads/wave` が `repo.tip` のまま
- alias の bytes と nlink=2 が不変

`_stub_unoccupied` は両方に入れる。正常系の対象外要因を減らし、M1 で snapshot を通過した場合も occupancy による偽 KILL を避ける（135〜140行）。

**A には CLI 実行前に snapshot 層の拒否を直接確認する assertion を加える。**

```python
fd = os.open(admin, os.O_RDONLY | os.O_DIRECTORY)
try:
    with pytest.raises(ValueError, match="admin entry is not a single regular file"):
        cleanup._admin_snapshot(fd)
finally:
    os.close(fd)
```

理由は、M1 でも resolver の631行が `gitdir` を既定拒否するため、CLI 結果だけでは変更した述語の境界を検証できないからである（1183〜1185行）。直接検証を加えれば、A は root registry の snapshot 境界、B は `modules/` 配下の非 object 境界をそれぞれ守れる。追加の repo 作成は不要。

既存負例 C は変更せず残す。

```text
orchestrator/tests/test_dev_wave_cleanup.py::test_admin_journal_unrelated_temporary_does_not_allow_hardlink
```

## recovery 正例と読取 race のテスト

recovery 正例は既存 `test_unpublished_admin_journal_reenters` の **`linked` ケースだけ**へ helper を加える（1239〜1294行）。parameter の直積は増やさない。

```text
orchestrator/tests/test_dev_wave_cleanup.py::test_unpublished_admin_journal_reenters[linked]
```

`linked` は final journal が存在し、temporary と hardlink を共有した中断状態なので、880→893→837行の recovery 経路へ入る。`write` / `publish` は final journal がなく、同じ経路を証明しない（1281〜1285行）。

`linked` ケースでは、初回 rc=30 の時点で object alias が nlink=2、再入後は既存の `occupancy_phases=()` の成功確認に加え、alias の bytes 不変・nlink=1 を確認する。これで recovery における prefix の伝播を追加 repo なしで検証できる。

P3 と M4 は、Git repo 不要の小さな読取テストで検証する。

```text
orchestrator/tests/test_dev_wave_cleanup.py::test_admin_read_link_race[object]
orchestrator/tests/test_dev_wave_cleanup.py::test_admin_read_link_race[registry]
```

設計は以下。

1. 初期 nlink=1 の実ファイルと親ディレクトリ FD を作る。
2. 元の `os.fstat` を保存する。
3. 対象 inode の最初の `fstat` だけ、実際の stat 結果を取得した直後に `os.link` してから、取得済みの結果を返す wrapper に置換する。
4. 後続の `fstat` は実値を返す。stat 結果そのものは捏造しない。
5. object は `allow_shared_object=True` で bytes が返ることを確認する。
6. registry は keyword を省略し、`admin entry changed while reading` を確認する。
7. 注入が実行され、bytes 不変、実 nlink=2 であることを確認する。

これは755行と764行の間で実 inode に link を追加する決定的な interleaving であり、sleep や並行 process は不要。ctime の時計分解能に依存せず nlink 差で負例が成立する。M4 を殺せる見込みは静的に確認できるが、実測は親が行う。

DW-O06 については、本案は real submodule を初期化しないため、依頼で示された「submodule 系 real-repo test」の条件には該当しない。既存 `_make_repo` が通常の real Git repo を作ることとは区別する（57〜88行、P7）。

## P6：変異の事前登録

以下は上記 diff 適用後の source を対象とする。全件 `file` は `tools/dev_wave_cleanup.py`、`hang_risk=false`。各変異は1箇所置換とする。

`tools/mutation_harness.py:544〜577` の契約に従い、spec root は次のキーだけを使う。

```text
schema, estimated_run_seconds, timeout_seconds,
hang_timeout_seconds, mutations
```

各 mutation は次のキーだけを使う。

```text
id, category, replacements, expected_nodes,
expected_status, hang_risk
```

replacement は `file / old / new` のみ。説明文や結果欄を spec に足さない。`old` がちょうど1回出現することは1083〜1089行の契約で確認する。実装後に anchor が変わった場合、変異実行前に登録を合わせる。

**M0：等価変異、採用。**

```json
{
  "file": "tools/dev_wave_cleanup.py",
  "old": "    return parts[0] == \"modules\" and \"objects\" in parts[1:-1]",
  "new": "    return (parts[0] == \"modules\" and \"objects\" in parts[1:-1])"
}
```

`category="positive"`、`expected_status="SURVIVED"`、`expected_nodes=[]`。括弧だけなので受理集合・生成 argv は変わらない。

**M1：述語恒真、採用。**

```json
{
  "file": "tools/dev_wave_cleanup.py",
  "old": "    return parts[0] == \"modules\" and \"objects\" in parts[1:-1]",
  "new": "    return True"
}
```

`category="negative"`、`expected_status="KILLED"`。

```text
orchestrator/tests/test_dev_wave_cleanup.py::test_admin_nonobject_hardlink_is_rejected[gitdir]
orchestrator/tests/test_dev_wave_cleanup.py::test_admin_nonobject_hardlink_is_rejected[submodule-config]
```

A は追加した snapshot 直接検証で、B は CLI が非 object hardlink を受理してしまうことで KILL。赤理由はいずれも「非 object を共有 object と誤分類」である。A の CLI 検証だけを根拠に KILL 期待を登録してはならない。

**M2：述語恒偽、採用。**

```json
{
  "file": "tools/dev_wave_cleanup.py",
  "old": "    return parts[0] == \"modules\" and \"objects\" in parts[1:-1]",
  "new": "    return False"
}
```

`category="positive"`、`expected_status="KILLED"`。

```text
orchestrator/tests/test_dev_wave_cleanup.py::test_admin_shared_objects_are_removed
orchestrator/tests/test_dev_wave_cleanup.py::test_unpublished_admin_journal_reenters[linked]
```

両方とも初回 preflight で object hardlink を拒否する。通常正例は期待 rc=0 に対して20、recovery fixture は期待する初回 rc=30 に対して20。共通の赤理由は「正当な object hardlink の拒否」。

**M3：撤去側だけ既定拒否へ戻す、採用。**

```json
{
  "file": "tools/dev_wave_cleanup.py",
  "old": "            raw = _read_admin_file(\n                fd, name, allow_shared_object=_is_admin_object(prefix, name))",
  "new": "            raw = _read_admin_file(fd, name)"
}
```

`category="positive"`、`expected_status="KILLED"`。

```text
orchestrator/tests/test_dev_wave_cleanup.py::test_admin_shared_objects_are_removed
orchestrator/tests/test_dev_wave_cleanup.py::test_unpublished_admin_journal_reenters[linked]
```

snapshot は通るが、削除時の object 再読で拒否する。通常正例と recovery の再入は **rc=30、`phase=admin-remove`**。例外変換は `_remove_admin` 内ではなく、呼出し元 `_mutate` の1300〜1301、1322〜1323行で行う。

**M4：stable の除外を registry に拡大、採用。**

```json
{
  "file": "tools/dev_wave_cleanup.py",
  "old": "        def stable(st):\n            if allow_shared_object:",
  "new": "        def stable(st):\n            if True:"
}
```

`category="negative"`、`expected_status="KILLED"`。

```text
orchestrator/tests/test_dev_wave_cleanup.py::test_admin_read_link_race[registry]
```

初回 stat は nlink=1 なので入口検査を通る。その後の実 link による変動を、変異後の `stable()` が見逃すため `pytest.raises` が失敗する。入口の nlink 拒否など、別理由では止まらない設計である。

この実 link を使う fixture が対象環境で成立しない場合、未検証の KILL を記録せず M4 の登録を取り下げる（依頼の F28 条件）。現時点では実行可能な設計を示せるため採用を推奨する。

既存赤および `--deselect` の必要性は未実測。brief:21 の除外集合が空という記述から、既存赤がないとは断定しない。計画では `--deselect` を追加せず、親の baseline で確認する。

## consumer、実測、所要時間

`test_pytest_collection_config.py:388〜393` の `test_real_occupancy_scan_rejects_live_process_cwd` と488行の `test_git_argv_spy_sees_only_allowlisted_cleanup_commands` は名前・parameter を変更しない。既存 recovery の `linked` node 名も維持する。

docs/dev-wave と DW-O28 literal は変更しない。`check_docs.py` 自体も変更しない。文書成果物は親が扱う worklog / failures fragment と段9の一次記録に限定する。

親の検証順は次を推奨する。

1. 新規正負例、読取 race、既存 journal / recovery / registry 再検査の焦点走。
2. baseline 緑を確認して M0〜M4 を実行。
3. cleanup test 全体と node pin consumer の検証。
4. 指定の受入全走 `tools/dev_wave_wait.py acceptance --lease-optional`。
5. land 後、本 wave の DW-O28 自己撤去を1回実測し、rc と診断を記録。

pytest は親側の所定 runner 経由で行う。本段では実行しない。

追加コストは通常成功1 repo、負例2 repo、repo 不要の race 2ケース。recovery は既存 `linked` ケースへ synthetic file を足すだけで、repo 作成回数を増やさない。受入全走5分以内と `test-time-regression-rule` 適合は未実測であり、親の計時で判定する。

## 分割と親 brief への異議

段5は **author 1本、tool と test を同一所有**で足りる。述語、呼出し、fixture、変異 anchor が密接であり、実装を分割する利点は小さい。段6のレビューは2本を推奨する。

- A：受理集合。root registry と modules 非 object の拒否、述語が対象を広げすぎていないこと、regular / symlink / marker の境界、D2119 項8の維持。
- B：race と recovery。`stable()` の object 限定、全 snapshot と削除再帰の prefix、journal の既定拒否、M1 の到達性と M3 の rc、各変異の赤理由。

親 brief への異議・補足は次のとおり。

1. **P2 の件数誤り**：既定拒否を残すのは6呼出し。列挙された対象自体は正しい。
2. **P6 の M1 の到達性**：A の CLI は631行で拒否されるため、述語恒真を殺せない。A に snapshot 層の直接 assertion を追加して解消する。
3. **P3 と不変条件(iv)の表現**：P3 は最終 nlink が1へ戻る link/unlink 中の ctime 変動も許容する。「追加受理する静的 file 形は object の nlink>1」「同じ object に限り link 操作に伴う読取中の nlink/ctime 変動を許容」と分けて記載すると正確。
4. **DW-O13 の一般化**：115 regular / 31 shared、loose25 / pack6、symlink0、registry nlink=1 は本 wave の観測値として扱う。将来の全 admin や実際の race 発生を証明する値ではない。
5. **brief:5 の全数表現**：F1026 と insight §1.3 に従い、「object hardlink が残り、通常 preflight の snapshot に到達する対象では rc=20」とする。過去の蓄積全体の原因や「直近11 wave 連続」は、今回の射影資料だけでは裏付けを独立確認できない。
6. **文書 scope の表現**：brief:6 の「docs は fragment のみ」と18行の insight README は、後者を段9一次記録という既定成果物として明示すれば整理できる。author のコード変更範囲は広げない。

## 総括

**推奨案**：`_is_admin_object(prefix, name)` で `modules/` 始まりかつ中間 component に `objects` がある path を分類し、その regular file の nlink>1 だけを追加受理する。object の `stable()` から nlink / ctime を外し、registry の比較は現状維持する。snapshot と撤去再帰へ同じ述語・prefix を通す。

**正例・負例 node**（すべて `orchestrator/tests/test_dev_wave_cleanup.py::` 配下）：

- 正例：`test_admin_shared_objects_are_removed`
- recovery 正例：`test_unpublished_admin_journal_reenters[linked]`
- 負例 A/B：`test_admin_nonobject_hardlink_is_rejected[gitdir]`、`[submodule-config]`
- 既存負例 C：`test_admin_journal_unrelated_temporary_does_not_allow_hardlink`
- race 正負例：`test_admin_read_link_race[object]`、`[registry]`

**変異**：M0 は SURVIVED 期待で採用、M1〜M4 は KILLED 期待で採用。M1 の A には snapshot 直接検証が必要。M3 は rc=30。M4 は実 `os.link` を初回 stat 後に注入する負例で到達させる。全結果は未実測。

**親 brief への異議**：6呼出しへの訂正、M1 の到達性修正、全数 rc=20 と nlink 時系列の過大な一般化の回避、P3 と静的受理集合の区別。T-2778 や新規 gate は不要。

**予算見積**：以後の Codex 子は author 1本＋並列 review 2本の計3本。author 20〜35分、review 10〜20分、親の焦点・変異・受入確認10〜20分で、待ち時間・追加修正・land を除く wall 40〜75分程度。見積は未実測であり、受入全走の5分上限とは別枠である。