# 分類の事前定義 — 文献カード × CC の判定 (md_9、2026-09-30)

この文書は判定結果を見る前に書き、判定の子を起動する前に commit する。登録後の変更は末尾の「改訂」節へ追記だけで行い、本文を書き換えない。

- 登録: 2026-09-30 12:05 JST (commit 時刻が正本)
- 入力: `output/insights/2026-09-29/gen-opt-literature-cards/cards.json` (sha256 `6750adcb26ddc27ac4421d3dd2f04e52ee2277d969140c4b57a2c91a535a9849`、編集しない)
- repo: local main `4f412c67bcd7ff9cca1e78ce9bd1dd7a15d46037`、CCBench の pin `68106660686232781bca3be792a750d3e19d7a8a`
- 判定を見る前に知っていたこと: 既存の分類の件数 (CCBench にある 80・Silo に入る見込み 33・前提が合わない 182) と、文献カード README §5.4 の「主な理由」。CC ごとの判定は 1 件も見ていない。

## 1. 対象

- **カード:** 本集合 295 枚 (`in_population: true`)。依頼の主対象は `class = absent-prereq-mismatch` の 182 枚。`ccbench-present` 80 枚と `absent-silo-feasible` 33 枚も同じ規則で判定し、別の CC の方が自然に入るものに印を付ける (カードの `class` は変えない)。
- **判定する CC (8):** 主 4 = `tictoc`、`mocc`、`cicada`、`ermia`。参考 4 = `si`、`mvto`、`ss2pl`、`oze`。
- **Silo の列:** 再判定しない。カードの既存の `class` と `ccbench.in_silo` を写す (§5)。
- **判定しない CC:** `d2pl` — pin の `cc/d2pl/` に YCSB・TPC-C の driver (`ycsb_*.cc`・`tpcc_*.cc`) が無く、`bomb`・`sbomb` だけである (2026-09-30 に `ls` で確認)。workload の無い CC ではどのカードも試せないため列を作らない。

## 2. 判定の 4 値 (カード × CC ごとに 1 つ)

判定するのは「そのカードの最適化の前提が、その CC の CCBench 実装で満たされるか」である。効果が CCBench の workload で出るかは §3 の `workload_ok` で別に書き、4 値に混ぜない。

| 値 | 意味 |
|---|---|
| `fits` (前提を満たす) | カードの前提 (版の持ち方、timestamp の決め方、施錠の方式、validation の有無、必要なメタデータ) がその CC の CCBench 実装に既にあり、その CC の骨格を変えずに最適化そのものだけを足せる。同じ機構が既にその CC にある場合も `fits` とし、`already_in_cc = true` を付ける。 |
| `minor` (小改造で満たす) | 足りない前提が、次の許容範囲 m1〜m4 に収まる。**骨格** — 版の持ち方 (単版 / 多版)、serialization point と timestamp の決め方、施錠の方式 (OCC の commit 時施錠 / 2PL の lock 表と待ち)、正しさの論拠 — を変えるものは小改造でない。 |
| `no` (満たさない) | 骨格の変更が要る、または CCBench のどの CC にも無い前提 (事前宣言の batch・決定論実行・partition・ディスク・HW・分散など) が要る。理由コード (§4) を 1 つ以上付ける。 |
| `unknown` (判断不能) | カードの欄から前提が決まらない (前提の欄が空か曖昧で、機構の説明からも決まらない、または前提が書かれた節を `not_read` と書いている)、または CC の性質が CC 前提表 (`cc-profiles.md`) で「未確認」。**他の値へ寄せない。** 理由コード `card-underspecified` / `cc-unverified` を付ける。 |

小改造の許容範囲 (`minor` にはどれに当たるかを必須で書く):

- **m1:** tuple または版に field を足す (固定サイズ)。
- **m2:** worker ごと、または全体で共有する状態を足す (固定サイズ)。
- **m3:** 既存の相 (read / validation / write / abort 後 / commit 後) に検査・分岐を足す、または相の中の順序を変える。
- **m4:** 既存の driver が取引の開始前に既に持つ情報 (YCSB の取引生成が作る操作列と key 集合など) を CC へ渡す口を足す。

m1〜m4 を 2 つ以上組み合わせても、骨格を変えなければ `minor` とする。組み合わせた数は `minor_parts` に書く。

## 3. 付随する欄 (カード × CC ごと)

| 欄 | 値 | 定義 |
|---|---|---|
| `already_in_cc` | true / false / unknown | 同じ機構がその CC の CCBench 実装に既にある。根拠はカードの `ccbench.where` と CC 前提表。true なら段 A の候補から外す。 |
| `workload_ok` | yes / no / unknown | その CC の CCBench に、この最適化の効果が現れうる workload driver (YCSB または TPC-C) がある。scan・述語・列の分割・可換演算・insert/delete に依存し、その CC の driver にその操作が無ければ no。 |
| `reasons` | 理由コードの列 | `no` と `unknown` で必須、`minor` では m1〜m4 を必須。`fits` では空でよい。 |
| `basis_fields` | カードの欄名の列 | 判定に実際に使った欄 (§6)。 |
| `note` | 日本語 1〜2 文 | 何が足りる / 足りないか。 |

カード単位の欄:

| 欄 | 定義 |
|---|---|
| `more_natural_on` | `class` が `ccbench-present` または `absent-silo-feasible` のカードについて、次の両方を満たす CC の列: (a) その CC で `fits` かつ `already_in_cc = false`、(b) カードの `base_protocol` または前提の核 (版の持ち方・timestamp の方式・施錠の方式) がその CC と一致し、Silo とは異なる。`ccbench-present` で `already_in_cc = true` の CC は `natural_home` として別に書く (移植の出所)。どちらも無ければ空。 |

## 4. 理由コード

`no` 用 (1 つ以上):

| コード | 意味 |
|---|---|
| `mv-required` | 多版 (版の連結・古い版の読み・版の GC) が要るが、その CC は単版 |
| `sv-required` | 単版の性質 (版と lock が同じ word にある等) が要るが、その CC は多版 |
| `ts-scheme` | timestamp の決め方 (開始時刻の割当て・commit 時の計算・区間) が合わない |
| `lock-regime` | 2PL の lock 表・待ち・未 commit 値の読み (dirty read) が要るが、その CC は OCC 型、またはその逆で commit 時の validation が要るが CC は 2PL |
| `predeclared` | 事前宣言の batch・決定論実行・静的解析が要る (m4 の「開始前に key 集合を渡す」では満たせない) |
| `partition` | データの partition と partition ごとの実行が要る |
| `platform` | ディスク・HW (HTM・RDMA など)・分散・複数ノードが要る |
| `gc-structure` | GC・版の回収の方式が合わない (その CC の回収経路と両立しない) |
| `other:<短い説明>` | 上のどれにも当たらない |

`unknown` 用: `card-underspecified`、`cc-unverified`。

## 5. Silo の列

再判定せず、カードの既存の欄を写す。

| カードの欄 | Silo 列の表記 |
|---|---|
| `class = ccbench-present` かつ `ccbench.in_silo = あり` | `present` |
| `class = ccbench-present` かつ `ccbench.in_silo ≠ あり` | `port-candidate` (他の CC にあり Silo に無い) |
| `class = absent-silo-feasible` | `feasible` (既存の判定) |
| `class = absent-prereq-mismatch` | `mismatch` (既存の判定) |

## 6. 判定に使う欄と優先順

1. `prerequisites` (前提の正本)
2. `mechanism`、`implementation_gist` (前提が曖昧なときの補い)
3. `base_protocol` (原典がどの CC 族の上か)
4. `requires_predeclared_sets` (true は `predeclared` の強い手がかり。ただし前提が「開始前の key 集合」だけで m4 で満たせるなら `minor`)
5. `silo_prereq` (Silo で何が足りないかの記述。他の CC でも同じ不足かの手がかり)
6. `correctness` (正しさの論拠がその CC の性質に依存するか)
7. `ccbench` (`already_in_cc` の判断)
8. `workloads_effective`、`workloads_ineffective`、`verifier` (`workload_ok` と段 A の条件だけに使う)
9. `not_read` (`card-underspecified` の判断)

CC 側の性質は `cc-profiles.md` (CCBench の実ソースで確かめた表、行番号つき) だけを根拠にする。cc-readiness の要約や記憶で代用しない。

## 7. 段 A の候補 (CC ごと)

次をすべて満たすカードを、その CC の段 A 候補とする。

1. `ccbench.presence = なし` (CCBench に無い)
2. その CC で `fits` または `minor`、かつ `already_in_cc ≠ true`
3. その CC で `workload_ok = yes`
4. カードの `verifier` が `observable` または `conditional:*` (今の検査器で見られる、または差し込み点を合わせれば見られる)

並べ方 (主観の順位は付けない): `fits` → `minor`、その中で `verifier = observable` → `conditional`、その中で `minor_parts` の少ない順、同順は `card_id` の辞書順。上位 5 件を README に載せ、全件は機械可読 file に置く。
`ccbench.presence = 一部` のカードは同じ規則で別に数える (副候補)。

## 8. 集計

CC ごとに、4 値の件数を (a) 182 枚、(b) 80 枚、(c) 33 枚、(d) 295 枚で出す。`fits + minor` (`already_in_cc = true` を除く) の効果の 3 分類 (`effect_category`) の内訳を出す。`unknown` は独立に数え、どの値にも足さない。

## 9. 準備の表と順番の規則

各 CC について、gen-opt のベースにするのに欠けている準備を 5 段に並べる: (1) trace 計装、(2) certified を出す証拠面、(3) 性能計測、(4) LLM が書く口、(5) 比較基盤。状態は 有 / 部分 / 無 で、根拠は repo の実物 (file・決定番号)。

各段の重さ (結果を見る前に固定):

- **S (1 点):** 他の CC 用の既存実装を protocol 引数や設定で差し込む程度で、先例がある。
- **M (2 点):** 新しい計装 patch、新しい証拠面 1 つ、新しい driver 経路 1 つなど、判定器の意味を変えない新規実装。
- **L (3 点):** 判定器の意味の拡張 (多版・2PL の意味論、新しい anomaly の定義)、または LLM の口と検査器一式の新設。
- 既に有る段は 0 点。

順番の推奨を書くときは、段 A 候補数 (§7、`fits` + `minor`) と重さの合計の両方を表に並べ、**候補数 ÷ (重さの合計 + 1)** の大きい順を第一案とする。**certified を出す証拠面 (段 2) が「無」の CC は、その段を済ませるまで「使える」と書かない。** 規律 2・3 を緩める準備は数えない。

## 10. 検算

- 全組 (295 × 8 = 2,360) がちょうど 1 件ずつあり、値・理由コードが上の語彙に収まることを機械で確かめる。
- 親が固定 seed の無作為抽出 30 組と、各 CC の段 A 候補の上位 5 件を、カードと CC 前提表から読み直す。食い違いは件数と中身を README に残し、判定を直すときは直した組を列挙する。
- 段 6 で独立の read-only レビューを 1 本行う。

## 改訂

(なし)
