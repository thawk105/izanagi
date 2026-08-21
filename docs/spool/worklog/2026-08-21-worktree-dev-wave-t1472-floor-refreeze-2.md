---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: worktree-dev-wave-t1472-floor-refreeze
seq: 2
title: D510 追随実装の所在を監査し between_run_floor.py 誤前提を訂正、項目6は前提条件付きで見送った (docsのみ、branch worktree-dev-wave-t1472-floor-refreeze)
---

## 本文

- 段2 codex plan (`--reasoning max`, sandbox read-only) と段3 敵対2レンズ (`--lane sol`=
  正しさ境界、`--lane luna`=整合・実効性・所有範囲) で、D510 (2026-08-18) の判定器・
  3表・attempt registry・role payload 非干渉性の実装状況を file:line で監査した。
  当初 command 引数が土台に指定した `orchestrator/campaign/between_run_floor.py` は
  D510 と無関係 (A2 between-run noise floor calibration driver) であり、実際の実装は
  `orchestrator/campaign/s8c_result_judge.py` (T-1352)・`orchestrator/campaign/
  trial_registry.py` (T-325・T-1310・T-1337)・`orchestrator/campaign/
  s8c_generation_projection.py` 等 (T-1311) に既に存在すると確定した。詳細は
  {{D:d510-followup-implementation-audit}}。
- 唯一の未実装項目 (測定の近接性ラベル、D510項目6) は、レンズ luna が「`judge()` に
  production caller が存在せず DW-G04 の発火 gate が不成立」と決定的に指摘し、
  レンズ sol が最小実装案自体の設計欠陥 (raw-value attestation に束縛されない
  `relation_kind` の自己申告可能性、3表内容への意図しない byte 変化、既存受理集合との
  矛盾) を独立に発見した。両者を踏まえ段4裁定で実装を見送った。一次資料:
  `output/insights/2026-08-21_t1472-floor-refreeze/README.md` (brief・段2プラン・
  段3敵対2レンズ逐語・段4裁定を保存)。
- `ListAgents` 実測 (17 peer session) と `git diff main..<branch> --stat` 実測により、
  `worktree-dev-wave-t1472-c02-arm-noninterference` (D510項目5=role payload非干渉性を
  担当している可能性が高い、ahead=0で未commit・live busy) との将来の入力契約統合コストが
  未定義と判明した。また `worktree-T-1371-official-run-root`/
  `worktree-dev-wave-t1280-role-output-contract`/
  `worktree-dev-wave-t1458-noncertifying-consumer` が `trial_registry.py`/
  `p3_autonomous_workload_trial.py`/`autonomous_trial_completeness.py` を活発に変更中と
  確認し、本waveはこれらへ触れなかった (実装差分ゼロのため実害なし)。T-425/T-972/
  rulings-calibration-registration 系の候補 branch は全て main に完全包含済み
  (`ahead=0`) と確認した。
- t-1458系peerセッション2件から、main受入が external/ccbench の gitlink 前進
  (511c9538→ef9328a3) 絡みで一時赤になりうる (provenance trailer欠落・
  承認定数不一致) との共有を受けた。本waveの編集面外のため対応せず、段9受入投入前の
  main再確認で自然に反映させる方針とした。
- 実装差分ゼロ (docsのみ) のため変異matrixは対象外 (DW-S04)。記録前検査として
  `python3 tools/check_docs.py` = 違反なし (無関係の既存警告2件のみ)、
  `python3 tools/spool_fold.py --dry-run` = `status: planned` (fragment形式・base整合とも
  正常) を確認した。受入全走は段9で実施する。

## 次の一手差分

### 新規

- {{T:d510-item6-proximity-labeling-followup}} **P2・新規**: D510項目6 (測定近接性ラベル)
  を実装する将来wave。前提条件: (a) provenance (timestamp・環境/実装/toolchain
  identity・関係区分) を生成し `s8c_result_judge.judge()` へ渡す production producer の
  新設、(b) `relation_kind` を raw-value attestation と同じ信頼境界 (署名・registry束縛)
  に載せる設計、(c) t1472-c02-arm-noninterference (D510項目5) 完了後に C02 の
  registry-slot/digest 参照との入力契約統合方針を決定、(d) 近接性ラベル・時間差を3表
  (`_table_bytes`/`publish_result_table`) へどう反映するかの明示設計。一次資料:
  `output/insights/2026-08-21_t1472-floor-refreeze/README.md`。
