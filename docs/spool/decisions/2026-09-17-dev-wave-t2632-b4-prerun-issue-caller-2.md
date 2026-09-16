---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2632-b4-prerun-issue-caller
seq: 2
---

## {{D:b4-prerun-caller-scope}}. B-4 prerun publication の production 呼び手は現物からの不足報告と空 batch での発行器到達までを担い、bootstrap 所属を batch 所属で真にしない

**決定:** 発行器 `issue_b4_prerun_publication` の production 呼び手 (`orchestrator/campaign/p3_b4_prerun_caller.py`) の
責務を次に固定する。

- 入力は合成ループ campaign の checkpoint (`loop_state.json` の whiteboard) と `campaign.lock` だけとし、argv で明示された
  campaign root だけを読む。走査 framework・sidecar 入力・ID 規約・耐久 carrier・resolver は作らない。
- 候補は `whiteboard[].result == "rejected"` の exact 一致だけとする。これは供給源を赤 precursor に限る D1936 項 8 に
  よるもので、registry が SUCCESS を受理しないからではない (台帳型は SUCCESS を受理し、manifest の適格性で除く)。
- 候補が 1 件でもあれば、現行の保存形式に出所の無い 12 field (attempt_id / block_id / digest_red_classes / workload /
  calibrated_workload_member / initial_proposal_sha256 / bootstrap_member / reference_tps / reference_snapshot_hash /
  reference_receipt_hash / reference_is_unique / arm_digest_received) を全候補ぶん集計して typed に止まり、発行器を呼ばない。
  欠落は保存形式の既知の制限に基づく静的分類であり、記録の `artifact_path` / `artifact_key` は参照した出所が無いので null。
- 候補 0 件なら空 batch で発行器をちょうど 1 回呼び、typed rejection または receipt を JSON 1 行で返す。
- publication root は実行時に発行器と同じ checkout から解決し、呼び手は選べない (D1881)。
- **`bootstrap_member` は「発行 batch に含めた行だから真」とはしない。** 事前固定した bootstrap 集合との照合に
  ならず述語を恒真化する (D1881 の理由と同じ)。何を集合とし、いつ固定するかは未裁定のまま残す。
- 真偽値 4 つ (上の 3 つと arm_digest_received) を無根拠に埋めず、行を捏造せず、発行器・台帳の受理集合を変えない。

併せて、前 wave の一次資料が置いた順序「封印発行 (1) は §5 の 2 欄 (2) と独立に閉じられ、base campaign 起動 (3) は
両方の後」を訂正する。発行器は適格行が 201 未満なら `design_not_feasible` で拒否するので、封印 receipt の取得は
(2) と (3) の両方と、proposal・走行・参照点の対応証拠を前提とする。(1) で独立に閉じられるのは production 経路の実在だけである。

**理由:**

- 現行の保存形式は D39 決定 3 のリーク遮断として whiteboard を 5 field に限り、proposal document を保持しない (D1846)。
  したがって非空 batch は現物から構成できず、構成できるふりをする経路 (placeholder hash、真偽値の True 固定、
  genome からの再構成) はいずれも捏造か述語の恒真化になる。呼び手が正直にできるのは、何が無いかの報告と、
  候補 0 のときに発行器の拒否まで到達することだけである。
- 「batch に含めたから bootstrap 所属」は、任意の提案を登録操作だけで述語に通す形であり、発行器自身も
  `caller_schedule_is_not_bound_to_an_external_authoritative_population` を非保証として掲げる。
- 依頼は「組めなければ何が足りないかを実測で書いて返す (実発行を完了条件にしない)」であり、成功経路の一般化は DW-G04 の
  発火条件 (既存 artifact) を欠く。

**却下した選択肢:**

- `bootstrap_member` を発行 batch 所属で真とする (親の当初案 P1) — 述語の恒真化。
- 12 field を探索して埋める resolver、campaign 走査 framework、attempt_id 規約の新設 — 発火する現物が無く、
  D1936 項 8 の「母集合を作るための追加基盤」に近づく。
- 候補 0 のとき発行器を呼ばず成功扱いにする — 発行器の拒否理由を記録に残せず、到達確認にならない。
- 成功 JSON を stub で検査する — F649。実発行器に 201 行の合成 batch を通す test で代替した (現物から組めることの証拠ではない)。
