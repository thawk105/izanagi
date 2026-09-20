## 所見 (R-1 …)

**結論：must-fix 1 件、should 4 件、nit 1 件、記録 1 件。** 二語を分ける中心命題は正しいですが、root の pin を全解決経路へ広げた記述は実装と一致しません。静的検査のみ実施し、ファイル変更・pytest・job 投入は行っていません。

**R-1 / 対象：`docs/pegasus-runbook.md:1757`、§7.9 語 A の exploration root / 主張：process pin の適用範囲が広すぎる。**

- **根拠：** `orchestrator/campaign/layout.py:380` は `Only the environment path is canonicalized and admitted, then pinned`。383–384 行は明示引数をそのまま返し、391–396 行は env 未設定・pin 無しなら repo 既定を返す。pin を設定するのは env 経路の409–413 行だけ。
- **放置時の影響：** 読み手が、明示引数や repo 既定で最初に解決した root も process 全体で固定されると誤認する。
- **分類：must-fix**
- **是正案：**
  - 置換前：`> repo 既定 (`output/`) の順で解決し、process 内で最初の解決値に pin される`
  - 置換後：`> repo 既定 (`output/`) の順で解決する。env 経路で解決した値は process 内に pin され、以後その経路では env の変更・削除を拒否する。明示引数と repo 既定はこの pin の対象ではない`

**R-2 / 対象：`docs/pegasus-runbook.md:1794`、対応表「環境変数」語 A cell / 主張：「exploration だけ base を差し替えられる」は限定先が曖昧。**

- **根拠：** `layout.py:417` 以下は official にも明示引数と `IZANAGI_OFFICIAL_OUTPUT_ROOT` の解決経路を持つ。`resolve_campaign_output_root` の459–462 行は use class ごとに別 resolver を選ぶ。新節自身も1755行で official の env を説明している。
- **放置時の影響：** この env が exploration 専用という意味では正しいが、base の指定・変更機構が exploration にしかないという意味にも読め、表と本文が矛盾する。
- **分類：should**
- **是正案：**
  - 置換前：`IZANAGI_EXPLORATION_OUTPUT_ROOT` `(exploration だけ base を差し替えられる)`
  - 置換後：`IZANAGI_EXPLORATION_OUTPUT_ROOT` `(この env は exploration の base 解決に使い、official の base 解決には使わない)`

参照元 `docs/orchestrator-design.md:115` に同様の表現がありますが、現行コードの説明に転記するときは限定が必要です。

**R-3 / 対象：`docs/pegasus-runbook.md:1768`、語 A の docstring 説明；`adjudication.md:9` / 主張：二つの docstring の観察から code 全体へ一般化している。**

- **根拠：** `layout.py:547` の「探索専用 layout」と597行の「探索 layout」は語 A。一方、`b10_backoff_static_tail_formal.py:354` の `mode source must be exploration` は `run_kind == "t2418-explore"` の検査で、語 B。新節1787行も後者を明記している。
- **放置時の影響：** code 内の exploration／探索を一律に語 A と読む規則ができ、今回区別したい B-10 の語 B を再び誤分類する。
- **分類：should**
- **是正案：**
  - runbook 置換前：`**code 中の「探索」はこの語 A である。**`
  - 置換後：`**この 2 つの docstring 中の「探索」は語 A である。**`
  - adjudication 置換前：`code 中の「探索」は語 A。`
  - 置換後：`この docstring 中の「探索」は語 A。`

**R-4 / 対象：`docs/pegasus-runbook.md:1796`、対応表「直交性」両 cell / 主張：分類軸の違いを、値の双方向の非含意まで広げている。**

- **根拠：** D1848 却下肢3は「探索走を exploration output root へ移す」を却下。現行 `backoff_extended_sweep.py:644` と648行は同じ `search_config` に `t2418-explore` と `official` を置き、1461行でも `official` を渡す。対象を D1813 の現行探索走に限定すれば、語 B に対応する語 A の値は明確に `official`。
- **放置時の影響：** 「異なる分類軸」と「現行実装の対応関係も存在しない」が混同され、表の実例行と直交性行が食い違う。
- **分類：should**
- **是正案：**
  - 置換前：`| 直交性 | 語 A の値は語 B を含意しない | 語 B の値は語 A を含意しない |`
  - 置換後：`| 読み違えない点 | use class の宣言だけでは正式標本への帰属は決まらない | D1813 の探索走を exploration use class と読み替えない。現行実装の宣言は official |`

**R-5 / 対象：`docs/glossary.md:177`、新項目の namespace と語 B の定義 / 主張：省略によって既定 path と対象測定の限定が落ちている。**

- **根拠：** `layout.py:599`–601行の形は `<base>/exploration/campaigns/<id>/`。`output/` は base の既定値である。D1813 は「静的 backoff」の右側の測定を2段にする裁定であり、任意の2段測定の第1段を定義してはいない。
- **放置時の影響：** glossary 単独の読み手が namespace を repo 内の固定出力先と捉え、他の2段測定まで `t2418-explore` の説明を適用しうる。
- **分類：should**
- **是正案：**
  - 置換前：`campaign root の namespace (`output/exploration/campaigns/<id>/`)`
  - 置換後：`campaign root の namespace (`<base>/exploration/campaigns/<id>/`、base の既定は `output/`)`
  - 置換前：`D1813 の**探索** — 測定を 2 段で行うときの第 1 段。`
  - 置換後：`D1813 の**探索** — 静的 backoff の 1000 マイクロ秒超を測る 2 段構成の第 1 段。`

これは機体固有値の混入ではありません。一般化された path 自体は掲載可能です。

**R-6 / 対象：`brief.md:17`、一次資料の root 説明 / 主張：resolver が返す base と namespace 付加後の path を取り違えている。**

- **根拠：** `layout.py:396` は `repo_output_root()` を返し、同関数48行は `output` を返す。`exploration` の付加は601行。
- **放置時の影響：** 親資料を再利用した際に base に `exploration` を二重付加する説明へ戻りうる。今回の runbook 本文1758行では既に正しく `output/` と書けている。
- **分類：nit**
- **是正案：**
  - 置換前：`(省略時 repo 既定 `output/exploration/`)`
  - 置換後：`(明示引数・env とも省略時の base は repo 既定 `output/`。layout がその下に `exploration/campaigns/<id>/` を付ける)`

**R-7 / 対象：`brief.md:33`、条件表再評価の根拠 / 主張：限定的 grep から「構造 lint のみ」「束縛なし」を全称で断定している。**

- **根拠：** `projection/parent-measurements.md` が示す検索は `pegasus-runbook` を限られた Python glob で探すものと、`exploration campaign / 8c` の完全な文字列を探すもの。glossary の全参照、間接参照、文字列を持たない検査まで不存在とする根拠ではない。
- **放置時の影響：** 今回の docs-only 差分の判断とは別に、不完全な探索結果が文書全体の非拘束性を証明した記録として残る。
- **分類：記録**
- **是正案：**
  - 置換前：`runbook / glossary は check_docs の構造 lint のみ、凍結 chain・hooks に束縛なし、実測 grep`
  - 置換後：`射影された grep の範囲では runbook 参照として check_docs が検出され、該当 checklist 文言の一致は 0 件。glossary を含む全参照・間接束縛の不存在までは確認していない。提示差分は runbook / glossary の説明文追加だけである`

追加の gate や全域監査を要求する所見ではなく、証拠の射程を記録に合わせる指摘です。

## 逐語照合の対照表 (命題 / 新節・glossary の文 / 一次資料の逐語 / 一致・不一致)

以下のコードファイル名は `orchestrator/campaign/` 配下、job／submit script は `tools/pegasus/` 配下です。D番号は指定された射影の原文を指します。

| 命題 | 新節・glossary の文 | 一次資料の逐語・位置 | 一致・不一致 |
|---|---|---|---|
| 冒頭の目的・非変更範囲 | §7.9「語の整理だけ」「受理集合…には触れない」 | D1879「…別語である件の整理だけ」「working bytes 拘束…と…必須化は採らない」 | 一致。提示patchも文書2 fileのみ |
| 語 A の意味 | 「宣言する『利用意図』」 | D528 決定4「宣言は利用意図」 | 一致 |
| 閉表4値 | `official / exploration / qualification / dry` | D528 決定1に同じ4値 | 一致 |
| materialize 2値 | 「前2値だけ」 | D528 決定6「campaign sink が materialize できるのは `official` と `exploration` だけ」 | 一致 |
| 標本帰属とは別 | 「正式標本に入るかどうかは決まらない」 | D1848 理由5「標本への帰属…と…use class…で別物」、D528 決定8「宣言は権威ではない」 | 一致 |
| official の形 | `<base>/campaigns/<id>/` | `layout.py:256`：`os.path.join(root, "campaigns", cid)` | 一致 |
| official の base | 明示引数か official env、repo fallback 無し | `layout.py:419` 明示引数分岐、427行 env 取得、434行以下「official output_root は明示必須」 | 一致 |
| exploration の形 | `<base>/exploration/campaigns/<id>/` | `layout.py:601`：`os.path.join(root, "exploration", "campaigns", cid)` | 一致 |
| exploration の優先順位 | 明示引数 > env > `output/` | `layout.py:383`、389、396、48行 | 一致。明示引数は非空の場合 |
| process pin | 「最初の解決値に pin」 | `layout.py:380`–381：`Only the environment path ... pinned` | **不一致：R-1** |
| namespace marker | official consumer が拒否する側 | D123 決定5「official report は…exploration なら拒否」「marker が無い root は受理」；設計文書113行 | 一致。全経路の拒否保証とは読まない |
| 外部 exploration root | hooks 防護外、certified／proof-chain 材料を置かない | D158「外部 root は repo hooks…防護の外…certified 材料・proof chain 素材を置かない」 | 一致。既存規律の再掲 |
| 宣言の場所 | module 定数と `run_campaign` 引数 | D528 決定5・7。決定9は8cが直接 layout を呼ぶ例外を明示 | 概要として一致。全 producer が両方を通る意味ではない |
| exploration producer 7 module | s4 5 + 8c + A-1 | 定数位置：`p3_s4_loop.py:116`、`p3_s4_loop_sort.py:104`、`p3_s4_loop_trigger_gating.py:102`、`p3_s4_red.py:66`、`p3_kickoff.py:49`、`p3_autonomous_workload_trial.py:141`、`paper_story_a1_paired.py:97` | 一致。今回の top-level AST 走査でも7件 |
| D123 の6 driverにA-1なし | A-1の直後の括弧 | D123 決定2はs4 5 moduleと8cを列挙 | 一致 |
| backoff 4 producer が official | 列挙された4 module | `backoff_sweep.py:491`、`backoff_extended_sweep.py:1461`、`b10_backoff_shape_sweep.py:4485`、`b10_backoff_static_tail_formal.py:761` に `declared_use_class="official"` | 静的な呼出し記述として一致 |
| layout 名・docstring | 2 symbolと「探索専用 layout」「探索 layout」 | `layout.py:546`–547、594–597 | 一致 |
| code全体の語義 | 「code 中の『探索』は…語 A」 | 上記docstringと formal driver354行では対象軸が異なる | **過剰一般化：R-3** |
| 語 B の定義 | 静的 backoff 1000µs超の第1段 | D1813表題・決定「右側の測定は2段」「第1段は探索」 | 一致 |
| 開示・事前登録 | 正式標本へ混ぜず、格子・停止基準を開示／前向き登録 | D1813「探索値は正式標本へ混ぜず…開示」「探索結果を見た後・本格 cohort の投入前に事前登録して凍結」 | 一致。凍結の省略は否定・緩和ではない |
| 第3の RUN_KIND | extended sweep の `t2418-explore` | `backoff_extended_sweep.py:81`–84 の3値 tuple、D1848決定 | 一致。job 全体には別 module の第4種別もある |
| 成果物3か所 | search_config／JSON／dat provenance の同値5 field | 同file644–648、1165–1169、1272–1276。claim scope literalは96行 | 一致 |
| 探索走は official | 宣言・export・rootを移さない | 同file1461行、`b10_backoff_grid.sh:578`、D1848却下肢3、T-2418 insight75–87行 | 一致 |
| 第2段の所在 | preregistration、別formal module、`t2500-tail-formal` | `docs/b10-backoff-static-tail-submission.md:3`–8に同じ文書・module・種別 | 一致。投入済みとは主張していない |
| flag受理条件 | `--explore-campaign` は formal限定、絶対path | submit script60–82行：formalで必須、他種別で拒否、66行から絶対・実在directory検査 | 一致 |
| flagが指す対象 | 語 B の探索campaign | submission文書23–24行、formal driver354行 `run_kind == "t2418-explore"` | 一致。submitter単独がrun kindを検証するという意味ではない |
| campaign directory の形 | `<output parent>/<group>-<workload>/campaigns/<id>/` | submit script236–239行で root と `B10_OUTPUT_ROOT`、job258行で受領、layout256行で suffix付加 | 一致。標準submit経路で生成される形であり、flagの文字列形式検査そのものではない |
| modeの用途 | mode比較、探索数値を本走判定に入れない | formal driver351–358行はverify記録の `workload.tag` を返す。734行と800–801行で使用。submission文書24行も明記 | 一致。sourceのadmission等を省略する意味ではない |
| 検査文言 | `mode source must be exploration` は run kind要求 | formal driver354行の比較式と文字列 | 一致 |
| 表：分類対象 A | 出力先・namespace・durable root policy | D528決定4、layout459–462行、D1848却下肢3 | 一致。宣言自体をdurability保証とはしていない |
| 表：分類対象 B | 第1段は正式標本に入らず開示 | D1813「探索値は正式標本へ混ぜず…開示」 | 一致 |
| 表：宣言場所 A | 定数／run_campaign引数 | D528決定5・7・9 | 一致。8c直接呼出しの境界は上記のとおり |
| 表：宣言場所 B | `--run-kind`、4成果物field | submit script26–29行、job615行、extended sweep644–647行ほか | 一致 |
| 表：env A | explorationだけbase変更 | layout417–452行はofficial側の指定機構も持つ | **限定が曖昧：R-2** |
| 表：env B | 「無し。…official envをexport」 | 語 B はrun kind／fieldで表現。job578行はofficial env | 一致。「語 B を指定する専用envは無し」の意味 |
| 表：実例 A | A-1はexploration、jobがenv export | `paper_story_a1_paired.py:97`、7312、7559行；job831行 | 一致。正式標本か否かは未判定 |
| 表：実例 B | t2418はofficialの探索走 | extended sweep644–648行、1461行 | 一致 |
| 表：直交性 A/B | 双方向とも非含意 | D1848と現行コードは具体的対応 `t2418-explore → official` を持つ | **過剰一般化：R-4** |
| 読み分け段落 | 語 A／Bの表記群、探索走＝official×探索 | 上記layout・driver・D1813／D1848 | 本件の文脈では一致 |
| glossary：一般定義・閉表 | 未知候補を試す／利用意図の4値 | 一般説明とD528決定1・4 | 一致 |
| glossary：namespace | `output/exploration/campaigns/<id>/` | layout599–601行はbase可変 | **既定の限定不足：R-5** |
| glossary：語 B | 「測定を2段で行うときの第1段」 | D1813は静的backoff右側の測定に限定 | **対象の限定不足：R-5** |
| glossary：帰属と実装 | 混ぜず開示、t2418、official、A-1帰属は別 | D1813、D1848、extended sweep644–648行、D528決定8 | 一致 |
| glossary：詳細委譲 | 対応表はrunbook §7.9 | 同節1790–1796行に表が実在 | 一致 |
| §8の追加句 | checklistのexplorationはuse class | D158の対象、D1848理由5 | 一致。既存checklistの実行要件は変更していない |

## 裁定引用の忠実性 (問い 2)

| 裁定 | 評価 |
|---|---|
| **D1879** | 採る1件＝語の整理、採らない2件＝working bytes拘束・既存consumerの`extended`必須化、という範囲を維持している。意味witnessを「引き続き見送り」とする誤引用もない。 |
| **D1848 理由5・却下肢3** | 標本帰属とuse classが別物であること、探索rootへ移さないことを忠実に反映。成果物fieldの抜粋は全項目列挙とは宣言しておらず、他fieldの削除を意味しない。 |
| **D528 決定5・7** | 必須引数と宣言由来の族という要旨は一致。ただし8cは決定9の直接layout経路であり、「全producerが必ずrun_campaignへ宣言を渡す」という保証にはできない。今回の文は概要として読める。 |
| **D528 閉表・materialize** | 4値／2値とも一致。`official`が標本の正式性を証明しない説明は決定8とも整合する。 |
| **D123** | 6 driverの列挙にA-1がない点は正しい。歴史成果物の移動を求める文もない。markerによる拒否はblocklistの説明として一致し、marker無しも含む全面拒否保証ではない。 |
| **D158** | 優先順位・外部exploration rootの防護境界は一致。pinの記述はenv経路の限定が必要（R-1）。当時の「officialはenvを参照しない」を現行official envまで広げてはならない（R-2）。 |
| **D1859** | 成果物に全経路の意味witness保証を追加していない。T-2418 insightの歴史的な`unestablished`も現行状態として再掲しておらず、射程拡大はない。 |

## scope 超過と欠落 (問い 3・4)

**新しい運用gate・検査・台帳・将来提案は見つかりませんでした。** 「certified材料・proof chain素材を置かない」はD158の既存規律、「正式標本へ混ぜない」「事前登録する」はD1813の再掲です。語の読み分けを求める文も依頼の目的内です。提示差分に、凍結成果物・正式consumerの受理集合・`run_kind`必須化・正しさゲートを変更する文はありません。

定義A・定義B・対応表・読み分けはすべて§7.9内に揃っています。`--explore-campaign` と検査文言の追加は、実際に語Bを使う入口を示すため有用です。「第3の表記」であって「第3の意味」ではない構成も妥当です。docstringの例も、R-3のように対象を限定すれば誤解を減らします。

glossaryは既存の「太字用語＋読み — 一般定義。*izanagi:* 固有の意味」の書式に沿い、機体固有の絶対pathを含みません。近傍項目より長く、field名や裁定番号は多いものの、詳細をrunbookに委ねる導線はあります。R-5の限定を足せば単独でも読みやすくなります。

§8の追加句は既存のexploration checklistを語Aに結び直す説明です。export先・設定タイミング・worktree内materialize拒否の要件を増減していません。

親brief／裁定については、次の範囲まで確認できます。

- **P1・P2：** glossary追加は依頼の「必要なら」に収まり、節の配置も要求を満たす。
- **P3：** brief27行の「A-1対測定（正式測定）」は提示根拠では未確立。ただしadjudication8行が「正式か否かは本節で判定しない」へ修正しており、成果物にも前の断定は残っていない。
- **7 module：** `orchestrator/campaign/*.py` のmodule-level代入をASTで再走査し、7件すべて`exploration`と確認した。実行時の全経路を測定した証拠にはしない。
- **段2・3省略の3条件：** 設計上の選択はP1〜P3を親が確定し、提示差分は正しさ防壁・受理集合を変更しない説明文に限定される。省略判断を覆す実装変更は見つからない。ただしDW-C00／DW-S04本体は指定射影にないため、手続規定そのものへの適合を独立に認証したわけではない。
- **review 1本：** 事実照合とscope点検を同一レビューで扱える差分。ただし1本にしたこと自体は事実誤りゼロの証拠にはならず、本レビューでR-1等が残った。
- **grepによる非拘束性：** R-7の範囲を超えて一般化できない。裁定inbox等の再走査記録も親の報告であり、本レビューでは再実施していない。

## 総括

**R-1の修正が必要です。** envだけに適用されるpinを全解決経路の保証として書いています。R-2〜R-5も限定を明確にする修正を推奨します。

「D1813の探索走はuse classでは`official`」「use classの`exploration`だけでは標本帰属は決まらない」という中心説明は一次資料と一致します。コード変更や新しい検査を追加せず、文言の限定だけで是正できます。