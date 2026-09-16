---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t2125-historical-policy-version
seq: 2
---

## {{D:historical-policy-recorded-comparison}}. 歴史閲覧は記録 policy と照合し、記録側へ向ける比較は policy SHA と stock pin の 2 つに限る

**決定:** `CampaignReadPurpose.HISTORICAL_RAW` で v2 campaign を読むときだけ、campaign lock に記録された
build admission policy を別型 (`HistoricalBuildAdmissionPolicy`) の専用 decoder で読み、現行 policy との
一致は要求しない。記録側へ向ける比較は、build receipt の `policy_sha256` と stock class の
source commit (`repo_stock_pin`) の **2 つだけ**とする。generator 登録・review 登録・coder authority の
照合は現行の登録簿と literal のまま残す。診断は `classification="historical-policy-version"` に出し、
`admission_status` は既存の `historical-not-reclassified` を再利用する。epoch は変えない。
`CERTIFIED_ACCEPTANCE` は従来どおり現行 policy との一致を要求する。

**理由:**
- 照合が purpose 分岐より手前にあり、policy の版が上がると過去の v2 campaign を purpose を問わず
  読めなくしていた。D1653 / D1770 が decoder 層で、D1841 が認証 attempt 層で同型の問題を
  「記録どおりに読む」方向で解いており、本決定は policy 層の同型である。
- 5 つの比較すべてを記録側へ向けると、外部の登録簿・authority との照合が自己申告の整合確認へ
  変わる。実測された版上げ事象は `CURRENT_PIN` の前進 (`fb5e74a17`、2026-08-12) だけであり、
  registry への member 追加では receipt が指す ID は現行 enum に残るので現行照合を通る。
  **registry と authority を現行照合のまま残せば、偽造 policy が架空 generator / authority を
  名乗っても現行の登録簿が拒否する。**
- 既存 status を再利用すると、`layer3_report.py` と `autonomous_trial_completeness.py` の
  certifying 条件 (`admission_status == "admitted"`) を構造的に満たさない。`layer3_schema.json` は
  classification enum を広げる代わりに `certifying_input=true` 側を従来 2 値に制限して相殺する。
- 歴史閲覧で成立する保証は「記録 policy と記録 receipt の内的整合」までであり、記録値が当時
  実在した policy だったことは保証しない。この限界は classification と
  `current_verifier_conformance = "unknown"` (D1365) で表に出す。

**却下した選択肢:**
- **5 つの比較すべてを記録側へ向ける (段 2 plan の案)** — 外部照合が自己申告へ落ちる。
  registry 削除・authority 変更は未実測の事象で、`DW-G05` の仮想リスクに当たる。
- **歴史閲覧では policy 照合そのものを外す** (`s8b_binary_admission.validate_portable_binary_record` の
  `expected_policy=None` と同型) — lock と WAL の receipt が同じ policy に束縛されているという
  内的整合まで失う。
- **識別子を epoch の `reason_code` に足す** — D1365 が記録 epoch の reason enum と certified 側の
  `current-closure-unavailable` を変えないと定めている。policy 差は verifier closure の理由でもない。
- **`BuildAdmissionPolicy` の subclass にする** — `wal.py` の exact 型検査を通らず、別入口・別返却型を
  求める D1653 の条件にも反する。

**残余:** registry からの member 削除・改名、`_AUTHORITY_KIND` / `POLICY_SCHEMA` literal の変更が
起きると歴史閲覧はまた塞がる。いずれも実測されていない事象であり、本決定では扱わない。
