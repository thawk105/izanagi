---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-27
wave: dev-wave-acceptance-user-site-gate
seq: 3
---

## 新規

### {{F:bound-runner-isolation-hides-user-site-dependency}}. 受入子を隔離した結果 user site の依存が消え、全 wave の受入が取れなくなった [恒真ゲート] [検査漏れ]

- 事象: 2026-08-27 の午後、**受入全走が全 wave で取れなくなった。**
  少なくとも 3 つの dev-wave (t2010 / t1981 / t2001) が land 前で停止し、
  合計 10 回以上の受入投入がすべて `rc=70 / source_rc=16` で失敗した。
  最後の緑受入は 14:27 (`tested_main = 98f61815c`)。
- 根本原因: `b93861570` が `runner_binding` 経路を導入し、同 commit で計算ノードの
  内側 runner に **`-I` (isolated mode) を新規追加**した。`-I` は `-s` を含むので
  user site が `sys.path` から落ちる。**`pytest-xdist` は user site にしか無い**ため
  import できず、`tools/run_tests.py` が `_PEGASUS_DISPATCH_RC` (=16) を返す。
  発生点は同 file の内部 shard 検査による**無言の return** であり、
  `K=1` の通常経路では逐語の診断が出る。**現れ方が K に依存するため、
  wave ごとに症状が違って見えた** (逐語を見た wave と 0 byte stdout の wave が混在した)。
- **機構は自分の受入で一度も実行されないまま着地した。** `b93861570` の commit message 自身が
  「manifest が 1 key も無ければ現行の pathname 起動を維持する
  (段階 P 自身の受入がこの経路を通る)」と書いており、
  `git merge-base --is-ancestor b93861570 98f61815c` は偽である。
- 恒久対応: {{D:bound-runner-user-site-gate}} — 外側で検証した distribution root を
  positional argv で隔離子へ渡し、bootstrap は末尾 `append` するだけにする。
  `-I` は維持する。**正例は実子を起動して marker JSON から `xdist.__file__` の
  注入 root 配下性 / version / isolated・ignore_environment・no_user_site の 3 flag /
  実行 digest を検査する** (`orchestrator/tests/test_pegasus_dispatch_compute.py` の
  `test_bound_child_imports_xdist_from_validated_appended_root`)。
  負例は注入除去・`.pth` と `usercustomize.py` の不実行・敵対的 `PYTHONUSERBASE` /
  `PYTHONPATH`・外側検証の fail-closed の 4 面。
- 再発検知: 受入が `rc=70 / source_rc=16` で落ちたら、まず
  `request.json` に `runner_binding` があるかを見る。あれば束縛経路である。
  計算ノードの子の rc=16 は `error: null` を伴い、例外ではなく**正常終了として 16 を返している**。
  束縛経路だけが落ち非束縛の dispatch が通るなら本型を疑う。

### {{F:name-grep-misses-alias-bound-implementation}}. 別名で grep して実装を「未被覆」と誤判定した [検査漏れ]

- 事象: 束縛起動の機構について「テスト参照 0 件、正例が存在しない」と 2 セッションが判断し、
  親もそれを裁定文へ取り込んだ。**実際には正例が 3 本あった**
  (`orchestrator/tests/test_pegasus_dispatch_compute.py` の
  `test_bound_child_executes_main_blob_not_worktree` /
  `test_bound_child_reports_digest_of_executed_buffer` /
  `test_job_run_emits_exact_runner_binding_report_for_bound_request`)。
- 根本原因: `_bound_runner` / `_BOUND_RUNNER` で grep したが、
  **実体の関数名は `_run_bound_tests_child`** である。別名束縛を落とした。
  定数 `_BOUND_RUNNER_BOOTSTRAP` の参照が 0 件だったのは事実で、
  そこから「機構が未被覆」へ飛躍した。
- 影響: 誤りのまま進むと**既存の正例を重複させる新テストを書く**ことになり、
  実際に欠けていた面 (`-I` 下の dependency path) は空いたままになる。
  本 wave では実装前に訂正され、新テストは dependency 面だけを足す形になった。
- 恒久対応: memory `authoritative-closure-before-counting` /
  `pin-closure-search` の再確認。**「N 件」「0 件」と書く前に、
  識別子だけでなく呼出し関係で閉包を引く。** 定数名の不在を機構の不在の根拠にしない。
- 再発検知: 「テスト参照 0 件」「未被覆」を主張する所見は、
  **実体の関数名・呼出し関係で引き直したか**を確認してから採用する。
