## 1. 採用方針と静的検査の結論

**remove-child 専用の `-D` 経路を設け、wave 本体の `-d` 経路は維持する案を採る。** `/cleanup-branches` は P2 の連言を全文で明文化し、必要な bundle 保存・台帳追記だけを mutation allowlist に追加する。

実装前に処理すべき食い違いが3点ある。

1. **integration は commit の恒久到達性を保証しない。** 所有 path の tree 一致で受理した子の commit は、branch 削除後に到達不能になりうる。
2. **P3 と現行台帳 validator が衝突する。** 現行は `pending` の `resolution_note` を null に限定する。P3 を満たすため、この注記契約の最小改訂が必要。
3. **A/B の行単位分割だけでは段9の成功を保証できない。** integration はファイル全体を比較するため、両者が編集する pin ファイルの最終内容を各子木へ揃える必要がある。

以下の行番号は指定 worktree の現行版。T-2814 差分はメモリ上で適用し、base **6,201 bytes** を確認した。ファイル変更・Git 変更操作・pytest 実走は行っていない。

## 2. remove-child の実装箇所・順序・失敗契約

対象は [tools/dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2820-branch-residue/tools/dev_wave_cleanup.py:1736)。

| 箇所 | 変更 |
|---|---|
| L1–16 docstring | 子 branch の統合条件、専用 `-D`、失敗時の保持、wave 本体との差を追記 |
| L225–300 `_validate_git_argv` | exact な `branch -D -- <name>` だけ形として追加 |
| L303 `_git` | 共通 runner では `branch -D` を拒否する |
| L1306 `_delete_branch` | `-d` 固定のまま維持 |
| L1533 `_assert_child_integration` | 現行の受理条件を維持 |
| L1549 `_assert_child_history` | 「retained branch」という説明を改訂。受理述語は不用意に変えない |
| L1717 `_child_receipt` | 新 receipt の branch 削除記録と実 ref 不在を検査 |
| L1834–1836 postcondition | branch 不変検査を、削除直前の一致検査と削除後の不在検査に置換 |
| L1837 receipt | 削除対象・削除完了・証明時 main を記録 |

**削除順序は現行撤去処理の後に branch 削除を置く。**

```text
integration → evidence 保存・照合 → unlock → checkout --detach
→ 再検査 → worktree directory 撤去 → admin 再検査・削除
→ registry/path/admin 不在確認 → integration・branch tip 再照合
→ 子 branch -D → ref 不在確認 → removed.json
```

理由は次のとおり。

- attached のまま branch を先に消す案は採らない。通常 Git が拒否し、強引な ref 操作なら HEAD の参照を壊す。
- detach 後なら HEAD 自体は branch 削除で壊れない。ただし現行 `_recheck_admin` L1006 は、子 branch が proof の HEAD を指すことを再検査する。先行削除はこの既存検査を壊す。
- admin 撤去失敗時には branch を残す方が、現在の partial 契約と整合する。

削除直前は保存済み HEAD reflog SHA 集合を使い、`proof.main_tip`・`proof.head`・所有 path の統合条件を再照合する。証明不能を bundle で代替しない。

**`_delete_branch(..., force=True)` のような共通化はしない。** `_run_child` 内の専用ローカル関数として `_delete_integrated_child_branch` を置き、固定 argv を直接実行する。`_delete_branch` と同じ診断行・削除 SHA 照合を行うが、共通化するなら副作用のない診断解析だけに限定する。

allowlist の追加形は、既存 `-d` prefix の比較を集合にした上で追加する1要素：

```python
("branch", "-D", "--"),
```

既存の `len(argv) == 4`、非空名、先頭 `-` 禁止は維持する。さらに共通 `_git` はこの形を実行前に拒否し、専用関数だけが `_validate_git_argv` を通した固定 argv を `subprocess.run` する。これにより、共通 helper に `-D` を渡して実行できる構造を作らない。

docstring 追記案：

```text
remove-child は integration 証明済みの登録子木を撤去し、attached 子 branch も
専用経路で git branch -D により削除する。証明不能は rc=20 で木と branch を残す。
wave 本体の branch は git branch -d のみ。内容一致による統合は子 commit の
main 祖先性を意味しない。撤去開始後の失敗は rc=30 で報告する。
```

receipt は既存 field を残し、少なくとも次を追加する。

```json
{
  "branch_deleted": true,
  "deleted_branch_tip": "<削除前の full HEAD>",
  "integration_main_tip": "<証明時の full main SHA>"
}
```

detached 子は `branch_deleted=false`、`deleted_branch_tip=null`。再実行時は証拠 digest に加え、削除済み branch が再出現していないことを検査する。旧 receipt を、branch 削除まで済んだ新 receipt と解釈しない。

**branch 削除失敗は rc=30、phase=`branch-delete`。** 木と admin は消え、branch は残りうる。成功 receipt `removed.json` は発行せず、既存 evidence と診断を残す。診断解析失敗では実際には branch が消えている場合もあるため、「失敗なら branch 残存」と断言しない。自動再開機構や新 journal は追加しない。

## 3. integration・履歴保証とテスト変更

`_assert_child_integration` L1533 は次のいずれかで受理する。

- HEAD reflog 全 commit が main の祖先。
- 非空の `owned_paths` 全件について、子 HEAD と main の tree entry が一致。

続く `_assert_child_history` L1549 は、main の祖先でなくても **子 HEAD の祖先なら受理**する。このため、**子 branch 削除後に到達不能になる commit がない、とは言えない**。現在の正例 fixture L103 自体が非祖先の子を作る。

今回維持する保証は「採用された所有 path の内容が main にある」であり、「子の全 commit object・過去版が main から到達可能」ではない。`committed.patch` も履歴 pack ではない。この区別を新 D と docstring に明記し、P5 は維持する。祖先性だけに狭めて正例を消す変更も、reflog 検査を丸ごと外す変更も採らない。

[orchestrator/tests/test_dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2820-branch-residue/orchestrator/tests/test_dev_wave_cleanup.py:171) の変更案：

| 現行箇所／新 node 案 | 検査 |
|---|---|
| L171 を `test_remove_child_archives_dirty_integrated_author_and_deletes_branch` へ変更 | 非祖先・所有 tree 一致の正例で、実 `-D`、木/admin/ref 不在、receipt、dirty 復元を確認 |
| L266 `test_remove_child_rejects_unintegrated_author_commit` | rc=20、木・admin・branch・evidence 不変を維持 |
| L139 `_child_rejected` | mutation spy に branch 削除も加える |
| L311 `test_remove_child_reflog_retained_by_other_branch` | `author` は保持、撤去対象 `other` は削除へ期待値変更 |
| L413 `test_remove_child_already_clean_with_receipt` | 子 ref 不在と再実行時の無変更を確認 |
| L453 submodule 正例 | 成功時の author branch 保持 assertion を不在へ変更 |
| 新 `test_remove_child_branch_delete_failure_is_partial` | Git の削除拒否を注入し、rc=30、木/admin 不在、branch 残存、成功 receipt なし |
| 新 `test_remove_child_receipt_rejects_recreated_branch` | receipt 後の同名 ref 再出現を拒否 |
| 新 `test_wave_cleanup_uses_only_lowercase_d` | wave 本体の実 argv が `-d` のみ |
| 新 `test_common_git_runner_rejects_force_delete` | 完全な `("branch","-D","--","x")` を共通 runner が subprocess 前に拒否 |
| 新 `test_force_delete_call_is_scoped_to_remove_child` | 専用実行箇所と caller の構造を固定 |

L1987 付近の全面 `-D` 禁止テストは、**共通 runner での禁止**と**子専用形の許可**に分割する。L2010 付近の validator 負例から正規形だけを外し、`--` 欠落、余分な引数、force の並べ替え等は引き続き拒否する。

正例の観測は `_git` spy だけでは専用経路を見逃すため、実処理へ委譲する `subprocess.run` 観測 wrapper を使う。

## 4. DW-O28 新本文案と byte 数

[docs/dev-wave/operations.md:209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2820-branch-residue/docs/dev-wave/operations.md:209) の節全文を次に置換する。**UTF-8、LF、末尾 LF 込みで995 bytes**。1,000 bytes 上限は変更しない。

```markdown
## DW-O28 — land 後の自己撤去

`landed`/`already-landed` 後、段 9 に計算ノード job 終端後、main worktree から `python3 tools/dev_wave_cleanup.py` で撤去(path は絶対、`--main-worktree <MAIN>` は両方に付ける)。
先に manifest(`DW-S05-A`)の子木を `remove-child --manifest <M> --child-worktree <P> --evidence-dir <D>` で(回収 wave は旧分も)、次に wave 本体を `--wave-worktree <WAVE> --wave-branch <BRANCH> --tested-wave-tip-sha <TIP>` で撤去し、次 wave・ユーザー・`/cleanup-branches` へ引き渡さない。
非占有・main 祖先性(子木は所有 path の tree entry 一致でも可)・dirty 退避・manifest 束縛を検査。不成立・不明は木と branch を残す。統合証明済み子 branch だけ tool が `-D` で消す。
F26: `git worktree remove`/`git submodule deinit` 不可。wave branch は `-d` のみ、手打ち `-D` 禁止。残す子木は親が unlock し理由を次 wave の worklog へ記録。
```

親が本文を担当し、author A が次を同じ変更へ追随させる。

- `tools/check_docs.py:629` の `DEV_WAVE_DW_O28_SECTION_LITERAL`
- `orchestrator/tests/test_check_docs.py:189` の `_SYNTHETIC_DW_O28_SECTION`
- 同 L9487、L9684 の `996` → `995`

## 5. cleanup command・Codex overlay の文面と予算

[.claude/commands/cleanup-branches.md:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2820-branch-residue/.claude/commands/cleanup-branches.md:12) の allowlist 段落を、T-2814 適用後に次へ置換する。

```text
状態変更の allowlist は、(1) §2 を満たす既存 local branch の `git branch -d` または条件つき `-D`、(2) §2 を満たし
所有確認済みの既存 worktree について §3 が定める detach・branch 解放・directory と対応 metadata の
撤去、(3) §2 の repo 外 bundle・検査結果の保存と `docs/unreachable-object-ledger.md` への損失 entry 追記だけ。
(3) だけを本節の file 編集禁止・§4 の差分禁止・§6 の記録禁止の例外とし、stage/commit は許さない。
Codex はさらに real prune を許さない。§1〜§4 の読み取り検査と final での報告は
state mutation ではなく許可する。overlay は許可集合を狭めるだけで、本 command は再許可しない。
```

bundle は repo 外の mutation、台帳転記は repo file の mutation なので、`-D` だけを allowlist に足しても P2 は実行できない。上記はこの2点を明示的に解決する。一般 worklog・自己改善・commit の権限は追加しない。

現行 L42 の §2 を次に置換する。

```markdown
## 2. 安全条件 (満たさないものは削除せず報告に回す)

- 安い条件: local main / primary worktree、foreign・locked・所有不明は inventory/report のみ。
  worktree: HEAD 直近 (目安 1h) は保持、main 取込済み必須。
  branch: **ahead=0 (main 取込済み)** は `git branch -d`。
  -d 拒否は取込漏れの兆候、停止・報告
- ahead>0 の `-D` は所有 wave の記録 commit が main の祖先で、稼働 wave・locked checkout・
  HEAD 1h 以内・棚卸し後の新規を除外した対象だけ。削除前に対象全件を repo 外へ
  `git bundle create <bundle> <ref>...` で退避し `git bundle verify <bundle>` 成功と tip 一致を確認。
  §1 の全候補集合で `check_branch_rescue.py --ledger-check` 1 回の結果を保存し、
  損失 commit 全件を台帳へ pending で転記してから削除する。この連言の不成立・不明は保持。
- 未追跡 `output/` (`exploration/`・`env/`) は該当 wave の insight「証拠の所在」節で
  repo 外原本か確かめ、原本なら候補にせず残置・報告 (F1034)
- 高い条件: 削除直前に §1 の status 空を再確認。§3 の占有・判定不能は保持。
  main checkout で `[ -f .git/worktrees/<name>/locked ]` が真なら保持 (登録先不明も保持)。
  迷えばユーザー確認。対象内で作業中は先に main checkout へ退出
```

`<name>` は branch 名から推測せず、対象 checkout の admin binding から特定する。branch が checkout されている場合も、その checkout の lock を削除直前に検査する。

連動変更は2か所。

- §3 手順2、現行 L57：

  ```text
  2. `git branch -d <branch>` (§2 の -D 条件成立時だけ `git branch -D -- <branch>`)
  ```

- §5、現行 L82 の後：

  ```text
  bundle の絶対 path・sha256・verify 結果と、台帳転記件数・entry_id・未 commit の差分を報告する。
  ```

§1 の checker は移動・重複起動させない。rc は削除許可ではなく可視化結果として扱い、損失集合を確定できない結果で「全件転記済み」と扱わない。

**この具体案の計数結果：**

| 項目 | UTF-8 bytes |
|---|---:|
| T-2814 適用後 base | 6,201 |
| §0 置換差分 | +272 |
| §2 置換差分 | +646 |
| §3 変更 | +63 |
| §5 追加・空行 | +124 |
| 完成本文 | **7,306** |

6,204 には収まらない。数学的な最小増枠は **1,102 bytes**。追加実 byte と増枠を一致させる指定を厳密に採る場合は **+1,105、上限7,309** とし、既存の余白3 bytes だけを維持する。D704/D2043 型の記録には、この内訳と「安全条件を削らず入口に保持する理由」を書く。余裕込みの丸めた増枠はしない。

Codex 専用の全面 `-D` 禁止は追加しない。既存の ownership・residency・権限不足・real prune 禁止の縮退で足りる。[SKILL.md:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2820-branch-residue/.agents/skills/cleanup-branches/SKILL.md:20) に追加する案：

```text
- `-D` も dispatcher §2 の全条件下だけで実行する。§2 の bundle・検査結果保存・台帳追記以外の記録と stage/commit は許さない。
```

提供された overlay は2,646 bytes、追加166 bytes、完成 **2,812 bytes ≤ 3,100**。T-2814 land 後の実 overlay に別変更があれば再計数する。

## 6. 損失 commit 227件の転記手順と schema 整合

**候補なしの再走だけでは227件を再構成できない。**

- `audit_dangling_commits.py:287` は `fsck --unreachable --no-reflogs` を使用する。HEAD **reflog** が残るだけなら到達性の根には数えない。
- ただし現存 HEAD・ref から到達可能なら別であり、単に「reflog がある」と混同しない。
- 同 L1590 の audit は、到達不能 commit の変更 path が main／他 local branch tip に存在すると報告対象から外す。spool/archive、再生成可能物の除外もある。したがって全損失 commit の列挙器ではない。
- `check_branch_rescue.py:1854` はその audit findings だけを `unledgered-audit-finding` にする。
- 同 L2014 の候補あり分岐でしか closure・GC・retention を計算しない。候補なしでは `gc=null`、closure 0件となる。

既に job dir にある親の [ledger-check-1.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2820-branch-residue/ledger-check-1.json) を読み取った結果も一致する。親 report は rc=3、audit 87件。227件との共通部分は **66件**、未通知は **161件**、227件外が **21件**。これは既存 report の照合結果であり、本段で checker を実走した結果ではない。

転記は次の手順にする。

1. `loss-commits-oid-state-commit.tsv` を母集合に固定する。227 unique OID、内訳 landed 26／indeterminate 197／not-landed 4 を確認する。
2. 既存台帳との OID 重複を除外・照合する。audit の66件だけに縮めない。追加21件は別集合として報告する。
3. 元の `loss-commits.tsv` の branch 対応と `deleted-branches.tsv`、bundle の `list-heads` から削除 ref・full tip を回収する。今回の3列 TSV だけでは `source_refs` を復元できない。
4. 元 report の消失を明記し、job dir の生成 script で227 OID を直接観測する。既存 `_retention` L1374、GC 観測 L1288、landed assessment L1554 の意味に合わせ、候補 ref の再作成はしない。
5. `docs/unreachable-object-ledger.md` 末尾へ1 OID・1行・26 field で追記する。生成 script と raw 観測は repo に入れない。

field の埋め方：

| field 群 | 値・扱い |
|---|---|
| `schema` / `object_type` / `assessment_schema` | 既存固定値 |
| `entry_id` | `t2820-cleanup-20260921-<full-oid>` |
| `recorded_at` | 実際の転記時刻、UTC RFC3339 |
| `source_refs` | `["refs/heads/<削除したbranch>", …]` |
| `source_tips` | 上記 ref → **削除前 tip**。対象 object OID で代用しない |
| `assessment_report_sha256` | 再取得した実 assessment report の SHA-256。取得不能なら `""` は現行 schema 上許容されるが、元 report 消失を reason に明記 |
| `object_oid` | TSV の full OID |
| `assessment_verdict` | 元 TSV 判定を維持するか、再判定値と元判定を明確に分離して記録 |
| `assessment_reason` | 元 report 消失・TSV 由来・再観測の有無を具体的に記載 |
| `storage_kind` | 再観測の `loose` / `packed` / `loose-and-packed` / `alternate`。不明は `indeterminate` |
| `object_mtime` | 実測 loose mtime、なければ null。pack mtimeを代入しない |
| `loss_possible_not_before` | 算出できた下界。算出不能時は既知の削除前時刻を保守的下界として使い、その根拠を明記 |
| `lower_bound_basis` | 実測由来の basis、または `historical-cleanup-start-conservative-floor` 等の説明的 string |
| `gc_auto_threshold` / `gc_auto_sample_count` | 実測値。不明なら null |
| `gc_auto_sample_threshold` | threshold が既知なら `(gc_auto_threshold + 255) // 256`、不明なら null |
| `gc_auto_sample_fanout` | `"17"` |
| `gc_auto_heuristic_version` | `"git-2.34.1-fanout-17-sample"` |
| `loose_count_at_loss` | 削除時の観測が消失しているため null。現在値で過去を捏造しない |
| `status` | `"pending"` |
| `resolved_at` / `rescue_ref` | null |
| `resolution_note` | bundle 絶対 path、実 SHA-256、verify 結果、元判定、未解決である旨 |
| `object_retention_provided` | false |

下界を取り直せない場合、一次資料の cleanup 開始 **2026-09-21 00:20 JST** を使うなら `2026-09-20T15:20:00Z`。これは保管期限の再現ではなく、既知の削除前時刻まで下界を戻す保守的記録である。bundle があることから保持期限を延長しない。

**P3 のために必要な最小追加変更：**

- `docs/unreachable-object-ledger.md:55`：pending は `resolved_at`／`rescue_ref` を null とし、`resolution_note` は未解決の保管情報を許す、と改訂。
- `tools/check_branch_rescue.py:1737`：pending の note を null または非空 string とする。他 status の条件は維持。
- `orchestrator/tests/test_branch_rescue_ledger.py:109,220,263`：文書 pin と pending の期待値を同期。日時・救出 ref の先行設定は引き続き拒否する。

現行 schema のまま **pending＋非null note を合法に埋める方法はない**。status を `accepted-loss` に変えて回避してはならない。26 field と「覆わない範囲2」は変更しない。

## 7. decisions／failures／worklog fragment の骨子

`docs/spool/README.md:26` の命名・frontmatter、各 ledger README の文法に従い、3 fragment とする。既存 D/F 本文へ直接挿入しない。

**decisions：`{{D:cleanup-force-delete-and-child-branch}}`**

決定本文には2経路を別々に記す。

- remove-child：manifest 登録済みで既存 integration が成立した子 branch だけ専用 `-D`。証明不能は rc=20 で木・branch を保持。
- cleanup：P2 の全連言下だけ `-D`。bundle・検査結果保存・損失 entry 追記を狭く許し、stage/commit は許さない。

supersede／維持をそれぞれ明記する。

| 既存裁定 | supersede する文 | 維持する文 |
|---|---|---|
| D703 | 例外対象を wave 本体だけに限定する部分を、今回の2経路に限り拡張する | **wave 本体は tested tip の祖先性と `-d` のみ** |
| D2163 | 「子 branch は削除しない」と、子 branch 削除は固定費削減に不要とした却下理由 | manifest exact path、非占有、統合条件、証拠退避、producer 終端、判定不能保持 |
| D204 | 対象特定の都度発話を要する原則の狭い例外として2経路を追加 | その他 branch、恒久 permission rule 禁止、remote/push 境界 |
| D2042 | `ahead=0` だけを許す部分に裁定済み `-D` 分岐を追加 | 安い条件→高い条件、全 surviving status 保存、破壊操作の直列化 |

さらに pending 注記契約と byte 増枠の具体値を記録する。D1430 の accepted-loss を今回へ流用しない。

**failures：`{{F:cleanup-allowlist-structural-residue}}`**

- 事象：子 branch は patch 統合後も ahead>0 のまま残り、約40 wave 分・155本が蓄積した。2回の掃除が手作業へ落ちた。
- 根本原因：段9は木だけを撤去し、cleanup の allowlist は祖先性のある branch しか削除できず、生成する残骸に対応する撤去経路がなかった。
- 恒久対応：`dev_wave_cleanup.py remove-child` の専用削除と、cleanup §0/§2 の P2 分岐・lock 再検査へ具体的にリンクする。
- 再発検知：非祖先・所有 tree 一致の正例、未統合保持、wave `-d`、専用経路以外の拒否、文書 pin、および本 wave の段9実走で確認する。

F747 は権限を広げすぎる型、今回は必要な撤去対象を受理できない型として区別する。F747 の一般的な編集・commit 禁止を取り払う恒久対応にはしない。

**worklog：** 成果物1〜6、227件の由来と観測限界、受入・変異の実測結果、段9の実結果を記録する。まだ走っていない結果は書かない。

## 8. 変異事前登録候補

node 名は新設案。全て実装後に baseline 緑を確認してから変異する。

| 分類 | 何を変異させると | 落ちるべき test node |
|---|---|---|
| 正例 | 子専用 `-D` を `-d` に変更 | `test_remove_child_archives_dirty_integrated_author_and_deletes_branch` |
| 正例 | 子 branch 削除呼出しを省略 | 同上：ref 不在 assertion |
| 正例 | 所有 tree 一致の受理を無効化 | 同上：非祖先 fixture が rc=0 にならない |
| 負例 | integration 不一致の拒否を無効化 | `test_remove_child_rejects_unintegrated_author_commit` |
| 負例 | reflog-only 分岐の拒否を省略 | `test_remove_child_rejects_unreachable_reflog_history` |
| 負例 | wave `_delete_branch` を `-D` に変更 | `test_wave_cleanup_uses_only_lowercase_d` |
| 負例 | 共通 `_git` の `-D` 拒否を除去 | `test_common_git_runner_rejects_force_delete` |
| 負例 | `--` 欠落／余分な引数を許可 | `test_git_argv_validator_directly_rejects_forbidden_commands` と trailing-arguments node |
| 順序 | branch 削除を admin 撤去前へ移動 | 新 `test_remove_child_deletes_branch_after_admin_removal` |
| partial | 削除失敗でも removed を返す／receipt を出す | `test_remove_child_branch_delete_failure_is_partial` |
| 再実行 | receipt 時の ref 不在検査を除去 | `test_remove_child_receipt_rejects_recreated_branch` |
| 文書 | DW-O28 literal の ASCII 1 byte を変更 | `test_normative_exact_section_contract_is_handwritten_and_complete` |
| 文書 | operations 本文の1 byteだけ変更 | `test_normative_exact_section_pins_accept_real_repo` |
| 文書 | cleanup command／skill の1 byteだけ変更 | 既存 `test_cleanup_command_one_byte_change_is_rejected`／`test_cleanup_skill_one_byte_change_is_rejected` |
| 台帳 | pending の note を再び null 限定にする | 新 `test_pending_ledger_entry_accepts_preservation_note` |

P2 は文章による契約なので、SHA pin だけで実行者の遵守を証明したとは扱わない。command 単体・command＋overlay の読解レビューで、P2 の各条件欠落、lock 後付け、削除0件時の不要な記録権限を確認する。

## 9. 本 wave の段9実走手順と成立条件

現行 tool は必要な入力形式を既に持つ。

- `tools/dev_wave_cleanup.py:1471`：manifest は repo／共通 Git dir／登録 worktree の外。
- schema は `izanagi-dev-wave-child-worktrees/v1`。
- header は exact な `wave_worktree`。
- entry は `path`、`purpose`、`branch`、`owned_paths` のみ。attached branch は full ref、rename は旧新 path を列挙。
- evidence は子ごとの repo 外空 directory。既存非空 directory は拒否する。
- `docs/dev-wave/workers.md:21`：作成時登録、fix は同木再利用・再登録が既存契約。

**本段では author A/B/fix の実 manifest はまだ確認できていない。** job dir にある launcher の `artifacts/.../manifest.json` を、`child-worktrees.json` と同一視しない。

実走手順：

1. 子作成時に manifest 登録。所有 path を後から削って integration を恒真化しない。
2. fix を含む最終採用内容を確定し、各子 HEAD の所有 file 全体が最終 wave 内容と一致するか確認する。
3. land 成功、fold 終了、全 producer・計算ノード job 終端、再投入禁止を確認する。
4. **land 後の main checkout にある改訂 tool** を、cwd も main にして起動する。子ごとに異なる evidence dir を指定する。
5. rc=0、木/admin/ref 不在、`removed.json` と証拠 digest を確認する。rc=20 の子は保持し理由を報告する。
6. 子の処理後、wave 本体は従来 CLI の `-d` 経路で撤去する。

land は内容を main へ入れるが、**全子木との tree 一致を自動では保証しない**。特に共有 pin ファイル、fix が後から変更したファイル、fold で消費される fragment が問題になる。対象ファイルを持つ各子に最終採用内容を正規の author/fix 作業として反映し、終端 commit を確定しておく必要がある。main 側に後続変更が入れば再び不一致になりうる。

したがって現時点で「A/B/fix 全てが正例になる」と断定しない。実走で証明できなかった子を削除したり、bundle 経路へ送ったりして完了扱いにはしない。

## 10. T-2814・author A/B の衝突と担当分割

| 担当 | 現行アンカー |
|---|---|
| A | `tools/check_docs.py:629` DW-O28 literal |
| A | `test_check_docs.py:189` fixture、L9487・L9684 byte assertion |
| B | `tools/check_docs.py:286` command budget |
| B | 同 L780 skill SHA、L788 command SHA |
| B | `test_check_docs.py:576` skill SHA、L579 command SHA |
| B | 同 L582 skill 全文、L625 command 全文 |
| B | 同 L9944 budget test、fixture 長・超過用 padding・超過期待値 |
| 親 | `operations.md:209` 本文、台帳 entry、3 fragment |
| A または明示した追加所有担当 | `check_branch_rescue.py:1737` と `test_branch_rescue_ledger.py` の pending 注記契約 |

**A/B の編集 hunk は離れているため、通常のテキスト merge では分割可能。ただし file 単位の所有・integration では非競合になっていない。**

実施順は次とする。

1. B は T-2814 land 後の版から開始する。T-2814 が変更した全文 fixture・SHA・6,201 bytes の前提を取り込む。
2. A/B が同じ2ファイルを所有する点を明示し、共有ファイルの統合は直列化する。共有ファイルを互いに古い全文で上書きしない。
3. post-claim merge 後の完成 bytes から B が2 SHAを再算出する。A は確定した995-byte本文を literal／独立 fixture に反映する。
4. 各子の最終所有ファイルと完成版との差を確認し、必要な同期を終端前に行う。行単位の非競合を、段9の証明成立と取り違えない。
5. budget test の超過用 padding も更新する。元の固定 `23` を残すと新予算の境界を検査できない。

計数はメモリ上で UTF-8 bytes を数えたもの。独立 Python 再計数は、文面に含まれる防護パスと backtick を理由に guard が拒否したため実行できていない。ファイルは書いておらず、チェック・受入・変異の実走結果は未取得である。

## 総括

採る案は、統合証明後の子専用 `-D` と、P2 全連言による cleanup の条件付き `-D`。
wave 本体の `-d`、未統合 rc=20、P5、周期 sweep 禁止は維持する。
DW-O28 は995 bytes。cleanup 案は7,306 bytesで、実差分に対応する増枠が必要。
P3 を満たすため、pending の保存注記だけを許す既存 schema 契約の最小改訂を加える。
最大の risk は、所有内容の一致を commit 履歴の保全や全子木の段9成功と誤認することである。