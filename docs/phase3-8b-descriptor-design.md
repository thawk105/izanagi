# Phase 3 段 8b: workload descriptor の前向き設計

**状態: 起草 (draft) — 実走前凍結の対象項目を仕様化する。発効はユーザー承認後**

## 1. 目的と主張の型

本設計は、型付き workload descriptor（ワークロード記述子）を入力として、並行性制御
(Concurrency Control; CC) の variant（構成）を扱う段 8b の**実走前**仕様である。

- **selector 実験**は、固定された variant 集合から descriptor 条件付きで選択する。
  これは workload-aware selection（ワークロードを考慮した選択）を検査するにとどまり、
  descriptor-conditioned synthesis（descriptor 条件付き合成）の証拠には数えない。
- **generation/search 実験**は、proposal/search（提案・探索）の開始前に descriptor を与え、
  descriptor on/off または swapped（入替え）対照を置く。**「ワークロード特化合成」**の
  システム主張にはこちらが必須である。

`docs/phase3.md` の「(8b 未着手) workload 次元のループ入力化」が規定する通り、既知の
rr5/rr50/rr95 と D50/P2-4 の結果はすでに既知である。したがって、それらは
**「配線 demo または結果既知の事前登録付き追試 (confirmatory とは呼ばない) にしか使わない」**。
新発見には数えず、D50 の機械 sweep も pilot（予備調査）/既知証拠から将来の自動システム成果へ
遡及的に再分類しない。

## 2. descriptor の型定義

### 2.1 JSON Schema 風の凍結 schema

実装時の canonical JSON は次の型を満たす。キーの追加・値域変更は本設計の再凍結対象である。

```json
{
  "type": "object",
  "required": ["schema_version", "source", "read_write", "contention", "scale", "objective", "correctness"],
  "additionalProperties": false,
  "properties": {
    "schema_version": {"const": "8b-v1"},
    "source": {"enum": ["campaign_search_config_projection", "human_declared"]},
    "read_write": {
      "type": "object",
      "required": ["read_ratio_percent", "rmw"],
      "additionalProperties": false,
      "properties": {
        "read_ratio_percent": {"type": "integer", "minimum": 0, "maximum": 100, "description": "percent"},
        "rmw": {"type": "integer", "enum": [0, 1], "description": "0 or 1 boolean"}
      }
    },
    "contention": {
      "type": "object",
      "required": ["skew", "label"],
      "additionalProperties": false,
      "properties": {
        "skew": {"type": "number", "minimum": 0.0, "maximum": 1.0, "description": "Zipf parameter"},
        "label": {"enum": ["low", "high"]}
      }
    },
    "scale": {
      "type": "object",
      "required": ["records", "threads"],
      "additionalProperties": false,
      "properties": {
        "records": {"type": "integer", "minimum": 1, "description": "records"},
        "threads": {"type": "integer", "minimum": 1, "description": "threads"}
      }
    },
    "objective": {"enum": ["maximize_throughput_tps"]},
    "correctness": {"enum": ["serializable_legacy_and_s2"]}
  }
}
```

`read_ratio_percent` は CCBench YCSB の `rratio` に対応する読み取り割合であり、`rmw=1` は
read-modify-write、`rmw=0` は分離 read/write を表す。`contention.label` は数値 `skew` と
`records`/`threads` を再計算して置換しない、設計時に宣言した分類である。

**禁止フィールド:** 勝者名、variant 名、実測 throughput、順位、過去の比較差、recommendation、
またはこれらから復元できる値は descriptor に含めない。これは D39/D47 と同型のリーク制御である。
descriptor を受け取る planner-v4/coder-v4 は `tools=[]` の構造遮断であり、信頼中核が
射影した inline JSON だけを前渡しし、構造化出力だけを受け取る (`docs/agent-architecture.md` の
planner/coder 節)。

### 2.2 生成元と固定方法

- `campaign_search_config_projection`: 承認済み campaign の `search_config` と workload 設定から
  機械的に射影する。射影関数の版、入力 canonical JSON の hash、出力 descriptor の hash を
  campaign manifest に記録する。射影出力は planner/coder/selector へ渡す**前**に、(1) `jsonschema`
  による本 schema の検証、(2) 全キーの再帰走査による禁止フィールド検査、をこの順に必ず通す。
  いずれか一方でも違反すれば fails-closed とし、descriptor を破棄して campaign の起動を拒否する。
  警告だけで続行してはならない。実装タスクの受け入れ条件は、この二段検証の実装に加え、禁止フィールドを
  注入した descriptor（子階層の `read_write.measured_tps` と `contention.winner` を含む）が実際に
  検証で落ちる positive control テストを置くことである。
- `human_declared`: 上記に未表現の目的または正しさ制約だけを、人間が schema 内の値として指定する。
  指定者・理由・承認時刻を記録する。勝敗や実測値を根拠として書かない。

現在の既知空間は `orchestrator/campaign/p2_2.py` の `skew=0.9`、`rratio ∈ {95, 50, 5}`、
`records=1m`、`threads=48`、`clocks_per_us=1800` である。これは descriptor の例示および
配線 demo にのみ用いる。

## 3. holdout workload と全件報告規則（凍結項目 1）

### 3.1 前提と候補

既存 3 点 rr95/rr50/rr5 (`skew=0.9`, `records=1m`, `threads=48`, `rmw=0`) は結果既知であるため、
holdout にはできない。承認前に候補を次の 4 点に限定し、承認時にこの中から 2 点を採る。

|候補 ID|CCBench YCSB 条件|既知でないことの確認手順|
|---|---|---|
|H1|`rratio=80`, `skew=0.9`, `rmw=0`, 1m records, 48 threads|下記の三軸正規表現を `<rratio>=80`、`<skew>=0.9`、`<rmw>=0` に具体化して全件検索する。|
|H2|`rratio=20`, `skew=0.9`, `rmw=0`, 1m records, 48 threads|同じ三軸正規表現を `<rratio>=20`、`<skew>=0.9`、`<rmw>=0` に具体化して全件検索する。rr5/rr50/rr95 の補間結果を測定済み扱いしない。|
|H3|`rratio=50`, `skew=0.7`, `rmw=0`, 1m records, 48 threads|同じ三軸正規表現を `<rratio>=50`、`<skew>=0.7`、`<rmw>=0` に具体化して全件検索する。|
|H4|`rratio=50`, `skew=0.9`, `rmw=1`, 1m records, 48 threads|同じ三軸正規表現を `<rratio>=50`、`<skew>=0.9`、`<rmw>=1` に具体化して全件検索する。既存 `rmw=0` 計測を非同一と明記する。|

検索は各軸の canonical 符号化を網羅する。各 `<v>` について rratio は
`(?:ycsb_rratio=<v>|"ycsb_rratio": "<v>"|"ycsb_rratio":"<v>")`、skew は
`(?:ycsb_zipf_skew=<v>|"ycsb_zipf_skew": "<v>"|"ycsb_zipf_skew":"<v>")`、rmw は
`(?:ycsb_rmw=<v>|"ycsb_rmw": "<v>"|"ycsb_rmw":"<v>")` を使い、候補ごとに三軸すべてを
同じ規約で照合する。0 件だけでは誤った文字列を探す偽保証になり得るため、freeze 生成時には既知点
rr50 を同じ rratio 正規表現で positive control 検索し、hit 数が 0 より大きいことを確認する。
各候補について (a) 検索対象ディレクトリ一覧、(b) 実行した検索式、(c) 三軸照合の一致 0 件の出力
hash、(d) rr50 positive control の検索式と hit 数、(e) 人間の確認者を、**計測開始前**に固定する。
一致が 1 件でもあればその候補を holdout から外し、残候補のみで再承認する。既存 WAL が欠落している
可能性はこの確認で解消しないため、「リポジトリに記録された既知性」に関する確認であることも報告する。

### 3.2 選択手続き

**推奨裁定:** 設計承認時に、人間が上記の候補から 2 点を選び、選択理由を「結果を閲覧していない
ことを検証した後の被覆目的」に限って承認記録へ固定する。

承認 commit hash を seed とする機械選択は恣意性を減らす利点がある一方、候補列挙・hash 作成順・
commit 内容に選択自由度を移す。候補が 4 点と小さく、各候補の未既知性を人間が監査できる本設計では、
理由と証跡を明示する人間選択の方が監査可能である。選択後の候補差替え、追加、seed の再試行は
**再凍結 + 承認**なしに行わない。

### 3.3 全件報告規則

- 各 holdout 条件、各 arm、各 variant、各試行について、開始・build・legacy verify・S2 verify・
  bench・abort・timeout・screen-reject を WAL に残す。成功値だけを別表に選別しない。
- 結果表は「全 holdout × 全 arm × 全固定 variant」を行として列挙し、欠測は理由付きの
  **判定不能**として残す。後からの除外は、開始前に列挙した機械故障理由に限り、元行を残して
  `excluded_reason` を付す。
- bench-first screening v2 (D58) を opt-in した場合、screen 棄却は除外ではなく**報告済み転帰**である。
  機械故障だけを表す `excluded_reason` とは別に `screen_outcome` を記録して行を残し、報告から落としては
  ならない。generation/search 実験では提案 universe（全 attempt、全 reject、全 screen 棄却）も manifest
  と同様に全件報告の対象とする。
- `output/s6-rounds/` の S-2/S-3 提案ラウンド束と同じく、報告生成器は output directory の
  個別選択ではなく freeze manifest に記録した全 campaign ID を入力にする。manifest 外の
  campaign を結果へ混入させず、manifest 内の campaign を黙って落とさない。

## 4. 対照設計（凍結項目 2）

各 holdout に対し、以下の 3 arm を同一 schedule block 内でランダム化する。

|arm|planner/coder/selector に渡す入力|目的|
|---|---|---|
|on|当該 holdout の正しい descriptor|descriptor 条件付き挙動の観測|
|off|selector には descriptor を渡さず静的既定選択とし、planner/coder には固定の中立入力|descriptor 非使用対照|
|swapped|同じ holdout 集合の別条件の descriptor|誤った descriptor が選択を駆動するかの検査|

`swapped` は対象 workload の benchmark 設定を変えず、入力 descriptor だけを置換する。対応先は
承認時に derangement（自己対応なしの置換）として固定し、実走者・エージェントへ対応表を公開しない。
全 arm は**同一 variant 集合、同一探索予算、同一 correctness gate、同一乱数・ブロック化規則**を
用いる。selector 実験では固定集合から選び、generation/search 実験では arm 間で search space と
開始状態も同一にする。

凍結項目 2 の任意対照のうち、blind（内容を伏せたダミー descriptor）は置かず swapped のみを採る。
別 workload の実 descriptor はダミーより強い攪乱であり、swapped が blind を強く含意するためである。

## 5. variant 集合・探索予算・correctness gate・対象別 floor・選択規則（凍結項目 3）

### 5.1 selector 実験の固定 variant 集合、採点 oracle と予測選択

`output/s1-freeze/known_axes_freeze.json` の各 workload `entries` を基点に、次の 6 構成を
canonical genome/implementation hash ごとに freeze する。

`p2_2_flag_opt`, `backoff_fixed_best`, `sort_best`, `system_gate`, `ident_all`, `stock_common`

選択は次の二層を混同しない。

1. **採点 oracle（descriptor 非依存）:** holdout workload ごとに freeze した 6 構成をすべて評価し、
   correctness を通過した構成だけを候補として一意最大を ground-truth 最良と確定する。同値最大、欠測、
   non-finite 値は tie / 判定不能へ倒す。これは arm 間で不変であり、対象別 between-run floor の算出基盤でも
   ある。既知 workload 別 argmax を holdout へ転記せず、同 freeze の `selection_rules` は参照用の実例に
   とどめる。
2. **selector の予測選択（descriptor 依存）:** これが実験対象である。selector は planner-v4/coder-v4 と
   同型の `tools=[]`・構造化出力だけのエージェントとし、固定 6 構成の識別子と設計由来の静的メタデータだけを
   入力にする。実測性能値は渡さない。on は当該 holdout の正しい descriptor、off は descriptor なしでの
   静的既定選択、swapped は derangement で別 workload の descriptor を入力にし、6 構成からちょうど 1 件を
   予測選択として返す。

`system_gate` と `ident_all` は D50 の結果を新規根拠にせず、固定 comparator としてのみ扱う。

### 5.2 gate・floor・予算

- **correctness gate:** 現行 `verify` の legacy + S2 をそのまま使用する。緩和、片方のみの通過、
  screen-reject を certified 扱いする変更は不可である（絶対規律 2）。
- **ビルド分離:** floor、oracle の性能差、判定表に使う数値は trace-disabled build の bench だけから採る。
  correctness gate は trace-enabled build の `verify` だけから採り、両者は別ビルド・別 run とする
  （CLAUDE.md 絶対規律 1）。予算台帳は両者を合算計上してよいが、性能比較に verify 側の数値を混ぜない。
- **対象別 between-run floor:** S-1 checklist が予定する対象別再実測を、holdout の各 workload と
  比較対に先行させる。数値はこの draft では凍結しない。発効時には `floor_<holdout>` の値、測定
  n、時間分離 block、算出式を空欄から埋めて再凍結する。floor 未確定・欠測・hash 不一致は判定不能である。
- **探索予算:** 第一単位を累積**ベンチ実時間（秒）**とする。arm ごとの上限 `B_arm_seconds`、
  holdout ごとの上限、総上限 `B_total_seconds` を発効時に数値で凍結し、build/verify/bench/timeout
  を含む wall time を台帳に記録する。LLM 呼び出し回数は第二軸の上限として併記してよいが、予算の
  代替にしない。予算不足は未実施 arm を対称に判定不能へ倒し、途中成績で arm を止めない。

bench-first screening v2 は D58 の範囲で**opt-in**できる。ただし基準点・floor 再実測・S-1・
検証相・LLM loop には適用しない。採用する初回 campaign では、
`output/insights/2026-07-14_bench-first-screening-design.md` §5–7 の 4 基準、すなわち
誤棄却ゼロ、結論不変、総機械時間の削減率、同一 genome の on/off fitness の floor 内一致を
on/off で報告する。逐次停止は D58 の対象外であり、本設計へ導入しない。

## 6. 判定基準（凍結項目 4）

「異なる勝者が出た」だけでは descriptor が選択を駆動した根拠にならない。以下は selector 実験の
最小判定表であり、generation/search 実験にも選択段の判定として適用する。

|条件|成立|不成立|判定不能|
|---|---|---|---|
|on/off 予測差|on の予測選択が off の予測選択と異なる holdout が存在する|完全なデータがあり、全 holdout で同一予測|selector 出力欠測または不正|
|swapped 追従|swapped の予測が swap 元 workload に対する on の予測へ追従し、descriptor を実際に消費した証拠を示す|完全なデータがあり、その追従がない|derangement 未固定、selector 出力欠測または不正|
|oracle floor 超|on の予測構成と off の予測構成の oracle 実測性能差が当該対象別 between-run floor を超える|完全なデータがあり、差が floor 以下|oracle 非一意、欠測、gate 不通過、floor 未確定|
|結論|上 3 条件の連言が成立|完全なデータがあり、いずれかが不成立|前 3 条件のいずれかが判定不能|

swapped の追従は、swap 元 workload における on の**予測選択**との一致として、結果を実走する前の
対応表へ固定する。後から oracle winner を見て整合性を定義してはならない。一つの同一選択が複数
descriptor で予測されることは、データが完全なら「この固定集合では descriptor 駆動を支持しない」と
報告する。

統計検定を主張に加える場合は、`docs/phase3-main-experiment.md` の「2026-07-15 着手時確定 —
S-1 サンプル設計 4 点」と同じく、**n、検定単位、検定力（α を内包。又は prospective power 未保証の明記）、
総予算**を実走前に数値で凍結する。本 draft は対象別 floor が未再測定のため、これらの数値を
**floor 再実測後に確定**と保留する。保留中は効果量・全件記述を報告できても、検定付きの肯定主張はしない。

## 7. 段階計画とアブレーション

1. **最小 end-to-end（E2E）:** 固定 6 構成の selector 実験を先に実装・実走する。これは入力射影、
   on/off/swapped、freeze、全件報告の配線を検査する最小面である。
2. **generation/search 実験:** selector の成功・失敗と独立に、ワークロード特化合成を主張する前に
   実施する。selector が有意でも、この段を省略して合成主張へ進まない。
3. **8a 軸の再利用:** `silo-backoff-trigger-gating` を高競合で再利用する場合は、この holdout、
   arm、全件報告、gate、floor の全規定に組み込む。`docs/phase3.md` の 2026-07-14 裁定どおり、
   低競合（records=100k/threads=4）の単独再ホストはせず、既知 rr 比率の winner switching を
   新発見として数えない。
4. **screening の ablation:** screening opt-in 時だけ同一 genome 集合を screening on/off で走らせ、
   §5.2 の 4 基準を全件報告する。screening は descriptor on/off/swapped の代替ではない。

## 8. この文書が凍結するものと変更手続き

発効時に本書は次を凍結する。

- descriptor schema、禁止フィールド、生成元、射影記録。
- holdout 候補の未既知性確認手順、選択済み holdout、全件報告 manifest。
- on/off/swapped の arm、swapped 対応、variant 集合、correctness gate、選択規則。
- floor の算出入力、探索予算、判定表、検定を行う場合の数値 4 点（n、検定単位、検定力（α を内包）、総予算）。
- screening opt-in の有無と、採用時の 4 基準 ablation。

発効後に holdout、schema、variant 集合、予算、gate、floor、選択規則、判定基準、統計数値、
screening の範囲を変更する場合は、旧 freeze と変更理由を残し、**再凍結 + ユーザー承認**を要する。
既知 rr5/rr50/rr95 の配線 demo を追加しても、この手続きを迂回して新規科学的主張へ数え替えてはならない。
