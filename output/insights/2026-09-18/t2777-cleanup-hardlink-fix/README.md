# [T-2777] `tools/dev_wave_cleanup.py` の hardlink 拒否を registry file と object store で分ける — 段 9 の自己撤去 (DW-O28) が submodule 初期化済み worktree で rc=20 になる F1026 の恒久対応

- authority: none
- default_effect: no-state-change
- 日付: 2026-09-18
- wave: dev-wave-t2777-cleanup-hardlink-fix (branch `worktree-dev-wave-t2777-cleanup-hardlink-fix`、軽量版 + 段 2/3/6 の敵対子)
- 起点: ユーザー依頼 [T-2777] (P1、F1026、entry 1641)。案は `output/insights/2026-09-18/cleanup-si-routing/README.md` §3.2 案 A
- 基準: local main `24ede1d11` (wave 開始時) → `302b94796` へ ff (段 4 直前、docs のみの前進)。実装 commit = `94715928d` (1 巡目) + `fbd8c7038` (fix 1)
- job dir (prompt・log・patch・変異台帳の原本): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2777-cleanup-hardlink-fix/`

## 0. 結論

- **恒久対応を実装した。** `_read_admin_file` の `st_nlink != 1` 拒否は、admin dir 相対 path が **object の名前形** (`modules/…/objects/<2hex>/<38|62hex>` の loose object、`modules/…/objects/pack/pack-<40|64hex>.<ext>` の pack file、かつ `modules` と末尾 3 component の間に `refs` / `logs` を含まない) の regular file に限り `nlink > 1` を許容する (`_is_shared_object_path`、`allow_shared_object`)。同 file では読取中の安定性検査 (`stable()`) から `st_nlink` / `st_ctime_ns` を外す (他 worktree の local clone が同一 inode へ link を張り、nlink と ctime が読取中にも変わるため。本 wave の admin dir で nlink は 10:41 の 275〜288 → 11:03 の 293 と増加を実測)。
- **受理集合の拡大はそれだけ。** registry file (root 直下の `gitdir` / `commondir` / `HEAD` / `index` / `logs/**` 等、journal、`modules/**` の非 object: `config` / `HEAD` / `refs/**` / `logs/**` / `packed-refs`)、symlink・特殊 file・操作 marker、nlink==0 の拒否、snapshot の length+sha256 照合、撤去対象が自 wave の admin gitdir だけ (D2119 項 8) はすべて不変。`_read_admin_file` の 7 呼出しのうち述語を通すのは `_admin_snapshot` と `_remove_admin_entries` (prefix を再帰へ伝播) の 2 経路だけで、resolver (`_administrative_gitdirs_for_wave`)・binding (`gitdir` / `commondir`)・journal の 6 呼出しは既定 (拒否) のまま。
- **検証:** 正例 1 (synthetic の loose + pack + `.idx` + 入れ子 store を hardlink 入りで撤去、alias の bytes 不変・nlink が 1 に戻る)、負例 6 (`gitdir` は snapshot 層の直接 assertion 付き、`modules/sub/config`、`refs/objects/topic`、submodule 名 `objects` の `config`、`refs/heads/objects/ab/<38hex>`、`logs/refs/heads/objects/ab/<38hex>`)、race 2 (fstat 初回に実 `os.link` を注入する決定的 test: object は読める、registry は `admin entry changed while reading`)、recovery 既存 2 case (`linked`、`None-gitdir`) の拡張。変異 matrix (§5) は M0 等価 SURVIVED、M1〜M5 KILLED、MISMATCH 0。受入全走は §6。
- **段 9 の自己撤去 (live 正例) の rc は本 README には書けない** (段 9 は land 後で、この記録 commit は land 前に凍結される)。最終報告に載せ、次 wave の worklog へ記録する (F1026 の記載どおり)。
- **限界 (裁定済み、追加実装しない):** (a) `objects/info/*`、`multi-pack-index`、`pack-*.bitmap` 等の名前形外の store 補助 file が hardlink されていれば現行どおり rc=20 (fail-closed)。本 wave の source store (`.git/modules/<top>/objects/`) は `info/` 空・`pack/` は `.pack`/`.idx` のみ (11:10 JST 実測) なので、現環境では到達しない。(b) submodule の path 自体が `refs` / `logs` を component に持つ場合の真の store も rc=20 (安全側)。(c) object file では ctime だけに残る改変履歴の検出が弱まる (残るのは dev/ino/mode/size/mtime の安定性と撤去直前の length+sha256 一致。object は内容アドレスの不変 file で、撤去は自 wave の directory entry の unlink のみ)。(d) 段 9 の live 成功 1 回は「その時点の本 wave の構成」しか証明せず、全 worktree での解消を一般化しない。

## 1. 変更面

| file | 変更 |
|---|---|
| `tools/dev_wave_cleanup.py` | `_OBJECT_FANOUT_RE` / `_LOOSE_OBJECT_RE` / `_PACK_OBJECT_RE` / `_REGISTRY_TREE_NAMES`、`_is_shared_object_path(prefix, name)`、`_read_admin_file(fd, name, *, allow_shared_object=False)` (入口条件と `stable()` の分岐)、`_admin_snapshot` の呼出し、`_remove_admin_entries(fd, snapshot, recheck, *, prefix="")` と再帰・root 呼出し |
| `orchestrator/tests/test_dev_wave_cleanup.py` | helper `_add_shared_admin_objects`、`test_admin_shared_objects_are_removed`、`test_admin_nonobject_hardlink_is_rejected[6 case]`、`test_admin_read_link_race[object|registry]`、`test_cleanup_partial_admin_removal_reenters[None-gitdir]` と `test_unpublished_admin_journal_reenters[linked]` への alias assertion 追加 (既存 assertion の削除 0 行、node 名 pin 2 件不変) |

docs は spool fragment (worklog / failures) と本 insight のみ。`docs/dev-wave/*.md` は触っていない。

## 2. 段 1 で実測した事実 (DW-O13 の入力)

本 wave の admin dir `.git/worktrees/dev-wave-t2777-cleanup-hardlink-fix/` (10:41 JST、submodule 初期化直後): regular file 115、うち nlink>1 が 31、全件 top-level submodule の `objects/**` (loose 25 + pack 6 = `pack-<40hex>.{pack,idx}` ×3)、nlink = 275 / 285 / 288 (11:03 に 293)。入れ子 submodule の store は nlink==1 (同じ形)。symlink 0。registry file は全件 nlink==1。**この値は本 wave の 1 admin dir の観測であり、全 worktree への一般化ではない** (段 3 レンズ A / B の指摘で限定)。

## 3. 段 2〜4 — plan と敵対相談が親 brief を直した点

- plan (codex、`verbatim/s2-plan.md`): 既定拒否を残す呼出しは 5 でなく 6。負例 A (`gitdir` の hardlink) の CLI は resolver 631 行が snapshot より先に拒否するので、述語恒真 M1 を殺すには snapshot 層 (`_admin_snapshot(fd)`) の直接 assertion が要る。M3 (撤去側だけ既定) は rc=30 `phase=admin-remove`。M4 は fstat 初回に `os.link` を注入する決定的 race test で殺す。「全数で rc=20」は F1026 の条件付き表現へ。
- consult A (`verbatim/s3-consult-A.md`) **must-fix A1**: plan の述語「中間 component に `objects`」は `modules/sub/refs/objects/topic` (ref 名 `objects/topic`) や submodule 名 `objects` の `config` を受理する。consult B: must-fix なし、`stable()` 除外で ctime 履歴検出が弱まる旨を明記、M4 wrapper の仕様 (保存 fstat・dev/ino 照合・先行フラグ)。
- 段 4 裁定 (`verbatim/s4-ruling.md`): 構造的規則 (`objects` の親 dir に `HEAD`+`config` があれば gitdir) は**却下** — 撤去は名前順で `HEAD` → `config` → … → `objects` なので、部分撤去後の再入で生きた snapshot が object を registry と誤分類して rc=30 で詰まる。path だけで決まる**名前形**の規則を採用。

## 4. 段 5〜6 — 実装とレビュー

- author 1 巡 (codex、7 分): 実装 + 直接呼出し (`DIRECT_CALL_PASS` 9 node、反実仮想で赤化確認)。指摘: 裁定の M1 `return parts[0] == "modules"` は gitdir 負例を殺さない → M1 = `return True` に改訂。負例では tool の `git status` が index を任意更新して `_admin_tree_state` の inode 比較を壊すため `GIT_OPTIONAL_LOCKS=0` を設定 (レビュー A が「拒否を迂回しない、index を比較対象に残す点で代替より強い」と判定)。
- レビュー A (`verbatim/s6-review-A.md`) **NO-GO、must-fix A1**: ref 名 `objects/ab/<38hex>` (`git check-ref-format` rc=0 の合法な名前) の loose ref とその reflog が object の名前形に一致し registry hardlink を受理する。親が段 4 で「害は無い」と見送った点を、不変条件 (i) との衝突として是正。レビュー B (`verbatim/s6-review-B.md`) GO。
- fix 1 (codex): `modules` と末尾 3 component の間に `refs` / `logs` があれば False。負例 2 case 追加。受理集合は縮小方向のみ。
- 焦点再レビュー (`verbatim/s6-focus-1.md`): A1 closed、製品コード must-fix なし。**変異登録の must-fix**: fix 後の最終 `return` は末尾名前形だけなので、その 2 行を `return True` にしても 760/763 行の `if` が負例を拒否し続け M1 は恒真にならない → 親の final v1 は erratum (§5.1)、M1 の `old` を述語本体全体 (759〜766 行) にした v3 で再走 (§5.2)。
- 焦点走: 1 巡目 150 passed (計算ノード、4.4 秒)、fix 後 152 passed (login、14.1 秒)。consumer `test_pytest_collection_config.py` 76 passed (計算ノード、103 秒)。

## 5. 変異 matrix (container `.codex/worktrees/t2777-mutcontainer`、`tools/mutation_harness.py` 直接、dispatch、runner = `run_tests.py orchestrator/tests/test_dev_wave_cleanup.py -q -rf --force-dispatch`)

### 5.0 probe (94715928d、全件 SURVIVED 登録で観測 node を集める、`verbatim/mutation-probe.json`)

M0 SURVIVED、M1 (末尾 return = 当時は述語全体) → 負例 4、M2 → 正例 + `linked` + `None-gitdir`、M3 → 同 3 node、M4 → `race[registry]`。予測と完全一致、余分な赤 node なし。6 走 5 分。

### 5.1 erratum — final v1 (fbd8c7038、`verbatim/mutation-spec-final.json` / `mutation-final.json`)

M1 の `old` を末尾 return 2 行にしたため恒真化に失敗し **M1 SURVIVED (期待 KILLED、rc=1)**。M0 SURVIVED (期待どおり)、M2 / M3 / M4 / M5 は期待 node 完全一致で KILLED。焦点再レビューが投入直後に指摘したとおりで、初回結果として保存する (DW-M02)。

### 5.2 最終 — final v3 (fbd8c7038、`verbatim/mutation-spec-final-v3.json` / `mutation-final-v3.json`、rc=0)

| 変異 | 内容 | 期待 | 結果 | 失敗 node |
|---|---|---|---|---|
| M0 | 述語の最終 return を外側括弧で包む (等価) | SURVIVED | SURVIVED | — |
| M1 | 述語本体全体を `return True` (恒真) | KILLED | KILLED | `test_admin_nonobject_hardlink_is_rejected` の 6 case |
| M2 | 末尾 return を `return False` (現行復帰) | KILLED | KILLED | `test_admin_shared_objects_are_removed`、`test_unpublished_admin_journal_reenters[linked]`、`test_cleanup_partial_admin_removal_reenters[None-gitdir]` |
| M3 | `_remove_admin_entries` 側の読取だけ既定 (拒否) に戻す | KILLED | KILLED | M2 と同じ 3 node (rc=30 `phase=admin-remove`) |
| M4 | `stable()` の分岐 `if allow_shared_object:` を `if True:` (registry も nlink/ctime を見ない) | KILLED | KILLED | `test_admin_read_link_race[registry]` |
| M5 | `refs`/`logs` の除外節を `if False:` | KILLED | KILLED | `[ref-shaped-object]`、`[reflog-shaped-object]` |

baseline PASSED (152 node)、matching 6/6、MISMATCH 0、7 走。

## 6. 受入全走

attempt 1 (12:03〜12:20 JST、17 分、`tools/dev_wave_wait.py acceptance --lease-optional -- python3 tools/run_tests.py`): verdict **`child-green`**、tested main `1e844bcbc`、tested tip `3d44403f2` (post-claim merge で local main 47 commit を取り込んだ merge commit)、25,095 passed / 69 skipped、3 shard、lease 未取得 (D662 の疑似 holder `e349ce85ff62`、`release` 不要)。受領証は job dir `acceptance-receipt-1.json` (schema の全 field あり)。投入時の login load は下降局面 (1 分 11.9 < 5 分 14.2 < 15 分 17.3)、他 wave の受入 leader 3 本と同時 (受入調停 thread から「中断しない、赤なら門番条件で再投入」の通知あり。赤は出なかった)。

## 7. 段 9 の自己撤去 (live 正例)

land 後に `python3 tools/dev_wave_cleanup.py --main-worktree <MAIN> --wave-worktree <WAVE> --wave-branch <BRANCH> --tested-wave-tip-sha <TIP>` を本 wave 自身の worktree (hardlink 31 件入り) に当てる。結果 (rc・status) は本 README の凍結後なので最終報告と次 wave の worklog に載せる。

## 8. 工数

codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 1、focus 1、全段 `gpt-6-astra` / medium)。変異 matrix 3 走 (probe、final v1 erratum、final v3)。計算ノード job: 焦点走 2、consumer 1、変異 19 走 (3 matrix × (baseline + 変異))、受入 1。

## 9. verbatim 一覧 (本 dir `verbatim/`)

`s1-brief.md`、`s2-plan.md`、`s3-consult-A.md`、`s3-consult-B.md`、`s4-ruling.md`、`s5-author.md`、`s6-review-A.md`、`s6-review-B.md`、`s6-ruling.md`、`s6-fix1.md`、`s6-focus-1.md`、`mutation-spec-probe.json`、`mutation-probe.json`、`mutation-spec-final.json`、`mutation-final.json` (erratum)、`mutation-spec-final-v3.json`、`mutation-final-v3.json`。
