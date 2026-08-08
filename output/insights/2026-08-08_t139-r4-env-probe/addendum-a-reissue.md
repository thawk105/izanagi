# [T-139] 本走 — 事前登録 追補 A (案。ユーザー承認前は発効しない)

```text
authority: none
default_effect: no-state-change
study_label: rf_partial_recovery / paired_cluster / main_study / addendum_a
document_kind: preregistration_addendum_a
```

## 0.0 本版について (2026-08-09 再発行)

**本書は 2026-08-08 版 (`output/insights/2026-08-08_t139-addendum-a/addendum-a.md`) の再発行である。**
裁定 R4 = (a) に従い、凍結前に gen_S で非 study の環境 probe を 1 本走らせ、その実測を反映した。

初版からの差分は次の 4 箇所だけであり、**他の 9 field の値は 1 文字も変えていない。**

| 箇所 | 変更 |
|---|---|
| `a03` | 許容範囲 `[0, 1.0]` は**変えていない**。probe による支持測定 (13 窓、最大 `0.0791`) を追記した |
| `a04` | 「その分は予備 2 本が吸収する」を**削除**した (core §9 に照らして**偽**だった)。写像先を `判定不能` 一意に絞った |
| `a08` | 「probe の `COMMON` との唯一の差は `-DCCBENCH_TRACE`」を**削除**した (**偽**だった)。compiler の実測 digest を期待値として追記した |
| `a08` 付記 | `CCBENCH_TRACE=1` build の witness (`stock` のみ) を追記した |

**`a03` の許容範囲は probe の観測から導出していない。** 判定写像は probe の実行より前に凍結してあり
(`derivation-map.md` と `t139_r4_env_probe_contract.json`)、probe が返すのは
`feasible` / `not_feasible` / `incomplete` の 3 値だけである。
観測に合わせて数値を選ぶ設計は、段 3 と段 6 の敵対検証で 2 案とも
「実現値を必ず含む許容範囲」(core §14 の禁止) に該当すると反証されたため採用しなかった。
経緯は `derivation-map.md` §2 に逐語で残してある。

## 0. 本書の位置づけ

本書は凍結事前登録 core が §14 で閉集合として列挙する **追補 A** である。
core の文章を一切変更しない。core が `a01`〜`a13` として名前だけ固定した数値パラメータを、
**本 study のデータを 1 点も見る前** (pilot 1 本目の投入より前) に確定する。

**発効点。** 本書は、本書を承認する決定を canonical 台帳へ fold した commit 以後にのみ効力を持つ。
それ以前に pilot を投入してはならない。本書は自分自身の digest を本文へ書かない (自己参照の禁止)。

**従属先 core (path・commit・blob digest の三つ組):**

```yaml
core_ref:
  path:   output/insights/2026-08-07_t139-mainrun-design/preregistration.md
  commit: 88d68f9127b31df5aafc3d59607896626a1652e8
  sha256: ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9
```

`commit` は限定例外の決定 (D234) を canonical 台帳へ fold した commit `F` である。
本書の `fields` は `{a01, a02, …, a13}` を**過不足なく**設定する (exact-key。欠落も余剰も解決失敗)。

**envelope の grammar (exact-key を一意に検査するための parser 規則)。**
本書は 3 つの部分からなる。

```text
envelope := metadata (先頭の YAML fence) , preamble (§0) , fields , disclaimers (末尾節)
fields   := "## fields" の直後から、次の "## " 見出しまでの範囲
key      := fields の範囲内に現れる "### " 見出しの、先頭の空白なしトークン
```

**field key はこの規則で得た 13 個だけである。**§0 の `core_ref`、metadata の YAML key、
本文中や末尾節に現れる `aNN` 形の文字列 (相互参照) は field ではない。
**全文を grep して `aNN` を集める形の解決を禁じる。**
本書の機械可読形 (この規則を実装した parser、または同内容の構造化文書) の発行は
producer 実装 wave の責務であり、本書はコードを追加しない。
§15 の投入 gate 要件 5 が `a01`〜`a12` を基準に書いている点は、
同ディレクトリの `erratum-core-s15.md` が `a01`〜`a13` へ supersede する。

**本書が凍結するのは規則と期待値であり、実行の結果ではない。** build 後にしか存在しない digest
(実 binary hash、実 `identity_sha256`、実 schedule 表の digest) は本書では固定せず、
本書が固定した規則から producer が導出し、独立 validator が再導出して照合する。

---

## fields

### a01 — 1 割当ての時間予算表

割当ては 2 種類ある。いずれも `elapstim_req` は `01:00:00` (3600 秒) とする。

**性能 binary の生成元を一意にする。** 主経路の「割当ての外で build する」とは
**性能 cluster 割当ての外**という意味であり、実際の生成元は下記 (B) の検証割当て **1 本だけ**である。
6 build (性能 3 arm + correctness 3 arm) はすべて検証割当てで作り、性能 3 arm の artifact を
immutable path へ保存して以後の全性能 cluster がそれを stage する。
**同じ nominal 構成の性能 build を 2 度作らない。**

**(A) 性能 cluster 割当て (主経路。build は検証割当てで済ませてある)**

| phase | 上限 (秒) | 算定 |
|---|---:|---|
| preflight (admission・環境証明・schedule 導出・prebuilt binary hash 検証) | 180 | 固定 cap |
| build | 0 | 検証割当てで作った artifact を stage するだけ (`a05` が binary を束縛する) |
| correctness / liveness | 0 | 別割当て (絶対規律 1。同一割当てへ混ぜない) |
| 性能 run | 540 | `36 run × 15` |
| arm 間待機 | 720 | `24 gap × 30` |
| block 間待機 (workload 切替の 1 回を含む) | 660 | `11 gap × 60` |
| raw parse・受領証生成・phase 完全性検証 | 180 | 固定 cap |
| 後片付け・publish | 120 | 固定 cap |
| **小計 (非余裕)** | **2400** | |
| internal contingency | 900 | |
| **internal deadline** | **3300** | 小計 + contingency |
| scheduler safety | 300 | |
| **要求 walltime** | **3600** | `elapstim_req=01:00:00` |

**(B) 検証割当て (trace-enabled correctness / liveness。本 study で 1 本)**

| phase | 上限 (秒) |
|---|---:|
| source staging・patch 適用・identity 記録 | 180 |
| 6 build の configure / build (`6 × (60 + 180)` の直列総和) | 1440 |
| 6 build の compile manifest 抽出・`CMakeCache` 照合・`nm` 検査・binary hash・受領証 (`6 × 60`) | 360 |
| correctness / liveness run (`2 workload × 3 arm × 60`) | 360 |
| evidence 検証 | 180 |
| 後片付け | 120 |
| **小計 (非余裕)** | **2640** |
| internal contingency | 660 |
| **internal deadline** | **3300** |
| scheduler safety | 300 |
| **要求 walltime** | **3600** |

build phase を 1 本の 1500 秒 cap にすると、configure / build の直列総和 1440 秒に対して
manifest 抽出・`nm`・hash・受領証 6 組の余地が 60 秒しか残らない。
上表は **build phase (1440) と build 後処理 phase (360) を分離**し、それぞれに cap を課す。
`6 × (60 + 180)` は probe の実測 cap (`sh:421,423`) をそのまま使った上限であり、
実 elapsed の証拠ではない。

**hard cap の契約。** 各 phase の上限 `cap` は助言ではなく強制する。
`SIGTERM` を `cap − 10` 秒の時点で送り、`SIGKILL` を `cap` の時点で送る
(grace 10 秒は cap の**内側**に取る。`cap` 到達時に TERM を送って 10 秒後に KILL する形だと
cap を 10 秒超過する)。`timeout --foreground` だけでは TERM を無視する子を止められない。
cap は各 run・各 build の subprocess 単位ではなく、上表の **phase 単位**に課す。
**全 phase の cap の直列総和は internal deadline を超えてはならない** —
上表では (A) が `2400 ≤ 3300`、(B) が `2340 ≤ 3300` で成立する。
queue 待ちは割当て実行前なので `elapstim_req` の直列総和には算入しない。

実時間を見て cap や contingency を再配分してはならない。

### a02 — arm 間・block 間・workload 切替時の待機秒数

| 境界 | 秒 |
|---|---:|
| 同一 block 内の arm 間 | 30 |
| block 間 | 60 |
| workload 切替 | 60 (block 境界と同一の待機。`60 + 60` と加算しない) |
| cluster 最後の run の後 | 0 (待機を置かない) |

1 cluster あたりの待機総量は `24 × 30 + 11 × 60 = 1380` 秒である
(1 cluster = 12 block、block 内に arm 間 gap が 2 つ、block 間 gap が 11 個)。

待機は測定プロトコルの一部であり、推定量・検定統計量・区間の式を変えない。
**待機を実行時に延長・短縮してはならない** (adaptive wait の禁止)。
待機中に追加の観測・再試行・再 build を行わない。
pilot より前に固定し、pilot 後に変更しない。

### a03 — 待機後の環境復帰を判定する指標と許容範囲

**指標 `cpu_busy_core_equivalents`。** 各性能 run の**直前**、待機の末尾 10 秒窓で測る。

```text
Δc      = 待機末尾の 10 秒窓の始点と終点で読んだ /proc/stat の "cpu" 集計行の差分
total   = Δ(user) + Δ(nice) + Δ(system) + Δ(idle) + Δ(iowait) + Δ(irq) + Δ(softirq) + Δ(steal)
busy    = total − Δ(idle)
cpu_busy_core_equivalents = 48 × busy / total
```

- 列は上記 8 列**のみ**を使う。`guest` / `guest_nice` は `user` / `nice` に既に含まれるので加算しない。
- `iowait` は busy に数える (厳しい側)。
- 窓長は単調時計で `10.000 ± 0.100` 秒とし、**実測した窓長と両端の raw counter を受領証へ残す**。
- 48 はノードの physical core 数である (Pegasus gen_S、HT 無効)。

**観測窓の所在と順序。** 1 cluster の 36 run に対し待機境界は `24 + 11 = 35` 個しかなく、
**最初の run には先行する待機が無い。**最初の run の観測窓は preflight phase の中に置く。
順序と sub-cap を逐語で固定する (preflight cap は 180 秒、`TERM_at = 170`)。

```text
preflight:
  [0, 150)   admission・環境証明・schedule 導出・prebuilt binary hash 検証   (sub-cap 150 秒)
  [150, 160) 10 秒の環境観測窓                                              (a03 の観測)
  [160, 165) 判定 (validator が再計算する raw を確定する)
  [165, 170) performance_started marker の作成
  → marker 作成から最初の exec までの間隔は Δ_max = 5 秒以内
```

以後の 35 run は**直前の待機の末尾 10 秒**を観測窓とし、
観測終了から当該 run の exec までの間隔も `Δ_max = 5` 秒以内とする。
**観測窓と exec の間に他の作業・任意待機を挟まない。**
したがって観測窓は run ごとにちょうど 1 つ存在する (36 個)。

**malformed な counter の扱い (fail-closed。実装裁量を残さない):**

| 事象 | 帰結 |
|---|---|
| `/proc/stat` の `cpu` 集計行が 8 列に満たない | 判定不能として `a04` の写像へ送る。zero-fill しない |
| いずれかの列の差分が負 | 同上 |
| `total ≤ 0` | 同上 |
| 窓長が `10.000 ± 0.100` 秒の外 | 同上 |

いずれの場合も**指標を「成立」と扱わない**。再観測・窓の取り直しを行わない。

**許容範囲 (pilot 前に固定した有限区間):**

```text
0.0  ≤  cpu_busy_core_equivalents  ≤  1.0
```

**恒真化の禁止に対する適合。** 本指標は割当てごと・run ごとに変動する実測量であり、定数ではない。
許容範囲は有限の閉区間であり、指標の取りうる範囲 `[0, 48]` の真部分集合である。
producer は `recovered` に相当する boolean を持たない — **raw counter 2 点と単調時刻だけを記録し、
値の再計算と判定は独立 validator が行う。**不成立時に追加待機・再観測・窓の取り直しを行わない。

**`load1` は判定に使わない。** 1 分平滑のため直前の自 run の寄与が 30 秒後に `e^{-0.5} = 60.65%`、
60 秒後に `e^{-1} = 36.79%` 残り、「現在の外乱」ではなく「自分の履歴」を測る。
`load1` は診断値として併記するだけとし、受理条件の入力にしない。

**支持する測定 (裁定 R4 (a) の環境 probe。2026-08-09 実測)。**

非 study の環境 probe を gen_S で 1 本走らせた (request `0:896504.nqsv`、node `bnode028`、
run commit `1fa2b75b09b0b0e2e0e27a6f2cbedb058e8eb9f7`、
成果物 `output/env/pegasus/t139-r4-env-probe/0:896504.nqsv/`)。
判定写像は probe の実行より前に凍結してある
(`output/insights/2026-08-08_t139-r4-env-probe/derivation-map.md` と
`tools/pegasus/probes/t139_r4_env_probe_contract.json`)。**閾値は観測から作っていない。**

13 窓 (preflight 1・30 秒待機後 6・60 秒待機後 6) すべてが `valid` で、
すべてが `[0, 1.0]` に入った。判定は **`feasible`**。

| 窓 | 待機 (秒) | `cpu_busy_core_equivalents` | 窓長 (ms) | `load1` (診断) |
|---|---:|---:|---:|---:|
| `preflight` | — | 0.0070 | 10009.7 | 0.58 |
| `post-01` | 30 | 0.0100 | 9990.7 | 0.35 |
| `post-02` | 60 | 0.0110 | 9959.7 | 1.53 |
| `post-03` | 30 | 0.0150 | 9989.8 | 3.33 |
| `post-04` | 60 | 0.0100 | 9959.9 | 1.22 |
| `post-05` | 30 | **0.0791** | 9990.0 | 3.01 |
| `post-06` | 60 | 0.0753 | 9959.9 | 1.10 |
| `post-07` | 30 | 0.0060 | 9989.9 | 2.94 |
| `post-08` | 60 | 0.0070 | 9959.7 | 2.40 |
| `post-09` | 30 | 0.0080 | 9989.9 | 1.58 |
| `post-10` | 60 | 0.0100 | 9959.2 | 1.94 |
| `post-11` | 30 | 0.0090 | 9989.8 | 1.18 |
| `post-12` | 60 | 0.0110 | 9959.8 | 1.84 |

**最大は `0.0791` core-equivalents** (`post-05`、30 秒待機後) で、許容上限 `1.0` の 7.9% である。
窓長は 13 窓すべてが `10.000 ± 0.100` 秒に収まった。

**`load1` を判定に使わない選択は、この実測で裏付けられた。** `post-03` は `load1 = 3.33` だが
実測の busy は `0.0150` core-equivalents であり、両者は 2 桁以上乖離する。
`load1` に `[0, 1.0]` を当てていれば、正常な割当てが軒並み不成立になっていた。

> **この測定が主張しないこと。** `feasible` は、非専有 gen_S の**単一ノード・単一割当て・
> 当該時刻**に、stock だけを用いた 13 個の**相関した** node-global 観測がすべて `[0, 1.0]` に
> 入った、という記述的結果だけを表す。**割当て間 (cluster 間) 変動の観測は 0 点**であり、
> 13 窓は独立標本でも本走の 3 arm・36 run の履歴の再現でもない (本走は 30 秒 gap が 24 個、
> 60 秒 gap が 11 個)。観測された負荷を自 run の残渣・他テナント・特定 thread へ因果帰属しない。
> 将来割当ての分位点・上側許容限界・被覆率・偽拒否率・偽受理率、26 割当てへの保証、
> および `[0, 1.0]` が待機の十分性検査として適切であることは、いずれも主張しない。
> **本 probe は `a03` の許容範囲を導出も変更もしていない。**

### a04 — 復帰しなかった場合の失敗の写像先

§9 の既存分類への写像だけを決める。**新しい分類を作らない。**

境界は **durable な `performance_started` marker** の有無ひとつとする。marker は create-only で書き、
その path・size・SHA-256 と raw pointer を受領証へ残す。

**`a03` の不成立は、位置にかかわらず「開始後の失敗」へ写す (既定)。**

当初案は「marker の不在」を開始前の根拠にしていたが、これは
**marker と run log の両方を消すだけで、不利な attempt を予備で置き換えられる経路**を残す。
「job の stdout / scheduler 出力を外部証拠にする」案も trust root にならない —
その内容を書くのは job、すなわち producer 自身だからである
(append-only は改竄防止であって、内容の真実性と全 exec の完全捕捉を保証しない)。

現在 **producer の権限外にある exec の完全な記録は存在しない**。
したがって `a04` は、実現可能で fail-closed な唯一の写像を採る。

| 事象 | 写像先 (§9 の既存分類) | 置換 |
|---|---|---|
| `a03` が不成立 (preflight の観測窓・待機末尾の観測窓を問わない) | 性能測定の**開始後**の失敗 | **置換しない。**reject または判定不能 |
| `a03` の観測が malformed (8 列未満 / 負差分 / `total ≤ 0` / 窓長逸脱) | 同上 | **置換しない** |
| marker が存在し、その後に他の失敗 | 性能測定の**開始後**の失敗 | **置換しない** |
| marker が不在で、かつ性能 run の raw 痕跡が 1 件でも存在する | 性能測定の**開始後**の失敗 | **置換しない** |
| correctness anomaly | 候補の**終端 reject** (marker と無関係) | 削除も置換もしない |

**`a03` 不成立の写像先は「判定不能」一意とする** (`reject` を選ばない)。
core §9 の当該分類は「reject または判定不能」の二択を残しているが、
**結果を見てどちらかを選べる裁量を残さない**ため、`a04` の権限
(「§9 の既存分類のどれに写すか」を決める) の範囲内で一方に固定する。
§9 の分類を増やしてはいない。

**この既定は core §9 が許す予備置換を `a03` については使わない**という選択である。
コストは「preflight 段階の環境不調でも cluster を 1 本失う」ことである。

> **訂正 (再発行時)。** 初版はこのコストを「`J_max` の余裕と**予備 2 本**が吸収する」と書いたが、
> **これは偽である。**core §9 が予備置換を許すのは**性能測定の開始前**の infra failure だけであり、
> 本 field は `a03` 不成立を**開始後**の失敗へ写している。したがって予備 2 本はこの損失を
> 吸収できない。失った cluster は `J_max` の余裕でのみ吸収され、
> 必要な `J` に届かなければ study は `design_not_feasible` で終端する。

> **緩和には producer 権限外の trust root が要る。**
> `a03` の不成立を開始前 infra failure として予備置換したいなら、
> 全 process launch の完全な列を producer が書けない主体 (exec broker / 独立 collector) が
> 記録し、その記録を受領証が指す設計が要る。その可否は `package.md` の裁定 R7 が扱う。
> **本 wave はそれを実装しない。**

**性能測定の開始後に起きた失敗を、開始前の infra failure へ写してはならない。**
写像は上表だけで決め、TPS・失敗した arm・残り run 数を参照しない。

### a05 — 割当て外 build を採る場合の binary identity 束縛方法

**hash の対象:** 各 arm の性能 executable の**ファイル全 bytes** の SHA-256 (lowercase 64 hex) と byte size。

**「割当て外」の定義。** 本 field でいう割当て外 build とは、**性能 cluster 割当ての外**、
具体的には `a01` (B) の検証割当てで作ることを指す。検証割当てが性能 binary の**唯一の生成元**である。

**束縛の手順:**

1. 検証割当てで build した artifact を immutable path へ保存し、その `path / size / sha256` を記録する。
2. 各性能 cluster 割当てへ staging した artifact も同様に記録する。両者の digest は一致しなければならない。
3. 実行は **content-addressed copy** に束縛し、各 run に exec witness
   (実行した path・inode・size・実行直後に再計算した digest・単調時刻) を残す。
4. 再 hash を 3 点で行う — staging 直後、最初の run の前、最後の run の後。
5. symlink を拒否する。hash と parse は同一 byte buffer に対して行う。

**記録先:** `arms.*.binary` (arm ごとの digest) と `actual_runs[].binary_sha256` (run ごとの参照)。
両者の一致を validator が再計算して確かめる。**producer の申告 digest を権威にしない。**

**併せて記録するもの:** 全 translation unit の compile manifest、link argv、
compiler executable の SHA-256、動的依存と ELF interpreter、source tree / patch / 依存 pin の witness。

> **本 field が保証しないこと。** 外部の時刻根拠なしには、producer が別 bytes を走らせながら
> 整合した受領証を作る偽造は検出できない。これは core §15 が明示する非保証と同じであり、
> 本 field はそれを解消しない。

### a06 — 予備経路を採る場合の要求 walltime

割当て外 build が成立しない場合にだけ、build を割当て内に戻す予備経路を採る。

```text
elapstim_req      = 01:30:00  (5400 秒)
```

| 区分 | 秒 |
|---|---:|
| 主経路 (A) の非余裕 | 2400 |
| source staging | 180 |
| 3 arm の configure + build (`3 × (60 + 180)`) | 720 |
| **小計 (非余裕)** | **3300** |
| internal contingency | 1500 |
| **internal deadline** | **4800** |
| scheduler safety | 600 |
| **要求 walltime** | **5400** |

**経路の選択は当該割当ての投入前に固定する** — 性能値を 1 つも見ていない時点で決め、
走行後に選び直さない。

**予備経路でも binary identity は 1 つに保つ。** 予備経路では性能 cluster 割当ての中で build するが、
**得られた binary の SHA-256 が検証割当ての artifact と一致しなければ、その割当ては fail-closed で
reject する** (「cluster ごとに別の binary で測る」ことを許さない)。
一致検査は `a05` の経路で行う。

### a07 — W1 / W2 の driver 引数一式

**明示 argv (要素と順序を exact 比較する):**

```text
W1 = -ycsb_rmw=true -ycsb_zipf_skew=0.9 -ycsb_tuple_num=10000 -ycsb_max_ope=10 -thread_num=48 -extime=3
W2 = -ycsb_rratio=50 -ycsb_zipf_skew=0.5 -ycsb_tuple_num=100000 -ycsb_max_ope=10 -thread_num=48 -extime=3
```

**effective flag map (既定値の変化で workload が変わるのを防ぐため全件を固定する):**

| flag | W1 | W2 |
|---|---:|---:|
| `clocks_per_us` | 2100 | 2100 |
| `epoch_time` | 40 | 40 |
| `extime` | 3 | 3 |
| `thread_num` | 48 | 48 |
| `ycsb_max_ope` | 10 | 10 |
| `ycsb_rmw` | 1 | 0 |
| `ycsb_rratio` | 50 | 50 |
| `ycsb_tuple_num` | 10000 | 100000 |
| `ycsb_zipf_skew` | 0.9 | 0.5 |

**build 時 option map (`ShowOptParameters()` が報告するもの。性能 build):**

```text
ADD_ANALYSIS 0 : BACK_OFF 0 : KEY_SIZE 8 : MASSTREE_USE 1 :
NO_WAIT_LOCKING_IN_VALIDATION 1 : PARTITION_TABLE 0 : PROCEDURE_SORT 0 :
SLEEP_READ_PHASE 0 : VAL_SIZE 4 : WAL 0
```

各 run の log の `#FLAGS_` 行と `ShowOptParameters()` 行を**上表の exact map として照合する**。
一致しなければ受理しない。`#FLAGS_` 行が保証するのは実行 process が報告した effective 値だけであり、
caller argv・既定値の由来・source identity は保証しない (それらは `a05` / `a08` が担う)。

W1 / W2 は workload の同一性を固定するものであり、pilot 後に変更しない。変更は別 study である。

### a08 — 3 arm それぞれの source / patch / build identity と compile argv

**source triple (全 arm 共通):**

```yaml
repo_commit:  425ed1908dfd78cda97c48c2b248cdf6b83b1e91
ccbench_pin:  d706650cdb31e442bef45b9b4216951d4fb40969
patch_path:   tools/pegasus/probes/t139_positive_control.patch
patch_sha256: 3b9cdf1635c2afdbfa24af2b5e84e841773144147fe0d00c8b5e794817051951
```

**arm ごとの差分:**

| arm | patch | mode macro |
|---|---|---|
| `stock` | 適用しない | なし |
| `mode1` | 適用する | `-DIZANAGI_T139_PC_MODE1=1` |
| `modeX` | 適用する | `-DIZANAGI_T139_PC_MODEX=1` |

**依存 pin:**

```yaml
gflags:     e171aa2d15ed9eb17054558e0b3a6a413bb01067
glog:       8f9ccfe770add9e4c64e9b25c102658e3c763b73
masstree:   b3c5d054b66b08374d7a6ff5a0faeaf28b041a38
mimalloc:   02a2f5df9d7d46d30263b83832eebeeab62dc5fe
googletest: f8d7d77c06936315286eb55f8de22cd23c188571
```

**configure argv template (全 arm 共通の部分):**

```text
-DCMAKE_BUILD_TYPE=Release
-DENABLE_SANITIZER=OFF
-DCCBENCH_TRACE={0 | 1}
-DCCBENCH_BACK_OFF=0
-DCCBENCH_BACKOFF_FIXED=-1
-DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1
-DCCBENCH_NO_WAIT_OF_TICTOC=0
-DCCBENCH_WAL=0
-DCCBENCH_CCACHE=OFF
-DCMAKE_EXPORT_COMPILE_COMMANDS=ON
-DCMAKE_C_COMPILER_LAUNCHER=
-DCMAKE_CXX_COMPILER_LAUNCHER=
-DRULE_LAUNCH_COMPILE=
-DCMAKE_TOOLCHAIN_FILE=
-DCMAKE_PREFIX_PATH={PREFIX}
-DFETCHCONTENT_SOURCE_DIR_MASSTREE={TP}/masstree
-DFETCHCONTENT_SOURCE_DIR_MIMALLOC={TP}/mimalloc
-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST={TP}/googletest
-DIZANAGI_GFLAGS_SRC_HEAD={gflags pin}
-DIZANAGI_GLOG_SRC_HEAD={glog pin}
-DCMAKE_C_COMPILER={gcc}
-DCMAKE_CXX_COMPILER={g++}
```

**この共通部分の順序と内容は probe の `COMMON` (`t139_positive_control_probe.sh:394-404`) を
基礎とするが、同一ではない。**差は 2 点ある。

1. `-DCCBENCH_TRACE` が `0` 固定でなく build 種別で `0 | 1` を取る。
2. **compiler の渡し方が異なる。**既存 probe は `-DCMAKE_C_COMPILER=$(command -v gcc)` を渡すが、
   本 field は `realpath -e` で解決した絶対 path を要求する。

> **訂正 (再発行時)。** 初版は「唯一の差は `-DCCBENCH_TRACE`」と書いたが**偽であった**。
> login node の実測では `command -v gcc` = `/usr/bin/gcc`、`readlink -f` =
> `/usr/bin/x86_64-linux-gnu-gcc-11` であり、**両者は異なる文字列である。**
> exact argv validator はこの 2 つを別 token として扱うため、
> 「同一」と書いたまま実装すると validator が正しい build を拒否するか、
> 比較を緩めて別 build を受理する。realpath 側を採るのは、
> alternatives の切替で `/usr/bin/gcc` の指す実体が study 中に変わっても検出できるためである。

**token の展開規則と結合順序 (実装差を残さない):**

- `{PREFIX}` = 依存の install root、`{TP}` = third-party snapshot root。いずれも
  **`realpath` で symlink を解決した絶対 path** とし、受領証へ逐語で記録する。
- `{gcc}` / `{g++}` = `command -v` の結果を **`realpath` で解決した絶対 path**。
- `{gflags pin}` / `{glog pin}` は上記の依存 pin の 40 桁 hex。
- 最終 configure argv = **上記共通部分を記載順に並べ、その末尾に**
  `-DCCBENCH_ADD_ANALYSIS=<0|1>`、`-DCMAKE_CXX_FLAGS=<mode macro>` を **この順で**連結したものとする
  (probe の `COMMON[@]` + `extra[@]` と同じ形。`-DCCBENCH_TRACE` は共通部分の中にあり、
  **末尾で重複指定しない**)。`stock` の `mode macro` は空文字列であり、
  `-DCMAKE_CXX_FLAGS=` の形で必ず渡す (省略しない)。
- **6 通りの最終 argv 配列 (3 arm × 2 build 種別) を、arm ごと・build 種別ごとに逐語で受領証へ残す。**
  validator は 6 本すべてを exact 比較する。

**compiler identity。** 検証割当てで最初に build する際、
`realpath` 済みの compiler 絶対 path・`--version` の逐語出力・executable bytes の SHA-256 を記録し、
**以後の全 build がこの 3 つと exact 一致する**ことを要求する。
再照合は configure の直前・`cmake --build` の直前・build 直後の 3 点で行う。

**期待値 (裁定 R4 (a) の環境 probe で実測。request `0:896504.nqsv`、node `bnode028`、2026-08-09):**

| | `command -v` | `realpath -e` | executable SHA-256 | size (bytes) |
|---|---|---|---|---|
| `gcc` | `/bin/gcc` | `/usr/bin/x86_64-linux-gnu-gcc-11` | `821af3c74506283c179ca413bb33e6b528805a4dd8a5c09df125e5ad560a9e89` | 928584 |
| `g++` | `/bin/g++` | `/usr/bin/x86_64-linux-gnu-g++-11` | `2360901d864cf10bfd6296e261cb2c14053552a80377761ab07146ec9ec9a2c0` | 932680 |

`--version` の 1 行目 (両者とも同一 release):

```text
x86_64-linux-gnu-gcc-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0
x86_64-linux-gnu-g++-11 (Ubuntu 11.4.0-1ubuntu1~22.04.3) 11.4.0
```

**`command -v` と `realpath` が実際に異なることが計算ノードでも確定した** (`/bin/gcc` に対し
`/usr/bin/x86_64-linux-gnu-gcc-11`)。configure へ渡すのは **realpath 側**とする。
alternatives の切替で `/bin/gcc` の指す実体が study 中に変わっても、realpath 側なら検出できる。

> **注意。** 上表は**単一ノード (`bnode028`) の単一時刻の観測**である。
> 他ノードで同じ digest が得られることは主張しない。
> 本 field が要求するのは「検証割当てで最初に記録した 3 つと、以後の全 build が exact 一致する」
> ことであり、上表はその期待値が実在の値として取得可能であることの witness である。

**build 種別ごとの macro map (絶対規律 1 の分離):**

| build 種別 | `CCBENCH_TRACE` | `CCBENCH_ADD_ANALYSIS` | 用途 |
|---|---:|---:|---|
| 性能 build (3 arm) | 0 | 0 | 3 arm すべてこの build で測る |
| correctness / liveness build (3 arm) | **1** | 1 | 別ビルド・別 run・**別割当て** |

`CMakeCache.txt` の `CCBENCH_TRACE:STRING` と `CCBENCH_ADD_ANALYSIS:STRING` を上表と exact 照合する。

**正規化規則 (`identity_sha256` の作り方):**

実 `compile_commands.json` から全 translation unit の argv を抽出し、
一時 root (`{SOURCE}` `{MASSTREE}` `{MIMALLOC}` `{GFLAGS}` `{GLOG}`) を token へ置換した
UTF-8 JSON の SHA-256 を `compile.identity_sha256` とする。link argv と compiler executable の
SHA-256 も同じ受領証へ記録する。

**本 field が凍結するのは、上記の source triple・mode macro・argv template・macro map・正規化規則である。**
実 `identity_sha256` と実 binary digest は build の結果なので本書では凍結せず、`a05` の経路で
受領証へ記録し validator が再計算する。

**`CCBENCH_TRACE=1` build の witness (裁定 R4 (a) の環境 probe で実測、2026-08-09)。**

初版の時点では、J=1 screen の liveness build が実際には `TRACE=0 / ADD_ANALYSIS=1` であり、
`CCBENCH_TRACE=1` の build が通る witness は 1 件も存在しなかった。**この穴は塞がった。**

| build 種別 | `CCBENCH_TRACE` | `CCBENCH_ADD_ANALYSIS` | 結果 | configure (秒) | build (秒) |
|---|---:|---:|---|---:|---:|
| 性能相当 | 0 | 0 | 成功 | 1.5 | 14.0 |
| **correctness / liveness 相当** | **1** | **1** | **成功** | 1.5 | 4.6 |

request `0:896504.nqsv`、node `bnode028`、arm は `stock`。
`CMakeCache.txt` の `CCBENCH_TRACE:STRING` / `CCBENCH_ADD_ANALYSIS:STRING` を上表と exact 照合し、
`compile_commands.json` から抽出した実 argv も照合したうえで `ycsb_silo.exe` の生成を確認した。

> **主張の限定。** これは **`stock` 1 arm の base witness** である。
> `mode1` / `modeX` は patch を当てた枝であり、mode macro と trace 実装の相互作用によって
> それらだけが compile failure になる可能性は**排除していない**。
> したがって本 witness は、**検証割当てで 3 arm × TRACE=1 の build を省く根拠にはならない。**
> 3 arm の witness を probe で取るかどうかは裁定パッケージへ返す。

### a09 — block 実行順を選ぶ事前 seed と許容 schedule 集合の定義

**arm 記号:** `S = stock`、`D = mode1`、`X = modeX`。

**順列集合:**

```text
Π = { SDX, SXD, DSX, DXS, XSD, XDS }   (3 arm の全 6 順列)
```

**許容 schedule 集合。** cluster slot `j` (1-origin) の schedule は次をすべて満たすものとする。

1. workload ごとに 6 block を持ち、各 block は `Π` の要素をちょうど 1 回ずつ使う
   (1 workload = 18 run、1 cluster = 2 workload × 18 = **36 run**)。
2. 一方の workload の 6 block を連続実行し、その後もう一方の 6 block を実行する
   (workload 切替は cluster あたり 1 回)。
3. 先行 workload は slot の偶奇で決める — **奇数 slot は W2 先行、偶数 slot は W1 先行**。
   これにより任意の prefix `1..r` で W1 先行と W2 先行の本数差は `⌈r/2⌉ − ⌊r/2⌋ ≤ 1` となり、
   core §7 の「cluster 間で差 1 以内」を満たす。
4. 置換 attempt は新しい slot を作らず、**置換対象の slot と同じ schedule** を使う。

**seed (逐語):**

```text
7df15572d2d88f172bc69bea9bc2dc53eddcbef41211d8ece7b0a592e5b2615d
```

これは次の ASCII byte 列 (末尾 newline なし) の SHA-256 である。

```text
t139-mainrun-a09-v1|ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9
```

**block 順の導出 (runtime 乱数を使わない)。** workload `w ∈ {W1, W2}` の 6 block は、
各 `p ∈ Π` について次の digest を計算し、`(digest, p)` の昇順に並べる。

```text
key(j, w, p) = SHA-256( "t139-a09-v1|" || seed || "|" || dec(j) || "|" || w || "|" || p )
```

**preimage の byte grammar (実装差を消すために逐語で固定する):**

- 全体は ASCII byte 列とし、末尾 newline を付けない。
- `seed` は上記 64 文字の **lowercase hex ASCII 文字列**として連結する (32 raw bytes ではない)。
- `dec(j)` は slot 番号の十進 ASCII で、**符号なし・先頭ゼロなし** (`1`, `2`, …, `13`)。
- `w` は `W1` または `W2` の 2 文字。
- `p` は `SDX` 等の 3 文字。
- 区切りは ASCII の縦棒 `|` (0x7C) 1 文字。
- 比較は digest の **32 raw bytes を辞書順**で行う (hex 文字列の順序と一致する)。
- digest が完全一致した場合の tie-break は `p` の ASCII 昇順。

**導出結果の凍結。** producer は投入前に slot 1〜13 の schedule 表を導出して発行し、
その canonical bytes の SHA-256 を受領証へ記録する。**validator は seed と本規則から
schedule をゼロから再導出して照合する。**実 TPS・失敗理由・runtime 乱数を入力にしない。

### a10 — `J_max` の数値、26 割当ての内訳、pilot 推定から `J` を一意に導く手続き

**26 割当ての内訳 (上限 26 は core §11 が固定。内訳は目安であり本 field が確定する):**

```text
検証割当て (trace-enabled correctness / liveness)      1
pilot の適格 cluster                                    8
pilot の開始前 infra failure に対する予備               2
本走の適格 cluster の上限 (J_max)                      13
本走の開始前 infra failure に対する予備                 2
                                                      ---
合計                                                   26
```

```text
J_max = 13
候補集合 = {4, 5, …, 13}
```

検証割当てに予備は置かない。そこで correctness anomaly が出れば候補の終端 reject、
開始前 infra failure で完了できなければ `design_not_feasible` とする。
本走の `J` が 13 未満でも、未使用 slot を予備・追加反復・別候補へ振り替えない。

**pilot 母数。** 各適格 pilot cluster `j` について

```text
Y_j = ( N_W1,j , H_W1,j , G_W1,j , N_W2,j , H_W2,j , G_W2,j )ᵀ  ∈ R⁶
```

を作る。`n_p = 8`、`p = 6`、`ν = n_p − 1 = 7`。標本平均を `Ȳ`、不偏標本共分散を `S_p` とする。
`S_p` が正定値でなければ `design_not_feasible`。

**planning model (推論仮定として明示する。実証されたとは主張しない):**

```text
Y_j  iid ~  N_6( μ , Σ )
```

**共同 95% 信頼集合 `Θ`。** 検出力の下界に必要なのは**各成分の周辺量** `(μ_k, Σ_kk)` だけなので、
`Θ` を次の 2 つの同時集合の積として定める (行列全体の Loewner 区間も Wishart 極値分位点も使わない)。

```text
M = { μ : n_p (Ȳ − μ)ᵀ S_p⁻¹ (Ȳ − μ)  ≤  c_M },
      c_M = p(n_p−1)/(n_p−p) · F_{p, n_p−p, 0.975}          (p = 6, n_p = 8)

V = { Σ : Σ_kk ≤ ν (S_p)_kk / χ²_{ν, 0.025/6}   (k = 1..6) },   ν = n_p − 1 = 7
```

`M` の失敗確率は 0.025、`V` は 6 成分へ `0.025/6` ずつ配った Bonferroni なので失敗確率は 0.025 以下。
両者を Bonferroni で束ねるので `Θ` の共同被覆は**少なくとも 95%** である。
**同じ `Θ` を全候補 `J` に使う**ので、候補ごとの追加補正は要らない。

**成分ごとの最悪値 (いずれも閉形式):**

```text
μ⁻_k   = inf_{μ ∈ M} μ_k    = Ȳ_k − sqrt( c_M · (S_p)_kk / n_p )
Σ⁺_kk  = sup_{Σ ∈ V} Σ_kk   = ν (S_p)_kk / χ²_{ν, 0.025/6}
```

**`d = 1.0` gate (core §6 の裁定 U4。引き下げない):**

```text
d⁻ = min_{k=1..6}  μ⁻_k / sqrt( Σ⁺_kk )
```

`d⁻ < 1.0` なら効果量を引き下げず `design_not_feasible` とする。

> **等式が成り立つ枝を限定する。** `μ⁻_k ≥ 0` がすべての `k` で成り立つ枝では
> `d⁻ = inf_{Θ} min_k μ_k/sqrt(Σ_kk)` が成立する。どこかで `μ⁻_k < 0` なら、
> `V` が分散の下限を持たないため真の infimum は `−∞` になりうるので、`d⁻` は infimum と一致しない。
> ただしその枝は `d⁻ < 1.0` で必ず終了するため gate の判定は変わらない。
> **`d⁻` を無条件の infimum として引用してはならない。**

**確率層の記号を分ける。** 以下、`β_plan = 0.05` は **planning の不確実性** (pilot 母数が `Θ` に
入らない確率) を表し、`α₁ = 0.025` は**本走の型 I 誤り**を表す。両者は別の層であり、
足したり相殺したりしない。`M` は `1 − β_plan/2`、`V` は 6 成分へ `β_plan/2 / 6` ずつ配る。

**最悪検出力の下界 (相関に依存しない union bound。`Θ` 全体に対する認証された下界である):**

**統計量の定義 (曖昧さを残さない)。** 本走の `J` cluster から作った 6 次元代表値ベクトルの
標本平均を `μ̂`、**不偏**標本共分散 (分母 `J−1`) を `Ŝ_J` とし、

```text
s_k = sqrt( (Ŝ_J)_kk )          (成分 k の標本標準偏差)
T_k = √J · μ̂_k / s_k
```

とする。成分は `k = 1..6`、すなわち `(N_W1, H_W1, G_W1, N_W2, H_W2, G_W2)` である。
`G = D − N` なので `s_GG = s_DD + s_NN − 2 s_ND` であり、`a11` の `(N,D)` 領域から出る
`G` の下限 `Ḡ − q·sqrt(s_GG/J)` はこの `s_k` と同一である。
**したがって `a11` の受理条件 `P_W1 ∧ P_W2` は `∩_{k=1..6} { T_k > q }` と一致する**
(`N`・`G` は `(N,D)` の 2 次元領域の支持関数から、`H` は片側領域から出るが、
いずれも `成分平均 − q·sqrt(成分分散/J) > 0` という同一の形になる)。

planning model のもとで `T_k` は自由度 `J−1`・非心度 `δ_k = √J · μ_k / sqrt(Σ_kk)` の
**非心 t 分布**に従う。これは**周辺分布なので成分間の相関に依存しない**
(独立性は要らない — 各成分の周辺だけを見るため)。
非心 t の CDF は `δ_k` について非増加なので、`Θ` 上の最悪値は `δ⁻_k = √J · μ⁻_k / sqrt(Σ⁺_kk)` で取る。

```text
p_k(J) = F_nct( q(J, α₁) ;  df = J−1 ,  ncp = δ⁻_k )        (成分 k の失敗確率の上界)

L_J    = max( 0 ,  1 − Σ_{k=1..6} p_k(J) )
```

Bonferroni (union bound) は**任意の相関**で成り立つので、

```text
L_J  ≤  inf_{(μ,Σ) ∈ Θ}  P_{μ,Σ}( P_W1 ∧ P_W2 )
```

が成り立つ。すなわち `L_J` は core §6 が要求する「pilot 母数の共同信頼集合上の最悪検出力」の
**認証された下界**である。保守側であり、相関が有利な場合には真の最悪検出力より小さい値を返す。

> **Monte Carlo を使わない。** `L_J` は非心 t の CDF・`F` 分位点・`χ²` 分位点の 3 つだけで決まる
> 閉形式である。乱数・seed・反復数・solver の分岐順に依存しない。

**数値の認証 (「相対誤差 1e-12 で丸める」だけでは上界にならないので、区間で扱う):**

各 `p_k(J)` は近似値ではなく**認証区間** `[p_k^L, p_k^U]` として評価する
(非心 t の CDF を、外向き丸めの区間演算で `p_k^L ≤ 真値 ≤ p_k^U` かつ `p_k^U − p_k^L ≤ 1e-9`
となるまで評価する)。同様に `q` も認証区間で求め、`p_k` の評価には**上端の `q` を使う**
(`q` が大きいほど `p_k` は大きく、保守側)。そのうえで

```text
L_J^cert = max( 0 ,  1 − Σ_{k=1..6} p_k^U )        (認証された下界)
U_J^cert = max( 0 ,  1 − Σ_{k=1..6} p_k^L )
```

とする。`p_k` を個別に丸めてから合計する (合計後に丸めない)。

**選択規則:**

```text
J = min { j ∈ {4, …, 13} :  L_j^cert ≥ 0.80 }
```

ただし **`[L_j^cert, U_j^cert]` が `0.80` を跨ぐ候補が 1 つでもあれば `design_not_feasible`** とする
(認証幅を狭めれば別の `J` になりうる状態を残さないため)。
該当 `J` が無い場合、`J_max` を増やさず `design_not_feasible` とする。
実装間の差を消すため、`(J, δ⁻, q)` の reference vector と期待 `[L^cert, U^cert]` を
producer が投入前に発行し、validator が再計算して照合する。
`design_not_feasible` は当該候補・親系列の**終端状態**であり、
再開は全試行を保持した新 study・新しい有意水準割当てに限る。

pilot の raw は上記の固定写像への入力としてのみ使い、本走の推定・p 値・区間へ合算しない。
`J_max`・信頼水準 (`0.975` と `0.025/6`)・候補集合・丸め方向・許容誤差は pilot の結果を見て変更しない。

### a11 — 同時信頼領域 `C_w` の構成と臨界値 `q` の導出規則

**線形汎関数の関係 (親が検算済み)。** cluster 代表値を `(S, D_g, X)` とすると

```text
( N , H , G )ᵀ  =  [ 0  −1   1 ;  1−κ  −1   0 ;  1   0  −1 ] ( S , D_g , X )ᵀ ,   det = κ = 0.20
```

なので `N`・`H`・`G` は同じ 3 次元平均の**独立な**線形汎関数である
(したがって 3 者を同時に押さえるには 3 次元を扱う必要がある)。`D = N + G`。

**領域の定義 (逆行列を使わない支持関数形):**

任意の `c` について次を満たす閉凸集合を `E_k(q)` と書く。

```text
inf_{v ∈ E_k(q)} cᵀv  =  cᵀ v̂  −  q · sqrt( cᵀ S c / J )
```

`S` が正則ならこれは通常の楕円体と一致し、特異でも右辺は定義される。
**`C_w` は次の積とする。**

```text
C_w(q) = { (N,H,G) : (N, D) ∈ E_2(q) かつ H ∈ [ H̄ − q·sqrt(s_HH/J) , ∞ ) }
```

すなわち `(N, D)` については 2 次元領域、`H` については片側領域を、**共通の `q`** で束ねる。

**`q` の導出規則 (`J` と `α_k` だけの関数。pilot の共分散から選ばない):**

```text
q(J, α_k) = 次を満たす最小の q ≥ 0
            [ 1 − F_{2, J−2}( q² (J−2) / (2(J−1)) ) ]  +  [ 1 − T_{J−1}(q) ]  ≤  α_k
```

第 1 項は 2 次元 Hotelling 領域の失敗確率、第 2 項は `H` の片側領域の失敗確率であり、
union bound により `C_w(q)` の被覆は少なくとも `1 − α_k` である
(2 つの領域の従属性にかかわらず成立する)。
数値解は相対誤差 `1e-12` 以下で求め、**小数第 9 位で切り上げる** (`q` を大きくする側 = 保守側)。

> **「pilot 前に固定する」の意味。** pilot 前に固定するのは**写像 `J ↦ q(J, α_k)` と `α_k` の値**である。
> `J` は `a10` の手続きで pilot から一意に決まり、その時点で `q` の数値が確定して以後動かない。
> pilot の結果を見て `q` の**規則**や `α_k` を選び直す経路は存在しない。

**core §4 の Fieller 係数との整合。** `(N, D)` 領域の ratio projection は

```text
A = D̄² − q² s_DD/J ,   B = N̄D̄ − q² s_ND/J ,   C = N̄² − q² s_NN/J ,   A r² − 2Br + C ≤ 0
```

であり、core §4 の式を変更しない。`N > 0` の下限も `G = D − N > 0` の下限も同じ領域・同じ `q` から出る。

**採らない構成と理由:** 3 次元 Hotelling は式としては正しい (`q² = 3(J−1)/(J−3) · F_{3,J−3,1−α}`) が、
primary が使わない全線形方向まで同時に覆うため不要に大きい `q` を課す。
studentized maximum modulus を pilot の相関から較正する案は、`q` を pilot の raw に依存させる経路を開く。
3 本の周辺 Bonferroni 区間だけを使う案は、ratio projection が上記の 2 次式にならない。

**primary の権威。** primary の判定は **`N`・`H`・`G` の同時下限と core §5 の first-match 表**である。
`RF` の区間は core §16 の公表用であり、区間が `(0,1)` に含まれることだけから pass を導かない
(分母が負の枝では比が `(0,1)` に入りうるが、その領域は §5 軸 2 の順 2 `degradation_absent`
(正例 false) が区間の形を見る前に吸収する)。

**計算可能性の事前条件。** `S_w` が正定値でなければ統計量を計算しない。この場合は
core §7 の既存文 (「pairing・順序均衡・受領証のいずれかが成立しなければ判定不能」) と同じ
**判定不能**へ写す。ridge・pseudoinverse・次元縮約のいずれも採らない。**新しい失敗分類を作らない。**

**workload 間の多重性。** primary は `P_W1 ∧ P_W2` の intersection-union である。
global null は `H_{0,W1} ∪ H_{0,W2}` であり、global pass は null である workload の
false-pass 事象の部分集合なので、size は最大 `α_k` である。**W1 / W2 へ `α/2` を配分しない。**

### a12 — weak null の型 I 誤りを較正する事前 simulation の仕様

**位置づけ。** 本 simulation は、`a11` の planning model のもとでの**事前固定 stress check** である。

> **core §7 の逐語との差。** core は「weak null の型 I 誤りは事前 simulation で**較正する**」と書く。
> 本 field はその較正を**与えない** — cluster 間変動の観測が 1 点も無いためである。
> したがって本 field が core §7 の義務を満たしたと扱ってはならない。
> この差をどう解消するか (core §7 への第 2 の erratum / 新 core / 独立 cluster データの先行取得) は
> `package.md` の裁定 R2 が扱う。**本 wave はこの差を解消していない。**

入力は J=1 engineering screen の raw だけであり、**割当て間 (cluster 間) の変動は 1 点も観測されていない**
(core §17)。したがって本 simulation は「cluster level の weak mean null における真の型 I 誤りを較正した」
とは主張しない。主張するのは「事前固定した empirical stress model のもとで、
`a11` の手続きが名目 `α₁` を超えないこと」だけである。

**固定入力:**

```text
path   = output/env/pegasus/t139-positive-control-probe/0_892042.nqsv/throughput.tsv
sha256 = 755cfa7ea7c22ac763f404769103fd2ff0c49763c79369ac826db6a32b71c4f2
```

**data-generating model.** 各 workload `w`、rep `r = 1..5` について

```text
Z_{w,r} = ( X − D_g ,  (1−κ)S − D_g ,  S − X )      (κ = 0.20)
e_{w,r} = Z_{w,r} − (1/5) Σ_{s=1..5} Z_{w,s}
```

を作り、`{e_{w,r}}` を 3 次元 residual の empirical support とする。
simulation 内の 1 cluster は、`a09` の 6 permutation block へ `e_{w,r}` を復元抽出で 6 回割り当て、
その平均を cluster 代表残差とする。各 simulated dataset はこれを `J` cluster 生成する。

**乱数と反復数:**

```text
B     = 1,000,000                (候補 J × null 成分 の各セル)
J     = 4, …, 13                 (10 通り)
成分  = 6                        (W1/W2 × N/H/G)
セル  = 60
seed  = 01dad84c523b0a476655b91979c91d7174e40bb5a27757ada312abf2fe158ed2
```

seed は次の ASCII byte 列 (末尾 newline なし) の SHA-256 である。

```text
t139-mainrun-a12-v1|ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9
```

乱数 stream は `SHA-256( seed || domain || uint64_be(counter) )` の counter mode とし、
5 で割る際は modulo bias を避ける rejection sampling を使う。
**ライブラリ固有の PRNG に依存しない。**

**判定規則:**

各 weak-null face では対象成分の母平均を 0 に置き、
「対象成分の下限が 0 を超えるか」だけを数える (連言全体の false-pass 確率の上界である)。
false-pass 件数を `x_{Jk}`、familywise Monte Carlo error を `δ_MC = 0.001` として

```text
U_{Jk} = Beta⁻¹( 1 − δ_MC/60 ;  x_{Jk} + 1 ,  B − x_{Jk} )        (x = B のとき U = 1)
pass  ⟺  全 60 セルで  U_{Jk} ≤ α₁
```

**実行時期と失敗時の帰結。** 本 simulation は **pilot 1 本目の投入より前**に完走させる。
pilot の raw を一切入力にしない。
1 セルでも超過、simulation が未完了、入力 digest 不一致、seed / 反復数の不一致のいずれかなら
`design_not_feasible` とする。**`q` の緩和・候補 `J` の部分除外・pilot raw を使った再較正は行わない。**

### a13 — primary 系列に割り当てる有意水準

```yaml
familywise_alpha: 0.05
spending:
  domain: k = 1, 2, 3, …            # primary 系列の正規の根からの通し番号
  alpha_k: 0.05 / (k * (k + 1))
current_study:
  k: 1
  alpha: 0.025
unspent_tail:
  reclaim: false
  redistribute: false
```

```text
Σ_{k≥1} 0.05 / [ k(k+1) ] = 0.05
```

なので、**候補数の上限を必要としない** — 追補 B の `b01` (候補数上限) に依存しない。
`b01` が有限 cap を置いても未使用の tail は捨て、既存候補へ戻さない。

**`q` はここから導く。**`a11` の `q(J, α_k)` に `α₁ = 0.025` を入れる。
追補 B は `q` に影響する量を一切持たないので、primary の判定基準は pilot より前に完全に固定される。

**正規の根と ordinal の束縛 (primary 系列):**

- primary 系列の累積台帳の**正規の根**は、限定例外の決定 (D234) を canonical 台帳へ fold した
  commit `F = 88d68f9127b31df5aafc3d59607896626a1652e8` とする。
- 本 study はこの根に対する **`k = 1`** を占める。ordinal の予約は create-only であり、
  失敗・中断した試行も保持して番号を解放しない。
- **予約は producer が選べない canonical な台帳で原子的に行う。** 受領証は
  台帳の path・予約 entry の digest・予約 commit を必須記録し、validator は台帳を読み直して
  `(family_root, ordinal)` の**重複が無いこと**を確認する。
  **本書の宣言 (`k = 1`) は自己申告であり、それ自体は権威ではない。**
  台帳側の予約が無い、または重複しているなら pilot を投入しない。
- 新しい親系列 ID の自己申告で `k` をリセットできない。

> **本書だけでは閉じない。** 「自己申告でリセットできない」という規範は、
> caller が選べない外部台帳が実在してはじめて防壁になる。その台帳の実体化は
> producer 実装 wave の責務であり、本書はコードを追加しない
> (`package.md` の裁定 R3 が扱う)。台帳が無い状態で複数 study が同じ根に対し
> `k = 1` を主張すると、独立な 3 つの真の帰無で全体誤り率は
> `1 − (1 − 0.025)³ ≈ 0.0731 > 0.05` になる。
- 追補 B が本 study を `k ≠ 1` と示した場合は、`q` を別 `α` で計算し直さず **本走の投入を拒否する。**

> **本 field と追補 B の境界について。** core §14 は「累積台帳を束縛する正規の根の同定方法」を
> `b03` に置いている。本書が primary 系列の根と ordinal をここで束縛するのは、
> `α_k` が `k` に依存する以上、根が本走前 (追補 B) まで未定だと primary の有意水準が
> pilot 前に固定されないためである。この読みの採否は `package.md` の裁定 R3 が扱う。

---

## 本書が主張しないこと

- **本書が投入 gate を機械的に実装した、とは主張しない。** 本書は文書上の値と規則だけを定める。
  resolver・producer・validator・consumer・投入 script は producer 実装 wave の責務である。
- **`a03` の許容範囲を将来の全割当てが通る、とは主張しない。**
  2026-08-09 の環境 probe (request `0:896504.nqsv`) は 13 窓すべてが `[0, 1.0]` に入り
  最大 `0.0791` core-equivalents だったが、**これは単一ノード・単一割当ての記述的結果**であり、
  割当て間変動の観測は 0 点である。分位点・被覆率・偽拒否率を主張しない。
- **`CCBENCH_TRACE=1` の build が 3 arm すべてで通る、とは主張しない。**
  同 probe で `stock` の `TRACE=1 / ADD_ANALYSIS=1` build 成功は実証したが、
  `mode1` / `modeX` は patch を当てた枝であり未検証である。
- **`a12` が cluster level の真の型 I 誤りを較正した、とは主張しない** (cluster 間変動が未観測)。
- **`a11` の被覆 `1 − α_k` と `a10` の検出力下界が、分布仮定なしに成り立つ、とは主張しない。**
  Hotelling・`t`・非心 `t` の有限標本分布は **cluster 代表値の iid 多変量正規 planning model** に
  依存する。cluster 分布が非正規なら被覆も検出力下界も保証しない。
- **`a10` の `L_J` が真の最悪検出力に近い、とは主張しない。** union bound による下界であり、
  相関が有利な場合は真値より小さい (保守側に外れる)。
- **`a12` の `pass` が数学的な確定証明である、とは主張しない。** familywise `1 − δ_MC` の
  上側信頼主張であり、`δ_MC = 0.001` の確率で誤った通過を許す。
- **`a05` が偽造を検出する、とは主張しない** (core §15 の非保証と同じ)。
- **`a08` の compiler digest が他ノードでも同一である、とは主張しない。**
  2026-08-09 の環境 probe が `bnode028` で実測した値を期待値として記録したが、
  他ノード・他時刻で同じ digest が得られることは検証していない。
  本 field が要求するのは「検証割当てで最初に記録した 3 つと以後の全 build が exact 一致する」
  ことであり、ノード間の同一性ではない。
