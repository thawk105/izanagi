## 対応表

| 所見 | 状態 | 対応 |
|---|---|---|
| 1. 変異テストの単一理由性 | partial | 入力を分離・再照準済み。実走は rc=16 で未実施 |
| 2. 恒真な検査 | partial | preimage 検査を v1 に限定し、root 自己不一致の恒真 conjunct を削除。実走未実施 |
| 3. `campaign_output_root` の射程 | partial | caller 指定 base 配下の整合性だけを保証すると明記。実走未実施 |

`closed` や `regressed` と判定した所見はありません。

## 修正内容

所見 1:

- envelope テストを、lifecycle digest だけが異なる入力と、disk bytes だけが in-memory plan と異なる入力へ分割しました。[test_reflux_formal_consumer.py:767](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-c/orchestrator/tests/test_reflux_formal_consumer.py:767)
- 別 trial 入力は、plan、envelope digest、provenance、lock、WAL の canonical leaf を整合させ、論理 campaign identity だけが不一致になる形へ変更しました。[test_reflux_formal_consumer.py:843](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-c/orchestrator/tests/test_reflux_formal_consumer.py:843)
- 過去 attempt 入力も同様に canonical leaf 内へ置き、`attempt_capability_sha256` だけが現 attempt と異なる形へ変更しました。[test_reflux_formal_consumer.py:875](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-c/orchestrator/tests/test_reflux_formal_consumer.py:875)
- 両入力について projection と source WAL が plan の canonical leaf 内にあることを setup assertion で確認します。[test_reflux_formal_consumer.py:641](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-c/orchestrator/tests/test_reflux_formal_consumer.py:641)
- root 所属テストは、実際の検査範囲に合わせて ordered WAL refs のテストへ改名しました。[test_reflux_formal_consumer.py:907](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-c/orchestrator/tests/test_reflux_formal_consumer.py:907)

所見 2:

- decoded preimage 比較は、v2 では decoder が既に保証するため、raw v1 lock にだけ発火する位置へ移しました。[reflux_formal_consumer.py:423](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-c/orchestrator/campaign/reflux_formal_consumer.py:423)
- WAL path の `path != computed_root` を除き、実効的な `is_relative_to(computed_root)` だけを残しました。[reflux_formal_consumer.py:955](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-c/orchestrator/campaign/reflux_formal_consumer.py:955)

所見 3:

- module docstring と公開関数 docstring に、保証が caller 指定 base の canonical leaf 配下の artifact consistency に限られることを記載しました。[reflux_formal_consumer.py:20](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-c/orchestrator/campaign/reflux_formal_consumer.py:20) [reflux_formal_consumer.py:1251](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-c/orchestrator/campaign/reflux_formal_consumer.py:1251)
- deployment 上の唯一の root、物理実行、trusted harness の認証は保証しないと明記しています。
- D1674 は evidence root を trusted harness だけが書けるという運用前提として残しています。

## 所見 2 の拒否集合維持根拠

- decoded preimage: v2 decoder は exact key、inner canonical JSON、outer canonical JSON を既に検査します。[campaign_lock.py:513](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-c/orchestrator/campaign/campaign_lock.py:513) 一方、v1 は元 text を保持するため、再構成した canonical preimage との比較を v1 分岐へ移しました。非 canonical v1 の拒否テストも追加しています。[test_reflux_formal_consumer.py:923](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-c/orchestrator/tests/test_reflux_formal_consumer.py:923) したがって従来拒否した decoded input は失われません。
- `path != computed_root`: ordered WAL refs は physical binding より先に解決され、regular file 以外を拒否します。[reflux_formal_consumer.py:1302](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-c/orchestrator/campaign/reflux_formal_consumer.py:1302) [reflux_result_evidence.py:487](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-c/orchestrator/campaign/reflux_result_evidence.py:487) また、同じ `computed_root` 配下の `campaign.lock` が既に読めているため root 自体は directory です。[reflux_formal_consumer.py:907](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-c/orchestrator/campaign/reflux_formal_consumer.py:907) 解決済み regular file がその directory 自体と等しくなる入力は先に拒否されるため、削除による受理拡張はありません。

## 所有外 caller への波及

静的検索で `evaluate_formal_origin` の production caller は [p3_autonomous_workload_trial.py:1862](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-c/orchestrator/campaign/p3_autonomous_workload_trial.py:1862) の 1 件だけでした。

- 公開 signature と戻り値は変更していません。
- caller が渡す `campaign_output_root` は認証済み deployment root として扱われません。
- base commit 時点では同 caller の必須 3 引数不足が残っていますが、これは並行する別所有単位の修正対象です。
- private helper の所有外 caller はありません。

## 検査

`python3 tools/run_tests.py orchestrator/tests/test_reflux_formal_consumer.py -q` を実行しましたが、Pegasus の `qstat -Q` preflight が失敗して rc=16、`child_started=false` でした。実走した nodeid はありません。

`git diff --check` は成功しました。変更は指定された 2 ファイルだけで、docs 編集や commit は行っていません。述語無効化による変異実走も同じ理由で未実施です。

## 総括

- envelope の digest 検査と in-memory bytes 検査を別テストへ分割。
- 別 trial と過去 attempt の入力を plan の canonical leaf 内へ再照準。
- テスト名を実際の検査範囲へ修正。
- decoded preimage 検査を実際に発火する v1 入力へ限定。
- 恒真な root 自己不一致 conjunct を削除し、拒否集合維持根拠を確認。
- caller 指定 base と D1674 の保証限界を明記。
- repository test runner は rc=16、実走 nodeid なし。
- 残る赤は未判定で、変異 kill の実測も親での実走待ち。