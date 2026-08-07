---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-07
wave: dev-wave-t595-reasoning-ab
seq: 2
---

## {{D:reasoning-effort-adoption-latch}}. reasoning effort の既定は A/B が済むまで機械 pin で守る

**決定:** `docs/dev-wave/workers.md` の `DW-S02` / `DW-S03` が規定する `reasoning=max` を
`tools/check_docs.py` が節ごとに exact pin する。節から HTML comment と code fence を除いた
可視本文の effort 表記 (`reasoning=` / `reasoning_effort=` / `model_reasoning_effort=`、
引用符付きの値を含む) をすべて抽出し、値の列が厳密に `["max"]` のときだけ受理する。
引用行は可視として数える。段 5 の `reasoning=high` は pin しない。

解除は自動化しない。次の 3 段だけが解除経路である。

1. paired・blind・非劣性 A/B を完了し、対象段と採用値を明記した後継裁定を記録する。
2. 同一変更で `workers.md`、節別 pin、finding 文言、独立テスト、変異 spec を裁定どおり更新する。
3. 統合負例・関連テスト・`check_docs`・provenance を再走し、契約と latch を原子的に land する。

**理由:**
- D207 は「引き下げの可否は paired・blind・非劣性の評価だけが決める」と規定していたが、
  実測すると `check_docs.py` に `reasoning` の出現は 0 件で、規定は prose だけだった。
  誰かが `workers.md` の記述を書き換えても全検査が緑のまま通る状態であり、
  D207 の実効性は書き手の規律だけに依存していた。
- 検出力を下げる変更は規律 2 (正しさゲートを緩める変異を許さない) の対象である。
  A/B が未完了である以上、既定を動かせない状態を機械で保つのが fail-closed である。
- finding 文言は時系列の事実を断定しない。検査が読むのは `workers.md` だけで A/B 台帳ではないため、
  「A/B 未充足」と書くと採用後に誤報になる。「現行 adoption pin と不一致」に留める。

**却下した選択肢:**
- 値の出現数だけを数える — 可視の命令を `high` にしたうえで comment / fence 内へ `max` を
  1 個置くと通り抜ける。実測で再現した。
- prose 表記 `reasoning=` だけを認識する — 実際の起動キーは `model_reasoning_effort=` であり、
  実キー表記で `high` に下げたうえで `max` を例示として残すと通り抜ける。実測で再現した。
- 引用行を可視から除く — 引用は例示にも規範指示にも使えるため、規範の `high` を隠せる。
  除かない側が fail-closed である。引用内の effort 例示は拒否されるが、
  comment / code fence 内の例示は引き続き受理する。
- 段 5 の `high` も pin する — D207 が固定しているのは段 2/3 の `max` だけであり、
  scope 外の受理集合縮小になる。

## {{D:reasoning-ab-endpoint-requires-full-waves}}. D207 の endpoint をそのまま満たす A/B は完全 dev-wave 規模の campaign になる

**決定:** D207 が必須とした endpoint (後段の must-fix 件数と fix 巡回数) は段 2/3 の下流量であり、
1 replicate = 1 本の完全な dev-wave になる。したがって A/B の実走は単一 wave の作業ではなく、
予算と時間を伴う独立 campaign として扱い、着手可否をユーザー裁定に返す。
代理 endpoint は置かない。

**理由:**
- 代理 (例: 段 2 の plan へ固定 effort のレビュアを当てて件数を数える) は実装・fix 巡回・retry を
  通らないため、D207 が排除しようとした「弱い起草が巡回を増やし総消費が上がる」経路を
  排除できない。置けば endpoint を落としたまま引き下げが通る経路になる。
- 歴史成果物から endpoint を復元する案は成立しない。`s6-fix*.md` の素朴な計数には
  fix worker 出力でない裁定文書が混入し、実装を伴う wave の同定も命名揺れに依存する。
  この分布を検出力の根拠にしてはならない。
- 必要規模は margin と分散に依存するが、片側 5% / 検出力 80% の正規近似だけでも
  10 pair 台後半に達し、有限標本・co-primary の joint power・欠測を入れればさらに増える。
  paired 差の分散も、引き下げ側 arm の分散も相関も未観測である。

**却下した選択肢:**
- 装置を case family へ一般化して full-wave endpoint 台帳と protocol 凍結まで実装する —
  endpoint を偽装不能にするには wave の全 worker を実際に起動する trusted supervisor と、
  外部 custodian の独立 trust root が要る。いずれも装置ファイルの外にあり、
  producer 契約の追記先である dev-wave reference は予算余地が 13 bytes しかない。
  閉じないまま実装すると「schema 試作」を「判断可能な装置」として台帳に記録することになる。
- n=2 の pilot を走らせる — 非劣性も分散も判断できず、case と margin を pilot 結果へ
  合わせる余地を作る。
