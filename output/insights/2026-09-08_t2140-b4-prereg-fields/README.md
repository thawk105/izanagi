# [T-2140] B-4 事前登録 §5 の残り欄と §10/§11 の記述矛盾訂正 (2026-09-08)

wave branch `worktree-dev-wave-t2140-b4-prereg-fields`。base commit 240ee6360、
記録前に local main `bf092abf0` を取り込み済み。docs-only (実装面の差分ゼロ)。

## 依頼と、依頼の前提が覆れた点

依頼は「§5 の未記入 8 欄のうち floor 以外を §5.1 の解除条件どおりに埋める」であり、
その根拠として「実走前に要るとされた裁定 2 件 (D1694 前提訂正・D1695 標本数) が
commit b9fe01263 で land 済みなので前提は解けている」を挙げていた。

**この前提は floor 欄にだけ掛かる。** D1694 / D1695 は §5.1 の floor 項への追記であり、
その追記自身が「それでも本欄の解除条件は 1 つも緩まない」と書いている。
他の 7 欄の解除条件は 1 つも解いていない。親が欄ごとに現物で測った結果が下表である。

|欄|§5.1 が要求するもの|実測した現在地|本 wave の扱い|
|---|---|---|---|
|赤 precursor の母集合|`analysis_manifest` と `scheduled_attempt_registry` の**実体**の path・sha256・行数|生成器 `p3_b4_prerun_issuer.py` は実在するが、実体は `output/` 配下に 1 件も無い|埋めない|
|primary outcome の演算定義|raw 試行記録から §5.1.1 の入力型を作る経路 + 一致検査 consumer の path と sha256|`p3_b4_analysis_path.py` の `_SOURCE_CLOSURE_PATHS` 5 member が実在。関連 test 緑|**記入した**|
|校正済み `PerfConfig`|calibrator が決めた値へ差し替えるまで記入しない|`p3_s4_loop.default_perf()` は未校正のまま (records=100000 / threads=4 / extime=1 / reps=2)|埋めない|
|総計測予算|arm 対称の exact な 3 種の予算値|repo に出所が無い。§5.1.1 自身が `n = 201` は予算超過見込みと書く|埋めない|
|env_tag|driver・site・tag の 3 つ組を同じ site resolver から機械導出|resolver は実在するが (`p3_s4_loop._SITE_ENV_TAGS`)、tag は site で `pegasus` / `linux-baremetal` に分岐し、正式実走 site が未確定|埋めない|
|model snapshot / prompt / projection|4 点 (宣言源・承認する人間・時点・不一致時の扱い) を別 commit で先に固定|§10 が「人間の指名を含むため AI が確定できない」と明記|埋めない|
|開始時刻|timezone 付きの予定開始時刻|repo から導出できる値ではなく、実行責任者の日程決定|埋めない|

**したがって本 wave が埋められたのは 10 表行 (独立値 11) のうち primary outcome の 1 値だけである。**
残りは「解除条件が未充足」であって、記入を怠ったのではない。

## 段 4 の裁定 (段 3 の 13 所見)

段 3 はレンズ A (正しさ境界・規律) とレンズ B (整合・実効性の現物検算) の 2 本。

**refuted 1 件。** レンズ A 所見 1「raw 試行記録の権威 producer が無いので closure に欠落があり、
primary outcome 欄は埋めてはならない」。根拠にした `p3_b4_analysis_adapter.py` の docstring
「raw fields that do not yet have an authoritative producer」は commit 592a08f32 (2026-08-27) 由来で、
**その後 `orchestrator/campaign/p3_b4_raw_record_producer.py` が commit bab79b6c4 (2026-09-03、[T-2141])
で入り、`treatment_fired` / `contaminated` / `protocol_ok` を snapshot bytes から導出している。**
さらに §5.1 が名指す「raw な試行記録から入力型を作る経路」は adapter 自身であり
(adapter docstring: "from B-4 raw artifact JSON to contract inputs")、producer はその上流で
raw 記録を作る側である。よって closure に欠落は無い。

**real だが記入を妨げないもの 2 件。**
- レンズ A 所見 2「consumer は adapter の contract 一致を挙動検査しない」。現物で真である
  (`assert_preregistration_matches_implementation` は contract / ledgers / path の 3 source しか受けない)。
  ただし §5.1.1 が定義するのは母集合規則・n・純関数・enum・verdict であり、それらは
  contract / ledgers / path に在る。consumer はその 3 者を検査するので、条件は満たす。
  **consumer 自身が宣言する限界 (AST 検査は限定的、hidden constant の不在は証明しない) は、
  記入によって消えるものではない。**
- レンズ A 所見 4「記入は §5.1 が塞いだ latent gate relaxation を開く」。§5.1 の当該警告は
  「**定義への参照だけで**埋めると実装が無いまま関門が開く」ことを塞ぐものである。
  本 wave が書いたのは定義への参照ではなく実装 artifact の path と sha256 であり、
  実装は実在する。警告の射程に当たらない。

**real で採用したもの 3 件。**
- レンズ B 所見 2。§11 の追記は「非 `None` の floor が渡るのは、検証を通る権威ある成果物 pin が
  §5 に書かれている場合だけ」と条件を明示せよ。採用し、両方の追記へ書いた。
- レンズ B 所見 4・5。親 brief の行番号・欄数 (10 表行 / 独立値 11) と、§11 の訂正箇所数 (1 か所ではなく 2 か所) の誤記。訂正した。

**real で裁定パッケージへ返すもの 4 件** (下の「ユーザー裁定へ返す項目」)。

**証拠で解消したもの 1 件。** レンズ A 所見 6「§10 の完了追記は証拠の裏取りが要る」。
親が `output/insights/2026-08-27_t1769-b4-wiring-probe/t2341-eligibility/` の現物を照合した。
3 件の JSON の sha256 は §5 の値セルの 3 値と exact 一致、3 件とも `result.passed` が真、
`result.pass_rule` が §5.1.0 (d) の凍結値、`run.axis` が §5.1.0 の対と exact 一致。
§5.1.0 の決定規則 (列挙順の先頭 1 件) が base を選ぶ。よって §10 の「埋められず」は stale である。

## 実際に変えた bytes

`docs/phase3-b4-reflux-ablation-preregistration.md` の 1 file のみ、31 行追加 1 行削除。

1. §5 の primary outcome 行を、`_SOURCE_CLOSURE_PATHS` の順で 5 member の path と sha256 に置換。
2. §10 の「対象 driver と軸の欄は埋められず」の直後へ erratum を追記 ([T-2398])。
3. §11.0 と §11.3 の「生成器は本書を読まず無条件に floor 不在を渡す」の直後へ erratum を追記 ([T-2424])。

**触っていない範囲。** §5.1.1 の raw bytes (文書の `#### 5.1.1` から §6 直前まで) は
`p3_b4_analysis_prereg_consumer.py` が sha256 `0ceab4cd...df30` で pin する。編集位置は
すべてその範囲の外であり、pin を含む test は編集後も緑である。floor 行、§5.1 と §5.1.1 の規範本文、
`docs/phase3-main-experiment.md` の bytes にも触れていない。

## 検査

- `orchestrator/tests/test_p3_b4_analysis_prereg_consumer.py`、`test_p3_b4_admission_record.py`、
  `test_p3_b4_material_report.py`、`test_p3_b4_analysis_path.py` — 編集後 117 passed。
- `python3 tools/check_docs.py` — 違反なし。
- §5 表の構造検査 — 12 行 (header 2 + data 10)、全行 2 セル、primary outcome 行は sentinel なし。
  残り 6 欄は sentinel を保つので、実走前の admission 検査は**閉じたままである**。
- 実装面の差分ゼロなので変異 matrix は免除 (DW-S04)。受入全走は免除していない。

## ユーザー裁定へ返す項目

1. **「その artifact」の読み (レンズ A 所見 3)。** §5.1 の primary outcome 欄が言う
   「その artifact path と sha256」を、(a) 実装 source file と読むか、(b) consumer が成功時に作る
   source-closure receipt と読むか。本 wave は (a) を採った。(b) と読む場合、現行の consumer は
   receipt を返すだけで path へ永続化しないため、**どう書いても欄は埋められない**ことになる。
   (b) が正なら本 wave の記入を 1 行差し戻す必要がある。
2. **開始時刻欄 (レンズ A 所見 5)。** §0 はこの欄だけ部分記入を許すので、
   「他欄が未了だから書けない」という親 brief の理由付けは誤りだった。予定開始時刻は
   実行責任者が決める日程であり repo から導出できないので、値の指名を求める。
3. **§11 の凍結。** 依頼にあった「§11 の凍結 commit」は本 wave では作れない。
   §11 は D1383 に基づく**未裁定の案**であり、§11 自身が「誰がどの証拠で floor 欄を発効させるかは
   ユーザーが決める」と書く。本 wave の commit は §11 の erratum を含む版を固定はするが、
   事前登録としての凍結ではない。凍結には §11.1 / §11.2 の採否裁定が要る。
4. **同型の陳腐化が §7.2 と §10 にも残る (レンズ B 所見 7、本 wave の scope 外)。**
   両節は「manifest・append-only registry・完全性 consumer は存在しない」と断言するが、
   `p3_b4_analysis_ledgers.py` に registry の封印・manifest 生成・完全性検査が実在し、
   consumer と材料レポートがそれを通る。**file-drawer 全体が閉じたとは言えない**ので、
   訂正の文面は「機構が存在しない」という一括断言だけを対象にすべきである。

## 一次資料

- `verbatim/stage1-brief.md` — 親の段 1 brief (欄ごとの実測表を含む)。
- `verbatim/stage2-plan.md` — 段 2 の file:line プラン。
- `verbatim/stage3-lens-a.md` — 段 3 レンズ A (正しさ境界・規律)。
- `verbatim/stage3-lens-b.md` — 段 3 レンズ B (整合・実効性の現物検算)。
