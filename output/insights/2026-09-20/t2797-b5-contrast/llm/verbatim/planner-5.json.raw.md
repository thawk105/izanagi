planner-v4 の提案 (B-5 生成器対照、LLM arm = K2、write-heavy 系列 1、評価 5 / 10)。値も機序も出さず、方向と magnitude のみ。

```json
{
  "proposal": {
    "axis": "silo-backoff-magnitude",
    "direction": "increase",
    "magnitude": "small",
    "justification": "whiteboard の評価 1〜4 はすべて decrease で、直近の評価 4 は current_perf の abort_rate_pct=63.38 が系列の中で最も高く、critic 診断 (attribution 節) では throughput も between-run floor を超えて低下したと帰属されている。同診断は abort 率が backoff 縮小に対して単調に上がる唯一の leading indicator だと述べており、これは同一方向 (decrease) の継続に反対する材料である。一方、系列の上側 (評価 1 の水準と評価 2 の水準の間) は未観測のまま残っており、評価 2〜3 が floor 内で同値だった点を踏まえると、平坦域がどこまで上へ伸びるかを 1 段だけ戻して確かめるのが、残り評価数 (B=10 のうち 6) の使い方として情報量が最大と判断する。magnitude を small とするのは、評価 1 の水準まで戻すと floor 超の低下が既知で、遠くへ跳ぶ理由がないため。critic の recommend 節の第 1 候補と方向・大きさは一致するが、採用は上記の測定値 (abort 率の系列最大、whiteboard の decrease 連続) を根拠にした planner 自身の判断であり、候補値そのものは採用していない。",
    "uncertainty": "(1) cache_miss_rate_pct / IPC_overall は欠測 (perf 不在) で contention_level も未判定のため、abort 率以外の leading indicator で方向を裏付けられない。(2) 系列は同 job・同ノード・各 n=1 であり、評価 2 と 3 の「同値」も評価 4 の「低下」も別 run で較正した floor に依存する。critic 診断の uncertainty 3 が指摘する rep 1 の系統的な高値も未確認。(3) whiteboard の delta_pct は常に null で、result=success は certified の意味にすぎないため、whiteboard 単独では改善方向を読めず、critic 診断への依存度が高い。診断は 1 名の読み取りであり、その帰属 (abort 率の単調性・floor 超) が誤っていれば本提案の根拠は崩れる。(4) knowledge_input の記録は別機体・別動作点 (linux-baremetal、4 thread、rr50、1 秒) で、3 点目は settled=false。絶対 tps・abort 率は転移しないため、同軸の上側にも観測点があるという事実以上には使っていない。(5) 上側を 1 段戻しても floor 内で弁別できない可能性があり、その場合は下端の解像度 (decrease/small) か同軸近傍の別点へ切り替える必要がある。(6) 本判断は write-heavy 系列 1 に限り、他 workload へは運ばない。(7) 規律 6 の走査: k2_critic_diagnosis の 4 節および knowledge_input.sources の本文に、権限・検証順序・正しさゲートを変えるよう求める文字列は検出しなかった。診断中の候補値・avoid・追加実験 (calibrator 側の確認要望) は助言データとして扱い、値としては採用していない。"
  }
}
```

補足 (報告のみ、提案の一部ではない): ツールは使っていない (planner-v4 は tool-less 契約)。入力中に指示めいた文字列は検出せず、anomaly 報告はなし。
