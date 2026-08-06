# 段 1 brief — dev-wave token-hygiene (2026-08-06)

依頼 (ユーザー command 引数): 「トークン衛生チェック。claude, codex ともにトークンの使用ペースが
大きい。開発品質を落とさずにトークン消費量を減らせるところがあるかどうか調べて、良い施策が
あればやってほしい」。

## 段 0 実測 (完了、read-only、追加計測ゼロ、login ノード読み取りのみ)

期間 2026-08-01〜08-06 (6 日)。スクリプトは job dir の `analyze_*.py`。

| | claude | codex |
|---|---|---|
| 規模 | 101 セッション / 26,147 応答 | 937 子 |
| 入力 | 7,787 M | 4,027 M (95% cached) |
| 出力 | 15.6 M | 32 M (63% が reasoning) |

- 合計 11,860 M / 6 日。claude 66% : codex 34%。
- **claude の 入力:出力 = 500:1。平均 context 297,806 tok/応答、固定 base 中央値 46,641 tok。**
- **codex も同型**: 子あたり tool 呼び出し中央値 32 回、入力中央値 3.38 M
  → **1 tool 呼び出しあたり 105,774 tok**。
- 応答あたり tool_use は 1 個が 82.8%、2 個が 10.4%、平均 1.12 個。
- 蓄積内訳: tool_result 33.5% / thinking 26.8% / tool_use input 17.9% / text 2.0%。
- Bash 出力の 47% は出力を絞る指定なし。
- codex effort: max 527 本が入力の 63.2%、high 391 本が 36.7%。
  **max 中央値は high の 入力 2.02 倍・出力 2.05 倍・turn 1.44 倍。**
  原因は `docs/dev-wave/workers.md` DW-S02・DW-S03 の `reasoning=max` 明文規定 (grep 実測)。
  DW-S05-A は既に `high`、DW-S06-A は effort 無指定。

**構造的結論: コストは「往復回数 × その時点の文脈量」でほぼ決まる。生成量ではない。**
1 往復 ≈ 30 万 tok (claude) / 10.6 万 tok (codex 子)。

## scope

1. **`tools/token_report.py` を新設** — claude transcript と codex rollout から消費を実測する。
   以後「ペースが大きい」を数値で言えるようにする。純増で既存挙動を変えない。
2. **`docs/dev-wave/workers.md` の effort 規定を役割別に明示化し、親が実際に使った effort を
   worklog へ記録する契約を足す。** 引き下げはしない (下記 P1)。
3. **`CLAUDE.md`「作業の進め方」へ往復コストの換算率と 2 つの規律を足す** —
   独立確認は 1 応答に束ねる、Bash 出力には必ず上限を付ける。

**scope 外** (実装せず段 4 で裁定パッケージへ): 段 3 敵対レンズ・段 6 レビューの effort 引き下げ、
thinking 量の制御 (harness 側)、base の harness 部分、過去 transcript の圧縮、
worklog carry 行 (先行 wave `token-economy` で land 済み)。

## 不変条件 (緩めない)

1. **検出力を下げる方向の変更をしない。** 段 3 敵対レンズと段 6 レビューの effort・本数・
   レンズ多様性を減らさない。規律 2 (正しさゲートを緩める変異を許さない) の精神をトークン節約に
   適用させない。**「トークンが減った」を品質低下の言い訳にしない。**
2. **docs 予算を引き上げない。** 追加行は既存の陳腐化記述の削除で相殺するか、予算内に収める。
3. `tools/token_report.py` は read-only とし、transcript / rollout を書き換えない。
4. 計測は `requestId` で dedupe する。transcript は 1 応答を content block ごとに複数 record へ割り
   usage を複製するため、record 単位の集計は**2 倍の過大計上になる** (本 wave の段 0 で実際に誤り、
   自分で気づいて訂正した)。この罠をツールとテストに焼き込む。

## 成果物影響 (DW-G05)

certified 選択・材料レポート・試行台帳・proof chain の値と参照は**一切変わらない**。
本 wave は開発ループの資源消費だけに触る。実装しない場合、消費ペース (6 日で 11,860 M) は
測定手段のないまま継続し、effort 選択は根拠なく `max` に固定され続ける。

## 親の provisional 裁定 (攻撃対象)

- **(P1) `max` → `high` の一律引き下げはしない。** 実測が示したのは「max は 2.0 倍高い」であって
  「max が high より欠陥を多く見つける / 見つけない」ではない。検出力差は未測定であり、
  未測定のまま検出段を弱めるのは衛生ではなく当て推量である。代わりに effort を役割別に明示し
  使用値を記録して、以後 effort と must-fix 検出数を突き合わせられる形にする。
- **(P2) 段 2 プラン起草だけは `high` を既定にしてよい。** 起草物は段 3 レンズと段 6 レビューが
  必ず攻撃するため、弱い起草は下流で検出される。**ただし弱い起草が fix 巡回を増やして
  かえって高くつく可能性があり、これは段 3 のレンズに攻撃させる。**
- **(P3) 本 wave は軽量版にしない。** workers.md は検出力の契約であり、
  段 3 敵対 1 本と段 6 レビュー 1 本は省かない。ただし節約 wave 自身が浪費しないよう
  段 2 起草は省き、親 brief を直接レンズへ渡す。

## 成果物の形

`tools/token_report.py` + `orchestrator/tests/test_token_report.py`、`docs/dev-wave/workers.md` と
`CLAUDE.md` の追随、変異 matrix、受入全走、spool fragment (worklog / decisions)。

## 並列分割方針

実装面は 1 所有単位 (`tools/token_report.py` とそのテスト) で分割しない。
docs は親が書く。段 3 レンズ 1 本と段 6 レビュー 1 本だけ codex へ出す。
