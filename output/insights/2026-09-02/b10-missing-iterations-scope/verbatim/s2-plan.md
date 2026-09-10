## 結論

プランの中心は「変種 ID」と「欠けた workload-specific attempt」を分けることです。

- `c7c331ebe662` と `292d58f1dad8` は genome に由来する workload 共通の `variant_id` です。両 ID は write-heavy の 45-cell provenance に各 3 record 存在します。
- 45 cell に入っていないのは、balanced/read-heavy の未完了 `build_attempt_id` と、その 7 反復です。「2 変種は 45 cell に含まれない」とは書けません。
- 45 record 自体の `correctness_certified=true` は維持されます。ただし射程は write-heavy、request `965564.nqsv`、15 認証単位に閉じ、balanced/read-heavy や予定 294 反復へは拡張できません。
- ファイル変更、commit、pytest 実走は行っていません。`git status --short` は空でした。

## insight の予定行と節構成

対象は `output/insights/2026-09-02_b10-missing-iterations-scope/README.md` です。物理行は次の配置を推奨します。

| 予定行 | 見出し・内容 | 役割 |
|---:|---|---|
| L1 | `## B-10 正式走の欠測 7 反復 — 45 cell は維持されるが、3 workload 結論には使えない` | タイトルも `##` にする |
| L3-L9 | 判定の要約 | 依頼の 3 問へ各 1 文で先に回答 |
| L11 | `## 単位と母集団` | `variant_id`、workload、campaign、build attempt、cell を分離 |
| L13-L24 | 用語表と予定 294 / 観測 287 の母集団 | `performance` タグを性能 cell と誤読させない |
| L26 | `## 欠測した 7 反復の同定` | 2 attempt と欠測数を確定 |
| L28-L43 | balanced / read-heavy の観測・欠測表 | legacy と performance-tag verify を分ける |
| L45 | `## 2 変種が入る主張・図・集計` | 問い 1 の本体 |
| L47-L70 | 帰属 matrix と注意書き | 287、238 回帰、約 7 倍、45 cell、Fig2b/2c を列挙 |
| L72 | `## 45 cell の correctness_certified の射程` | 問い 2 の本体 |
| L74-L93 | 維持されるもの／拡張できないもの | P1-1 を狭義支持・広義限定 |
| L95 | `## 論文で使える範囲` | 問い 3 の本体 |
| L97-L121 | 使える／使えない／但し書き付きの表 | confirmatory result と運用分析を分離 |
| L123 | `## 規律 7 による追記訂正` | entry 1189 を上書きせず訂正 |
| L125-L137 | 壁時計理由と variant wording の訂正文 | balanced 5 / read-heavy 2 を分ける |
| L139 | `## 書いてはいけないこと` | 過大・過小一般化を列挙 |
| L141-L158 | 禁止文と置換方向 | insight 内の最終防護 |

## L3-L9 判定要約の主張と一次資料

| 予定行 | 書く主張 | 一次資料 |
|---:|---|---|
| L3-L4 | 4 campaign では 49 build attempt × 6 verify 枠 = 294 に対して `verify_done` は 287、欠測は 7。 | `docs/b10-backoff-shape-preregistration.md:423-429`。4 WAL の jq path `.stage`、`.variant`：`/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-write-heavy-formal-068fd2cd/runs/wal.jsonl`、`.../b10-backoff-shape-silo-balanced-formal-15e75b3f/runs/wal.jsonl`、`.../b10-backoff-shape-silo-write-heavy-formal-e3de15eb/runs/wal.jsonl`、`.../b10-backoff-shape-silo-read-heavy-formal-ed8a676b/runs/wal.jsonl` |
| L5 | 欠測は balanced `c7c331ebe662` の performance-tag 5 枠と、read-heavy `292d58f1dad8` の同 2 枠。 | balanced WAL / read-heavy WAL の jq path `select(.variant==...) | {stage, payload.genome, payload.workload.tag}`。登録反復数は `docs/b10-backoff-shape-preregistration.md:423-429` |
| L6-L7 | 欠測 7 は 45 write-heavy record の真偽を下げないが、balanced/read-heavy の認証や完全な 3-workload 系列を意味しない。 | `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/output/insights/2026-08-31_t1905-b10-formal-run/reports/write-heavy/b10_backoff_shape_provenance.json` の jq path `.records[] | {workload,request_id,build_attempt_id,correctness_certified,missing}` |
| L8-L9 | 論文では scoped な run fact と運用分析だけが利用可能で、事前登録した 3-family の confirmatory 結論には使えない。 | `docs/b10-backoff-shape-preregistration.md:460-486`、同 `:658-677`。provenance の jq path `.official_certification`, `.judgement.families[]` |

## L11-L24 単位と母集団の主張と一次資料

| 予定行 | 書く主張 | 一次資料 |
|---:|---|---|
| L13-L16 | `variant_id` は workload 固有ではない。同じ `c7c331ebe662` / `292d58f1dad8` が write-heavy provenance にも現れる。 | provenance の jq path `.records[] | select(.variant_id=="c7c331ebe662" or .variant_id=="292d58f1dad8") | {workload,point,variant_id,build_attempt_id,request_id}` |
| L17-L19 | 欠測の同定単位は `(workload, campaign_id, build_attempt_id, tag, repetition)` とする。variant ID だけで「45 cell に不在」と判定しない。 | balanced WAL の `.payload.build_attempt_id="358527d389db442ade4e8d1fb789a041"`、read-heavy WAL の `.payload.build_attempt_id="4506672584e9ab3f4d012e91ce90f1e3"`。write-heavy provenance の対応 ID は `ca8336bbaf75ed924981e13357ec9461` と `58937c239a567a724717b962ff30d1c4` |
| L20-L22 | WAL の `payload.workload.tag=="performance"` は trace 有効 verify の workload tag であり、45-cell throughput record そのものではない。 | 各 WAL の jq path `.stage=="verify_done"`, `.payload.workload.tag`。`output/insights/2026-09-02_b10-trace-truncation/README.md:12-13`、同 `:229-231`。`docs/b10-backoff-shape-preregistration.md:647-655` |
| L23-L24 | 45 cell は 3 block × 15 point の performance record、認証単位は distinct `(variant_id, build_attempt_id)` 15 組。 | provenance の jq path `.records|length`, `[.records[]|[.variant_id,.build_attempt_id]]|unique|length`。既存 insight `output/insights/2026-09-02_b10-trace-truncation/README.md:22-26` |

## L26-L43 欠測同定の主張と一次資料

| 予定行 | 書く主張 | 一次資料 |
|---:|---|---|
| L28-L32 | balanced の `c7c331ebe662` は `BACKOFF_FIXED=1100`、point は `symmetric-modulo-mu100`。legacy 1 回のみ観測し、performance-tag 5 回が未実行。 | balanced WAL の jq path `select(.variant=="c7c331ebe662") | {stage,payload.genome,payload.workload.tag,payload.certified}`。point 対応は provenance の `.records[] | select(.variant_id=="c7c331ebe662") | {point,genome}` |
| L33-L37 | read-heavy の `292d58f1dad8` は `BACKOFF_FIXED=2`、point は `constant-mu2`。legacy 1、performance-tag 3 を観測し、後者 2 回が未実行。 | read-heavy WAL の jq path `select(.variant=="292d58f1dad8") | {stage,payload.genome,payload.workload.tag,payload.certified,payload.commits}`。point 対応は provenance の `.records[] | select(.variant_id=="292d58f1dad8") | {point,genome}` |
| L38-L40 | 両 attempt の観測済み 5 verify はすべて `certified=true`、`verdict="serializable"`、`anomalies=0`。未実行 7 回とは別列に置く。 | 上記 2 WAL の jq path `select(.stage=="verify_done" and (.variant==...)) | .payload | {certified,verdict,anomalies}` |
| L41-L43 | 全体の観測内訳は legacy 49、performance-tag 238。欠測 7 はすべて予定された performance-tag 枠。 | 4 WAL の jq path `select(.stage=="verify_done") | .payload.workload.tag`。登録反復構成は `docs/b10-backoff-shape-preregistration.md:423-429` |

## L45-L70 帰属 matrix の草案

| 対象 | 287 verify の完全性集計 | 238 performance-tag 時間回帰 | 「read-heavy は約 7 倍」 | 45 write-heavy cell | Fig2b / Fig2c |
|---|---|---|---|---|---|
| balanced `symmetric-modulo-mu100`, ID `c7c331ebe662` | legacy 1 回が入る | 0 回。入らない | 入らない | 同じ ID / point の write-heavy record が 3 件入る。ただし balanced build attempt は入らない | formal attempt は入らない |
| read-heavy `constant-mu2`, ID `292d58f1dad8` | legacy 1 + performance-tag 3 = 4 回が入る | performance-tag 3 回が入る | 16.916M-16.938M commit の 3 回が入る | 同じ ID / point の write-heavy record が 3 件入る。ただし read-heavy build attempt は入らない | formal attempt は入らない |
| 未実行の 7 反復そのもの | 入らない | 入らない | 入らない | 入らない | 入らない |

この matrix の各主張には次を対応させます。

| 予定行 | 主張 | 一次資料 |
|---:|---|---|
| L47-L51 | 287 aggregate には balanced 側 1、read-heavy 側 4 の観測済み verify が入る。 | balanced / read-heavy WAL の jq path `select(.stage=="verify_done" and (.variant=="c7c331ebe662" or .variant=="292d58f1dad8"))` |
| L52-L55 | 238 回帰には read-heavy `292d58f1dad8` の 3 回だけが入り、balanced `c7c331ebe662` は 0 回。 | 4 WAL の jq path `select(.stage=="verify_done" and .payload.workload.tag=="performance") | .variant`。回帰の定義と結果は `output/insights/2026-09-02_b10-trace-truncation/README.md:148-158`、再現字段は同 `:240-248` |
| L56-L59 | 「read-heavy の検査対象は約 7 倍」の高 commit 群には `292d58f1dad8` の 3 回が含まれる。 | read-heavy WAL の `.payload.commits` が `16937619`, `16916573`, `16929436`。既存主張は `output/insights/2026-09-02_b10-trace-truncation/README.md:194-202` |
| L60-L64 | 45-cell provenance には両 variant ID が各 3 record あるが、workload は write-heavy、request は `965564.nqsv`、build attempt は incomplete attempts と異なる。 | provenance の jq path `.records[] | select(.variant_id=="c7c331ebe662" or .variant_id=="292d58f1dad8") | {workload,point,variant_id,build_attempt_id,request_id}` |
| L65-L68 | Fig2b は `backoff-sweep-*`、Fig2c は `b10-backoff-grid-*-sweep-*` が入力で、4 formal campaign は入力ではない。 | `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/docs/paper-story/figures/fig2b_backoff_sweep_3workload.provenance.json` の `.inputs[].campaign`。`.../fig2c_b10_extended_backoff.provenance.json` の `.external_source_locator.root_at_generation`, `.data[].campaign_id` |
| L69-L70 | 図に同じ μ 座標があっても、それを formal attempt の採用と呼ばない。 | Fig2b/2c の上記 provenance と、formal WAL の campaign ID の不一致 |

## L72-L93 45 cell の射程

| 予定行 | 書く主張 | 一次資料 |
|---:|---|---|
| L74-L77 | 45/45 record は今も `correctness_certified=true` かつ `missing=false`。欠測 7 による遡及的な降格はしない。 | provenance の jq path `[.records[]|{correctness_certified,missing}] | group_by(.)`。既存記録 `output/insights/2026-08-31_t1905-b10-formal-run/README.md:34-40` |
| L78-L81 | 45 record の範囲は write-heavy、request `965564.nqsv`、15 distinct 認証単位。 | provenance の `.records|length`, `[.records[].workload]|unique`, `[.records[].request_id]|unique`, `[.records[]|[.variant_id,.build_attempt_id]]|unique|length` |
| L82-L85 | 認証元は write-heavy `e3de15eb` の legacy 15 + performance-tag 75 = 90 trace verify。 | `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-write-heavy-formal-e3de15eb/runs/wal.jsonl` の `.stage`, `.payload.workload.tag`, `.payload.certified` |
| L86-L88 | balanced/read-heavy の欠測 attempt は 45 record の認証元ではない。だが point / variant ID 自体は write-heavy record に存在する。 | provenance と balanced/read-heavy WAL の `build_attempt_id` 比較 |
| L89-L91 | したがって欠測は 45 record の row-level truth を限定しないが、3 workload、4 campaign、294 verify の完全性へ拡張することを禁止する。 | provenance の workload/request 範囲と、4 WAL の stage 内訳 |
| L92-L93 | `correctness_certified` は trace 有効 run の変種認証であり、trace 無効 performance run の履歴を検査した意味ではない。 | `docs/b10-backoff-shape-preregistration.md:643-655`、`output/insights/2026-09-02_b10-trace-truncation/README.md:226-231` |

## 親の P1 3 件への対応

| P1 | 判定 | 材料を置く節 |
|---|---|---|
| P1-1「欠測は 45 cell の射程を一切限定しない」 | 狭義支持、広義限定。45 record 自体は維持される。一方、「一切」を cross-workload 一般化まで含めるなら反証する。 | `## 45 cell の correctness_certified の射程` L74-L93 |
| P1-2「2 変種が実際に入る集計は 238 回帰だけ」 | 反証。read-heavy の 3 performance-tag 回は回帰に入るが、balanced は入らない。加えて観測済み verify は 287 aggregate に両方入り、同一 variant ID は 45 write-heavy records にも入る。図の formal 非帰属は支持。 | `## 2 変種が入る主張・図・集計` L47-L70 |
| P1-3「balanced 5 は壁時計、read-heavy 2 は壁時計ではない」 | 支持。read-heavy 撤去の理由は記録以上に推測しない。 | `## 規律 7 による追記訂正` L125-L137 |

## L95-L121 論文で使える範囲

| 分類 | 草案 | 根拠となる一次資料 |
|---|---|---|
| 使える | 「request `965564.nqsv` の write-heavy 45 records は全件 `correctness_certified=true` / `missing=false` だった。」 | provenance の `.records[] | {workload,request_id,correctness_certified,missing}`、`output/insights/2026-08-31_t1905-b10-formal-run/README.md:34-40` |
| 使える | 「4 formal attempts の trace verify は予定 294 に対し 287 が記録され、7 は未実行だった」と completeness disclosure に書く。 | 4 WAL の `.stage`、`docs/b10-backoff-shape-preregistration.md:423-429` |
| 使える | 「観測された 287 verify の範囲では `certified=true` だった」。必ず「観測された」を残す。 | 4 WAL の `select(.stage=="verify_done") | .payload.certified`、`output/insights/2026-09-02_b10-trace-truncation/README.md:47-69` |
| 使える | Fig2b/2c の入力が formal 4 campaign ではないこと、および本欠測が両図の欠測ではないこと。 | Fig2b `.inputs[].campaign`、Fig2c `.data[].campaign_id` と `.external_source_locator.root_at_generation` |
| 使えない | 「3 workload で constant と symmetric-modulo の差を事前登録手続きにより確定した」。 | `docs/b10-backoff-shape-preregistration.md:460-486`。provenance `.judgement.families[]` では balanced/read-heavy が `indeterminate`、`.official_certification=false` |
| 使えない | balanced `symmetric-modulo-mu100` または read-heavy `constant-mu2` について、5 performance repetitions が揃った cell estimate として報告する。 | balanced/read-heavy WAL の `.payload.workload.tag` と commit 不在。両 campaign には formal report record がない |
| 使えない | 未実行 7 回について serializable、anomaly zero、certified と書く。 | WAL に該当 `verify_done` record が存在しない。事前登録の即 reject 規律は `docs/b10-backoff-shape-preregistration.md:651-655` |
| 使えない | write-heavy の機械生成された `not-detected` を、正式系列全体の confirmatory 結論として使う。 | report `output/insights/2026-08-31_t1905-b10-formal-run/reports/write-heavy/b10_backoff_shape_report_965564.nqsv-4911e3361f48.md:61-65` に対し、formal-run insight `:62-64` は結論化を拒否し、provenance は `.official_certification=false` |
| 但し書き付きで使える | 45 write-heavy cell の throughput・abort・backoff call 数を descriptive result として使う。ただし 1 workload / 1 request と明記し、3-workload shape conclusion にしない。 | report `:13-59`、provenance `.records[]`、formal-run insight `:62-66` |
| 但し書き付きで使える | 238 performance-tag verify の commit 数と混合所要の回帰を、checker 運用コストの retrospective analysis として使う。B-10 throughput 効果や機構的限界費用とは呼ばない。 | 4 WAL の `.ts`, `.payload.commits`, `.payload.aborts`, `.payload.workload.tag`。`output/insights/2026-09-02_b10-trace-truncation/README.md:148-175`、同 `:186-192` |
| 但し書き付きで使える | read-heavy の観測済み 4 変種で checker 対象 commit が write-heavy より約 7 倍だったという運用説明。full grid や workload 一般の比率にはしない。 | read-heavy WAL の `.payload.commits`、既存 insight `:194-202` |
| 但し書き付きで使える | balanced 85、read-heavy 22 の観測済み trace verify の integrity 結果。未実行 7、common-mode failure、trace 無効 performance run は覆わない。 | balanced/read-heavy WAL の `.payload.certified`, `.payload.verdict`, `.payload.anomalies`。既存 insight `:210-236` |

## L123-L137 規律 7 の追記訂正文案

新規 insight の `## 規律 7 による追記訂正` に、次の形で置くのが安全です。

> worklog entry 1189 の「実行されずに終わった 7 反復は外側 job の壁時計打ち切りによる」という原因帰属を追記で訂正する。balanced の 5 反復は request `963545.nqsv` が 21,609 秒を使用し、remaining elapse 0 秒で SIGKILL されたため、壁時計打ち切りである。read-heavy の 2 反復は request `965996.nqsv` が 20,950 秒を使用した時点で 22,250 秒を残しており、壁時計打ち切りではない。当時の正式走記録どおり、read-heavy はユーザー裁定により撤去された。2 件はいずれも検査による reject ではなく、未実行の反復であるという entry 1189 の結論は維持する。

根拠：

- balanced scheduler：`/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/f4aa966444a33e90af5131f79c4a67ca/scheduler.stderr:2-16`
- read-heavy scheduler：`/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/9b304374f905603052929a9d629f956b/scheduler.stderr:1-16`
- read-heavy のユーザー裁定撤去記録：`output/insights/2026-08-31_t1905-b10-formal-run/README.md:68-72`、同 `:147-152`
- 訂正対象：`/home/SFC/tanab/.claude/jobs/0afdc8ef/tmp/dw/b10-missing-iterations-scope/verbatim-worklog-1189.md:23-25`

続けて、variant wording も追記で限定するのを推奨します。

> entry 1189 の「その 2 変種は 45 cell に含まれない」は、欠けた balanced/read-heavy の build attempts と未実行 7 反復が 45 cell の認証元ではない、という意味に限定する。同じ genome-derived `variant_id` と point は write-heavy の 45-cell provenance に各 3 record 存在する。

既存 entry 1189、既存 formal-run insight、既存 trace-truncation insightの bytes は変更しません。

## worklog fragment 1 本の内容案

`docs/spool/` の新規 fragment は、次の 3 bullet だけで十分です。

```markdown
## 2026-09-02 (...) — B-10 欠測 7 反復の射程を追記で確定

- 新規 insight で、balanced symmetric-modulo-mu100 の performance-tag 5 回と
  read-heavy constant-mu2 の同 2 回が未実行だったことを記録した。
- worklog entry 1189 の壁時計原因を追記訂正した。balanced 5 回は壁時計、
  read-heavy 2 回は壁時計ではなく、ユーザー裁定による撤去後に未実行で残った。
  「検査による reject ではない」という当時の結論は維持した。
- 45 write-heavy records の correctness_certified は維持されるが、
  1 workload・1 request・15 認証単位を越えて一般化しない。
```

canonical worklog や entry 1189 自体の編集は提案対象にしません。

## 書いてはいけない文

| 禁止文 | 問題 |
|---|---|
| 「欠測 7 反復は無害である。」 | row-level certification、3-family 推論、運用回帰で影響が異なるため、一語で畳めない |
| 「欠測した 2 変種は 45 cell に含まれない。」 | 同じ `variant_id` は write-heavy 45 cell に各 3 record 入る |
| 「欠けた balanced/read-heavy build attempts は 45 cell に含まれないので、2 変種は未測定である。」 | point 自体の write-heavy 測定まで消してしまう |
| 「45 cell は 3 workload・294 反復から認証された。」 | 実際は write-heavy、request `965564.nqsv`、15認証単位 |
| 「7 反復が欠けたので 45 cell の correctness_certified も不完全である。」 | 45 records は全件 true / missing false のまま |
| 「45 cell が認証済みなので balanced と read-heavy でも同じ 2 点は認証済みである。」 | workload と build attempt を越えた移送 |
| 「未実行 7 回も anomaly zero / serializable だった。」 | WAL record がなく、検査されていない |
| 「欠測 7 回はすべて壁時計打ち切りだった。」 | read-heavy は 22,250 秒を残していた |
| 「read-heavy は 12 時間枠を使い切ったため撤去された。」 | scheduler 実測に反する |
| 「read-heavy が撤去された技術的理由は X である。」 | 記録されたユーザー裁定を越える理由推測は禁止 |
| 「両方の欠測変種が 238 回帰に入っている。」 | balanced 側は performance-tag 0 回 |
| 「欠測変種が入る集計は 238 回帰だけである。」 | 観測済み反復は 287 aggregate に入り、同じ ID は45 recordsにも入る |
| 「performance 238 反復は B-10 の throughput performance cell である。」 | trace 有効 verify の tag であり、45-cell record と別 |
| 「read-heavy の検査対象は一般に write-heavy の 7 倍である。」 | 観測済み 4 変種の範囲を越える |
| 「Fig2b/2c は今回の formal run の不完全データを含む。」 | provenance 上は別 campaign 系列 |
| 「write-heavy で有意差がなかったので 2 形は同等である。」 | `not-detected` は同等性証明ではなく、formal narrative も結論化していない |
| 「3-family Holm 判定は完了した。」 | balanced/read-heavy は indeterminate、official certification は false |

## 総括

- プランの要点：
  - 欠測単位を variant ID ではなく workload / campaign / build attempt で記述する。
  - 287 aggregate、238 回帰、約 7 倍、45 records、図を別々に帰属させる。
  - 45 records は維持するが、3-workload confirmatory result にはしない。
- 最も割れやすい判断：
  - `c7c331ebe662` と `292d58f1dad8` が workload 共通 ID であるため、「2 変種は 45 cell に含まれない」という P1-2 周辺の表現は成立しない。
  - P1-1 の「一切限定しない」は、45 record 自体に限れば正しいが、論文上の一般化まで含めると過大である。
- 親が段 4 で裁定すべき点：
  - P1-2 を反証扱いとし、「欠けた 2 workload-specific attempts は 45 cell の認証元ではない」へ置換するか。
  - entry 1189 の追記訂正に、壁時計理由だけでなく「2 変種は 45 cell に含まれない」の単位訂正も含めるか。推奨は含める。
  - write-heavy の `not-detected` を論文の confirmatory 結論には使わず、45 cell の descriptive record だけを但し書き付きで残すか。推奨はその境界です。