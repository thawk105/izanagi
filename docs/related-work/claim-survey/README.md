# claim-survey — 主張軸別の調査状態の凍結スナップショット

**規則の正本は `docs/related-work/README.md` の「7.7 主張軸別の調査状態と、不在主張の成立条件」である。**
本ディレクトリはその規則を当てた**時点ごとの実測**を凍結して束ねる。
`docs/related-work/literature-map/` (監査前の生データ)、`docs/related-work/notes/`
(個別論文の精読記録)、`docs/related-work/shinka-deepdive.md`
(単発の深掘り) とは役割が違い、ここに置くのは**軸を横断した棚卸しと監査記録**だけである。

## 読む時

論文の positioning を書くとき、関連研究を追加したとき、主張軸を改訂したときだけ読む。
日常セッションのブート対象にしない (D35)。

## 決まりごと

- **各ファイルは日付付きの凍結物であり、書いた後は上書きしない。** 内容を更新したいときは
  新しい日付のファイルを足す (`docs/paper-story/` と同じ原則)。
- **各ファイルは入力 path、入力 commit、入力 digest の所在、文献 cutoff、作成日を持つ。**
  その文書だけで「いつの何から導いたか」を復元できるようにする。
- **現在値をここへ書かない。** 進行中の可変状態 (どの軸が今どの段階か、未充足の残件) の正本は
  `docs/worklog.md` の末尾エントリである。本 README も一覧以外の状態を持たない。
- ここに置いた判定は `docs/related-work/README.md` と同格の正本ではない。
  矛盾したら `docs/related-work/README.md` が勝つ。

## 一覧

| 日付 | ファイル | 中身 |
|---|---|---|
| 2026-08-26 | `2026-08-26-inventory.md` | 5 つの主張軸 × 検索記録の成熟度の初回棚卸し。軸 1 の分類 pilot、軸 1 の主張履歴を含む。**§3.1 の 29 行の現行値と C/D 欄の由来は `2026-08-27-axis1-pilot-cd-provenance.md` が持つ** |
| 2026-08-26 | `2026-08-26-correction-5-audit.md` | Polyjuice / CCaaLF→NeurCC の特徴づけについて、paper-story 最新版・`docs/related-work/README.md` 7.1・`docs/related-work/literature-map/` の Markdown と CSV の四者を突き合わせた監査 |
| 2026-08-26 | `2026-08-26-cir-cvn-adjudication.md` | `2604.09318` (CIR+CVN) の `要裁定` を一次資料で解いた記録。軸 1 への接地判定と、`docs/paper-story/` §3 の 1 が落としてはならない 2 つの限定 |
| 2026-08-27 | `2026-08-27-axis1-search-preregistration.md` | 軸 1 の 7.7.4 事前登録。索引 3 つの実測、共有の暦境界による cutoff、6 枝 × 3 索引の query catalog、完走述語、停止条件、母集合の外。**登録であって実行ではない** |
| 2026-08-27 | `2026-08-27-axis1-adjudication-3.md` | 軸 1 分類 pilot に残る `要裁定` 3 件 (`2404.13359` / `2512.18746` / `2605.22721`) を一次資料で解いた記録。A の読み方の明示、件数保存則、`docs/paper-story/` §3 の 1 が落としてはならない 3 つの限定 |
| 2026-08-27 | `2026-08-27-axis1-pilot-cd-provenance.md` | 軸 1 分類 pilot 29 行の**現行値の統合表示**と、C/D 欄の証拠階層 (一次資料 4 行 / 監査前要約 25 行)。集計と行間比較の恒久禁止 (D1156)。新しい判定はしていない |
| 2026-08-27 | `2026-08-27-axis1-search-execution.md` | 事前登録した軸 1 検索の**実行記録**。枝ごとの完走判定、control、未完走の理由の分類、`AX1-Q6@dblp` の宣言的除外 (D1155)。生証拠は `output/insights/2026-08-27_t1969-axis1-search-execution/`。**軸 1 は `未完走` であり成熟度は `RW1` のまま** |
| 2026-08-27 | `2026-08-27-axis3-search-preregistration.md` | 軸 3 の 7.7.4 事前登録。事実層と仮説層の二層分類、74 語 10 枝、arXiv / OpenAlex の完全 query と DBLP の server 側連言 1523 本、typed AST による期待 echo 照合、補助探索の完走述語、query 単位の失敗境界、母集合の外、`RW3` 前に閉じるべき blocking 5 件 (B1〜B5) と non-blocking 4 件 (N1〜N4)。**登録であって実行ではない。軸 3 は `RW0` のままである** |
| 2026-08-27 | `2026-08-27-axis3-index-measurements.md` | 軸 3 の事前登録に用いた索引実測。arXiv の 6 syntax class、OpenAlex の echo 正規化とレート制限、DBLP の前方一致連言・三分ハイフン・ページング・1 対の集合等価性。**構文事実の観測であって本検索ではない** |
| 2026-08-28 | `2026-08-28-axis1-a-reaudit.md` | 軸 1 の A 欄の再監査 |
| 2026-08-29 | `2026-08-29-axis1-search-amendment.md` | 軸 1 の検索契約の改訂 (事前登録)。旧契約と旧実行記録の bytes は変えていない (D1207 / D1208) |
| 2026-08-29 | `2026-08-29-axis1-search-catalog.json` | 軸 1 の改訂契約に対応する query program (機械可読 catalog) |
| 2026-08-30 | `2026-08-30-axis1-search-execution.md` | 改訂契約による軸 1 の**実行記録**。生証拠は `output/insights/2026-08-29_t2033-axis1-retake/`。**軸 1 は `未完走` であり成熟度は `RW1` のまま** |
| 2026-09-01 | `2026-09-01-axis3-search-amendment.md` | 軸 3 の検索契約の改訂 (事前登録)。旧 1543 主 query ID を supersede し、arXiv 360 年 shard・OpenAlex 10・DBLP 1523 の計 1893 主 query と非主 229 stream を後継化する。旧登録 §7.1 条件 1 を 3 索引すべてへ適用し、registration seal の受理 closure を実行器 source 2・schema 4・凍結入力 2 に限る。**登録であって実行ではない。軸 3 は `RW0` のままである** |
| 2026-09-01 | `2026-09-01-axis3-registration-preflight.md` | 軸 3 の **network-zero な registration preflight の実行記録**。2122 行 catalog と registration seal を発行し、blocking のうち B4 (規範 parser の正例 7・負例 6) だけが閉じた。**外部 request は 1 本も出していない。軸 3 は `RW0` であり、世界の不在は支持しない** |
| 2026-09-02 | `2026-09-02-axis1-search-amendment.md` | 軸 1 の検索契約の**再改訂** (事前登録)。OpenAlex の完走条件 1 を `oqo` の順序非依存な比較へ改め、登録 epoch を `AX1-20260902-E1` へ、全 query ID を新規化する。旧 epoch の走行は `未完走` に固定し全枝を再実行する (D1432、旧改訂 §8 の意味的 amendment 条項)。**登録であって実行ではない。軸 1 は `RW1` のままである** |
| 2026-09-02 | `2026-09-02-axis1-search-catalog.json` | 軸 1 の再改訂契約に対応する query program (機械可読 catalog) |
| 2026-09-03 | `2026-09-03-sysinsight-adjudication.md` | `2603.22708` (SysInsight, PVLDB 19(6) 2026) を一次資料で解いた記録。7.1 の knob 系譜エントリが持つ 2 文の裁定 — 「CC のロジックには手が届かない」は介入面でしか成立せず待機は読解されている / 「P2-5 と同方向を指す外部証拠」は無限定には残せない。7.11 倍が GPTuner に対する数字であって専業 ML/RL に対する数字ではないことの確定、落としてはならない 3 つの限定、軸 1 `除外` / 軸 2 `部分接地` / 軸 3 `部分接地` (狭い能力についてだけ `競合`) の判定を含む。**新しい検索ではないので軸 1 は `RW1` のまま。pilot 29 行も動かさない** |
| 2026-09-03 | `2026-09-03-axis1-search-execution.md` | 再改訂契約による軸 1 OpenAlex の**1 窓目の実行記録**。条件 1 は取得した全 93 頁で `可` になり、順序の差で落ちた頁はゼロ。塞ぎは条件 5 (`distinct_work_id_total_mismatch`) へ移り、**同じ request を同日に 2 回投げて判定が両方向に反転した** (U11 の実データ初観測)。78 leaf のうち完走 1・pass 2 待ち 8・条件 5 で未完走 3・未走 66。生証拠は `output/insights/2026-09-03_t2090-axis1-openalex-window1/`。**軸 1 は `未完走` であり成熟度は `RW1` のまま** |
| 2026-09-03 | `2026-09-03b-axis1-cond5-confirmations.md` | D1331 が要求した 3 確認を、2026-09-03 の凍結 bundle のオフライン解析で完了した記録 (**新規 HTTP 0 件**)。(a) 返却されない別 ID は実在する — 同じ登録 request の独立 2 走で返却集合が各 1 件ずれ、`W7168152262` と `W7161158986` を名指しできる。(b) 集合は安定しない。(c) 申告総数は 1 走の全頁でも 2 走間でも動かず、動くのは関連度スコアと並び順である (共通 snapshot 識別子が無いため索引側 snapshot drift そのものは判断不能)。**条件 4 と条件 5 はどちらも改訂しない** — 判断は「1 走の返却集合を完全とみなせない」の 1 点だけに依存し、単一機序の確定にも登録第 2 走の digest にも依存しない。凍結実行記録 §4 の「申告総数も動く」を訂正する。**既存の条件 5 不成立へ免除を与えない。**U11 の解決と条件 4/5 の追認はユーザー裁定に残る。生証拠は `output/insights/2026-09-03_t2258-axis1-cond5-confirmations/`。**軸 1 は `未完走` であり成熟度は `RW1` のまま** |
| 2026-09-05 | `2026-09-05-axis1-search-execution.md` | 再改訂契約による軸 1 OpenAlex の**2 窓目の実行記録**。独立 2 走目 8 本のうち 7 本が完走し、`Q3-SY1992` は 2 日を隔てた 2 走目で申告総数ごと 1 件増えて `second_pass_digest_mismatch` (9/3b §7.1 が未観測とした登録第 2 走の安定性の初観測)。初回取得を 22 leaf 足し、78 leaf のうち完走 8・pass 2 待ち 22・再開点なしの未完走 4・未走 44。生証拠は `output/insights/2026-09-05_t2090-axis1-openalex-window2/`。**軸 1 は `未完走` であり成熟度は `RW1` のまま** |
| 2026-09-05 | `2026-09-05-backoff-axis-registration.md` | **2 本目の論文** (`docs/paper-story-backoff/`) の主張軸 B5「更新間隔を動的に決める backoff」の登録。軸を 4 条件 (対象 / 機構 / 動的化 / 正しさ) へ分解し、`docs/related-work/` 配下の全 file を 11 語で走査した**内部の不在** (直接接地 0 件、近傍 1 件 = Polyjuice の文献マップ要約) を母集合と走査語つきで凍結。世界側の候補 3 群 (Cicada 原論文 / 確率近似の適応 step・窓 / STM の適応 contention manager) は未検索・未読・書誌未確定の `要裁定`。**新しい検索は 1 本も行っていない。軸 B5 は `RW0` であり、世界の不在は支持しない。本体論文の軸 1〜5 は動かさない** |
