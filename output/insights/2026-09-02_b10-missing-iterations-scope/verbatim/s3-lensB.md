## 所見 1 — 「欠測 7」は開始済み attempt だけの数で、正式 request 全体の欠測ではない

- 所見: 最重要の不整合である。`294 = 49 build_start × 6` と `7 = 294 − 287` は開始済み attempt に限った事後分母である。read-heavy は予定 15 点中 `build_start` が 4 点しかなく、未開始 11 点の 66 verify 枠が分母から消えている。
- 根拠: 事前登録は 3 workload、各 15 点、legacy 1 回 + performance 5 回を要求する。[事前登録:400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/docs/b10-backoff-shape-preregistration.md:400)、[事前登録:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/docs/b10-backoff-shape-preregistration.md:423)、[生成器:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/orchestrator/campaign/b10_backoff_shape_sweep.py:96)、[生成器:547](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/orchestrator/campaign/b10_backoff_shape_sweep.py:547)。read-heavy WAL の `.stage=="build_start"` は 4 variant のみで、15 variant 集合との差は 11。

  - 4 request 単位: `4 × 15 × 6 = 360` 枠、観測 287、完了記録なし 73。
  - 登録された 3-workload 組として完成済み write-heavy 1 本を選ぶ場合: `3 × 15 × 6 = 270` 枠、観測 `90 + 85 + 22 = 197`、完了記録なし 73。
  - 73 の内訳: balanced 5、read-heavy 68。read-heavy 68 は未開始 11点×6=66 と、開始済み constant-mu2 の残り2。
  - タグ別には予定 legacy 60 / 観測49 / 欠け11、予定 performance 300 / 観測238 / 欠け62。

- 成果物への影響 1 行: insight が「予定294、欠測7」を正式系列全体の completeness と書くと、欠測を 66 枠過小計上する。
- 推奨対応: 7 を「開始済み49 attempt 内の未完了 verify 枠」と限定し、正式 request 全体については 360/287/73 と legacy 60/49/11、performance 300/238/62 を併記する。

## 所見 2 — 指定された数値の独立再集計

- 所見: 数値そのものは全て親の値と一致した。ただし 49 / 47 / 294 / 7 / legacy 49 の単位と分母には所見1の限定が必要である。
- 根拠: 4 WAL の `.stage`、`.payload.workload.tag`、対象 variant、write-heavy provenance の `.records` と `.judgement.families[]` を直接集計した。

| 値 | 独立導出 | 判定 |
|---:|---|---|
| 49 | `build_start = 15 + 15 + 15 + 4` | 一致。ただし 49 variant ID ではなく49 `(campaign, variant)` attempt。distinct variant ID は15 |
| 47 | `commit = 15 + 14 + 15 + 3` | 一致。47 committed attempts |
| 294 | `49 started attempts × (legacy 1 + performance 5)` | 算術は一致。「正式系列の予定総数」は不一致 |
| 287 | `verify_done = 90 + 85 + 90 + 22` | 一致。4 attempt の観測 aggregate |
| 7 | started attempt 内で `294 − 287` | 一致。ただし全 request 欠測は73 |
| 5 | balanced `c7c331ebe662`: legacy 1、performance 0、予定 performance 5 | 一致 |
| 2 | read-heavy `292d58f1dad8`: legacy 1、performance 3、予定 performance 5 | 一致 |
| 45 | provenance `.records|length` | 一致 |
| 15 | distinct `(variant_id, build_attempt_id)` | 一致 |
| 238 | performance `75 + 70 + 75 + 18` | 一致 |
| legacy 49 | legacy `15 + 15 + 15 + 4` | 一致する観測数。全 request では11欠け |
| 70 | balanced performance `14 × 5` | 一致 |
| 18 | read-heavy performance `5 + 5 + 5 + 3` | 一致 |
| 3 | read-heavy constant-mu2 の performance verify_done | 一致 |
| 18 pair | `3 block × 6 μ`。provenance の write-heavy pairs=18、balanced/read-heavy reasons=18ずつ | 一致 |

  一次資料は4本の `/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/official-output/campaigns/b10-backoff-shape-silo-*-formal-*/runs/wal.jsonl` と [provenance](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/output/insights/2026-08-31_t1905-b10-formal-run/reports/write-heavy/b10_backoff_shape_provenance.json) である。

  「約7倍」も限定付きで再現した。対応点の平均 commit 比は none `16.888M / 2.339M = 7.22`、zero-loop `17.089M / 2.393M = 7.14`、constant-mu2 `16.928M / 2.478M = 6.83`。3高commit点では約7倍だが、adaptive は約5.03倍である。

- 成果物への影響 1 行: 数値表は維持できるが、49を「変種」、294を「事前予定」、7を「正式系列全体の欠測」と呼ぶことはできない。
- 推奨対応: 単位を `build attempt record`、`started-attempt denominator`、`request-level denominator` に分ける。

## 所見 3 — 原因帰属は balanced と read-heavy で証拠の強さが違う

- 所見: balanced 5 の壁時計帰属は scheduler 単独で一意。read-heavy 2 は scheduler+WALだけでは「壁時計ではない」までしか決まらず、ユーザー撤去への帰属には contemporaneous worklog が必要である。
- 根拠:

  - balanced scheduler は `Exceeded per-req elapse time limit`、SIGKILL、remaining 0 秒を明記する。[scheduler.stderr:2](/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/f4aa966444a33e90af5131f79c4a67ca/scheduler.stderr:2)。ノード障害、driver自主停止、claim競合とは両立しない proximal cause である。
  - read-heavy scheduler は `Terminated` と remaining 22250 秒だけで、送信主体を記録しない。[scheduler.stderr:1](/work/1/SFC/tanab/izanagi-job-evidence/b10-backoff-shape/submissions/9b304374f905603052929a9d629f956b/scheduler.stderr:1)。scheduler+WALだけなら管理者停止、ノード側終了、driver/process-group由来のSIGTERMも論理上排除できない。
  - 一方、同時代記録は明示的に `qdel` を実行したと記す。[docs/worklog.md:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/docs/worklog.md:65)。これを加えればユーザー撤去に閉じる。
  - claim競合は WAL 作成前の `acquire_claim` で停止する。[loop.py:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/orchestrator/campaign/loop.py:198)。22 verify_done まで進んだ read-heavy の終端原因にはならない。

- 成果物への影響 1 行: 「scheduler受領証でread-heavy撤去まで確定」は過大で、証拠連鎖を省くと代替説明が残る。
- 推奨対応: 「scheduler は非壁時計を確定し、`docs/worklog.md` の qdel 記録がユーザー撤去を確定する」と二段に書く。

## 所見 4 — M13 の反実仮想は条件付きで成立するが、spec の字義だけからは出ない

- 所見: 「他が全て揃えば、この欠けだけで balanced/read-heavy の2族が indeterminate」は、bound implementation を含む前提付きなら成立する。ただし7という個数が必要なのではなく、両 workload の各 attempt に未完了 repetition が1件以上あることが十分である。
- 根拠: 必要な前提は次の全てである。

  1. legacy 1回と performance 5回を全て通るまで attempt を certified/commit しない。[pipeline.py:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/orchestrator/campaign/pipeline.py:131)、[pipeline.py:1521](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/orchestrator/campaign/pipeline.py:1521)。
  2. committed attempt だけが performance cell の certification source になる。[b10_backoff_shape_sweep.py:2430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/orchestrator/campaign/b10_backoff_shape_sweep.py:2430)。
  3. write-heavy の同一 variant ID の認証を balanced/read-heavy へ移送しない。
  4. certification 不在なら、その点の3 block record が `missing` または `correctness-not-certified` になる。
  5. balanced symmetric-mu100 または read-heavy constant-mu2 の片腕が無ければ、それぞれ3 block分の pair が unusable になる。
  6. 18 pair のうち1件でも unusable なら族全体が indeterminate。[事前登録:460](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/docs/b10-backoff-shape-preregistration.md:460)、[judge:1744](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/orchestrator/campaign/b10_backoff_shape_sweep.py:1744)。
  7. 「他が全て揃う」には、read-heavy の未開始11点、全 performance block record、exposure、stability、反対腕を含む残り15 pair全ての usable が含まれる。

  実測されていないのは前提4の反実仮想 record materialization、前提7の全条件、後続 attempt による認証置換がないこと。実際の provenance は balanced/read-heavy とも performance record が0で、18 pair全部が missing である。[provenance:5431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/output/insights/2026-08-31_t1905-b10-formal-run/reports/write-heavy/b10_backoff_shape_provenance.json:5431)。

- 成果物への影響 1 行: M13を無条件の「事前登録の字義」と書くと、verify attemptからanalysis cellへの実装上の橋を隠す。
- 推奨対応: 「bound implementationとworkload-specific certificationを前提とする反実仮想」と明記し、「7件全てが必要」ではなく「両 attempt の未完了が各族をindeterminateにする」と書く。

## 所見 5 — 親が列挙していない下流派生先がある

- 所見: 新しい図や未列挙のコード consumer は見つからなかったが、正式走 insight、worklog、分散設計、決定記録に read-heavy の部分 attempt を含む運用値の派生記述がある。
- 根拠: tracked の `output/insights/**/README.md` 488本、`docs/**/*.md` と `docs/*.md` 1059本、`tools/plotting/` と `orchestrator/` 921 file を、campaign ID、request ID、287、238、commit相関、1690万、23分、約7倍、provenance名で検索した。

  - [formal-run insight:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/output/insights/2026-08-31_t1905-b10-formal-run/README.md:147) と [archive worklog:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/docs/archive/worklog-phase3-0902-1186.md:58) の 1690万 commit / 約23分。
  - [docs/worklog.md:1405](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/docs/worklog.md:1405) の T-2191 は 238 回帰から 70.0–87.0 μs/commit と15認証単位を派生させている。
  - [分散設計:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/docs/b10-multinode-formal-run-design.md:16) と [同:115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/docs/b10-multinode-formal-run-design.md:115) の5時間・3変種・約25時間外挿。job wallには未commitの第4変種で消費した時間も含まれる。
  - [D1485:46378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/docs/decisions.md:46378) も23分を優先順位判断へ使用する。
  - Fig2b は別の `backoff-sweep-*`、Fig2c は固定された `b10-backoff-grid-*-sweep-*` 入力であり formal WAL は不使用。[Fig2b provenance:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/docs/paper-story/figures/fig2b_backoff_sweep_3workload.provenance.json:19)、[Fig2c generator:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/tools/plotting/plot_b10_extended_backoff.py:75)。
  - `orchestrator/campaign/b10_backoff_shape_sweep.py` の正式 analyzer は block records を読むが、balanced/read-heavy の block records は存在しない。部分 WAL を自動集計する別 consumer は見つからなかった。

- 成果物への影響 1 行: 「混入先はtrace insight 1件だけ」は refuted で、少なくとも運用設計と優先順位判断へ派生している。
- 推奨対応: 新 insight の帰属 matrix に「直接集計」と「その派生記述」を分け、上記4文書を追加する。`docs/paper-story/` への変更提案はしない。

## 所見 6 — worklog entry 1189 には4種類の訂正が必要

- 所見: 壁時計と45-cell wording以外に、「予定294」「実行されず」「何の正しさ主張も担わない」も実測と釣り合わない。
- 根拠: 訂正対象は [entry 1189:986](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/docs/worklog.md:986) と required projection の `/home/SFC/tanab/.claude/jobs/0afdc8ef/tmp/dw/b10-missing-iterations-scope/verbatim-worklog-1189.md:23-25`。

  1. 「予定294」は開始済み49 attemptの事後分母。request-level は360、欠け73。
  2. 「7反復は実行されず」は強すぎる。WAL が証明するのは `verify_done` が無いことだけである。balanced は最後の legacy 完了からscheduler終了まで約80秒、read-heavyは3回目performance完了から終了まで約264秒あり、次 repetition が開始済みだった可能性を排除できない。
  3. 「外側jobの壁時計」はread-heavyで誤り。
  4. 「2変種は45 cellに含まれない」は variant ID 読みで誤り。正しいのは workload-specific build attempt が認証元でないこと。
  5. 「何の正しさ主張も担っていない」は、未完了枠が positive row-level correctness を担わないという狭義では正しいが、事前登録の family testability と official certification を左右しうるため広義では誤り。

- 成果物への影響 1 行: 現行文は欠測を無害な未起動枠として読ませ、confirmatory missingnessへの影響を消す。
- 推奨対応: 「完了記録のない枠」「positive certification は担わないが、完全性とfamily判定の制約を担う」へ追記訂正する。

## 所見 7 — M1〜M14 の一般化監査

- 所見: raw countの多くは正しいが、M1/M3/M7/M9/M10/M12/M13に測定範囲を越えた表現がある。
- 根拠:

| 項目 | 判定 |
|---|---|
| M1 | stage count は一致。49を「変種」、294を「予定」とする一般化は不可 |
| M2 | 開始済み attempt の未commit 2件として正しい。read-heavy未開始11点は対象外 |
| M3 | 観測タグ数は正しい。「legacy欠測0」は開始済み49 attempt限定。request全体では11欠け |
| M4 | 観測22件の記述として正しい。read-heavy 15点やrep分布の代表とは言えない |
| M5 | 45/15/requestは正しい。「2変種が寄与しない」はbuild attempt読みのみ。variant IDは各3record |
| M6 | 空directoryというsnapshotは正しい。「成果物なし」はWAL/lock/submission evidenceを除く限定が必要 |
| M7 | tracked paper figureについて正しい。「図は存在しない」というuntracked/externalまで含む全称は未証明 |
| M8 | balanced壁時計、read-heavy非壁時計まで。撤去主体にはworklogが必要 |
| M9 | 直接238回帰の内訳は正しいが、consumer inventoryとして不完全 |
| M10 | balancedはschedulerで確定。read-heavy撤去はscheduler単独ではなくworklogとの合成証拠 |
| M11 | 一致。variant IDとattemptの分離は正しい |
| M12 | provenance fieldsは一致。7が各3 pairへ関係するのは反実仮想上の写像で、actual reasonsの直接帰属ではない |
| M13 | bound code込みの条件付き主張。spec字義だけ、または実測済みの帰結ではない |
| M14 | 指定2図とtracked docsの範囲で一致。repo外図一般には拡張不可 |

- 成果物への影響 1 行: M1/M3の一般化を残すと insight 全体の completeness denominator が誤る。
- 推奨対応: 各M項目に「observed」「started attempts」「tracked paper figures」「scheduler + worklog」の境界語を加える。

## 所見 8 — 論文利用3分類は4項目を変更すべき

- 所見: plan子の禁止項目は概ね妥当だが、「使える」3項目と238/約7倍の但し書きを修正する必要がある。
- 根拠:

| plan項目 | 判定 |
|---|---|
| request 965564 の45 recordsがtrue/false | 「使える」から「但し書き付き」へ。write-heavy 1 request、top-level official certification=falseを併記 |
| 294/287/7 completeness disclosure | as-writtenは使えない。360/287/73、または登録3-workloadの270/197/73へ修正すれば使える |
| 観測287が全てcertified | 「但し書き付き」へ。4 attempt、write-heavy重複、未開始11点、common-mode限界を明記 |
| Fig2b/2cがformal入力でない | 「使える」のまま |
| 3-workload confirmatory結論 | 「使えない」で一致 |
| balanced mu100/read-heavy mu2を5rep cellとして報告 | 「使えない」で一致 |
| 完了記録のない枠をserializable等と書く | 「使えない」で一致。「未実行」ではなく「verify_doneなし」 |
| write-heavy not-detectedを正式系列結論にする | 「使えない」で一致 |
| 45-cell throughput等のdescriptive result | 「但し書き付き」で一致 |
| 238回帰 | 「但し書き付き」を維持。ただし read-heavy 18にuncommitted attemptの3/5 rep、全体にtermination由来のcensoringがあると追加 |
| 約7倍 | 「但し書き付き」を維持。3高commit点の6.83–7.22倍であり、adaptiveは約5.03倍、full gridではない |
| balanced85/read-heavy22のintegrity | 「但し書き付き」を維持。ただし欠けはstarted内7、request全体73と分離 |

- 成果物への影響 1 行: 294/287/7をそのまま論文のcompleteness disclosureに使う分類は重大な過少報告になる。
- 推奨対応: 上表の4変更と、238/約7倍へのcensoring注記を段4で採用する。

## 所見 9 — brief (P1) 3件の判定

- 所見:

  - P1-1: **refuted as written**。45 record自体のtruthが下がらない狭義部分だけはrealだが、「射程を一切限定しない」は3-workload completenessとfamily inferenceまで読めるため成立しない。
  - P1-2: **refuted**。287 aggregate、同じvariant IDの45 records、formal-run/worklog/分散設計/決定への派生がある。図にformal attemptが入らない部分だけreal。
  - P1-3: **real**。balancedは壁時計、read-heavyはqdelによるユーザー撤去。ただしread-heavyの主体確定にはschedulerだけでなくworklogを要する。

- 根拠: P1-1は provenance `.records`, `.official_certification`, `.judgement.families[]`、P1-2は所見5、P1-3は所見3のscheduler受領証と [docs/worklog.md:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-b10-missing-iterations-scope/docs/worklog.md:65)。
- 成果物への影響 1 行: P1-1/P1-2を維持すると、attemptとvariant ID、row truthとconfirmatory scopeが再び混同される。
- 推奨対応: P1-1を「45 write-heavy recordsのrow-level truthは維持」、P1-2を直接集計と派生先の完全なmatrix、P1-3を二段証拠へ置換する。

## 総括

- 最も重い所見3件:

  - `7` は開始済み attempt 内だけ。正式 request 全体では `360 / 287 / 73`、legacy欠け11、performance欠け62。
  - M13はspec字義だけの実測結論ではなく、bound implementationと未実測の「他15 pair全てusable」を要する反実仮想。
  - 下流は238回帰だけではなく、formal-run記録、worklog T-2191、分散設計、D1485へ派生している。

- (P1) 判定:

  - P1-1: **refuted as written**。狭いrow-level部分のみreal。
  - P1-2: **refuted**。
  - P1-3: **real**。scheduler + contemporaneous qdel記録による。

- 親が段4で必ず裁定すべき点:

  - insightの主分母を7に閉じるか、正式request全体の73を正面から開示するか。推奨は両方を階層表示すること。
  - 「未実行」を「verify_done完了記録なし」へ直すこと。
  - M13を条件付き反実仮想として残すか。推奨は残すが、必要前提とactual 18-pair missingを併記すること。
  - P1-1/P1-2をrefutedとして置換し、paper分類の294/287/7項を修正すること。
  - read-heavy帰属をscheduler単独ではなくqdel worklogとの合成証拠として書くこと。

ファイル変更、commit、pytest実走はいずれも行っていない。worktreeはcleanのままである。