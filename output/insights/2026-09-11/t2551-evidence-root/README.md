# T-2551: 段4jobの証拠保存先

authority: none
default_effect: no-state-change

D1936項5を実装した。canonical化した保存先を元の環境変数へ再exportする1行で、
shellと後段Pythonの保存先を揃える。D1773/D1801のCMAKE_PREFIX_PATH exact3行、
receipt schema、admission分類、correctness/anomaly拒否は変えない。

既存job契約fixtureは入力cwdからrepoへ実shellで移動し、後段Pythonが受け取った
環境値・cwd・解決先・実書込先を照合する。相対/絶対pathを検査する。
build/scheduler/driver本体は既存stubであり、本番compute実験の実証ではない。

## 独立レビュー

author-result.md、review-a-result.md、review-b-result.mdに逐語を保存した。
全workerはgpt-6-astra / medium、authorはworkspace-write、review2本はread-only。
両reviewのreal/must-fixは0。保存先不一致、恒真保証、既存契約ドリフト、scope逸脱の
候補はコードによる反証を確認し、親もrefutedとして採用した。
authorのテストはqstat preflight失敗で子未起動。子の未実走を緑としない。

review-b-result.mdのみdiff --checkに従い、行7/10/13/16の末尾ASCII空白2個を除去した。
正規化版は終端LFを補った2033 bytes。復元はその4行へ空白2個を戻し、終端LFを除去する。
原文は2040 bytes、SHA-256
`1833c5790207cfe621bf6dff0b94e0d47a8a388a1541f56f6305c50e57c2afe6`。可視文字は変更していない。

## 変異事前登録

M1はexportの1行を削除する。相対pathケースだけがcwd移動後の書込失敗を検出し、
絶対path正例は通ることを期待する。静的marker検査を同時に走らせず単一理由性を保つ。
既存mutation_harnessを使い、期待nodeは
`orchestrator/tests/test_p3_s4_loop_job_contract.py::test_evidence_root_reaches_actual_job_driver_as_canonical_path[relative]`。

## 作業環境で観測した点

新規worktreeのsubmodule初期化中断後、再試行はrc0だったがnested checkoutの空index lockと
未展開tracked fileが残り、startupがdirtyを検出した。当該gitの不在をps/lsofで確認し、
専用worktree内でlock退避・HEAD復元・再帰初期化を行い、fresh/midflight startupを通した。
この復旧は本題のproduction変更に含めていない。

## 検査の実測

- 固定実装commit: 909406b4d3690a4a3a3d659abaf8c1f4eaa7e8c9。
- job契約file全体: 82 passed / 3.31秒、job 991681.nqsv (Elapse 9秒)。
- M1 baseline: 相対/絶対path、実consumerの拒否時保存/green経路、registry分類の5件成功 (2.62秒)。
- M1変異: relativeだけが失敗、absoluteと他3件は成功。KILLED 1/1、期待node集合完全一致、harness rc0。
  Pythonがcwd変更後の相対pathへ書いてFileNotFoundErrorとなるため、文字列の診断差だけをkillにしていない。
- 全史provenance: 9631件、新規違反0、既知56、rc0。既知履歴違反を解消したとは主張しない。
- check_codex_agents、check_docs、diff --checkは成功。
- 記録前受入: tested main `8d3127699fdfa1467ce5324ed2b934c9a552dcaf`、tested tip
  `df3bd8ce5e2f8e270d1a2e736ec48bdf959c224d`、23,070 passed / 68 skipped、child-green。
  3 shard、全体red node 0、前後fingerprint一致。既存holdを含む既定受入で、今回の除外追加は0。
  `acceptance-recorded.json`と`acceptance-recorded.log`に受領証と集約結果を保存した。
  段4関連docs-only waveのmain追記はphaseの同位置で競合したため、両項を保持して統合した。

新規実験、保存基盤一般化、correctness gate緩和は行っていない。
