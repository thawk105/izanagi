# 段 6 裁定 — レビュー 2 本 + 親所見

レビュー A (正しさ境界) と B (波及・互換・裁定対応) はいずれも rc=0、`check_codex_output.py` 緑。
**両者とも「今回の差分による `CERTIFIED_ACCEPTANCE` の受理集合拡大」「schema 禁止条件の不発」
「scope 逸脱」「変異位置の消失」は無い**と独立に判定した。

## must-fix

### PF-01 (親所見、blocker) — 保存済み Layer 3 report が再構築と一致しなくなった

**どちらのレビューも指摘していない。** 親が B-09 (焦点走の漏れ) を追跡して実測した。

`autonomous_trial_completeness.py` は保存済み report と `build_report` の再構築を
`_canonical_bytes` で byte 比較し、不一致なら
`_fail("campaign-chain", "persisted layer3 report differs from fresh rebuild")` で落とす。
段 5 で `build_report` が top-level `current_verifier_conformance` を出すようになったため、
**同 field を持たない保存済み report は必ず食い違う。**

**親の実測:** `output/campaigns/` 配下の保存済み `layer3_report.json` は 7 件。
先頭 1 件の top-level key を列挙したところ 15 key で、`current_verifier_conformance` は無い
(v2 形式で `admission_decision` も `campaign_verifier_epoch` も持たない)。7 件とも同 field の
出現回数は 0。

**成果物影響:** 過去の自律試行 chain が、現行コードとの差だけを理由に無効化される。
**本 wave が防ごうとしている絶対規律 7 の違反そのものを実装が作り込んだ。**

**この型はテストだけでは見えない。** テスト内で保存済み report を `build_report` で作れば
両側に新 field が付き緑になる。実成果物だけが壊れる。

**直し方:** 同 file に既にある legacy omission の正規化 (`include_epoch` /
`include_verifier_assessment_basis`) と**同型**の flag を 1 つ増やす。保存済み側に無ければ
両側から落とし、**有れば従来どおり厳密に比較する** (受理を広げない)。
保存済み report へ field を書き足して通す「修正」は禁止 (過去の成果物の改竄)。

### PF-02 (= B-07) — certified の正例と schema 負例が同一 node に同居

`test_certified_report_omits_and_schema_forbids_current_verifier_conformance` が
(1) 本物の certified report に field が無い (producer liveness) と
(2) 注入すると schema が拒否する (consumer fail-closed) を 1 node に詰めている。
事前登録した **L1 と C2 が同じ node を赤にする**ため、変異の帰属が一意でない (DW-M03/M04)。
→ 2 node に分割する。

### PF-03 (= T-02) — 既定値付き `pop` が field の実在を要求していない

`layer3_report.py` の certified 昇格が `report.pop("current_verifier_conformance", None)` で、
歴史側の投影が消えても素通りする。`build_accepted_report` は必ず `build_report` を通るため
field は常に存在する。既定値なしの形にして、除去処理の存在証明と D2 / L1 の帰属を鋭くする。

## 採用しない (記録する)

| ID | 出所 | 判定 | 扱い |
|---|---|---|---|
| A-02 | レビュー A | real | `require_persisted_certified_commit` の loop は COMMIT 0 件で空回りし、COMMIT 証拠のない campaign へ certified view が出る。**今回の差分が導入したものではない。** scope 外 → 裁定パッケージ RP-4。 |
| A-03 | レビュー A | real | module global token による exact view 偽造。**D1252 が既に裁定済み**で新事実ではない。再提起しない。 |
| T-01 | レビュー A | real | 新規 6 node のうち構造回帰・dirty certified 負例・certified schema node の 3 つは**旧実装でも通る**。段 4 の P-01 裁定と整合する。**worklog に正直に書く** — これらは回帰 pin であって D1245 実装の存在証明ではない。存在を証明するのは (b) 表示・(d) 投影・(e) 保存済み互換の 3 node と、変異 D1/D2/C1/C2。 |
| D-01 | レビュー A | real | property が定数のため、現行閉包が clean でも表示は unknown であり「現在適合している」の肯定表示はできない。**段 4 の P-03 で明示的に受容済み。** |
| E-01 | レビュー A + 親 | real | `test_existing_certifying_v3_missing_epoch_remains_readable` に `del` 行が 1 つ足された。**期待値・assert・raises は不変**で、手作りの certifying report から producer が出さない field を外すための fixture 調整である。許容し、記録する。**実装子の完了報告の「既存テストを一つも変更していない」は不正確** — 追加のみだが既存 test の本文は変わっている。 |
| B-09 | レビュー B | real | 焦点走の漏れ。**親が §4 で焦点集合を拡張する** (コード変更なし)。 |
| A-01 / E-02 / M-01 / S-01 / O-01 / B-01〜B-06 / B-08 | 両レビュー | refuted | 受理集合不変、nested epoch と S-1 投影不変、変異 7 位置は全て健在、schema 禁止は実効、scope 逸脱なし、保存済み受理集合は縮小せず、oracle 契約不変、表示は実バイトへ到達、裁定 §2 は過不足なし。 |

## 裁定パッケージ追加

### RP-4. COMMIT 0 件の campaign へ certified view が出る (A-02)

`_require_admitted_campaign` の certified 分岐は全 COMMIT record に
`require_persisted_certified_commit` を掛けるが、**COMMIT が 1 件も無い campaign では loop が
空回りし、証拠なしで view が発行される。** 既存テストもこの受理を要求している。
本 wave の差分が導入したものではなく、受理集合を縮小する変更は D1246 の共通 admission helper と
既存 consumer の全数に触れるため、単独の裁定を要する。親の推奨: 別 T として起票する。

## 変異事前登録の更新

段 4 の 7 変異はレビュー A が独立に「位置と old 逐語がすべて存在」と確認し、親も実装後の
コードから 7 件すべての一意性を機械で再検証した (`mutation-spec-probe.json`)。
**fix 後に anchor を取り直す** (PF-02 で node 名が変わり、PF-03 で L1 の old 逐語が変わるため)。
帰属は次のとおり固定する。

- L1 → 分割後の producer liveness node だけ
- C2 → 分割後の consumer fail-closed node だけ
- D2 → 歴史 report 投影 node
- 新規: PF-01 の回帰テスト node は、正規化 flag を落とす変異で赤になること

## 焦点走の拡張 (B-09)

段 4 §6 の 12 file に次を加える。

- `orchestrator/tests/test_autonomous_trial_completeness.py` (PF-01 の変更面)
- `orchestrator/tests/test_trial_registry.py`
- `orchestrator/tests/test_t126_qualification_artifacts.py`
- `orchestrator/tests/test_official_perf_closure.py`
- `orchestrator/tests/test_s1_known_axes_freeze.py`
- `orchestrator/tests/test_s8b_oracle_driver.py`
