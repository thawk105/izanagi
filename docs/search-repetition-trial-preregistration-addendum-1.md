# 探索の独立反復の試走 — 事前登録 v1 の追補 1: 候補生成の seed preimage と系列番号、試走の課題を S1-wh だけにする (2026-09-23)

本書は `docs/search-repetition-trial-preregistration.md` (v1、以下「本登録」) §0 の手続きによる追補である。本登録の bytes は変えない。
**試走の最初の候補生成より前** (smoke を含め、試走・本比較の系列を 1 本も走らせていない時点) に置く。結果を見た後の変更ではない。

## 1. 理由 — 本登録 §4 と実装の食い違い

本登録 §4 は系列の preimage を `t2849-harness-v1|<arm>|<workload>|t2850-trial-s<b>` (本比較は `t2850-main-s<b>`) とし、
系列 id の文字列で試走と本比較を分けると書いた。実装 (commit `7ea9aa09dad0012aebd5464c70a9e468c409dd92`、D2233、
`orchestrator/campaign/t2849_generators.py`) は系列 id を**正の整数** `series` として preimage に入れ、文字列の系列 id や cohort 名を受ける口を持たない。
試走は依頼によりこの commit に固定して走らせるので (発効束)、実装を変えず、本登録 §4 の preimage を実装どおりに登録し直す。
cohort 名は評価の slot key (`--b5-slot`) には入るが、候補の値の選択には入らない。

## 2. 登録する preimage (本登録 §4 の「seed preimage」の項を置き換える)

`<workload>` は `write-heavy` / `read-heavy` / `balanced`、`<R>` は系列番号 (10 進の正の整数)、`<a>` は原提案の番号 (1 起点)。

| 手法 | preimage |
|---|---|
| random | `t2849-harness-v1|random|<workload>|<R>|<a>|<counter>` (棄却抽出の counter は 0 から) |
| sweep | 格子 26 点の各 v について `t2849-harness-v1|sweep|<workload>|<R>|<v>` の SHA-256 昇順 (同値は v 昇順) |
| 進化 | 親があるとき `t2849-harness-v1|evolution|<workload>|<R>|<a>|0`。親が無いときは random と同じ規則で arm 名 `evolution-fallback` |
| BO | 決定的 (乱数なし)。学習点が 0 のときは random と同じ規則で arm 名 `bo-fallback`、失敗集合を除く |
| LLM (K0) | 乱数の preimage なし (提案は親 session の役割呼び出し) |

## 3. 系列番号の割り当て

- **試走:** 系列番号 R = block 番号 b (1, 2, 3)。本登録 §4 の「block b には全 cell の系列番号 b を 1 本ずつ置く」はそのまま。
- **smoke (費用と疎通の確認、試走の標本に数えない):** R = 9、block 9、cohort `t2850-smoke-v1` と LLM 経路の再 smoke の `t2850-smoke-v2`。smoke の性能値は生成・選択に使わない。
- **本比較:** 試走の 1〜3 と smoke の 9 のどれとも重ならない整数を、本比較の最初の生成より前の追補で固定する。
  同じ (手法, workload, R) は同じ候補列を生むので、重なると本比較の系列が試走・smoke の系列の再演になる。

## 4. 試走の課題を S1-wh だけにする (ユーザー裁定、2026-09-23)

### 4.1 理由

smoke (試走の標本ではない、§3) の実測で、評価 1 回 (1 session) の所要の大半が正しさの検証 (legacy 1 回と、動作点の 3 秒の trace 5 本の直列性検査) だと分かった。

| 実測 (smoke、2026-09-23) | 1 session | うち検証 | うち bench |
|---|---:|---:|---:|
| write-heavy の stock | 258 s | 210 s | 16 s |
| write-heavy の候補 (5 µs・10 µs、測り直しを含む 3 回) | 510〜517 s | 465〜472 s | 16 s |
| read-heavy の stock | 741 s | 697 s (1 本 135〜139 s) | 17 s |
| read-heavy の参照点 `p2_2_flag_opt` | 1,873 s 以上 (walltime で打ち切り) | — | — |

read-heavy の候補の 1 session は、stock と同じ 741 s から、固定 5 µs の既存記録 (3 秒の trace の検証 1 本 433 s、`output/insights/2026-09-23/t2847-verifier-capacity/README.md` §5) から換算した約 2,210 s までの幅に入る。
この単価で本登録 §3.3 の試走 (2 課題) を見積もり直すと 110.9〜252.2 node 時間 (本登録 §9.1 の試算は 128.7〜145.4、§9.2 の上限は 200) になり、上側は上限を超える。
ユーザーはこれを見て、試走の課題を S1-wh だけにすることを選んだ。本登録 §2.2 が S1-rh を入れた理由 (read-heavy の検証費を実測で置き換える) は、上の smoke の実測で一部済んでいる
(候補の 1 session は未測定のまま)。

### 4.2 変更 (本登録 §2.2・§3.3・§4 の該当箇所を置き換える)

- **試走の課題:** S1-wh だけ。S1-rh は試走に入れない。
- **規模:** cell 5、系列 15 (各 cell 3)、探索の評価 150、原提案の上限 450、論理 session 300 (系列 15 × 18 + block job 3 × 10)。
- **配置:** block b (1, 2, 3) に S1-wh の 5 手法の系列 b と block job `S1-wh|block|s<b>` の計 6 job。投入順は、この 6 識別子を辞書順に並べた列に、
  本登録 §4 の鍵 `t2850-trial-order-v1|<b>` と手順を当てて決める (12 識別子の順序から read-heavy を抜いた部分列ではない)。
- **見積り (実測の単価):** 42.4〜60.6 node 時間 (中心 47.6)。LLM の直列時間は 1.9〜19.5 時間 (中心 6.5。3 系列 × 10〜30 機会 × 225〜780 s)。
  計算は repo 外の `dev-wave-t2850-trial-run/estimate/` (発効束に写す)。費用上限は本登録 §9.2 の 200 node 時間のままとし、見積りの上側を超えそうになったら新しい投入を止めてユーザーに再確認する。

### 4.3 本比較の規模の規則 (本登録 §8) への影響

- §8.1 の s_plan は S1-wh の試走だけから作る。本比較に S1-rh・S1-bal を入れるときの s_plan は、本登録どおり試走した課題 (S1-wh) の値の流用で、**未検証の外挿**である。
- §8.1 の c(t′, m) = max_t c(t, m) は、試走した課題が S1-wh だけなので、read-heavy では上の smoke の実測に照らして**過小になることが分かっている** (read-heavy の 1 session は write-heavy の 1.4〜4.3 倍)。
  本比較に read-heavy を入れる場合は、本比較の計算確認の前の追補で、read-heavy の c を smoke の単価 (または新しい実測) から別に示す。本書はその値を決めない。
- §6.2 の T_c は S1-wh だけに定まる。E_T の族は S1-wh だけになる。

## 5. 影響

- 影響する系列: 試走の全系列 (まだ 1 本も走っていない。smoke は標本に数えない)。
- 本登録の他の規則 (手法・予算・記録・比較・規模の規則の式) は変えない。
- 投入順の識別子の `<手法>` には実装の arm 名 (`random`・`sweep`・`bo`・`evolution`・`llm`) を使う。
