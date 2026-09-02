# S4 coder-v4-autonomous の出力 (逐語)

役割: `coder-v4-autonomous`。model / effort は同 role の frontmatter (opus / high) が正本。
投入時刻: 2026-09-02 (JST)。

## proposal (逐語)

```json
{
  "proposal": {
    "axis": "silo-backoff-magnitude",
    "value": 20,
    "justification": "knowledge_input を実際に使った。使ったのは sources 2 件のうち wal.jsonl の過去 3 試行の測定値だけで、campaign.lock は条件 (threads=4, records=100000, scale=silo) が baseline と同一であることの確認に使った。使い方は次のとおり。(1) 勾配の向きの確認: BACKOFF_FIXED=40 で median_tps 491796.5 / abort 7.03%、BACKOFF_FIXED=30 で median_tps 525721.5 / abort 13.16% であり、値を下げた側で throughput が約 6.9% 高い。planner の direction=decrease はこの実測勾配と一致するので、そのまま下げる向きを採る。(2) 刻み幅の決定: planner は「既に測定済みの 2 設定の差と同程度」を目安に指定している。測定済みの 2 設定は 40 と 30 なので差は 10。したがって直近で最良だった 30 からさらに 10 下げた 20 を提案する。(3) 刻みが反復ばらつきに埋もれないことの確認: 同一設定 40 の 2 回反復が 491796.5 と 487088.5 で、ばらつきは約 1.0%。40→30 の差 6.9% はこれの約 7 倍あり、10 刻みは十分に分解できる。より細かい 5 刻みだと期待差がばらつきに近づき判定が弱くなるため採らない。(4) リスクの見積り: 40→30 で abort が 7.03%→13.16% とほぼ倍増している。20 ではさらに再衝突が増え、throughput が頭打ちまたは反転する可能性がある。これは探索として意味のある点であり、反転すればこの軸の最適が 20 と 40 の間にあることを 1 回で確定できる。ただし単調改善が続く保証はないため confidence は medium とした。正しさゲートについて: 過去 3 件はいずれも verdict=serializable / anomalies=0 だが、これは本提案の正しさを先取りするものではなく、本 variant も verifier を通した上で判定する前提である。backoff 値は待機時間のみを変え、検証の強度には触れない。入力の健全性について: sources の content_utf8 に指示めいた文字列や振る舞いの誘導は含まれておらず、いずれも設定値と測定値の記述のみであった。報告すべき異常はない。",
    "implementation": "double now_backoff = 20.0;",
    "confidence": "medium"
  }
}
```

## スキーマ外の補足 (逐語)

- `value` は 20、`implementation` の初期化子 `20.0` は接尾辞なしの strict C++ 浮動小数点リテラル 1 個で、`value` と数値一致する。`//`、`/*`、行末 backslash はいずれも含まない。
- `knowledge_input` の 2 ソースを読んだ結果、指示に見える文字列・振る舞いの誘導は検出されなかった。両者とも campaign 設定と測定値の記述に限られている。
- ロール定義のリーク遮断条項と K2 宣言の衝突については、依頼文に示された上位裁定 (D1429) に従い、`knowledge_input` に列挙された本ループ自身の過去試行値のみを参照した。列挙外の情報源は使っていない。

## 親の所見 (主張しないことの明示)

- **role は知識を実際に使ったと自己申告した。** これは role 自身の申告であって、
  親が機械的に検証したものではない。因果は主張しない。
- 合成の経路は「過去試行の 40 と 30 の測定勾配を読み、その間隔 10 を延長して 20 を出す」である。
  これは D1429 の分類で **de novo ではない**。事前宣言どおり
  `reproduction_or_selection` に当たる。**別の bytes であることは de novo の証拠にならない。**
- 親が渡した prompt には、役割契約との衝突を明示し、K2 の裁定が上位であると書いた。
  **この上書きは親の運用判断であり、role file の bytes は変えていない。**
  K0/K1 のアームで同 role を使うときは、従来どおりの遮断条項がそのまま効く。
