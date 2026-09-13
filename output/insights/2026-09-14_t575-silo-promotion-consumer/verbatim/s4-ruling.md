# 段 4 裁定 — [T-575]

基準 commit: `75bea8e5f` (段 4 直前に local main 再確認、乖離なし)。
裁定 inbox (`docs/handoff/`) 再走査: 残ファイルは T-1998 の中断 handoff 1 件のみ。本 wave と無関係。

## 結論

**silo 昇格を実行する consumer は、確認した静的参照閉包に存在しない。**
ただし無限定の不存在保証はしない。判定対象は **「silo ladder の characterization 証拠を、
研究目標・回復計測・通常 pipeline の適格性へ昇格させる consumer」** に限定する。

証拠の検査・発行を行う consumer (`orchestrator/campaign/silo_ladder_rung1.py` の `collect`) は
実在し、Python 以前に書く shell/PBS writer も実在する。これらは昇格ではない。

### 親が独立に検算した実測 (子の所見に依存しない)

- `orchestrator/campaign/silo_ladder_rung1.py:4959-4962` — 発行 document の `classification` は
  `evaluation_role="ability_probe"` / `research_goal_eligible=False` /
  `recovery_measurement_eligibility=False` を**リテラルで固定**する。producer に適格な成果物を
  出す枝が無い。
- `orchestrator/campaign/silo_ladder_rung1_contract.py:518` — `len(entries) != 1` を違反として
  記録する。ledger は exact-one である。
- `orchestrator/campaign/condition_meaning_gate.py:3478-3480` —
  `_PROMOTION_USE_CLASSES = {"certified-selection", "floor", "oracle", "paper"}`。
  repo 自身の語彙で「昇格用途」はこの 4 つであり、silo は含まれない。
- `orchestrator/campaign/silo_ladder_rung1.py:2236-2237` — ladder driver は
  `use_class="raw-measurement"` を渡す。これは `_RAW_USE_CLASSES` 側である。
- production の昇格用途 call site は `orchestrator/campaign/s8b_oracle_n_pilot.py:1025`
  (`use_class="oracle"`) のみ (親が `rg -n "use_class\s*=" orchestrator tools` で実測)。

## 所見の裁定

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| A1 | レンズ A | `collect` の受理・公開が実質的な昇格である | refuted | 不採用 (反例にならない) |
| A2 | レンズ A | Python 外の writer が昇格 consumer の反例になる | refuted | 不採用 |
| A3 | レンズ A | alias・辞書 dispatch・test 差替えから昇格へ到達する | refuted | 不採用 |
| B1 | レンズ A | 段 2 が `output/**` を丸ごと探索から落とした根拠がない | real | **採用** — 記録に探索範囲を明記 |
| B2 | レンズ A | shell 経路を「検索した」と「閉じた」が区別されていない | real | **採用** — 実在 writer を記録に明記 |
| B3 | レンズ A | 段 2 の `ability_probe` 批判が親 brief への誤帰属 | real | **採用** — 親 prompt の誤りとして handoff に残す |
| C1 | レンズ A | 完全一致 0 件から意味的訂正対象 0 件は導けない | real | **採用** |
| C2 | レンズ A | 除外は「昇格用途」に限定しないと書込み入口の過少計上になる | real | **採用** — D 本文で射程を限定 |
| C2' | レンズ A | D196 の保留理由をそのまま現在の blocker として再掲するな | real | **採用** — 記録で blocker の現状を断定しない |
| 1 | レンズ B | `patches/README.md` の「新 rung は登録必須」に exact-one の限定が欠ける | real | **採用 (scope 内・局所修正)** |
| 2 | レンズ B | 他の必須文書に適格性の過大宣言は無い | refuted | 不採用 (訂正しない) |
| 3 | レンズ B | `output/**` 一括凍結扱いは不当。ただし昇格誤記は 0 件 | real | **採用** — 探索範囲の記録のみ |
| 4 | レンズ B | 「不在/実在」の並記は射程を失わせる。記録は 1 文に固定せよ | real | **採用** |
| 5 | レンズ B | 既存 decisions への限定追記は禁止された台帳新設ではない | refuted | 採用 (scope 内と確認) |
| 6 | レンズ B | D162 決定 (7) だけでは T-575 解決済みと言えない | refuted | 採用 (射程差を記録) |
| 7 | レンズ B | 訂正対象 0 件は過小。1 件・2 箇所へ修正 | real | **採用** |
| 8 | レンズ B | `docs/phase3.md` に T-575 の記述は無い | refuted | 不採用 (訂正対象ではない) |

## scope の確定

- **scope 内:** (a) 判定の canonical 記録 (decisions fragment 1 本)、(b) `patches/README.md` の
  登録手順への限定追記 2 箇所、(c) worklog fragment (T-575 を完了)、(d) insight への逐語凍結。
- **scope 外 (実装しない):** 新しい gate・検査・registry・適格性 sidecar・入口登録制度・
  恒久監査・一般化。活性化権限そのものの実装 (D196 / D215 で保留中)。
  凍結記録 (`docs/archive/**`、`output/insights/**`、`patches/ledger.json`、
  `output/env/pegasus/**`) の bytes 変更。

## レンズ B 所見 1 を scope 内とする理由

依頼の逐語は「『silo 昇格入口』という語を使う全箇所を訂正する」である。所見 1 の対象は
その語そのものではない。しかし `patches/README.md:465` の「新 rung は登録必須」は、
**梯子へ新しい rung を入れる登録入口が現行契約に在るかのように読める**唯一の現行記述であり、
本 wave が確定する命題 (入口の不在) と同じ面にある。実際には
`silo_ladder_rung1_contract.py:518` が entry 数を 1 に固定しており、2 本目の rung を
登録すると契約検査が違反を記録する。追記は 1 節の限定句だけで、gate・検査・台帳を増やさない。
したがって仮想リスク向けの追加ではなく、本題の局所修正として採用する。

## 変異事前登録

**免除。** 実装面 (D95 決定 2 = 非 Markdown) の差分がゼロである。本 wave の変更は
`docs/spool/**` の fragment と `patches/README.md` (Markdown) と `output/insights/**` の
新規 insight だけで、Python・shell・C/C++・CMake・patch/diff を 1 byte も変えない。
受入全走は免除しない。

## 段の進め方

- 段 5 (Codex 実装子): **なし。** D95 決定 (1) の「docs-only は親が本文を直接編集でき、子ゼロでよい」
  に従う。
- 段 6: 書いた D 本文と README 追記に対する敵対レビュー 1 本を read-only codex で回す。
  過大主張 (無限定の不存在保証) が入っていないかを焦点にする。
- 段 7: 記録。段 8: 自己改善。段 9: land。

## 記録する 1 文 (D の決定行)

> 基準 commit `75bea8e5f` で確認した静的参照閉包では、silo ladder の characterization 証拠を
> 検査・発行する consumer は実在するが、その証拠を研究目標・回復計測・通常 pipeline の適格性へ
> 昇格させる consumer は存在しない。したがって活性化権限の入口集合に「silo 昇格入口」を数えず、
> ability probe の writer を結線して昇格入口を守ったと報告しない。
