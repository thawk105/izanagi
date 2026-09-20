指定資料の静的検査と、保存済み JSON／TSV の集合照合、Git object の読み取りだけを実施しました。書き込み・branch 操作・pytest 実走はしていません。以下、`J/` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-branch-residue-cleanup/` を指します。

## A-1. 所有外の最終差分が退避されない、という疑義は成立しない

**判定: refuted**

**根拠:** [tools/dev_wave_cleanup.py:1681](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/dev_wave_cleanup.py:1681) の `committed.patch` は、merge-base から子 HEAD までを **path 制限なし**の binary／full-index／no-renames diff で保存する。`tracked.patch`、`index.patch`、未追跡・ignored を含む `dirty.tar.gz` も別に保存し、fsync と再読照合を行う。

既存 fixture は所有外の `author-result.md` を commit 済みにしており、[test_dev_wave_cleanup.py:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/orchestrator/tests/test_dev_wave_cleanup.py:217) がその内容を `committed.patch` に確認している。したがって D2163 の退避は、HEAD に残る commit 済み所有外差分も覆う。rename も旧新 path の正味差分として保存される。

**影響:** 「報告 file は dirty ではないので無退避で消える」という批判は誤り。ただし保存先は main ではなく証拠 dir であり、「全内容が main にある」という brief の説明は成立しない。

**最小修正:** 保全先を「所有内容は main、所有外の最終差分は証拠 dir」と区別する。過去版まで保存したとは書かない。

## A-2. 履歴検査が削除予定 branch を保全先として数えている

**判定: real — must-fix**

**根拠:** [tools/dev_wave_cleanup.py:1549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/dev_wave_cleanup.py:1549) は、main に無い reflog commit でも子 HEAD の祖先なら受理する。`J/s2-plan.md:23–24,86–88` はこの述語を維持し、その branch を削除する。

既存 `_make_child_repo` に次の履歴を足すだけで反例になる。これは**静的に構成した反例で、実走していない**。

1. 所有 `tracked.txt` を main と一致させたまま、所有外 `transient-report.md` に固有内容を書いて commit C。
2. 同 file を削除して commit D。子 HEAD を D とする。
3. C は D の祖先なので履歴検査を通る。所有 path 一致も通る。
4. merge-base と D の双方に file が無いため、`committed.patch` に固有内容は出ない。clean なので dirty 退避にも出ない。
5. 木・admin・子 branch の撤去後、他の保持 ref が無ければ C と固有内容の保全根を失う。

所有 file の途中版、rename 前にしか存在しない固有内容でも同型である。既存負例 [test_dev_wave_cleanup.py:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/orchestrator/tests/test_dev_wave_cleanup.py:320) は reset で HEAD の祖先から外れた履歴だけを検査しており、この反例を捕捉しない。

**影響:** 「commit object の同一性を失うだけ」でなく、main に採用されず証拠にも無い内容を失いうる。P5 の台帳対象外まで維持すると、その損失の記録も残らない。段2は保証を「採用された所有 path」へ狭めているが、D2163 の履歴保全条件を維持したことにはならない。

**最小修正:** 削除予定 branch による到達性を、削除後の保全証明として数えない。上記の追加→削除履歴を必須反例にし、「述語据置き・branch 削除・履歴条件維持・P5 維持」を同時成立とする記述を撤回する。

## A-3. 削除順序による HEAD 破壊は、段2の順序なら起きない

**判定: refuted**

**根拠:** `J/s2-plan.md:29–44,65–77` は、detach → 木撤去 → admin 撤去 → 不在確認 → branch 削除 → receipt の順を明記する。現行も [tools/dev_wave_cleanup.py:1821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/dev_wave_cleanup.py:1821) で detach し、HEAD が保存済み SHA と一致することを確認する。

- 木／admin 撤去の途中失敗では branch が残る。
- branch 削除拒否では木／admin が消え、branch が残る。
- 削除後の診断解析や receipt 書込み失敗では、branch も消えている場合がある。
- detach 後の branch 削除は木の HEAD を壊さない。段2ではさらに木自体の撤去後に削除する。

**影響:** 順序そのものの欠陥はない。ただし `removed.json` は成功 receipt であり、partial の実状態を表現する receipt ではない。「rc=30 なら branch は残る」「receipt 無しなら未削除」とは判断できない。

**最小修正:** 段2の説明を維持し、診断不正・receipt 書込み失敗も partial の確認対象に含める。`DW-O28` 案の「不成立・不明は木と branch を残す」は**撤去開始前の拒否**に限定して書く。

## A-4. `-D` が wave 本体へ漏れる構造は、段2で対処されている

**判定: refuted**

**根拠:** 現行 [tools/dev_wave_cleanup.py:1306](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/dev_wave_cleanup.py:1306) の `_delete_branch` は `-d` 固定で、診断行の短縮 SHA を解決して期待 tip と照合する。

`J/s2-plan.md:46–54,102–108` は、共通 `_git` で `-D` を拒否し、`_run_child` 内の専用関数だけが固定 argv を実行すると指定する。`-D` でも同じ診断 SHA 照合を要求している。allowlist 一行追加だけの案ではない。

**影響:** 計画どおりなら共通 helper 経由の漏出は閉じる。親 brief の「postcondition 一か所＋allowlist 一行」だけを実装すると、この限定が欠落する。

**最小修正:** brief の最小差分説明を段2に合わせる。実装レビューでは専用呼出し箇所と共通 runner の拒否を確認する。

## A-5. manifest はユーザー発話の代用品ではないが、新 D の対象束縛には使える

**判定: refuted**

**根拠:** `J/rulings-verbatim.md:3–11,55–74` は、D204 の通常適用と、ユーザー裁定に基づく狭い恒久例外を区別する。D2163 自身も同 `:84–96` で未署名 manifest と作成世代の限界を明記している。[tools/dev_wave_cleanup.py:1471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/dev_wave_cleanup.py:1471) も同じ信頼境界である。

今回の根拠は manifest 単独ではなく、`J/user-brief-20260921.md:28–31,39–41` の「子 branch も消す」を含む成果物指定である。段2 `:274–279` も D204 の通常適用ではなく部分 supersede として扱っている。

**影響:** 「未署名だから今回の変更は無権限」という批判は成立しない。一方、manifest を「対象を指定したユーザー発話」や署名付き所有証明と説明すると、将来の削除対象を誤って広げる。

**最小修正:** 新 D はユーザー指定を権限根拠とし、manifest はその対象を束縛する信頼済み入力と明記する。A-2 の内容喪失まで、この一般的な再発防止指示で受容済みとは扱わない。

## A-6. 「155本／40 wave が D2163 の却下理由を覆す」は過大な一般化

**判定: real — must-fix（記録の正確性）**

**根拠:** `J/brief.md:7,18,39` は「40 wave 分」と断定するが、起点資料 `J/user-brief-20260921.md:13–14` は「1 wave あたり2〜8本」「155本 ≈ 約40 wave 分」という概算である。wave ごとの集計ではない。

D2163 が子 branch の `-d` を「固定費削減に不要」と却下した引用自体は正しい（`J/rulings-verbatim.md:118`）。しかし同裁定の実測は worktree／handoff の走査費用（`:101–108`）であり、F26 による land 停止も worktree の話（`:42–43`）。branch の本数だけでは、その理由を覆したとは証明できない。branch 棚卸し費用の既存証拠は D2042 `:134–137`、反復判定の費用は D1430 `:185–190` に別途ある。

また `J/excluded-branches.tsv:1–24` は、稼働11・locked7・直近1・新規5で計24件。起点 brief の locked6 は一件不足する。155は削除指示時の数で、140件の削除実績と同一集合だとは確認できない。

**影響:** 概算が独立した実測へ、branch 掃除の摩擦が land 阻害へ変換され、恒久裁定と failures に誤った因果が残る。

**最小修正:** 「約40 wave 相当の概算」「155本は指示時の数」「削除実績140本」を分ける。D2163 の改訂理由は今回確認した掃除の摩擦に限定し、worktree 起因の land 停止と分離する。

## A-7. 監査から消えた161件は、main への内容着地が証明された161件ではない

**判定: real — must-fix**

**根拠:** [audit_dangling_commits.py:287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/audit_dangling_commits.py:287) は `fsck --unreachable --no-reflogs --connectivity-only` を使う。worktree HEAD **reflog** が非通知の理由ではない。

一方、[同:1631](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/audit_dangling_commits.py:1631) は変更 path が main **または他 local branch tip** に存在すれば通知から外す。blob は比較しない。`docs/spool/`、`docs/archive/` 等の除外もある。同 `:64–66` は「既存ファイルへの変更・削除・同名別内容・gitlink 更新」が検出対象外と明記する。

保存資料の集合照合では、227件すべてが保存済み fsck 1,721件に入り、監査87件との共通部分66件、非通知161件、監査のみ21件を確認した。さらに161件を現時点の object／tree で読み取り分類すると：

| 非通知を説明する条件 | 件数 |
|---|---:|
| 監査の bulk log が変更 path を列挙しない | 38 |
| 対象 path がすべて現在の main に存在 | 119 |
| 除外 path のみ | 3 |
| main に無い path が他 branch tip に存在 | 1 |

最後の一件は `8f6aee197…`。main に無い13 path が、残存 tip `0709a4018…` に存在した。これは現在の読取結果であり、01:21の snapshot を再実行したものではない。

**影響:** 追加実測の「161件は内容が main に着地している証拠あり」は、この監査結果から導けない。同名別内容の喪失を landed と誤認し、台帳の判定や削除理由を汚染する。

**最小修正:** 「161件は監査の報告対象外」と訂正する。監査非通知を landed assessment へ変換しない。1,634件の非通知についても同様。

## A-8. 転記は227件すべてが対象で、監査のみ21件も別の追記義務を持つ

**判定: real — must-fix（21件の扱い）**

**根拠:** [docs/unreachable-object-ledger.md:45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/docs/unreachable-object-ledger.md:45) は、次の二つを独立した追記条件にする。

- 事前の損失閉包に入り、削除後に恒久 ref から到達不能になった commit。
- `unledgered-audit-finding` として通知された object。

227件は保存された損失集合であり、全件が保存済み fsck 到達不能集合に含まれる。landed／非通知を理由に66件へ縮める根拠はない。内訳26／197／4も再計数で一致した。

また `J/ledger-check-1.json:1` の未記帳87件のうち、21件は227件外で、`J/audit-only-21.txt:1` 以下の集合と一致する。古い commit であることは追記条件を解除しない。段2 `:219` の「別集合として報告する」だけでは、この義務の扱いが未確定である。

**影響:** 227件だけを処理して「台帳照合完了」とすると、既知の未記帳21件が残る。逆に21件を今回の削除に帰属させると `source_refs/source_tips` を偽る。

**最小修正:** 227件は全件転記する。21件は監査由来として別扱いにし、追記対応の担当・完了範囲を明示する。今回の削除実績へ混ぜない。

## A-9. 候補なし再走は、消失した削除前 assessment の代替にならない

**判定: real — must-fix（親 brief）**

**根拠:** `J/brief.md:16,40` は候補なし再走で report SHA・storage・mtime・GC・期限を取り直すとする。しかし [check_branch_rescue.py:2014](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-branch-residue-cleanup/tools/check_branch_rescue.py:2014) は候補ありの場合だけ閉包・GC・個別 retention／assessment を計算する。実際の `J/ledger-check-1.json:1` は `gc=null`、閉包0件である。

個別 landed assessment の hash は同 `:1636` の checker stdout の hash。監査出力の hash は同 `:1850` の別物である。元 `rescue2.json`、候補なし rescue report、監査出力、再取得した個別 assessment を混同できない。

段2 `:206–248` はこの問題を概ね修正している。なお元 report 消失の原因「job dir f9f84e36 の削除」は親の申告であり、指定資料から削除イベント自体は独立検証できない。

**影響:** 新しい report の hash を古い verdict の根拠として付けると、hash を辿っても記載判定を再現できない。現在の mtime／GC 観測を削除時の観測として書くこともできない。

**最小修正:** brief を段2へ同期する。再 assessment を使うなら、その hash と verdict を組にする。`assessment_reason` には元 report 不在、元 TSV の判定、再観測時点・根拠、復元できない項目を明記する。元 SHA の代用品とは書かない。

## A-10. cleanup 案は「削除前に pending 転記」と現行追記条件が衝突する

**判定: real — must-fix**

**根拠:** `J/s2-plan.md:153–157` は「損失 commit 全件を台帳へ pending で転記してから削除」とする。現行台帳 `:46–48` は**削除・撤去後に恒久 ref から到達不能になった場合**の追記である。

削除を拒否された branch や、途中停止で未処理の branch の commit は、予測閉包に入っていても実際には到達可能なままになる。段2の schema 改訂 `:253–259` は pending の注記だけで、この時点の衝突を解消していない。

**影響:** 削除失敗でも「到達不能 object」の pending entry が残り、実際には起きていない喪失と期限通知を記録する。候補集合全体の予測と、部分成功後の実損失を混同する。

**最小修正:** 削除前 report の保存と、実際に追記条件を満たした object の確定を分ける。前倒し転記を採るなら、その意味と部分失敗時の扱いも契約改訂に含める。pending note の緩和だけで整合済みとしない。

## A-11. T-2814 後の余白3 bytes は正しい

**判定: refuted**

**根拠:** [T-2814差分](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-branch-residue-cleanup/t2814-cleanup-command-diff.patch:1) を指定 worktree の本文へメモリ上で適用して再計数した。現物6,181 bytes、適用後6,201 bytes、D2043 の上限6,204 bytesとの差は3 bytesだった。ファイルは書いていない。

**影響:** この計数に誤りはない。ただし提供差分の適用結果であり、将来 land する最終版が同じことまでは証明しない。

**最小修正:** 「提供された T-2814 差分では余白3 bytes」と限定する。nit として、段2内に残る旧 worktree 名・旧 job dir 名のリンクも現行パスへ直す。

## 総括

must-fix: 削除予定 branch に依存する履歴保全、監査非通知＝内容着地という誤認、削除前 pending 転記の契約衝突。  
must-fix: 227件の根拠を保った全件転記、監査のみ21件の扱い、assessment hash と判定の対応、概算・因果の記録訂正。  
refuted: 所有外の最終差分の無退避、段2の削除順序による HEAD 破壊、共通 runner への `-D` 漏出、余白3 bytes の誤計数。  
nit: 旧パスリンクと行番号の同期。テスト未実走。