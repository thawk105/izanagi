# 段 4 裁定 — [T-2102] D1344 の実測と択一

## 1. 何を測ったか、何が測れなかったか

D1344 は 2 つを要求している。(i) 予定されている scheduled input すべての `reference_tps` の
列挙、(ii) 非有限十進が**正当な upstream 出力**として一度でも生じるかの実測。
この 2 つは別の問いであり、本 wave での到達点も違う。

### (i) 文字どおりの列挙 — 実行した。production は 0 件、実在するのは fixture だけ

段 2 の plan 子が指定した手順どおり、封印済み registry の
`scheduled_attempts[*].reference_tps` と manifest の `rows[*].reference_tps` を
wire 形 `[分子, 分母]` のまま読み、`Fraction` にして既約分母から 2 と 5 を除いた。
**十進にも float にも変換していないので、この判定は恒真ではない。**

走査範囲は、この user が読める data filesystem 全域 (`/work/1/SFC/tanab` =
`/work/SFC/tanab`、`/home/SFC/tanab`、`/tmp`、`/dev/shm`)。結果 (`measurement-4.json`):

- B-4 封印済み成果物 **10 件**発見 (`scheduled-attempt-registry.jsonl` /
  `analysis-manifest.json` / 経路上の同名成果物)
- `reference_tps` の値 **2010 件**、相異なり **201 種**、**非有限十進 0 件**
- null 0 件、比でない値 0 件。相異なり 201 種はすべて `(N, 10)` の形
- **10 件すべてが pytest fixture** (`/tmp/pytest-of-tanab/` 配下)。
  production 由来の封印済み registry は **0 件**
- 走査できなかった dir 21 件はすべて他ユーザー・他セッションの private dir
  (permission denied)。全件を path 付きで記録した

したがって **production の scheduled input は 0 件**である。理由は「まだ作っていない」ではなく、
**`B4ScheduledAttemptInput` を祖先 certified snapshot から構成する producer が repo に存在しない**
ことである。registry の直接の入力は caller が渡す値であり、issuer 自身が
「caller schedule は外部の authoritative population に束縛されない」と明記する
(`p3_b4_prerun_issuer.py`)。非 test の構築点は prereg consumer の自己検査用 fixture
`_behavior_attempt` だけである。

**production の空集合を「非有限十進 0 件」の根拠には数えない。** これは段 3 の 3 レンズが
一致して警告した恒真化であり、その警告は正しい。fixture の 2010 件も production 値域の
証拠には数えない。数えるのは (ii) の値域実測である。

### (ii) `reference_tps` が指す量の値域 — 実測完了、非有限十進 0 件

事前登録 §5.1.1 は `reference_tps` を「その block の precursor から祖先方向へ辿って最初に
現れる certified snapshot の session-level throughput」と定める。この**量**の記録は
campaign WAL の終端 commit record にしか存在しない。実在する全記録を数えた。

| 実測 | 走査範囲 | 観測数 | 非有限十進 |
|---|---|---|---|
| 1 | repo 内 2 root、WAL 60 file | 5,928 | 0 |
| 2 | `output/campaigns/` の key 名 `tps`/`throughput` を含む**全 field** | 4,034 | 0 |
| 3 | `/work/1/SFC/tanab` 全体、WAL 5,541 発見 / 5,537 走査 | 443,911 | 0 |
| 5 | `/home/SFC/tanab`、`/dev/shm` | 0 (WAL 2 file、throughput 欄なし) | 0 |
| 4 | 実在する全封印済み registry / manifest (fixture 10 件) の exact 比 | 2,010 | 0 |

実測 3 は repo 外の official output root (`b10-backoff-grid-runs*`) を含む。
読めなかった 4 file と JSON 行 parse 失敗 22 件は件数と path を記録した。
4 file はいずれも「切り詰めた WAL を拒否する」ことを試す pytest fixture であり
campaign 成果物ではない。

## 2. 恒真性批判への回答 (段 3 の中心的所見)

段 3 の 3 レンズは「JSON の十進 token も IEEE-754 の float も定義上必ず有限十進なので、
その表現を測る限り結果は恒真だ」と指摘した。**この指摘は数学的に正しい。**
恒真な検査を exact 値域の非自明な証明と呼んではならない。

しかし批判の**含意** — 「恒真なゼロの背後に、丸められた正当な非有限 exact 比が隠れている
かもしれない」 — は成立しない。隠れるためには丸める前の exact 値がどこかに存在するか、
材料から再構成できる必要がある。

- 上流に有理数演算が無い。`benchparse.py` の `throughput_tps()` は float を返し、
  代替経路 `commits / extime` も float 同士の除算である。中央値も float 演算。
  campaign の非 test コードで `Fraction` を使うのは B-4 分析系、A-1 headline、
  s8b floor、b10 sweep だけで、throughput を作る側には無い。
- 高精度版の材料が記録に無い。`benchparse.py` が高精度版として名指しする
  `commit_counts_` と `actual_extime` は、campaign 成果物の全域で**それぞれ 0 件**である
  (完全走査、rc=1)。WAL の commit payload は `fitness_tps` / `cv` / `high_variance` /
  `unstable` の 4 key だけ。`pipeline.py` は `commit_counts_` を stdout から witness counter
  として読むが WAL へは載せない。

したがって、この量は float として**生まれて**おり、丸められた exact 前身は存在しない。
exact 比としての読み替えは、遡っても再構成できない。
段 3b の再検証子もこの含意を **無効化** と判定した。

## 3. real / refuted の裁定

### real (採用)

- **R1** — 親の当初母集合 (`commit.fitness_tps`) は §5.1.1 の `reference_tps` の定義そのもの
  ではない。祖先探索・snapshot hash・receipt hash・`PerfConfig`・`env_tag` の照合をしていない。
  → 裁定: 採用。ただし実測 2・3 で、参照点になりうる値を key で絞らずに数える上位集合へ
  拡張した。真の参照値はこの上位集合から選ばれる (他の記録が存在しないため)。
  上位集合で 0 件なら部分集合でも 0 件である。
- **R2** — 十進 token 判定と float 往復判定は有限十進について恒真である。
  → 裁定: 採用。§2 のとおり、恒真性そのものは認めたうえで、含意を実測で塞いだ。
  記録では「恒真な検査の 0 件」ではなく「exact 前身が記録に不在」を根拠として書く。
- **R3** — `layout.py` は official output root を任意の絶対 path に許すため、
  走査は原理的に閉じない。
  → 裁定: 採用。閉じられる範囲は閉じた (`/work/1/SFC/tanab` = `/work/SFC/tanab`、
  `/home/SFC/tanab`、`/tmp`、`/dev/shm`。この user が書ける data filesystem は `/work` と
  `/home` のみ)。走査できなかった 21 dir は他ユーザー・他セッションの private dir であり
  全件を記録した。閉じられない残余は限界として明記する。
  **「マシンのどこにも無い」とは書かない。「この user が読める範囲には無い」と書く。**
- **R4** — 段 2 の 4 境界案は "registry-only" ではない。`_ratio_payload` と
  `_ratio_from_payload` は registry と manifest の共用 codec であり、
  `_manifest_row_payload` は manifest 固有である。
  → 裁定: 採用。実装 wave への申し送りにする。本 wave では実装しない。
- **R5** — 既存テスト
  `test_p3_b4_raw_record_producer.py::test_m12_nonterminating_reference_ratio_has_only_named_rejection`
  は、registry で先に拒否すると producer の `_fraction_token` へ到達しなくなる。
  M12 を registry 拒否期待へ単純に書き換えると、**producer の丸め禁止分岐を一切検査しない
  恒真な保証**になる。
  → 裁定: 採用。**これは絶対規律 2 に直接触れる**ので、実装 wave の must-fix とする。
  M12 は `_fraction_token((1,3))` の直接検査へ再定義して producer 側の防壁を維持する。
- **R6** — `p3_b4_analysis_ledgers.py` は凍結 5-file closure の member なので、
  狭める側も closure identity を動かす。
  → 裁定: 採用。ただし R7 により費用は同等ではない。

### refuted (不採用)

- **F1** — 「恒真なゼロの背後に正当な非有限 exact 値が隠れうる」。
  → §2 のとおり材料が不在で再構成不能。段 3b も無効化と判定。
- **F2** — 「caller が任意の有理数を渡せるのだから非有限十進は正当な upstream 出力になりうる」。
  → issuer 自身が caller schedule の非束縛を明記する。transport 経路であって upstream 出力ではない。
  段 3 の sol・段 3b の両方が refuted 側で一致。
- **F3** — 「封印済み registry が無ければ原理的に測れない」。
  → 完全な pre-seal batch でも測定できる。ただし現状その batch も producer も無い (§1(i))。
- **F4** — 「closure member の bytes を固定値 pin した現存成果物がある」。
  → 検索 0 件。receipt は live bytes から生成される。固定されているのは §5.1.1 の
  section hash であって ledger bytes の hash ではない (R7)。
- **F5** — 「4 境界案なら非有限十進 attempt が先頭 201 件の選抜後まで残る」。
  → `generate_analysis_manifest()` は先頭で `assert_scheduled_registry_complete()` を呼び
  `_validate_attempt` を通すので、選抜前に落ちる。適格性述語へ足す必要はない。
- **F6** — 「本 wave で狭めるコードまで実装すべき」。
  → ユーザー引数が成果物を実測と択一の確定までと明記している。段 3 の luna も
  「実装しない判断は正しい」とした。

### 新事実 (R7)

凍結 closure の拘束は AST 構造 assertion と §5.1.1 の literal 一致であって、
member bytes の固定 hash pin ではない。現存する固定 pin は 0 件で、receipt は live bytes
から生成される。よって D1344 が (b) の却下理由に挙げた「凍結を動かす費用」は、
(a) 側では **closure identity が変わるだけ**で、更新すべき既存 pin は無い。
(b) 側は raw JSON schema の受理形を増やす変更であり、費用は同等ではない。

## 4. 択一の裁定

- **(b) を支持する production 証拠は 0 件である。** 正当な非有限十進の upstream 出力は
  実在せず、記録されておらず、再構成もできない。凍結された消費側を改訂して
  「何も生産しない値」を exact に運べるようにするのは、空集合のために凍結費用を払うことになる。
- **証拠の向きは (a) で一貫している。** 段 2・段 3 sol・段 3 luna・段 3b の 4 子すべてが
  (a) 側で一致し、(b) を支持する証拠を 1 つも挙げなかった。
- **ただし D1344 が文面で要求した (i) の列挙は、production については母集合が空である。**
  空である理由は「まだやっていない」ではなく、**registry の上流を束縛する producer が
  存在しない**ことである (D1345 / T-2103 と、precursor 束縛の T-2050 / T-2051 の領域)。
  これは D1344 の裁定時に見えていなかった事実である。
  手順自体は実行済みで、実在する全 registry (fixture 10 件、値 2010) でも非有限十進 0 件だった。

`DW-S04` に従い、親は承認済み裁定を不採用にせず、新事実を添えてユーザー再裁定へ返す。
本 wave が確定するのは次の 4 点であり、狭める実装は行わない。

1. `reference_tps` が指す量の production 値域には非有限十進が存在しない (実測 443,911 観測)。
2. 封印済み registry の文字どおりの列挙でも非有限十進 0 件 (2010 値)。ただし全件 fixture 由来。
3. (b) を支持する証拠は 0 件である。
4. D1344 の (i) は producer 不在のため production では空集合であり、
   その不在自体が別タスクの主題である。

### ユーザーへ返す択一

- **α (推奨)** — 値域の実測をもって D1344 の条件が満たされたと見なし、
  registry の受理値域を狭める実装を次 wave へ出す。根拠: 狭める側は受理集合を**縮めるだけ**で
  規律 2 に反しない。publication 段階で必ず落ちる値を封印段階で落とすので、
  201 試行を実走してから `EVIDENCE_SCHEMA` で失う経路が消える。(b) には証拠が 1 つも無い。
- **β** — producer (T-2050 / T-2051 / D1345) が実装され、完全な pre-seal batch を
  列挙できるようになるまで狭める実装を待つ。根拠: D1344 の文面に厳密に従う。
  代償: それまで registry は publication で必ず落ちる値を封印できる状態のまま残る。

**どちらの場合も (b) は採らない。丸め受理も採らない (D1344 が却下済み)。**

## 5. 実装 wave への申し送り (本 wave では実装しない)

- 述語: 既約分母から 2 と 5 を除いた残りが 1 (= 有限十進有理数)。
  `p3_b4_raw_record_producer.py:_fraction_token` の数値上の受理集合と一致する。
- 配置の択一 (R4): `_validate_attempt` だけに置く「registry admission 限定」か、
  段 2 案の 4 境界 (`_validate_attempt` / `_ratio_payload` / `_ratio_from_payload` /
  `_manifest_row_payload`) か。後者は manifest の wire 受理集合まで縮める。
  **どちらを採るかは実装 wave の裁定事項**であり、「registry only」と説明しながら
  4 境界を採ってはならない。
- **must-fix (R5)**: M12 を `_fraction_token` の直接検査へ再定義する。
  registry 拒否期待へ単純に移すと producer の丸め禁止分岐が無検査になる (規律 2)。
- 適格性述語 `_attempt_is_eligible` と `generate_analysis_manifest` には置かない (F5)。
- `as_b4_exact_fraction` (`p3_b4_analysis_contract.py:233`) には置かない。
  adapter/contract 共有の単一変換権威であり、狭めると §5.1.1 の
  `reference_value_domain_error` の意味までずれる。
- 文書 §5.1.1 は変えない。純関数契約は「有限の正の exact rational」のままとし、
  有限十進制約は実走前 registry admission の別層として記録する。
  段 2 と段 3 luna がともにこの切り分けを支持した。
- 正例 `(1, 10)`、負例 `(1, 3)` (発火目的) と `(1, 30)` (境界)。
  `[1, 30]` は既約かつ canonical なので `not reduced` ではなく新検査が発火する。

## 6. 実装面の差分ゼロ

本 wave の成果物は docs (insight + spool fragment) のみ。`DW-S04` により変異 matrix は免除。
受入全走は免除せず親が実走する。
