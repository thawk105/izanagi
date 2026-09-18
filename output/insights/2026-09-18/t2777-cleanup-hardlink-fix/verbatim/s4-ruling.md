# 段 4 裁定 — [T-2777] (2026-09-18 11:12 JST、親)

裁定 inbox 再走査: main は 24ede1d11 → 302b94796 (16 commit、docs/dev-wave/operations.md の DW-O23/O27 縮約と insight のみ。tool/test は不変、T-2777/T-2778 の新裁定なし)。自 branch を ff-only で 302b94796 へ揃えた。

## 所見の裁定

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A1 | plan の述語 (中間 component に `objects`) は `modules/sub/refs/objects/topic` (ref 名 `objects/topic`)、`modules/objects/config` (submodule 名 `objects`)、`modules/sub/logs/refs/objects/topic` の registry file を受理する | **real / must-fix** | 採用。分類規則を (P1') に置換 |
| A2 | unlink が外部 alias の bytes を消す / semantic・symlink・marker 迂回 | refuted | — |
| A3 | 負例 A の直接 assertion が locked で先に落ちる / B が述語に届かない / nlink==0 を許容 | refuted | — |
| A4 | object store 外の hardlink の分布は未確定 (nit)、synthetic fixture の被覆限定 (nit)、brief の一般化 (nit) | real / nit | 表現を訂正、fixture に `.idx` と入れ子 store を足す |
| B1 | `stable()` から nlink/ctime を外すと ctime による変更履歴の検出が弱まる (同 size・mtime 復元の上書きは inode 同一でも可能) | real / nit (説明の過大) | 採用: 保証の記述を訂正。実装は plan どおり (object に限り除外)。撤去前の sha256 照合は残る |
| B2 | `linked` fixture は部分撤去後の再入を被覆しない | real / nit | 採用: 既存 `test_cleanup_partial_admin_removal_reenters` の `removed="gitdir", tamper=None` の 1 case にだけ helper を足す (node 数不変) |
| B3 | M1 到達性 (A の直接 assertion + B の CLI) | refuted (plan 正) | plan どおり |
| B4 | M3 は rc=30 phase=admin-remove、部分撤去・journal 公開済み | refuted (plan 正) | 変異実測で stderr の phase を確認 |
| B5 | M4 wrapper の具体化 (保存 fstat、dev/ino 照合、先行フラグ、patch 範囲) | refuted (成立) + 仕様 | 採用: 仕様を author へ渡す |
| B6 | harness の空 expected_nodes 契約は未確認 (nit) | 親確認事項 | 親が probe で確認 (DW-M07 の probe 手順) |
| B7 | 所要 +0.3〜2 秒 | nit | 親が計時 |
| P2 5→6 呼出し | real | brief 訂正 |
| 全数 rc=20 の表現 | real | brief 訂正 (F1026 の条件付き表現) |

## (P1') 分類規則 — 「object の名前形」で決める (親の裁定、A1 の是正)

構造的規則 (`objects` の親 dir に `HEAD` と `config` があれば submodule gitdir) は却下する。理由: 撤去は名前順 (`HEAD` → `config` → … → `objects`) なので、部分撤去後の再入で生きた snapshot は `HEAD`/`config` を失い、object を registry と誤分類して再び rc=30 で詰まる (`_recheck_admin` 931/951 行は生きた木を再走査する)。path だけで決まる規則にする。

`_is_shared_object_path(prefix: str, name: str) -> bool` (module 定数 regex):
- `parts = (prefix + name).split("/")`、`parts[0] == "modules"` かつ `len(parts) >= 5` (最短 `modules/<sub>/objects/<xx>/<hash>`)。
- `parts[-3] == "objects"` かつ次のどちらか:
  - loose: `parts[-2]` が `[0-9a-f]{2}` かつ `name` が `[0-9a-f]{38}` または `[0-9a-f]{62}` (SHA-1 / SHA-256 repo)。
  - pack: `parts[-2] == "pack"` かつ `name` が `pack-[0-9a-f]{40}\.[a-z]+` または `pack-[0-9a-f]{64}\.[a-z]+`。
- それ以外はすべて False (`objects/info/*`、`multi-pack-index`、`refs/objects/topic`、`modules/objects/config`、`logs/**`、`hooks/**`、`packed-refs`、`index`、`config`、`HEAD` を含む)。実環境の source store (`.git/modules/<top>/objects/`) は `info/` が空で `pack/` は `pack-<40hex>.{pack,idx}` のみ (11:10 JST 実測)。この形の外に hardlink が現れたら現行どおり rc=20 (fail-closed) で、その時の file 名を根拠に形を足す (本 wave では足さない)。
- 判定は名前形だけで、bytes・git object 形式・sibling を見ない。regular file の確認・symlink 拒否・marker 拒否は現行のまま `_read_admin_file` / `_admin_snapshot` に残る。

`_read_admin_file(fd, name, *, allow_shared_object=False)`: 入口検査は `not S_ISREG or (st_nlink != 1 and not (allow_shared_object and st_nlink > 1))` で拒否 (nlink==0 は常に拒否)。`stable()` は `allow_shared_object` のとき `(dev, ino, mode, size, mtime_ns)`、それ以外は現行の 7 要素。呼出し側: `_admin_snapshot` 798 行と `_remove_admin_entries` 971 行だけが `allow_shared_object=_is_shared_object_path(prefix, name)` を渡す。`_remove_admin_entries` に `*, prefix: str = ""` を足し、再帰で `prefix + name + "/"`、1027 行は `prefix=""`。他 6 呼出し (631、831、832、880、1013、1034) は不変。snapshot の content (length + sha256) は不変、nlink は入れない。

保証の記述 (B1): object file では読取中の nlink/ctime 変化を許容するため、「ctime だけに履歴が残る改変」の検出は弱まる。残るのは inode/dev/mode/size/mtime の安定性と、snapshot 時と撤去直前の length+sha256 一致。object は内容アドレスの不変 file であり、撤去は自 wave の directory entry の unlink だけ (973 行) なので、他 worktree の alias の bytes に触れる経路は増えない。

## テスト (P5')

helper `_add_shared_admin_objects(repo, tmp_path)` — admin dir (`repo.main/.git/worktrees/wave`) に synthetic file を置く:
- `modules/sub/HEAD`, `modules/sub/config` (nlink 1、通常 file)
- `modules/sub/objects/ab/<38hex>` (loose)、`modules/sub/objects/pack/pack-<40hex>.pack`、`.idx`
- `modules/sub/modules/nested/HEAD`, `modules/sub/modules/nested/config`, `modules/sub/modules/nested/objects/cd/<38hex>` (入れ子 store)
- object 4 件を `tmp_path` 直下 (admin と common の外) へ `os.link` し nlink==2 を assert。alias と期待 bytes の組を返す。

node:
- 正例 `test_admin_shared_objects_are_removed`: `_make_repo` → `_stub_unoccupied` → helper → `_run` → `_assert_success_output(..., "removed", occupancy_phases=("preflight","recheck"))`、`_assert_removed`、admin dir 不在、各 alias の bytes 不変・nlink==1。
- 負例 `test_admin_nonobject_hardlink_is_rejected[<param>]` (4 case、各 1 理由): `gitdir` (root registry; CLI rc=20 に加え、CLI 前に `cleanup._admin_snapshot(fd)` の `pytest.raises(ValueError, match="admin entry is not a single regular file")` を直接 assert — resolver 631 行が先に落ちるため CLI だけでは述語を検証しない)、`submodule-config` (`modules/sub/config`)、`ref-named-objects` (`modules/sub/refs/objects/topic`)、`submodule-named-objects` (`modules/objects/config`; `modules/objects/HEAD` も置く)。全 case: `(rc, out) == (20, "")`、stderr に文言、`_admin_tree_state` 不変、`refs/heads/wave == repo.tip`、alias の bytes・nlink==2 不変。`_stub_unoccupied` を入れる。
- recovery 正例: 既存 `test_unpublished_admin_journal_reenters[linked]` と `test_cleanup_partial_admin_removal_reenters[gitdir-None]` (param id は現物で確認) の該当 case にだけ helper を足し、初回 rc=30 時点で alias nlink==2、再入成功後に bytes 不変・nlink==1 を assert。parametrize の直積は増やさない。
- race `test_admin_read_link_race[object|registry]`: git repo 不要。`tmp_path` に file (nlink 1) と親 dir fd。元の `os.fstat` を保存し、wrapper は保存関数で stat を取り、(dev, ino) が対象と一致し未注入ならフラグを先に立てて `os.link(target, alias)` を実行してから取得済み stat を返す。以後は実値。patch は `monkeypatch.setattr(cleanup.os, "fstat", wrapper)` を `_read_admin_file` の直接呼出しの間だけ。object: `allow_shared_object=True` で bytes が返る。registry: keyword なしで `ValueError("admin entry changed while reading")`。両方で注入実行・bytes 不変・実 nlink==2 を assert。DW-O14: wrapper は実物へ委譲し実 file へ実 link を張る観測 wrapper で、`_read_admin_file` は本 wave の編集対象 (no-touch でない)。

既存負例 C (journal) は不変。node 名 pin 2 件 (`test_real_occupancy_scan_rejects_live_process_cwd`、`test_git_argv_spy_sees_only_allowlisted_cleanup_commands`) は不変。

## 変異の事前登録 (P6'; anchor は実装後に DW-M07 で再検証、期待 node は probe で完全集合を取る)

file はすべて `tools/dev_wave_cleanup.py`、`hang_risk=false`。
- M0 (positive / SURVIVED / nodes []): `_is_shared_object_path` の最終 `return` 式を外側括弧で包む等価変異。
- M1 (negative / KILLED): `_is_shared_object_path` の本体を `return parts[0] == "modules"` (modules 配下なら恒真) に置換 → 負例 4 case が KILL (gitdir は直接 assertion、他 3 は CLI rc=0 化)。
- M2 (positive / KILLED): 本体を `return False` に置換 → 正例、`linked`、`gitdir-None` が KILL (rc=20)。
- M3 (positive / KILLED): `_remove_admin_entries` 側の呼出しだけ `allow_shared_object` を外す → 正例、`linked`、`gitdir-None` が rc=30 phase=admin-remove で KILL。
- M4 (negative / KILLED): `stable()` の分岐条件 `if allow_shared_object:` を `if True:` に置換 → `test_admin_read_link_race[registry]` が KILL。
- 期待 node 集合は実装 commit 後の probe (全件 SURVIVED 登録) で観測してから最終 spec に書く (DW-M07)。probe と本走の runner argv は `orchestrator/tests/test_dev_wave_cleanup.py` 1 file (自走 harness あり、baseline 143 node / 13 秒 login)。本走は `--runner-mode dispatch`、job dir 内の detached worktree (統合 commit) に対して harness 直接。

## scope 外 / 裁定パッケージ候補
- なし (両 consult とも候補なし)。[T-2778] は含めない。object store 外の hardlink を将来許容する要望は別裁定。

## 段 5 分割
- author 1 本 (tool + test 同一所有、workspace-write、`--max-model-calls 400`)。commit 禁止・docs 編集禁止・pytest 実走不可 (import + 直接呼出しで fixture 成立と反実仮想を確認させる)。
- 段 6 review 2 本: A = 受理集合の境界 (名前形の広狭、registry 拒否の恒真性、D2119 項 8)、B = race/recovery/変異帰属 (prefix、M1〜M4 の到達性と単一理由性、wrapper の安全性)。
