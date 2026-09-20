指定資料はすべて読めた。静的照合のみ実施し、書き込み・作図・pytest は行っていない。**must-fix は1件：Act 行の内部 ID の表示。状態 JSON の誤写・判定の過大化は見つからなかった。**

以下、本文の行番号はすべて凍結版 `docs/paper-story/2026-09-19.md` を指す。

## must-fix

**A-M1：Act の8行から内部 ID の接頭辞を除く。**

- **根拠：** provenance の `act1-evaluator`〜`act3-descriptive` の8項目。生成器244行が `item["id"] + ": " + item["label"]` を描くため、`act1-evaluator:` 等が実表示されている。作図規約 §5 の短い図中用語・内部識別子を露出させない趣旨に反する。厳密には軸ラベルではないが、この模式図で内部 ID を読者に見せる必要はない。
- **放置時：** PNG/PDF と provenance の実表示文字列に、本文の項目名ではない内部識別子が8個残る。
- **是正：** **生成器**244行は `item["label"]` だけを見出しとして描き、副ラベルは維持する。351〜353行の期待文字列も同時に直す。`drawn_items.id`・領域所有 ID はそのまま残す。**README** §5 の説明も「Act 行は短い名前＋副ラベル、証拠項目は項目 ID＋短い名前＋副ラベル」へ合わせる。

証拠項目の `A-1`〜`B-10` は本文の項目 ID なので残してよい。`Act 1`〜`Act 3` も本文の幕構成を示す構造参照として問題ない。

## should

**A-S1：README の「同じ配置が得られる」という無条件の保証を狭める。**

- **根拠：** README 草稿「再現できるのは『値』であって『バイト列』ではない」。生成器198〜209行・245〜251行は font の実測幅・高さから折返しと後続行の位置を決める。草稿自身も matplotlib の版と font 解決への依存を認めている。
- **放置時：** README が、同じ入力だけで環境をまたいだ配置一致まで保証する説明になる。実際には改行・配置が変わり、layout check が拒否する可能性もある。
- **是正：** **README** を「再現対象は記録された状態と表示内容。配置は描画環境に依存し、保存前に検査する。byte 一致は保証しない」へ変更する。見出しの「値」も「状態・表示内容」へ直す。

## nit

**A-N1：fig9 節との書式一致と、着地後照合 test の不存在は、今回の射影だけでは独立確認できない。**

- **根拠：** 指定された図 README は1〜30行で、fig9 の詳細節を含まない。test 本文も射影外。S4 の試験計画には CLI 出力 hash の照合があるが、これは着地済み図の継続照合とは別である。
- **放置時：** 図・JSON・provenance が変わるとは言えない。README の当該説明だけが未検証事項として残る。
- **是正：** **README** の確定時に親が fig9 節と test 本文を照合する。本レビューを、それらまで確認済みとする根拠にはしない。大文字 placeholder は所見に数えない。

## 逐語照合：証拠16項目

4状態は本文の日本語状態語そのものではなく、S4 で定義した編集分類である。以下の「一致」は、その分類と副ラベルの意味が本文に一致することを示す。

| ID | JSON `state` / `sublabel` | 本文の対応・判定 |
|---|---|---|
| A-1 | `uncertified` / `descriptive; non-certifying; fulfilment undetermined; reauthorization requires human action` | 2467〜2470、2502〜2505行：「充足は未判定」「非認証 lane」「descriptive」「再認可と formal 化はユーザー手番」。**一致**。審議中という判定を足していない。 |
| A-2 | `obtained` / `observed-positive; limitations retained` | 2429〜2445行：取得済み判定は不変、限定あり、`observed-positive` の執筆材料。§0 85行にも判定語あり。**一致**。 |
| A-3 | `obtained` / `settled; rule only; not evidence` | 2420〜2424行：報告規則が決着、新測定・認証更新ではなく証拠に数えない。**一致**。 |
| A-5 | `not-obtained` / `unfulfilled; Pegasus does not establish separate-boot reproduction` | 2527〜2535行：未取得・未充足、Pegasus の結果を別 boot 再現へ読み替えない。**一致**。 |
| A-6 | `obtained` / `reject; limitations retained` | 2451〜2455行：取得済み、限定あり、性能判定は `reject`、正しさ証拠の欠落ではない。**一致**。 |
| A-4 | `awaiting-ruling` / `adoption decided; chain not landed; inactive; human action pending` | 2861〜2864行：採用裁定済み、chain 未取り込み、A/X は人間手番、未発効。**一致**。凡例が human action を含むため、採用自体が未裁定とは読ませていない。 |
| B-1 | `obtained` / `not met` | 2550〜2552行：測った比較判定は不成立。**一致**。「判定がある」という obtained の定義が必要で、凡例・caption に保持されている。 |
| B-2 | `not-obtained` / `not run; layered blockage` | 2555〜2560行：未実走、閉塞は層。**一致**。 |
| B-3 | `not-obtained` / `not completed; authority absent` | 2586〜2590行：未完走、最上流は権限不在。**一致**。未実走へ強めていない。 |
| B-4 | `not-obtained` / `not run; descriptive-only; specs frozen; eligible precursor absent` | 2623〜2625行：未実走、記述統計限定、spec 凍結、適格 precursor なし。**一致**。 |
| B-5 | `not-obtained` / `not obtained` | 2698〜2702行：未取得。label の予算を揃えた生成器比較も、因果的必要性から狭めた主張に沿う。**一致**。 |
| B-6 | `not-obtained` / `loop exercised; leak control incomplete` | 2705〜2718行：ループ実走はあるがリーク制御は未完備。**一致**。部分実走を消していない。 |
| B-7 | `uncertified` / `materials complete; not promoted to requirement fulfilment` | 2719〜2720行：材料はそろったが要件充足へ昇格させない裁定。**一致**。材料内の correctness 認証を取り消していない。 |
| B-8 | `not-obtained` / `not obtained` | 2736〜2737行：未取得、独立検証相を持たない。**一致**。 |
| B-9 | `uncertified` / `screening support scoped; deep check stopped by ruling; secondary view applied, non-certifying` | 2738〜2761行：(a) 対応済みだが一般的完全性は主張しない、(b) 本体強化は裁定停止、(c) 二次 view 適用済み・非 certifying。**一致**。 |
| B-10 | `uncertified` / `grid and tail judged; performance uncertified; not closed` | 2765〜2769行：grid・tail 判定あり、項目は未閉鎖。性能未認証は151〜153行が明示。**一致**。 |

各 `source_anchor` はすべて `§8 <当該ID>` で正しい項目を指す。A-4 が B 群内に置かれる点も2861行と一致する。全16アンカーについて、指定節内の見出しがそれぞれ1件であることも読み取り処理で確認した。

## 逐語照合：Act

| 行 | JSON `state` / `sublabel` | アンカー・本文との照合 |
|---|---|---|
| `act1-evaluator` | `obtained` / `complete` | `§0 act 1`、80行：「信頼できる評価器」「完了」。**一致**。 |
| `act2-hypothesis` | `obtained` / `falsified` | `§0 act 2`、81〜82行：当初の探索仮説を反証。**一致**。 |
| `act2-value` | `obtained` / `relocated to synthesis` | `§0 act 2`、81〜82行：価値は探索空間の外への合成。**一致**。 |
| `act3-claim` | `obtained` / `not met` | `§8 B-1`、2550〜2552行。§0 83〜84行とも**一致**。 |
| `act3-scope` | `null` / `lifted; preparation underway` | `§0 item 3`、123〜134行：Silo 限定解除、準備着手。**一致**。認証取得へ分類していない。 |
| `act3-mechanism` | `null` / `advanced; claim remains unmet` | `§0 act 3`、83〜84行：機構は進展、主張は不成立。**一致**。 |
| `act3-formal` | `obtained` / `A-2 observed-positive; A-6 reject; T-1998 accepted` | `§0 act 3`、85〜87行：判定の組が**一致**。A-1 を正式判定へ加えていない。 |
| `act3-descriptive` | `uncertified` / `completed; non-certifying` | `§0 item 1`、92〜105行：attempt 完走、非認証のまま。**一致**。 |

Act 見出しの `progress` も、第1幕・第2幕の `complete`、第3幕の `in-progress` が80〜87行と一致する。見出しのアンカーは順に `§0 act 1/2/3`。Act 見出し・行の全アンカーも、それぞれ見出し1件に対応している。

**段3 A-S1 の指定修正7件はすべて反映済み。** A-1 の充足未判定・人間手番、A-4 の採用裁定済み、A-5 の別 boot 限定、B-4 の descriptive-only、B-7 の未昇格、B-9 の限定・裁定停止・適用済み、Act 3 A-1 行の completed が JSON と `drawn_items` に残っている。

## 数量・caption・正しさ境界

- **測定値・件数・反復数の混入はない。** 凡例定義にも数量はない。
- 数字入り token は存在する。証拠 ID、`T-1998`、Act 番号、脚注・caption の版日付・節番号・図番号は、S4 が許した宣言 ID または構造参照である。
- それらに加えて、未宣言の `act1-evaluator:` 等が8個表示される。測定数量ではないが、内部 ID の漏出として **A-M1** で除く。
- caption は README 草稿と provenance で同一。生成器の固定 template とも整合する。
- `obtained` を主張支持と同一視せず、B-1 の不成立、A-6 の reject、A-3 の規則という限定を保持している。
- `This figure summarizes recorded statuses; ...` と `Statuses are recorded, not evaluated, here.` は、この図が行わない判断を説明する文であり、正しさゲート全体の不変を検証・保証した文とは読まない。認証・認可を与える文もない。
- identity 修正で A-2/A-6 を遡及的に強めない文は、172〜174、2435〜2438行と一致する。規律7の扱いは正しい。

なお、provenance の入力 JSON・本文・生成器の SHA-256 は、今回読んだ現物とすべて一致した。

## README 草稿の確認

| 対象 | 結果 |
|---|---|
| A-5「投入2度と balanced 生値1走」 | 2536〜2539行と一致。ただし本文の順序は、測定前停止の投入2度に続き、後日 balanced 生値取得。後者は finalizer 前失敗・主張へ転用不可で、草稿も要件充足とはしていない。 |
| B-6「K2 の2巡が閉じた」 | 2705〜2718行と一致。リーク制御未完備の限定も保持。 |
| A-4「D2120 項2」「A/X は人間 commit」 | 135〜146行と一致。裁定済みと未発効を区別している。 |
| 27項目＝Act 見出し3＋Act 行8＋証拠16 | JSON・provenance の実数と一致。凡例・脚注まで含めた全 Text 数という意味ではない。 |
| 拒否条件 | 生成器の key/schema/state/ID/anchor/path/自由文/prefix/既存出力/layout 検査と対応。数量検査は固定語集合等の字句検査であり、任意の自然言語数量を検出するものではない。 |
| 4状態の説明 | JSON 定義と一致。obtained の非支持判定、uncertified の項目単位、人間手番、部分実走を含む未取得の区別も適切。 |
| proof chain | 入力・生成器 hash、実表示27項目、caption の説明は現物に対応。実走結果・test・変異結果は placeholder の確定時に親が裏付ける事項。 |
| 行番号参照・可変状態 | 草稿には本文への行番号参照はない。状態は09-19版 snapshot として明示されており、稼働中の可変状態の台帳にはなっていない。 |
| 凍結物の書換え | 示唆なし。旧図・本文を残し、状態変更時は別 JSON・別 filename とする。 |
| fig9 書式・着地後照合 test の不存在 | **A-N1：独立未確認**。生成時の hash 照合と着地後の照合を区別する説明自体は妥当。 |

09-20版以降との整合手順も問題ない。稼働中 wave を数えない引用は2341〜2343行に対応し、比較対象を enum だけでなく限定・未了理由・人間手番まで広げている。入力 JSON の保持を「方針」、PNG/PDF/provenance の保持を「凍結規則」と分ける点も、図 README 冒頭と一致する。09-20版の状態自体との一致は、今回の射影からは判定していない。

## 総括

**must-fix：A-M1 の1件。**

fix 子へ渡す変更は、**Act 行の表示から内部 ID 接頭辞を除き、生成器の `_drawn_items` 期待文字列も同期すること**。内部 ID・状態 JSON・証拠項目 ID・副ラベルは維持する。親は README §5 の説明と、修正後の図・provenance を整合させる。凍結済み成果物への修正は別 filename とする。

併せて **A-S1：README の配置再現保証を限定**する。状態16項目とAct 8行、各アンカー、caption の判定境界について、追加の修正は不要。