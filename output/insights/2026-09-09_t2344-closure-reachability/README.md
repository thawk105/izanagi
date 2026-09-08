# [T-2344] enforcement source closure の未収載 module — production 到達性と受理判定寄与の実測

- 実測日: 2026-09-09
- 測定 commit: `2143a49c0c9037b303106eca4cfc346797d3f1b3` (記録時の main は `b57e35426`。
  閉包の寸法は両 commit で完全一致することを再測して確認した)
- 根拠裁定: D1513 (2026-09-02 ユーザー裁定。「今は決めない。先に 69 module の production 到達性と
  受理判定への寄与を実測し、その結果を持って改めて諮る」)
- 上位裁定: D1075 (推移閉包へ広げる。段階実装可。保証の文言は閉包が閉じるまで広げない)
- 本 wave の性格: 調査のみ。repository の実装面の差分はゼロ。測定道具はすべて repository の外に置いた。
- 収載するかしないかの判断は本 wave では出さない。裁定パッケージとして最後の節に置く。

## 結論の要約

1. **未収載の module は、認証の受理を決める経路で実際に動いている。** 認証受理 API を実 campaign
   50 本に対して走らせると、未収載のうち 4 本が関数本体まで実行され、12 本が module 本体だけ実行された。
   freeze / spec の検証経路ではさらに別の 6 本が関数本体まで実行された。
2. **ただし「動いている」と「受理の可否を変える」は別で、後者は今回の corpus では確認できなかった。**
   実行済みの分岐を 1 個ずつ反転する反実仮想を 10 か所で行い、受理の判定が変わった例は 0 件だった。
   7 件は module 自身の自己検査が import 時に発火して入口ごと停止する「可用性依存」で、3 件は判定不変または
   反転できる分岐が無かった。**この 0 件は非寄与の証明ではない** — 手元の 50 campaign はすべて拒否され、
   受理へ抜ける深い経路が 1 度も実行されないためである。
3. **裁定の枠組み自体に穴がある。** 「残り 69 (現行 77) module」という候補集合は、収載 tuple から
   静的 import を辿って作られている。そのため**認証成果物を発行する module 自身が候補集合の外**にある。
   全部収載しても発行器は束縛されない。発行器を起点に同じ展開をすると候補集合は 160、
   収載 tuple 起点の 140 と合わせて 165 になり、未収載は 77 ではなく 102 になる。

## 引数と carry の前提のうち、実測で覆したもの

carry (worklog archive `worklog-phase3-0905-1279.md` の `[T-2344]`) と D1513 は
「第 1 層 62 path」「残り 69 module」「全 131」と書いている。現行はどれも違う。

| 集合 | 2026-09-02 (`a94ba713b`) | 2026-09-09 (`2143a49c0`) |
|---|---|---|
| 収載 tuple (`CONTRACT_LOADER_RELATIVE_PATHS`) | 62 | **63** |
| tuple 起点の静的 import 発見集合 | 131 | **140** |
| 未収載 | 69 | **77** |
| producer 起点の発見集合 | 未測 | **160** |
| 両者の和 | 未測 | **165** (未収載 **102**) |

63 になったのは T-2429 (2026-09-08) が `orchestrator/campaign/verify_fanout_worker.py` を
足したためである。`campaign_lock.py` の comment も既に「exact 63 path」と書いている。

### 測定道具の正例対照

閉包を数える probe が T-733 の測定を再現するかを、実際の歴史 commit に対して確かめた。

- `a94ba713b^` (拡張前) の収載 24 から 1 段展開すると 62 になり、T-733 が着地させた 62 tuple と
  **集合として**一致した (両方向の差集合が空)。内訳も「新規の明示 import 先 36 + 実行時 package
  初期化 2」で一致し、初期化の 2 本は `orchestrator/critic/__init__.py` と
  `orchestrator/qualification/__init__.py` だった。
- 同 commit の全展開も 131 / 未収載 69 で、先行 insight の記録と一致した。

**順序は一致していない。** probe は集合を sort して返すのに対し、着地した tuple は curated 順である。
tuple 順は epoch の preimage に効くので、「bit 単位で再現した」とは書けない。再現したのは
**member 集合と件数**である。これは段 3 のレンズ A の指摘を採って直した。

### 第 1 層すら閉じていない

T-733 が名乗った「pre-T733 の 24 path から直接委譲される 1 段目まで収載した」は、
現行 HEAD では成立しない。24 seeds から 1 段展開すると 64 になり、収載 63 に含まれない 2 本が出る。

| 未収載の 1 段目 | どこから import されるか |
|---|---|
| `orchestrator/calibrator/analyze.py` | `orchestrator/campaign/pipeline.py:33` |
| `orchestrator/campaign/backoff_hole_grammar.py` | `orchestrator/campaign/wal.py:40`、`orchestrator/campaign/loop.py:26` |

どちらの import も `a94ba713b` には無く、T-733 の着地後に入った。閉包は自分では追随しない。

## production 到達性

### 3 つの層を分けて数える

静的 import の発見集合は**上界**である。`ast.walk` は関数内 import も条件分岐内 import も拾うため、
「発見集合に居る」は「production で走る」を意味しない。そこで実行時に 3 層を分けて観測した。

- **import 到達**: 対象を import したとき `sys.modules` に載るか。
- **module 本体の実行**: import 時に module 本体 (と class 本体) の行が実行されたか。
- **関数本体の実行**: module 初期化ではなく、関数・method の中の行が実行されたか。

観測は commit 固定の blob と disk bytes を照合する専用 loader で行い、`.pyc` は一切読まない。
trace は入口の import より**前**に設置してあるので、import 時の実行も観測に入る。
frame の種類は `co_flags` で判定する — `CO_OPTIMIZED` があれば関数、無くて `CO_NEWLOCALS` があれば
class 本体、どちらも無ければ module 本体である。

### 観測点

repository の中で認証成果物の発行・受理を実際に決める入口を 2 つ選んだ。

1. **認証受理 API**: `orchestrator/campaign/artifact_admission.py` の
   `require_admitted_campaign(..., CampaignReadPurpose.CERTIFIED_ACCEPTANCE)` と
   `require_certified_commit_evidence()`。実 campaign 50 本 (repository 内 30、外部測定 root 20) に対して走らせた。
2. **freeze / spec の検証経路**: oracle report の発行 CLI が観測を作る前に必ず通す
   `s8b_ratified_freeze.load_ratified_freeze` → `assert_g1_floor_selection_identity` →
   `reverify_published_freeze` → `s8b_oracle_spec.load_approved_spec`。

### 結果

| 入口 | 未収載で関数本体まで実行 | 未収載で module 本体だけ |
|---|---:|---:|
| 認証受理 API (repository 内 30 campaign) | 4 | 12 |
| 認証受理 API (外部 20 campaign) | 4 | 12 |
| freeze / spec 検証 | 6 | 11 |

認証受理 API で関数本体まで実行された 4 本:

| module | 実行行数 |
|---|---:|
| `orchestrator/campaign/sort_swo_oracle.py` | 188 |
| `orchestrator/campaign/materializer_admission.py` | 15 |
| `orchestrator/campaign/coder_effect_gate.py` | 8 |
| `orchestrator/campaign/backoff_hole_grammar.py` | 2 |

freeze / spec 検証で関数本体まで実行された 6 本:
`sort_swo_oracle.py` (188)、`s8b_ratified_freeze.py` (105)、`s8b_oracle_manifest.py` (14)、
`materializer_admission.py` (15)、`s8b_holdout_freeze.py` (8)、`t080_freeze_migration.py` (3)。

同じ入口で実行された収載 member は認証受理 API (repository 内) で 14 本、外部 corpus で 12 本、
freeze 経路で 8 本だった。未収載で関数本体まで実行されたものは、3 つの入口の和で 8 本になる。
収載 member 側で最も多く実行されたのは `artifact_admission.py` の 253 行である。

### 参考: import 到達だけの数字

収載 member 63 本と認証 consumer 6 本をそれぞれ単独 import すると、未収載 77 のうち 45 本が
収載 member の import だけで載り、7 本が consumer の import で載り、25 本は載らなかった。
ただし**この数字を到達性として使ってはならない。** 実際の gate (`contract_loader_binding.py` の
`capture_contract_loader_binding()`) は 63 本の bytes を読んで hash するだけで、63 本を import しない。
「収載しているから import する」実験で載った module を「gate が使う材料」と読むと、
収載という前提が到達性を作り、その到達性で収載拡大を正当化する循環になる。

## 受理判定への寄与 (反実仮想)

### 測り方

「寄与」を「その module の挙動を変えると受理の判定が変わる」と定義し、実際に変えて確かめた。

- 変更は **memory 上だけ**で行う。repository の file は 1 byte も変えていない。
- 変更内容は、**baseline で実行された `if` の条件を 1 個だけ否定する**こと。型は保たれる。
- 変更が実際に発火したことを、mutant 実行でその行が line event を出したことで確認する。
- 判定 vector は「受理された campaign の集合」と「campaign ごとの拒否の種類と理由コード」の組。
- 入口が例外で止まった場合は、vector が変わっていても **C+ ではなく可用性依存 (CD)** とする。
  判定面まで到達していないためである。

### 結果 (認証受理 API、10 site)

| 分類 | 件数 | 意味 |
|---|---:|---|
| C+ (判定が変わった) | **0** | — |
| CD (可用性依存) | 7 | module 自身の自己検査が import 時に発火し、入口ごと停止した |
| C0 (発火したが判定不変) | 1 | — |
| C? (反転できる分岐が実行行に無い) | 2 | — |

CD の 7 件は `coder_effect_gate.py` の 2 か所 (`effect categories must be unique`、
`effect identifiers must belong to exactly ...`) と `sort_swo_oracle.py` の 5 か所である。
いずれも「この module が壊れていると認証経路は動かない」ことを示すが、
「この module が受理の可否を決めている」ことは示さない。

### この 0 件をどう読むか (重要)

**非寄与の証明ではない。** 理由は 3 つある。

1. **baseline が受理を 1 件も出していない。** repository 内 30 campaign は `E0`
   (`v1-authority-absent`)、外部 20 campaign は campaign.lock の exact key 集合不正で拒否される。
   受理へ抜ける深い経路は、この機械のどの corpus でも実行されない。
2. **1 module につき最大 6 か所の変異しか試していない。** ある変異が判定を変えなかったことは、
   その module 全体が非寄与であることを意味しない。
3. **module 本体だけ実行された 12 本と未観測の module には、反実仮想を回していない。**

## 代償側の実測

D1513 は「代償は実測済み、便益が未測」と述べている。代償側も数字を取り直した。

### 1. epoch を動かしうる commit の頻度

`2026-08-10` から測定 commit `2143a49c0` まで (commit 7008 本):

- 収載 member に触れた commit: **312**
- 未収載 module に触れた commit: 358 (うち収載 member に触れていないもの **253**)
- 未収載のうち 30 日間 1 度も触られていない module: 14

全 140 まで広げると、epoch を動かしうる commit は 312 から 565 (+81%) になる。
これは **commit 境界での潜在的な epoch 変更**であり、実際に発行された epoch の回数ではない。
成果物を発行しない中間 commit も 1 件と数えるため過大に出る。逆に、tuple 変更そのものの一回限りの
代償は含んでいないので過小にも出る。

### 2. 記録済み lock が読めなくなる代償 (実行して確かめた)

repository と外部測定 root にある campaign.lock 48 本を、実際の decoder 2 本に通した。

| lock が持つ key 数 | 件数 | 認証 decoder | 歴史 decoder |
|---|---:|---|---|
| authority 無し (E0) | 32 | — | — |
| 24 (pre-T733) | 13 | 拒否 | **通る** |
| **62** | **3** | **拒否** | **拒否** |
| 63 (現行) | 0 | — | — |

**exact-62 の 3 本はどちらの経路からも読めない。** 実体は paper-story A-2 の t2364 系列
(2026-09-07 記録、rr5 と rr50) と A-6 系列 (2026-09-08 記録、rr95) の campaign.lock である。
T-733 が 62 へ広げたときは pre-T733 の 24 用に歴史 grammar を用意したが、
T-2429 が 63 へ広げたときに 62 用の歴史 grammar が用意されなかった。

これは「閉包 member を 1 本足すと、その前に記録された lock がすべて読めなくなる」という代償が
**実際に発生した事例**である。77 本足す判断は、同じことを 1 回起こす判断でもある。

**ただし今この 3 本が何かを壊しているわけではない。** A-2 の図の生成器を両 root に対して実際に
走らせると、exact-24 の t2022 系列は通り、exact-62 の t2364 系列は通らない。しかし t2364 側の
失敗理由は lock の decode ではなく、生成器が現行の certification / manifest から組み立てる計画に
含まれる別の campaign の WAL が t2364 root に無いこと (`external input missing: .../wal.jsonl`) である。
つまり **exact-62 の 3 本は現時点でどの consumer からも読まれていない**。
機構としての破れは実在するが、影響は潜在である。この 3 本を読む必要が生じた時点で顕在化する。

## 候補集合そのものの欠落

段 3 のレンズ A が指摘し、親が裏取りした。**認証成果物を発行する module 自身が候補集合の外にある。**

| module | 役割 | tuple 起点の発見集合 140 に居るか |
|---|---|---|
| `orchestrator/campaign/s8b_oracle_report.py` | oracle report を発行する CLI | **居ない** |
| `orchestrator/campaign/s8b_abort_reason_contract.py` | abort 理由の受理を決める | **居ない** |
| `orchestrator/campaign/s8b_outcome_stage_contract.py` | outcome と段階証拠の受理を決める | **居ない** |
| `orchestrator/campaign/autonomous_trial_completeness.py` | 認証受理を要求する consumer | **居ない** |
| `orchestrator/campaign/b10_backoff_shape_sweep.py` | 同上 | **居ない** |

候補集合は「収載 tuple から import を辿る」規則で作られているので、**発行器のように
tuple から辿られない側は構造的に入らない**。したがって「140 へ全部広げる」は
「認証経路が source-bound である」を推移閉包の意味で成り立たせない。

発行器 6 本を起点に同じ展開をすると 160 module になり、tuple 起点の 140 と合わせて 165、
未収載は 102 になる。

## 成果物へ出る保証の文言が実態とずれている

`orchestrator/campaign/artifact_admission.py` の
`CAMPAIGN_VERIFIER_EPOCH_SCOPE` は「curated exact 62 path」「2026-09-01 の静的 import 発見集合
131 module」、`CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE` は「同発見集合の未収載 69 module」と
書いたままである。現行は 63 / 140 / 77 である。

この 2 定数は `orchestrator/campaign/s8b_oracle_report.py` が oracle report の
`identity_scope` / `excluded_scope` へ書き出す。つまり**実際に束縛している集合と、
成果物が名乗る集合が食い違っている。** 束縛そのもの (exact-63 の key 集合検査) は正しく効いているので、
受理集合は現状のまま正しい。誤っているのは説明文である。本 wave では直していない。

## 自分の測定で見つけて直した誤り

裁定に使う数字なので、途中で直した分も残す。

1. **class 本体を関数実行と数えていた。** `co_name != "<module>"` で判定していたため、
   dataclass の field 定義など import 時に必ず走る class 本体が「関数まで実行された」に混ざり、
   未収載の実行を 11 本と数えていた。`co_flags` で 3 種を分けたところ 4 本になった。
2. **反実仮想の分類順序が誤っていた。** 入口が例外終了した mutant を、判定 vector が変わったという
   理由で C+ に分類していた。入口が判定面へ到達していないので CD が正しい。直す前は C+ 2 件、
   直した後は 0 件である。
3. **撤回した測定が 1 件ある。** 最初に書いた実行到達性 probe は、対象を import した**後**に
   profiler を設置していた。そのため import 時の実行を構造的に観測できず、
   「未収載の実行 0 件」という結果を出していた。段 3 のレンズ A がこれを指摘した。
   この結果は撤回し、import より前に trace を張る probe の結果で置き換えた。

## 段 3 の敵対レビューの裁定

レンズ A (正しさ境界) とレンズ B (整合と実効性) を並列で走らせた。主な所見の裁定は次のとおり。

| 所見 | 裁定 | 対応 |
|---|---|---|
| 候補集合に発行器が居ない (A) | real | 親が裏取りして本 insight の主要結論に採用した |
| 実行到達性 probe が import 前の実行を落とす (A) | real | 該当測定を撤回し、置き換えた |
| 「bit 単位で再現」は過大 (A) | real | 「集合と件数の一致」に直した |
| 1 変異の null を module 全体の非寄与と読むな (A) | real | 分類の単位を module でなく変異箇所にした |
| import 到達を受理材料と読むのは循環 (A) | real | 参考値として層を分け、到達性としては使わないと明記した |
| 判定 vector に拒否の種類と理由を入れよ (A) | real | 実装済み (受理集合だけでなく拒否理由も vector に入れた) |
| epoch churn は実発行数でなく commit 境界の潜在数 (B) | real | 名前と限定を本文へ入れた。終端 commit と path 別内訳も記録に足した |
| tuple 変更の一回限りの非互換が未計測 (B) | real | lock 48 本を実 decoder に通して計測し、exact-62 の 3 本を見つけた |
| 中間案を選べる形の出力が要る (B) | real | 裁定パッケージに候補を並べた |
| 受入検査の増分が未測 (B) | real・本 wave では未実施 | 裁定パッケージで「測るなら次の wave」と明記した |
| `enrolled ⊆ discovered` を恒久 gate へ (B) | scope 外 | 機構追加は本 wave の scope 外。裁定候補として記す |
| production 入口の恒久 registry (B) | scope 外 | 同上 |

## 測定の射程 (この結論が言えないこと)

- 観測点は認証受理 API と freeze / spec 検証の 2 つである。repository 全体の production 入口を
  網羅していないので、**ここで実行されなかった module を「到達不能」とは言えない。**
- 反実仮想の 0 件は、受理が 1 件も出ない corpus 上での 0 件である。
- 別 interpreter の subprocess を起動する経路があれば、その中の実行は観測できていない。
  今回の 2 入口では、観測対象の外部 process 起動は無かった。
- 静的発見集合は import 文だけを辿る。data file、生成物、外部 command、動的 import による委譲は
  最初から対象外であり、これは D1651 が既に文言へ書いている限定と同じである。

## 裁定パッケージ

D1513 が求めた実測は揃った。ここから先は決めていない。選択肢と、それぞれで確定する量を並べる。

### 前提として先に決めたほうがよいこと

- **候補集合の定義を、収載 tuple 起点のままにするか、発行器起点を足すか。** ここを決めないと
  「閉包が閉じた」の意味が定まらない。tuple 起点のままなら上限は 140 (未収載 77)、
  発行器起点を足すと 165 (未収載 102) になる。
- **閉包を 1 本でも動かすなら、その版の歴史 grammar を同時に用意するか。** 用意しないと、
  直前に記録された lock が両経路から読めなくなる。exact-62 の 3 本で既に起きている。

### 選択肢

1. **現行 63 を維持し、保証の文言を実態 (63 / 140 / 77) へ合わせる。**
   代償ゼロ。ただし D1075 が命じた「推移閉包へ広げる」は未達のまま固定される。
   1 段目の未収載 2 本が残るので、「直接委譲の 1 段目まで収載した」という説明も同時に直す必要がある。
2. **1 段目の drift 2 本だけ足して 65 にする。** T-733 が名乗った状態を回復する最小の案。
   epoch churn の増分は小さい (`analyze.py` と `backoff_hole_grammar.py` の 2 path 分)。
   ただし推移閉包にはならない。
3. **現行 63 からの 1 段目 18 本を足して 81 にする。** 段階実装の次の 1 段。
4. **実測で production 経路に到達した module だけ足す。** 認証受理 API と freeze 経路で
   関数本体まで実行された未収載は、重複を除いて 8 本 (`sort_swo_oracle`、`materializer_admission`、
   `coder_effect_gate`、`backoff_hole_grammar`、`s8b_ratified_freeze`、`s8b_oracle_manifest`、
   `s8b_holdout_freeze`、`t080_freeze_migration`)。ただしこれは「静的 import 推移閉包」とは
   名乗れないし、corpus が変われば集合も変わる。
5. **発見集合 140 まで広げる。** epoch を動かしうる commit が 312 → 565 (+81%)。
   それでも発行器は束縛されない (上記の欠落)。
6. **発行器起点を含む 165 まで広げる。** 「認証経路が source-bound」を推移閉包の意味で
   名乗れる唯一の案。代償は 5 より大きく、未測。

### 決める前に測っておくと良いもの (本 wave では未実施)

- 候補集合ごとの受入検査の増分件数と所要時間。D1513 が引用する「190 件増」は T-733 時点の値で、
  現行の増分は測っていない。
- 受理へ実際に抜ける campaign を 1 本用意したうえでの反実仮想。今回の 0 件はこれが無い状態の 0 件である。

## 再現手順と成果物

測定道具は repository の外 (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-reachability/`)
に置いた。逐語は `verbatim/` に置いてある。

| ファイル | 内容 |
|---|---|
| `closure-head.json` | 測定 commit での収載 63 / 発見 140 / 未収載 77 と import edge |
| `closure-control-pre-t733.json` | `a94ba713b^` の 24 から 1 段展開した 62 (正例対照) |
| `closure-t733-landed.json` | `a94ba713b` での 62 / 131 / 69 (正例対照) |
| `producer-universe.json` | 発行器起点の 160、和 165、未収載 102 |
| `trace-admission-repo.json` | 認証受理 API を repository 内 30 campaign に対して走らせた trace |
| `trace-admission-external.json` | 同、外部 20 campaign |
| `trace-freeze.json` | freeze / spec 検証経路の trace |
| `counterfactual-admission.json` | 反実仮想 10 site の結果 |
| `epoch-churn.json` | commit 境界の潜在 epoch 変更と path 別内訳 |
| `lock-grammars.json` | 記録済み lock 48 本の key 数の内訳 |
| `decode-matrix.json` | 各 lock を認証 decoder と歴史 decoder に通した結果 |
| `import-reachability.json` | 参考値。単独 import での到達 (到達性としては使わない) |
| `consumer-cohort-check.json` | A-2 図の生成器を exact-24 / exact-62 の両 root に対して走らせた結果 |
| `verbatim/probe-closure.md` | 閉包を数える probe の逐語 |
| `verbatim/probe-production-trace.md` | production 入口を trace する子 process の逐語 |
| `verbatim/probe-counterfactual.md` | 反実仮想の driver の逐語 |

再現するには、`verbatim/` の 3 本を repository の外へ書き出し、測定 commit を引数に渡す。
`probe-production-trace.md` の子は `python3 -I -B` で起動し、起動時に `orchestrator` が
既に import されていれば測定を無効にする。
