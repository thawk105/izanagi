# [T-2124] 段 6 裁定 — 敵対レビュー 2 本の所見

## レビュー A (正しさ防壁): 所見ゼロ

blocker 0 / must-fix 0 / nit 0。攻撃 6 項目すべて「破れなし」で、根拠を実物 file:line で示した。

DW-M02 により**所見ゼロを変異なしで緑と数えない**。変異 matrix の本走で裏取りする。

レビュー A が実物で確認した主な点:

- E0 拒否は v1 入力集合全体に残る。`schema_version` を持たない JSON object は
  (仮に `authority` key があっても) v1 として decode され `authority is None` になり、
  必ず `E0 / v1-authority-absent` → 局所 raise になる。
- 変更前に E0 以外で拒否されていたのは「正しい v2 / E1 に対する現行閉包取得不能」だけであり、
  それは D1387 が許した緩和そのもの。lock から `E1-stale` を直接生成する production 経路は無い。
- 負例の `_REAL_...` は autouse fixture 定義より前 (module line 31 vs 36) で保存され、
  production 関数を掴む。`_fixture` が書く lock は `{"fixture": "s1", "role": role}` だけで
  `schema_version` も `authority` も無く、production decoder 上の v1 である。
- 正例の v2 helper は HEAD commit の対象 blob を読んで production encoder を通し、
  検証側も同じ記録 commit の blob を読み直すため `_verify_committed_loader_binding` を通る。
- `s1_report` は `artifact_admission._require_verifier_epoch_for_purpose` を実行時に
  module 属性として参照するため、spy の monkeypatch が確実に捕捉する。
- xdist の worker は別 process で module global を共有しない。monkeypatch は function scope。
- 既存 assert の反転・緩和・skip・削除は 1 件も無い。

## レビュー B (変異と検出力): 所見 4 件

### 所見 B-1: E1 epoch identity を改変する変異が生き残る — real、しかし本 wave の scope 外

**判定: real。実装しない。裁定パッケージとしてユーザーへ返す。**

中央 gate の戻り値を、同じ `state="E1"` / `reason_code="recorded-closure"` を持つが
別の有効な 64 桁 SHA の `CampaignVerifierEpoch` へ差し替える変異は、正例 4 assert を
すべて通り抜ける。負例は E0 で先に終了し、他の S-1 node は autouse fixture が
実 callee を通さない。

scope 外とした理由 (DW-G05 / DW-S04):

- **明示要求内でない。** 依頼文は「E0 拒否が生きたままであることを負例テストで固定する」を
  求めており、E1 診断の同一性は求めていない。依頼文は
  「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と明示している。
- **実在欠陥ではない。** レビュー A が E0 経路・E1 経路の両方を実物で確認し、
  現行実装に誤りは無い。所見は仮想の変異に対する検出力の話である。
- **本 wave が作った穴ではない。** 変更前は実 callee を通るテストが 1 本も無かったため
  (autouse fixture が全 node で差し替えていた)、同じ変異は変更前も同じく生存した。
  本 wave は上流側 (decode・v1 E0 導出・局所 raise) の検出力を**増やしている**。

**裁定パッケージとして返す内容:** 正例へ
「返った epoch の `campaign_verifier_epoch` が、同じ lock bytes から独立に導いた
`_recorded_campaign_verifier_epoch(...).diagnostic` のそれと一致する」assert を 1 本足せば
閉じる。成果物影響は
「`hard_gates.certified.campaign_verifier_epochs` が別の closure を指す epoch identity を
載せうる」。着手費用は assert 1 行。次タスク候補として worklog へ書く。

### 所見 B-2: rejection reason の `message` 変更が検出されない — real、nit、不採用

変更前後とも誰も殺さない。成果物影響は「JSON / Markdown report の拒否説明文が無検出で変わる」
だけで、certified 選択・受理集合・台帳は変わらない。DW-G05 により nit とし、
追加 review を起動しない。段 4 が exact envelope 比較を不採用にした裁定と整合する。

### 所見 B-3: M1 / M2 の凍結した赤面説明が実際の最初の赤面と一致しない — real、erratum で訂正

**判定: real、採用。ただし期待 node 集合は変えない (DW-M08)。**

段 4 で凍結した変異事前登録の「単一理由性の確認」欄の**散文**が不正確だった。訂正:

- **M1** (局所 E0 raise 削除): 実際には WAL 読取禁止の assert が先に発火し、
  `_assess_campaign` の広い catch で `schedule_ledger_invalid` へ変換される。
  pytest 上で最初に赤になるのは `reason["code"] == "campaign_verifier_epoch_rejected"`。
  期待 node は変わらず `test_non_e1_campaign_is_structured_and_wal_is_not_read` 1 件。
- **M2** (purpose を `CERTIFIED_ACCEPTANCE` へ戻す): 実際には 4 assert のいずれでもなく、
  実 callee 呼出し行で `CampaignVerifierEpochRejected` が未捕捉で出て node が error になる。
  期待 node は変わらず `test_v2_epoch_gate_is_historical_when_current_closure_is_unavailable` 1 件。

**erratum として残す (DW-M02)。凍結した期待 node 集合は変更しない。**
DW-O12 のとおり凍結は自分が直前に書いたものでも拘束するため、
期待 node を変えず散文の誤りだけを追記で訂正する。

### 所見 B-4: 新規 node が duration ledger に無い — real、nit、不採用

**親が実測して裏を取った:**

- G5 coverage は実 collection (`--collect-only orchestrator/tests`) の全 node を母集合とするため、
  新規 node 1 件は分子から外れる。ledger は 19,519 key、閾値は 90%。
  1 件では閾値を割らない。
- `orchestrator/tests/conftest.py` の `_acceptance_duration_for_item` は
  duration 不明を `None` で返し、`unknown_cost` に保守的な見積り値を当てて並べ替えるだけである。
  **fail-closed ではない。**受入全走を赤にしない。
- `test_t1574_changed_suite_ledger_node_delta_is_exact` の exact 対象 suite に
  `test_s1_report.py` は含まれない (レビュー B が確認)。

成果物影響は無い (certified 選択・report・台帳は不変、受入 scheduling の見積りだけ)。
DW-G05 により nit。ledger を手で編集するのは scope 外で、
かつ exact delta 検査の意味を壊しうるため行わない。

## fix 子の要否

**不要。** 採用した real 所見のうち実装面の変更を要するものは 0 件である。
B-1 は scope 外で裁定パッケージ送り、B-2 / B-4 は nit で不採用、
B-3 は親自身の裁定文書の erratum である。
したがって DW-S06-B の fix 投入は行わず、DW-S06-C の焦点再レビューも起動しない。

## 変異事前登録 (段 4 の 4 件を維持。erratum 付き)

| # | 変異 | 期待 | 期待 node (完全集合) |
|---|---|---|---|
| M1 | 局所 E0 `raise` を削除 | KILLED | `orchestrator/tests/test_s1_report.py::test_non_e1_campaign_is_structured_and_wal_is_not_read` |
| M2 | purpose を `CERTIFIED_ACCEPTANCE` へ戻す | KILLED | `orchestrator/tests/test_s1_report.py::test_v2_epoch_gate_is_historical_when_current_closure_is_unavailable` |
| M3 | 中央 gate 呼出しを削り `return recorded.diagnostic` | KILLED | `orchestrator/tests/test_s1_report.py::test_v2_epoch_gate_is_historical_when_current_closure_is_unavailable` |
| M4 | E0 で `ArtifactAdmissionError` を投げる | KILLED | `orchestrator/tests/test_s1_report.py::test_non_e1_campaign_is_structured_and_wal_is_not_read` |

erratum: M1 / M2 の「最初に赤になる assert」の散文は段 4 時点で不正確だった (所見 B-3)。
期待 node 集合は不変。
