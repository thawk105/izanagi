---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t541-t507-attestation
seq: 2
---

## {{D:attestation-reach-two-layer}}. 資格判定 attestation の受理集合を空から非空へ変える — 観測側 hash は parser を通し、判定条件は一切変えない

**決定 ([T-541] / [T-507] のユーザー裁定 = 択 (a) の実装):** 資格判定 (T126) driver の環境 attestation に
あった 2 層の型不整合を直し、成功経路を到達可能にする。**受理集合は「常に空」から「非空」へ変わる。**
D96 が課す手続 (新しい設計判断の記録 + 境界テストの同時更新) を本 D と
`test_t541_attest_*` が満たす。

**射程は次の 3 点だけである。**

1. 比較の expected を `verified.calibration.attestation_profile` にする
   (従来は `CalibrationV2` そのものを渡しており、必ず型エラーになっていた)。
2. 観測側 hash を、観測を `pegasus-probe-output/v2` の exact 4 key 文書へ落として既存
   `parse_probe_output` に通し、既存 `observed_profile_sha256` で求める形にする。
   比較の observed 側も同じ parser 復元値を見る。
3. 出力 envelope を `t126-qualification-attestation/v2` (exact 6 field) へ上げ、
   `observed_profile_projection_schema` を **parser の戻り値が持つ source schema から**記録する。

**変えないもの (絶対規律 2):** `_recorded_verdict`、`EFFECTIVE_CLOCK_TOLERANCE_PCT`、比較 field 集合、
全行 pass 要求、非空要求、共有 API の signature と意味、較正 artifact、contract registry。
広げたのは「**型が合えば比較が実行される**」ところまでであり、**通る条件は 1 つも緩めていない**。

**理由:**

- 成功経路が一度も到達できない保証は、恒真な保証の最も重い形である。資格試行が主張する環境同一性は、
  直すまで実データの裏づけを 1 件も持っていなかった。
- 観測側 hash に in-process 専用の関数を新設せず parser を通すのは、2026-08-05 の R-3 が定めた
  「projection version を呼出側の自由引数にせず、parser の戻り値が持つ source schema から導出する」を
  守るためである。**ただし driver が生成文書の版を選んでいることは事実であり、「parser が版を独立に
  発見する」とは書かない。** 守られているのは「hash 呼出し時に projection を自由選択する API を
  作らない」という禁止の方である。
- 実データでの到達を計算ノードで 1 回確認した (Request 861.nqsv、`status: accepted`、21 field 全 pass)。
  login node では同じ較正に対し 6 field が**正当に** fail する — 96 論理コア・SMT 有効の観測が
  48/48・SMT 無効の較正と一致しないためで、型の問題ではない。

**この D が主張しないこと:**

- **記録値の由来への感度は検証範囲外である。** `observed_profile_projection_schema` を
  `parsed.schema_version` から取るか同値の literal で書くかは、driver が生成文書の版を v2 に
  固定している現行経路では出力が変わらず、変異でも検出できない (段 6 のレビューが指摘し、親が
  事前登録を SURVIVED 期待へ訂正した)。実装は由来から取る形を維持するが、**保護されているとは
  数えない。**
- attempt evidence への保存、資格試行の完走、certified 選択の成立は含まない。T126 result は
  `evidence-only/no-promotion` であり、今回の到達をそこまで拡張して報告してはならない。
- 不一致で終わったときに field 別の内容が成果物へ残らない既存の欠落は直していない
  ({{T:attestation-mismatch-rows-not-persisted}})。

**却下した選択肢:**

- **in-process 専用の projection / hash 関数を足す** — parser 起点の既存経路とは別に schema 決定経路と
  canonicalization を増やし、R-3 の構造的な誤選択防止を弱める。
- **`ParsedProbeOutput` を直接構築する** — parser の形状検査を飛ばす。
- **`probe()` の戻り値型を変える** — 既存 consumer の契約へ波及する。
- **expected 型へ変換して既存 `profile_sha256` を使う** — 観測に存在しない tolerance を持ち込み、
  観測 projection の意味を変える。

**境界テストの形 (D96 の 2 点目):** 現挙動 (一致入力も型不整合で拒否する) を保存していた
`test_t452_attest_preserves_intentional_fail_closed_behavior` を、実比較・実 parser・実 hash を通す
受理／拒否の境界テストへ置き換えた。stub は較正読込みと probe の 2 つだけ (空比較の負例のみ
`compare_profiles` を差し替える)。観測 hash の期待値は入力 mapping から独立に算出する。
拒否側は governor 不一致・帯の端の直外・空比較・probe 例外を固定する。

**テスト入力の tolerance について:** 共有 fixture の `effective_clock.tolerance_pct` は 5.0 で、
現行 policy の 2.0 と一致しない。比較実装は両者の一致を要求するため、**この不一致だけで必ず落ち、
帯判定に到達しない**。境界テスト内で入力を policy 定数へ揃えた (literal は焼き込まない)。
判定条件は変えておらず、policy 外 tolerance を拒否する保護は `test_env_attestation.py` の既存
テストが引き続き固定している。共有 fixture 自体は変更していない。

**研究状態への影響:** 資格試行の環境同一性主張が、初めて実データの裏づけを持つ。
certified 選択・材料レポート・proof chain の値はこの wave では変わらない。
