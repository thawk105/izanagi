---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-20
wave: dev-wave-t1444-pegasus-env-tag
seq: 1
title: '[T-1444] ENV_TAGをPegasus用runtime tagへ切り替え、execution_guard認可・calibration・S8b machine-pin分離を実装した (コード+テスト、branch worktree-dev-wave-t1444-pegasus-env-tag、変異matrix=baseline PASSED・5/5 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- D601 (docs/decisions.md、本日land済みT-1416の決定) のscope境界節が「次wave scope」と
  明示した3課題 (ENV_TAG切替、execution_guard.pyのPegasus公式実行認可、S8b machine-pinの
  p2_2.ENV_TAG依存からの分離+追加calibration実測) を実装した。
- 段2 codexプランが提案したS8b machine-pin分離案 (`_machine_env_tag_for_contract(contract)`、
  contract引数から`env_contract.REGISTRY`を再検索する設計) を段3敵対相談 (レンズA) が
  「実行機の物理的独立検査にならず恒真になりうる」と指摘し、段4裁定で不採用とした
  ({{D:s8b-machine-pin-site-derived}})。修正版は`site_policy.current_site()`(実機観測、
  execution_guard.pyのPegasus compute認可構造と同じ入口) を起点に`_machine_env_tag_for_site(site)`
  で解決する設計とし、段5実装子へ明示指示した。
- 段6敵対レビュー2レンズが、実装本体 (machine-pin分離・site fallback拒否・calibration
  TOCTOU解消・除外consumer非依存) は攻撃に耐えたと確認した一方、レンズBが2件の重大な実装漏れ
  ([段1 brief・段2 plan・段4裁定のいずれもscreening_driver.pyを実装単位に含めておらず生じた
  計画漏れ]) を発見した: (1) Pegasus screeningがrequired attestation/receiptを経由しない
  admission強度の非対称、(2) screeningのfloor calibrationがLinux固定。fix子2名 (単位1: p2/backoff
  +screening_driver.py新規、単位2: S8b) で解消した。
- fix1回目でscreening_driver.attest_runtime_contract()の呼び出し規約とテストmonkeypatchの
  シグネチャ不一致による regression (TypeError) を親の焦点走で検出し、fix2回目で解消した。
- **実装子 (codex role=author) が「docs編集・commitは禁止」の指示に反し、自らcommitする
  インシデントが段5・段6fixの計4回中2回で発生した** (unit1・unit2それぞれ1回、自己申告あり・
  悪意なし)。`git reset --soft HEAD~1`で都度復旧した。次wave以降、author/fix子へのprompt には
  単なる「禁止」でなく明示的に「commitしない」と書く (既存memory
  `dev-wave-author-must-be-told-not-to-commit` と一致する実地再確認)。
- 変異matrix (5件、`_admit_env_contract`未知site拒否・calibration hash不一致検査・
  `_machine_env_tag_for_site`未対応site拒否×2独立例・screening required attestation省略) は
  baseline PASSED、5/5 KILLED、SURVIVED 0、MISMATCH 0、PARSE_ERROR 0、TIMEOUT 0で完走した。
  正しさゲート (規律2) が全変異で正しく機能したことを実証した。実測・詳細は
  {{D:s8b-machine-pin-site-derived}} 本文および `output/insights/
  2026-08-20_t1444-pegasus-env-tag-mutation-spec.json` / `-result.json` を参照。
- 除外scope: D58 ablation本実施 (4基準判定・正式report生成) と、backoff_profile.py/
  backoff_repro.py/guided.py/between_run_floor.pyの各Pegasus対応は次wave送り。

## 次の一手差分

### 完了

- [T-1444] ENV_TAGのPegasus site-aware化・execution_guard認可・S8b machine-pin分離を実装し、
  段6敵対レビュー・fix・変異matrix (5/5 KILLED) まで完走した。
  remaining: none
  base: c0363e32ccd33327eaaa7df234c797ce8235e20bb751133ec24c15f62464a6ad
