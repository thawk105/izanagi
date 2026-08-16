## 実装プラン

行番号は現在の checkout 基準である。brief の `_replay_manifest:3886-3890` は現行ではずれており、実体は `tools/codex_reasoning_ab.py:4658`、oracle 完全一致は `:4887-4890` にある。

### 編集面と検査順

1. `tools/codex_reasoning_ab.py:915-981` の `_submodule_worktree_state`

   - 既存の path containment、directory 判定、`rev-parse --show-toplevel`、`HEAD/gitlink` 照合をそのまま残す。
   - 既存 `HEAD/gitlink` 照合の直後、return の前に `actual_admin = _git_dir(candidate_path)` を求め、`actual_admin == admin_dir` を必須にする。
   - 新規理由は例えば `initialized submodule gitdir/admin mismatch: <path>: <actual> != <expected>` とし、`RC_SNAPSHOT=20`。
   - これにより攻撃 D を落とす。既存の以下の文字列は一字も変更しない。
     - `initialized submodule HEAD/gitlink mismatch`
     - `submodule object store cannot be inspected`
     - `submodule worktree is not a directory`
   - HEAD 照合を先に残すため、既存 HEAD mismatch ケースの理由優先順位も保つ。

2. `tools/codex_reasoning_ab.py:1200-1237` の `_index_stage_entries` 直後

   新規に `_submodule_content_identity_reasons(snapshot, repositories)` を置く。各 initialized repository に対し次の順で実行する。

   1. index と `HEAD^{tree}` の比較。
   2. `_index_stage_entries` で mode、blob id、path を取得。
   3. 各 path を `lstat` し、file type と実行 bit を検査。
   4. symlink blob を照合。
   5. regular file 群を一括で path-aware hash し、index blob id と照合。

   新規理由の安定 prefix は以下とする。

   - `initialized submodule index/HEAD tree mismatch: <repo>`
   - `initialized submodule worktree/index mismatch: <repo>: <path>`
   - `initialized submodule content cannot be inspected: <repo>: ...`

   helper は理由を返し、既存の closure 理由と併記できる形にする。単純な `git diff-files` 判定にはしない。

3. `tools/codex_reasoning_ab.py:984-1037` の `_submodule_inventory`

   - `rows` の `path`、`gitlink_commit`、`initialization` は変更しない。
   - 現行 DFS と `seen` による重複・循環拒否を維持する。
   - 内容 helper は inventory 自体に埋め込まず、inventory が返す全 initialized repository に gate 側から一度だけ掛ける。これにより次を守る。
     - `_preflight_snapshot_relocation` と `_seal_git_object_closure` のたびに全ファイルを再 hash しない。
     - `test_uninitialized_nested_submodule_gitlink_pin_rejects_change` の既存「inventory 後に pin mismatch」という検査段を不用意に変えない。
     - uninitialized descendant は inventory 行には残すが、存在しない worktree bytes を hash しない。

4. `tools/codex_reasoning_ab.py:1396-1435` の `_git_closure_reasons`

   - `initialized, submodules = _submodule_inventory(snapshot)` を一度だけ取得。
   - 既存 ref、fsck、forbidden object、filesystem allowlist の理由を先に作り、その後に content identity 理由を追加する。既存理由の順序を最大限維持する。
   - `tools/codex_reasoning_ab.py:1240-1257` の `_expected_filesystem_files` に optional な precomputed `initialized` 引数を足し、ここから渡す。二度目の inventory を避ける。
   - P3 を採る場合のみ、closure 有効時に `(snapshot, *initialized)` の local config を調べ、post-seal の `submodule.*` を別理由で拒否する。この検査は `_seal_git_object_closure:1123-1141` より後の verify 側へ置く。seal 前に置くと、初期化用 URL を消す前に自己拒否するため不可。

5. `tools/codex_reasoning_ab.py:1603-1727` の `verify_snapshot`

   - `enforce_closure=True` は `_git_closure_reasons` 経由で内容照合する。
   - `enforce_closure=False` の else 枝 `:1690-1691` でも、inventory が返した initialized repository に同じ helper を掛ける。custom spec で gate を迂回できなくする。
   - oracle dict `:1706-1726` には何も追加しない。正常 snapshot の canonical bytes、`submodule_manifest_sha256`、`manifest_sha256` を不変にする。
   - `_preflight_snapshot_relocation:1059-1120` は変更しない。そこから inventory を呼ぶため marker/admin 束縛は効く一方、既存の absolute marker と `core.worktree` の理由は残る。

6. `tools/codex_reasoning_ab.py:715-762` の `_init_submodules_from_local_source`

   - marker/admin と既存 HEAD/gitlink は `_submodule_worktree_state` の共通強化により source 側にも必ず適用される。
   - source の全 worktree bytes まで要求するかは段 4 裁定とする。厳格案なら `state == "initialized"` の直後、`initialized.append` より前に content helper を `local` へ掛ける。
   - 推奨案では full content helper は source に掛けない。source の普通の tracked bytes は clone 入力ではなく、Git は local repository の object database から destination の gitlink commit を checkout するためである。destination snapshot には full gate を掛ける。
   - 現行の source index と `.gitmodules` の整合検査は残す。したがって source 側を無条件に緩める変更にはしない。

### Git argv と object closure

| 目的 | argv | sealed object closure を変更しない根拠 |
|---|---|---|
| index↔HEAD tree | `["git", "diff-index", "--cached", "--quiet", "--ignore-submodules=none", "HEAD", "--"]` | `--cached` は tree と既存 index を読むだけ。Git の説明上も `write-tree` せず同等比較を行う command。`--ignore-submodules=none` は post-seal の `ignore=all` を明示的に上書きする。 |
| index entry 列挙 | `["git", "ls-files", "--stage", "-z"]` | 既存 index の read-only 列挙。object も index も書かない。 |
| regular file hash | `["git", "hash-object", "--", path1, ..., pathN]` | `-w` が無いため blob id を計算するだけで object database へ書かない。path ごとの clean/EOL filter が適用される。argv 上限を避ける場合だけ固定 byte 上限で chunk 化する。 |
| symlink blob 読取 | `["git", "cat-file", "blob", object_id]` | 既存 object の読取だけ。 |
| marker 解決 | `["git", "rev-parse", "--absolute-git-dir"]` | marker が指す既存 admin dir を解決するだけ。 |
| P3 config 再検査 | `["git", "config", "--local", "--name-only", "--get-regexp", "^submodule\\."]` | 値の設定・削除 option がなく read-only。rc=1 かつ空 stdout を「不在」とする。 |
| custom filter 判定を採る場合 | `["git", "check-attr", "--stdin", "-z", "filter"]` と `["git", "check-attr", "--cached", "--stdin", "-z", "filter"]` | attributes の照会のみ。NUL 区切り入力により改行を含む path も扱える。 |

`git write-tree` は禁止する。攻撃 C のように index が HEAD と異なる状態で実行すると新しい tree object を object database に生成し、その tree が ref から到達不能となる。後続 `git fsck --unreachable` を内容 gate とは別の偶発理由で赤くし、封緘済み closure 自体も汚す。

### worktree↔index の場合分け

| index mode | worktree 検査 |
|---|---|
| `100644` | non-symlink regular file を要求。owner execute bit が立っていれば mode mismatch。path-aware `hash-object` の結果を index blob id と比較する。 |
| `100755` | non-symlink regular file と owner execute bit を要求。Git が保持するのは executable category であり、全 permission bit の完全一致は要求しない。blob は `100644` と同じ方法で照合する。 |
| `120000` | `lstat` が symlink であることを要求。`os.fsencode(os.readlink(path))` を `git cat-file blob <index-id>` の bytes と直接比較する。target を dereference しない。 |
| `160000` | blob hash 対象外。親 index の gitlink id と child `HEAD` は既存 state 検査、child の index/HEAD/worktree は再帰した repository 自身の gate で検査する。uninitialized なら bytes 検査せず、既存 `verify_snapshot:1693-1695` が拒否する。 |
| CRLF・built-in attributes | raw bytes の hash ではなく、path-aware `git hash-object` で clean 後の blob id を比較する。したがって index と意味的に同じ CRLF checkout は受理できる。 |
| custom `filter=<driver>` | path-aware hash なら index と一致させられるが、外部 clean driver が起動しうる。段 4 で許可か fail-closed 拒否かを裁く。 |

filter 問題は実在する。CCBench の `.gitattributes` は `* text=auto eol=lf` である。read-only probe では `probe\r\n` の raw hash は `89bc60...`、`--path=README.md` の attribute-aware hash は `da0c4e...`、`probe\n` の raw hashも `da0c4e...` だった。したがって素の hash 比較は不可である。一方、現行 CCBench に `filter=` 属性はなく、設定済みの LFS driver を選択する path もない。

### 再帰と実 CCBench

`_submodule_inventory` の `repositories` は全深さの initialized repository を DFS 順で含むため、内容 helper はこの flat list 全体へ一度掛ける。gitlink 自体は親で、child files は child repository で検査され、深さごとに同じ三者照合になる。

現 worktree では `external/ccbench` は initialized、`external/ccbench/third_party/shirakami` は `-fb14...` の未初期化で、directory も空である。したがって CCBench の 404 regular files と 1 gitlink は検査するが、Shirakami の存在しない bytes へ降りない。snapshot oracle まで進めば、未初期化行は従来どおり `submodule is not initialized` で拒否される。

## 受理集合の変化

reject-only 案では、snapshot の新受理集合は概念的に次となる。

`A_new = A_old ∩ marker_admin ∩ index_head ∩ worktree_index ∩ optional_postseal_config`

従って新規に accept へ入るものはなく、`A_old - A_new` は次の集合である。

| 対象 | 現行 test / production | 修正後 | P1 reject-only の oracle bytes | 証拠記録案の oracle bytes |
|---|---|---|---|---|
| A: child index 空、worktree 空、`ignore=all` | 既存 node なし。親 probe と production `verify_snapshot` は accept | index/HEAD mismatch で `RC_SNAPSHOT` | oracle を生成しない | 同左 |
| B: child bytes 改変、size/mtime 保存、`ignore=all` | 既存 node なし。production は accept | worktree/index mismatch | oracle を生成しない | 同左 |
| C: HEAD tree にない index+worktree file、`ignore=all` | 既存 node なし。production は accept | index/HEAD mismatch | oracle を生成しない | 同左 |
| D: relative marker を rogue admin へ変更 | 既存 node なし。production と relocation preflight は accept | marker/admin mismatch | oracle を生成しない | 同左 |
| clean content + post-seal `submodule.*` config | 現行 closure は config metadata を oracle に載せて accept | P3 採用時だけ reject | oracle を生成しない | 同左 |
| symlink target または executable category の不一致を `ignore=all` で隠す | path 集合は同じなので現行 accept | worktree/index mismatch | oracle を生成しない | 同左 |
| clean-filter 後に同じ CRLF worktree | 現行 Git status は clean | 引き続き accept | 完全に byte-identical | 新証拠 field 分だけ必ず変化 |
| 無改変 initialized submodule | `test_verify_snapshot_submodule_gate_accepts_all_initialized` が accept | 引き続き accept | `submodules`、両 SHA、oracle 全 bytes が不変 | row 内記録なら両 SHA が変化。別 field でも oracle と `manifest_sha256` は変化 |
| uninitialized nested submodule | `_git_closure_reasons` 単体の既存 node は accept、`verify_snapshot` は既に reject | 同じ | 変化なし | clean oracle に証拠を足すなら変化 |
| dirty な live source | 現行は dirt の種類によって accept | strict P4 なら新規 reject。推奨案なら現状維持し destination を検査 | destination が正常なら不変 | destination の正常 oracle も変化 |

既存 node への扱いは次のとおり。

- `test_verify_snapshot_submodule_gate_accepts_all_initialized`: 正例として維持・強化する。
- `test_uninitialized_nested_submodule_is_manifested_and_accepted`: initialized child だけ照合し、未初期化 grandchild は降りないため維持する。
- `test_uninitialized_nested_submodule_gitlink_pin_rejects_change`: content helper を inventory 自体へ埋め込まないため、既存の pin mismatch 検査段を維持する。
- `test_snapshot_relocation_preflight_rejects_absolute_gitdir`: absolute marker が正しい admin を指す場合は新 marker gate を通り、既存 `absolute submodule gitdir is not relocatable` で拒否され続ける。
- `test_shared_base_copy_preserves_metadata_and_relocates_submodules`: skip-worktree / assume-unchanged flag に依存せず実 bytes を読むが、内容が同じなので受理され続ける。

production では `verify_snapshot` の closure 有効・無効両経路と、`_replay_manifest:4887-4890` の再検証に効く。正常な過去 oracle は reject-only 案なら完全一致を保つ。攻撃済みの保存 snapshot は replay 中に拒否される。`collect_run` / `make_packets` に独立再検証を追加したとは扱わず、そこは brief どおり T-1263 のままとする。

## テスト設計

`orchestrator/tests/test_codex_reasoning_ab.py:2004-2101` の `_synthetic_verify_snapshot_with_submodules` は既存の返値と既定動作を保ったまま、keyword-only の `source_setup` と `initialized_setup` callback を追加する。

- `source_setup(source, index)` は commit 前に `.gitattributes`、symlink、executable file などを作れるようにし、既存 `git add child.txt` を `git add --all` へ置き換える。
- `initialized_setup(submodule, index)` は checkout 後、seal 前に CRLF 表現や test 用 config を用意できるようにする。
- callback のため `orchestrator/tests/test_codex_reasoning_ab.py:45-55` の typing import に `Callable` を追加する。
- 攻撃 A〜D は fixture が seal を終えてから適用し、修正後 helper に阻まれて再 seal できない setup にはしない。

`_synthetic_verify_snapshot_spec:2104-2128` は clean snapshot 作成時の `submodule_manifest_sha256` を spec に pin できるようにする。A〜D は manifest の三 field を変えないため、この pin が通っても内容 gate が拒否することを示せる。

提案 node は以下である。

| node | 対象 |
|---|---|
| `test_verify_snapshot_submodule_content_gate_rejects_empty_index_and_worktree` | 攻撃 A。child に `read-tree --empty`、`.git` 以外を削除、親に `ignore=all`。 |
| `test_verify_snapshot_submodule_content_gate_rejects_worktree_blob_mismatch_with_preserved_stat` | 攻撃 B。同じ byte 数に差し替え、mtime を復元し、stat cache 非依存を証明。 |
| `test_verify_snapshot_submodule_content_gate_rejects_index_entry_absent_from_head_tree` | 攻撃 C。`extra.txt` を index と worktree に追加し、親で ignore。 |
| `test_verify_snapshot_submodule_content_gate_rejects_git_marker_bound_to_rogue_admin_dir` | 攻撃 D。小さい synthetic admin を同じ深さの `rogue` へ複製し、relative marker だけ変更。 |
| `test_verify_snapshot_submodule_gate_accepts_all_initialized` | 既存正例を維持し、oracle key 集合、manifest row、SHA が増えていないことも確認。 |
| `test_submodule_content_gate_accepts_clean_filter_equivalent_crlf` | raw hash は異なるが path-aware hash は index id と一致する正例。 |
| `test_submodule_content_gate_rejects_symlink_target_mismatch` | `120000` の target bytes 改変。 |
| `test_submodule_content_gate_rejects_executable_bit_mismatch` | `100755` と実 worktree owner execute bit の不一致。 |
| `test_verify_snapshot_rejects_post_seal_submodule_config` | P3 採用時。内容無改変でも post-seal `submodule.*` を拒否。 |
| `test_submodule_content_gate_rejects_active_custom_filter_attribute` | custom driver を禁止する裁定の場合。 |
| `test_init_submodules_from_local_source_rejects_dirty_initialized_source` | strict P4 を選ぶ場合のみ。 |
| `test_init_submodules_from_local_source_allows_irrelevant_dirt_and_validates_destination` | 推奨 source 方針を選ぶ場合。 |
| `test_submodule_content_gate_batches_hash_object_without_object_writes` | 3 個以上の regular file でも repository 当たり 1 batch、`write-tree` なし、`hash-object -w` なしを記録。 |

全 node で `caught.value.rc == TOOL.RC_SNAPSHOT` と新理由 prefix を検査する。A〜C では `ignore=all` 自体を残し、既存 status gate ではなく新しい三者照合が発火したことを確認する。

成長比例コストは次の形で抑える。

- すべて `tmp_path` 上の 1 commit、1 submodule、数 file の synthetic repo を使う。
- `_ROOT`、`benchmark_snapshots`、historical sessions、`output/` の件数を走査しない。
- 攻撃 D が複製する admin dir も synthetic の固定サイズである。
- 新 helper は `git log`、`rev-list --all`、artifact walk を追加しない。
- regular file は repository ごとに一括 hash し、process 数を file 数へ比例させない。読む bytes 量が tracked bytes に比例することだけは内容照合上不可避である。
- command 記録 node で batch 性と object-write command の不在を固定する。

この子では pytest は実行しておらず、上記は静的検査と read-only Git probe に基づく設計である。

## 未解決の裁定候補

1. **oracle 証拠を記録するか**
   - 推奨: P1 の reject-only。
   - 理由: 正常 snapshot の oracle と両 SHA を完全不変にでき、`_replay_manifest` の byte 完全一致を壊さない。証拠 field 案は schema、schedule pin、保存 manifest の再発行まで波及する。

2. **source live worktree に full 三者照合を要求するか**
   - 推奨: 現行の source topology 検査、HEAD/gitlink、新 marker/admin 束縛までとし、普通の tracked bytes の dirt は許す。生成された destination を full 検査する。
   - 理由: local clone が読むのは source object database であり、dirty worktree bytes ではない。strict 案は安全性を増やさず、開発中 CCBench を新たに拒否しうる。
   - strict を採るなら `:715-762` で helper を明示的に呼び、source 受理集合が縮むことを記録する。

3. **post-seal `submodule.*` config を独立に拒否するか**
   - 推奨: closure 有効 snapshot では拒否する。
   - 理由: A〜C は直接 gate で既に落ちるが、seal が全 section を消す契約を verify 側でも確認できる。source や `enforce_closure=False` へは適用しない。

4. **custom external clean filter を許すか**
   - 推奨: built-in `text`、`eol` 等は path-aware hash で許し、active な `filter=<driver>` は当面 fail-closed で拒否する。
   - 理由: `hash-object` 自体は object を書かないが、外部 clean driver の副作用までは保証できない。現行 CCBench は custom filter を使わないため対象受理集合への実害がない。
   - 許可する裁定なら、clean-filter-equivalent の正例と、filter 実行後も `.git` metadata が不変である検査が必要になる。

5. **P5 の「1 秒未満」を確定値として扱うか**
   - 推奨: まだ確定しない。
   - 理由: 親の測定には新しい path-aware 全 file hash が含まれていない。404 regular files を一括 hash する実装後、親が実 snapshot 3 repo で再測定してから記録する。

## 総括

- snapshot 側は marker/admin、index/HEAD tree、clean-filter 後の worktree/index を全 initialized depth で照合する。
- `write-tree` と `hash-object -w` は使わず、正常 snapshot の oracle bytes は変えない。
- CCBench は検査するが、未初期化の Shirakami の bytes へは降りず、既存の未初期化拒否を維持する。
- source の full dirt 拒否、post-seal config、custom filter の扱いは段 4 の明示裁定事項である。
- A〜D と無改変正例は小さい synthetic repo だけで固定し、履歴・成果物量へ比例する新テストを作らない。