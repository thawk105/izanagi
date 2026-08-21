---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t1472-c02-arm-noninterference
seq: 1
title: '[T-1472由来] 8c事前登録C02 (off arm payload非干渉性) を実装した (コード+テスト、branch worktree-dev-wave-t1472-c02-arm-noninterference、変異matrix = baseline PASSED・6/6 KILLED・SURVIVED 1件(erratum、意図通り)・MISMATCH 0、受入 verdict=child-green)'
---

## 本文

- T-1472 (2026-08-21 readiness audit) が特定した H1/H2 正式実験のblocker群のうち、
  C02 (arm 非干渉性) だけへscopeをnarrowして実装した。8c事前登録 §4/§6条件2 の
  非干渉性節が「本書の発効時点でこの性質は成立していない」と自己申告していたgapを埋める。
- **事実訂正 (command前提を覆す新事実)**: command/監査READMEは `s8c_arm_inputs.py` を
  「autonomous runnerにもcompleteness consumerにもimportされないleaf module」と記していたが、
  実際には `p3_autonomous_workload_trial.py`/`trial_registry.py` は既に2026-08-18の
  [T-1311] 単位A/Bで配線済みだった (import grep実測で判明)。未配線は completeness consumer
  だけであり、監査は「leaf module」docstring (s8c_arm_inputs.pyがrunnerをimportしないという
  一方向の記述) を双方向の未配線と誤読していた (F451と同型の罠)。
- **実装**: `_common_payload()` にarm引数を追加し、off armのとき workloadを中立定数
  `OFF_NEUTRAL_PAYLOAD_WORKLOAD` へ、descriptor_bindingからholdout依存の
  `arm_binding_digest_sha256` を除去した。provider-facing invocation IDとaudit-only
  invocation IDを分離する `_provider_and_audit_invocation_ids()` を新設し、off armでは
  provider-facing IDにholdout不変なcontent_digest_sha256を使い、実arm_binding_digestは
  audit-only IDとしてjournal event側にだけ残した。critic reflowのcritic_digest/
  candidate_labelもoff armで中立化した (`_run_one_pending_critic()`一箇所への集約で
  generation中・finish時pending drainの両経路をカバー)。`autonomous_trial_completeness.py`
  の追随検査はexact述語化した。
- 段2 codex planは「provider-facing invocation IDは監査専用」と誤認しており、段3敵対2レンズが
  独立に (invocation IDが実digest/実workloadを保持したままproviderへ渡る) blockerを発見、
  段4裁定でinvocation ID自体の分離設計へ修正した。段6敵対レビュー2本はblocker 0件、
  major 2件 (auditor pre-audit skip経路の変異検出テスト欠落、completeness exact判定の
  digest値改変ケース欠如) をfix 1巡目で解消。fix 2巡目は新規テストのfixture値
  (`DRIVER_STOP_REASONS`に無い文字列) を是正。変異matrix実測でm6が単層変異では別の独立した
  exact key-set検査にmaskされると判明し (DW-M02の想定挙動)、dual-layer変異へ再構成して
  解消した。単層版はerratumとしてSURVIVED期待のまま`mutation-spec.json`に保全した。
- 受入1回目でtest_trial_registry.py 13件が赤 (main単独では非再現、自分の実装由来と確定)。
  原因は `autonomous_trial_completeness.py` を変更する際、`p3_autonomous_workload_trial`の
  importerだけをconsumer test拡張対象にし、`autonomous_trial_completeness`自体のimporter
  (8ファイル、trial_registry.pyのテストを含む) を見落としたこと ({{F:consumer-test-single-module-grep}}
  参照)。test_trial_registry.pyのfixtureをoff-arm neutralization要件へ追随させ解消した
  (fix4)。受入2回目以降はmain進行に伴うlog-file再利用衝突・preclaim-history-provenance
  timeout (既知の混雑事象) で2回リトライし、4回目で `child-green` を得た。
- **scope外として明示 (裁定パッケージ、{{D:provider-audit-id-split}} 参照)**:
  generation≥2の実測結果依存チャネル (harness_resultのmetrics/outcome、critic_feedback) は
  中立化しない — 真の実験結果であり実装バグではないため。「非干渉性が完全に成立した」とは
  主張せず、「generation 1相当の共通payload構成 (workload・descriptor_binding・
  invocation_id) がholdout非依存になった」に限定して主張する。次の一手として、
  この残存ギャップの取り扱い (許容限界として明文化するか将来wave/ユーザー裁定で
  結果チャネルの加工機構を検討するか) をユーザー裁定へ残す。completeness の
  s8c_arm_inputs経由の意味的digest chain検証 (単位C) も未実装のまま。
- 条件2の評価器 (`s8c_preregistration_evidence.py`) の充足状態遷移はこのwaveでは未実測
  (次の一手)。
- 一次資料: `/work/1/SFC/tanab/dev-wave-jobs/2026-08-21_t1472-c02-arm-noninterference/`
  (brief・plan・段3レンズ2本・段4裁定・段5実装・段6レビュー2本・fix1-4・変異spec/out・
  受入receipt)。

## 次の一手差分

### 新規

- {{T:s8c-c02-generation2-scope}} **P2・裁定待ち**: C02のgeneration≥2結果依存チャネル
  (harness_result・critic_feedback) の非干渉性を将来どう扱うか (許容限界として明文化するか、
  結果チャネルの加工機構を新設するか) をユーザーへ確認する。
- {{T:s8c-c02-decider-evidence-check}} **P3**: C02実装後、`s8c_preregistration_evidence.py`
  の条件2評価器の充足状態 (UNSATISFIED→EVIDENCE_UNDEFINED等) をlibrary経由で実測し記録する
  (前例: `output/insights/2026-08-18_s8c-c12-c04-consumer/README.md`)。
