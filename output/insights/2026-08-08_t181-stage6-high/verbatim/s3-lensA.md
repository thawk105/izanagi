結論から言うと、現行の二行置換案は land を止めるべきです。bytes の実測は正しいものの、条件・worker 本数の許可を削り、S06-C の effort を一意に固定できていません。

### A-01 — docs-only まで二本レビューを要求する読みが成立する

- 主張: `実装 wave は` の削除により、義務の適用集合が実装 wave から段 6 全般へ拡大する。許容される wave 実行集合は逆に縮小する。
- 根拠: 現行は [workers.md:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/workers.md:48) の「`実装 wave は…必ず 2 本並列`」。変更案は [s2-plan.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/s2-plan.md:18) の無条件形。一方 [core.md:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/core.md:11) は「段 6 の review 子を省ける」、[core.md:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/core.md:14) は「docs-only は子ゼロでよい」と逐語で許可する。
- 判定: real / must-fix。
- 成果物影響: docs-only・軽量 wave に本来ない review 所見が worklog/insights へ増えるか、契約矛盾を抱えたまま decisions と land 差分が残る。

### A-02 — F146 は「1 本」が stale だとは示していない

- 主張: プランは worker 本数と巡回数を混同している。
- 根拠: F146 見出し自体が [failures.md:3389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/failures.md:3389) の「焦点再レビュー **1 巡**では閉じなかった」。[failures.md:3391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/failures.md:3391) は「4 巡」、[failures.md:3401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/failures.md:3401) は「`regressed` が 0 になるまで回す」。現行の担い手 [operations.md:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/operations.md:85) も対応表と「3 巡」を規定する。訂正 [failures.md:3414](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/failures.md:3414) が stale としたのは「対応表要求の担い手は S06-C」という記述だけで、`1 本` ではない。
- 判定: real / must-fix。プランの [s2-plan.md:102](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/s2-plan.md:102) と [s2-plan.md:107](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/s2-plan.md:107) の「誤った一巡上限」は refuted。
- 成果物影響: 各巡一人でよいという許可が消え、reviewer 数が未規定または増加し、所見数・fix・消費量とその worklog/decision 記録が変わる。

### A-03 — 「意味等価」は逐語照合で refuted

- 主張: 変更後二文は effort 追加だけではなく、既存の条件・許可も削る。
- 根拠: [s2-plan.md:9](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/s2-plan.md:9)〜[s2-plan.md:35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/s2-plan.md:35) の新旧対照から、消える逐語は次の四つ。

  - `実装 wave は` — 義務の適用条件。
  - `並列 fix の` — 何を統合した後かという条件。
  - `1 本` — 一巡に投入してよい reviewer 本数。
  - `でよい` — 許可・十分性の modal。

  `異なるレンズの敵対レビューを必ず 2 本並列で行う` と、統合後に全体を焦点再レビューする本体は残る。
- 判定: real / must-fix。
- 成果物影響: worklog/decision が「stage 6 effort のみ変更」と記録しても、land 差分は wave 適用条件と worker cardinality まで変更した状態になる。

### A-04 — S06-B の除外は一意に読める

- 主張: fix 子まで `review 子` に含まれるという疑義は反証できる。
- 根拠: [workers.md:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/workers.md:52) は `DW-S06-B — 段 6 fix`、[dev-wave.md:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/.claude/commands/dev-wave.md:77) はこれを「fix を codex へ再投する子」として段 5 の「実装子契約」を全文継承させる。[workers.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/workers.md:24) により値は既に `high`。
- 判定: refuted / nit。
- 成果物影響: S06-B へ新 literal や新 pin を加える必要はなく、追加すれば単一正本と checker 受理集合だけが余計に変わる。

### A-05 — S06-C/O16 への適用は一意でない

- 主張: S06-A 内の `段 6 の review 子` が別 leaf の S06-C まで拘束することは、plan にしか書かれていない。
- 根拠: [workers.md:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/workers.md:46) と [workers.md:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/workers.md:65) は別 leaf。[workers.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/workers.md:3) は指定 leaf を worker 起動前に読む契約である。段開始時には A/B/C を読むが、焦点再レビュー直前の条件 dispatch は [dev-wave.md:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/.claude/commands/dev-wave.md:98) で O16 だけを指定し、[operations.md:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/operations.md:83)〜87 に effort はない。
- 判定: real / must-fix。
- 成果物影響: manager が焦点再レビューを未規定/default effort で起動すると、must-fix 集合、insight、decision、最終 land 差分が変わる。

### A-06 — P2 の pin は矛盾した S06-C を受理する

- 主張: S06-A だけの exact pin は「段 6 review 子すべて」を機械固定しない。
- 根拠: プランは [s2-plan.md:56](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/s2-plan.md:56)〜64 で S06-A だけを検査し、[s2-plan.md:68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/s2-plan.md:68) で S06-C を明示的に pin 外にする。現行抽出規則は [check_docs.py:276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:276) と [check_docs.py:1689](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:1689)。メモリ上で A=`high`、C=`max` を置くと、値列は `A=["high"], C=["max"]` でも提案された A-only 条件は `True` だった。
- 判定: real / must-fix。
- 成果物影響: checker が矛盾した contract を受理し、焦点レビューの effort と所見集合が decisions/worklog の宣言から乖離する。
- 修正条件: A と C を個別に `high` pin し、B は継承のため effort literal 不在も検査する。

### A-07 — P1 は T-181 から一般化できない

- 主張: T-181 が支持するのは限定 focused-review packet の記述的結果だけで、初回敵対レビュー二本への外挿ではない。
- 根拠: brief 自身が [brief.md:55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/brief.md:55)〜58 で「実測したのは焦点再レビューのみ」と認める。一次資料は [README.md:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/output/insights/2026-07-30_t181-reasoning-ab/README.md:10) で「名指しした R-1」を endpoint とし、[README.md:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/output/insights/2026-07-30_t181-reasoning-ab/README.md:53) で「この 6 run で劣化を観測しなかっただけ」、[README.md:58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/output/insights/2026-07-30_t181-reasoning-ab/README.md:58) で `experiment_complete=false` とする。[phase3.md:706](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/phase3.md:706) は再走なしの policy 根拠化を禁止する。
- 判定: real / must-fix。
- 成果物影響: 未測定の初回レビューで検出できる所見が変わり、worklog/insights/decision と land fix 集合が変わりうる。
- 注記: P1 は「人間が証拠外挿と承知して全段 6 を選ぶ」という裁定なら成立するが、T-181 の証拠結論としては成立しない。

### A-08 — 「未 pin だから引き下げでない」は D207 の理由を回避している

- 主張: 段 6 が D207 の列挙対象外なのは事実だが、それだけで正しさ側の検討を免除できない。
- 根拠: 親は [brief.md:26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/brief.md:26)〜28 で対象外を根拠にする。一方 D207 は [decisions.md:9891](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/decisions.md:9891)〜94 で paired・blind・非劣性だけを採否根拠とし、理由部 [decisions.md:9901](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/decisions.md:9901) は「検出力を下げる変更は規律 2 の対象」と一般化する。D223 も [decisions.md:10505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/decisions.md:10505) で A/B 未完了なら fail-closed とする。
- 判定: real / must-fix。
- 推論: `high` exact pin は将来の `max` を拒否するため、未規定状態からでも検出力の高い経路を閉じうる。効果方向は未測定なので「下げていない」とは証明できない。
- 成果物影響: P4 decision が「未 pin 箇所なら未認証 evidence で固定可能」という抜け道になり、後続 worklog/decisions の受理根拠を弱める。
- 修正条件: 新 decision 自体は妥当な器だが、D207 の段 6 限定・人間裁定による明示的例外／supersession として記録する必要がある。

### A-09 — evidence-aware な再裁定が記録上存在しない

- 主張: brief の「親は evidence 欠落を承知」は、ユーザーが欠落開示後に再裁定した証拠ではない。
- 根拠: 引用されたユーザー逐語は [brief.md:5](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/brief.md:5)〜6 の「過去に差がなかったと思う。それなら high」であり、未認証事実の開示を含まない。ところが [brief.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/brief.md:16) は親の認識だけを記す。[core.md:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/core.md:35) は承認済み裁定の前提を覆す新事実を再裁定へ返す契約。
- 判定: real（提示記録上）/ must-fix。別の逐語再裁定が実在するなら、その引用を brief に足せば refuted。
- 成果物影響: 現状のままでは worklog/decision が「ユーザーは証拠限界を承知して採用」と事実以上に記録する。

### A-10 — bytes 実測への疑義は refuted

- 主張: 親の `25,196 / headroom 4` と S06 三節の effort 0 件は再現した。
- 根拠: HEAD `6cc3e59a7102c2f6fd93896ebb445a4f93805ea0` で `wc -c` は core `8,646`、workers `4,575`、operations `8,301`、mutation `3,674`、合計 `25,196`。[check_docs.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/tools/check_docs.py:254) の上限は `25,200`。同じ節抽出・regex では A/B/C が各一節、値列はいずれも `[]`。計画二置換の `+2` も再現した。
- 判定: refuted / nit。
- 成果物影響: 測定 drift による worklog・insight・land 差分の変更はない。

### A-11 — より安全な byte 捻出案は存在する

- 主張: `1 本でよい` や `実装 wave は` を落とさず、A/C を個別 pin できる余地を作れる。
- 根拠: [operations.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/operations.md:3)〜4 の導入二文は、発火条件・正本・直前読了・停止条件を保ったまま縮約できる。静的候補は次のとおり。

  - [workers.md:48](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/workers.md:48)
    `review 子は `reasoning=high`。実装 wave は異なるレンズの敵対レビューを必ず 2 本並列実行する。`
  - [workers.md:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/workers.md:67)
    `並列 fix の統合後、全体の焦点再レビューは各巡 `reasoning=high` の子 1 本でよい。`
  - [operations.md:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t181-stage6-high/docs/dev-wave/operations.md:3)
    `発火条件は入口の条件 dispatch、成立時の実行手順だけは本書が正本。該当節を操作直前に読み、停止条件を迂回しない。`

  byte 差は順に `+36 / +30 / -67 = -1`、aggregate `25,195`、workers `4,641`、operations `8,234`、余地 `5`。旧 operations 導入逐語の live consumer は静的検索で同ファイル以外に見つからなかった。
- 判定: real / must-fix。文言は候補だが、現行の危険な削除が byte 上不可避という主張は refuted。
- 成果物影響: land 差分は intended な A/C effort 固定だけを表し、worklog/insights/decisions に cardinality や docs-only 条件の暗黙変更を持ち込まない。

pytest、`check_docs` 全走、provenance は実行していない。行ったのは read-only の逐語照合、byte 計数、現行 parser によるメモリ上の静的抽出だけであり、「緑」とは報告しない。

## 総括

- 現行二行置換は `実装 wave は` と `1 本でよい` を失うため land を止める。
- F146 の stale 対象は巡回・対応表担い手であり、各巡の reviewer 本数ではない。
- S06-A と S06-C は別々に `high` を明記・pin し、S06-B は継承のままにする。
- T-181 は未認証かつ focused review 限定で、P1 の全レビュー一般化を証明しない。
- evidence 欠落開示後のユーザー再裁定を逐語で残し、D207 との限定例外関係を新 decision に明記する。
- byte 実測は正しいが、安全な代替縮約があり、上限は現在案を正当化しない。