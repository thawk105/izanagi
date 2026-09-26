---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-26
wave: worktree-dev-wave-t2865-silo-policy-stage-e
seq: 2
---

## 再発

### F30

- **再発: 2026-09-26** — [T-2865] 段階 E の wave で、承認済みの `.claude/agents/auditor.md` 改訂を統合する前に、その path の pin 閉包 (DW-O09 の `git grep -n`) を段 1 で引かなかった。`orchestrator/tests/test_mocc_template_proof.py` の consumer が MOCC template proof JSON に記録された auditor.md の whole-file sha256 と現行の一致を要求しており、統合後の焦点走で初めて 2 件の赤として現れた。land 前に検出し、束縛を記録済みの MOCC 用 auditor 項目と現行項目の一致へ置き換えた ({{D:silo-policy-stage-e}} 決定 8、proof は取り直さない)。実害なし。恒久対応は既存どおり (DW-O09: 変える file の path で pin する test・台帳を着手前に全列挙する。role 定義の `.md` も対象)。

### F936

- **再発: 2026-09-26** — [T-2865] 段階 E の wave で、焦点走 (`tools/run_tests.py --force-dispatch`) の job が待ち行列にいる間に、親が runbook を未 commit で編集した。job は走行開始時点の作業ツリーを見るため、`orchestrator/tests/test_p3_b4_wiring_probe.py` の「作業ツリーの変更は source と test だけ」検査が docs の未 commit 変更で赤になった (非帰属の赤 1 件)。runbook を commit してから次の焦点走で緑を確かめた。実害なし。恒久対応は既存どおり (memory `dirty-tree-during-pending-job`: 投入中の job がある worktree では書かない)。

### F1031

- **再発: 2026-09-26 (near miss、[T-2865] wave)** — 段 6 の fix 用 branch を切る script に、wave commit の SHA を `git rev-parse` の出力から写さず短縮形 (`41b8019a9`) に 1 文字足して渡し、`git checkout -b` が `is not a commit` で拒否した。何も作られずに止まったので実害は無い。`rev-parse` の値で作り直した。行動規律は既存どおり (直前の `git rev-parse` の出力を逐語で写す)。
