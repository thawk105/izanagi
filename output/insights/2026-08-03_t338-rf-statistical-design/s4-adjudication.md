# 段 4 裁定 — [T-338] RF 統計設計 (dev-wave 2026-08-03)

`authority: none` / `default_effect: no-state-change` — 本書は凍結記録であり、可変状態の正本
(worklog 末尾) ではない。ユーザーへ返す成果物は同 dir の `package.md`。

## 結論

**段 3 の両レンズが独立に NO-GO を返した。** ただし本 wave は実装 wave ではなく
**裁定パッケージを起草する wave** なので、NO-GO は「実装へ進めない」ではなく
**「5 点だけでは閉じない — パッケージの形を変えろ」**という意味である。親はこれを real と裁定し、
パッケージを 5 点から **11 件の裁定項目**へ組み替えた。

**[T-338] の前提そのものが不完全だったことが本 wave の最大の実測である。**
裁定 (121) は「RF 統計設計のうち **paired session 差による floor の取り方**を正例より先に裁定する」
だったが、両レンズが独立に示したとおり、**floor の意味は推定量 (estimand) が決まらないと定まらない。**
`RF = E[N]/E[D]` と `E[N/D]` では floor が守るべき量が違い、`δ_D` (最小識別幅) を置くかどうかで
判定式そのものが変わる。したがって「floor を先に裁定する」は単独では実行できない。
これは裁定の否定ではなく、**裁定を実行するために必要な前提の追加**である。

## レンズ A (統計的妥当性) の裁定 — 12 real / 4 refuted

| # | 所見 | 親の裁定 | 反映先 |
|---|---|---|---|
| A-1 | RF の estimand が一意でない (`E[N]/E[D]` は gap 加重) | **real・採用** | package Q1 |
| A-2 | 「分母が有意になるまで未定義」は選択後推論を生む。状態名も誤り | **real・採用** | package Q9 |
| A-3 | restricted randomization は weak mean null に有限標本 exact でない。実 probe の位置 balance も崩れている (W1 の stock は position 3 が 3 回、position 2 が 0 回) | **real・採用** | package Q6 |
| A-4 | family は global all-pass に過剰、candidate 選択に不足。`D=N+G` なので 3 つは独立でない | **real・採用** | package Q7 |
| A-5 | J=16 に power 根拠がない。d=0.5 なら概算 42〜49 cluster | **real・採用** | package Q5 |
| A-6 | fresh CV 3 値から paired floor も abort 一般化も導けない | **real・採用 (親の誤りの訂正)** | 下記 erratum、package Q3 |
| A-7 | 「別 allocation でなければ D19 の再演」は強すぎる (allocation ID は独立性の必要十分条件でない) | **refuted・採用 (親の追補 B の縮約)** | package Q4 |
| A-8 | 現存 probe は J=1 で between-cluster paired 分散を推定できない | **real・採用** | package Q4/Q5 |
| A-9 | 追補 D の「二つの floor の最大」は統計手続きにならない | **real・採用 (親の案の撤回)** | 下記 erratum、package Q3 |
| A-10 | Fieller primary は方向として正しいが J=16 の被覆と同時性が未解決 | **real・採用** | package Q9 |
| A-11 | complete-session 規則と reserve replacement は MNAR を直さない | **real・採用** | package Q8 |
| A-12 | P1 の自動 unpaired fallback は fail-closed でない | **real・採用 (親の P1 の撤回)** | 下記 erratum、package Q3 |
| A-13 | preregistration ancestry だけでは「値を見る前」を証明できない | **real・採用** | package Q10 |
| A-14 | floor gate と検定の AND 直列化それ自体は型 I 誤りを増やさない | **refuted・採用** | package Q3 の注 |
| A-15 | clamp 禁止と `RF>1` の機序非帰属は維持すべき | **refuted・採用 (親の P4 の当該部分を維持)** | package Q9 |
| A-16 | P6 (Gate1 √2 を別件に保つ) は RF 設計を壊さない | **refuted・採用 (親の P6 を維持)** | package 前文 |

## レンズ B (整合と実効性) の裁定 — 13 real / 5 refuted

| # | 所見 | 親の裁定 | 反映先 |
|---|---|---|---|
| B-1 | 16 allocation 案は G12 (single_process) と両立しない | **real・採用** | package Q4 |
| B-2 | paired 採用は D19/roadmap の例外新設。D104 は supersede 根拠にならない | **real・採用 (親の brief の先例引用が過大)** | 下記 erratum、package Q3 |
| B-3 | fresh CV からの paired margin 縮小の一般化は支持されない | **real・採用 (A-6 と同旨)** | erratum |
| B-4 | Layer3 の floor 閉表を広げるだけでは置き場所が誤る (env calibration と trial 固有統計は別物) | **real・採用 (親の追補 C の修正)** | package Q3/Q11 |
| B-5 | producer から certified consumer までの経路が無く gate が発火しない | **real・採用** | package Q11 |
| B-6 | `pairing_valid` 等を field にするだけでは gate にならない (D127 と同型) | **real・採用** | package Q11 |
| B-7 | 5 点の外の未提示裁定 (estimand・primary endpoint・`δ_D`) が受理条件を支配する | **real・採用** | package Q1/Q2 |
| B-8 | J=16 は検定・family と整合せず費用裁定にもなっていない | **real・採用** | package Q5 |
| B-9 | 新 trial ID による candidate 差し替えは多重性をリセットできる | **real・採用** | package Q7 |
| B-10 | P5 は correctness failure を session deletion で隠す | **real・採用 (親の P5 の修正)** | package Q8 |
| B-11 | P1 の自動 unpaired fallback は fail-closed でない | **real・採用 (A-12 と同旨)** | erratum |
| B-12 | Fieller の分類規則が unbounded/disjoint の全域を覆っていない | **real・採用** | package Q9 |
| B-13 | D116 を RF へ自動拡張し「追加凍結不要」としたのは未裁定 | **real・採用** | package Q10 |
| B-14 | docs-only で終えること自体は正しい | **refuted・採用** | 本 wave の scope 維持 |
| B-15 | P6 (Gate1 √2 を別件に保つ) は正しい | **refuted・採用** | package 前文 |
| B-16 | 「存在しない paired field を既存扱いしている」は成立しない | **refuted・採用** | — |
| B-17 | paired 化そのものが規律 2 違反とは言えない | **refuted・採用** | package Q3 の注 |
| B-18 | 追補 B の「現存 probe は J=1」は正しい | **refuted (= 事実認定は維持)** | package Q4 |

## 親自身の誤りの訂正 (erratum)

本 wave で親が書き、段 3 が実データで反証したものを明示的に取り下げる。

1. **「paired にすれば floor は小さくできる」(brief 追補 D の前提) を撤回する。**
   `Var(A−B) = Var(A) + Var(B) − 2Cov(A,B)` であり、既存の calibration JSON は
   **covariance を 1 つも持たない**。正なら縮み、負なら増える。方向は未知である。
   さらに分母 gap が小さければ絶対 SD が縮んでも `s(D)/D̄` は発散しうる。
2. **「abort 率が高いほど run 間ドリフトが大きい」という一般化を撤回する。**
   実測は逆方向を含む — abort 81.95% の write-heavy が CV 0.666%、abort 70.47% の
   balanced が CV 1.067% である。3 workload 各 1 系列では単調性も因果も識別できない。
   `docs/decisions.md` D19 の当該記述を RF へ一般化してはならない。
3. **追補 D の「fresh 下限と cross-window 値の最大を取る」案を撤回する。**
   独立な分散成分なら total SD は `√(σ₁²+σ₂²)` で max より大きく、同じ量の noisy な推定 2 つの
   max にも所定の被覆はない。**既存 `BETWEEN_RUN_CV = 0.030` がこの heuristic の産物である
   という事実認定は維持する**が、それを RF へ移植することは推奨しない。
4. **brief (P1) の「paired 前提が崩れたら unpaired へ fail-closed で戻す」を撤回する。**
   同一 session の arm は相関しており、負 covariance では unpaired の
   `√(s_a²+s_b²)` が真の差分散を**過小評価する**。段 2 とレンズ 2 本が独立に拒否した。
   正しくは `pairing invalid ⇒ indeterminate` である。
5. **brief の「D104 が paired 比較を承認済みの型として挙げている」を縮約する。**
   D104 決定 (4) は受入全走施策の一次証拠に関する記述であり、**RF floor の既裁定変更ではない**。
   先例として引けるのは「paired という手法が過去に採られたことがある」までである。
6. **追補 B の強い形 (「別 allocation でなければ D19 の再演」) を縮約する。**
   allocation ID は独立性の必要十分条件ではない。独立単位は対象母集団と相関構造から定義し、
   node / 時間窓を cluster として数える。**事実認定 (現存 probe は J=1) は維持する。**

## 段 2 プランの誤りで親が採らなかったもの

- **「16 independent sessions を最小とする」を採らない。** power 設計でなく SD の相対 SE から
  選ばれており、片側仮説なのに標本数説明は両側 sign-flip の最小 p を使っている (A-5)。
  さらに各 session を別 allocation とする形は G12 と両立しない (B-1)。
- **「D116 方式で追加凍結は不要」を断定として採らない。** D116 の射程は 8c 正式系列であり、
  RF への拡張自体が裁定項目である (B-13)。
- **`E[N]/E[D]` を既定として採らない。** 目的から決まる択一として返す (A-1/B-7)。

## 引用の実在検査 (親が実施)

段 2 とレンズ 2 本が引いた一次資料のうち、親が独立に開いて実在を確認したもの:
`order.tsv` / `throughput.tsv` の列構成、`silo_ladder_rung1.json` の 4 行
(`all_pass` / `recovery_measurement_eligibility` / `schedule_receipt` / `seed`)、
`docs/phase3-8c-preregistration.md` の 2 行、3 つの calibration JSON の CV と abort 値、
`layer3_report.py:218,231`、`p2_2.py:62`、`pegasus-runbook.md:432-434`、`glossary.md:119`。
**すべて実在した。捏造は検出していない。**

ただしレンズ A が挙げた**外部文献 (arXiv) は read-only sandbox で取得できないため未検証**である。
パッケージでは論拠を本文の統計的論証に置き、文献は参考表示に留める。

## 本 wave が実装しないことの確認

`DW-S04` により、scope 外の real 所見は実装せず裁定パッケージで返す。本 wave の変更は
docs (insight + spool fragment) のみで、コード・テスト・gate・artifact・凍結 bytes は
1 byte も動かさない。したがって**変異 matrix と受入全走は射程外**である。
