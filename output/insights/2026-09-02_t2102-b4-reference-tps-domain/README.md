# [T-2102] B-4 `reference_tps` の実値域 — D1344 の実測

D1344 が求めた実測を行い、非有限十進の `reference_tps` を registry で禁止するか
凍結済み consumer を改訂するかの択一に、証拠を当てた記録である。

- wave: `worktree-dev-wave-t2102-b4-reference-tps-range`
- 基準 commit: `28ebff456b9f57a927854950b5030fa77aec6529`
- 実測日: 2026-09-02 (JST)
- 実装面の差分: なし。本 wave は実測と択一の裁定までを成果物とする。

## 問い

`reference_tps` は、事前登録 §5.1.1 で「その block の precursor から祖先方向へ辿って最初に
現れる certified snapshot の session-level throughput」と定義される。
凍結された raw-record producer は、この値を canonical JSON の十進 token として出力する。
既約分母に 2 と 5 以外の素因数が残る有理数は有限十進で書けないため、producer は
`reference_tps has no finite decimal expansion` で構造化拒否する。

D1344 の択一は次である。**(a)** registry の受理値域を狭めて非有限十進を封印前に禁じるか、
**(b)** 凍結された消費側を改訂して exact ratio を受け取れるようにするか。
丸めて受理する案は、受理集合を広げ凍結側が受け取る値を元の値と別物にするため、
絶対規律 2 に反するとして D1344 が却下済みである。

## 母集合を 2 通りに取って測った

「予定されている scheduled input すべての `reference_tps`」という指定は 2 通りに読める。
どちらでも測った。

### 読み A — 封印済み registry の `reference_tps` を文字どおり列挙する

wire 形 `[分子, 分母]` のまま `Fraction` にし、既約分母から 2 と 5 を除いて残りが 1 かを見る。
**十進にも float にも変換しない**ので、この判定は恒真ではない。

走査範囲はこの user が読める data filesystem 全域。結果は `measurement-4.json`。

| 項目 | 値 |
|---|---|
| 封印済み成果物 | 10 件 |
| `reference_tps` の値 | 2,010 件 |
| 相異なり | 201 種 (すべて `(N, 10)` の形) |
| **非有限十進** | **0 件** |
| null / 比でない値 | 0 件 / 0 件 |
| 走査できなかった dir | 21 件 (すべて他ユーザー・他セッションの private dir。全件を path 付きで記録) |

**10 件はすべて pytest fixture である。production 由来の封印済み registry は 0 件だった。**
したがって読み A の production 母集合は空であり、その空集合を「0 件」の根拠には数えない。

空である理由は「まだ作っていない」ではない。**`B4ScheduledAttemptInput` を祖先 certified
snapshot から構成する producer が repo に存在しない**ためである。registry の直接の入力は
caller が渡す値であり、issuer 自身が「caller schedule は外部の authoritative population に
束縛されない」と明記する。非 test の構築点は、事前登録 consumer の自己検査用 fixture だけである。

### 読み B — `reference_tps` が指す量の production 値域を列挙する

certified snapshot の session-level throughput が実際に取る値を全件数えた。
この量の記録は campaign WAL の終端 `commit` record にしか存在しない。

| 実測 | 走査範囲 | 観測数 | 非有限十進 |
|---|---|---|---|
| 1 (`measurement-1.json`) | repo 内 2 root、WAL 60 file | 5,928 | 0 |
| 2 (`measurement-2.json`) | campaign 成果物の key 名に `tps`/`throughput` を含む**全 field** | 4,034 | 0 |
| 3 (`measurement-3.json`) | この user の `/work` 全体、WAL 5,541 発見 / 5,537 走査 | 443,911 | 0 |
| 5 (`measurement-5.json`) | `/home` と `/dev/shm` | 0 (WAL 2 file、throughput 欄なし) | 0 |

実測 3 の内訳は `commit.fitness_tps` 66,119 観測 (相異なり 615)、
`bench.median_tps` 62,691 観測 (相異なり 584)、`bench.tps[]` 系列 315,101 観測
(相異なり 2,841)。3 つの母集合は重なるので相異なり数は足さない。

実測 3 は repo 外の official output root を含む。読めなかった WAL 4 件と JSON 行の
parse 失敗 22 件は件数と path を記録した。4 件はいずれも「切り詰めた WAL を拒否する」ことを
試す pytest fixture であり campaign 成果物ではない。

実測 2 が拾った key 名は `tps` / `median_tps` / `throughput_tps` / `fitness_tps` /
`session_throughputs` / `throughputs` / `baseline_tps` の 7 種である。
key を指定せずに拾っているので、実測 1 の上位集合になる。

## 恒真性 — この数え方が自明でない理由

段 3 の敵対検証は「JSON の十進 token も IEEE-754 の float も定義上必ず有限十進なので、
その表現を測る限り結果は恒真だ」と指摘した。**この指摘は数学的に正しい。**
読み B の判定は、その表現の上では恒真である。恒真な検査を exact 値域の非自明な証明と
呼んではならない。

しかし批判の**含意** — 「恒真なゼロの背後に、丸められた正当な非有限 exact 比が隠れている
かもしれない」 — は成立しない。隠れるためには丸める前の exact 値が存在するか、
材料から再構成できる必要がある。どちらも無い。

- **上流に有理数演算が無い。** CCBench 出力の解析器 `orchestrator/calibrator/benchparse.py` の
  `throughput_tps()` は `float` を返し、代替経路の `commits / extime` も float 同士の除算である。
  中央値も float 演算。campaign の非 test コードで `Fraction` を使うのは B-4 分析系、
  A-1 headline、s8b floor、b10 sweep だけで、throughput を作る側には無い。
- **高精度版の材料が記録に無い。** `benchparse.py` が高精度版として名指しする
  `commit_counts_` と `actual_extime` は、campaign 成果物の全域で**それぞれ 0 件**である
  (完全走査)。WAL の commit payload は `fitness_tps` / `cv` / `high_variance` / `unstable` の
  4 key だけ。`pipeline.py` は `commit_counts_` を stdout から witness counter として読むが
  WAL へは載せない。

したがってこの量は float として**生まれて**おり、丸められた exact 前身は存在しない。
exact 比としての読み替えは、遡っても再構成できない。
根拠として書くべきは「恒真な検査の 0 件」ではなく、**exact 前身が記録に不在であること**である。

読み A の判定は表現の上でも恒真でない (wire 形の exact 比をそのまま見ている) ので、
この批判の射程外である。

## 裁定

- **(b) を支持する production 証拠は 0 件である。** 正当な非有限十進の upstream 出力は
  実在せず、記録されておらず、再構成もできない。凍結された消費側を改訂して
  「何も生産しない値」を exact に運べるようにするのは、空集合のために凍結費用を払うことになる。
- **証拠の向きは (a) で一貫している。** 段 2 の plan 子、段 3 の 2 レンズ、段 3b の再検証子の
  4 子すべてが (a) 側で一致し、(b) を支持する証拠を 1 つも挙げなかった。
- **ただし D1344 が文面で求めた読み A の production 母集合は空である。** 空である理由は
  上流を束縛する producer の不在であり、これは D1344 の裁定時に見えていなかった事実である。
  よって狭める実装へ進むかはユーザー裁定に返す。詳細と択一 α / β は
  `verbatim/s4-ruling.md` の §4 にある。

**どちらの場合も (b) は採らない。丸め受理も採らない。**

## 実装 wave への申し送り (本 wave では実装しない)

`verbatim/s4-ruling.md` §5 が正本。要点だけ再掲する。

- 述語は「既約分母から 2 と 5 を除いた残りが 1」。
  `p3_b4_raw_record_producer.py` の `_fraction_token` の数値上の受理集合と一致する。
- 配置は「registry admission 限定 (`_validate_attempt` だけ)」か
  「段 2 案の 4 境界」かの択一である。後者は registry だけでなく manifest の wire 受理集合まで
  縮める。**「registry only」と説明しながら 4 境界を採ってはならない。**
- **must-fix**: 既存の変異検査 M12 は、registry で先に拒否すると producer の
  `_fraction_token` へ到達しなくなる。registry 拒否期待へ単純に移設すると、
  producer の丸め禁止分岐を一切検査しない**恒真な保証**になる。
  M12 は `_fraction_token` の直接検査へ再定義して producer 側の防壁を維持する。
  これは絶対規律 2 に直接触れる。
- 適格性述語と manifest 生成へは置かない。`generate_analysis_manifest()` は先頭で
  `assert_scheduled_registry_complete()` を呼び `_validate_attempt` を通すため、
  非有限十進は先頭 201 件の選抜より前に落ちる。
- `p3_b4_analysis_contract.py` の `as_b4_exact_fraction` には置かない。
  adapter と contract が共有する単一変換権威であり、狭めると §5.1.1 の
  `reference_value_domain_error` の意味までずれる。
- 事前登録文書 §5.1.1 は変えない。純関数契約は「有限の正の exact rational」のままとし、
  有限十進制約は実走前 registry admission の別層として記録する。

## 凍結 closure について

狭める対象の `orchestrator/campaign/p3_b4_analysis_ledgers.py` は、凍結された 5-file
analysis source closure の member である。よって狭める側も closure identity を動かす。
ただし closure member の bytes を固定値で pin する成果物・docs・test は 0 件で、
receipt は live bytes から生成される。固定されているのは事前登録 §5.1.1 の section hash で
あって ledger bytes の hash ではない。更新すべき既存 pin は無い。

## 限界

- `orchestrator/campaign/layout.py` は official output root を任意の絶対 path に許すため、
  走査は原理的に閉じない。閉じたのはこの user が読める data filesystem の全域であり、
  「マシンのどこにも無い」とは書けない。
- 読み A の production 母集合が空である以上、production の scheduled input を実際に測った
  ことにはならない。測ったのは読み B の値域と、実在する fixture registry である。
- 段 2・段 3・段 3b の子はいずれも読み取り専用の静的検査だけを行い、
  pytest を実走していない。子の非実走を緑と数えていない。
  親が実走した受入の結果は worklog エントリに書く。

## 一次資料

- `measurement-1.json` / `measurement-2.json` / `measurement-3.json` /
  `measurement-4.json` / `measurement-5.json` — 実測の生結果。
  実測 1 と 3 は非数値 record の逐一列挙と token 見本を件数へ畳んである
  (`_trimmed` 欄に明記)。非有限十進の欄は 0 件なので畳んでいない。全文と実測手順の
  script は dev-wave job dir `2026-09-02_t2102-b4-reference-tps-range` に残る。
- `verbatim/s1-brief.md` — 親の段 1 brief。
- `verbatim/s2-plan.md` — 段 2 の plan。母集合の反論と 4 境界案。
- `verbatim/s3-sol.md` — 段 3 レンズ 1。実測そのものを疑う。
- `verbatim/s3-luna.md` — 段 3 レンズ 2。裁定と帰結を疑う。
- `verbatim/measurement-addendum.md` — 段 3 の後に親が取った追加実測 A〜D。
- `verbatim/s3b-recheck.md` — 追加実測を渡した再検証。
- `verbatim/s4-ruling.md` — 段 4 裁定。real / refuted と択一 α / β。
- `verbatim/ERRATUM.md` — 子 4 file の行末空白を可逆に正規化した記録。
  原文 sha256 と byte 数、復元法。可視文字は不変。
