# 段 1 brief — [T-941] P6 意味的充足契約の機械実装 (第 1 単位) + [T-942] V-12

## 確定済みユーザー裁定 (逐語は `rulings-verbatim.md`)

- [T-941] は「P2・裁定済み → 起動可」(`docs/archive/worklog-phase3-0902-1184.md:129-131`)。P6 の機械実装と認定は本 task の所有。
- [T-942] V-12 (材料レポート renderer の結線) は「P6 実装 wave へ同梱」で確定 (`docs/archive/worklog-phase3-0813-516.md:633-635`)。
- 契約の規範は D156 (`docs/decisions.md:7742`)。本文の正本は `output/insights/2026-08-04_t433-p6-sufficiency-contract/README.md`、設計の正本は `output/insights/2026-08-03_t244-p6-contract/README.md`。
- cap-lift 自体の実施と off アームの予算は本 wave の外。8c の schedule 正本 (T-2159) は触らない。

## 親の前提実測 (brief 前に実行した)

- `derive_p6_cut` / `PrecommittedHypothesis` / `P6Derived` は repo に不在。`orchestrator/tests/test_reflux_formal_consumer.py:920-921` が `reflux_formal_consumer.py` 内での定義不在を **pin している**。本 wave はこの pin を外さない (新規 module 側に置く)。
- **生きた呼び手が実在する**: `orchestrator/campaign/reflux_formal_consumer.py:1033-1043` が条件 8 を `P6Unavailable` で fail-closed にして terminal を返す。`FormalConsumerResult` は 2 値のみ (`:259`)。
- **中心的欠陥 (本 wave の主目的)**: 同 `:833-841` の `_validate_wal_outcomes` は、terminal abort の `candidate_attributable` / `truncated` / `witness_class_sha256s` を **ordered-WAL projection の自己申告 field としてそのまま信じ**、`witness_class_sha256s == [physical["constraint_sha256"]]` という**自己申告どうしの照合**しか行わない。fixture (`orchestrator/tests/reflux_origin_fixture_builder.py:353-360`) がこの 3 field を定数で書いている。witness から class を導く信頼された計算機は存在しない。
- DW-O09 pin 閉包: `test_frozen_artifacts.py` の `FROZEN_MANIFEST` 23 key に layer3 も reflux も無い。layer3 は `layer3_schema.json` への**構造 pin** が 3 箇所 (`test_layer3_report.py:866,1369` / `test_s8b_oracle_driver.py:5034`)。凍結 bytes の pin は無い。
- 稼働 wave との編集面重複 (40 worktree の未 commit 差分まで走査): T-2191 が `orchestrator/verifier/{core,dsg,parse}.py` と `test_verifier.py`、T-524 が `test_reflux_origin_binding.py` と `test_reflux_originless_compatibility.py`。**この 6 ファイルは本 wave の編集禁止面**。`reflux_*.py` 本体と `layer3_report.py` は誰も触っていない。

## scope — 実装するもの

**単位 1 (P6 witness 層 = 信頼された評価器)。** 契約 SC-01 / SC-02 / SC-03a / SC-03b / SC-03c / SC-03d を機械化する。

1. 構造化 witness の閉じた和 — `CycleWitness` (非切詰め・integrity clean・`verdict="non-serializable"`) ∪ `IntegrityWitness` 3 種 (`lock_coverage` / `write_intent` / `permutation`)。未知 kind は `P6ContractError(unknown-witness-kind)` で fail-closed。環境起因の失敗からは発火しない。**(P3) の実測に従う分担**: `permutation` は既存 `permutation_violation_details` から構造化し、`sample` 打ち切り (5 件上限) に当たる証拠は `witness-truncated` にする。`lock_coverage` / `write_intent` は本 wave では構造化せず、**既知 kind として認識したうえで fail-closed** にする (無視して素通りさせない — 設計 §3.2.2 の回避阻止はこの認識で保つ)。
2. 正規化器 — 設計 §3.3 の 8 規則 (内部整合 / rotation 辞書式最小・辺方向は同一視しない / txid 破棄・位置保存 / key 分割の保存 / version 等値関係と genesis 判別の保存 / reason 正準ソートと重複件数保存 / `phenomenon` の再導出照合 / `edges[].types` は検査のみ)。切詰め witness は `witness-truncated` で拒否。複数 anomaly は class-set 規則で全件処理し、単数へ黙って畳まない。
3. **出所の移動 (本 wave の成果物影響)** — `_validate_wal_outcomes` が `candidate_attributable` / `truncated` / `witness_class_sha256s` を自己申告として読むのをやめ、構造化 witness から再計算した値と照合する。申告と導出が食い違う ordered-WAL projection は FC07 で拒否する。
4. SC-01 の attempt 束縛 — `verify_done` payload に `build_attempt_id` が無い実測 (設計 §3.2.1) に従い `build_start`/`abort` の区間一意性で束縛し、非一意なら `ambiguous-wal-binding`。`records_by_stage()` は last-wins なので使わない。

**単位 2 (V-12)。** `docs/phase3-8c-wiring-design.md:646`「材料レポート renderer は現在 WAL と whiteboard しか読まず、ledger も result-evidence も読まない」を閉じる。`reflux_origin_ledger` と `reflux_result_evidence` を読む結線と、V-10 裁定が課した保証限界の明記。

## scope 外 (実装しない。名乗らない)

帰納段 (SC-04 `PrecommittedHypothesis` / SC-05 `marginal_keys` / SC-06 反証 seal)、admission 結線 (SC-12)、全入口 inventory (SC-08b)、認定手続 (SC-10 / SC-11 / §5 認定 request / §7 attestation / §8 認定記録)、`derive_p6_cut` 本体、cap-lift 結線、`MAX_APPROVED_GENERATIONS` の変更。**したがって P6 の状態は `NOT_IMPLEMENTED` のままであり、本 wave は認定・`NOT_CLAIMED`・cap-lift のいずれも主張しない。** 仮想リスク向けの gate・検査・台帳・一般化を足さない。

## 不変条件

- 規律 2 を緩めない。設計 §3.6 の固定条項「禁止集合に含まれない候補も各 query ごとに通常の verifier を必ず通す」に触れる変更を入れない。
- 4 値結果型を二値化しない。`NOT_IMPLEMENTED` / `NOT_CLAIMED` は状態語であって 4 値結果ではない (契約 §1)。
- `test_reflux_formal_consumer.py:920-921` の pin を弱めない。
- 編集禁止面 6 ファイル (上記) を触らない。`orchestrator/verifier/` は読むだけ。
- 受理集合の変更は D96 手続に従って「新たに拒否する群」を列挙する。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1)** 「出所の移動」だけで DW-G05 の成果物影響を満たす、という親の判断。反対仮説 = 帰納段と admission 結線が無い限り受理集合は実質変わらず、単位 1 は「呼び手の無い部品」(T-434 前 wave が撤退した欠陥型) と同型である。
- **(P2)** V-12 を `layer3_report.py` 本体でなく**独立の reader/verifier module** として実装すれば [T-326] の裁定 (b)「本体の深い一致強化は実施しない。強化は新 verifier 経由だけ」(`docs/phase3.md:591`) と両立する、という親の読み。反対仮説 = 新入力の追加自体が本体改変であり (a) の再裁定が要る。
- **(P3) — brief 前の実測で部分否定済み。裁定を scope へ反映した。** 実測: (i) `permutation` は既に構造化されている (`orchestrator/verifier/model.py:152` `permutation_violation_details` / `report.py:72-92`)。ただし `sample` が 5 件で打ち切られるため 6 件目以降は**構造上つねに切詰め**であり、契約 SC-03d により `witness-truncated` に落ちる。(ii) `lock_coverage_violations` / `write_intent_violations` は整数のみで、構造化には `orchestrator/verifier/{core,parse}.py` の変更が要る = **T-2191 の編集面**。よって本 wave はこの 2 種を構造化しない。残る (P3) = 「構造化しないまま、閉じた和の discriminator だけで §3.2.2 の回避阻止 (失敗を cycle channel から integrity channel へ移す) を実際に塞げるか」。
- **(P4)** 本 wave の 2 単位が 1 wave に収まる、という親の見積り。

## 成果物の形

新規 module (P6 witness 層) + `reflux_formal_consumer.py` の結線 + calibration corpus (契約 §4 の C-01 / C-02 / C-02b〜C-02e / C-06 / C-07 / C-08 / C-09 / C-10L/W/P) + 変異事前登録表 (conjunct 単位、契約 §6) + V-12 結線 + insight 1 本 + worklog 1 エントリ。

## 並列分割

- 子 A = 単位 1 全部 (witness 型・正規化器・consumer 結線・calibration)。producer/consumer 契約が単位を跨ぐので **1 子に持たせる**。
- 子 B = 単位 2 (V-12)。編集面が `layer3_report.py` 周辺で独立。

## 受入・実測環境

ベンチ実測なし。受入は login node での全走 (§7.0.0 の既定自動判定に従う)。計測機固有情報は runbook 側。
