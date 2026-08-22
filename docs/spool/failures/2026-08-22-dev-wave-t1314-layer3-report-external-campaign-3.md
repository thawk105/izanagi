---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-22
wave: dev-wave-t1314-layer3-report-external-campaign
seq: 3
---

## 新規

### {{F:consult-lane-job-id-collision}}. 段3並列lane起動で明示job-idがlaneと合成されず衝突した [手順漏れ]

- 事象: 段3の敵対相談で sol/luna 両レンズに同一の明示 `--job-id consult1` を渡して並列起動した。
  `tools/dev_wave_codex.py` の artifact bucket が `--job-id` だけで決まり `--lane` と合成
  されなかったため、両方が同じ `consult1/` バケットを取り合った。先発 (luna) は
  「NG: attempt artifact が既に存在する」で安全に rc=2 拒否されたが、後発 (sol) は約10分間
  実際に走行し `attempt-0001.output.md` へ実出力を書いたにもかかわらず、receipt.json の
  finalize 時点で既に luna の失敗 receipt がバケットを占有しており
  「NG: 既存の完全な receipt は上書きできない」で正式な receipt を作れなかった。
  `dev_wave_wait.py producer` はどちらも rc=70 (pid死亡+.done欠落) として報告し、
  一見「両方失敗した」ように見えた。
- 根本原因: DW-O01/DW-C01 は artifact bucket が (wave, stage, lane) の組で決まると記す一方、
  明示 `--job-id` を渡した場合の合成規則 (lane を含めるべきか) を明記していない。
  `tools/dev_wave_codex.py` の実装は `--job-id` 指定時にそれを bucket 名としてそのまま使う
  (lane を合成しない) ため、並列 lane 起動で明示 job-id を lane ごとに書き分けないと衝突する。
- 恒久対応: 未実施。段8で `docs/dev-wave/operations.md` の `DW-O01` (`L1.5` 予算超過) と
  `docs/dev-wave/core.md` の `DW-C01` (逐語 exact 契約節、挿入不可) の両方への追記を試みたが
  いずれも `tools/check_docs.py` の構造検査 (予算・exact 契約) に阻まれ本 wave では見送った。
  ユーザー裁定へ、値上げ (予算緩和) を伴わない解決策 (他 leaf 節への配置転換、既存文の圧縮
  余地の拡大等) の検討を委ねる。
- 再発検知: 未整備。`tools/dev_wave_codex.py` 側でのバケット衝突検出時の警告強化、または
  `--lane` 指定時に `--job-id` へ自動で lane を suffix する変更が候補になりうるが、
  いずれも本 wave の scope 外。

### {{F:mutation-attempt-out-pairing}}. `mutation_worktree.py`の`--wrapper-attempt`は`--attempt-out`と同時指定必須という制約が`--help`から読み取れない [手順漏れ]

- 事象: 段6の変異matrix実走で `--wrapper-attempt 1` だけを指定し `--attempt-out` を省略して
  `tools/mutation_worktree.py` を起動したところ、`mutation worktree aborted: --attempt-out と
  --wrapper-attempt は同時指定が必要` で即座に (実際の変異走行前に) 中止した。
- 根本原因: `--help` の出力は両オプションを独立した optional として表示し、相互依存を示さない。
  `docs/dev-wave/mutation.md` の `DW-M07` も「`--wrapper-attempt`は整数」とだけ記し、
  `--attempt-out` との同時指定契約には触れていない。
- 恒久対応: `docs/dev-wave/mutation.md` の `DW-M07` へ「`--attempt-out` と `--wrapper-attempt`
  は同時指定必須で、片方だけの指定は起動前に中止する」旨を段8の自己改善 routing で追記した
  (本 wave の同時 commit)。実害は起動直後の rc=2 で判明し変異は1件も実行されなかったため、
  評価結果への影響はない。
- 再発検知: `--plan-only` による事前確認をこの wave 自身が実施し、同型の引数エラーを
  実走前に検出できることを確認した (再発防止というより検出済みの回避策)。
