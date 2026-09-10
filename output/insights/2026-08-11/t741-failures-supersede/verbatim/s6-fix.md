## 所見対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| F0 | partial | 挿入位置・payload を是正し3境界の probe は通過。pytest は基盤 rc=16 で未実走 |
| F1 | partial | 追加 entry 順から expected を生成し、多重集合検査と逆順正例を追加。pytest 未実走 |
| F2 | partial | HTML comment 除去投影と fence 正例を追加。pytest 未実走 |
| F3 | partial | LF-only 分割、禁止6文字の明示拒否、byte 保存テストを追加。pytest 未実走 |
| F4 | partial | 実 canonical 3境界の前提 assert を追加。pytest 未実走 |

`regressed` はありません。実装・手動 probe は完了していますが、worker 契約に従い pytest 未実走のため `closed` とはしていません。

## 実装した変更

- [tools/spool_fold.py:366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:366)
  - HTML comment を空文字へ連結する投影を追加し、R4 検査だけで使用。
- [tools/spool_fold.py:788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:788)
  - supersede validate の行分割を `split("\n")` へ統一。
  - U+2028、U+2029、U+0085、CR、VT、FF を `failure-supersede-shape` で拒否。
- [tools/spool_fold.py:873](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:873)
  - CR が file-level 検査で先に停止する場合にも shape issue を明示。
- [tools/spool_fold.py:1642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1642)
  - fold 側も LF-only 分割と禁止文字検査へ統一。
- [tools/spool_fold.py:1710](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1710)
  - supersede の挿入位置を対象 entry 最終非空行の LF 直後へ変更。
  - payload を挿入行群と末尾 LF のみに変更。
  - `_insert_failure_recurrences` は変更していません。
- [tools/spool_fold.py:1770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/tools/spool_fold.py:1770)
  - topology expected を実際の追加 entry 順に変更し、allocation 多重集合との一致も検査。
  - 採番用 `symbols` の sort は維持。
- [orchestrator/tests/test_spool_fold.py:1093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1093)
  - F0 の byte-exact 期待値を是正。
- [orchestrator/tests/test_spool_fold.py:1261](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1261)
  - 禁止6文字の拒否と、受理本文の byte 保存を独立固定。
- [orchestrator/tests/test_spool_fold.py:1364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1364)
  - comment のラベル内部・前後・item 前を拒否し、fence 内 decoy を受理。
- [orchestrator/tests/test_spool_fold.py:1467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1467)
  - 同一 wave/seq、異なる authored、offset/path 逆順の正例を追加。
- [orchestrator/tests/test_spool_fold.py:1533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t741-failures-supersede/orchestrator/tests/test_spool_fold.py:1533)
  - 実 canonical の空行なし・空行1行・EOF 前提を先に assert。

`test_check_docs.py` と `test_dev_wave_land.py` の段5差分には、今回追加変更をしていません。

## 走らせた検査

- 焦点10 nodeid: rc=16、pytest 起動前停止
  - F0〜F4の新規・境界・topology nodeid
  - 理由: `qstat -Q preflight rc=1`
- 関連3ファイル全体:
  - `test_spool_fold.py`
  - `test_check_docs.py`
  - `test_dev_wave_land.py`
  - rc=16、pytest未実走
- 最終 topology 2 nodeid再試行: rc=16、pytest未実走
- pytestではない手動 probe:
  - supersede/topology 系26関数: rc=0
  - check_docs consumer、meta-test、land consumer 3関数: rc=0
  - pytest緑の証拠には数えていません。
- `python3 -m py_compile`、変更4ファイル: rc=0
- `git diff --check`: rc=0
- `python3 tools/check_docs.py`: **rc=0**（パイプ不使用）
- `python3 tools/check_codex_agents.py`: rc=0

## 受理集合への影響

- F1 は誤った topology 順序で拒否されていた既存正当入力を回復します。採番順・割当 ID は変えません。
- F2 は Markdown 上で可視の `- **supersede:` 誤用だけを追加拒否し、fence 内 decoy と通常 prose は維持します。
- F3 は指定された行区切り文字を shape 違反として追加拒否します。通常の Unicode 本文は byte-exact に保存します。
- F0 は新規 supersede 行の空行配置だけを正します。canonical の既存 bytes、再発 helper、既存 ledger の受理集合は変更しません。
- fail-open 化や段4裁定 E 節を超える変更はありません。

## 要裁定 / 未実装

- 新たな要裁定はありません。
- 実装上の未実装はありません。
- pytest・変異・受入全走は dispatch 基盤障害のため未実走です。
- docs は編集していません。
- commit は作成していません。
- scope 外3件には触れていません。

## 総括

F0〜F4の修正と回帰テストは実装済みです。静的検査、必須 checker、手動 probe は通過しましたが、pytest は基盤 rc=16 で起動できていないため、最終状態は「実装済み・pytest未実走」です。