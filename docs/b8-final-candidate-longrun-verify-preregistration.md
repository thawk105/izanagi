# B-8 最終候補の長時間・独立反復 trace 検証 — 対象・「種」・「長時間」・判定規則を結果を見る前に固定する事前登録

本書は、論文素材 §8 の **B-8 (種を変えた長時間実行による最終候補の検証)** を取得するための規則を、
結果を見る前に固定する。対象 (何を検証するか)、「種を変えた」の操作的定義、「長時間」の操作的定義と
校正、判定規則、予算、主張しないことを 1 つの文書に置く。

**本書は事前登録の作成だけを行う。** 発効、試走、本走、runner の実装、phase doc・論文ストーリーの編集は
含まない。本書が存在することは、測定の認可にならない。**台帳 ID は未起票である** (出所は
`docs/paper-story/2026-09-20.md` §8 の B-8 と、採用候補 2 genome の検証相 (D2160) を B-8 の取得と
書かないと決めた同版の仕分け)。

同型の先例は B-5 生成器対照の事前登録 (`docs/b5-generator-contrast-preregistration.md`、D2158、未発効) と、
発効済みの `docs/t1998-balanced-stock-inline-preregistration.md` である。検証の規則そのものは
`docs/phase3-main-experiment.md` 層 1 (iv 付属) 「検証相の拘束数値」と、それを準用した D2160 を出発点にし、
B-8 の 3 要件に合わせて変えた箇所を §2〜§4 で明示する。

## 0. 版と発効

**本書は v1 であり、これが初版である。** 改訂履歴はまだ無い。

文書を作った commit と、本走を認可する**発効 commit** を区別する。発効は、ユーザーの本走認可を伴う
日付付き commit と、その認可を記録した決定 (D 番号) による。発効前の本書は未発効の登録であり、
本書だけを根拠に測定を始めてはならない。

**発効後は既存本文の bytes を書き換えない** (D1789)。訂正は末尾へ `## N. Erratum` として追記する形で
だけ行い、訂正の理由・日付・適用する cohort・判定への影響を書く。**結果を見た後の判定規則の変更は、
有利・不利の向きを問わず事後改訂である。** 当初の規則で得た結果を本書の結果として報告し、事後改訂の
下で得た結果は別欄に分けて報告する。Erratum を追記すると file 全体の SHA-256 は変わるので、発効時に
記録した測定版の SHA-256 を保存し、追記後の版と cohort の対応を Erratum に書く。

**本書は解析器の pin を持たない。** B-8 の判定は §6 の規則を機械適用する runner の集計で決まるが、
本書専用の consumer は未実装であり (§10)、凍結は文書契約に留まる。本書自身の hash や本書を含む commit
hash を本文へ埋め込まない (hash の自己参照は禁止)。発効時には本書の raw bytes の SHA-256 を決定記録へ
写し、測定時点の版と後日の解析規則の版を別々の定数として記録する (D1790)。

本書の規則に加え、§12 の「発効束」に列挙した実値 (対象の択、identity の期待値、verifier の版、runner の
bytes、校正 job の walltime など) を発効前に固定する。発効束の項目が 1 つでも未確定の間、本書は発効可能な
実験構成ではない。校正の結果と本走 job の walltime は発効の後に決まるものであり、発効束には含めない (§12)。

## 1. 主張の形と、主張しないこと

### 1.1 主張しうること

成立時に許す主張は、次の**操作的事実**に限る (roadmap §3.2「報告するのは条件、seed、trace 規模、観測
verdict」)。

> 対象 X (§2 で択一) の trace-enabled build を、独立 8 反復 × 3 workload (extime E s、計 24 verify) で
> trace 検証し、本走 24 verify の全件で verifier は `serializable`・certified を返し anomaly は 0 件だった。
> 校正で完走した k' 件の verdict も `serializable`・anomaly 0 だった。校正で完走しなかった走は k 件あり
> verdict を持たない。

失格の場合は、同じ強さで次を書く。

> 対象 X の独立反復 × 長 extime の trace 検証は失格である (絶対規律 2)。判定集合のうち anomaly を検出した verify は
> i 件 (anomaly 計 a 件)、verdict が `serializable` でなかった verify は j 件 (i と j は重なりうる。i ≥ 1 または j ≥ 1)。
> 種別・依存の構造、および anomaly 0 件で `serializable` でない場合の verifier の理由は §6.2。

i・j・a は §6.2 の記録から写した観測値であり、観測していない側を書かない (anomaly があって verdict が
`serializable` なら j = 0 と書き、その逆なら i = 0 と書く)。

**「B-8 を取得した」と書けるのは、§12 の確認事項 1〜3 (対象・種・長時間の各定義が論文ストーリーの
仕分けを満たすこと) をユーザーが発効時に確認した場合だけである。** 本書の規則で本走が完走しても、その
確認が無ければ「B-8 に関連する追加検証」であって取得ではない。

### 1.2 主張しないこと

- **性能。** trace-enabled build の throughput・commit 数は診断生値であり、性能値・比較・優劣に使わない
  (絶対規律 1)。本書は性能値を 1 つも含まない。
- **形式的信頼度 1−εⁿ。** ε (1 走あたりの見逃し確率) の定義、seed の identity、走の独立性のいずれも
  記録・較正できない。反復数 n を指数に載せる文を書かない (§1.3)。
- **「serializable であることが示された」「全走 anomaly ゼロ」。** certified の射程は観測した point
  read / write の trace に限る。校正の未完走走 (indeterminate) があれば「全走」とは書かず件数を添える。
- **S-1 (iv 付属) の充足。** 対象を案 A に取り規則を準用しても、S-1 の 12 時間予算・07-16 校正 (3 s)
  ・凍結文書の下での実施ではない。`output/reports/s1_direct_comparison/report.md` 冒頭の「本設計は独立な
  検証相を持たない」は S-1 の設計事実として真のままであり、本書はそれを書き換えない。本書は別登録の事後の
  検証を 1 本足す。
- **既存 certified 記録の昇格・降格** (絶対規律 7)。A-2 / A-6 / [T-1998] / S-1 campaign の判定と記録の
  bytes は変えない。anomaly が出た場合の扱いは §6.3 のとおり追記で訂正する。
- **長い extime や多い反復の効能。** 「6 s は 3 s が見逃す誤りを捕まえる」「n=8 で十分」とは書かない
  (§1.3)。長さと反復は登録した条件であって、検出力の主張ではない。
- **他 pin・他環境・他 workload・他 protocol への転移。** 結論は現行 pin、Pegasus gen_S、3 workload の
  動作点、silo に束縛される。
- **headline の復活、B-1 / B-5 / B-7 / B-10 の充足、mocc の G2 根因。** 本書はそれらに触れない。
- **verifier の完全性。** verifier は自前 mini-verifier であり predicate / phantom / fairness / 未観測実行を
  保証しない (roadmap §3.1 Tier 1)。

### 1.3 反例を作ったので書かない統計文

事前登録に「この条件は X を防ぐ」「n を増やせば信頼度が上がる」と書く前に、最小の反例を作った。作れた
文は本書に書かず、対応する事項を**仮定**として登録する。

1. **「独立 8 反復で anomaly 0 なら見逃し確率は εⁿ 以下」** — ε は 1 走あたりの見逃し確率 (§1.2 と同じ
   意味、露出確率は 1 − ε)。この式が n 反復の情報を表すのは、各走が走の条件に依らない同じ ε で独立に
   見逃すという前提の下だけである。前提が崩れる例: 実行時間が閾値 T を超えて初めて現れる決定的な誤り
   (例: 単調カウンタが特定の桁を跨ぐときだけ壊れる) は、extime < T の走では ε = 1 (n をいくら増やしても
   0 件のまま、εⁿ = 1 で n の情報が無い)、extime ≥ T の走では ε = 0 (1 走で必ず出る)。ε は走の条件で 0 か
   1 に振れ、条件に依らない定数として置けない。本書は ε の値も走の独立性も測れない。→ 反復数は「操作的
   事実の件数」として報告し、確率へ変換しない。
2. **「extime を 2 倍にすれば露出機会も 2 倍」** — 反例: 依存 cycle の発生数は commit 数に比例せず、競合
   の時間構造 (abort の連鎖、backoff で薄まる衝突) で決まる。露出機会が長さに比例するかは測っていない。
   → 長さは「開発相の 3 s より長い」という要件として登録し (§4.1)、効能は主張しない。
3. **「3 s を 24 回 (累計 72 s) 走らせれば 72 s の走と同じ」** — 反例: 1 走内でだけ進む状態 (epoch・TID
   の単調増加、GC・メモリ回収の蓄積、DB の hot set の変化) は走をまたいで引き継がれない。累計時間は
   1 走の長さの代わりにならない。→ 系列長での代替を採らない (§4.4)。
4. **「自己シードの 48 thread × 24 verify なら seed は事実上すべて異なる」** — seed は
   `std::random_device` の 32 bit 値 1 つから作られる (§3.1)。使われる seed は 1 走 48 個 × 24 verify =
   1152 個 (案 B は 2 候補で 2304 個)。`std::random_device` が独立一様に 32 bit を返すと**仮定すれば**、
   同じ値の再出現確率は誕生日近似 (n² / 2³³) で 1.5 × 10⁻⁴ (案 A) / 6.2 × 10⁻⁴ (案 B) だが、本書はその
   仮定を実測しないし、値を記録できないので再出現の有無は**検査できない**。→ 「すべて異なる」とは書かず、
   独立性を操作的仮定として登録する (§3.4)。

## 2. 対象 — 択と推奨

B-8 の要件本文が求める対象は「headline に載せる最終候補」である (`docs/phase3-main-experiment.md` 層 1
(iv 付属): 対象 = headline 最終候補 = 系側 gate 構成のみ)。論文ストーリー 2026-09-20 §8 の B-8 は、
D2160 の検証相を B-8 の取得と書かない理由の (1) に「対象が S-1 の最終候補 (系側 gate 構成 g_rl / g_rt)
ではなく採用静的 backoff 2 genome である」を挙げた。本書は 2 案を並記し、推奨を付け、**択一は発効時に
D 番号で記録する** (§12)。択が決まらない間、本書は発効可能な構成ではない。

### 2.1 案 A (推奨) — S-1 の最終候補: 系側 gate 構成 g_rl / g_rt

| workload | 構成 | flags (silo、`BACKOFF_TRIGGER_GATING=1` を含む) | gate 述語 (逐語) |
|---|---|---|---|
| balanced (rratio 50) | `g_rl` | `BACK_OFF=1, NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0, WAL=0, BACKOFF_TRIGGER_GATING=1` | `izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset \|\| izanagi_abort_reason_ == IzanagiAbortReason::kReadValiLocked;` |
| write-heavy (rratio 5) | `g_rt` | 同上 | `izanagi_gate_pass = izanagi_abort_reason_ == IzanagiAbortReason::kUnset \|\| izanagi_abort_reason_ == IzanagiAbortReason::kReadValiTid;` |
| read-heavy (rratio 95) | `g_rl` | 同上 | balanced と同じ |

- 出所: `output/s1-freeze/known_axes_freeze.json` の `entries.<workload>.system_gate` (S-1 の凍結、CCBench
  pin は当時の `d706650c…`)。workload ごとの割付は同 file の `s1b_pairing` (gate on = g_rl / g_rt、gate off
  = ident_all) と一致する。
- 1 対象 = 3 (workload, 構成) 組 × 8 反復 = **24 verify**。g_rl を write-heavy で、g_rt を balanced /
  read-heavy で走らせることは本書の対象に含めない (S-1 が headline に載せた割付だけを検証する)。
- 実装経路: `patches/silo-backoff-trigger-gating-variant.patch` (template) に gate 述語を
  `orchestrator/campaign/axis_trigger_gating.py` の経路で埋めた variant。S-1 の凍結 (`known_axes_freeze.json`)
  は CCBench pin の前進により `IZANAGI_FREEZE_HOLD` (`s1-known-axes.ccbench-submodule-head-pin`、解除は
  ユーザー明示命令のみ) の下にあるが、variant の build 自体は凍結の照合を経由しない。**現行 pin での
  厳密適用 (driver と同じ `git apply`)・trace-enabled build・identity の導出は本書の起草時点で未実測**
  であり、発効前の試走で確かめる (§10、§12)。

### 2.2 案 B — 採用静的 backoff 2 genome (fixed-5 / fixed-10)

| 候補 | genome (silo、共通 `NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0, WAL=0`) | 出所 | 現行 patch 下の identity (`src_token` = `source_bytes_sha256`、D2160 項 2) |
|---|---|---|---|
| fixed-5 | `BACK_OFF=1, BACKOFF_FIXED=5` | [T-1998] 事前登録 v1 の target = A-2 rr50 採用値 | `678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12` |
| fixed-10 | `BACK_OFF=1, BACKOFF_FIXED=10` | A-2 rr5 採用値 | `16c299355ba7d786534b320e99eb2a566622a3a3f9fee59c6b0886519a1a479d` |

- 2 候補 × 3 workload × 8 反復 = **48 verify**。候補ごとに判定する (一方の失格は他方に波及しない)。
- 実装経路は D2160 の wave が使ったもの (`patches/silo-backoff-fixed.patch`、Codex author 作の runner、
  repo 外)。identity の期待値は上表の値を発効束へ写す。
- **この 2 候補は D2160 で 3 s × 8 反復 × 3 workload の検証相を通っている** (判定集合 30 verify / 候補 =
  本走 24 (3 s) + 校正完走 6 (3 s が 3 件、6 s が 3 件)、anomaly 0)。案 B で本書が足すのは「長時間」(§4) の
  1 要素だけであり、「種」の定義は D2160 と同じである。

### 2.3 推奨の理由と、案 B を選ぶ条件

**推奨は案 A である。**

1. 論文ストーリー 2026-09-20 §8 の仕分けは、対象が S-1 の最終候補でないことを B-8 未取得の理由 (1) に
   数える。案 B は種・長さを満たしても理由 (1) が残り、**B-8 の定義を再裁定しない限り B-8 にならない**。
2. S-1 で成立した唯一の主張 S-1b (gate on / off の効果、`docs/paper-story/2026-09-20.md` 第 3 幕 (a)) が
   載せている variant は g_rl / g_rt であり、本書起草時に見つかった正しさの証拠は S-1 campaign の開発相 certified
   である。
   S-1 の 24 verify 本走は、S-1 直接比較 report の記述 (「本設計は独立な検証相を持たない」) と本書起草時に
   検索した成果物の範囲では実施されていない (網羅監査ではない、§8)。独立反復 × 長 extime の検証記録が
   見つからない最終候補は案 A だけである。
3. 案 B は既に 30 verify / 候補 (3 s が 27 件、6 s が 3 件) を持ち、6 s でも anomaly 0 の verdict を各 workload
   1 件ずつ持つ。同じ 2 候補に 6 s × 8 反復を足しても、それは既知結果の追試になる (§8)。案 A には現行 pin での
   6 s 以上の verdict が検索範囲に無い。本書は得られる情報の多少を比べず、「既知結果の追試か、記録の無い初回
   検証か」の区別だけを推奨の根拠にする。

**案 B を選ぶのが正当な条件** (いずれかが発効前に成立した場合):

- 現行 pin で g_rl / g_rt の trace-enabled build が成立しない、または identity が導けない (試走で判明)。
- ユーザーが B-8 の「最終候補」を「論文が採用値として報告する静的 backoff」へ再定義する裁定を出す
  (その場合、論文ストーリー §8 B-8 の仕分け (1) も同時に改める)。

案 A と案 B の**両方**を 1 つの cohort として走らせることは本 v1 に無い。採るなら結果を見る前に別仕様
として固定する (費用は §11 の和になる)。

### 2.4 identity の規則

- 対象は現行 CCBench pin (`pin.CURRENT_PIN`、submodule gitlink と一致すること) と現行 patch の下で build し、
  `source_digest.resolve_evidence(genome, pin, cxx="g++")` の `src_token` と `source_bytes_sha256` の両方が、
  発効束に写した期待値と build 前後で一致することを各 verify の起動条件にする (D2160 項 2 と同じ)。
- 案 A の期待値は発効前の試走で導出して発効束へ写す。07-16 校正が記録した g_rl の `src_token`
  (`4608a96e…`、pin `d706650c…`) は旧 pin の値であり、一致しないことが予想される。**旧 pin の値を期待値に
  せず、履歴上の対応として併記する** (A-2 の旧 token を期待値にしなかった D2160 項 2 と同型)。
- 期待値は観測後に動かさない。不一致の verify は判定集合に入れず「規約不適合」として件数を開示する。
- binary は node ごとの別 build になりうる (D2160 の 18 job は `binary_sha256` が異なった)。「同一 binary で
  24 反復した」とは書かず、source identity と toolchain の同一性だけを主張する。

## 3. 「種を変えた」の操作的定義

### 3.1 CCBench の乱数の実体 (現行 pin の source)

- `external/ccbench/include/random.hh` の `Xoroshiro128Plus::init()` は `std::random_device` から **32 bit 値を
  1 つ**取り `s[0]` に置き、`s[1] = splitMix64(s[0])` とする。
- `external/ccbench/include/ycsb.hh` の `YcsbWorkload` は member `Xoroshiro128Plus rnd_` の既定 constructor で
  1 回、自身の constructor の `rnd_.init()` でもう 1 回シードし (後者が上書きする)、
  `external/ccbench/common/runner.hh` の `worker_body` が **worker thread ごとに** `Workload workload;` を
  stack 上に構築する。したがって 48 thread の走は 48 個の自己シード (抽出は各 2 回、使うのは 2 回目) を持つ。
- ycsb の gflags 定義は `ycsb_rmw / ycsb_max_ope / ycsb_rratio / ycsb_tuple_num / ycsb_zipf_skew` の 5 つで、
  **seed を与える flag は無い。** seed 値は、本書起草時に読んだ初期化経路 (上の 3 file) では出力されない
  (bench の stdout・trace の全出力経路は追っていない。読解による確認であり、反証があれば §12 で扱う)。
- S-1 事前登録 層 2 は「seed×N の操作的定義: ycsb は CLI seed を持たず RNG は run ごとに自己シードする —
  seed×N は独立 N 反復を意味し、決定論的 seed 固定は導入しない (CCBench 改変 (D16) を要するため)。独立性は
  操作的仮定」と登録している。D2160 も同じ定義で実施した。

### 3.2 本書の定義 (採用)

**「種を変えた N 反復」= N 個の独立な bench process を、それぞれ新しい OS process として起動し、各 process
の各 worker thread が `std::random_device` から自己シードすること。** 1 つの verify は 1 つの bench process
(1 trace 集合) に対応し、同一 process の trace を分割して複数の verify に数えない。

各 verify で**記録する項目** (seed の代わりに「種が異なる走であること」を識別する): rep-id、bench の
PID、開始時刻 (wall clock と monotonic)、argv 全文、node 名、binary の sha256、source identity、trace の
byte 数・行数・commit witness。これらは D2160 の runner が記録した項目と同じである。

この定義は S-1 事前登録 層 2 の登録定義をそのまま採り、B-8 のために強めも弱めもしない。**論文ストーリー
2026-09-20 §8 の仕分け (2) は「数値 seed・乱数列の独立性は記録できない」を B-8 未取得の理由に数えている。**
本書はその事実を否定せず、「記録できない seed 値ではなく、独立 process の自己シードを『種を変えた』の
定義とする」ことを登録し、**その定義を B-8 の要件として認めるかを発効時のユーザー確認事項にする** (§12)。

### 3.3 代替 (採らない) — seed 注入の実装を前提条件にする

CCBench に seed を受け取る flag と log 出力を足せば seed 値は記録できる。本書はこれを前提条件に**しない**。

- CCBench 改変は D16 の性質分岐 (上流 PR / out-of-tree patch / EVOLVE-BLOCK) に従う別の変更単位で、本書の
  作成の認可に含まれない。
- seed 注入を含む build は対象の source bytes を変え、`src_token` が候補のものと一致しなくなる。検証したの
  は「採用候補そのもの」ではなく「seed 注入版」になり、規律 7 の下で別の identity として記録するほかない。
- seed を固定すると同一 seed の再走が可能になるが、B-8 が求めるのは再現ではなく**異なる**走である。値の
  記録が無くても、新 process の自己シードは「異なる走」を操作的に与える。

発効前に seed 注入が別の変更単位で着地していた場合も、本 v1 はそれを使わない。使うなら別仕様として
結果を見る前に固定する。

### 3.4 限定

- 独立性は操作的仮定である。`std::random_device` の実装 (CPU 命令か OS の entropy か) は toolchain 依存で
  あり、本書は実測しない。
- seed 値を記録しないので、同じ 32 bit 値の再出現 (§1.3 項 4) の有無は検査できない。
- 「seed を変えた」を「異なる乱数列であることを検証した」と読み替えない。

## 4. 「長時間」の操作的定義と校正

### 4.1 要件

**「長時間」= 1 走 (1 bench process) の extime が、開発相の trace 検証および D2160 の検証相が用いた 3 s より
長いこと。** 本書は extime ≥ 6 s を必要条件とし、値は §4.2 の校正で決める。**3 s へ丸めない** — 校正の
結果 3 s しか適格でなければ「候補なし」として本走を投入せず、B-8 は未取得のままにする。

背景 (整合のために書く): S-1 (iv 付属) は「1 verify ≤ 10 分に収まる最大値」を校正で採ると登録し、07-16 の
校正で 3 s に確定した。その規則の下では 3 s が「長 extime」だった。論文ストーリー 2026-09-20 §8 の仕分け
(3) は、D2160 の 3 s を B-8 の「長時間実行」と認めていない。本書は仕分け (3) に従い、B-8 の定義として
3 s より長いことを要求する。これは S-1 の登録を変えるものではなく、B-8 の別登録である。

### 4.2 校正の規則 (段 A)

各 (対象, workload) について、extime を **{6, 10} s の昇順**に各 1 回、trace-enabled build で trace run +
verifier 実走する。

- **適格** = bench 完走 ∧ trace 保全済み ∧ verifier 完走 ∧ `serializable` ∧ certified ∧ `anomaly_count` = 0 ∧
  identity 一致 ∧ **verifier wall ≤ 1800 s**。
- verifier wall > 1800 s、または verifier 未完走 (hard timeout / kill / rc≠0 / JSON 破損)、または bench 失敗
  で、**その extime 以上を打ち切る** (10 s を走らせない)。
- **未完走は `indeterminate` (operational) として記録し、verdict を持たない** (D2160 項 5 の規則を継承)。
  資源上限は正しさシグナルではない。未完走の trace も保全し、件数と保全先を報告に必ず開示する。
- **校正で完走した verifier に anomaly が 1 件でもあれば、当該対象は即失格** (絶対規律 2)。本走は投入しない。
- 対象の extime = 3 workload すべての適格集合の共通部分の最大値 (対象ごとに 1 値、workload 別にしない)。
  **共通部分が空なら「候補なし」で本走を投入しない。** 6 s へも 3 s へも丸めない。
- 校正の実消費は本走と別欄で報告する (§7)。校正で完走した verdict は判定集合に入る (§6.1)。

verifier wall の上限 1800 s は、D2160 の 600 s (S-1 の「≤ 10 分」) を 3 倍にした運用上の予算であって
正しさの条件ではない。理由: 現行 verifier で 6 s の read-heavy は 808〜864 s で完走しており (§4.3)、600 s
では 6 s が構造的に不適格になる。上限を観測後に動かさない。

### 4.3 現行 verifier での見込み (事実であって規則ではない)

D2160 の校正 (Pegasus gen_S、現行 verifier = 2026-09-02 の並列化後、fixed-5 / fixed-10) の実測:

| workload | 6 s: commit / verifier wall s / 主 process maxrss GiB | 10 s の結果 |
|---|---|---|
| write-heavy | 5.02M / 247.5〜250.6 / 18.8 | 8.32〜8.35M commit、hard timeout 3600 s で未完走 (主 process の CPU 時間は 6 s 走より少なく、worker 側の停滞が疑われる) |
| balanced | 8.60〜8.86M / 344.0〜357.0 / 26.9〜27.8 | 14.23〜14.75M commit、verifier が 294.9〜303.1 s で SIGKILL (2 node で再現、`killed_unknown`。node memory 128 GiB、per-job cgroup なし) |
| read-heavy | 30.7〜32.8M / 807.8〜864.3 / 80.2〜85.6 | 規則により未実走 |

- したがって現行 verifier では、案 B の extime は **6 s** になると見込まれる。案 A (g_rl / g_rt) は commit 数が
  異なる (07-16 の cygnus 校正では g_rl read-heavy 3 s が 5.28M txn、旧 verifier で 433.3 s) ので本書は
  予測を固定せず、校正で決める。
- 10 s が適格になるには verifier の未完走 2 型 (balanced の kill、write-heavy の停滞) が解消される必要がある。
  本書の起草時点で、その原因同定と省メモリ化・分割を扱う別 wave (`dev-wave-verifier-capacity`) が進行中
  である。**本書はその成果を前提条件にしない。** 発効時点の verifier で校正し、10 s が適格なら 10 s、
  でなければ 6 s になる。verifier の版は校正と本走で同一に固定し (§5)、途中で変えない。
- read-heavy 6 s の主 process maxrss 80〜86 GiB は node memory 128 GiB に対し余裕が小さい。校正で完走しても
  本走の一部が kill される可能性があり、その扱いは §6.4 (同一 trace の再検証 1 回) に従う。

### 4.4 代替 (採らない)

- **(3a) extime 3 s のまま反復数を増やし、累計 trace 時間で「長時間」に代える。** 採らない。§1.3 項 3 の
  とおり 1 走内でだけ進む状態を捕まえず、仕分け (3) の「長時間実行」にもならない。D2160 の 30 verify /
  候補に反復を足すだけになる。
- **(3c) verifier 容量の改善を前提条件にして extime 10 s を固定する。** 採らない。未着地の別 wave の成果に
  本書の発効を従属させることになる。§4.2 の校正は、改善が着地していれば 10 s を自動的に選ぶ。
- **(3d) verifier wall の上限を撤廃して 10 s を強行する。** 採らない。write-heavy 10 s は 3600 s では未完走で、
  より長く待てば完走するかは未確認である。上限を撤廃すると 1 verify の予算が定まらず、完走の可否が node の
  資源状態に依存する走を判定集合へ混ぜることになる。上限の値 (1800 s) は予算の条件であって正しさの条件では
  ない (§4.2)。

## 5. 反復数、workload、固定条件

- **N_verify = 8 独立反復 / workload** (S-1 (iv 付属) から準用、**削らない**)。3 workload で 24 verify /
  対象。信頼度の指数を観測後に弱める自由度を残さないという S-1 の理由をそのまま継承する (ただし本書は
  信頼度を主張しない、§1.2)。
- workload の動作点 (D2160 と同一): `ycsb_tuple_num=1,000,000`、48 thread、Zipf 0.9、`ycsb_rmw=0`、
  `ycsb_max_ope=10`、`clocks_per_us=2100`、write-heavy (`rratio=5`) / balanced (`rratio=50`) / read-heavy
  (`rratio=95`)、numactl なし。
- build: trace-enabled (`-DCCBENCH_TRACE=1`) の**正しさ専用 build**。性能用 build は作らない。configure の
  残りは対象ごと (案 A: `axis_trigger_gating` の経路が出す flags、案 B: D2160 の検証相の results 稿 §1.2 の
  configure) で、発効束に逐語で写す。toolchain は g++-11 (Ubuntu 11.4.0) を既定とし、発効束で固定する。
- verifier: `python3 -m orchestrator.verifier <trace_dir> --json --expected-commits <commit witness>
  --protocol silo --ccbench-root <checkout>` (別 process)。**verifier module の file 別 sha256 を発効束に
  写し、校正と本走で同一の版を使う。** `--lenient` は使わない (integrity 不良は既定どおり失敗側)。
- 実行: Pegasus gen_S の計算ノード (各 job 1 node、node-local build)。bench と verifier の直前に単独性検査
  (runbook の手順)。1 verify = build (cache 可) → bench → C 行の数え直し → trace の保全 (zstd) → verifier。
  cygnus は使わない。
- bench 失敗 (rc≠0、trace 欠落、commit witness 不一致) の verify は判定集合に入れず、bench を**再生成しない**。
  件数を「規約不適合」として開示する。bench 失敗が 1 件でもあれば pass にならない (§6.1)。
- trace は verify 後に削除せず zstd で保全する (S-1 (iv 付属) が信頼度を主張しない理由の 1 つに挙げた
  「trace の永続保全が無い」への対応。D2160 の runner は本走 48 走 + 校正実走 16 走 = 64 走 × 48 file を
  4.36× に圧縮して保全した)。
  保全先は repo 外 (job dir) とし、path を報告に書く。

## 6. 判定規則

### 6.1 判定集合と 3 値

- **判定集合** = 本走 24 verify (案 B は候補ごとに 24) ∪ 校正 (§4.2) で完走した verdict。
- 判定は次の順に 1 度だけ評価し、最初に成立した値を採る (3 値は排他)。
  1. **失格** = 判定集合に、`anomaly_count` ≥ 1 または verdict が `serializable` でない verify が 1 件以上ある。
     校正・本走のどちらで出ても即失格、再実行しない (絶対規律 2)。
  2. **pass** = 失格でなく、本走 24 verify のすべてが bench 完走・trace 保全済み・verifier 完走・
     `serializable`・certified・`anomaly_count` = 0・identity 一致である。校正の完走 verdict には certified を
     要求しない (校正の役割は extime の決定と anomaly の検出であり、certified でない校正 verdict は件数と理由を
     開示する)。校正の未完走 (indeterminate) は pass を妨げないが、件数と保全先を必ず開示する。
  3. **未確定** = 上の 2 つのどちらでもない (本走の未完走が §6.4 の再検証後も残る、bench 失敗、identity 不一致、
     規約不適合)。未確定は B-8 未取得のままであり、pass に丸めない。
- 判定は runner の集計が §6 を機械適用して出す。**pass は研究の成功宣告ではない** (D12)。

### 6.2 anomaly の構造化報告 (絶対規律 3)

失格の原因になった verify (anomaly を検出した verify、および anomaly 0 件でも verdict が `serializable` でない
verify) について、verifier の JSON から次を逐語で記録し insight に置く: verdict とその理由、witness cycle
(依存の種類 ww / wr / rw と関与する trx の識別子、`--max-report` の既定 20 本まで)、G2 の有無、当該 trace の
保全先と sha256、対象の identity、workload、extime、rep-id。「anomaly が出た」「serializable でなかった」の一言で
終えず、**どの trx 間のどの依存で cycle ができたか**、cycle が無いのに `serializable` でない場合は **verifier が
何を理由にそう判定したか**を残す (後者の原因の確定は本書の範囲外で、失格の判定は変えない)。次の variant 生成は B-8 の scope ではないが、この記録が論文の失敗報告と
S-1b / A-2 の限定の材料になる。

### 6.3 失敗時 (失格) の扱い

- **案 A が失格した場合:** 系側 gate 構成 g_rl / g_rt は正しさを破る variant として無価値になる (絶対規律 2)。
  論文の S-1b (gate on / off の効果) の記述には「独立反復 × 長 extime の検証で失格 (§1.1 の形: anomaly を検出した
  verify i 件、`serializable` でない verdict j 件)」という限定を**追記**
  し、S-1 campaign の certified 記録・`s_prime_final_report.md`・`known_axes_freeze.json` の bytes は
  書き換えない (絶対規律 7: 過去の判定は追記でのみ訂正する)。S-1b を「成立」のまま報告しない。
- **案 B が失格した場合:** 当該候補 (fixed-5 または fixed-10) について、A-2 / [T-1998] / A-6 の性能判定の
  記述に同じ限定を追記する。既存 certified 記録 (別走の正しさ記録) の bytes と判定は変えない。D2160 の
  検証相 (3 s、anomaly 0) の記録も変えず、「3 s では出ず E s で出た」という 2 つの事実として併記する。
- どちらの場合も、失格を性能値・比較へ変換しない。失格は論文で隠さず、pass と同じ強さで報告する。追記の文言は
  §6.2 の記録 (verdict・anomaly 件数・理由) から書き、観測していない anomaly や cycle を書かない。

### 6.4 未完走、再検証、再投入

- 本走 verifier の未完走 (hard timeout / kill / rc≠0 / JSON 破損) は、**同一の保全済み trace に対する再検証を
  1 回だけ**許す (bench は再生成しない)。再検証でも未完走なら当該枠は indeterminate のまま、対象は未確定。
- 校正 verifier の未完走は再検証しない (校正はその extime 以上の打ち切りを決めるだけ)。
- verifier が anomaly を出した枠は再検証しない (絶対規律 2)。
- 未確定で終わった cohort をやり直すときは、本 v1 の下で「同じ規則の新 cohort」として投入し、規則を変える
  なら Erratum (§0) で先に固定する。未確定の cohort の verdict を新 cohort に混ぜない。

## 7. 予算と停止

- **本走の予算: 24 verify の job 実消費 (dispatch Elapse の和) ≤ 14400 s (4 h) / 対象。** S-1 (iv 付属) の
  「総検証相予算 ≤ 4h」の数値を継承する (ただし S-1 の 12 時間総枠の内訳としてではなく、本書独自の上限)。
  校正は別欄で全額を報告し、この上限に含めない。
- 本走の見込み B(E) = Σ_workload 8 × (bench + 数え直し + verifier + 保全) の校正実測 + job 固定費 (setup・
  hydrate・build) × job 数。**B(E) > 14400 s なら、§4.2 の適格集合の共通部分の中で次に大きい値へ 1 段下げる。
  適格集合に無い値へは下げない (校正で不適格だった extime で本走を投入しない)。下げる先が無ければ本走を
  投入しない** (N_verify は削らない)。案 B は候補ごとに判定する。
- 投入後の超過は途中で止めず、判定と別欄に「計画拘束の不充足」として書く。観測値 (anomaly の有無) を
  理由に停止・再測・打ち切りをしない。
- 投入前後で予算を分け、queue 待ち・親の待機は job 実消費に含めない (別欄)。
- job の walltime 予約は、校正 job は D2160 の校正実測の最大所要 × 倍率、本走 job は本書の校正実測の最大所要 ×
  倍率で決め、上限式 (setup + build + bench + 数え直し + 保全 + verifier の hard timeout + 終了余裕) が予約を
  超えないことを投入前に検査する (D2160 の校正では上限式が
  予約 2 h を超えていた、results 稿 §4 項 9)。

## 8. 既知結果台帳と HARKing 境界

本書を書いた時点で既知の、対象・規則に関わる結果を開示する。**これらは本書の判定集合に入れない。**

| 既知結果 | 内容 | 本書との関係 |
|---|---|---|
| D2160 の検証相 (2026-09-19〜20、Pegasus gen_S、現行 verifier) | fixed-5 / fixed-10 の 3 s × 8 反復 × 3 workload = 24 verify + 校正完走 6 (3 s が 3、6 s が 3) = 30 verify / 候補、すべて `serializable`・certified・anomaly 0 | 案 B の候補について、3 s の結果は既知。**6 s の校正 6 verify (3 workload × 2 候補) も完走・anomaly 0 で既知** |
| 同 校正の 10 s | balanced 2 件 SIGKILL、write-heavy 2 件 hard timeout (verdict なし) | §4.3 の見込みの根拠。正しさの情報は無い |
| 07-16 の S-1 検証相校正 (cygnus、旧 verifier、pin `d706650c…`) | g_rl read-heavy 3 s: 433.3 s / maxrss 25.7、6 s: 974.7 s / maxrss 51.4 (記録の `maxrss_gb`)、両方 `serializable`・certified | 案 A の g_rl read-heavy は旧 pin・旧環境で 6 s まで anomaly 0 が既知。現行 pin の identity は異なる |
| S-1 campaign (2026-07、旧環境・旧 pin) | 18 セル × N=8 の各セッションの開発相 correctness で certified (S-1a / S-1b は certified 標本のみ) | 案 A の対象が開発相の短 trace 検証を通っていることは既知。独立反復 × 長 extime の記録は検索範囲に無い (§2.3) |
| A-2 / [T-1998] / A-6 の別走 correctness | fixed-5 / fixed-10 の legacy 1 回 + performance 側 5 回の certified | 案 B の候補の開発相記録。本書は変えない |

**HARKing 境界:**

- §4.2 で extime の候補を {6, 10} s に置き、上限を 1800 s にしたのは、上表の D2160 の 6 s が 3 workload
  すべてで完走し anomaly 0 だったことを知った上での選択である。つまり案 B については「6 s で anomaly 0 が
  出る」という結果の一部を知ってから規則を書いている。本書はこれを隠さず、案 B を選ぶ場合は 6 s の
  結果が**既知結果の追試**であることを報告に添える。
- 案 A については、本書起草時に検索した範囲 (D2160 の results 稿と insight、07-16 の校正 JSON、S-1 の凍結と直接比較
  report、決定台帳) に、現行 pin・現行 verifier での 6 s 以上の verdict は見つからなかった (網羅監査ではない)。
- 判定規則 (§6) は D2160 項 3・5 の規則を継承しており、D2160 の結果を見た後に有利な向きへ変えた点は無い。
  変えた点は「extime の候補集合 ({3,6,10} → {6,10})」「verifier wall の上限 (600 → 1800 s)」の費用側の 2 つと、
  失格条件に「verdict が `serializable` でない」を明示した 1 つ (D2160 項 5 は anomaly だけを書く。緩める向きでは
  なく、anomaly 0 件で `serializable` でない verdict も失格に数える) である。

## 9. 失敗条件 (a)〜(e) の本書版

論文素材の事前登録 (`docs/phase3-main-experiment.md`) が置く失敗条件 (a)〜(e) のうち、本書が扱うのは (a) だけ
である。

- **(a) 合成が certified を破る:** anomaly 1 件で対象は失格、variant は無価値 (§6.1、§6.3)。本書が B-8 を
  取得する経路はこの (a) を長い trace と独立反復で試すことである。失格は正当な結末として最初から認め、
  pass と同じ強さで報告する。
- **(b)〜(e)** (性能差が floor 以下、機械探索で再現、クロスプロトコル最良への劣後、workload 特化の退行) は
  本書の対象外である。本書の pass から (b)〜(e) のいずれについても何も言えない。

## 10. 既存機構での実行可能性の照合

2026-09-20 時点の repo (local main `947fd160a`) で親が実コードと成果物を読んで照合した結果である。「実在」は
部品の存在であって、本書の契約に接続済みという意味ではない。

| 要素 | 既存機構 (所在) | 実在する部分 | 欠ける部分 | 判定 |
|---|---|---|---|---|
| verifier | `python3 -m orchestrator.verifier` (`--json --expected-commits --protocol --ccbench-root`) | 現行版 (2026-09-02 並列化後)、G2 を含む cycle 検出、integrity 判定 | 10 s trace の完走 (balanced kill、write-heavy 停滞。別 wave が扱う)。本書は 6 s で成立しうる | 実装不要 (6 s) / 別 wave (10 s) |
| runner | D2160 の wave の `probe/verify_phase_runner.py` (Codex author 作、**repo 外の job dir**、`calibrate / verify / reverify / summarize / selftest`) | 校正・本走・再検証・集計・trace 保全・identity 検査・単独性検査の一式 | 対象を fixed 2 genome に固定している。案 A の build 経路 (`axis_trigger_gating`)、extime 候補 {6,10}、上限 1800 s、ruling の sha 束縛の分離 (規則 file と追補 file を分ける) | **改版が要る** (Codex author、repo 外に保全) |
| 案 A の build | `patches/silo-backoff-trigger-gating-variant.patch` + `orchestrator/campaign/axis_trigger_gating.py` + `s8a_trigger_sweep._genome(1)`、`buildcache.build(genome, PIN, trace=True)` | S-1 校正器 `s1_verify_extime_calibration.py` が同経路で g_rl を build した実績 (旧 pin) | 現行 pin への厳密適用・trace-enabled build・identity の導出は未実測 (`patch -F0 --dry-run` では `cc/silo/transaction.cc` の全 hunk が当たり、hunk #10 は 13 行の offset) | **試走が要る** |
| 案 A の凍結との関係 | `output/s1-freeze/known_axes_freeze.json`、`IZANAGI_FREEZE_HOLD` (`s1-known-axes.ccbench-submodule-head-pin`) | gate 述語・flags の逐語 | 凍結は pin の前進で hold 中。本書は凍結の照合を経由せず、述語と flags を発効束に逐語で写す。hold の解除は本書の前提条件でない | 実装不要 |
| 案 B の build | `patches/silo-backoff-fixed.patch`、D2160 の configure | 現行 pin で 18 job の build と identity 一致の実績 | — | 実装不要 |
| identity | `source_digest.resolve_evidence` | `src_token` / `source_bytes_sha256` | 案 A の期待値 (試走で導出) | 試走が要る |
| trace 保全 | D2160 runner の zstd 保全 (`-T0 -3`、4.36×) | 保全と manifest | — | runner に含む |
| 単独性検査 | Pegasus runbook の手順、D2160 runner が bench・verifier 直前に実行 | 実行 | — | runner に含む |
| 記録先 | `docs/paper-story/results/` 系列稿、insight、decisions | 先例 (D2160 の 3 点) | 本書専用の consumer (§6 の機械適用) | runner の `summarize` で代替、専用 consumer は作らない |
| phase doc への追記 | `docs/phase3-main-experiment.md` | — | 同文書は `known_axes_freeze.json` の source sha256 として凍結され追記できない (D2160 項 6)。本書は追記を要求しない | 不要 |

**本 docs-only の変更単位では、これらを実装しない。** 実装 (runner の改版) は D95 に従い Codex author の別
変更単位で行い、その認可は本書の作成の認可に含まれない。

## 11. 費用の見積り

算術は D2160 の校正実測 (fixed-5 / fixed-10、Pegasus gen_S、現行 verifier) からの外挿であり、案 A の値では
ない。案 A は校正で決める。

**案 B、extime 6 s、1 候補 (24 verify) の本走:**

| workload | 1 verify の所要 (bench + 数え直し + 保全 + verifier、校正 6 s の実測) | × 8 |
|---|---:|---:|
| write-heavy | ≈ 6.3 + 4.9 + 8.1 + 250 ≈ 270 s | ≈ 2,160 s |
| balanced | ≈ 6.4 + 8.9 + 14.3 + 357 ≈ 387 s | ≈ 3,090 s |
| read-heavy | ≈ 6.3 + 32.2 + 45.5 + 864 ≈ 948 s | ≈ 7,590 s |
| job 固定費 (setup + hydrate + build ≈ 31 s / job、6 job) | | ≈ 190 s |
| **合計 (B(6) の目安)** | | **≈ 13,000 s ≈ 3.6 h** |

- 3 s の本走実消費は 6316 S (fixed-5) / 6134 S (fixed-10) (24 verify、≈ 263 / 256 S / verify) だった。6 s は
  verifier の所要が約 2.1〜2.2 倍になり、read-heavy が全体の 6 割を占める。
- 上限 14400 s (§7) に対する余裕は約 1,400 s であり、node の混雑や保全の遅れで超えうる。超えれば §7 の
  規則で本走を投入しない (6 s より下は無い)。**この見積りは実 wall の予測ではない** — queue 待ち・
  親の待機を含まず、校正実測の 1 点からの外挿である。
- 案 B の 2 候補で ≈ 7.2 h、校正 (各 workload で 6 s + 10 s、10 s の未完走が 3600 s の timeout に達する
  可能性を含む) は候補あたり最大で ≈ 6 s 分 1,600 s + 10 s 分 ≤ 3 × 3,600 s の桁になり、別欄で全額を報告する。
- **trace の保全容量:** D2160 の 64 走 (本走 48 走 = 3 s、校正実走 16 走 = 3 s 6 + 6 s 6 + 10 s 4) で原本
  213.3 GB → zstd 48.9 GB (4.36×)。1 走の trace 量は workload と extime で桁が違うので、本書は 6 s 24 走の容量を
  算術で固定せず、校正で保全した 6 s の 3 走の manifest から本走前に見積もる。桁の目安だけ書く: 64 走を 3 s
  相当に換算すると 54 + 6 × 2 + 4 × 10/3 ≈ 79 走、1 走 (3 s 相当) ≈ 2.7 GB、6 s 24 走 ≈ 130 GB 原本、zstd ≈ 30 GB /
  対象 (extime に比例するという仮定の算術であり、実測ではない)。校正 (10 s を含む) の保全も加わる。保全先の
  空き容量を投入前に確認する。
- **案 A:** verifier の所要は commit 数と依存辺の数で決まり、g_rl / g_rt の 6 s の commit 数は本書の起草時点で
  測っていない。07-16 の旧環境では g_rl read-heavy 3 s の txn 数 (5.28M) は fixed-10 read-heavy 3 s の
  commit 数 (15.4M) の 3 分の 1 程度だったが、環境も verifier も違うので費用の予測に使わない。
- 計算ノード job 数の目安: 校正 3 job (対象あたり、1 job = 1 (workload, 構成) で {6, 10} s を昇順)、本走 6 job × 4 反復 (対象あたり)。

## 12. 発効束、凍結、本書が閉じないもの

発効前に、次の実値と本書の契約を 1 つの対象 cohort へ結び付ける。

- 本走認可の日付、決定 (D) 番号、承認対象の commit、**対象の択 (案 A / 案 B)**。
- 本書の raw bytes の SHA-256 と、その保存先。
- CCBench pin (`pin.CURRENT_PIN` と submodule gitlink の一致)、patch の bytes と sha256、gate 述語・flags の
  逐語 (案 A)、configure の逐語、toolchain の版。
- 対象ごとの identity の期待値 (`src_token`、`source_bytes_sha256`。案 A は試走で導出)。
- verifier module の file 別 sha256、runner の bytes と sha256 (規則 file と追補 file を分ける)。
- 環境: Pegasus gen_S、node の種類、単独性検査の手順、trace 保全先とその空き容量。
- 校正 job の walltime とその根拠 (D2160 の校正実測の最大所要 × 倍率)、上限式の検査結果。
- 既知結果台帳 (§8) の差分。

発効の**後**・本走の**前**に記録するもの (発効束ではない。校正は発効の後に走らせるので、その結果を発効の条件にしない):

- extime の校正結果 (段 A、対象あたり 3 workload × {6, 10} s = 6 行、案 B は 2 候補で 12 行) と、そこから §4.2 で
  機械的に決まった extime、§7 の予算規則で段下げした場合は本走の extime とその根拠 (B(E) の値)。本書の Erratum
  ではなく決定記録と insight に置く (規則は不変)。
- 本走 job の walltime とその根拠 (校正実測の最大所要 × 倍率)、上限式の検査結果、保全先の空き容量の再確認。

この一覧は機械 gate の新設指示ではない。現在ある検査と、文書上の確認と、未実装を区別する。**本 v1 の
変更面は本書と `docs/README.md` の 1 bullet だけである。**

本走認可時にユーザーへ確認する事項 (本書の作成を止める事項ではない):

1. **対象の択** — 案 A (推奨) か案 B か。案 B を選ぶ場合は、論文ストーリー §8 B-8 の仕分け (1) を改める
   裁定を同時に出すか、「B-8 ではなく関連する追加検証」として走らせるかを決める。
2. **「種を変えた」の定義** — §3.2 (独立 process の自己シード、seed 値は記録しない) を B-8 の要件として
   認めるか。認めなければ、seed 注入は別の変更単位 (D16) であり本 v1 の対象外である。
3. **「長時間」の定義** — §4.1 (extime ≥ 6 s、校正で決める、3 s へ丸めない) を認めるか。
4. **B-8 の書き方** — pass の場合に論文ストーリー §8 B-8 を「取得」と書くこと、失格の場合に §6.3 の追記を
   行うことの確認。
5. **費用** — 本走 ≤ 4 h / 対象、校正の別欄、verifier wall 上限 1800 s、案 B なら 2 候補分。
6. **runner の実装** — D2160 runner の改版 (Codex author、repo 外) の認可。案 A なら現行 pin での build・
   identity の試走の認可。試走の結果は判定集合に入れず、既知結果台帳に開示する。
7. **verifier の版** — 発効時点の版で固定すること。別 wave の容量改善を待つか待たないか。

本書は、ユーザーの本走認可、実装の存在、実送達、cold-boot、無人実行、一般的な安全性を代行しない。
S-1 の凍結 (hold) の解除、phase doc への追記、headline・S-1a の判定、A-2 / A-6 / [T-1998] の性能判定を
変えない。既存の結果、certified 選択、材料レポートの値、試行台帳は変更しない。

## 13. 過大主張チェックリストとの整合

`docs/paper-story/2026-09-20.md` §7 の既存項目 (検証相を「S-1 (iv 付属) の充足」「B-8 の取得」「全走
anomaly ゼロ」「serializable であることが示された」と書かない、certified の保証範囲、trace-disabled の性能と
別走の correctness を混同しない、など) に加え、本書の結果を書くときは次を守る。

- 主張は §1.1 の操作的事実に限る。「証明」「保証」「信頼度」を書かない。
- 判定集合の件数、校正の未完走件数、規約不適合の件数、extime、反復数、workload を数値主張に必ず添える。
- 「種を変えた」は §3.2 の定義であることを添え、seed 値は記録していないと書く。
- 「長時間」は「開発相・D2160 の 3 s より長い extime E s」と書き、E の値を書く。
- 案 B の 6 s の結果は既知結果の追試であること (§8) を添える。
- 案 A の pass を S-1a の不成立・S-1b の性格 (結果既知の追試) の変更に使わない。
- 対象の identity は現行 pin・現行 patch に束縛され、旧 pin の S-1 campaign と source bytes が異なることを
  添える。「同一 binary で 24 反復」とは書かない。
- verifier の版と限界 (predicate / phantom / fairness / 未観測実行を保証しない) を添える。
- 失格は隠さず、pass と同じ強さで、§6.2 の構造とともに報告する。
- 配線・文書・hash・lint の成功を、測定結果や機械的強制と呼ばない。

## 14. 本書が閉じないもの (まとめ)

- 本走の認可と実施。runner の改版。案 A の試走 (build・identity)。
- B-8 の要件 (対象・種・長時間) の各定義が論文ストーリーの仕分けを満たすかの最終確認 (発効時のユーザー確認)。
- verifier の 10 s 容量 (別 wave)。extime が 6 s に留まるか 10 s に届くかは校正で決まる。
- S-1 の凍結 hold、phase doc への確定値の追記 (D2160 項 6 の繰延べ)。
- seed 値の記録 (CCBench 改変、D16)。乱数列の独立性の証明。
- (b)〜(e) の失敗条件、B-1 / B-5 / B-7 / B-10、クロスプロトコル、mocc。
- 長さ・反復数の検出力。本書は条件を固定するだけで、その効能を主張しない。
