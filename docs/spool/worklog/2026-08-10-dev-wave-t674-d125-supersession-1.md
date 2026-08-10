---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-10
wave: dev-wave-t674-d125-supersession
seq: 1
title: [T-674] の残余 (5) を消化し D125 決定 (2) の campaign id 不変条項を前向きに失効させた — 破ったのは本 wave ではなく land 済み production が 3 世代で 3 回 (docs のみ、実装差分なし、branch worktree-dev-wave-t674-d125-supersession)
---

## 本文

- **ユーザー裁定 (2026-08-09 /rulings、archive worklog エントリ 337) の [T-674] 6 問のうち、
  残余 (5) だけを消化する docs-only wave。** (1)(4)(6) は [T-671] 実装 wave (エントリ 355、
  D259 決定 8・9) で消化済み、(2)(3) は防御的堅牢化として見送り済みである。
  本 wave で 6 問すべてが決着した。設計は {{D:d125-campaign-id-invariance-superseded}}。
- **段 4 で `4→7→8→9` へ分岐し、子を 1 本も起動しなかった。** 判断の根拠を残す —
  (a) 設計択一が割れない (前向き supersession という方式はユーザー裁定が確定させており、
  D125 決定 (2) を分割してよいかは D259 決定 7 が「`measurement_env` は identity に残す」と
  既に確定させている)、(b) 正しさ防壁に触れない、(c) コードを 1 byte も編集しないので
  受理集合が変わらない。ユーザーの依頼も軽量 wave を明示していた。
- **親が段 1 で裁定前提を実測し、裁定文の読みを 1 点狭めた。** 起票文と t530 実装 wave の記録は
  「[T-343] が既に破っている」と**単発の違反**として書くが、実測では pre-T343 → T-343 → T-530 →
  [T-671] の**3 世代で 3 回**変化していた。しかも [T-671] (D259 決定 1) が契約 hash を pre-image から
  外した結果、現行値は T-530 値ではなく T-343 値へ**戻って**いる。したがって正確な記述は
  「[T-343] が破った」ではなく「**不変を保つ機構が最初から存在しない**」であり、新 D はこの形で書いた。
  裁定の方向 (前向き supersession で記録する) は変えていないので、`DW-S04` の「未見の新事実」には
  当たらないと裁定した。
- **実測は 5 点すべて一次資料から取った (F1)。** (i) `measurement_env` の実装実在と site 射影、
  (ii) 現行 OTHER id を T-343 値へ等号 pin し T-530 値へ非等号 pin する test 定数 6 本、
  (iii) `output/campaigns/` の 30 campaign・30 lock、(iv) pre-T343 値の dir が 1・現行値の dir が 0・
  T-530 値の dir が 0、(v) `discover_campaign_dir` が dir 名 prefix の glob で id 非依存であること。
  既存 docs の記述は (ii)(iv) を裏取りするまで根拠にしていない。
- **変異 matrix は免除した。** 実装差分ゼロ (コード・テスト・script いずれも 0 byte) で、
  変異させる対象が存在しない。`DW-S04` の免除条件に合致する。
- **受入要否の判定証拠 ([T-648] fallback 義務)**: 本 wave は docs-only・実装差分ゼロだが、
  **実 repo を読むテストは存在する**。判定手順 = `orchestrator/tests/` から実 checkout の `docs/` を
  読むテストを名指しで探し、`test_check_docs.py` と `test_spool_fold.py` の 2 file が該当
  (他は不存在)。したがって受入全走を免除せず実施した。

## 次の一手差分

### 完了

- [T-674] 残余 (5) を消化した。D125 決定 (2) の「OTHER の campaign_id は 1 bit も変えない」は
  {{D:d125-campaign-id-invariance-superseded}} で前向きに失効させ、env による identity 分離
  (D259 決定 7) だけを残した。(1)(4)(6) は [T-671] 実装 wave (D259 決定 8・9) で、(2)(3) は
  見送りで決着済みであり、6 問すべてが終端した。
  remaining: none
  base: a81cc2a17c416746c28b7bf248bfe02220f226c6b5516b7cccef78089cc84857
