---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-22
wave: worktree-dev-wave-t1479-known-violation-merge-authorship
seq: 1
---

## 新規

### {{F:parent-direct-edit-after-merge-resolved}}. merge競合解消の例外を次のcommitへ繰り越し、親(Claude)が実装面を直接編集した [権限逸脱]

- 事象: 段6で受入前local main取り込み中に発生したmerge競合 (`8440a148`) は、Codexが
  mid-merge (conflict marker残存) の作業木へdispatchできないため親が直接解消した
  (正当な例外)。ところが続く登録commit (`fdd2a427`: `8440a148`の登録+stale化した
  既存2件の削除) でも、親が同じ流れで`KNOWN_PROVENANCE_VIOLATIONS`を直接編集して
  commitしてしまった。この時点でtreeは既にclean (non-mid-merge) でCodexへ通常
  dispatch可能だったため、2件目には正当な理由が無かった。
- 根本原因: merge競合解消の例外を「直前の自分の行動 (直接編集した)」にひもづけて
  継続適用してしまい、例外の本来の適用条件 (tree状態がmid-mergeかどうか) を
  次のcommitの前に再確認しなかった。
- 検知経緯: 受入acceptance (4回目試行) が`fdd2a427`自体を`MISSING_CODEX_AUTHOR`
  として検出し発覚した。`git reset --soft HEAD~1` (差分は保持、参照patchも別途保存)
  で取り消し、Codex `--stage author`へ正しく再委任して同一内容であることを確認した
  上でcommitし直した (fix2)。
- 恒久対応: [[dev-wave-merge-exception-does-not-carry-forward]] (persistent memory) —
  段6でmerge競合を親が直接解消したら例外はその1 commitで終わる、次に実装面へ触る
  commitを作る前に必ず`git status`でclean/non-mid-mergeを確認しCodexへ戻す、という
  手順を今後のdev-wave manager実行時に読み込む形で記録した。
- 再発検知: 次にdev-wave 段6でmerge競合の親直接解消が発生した場合、その直後の
  commitのAI-Agent trailerに`role=author`(codex)が無ければ、受入acceptanceの
  provenance checkerが同じ`MISSING_CODEX_AUTHOR`型で機械的に検出する
  (fail-closed、本waveの根本修正後も直接編集そのものは検出対象のまま)。
