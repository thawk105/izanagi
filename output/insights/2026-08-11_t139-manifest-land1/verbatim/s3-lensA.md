NO-GO です。現状の land 1 には blocker 8 件、land 2 設計には blocker 3 件があります。段 2 が挙げた 6 件は、RI-B1 を除く 5 件が real でした。一方、段 2 が見落とした承認状態文、pilot slot 閉包、台帳→manifest の trust root などがあります。

pytest・build・PBS は実行していません。静的読取、Git の read-only 照合、SHA-256 再計算だけを行い、作業木が clean のままであることを確認しました。

## 実測値の独立照合

すべて親の値と一致しました。

- core: `ac939af4de87dff0cd3964e37cef975d57919a709d57f4e9523c8b6a9fcd60e9`
- core 221 行 LF 込み: `225268a9fe702eae37ac3f4c150fcbc24e71835ce40bd3735ce0116784278e89`
- core 333 行 LF 込み: `a7852ad9a4812f8adc8ebf33354a5934bd6620205a23defa48732a1737a89952`
- erratum-1 のみ: `d1782b04ceb7cd56a3d10e2e6efb4eb7f90e6a89506a74bba727d34a5f79de82`
- erratum 2 本: `dfb821a5ff0b085f7092bbd5536772a8c6728ec946291a6e6eb61da9fbef678c`
- 逆順適用も同じ `dfb821…678c`
- core 中の `較正` は 221、333 行のちょうど 2 件
- `jsonschema == 3.2.0`、`Draft202012Validator` は不在
- 現行 record-items、再発行稿、erratum-2 の各 digest も親の値と一致

## 段 2 の RI/ER/SC 判定

| ID | 独立判定 | 理由 |
|---|---|---|
| RI-B1 | **refuted** | exact blob の規範的参照は一般に有効。非承認 blob でも、新文書が固定三つ組で incorporation すれば内容に規範力を与えられる。ただし role の明記は必要 |
| RI-B2 | **real** | 未閉包 object・enum と内部矛盾が複数ある。ただし `translation_units` map 自体は `propertyNames` と値 schema で閉じられるため、その小論点は過大主張 |
| RI-B3 | **real** | marker 不在だけで pre-performance とするため、性能 raw を持つ attempt を置換可能にできる |
| RI-B4 | **real** | current-tip 重複検査だけで、削除後の ordinal 再利用を検出しない |
| ER-B1 | **real** | core 333 行が較正義務を残す |
| SC-B1 | **real** | schema が未作成なだけでなく、現文書から exact に一意生成できない |

したがって段 2 の「独立 blocker 6 件」は 1 件過大で、上記集合では 5 件です。

## 所見

1. `[blocker]` record-items 再発行稿は、承認後に自身の承認状態について偽を述べる。

   根拠: [`record-items-reissue.md:7,12–17,299`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:7) の `approval_status: draft_unapproved`、「まだ承認されていない」「本書は承認されていない」。

   失敗シナリオ: `F_r` が当該 SHA を承認 → 台帳を読む resolver は approved、本文を読む実装は draft と判定 → 同一 blob が実装ごとに受理・拒否へ分岐。

   影響: post-`F_r` の `record_items` 承認集合が一意に定まらない。

2. `[blocker]` erratum-2 にも同じ自己失効文がある。

   根拠: [`erratum-core-s7-stresscheck.md:1,9,20–23,61–62,131–132,155–160`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/erratum-core-s7-stresscheck.md:1)。

   承認後に偽になるのは `(案)`、`draft_unapproved`、「まだ承認されていない」、「承認されたのは方向であり本書ではない」、「本書が承認されたとは主張しない」等。対して「**起草時点で** `F_s` は存在しない」[`同:125`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/erratum-core-s7-stresscheck.md:125) は歴史的記述なので偽にはならない。

   失敗シナリオ: manifest が approved errata に含める一方、文書 metadata と説明は draft を主張 → membership の取得元次第で適用結果が変わる。

   影響: effective core digest と pilot 停止状態が実装依存になる。

   Authority header の `authority: none` / `default_effect: no-state-change` 自体は先例と一致します。承認済み追補 A [`addendum-a-reissue.md:3–8`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:3) と erratum-1 [`erratum-core-s15.md:3–9`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-addendum-a/erratum-core-s15.md:3) も同形式です。core は `authority:none` を「可変状態の正本ではない」の意味と定義しています [`preregistration.md:23–24`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:23)。問題は候補だけが追加した現在形の `approval_status` です。

3. `[blocker]` RI-B2 は real。exact-key 閉包は完成しておらず、正例を拒否する矛盾もある。

   根拠:

   - 全 nested object を閉じたとの主張 [`record-items-reissue.md:41,130–135`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:41) に対し、`environment.attestations[]`、`dependency_pins[]`、`actual_runs[]`、`correctness_evidence[].run_scope` 等の item key・型・nullability がない。旧稿も名前を挙げるだけです [`record-items.md:56–65`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-addendum-a/record-items.md:56)。
   - `binary_rehash[]` を合計 3 件に固定 [`record-items-reissue.md:193–194`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:193) するが、a05 は 3 arm の各 binary を 3 点で再 hash するため 9 件必要 [`addendum-a-reissue.md:309–329`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:309)。
   - 7 列 raw では `malformed_reason=null` を許す [`record-items-reissue.md:101–107`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:101) 一方、閉包節は `short_columns` を必須化する [`同:167–173`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:167)。
   - `exclusivity.method` は key だけあり enum が閉じていない [`同:177–188`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:177)。

   失敗シナリオ: 正当な allocation が arm×point の 9 rehash 行を記録 → literal validator は「3 要素でない」と拒否。別実装は「arm ごとに3」と読み受理。

   影響: eligible cluster 集合と certified 選択が validator 実装ごとに変わる。

4. `[blocker]` RI-B3 は実在する受理拡大である。

   根拠: `pre_performance_infra_failure` は marker 不在しか要求しない [`record-items-reissue.md:65–70`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:65)。a04 は marker 不在でも性能 raw があれば post-performance、置換不可とする [`addendum-a-reissue.md:277–283`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:277)。

   失敗シナリオ: attempt A に `marker=null`、`reason_code=pre_performance_infra_failure`、1 run の `run_log/raw`、厳密 prefix、failure pointer を置き、attempt B で A を置換 → 再発行稿の表は通るが、a04 では A は post-performance で置換禁止。

   影響: 不利な実 run を置換して適格 8 本から落とせるため、測定値・J・certified 判定が変わる。

5. `[blocker]` RI-B4 は R3 の full-history 要件を満たさない。

   根拠: 再発行稿が要求するのは台帳の再読と current-tip 重複検査だけ [`record-items-reissue.md:215–218`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:215)。a13 は create-only、解放不可を要求する [`addendum-a-reissue.md:919–930`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:919)。

   失敗シナリオ: commit L1 で `(F,1)` を予約 → L2 で削除 → L3 で別 study が `(F,1)` を再予約。L3 tip は重複ゼロなので現稿の verifier は受理する。

   影響: `α₁=0.025` を複数 study が使い、familywise error と `q` の参照が壊れる。

6. `[blocker]` ER-B1 は real。1 operation では科学的主張が矛盾したまま残る。

   根拠: operation は core 221 行だけを置換 [`erratum-core-s7-stresscheck.md:73–99`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/erratum-core-s7-stresscheck.md:73)。core 333 行は `a12` を「型 I 誤りを較正する」仕様と呼び続ける [`preregistration.md:331–334`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:331)。承認済み追補 A の見出しにも同語が残る一方、本文は較正を明確に否定する [`addendum-a-reissue.md:825–838`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:825)。

   失敗シナリオ: stress-check transcript を作成 → §7 と a12 本文を読む consumer は受理するが、core §14 の表を literal に読む consumer は「calibration でない」と拒否。または材料 report が「較正済み」と誤記する。

   影響: a12 受理集合と公表可能な科学的主張が二重化する。

   波及最小の解は、erratum-2 を core 221/333 行の **2 operation** にすることです。未承認 blob 1 枚と validator、合成 hash の更新だけで済み、新 artifact を増やしません。承認済み追補 A は再発行しないでください。825 行の見出しは直後の本文が較正を否定しているため、approval payload と material report に「legacy label であり較正主張ではない」と明記するのが最小です。逐語上の語も消す必要があると裁定するなら、追補 A 全体の再発行ではなく、その一行だけを対象にする別の exact correction が次善です。

7. `[blocker]` SC-B1 は real。ただし Draft 2020-12 固定は解ではない。

   根拠: schema blob は未作成 [`package.md:157–168`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/package.md:157)。さらに上記未閉包があるため一意に生成できない。段 2 は Draft 2020-12 engine を後段へ送る [`s2-plan.md:124–144`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s2-plan.md:124) が、現環境は Draft 7 だけである。

   失敗シナリオ: land 1 で 2020-12 schema を承認し、land 2 の Draft 7 engine が未知 keyword を無視 → extra field を含む receipt が engine A では拒否、engine B では受理。

   影響: schema engine の選択がそのまま受理集合を変更する。

   推奨は **Draft 7** です。必要な `patternProperties`、`propertyNames`、`additionalProperties:false`、`if/then/else` は表現できます。外部 `$ref`・`format` 依存・2020-12 専用 keyword を使わず、duplicate-key と foreign key 等は別の固定 semantic validator へ置く。schema/dialect と正負の conformance vectors を規範とし、engine はその実装として検査する形が、land 1 と land 2 の間で受理集合を動かしません。

8. `[blocker]` pilot で消費する 8 slot の identity が凍結されていない。

   根拠: core は pilot 8 本を固定 [`preregistration.md:171–177`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-07_t139-mainrun-design/preregistration.md:171)。a09 は slot 1〜13 の schedule を発行する [`addendum-a-reissue.md:562–571,603–605`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:562) が、pilot がどの 8 slot を使うかを定めない。再発行稿も replacement の同一 slot しか固定しない [`record-items-reissue.md:231–238`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:231)。

   失敗シナリオ: producer A は `{1,…,8}`、producer B は `{6,…,13}` を pilot に採用。さらに初期結果を見て残り slot を選んでも、各 slot 内 schedule と本数 8 は満たせる。

   影響: 実行順・観測値・pilot 共分散・J が結果依存で変わる。pilot slot 集合を pilot 前に exact に固定する必要がある。

9. `[blocker]` land 2 は「台帳 → manifest」の最初の矢印を実装計画に持たない。

   根拠: D262 は台帳 payload が root と要求する [`decisions.md:12140–12145`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:12140)。一方、段 2 は「manifest を唯一の trust root」とする [`s2-plan.md:524–528`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s2-plan.md:524)。M1/M2 も `F_r` の祖先性と manifest/caller の比較だけで、`F_r:docs/decisions.md` の payload と manifest の一致を検査しない [`同:672–675`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s2-plan.md:672)。

   失敗シナリオ: `approval_fold_commit=F_r` を保った偽 manifest が、攻撃者の record/schema/erratum 三つ組を列挙 → expected digest も manifest 自身から取得 → caller 非依存・祖先検査・自己整合はすべて通る。

   影響: 未承認 blob が承認済み identity になり、受理集合全体を書き換えられる。

   D262 の旧 record と新 record が双方 approved に見える問題も、ここを閉じなければ残ります。段 2 の post-`F_r` 限定文 [`s2-plan.md:290–294`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s2-plan.md:290) は方向として正しいですが、resolver が `F_r` の machine-readable payload を読み、manifest と exact 一致させる必要があります。

10. `[blocker]` Git trust root は `PATH` 差し替えで迂回できる。

    根拠: 既存 `blobref` は `PATH` を継承 [`blobref.py:21–31,138–151`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/blobref.py:21) し、`["git", ...]` を起動する [`blobref.py:162–180`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/blobref.py:162)。参照先の `trial_registry` も同型 [`trial_registry.py:476–500`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/campaign/trial_registry.py:476)。

    失敗シナリオ: producer が `PATH=/attacker/bin` とし偽 `git` を配置 → approved blob bytes 自体は本物を返しつつ、`rev-parse` と `merge-base` だけ「`F_r` は ancestor」と偽装 → pre-`F_r` measurement が通る。SHA の偽造は不要。

    影響: `measurement_head`、fold ancestry、ledger history、blob commit 参照が trust root でなくなる。

    `GIT_DIR`、`GIT_WORK_TREE`、object-directory 系環境変数は allowlist で除かれ、`blobref` は shallow/replace/grafts と tree symlink mode を拒否しており、この部分は良好です [`blobref.py:209–262`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/blobref.py:209)。ただし resolver の全 Git 呼出しを同じ hardening に統一し、実行する Git を絶対 path と identity で固定する必要があります。

11. `[blocker]` R1 と R3 の reservation 時系列循環は real で、通る正例を構成できない。

    根拠: a13 は pilot 前に canonical ledger の予約を要求 [`addendum-a-reissue.md:919–929`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:919)。R1 は manifest・producer・pilot を land 2 の同一 land に置く [`s1-brief.md:11–18`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s1-brief.md:11)。段 2 自身の因果列も正しい [`s2-plan.md:598–620`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s2-plan.md:598)。

    失敗シナリオ: reservation を未 land branch にだけ置く → canonical main に無いため submit を拒否。先に main へ ff → pilot 結果を含む最終 tip を後からもう一度 land する必要が生じ、「同一の一回の land」を満たさない。

    影響: gate の正例が永久に成立せず、pilot・receipt・J・certified 選択が一つも生成されない。これはユーザー裁定が必要な blocker であり、こちらでは解釈を選ばない。

12. `[must-fix]` RI-B1 の一般論は refuted だが、legacy blob の role は payload で明示する必要がある。

    根拠: 再発行稿は旧 path と SHA を固定し [`record-items-reissue.md:8–9`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:8)、旧 §§0–3 の限定部分を逐語 incorporation する [`同:19–27`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:19)。これは一般に有効である。

    失敗シナリオ: `non_approved` を global deny と読む resolver は旧条項を読み込まず受理条件を落とす。逆に旧 blob を `record_items` root として許す resolver は supersession を無効化する。

    影響: 旧 exact 条件が消えるか、旧 record 全体が再承認される。旧三つ組を `incorporated_normative_dependency`、非承認を `not_approved_as_record_items_root` と role 分離すべきである。

13. `[must-fix]` working-file evidence の symlink/TOCTOU 防止が land 2 の所有面に書かれていない。

    根拠: 要件は単一 fd と symlink 拒否を明記する [`record-items-reissue.md:46–51`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:46) が、U2 は loader/writer/semantic verifier の列挙だけ [`s2-plan.md:505`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s2-plan.md:505)。

    失敗シナリオ: validator が `is_symlink()` 後に通常 open → producer が親 directory または leaf を交換 → 検査時と hash/parse 時で別 raw を読む。

    影響: a03、run log、intent、correctness evidence の参照先が入れ替わり、eligible cluster 集合が変わる。dirfd walk、各 component の `O_NOFOLLOW`、同一 fd の `fstat/hash/parse` が必要。

14. `[must-fix]` `verify_prereg_receipt` の理由 payload 自体は pass/fail の言い換えではないが、iteration correctness の構造化 anomaly を運ぶ経路が未指定。

    根拠: plan の predicate payload は pointer・期待制約・digest・依存 edge を持ち十分構造化されている [`s2-plan.md:549–577`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s2-plan.md:549)。しかし U5 は correctness を実行するとだけ記し [`同:508`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s2-plan.md:508)、既存 verifier が返す trx/cycle/edge/reason 構造 [`report.py:4–6,33–75`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/verifier/report.py:4) を receipt、trial ledger、次手へ渡す契約がない。

    失敗シナリオ: G2 cycle 検出 → `correctness_anomaly` と generic predicate だけ保存 →どの trx・rw edge・key が壊れたかが次 iteration へ届かない。

    影響: reject 自体は同じでも、材料 report と次候補生成の入力が失われ、絶対規律 3 を満たさない。

15. `[must-fix]` M24 の `returncode` 枝は恒真・空振り検査になる。

    根拠: mutation は consumer が `admission_telemetry[].returncode` を使う形を検出するとする [`s2-plan.md:695`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s2-plan.md:695) が、exact key は `{ordinal,kind,receipt,fixed_inputs,ledger_evidence}` だけで `returncode` が存在しない [`record-items-reissue.md:205–216`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:205)。

    失敗シナリオ: mutation receipt に `returncode` を足す → schema の unknown-field gate で先に落ち、consumer がそれを権威化しているかには到達しない。

    影響: 「consumer 自己申告非依存」の mutation coverage が実際には成立しない。既存の有効 field で検査するか、`returncode` を evidence-only field として正式に閉包する必要がある。

## Q-A 第三分岐

6 条件は JSON 上の恒真式ではありません。しかし producer 権限内の世界では恒真化できます。

具体例は、preflight observation に 7 列の偽 `/proc/stat` raw、単調な 10 秒時刻、`malformed_reason=short_columns`、`marker=null` を置き、actual run を receipt から消す構成です。全 6 条件を満たしつつ、実際には run 済みにできます。

これは [`record-items-reissue.md:282–291`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-10_t139-manifest-w1/record-items-reissue.md:282) が明記しており、R2(a) が引き受けた残余なので、それ自体は blocker に数えていません。RI-B3 は別問題で、post であるべき実 run を pre に写して置換可能にするため blocker です。

## 承認 payload の判定

- 旧 record を「D262 時点では歴史的に approved、post-`F_r` manifest の root role では non-approved」と時間・role 付きで書く方向は正しい。
- `approved_blobs.commit = B_docs` として blob を fold 前に commit する手順は正しい。既存 D262 の各 blob commit も `F_e` の祖先であることを再確認した。
- 現行 erratum に対する order と `d1782…` / `dfb821…` は実測一致。ただし ER-B1 修正後は erratum SHA と composed SHA を再計算しなければならない。
- manifest が land 1 の `F_r` を literal に持つ構造は自己参照を起こさない。
- `D263.reason[...]` の疑似 selector [`s2-plan.md:239–245`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-w2/s2-plan.md:239) は曖昧である。D263 の誤った二文 [`decisions.md:12170–12175`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:12170) を逐語引用して supersede すべきである。

## 絶対規律と scope

- 規律 1: plan は trace-enabled correctness と trace-disabled performance を別 run・別 allocation に置いており適合。
- 規律 2: anomaly を終端 reject とする点は適合。ただし RI-B3 は不利な性能 run の置換を可能にするので、その部分が違反。
- 規律 3: iteration の定義と事前 correctness は適合。`verify_prereg_receipt` の payload も十分構造化。ただし実 G2 anomaly の還流契約は must-fix。
- R4 が名指しした submitter、intent、PBS、driver、collector、writer、iteration verifier、certified analysis、report、trial registry は U0〜U9 にすべて存在する。U0〜U6 だけの vertical slice は成果物を変えないため、plan 自身のいうとおり途中 land 不可。
- scope 外だが real な層は 2 件:
  1. producer 権限外の raw/exec collector。R2 により非保証として引受済み。
  2. `b03` 個別公表系列台帳と新 core 側 consumer。承認保留裁定により現 wave 外。

## 親 P1〜P6

| P | 独立判定 |
|---|---|
| P1 | **概ね正しい。** local main から docs-only branch を切り exact path allowlist で差分を検査すれば R1 を満たす。第1波コードを失うわけではなく land 2 branch に残る。ただし land 1 後、w2 は `F_r` を merge し旧候補 blob/定数を置換する手順を明記すべき |
| P2 | **誤り。** 現文書は exact 1:1 schema を生成できず、2020-12 固定にも根拠がない |
| P3 | **部分的誤り。** 現行 hash の実測は正しいが approval-ready ではない。ledger→manifest 比較と ER-B1 修正後 hash が必要 |
| P4 | **誤りなし。** `b03` scope 外は裁定と整合 |
| P5 | 段 2 の「親の誤り 5/6」は **refuted 寄り**。親は見積りを確定値とせず「未確定」と明記している。15,420 行も詳細設計前の推定なので `[suspicion]` に留めるべき。a13 の因果循環は別の real blocker |
| P6 | **部分的 real。** 「pilot 8 slot」という表現自体を誤りと断定するのは過大だが、13 slot 中どの 8 個かが未凍結なのは blocker。並列性が runbook だけでなく費用更新規則にも拘束されるという段 2 の指摘は正しい |

## 総括

GO/NO-GO: **NO-GO**  
blocker 件数: **11 件**  
凍結してはいけない文書欠陥: **9 件（blocker 級 8 + legacy 参照 role の must-fix 1。うち 1 件は schema 未作成）**  
scope 外だが real な層: **2 件**