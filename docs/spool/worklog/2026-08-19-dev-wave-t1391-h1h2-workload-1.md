---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t1391-h1h2-workload
seq: 1
title: '[T-1391] H1/H2 workload定義を8c supervisorへ実装し、登録済みbuild reportのacceptance正例を緑にした (コード + テスト + 記録、branch worktree-dev-wave-t1391-h1h2-workload、変異matrix = baseline PASSED・2/2 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- 着手前提確認 (command指示どおり): [T-1379] (C05 activation) と t944系 (bounded pilot
  task-run) は編集面重複なしと確認した。一方、指示にない稼働wave `dev-wave-t1353-c03-c08` が
  対象file (`p3_autonomous_workload_trial.py`、`trial_registry.py`) を直接編集中だったため、
  land (main=945358fb) まで着手を待った。
- premise訂正: command引数「`HOLDOUT_BINDINGS`/`WORKLOADS`はp2_2.py, p3_autonomous_workload_trial.py
  に実在確認済み」のうちp2_2.py側は誤りだった。p2_2.pyのWORKLOADSはlist型・別domain
  (calibration代表workload3点) でtrial_registry/p3/s8b_holdout_freezeへのimportが0件、識別子名
  `WORKLOADS`の字面一致による誤認と判明し、scope外とした。
- 根本原因: `autonomous_trial_completeness.py`のproducer-supported gateが`producer.WORKLOADS`
  だけを見て`producer.FORMAL_WORKLOADS`(H1/H2由来のrr80/rr20を含む、既存)を見ていなかった。
  `resolve_workload_entry`は既に両辞書を参照しており、gate側だけが非対称だった。
- 段3敵対相談 (2レンズ、`gpt-5.6-luna`) が、`run_trial`にも同型のWORKLOADS単独gateがあると
  独立に2本とも指摘した。実測の結果、`run_trial`は自身のgateへ到達する前に
  `_preflight_workload_profile`の無条件fail-closedを通り、これはexploratory以外の起動を
  「二段束縛 (`prereg_content_commit`/`prereg_effective_commit`) 未消費」で常に拒否する
  (`docs/phase3-s8c-autonomous-trial-runbook.md`が明言)。これは`docs/phase3-8c-preregistration.md`
  §6の前提条件8 (本waveが対象とする前提条件1とは別項目) に相当し、`run_trial`のgate単独修正は
  受理集合を1件も変えないためscope外・backlogと裁定した。
- 段6敵対レビュー (2レンズ) が、否定側テストのreceipt非生成assertionが恒真だった実問題を検出。
  fixは4巡を要した: 1巡目はreport fieldを個別書き換えたがreceipt検証パスが依然恒真、2巡目で
  `workloads_requested`の同期を追加したが別check (`_check_workload_coverage`) に阻まれ、
  3巡目で`workloads_requested`も揃えたがさらに別check (run-envelope、events側の`workloads`
  フィールド比較) に阻まれた。個別fieldを追いかける方式は際限がないと判断し、
  report/eventsを一切変更せず`resolve_workload_entry`をmonkeypatchして特定workloadだけ
  「非対応」に見せかける設計へ転換したが、これも`_accept()`内の別gate (arm-digest-chain、
  同じresolverを別目的で呼ぶ) に先に引っかかった。3巡上限に達したため、親が
  「直接gate呼び出し (`assert_campaign_layer3_chain`) のexact文字列検証で拒否理由の正確性は
  証明済み、`_accept()`経由は例外型とreceipt非生成の証明で十分」と裁定し、4巡目でその反映
  (exact文字列一致要求を型検査へ緩和) だけを行い収束させた。
- セッション中盤、dev-wave段3で`--lane sol`を使ったところユーザーから「高額モデルを使うなという
  指示だったはず」と指摘された。D514 (2026-08-18) により`--lane`はmodelを指さない
  レンズ識別子になっており技術的には`gpt-5.6-luna`しか起動しない (実害ゼロ、`codex exec`起動前に
  kill済み) が、既存memory `subagent-model-economy.md` (2026-07-26付) に
  「最難の敵対検証はgpt-5.6-sol」という古い推奨が残っていたのが一因と判明し訂正した。
  以降、全codex呼び出しは`--lane luna`のみ・レンズの多様性はprompt本文側で作る方式へ切り替えた。
- 変異matrix: `t1391.revert-formal-workload-gate` (gate拡張を元に戻す)、
  `t1391.broaden-resolver-exception-catch` (例外捕捉を`Exception`へ広げる) の2件を登録。
  probeでbaseline緑・両変異ともSURVIVED 0を確認し、変異1が想定より広く2テストを殺すと判明した
  ため期待nodeを完全集合へ更新して本走。結果: baseline PASSED・2/2 KILLED・SURVIVED 0・
  MISMATCH 0。

## 次の一手差分

### 完了

- [T-1391] 前提条件1 (H1/H2 workload定義) をacceptance gate側 (`autonomous_trial_completeness.py`
  のproducer-supported判定) へ実装し、登録済みbuild reportのacceptance正例を緑にした。
  `run_trial`経由の実起動は前提条件8 (二段束縛) 未消費のため引き続き到達不能 (別項目、本裁定の
  対象外)。
  remaining: none
  base: 05c8ca5f567f4232f967796a983036cac42f5162f8148f6851815f75b317b670
