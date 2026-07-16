# workload-aware selection のリーク制御 — 「値」でなく「来歴」で遮断した一次事例

- 日付: 2026-07-16
- 記録種別: 設計判断の一次事例 (探索の妥当性文書)。**有効性実証ではない** — selector は未実走で、
  §9 再凍結 draft の承認待ち
- 正本: `docs/phase3-8b-descriptor-design.md` §9 項 2、worklog 2026-07-16 (5) 素材、D47 決定 1

## 事例

8b selector 実験の設計裁定で、selector-visible なカタログから holdout freeze の
`variant_binding` 生フィールド (flags・backoff 値・comparator・gate 述語・sources パス) を
全遮断し、渡すのは固定 6 件の `{choice_id: c01..c06, mechanism: 制御語彙}` のみとした。

判定基準が新規性を持つ: 遮断対象を「勝ち筋の実測値そのもの」に限定せず、**値の lineage が
性能結果由来かどうか**で決めた。variant_binding の生値は個々には中立に見えるが、その構成が
既知 workload の argmax 由来である (= 選抜という形で性能情報を運ぶ) ため遮断。`sources` パスは
anchor workload 名を直接含むため遮断。ID→構成の解決は信頼中核だけが予測**後**に行う。

## 一般化仮説 (未検証)

LLM に選択・合成をさせる実験のリーク制御は「その値を見せると答えが分かるか」の直接判定
(可視性) だけでは不足で、「その値は性能結果を経由して選ばれたか」(来歴) で判定する必要がある。
値でなく lineage を追う点で、planner/coder の構造遮断 (D39 決定 7、D45) と同じ系列に属する。

## 限界

- selector 未実走のため、この遮断が予測品質・追従判定に十分だったかは oracle 実走後にのみ言える
- mechanism 制御語彙は機構分類までは隠さない (敵対相談 C2 の指摘。逐語 =
  `output/insights/2026-07-16_s8b-freeze-consultations.md`)
