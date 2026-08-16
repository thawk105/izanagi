# 焦点再レビュー後の親裁定 ([T-523])

`DW-O16` の fix 3 巡上限に到達。以降は親が real/refuted を裁定して閉じる。

## 対応表の受領

review_a 1-8 / review_b 1-8 の 16 件: **closed 9 / partial 7**。
partial 7 件のうち 5 件は下記「新所見」と同一原因、2 件 (spawn meta-test の認識 API 限定) は
`DW-G05` により nit へ降格 (成果物の値・受理集合・参照は変わらない。検出力の限界を
meta-test の主張文言側で既に狭めてある)。

## 新所見 5 件の裁定

### N1. private receipt creator から台帳無しで token を発行できる — **real / 修正しない**

`_new_durable_attempt_consumption_receipt()` と
`_issue_holdout_observation_admission_from_receipt()` は private だが、import 権限を持つ
caller は直接呼べる。issuer 側で durable marker を検証しても、marker path と root を
caller が供給する以上、偽造は閉じない (中立 leaf は canonical root を知らない。
知らせれば層反転)。**Python ではこの境界を機構的に封じられない。**

**裁定:** 実装では閉じない。**保証の縮小として「主張しないこと」の 5 項目目に明記する** —
「private Python API を直接 import できる caller に対する保護は主張しない」。
D・worklog・module docstring の三箇所へ書く。

### N2. private core の外部 measure が publishable artifact を作れる — **real / scope 外**

`_run_campaign_core(..., measure_fn=attacker)` は attempt marker を 1 件消費しつつ、
callback 内で任意回数 spawn して選別値を `result.json` に載せられる。

**裁定:** N1 と同じ private-API 経路だが、**publishable artifact を作れる点でより重い**。
閉じるには publish 経路と注入可能 harness の分離という構造変更が要り、本 wave の
3 巡上限を超える。**裁定パッケージへ返し、次タスクとして起票する。**

### N3. pilot 承認 flag が標準 PBS wrapper へ結線されていない — **real / scope 外 (運用裁定)**

`tools/pegasus/floor_campaign.sh` は承認 flag を渡さないため、標準投入経路から
pilot を起動できない。**これは安全側の拒否であり、無条件付与は採らない。**
承認を誰がどう与え、どこに記録するかは運用の設計判断である。

**現時点の実害はゼロ** (floor run の実績は 0 件、[T-527] により正式 H1/H2 は
projection 不在でそもそも起動できない)。**裁定パッケージへ返す。**

### N4. claim 後にも失敗しうる非計測処理が残り、docstring が実体より強い — **real / 限定 fix**

claim は `runner.run()` の直前へ移ったが、`_validate_live_admissions` /
host provenance / process identity は `runner.run()` 内で claim より後に走る。
そこで失敗すると journal 不在のまま 12 cell の鍵が焼ける。
かつ docstring は「全ての非計測 preflight 後」と書いており、**実体より強い**。

**裁定:** **「謳っているのに発火しない保証」を land しない。**
変異走行の完了後に、(a) docstring を実体へ合わせる、(b) 可能なら claim をこれらの検査より
後へ移す、の 2 点だけを対象にした限定 fix を 1 本入れる。
**敵対レビューの再巡は行わない** (3 巡上限の趣旨を守る)。親がテストと変異で裏取りする。

### N5. `_profile_run` 自体は無防備 — **real / 修正しない (N1 と同型)**

`profile_point` は保護比率を拒否するが、private の `_profile_run` は直接呼べる。
N1 と同じ private-API 経路。**N1 の 5 項目目の明記でカバーする。**
ただし spawn meta-test の allowlist 根拠コメントは「public 入口が拒否する」であって
「private helper も拒否する」ではないことを確認済み — 過剰主張はしていない。

### 既存テストの弱体化について

焦点レビューは反転・緩和・skip・削除・xfail を **1 件も検出していない**。
`test_s8b_freeze_io.py` の合成 fixture が rr80/rr20 になっている件は
**should** であり、本 wave では直さない (主 fixture の rr79/rr23 は維持されている)。
次タスクへ起票する。

## 本 wave が主張しないこと (最終形。D と worklog に書く)

1. 台帳無しの result を下流 verifier / ratified closure / report が拒否すること。
2. 直接 `subprocess.run` する将来の producer の機械的封鎖 (meta-test は検出であって封鎖ではなく、
   認識する起動 API は限定表である)。
3. 未 commit ledger の削除に対する保護。
4. 独立 clone 間の一回性 (共有するのは 1 repository の worktree 群まで)。
5. **private Python API を直接 import できる caller に対する保護** (N1 / N2 / N5)。
