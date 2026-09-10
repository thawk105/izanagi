# [T-2188] 段 4 裁定 — プラン v2 と変異事前登録

2026-09-09。親 (dev-wave manager) が段 2 プランと段 3 の 2 レンズを裁定した。
base `cbcdb6c91`。段 3 の所見は `codex/s3-lens1.md` (測定の妥当性) と `codex/s3-lens2.md`
(受理集合と凍結) にある。

## 0. 裁定の要旨

**段 3 は親の解釈を 2 件倒した。どちらも撤回する。**
主判定の設計はレンズ 1 の是正案どおり作り直す。標本数は 6 セルのまま増やさない。
受理集合の緩和はレンズ 2 の指摘どおり新セル集合だけに閉じる。

## 1. 親自身の解釈に対する裁定 (撤回 2 件)

| # | 親の主張 | 裁定 | 理由 |
|---|---|---|---|
| I-1 | 窓内 commit 数は Poisson ではない (分散/平均 459〜917)。T-2216 の容疑 3 は外れた | **撤回 (real な反証)** | レンズ 1: 生の分散/平均は (a) `window_us` が 2.5〜45 ms と動くこと、(b) `backoff_before` が動くこと、(c) `cw` が commit 数 10,000 で止まる停止規則の標本であること、の 3 つで説明が付く。**平均の違う Poisson の混合は、条件付きに Poisson でも生の分散/平均が大きく出る。** 記録は `not_adjudicated` へ戻す |
| I-2 | 窓が広い側でも符号はコイン投げ | **撤回 (real な反証)** | レンズ 1: `directional_success` は独立な正解に対する的中率ではない。代数的にほぼ「次の観測勾配が正だったか」に還元され、実際に親の数値でも正勾配 494 件と成功 494 件が一致する。**この量が 0.5 なのは定常な歩行なら当然で、情報を持たない** |

**この 2 件の撤回は成果である。** 既存の `directional_success` を「勾配符号の的中率」と読んだ記録が
本 wave 以前から存在するので、その読みが成り立たないことを insight に明記する。

**Fano の所見 (`codex/s4-parent-finding-fano.md`) も射程を狭める。** model の `M_fano2` / `M_fano4`
を上げると予測が実測の谷へ向かうこと自体は artifact の値どおりだが、**親が測った 459〜917 は
計数トリガのセルの値であり、model の推定対象 (時間トリガの窓) とは別物である。**
したがって「model の探索幅が 2 桁足りない」とは書けない。書けるのは
**「記録済み trace は全部が計数トリガなので、stock の時間トリガ窓の Fano は 1 度も測られていない」**
までである。**時間トリガ窓の Fano を測ることは、新しい計測 (単位 B) の主要な出力の 1 つにする。**

## 2. レンズ 1 の所見に対する裁定

| # | 所見 | 裁定 | 措置 |
|---|---|---|---|
| L1-1 | 主判定が「勾配符号の的中率」を測っていない | **real・採用** | `directional_success` を機序判定から外す。代わりに **state-conditioned な符号不安定度** (直前 event の `{before, after}` の辺ごとに勾配符号の不一致率を出し、両条件で共通台の重みを固定して滞在構成の差を除く) を使う |
| L1-2 | `Δ ≤ −0.10` は「ノイズ増加」の予測方向ではない | **real・採用** | 無条件の符号率を判定から外したので消える。新判定は不安定度が**上がる**向きで書く |
| L1-3 | `scored ≥ 100` は有効な最低量でない (系列依存) | **real・採用** | 件数だけの条件をやめ、走行を 3 等分した各区間で符号が同方向かを併記する。`scored` を独立反復数として扱わない |
| L1-4 | 既存 `cw` は広い時間窓の対照でない | **real・採用** | 対照を新セル集合の中に作る (下記 §4) |
| L1-5 | 親の I-1 は実測から導けない | **real・採用** | §1 のとおり撤回 |
| L1-6 | 静的 `T(b)` を正解方向にする案は循環 | **real・採用** | 採点から外す。感度分析としてだけ残し `mixture_assumption_required: true` を付ける |
| L1-7 | 末尾 65,536 件は全走行の推定対象でない | **real・採用** | §5 のとおり、判定を末尾 slice へ明示的に限定する |
| L1-8 | 末尾偏りが判定と同じ向きに働きうる (自己成就) | **plausible・採用** | 滞在は event 加重と時間加重の**両方**を出し、どちらでも同じ向きかを見る。片方だけを主判定にしない |
| L1-9 | 陽性対照の絶対区間が非対称 (−0.13% で落ち +11% は通る) | **real・採用** | 形の保存 (shape preservation) へ変更。§6 |
| L1-10 | T-1941 との並置から機序について言えることはない | **real・採用** | `decision_eligible: false` の記述統計に限定。**brief の「最頻値 0 対 中央値 100 で形が違う」は撤回する** |
| L1-11 | 取りこぼし許容は材料の完全性を失う | **real・採用** | §5 |
| L1-12 | 規律 3 は形式的には満たすが独立な事前登録ではない | **plausible・採用** | 「新しい 10 µs trace に対する条件付き事前固定」と記録する。盲検の確証試験とは呼ばない |
| L1-13 | 6 セルは最小だが識別に必要な集合でない (時間トリガの広窓対照が無い) | **real・採用** | §4 |

**レンズ 1 の是正案 4 の一部は不採用。** ring を広げる案と online 十分統計を足す案は、いずれも
`patches/cicada-adaptive-dynamic.patch` の変更を伴う。同 patch は
`docs/dynamic-backoff-preregistration.md` が「本書を含む commit で凍結」と束縛しており、
反実仮想 2 本の事前登録も同じ patch stack を前提にしている。**凍結された patch を本 wave で
変えない。** 代わりに §5 の限定を採る。

## 3. レンズ 2 の所見に対する裁定

| # | 所見 | 裁定 | 措置 |
|---|---|---|---|
| L2-1 | overflow 受理が既存 3 集合へ無条件に波及する | **real・採用** | `_parse_backoff_trace` に `allow_overflow` を既定 `False` で足し、`args.cells == NONMONOTONIC_TRACE_CELLS_TEXT` のときだけ `True`。同じ stdout が `True` で通り `False` で落ちる対を test に置く |
| L2-2 | `dropped == 0` は反実仮想解析の推定対象を成立させる保証だった | **real・採用** | L2-1 で閉じる |
| L2-3 | cohort 2 は乱数の位相まで完全列に依存 | **real・採用** | 同上 |
| L2-4 | 「新集合には事前登録 SHA が付かない」は counterfactual 側だけ。旧 `prereg_sha256` は無条件に残る | **real・採用** | 親が現物で確認した (`_prereg_sha256()` は `docs/dynamic-backoff-preregistration.md` の hash を全 payload へ書く)。記録は「counterfactual preregistration なし、旧 `prereg_sha256` は出所の刻印として残る。**その事前登録された比較への帰属ではない**」と書く |
| L2-5 | Python / PBS の新しい軸対応を守る test が無い | **real・採用** | 既存 `test_backoff_trace_contract_accepts_only_three_exact_cell_literals` を 4 集合対応へ更新し、PBS の `case` から各集合の workload / threads / extime を抽出して対で照合する。**新 nodeid を増やさず既存 test の中で閉じる** |
| L2-6 | `certified: False` は冗長で、共通 payload へ足すと既存の性能成果物の schema まで変える | **real・採用** | **driver payload へは足さない。** 既存の `headline_eligible=False` / `throughput_scope=diagnostic_only` / metadata の `not_certified` で足りる。単位 A の解析器の出力にだけ literal で持つ |
| L2-7 | 投入変数名は一致。ただし現物のままでは新集合が default 枝で拒否され、単一 workload / thread も旧 global 軸検査で拒否される | **real・採用** | PBS に新枝と軸別検査を足す |
| L2-8 | 規律 1 の分離は維持されている | **確認・変更なし** | 触らない |

## 4. プラン v2 — 単位 B の格子 (6 セル、増やさない)

`count_window = 0` / `count_cap_us = 0` は **stock の時間トリガのみ**であり、
計数窓の機構は `#if BACKOFF_COUNT_WINDOW > 0` でコンパイル時に消える
(`patches/cicada-adaptive-dynamic.patch` 126/216/225/248 行、`cmake/Options.cmake` の既定 0)。
parser も `count_window = 0` を許す (`count_window=0 requires count_cap_us=0`、driver 521 行)。
したがって次の 6 セルは **stock の適応 backoff に trace 計装だけを足したもの**である。

| label | 刻み µs | 更新間隔 µs | 上限 µs | 役割 |
|---|---:|---:|---:|---|
| `nm-step0.5` | 0.5 | 10 | 1000 | 最良点。形の保存の陽性対照 |
| `nm-step1` | 1 | 10 | 1000 | **主判定の狭窓側** |
| `nm-step1-u2560` | 1 | 2560 | 1000 | **主判定の広窓側 (時間トリガ、他の軸は全部同じ)** |
| `nm-step2` | 2 | 10 | 1000 | 上限 50 µs の自然実験 (2.062 倍) と接続する点 |
| `nm-step25` | 25 | 10 | 1000 | 谷。形の保存の陽性対照 |
| `nm-step100` | 100 | 10 | 1000 | 回復。形の保存の陽性対照。T-1941 と同条件 |

軸は write-heavy のみ、48 スレッド、extime 3 秒、rep 1。**レンズ 1 の指摘どおり `nm-step5` を
`nm-step1-u2560` へ置換した。**これで主判定の 2 条件は刻み・上限・トリガ型・workload・スレッド数・
extime・patch stack がすべて同じで、**更新間隔だけが違う**。

## 5. ring の取りこぼしに対する裁定

- ring は広げない (§2 末尾の理由)。
- **全走行について測れる量が 1 つある。** `trace_summary.updates` は取りこぼした分も数えるので、
  `updates / extime` が**全走行の平均更新率**、その逆数が**全走行の平均実効更新間隔**になる。
  これは T-2216 §2 が「`Backoff_` と共に伸びる」と論じた量そのもので、**全走行について測れる。**
  これを単位 B の第一の出力にする。
- それ以外 (滞在分布、窓内 commit 数の Fano、符号不安定度) は**末尾 slice に限定**し、
  出力に `terminal_slice_only: true` と、`sum(window_us) / (extime × 1e6)` で計算した被覆率を必ず付ける。
- **機序の結論の語彙を固定する。** 末尾 slice で条件が満たされた場合は
  `terminal_slice_association_only`、全走行への一般化は `not_adjudicated` とする。
  **「機序を確定した」とは書かない。**

## 6. 事前固定する判定 (結果を見る前に凍結する)

**J0 (陽性対照・形の保存).** 新 trace の 5 つの 10 µs セルの throughput を、既存の trace 無し実測
(48 スレッド write-heavy、刻み 0.5 / 1 / 2 / 25 / 100 → 3,547,516 / 1,911,376 / 1,647,478 /
1,241,671 / 1,379,061 tps) と比べる。**セル共通の乗法係数を 5 点の比の中央値として求めて除いた後**、
(a) 0.5 → 1 の崖 (比 1.5 倍以上の低下)、(b) 25 → 100 の回復 (比 1.05 倍以上の上昇)、
(c) 各点の正規化残差が ±25% 以内、の 3 つを要求する。
落ちたら `observer_control_failed` とし、**共通係数と各点の残差を主結果として記録する**
(「どの刻みで計装が形を変えたか」が wave の実結果になる)。機序の採否はしない。

**J1 (符号の不安定度・末尾 slice).** `nm-step1` と `nm-step1-u2560` について、
各 event の勾配符号を直前 event の順序なし辺 `{backoff_before, backoff_after}` に割り当て、
**両条件に共通して現れる辺だけ**を取り、辺ごとの符号不一致率を**共通台の重みを固定して**平均する。
支持方向は「10 µs 側の不一致率が 2560 µs 側より 0.10 以上高い」。
走行を 3 等分した各区間でも同じ向きかを併記し、3 区間すべてで同方向でなければ
`direction_unstable` を付ける。反対向き・差が閾値未満・共通辺が 10 未満のいずれも
`not_supported` として記録する。

**J2 (悪い領域への滞在・末尾 slice).** 刻み軸の 5 セルについて、時間加重と event 加重の両方で
`P(Backoff_ > 50 µs)` と `P(Backoff_ > 100 µs)` を出す。支持方向は「谷 (`nm-step25`) の滞在が
最良点 (`nm-step0.5`) より高い」。**両方の重みで同方向でなければ `weight_sensitive` を付ける。**
これは上限 50 µs の自然実験 (T-2216 §1、2.062 倍の回復) と接続する既存の因果的材料であり、
静的 `T(b)` を正解ラベルに使わない。

**J3 (時間トリガ窓の Fano・末尾 slice).** 5 つの 10 µs セルと広窓セルについて、
窓内 commit 数の分散/平均を出す。**これは記述であって判定ではない。**
値を model の `M_fano2` / `M_fano4` が使う 2.0 / 4.0 と並べて記録する。

**J4 (全走行の実効更新間隔).** 各セルの `updates / 3 秒` の逆数を出す。
名目 10 µs との比を書く。**これは全走行の量である。**

**J1〜J4 は結果を見る前に本文書で凍結した。結果を見てから閾値・向き・語彙を変えない。**

## 7. scope の確定

- **単位 A (実装面):** 既存成果物の再解析器。撤回 2 件の根拠を数値で出し、
  記録済み trace 26 file が全部計数トリガであることを実測で示し、
  T-1941 と静的 `T(b)` を `decision_eligible: false` の記述統計として並べる。
- **単位 B (実装面):** driver の第 4 セル集合、`allow_overflow` の新集合限定、PBS の新枝と軸別検査、
  既存 test の 4 集合対応と 2 層軸対応、投入と計測。
- **単位 C:** insight / worklog / decisions fragment。
- **scope 外 (裁定で明示的に外した):** ring 拡大と patch 変更、model への実測 Fano 追加
  (時間トリガの Fano が未測なので、いま入れる値が無い)、静的曲線を正解ラベルにする採点、
  balanced / read-heavy への一般化、新しい gate・検査・台帳・一般化の新設。

## 8. 変異事前登録 (B-057、実装前に登録)

| ID | 位置 | 変異 | 赤になるべき層 |
|---|---|---|---|
| M1 | driver `_validate_backoff_trace_contract` の新集合の枝 | 新集合の workload 束縛を外し任意を受理 | 新集合の軸 drift 負例 |
| M2 | driver `_parse_backoff_trace` の `allow_overflow` 既定 | 既定を `True` にする | 既存 3 集合が `dropped > 0` を拒否する負例 |
| M3 | driver `_parse_backoff_trace` の overflow 算術 | `retained == min(updates, 65536)` の検査を落とす | overflow の count drift 負例 |
| M4 | PBS の `NONMONOTONIC_TRACE_CELLS_RAW` | 1 文字変える | 2 層 byte 一致 |
| M5 | PBS の新枝の `TRACE_WORKLOADS_RAW` | `write-heavy` を `balanced` にする | 2 層軸対応 |
| M6 | 解析器の推定対象ラベル | `decision_eligible` を `True` にする | ラベル正負対 |
| M7 | 解析器の `directional_success` 再計算 | 保存値をそのまま採用する | drift 検出の負例 |
| M8 | 解析器の `terminal_slice_only` と被覆率 | 出力から落とす | 出力契約の負例 |
| M9 | 解析器の J0 (形の保存) | 共通係数を除かず絶対値で比べる | J0 の正負対 |
| M10 | 解析器の J1 の共通台の重み固定 | 重み固定を外し無条件平均にする | J1 の正負対 |

各変異は実装後に「同じ入力を拒否する層が前後にも内側にも無い」ことを確認し、
確認できなければ登録から外して実効 gate へ再照準する (DW-M01、F820/F28)。
**受理集合を広げる変異 (M1) と狭める変異 (M2) の両方を登録し、過剰拒否の正例も置く。**

## 9. 並列分割

単位 A と単位 B は編集面が交わらないので実装子 2 本を並列。
単位 A = `orchestrator/campaign/backoff_nonmonotonicity_analysis.py` と対の test。
単位 B = `tools/pegasus/probes/t2187_adaptive_const_probe.py` / `.pbs` と
`orchestrator/tests/test_t2187_adaptive_const_probe.py`。
[T-2213] が単位 B と同じ file を編集中なので、統合は親が行い、競合解決だけ子へ返す。
