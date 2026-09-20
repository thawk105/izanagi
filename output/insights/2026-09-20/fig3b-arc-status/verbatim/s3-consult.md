指定資料はすべて読めた。静的レビューのみ実施し、変更・作図・pytest は行っていない。以下、S＝09-19 版本文、P＝段2 plan、B＝親 brief、F＝図 README、C＝作図規約とする。

## レンズ A

### must-fix

**A-M1：数量検査が、正常な脚注自身を拒否する。**

- **根拠：** P「JSON／数値文字列の規則」「図の要素」。脚注の `§8`・`§0` は許容 ID 集合にも日付例外にも入らない。残存数字の拒否をそのまま実装すると失敗する。
- **放置時：** 実 JSON の正常生成が保存前に止まり、図が出ない。
- **是正：** 文書参照を構造化して生成するか、脚注を `Evidence states and act summaries follow the cited frozen story.` 等へ変更する。caption にも同じ検査を掛けるなら、`Figure 3b`・`section 0/8` を構造的参照として区別する。単なる数字の包括的許可にはしない。

表示案に実測値・反復数等の混入は見つからない。残る数字は日付、項目・図・節・Act の識別子であり、数量とは区別すべきである。

**A-M2：`source_anchor` は項目 ID 形へ変更する。行範囲の存在確認では出所の対応を検査できない。**

- **根拠：** P「JSON／fail-closed検証」「09-20版との整合」、CLAUDE.md「作業の進め方」項6(b)。
- **放置時：** 範囲内の無関係な行でも検証を通り、README への転記では docs 間の行番号参照禁止に抵触する。09-20 版への照合も行位置に依存する。
- **是正：** `§8 A-1`、`§0 第3幕`、`§0 item 3` 等を用いる。生成器は指定本文内の見出しの一意な存在だけを確認し、意味の一致は独立レビューで確認する。

比較は次のとおり。

| 観点 | 行番号形 | 項目 ID 形 |
|---|---|---|
| 凍結本文への束縛 | 本文 SHA-256 と組み合わせれば位置を特定できる。ただし範囲内確認だけでは対応が弱い | 本文 SHA-256 と項目の一意存在で束縛できる |
| 09-20 land 後 | 行位置を探し直す必要がある | 同じ項目を意味単位で比較できる |
| 規則整合 | JSON 自体への禁止適用は断定しないが、docs に持ち出せない | JSON・README を同じ参照方式にできる |

見出し matcher は実文に合わせること。S の A-1 は `- **A-1 (`、A-3・B-1 等は `- **A-3.` 型であり、括弧型だけでは正常入力を拒否する。また、scope 解除の参照は **§0 item 3** であり item 2 ではない。

### should

**A-S1：P6 の主状態は概ね妥当。ただし短縮で落ちた限定を補い、親 brief の定義を plan に合わせて直す。**

- **根拠：** S §8 各項冒頭、§0、P「JSON」、B「P6」。
- **放置時：** A-4 は未裁定、B-9 は未適用・一般対応済み、A-5/B-6 は実走なし、と読める余地が残る。
- **是正：** 以下の照合結果を JSON と親 brief の双方へ反映する。

| 項目 | `state`・`sublabel` の照合結果 |
|---|---|
| A-1 | `uncertified` は妥当。`reauthorization pending` は「申請が審議中」とも読めるため、`reauthorization requires human action` が忠実。充足未判定も保持したい。 |
| A-2 | `obtained`／`observed-positive; limitations retained` は妥当。肯定的判定自体は本文にある。取得済みを無限定な性能保証にしない。 |
| A-3 | `obtained` は「規則の決着」という定義でのみ妥当。`rule only; not evidence` と `A-series items` を維持する。A 群の実証的残件が閉じた扱いにはしない。 |
| A-5 | `not obtained` は妥当。`Pegasus ineligible` は対象限定が弱い。`Pegasus does not establish separate-boot reproduction` が正確。生値取得はあるが要件を満たす証拠ではない。 |
| A-6 | `obtained`／`reject; limitations retained` は妥当。性能 reject と correctness 証拠の欠落を混同していない。 |
| A-4 | 本文は**床採用が裁定済み、未発効、人間手番**。`awaiting ruling` は逐語対応ではなく広い編集分類。副ラベルに `adoption decided` を足し、凡例で pending human action を明示する。 |
| B-1 | `obtained`／`not met` は妥当。「比較判定が存在する」の意味に限定する。 |
| B-2 | `not obtained`／`not run; layered blockage` は冒頭と整合。 |
| B-3 | `not obtained`／`not completed; authority absent` は整合。`not run` に強めていない点も適切。 |
| B-4 | 現案は整合。ただし本文の「記述統計へ限定」が落ちるため、`descriptive-only` を補うと射程が明確になる。 |
| B-5 | `not obtained` は整合。label が因果的「必要性」を復活させず、予算を揃えた比較になっている点は適切。 |
| B-6 | `not obtained`／`loop exercised; leak control incomplete` は整合。部分実走を隠していない。 |
| B-7 | `uncertified` は項目単位の分類として妥当。`requirement not met` は本文の理由段落にも支えられるが、`not promoted to requirement fulfillment` の方が裁定を忠実に写す。材料中の認証を取り消す意味ではない。 |
| B-8 | `not obtained` は整合。label の independent long-run は本文に支えられる。 |
| B-9 | 混合状態を `uncertified` とするのは妥当。ただし `screening supported` は一般的完全対応にも読め、`deep check halted` はユーザー裁定を落とし、`secondary view non-certifying` は**適用済み**を落とす。`screening support scoped; deep check stopped by ruling; secondary view applied, non-certifying` 等へ。 |
| B-10 | `uncertified`／`grid and tail judged; performance uncertified; not closed` は整合。性能未認証は §0 item 5 にも明記される。 |

Act 3 の5行も個別に照合した。

| 行 | 結果 |
|---|---|
| S' claim | `obtained / not met` は §0 第3幕・§8 B-1 と整合。 |
| Silo-only scope | `null / lifted; preparation underway` は §0 item 3 と整合。認証取得のマーカーを付けないのは適切。 |
| Mechanism work | `null / advanced; claim remains unmet` は §0 第3幕と整合。 |
| Adopted configuration | A-2 observed-positive／A-6 reject／T-1998 accepted は §0 第3幕と一致。走行数を落としても判定の組は保持される。 |
| A-1 descriptive attempt | `uncertified / non-certifying` は §0 item 1 と整合。`completed; non-certifying` なら完走した事実も残る。 |

4状態の定義について：

- **obtained：** plan の「判定または完了が記録され、主張支持とは限らない」は妥当。brief の「正式 protocol」は A-3 の規則決着や Act 完了を包摂しないため修正する。
- **uncertified：** 項目単位の未昇格等を表す編集分類であり、材料すべての非認証を意味しないと明記する。
- **awaiting ruling：** 人間の実行待ちも含む定義なら A-4 を置けるが、状態名だけでは狭すぎる。表示を `awaiting ruling / human action` とする案が最も明快。
- **not obtained：** plan の修正を採る。brief の「実測・実走がまだ無い」は A-5/B-6 と矛盾する。

数量削除のうち、`3 formal runs` と `round 2` の削除は現案で意味を保っている。A-5 の「0件」は未取得の**理由**ではなく取得件数であり、削除自体は問題ない。B-9 の `applied once` は `once` だけを落とし、`applied` は残すべきである。

**A-S2：caption は図の記述範囲を述べ、ゲート不変の保証文にしない。**

- **根拠：** P「caption正文案」、S §0 item 8・§8 A-2/A-6、C 冒頭。
- **放置時：** `no correctness gate ... is changed` が、図生成時の検査でゲート不変まで保証した文に読める。
- **是正：** 次の程度に縮める。

> This figure summarizes recorded statuses; it does not evaluate correctness, certify performance, or authorize further work. A-2 and A-6 retain the judgments made under the identity layer used at the time; later identity fixes do not strengthen them retrospectively.

現案の脚注に認証・認可を与える肯定文はない。`Historical judgments retain their original scope and limitations` も規律7に沿う。上記はその対象を明確にする修正である。

**A-S3：09-20 整合は状態 enum だけでなく、限定・人間手番まで比較する。入力 JSON の保持は図の凍結規則とは別に説明する。**

- **根拠：** P「09-20版との整合」、F 冒頭、B「確定済みユーザー裁定」「模擬／実の差」。
- **放置時：** 同じ enum のまま限定だけ変わった場合を見落とし、09-20 と整合したという README 記述が過大になる。
- **是正：** 項目ごとに state、副ラベルの事実、限定、未了理由、人間手番を比較する。図が09-19 snapshot として正しい限り、そのまま保持できる。新状態を描く場合は別 filename とする。

F が凍結対象にするのは PNG/PDF/**provenance JSON** であり、`tools/` の入力 JSON まで自動的に凍結する規則ではない。ただし、旧図の再現入力を保つため別 snapshot を追加する運用は合理的である。「規則上必須」と「再現のため採る方針」を分ける。

二重の日付は矛盾ではないが、入力名を `arc_status_story_2026-09-19.json` 等にすると混同が減る。作成日は図名・provenance に記録できる。

親 brief の前提の確度は以下のとおり。

| 前提 | 判定 |
|---|---|
| 09-20 草稿は時点語だけの置換 | 射影内に草稿がなく、独立未確認。plan も未確認と明記している。 |
| fig4 の限定例外と同型 | 指定された F の範囲に fig4 節本文はなく、同型性は未検証。値なし模式図の入力説明は本図自身の根拠で書ける。 |
| 状態語は §8 冒頭から取れる | 条件付き。Act は §0、A-2 の observed-positive 等は冒頭以外も参照し、4状態への分類は人による射影である。 |
| 稼働中 wave を数えない | S §8 冒頭が明記。**同版の基準 HEAD 時点の規則**として確認できる。 |
| test は数秒以内／本 wave に模擬なし | 所要は未実測。正常入力は実資料だが、変異・変更 fixture は合成入力なので、後者は「科学的状態表は模擬ではない」と範囲を限定する。 |

## レンズ B

### must-fix

**B-M1：状態変更テストに、色・マーカーの実 artist の検査が必要。**

- **根拠：** P「図の要素」「test_changed_input_reaches_artists_and_provenance」「provenance field」。
- **放置時：** 全セルを同じ色・マーカーで描いても、Text と provenance の state だけ正しければ緑になりうる。図の主要情報が誤る。
- **是正：** test 側で独立に定めた状態→色・マーカー対応を、Patch の facecolor、Line2D の marker・塗り設定と比較する。Act の中立2行も証拠状態のマーカーを持たないことを確認する。生成器の対応表を期待値に流用しない。

**B-M2：変異候補の「単一理由性」が未成立。特に数量拒否と項目展開を分解する。**

- **根拠：** P「変異候補」「test」。雛形 `_publish_outputs` は prefix 検査後に layout 検査を呼ぶ。
- **放置時：** 別の拒否層で赤になっただけの結果を対象検査の実効性として計上し、数量や描画状態の欠陥が残る。
- **是正：** 次表の条件で事前登録を具体化する。赤は非0だけでなく、対象例外・理由を確認する。

| 候補 | 帰属上の問題／是正 |
|---|---|
| state enum から `uncertified` 削除 | 正常 JSON が enum 検査で落ちることを確認すれば単純。ただし「無効 state を通す」欠陥の検出ではないので、検証する方向を明記する。 |
| 未知 field 検査削除 | exact-key 検査と別の unknown-key 検査が二重なら片方削除が等価になりうる。未知 key を無視できる入力で、その検査だけの削除により受理される条件にする。 |
| 量拒否 regex を空にする | 常時拒否なので正常例で kill できるが、数量漏出を検出した証拠ではない。常時不一致への変異は `38%` 等が残存数字検査でも拒否される。対象層だけが拒否する `three runs` 等を使い、単位・数詞・数字規則を区別する。 |
| bbox 交差を常に真／面積ゼロ | 別々の変異にする。面積ゼロ用は**同じ所有セル内の2 Text だけ**を重ね、マーカーや領域境界から離す。逸脱 fixture と一緒にしない。 |
| provenance hash を空にする | 独立 hash 比較は適切。ただし digest 形式検査が先に拒否するならその層の赤になる。有効長の誤 digest にすると値の独立照合を試せる。 |
| 描画／provenance 展開を定数化 | 描画、provenance、両方を区別する。変更 state の期待値は色・マーカーまで含める。未変更の実 JSON と同じ定数は、基準入力だけでは観測上等価。 |
| prefix 検査を外す | `main` と publisher の片方だけ除去すると、他方で拒否される。共通 validator の述語を対象にするか、呼出し箇所ごとの目的を分ける。 |
| publisher の layout 呼出し削除 | 直接 publisher に、他の契約は正常な衝突 Figure を渡す。事前に test 側で check して落ちたり、描画項目一致検査で落ちたりしない fixture にする。 |

raw JSON と実 Text から期待値を作る方針はよい。ただし marker の意味、描画対象の欠落、caption の固定文まで独立性が及ぶかは別問題である。等価変異は kill 数に含めず除外する。

### should

**B-S1：数量拒否は小さい表示契約に絞り、ID の字形検査を意味検証と呼ばない。**

- **根拠：** P「数値文字列の規則」、B「不変条件」。
- **放置時：** 必要な ID が増えるたびに実装修正が必要になり、一方で自然言語の数量はなお漏れる。
- **是正：** 構造的 ID・日付・節参照と自由文を分離する。自由文には残存数字、限定した数詞・単位の拒否を掛け、意味は本文照合で担保する。

反例は次のとおり。

| 方式 | 過剰拒否 | 過剰許容 |
|---|---|---|
| 現行の明示集合 | 正当な `D2148`、`fig3b`、版識別子 `v3` を拒否する | `a dozen runs`、`applied twice` は列挙数詞に含まれず通りうる。ID を許しただけでは周囲の意味も検証できない |
| 提案の ID 正規表現 | `v3` や `Act 3` は別扱いが必要 | `N30`、`P95`、`MS10` 等、数量を表す字形まで ID として通す |
| 部分一致で例外除去 | — | `fig8.5` や長い token の一部を消す実装は危険。token 全体一致と残存数字検査が必要 |

明示 whitelist は現状それ自体が恒真ではない。むやみに拡張するより、今回の自由文を短く固定し、構造化 ID は別経路で生成する方が最小である。NFKC は小さい処理なので残してよい。完全な自然言語数量判定への拡張は削る。

**B-S2：layout dict は必要。ただし所有関係と衝突関係を分ける。**

- **根拠：** P「layout checkの対象」、C §§9–10、G `check_figure_layout`。
- **放置時：** 親領域と子領域の意図的包含を衝突として拒否したり、複数行文字や横線を誤判定したりする。
- **是正：**
  - 背景 Patch と Text は衝突対象にしない。これは plan が既に適切に区別している。
  - 所有セルの非交差は**兄弟セル同士**に限定する。Act 箱と内部行領域の包含は許す。
  - 複数行 Text は全体 bbox を使う。行間を含む保守的判定なので、そこへ別 Text を入れる設計を避ける。
  - marker は単一点 Line2D と marker padding を含む bbox で検査する。中立の横線は marker と同じ「正の高さ」条件にしない。
  - 200 dpi の実 renderer で検査し、PDF は別途目視する。Agg の通過を PDF の完全保証とはしない。

実寸 fixture の条件は、同じ Figure 寸法・dpi・font 設定、Act の行数1/2/5、A の5セル、B の11セルと空き枠、同じ文字量・改行・凡例定義・脚注・marker を持つこと。短い合成ラベルへの置換では密度を再現できない。変更 fixture は本文照合の試験ではなく、描画への伝達確認として扱う。

font 解決の環境依存は F が明記している。余白を確保し、環境情報を provenance に残す。font の完全 pin はこの依頼には不要。

**B-S3：最小性は test 本数より描画の重複で整理する。新 gate との境界も限定する。**

- **根拠：** B「scope」、C §§9–10、P「生成器」「test」。
- **放置時：** 1枚の生成器が汎用入力検証器へ膨らみ、受入時間と保守対象が増える。
- **是正：** 次の整理を推奨する。

| 要素 | 扱い |
|---|---|
| layout dict、全 Text 検査、marker bbox | 残す。意味を持つ表示の保存前検査に必要 |
| 既存出力拒否 | 残す。凍結物保護として合理的 |
| `--states` | 残してよい。別 snapshot の再現に役立つ小さい機能 |
| NFKC、基本型・重複 ID 検査 | 残す |
| ID ごとの伸び続ける whitelist、定義文を JSON とコード双方に完全複製 | 縮小。意味の正本を重複させない |
| JSON の全異常ケースごとの Figure 生成 | 不要。描画せず parametrized test にまとめる |
| 独立 hash、変更入力、衝突時の無出力 | 残す。成果物の正しさに直結する |

入力検証と保存前 layout check は、**この図の生成を拒否する局所検査**であり、C §9 が要求している。科学的認証・採用・他タスクの進行可否を決めない限り、scope 外の新 gate とは区別できる。指定本文1ファイルのアンカー確認もこの範囲でよい。他の図・全 repo・wave 状態を走査して公開可否を判定する検査へ広げると、新 gate／台帳に近づく。

**B-S4：所要は「数秒」と置かず、実描画回数を予算化する。**

- **根拠：** P「test」「図の要素」、B「P4」。
- **放置時：** 単体 test の想定時間が受入全体の5分予算を圧迫し、未測定の所要が確定事項になる。
- **是正：** 正常・provenance 検査の不要な再描画を減らし、保存は正常 CLI の1回を基本とする。

3200×2300＝736万画素で、RGBA buffer だけで約28 MiB。計画どおり個別 fixture を作ると、正常、衝突2種、出力抑止、provenance、変更入力、CLI で概ね **7〜8回程度の実寸描画**、さらに PNG/PDF 保存時の描画が加わる。所要は概ね

`描画回数 × 1描画時間 ＋ PNG/PDF保存 ＋ import/font初期化`

で決まり、静的には秒数を確定できない。仮に1描画0.5〜2秒なら描画分だけで数秒〜十数秒となるが、これは予算例であり実測値ではない。

`tmp_path` を使い、Figure は例外時も close、CLI 子にも Agg を固定する。失敗時は隠し一時ファイルを含めて確認する。pytest の tmp 領域保持と publisher の一時ファイル清掃は別である。xdist の font cache 競合について、この射影から当 repo の既知障害は確認できないため断定しない。

### nit

**B-N1：provenance checker・docs lint の適合は、指定射影だけでは独立確認できない。**

- **根拠：** B「変更面」、P「JSON」「test／README」。`tools/check_ai_provenance.py`、`tools/check_docs.py`、`tools/plotting/README.md` の本文は今回の射影外。
- **放置時の影響：** 所有分担そのものの矛盾は見つからないが、checker 適合・lint 通過を実証済みとは報告できない。
- **是正：** 親の受入時に現物で確認し、plan の記述は設計上の見込みとして扱う。

brief に記された D95 の分類に従えば、生成器・入力 JSON・test を Codex author、図生成と Markdown を親が扱う分担は整合している。ただしファイル配置だけでは、commit の provenance 要件を満たした証拠にはならない。

また、paper-story が lint 対象外という記載が正しくても、それを `tools/plotting/README.md` に一般化できない。後者の対象判定・予算・構造 lint は未確認であり、新節の分量を確定する前に親が確認する必要がある。

## 総括

**must-fix は4件。**

1. **A-M1：** 数量検査が正常脚注の `§8`・`§0` を拒否する。
2. **A-M2：** 行番号アンカーを項目 ID 形へ変更し、本文内の一意存在を確認する。
3. **B-M1：** state の伝達を Text/provenance だけでなく、実際の色・マーカーで検証する。
4. **B-M2：** 変異を拒否層ごとに分け、別層の赤・等価変異を除く。

**plan v2 に入れる変更は次の5件にまとめられる。**

1. 親 brief と JSON の状態定義を統一し、A-4 の裁定済み、B-9 の適用済み・裁定停止等の限定を補う。
2. 項目 ID アンカーと本文 hash を用い、09-20 との比較対象に限定・人間手番も含める。
3. 構造的参照と自由文を分け、数量検査を正常表示と両立させる。
4. 色・マーカーの独立検査、実寸 layout fixture、単一理由の変異設計を確定する。
5. 描画重複を減らし、所要・PDF表示・checker/lint 適合は親の実測事項として残す。