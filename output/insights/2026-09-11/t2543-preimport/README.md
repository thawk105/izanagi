# T-2543 — 条件関門を probe import 前に検査する

authority: none
default_effect: no-state-change

正本は `docs/decisions.md` D1936項30と
`docs/archive/worklog-phase3-0910-1410.md` の T-2543。
shell の既存 BOUND_PATHS に条件関門を1件追加した。既存 dirty 検査と内容照合の対象が
Python側の5pathと揃い、条件関門 import 前に拒否できる。先行する Python 版確認は残る。
汎用 import 閉包、新しい防護機構、receipt schemaの変更はない。

## 検査

- 修正前の t316 module: 129 passed、job 991680.nqsv、pytest 4.66s。
- 修正後の同 module: 144 passed、job 991695.nqsv、pytest 4.58s。
- 関連5file（t316、hooks、収集設定、growth hold契約、受入順序）:
  856 passed、1 skipped、pytest 102.48s。変異台帳のbaselineが一次記録。
- M1: 条件関門entryを1行だけ除去し KILLED、期待node完全一致。
  `test_execution_binding_shell_dirty_gate[condition-unstaged]` と
  `test_execution_binding_shell_dirty_gate[condition-staged]` が、
  期待する `(3, "")` に対する `(0, "T2543_AFTER_DIRTY\n")` の挙動差で失敗した。
- 固定anchorは `4c335f132a753009a16085717525661dabc44857`。
  注入差分はPBSの1行削除だけで、終了後のdiff空とclean treeを確認した。
- `check_codex_agents.py` / `check_docs.py` はrc=0。
  anchorの全史provenanceは9631件、新規違反なし、既知違反56件を保持。

局所Bash断片と実Gitの検査、および実PBSの順序契約である。
PBS全体の実機probe・性能測定を実走したという主張はしない。

## 独立確認と実行上の事実

plan1・consult2・author1・review2の6 workerを隔離codex execで実行した。
すべてaccepted、modelはgpt-6-astra、effortはmedium。実装面はauthorのみが編集し、
親は記録・統合を担当した。2レビューとも新規must-fix/nitは0件。
親は多層検査によるmaskの指摘を採用し、fixtureや構造assertでの偽killを除いた。
逐語は `verbatim/`、M1事前登録と全結果は同directoryのJSON。

author環境ではqstat事前確認が失敗してchildを起動できず、未実走として受領した。
親の焦点走はbounded localのcap OOM後、既存runnerの自動dispatchで成功した。
その途中に親が追加したforce-dispatchは既存orphan holdに拒否され、追加childは起動しなかった。
holdを変更せず元の走行を待った。子のPBS構文確認もhook拒否で未実施として扱う。

起動時のregistered worktree、main/外部handoff、t316関連worker processには同対象所有を確認せず、
外部rulings inboxにも本件更新はなかった。過去archiveと既存receiptを再ラベルしない。

## ログの可逆正規化

Gitの末尾空白検査に従い、ログの空中継行 `| ` を `|\x20` と表記した。
各ログ2行のみ。復元はbytes置換 `b"|\\x20\n" → b"| \n"`。
原文はbaseline.logが2366 bytes、SHA-256
`398cc8bfe33e92cbe121710216a6741d3397f605ad790c034225b602bceaada1`、
focused.logが2883 bytes、SHA-256
`9dd506b4076bee7a06cd0fcdc59c04ed43efe423e3404db875e4a69e6a03b58f`。
