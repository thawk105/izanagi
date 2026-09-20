## 決定 (P1〜P6)

**P6 の主状態は維持し、定義・表示・格子配置を修正する。** 実装・作図・pytest は行っていない。指定資料はすべて読めた。

以下、既存ファイルの参照を短縮する。

- `S` = `docs/paper-story/2026-09-19.md`
- `G` = `tools/plotting/plot_a1_sized_paired.py`
- `T` = `orchestrator/tests/test_plot_a1_sized_paired.py`
- `F` = `docs/paper-story/figures/README.md`
- `C` = `tools/plotting/FIGURE_CONVENTIONS.md`
- `B` = `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-fig3b-arc-status/BRIEF.md`

新規ファイルの行番号はまだ存在しないため捏造せず、**新規ファイル名＋関数名／JSON key と、実在する雛形の file:line** で指定する。

| 裁定 | 採否と理由 |
|---|---|
| P1 | **変える。** 上段3箱は採用。下段は A＝1行5列、B＝2行6列の11セルとする。Bを1行11列にすると副ラベルが読めない。A見出しは `A-series items` とし、A-3 に `rule only; not evidence` を残す。根拠：`B:45–48`、`S:2418–2424`。 |
| P2 | **採る。** 図中は英語、DejaVu Sans。`B:49`、`G:298–300`。 |
| P3 | **採る。** 判定語と資格限定は副ラベルに置く。`3 formal runs`、`0 attempts`、`round 2`、`applied once` は数量なので写さない。対応する項目名・判定語で置換する。`B:50–51,62–78`。 |
| P4 | **採る＋補う。** 実JSONでの実寸描画に、実Figureの衝突・逸脱・出力抑止テストを加える。着地bytesのpinは作らない。`C:96–113`、`T:212,221,232`。 |
| P5 | **採る。** 入口READMEは変更しない。旧fig3が本文と不一致という注記は現在も真。`B:55`、`S:221–223`。 |
| P6 | **主状態は採る、定義を変える。** `obtained` は肯定的結論や要件充足を意味しない。`not obtained` は「当該要件の証拠が未取得」であり、部分実走の不存在を意味しない。Actの進捗と証拠状態は別fieldにする。`S:2420–2424,2550–2554,2705–2718`。 |

## JSON

置き場は **`tools/plotting/arc_status_2026-09-20.json`**。日付は図の作成日で、本文の版は独立した `story_version` で明示する。

JSONも実装面である。`tools/check_ai_provenance.py:75–76,1583–1596` に従い、authorの対象に含める。

schemaは独立したJSON Schemaファイルを増やさず、`plot_arc_status.py::load_states` 内で検証する。読み込み・例外正規化は `G:122–143`、型と必須条件は `G:79–99` が雛形。

**全文案：**

```json
{
  "schema": "izanagi-arc-status/v1",
  "story_version": "2026-09-19",
  "story_path": "docs/paper-story/2026-09-19.md",
  "state_definitions": {
    "obtained": "A recorded judgment or completion exists; it need not support the claim.",
    "uncertified": "Materials exist; the item is not certified, promoted, or closed.",
    "awaiting ruling": "Further authorization or human action remains pending.",
    "not obtained": "The required evidence is not yet obtained, including blocked work."
  },
  "acts": [
    {
      "id": "Act 1",
      "label": "Trustworthy evaluator",
      "progress": "complete",
      "state": "obtained",
      "source_anchor": "§0:L80-L80",
      "items": [
        {
          "id": "act1-evaluator",
          "label": "Build a trustworthy evaluator",
          "state": "obtained",
          "sublabel": "complete",
          "source_anchor": "§0:L80-L80"
        }
      ]
    },
    {
      "id": "Act 2",
      "label": "Falsification and synthesis",
      "progress": "complete",
      "state": "obtained",
      "source_anchor": "§0:L81-L82",
      "items": [
        {
          "id": "act2-hypothesis",
          "label": "Search hypothesis",
          "state": "obtained",
          "sublabel": "falsified",
          "source_anchor": "§0:L81-L82"
        },
        {
          "id": "act2-value",
          "label": "Value beyond the search space",
          "state": "obtained",
          "sublabel": "relocated to synthesis",
          "source_anchor": "§0:L81-L82"
        }
      ]
    },
    {
      "id": "Act 3",
      "label": "Code-level synthesis",
      "progress": "in progress",
      "state": null,
      "source_anchor": "§0:L83-L87",
      "items": [
        {
          "id": "act3-claim",
          "label": "S' claim",
          "state": "obtained",
          "sublabel": "not met",
          "source_anchor": "§8:L2550-L2554"
        },
        {
          "id": "act3-scope",
          "label": "Silo-only scope",
          "state": null,
          "sublabel": "lifted; preparation underway",
          "source_anchor": "§0:L123-L133"
        },
        {
          "id": "act3-mechanism",
          "label": "Mechanism work",
          "state": null,
          "sublabel": "advanced; claim remains unmet",
          "source_anchor": "§0:L83-L87"
        },
        {
          "id": "act3-formal",
          "label": "Adopted configuration",
          "state": "obtained",
          "sublabel": "A-2 observed-positive; A-6 reject; T-1998 accepted",
          "source_anchor": "§0:L85-L87"
        },
        {
          "id": "act3-descriptive",
          "label": "A-1 descriptive attempt",
          "state": "uncertified",
          "sublabel": "non-certifying",
          "source_anchor": "§0:L100-L105"
        }
      ]
    }
  ],
  "evidence_groups": [
    {
      "id": "A",
      "label": "A-series items",
      "items": [
        {
          "id": "A-1",
          "label": "Paired headline estimand",
          "state": "uncertified",
          "sublabel": "descriptive; non-certifying; reauthorization pending",
          "source_anchor": "§8:L2467-L2470"
        },
        {
          "id": "A-2",
          "label": "Write-heavy / balanced certification",
          "state": "obtained",
          "sublabel": "observed-positive; limitations retained",
          "source_anchor": "§8:L2429-L2438"
        },
        {
          "id": "A-3",
          "label": "Reporting rule",
          "state": "obtained",
          "sublabel": "settled; rule only; not evidence",
          "source_anchor": "§8:L2420-L2424"
        },
        {
          "id": "A-5",
          "label": "Separate boot reproduction",
          "state": "not obtained",
          "sublabel": "unfulfilled; Pegasus ineligible",
          "source_anchor": "§8:L2527-L2539"
        },
        {
          "id": "A-6",
          "label": "Read-heavy certification",
          "state": "obtained",
          "sublabel": "reject; limitations retained",
          "source_anchor": "§8:L2451-L2455"
        }
      ]
    },
    {
      "id": "B",
      "label": "B-group requirements",
      "items": [
        {
          "id": "A-4",
          "label": "Official floor",
          "state": "awaiting ruling",
          "sublabel": "measured; chain not landed; inactive; human action pending",
          "source_anchor": "§8:L2861-L2867"
        },
        {
          "id": "B-1",
          "label": "Beyond best known axis",
          "state": "obtained",
          "sublabel": "not met",
          "source_anchor": "§8:L2550-L2554"
        },
        {
          "id": "B-2",
          "label": "Descriptor causal evidence",
          "state": "not obtained",
          "sublabel": "not run; layered blockage",
          "source_anchor": "§8:L2555-L2560"
        },
        {
          "id": "B-3",
          "label": "Formal holdout series",
          "state": "not obtained",
          "sublabel": "not completed; authority absent",
          "source_anchor": "§8:L2586-L2590"
        },
        {
          "id": "B-4",
          "label": "Detailed anomaly feedback",
          "state": "not obtained",
          "sublabel": "not run; specs frozen; eligible precursor absent",
          "source_anchor": "§8:L2623-L2628"
        },
        {
          "id": "B-5",
          "label": "Budget-matched generator comparison",
          "state": "not obtained",
          "sublabel": "not obtained",
          "source_anchor": "§8:L2698-L2704"
        },
        {
          "id": "B-6",
          "label": "Leak-controlled execution",
          "state": "not obtained",
          "sublabel": "loop exercised; leak control incomplete",
          "source_anchor": "§8:L2705-L2718"
        },
        {
          "id": "B-7",
          "label": "All-workload regression reporting",
          "state": "uncertified",
          "sublabel": "materials complete; requirement not met",
          "source_anchor": "§8:L2719-L2735"
        },
        {
          "id": "B-8",
          "label": "Independent long-run validation",
          "state": "not obtained",
          "sublabel": "not obtained",
          "source_anchor": "§8:L2736-L2737"
        },
        {
          "id": "B-9",
          "label": "Mechanism reporting",
          "state": "uncertified",
          "sublabel": "screening supported; deep check halted; secondary view non-certifying",
          "source_anchor": "§8:L2738-L2761"
        },
        {
          "id": "B-10",
          "label": "Extended mechanism evidence",
          "state": "uncertified",
          "sublabel": "grid and tail judged; performance uncertified; not closed",
          "source_anchor": "§8:L2765-L2767;§0:L149-L153"
        }
      ]
    }
  ]
}
```

`source_anchor` は `story_path` 内の実行番号を指す。ここに示した英訳・短縮は逐語引用ではなく、人が行った状態射影である。生成器はアンカーの存在・範囲まで検査し、本文の意味から状態を再判定しない。

**fail-closed検証：**

- 各階層のkey集合を完全一致させ、未知field・不足field・重複JSON key・NaN/Infinityを拒否。
- `state_definitions` のkeyは上記4値に完全一致。定義文もv1の契約として照合する。
- 証拠項目の `state` は4値のみ。`null` はActの中立的な進捗／説明行だけに許す。第5の証拠状態にはしない。
- Actは3件。AのID順、BのID順は上記と一致。全objectのIDは一意。これは当図の構造契約であり、plotting全体の目録ではない。
- `story_version` は有効なISO日付、`story_path` はその版の `docs/paper-story/<date>.md`。JSONと本文はrepo内の実在ファイルに限定する。
- `source_anchor` は `§0` または `§8` と `L開始-L終了` の連結形式。開始≤終了、本文の行数以内を確認する。

**数値文字列の規則：**

描画対象の `label`、`sublabel`、凡例文、生成する脚注に専用検査を掛ける。schema、path、source line番号は描画しない。

1. NFKC正規化した検査用文字列に対し、`%`、`％`、`µs`、`μs`、独立した単位語 `tps/us/ms/ns/seconds/percent`、`p\s*[=<>≤≥]`、数値代入 `A\s*=` を拒否する。
2. 数字入りtokenは、境界付きの**明示的ID集合**だけを許す。当初は A-1〜A-6、B-1〜B-10、P2-4、P2-5、S-1a、D2114、T-1998、fig3、fig8、fig9、attempt-0001。これらを除いた後に残るUnicode数字を拒否する。
3. 日付は脚注の `story_version` に一致するものだけ許す。`Act 1`〜`Act 3` は構造化IDから生成し、自由文の数量例外にしない。
4. `three runs` のような抜け道を避け、自由文では英語数詞 `zero/one/.../nineteen/twenty/.../ninety/hundred/thousand/million/billion` も拒否する。本案の表示文には不要。
5. 正常例 `A-1 / S-1a / D2114 / fig8 / attempt-0001` と異常例 `38% / 10 tps / 2 µs / p = .05 / A=0.58 / 30 pairs / three runs` を別々に試す。

任意の自然言語から数量を完全に抽出する検査ではない。有限の表示契約と拒否例を機械検証し、意味の妥当性は本文照合レビューで担保する。

## 生成器

新規 `tools/plotting/plot_arc_status.py` は自己完結とする。既存生成器のimport、共有framework、pluginは作らない。

| 関数／部分 | 設計と雛形 |
|---|---|
| 定数・例外 | Agg、DejaVu Sans、schema、既定JSON、4色・4マーカー、FigureDataError／FigureLayoutError。`G:19–29,71–85`。 |
| `load_states` | JSON・本文をそれぞれ一度bytesで読み、同じbytesからparse／SHA-256を得る。上記検証後に内部データと入力記録を返す。`G:122–150` の分離を使い、統計・pin表・認証再計算は移植しない。 |
| `make_figure` | 次節の固定幾何を使用。`G:298–331` の「データからartistを作る」構造だけを採る。 |
| `check_figure_layout` | `G:334–368` のbbox交差・包含・実rendererを移植。3軸前提の `G:346–348,358–363,369–371` は置換する。 |
| `build_provenance` | `G:374–388` を簡素化し、入力・描画項目・環境・captionを記録。 |
| `_publish_outputs` | `G:414–445` の「検査→一時出力→hash→公開→失敗時cleanup」を採る。 |
| `main` | `G:448–468` のparse、rc非0、finallyでcloseを採る。 |

`make_figure` は `fig, layout` を返す。`layout` は各箱・セル・凡例・脚注の所有領域とartist参照を保持する小さな内部dictでよい。

**layout checkの対象：**

- 軸は作らず、`fig.transFigure` 上のpatch・Text・Line2Dで描く。
- `fig.canvas.draw()` 後、すべての可視・非空Textを `fig.findobj(Text)` で収集する。登録済みTextだけを見る方式にしない。
- 全Textのbboxについて、figure内包、所属領域の内包、他Textとの交差面積≤1 px²を要求する。
- Textの幅・高さが非有限／非正なら失敗させる。雛形の「幅がないのでskip」は採らない。
- マーカーもrenderer bboxを取得し、所有領域内包・Textとの非交差を検査する。
- 背景patchとその中の文字の重なりは意図した包含なので、衝突判定の組にはしない。
- 所有セル同士の重なり、隣セルへの文字の逸脱、未登録Textも失敗とする。
- 200 dpiで検査しPNGも200 dpi、`bbox_inches="tight"` は使わない。PDFの最終表示は親が目視する。

**provenance field：**

```text
schema = izanagi-arc-status-figure-provenance/v1
generated_utc
story_version
story_path
inputs[] = {kind: states|story, path, sha256}
generator = {path, sha256}
outputs[] = {path, sha256}             # PNG/PDFのみ
drawn_items[] = {id, state, label}
state_definitions
caption
argv
versions = {matplotlib, numpy}
```

`drawn_items` はAct見出し・Act行・証拠セルを描いた順に含める。`label` はIDと副ラベルを含む実表示文字列とし、折返し改行だけ正規化する。描画時のText参照から取得し、入力から期待される項目との一致も保存前に照合する。provenance自身のhashは自己参照になるので入れない。

**公開とCLI：**

```text
python3 tools/plotting/plot_arc_status.py
    [--repo-root PATH]
    [--states PATH]
    OUT_PREFIX
```

- `--states` 省略時は既定JSON。相対states pathはrepo root基準、相対OUT_PREFIXは呼出しcwd基準。
- prefix basenameは `re.match(r"^fig([0-9]+[a-z]*)_", name)`。`fig3b_...` を受理し、`foo_...` を拒否する。captionの図番号はcaptureした `3b`。
- layout check通過前は出力directory／一時成果物を作らない。
- PNG/PDFを一時保存し、そのbytesをhashしてprovenanceを作る。成功後に3ファイルを公開する。
- **既存の3出力のいずれかが存在すれば拒否**する。凍結物の上書きを認める雛形の退避・復元処理は採らない。再現は別directoryで行う。
- 3ファイルの同時atomic公開は保証しない。通常例外時は公開済みの新規ファイルを除去する。異常終了後の部分残存は次回実行で拒否する。

## 図の要素

根拠は `B:45–51`、配置の雛形は `G:298–331`、検査要件は `C:85–113`。

**figsize＝16×11.5 inch、200 dpi。** 以下は左下原点のfigure正規化座標。

| 領域 | 座標・寸法 |
|---|---|
| タイトル | `(0.03, 0.97)`、16 pt |
| Act箱 | 左下 `(0.03,0.66)`, `(0.35,0.66)`, `(0.67,0.66)`、各幅0.30・高さ0.26 |
| A見出し | `(0.03,0.63)`、11 pt |
| A格子 | 左端0.03、下端0.485、幅0.94、1行5列、列間0.01、高さ0.12 |
| B見出し | `(0.03,0.46)`、11 pt |
| B格子 | 左端0.03、下端0.205、幅0.94、2行6列、列間0.01、行間0.01、各高さ0.11 |
| 凡例 | `x=0.03..0.97, y=0.085..0.18`、2列2行 |
| 脚注 | `y=0.025..0.068`、8 pt、3行 |

Aセル幅は2.88 inch、Bセル幅は約2.37 inch。Bは上段 `A-4,B-1,…,B-5`、下段 `B-6,…,B-10`。末尾の空きには枠・マーカーを描かない。

- Act見出し13 pt、本文10 pt。Act 3は5行の要点を縦配置し、長い正式判定行だけ折り返す。
- セルはID 10 pt bold、短い名前9 pt、副ラベル8.5 pt。名前と副ラベルは別Textにする。
- 左右paddingは8 pt、マーカー用に左側14 ptを確保。単語境界で折り返し、収まらなければ保存を拒否する。自動縮小や切捨てはしない。
- Act 1は「evaluator／complete」、Act 2は「hypothesis／falsified」「value／relocated to synthesis」。Act 3はJSONの5項目。
- Act 3の箱は白〜薄灰色、`in progress` を文字で表示。scope解除と機構進展には中立の短い横線を付け、証拠状態のマーカーを付けない。

4状態の符号は次のとおり。B-1の否定判定も同じ `obtained` になるため、成功を連想させる緑色のチェック印は使わない。

| 状態 | マーカー | セルの淡色 |
|---|---|---|
| obtained | 塗り丸 `o` | 青系 `#DCEAF5` |
| uncertified | 中抜き菱形 `D` | 橙系 `#FCE8CF` |
| awaiting ruling | 中抜き三角 `^` | 紫系 `#EBDFF2` |
| not obtained | `x` | 灰色 `#EEEEEE` |

凡例は状態名とJSONの定義文を同一文面で置く。脚注案：

```text
Evidence states: paper-story 2026-09-19 §8; act summaries: §0. No values drawn.
Obtained does not imply a supported claim. A-3 is a settled rule, not new evidence.
Successor to fig3; the original remains frozen. No certification or authorization is granted.
```

## test

新規 `orchestrator/tests/test_plot_arc_status.py`。import方法と独立hash計算は `T:23–36`、JSON変更fixtureは `T:133–148`、実Figure系の設計参照は `T:212,221,232`。

| test名 | 検証 |
|---|---|
| `test_real_states_render_at_production_size` | 実JSONを読み、本物のFigureをcheckへ通す。Act3箱、A5セル、B11セル、表示された全ID／副ラベルを確認。 |
| `test_rejects_invalid_state` | 不正stateと証拠セルのnullを拒否。 |
| `test_rejects_duplicate_ids` | 同一group内・group間・Act行間の重複を拒否。 |
| `test_rejects_unknown_fields` | top-level、Act、group、itemの各階層に未知keyを注入。 |
| `test_display_text_rejects_quantities_and_accepts_ids` | 前述の正常IDと異常数量を個別に検査。 |
| `test_rejects_malformed_input` | 重複JSON key、型違い、欠落項目、不正source anchorを拒否。 |
| `test_layout_rejects_real_overlap_and_escape` | 本物のTextを同じ座標へ移動／セル外へ移動して失敗を確認。 |
| `test_layout_failure_publishes_nothing` | 衝突させた実Figureを実 `_publish_outputs` に渡し、3成果物も一時ファイルもないことを確認。 |
| `test_provenance_matches_input_bytes_and_artists` | 独立した `hashlib.sha256(read_bytes())` とinputsを比較。raw JSONをテスト側で展開した表示期待値、実Text、drawn_itemsを比較。 |
| `test_changed_input_reaches_artists_and_provenance` | 実寸を保ったJSONコピーのlabel/stateを変更し、Figureとprovenanceの両方に届くことを確認。科学的状態を変更するのはtmp fixtureのみ。 |
| `test_cli_accepts_fig3b_and_rejects_foo` | 有効prefixで一度だけ3出力を作り、magic bytes・出力hash・schema・caption・argv・versionsを検査。不正prefixはrc非0、出力なし。 |
| `test_existing_outputs_are_not_overwritten` | tmpの既存成果物が保存されることを確認。着地成果物は対象にしない。 |

JSON検証は描画せず、正常描画・変化fixture・衝突fixtureを必要数だけ作り、すべてcloseする。実PNG/PDF保存は正常CLIの1回を基本とする。数秒以内を目標とするが、**所要時間は未実測**。

`orchestrator/tests` 全体と `tools/check_docs.py` を `plotting / plot_arc_status / arc_status`、さらにglob・列挙・countパターンで検索した。既存fig9テストと検査方式は共通するが対象入力は異なる。**本図専用テストやplottingモジュール総数をpinする検査は見つからなかった。** `test_plot_dynamic_backoff.py:661` は当該図のpolicy格子契約であり、本図追加の目録制約ではない。

## 変異候補

新規sourceの実行番号はauthor後に段4台帳へ確定する。ここでは**関数内の変異対象式**と対応する既存雛形行を事前登録する。

| 変異対象 | 変異 | killするtest |
|---|---|---|
| `load_states` のstate集合検査（`G:144–150`型） | `uncertified` をenumから削除 | `test_real_states_render_at_production_size` |
| `load_states` のkey完全一致 | 未知field検査を削除 | `test_rejects_unknown_fields` |
| 表示文validatorの量拒否regex | regexを空文字にする | `test_display_text_rejects_quantities_and_accepts_ids` の正常例が失敗 |
| `check_figure_layout` の交差判定（`G:367`） | 条件を常に真にする／交差面積を常にゼロにする | 前者は正常実寸test、後者は `test_layout_rejects_real_overlap_and_escape` |
| `build_provenance` のinputs SHA-256（`G:137–141,379`型） | 空文字にする | `test_provenance_matches_input_bytes_and_artists` |
| 描画／provenanceの項目展開（`G:289–295,385`型） | 実JSONに依存しない定数へ置換 | `test_changed_input_reaches_artists_and_provenance` |
| prefix検査（`G:258–261,456`） | 検査を外す | `test_cli_accepts_fig3b_and_rejects_foo` |
| `_publish_outputs` の事前検査（`G:416`） | layout check呼出しを削除 | `test_layout_failure_publishes_nothing` |

「量のregexを無効化する」変異が空regexではなく常時不一致regexなら、同じtestの異常例がkillする。

**両層stubへの対策：** 正常系で `make_figure` と `check_figure_layout` をstubにしない。provenance期待値を生成器の展開helperから作らず、raw JSONと実Textから独立に比較する。実入力変更testがあるため、描画側とprovenance側を同じ定数にするだけでは緑にならない。これは設計上の確認であり、変異killの実測結果はまだない。

## README

一覧は `F:12–24` の形式で1行追加する。

```markdown
| `fig3b_arc_status_2026-09-20.png` / `.pdf` / `.provenance.json` | `tools/plotting/plot_arc_status.py` | `fig3_` の後継図。2026-09-19 版の3幕と §8 の状態を示す模式図。数値・新規判定を含まない。旧 fig3 は凍結のまま |
```

新節は `F:821–900` の順序を踏襲する。

1. **何を示す図か**：3幕、A系列5項目、B群11項目。A-3は規則の決着であり新しい証拠ではない。
2. **既存図との関係**：fig3の後継。旧fig3およびfig1〜fig9のbytesは不変。
3. **入力**：状態JSONと凍結09-19本文。本文が意味の正本、JSONはその射影。§1のWAL/dat規約に対し、値を描かない模式図に限定した入力の位置づけを明記。数値図への一般的な免除にはしない。
4. **再現**：計測機の外で、未使用prefixへ生成。
5. **作図規約への適合**：§5短いラベル、§6入力・描画・出力の鎖、§8依存とPNG/PDF、§9保存前検査、§10実寸fixtureと親の実走。
6. **キャプション正文**：下記をprovenanceと同一文字列で収録。
7. **proof chain**：親が実走後に記入。

再現command：

```bash
python3 tools/plotting/plot_arc_status.py \
  --states tools/plotting/arc_status_2026-09-20.json \
  /tmp/fig3b-reproduction/fig3b_arc_status_2026-09-20
```

作成時のみ出力prefixを `docs/paper-story/figures/fig3b_arc_status_2026-09-20` とする。着地後は再現directoryを変える。論理的な状態と図の再現を対象とし、byte一致は保証しない（`F:138–145`）。

**caption正文案：**

> Figure 3b. Status of the paper-story arc based on the frozen 2026-09-19 story: act summaries from section 0 and evidence-item states from section 8. Colors and marker shapes distinguish obtained, uncertified, awaiting ruling, and not obtained. Obtained records a judgment or completion, not necessarily support for a claim: B-1 remains not met and A-6 records reject. A-3 is a settled reporting rule, not new empirical evidence. A-1 remains descriptive and non-certifying; A-4 remains inactive pending human action. B-7, B-9, and B-10 are not promoted or closed by this figure. Historical judgments retain their original scope and limitations. No measurement values are drawn, no judgments are recomputed, and no correctness gate, certification, or authorization is changed. This is a successor to fig3; the original remains frozen.

proof chainには、生成器commit、入力2ファイルのhash、展開argv、実行環境、rc、3成果物、PNG/PDFの目視確認、test結果、変異結果、独立本文照合の所在を記す。**実走前に成功扱いで埋めない。**

`tools/plotting/README.md` は `166–194` の節を雛形に、用途、CLI、既定JSON、拒否条件、4状態の射程、出力3本、provenance schema、図READMEへの参照を追記する。

## 09-20 版との整合

**09-19版を正本に固定する案を採る。** `S:2341–2343` 自体が、稼働中waveを数えず着地済み正典から読むと明記している。

READMEには次を記す。

- 09-20本文がlandするまでは読み替えない。
- land後、親が本図の各 `source_anchor` と対応する状態語を照合する。
- 状態が変わらなければfig3bを維持し、09-19版由来という表示も維持する。
- 状態が変われば、**既存JSONを上書きせず新しいsnapshot JSONを追加**し、`story_version/story_path/source_anchor` を更新する。
- 新しい図は `fig3c_arc_status_<作成日>` 等の別filenameで生成し、fig3bとその入力snapshotを残す。

同filenameへの再生成は、凍結規則 `F:5–8` に反するため採らない。未landの09-20草稿の状態一致は今回独立に確認しておらず、段4・段7での親の確認事項とする。

## リスク

| 項目 | 推奨と根拠 |
|---|---|
| A-1 | **非認証を主状態に維持。** descriptive出力はあるが、充足・formal化は未判定。再認可待ちは副ラベル。裁定待ちだけでは現存する非認証材料を隠す。`S:100–105,2467–2470`。 |
| A-4 | **裁定待ちを維持。ただし人間手番を明記。** 床の採用自体は裁定済みであり、「採否の判断待ち」と読ませない。chain未land、A/X人間手番、未発効を副ラベルで保持。`S:2861–2864`。 |
| B-7 | **非認証を維持。** 材料中のA-2/A-6等の認証を取り消す意味ではない。同一variantの横断比較と床値超の判定を供給せず、要件へ昇格しないという項目単位の表示。`S:2719–2735`。 |
| B-9 | **非認証を維持。** screening対応済、深い一致検査は裁定停止、機序仮説viewは非certifyingという混合項目。単に未実走とも完了とも描けない。`S:2738–2761`。 |
| B-10 | **非認証を維持。** grid／cohort判定が存在することと、性能未認証・項目未閉鎖を併記。`S:149–153,2765–2767`。 |
| B-1 | **取得済み＋not metを維持。** 取得済みは比較判定がある意味。主張成立・肯定的証拠取得ではない。`S:2550–2554`。 |
| A-3 | **規則の決着として表示。** A系列に置くが、A群の実証的な残件が閉じたという意味にしない。`S:2418–2424`。 |
| B-6／A-5 | **未取得の定義を修正する必要がある。** 部分実走・生値は存在するため「実走が一切ない」とは書けない。当該要件の証拠が未取得とする。`S:2536–2539,2705–2718`。 |

最大の誤読リスクは4状態が科学的に一様な成熟度尺度に見えること。状態の割合、達成率、取得済み件数、成功矢印は描かない。Actの完了も、各方式の性能認証を意味しない。

生成器は判断を計算せず、人が本文から写した状態を描く。A-2/A-6の歴史的判定をidentity修正によって遡及的に強めない（`S:2435–2438`）。これらの表示・captionなら、規律2の緩和や採用認可を示す箇所は設計上ない。

## 総括

**3幕＋Aの1×5格子＋Bの2×6格子、状態JSON、自己完結した生成器、実Figureのfail-closed検査を採る。** P6の主状態は維持し、Act進捗の分離、未取得の定義修正、A-3／B-1の限定を必須にする。旧図・凍結本文は変更しない。

残る確認は3件。

1. 段3〜4で、修正した状態定義とA-4の「人間手番」表現を確定する。
2. 親の実走で、実寸レイアウト・PDF表示・数秒以内のtest所要・変異killを確認する。
3. 09-20版land後に状態差分を照合し、変化があれば別snapshot・別filenameの後継図にする。