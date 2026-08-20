# [T-189] model routing 比較実験 事前登録文書

> 対象: dev-wave 段2(plan)・段5(author) の codex model 選択 (`gpt-5.6-sol` 対 `gpt-5.6-luna`)。
> 状態: exploratory pilot の事前登録。実験走行・`qsub`・production の model routing 変更は
> 本文書の対象外 (D87)。
> 段3 敵対相談2レンズ (統計的妥当性・運用実現性) の所見16件を段4裁定で採用・反映し、
> 段6 敵対レビューが指摘した未閉包17件 (blocker8・major5・新規4) も fix で反映した
> (`routing_evidence_status` の3値化、§12 判定表の全面書き換えが中心)。

## 1. 目的・射程

D423 は、dev-wave 段2(plan)・段5(author) の codex model を、品質証拠なしに `gpt-5.6-sol` から
`gpt-5.6-luna` へ変更することを認めていない。paired・blind・held-out 複数 task・独立 oracle・
block randomization・cache 条件の分離・価格 version・事前登録済み非劣性 margin を備えた比較実験が
得られた場合にのみ再訪できる、としている。

D514 (2026-08-18) により、dev-wave は既に全段 `gpt-5.6-luna@max` へ統一されている。
`docs/dev-wave/operations.md` の DW-O01 権威行も次のとおりである。

```text
`<model>`: 全段 `gpt-5.6-luna` (段 3 の 2 本も同じ)。
```

D514 はこの変更を品質同等性の証拠ではなく費用に基づく運用選好として記録している。したがって
本実験の目的は変更前の事前判断ではない。先行した全 luna 化が持つ品質リスク (段3・段6 の検出
レンズが同一 model になったことによる系統的盲点) を事後検証し、将来の証拠に基づく sol 復帰
またはハイブリッド復帰の当否を判断可能にすることである。

**本文書が設計するのは exploratory pilot である。** 段3 の敵対相談 (統計レンズ) が、現実的に
確保できる held-out task 規模 (§6 参照、8〜10 task-stage 程度) はもとより、当初目標とした
24 task-stage であっても、confirmatory な非劣性を実証できる標本数に届かないことを算術的に
示した (§11 参照)。本文書は「非劣性を証明する実験」ではなく、**効果量を推定し、真に
confirmatory な実験に必要な標本数を再計算するための pilot** として設計する。これは D423/D207
の精神 (検出力を偽装しない、正しさシグナルを後付けで甘くしない) に沿った選択であり、甘い基準で
confirmatory を偽装する方向は取らない。

本実験の estimand は **requested model (要求 slug)** に対する差である。receipt、
`turn_context.model`、ledger に現れる model 名は要求値の echo として扱い、served model の証明
とは扱わない。F56 のとおり現行装置には served model attest 経路がないため、served model は
`unknown` と記録する。

比較対象は次の二つである。

- reference: `requested_model = gpt-5.6-sol`
- treatment: `requested_model = gpt-5.6-luna`

両 arm の `reasoning` は `max` に固定する。reasoning の `high`/`max` 比較は T-181、D243、D266 の
射程であり、本実験では model 軸と混同しない。

## 2. 対象・非対象

| 段 | 本実験での扱い |
|---|---|
| 段2 plan | 対象。同じ task、同じ snapshot、同じ prompt を sol/luna へ paired 投入する |
| 段5 author | 対象。固定した同一 plan と task context を sol/luna へ paired 投入する |
| 段3 敵対相談 | 非対象。D241 により sol/luna 混成が確定済み。ただし T-189 の結果は `2026-08-08_t182-luna-stage3-hybrid.md` の rollback 条件 (b) の材料になる |
| 段6 review/fix/focus | 非対象。D243/D266 の reasoning 軸を扱わず、model 比較 arm にも含めない |

段2の比較では、段5以降の入力を固定して plan model の差だけを測る。段5の比較では、歴史 task の
plan または事前登録済み固定 plan を両 arm に共通投入し、author model の差だけを測る。段2の
sol/luna 出力を段5へ流し、二つの model 軸を同時に変える end-to-end 比較は主解析にしない。

## 3. Estimand と解析手法 (段4裁定 A2/A5 反映)

段3 統計レンズが、主指標の分母・独立性・resampling 手法が未固定だと micro-average と
task-level 差のどちらを使うかで分析者自由度が生じ、層内 task 数が少ない場合 (最悪 4 task/層)
は bootstrap の resample 空間が数百通り程度に退化して margin を識別できないと指摘した (段3所見
A2, A5)。これを踏まえ、次を実験開始前に確定する (§13 lock 対象)。

- **primary estimand の式 (段6所見 A2/B7 反映)**: task-level coverage を次で固定する。

  ```text
  coverage(task, arm) = (両 reader が検出と一致した oracle finding 数)
                         / (その task の oracle finding 総数)
  ```

  oracle finding が0件の negative control task は §11.3 の false-finding 系列でのみ扱い、
  この coverage 式の対象 (positive task の分母) には含めない。primary estimand は
  `mean_task( coverage(task, luna) - coverage(task, sol) )` とし、task 間の平均は
  §6.2 の task type 層の実効 task 数に比例した層別重みを使う (層の目標数ではなく実際に採用した
  task 数で重み付けする)。finding-level の micro-average (§8.2 の記述的 coverage) は副解析に
  格下げし、同一 task 内 finding の相関を無視した過大な有効 n として primary に使わない。
- **解析手法とパラメータ (段6所見 A5 反映)**: task-cluster を resampling 単位とした片側 exact
  sign-flip permutation を primary とする。列挙単位は task-level paired 差の符号、統計量は
  層別重み付き平均差、片側有意水準は `α = 0.05`、信頼限界は permutation 分布の分位点から構成する。
  tie (差が 0 の task) は帰無仮説に有利な方向 (符号をランダムでなく両方向に数える保守的な扱い)
  とし、欠測 task (§4.1 の技術失敗) は §4.1 の ITT 規則に従って予定した符号割当のまま残す。
  層内 task 数が §11.1 の `N_positive_min` に満たない stage は、この手法でも識別力が乏しいため
  confirmatory 判定を出さず descriptive に限定する (§12 判定表)。
- 欠測・タイ・ゼロ差の扱いは、上記のとおり実験開始前 lock 時に固定し、実走後に変更しない。

## 4. 実験単位と paired protocol

一つの task-stage 組を実験単位とする。各単位には、同一の次の入力を使用する。

- task prompt bytes
- repo snapshot と snapshot manifest
- stage
- task type
- 固定した reasoning effort (`max`)
- cache condition
- oracle manifest
- downstream replay 条件

一つの task-stage 組から、sol と luna の二つの run を作る。二つの run は一つの block に属し、
block 内で一方の model を一度ずつ実行する。出力を相互に見せたり、一方の出力で他方の prompt を
変更したりしない。

段2では、各 model の plan を同一の固定 downstream replayer に投入し、acceptance に至るまでの
fix 巡回数を測る。段5では、同一の固定 plan を用いて author output を比較し、同じ downstream
replayer で fix 巡回数を測る。downstream model と effort は両 arm で固定する。

### 4.1 欠測処理 (段4裁定 A8 反映)

技術的な再試行は、出力内容を見て決めない。

- treatment 開始前の launcher、snapshot、receipt、cache context などの技術失敗だけは、同じ
  block の両 arm を一組として最大3世代まで再試行する。
- treatment 開始後の失敗は `post-treatment` として記録し、結果を救済する再走はしない。
- pair の片方が技術失敗した場合、もう片方だけを有効 run として数えない。
- `model_calls=0` や 400 拒否を「finding 0件」と採点しない。requested model の技術的無効 run
  として扱う。
- **primary 解析は intention-to-treat (ITT) とする。** 予定された全 pair を分母に含め、model
  拒否・post-treatment failure・cap-exceeded は事前定義した「品質/運用失敗」として扱う。
  per-protocol 解析 (技術失敗 pair を除外した解析) は感度分析に限定し、primary の代替にしない。
  片方だけ失敗した pair を解析から静かに落とせば、最悪例を除外して結果を良く見せる方向に開くため
  (段3所見 A8)。
- **provenance 無効と post-treatment outcome failure を区別する (段6所見 A8)。** §12「装置・
  provenance」gate が無効とするのは、schedule・prompt・snapshot・oracle・price version・receipt
  の hash mismatch や欠測など、**treatment 開始前**の束縛が壊れているケースに限る。この場合
  当該 task-stage 組は解析から除外し、実験全体の provenance 無効として扱う。一方、model 拒否・
  400・`post-treatment` 失敗は **treatment 開始後**の outcome であり、ITT の対象として予定通り
  分母に残し、「finding coverage 0、fix cap-exceeded 相当」の品質/運用失敗として採点する。
  この2種類を同じ「無効」として混同しない。

## 5. 装置設計と実装時の申し送り (段4裁定 B1/B2/B7 反映)

### 5.1 再利用する T-181 の骨格

T-181 (`tools/codex_reasoning_ab.py`) の次の契約を再利用する。

1. apparatus pin による装置、repo HEAD、Codex CLI、sandbox、config/auth の固定
2. snapshot の before/after oracle replay
3. schedule.json の block 固定と schedule hash
4. block 内の二つの arm の逐次実行
5. run receipt と token/cache/wall の保存
6. `make-packets` による opaque packet 化
7. custodian による packet-to-run mapping の隔離
8. 親 reader と独立 second reader の verdict freeze
9. mapping reveal 後の `aggregate`/`verify` による replay 認証

T-181 と同じく、実走中に装置や判定器を変更しない。T-181 で発生した F176 型の採点器修正を実走後に
行うことも禁止する。

### 5.2 model 軸への変更点 (実装は本 wave の scope 外)

段3 運用レンズが、以下の申し送りを file:line 実測で検証し、当初案が変更閉包になっていない
(定数・receipt schema・manifest replay・adjudication・CLI・score 層を含む横断的 refactor である)
ことを指摘した (段3所見 B1)。**「軽微な拡張」ではなく装置全層に及ぶ変更として申し送る。**

| 箇所 | 必要な変更 |
|---|---|
| `tools/codex_reasoning_ab.py:49` | `MODEL = "gpt-5.6-sol"` の単一 hard-code を routing authority にしない。`requested_model` を schedule slot から渡す |
| `tools/codex_reasoning_ab.py:161-170` | `EXPECTED_SCHEDULE`/`KNOWN_FINDINGS` の固定集合を、task catalog から生成する可変集合に変更する |
| `tools/codex_reasoning_ab.py:2511-2525` | `_normalized_exec_argv` に model slug の一意性・許可集合検査を追加する。model は treatment identity なので effort のように消去しない |
| `tools/codex_reasoning_ab.py:2544-2590` | `_launch_identity_value` に `requested_model` を含め、sol/luna の treatment identity を別物として固定する |
| `tools/codex_reasoning_ab.py:2627-2641` | `_codex_exec_argv` の引数へ `requested_model` を追加し、現在 `MODEL` を使っている `-m` 生成箇所 (`:2634-2635`) を `-m <requested_model>` に変更する。`model_reasoning_effort=max` は別引数として維持する |
| `tools/codex_reasoning_ab.py:2742-2994` | `_supervise_one` が slot の `requested_model` を読み、launch receipt (`:2864-2925`)、actual argv、completion receipt (`:2964-2984`、現状 model を含まない) に記録する |
| `tools/codex_reasoning_ab.py:2997-3268` | `supervise_pair` (現状 `:2997-3062` で単一 snapshot/prompt しか受けない) が同一 task の sol/luna block を検証し、model 順序を schedule に従って交互化する |
| `tools/codex_reasoning_ab.py:3301-3590` | launch receipt 検査を requested model 対応にし、実際の argv の `-m`、receipt、turn context の一致を fail-closed で検査する |
| `tools/codex_reasoning_ab.py:3606-3761` | `collect_run` の `expected_model=MODEL` 既定値を廃止し、slot 由来の `expected_requested_model` を検査する。served model と呼ばない |
| `tools/codex_reasoning_ab.py:4012-4090` | task-specific な入力処理層 (POS/NEG 固定処理の周辺) を task manifest 経由に拡張する |
| `tools/codex_reasoning_ab.py:4419-4490` | `_validate_schedule` (`:4427-4449`) の固定された `POS/NEG` × `max/high` 検査を、task、cache condition、`requested_model`、`price_version` の paired schema へ拡張する |
| `tools/codex_reasoning_ab.py:4493-4709` | adjudication 層を task-specific oracle (§5.3) に対応させる |
| `tools/codex_reasoning_ab.py:4849-4970`, `5232-5597` | `aggregate`/`verify`・manifest replay を task、stage、requested model、cache condition ごとに集計できるようにする。10 slot、`max/high` の hard-code を残さない |
| `tools/codex_reasoning_ab.py:5631-5792` | `make_packets` の10 slot固定を廃止し、task 数を manifest から取得する。public packet に model、stage、task_id、price version を出さない |
| `tools/codex_reasoning_ab.py:5793-6031` | `append-verdicts`、`freeze-verdicts`、`reveal-mapping`、mapping 出力層は T-181 と同じ順序で再利用し、oracle finding ID と cache/price の欠測も verdict/manifest に束縛する |

現在の T-181 実装は reasoning 軸専用であり、`MODEL` の置換だけでは T-189 の held-out task 実験に
ならない。実装担当は本表を「変更閉包」の出発点として扱い、依存関係を実装前に再確認すること。

### 5.3 装置以外に必要な仕組み (段4裁定 B2/B7 反映、実装は本 wave の scope 外)

以下は**要求仕様であり、いずれも未実装**である。実装は本 wave の scope 外 (D87)。次に必要な
仕組みを列挙する。

- **stage2-plan-replayer / stage5-author-replayer**: 段3運用レンズが「固定 downstream による
  fix-loop replayer」が一行で済まされ実装範囲が皆無だと指摘した (段3所見 B2)。少なくとも次を
  実験開始前に個別登録する。
  - stage2-plan-replayer: plan 入力 hash、固定 downstream model/effort pin (段5相当の author
    downstream を固定 model/effort で走らせる)、fix pass 上限、acceptance 判定条件、出力 hash
  - stage5-author-replayer: 固定 plan 入力 hash、author 出力の適用先、**固定 downstream
    model/effort pin (段6相当の review/fix downstream を固定 model/effort で走らせる。
    段6所見 B2: stage2 側にしか downstream pin が無いという未閉包を埋める)**、その receipt
    検証手順、fix pass 上限、acceptance 判定条件、出力 hash
  - 共通 harness の再利用は妨げないが、入出力契約と downstream model/effort pin は stage ごとに
    別々に固定する。
  - **stage2・stage5 いずれも、replayer 契約 (上記項目) が実験開始前に登録されていない場合、
    その stage の fix gate (§12) と overall 判定は `inconclusive` とする。** これが無い限り、
    fix 巡回数と downstream 影響は測定不能として扱う。
- **task-specific oracle manifest**: T-181 装置は `KNOWN_FINDINGS` を固定集合として前提にしており
  (`:167-170`)、verdict validator もその集合以外の `equivalent_to` を拒否する (`:5753-5790`、
  段3所見 B7)。task ごとの oracle finding ID、positive/negative control、reader agreement、
  task-stage-model 別 numerator/denominator を schema 化し、`_validate_schedule`、
  `_load_adjudication`、`_aggregate_verified` 全体で hash と件数を束縛する。
- task catalog と task type 層別器
- task ごとの snapshot、prompt、oracle manifest の hash 固定
- 独立 oracle ledger の作成・凍結
- cache context の cold/warm 管理と cache usage の記録
- price snapshot の保存
- 実験実施者から隔離された mapping custodian

served model attest は現行 repository 内に存在しない。これを本文書だけで解決したとは記録しない。

## 6. Held-out task の選定と block randomization

### 6.1 task universe (段4裁定 B3 反映)

段3 運用レンズが、直近 worklog から具体的に確認できる held-out 候補 (T-139・T-1115・T-619・
T-201・T-338 程度) を洗い出し、T-755 (submodule commit・実走未完了) や T-470 (production 未接続)
のような除外例も踏まえ、**現実的な候補は4〜5件程度、両 stage 使えても 8〜10 task-stage に留まる**
と見積もった (段3所見 B3)。

**24×2 task-stage という規模は目標値であり、実験開始条件ではない。** task 母集団が dev-wave の
継続により自然に増えるまでは、8〜10 task-stage 程度の exploratory pilot として実施する。

**段6所見 B3 (現実規模と層別目標の不整合)**: §6.2 の「4層×目標6件」「少なくとも4 negative task」
は、現実的な4〜5 task/段という規模と同時には成立しない。pilot 世代では次の具体的な内訳を
lock 時に固定する (数値は catalog 確定後に埋める placeholder であり、当て推量で確定しない)。

| 項目 | pilot 世代 (現実規模) | 将来 confirmatory 世代 (目標) |
|---|---:|---:|
| stage あたり task-stage 数 | 4〜5 (§6.1 実測) | 24 (層あたり6) |
| 4層すべてを満たすか | 満たさない可能性が高く、候補ゼロの層は catalog 確定後に記録する | 4層×6件を満たす |
| positive task 数 | catalog 確定後に確定 (`N_positive_lock`) | §11.4 power simulation の要求値 |
| negative control 数 | catalog 確定後に確定 (`N_negative_lock`)。§11.3 の絶対 false-finding gate が要求する最低数に届かない場合、当該 gate は descriptive に限定する | §11.3 の絶対 false-finding gate 最低値以上 |

pilot 世代で「目標6件/層」を満たせない層は、§6.2 の既定どおり候補を全数採用し confirmatory
判定の対象から外す。目標6件/層は将来世代 (task 母集団拡大後) の目標として分離し、pilot 世代の
実施条件にはしない。

候補集合は、実施済み dev-wave の段2・段5 task から、次を満たすものに限定する。

- prompt、repo snapshot、必要な入力 artifact が replay 可能
- T-181、T-182、T-189 の設計作業に使われた task ではない
- task の最終 acceptance、tests、bug reproduction、または独立した成果物評価が残っている
- prompt、snapshot、artifact に model slug が埋め込まれていない
- stage2なら plan、stage5なら author の入力境界を固定できる

task の採否は arm の出力を見る前に決める。実験後に「難しすぎた」「差が出なかった」task を除外
しない。

登録前 (実走開始前) に task catalog を作り、task ごとに prompt hash、snapshot hash、artifact、
acceptance、stage境界、slug混入有無、type、oracle件数、除外理由を固定する。この catalog 作成
作業自体は本 wave の scope 外 (実走前提の作業)。

### 6.2 task type と独立分類 (段4裁定 A4 反映)

各 task を次の相互排他的な層へ分類する。

1. `new-mechanism`: 新しい実行機構、契約、防壁を追加する task
2. `bug-fix`: 既存挙動の欠陥を修正する task
3. `check-or-test`: 検査、fixture、test、mutation を追加・強化する task
4. `docs`: docs のみを変更する task

分類は task brief の主目的を優先する。主目的が不明な場合は、`new-mechanism`、`bug-fix`、
`check-or-test`、`docs` の順を固定 tie-break とする。複合 task を実験結果に都合よく分類し直さない。

段3 統計レンズが、この tie-break は形式上固定されていても、複合 task の分類判断自体が実験実施者
に残り、model output・acceptance・難易度・候補数を見ていない保証がないと指摘した (段3所見 A4)。
これを踏まえ、次を追加する。

- **model output と候補数を見ない独立分類者2名**が、run schedule 作成前に task catalog と
  分類 manifest を凍結する。
- 意見不一致は第三者 adjudication とし、分類の hash・timestamp を保存する。
- 候補不足時に層を埋めるための再分類はしない。候補が目標数に満たない層を持つ stage は
  §12 の標本数 gate が未達となり `routing_evidence_status = inconclusive` に固定される。

各 stage について、4層から task を目標6件ずつ (実際には §6.1 の現実的規模に従う) 抽出し、
少なくとも4 taskは oracle finding が0件の negative control とする。ある層に候補が目標数に
満たない場合は候補を全数採用するが、その stage は `routing_evidence_status = inconclusive`
に固定され、`confirmatory-go`/`confirmatory-no-go` のいずれも出さない。

### 6.3 schedule と block

`task_id` ごとに、同じ task、stage、type、prompt hash、snapshot hash、oracle hash、cache
condition、price version を持つ2 slotを作る。

schedule row の提案 schema は次のとおりである。

```json
{
  "slot_id": "opaque-slot-001",
  "block_id": "b001",
  "block_order": 1,
  "stage": 2,
  "task_id": "T-xxx",
  "task_type": "bug-fix",
  "oracle_kind": "positive",
  "requested_model": "gpt-5.6-sol",
  "arm": "max",
  "cache_condition": "cold",
  "prompt_sha256": "<64 hex>",
  "snapshot_manifest_sha256": "<64 hex>",
  "oracle_sha256": "<64 hex>",
  "price_version": "<frozen version>",
  "price_snapshot_sha256": "<64 hex>"
}
```

`arm` は既存装置との互換性のため reasoning effort を表し、model を表さない。`sol`/`luna` という
lane 名を model authority として再利用しない。

randomization は次の順序で行う。

1. stage × task type × cache condition の層ごとに候補を canonical sort する。
2. task catalog hash と事前登録 version から決定的 seed を作る。
3. 各層から task を抽出する。
4. task block の順序を randomize する。
5. block 内の model 順序は sol-first / luna-first を交互に割り当てる。
6. schedule bytes を hash し、実走前に run root へ凍結する。

T-181 の `60,000 ms` の block 内 gap と `900,000 ms` の block 間上限を踏襲する。T-182 で観測された
同時実行数22のような外部 concurrency が残る場合、wall-clock の confirmatory 判定を行わない。

## 7. 盲検化手順 (段4裁定 B4 反映)

盲検の目標は、評価者が requested model を知らずに output の意味を裁定することである。

1. 実験実施者は schedule に従って run を行い、raw output と receipt を保存する。
2. custodian は run-to-packet mapping を新規 `0700` directory に保存し、public packet には
   opaque packet ID と本文だけを置く。
3. packet 本文から run ID、slot ID、model、lane、timestamp、token、wall、receipt path、
   price version を除く。
4. 親 reader と second reader は、model mapping、arm 別集計、他 reader の verdict、aggregate
   結果を見ずに各 packet を裁定する。
5. 両 reader の verdict を append し、全 packet の verdict を freeze する。
6. freeze 後にのみ mapping を reveal し、`aggregate`/`verify` を実行する。

段2の plan 文書や段5の diff には、文章の癖、変更量、命名、構成から model が推測される残差がある。
これを完全には消せないため、次を行う。

- packet renderer は metadata だけを除き、意味内容を改変しない。
- 出力中の model slug や自己申告を masking violation として記録する。
- reader は verdict とは別に、model を推測したかを記録する。

**blocker (段3所見 B4): 現行の T-181 装置の custodian 隔離 (`make_packets` が同一プロセスで
packet と custodian root を作る、`:5631-5664`) は、実験実施者と同じ Unix identity・同じセッション
が mapping を読める `same-owner-advisory` に過ぎない。** `--custodian-root` は path しか受け取らず
(`:6102-6125`)、独立 user/owner/handoff の検証は現行装置にない。

- **別 Unix user または実験者以外の人間が mapping を保持する実運用手順 (担当者・UID・handoff・
  ACL) を事前登録できない限り、`routing_evidence_status` は確定しない (`confirmatory-go`/
  `confirmatory-no-go` のいずれにもしない)。** same-owner の結果は `apparatus_diagnostic`
  (§12.1: 装置動作確認・効果量の粗い見積りにのみ使う) に限定し、品質証拠・rollback 材料には
  しない。
- 独立 custodian を別 Unix identity または別担当者で用意できない場合、その制約を隠さない。
  §12.3 判定表の blind gate はこの条件を明示的な blocker として扱う。

## 8. 独立 oracle と裁定体制

### 8.1 oracle ledger

oracle は model output から作らない。task の acceptance criteria、再現可能な bug、固定された
最終状態、独立 reviewer の確認から、実験開始前に task ごとの finding ledger を作る。

各 oracle finding は少なくとも次を持つ。

- `oracle_finding_id`
- severity
- must-fix 判定
- 根拠となる task artifact
- output 中で検出されたとみなす条件
- 同値 finding の canonical identity

oracle ledger にない novel finding は主指標の分母へ後付け追加しない。novel finding は別の探索的
ledger に記録し、T-182 の shadow-only finding と同じく主指標を救済する材料にはしない。

### 8.2 reader

親 reader と独立 second reader は、実験実施者および mapping custodian から独立する。second
reader は fresh session で起動し、親 verdict や arm 別候補数を見ない。

finding coverage は、両 reader が同じ oracle finding を検出したと一致した場合にのみ1件として
数える。不一致時は第三の blind adjudicator に回す。第三 reader が用意できない場合は、coverage
は保守的に未検出、false finding は検出として扱う。

主指標は §3 の primary estimand (task-cluster paired 差) に従う。副指標として、T-181/T-182 と
同じ numerator/denominator 型の記述的 coverage も報告する。

```text
記述的 finding coverage
= 両 reader が検出と一致した oracle finding 数 / oracle finding 総数
```

oracle finding が0件の negative control は分母から除き、false finding rate として別集計する。

## 9. Cache 条件の分離 (段4裁定 B5 反映)

T-182 は、sol の cached input `2,390,528`、luna の `895,488`、mini の `984,320` のように cached
input 比率が arm 間で異なり、同時起動や外部 concurrency も wall-clock を交絡させた。この数値を
model 固有の資源差として再利用しない。

T-189 では `cache_condition` を block の固定因子にする。

- `cold`: 各 arm の独立 cache context で事前 warm-up を行わない
- `warm`: 各 arm の独立 cache context に同じ task prefix を事前投入する
- 一つの task block の二つの arm は必ず同じ condition を使う
- cold/warm の task 数を各 stage・各 task type で均衡させる
- model 順序と cache condition を交互化・層別化する

**blocker (段3所見 B5): 現行の T-181 装置は provider 側 prompt cache の reset・namespace・
warm-up を制御・attest する手段を持たない** (`codex exec` argv に cache 制御引数なし、
`:2625-2646`。local `CODEX_HOME`/tmpfs 隔離のみ `:2649-2740`, `:2764-2817`。schedule validator
も `cache_condition` を検査しない `:4427-4449`)。

- **provider の cache reset/namespace capability を実走前に実測または契約として固定できない
  限り、cache condition を制御因子として扱わない。** これは事後に unknown と記録して済ませる
  のではなく、実走開始前の **blocker** として扱う (§12 判定表)。
- 実現できた場合は launch receipt に cache attestation を保存する。
- **段6所見 B5 (blocker と exploratory 報告の矛盾)**: cache capability が実走前に確認できない
  場合、cache-stratified な token/wall の schedule 自体を作らない。exploratory 層であっても
  「未検証の cold/warm ラベルを付けた resource 比較」を作成・報告しない。cache 制御を確認
  できない stage は、token/wall を **資源指標として報告しない** (§12 の resource-overall は
  当該 stage で `not-applicable` とする)。coverage・fix 等の非資源指標は cache 未確認でも
  §12 の quality 系列に従って exploratory 報告を続けてよい — cache 未確認が blocker になるのは
  資源比較 (token/wall) に限る。

各 run について、少なくとも `input_tokens`、`cached_input_tokens`、`output_tokens`、
`cli_reported`、cache ratio、wall-clock を保存する。`cli_reported` は T-182 と同じく、

```text
input_tokens - cached_input_tokens + output_tokens
```

で計算する。cache condition を無視した pooled resource 指標は主判定に使わず、cold/warm 別に
報告する (cache 制御が実現できた場合に限る)。

## 10. 価格 version (段4裁定 B6 反映)

D514 は、2026-07-30 時点の例として sol を入力 `$5` / 出力 `$30` per M、luna を入力 `$0.20` /
出力 `$1.20` per M と記録し、同日に luna が80%値下げされたことを記録している。古い価格表を
実験期間へ機械的に適用しない。

段3 運用レンズが、D514 の価格記述には数値と日付はあるが、provider の公式原表・SKU・取得方法・
version が記録されていないと指摘した (段3所見 B6)。実走前に、次の price snapshot を凍結する。

- provider の公式価格原表または billing API の出典 (URL・API endpoint 等)
- SKU mapping (model slug → 課金 SKU)
- capture command (取得コマンドまたは手順)
- raw snapshot の保存先 path と hash
- model ごとの input、output、cached input の単価
- 通貨
- price table version
- effective timestamp と取得 timestamp
- 価格が不明な token category

schedule の全 slot は同じ `price_version` を参照する。**上記項目が欠落する場合、schedule を
無効化する (fail-closed)。** 価格改定が実験開始前に発生した場合は、実験を開始せず価格 snapshot
と事前登録 version を更新する。実験中に改定された場合は、次の二つを分離する。

1. 比較可能性のため、全 run の正規化 cost は開始時に凍結した price version で計算する。
2. 実請求額は実際の billing version として別記録する。

価格改定後の実請求額を用いて、結果に都合よく cost 結論を再計算しない。価格改定が GO/NO-GO の
経済的解釈を変える場合は、新しい登録世代を作り、旧世代と混ぜない。

## 11. 指標と事前登録済み非劣性 margin の候補 (段4裁定 A1/A3/A6/A7/A9 反映)

### 11.1 標本数の限界 (段3所見 A1)

段3 統計レンズが、positive task が20件でも luna の損失0件のとき片側95%の「未観測損失率」上限は
概ね次のとおりだと算術で示した。

```text
1 - 0.05^(1/20) ≈ 13.9%
```

したがって coverage 差の下限は概ね `-0.139` まであり得て、margin 候補 `-0.05` を上回れない。
24件全てが有効でも約 `-0.117` である。**§6.1 の現実的な held-out 規模 (8〜10 task-stage) では
この問題はさらに悪化する。** 本文書はこれを隠さず、次の運用ルールを定める。

- **`N_positive_min` を実験開始前の lock 時に値入りで固定する (段6所見 A1)。** 値は §11.4 の
  power simulation から決定し、当て推量で決めない。実効 positive task 数 (negative control を
  除く) が `N_positive_min` に満たない stage は、`routing_evidence_status = inconclusive`
  で**固定**する (「descriptive/exploratory として報告する」という曖昧な扱いにせず、§12 の
  3値ラベルのうち inconclusive を確定的に割り当てる)。
- margin を満たさない、または必要な証拠が欠測する場合も、`routing_evidence_status` は
  `inconclusive` とし、luna routing の品質証拠として採用しない。

### 11.2 主指標・副指標の定義

主仮説は、luna の finding coverage が sol より事前登録 margin を超えて劣化しないことである。
副仮説は、luna が token、wall-clock、fix 巡回数について事前登録した上限を超えて悪化しない
ことである。

```text
Δcoverage_s  = mean_task( coverage(task, luna) - coverage(task, sol) )   (s ∈ {2, 5}、§3 primary)
Δlogtoken_s  = mean_task( log(token(task, luna)) - log(token(task, sol)) )
Δlogwall_s   = mean_task( log(wall(task, luna))  - log(wall(task, sol)) )
Δfix_s       = fix_rounds(luna, s) - fix_rounds(sol, s)
```

**段6所見 A9/N1 (尺度の不一致・未定義規則)**: token・wall は **log 尺度で計算する** (`Δlogtoken_s`/
`Δlogwall_s` は log 差、比率ではない)。§11.3 の margin 候補が示す `1.10`/`1.15` という比率尺度の
閾値は、判定時に `log(1.10)`/`log(1.15)` へ変換して `Δlogtoken_s`/`Δlogwall_s` と比較する
(本文の margin 表は読み手の直感に合わせ比率のまま表記し、実際の統計検定は log 尺度で行う、と
統一する)。zero token/wall は観測上あり得ないため zero 処理規則は不要。外れ値は、§6.3 の
block 内 gap (60,000 ms) と block 間上限 (900,000 ms) を超える run、および compaction・
rate limit が observed=true として記録された run を除外基準の対象とし、除外した run 数と
理由を報告に明記する。除外後の実効 task 数が §11.1 の `N_positive_min` を割る stage は、
resource gate を exploratory へ格下げする。集計統計量は task 平均の log 差 (上式) を primary
とし、中央値は副次的な記述指標として併記する。

### 11.3 margin 候補

以下を段4裁定前の推奨候補とする。実走開始前に一つの値を明示的に lock し、lock 後は変更しない。

| 指標 | 差の向き | 推奨する margin 候補 | 根拠 |
|---|---|---:|---|
| finding coverage (task-cluster paired) | luna − sol | 片側95%信頼区間の下限が `-0.05` より大きい | §11.1 のとおり、現実的な標本数ではこの margin を confirmatory に満たすのは困難。満たせない場合は `routing_evidence_status = inconclusive` に固定する |
| CLI reported token (per-task log ratio) | luna / sol | 95% CI 上限が `1.10` 未満 | cache 補正後でも10%超の追加消費を非劣性と扱わない |
| wall-clock (per-task log ratio) | luna / sol | 95% CI 上限が `1.15` 未満 | 外部 concurrency を除いたうえで、15%超の遅延を運用非劣性と扱わない |
| fix 巡回数 | luna − sol | 95% CI 上限が `+0.25` 未満 | D207 の「弱い起草が must-fix と fix 巡回を増やす」懸念を検出できる値。ただし §11.4 の power 検討が必要 |
| false finding rate (絶対値、段3所見 A6) | 各 arm 独立 | 片側95%上限が `0.05` 未満 (最低 negative task 数を満たす場合のみ) | 差分だけでなく絶対 false-finding rate に上限を設ける。critical/high の新規 false must-fix は1件でも NO-GO |
| false finding rate (差分) | luna − sol | 95% CI 上限が `+0.05` 未満 | coverage だけを上げる誤検出を許さない |

**段3所見 A6 / 段6所見 A6 (negative control 不足、分母未定義)**: false finding rate の
event 単位を **task-binary** に固定する — 1 negative task につき「false finding が1件以上
検出されたか」の2値のみを数え、同一 task 内の false finding 複数件を重複してカウントしない
(finding count 単位は採用しない。複数 false finding を持つ task が rate を過大に見せることを
避けるため)。分母は §6.2 で確定した negative task 数とする。

`N_negative_min` を実験開始前の lock 時に値入りで固定する (§13)。5%刻みを観測するには最低
20 negative task、0件から片側95%上限を5%未満にするには概ね59件が必要という試算 (task が
最低4件の場合、luna だけ1件の false finding で `1/4=25%` となり絶対 margin `0.05` を大きく
超える) を lock 値決定の参考にする。**absolute false-finding gate は、実効 negative task 数が
`N_negative_min` に満たない場合、`routing_evidence_status` に寄与させず (confirmatory gate
から外し)、descriptive 記録のみとする。** critical/high の false finding は `N_negative_min`
の充足有無に関わらず1件でも hard NO-GO とする (§12)。

**段3所見 A7 (D207 power 根拠)**: fix 巡回は24 task全体で1回増えても `+1/24=0.0417` にしかならず
margin `+0.25` には届かない。弱い起草が1〜数 taskの downstream fix を増やすという D207 の懸念を
平均値だけでは見逃す。critical finding の未検出や cap-exceeded (§4.1) は、平均値の margin とは
独立した hard NO-GO として扱う。

fix 巡回数は、target stage の出力を固定 downstream replayer (§5.3) に投入し、acceptance が
green になるまでの追加 pass 数とする。事前登録した上限を超えた task は `cap-exceeded` とし、
平均値を小さく見せるために切り捨てない。

価格 snapshot から算出する billing cost は副次的な記述指標とする。価格改定の影響を受けるため、
token、wall、fix の非劣性判定を cost 単独で置き換えない。

### 11.4 Power simulation (実験開始前 lock の必須項目)

margin 候補の検出力を当て推量で決めない。実走開始前の lock 手続きの一部として、次を行う。

1. 想定する劣化シナリオ (例: 1 taskで全 findingを失う、1 taskで追加fixが発生する等) を効果
   分布として仮定する。
2. §6.1 で確定した実効 task 数を用いて、§11.3 の各 margin candidate に対する検出力を
   simulation で見積もる。
3. **実用的検出力の閾値を `power_threshold = 0.80` に固定する (段6所見 A7)。** 検出力が
   この閾値を下回る margin は、より緩めるのではなく、「この規模では confirmatory 判定を
   出さない」(`routing_evidence_status = inconclusive` 固定) という扱いへ切り替える。
   D207 の原則 (検出力を下げる変更は規律2の対象) に反する方向、すなわち margin を緩めて
   見かけ上 GO を通しやすくする調整はしない。
4. simulation の実装コード hash、乱数 seed、想定した効果分布のパラメータ、出力 (各 margin
   candidate の検出力の値) を、§13 の lock 対象に含める。simulation を再実行すれば同じ
   `N_positive_min`/`N_negative_min`/margin 値が再現できることを、実験開始前に確認する。

**lock の実行順序 (段6所見 N3)**: (1) task catalog の凍結 (§6.1、独立分類者2名の署名を含む) →
(2) 実効 task 数の確定 (§6.2 の層別内訳、pilot 世代なら §6.1 の表) → (3) 本節の power
simulation の実行と `N_positive_min`/`N_negative_min`/margin 値の確定 → (4) schedule.json の
生成と hash 凍結 (§6.3)。各段階の成果物 hash を §13 に記録し、順序を入れ替えない。

この power simulation 自体の実行は実走開始前 lock の一部であり、本 wave (文書設計) の scope
外である。

## 12. 事前登録判定表 (段4裁定 A3/B3/B4/B5、段6所見 B4/B5/N2 反映)

### 12.1 `routing_evidence_status` — routing 判断・D423 証拠に使える結果は3値だけ

段6 敵対レビューが、exploratory 層にも quality/false-finding/fix の GO 条件を評価させ、その
NO-GO を rollback 材料として使う設計 (旧版) では、same-owner や cache 未制御下の結果が事実上の
品質証拠として一人歩きする抜け道になると指摘した (段6所見 B4/B5)。これを閉じるため、
production routing の判断・D423 の再訪証拠・rollback 材料として**参照してよい**結果を、
次の3値 `routing_evidence_status` だけに限定する。

- `confirmatory-go`: §12.3 の confirmatory gate をすべて満たした場合のみ。
- `confirmatory-no-go`: confirmatory 前提 (blind・標本数・cache の各 gate) を満たした上で、
  quality/false-finding/fix のいずれかが margin を超えた場合。
- `inconclusive`: 上記いずれでもない場合 (標本数不足、custodian 未実現、cache 未制御、
  provenance 無効等、confirmatory 前提が1つでも欠ける場合はすべてこれになる)。

**same-owner (custodian 未実現) の結果、または cache 制御が確認できない stage の resource
指標は、`routing_evidence_status` に一切寄与しない。** これらは別ラベル `apparatus_diagnostic`
として記録し、**装置動作確認・将来 confirmatory 実験に向けた効果量の粗い見積りにのみ使う。**
`apparatus_diagnostic` の結果を品質 GO/NO-GO、D423 の証拠、production routing の rollback 材料
として引用しない。§2/§7 の rollback 記述 (`2026-08-08_t182-luna-stage3-hybrid.md` の条件 (b))
を含め、本文書外の decision がこの結果を参照する場合も同じ制約を継承する。

### 12.2 quality-overall と resource-overall の分離 (段6所見 N2)

overall は単一の gate ではなく、次の3系列に分離する。

- **quality-overall**: coverage (stage2・stage5)・false finding・fix の各 gate の AND。
  `routing_evidence_status` を決める主系列。
- **resource-overall**: token・wall (cache gate に従属) の AND。品質が通っても resource が
  非劣性でない場合、`quality-overall` は独立に GO でありうるが、**production 採用の判断材料
  としては resource-overall の状態も併記必須**とする (token/wall だけで quality-overall を
  引き下げない。逆に resource が通っても quality が NO-GO なら routing 変更しない)。
- **apparatus-diagnostic-only**: same-owner または cache 未制御により confirmatory 前提を
  欠く場合の記述的結果。§12.1 のとおり routing 判断に使わない。

### 12.3 Gate 表

| Gate | 系列 | GO 条件 | NO-GO / 扱い |
|---|---|---|---|
| 装置・provenance | 前提 | 全 task が schedule、prompt、snapshot、oracle、price version、receipt に束縛され、`aggregate`/`verify` が replay 完了する (§4.1: treatment 開始前の束縛破綻に限る) | 欠測、hash mismatch、retry 規則違反、model mismatch は当該 task-stage を解析除外し実験 provenance 無効 |
| paired | 前提 | 各採用 task-stage に sol/luna の同一入力 pair がある (ITT、§4.1) | 片 arm のみの結果は採用しない |
| blind | confirmatory 前提 | mapping reveal は両 reader の verdict freeze 後、**独立 custodian** (別 Unix identity/別担当者、担当者・UID・handoff・ACL を事前登録) が管理する | same-owner-advisory (§7 blocker) の場合、`routing_evidence_status` は自動的に対象外。結果は `apparatus_diagnostic` に限定する |
| oracle | 前提 | oracle ledger が run 前に凍結され、親・second readerが独立に裁定する | oracle を結果後に追加・変更した場合は主解析無効 |
| 標本数 | confirmatory 前提 | 実効 positive task 数が `N_positive_min` 以上、negative task 数が `N_negative_min` 以上 (§11.1/§11.3、§11.4 power simulation で確定) | 満たさない gate 単位 (stage 別・指標別) は `inconclusive` に固定する |
| stage2 coverage | quality-overall | stage2 の primary estimand (§3) 片側95%CI 下限が `-0.05` より大きい | confirmatory 前提未達なら `inconclusive`。前提充足かつ margin 未達なら `confirmatory-no-go` |
| stage5 coverage | quality-overall | stage5 の primary estimand 片側95%CI 下限が `-0.05` より大きい | 同上 |
| false finding (絶対値) | quality-overall | `N_negative_min` 充足時、片側95%上限が `0.05` 未満 (task-binary 定義、§11.3) | 未充足なら descriptive のみ (confirmatory gate から除外)。critical/high は件数に関わらず1件で hard NO-GO |
| false finding (差分) | quality-overall | 95% CI 上限が `+0.05` 未満 | quality-overall の NO-GO 要因 |
| fix | quality-overall | fix 巡回差 CI 上限が `+0.25` 未満、critical cap-exceeded なし、stage2/stage5 replayer 契約 (§5.3) が登録済み | replayer 契約未登録なら `inconclusive`。契約済みで margin 未達なら NO-GO |
| cache | resource 前提 | provider の cache reset/namespace capability が実測または契約で固定され、launch receipt に attestation がある (§9 blocker) | 制御不能な場合、当該 stage の token/wall は資源指標として報告しない (`not-applicable`)。quality-overall には影響しない |
| token | resource-overall | cache gate 充足時、cache condition 別の `Δlogtoken` が `log(1.10)` 未満 (§11.2) | cache gate 未達なら `not-applicable` |
| wall-clock | resource-overall | cache gate 充足時、cache condition 別の `Δlogwall` が `log(1.15)` 未満 (§11.2) | cache gate 未達なら `not-applicable` |
| multiple comparison | quality-overall の構成則 | quality-overall は個別 gate の **AND** (intersection-union test) として判定し、個別 gate 単独に同時信頼区間は保証しない (段3所見 A3) | 個別 gate は descriptive としても報告し、非対称性 (真に全 gate が通る場合でも false NO-GO 率が上昇しうること) を記録に明示する |

### 12.4 状態遷移

1. 装置・provenance・paired・oracle の前提が1つでも崩れる task-stage は解析から除外する。
2. 残った task-stage 集合で、blind・標本数の confirmatory 前提を判定する。いずれか未達なら、
   その stage の quality 系列は `routing_evidence_status = inconclusive` で確定し、
   `apparatus_diagnostic` として資源・coverage の記述値のみ報告する。
3. confirmatory 前提を満たした stage だけ、quality-overall (§12.3) を評価し、`confirmatory-go`
   または `confirmatory-no-go` を確定する。
4. cache gate は resource-overall にのみ影響し、quality 系列の `routing_evidence_status`
   確定には関与しない。

`confirmatory-go` であっても、これは「要求した luna が当該 held-out task 集合で sol に
非劣性だった」という範囲に限る。現在の全 luna 化を遡及的に正当化したり、served model の品質
同等性を主張したりしない。

`confirmatory-no-go` は、段2/5の sol 復帰または段3を含むハイブリッド復帰を検討する材料とする。
`inconclusive`/`apparatus_diagnostic` は rollback の直接材料にはしない — これらは「まだ証拠が
無い」ことの記録であり、「証拠がある」ことの代用にしない。実際の rollback は D241、D514、
ユーザー裁定の手続に従う。

## 13. 変更管理

次は run 開始前に、§11.4 が定める順序 (task catalog → 実効 task 数 → power simulation →
schedule) で lock する。

- task universe hash (独立分類者2名の凍結署名を含む)
- task type 分類規則
- task 数と層別数 (実効数。pilot 世代は §6.1 の表、将来世代は §6.2 の目標)
- `N_positive_min`、`N_negative_min` (§11.4 power simulation の出力)
- power simulation の実装コード hash・乱数 seed・想定効果分布パラメータ・検出力の出力値
  (`power_threshold = 0.80` に対する判定結果、§11.4)
- randomization seed (§6.3 schedule 生成用、power simulation の seed とは別管理)
- schedule bytes
- oracle ledger
- apparatus pin
- cache protocol (制御可能性の実測結果。制御不能なら resource gate を `not-applicable` 固定)
- price snapshot
- margin 値 (§11.3、§11.4 power simulation を経て確定)
- custodian 実現方式 (same-owner-advisory か独立 custodian か。担当者・UID・handoff・ACL を
  独立実現する場合はその記録)
- stage2/stage5 replayer 契約 (§5.3: 入力・出力 hash、downstream model/effort pin)
- GO/NO-GO 判定表 (§12: `routing_evidence_status` 3値、quality-overall/resource-overall の
  適用条件を含む)

run 開始後は、oracle、margin、task 除外規則、判定表を変更しない。技術失敗の扱いは receipt に
基づいてのみ適用し、output の内容を理由に retry、除外、再分類を行わない。

## 14. limitation

- **現実的な held-out task 規模 (8〜10 task-stage、§6.1) では、margin 候補 (§11.3) を
  confirmatory に満たせる検出力がない可能性が高い (§11.1、§11.4)。** 24×2 という目標規模でも
  同様の限界が残りうる。
- 現行装置は served model を attest できず、結果は requested model に限定される。
- **独立 custodian が実現できない場合、T-181 と同じく masking は `same-owner-advisory` であり
  真の blind ではない。その場合 `routing_evidence_status` は確定せず、結果は `apparatus_diagnostic`
  に格下げし routing 判断・rollback 材料として使わない (§7 blocker、§12.1)。**
- **現行装置は provider 側 cache の制御・attest ができない。制御を実現できない場合、当該 stage の
  resource (token/wall) は `not-applicable` とし報告しない。quality 系列の判定には影響しない
  (§9 blocker、§12.3)。**
- plan の文章や author diff の書き癖から model を推測できる残差を完全には除去できない。
- oracle は独立に作成するが、oracle 自身の見落としを完全には排除できない。oracle 外の novel
  finding は主指標に追加しない。
- prompt cache が provider 側に残る場合、local cache context の分離だけでは完全な cold start を
  証明できない。
- `model_calls` は logical turn 数ではない。T-181 と同じく、turn 削減の主張には使わない。
- held-out task は実施済み task からの抽出であり、将来の未知 task への外的妥当性は保証しない。
- T-182 の n=1、非盲検、循環評価、事前登録なし、後付け採点、cache 比率の arm 間偏りは、本設計の
  oracle、blind、層別、cache protocol で再現させないことを目指すが、§7/§9 の blocker が
  解消されない限り、盲検性・cache 分離の一部は T-181/T-182 と同水準の限界を引き継ぐ。
- T-181 装置の model 軸拡張は横断的 refactor に相当し (§5.2)、段2/段5 downstream replayer・
  task-specific oracle schema (§5.3) を含め、実装コストは当初想定より大きい。
- 本文書は文書設計だけを行い、実験走行、`qsub`、production の model routing 変更は行わない。

## 総括

本文書は、D514 後の全 luna 化を事後検証し、D423 の将来再訪条件を満たすための exploratory pilot
として設計した。段3 の敵対相談2レンズ (統計的妥当性・運用実現性) が計16件の real 所見 (blocker
7件・major 9件) を出し、全件を段4裁定で採用・反映した。その反映を検証した段6 敵対レビューが
さらに17件の未閉包 (blocker8・major5・新規4) を指摘し、**`routing_evidence_status` の3値化
(§12.1) と quality-overall/resource-overall の分離 (§12.2) を中心に全件を fix で反映した。**
「裁定要求を反映したが、以下の残課題がある」というのが本文書の正確な状態であり、「全件
反映して完成した」という主張はしない。

| 要素 | 対応節 | 現状の到達度 |
|---|---|---|
| paired | §4、§6.3 | 設計は満たす |
| blind | §7、§12.1 | 設計は満たすが、独立 custodian 未実現なら `apparatus_diagnostic` に格下げし routing 判断に使わない (blocker) |
| held-out 複数 task | §6 | 設計は満たすが、現実規模は目標 (24×2) より小さい (pilot 世代 8〜10 task-stage、§6.1 の表) |
| 独立 oracle | §8 | 設計は満たす |
| block randomization | §6.3 | 設計は満たす |
| cache 条件の分離 | §9、§12.2 | 設計は満たすが、現行装置は制御手段を持たない場合 resource 指標を `not-applicable` とする (blocker) |
| 価格 version | §10 | 設計は満たす。**取得手順・原表・SKU を実走開始前の準備段階で凍結する契約を本文書で明記するが、実データそのものは本 wave では取得しない** (実データ取得は将来の実装・実走 wave が行う) |
| 事前登録済み非劣性 margin | §11、判定表 §12 | 候補値と lock 手続き (`N_positive_min`/`N_negative_min`/`power_threshold=0.80`) を明記。現実的標本数では confirmatory な検出力が不足する可能性が高く、その場合は `inconclusive` に確定的に固定する |

主指標は task-cluster paired 差による finding coverage (§3 の式)、副指標は log 尺度の
token・wall-clock 比、fix 巡回数、task-binary な false finding rate である。段2と段5は
別々に判定し、段3は非対象だが `confirmatory-no-go` の場合に限り rollback 材料として結果を
利用する (`inconclusive`/`apparatus_diagnostic` は rollback 材料にしない、§12.4)。
`requested_model` と `served_model` を分離し、served model は unknown のまま記録する。

**未解決点(実装・実走 wave が引き継ぐべき前提条件)**: (1) power simulation の実施と
`N_positive_min`/`N_negative_min`/margin の最終 lock (§11.4)、(2) 独立 custodian の実現方式
確定、(3) provider cache 制御可能性の実測、(4) T-181 装置の横断的 refactor (§5.2)、
(5) stage2/stage5 downstream replayer の実装 (§5.3、両 stage とも downstream model/effort
pin を含む)、(6) task catalog の実データ作成と独立分類者2名の確保 (§6.1/§6.2)、(7) price
snapshot の実データ取得 (§10)。いずれも本 wave の scope 外 (D87) であり、本文書はこれらの
前提条件を明示することで、将来の実装 wave が着手可能な状態を作ることを目的とする。
