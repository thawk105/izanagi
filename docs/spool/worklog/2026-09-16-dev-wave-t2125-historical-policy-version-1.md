---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-16
wave: dev-wave-t2125-historical-policy-version
seq: 1
title: [T-2125] 歴史閲覧を記録 policy で読めるようにし、照合先は policy SHA と stock pin の 2 つに限った (コード + docs、branch worktree-dev-wave-t2125-historical-policy-version、変異 matrix = probe 1 回 + 本走 baseline PASSED・8/8 KILLED・MISMATCH 0・期待 node 完全一致・F358 核 5 node を除いた delta 空 0 本)
---

## 本文

- ユーザー依頼は「歴史閲覧が前段で現行 policy と照合され、policy の版が上がると過去の v2 campaign が
  purpose を問わず読めなくなる問題を解く。`current-closure-unavailable` とは別の識別子を要する。
  当時の判定の閲覧と現行版による認証を分けて扱い、読めるようにすることを certified への昇格に
  使わない (規律 2)。[T-2483] / [T-2117] と編集面が重なる可能性があるので段 1 で実測する。
  本題の閲覧経路だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- **解いた。** v2 かつ `HISTORICAL_RAW` のときだけ記録 policy を別型の専用 decoder で読み、
  照合先を **2 つだけ** (receipt の `policy_sha256`、stock class の source commit) 記録側へ向けた。
  診断は `classification="historical-policy-version"`、status は既存の非認証値を再利用した。
  判断は {{D:historical-policy-recorded-comparison}}。
  一次資料は `output/insights/2026-09-16/t2125-historical-policy-version/README.md`。
- **`DW-G04` を満たしていない。満たしたことにせず記録した。** 現に停止している材料レポートは
  **0 件**である (外部 official root の v2 lock 20 件は policy preimage の 5 field すべてが現行と一致)。
  提示できるのは発火事象の計測 ID `fb5e74a17` (2026-08-12 の pin 前進) と、不一致条件を満たすが
  WAL 不在で手前で落ちる tracked lock 2 件まで。**台帳で名指しされた本題なので実装し、
  gate の趣旨は scope の切り詰め (照合先 5 → 2) で守った。**
- **段 1 の編集面実測。** [T-2117] は `tools/codex_reasoning_ab.py` の pin 可用性で重複なし。
  [T-2483] は `campaign_lock.py` の歴史 grammar で module も関数も別。両 branch は main と `0 0` で
  未 commit 編集面は読めなかった。
- **段 2 plan が親 brief を反証した。** 親は「編集面は 1 module」と書いたが、policy hash だけ直しても
  `build_admission.py` の stock class が `CURRENT_PIN` と照合するため旧 pin の campaign は落ちる。
- **段 3 レンズ A の中心所見を採り、plan の照合先 5 つを 2 つへ削った。** 記録 policy を照合先にすると、
  外部の登録・authority との照合が自己申告の整合確認に変わる。実測された版上げ事象は pin 前進だけで、
  registry からの削除・改名も authority literal の変更も一度も起きていない。**registry と authority を
  現行照合のまま残すことで、偽造 policy が架空 generator / authority を名乗っても現行の登録簿が拒否する。**
- **段 3 レンズ A が親の実測 2 件を反証した。** M4 の「今日は発火していない」は `repo_stock_pin` しか
  見ておらず preimage 全体へ一般化していた (親が 5 field で測り直し 20/20 一致)。M10 の「certified へ
  昇格する実経路がある」も立証過剰で、certified 再 admission が残るため**非認証 status を理由に
  最終 gate を不要と判断してはならない**と訂正した。
- **段 6 レビュー 2 本は独立に同じ must-fix 1 件へ収束した。** 新しい fixture が旧 pin を 2 箇所しか
  差し替えず、共有 helper `commit_receipt_support` が自分の名前空間の現行 pin で proof source を
  作っていた。import 時に作られる proof build context も差し替えが要る。fix 子が 12 行で閉じ、
  共有 helper 本体は無変更。
- **変異 M2 を matrix から外した。** certified 側の現行 policy 一致検査を 1 行消しても受理集合は
  変わらない — receipt の `policy_sha256` 照合と `wal.py` の exact 型境界が独立に拒否する。
  **多層防御であること自体は強みだが、「この 1 行が certified を守っている」とは言えない。**
- **変異 matrix の 1 回目は probe だった。** baseline PASSED・M9 KILLED・7 本 MISMATCH。7 本とも赤には
  なったが期待 node が狭すぎた (M1 は 157 node が赤)。`DW-M08` に従い観測 node 集合で再登録して
  本走し、**baseline PASSED・8/8 KILLED・MISMATCH 0**。初回は insight に erratum として残した。
- **F358 の共通核は 5 node、原因は `contract-loader-drift`。** 閉包 member を変異させた 7 本の
  `failed_nodes` の交差を取り、核を差し引いた delta を変異ごとに確かめた。**delta が空の変異は 0 本で、
  8/8 KILLED は核を除いても成立する。** M3・M4・M7 は delta = 1 で狙った node ちょうど
  (M7 は裁定 R3 の現行入口負例)。**ただし親は段 6 で核を差し引く前に「8/8 KILLED・完全一致」と
  書いており、段 8 で F358 を読み直すまで気づかなかった** (新規 F は採らず F358 の再発として記録)。
- **未 commit 由来の偽赤を 1 回踏んだ。** 焦点走が 19 件赤になり、本文は
  `contract-loader-drift: disk bytes が HEAD blob と不一致: orchestrator/campaign/wal.py`。
  変更した 3 module は enforcement source closure の member で、commit したら消えた。
- **local main 取り込み後の焦点走は 1362 passed** (`test_artifact_admission.py`、`test_build_admission.py`、
  `test_layer3_report.py`、`test_layer3_admission_diagnosis.py`、`test_t671_source_binding.py`、
  `test_autonomous_trial_completeness.py`、`test_p3_autonomous_workload_trial.py`、checkout `4b6a623e2`)。
- 工数: codex 子 7 本 (plan 1、consult 2、author 1 = 738 秒 / 25 call、review 2、fix 1)。
  計算ノード job は焦点走 8 本、変異 2 走 (probe + 本走、各 baseline 1 + 変異 8)。
- **scope 外として台帳に新規 T を立てなかった** (依頼が台帳の追加を scope 外と定めたため)。
  registry からの削除で再び塞がる残余、layer3 の通常 decoder による旧 grammar 拒否 ([T-2483])、
  critic digest に classification が届かないこと、記録 policy の真正性を検証できないことは
  insight の「残余」節に記録だけ残した。

## 次の一手差分

### 完了

- [T-2125] 歴史閲覧 (`HISTORICAL_RAW`) が現行 policy との一致を要求して過去の v2 campaign を読めなく
  なる問題を解いた。v2 かつ歴史閲覧のときだけ記録 policy を別型 decoder で読み、receipt の
  `policy_sha256` と stock class の source commit の 2 つを記録側と照合する。registry と authority は
  現行照合のまま。診断は `classification="historical-policy-version"` で、certifying 条件を構造的に
  満たさない。変異 matrix は本走 baseline PASSED・8/8 KILLED。
  remaining: none
  base: 80d86096c980960f97768eb925cf308c16559ffd392bdfdd14e7ba52c3ce3ca5
