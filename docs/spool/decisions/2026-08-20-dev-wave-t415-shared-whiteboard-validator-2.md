---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-20
wave: dev-wave-t415-shared-whiteboard-validator
seq: 2
---

## {{D:layer3-report-shared-whiteboard-value-domain}}. layer3_report と state_from_dict の whiteboard 値域検査を共有 validator で一本化する

**決定:** `orchestrator/campaign/p3_s4_loop.py` に新設した public 関数
`assert_whiteboard_value_domains(entry, index)` (`_WB_VALUE_DOMAINS` 直後に配置) を、
`state_from_dict` (checkpoint 復元) と `layer3_report.build_report` (層3材料レポート生成、
`_assert_unique_refs` より前の whiteboard 抽出直後) の両方から呼ぶ。direction/magnitude/result の
値域チェック実装を1箇所に集約し、独立実装によるドリフトを防ぐ。`layer3_report.py` 側は
`ValueError`/`KeyError` を捕捉し同ファイル既存の流儀どおり `Layer3ReportError` へ包む。

**理由:**
- `layer3_report.py` は `loop_state.json` を直接読み whiteboard を検査しない独立 reader であり、
  `state_from_dict` が拒否する値 (例: `direction="up"`) をそのまま層3材料レポートへ通し、
  内容由来の `wb:` source-ref へ焼き込んでいた (adjudication package
  `output/insights/2026-08-04_t287-checkpoint-values/adjudication-package.md` §2)。
- schema enum 案は手作業 runbook 経由の raw whiteboard 参照を閉じず、検査省略案は値チェックの
  主張を弱めるため、ユーザーは共有 validator 案を裁定した (2026-08-20)。
- production 層の import 方向は既存慣習 (`p3_s4_loop_sort.py`/`p3_s4_loop_trigger_gating.py`/
  `p3_autonomous_workload_trial.py` 等が既に `p3_s4_loop` を core module として import 済み) に
  ただ乗りする形とし、新規の共有 module は作らなかった (循環 import は生じない。
  `p3_s4_loop.py` 自身は `layer3_report` を import しない)。

**却下した選択肢:**
- `layer3_schema.json` へ direction/magnitude/result の enum を書く — schema 層でしか閉じず、
  手動 runbook (`docs/phase3-s4b/s5-sort/s8a-trigger-runbook.md`) の raw whiteboard 経路は残る。
- 検査を追加しない — 「checkpoint 値を成果物まで閉じた」という主張ができないまま。
- 値域検査の前に entry の形状・未知キー検査を新設する再順序化 — 受理/拒否の結果 (成果物の
  受理集合) を変えず診断分類の粒度だけが変わるため、規律5 (盛らない) により見送った。

**scope外:** producer 側 (`project_whiteboard`、in-memory 射影経路) の値域検査、origin 束縛/
integrity、エラーメッセージの redact、手動 runbook 経路のクローズは adjudication package
§1/§3/§4 の別項であり、いずれも独立のユーザー裁定を要するため本決定に含まない。
`autonomous_trial_completeness.py::_cross_binding_whiteboard` は raw whiteboard を読むが
唯一の下流使用が `canonical_record_ref` によるハッシュ化 (artifact bytes の provenance/
束縛検査) であり値域では分岐しないため対象外とした (D118 が指摘する T-287 相当ウェーブの残余の
うち、本決定が閉じるのは layer3_report 独立 reader の値域チェック欠落だけである)。
