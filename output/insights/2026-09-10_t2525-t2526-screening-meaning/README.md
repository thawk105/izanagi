# T-2525 / T-2526 — screening の要求側意味宣言と新走の整合

D1859・D1936 項19に従い、driver が要求した物理マイクロ秒から既存の意味宣言を作り、
generic screening の公開 API と stock checkout 両分岐へ転送した。
期待 bits は `float(physical)` から作り、観測や codec から逆算しない。
無宣言の乱択と他 macro の既存扱い、共通 gate は変更していない。

T-2418 の新走は campaign identity と report schema を v2 にし、config・JSON・DAT の
status を `driver_declared_static_backoff_physical_us` に揃えた。旧 v1 fallback はない。
事前登録は末尾追補だけで、既存本文と本格系列 spec の bytes を保持した。
旧 artifact、測定事実、s1 と paper A2 の現行 literal 宣言は変更していない。

## 検証と修正

- 実装 anchor: `cad6f46d86ae4dc31edadfbdfad39c65ed73d70a`。
- 実装は隔離 Codex author。親は docs と Git 統合を担当した。相談2本・レビュー2本・焦点再レビューの
  逐語は `verbatim/`。独自case拒否とcreate-only検査の追加案は不要として却下した。
- 初回の新設callerテスト2件は build admission 未束縛で失敗。既存の束縛APIをfixtureに適用し、
  assertionを変えずに修正した。親追補の§5参照誤りも修正し、焦点再レビューで両所見closed。
- 親の変更後焦点走は119 passed / 12.34秒。意味の正負は実C++観測で確認し、性能sinkは模擬である。
- consumer22ファイルは計算ノード991332.nqsvで1573 passed / 13 skipped、92.82秒。
  これは受入全走ではない。新たな性能測定は実施していない。
- 最初のbaseline2走は各98 passed / 10 failed。`/tmp/.git` と `dev-wave-jobs/.git` の祖先判定で
  temporary output が拒否された。別ユーザーのdirectoryに触れず、祖先に.gitのない専用TMPDIRで
  108 passedとなった。F457の既知型であり、製品gateは緩めていない。
- consumer初回はbounded localのメモリ上限に達した。走行中の親phase編集も検出され、runnerが
  自動fallbackを拒否した。差分を固定して計算ノードへ再投入した結果が上記1573件である。
- anchorの全史provenanceは9436件、新規違反なし、既知56件。

## 変異の解釈

M1=最終宣言欠落、M2=physicalをrawへ取り違え、M3=公開API転送欠落、M4=stock分岐転送欠落、
M5=候補caller宣言欠落、M6=v2 slugをv1へ戻す、M7=statusを旧未確立へ戻す。
M7は正しさgateのkillとは分けてmetadataの回帰検出として扱う。
初回probeで失敗node集合を取得し、本走の期待集合を固定した。
共有repoからの2走は全変異を検出したが、外側wrapperの共有木前後一致がfalseでrc125となった。
両走のteardownは完了しており、成功扱いにしない。専用cloneの同じanchorで同じ本走を再実行し、
7/7が期待失敗node集合と完全一致した。最終wrapperはchild_rc=0、shared_snapshot_matches=true、
teardown_completed=true、終了コード0。記録は `mutation-isolated-report.json` と同wrapper receipt。
M1〜M6は意味・受理・参照の検出、M7はmetadata回帰である。
変更テストの単独走もscreening56件、backoff15件、extended48件が成功した。

## dev-wave 改善候補

`docs/skill-self-improvement.md` を読み、並行wave下では同じcommitの独立cloneを
mutation wrapperの実行元に選ぶ作法を既存DW-O19/O20へ明確化する候補をhandoffに記録した。
本waveでは改善実装・新gate・次wave起動を追加しない。
