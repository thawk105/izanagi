# Phase 3 段 8b: workload descriptor の前向き設計

**状態: 発効 (2026-07-16 ユーザー承認) — 本文書の凍結項目は実走前凍結として効力を持つ。
以後の変更は再凍結 + 承認による**

**承認記録 (2026-07-16):** holdout はユーザー承認により **H1 (`rratio=80`) と H2 (`rratio=20`)**
を選択した。選択理由 (結果非閲覧の被覆目的に限る): descriptor の中核フィールド (read/write 比率)
が選択を最も直接に駆動すべき軸上の未測定内挿点 2 点であり、H3 (skew 変更)・H4 (rmw 変更) は
校正動作点 (skew=0.9, rmw=0 で確定した records/threads) の前提が変わり、descriptor 効果と校正の
ずれが交絡するため次サイクル以降に回す。選択時点で H1/H2 の測定結果はリポジトリのどこにも
存在しない (§3.1 の未既知性確認は実走前 freeze 手順で機械実行する)。選択後の差替え・追加は
§3.2 のとおり再凍結 + 承認なしに行わない。

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

## 9. 再凍結 draft 2026-07-16 — selector 実装裁定（項 1〜6 承認済み、項 7〜8 承認待ち）

selector 役の実装設計 (独立コンテキストの設計相談 2 本 + 親裁定) で、§4/§5.1 が未規定または
複数解釈を許す点が見つかった。以下は**選択規則に関わるため実装既定にせず**、再凍結事項として
ユーザー承認を求める。旧凍結からの変更理由は各項に付す。

**承認状態 (2026-07-16 ユーザー裁定、worklog 2026-07-16 (9) 追記・(11)):** bundle A = 項 1〜3、
bundle B = 項 4〜6 を承認 (発効)。項 7〜8 も承認 (発効、裁定資料 =
`output/insights/2026-07-16_s8b-ruling-package.md` の裁定 1〜2)。**項 8 は択 (a) = crash 後の
再走なし** (途中 crash は当該実験全体を判定不能に倒す。再走を許す変更は同資料 裁定 2 択 (b) の
attempt registry を §8 手続きで再凍結してから)。同日の追加裁定: A3-3 トポロジー (単一 block +
累積台帳 + 事前一括 reservation)・A3-4 status/rc 契約・R5 truth table 5 項目の推奨案を承認
(worklog (11)。再凍結本文は freeze v2 で §8 手続きに従い凍結する)。floor 実測 env は択 C
(env-neutral 共通実装の先行) を採用し、v2 数値を束縛する唯一の env-tag は floor 実測開始時に
確定する (ユーザーは当面 Pegasus で作業)。
承認は選択規則の確定であり、selector 予測の実実行はさらに前提条件 (freeze 再凍結による design
hash 追随 / trusted prediction runner / §6 量化 4 点の再凍結 + 結合 judge / resume 拒否の強化 —
worklog 2026-07-16 (9)「次の一手」1。A3-3・A3-4 の設計裁定は (11) で完了) を要する。

1. **off arm の静的既定選択 = `stock_common` 固定（agent 非呼び出し）。** §4 の「静的既定選択」は
   LLM を呼ばない固定規則と解する。`stock_common` は 6 構成中唯一 workload 別 argmax 由来でなく
   upstream defaults 由来であり、既定として最も防御可能。予測台帳には
   `decision_method="static_default"` を記録する。（旧凍結は off の具体既定値を未規定）
2. **selector-visible カタログは不透明 ID + workload 不変の中立機構語彙。** freeze の
   `variant_binding` 生フィールド（flags・backoff 値・comparator・gate 述語・sources のパス）は
   値の由来が既知 argmax であり、`sources` パスは anchor workload 名を直接含むため、selector には
   一切渡さない。渡すのは固定 6 件の `{choice_id: c01..c06, mechanism: 制御語彙}` のみで、全
   holdout・全呼び出しで byte 同一。ID→構成の解決は信頼中核だけが予測**後**に行う。（旧凍結の
   「設計由来の静的メタデータ」の解釈を、性能結果を lineage に持つ値を除外する側へ確定）
3. **swapped 追従の判定単位は構成 family ID の一致。** 現行 variant_binding は holdout ごとに
   実装実体が異なる（nearest-read-ratio-v1 の帰結）ため、§6 の「swapped の予測が swap 元への
   on の予測へ追従」は exact implementation でなく family ID（c01..c06 ↔ 6 構成名）の一致として
   判定する。主張は workload-aware family selection に限定される。
4. **予測は 2 holdout × 3 arm = 6 セルを各独立 1 回で固定。** on/swapped は fresh・tools なしの
   selector を同一 payload でもセルごとに独立実行し、結果の再利用・不正出力の再試行をしない
   （同一 payload の出力共有は swapped 追従を構造的な恒真にする。再試行は cherry-pick になる）。
5. **selector 出力の欠測・不正は fallback せず判定不能。** strict parser（未知キー・重複キー・
   複数選択・fence・非有限値を拒否）を通らないセルは `choice_id=null` で凍結し、§6 の該当条件を
   判定不能へ倒す。既定構成への fallback は置かない。
6. **予測凍結と oracle の分離。** 予測は `output/s8b-freeze/` 配下に承認後に生成する
   `selector_predictions.json` (本 draft 時点では未生成) として、oracle 実走前へ
   exclusive-create + 内容 hash + commit pin で封印し、swapped 追従の期待値
   （`on[derangement[target]].choice_id`）もこの時点で固定する。oracle 結果は別ファイルへ書き、
   予測ファイルを更新しない。floor/budget の後日再凍結でファイル全体 hash が変わっても予測を
   継続利用できるよう、holdout 条件・derangement・variant_binding・カタログ対応だけの部分 hash
   （selector_basis）で束縛する。
7. **oracle 集約規則 = 試行内中央値の構成中央値（median of medians）。**（§5.1 は一意最大の
   確定を規定するが集約統計量が未規定だった。floor は argmax の tie-break に使わず、on/off
   予測構成差の判定にのみ使う — §6 のとおり）
8. **実走後の途中再開は拒否。** 実走後は WAL に holdout 条件が現れ、freeze の未既知性検索が
   意図どおり fail するため、新プロセスでの resume は安全側で拒否する。resume を許す設計変更は
   未既知性検査範囲の変更であり、別途の再凍結 + 承認を要する。

floor・budget・n・seed・block・extime/reps・機械故障一覧（allowed_excluded_reasons）・検定数値は
§5.2/§6/§8 のとおり floor 再実測後の再凍結で数値を充填する（本 draft では凍結しない）。

**承認状態 (2026-07-18 ユーザー裁定、worklog 2026-07-18 (2)): floor protocol 凍結案パッケージ
F1 = 修正付き採用。** 裁定資料 = `output/insights/2026-07-16_s8b-floor-protocol-package.md`
(裁定資料は凍結族のため不変。F2〜F7・追加材料 B-1/B-2 は裁定継続中で、protocol JSON の凍結と
実装・テストの改訂は全裁定完了後)。修正内容:

- **標本設計の縮小 (ユーザー裁定):** トップ会議 (VLDB 等) の CC 実験報告水準に合わせ、温度・
  バックグラウンド処理起因の微細変動は追わない。2 block 構造と `min_block_gap_s=1800` を廃止し
  8 session 連続 1 パス。算出式から block 対比差 `delta_c` 項を削除:
  `floor_pair(c) = max(u_noise(c), wired_min_rel_floor × m_stock)`。`s8b-floor-stats/v1` は
  2 block 前提のため formula_id ごと再定義する。所見 D1/E1 (周期共鳴・contrast drift) は不採用へ
  降格し、「時間ドリフト・cold-boot・温度は floor に含まれない下限」を限界として報告に明記する
- **マシン異常検出の追加 (fail-closed 専用):** (i) `performance_anomaly` = session 内 5 反復の
  CV (stdev n-1 / 算術平均) > 10% → session 無効。F2 の閉じた除外理由表へ 4 行目として追加
  (必須証拠 = 全反復値、retry は既存スロット内、実時間は持ち時間の消費として計上)。
  (ii) `machine_anomaly` = セル間 CV (既存診断値 `cv_c = s_c / fmean(有効 session medians)`) >
  15% → 当該 pair の floor = null (判定不能)。閾値は protocol JSON に事前凍結し全セル同一適用。
  検出は無効化・判定不能へ倒す方向にのみ使い、測定の採り直しによる数値改善方向には使わない
- **維持:** n_sessions=8 / reps=5 exact / per-pair table (§5.2 のスカラーからの変更を含めて承認) /
  fail-closed null 意味論 / scale-adequacy gate ±10% / seed 均衡置換 (温度対策でなく実装コスト
  ゼロの基本衛生として維持 — ユーザー確認済み) / scalar_alt 併記 / 「記述的効果量 + noise gate、
  α・検定力未保証」の限定
- `master_seed` は未指定のまま (ユーザー記入欄、承認時に確定)

**承認状態 (2026-07-18 ユーザー裁定 続き、worklog 2026-07-18 (3)): F2・F3 = 推奨案どおり承認。**

- **F2 (運用・停止・retry・resume):** 閉じた除外理由表 (F1 裁定による `performance_anomaly` 行の
  追加込みで 4 行) / `retry_slots_per_cell=2` (campaign 通算、first-authorized-valid のみ採用、
  全試行の実時間を持ち時間の消費として計上) / journal は append-only + fsync、manifest・result は
  create-only / resume は同一 protocol・freeze・manifest・binary hash 限定の forward-only +
  binary 再ハッシュ照合 / 単独性は probe→measure→post-probe→journal の臨界区間 + strict probe
  (pgrep rc=1 のみ競合なし、検査不能は campaign abort)。correctness-red は floor に存在しない
  (perf 専用計測) も承認内容に含む
- **F3 (budget):** 三層 namespace (子枠間移転禁止) + 親 `B_campaign_wall` 全費用込み cap /
  oracle 側 verify ×96 (~11.6h prior) の正直計上 / `N_oracle=8` は非拘束の planning prior、
  `bench_max_rounds=1` / pilot は wall/bench 比の分解実測、cygnus 実測値は非拘束 prior。
  verify 証明書の cell 単位再利用は本パッケージどおり不提案のまま (起票なし)

**承認状態 (2026-07-18 ユーザー裁定 続き、worklog 2026-07-18 (3)): F4 = 修正付き採用 —
env contract 抽象を採用。** 凍結順序 (パッケージ承認 + protocol JSON 凍結 + env_tag 確定 →
selector 予測封印 (floor データ閲覧前) → floor 実走 → calculator 純関数の機械充填 + 独立再計算
一致 → v2 候補生成 + ユーザー承認 → oracle 実走) と「protocol JSON の env_tag が v2 数値を束縛
する唯一の env-tag」は推奨案どおり。修正内容:

- **「env_tag 一致検査のみ・env contract は Pegasus 差分に据え置き」を破棄し、
  `ExecutionEnvironmentContract` の抽象化を実装対象へ昇格** (ユーザー裁定: しばらく Pegasus を
  多用するため)。パッケージが F4 の既知限界とした「driver が cygnus 固有値 (48 threads /
  1M records / CLK1800 / numactl) をハードコードしたまま env_tag だけ記録」を env contract で
  解消する
- **所見 G12 の Pegasus 制約は「文書化のみ」から実装要件へ昇格:** campaign を単一 allocation /
  node / process で完遂 (パッケージの「block 単位」は F1 裁定で block 廃止のため campaign 単位に
  読み替え) / walltime 不足時は全廃棄 / hostname・boot id・job id・cpuset・UTC 記録 / PID 可視性の
  事前 probe / WAL は永続領域 (一時領域 `/scr` 不可) / module・toolchain・job script hash /
  monotonic 値は同一 process 内 duration 限定。計測作法は環境専用 runbook に従う
- env_tag の値は floor 実測開始時にユーザーが確定 (未指定のまま)。予測封印の位置は推奨どおり
  floor 前 (封印後は floor で構成順位が露出しても selector を動かせない拘束を含めて承認)

**承認状態 (2026-07-18 ユーザー裁定 続き、worklog 2026-07-18 (4)): F5 = 推奨案どおり承認。**
floor / budget は top-level 維持。floor は per-pair table 形
(`by_holdout.<h>.{pairs, scale_ref, scalar_alt}`) とし、manifest validator の per-pair 形状への
追随は v2 実装項目。transition table は 2 分離 — v1→v2 で変わってよい field の列挙 (floor /
budget / refreeze_note / schema_version / generator.sha256 / design_source.sha256 /
frozen_at_head / env_tag / floor_protocol / floor_source / experiment_numbers / v2 header) と、
v2 gN→gN+1 で変わってよいのは floor・budget・experiment_numbers 系 + header のみ。**それ以外の
diff は verifier 拒否。** 全 field に実 consumer を要求し、consumer 不在 field (例
`B_arm_seconds`) は消費側を同時実装しない限り凍結しない (恒真保証 F14 の拒否)。

**承認状態 (2026-07-18 ユーザー裁定 続き、worklog 2026-07-18 (6)): F6 = 択 (a) で確定、
F7 = 推奨案どおり承認、追加材料 B-1・B-2 = 採用、実装解釈の追認 2 件。floor protocol
パッケージ (F1〜F7) の裁定はこれで完結。**

- **F6 (a) 承認レコード方式:** approval record =
  `output/s8b-freeze/approvals/<generation_sha256>.json` (path は世代 bytes hash から導出、
  自己参照回避)。内容 = strict canonical JSON {generation_sha256, approver, approved_at, scope}。
  **ユーザーが commit し、その commit は `AI-Agent: none` 逐語 trailer を持つ。** 検証 = record
  存在 ∧ filename・内容 hash の世代一致 ∧ HEAD ancestry ∧ trailer ∧ 導入後の path 改変履歴なし。
  取り消し = 不可逆 tombstone。active 世代 = 明示 active pointer (複数 successor・pointer 不正・
  revoked → active なし fail-closed。「最新 = 有効」禁止)。発効順序 = 方式裁定 → source head →
  AI が inactive 候補生成 (AI trailer 付き commit) → ユーザーが別 commit で approval + active
  pointer → `load_ratified_freeze` のみが実走 consumer。「規約 attestation であり人間性の
  暗号学的証明ではない」限界を含めて承認 (強化選択肢 (b) 署名方式は将来の再裁定へ)。裁定前の
  問答で「自動合成ループは止めない (発効決定の機械化である)」を確認済み
- **F7 (v2 検証意味論):** (1) source は `frozen_at_head` (pre-generation source head へ再定義)
  の git blob bytes で照合 / (2) 未知性は二層 = v1 凍結時点で成立 ∧ v1 以後の conjunction hit が
  申告済み計測 closure と完全一致 (launch certificate 方式) / (3) 全 consumer を単一
  `load_ratified_freeze` へ統一 (duplicate key・NaN・未知 key 拒否、generation hash・連鎖・
  approval・active の一括検証) / (4) floor driver は暫定 bytes sha256 pin (実装済み)。
  protocol JSON = 機械正本・md = 説明、の正本分離を含む。closure 完全一致の代償 (申告漏れ
  1 件で fail-closed 不合格) を含めて承認
- **B-1:** manifest canonicalizer / writer を `allow_nan=False` へ統一 (fail-closed 強化) を採用
- **B-2:** 単独性 probe の身内除外を**自 PID のみ**へ縮小する方針を採用。適用対象 = 共有 helper
  (`competing_bench_pids`) と floor strict_probe の両方 (wave3 実査で同型の子孫除外を確認)。
  freeze-v2-design-material の子孫除外記載との差異は本裁定記録が上書きする (凍結文書は不変)
- **追認 2 件 (裁定文言の実装解釈):** (i) F2 の retry「block 末尾消化」は block 廃止 (F1) に伴い
  **round 末尾消化**へ読み替え (実装済み: retry 順は schedule 順で事前決定 + 他セル性能値への
  metamorphic test) — 追認。(ii) settle timeout は floor 経路が settle 非使用のため該当なし
  (第五の除外理由は置かない) — 追認
- 未指定のまま残る空欄: master_seed / env_tag (protocol JSON 凍結時にユーザー確定)、
  実行責任者・開始時刻 (floor 実走時)

## 10. 再凍結 2026-08-18 — 床値比較の撤去と事前割当 attempt registry (§8 手続きによる改訂)

**承認記録:** 2026-08-18 のユーザー裁定 ([T-1336] / [T-1337]、`/rulings` 全件 第 7 回)。
本節は §8 の変更手続きに従う再凍結であり、**旧凍結本文 (§5.2・§6・§9) は 1 byte も改変せず
履歴として残す**。矛盾が生じた箇所では本節が勝つ。上書きする範囲は §5.2 の対象別 floor bullet、
§6 の条件 3・結論行・検定数値の保留理由、§7 項 3 の「gate、floor の全規定に組み込む」のうち
floor に関する部分 (10.1 の対比規則と 10.4 の測定衛生へ読み替える)、§9 の前提段落が挙げる
「resume 拒否の強化」(10.5 の事前割当 attempt registry へ読み替える)、§9 項 7 の floor 用途と
項 8、および §9 末尾の数値充填列挙のうち floor に関する部分である。
それ以外の凍結項目は不変である。

**変更理由:** 過去に凍結した値と現在の測定値を比べる形をやめ、同じ campaign の中で対にして
測った値どうしの比較へ移す (D496)。測定が落ちたときの測り直しの単位は campaign 全体でなく
**落ちた構成だけ**とする (2026-08-18 の D496 決定 3 改訂)。

### 10.1 判定表の条件 3 と結論 (§6 の当該 2 行を上書きする)

|条件|成立|不成立|判定不能|
|---|---|---|---|
|反復単位の対比|holdout ごとに、`on` の予測構成と `off` の予測構成を**同一反復添字**で対にし、correctness gate を通過した trace-disabled bench の構成内中央値から差の列を作る。事前記入済みの `delta_min` / `sd_max` に対し、差の**有限な平均** > `delta_min` かつ**有限な標本 SD** <= `sd_max`|完全 block・反復 2 以上・数値パラメータ確定・gate 通過が揃い、予測構成が同一である、平均が `delta_min` 以下である、または標本 SD が `sd_max` を超える|selector 出力の欠測・不正、gate 不通過、反復添字の欠測・重複・不連続、不完全 block、反復 2 未満、非有限値、数値パラメータ未記入または hash 不一致|
|結論|on/off 予測差、swapped 追従、上記対比の 3 つが成立|完全なデータがあり、いずれかが不成立|いずれかが判定不能|

対比の作り方は次に限る。**schedule 上で隣接する行を対と見なしてはならない。**

- 対は同一 holdout・同一反復添字の 2 構成で作る。反復添字は manifest の schedule row が持つ
  replicate 添字であり、observations 側の schedule 添字で行の同一性と順序を照合する。
- 各反復が全 (holdout, 構成) を 1 度ずつ持つ**完全 block** であることを要求する。欠測・重複・
  1 始まりでない連番・cell 間の反復集合不一致は判定不能とし、行を削って対を作り直さない。
- 対にできない標本へ unpaired 推定で退避しない。

**判定が消費する量は、対差の有限な平均と有限な標本 SD だけである。** 標本 SD の分母は n-1 とする。
共分散・相関・相対差・散布比は必ず併記するが、主量へ昇格させない。これらが null または
非有限になっても、それだけで対比を判定不能へ倒さない — 理由付きの診断値として残す。

**走行内変動係数をそのまま閾値化しない。** 単独構成の変動係数、session 内反復の変動係数、
2 構成それぞれの標本 SD の単純加算は、条件の成立・不成立を決める入力にしない。対で測った
2 構成の差の分散は `Var(a) + Var(b) - 2 Cov(a,b)` であり、共分散を無視する形は正の相関の下で
差の分散を過大評価する。既存の走行内異常検出は測定衛生の fail-closed 判定として残せるが、
性能差の成立根拠にしない。

### 10.2 数値パラメータの制約と解除条件

`n` / `delta_min` / `sd_max` の**値は本節では凍結しない**。凍結するのは対の作り方、主量、
三値判定、比較の向き、退避の禁止、および次の制約である。

- `n` は整数かつ 2 以上。**登録した `n` は観測反復数と exact に一致しなければならない** —
  manifest は cell ごとに `n` を持ち、全 cell の観測反復集合が登録値と完全一致しないときは
  当該対比を判定不能とする。「反復 2 以上」を満たすだけでは足りない。
- `delta_min` は有限の正の実質効果境界。単位と向き (どちらの構成を引くか) を同時に固定する。
- `sd_max` は有限の非負。
- **契約値がこの制約を満たさない場合、個別の対比を判定不能にするのではなく、事前登録そのものを
  未発効へ倒す。** 不正な値で走った測定は本系列の試行に数えない。
- **この制約の現在の担保は「欄が空であること」だけである。** 8c の発効判定は欄が記入済みかどうかしか
  見ず、値の型・単位・範囲は検証しない。したがって**同欄を記入してよいのは、型・有限性・符号・単位・
  向きを機械検証する consumer が実在するときに限る**。それまで欄は未記入のままとし、未記入は
  8c の発効判定により未発効を意味する。この順序を守らない記入は、検証されない値で発効を通す。

値を記入してよいのは次がすべて成立したときに限る。schedule generator・manifest・反復束縛が
固定済みであること。正式結果とは別の対計画用 pilot が完全 block として成立していること。
対比と結果表を実際に消費する judge が実装済みであること。`n` / `delta_min` / `sd_max` を
**結果を見る前に**決めていること。§8 の再凍結とユーザー承認が済んでいること。

### 10.3 順位の事実と性能主張の二層化、および独立した選択評価表

- **生値層 (descriptive)。** 構成ごとの反復生値と、その構成内中央値による順位を全件報告する。
  同順位・欠測・gate 不通過も表から落とさない。**この表は `descriptive_only` であり、
  それ自体は性能主張ではない。**
- **公式性能層。** 公式の性能主張は、対になった生値の差とその標本分散**だけ**から出す
  (10.1 の条件)。公式表は成立・不成立・判定不能の三値 `official_status` を持ち、
  certified な選択を作る consumer はこの層だけを受理する。
- **選択評価表 (独立した第三の表)。** on/off 予測差、swapped 追従、予測構成と生値順位の整合を
  扱う。これは「選択が当たったか」の主張であり、性能向上の証明と呼ばない。
  **性能主張の二層は生値層と公式性能層であり、選択評価はその二層に含めない。**
  結果構造は「二層 + 独立した第三表」の計 3 表であって、選択評価を公式性能表へ混ぜない。

**この改訂で消える保証を名指しする。** 旧条件 3 とその周辺が要求していた次の 4 つは、
新しい生値側の主張からは消える。(i) 対象別 between-run floor の超過、(ii) scale adequacy gate、
(iii) oracle の一意最大 (unique-best) の確定、(iv) 両構成の eligibility 判定。
消えた分は、対差の分散が「この差は測定のばらつきより大きい」を担う形へ置き換わる。
順位が同じでも公式判定が不成立・判定不能へ変わりうること、およびその逆が無いことを、
consumer は区別しなければならない。

### 10.4 測定の近接性と主張の強さ

比較の主張の強さは測定の近接性で決まる。**同一機で連続して測った値どうしの比較が最も強い。**

- 各観測に、測定時刻・実行環境・実装および toolchain の identity を保存する。
- 比較を次の 3 種に区別し、**主張強度のラベルを別にする**。(a) 連続して測った対、
  (b) 事故からの復旧で時間差が生じた対、(c) 意図的に過去の凍結値と比べる形。
  (c) は採らない (D496 決定 1)。
- (b) を無修飾の「同時対測定」として報告してはならない。時間差の大きさを併記する。
- 数日規模のずれは現実として許容するが、過去であるほど・測定環境が異なるほど信頼性が弱まる
  ものとして扱う。

### 10.5 実走後の途中再開 (§9 項 8 を上書きする)

§9 項 8 の「実走後の途中再開は拒否 (択 (a))」は、2026-08-18 のユーザー裁定により
**freeze-wide の事前割当 attempt registry** (当時併記された択 (b)) へ改訂する。D496 決定 3 を
§9 項 8 より優先する。測り直しの単位は**落ちた構成だけ**であり、無傷の構成を巻き込まない。

- **事前割当。** freeze 全体の全 (holdout, 構成, 反復, attempt) slot を、最初の観測の前に
  閉じた集合として割り当て、追記専用の registry へ束縛する。
- **消費の範囲。** 落ちた構成の同じ反復についてのみ、次の事前割当 slot を消費できる。
  slot の後出し追加、成績を見た後の再走選択、成功済み構成の再測定を拒否する。
  割当の枯渇は当該対比を判定不能にする。
- **観測値の不変性。** 観測済みの値を後から差し替える経路は registry でも許さない。
  primary value が一度封印された attempt は再走できない。
- **失敗分類の事前確定。** 再走を許す失敗理由は**閉じた集合**とする。閉じた集合であることを
  宣言するだけでは足りず、次を同時に要求する。(i) 許可理由を**exact な列挙**として事前登録の
  凍結範囲へ書き、後から要素を足さない。(ii) 分類は**信頼側の起動器が行い**、その根拠は
  当該 attempt の性能出力の**外側**にある証拠 (process の終了状態、環境側の記録) に限る。
  (iii) 分類は信頼側が性能出力を読む**前**に確定し、create-only の受領証として残す。
  correctness-red を再測定で救済しない。値を見た後に parser 失敗や終端欠落へ分類し直して
  再走を得る経路を拒否する。**全 attempt を報告する。**
- **単一の registry。** freeze ごとに唯一の master registry root を測定開始前に固定する。
  **唯一性は宣言でなく束縛で担保する** — root の canonical path と初期 bytes hash を
  内容 commit または発効束縛 record が持ち、freeze identity を key とする exclusive-create で
  作られたものだけを正とし、同一 freeze に対する第二の root を全履歴走査で拒否する。
  slot は schedule 行・run-start 受領証・process identity・raw output の hash・terminal status へ
  一対一に束縛し、別 attempt 識別子の下での出力 bytes の再利用を拒否する。

### 10.6 本節が発効させないもの (epoch 境界)

**本節と対応する条件契約の世代は仕様だけを発効させ、測定を認可しない。** 8c 側の判定器・
証拠契約・attempt registry・結果 judge が追随するまで、本系列の測定は行わない。

- 本節の発効前および追随実装の発効前に走った run は legacy・exploratory であり、
  後から formal へ昇格・再解釈・混合しない。
- 最終判定層の現用実装は依然として旧条件 3 (床値超) と scale gate を使う。本節はその実装を
  変更しない。実装の追随は別 wave が行う。
- 性能成果物には、測定開始時の commit、発効中の事前登録 commit、判定器の版、registry root の
  hash を記録する。これらを欠く成果物を本系列の結果として受理しない。

### 10.7 本節の限界 (正直な現在地)

- **設計本文の bytes pin は現に一致していない。** `output/s8b-freeze/holdout_freeze.json` の
  `design_source.sha256` は本節を追記する前から現物と一致していなかった。当該照合は
  2026-08-12 のユーザー裁定により保留中であり、本節の追記で新たに発火するものではない。
  **保留は健全性の証明ではない** — 鎖は未検証のままである。pin の更新は追随 wave が行う。
- **本節は機械 record を持たない。** 8c 側の条件契約は世代 record で改訂を記録するが、
  8b にはその機構が無い。本節の改訂が行われた事実は git 履歴と本文だけが担う。

## 11. 再凍結 2026-08-19 — workload descriptor へ人間の自由記述方針ヒントを追加 (§8 手続きによる改訂)

**承認記録:** roadmap.md §1 の入力契約協議改訂 (2026-08-19 ユーザー協議、branch
`worktree-roadmap-workload-hint` commit `15b5c389`) と、その実装スコープを指定した同日の
dev-wave 起票がユーザー承認に当たる。設計境界は decision (`{{D:workload-policy-hint}}`)
に確定済み。本節は §8 の変更手続きに従う再凍結であり、**旧凍結本文 (§2.1 の schema ブロック、
§2.2 の生成元、§8 の凍結列挙) は 1 byte も改変せず履歴として残す**。上書きする範囲は
§2.1 の schema が持つ property 集合 (7 property → optional `policy_hint` を含む 8 property) と、
§2.2 の記述が前提とする「descriptor は既知の型付きフィールドだけを持つ」という暗黙の閉包
(hint という 8 番目の optional フィールドの存在を追加する) だけである。それ以外の凍結項目
(禁止フィールド、生成元 `campaign_search_config_projection`/`human_declared` の二値、
holdout・arm・variant 集合・gate・floor・判定基準) は不変である。

**変更内容:** `orchestrator/campaign/s8b_descriptor_schema.json` の `properties` へ
`"policy_hint": {"type": "string"}` を追加した (`required` には追加しない — 既存 descriptor
は無改修のまま有効)。`orchestrator/campaign/s8b_descriptor.py` の `project_from_search_config()`
は、入力 `search_config` に `policy_hint` キーがあるときだけ同名キーを出力 descriptor へ
条件付きで追加する。**キーが無い入力の出力 bytes は 1 bit も変わらない** — 凍結済み
`output/s8c-preregistration/arm-inputs/off-neutral-descriptor.v1.json` (281 bytes) は本節の
発効後も同一 bytes・同一 SHA-256 のままである (dev-wave 実装時に実測して確認した)。

**変更理由:** ユーザーとの協議で、workload descriptor に人間が任意で自由記述の方針ヒントを
添えられるようにする方針が決まった (roadmap.md §1)。AI 側の各段はヒントが与えられれば
そのまま判断材料に使ってよい (規律6 の未信頼入力ではなくユーザーの直接入力)。ヒントは
workload の傾向・重視目的の記述に限り、hole や具体実装 (勝ち筋) は roadmap.md §2 D44
「軸提案がループ内にあること」の要件により含めない。この境界は decision fragment に
確定しているが、**本節が凍結する schema・射影関数は値の内容を検査しない** (型検査 (str) と
禁止キー走査 (キー名のみ) だけを行う) — 内容面の境界は運用規律であり、machine gate は
新設しない (decision fragment の裁定どおり)。

**本節が発効させないもの:** 8c 自律パイプライン (`p3_autonomous_workload_trial.py` 等) は
本節の対象外であり、`policy_hint` を投入する入力境界を持たない (本 wave では追加しない)。
段8b の selector、段8a の axis-proposer への配線も本節の対象外。段4 の human-supervised loop
(`p3_s4_loop.py`) への配線は本節と同じ dev-wave が別途行うが、descriptor schema の凍結対象
ではないため本節には含めない。
