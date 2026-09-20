# 段 4 裁定 — 残骸 branch/worktree が溜まらない構造にする (2026-09-21 01:35 JST)

入力: 段 1 brief、段 2 plan (`s2-plan.md`)、段 3 lens A (`s3-lensA.md`、正しさ境界)・lens B (`s3-lensB.md`、実効性・過剰)、裁定 inbox 再走査 (第 27 回 = D2194、01:20 land)。

## 0. 段 4 直前に取り込んだ新事実

- main が `285477c00` → `2afb39768` (第 27 回 /rulings の記録 + fold) に進んだ。本 wave は commit 0 だったので ff-only で取り込んだ (01:33 JST)。
- **T-2820 / T-2821 が別件で採番された** (T-2820 = DW-O26 へ 2 test 追加、T-2821 = 候補 2 の検査付き撤去)。本 wave は未採番のまま worklog fragment の `{{T:branch-residue-cleanup}}` で新規起票し、同 fragment で完了に置く (title に番号を書かない)。
- **D2194 項 10 (T-2821) の前提は既に偽**: 候補 2 の 6 本 (`witlight-author` / `t2153-author` / `t2629-unit-probe` / `t2709-unit-probe` / `t2766-unit-impl` / `t2802-unit-probe`) と `impl-t2766-pairing-optin` は、裁定 (00:5x) の前 00:46 の cleanup で worktree 撤去 (retire-worktrees.json 13 本に含む) + branch を bundle 退避後 `-D` 済み (deleted-branches.tsv に含む)。DW-O12 に従い、worklog には裁定予定でなく実行済みの手順を書き、T-2821 を「完了 (別経路で裁定前に実施済み、branch は残さず bundle 退避後 -D、D2194 項 10 との差は記録)」に置く。
- D2194 項 10 は「今回の撤去操作では branch を残す」という個別裁定であり、恒久的な保持指示とは読まない。本 wave の `-D` 経路は、別裁定で「残す」と名指しされた対象を個別裁定なしに消さない、と D に明記する。

## 1. 所見の裁定 (real / refuted、採否)

| 所見 | 判定 | 採否・処置 |
|---|---|---|
| A-1 所有外の commit 済み差分は `committed.patch` に退避される | refuted (親 brief の説明が誤り) | 採用: 保全先を「所有内容 = main、所有外の最終差分 = 証拠 dir」と区別して D・docstring に書く |
| A-2 子 HEAD の祖先だが main に無い中間 commit (追加→削除等) の固有内容は、branch 削除で保全根を失う | **real must-fix** | 採用: 統合証明済み子 branch を `-D` する前に、`git bundle create <evidence>/history.bundle <HEAD> ^<main_tip>` で子の履歴を証拠 dir へ退避する (argv allowlist に固定形を追加、verify まで)。「述語据置き + 履歴条件維持」とは書かず、D に「内容統合は履歴保全ではない、中間版は証拠 dir の bundle が担う (object は延命しない)」と明記。反例 (追加→削除履歴) を test の正例に含める |
| A-3 削除順序で HEAD は壊れない。partial の receipt 表現 | refuted (順序) / 部分 real | 採用: 段 2 の順序 (detach → 木 → admin → 不在確認 → bundle → `-D` → receipt)。DW-O28 の「不成立・不明は木と branch を残す」は撤去開始前の拒否に限定して書く。branch 削除失敗は rc=30 phase `branch-delete`、成功 receipt を出さない |
| A-4 `-D` が wave 本体へ漏れない構造 | refuted | 採用: plan §2 のとおり共通 `_git` は `-D` を拒否、`_run_child` 内の専用関数だけが固定 argv を実行、診断 sha 照合も行う |
| A-5 manifest は権限根拠でなく対象束縛 | refuted | 採用: 新 D は「ユーザー指定 (2026-09-21) が権限根拠、manifest は対象を束縛する信頼済み入力」と書く |
| A-6 / B-9 「40 wave」「2〜8 本」「39 本同一」は概算、locked は 7 | real (記録の正確性) | 採用: 「155 本 = 指示時の数、削除実績 140、除外 24 (稼働 11 / locked 7 / 1h 1 / 新規 5)、約 40 wave 相当は概算」と書く。D2163 改訂の理由は今回確認した掃除の摩擦 (棚卸し 165 本 11 秒 + cherry 53 秒 + 手作業 26 分) に限定し、worktree 起因の land 停止 (F26) と分ける |
| A-7 監査非通知 161 件は内容着地の証拠ではない | **real must-fix** (親の追加実測の誤り) | 採用: 「161 件は監査の報告対象外 (変更 path が main / 他 branch tip に存在、または bulk log が path を列挙しない等)」と訂正。landed へ変換しない |
| A-8 / B-7 227 全件が転記対象、監査のみ 21 件も追記対象 | real | 採用: 227 件 (entry_id 接頭 `cleanup-20260921-`) + 21 件 (接頭 `audit-20260921-`、source_refs 空、verdict `indeterminate`、reason に「監査由来・削除 report なし」) = 248 entry を本 wave で転記。21 件を今回の削除へ帰属させない |
| A-9 候補なし再走は元 assessment の代替でない | real | 採用: `assessment_report_sha256` = 候補なし再走 report (`ledger-check-1.json`) の sha256 とし、`assessment_reason` に「元 report (rescue2.json) 消失、verdict は loss-commits.tsv 由来、再観測 (storage / mtime / gc) は転記時点」を明記。削除時の `loose_count_at_loss` は null |
| A-10 / B-5 cleanup 実行内で削除前に台帳へ pending 転記すると、台帳契約 (削除後) と land (tracked dirt 拒否) と F747 に衝突 | **real must-fix** | 採用: cleanup 実行内では台帳を書かない。削除前に report と転記候補 (JSON) を repo 外へ保存し、削除後の到達性で確定、§5 で別 wave (台帳転記) へ引き渡す。§0 の allowlist は「`-D` と repo 外 bundle/report 保存」だけ足す |
| A-11 余白 3 bytes | refuted | — (T-2814 の最終版は land 時に再計数) |
| B-1 同木で切り替えた旧 fix branch は manifest に無く残る | **real** (scope 外) | 今回は効果を「manifest の現行 branch」に限定して D と DW-O28 に明記。旧 fix branch は `/cleanup-branches` の `-D` 経路の回収対象。manifest への `retired_branches` 記録は次の一手候補 `{{T:child-manifest-retired-branches}}` として起票 (実装しない) |
| B-2 140 本の原因別比率は確定不能 | real | 採用: 段 9 = 正常終了経路の流入削減、cleanup `-D` = 既存・例外残骸の回収経路、と位置づけ、被覆割合は未確定と書く。証明不能な子は exact path/ref・理由を worklog へ記録 (現行 DW-O28 のまま) |
| B-3 「所有 wave が land 済み」の判定手順 | **real must-fix** | 採用: §2 に判定を 1 文で書く — 「branch 名の wave/T 識別子で `docs/worklog.md` + `docs/archive/` に完了 entry があること (grep)」。内容の全着地は要求しない (bundle と転記が保全を担う、今回の 140 本と同じ条件)。判定不能は保持 |
| B-4 bundle の置き場・予算 | real | 採用: 置き場 = `/work/1/SFC/tanab/dev-wave-jobs/cleanup-branches-<日付>/` (runbook §7.2 の探索根、job 自動削除対象外)。command には「repo 外の runbook §7.2 の dir」と書き、機体固有 path は runbook へ。`list-heads` = 候補 ref/tip 一致・verify・削除直前 tip 不変を条件に。増枠は完成 bytes から最小値 |
| B-6 schema 拡張は削除 | real | 採用: `resolution_note` = null 維持、validator / test / 文書 pin の変更なし。bundle 情報は `assessment_reason` + insight |
| B-8 author A/B の file 所有を素集合に | real | 採用: A = `tools/dev_wave_cleanup.py` + `orchestrator/tests/test_dev_wave_cleanup.py` のみ。B = command + overlay + `check_docs.py` (DW-O28 literal・2 sha・予算) + `test_check_docs.py` (fixture・literal・len・padding)。B は T-2814 land 後に 1 回起動 |
| B-10 追加 gate 不要、1h 条件は worktree 向け | refuted (追加の必要) | 採用: branch の除外は「稼働 wave / locked checkout / 棚卸し後の新規」に統合。lock 再検査 1 行は残す。Codex overlay は既存縮退で足り、`-D` を打たない全面縮退は足さない |
| B-11 新 D 1 件・新 F 1 件 (別型) | refuted (過剰) | 採用 |
| B-12 review 2 本、fix は real 所見時のみ | real | 採用 |

## 2. 割れうる前提の改訂

- (P1) → 段 9 の `-D` は remove-child が integration を証明した manifest 現行 branch だけ。`-D` 前に履歴を証拠 dir へ bundle 退避 (A-2)。証明不能 (rc=20) の子は木も branch も残し理由を worklog へ (現行どおり)。
- (P2) → `/cleanup-branches` の `-D` 連言 = 所有 wave の完了 entry が worklog/archive にある ∧ 稼働 wave・locked checkout・棚卸し後の新規を除外 ∧ 削除前に runbook §7.2 の dir へ `git bundle` + verify + list-heads 一致 ∧ rescue gate を同じ候補集合で 1 回 ∧ report・損失 commit・bundle 情報を同 dir に保存し §5 で台帳転記 (別 wave) へ引き渡す。cleanup 実行内で台帳を書かない (F747 不変)。
- (P3) → 248 entry (227 + 21) を既存 schema で転記。`status=pending`、note null、reason に由来。
- (P4) → DW-O28: 「統合証明済み子 branch は履歴を `<D>` へ bundle 退避してから tool が `-D`」。wave 本体は `-d`。
- (P5) → 維持 (台帳「覆わない範囲 2」不変)。

## 3. plan v2 (所有と順序)

1. 親 (今): DW-O28 新本文 (≤ 1,000 bytes) を `docs/dev-wave/operations.md` に書き、台帳 248 entry を生成 script (job dir) で作って `docs/unreachable-object-ledger.md` に追記、decisions / failures / worklog fragment、insight。docs commit。
2. author A (Codex、workspace-write、T-2814 と独立): `tools/dev_wave_cleanup.py` remove-child に (i) 履歴 bundle 退避 (`bundle create` / `bundle verify` を allowlist に固定形で追加)、(ii) 専用 `-D` (共通 `_git` は拒否、診断 sha 照合)、(iii) receipt field 追加と再実行時の ref 不在検査、(iv) docstring。`test_dev_wave_cleanup.py` に正例 (非祖先・所有一致・追加→削除履歴を含む子で bundle + `-D`)、負例 (未統合 rc=20 で不変 / wave 本体 `-d` のみ / 共通 runner の `-D` 拒否 / bundle verify 失敗で partial / receipt 後の再出現拒否)。
3. T-2814 land 待ち → main 取り込み (post-claim merge) → author B (Codex): command §0/§2/§3/§5 + SKILL.md overlay + `check_docs.py` (DW-O28 literal・2 sha・予算 = 完成 bytes) + `test_check_docs.py` (fixture・literal・len・padding)。親が command 本文の差分案を渡す。
4. 段 6: review 2 本 (正しさ境界 / 過剰・整合)、real なら fix (author 木を再利用)、変異 matrix、焦点走、受入。
5. 段 9: land 後の main の改訂 tool で本 wave の子木 (A / B) に remove-child を実走 → 正例。

## 4. 変異事前登録 (実装後に単一理由性を確認して確定)

| # | 変異 | 落ちるべき node (新設名は案) |
|---|---|---|
| M1 正例 | 子専用 `-D` を `-d` へ | `test_remove_child_archives_dirty_integrated_author_and_deletes_branch` |
| M2 正例 | 子 branch 削除の呼出しを省略 | 同上 (ref 不在 assertion) |
| M3 正例 | bundle 退避を省略 | 同上 (history.bundle 不在) / `test_remove_child_bundle_contains_intermediate_commit` |
| M4 負例 | integration 不一致の拒否を無効化 | `test_remove_child_rejects_unintegrated_author_commit` |
| M5 負例 | wave `_delete_branch` を `-D` へ | `test_wave_cleanup_uses_only_lowercase_d` |
| M6 負例 | 共通 `_git` の `-D` 拒否を除去 | `test_common_git_runner_rejects_force_delete` |
| M7 負例 | bundle verify 失敗でも removed を返す | `test_remove_child_bundle_verify_failure_is_partial` |
| M8 partial | branch 削除失敗でも removed / receipt | `test_remove_child_branch_delete_failure_is_partial` |
| M9 再実行 | receipt 時の ref 不在検査を除去 | `test_remove_child_receipt_rejects_recreated_branch` |
| M10 文書 | DW-O28 literal の ASCII 1 byte | `test_normative_exact_section_contract_is_handwritten_and_complete` |
| M11 文書 | cleanup command / skill の 1 byte | 既存 `test_cleanup_command_one_byte_change_is_rejected` / `..._skill_...` |
| M0 対照 | comment だけ | SURVIVED |

## 5. scope 外 real → insight / 次の一手

- B-1: 同木の旧 fix branch を manifest に記録して段 9 で消す → `{{T:child-manifest-retired-branches}}` (P3・新規)。
- 監査のみ 21 件の由来 (2026-08-23〜09-09) の個別 triage → 転記は本 wave、救出/受容の裁定は `/cleanup-branches` §5 型の裁定パッケージ候補として insight に置く。
