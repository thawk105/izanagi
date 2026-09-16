# B-10 静的 backoff 右 tail — 本走は既に済んでいた。投入せず、本番 CLI で集団判定を再導出した

`authority: none` / `default_effect: no-state-change`

**種別:** 実測 + 記録 + 裁定パッケージ。**実装面 (D95 決定 2) の差分はゼロ。**

- 日付: 2026-09-16 (JST)
- wave: `dev-wave-b10-tail-formal-submit`、branch `worktree-dev-wave-b10-tail-formal-submit`
- 起点 local main: `9d52ef1459fdae5bc97050155b28fce0601d259f`
- 依頼: 「B-10 残件『静的 backoff 右 tail の本走』を Pegasus へ投入し、3 workload を 1 集団として
  判定まで出す。投入前に submission §1 の 5 条件を 1 つずつ実測で確かめ、満たさないものがあれば
  投入せず理由を insight へ書く」

## 0. この wave が主張すること・しないこと

**主張する。**

1. **依頼の前提は stale だった。本走は 2026-09-15 に既に完走し、集団判定まで出ている。** §1。
2. **submission §1 の 5 条件のうち、条件 2〜5 は本日の実測で成立している。条件 1 は今回実測していない**
   (投入しなかったため)。**「5 条件が不成立だから投入しない」のではない。** §2。
3. **09-15 の cohort を、本日の本番 CLI (submission §4 の argv) で再導出した。終了コード 0、
   3 成果物すべてが 09-15 の成果物と byte 単位で一致した。** §4。これは記録の引用ではなく、
   現行 producer を実際に通した実測である。
4. **2 本目の cohort は投入しなかった。** 理由は事前登録が禁じているからではなく、
   2 本目の地位 (再現か置換か) を結果より前に決める必要があり、その決定権が本 wave に無いからである。
   §5。
5. **段 3 の 2 レンズは結論が割れた。**片方は「投入せよ」、もう片方は「再投入せず既存 cohort の確認を
   完了させよ」だった。**割れた事実を消さずに記録する。** §5・§6。

**主張しない。**

- **09-15 の cohort が事前登録の全条項を満たすと、当時の実行まで遡って監査したとは言わない。**
  §4 が示すのは「現行の loader が今日そのデータを受理し、同じ judgement を出した」までである。
  当時のビルド・resume 操作・実行履歴の独立監査はしていない。§4 の限界節。
- **飽和が存在しないとは言わない。**言えるのは、登録した格子・反復数・判定式の下で
  表現可能域である 9999 マイクロ秒までに飽和を観測しなかったことである (事前登録 §4.5 の言い方の固定)。
- **性能を認証していない。** `performance_certified: false` のままである。
  ここにある性能値を根拠に variant を採用してはならない (絶対規律 2)。
- **B-10 を閉じたとは言わない。T-2647 も閉じていない。** どの図表・主張へ載せるかは未定のままである。
- **同一事前登録に対する再現 cohort を恒久的に禁じるとは言わない。** §7 でユーザー裁定へ返す。

## 1. 依頼の前提が stale だった

依頼は投入手順書 `docs/b10-backoff-static-tail-submission.md` を根拠に挙げている。同書 §5 は
「本走を実際に投入した実績は**本書の作成時点では**無い」と書く。この限定は書かれた 2026-09-14 時点に
ついて真であり、現在も歴史的記述として真である。**現在の状態を述べた文ではない。**

一次資料で済を照合した結果、次が判明した。

| 事項 | 値 |
|---|---|
| 投入・完走 | 2026-09-15 (JST) |
| group id | `b10-backoff-grid-20260915T061814Z-545445` |
| job (write-heavy / balanced / read-heavy) | `0:998865.nqsv` / `0:998866.nqsv` / `0:998867.nqsv` |
| 出力親 | `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/` |
| `completion.json` | 3 job root すべてに実在 (3/3) |
| 集団報告 | `.../group-report-20260915/` の stem `.json` / `.dat` / `-complete.json` |
| 集団 verdict | `not-observed-in-any-workload` |
| 記録元 | `docs/archive/worklog-phase3-0915-1512.md` の [T-2647]、`output/insights/2026-09-15/t2266-tail-band/README.md` |

**`docs/worklog.md` (現行) に `T-2500` / `t2500` は 1 件も無い。**現行 worklog に残っているのは
下流項目 [T-2647] だけであり、これは「判定を下流へ渡す」——つまり本走そのものではなく、
出た否定的結論をどの図表・主張へ載せるかという未決事項である。

## 2. submission §1 の 5 条件の実測

| # | 条件 | 本日の実測 | 結果 |
|---|---|---|---|
| 1 | repo root からの投入 | **実測していない**。投入操作を行わなかったため | 未実測 |
| 2 | 事前登録 commit が HEAD の祖先 | `git merge-base --is-ancestor cad6f46d8 HEAD` → rc=0 | 成立 |
| 3 | 作業ツリーの文書 bytes = blob | 双方 `8084be04dc1fc6a78b0fa1ac4a16986add796945d8c4ecace86ed2df4c44a45a` | 成立 |
| 4 | 探索走 campaign 実在 | 3 workload 分が実在 (§3 に一覧) | 成立 |
| 5 | 出力親が repo 外の絶対 path | `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal` は repo 外 | 成立 |

**条件 1 を「成立」と書かない。**投入しなかったので判定できない。過去の実績は
09-15 の走行が repo root から投入されたことで示されているが、それは本日の実測ではない。

条件 3 の一致は「09-15 が束縛した bytes と、本日の作業ツリーの bytes が同じ」を示す。
**「初版発効時から 1 bit も動いていない」ではない。**事実は逆で、文書は 1 度追記されている (§3)。

## 3. 事前登録の版と、探索走の版

### 3.1 文書は 2 版ある

| 版 | commit | bytes | 文書 SHA-256 |
|---|---|---:|---|
| 初版 | `9e97d27b85912c1ce93e9552c7f587bee0d0bb13` | 69,575 | `b9b1f88834a2312841ba6d24c8428febf6490e68cfe6537543462e6b02e6decc` |
| 追補込み (09-15 の束縛先) | `cad6f46d86ae4dc31edadfbdfad39c65ed73d70a` | 71,231 | `8084be04dc1fc6a78b0fa1ac4a16986add796945d8c4ecace86ed2df4c44a45a` |

差分は `git diff --stat` で 21 行の追加のみ、位置は末尾 (`@@ -1079,0 +1080,21 @@`) だけである。
本文行の書き換えは 0 行。したがって §5 の機械可読 spec の bytes は不変で、
spec SHA-256 は両版とも `08f5849b7a6b7a7bf98917922e0d06283e4d837d370fb9371fc6282e388e80ef` である。

**依頼の「v1・発効済み」という呼び方は commit を一意に指さない。**追補込みの文書も §0 で
「本書は v1 である」と名乗っているためである。09-15 が束縛したのは追補込みの `cad6f46d8` である。

### 3.2 追補は §0 の更新契約を満たしていない (real な所見)

事前登録 §0 は「発効後の変更は旧版を Git 履歴に残したまま新しい commit で行い、
**変更理由と変更時点を本節へ明記する**」と要求する。2026-09-10 の追補は末尾に置かれており、
§0 には 1 行も記載が無い。**これは文書自身の更新契約違反である。**

**ただし、これを失敗条件 §7-12 (commit・blob・spec の未記録／bytes 不一致) へ読み替えない。**
§7-12 が問うのは記録と bytes の一致であり、09-15 の 3 件の束縛記録はいずれも
追補込みの commit / blob / spec で一致している。§4.5 が `invalid` と定義するのは §7 への該当であって、
§0 の記載場所違反を自動的に §7 のどれかへ当てる規定は無い。**存在しない失敗条件を足さない。**

### 3.3 探索走は v1 だが、それは本走を無効にしない

本走が正しさ検査の mode を読む探索走 campaign は 3 本あり、いずれも slug が v1 である。

```
.../b10-backoff-grid-20260908T193601Z-2540578-write-heavy/campaigns/t2418-backoff-static-explore-v1-silo-write-heavy-sweep-c9cea61a
.../b10-backoff-grid-20260908T193601Z-2540578-balanced/campaigns/t2418-backoff-static-explore-v1-silo-balanced-sweep-783ccbe8
.../b10-backoff-grid-20260908T193601Z-2540578-read-heavy/campaigns/t2418-backoff-static-explore-v1-silo-read-heavy-sweep-a3c44399
```

(いずれも `/work/1/SFC/tanab/b10-backoff-grid-t2418-explore/` 配下。
`t2418-backoff-static-explore-v2` で始まる directory は `/work/1/SFC/tanab` 配下の深さ 4 までに 0 件。)

2026-09-10 追補は「**この変更後の `t2418-explore` 新走は**…v2 とする」「**新走の loader** は v2 の
campaign を選び、v1 への fallback は設けない」と書く。**主語は T-2418 の新しい探索走とその loader で
あって、本走 driver ではない。**本走 driver の `load_explore_correctness_mode` は、明示的に渡された
campaign を歴史的 raw として読み、`run_kind == t2418-explore` と mode の一意性だけを確認する。
**したがって「探索走が v1 だから 09-15 の cohort は §7-18 に当たる」という攻撃は成立しない。**
これは段 3 のレンズ B が独立に到達した結論でもある (§6)。

加えて実測として、**3 本の探索走 campaign はいずれも mode が `legacy` で一致する** (WAL の
`workload.tag` を直接読んだ)。したがって、どれを渡すかは mode 比較の結果を変えない。

### 3.4 投入時の explore campaign の argv は保存されていなかった

09-15 の job 成果物 (`completion.json`、campaign lock、execution report、`qstat-f.stdout`、`env/`) の
どれにも `B10_EXPLORE_CAMPAIGN` の値は残っていない。**どの探索走 campaign を渡したかは、
保存された成果物からは特定できない。**§3.3 の mode 一致により本件の判定は変わらないが、
「保存されていない」という事実自体は記録しておく。

## 4. 本番 CLI による集団判定の再導出 — 3 成果物が byte 一致した

依頼の「3 workload を 1 集団として判定まで出す」を、新しい測定を作らずに果たすため、
submission §4 の argv をそのまま使って **09-15 の 3 campaign から集団判定を本日再導出した**。

```
python3.10 -I -B orchestrator/campaign/b10_backoff_static_tail_formal.py \
  --preregistration-commit cad6f46d86ae4dc31edadfbdfad39c65ed73d70a \
  report <write-heavy campaign> <balanced campaign> <read-heavy campaign> \
  --explore-campaign <t2418 explore v1 balanced campaign> \
  --output-root /work/1/SFC/tanab/b10-tail-formal-recheck-20260916
```

渡した 3 campaign は 09-15 の各 job の `completion.json` が `campaign_id` として記録している実体である。

- `t2500-backoff-static-tail-formal-silo-write-heavy-sweep-9cda88f0`
- `t2500-backoff-static-tail-formal-silo-balanced-sweep-1c8d08f7`
- `t2500-backoff-static-tail-formal-silo-read-heavy-sweep-9064a9e0`

**結果: 終了コード 0、標準出力・標準エラーともに空。**submission §4 は「判定が invalid のときも
報告は作られ、終了コードは 1 になる」と定めているので、**rc=0 は invalid でないことを意味する。**

生成された 3 成果物の SHA-256 は、2026-09-15 の成果物と**すべて一致した**。

| 成果物 | SHA-256 | 09-15 と一致 |
|---|---|---|
| `t2500-backoff-static-tail-formal.json` | `5f426ecbc16132048cf0c73eaf6960a395ec821a9f48cc04a83a787dceec8b28` | 一致 |
| `t2500-backoff-static-tail-formal.dat` | `758b3121cebf7562315a8a70d1f305ced678f90b393fc3cd2a4af87ca0c71c44` | 一致 |
| `t2500-backoff-static-tail-formal-complete.json` | `7192d1da0b4a032251a0e270ec60910a118a5f75844dc9276a6fba00a682d08c` | 一致 |

再導出した report の中身 (本日の実測):

- `verdict` = `not-observed-in-any-workload`
- `failures` = `[]` (空)
- `performance_certified` = `false`
- 3 workload すべて `state` = `not-observed`、各 6 区間・計 18 区間すべてが `declining`、
  局所平坦区間は 0

job の所要時間 (各 campaign の execution report の記録値):

| workload | `sweep_elapsed_s` (上限 11700) | `job_elapsed_s` (上限 18000) |
|---|---:|---:|
| write-heavy | 823.31 | 836.44 |
| balanced | 820.90 | 833.08 |
| read-heavy | 825.31 | 837.47 |

**この再導出が示さないもの。** 現行の loader が今日そのデータを受理したことは示すが、
当時の実行そのもの (ビルド、resume 操作、失敗 attempt の履歴) を独立に監査したことにはならない。
`job_elapsed_s` は driver が実行 receipt を書く直前の値であり、job script のその後の後始末・
成果物 hash 化・root の `completion.json` 作成を含まない。**job の最終終了時刻までは証明しない。**

## 5. なぜ 2 本目の cohort を投入しなかったか

### 5.1 投入しなかった理由 (裁定)

**(a) 依頼の成果物は既に存在し、再投入は同じ成果物をもう 1 つ作る。** 依頼が求めた
「3 workload を 1 集団とした判定」は §1 のとおり存在し、§4 で本日再導出して一致を確かめた。

**(b) 2 本目を正しく走らせるには、結果を見る前に 2 本目の地位を決める必要がある。**
事前登録は 1 つの cohort についての測定規則・判定規則を固定するが、**複数 cohort の合成規則も
選択規則も 1 行も持たない** (§4.5 の結末表と §7 の失敗条件を全文確認した)。したがって
「1 本目を権威として保持し 2 本目を再現として併記する」のか「2 本目で置き換える」のかは、
事前登録の外で新たに決めることになる。**これを結果が出てから決めるのは、正しさシグナルの
後付け (絶対規律 3) と同じ形になる。**

**(c) その決定権は本 wave に無い。** 依頼は「判定式・閾値・格子は事前登録が持つので本 wave で
決めない」と明示している。2 本目の地位の決定は、まさにこの類の決定である。

### 5.2 取り下げた根拠 — 段 3 のレンズ A が親の裁定理由を 3 つ壊した

親が段 1 brief に書いた (P1) の理由づけのうち、次の 3 つは**誤りとして取り下げる。**

1. **「§8.2 が『初回の本格投入時に』と書いているので、区別された初回が消費された」は成立しない。**
   同項は束縛を記録する時点の要求であって、2 度目の投入を禁じる条項ではない。
2. **「規律 2 が想定する最適化圧力の型と同じ」という援用は射程の拡大である。**
   絶対規律 2 の対象は anomaly を出した variant の即 reject と、検証を甘くする変異の不採用であり、
   正しさ検査を維持したまま別 cohort を足すことは、それ自体ではこの禁止に当たらない。
3. **規律 7 を「取り直す根拠が無い」の根拠に使ったのは誤りである。** 同規律は逆に
   「新しい測定はいつでも開始できる。開始条件に、過去の承認済み状態とのコード同一性を置かない」と
   明記している。規律 7 は初回をコード差だけで無効化しないことを支えるが、
   「初回が有効だから次を始めない」は支えない。

**したがって「事前登録が 2 本目を禁じている」とは書かない。禁じていない。**
投入しなかった理由は §5.1 の (a)(b)(c) だけである。

### 5.3 2 レンズは割れた — その事実を消さない

| レンズ | 結論 |
|---|---|
| A (事前登録の効力) | **「P1 は採らざるべき。既存 cohort の完走だけでは不投入は導けない」** — 追加 cohort を独立な再現走行として投入せよ |
| B (「済」の中身を疑う) | **「現時点では再投入せず、既存 cohort の確認を完了させる」** — ただし現証拠だけで valid と確定してもならない |

親は B 寄りに裁定したが、**A の中核の指摘 (事前登録は 2 本目を禁じていない) は real として採用し、
§5.2 で自分の根拠を取り下げた。** A が挙げた「再現走行を成立させる 4 条件」は §7 でユーザーへ返す。
B が求めた「現証拠だけで valid と確定するな」は §4 の再導出で実測に置き換えた。

逐語は `verbatim/stage3-consult-a.md`、`verbatim/stage3-consult-b.md`、`verbatim/stage2-plan.md`。

## 6. 子が訂正させた親の誤り

段 2 の plan と段 3 の 2 レンズが、親 brief の次を訂正させた。すべて本 insight 本文へ反映済み。

1. insight の配置が規約と不一致だった (`output/README.md` の日付 directory 規約)。
2. submission §5 の「作成時点では無い」を「現在は偽」と書いたのは誤読。限定付きの歴史記述である。
3. 「§8.2 の初回」から投入禁止を導いたのは誤り (§5.2)。
4. 「5 条件はどれも不成立ではない」を成立確認と同義に扱った。条件 1 は未実測である (§2)。
5. 「当時から 1 bit も動いていない」は過剰。示されたのは 09-15 の束縛 bytes と本日の bytes の
   同一性だけで、中間履歴の不変ではない。実際には 1 度追記されている (§3.1)。
6. 探索走の日付を「2026-09-08 完走」と書いたが、directory 名の `20260908T193601Z` は UTC であり
   JST では 2026-09-09 04:36:01、しかもそれは投入側の刻印であって完了時刻ではない。
7. 「§7 の失敗条件に 1 つも当たっていない」は当初の確認範囲を超えていた。§4 の再導出 (rc=0、
   `failures` 空) で初めて実測に置き換わった。

## 7. ユーザー裁定へ返すもの

**同一事前登録に対する再現 cohort を走らせるか。** 段 3 のレンズ A は、走らせてよいし
そのほうが望ましいと論じた。事前登録は禁じていない。走らせる場合、レンズ A が挙げた条件は次である。

1. 投入前提 (submission §1、事前登録 §8.1、環境・較正・correctness) を新走について改めて満たす。
2. **結果を見る前に**扱いを明記する — 初回結果を既知とした再現走行であり、初回を置換・合成せず、
   結果にかかわらず 1 本を報告する。
3. cohort を混ぜない。新しい identity・別の報告先で、登録済みの全格子と反復を実行する。
4. 主張の範囲を増やさない。両 cohort の判定を併記し、またぐ単一の有意水準保証や新しい統合 verdict を
   主張しない。不一致・invalid も開示し、性能未認証を維持する。

**親はこれを実装しなかった。**2 の「扱いを結果より前に明記する」が新しい方法論上の決定であり、
依頼が本 wave から明示的に外した領域だからである。

## 8. 本 wave が閉じないもの

- **[T-2647]。** 09-15 の否定的結論をどの図表・主張へ載せるかは未定のままである。
- **性能の認証。** `performance_certified: false` は動いていない。
- **当時の実行の独立監査。** §4 の限界節のとおり。
- **§0 の更新契約違反 (§3.2) の後始末。** 本 wave は事前登録本文を 1 bit も変更していない。
  結果が出た後の文書修正で遡及的に解消することはできない (事前登録 §0 自身が
  「結果 commit より後に書かれた変更は事前登録として数えない」と定める)。
