# 本体論文 (日本語) 方法節と実装対応メモの改稿 (2026-09-21 版) — B-8 の方法を加え、K2 の stock 対照口と B-5 の状態記述を揃えた wave の記録

authority: none / default_effect: no-state-change (可変状態の正本は worklog 末尾と現行 phase doc)

- wave: `worktree-dev-wave-paper-methods-ja-b8` (背景 job 57c44f00、専用 handoff は repo 外の job dir)
- 起点 = 採用時点の local main: `36fb14a3d` (2026-09-21 20:45 JST に fresh worktree、開始 gate `check_wave_startup.py --mode fresh
  --external-handoff` rc=0、main との乖離 0)
- 成果物: [`methods.md`](methods.md) (方法節草稿、6 節) と [`implementation.md`](implementation.md) (実装対応メモ)。前稿
  `output/insights/2026-09-20/paper-methods-ja/` (worklog entry 1749、照合基準 `482f19b88`) の本文 2 file を複製し、下の §3 の
  箇所だけを書き換えた。前稿の `methods.md` / `implementation.md` の bytes は変えていない (sha256 を wave 開始時と記録時に照合、§6)。
  前稿 dir の `README.md` には冒頭に前方 pointer の節だけを足した。**実装面の差分 0** (docs-only)。
- 依頼の逐語 (dev-wave 引数): [`verbatim/request.md`](verbatim/request.md)。

## 0. この wave が主張すること・しないこと

- 主張する: 新稿の B-8 の方法 (発効束・runner v5・校正段・本走段・3 値判定の規則) が、B-8 の事前登録 v1 本文、D2175 / D2186 項 1 /
  D2190 / D2194 項 1 / D2202 の本文、結果稿 `docs/paper-story/results/2026-09-21-b8-final-candidate-longrun-verify.md`、発効記録
  `output/insights/2026-09-21/t2807-b8-effective/README.md` (entry 1791) に対応していること。K2 の同 job stock 対照口が D2187
  (初投入の不成立) と D2205 (pair mode への修復、実機の再投入は未) を区別して書かれ、対照の成立を示唆しないこと。B-5 が
  D2200 項 1 の段階認可 (本走は未認可) として B-8 と分けて書かれていること。
- しない: 2026-09-20 以後の着地全般の総点検 (上の三つ以外の記述は前稿の照合 `482f19b88` を継承し、再照合していない)。
  新しい測定・合成・判定。既存の certified 記録・事前登録・凍結物・論文ストーリーの版・他の草稿の変更。英訳。gate・検査・台帳・
  一般化の追加。方法節への性能値・図の転載 (前稿の裁定を継承)。論文ストーリーの版や同日の草稿 (entry 1801) を出所にすること。

## 1. 段 1 brief (親、20:53 JST。逐語は [`verbatim/s1-brief.md`](verbatim/s1-brief.md) = 専用 handoff の段 1 節)

- 研究前進: 本体論文の方法節に B-8 (D2202 で `pass`) の方法を入れ、結果・要旨・限界の 3 草稿 (entry 1801) と方法節の不整合
  (方法節だけが B-8 を「未発効」と書く) を解消する。
- (P1) 採用時点 = `36fb14a3d`。三つの対象以外は前稿を継承し、再照合しないと本文冒頭と本 README に明記する。
- (P2) B-8 の方法は方法節 §3 (正しさ検証) の検証相の直後に置き、6 節構成を保つ。§6 の B-5 / B-8 の文は B-5 だけにして B-8 は §3 を指す。
- (P3) §2 の「新しい pin の main から旧系列を再開・再投入するのは行われていない」は、K2 の同 job pair の初投入 (pin 前進後の main、
  新しい campaign ID) と食い違って読めるので、K2 についてだけ揃え、他の系列は「前稿の照合時点の記述で、再照合していない」と限定する。
- 段 2・3 は省略 (軽量版。設計択一なし・正しさ防壁に触れない・受理集合不変)。段 6 は一次資料から事実を再抽出する docs-only なので
  `DW-C00` により read-only の独立レビュー 1 本 (2 レンズ) + 焦点再レビュー。
- 条件の再評価: `DW-O08` / `O09` / `O10` は非該当 (新規 path。前稿 dir を参照する test・pin・目録は `orchestrator` / `tools` / `hooks` /
  `output/s1-freeze` / `output/env` の grep で 0 件)、`O11` は削除なし、`O13` は gate の新設なし。

## 2. 稿の作り方

1. 入力: B-8 の結果稿 (全文)、発効記録 (全文)、B-8 事前登録 v1 の §0・§3.2・§4・§5・§6・§7・§10・§12、D2175 冒頭、D2186 項 1、
   D2190 全文、D2194 項 1・2、D2202 全文、D2187 全文、D2205 全文、D2200 項 1、D2172 項 4、D2206 の窓と収集 (B-5 / K2 の状態)、
   worklog entry 1746 / 1754 / 1755 / 1779 / 1790 / 1791 / 1795 / 1801 (archive の該当 file)、K2 pair の初投入 insight
   (`output/insights/2026-09-20/t2795-k2-pair-attempt/README.md` §0) と修復 insight (`output/insights/2026-09-21/t2795-pair-repair/README.md` §0)。
2. 実装アンカーの照合 (三つの対象の行だけ): pair mode は `orchestrator/campaign/loop.py` の `authorization_session` /
   `_AuthorizationSession` と、`_authorize_measurement` / `run_campaign` の keyword-only 引数、`p3_s4_loop.py` の `main` の
   pair mode 分岐 (`--run-iteration` と `--stock-control` の併用)、job body の `IZANAGI_S4_STOCK_CONTROL=1` の拒否条件を
   `36fb14a3d` で確かめた。B-8 の発効束 JSON・事前登録・template patch は repo 内の実在を確かめ、runner v5 は repo 外であることを
   発効記録 §1 と D2190 項 1 で確かめた。
3. 執筆: 前稿 2 file を複製し、methods §2 (K2 対照口の 2 段落と pin 前進の段落の末尾)、§3 (B-8 の 9 段落と判定の 3 項)、§6 (B-5 と
   B-8 の段落)、implementation の冒頭・正本の優先関係・表 2 行・読み分け 3 行・境界節・確認点を書き換えた。
4. 親の自己点検 (段 6 前): 相対リンクの解決 (README 以外 0 件不達)、本文中の repo 相対 path の実在 (不達は schema 名 4 件と前稿から
   継承した短縮表記 1 件だけ)、新稿の「未発効」「本稿の時点」「1 job も」の走査。

## 3. 前稿から変えた点

「型」は、前稿の記述が前稿の照合基準 `482f19b88` の時点で既に偽だったか、その後の着地で古くなったかを示す。

| 箇所 | 前稿の記述 | 新稿 | 根拠 | 型 |
|---|---|---|---|---|
| methods §3 (新設の段落群) | B-8 の方法は無い (§6 で「未発効」とだけ書く) | 登録と対象・定義、発効と発効束、runner v5、校正段、本走段、3 値判定、2026-09-21 の実施、限定 | 事前登録 §0 / §3.2 / §4.1 / §4.2 / §5 / §6.1〜§6.4 / §7 / §12、D2175、D2186 項 1、D2190 項 1〜5、D2194 項 1、D2202 項 1〜4、結果稿 §1〜§4、発効記録 §1〜§6 | 後の着地 (発効 commit `624c84986` は 2026-09-21 08:42 JST) |
| methods §2 (K2 対照口)、implementation 境界節の B-4 段落末 (「K2 の stock 対照口の追加と修復も」) | 「本稿の時点でこの口は実装済みであるが、1 job も投入していない」(境界節は「追加も」) | 修復前の 2 process 形の初投入 1 job と不成立 (D2187)、pair mode への修復 (D2205)、実機の再投入は未、同 job の stock 対照は未取得 | D2187、D2205、entry 1754 / 1795、両 insight §0 | 後の着地 (初投入は `482f19b88` より後の main `6a3e158` の submit-tree から。D2187 の main 着地は fold `7baf3f375`、2026-09-20 20:42 JST) |
| methods §2 (pin 前進の段落の末尾) | 「新しい pin の main からそれらを再開・再投入するには…整合が要り、本稿の時点では行われていない」 | 「前稿の照合時点ではいずれも行われておらず、本稿はその後を再照合していない」+ K2 の pair は前進後の superproject から CCBench を driver の旧 PIN `511c9538` へ checkout して (D1777 の手順)、新しい campaign として投入された | t2795-k2-pair-attempt README §1 (submit-tree `6a3e15809`、campaign `p3-s4-loop-s4-autonomous-b24749ae` = 新 ID・新 policy epoch、候補の `ccbench_commit` = `511c9538`) | 表記の限定 ((P3)。旧巡の campaign の再開ではないので、前稿の文が偽だったとは主張しない) |
| methods §6 (B-5 / B-8) | 「B-5 と B-8 は…事前登録 v1 が作られたが、いずれも未発効」 | B-8 は発効し 3 値判定まで済んだ (§3 を指す)。B-5 は未発効、試走は完走 (主標本外)、D2200 項 1 は段階認可で本走は未認可 | D2194 項 1、D2202、D2158、D2172 項 4、entry 1779、D2200 項 1、D2206 | 前稿の照合時点では真。B-8 の発効、B-5 の試走の完走 (entry 1779)、D2200 は後の着地 |
| implementation 境界節 | 「B-5 と B-8 の事前登録 v1 は未発効で、対応する runner・生成器は実装されていない」 | B-8 は発効・判定済み (repo 外の runner v5)。B-5 は未発効、driver と部品は着地、試走は完走、本走は段階認可のみ | 同上、D2190 | 前稿の照合時点では真 (B-5 の driver の初出は `c41cfb09f` = 2026-09-20 20:34 JST、D2190 の main 着地は fold `7c0a1c63a` = 同 22:54 JST で、いずれも後) |
| implementation 表 | K2 対照口の行は「0 件 (結線のみ)」 | K2 行を pair mode のアンカーと初投入の不成立・修復後の実機投入 0 件へ更新。B-8 行を追加 | 上と同じ | 後の着地 |
| implementation 読み分け | — | B-8 の `pass`、K2 pair の初投入、pair mode の結合検査の緑の 3 行を追加 | 上と同じ | 追加 |
| methods §1 / §5、implementation の A-1 行・境界節の兄弟 wave の文 | 「本稿の時点で…」(兄弟 wave の文の字面は「本稿は稼働中の兄弟 wave…」) | 「前稿の照合時点 (`482f19b88`) で…」(中身は再照合していない) | (P1) | 表記のみ。新稿の採用時点を指すと読めて偽になりうる文を、継承の範囲へ戻した |
| methods 冒頭、implementation の冒頭・正本の優先関係 (story の項の「本稿の基準」→「前稿の基準」と出所を制限する 1 文、stale 注記の項の参照先「本稿末尾」→「下の『実走・契約・未了の境界』節」と「(前稿から継承)」、B-8 / K2 / B-5 の出所 3 項)・2 表の見出し・境界節の「story 未反映の着地」の見出しと「揃えた着地」の段落・「飛躍しない」の拡張・確認点節 | 前稿の版・照合基準を書く | 新稿の版・採用時点・継承範囲・出所を書く | (P1)、依頼の出所規則 | 表記の修正と追加 (前稿の記述の真偽は変えない) |
| implementation 確認点節の継承段落のリンク | `[README](README.md) §5` (前稿 dir では前稿 README の must-fix 表を指した) | `[前稿 README](../../2026-09-20/paper-methods-ja/README.md) §5` | 段 6 の should-fix 4 | 複製で指す先が変わった表記の修正 |

## 4. 段 6 独立レビュー (read-only、1 本、2 レンズ) と親の裁定

- **代替の明記:** 本来は Codex の read-only 子が担う。Codex は利用上限 (復帰 2026-09-26 19:35 と表示。同日の entry 1801 / 1802 と
  [T-2833] の wave が実測) のため本 wave では起動せず、同じ prompt を Claude の独立 context の子 (Agent、subagent_type = Plan で
  Edit / Write を持たない、model = opus) に渡した。**同系統モデルなので Codex と同等の独立性は主張しない。** 子の終了後の作業ツリーの
  差分は、親の fix の編集と親が置いた verbatim 2 file だけだった (`git status` と `git diff` で確認)。
- prompt は [`verbatim/s6-review-prompt.md`](verbatim/s6-review-prompt.md)、報告の逐語は [`verbatim/s6-review.md`](verbatim/s6-review.md)。
  対象は commit `784db3f02`。所要 818 秒・道具 68 回 (完了通知の値)。
- **結果: GO** (must-fix 0 / should-fix 4 / nit 9 / refuted 24)。判定集合 30 枠を本走の条件へ丸ごと帰属させる文は、3 file と phase3 の項の
  全数走査で 0 件 (refuted)。

| # | 所見 | 裁定 | 反映 |
|---|---|---|---|
| S1 | K2 pair の初投入を「pin 前進後の main から」と書くのは superproject についてだけ真で、CCBench は driver の PIN `511c9538` へ checkout して走った | real・採用 | methods §2 の 2 箇所と implementation の K2 行に「前進後の superproject から、CCBench を driver の PIN へ checkout」を書いた (手順の出所 D1777 は methods §2 の K2 段落に明記) |
| S2 | bench 失敗の規則が本走段にしか無く、校正の bench 失敗でも pass と読める | real・採用 (規律 2 の向き) | 校正段に「校正・本走を問わず pass を妨げ、校正で出れば本走を投入しない (§5、D2190 項 3 (b))」、本走段と未確定の列挙に「校正・本走を問わない」 |
| S3 | 実施結果 (`pass`) の出所に D2202 を挙げたが、D2202 は手順で判定値を含まない | real・採用 | 出所を「結果稿 §3、発効記録 §3〜§5、entry 1791。実施手順は D2202」へ (methods §3 の実施段落、implementation の B-8 行と境界節の B-8 文の 3 箇所。同型の残り 1 箇所は焦点再レビューの F1 で直した) |
| S4 | 継承段落の `[README](README.md) §5` が新 dir では新 README (§5 = 限界) を指す | real・採用 | 前稿 README へ張り替えた |
| N1 | D2175 が固定したのは対象の 2 案と推奨 | real・採用 | 「対象の 2 案 (推奨は案 A)」 |
| N2 | 校正 walltime と hard timeout は承認の記録でなく `effective` 節の値、D 番号を振った fold が抜け | real・採用 | `effective` 節の内訳として書き直した |
| N3 | 「各 1 値」は D2190 項 2 でなく D2202 項 2。sha 不一致・判定集合外の混入が未確定の列挙に無い | real・採用 | 出所を分け、未確定の列挙に足した (D2190 項 3 (c)) |
| N4 | 結合検査の緑が実 build・bench を含むと読める | real・採用 | methods と読み分け表に stub の範囲を添えた |
| N5 | 事前登録 §13 の件数の併記 (未完走・規約不適合) が無い | real・採用 | 「校正の未完走・bench 失敗・規約不適合はいずれも 0 件」 |
| N6 | §6.1 項 2 の「校正の未完走は pass を妨げないが件数と保全先を開示」が無い | real・採用 | pass の項に足した |
| N7 | 実施事実の出所に実施記録を先に置く | real・採用 | methods の K2 に entry 1754 と pair-attempt insight §1、implementation の B-8 の出所を実施記録先頭へ |
| N8 | README §3 の表に載っていない書換えがある | real・採用 | 表に 2 行を足した |
| N9 | 発効束 JSON の作り方は方法節には細目で、1 文へ圧縮できる | 不採用 | 依頼が B-8 の方法の要素として「発効束」を名指ししている。N2 の訂正で正確さは保った |

### 4.1 焦点再レビュー (read-only、1 本、`DW-O16`)

- 1 巡目と別の独立 context の Claude 子 (同じく Plan、model = opus)。対象は fix commit `5326ad4ab`、所要 537 秒・道具 45 回 (完了通知の値)。
  prompt は [`verbatim/s6-focus-prompt.md`](verbatim/s6-focus-prompt.md)、報告の逐語は [`verbatim/s6-focus.md`](verbatim/s6-focus.md)。
- **結果: GO。** 対応表は closed 11 (S1〜S4、N1〜N7)・partial 1 (N8)・不採用が妥当 1 (N9)、regressed 0。新規は nit 6 件で、must-fix 0。
  親が書いた派生値 (所見の件数、B-8 の 9 段落と 3 項、「型」の commit と時刻、「本稿の時点」の 2 / 4 箇所) は子が現物から数え直して一致した
  (S3 の「2 箇所」だけ不一致 = F6)。3 巡上限のうち 2 巡目で閉じた (新規 nit は親が直し、3 巡目は起動していない)。

| # | 所見 | 裁定 | 反映 |
|---|---|---|---|
| F1 | implementation 境界節の「揃えた着地」の段落が、S3 と同型で D2202 を `pass` の出所に並べる | real・採用 | 「発効は D2194 項 1。判定は結果稿 §3・発効記録 §5・entry 1791、手順は D2202」 |
| F2 | methods の「受理する sha256 を各 1 値で明示して渡した」は実施事実なのに出所が D だけ | real・採用 | 「手順は D2202 項 2、実施は発効記録 §3.1・§5」 |
| F3 | bench 失敗の規則に D2190 項 3 (b) の限定 (開始して失敗した bench に限る、打ち切りの `not_run` は数えない) が無く、本走段の括弧に D2190 項 3 (b) が無い | real・採用 (誤読は厳しい側で、規律 2 を緩める問題ではない) | 校正段に限定を足し、本走段の括弧に D2190 項 3 (b) を足した |
| F4 | implementation の B-8 行に事前登録 §13 の件数の併記 (未完走・規約不適合 0) が無い | real・採用 | 「校正の未完走・bench 失敗・規約不適合は 0 件」 |
| F5 | README §3 に、implementation 境界節の「追加と修復」と、stale 注記の項の参照先の書換えが無い (N8 の partial) | real・採用 | K2 行と表記修正の行に足した。兄弟 wave の文の字面も併記した |
| F6 | README §4 の S3 の「2 箇所」は実際は 3 箇所。S1 の D1777 は methods の K2 段落にだけある | real・採用 | 本表の S1・S3 行を直した |

## 5. 限界

- **継承部分の未再照合:** 三つの対象以外の記述は前稿の照合 `482f19b88` のままであり、その後の着地で古くなった記述を含みうる。
  本 wave の作業中に目にした例として、A-1 sized の attempt-0002 は認可 record 経由で投入され完走した (entry 1755)。新稿の methods §5 と
  implementation の A-1 行は、その事実を書かず「前稿の照合時点では投入 0 件」の表記に留めた。新 pin の main から旧系列を再開するための
  整合も 2026-09-21 に系列ごとに実測されている (entry 1790、D2201)。いずれも依頼が総点検を scope 外とした範囲なので本文は直していない。
- **B-8 の runner v5 は repo 外である。** 新稿は runner の挙動を D2190 と発効記録の記述から書き、runner の source を本 wave で読み直していない。
- **段 6 は Codex の独立レビューを受けていない** (§4)。Claude の子 2 本 (review・focus) は同系統モデルである。

## 6. 検査 (記録 commit 前、親が login で実走)

- 前稿本文の不変: `methods.md` `47ff1403…d4f5fd6a`・`implementation.md` `705b5c01…6aa79b` は wave 開始時 (20:52 JST) と記録時で一致。
  前稿 `README.md` は冒頭の前方 pointer の分だけ変わる (開始時 `22b8d925…`)。
- `python3 tools/check_docs.py`: 違反なし (草稿 commit 前・fix 後の各回)。
- 相対リンク: 3 file のリンクはすべて解決する。本文の repo 相対 path は、schema 名 4 件と前稿から継承した短縮表記
  `verify-phase-adopted-backoff/README.md` 1 件を除いて実在する。
- 三軸語の走査 (`python3 -m orchestrator.campaign.s8b_holdout_freeze search`): rc=1 で、hit は rr80 / rr20 とも既存の 3 件
  (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の journal / manifest / result、entry 1787・1801 と同じ)。
  本 wave の file の hit は 0 件。
- `git diff --check`: 各 commit の staged 差分で空。
- 全史 provenance 監査 (`python3 tools/check_ai_provenance.py`): 草稿 commit `784db3f02` の後に 12,443 件・新規違反なし。
- 受入全走と land は記録 commit の後に走るので、その結果は本 README と worklog fragment には書かない。受領証と log は wave の
  artifact dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-methods-ja-b8/` に残る。
