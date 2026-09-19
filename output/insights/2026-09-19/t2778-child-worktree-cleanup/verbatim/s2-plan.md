## 1. 現行挙動

**子木専用 mode を追加し、既存 wave mode の判定・出力・再入契約は維持する設計を推奨します。** 指定資料とコードを静的に確認しました。ファイル変更、pytest、撤去の実走はしていません。以下の行番号は現行ファイルのものです。

`tools/dev_wave_cleanup.py:130` の既存 CLI は必須4組・任意1組のみを受理します。`_classify`（L685）の状態は次のとおりです。

| 状態 | directory | porcelain record | 指定 branch |
|---|---|---|---|
| a | あり | attached、HEAD一致 | tip一致 |
| b | あり | detached、HEAD一致 | tip一致で存在 |
| c | なし | detached、HEAD一致 | tip一致で存在 |
| d | なし | なし | tip一致で存在 |
| e | なし | なし | 不在 |

それ以外は拒否します。b は「branch不要」ではありません。

`_preflight`（L1065）は primary/main/tool の common gitdir 一致、main checkout の branch、tested tip と導出 landing tip の関係、cwd 対象外、fold state 不在などを確認します。a/b は clean、branch tip・branch reflog・HEAD reflog の全 commit が main 祖先、非占有が必要です。e も `_assert_already_clean`（L1351）で directory・record・admin・branch の不在を再確認します。

admin は `_bind_admin`（L835）で直接 registry child、inode、backpointer、commondir、内容 snapshot に束縛します。`_recheck_admin`（L945）は削除直前にも束縛と **HEAD reflog の main 祖先性**を検査します。

hardlink は一律許可ではありません。`_read_admin_file`（L774）で原則 `st_nlink == 1` を要求し、T-2777 の限定された submodule object store のみ例外です。refs/logs、binding、index 等への hardlink は拒否を維持します。

子木を既存 mode に渡すと、主に次で止まります。

- dirty：`_assert_clean_and_head`（L565）。
- 所有 path 限定 patch で取り込んだ子：`_assert_branch_safety`（L652）の祖先性。
- branch のない detached container：`_classify`。
- 入口だけ緩和しても、admin 撤去時の `_recheck_admin` で再度祖先性違反。

## 2. manifest 設計

置き場は固定名 **`<job-dir>/child-worktrees.json`**。job dir は primary、wave、全登録 worktree、common gitdir の外に置きます。

```json
{
  "schema": "izanagi-dev-wave-child-worktrees/v1",
  "job_dir": "/absolute/job",
  "wave_worktree": "/absolute/wave",
  "common_gitdir": "/absolute/repo/.git",
  "entries": [
    {
      "path": "/absolute/child",
      "purpose": "author",
      "branch": "refs/heads/impl-t2778",
      "base_sha": "<full-sha>",
      "owned_paths": ["tools/dev_wave_cleanup.py"],
      "registered_at": "<UTC timestamp>"
    }
  ]
}
```

header の wave path が必要です。entry の6項目だけでは「wave 本体を登録しない」を判定できません。

登録 CLI：

```text
python3 tools/dev_wave_cleanup.py register-child
  --main-worktree <M> --wave-worktree <W>
  --manifest <JOB>/child-worktrees.json
  --child-worktree <P> --purpose <PURPOSE> --base-sha <SHA>
  [--owned-path <repo-relative-file>]...
```

branch と timestamp は caller に書かせず、登録時の実体から取得します。purpose は `author|fix|mutation-container|probe|scratch`。

拒否条件：

- 相対 path、非正規表記、symlink component、入力と realpath の不一致。
- primary、manifest header の wave 本体、別 common gitdir、実在 record がない対象。
- job dir が repo 内、対象 directory 内、または削除対象と重なる配置。
- 不正・未知 schema、重複 JSON key、重複 entry path、型不一致。
- author/fix の `owned_paths=[]`、detached author/fix。
- owned path の絶対表記、`..`、`.git`、glob/pathspec magic、directory 指定。**正規化された個別 file path の閉集合**に限定する。
- base SHA が commit でない、登録時 HEAD の祖先でない。

同 path の再登録は **配列位置を保った置換**。fix 巡の branch・purpose・base・登録時刻の更新を許し、実体との一致を再検査します。ただし owned_paths の縮小によって不一致を隠せないよう、同じ編集単位では集合を維持します。変更が必要なら親が所有契約を更新してから明示登録します。

書込みは job directory の flock 下で、temporary file → fsync → atomic replace。読取り側も同じ lock と通常 file／非 symlink の検証を使います。登録直後、worker 起動前に成功を必須とします。

**耐性は fail-closed の整合検証です。** 手書きで branch・path・common 等を変えれば実体との照合で拒否します。一方、同一権限の主体が整合する manifest 全体を偽造したことや「本当に作成時に登録したこと」は、この schema だけでは証明できません。署名・hash chain は追加せず、その限界を明記します。

## 3. 子木撤去 mode の CLI と preflight

```text
python3 tools/dev_wave_cleanup.py remove-child
  --main-worktree <M>
  --manifest <JOB>/child-worktrees.json
  --child-worktree <P>
  --evidence-dir <JOB>/cleanup/<ENTRY>
  [--integration-ref <full-commit-sha>]
```

1呼出し1子木。integration-ref は省略可能な追加参照で、main は常に含めます。

| rc | 契約 |
|---|---|
| 2 | argv・path 表記・SHA 形式の不正 |
| 20 | manifest、実体、統合証明、退避可能性等の拒否 |
| 21 | mutation 前の占有 |
| 22 | mutation 前の占有判定不能・payload 不整合 |
| 30 | 退避書込み開始以降の失敗・割込み。後続処理を実行しない |

順序を固定します。

1. **manifest 束縛**：header、exact entry、schema、保存先を検査。
2. **記録実在・common 一致**：porcelain、`.git`、admin backpointer、HEAD、branch を突合せ。登録後の branch 変更は再登録なしでは拒否。
3. **対象制限**：非 primary、非 wave 本体、cwd 対象外、別 worktree を内包しないこと。fold state と進行中 Git 操作も拒否。
4. **占有**：既存 `_assert_unoccupied`（L484）を使用。
5. **統合証明**：以下の A または B。
6. **退避**：証拠 dir は不存在または空のみ。既存証拠を上書きしない。
7. **撤去**：unlock → detach → recheck → directory → admin → registry。
8. **branch と事後条件**：branch 保持／限定削除、directory・admin・record 不在、証拠存在を確認。

占有 payload は `check_worktree_occupancy.py:637` の契約をそのまま使用します。`unoccupied`、rc0、空 occupants/issues、対象一致等が必要です。既存の非阻害診断 `same_uid_cwd_unreachable` を新たな拒否条件には変えません。

**統合証明の具体形**

preflight 時に main と任意 integration-ref を commit SHA に固定し、集合を `R` とします。

```text
H = 現在HEAD ∪ HEAD reflogのold/new全非zero commit

A = 全 h∈H について、少なくとも1つの r∈R が h を祖先として持つ

B = owned_paths が非空、かつ
    ある1つの r∈R について、所有path全部の
    HEAD側とr側の (存在/不存在, mode, type, OID) が一致
```

B は **path ごとに別参照を選ぶことを禁止**します。blob ID だけでは executable bit や symlink の差を落とすため、tree entry 全体を比較します。削除は双方不存在として扱い、Git エラーを不存在扱いしません。未解決 index は拒否します。

空 owned_paths の probe/container は A のみ。空集合の全称真で B を通してはいけません。両方不成立なら比較参照と不一致 path を報告します。

**退避内容**

必須5ファイルを毎回作り、対象がなくても空 patch／空 tar を明示します。

| ファイル | 内容 |
|---|---|
| `tracked.patch` | `HEAD → worktree` の全 tracked 差分。binary・mode・削除を含む |
| `untracked.tar.gz` | 未追跡と ignored の実体。symlink を追わず相対名で保存 |
| `status.txt` | 撤去前 status。機械保存は NUL 区切りを保持 |
| `head-sha.txt` | detach 前 HEAD |
| `branch.txt` | 元の full branch ref。detached は明示表記 |

ただし、この5点だけでは保存が不足します。最小限、次も必要です。

- `index.patch`：HEAD→index。staged 編集を worktree で元に戻した場合も保存。
- `history.pack` と対象 SHA 一覧：main 非到達の HEAD reflog commit、および削除予定 branch の reflog commit と必要 objects。B で通った committed 所有外差分もここに含める。

`tracked.patch` は HEAD 基準なので、既に終端 commit に入った `author-result.md` 等を保存しません。branch 残置だけに依存すると、detached/reset 前履歴を失い得ます。追加 pack はこの穴だけを塞ぐものです。

退避の完了、fsync、内容再照合を済ませてから unlock します。削除直前に HEAD・branch・manifest・差分・未追跡一覧と内容が同じことを再確認します。特殊 file、退避できない dirty submodule／入れ子 repository は **対応済みと偽らず rc20 で保持**し、理由を出します。汎用 submodule 救出機構は本投入では作りません。

**detached と branch**

detached container は `branch=null` を受理し、detach／branch-delete を省略します。attached 子は branch を原則残置。削除する場合だけ、元 ref の tip 不変、他 holder 不在、**tip が現在の main の祖先**を再確認して `git branch -d -- <name>`。integration-ref の祖先であるだけでは削除しません。

phase 名は既存どおり：

```text
unlock → detach → recheck → remove-directory
→ admin-recheck → admin-remove → registry
→ branch-recheck → branch-delete → postcondition
```

その前に `backup` を追加します。mutation 後の占有再検査が21/22相当でも、外側の結果は既存と同じ `partial / recheck / rc30`。失敗後の自動続行・rollback・global prune は行いません。子 mode の不完全撤去を wave の a〜e に偽装せず、証拠と journal を保持して報告します。

## 4. 既存コードの再利用と非変更

変更点を次に限定します。

| 現行アンカー | 設計 |
|---|---|
| `dev_wave_cleanup.py:39` | 既存 `Args` は維持。別の RegisterChildArgs／RemoveChildArgs を追加 |
| L130 | `_parse_argv` は変更しない |
| L209 | 新しい読取り・退避用 Git argv の exact allowlist を追加 |
| L835 | admin binding の実処理を小さな内部 helper に抽出。既存 wrapper の引数と呼出順を維持 |
| L945 | 構造・snapshot 検査を共有。wave wrapper は従来の main 祖先性、child wrapper は固定した統合証明を再検証 |
| L1012 | 同じ削除機構を利用するため内部処理を抽出。子 journal は mode・manifest・証拠に束縛 |
| L1230 | `_remove_verified_tree` をそのまま使用 |
| L1272 | 既存 `_mutate` は維持。別 `_mutate_child` を追加 |
| L1367 | argv 先頭が `register-child`／`remove-child` のときだけ別経路へ dispatch |
| L1411 | 既存例外・rc・診断形式を維持 |

**単に `_recheck_admin` を skip する設計は不可**です。また、子 HEAD を架空の tested-wave-tip として `Args` に詰めません。

再利用するのは path 検査、record parser、identity、cwd、occupancy、admin snapshot／FD binding／限定削除、branch delete です。`_classify`、`_assert_clean_and_head`、`_assert_branch_safety` は子 mode には適用しません。

allowlist に追加する形は以下です。自由な Git 引数を通す入口は作りません。

- `ls-tree -r -z --full-tree <full-sha>`：tree entry 比較。
- `ls-files --stage -z`：index／gitlink／未解決 stage 確認。
- `ls-files --others -z`：ignored を含む未追跡列挙。
- `diff --binary --full-index --no-ext-diff --no-textconv --no-renames <sha> --`
- 上記 `diff` の `--cached` 形。
- `pack-objects --revs --stdout`：検証済み SHA を stdin へ渡す退避専用形。

pack の stdin／stdout は新しい狭い helper で処理し、既存 `_git` の呼出契約を変えません。既存 `rev-parse --verify`、`merge-base`、`rev-list --walk-reflogs` は再利用できます。

## 5. 所有 path

Codex author 1単位の閉集合は **4ファイル**とします。

1. `tools/dev_wave_cleanup.py`
2. `orchestrator/tests/test_dev_wave_cleanup.py`
3. `tools/check_docs.py` — L628 の DW-O28 literal のみ
4. `orchestrator/tests/test_check_docs.py` — L189 の synthetic fixture のみ

新 module は作りません。manifest、退避、子 mode をこの tool 内の専用関数に留め、汎用 cleanup framework にしません。

tests は既存 fixture（`test_dev_wave_cleanup.py:58`）から tmp main/wave を作り、追加 child と repo 外 job dir を構成します。既存 `_assert_removed` は branch 消失を要求するため流用せず、子用 assertion を追加します。L1534 以降の禁止 argv・spy テストは変更せず、新形を検証する node を追加します。

親の所有：

- `docs/dev-wave/workers.md:19` DW-S05-A：作成直後登録、fix 再登録、所有集合、登録失敗時は起動しない。
- `docs/dev-wave/operations.md:209` DW-O28：子→本体、旧 manifest の明示回収。
- 同 L156 DW-O20：必要な場合だけ登録への短い参照。
- decisions／worklog の spool fragment 各1。

`git_state.py:231` の終端処理は全残差を add／commit し、所有外報告も branch に入れます。この挙動は変更しません。

## 6. 不変条件と正負例

正例 node：

`test_remove_child_archives_dirty_integrated_author_and_keeps_branch`

tmp child に `tracked.txt` の author commit と所有外 `author-result.md` を作り、wave へは `tracked.txt` だけを取り込みます。child は main 非祖先のまま、さらに staged／unstaged 編集と `scratch.txt` を残します。実登録 CLI → 実 remove CLI を通します。

確認対象：

- rc0。
- 必須5ファイル、index 退避、必要な履歴退避の存在と内容。
- child directory、対応 admin gitdir、porcelain record の消失。
- child branch が元 SHA のまま残存。
- tmp 別 checkout で patch／tar の復元結果を照合。
- main、wave、別 child の不変。

成功例では Git・統合証明・退避・削除を stub しません。占有成功も実 scanner を通す node を用意し、環境起因の rc22 を成功扱いしません。

負例は以下です。表の phase は新 mode の固定診断名です。

| 入力 | 停止 phase／rc | 追加 node |
|---|---|---|
| manifest 外 path | `manifest` / 20 | `test_remove_child_rejects_unregistered_path` |
| 生きた process の cwd が child | `occupancy` / 21 | `test_remove_child_rejects_live_process_cwd` |
| scanner 判定不能 | `occupancy` / 22 | `test_remove_child_rejects_indeterminate_occupancy` |
| main 非祖先、所有 blob も不一致 | `integration` / 20 | `test_remove_child_rejects_unintegrated_author_commit` |
| 証拠 dir 非空 | `evidence` / 20 | `test_remove_child_rejects_nonempty_evidence_dir` |
| primary checkout | `preflight` / 20 | `test_child_modes_reject_primary_checkout` |
| header の wave 本体 | `preflight` / 20 | `test_child_modes_reject_wave_root` |
| argv の realpath 不一致 | `argv` / 2 | `test_child_modes_reject_noncanonical_path` |
| manifest 内 path の realpath 不一致 | `manifest` / 20 | 同 node の別 parameter |
| 別 common gitdir | `preflight` / 20 | `test_child_modes_reject_foreign_common_gitdir` |

登録時にも対象制限を検査し、手書き manifest に対して remove 側でも繰り返します。各負例は directory・admin・branch・既存証拠不変、unlock／detach／削除呼出しゼロを検証します。

追加必須 node は、空 owned_paths の空虚真拒否、参照を跨いだ blob 一致拒否、fix 再登録、detached 正例、退避後変更の rc30、各 mutation phase 失敗後の後続ゼロです。

## 7. 変異候補

すべて単一理由で事前登録できます。

| 変異 | 殺す node |
|---|---|
| exact manifest entry の確認を除去 | `test_remove_child_rejects_unregistered_path` |
| 統合証明を恒真にする | `test_remove_child_rejects_unintegrated_author_commit` |
| 空 owned_paths で B を成功にする | `test_remove_child_empty_owned_paths_requires_ancestry` |
| backup を実行せず成功扱い | `test_remove_child_archives_dirty_integrated_author_and_keeps_branch` |
| 占有検査を skip | `test_remove_child_rejects_live_process_cwd` |
| 非 main 祖先 branch も `-d` に送る | 正例 node 内の branch-delete 呼出しゼロ assertion |
| realpath 検査を文字列一致だけにする | `test_child_modes_reject_noncanonical_path` |
| admin 再検査で binding 比較を除去 | `test_remove_child_admin_binding_change_is_partial` |

branch 変異は「Git が結果的に拒否した」だけで検出したことにせず、禁止された `branch -d` 呼出し自体を spy で捕捉します。

## 8. 既存 pin の波及

- DW-O28 は `tools/check_docs.py:628` と `test_check_docs.py:189` の全文一致。
- **L9488 と L9686 に `== 989` の既存 assertion がある。** 期待値変更禁止を守るには、新本文も改行込み **989 bytes** にする必要があります。単に1000以下では不十分です。
- `test_check_docs.py:7178` 付近の変異は、`次 wave・ユーザー・`/cleanup-branches` へ引き渡さない` を置換対象にします。この文字列も本文に維持します。
- DW-O20 は996/1000 bytesなので、説明を追記するより現状維持を優先。登録説明は DW-S05-A に寄せます。
- `orchestrator/test_selection_contract.py:41` は cleanup test **file path** の契約。`test_pytest_collection_config.py:388` は `test_real_occupancy_scan_rejects_live_process_cwd` の node 名を参照。どちらも変更不要で、旧 node を改名しません。
- synthetic decisions の `D703`（`test_check_docs.py:1311`）は維持。新 D 番号は docs 本文へ書かず、fragment 内のみ placeholder を使います。
- 親 docs が未着地なら、旧 DW-O28 本文と新 literal の不一致を期待赤として名指しし、それ以外を同じ理由で処理しません。

実装後の検査対象は cleanup tests、check_docs tests、collection/selection 契約、docs checker。今回、それらの実走結果はありません。

## 9. 親 brief の攻撃

| 項目 | 成立しない条件・穴 | より単純な案／過剰部分 |
|---|---|---|
| **P1** | owned_paths を後から削れると不一致を隠せる。空集合、path別参照、mode無視、reset前履歴、committed所有外差分が穴 | 個別file閉集合・単一参照・tree entry比較に限定する。完全な採用証明 framework は作らない |
| **P2** | entry6項目だけでは親wave・repoを識別できない。登録時刻は作成時登録の証明ではない | headerにjob/wave/commonを追加。履歴台帳や署名は不要。固定順配列の置換で足りる |
| **P3** | 既存 admin 再検査をそのまま使うと B 成功後に失敗する。modeだけ追加して完了とはいえない | top-level dispatch＋子専用判定、admin構造検査だけ共有。既存a〜eの一般化は不要 |
| **P4** | manifest登録前の親死亡、mutation wrapperの内部作成、既にteardown済みのentryが残る | 正常経路は登録成功後に起動。欠落対象を無条件成功にせず報告。自動sweepで補完しない |
| **P5** | 1000以下に縮めても既存989 pinで赤になる | 新本文も989 bytesにする。上限引上げやassertion緩和は本投入では不要 |
| **P6** | 新番号回避は妥当だが、射影資料の既存裁定番号が不整合 | 新Dは遅延採番。旧裁定の正しい節は親が確認し、無関係な節をsupersedeしない |

P1 の代案 **「祖先性だけ＋親が `-s ours` merge」**には明確な利点があります。blob 比較と owned_paths を撤去判定から外し、子履歴を main から保存でき、branch の `-d` も通しやすくなります。

ただし、`-s ours` は内容採用を証明しません。報告・probe・不採用実装を含む子履歴を main の歴史に恒久的に取り込み、HEAD reflog の reset 前 commit は子 tip の merge だけでは救えません。段5の統合・provenance 契約にも波及します。**今回は P1 の限定実装を採り、この代案への運用変更は含めません。**

P4 には実体上の注意があります。`mutation_worktree.py:408`／L534 が作る Git worktree は：

```text
<scratch>/.izanagi-mutation-worktree/repo
```

外側 `.izanagi-mutation-worktree` は Git worktree ではありません。manifest の `path` は内側 `repo` にします。L947 の既存 teardown は外側 container 全体→admin の順に処理しますが、新 mode は **manifest 外の親 directory を削除しません**。外側残骸まで撤去できたとは報告しないこと。自己登録が scope 外なので、wrapper 内部作成の即時登録には親側で作成完了を観測する手順が必要で、この設計だけで全 producer の流入を機械的に閉じたとは主張できません。

また、`materials.md` の「D2148 項9」は **T-2051／B-4部分実装**であり、brief の cleanup の「項9(iii)」と一致しません。これはユーザー裁定の変更ではなく、親が fragment 起草前に直すべき出典不整合です。

## 総括

最小投入は、**4ファイル・子専用2 mode・既存 admin 撤去機構の限定共有・追加 tmp-repo tests**です。wave mode と既存テスト期待値は維持します。

親へ返す重要点は、**5ファイル退避だけでは履歴・index保存が不足すること、DW-O28は989 bytes維持が必要なこと、mutation外側containerは別物であること、D2148参照が不整合なこと**です。静的設計まで完了し、実装・テスト・dogfood撤去は未実施です。