---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2565-certify-repo-root-binding
seq: 1
title: [T-2565] certify 投入の検査木と job の実行木を qsub の cwd で束縛した (コード、branch worktree-dev-wave-t2565-certify-repo-root-binding、変異 matrix = baseline PASSED・6/6 KILLED・SURVIVED 0・MISMATCH 0・期待 node 完全一致)
---

## 本文

`submit_certify.sh` は `--repo-root` の木を検査し、job 側は `PBS_O_WORKDIR` から木を導出していた。
両者を結ぶ機構が無く、repo 外の cwd から投入すると検査木と実行木が別になりうる。qsub を
`REPO_ROOT` を cwd とする subshell で起動し、相対 `--job-script` を投入元 cwd 基準で絶対化して閉じた。
詳細と限界は insight `output/insights/2026-09-16_t2565-certify-repo-root-binding/`。

**段 3 が親 brief の断定を 2 つ退けた。** (a) 「木が食い違えば certify receipt の provenance が偽になる」は
過大だった。`pinned_clean` は CCBench の属性を書く field であり、全入力の checkout path 一致を表さない。
成立するのは「submit の検査が実行木に掛からない」「双方の third-party staging の同一性を誰も検査しない」まで。
(b) 「同じ commit・clean なら job 側の照合が通る」も十分条件として過大で、job は script hash・request ID・
project・queue・nodes・walltime・ratio・protocol・非 dry-run も照合する。

**不変条件を 1 つ緩める裁定をした ({{D:certify-submit-job-tree-binding}})。** 親が置いた「qsub argv を
1 bit も変えない」と「相対 `--job-script` の参照先を保つ」は両立しない。byte 不変を優先すると
「submit が検査した bytes と qsub が読む bytes が別」という経路を新設することになるため、
不変条件の方を譲った。既定入力と絶対入力では argv は変わらない。

**完了判定を観測範囲へ合わせた。** 当初 brief は「job 側の `PBS_O_WORKDIR` が一致することを実走テストで
示す」と書いたが、fake qsub が観測できるのは submit が起動するプロセスの実 cwd までである。
`PBS_O_WORKDIR` = 投入時 cwd は既存実測 (`output/insights/2026-09-07/a1-pilot-attempt-0002/README.md`) を
根拠とし、本修正を通した実 scheduler 観測は行っていない。

**レビューが実在の欠陥を 1 件見つけた。** 相対 path の絶対化に使った `$(pwd -P)` は command substitution の
仕様で末尾改行を落とすため、cwd 名が改行で終わる場合に検査した file と別の file を投入しうる。
本題の再発型なので must-fix として sentinel 方式で直し、正例テストを 1 件足した。同型は `:13,14,30` にも
既存だが、既存欠陥の族一般化は scope 外として触っていない。

**運用事故 1 件。** 変異 probe の初回投入が `orphan-hold` で起動前に中止した (`source_state=unchanged`、
dirty path なし)。原因は親が同じ worktree から全史 provenance 監査と変異 probe を並行 dispatch したことで、
`DW-O26` の直列化義務に反する。hold が指示する順序 (job の終端確認 → clean/HEAD 確認 → sidecar 手動削除) で
復旧し、手動 `qdel` は使っていない。変異は 1 つも注入されず木は clean のままだった。

**refuted (段 3・段 6 で退けた所見):** subshell が rc を失う、cd 失敗後に qsub を起動する、相対
`--attempts-root` の保存先が repo 側へ移る (外側リダイレクトで投入元基準に保たれるので、親 brief が
書いた「両引数とも絶対化が要る」は過剰だった)、絶対化が receipt schema を変える、既存テストの弱体化、
registry / runbook の連動変更、他 submit への波及。

**所要台帳は更新不要と実測で確定した。** 追加 7 ケースが未登録でも全収集被覆率 90% を割らない。

**M3 / M4 / M6 は厳密な単一理由性を満たさない。** 同じ不正状態を同一 node 内の後続 assertion も検出する。
因果は「異なる script の選択」に絞れるが、冗長 gate であることを明記し、単独変異の証拠としては
最初の殺傷点だけを根拠にする。初回 probe は全件 SURVIVED 登録で観測 node を集めたため MISMATCH 6 件に
なった。これは設計どおりで erratum として report を残した。

工数: codex 子 8 本 (plan 1・consult 2・author 1・review 2・fix 1・focus 1、いずれも gpt-6-astra / medium)。
計算ノード job は被覆率 2 回 (1 回は出力を tail で切って合否行を失い投げ直した)・全史 provenance 監査 1 回・
変異 probe 2 回 (1 回は上記 orphan-hold)・変異本走 1 回。焦点走 3 回は login。

## 次の一手差分

### 完了

- [T-2565] `submit_certify.sh` の `--repo-root` と job 側 `PBS_O_WORKDIR` を qsub の cwd で束縛した。
  相対 `--job-script` は投入元 cwd 基準で絶対化し、検査した file をそのまま投入する。
  remaining: none
  base: d41396b73fc3f6f14466141a140a9110cdbcc6cb27f36e42d1a308ad3933316f

### 新規

- {{T:certify-submit-path-resolution-hardening}} **P3・新規**: submit 系 shell の cd / pwd が
  `CDPATH` と相対 PATH 要素に弱い。`submit_certify.sh:30` の `$(cd "${2:?}" && pwd -P)` は `CDPATH` が
  設定されていると cd の出力と pwd が連結され、`--repo-root -P` はオプションとして解釈される。
  同型は `:13,14` にもある。また相対 PATH 要素があると、qsub を `REPO_ROOT` へ cd してから起動する
  現行実装では `REPO_ROOT/bin/qsub` を探索しうる。[T-2565] が scope 外として送った留保である。
  qsub の事前解決は `test_pegasus_tools.py` の「dry-run で cluster command を要求しない」既存契約と
  衝突するため、直すなら別案が要る。
- {{T:certify-job-script-hash-scope}} **P3・新規**: 認定 job の submit binding 照合が、実行中の
  spool script ではなく `$TOOLS/certify_calibration.sh` を hash している
  (`certify_calibration.sh:227`)。script 取り違えをこの照合が必ず捕捉するわけではない。
  [T-2565] が scope 外として送った留保である。束縛したい対象 (投入した bytes か repo 内の正規 script か) を
  決めてから直す。
