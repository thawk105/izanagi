## 所見

1. [missing-scope insight:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-missing-iterations-scope/README.md:52) — 数の算術は再現できるが、`197` の帰属を campaign ID で固定していない。

   - `270 = 3 workload × 15 point × (legacy 1 + performance 5)`。3 workload は [preregistration:400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/b10-backoff-shape-preregistration.md:400)、15 point は [driver:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/orchestrator/campaign/b10_backoff_shape_sweep.py:96)、6 verify 枠は [preregistration:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/b10-backoff-shape-preregistration.md:423) と [pipeline:131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/orchestrator/campaign/pipeline.py:131) から出る。
   - `294 = (15 + 15 + 15 + 4) started attempt × 6`、`287 = 90 + 85 + 90 + 22`、差 `7` は [missing-scope insight:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-missing-iterations-scope/README.md:76) から再現できる。
   - `197 = e3de15eb 90 + balanced 85 + read-heavy 22`、`270 - 197 = 73`。`360 = 4 campaign × 15 × 6`、`360 - 287 = 73` も一致する。
   - ただし [trace insight:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:26) の「残る 197」は `068fd2cd 90 + balanced 85 + read-heavy 22` で、同じ数値だが別の write-heavy campaign である。[plan:18](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/artifacts/plan-out.md:18) の archive 追記案は `e3de15eb` を明記していない。
   - 放置時の成果物影響: 値は同じでも provenance の campaign 集合が入れ替わり、台帳・レポートの参照が誤る。
   - 直し方: `197` を出す箇所すべてで、採用する 3 campaign ID を列挙し、「4 campaign 中の残り 197」と別集計であることを固定する。なお raw WAL は許可された repo 内資料に無いため、今回は表の再計算までで、WAL の独立再集計ではない。

2. [brief:70](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/brief.md:70) と [parent findings:38](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/parent-independent-findings.md:38) — 「294 の完全性分母は archive 2 file だけ」は refuted。

   実際に誤った予定分母を主張する未訂正箇所は、[archive 1189:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1189.md:23) と、非 archive の [trace insight:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:78) である。反対に archive 1197-1198 の [456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1197-1198.md:456) と [873](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1197-1198.md:873) は訂正またはタスク定義であり、誤用箇所ではない。さらに archive 1189 は [58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1189.md:58) と [448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1189.md:448) から当該 insight を直接参照し、A-6 insight も [164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_paper-story-a6-certification/README.md:164) から参照する。

   数字を使わない閉包も確認した。preregistration の「全 workload」「block あたり 15 点」([663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/b10-backoff-shape-preregistration.md:663)) は正しい 270 母集団を定める規範であり、formal-run の「15 変種すべて」([39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-08-31_t1905-b10-formal-run/README.md:39)) と trace insight の「15 変種 × 6」([22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:22)) は完走済み `e3de15eb` だけに限定されているため誤りではない。

   - 放置時の成果物影響: archive を直しても一次 insight の読者と A-6 の参照鎖には `294 / 287 / 7` が予定完全性として残る。
   - 直し方: trace insight を第三の訂正対象に加え、既存 bytes を書き換えず、同 insight 内で直接到達できる追記訂正を行う。

3. [archive 1187:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1187.md:9) — `cell`、`variant`、`attempt` が混ざっている。

   同行は「15 cell 中 3 cell」と書くが、性能 `fitness_tps` は全件 null であり、完了したのは 3 variant の認証 attempt である。1 workload の性能 cell は `3 block × 15 point = 45`。計画の [派生表:93](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/artifacts/plan-out.md:93) は当該箇所を引用しつつ「3 変種」へ無言で正規化している。

   - 放置時の成果物影響: 3/15 の認証進捗を性能 cell の 3/15 と読み、存在しない性能 record を受理済みと数えうる。
   - 直し方: archive 自体は追記訂正とし、派生一覧では逐語と正しい単位を別欄で示す。

4. [missing-scope insight:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-missing-iterations-scope/README.md:178) と [plan:89](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/artifacts/plan-out.md:89) — 「4 件」は文書単位の索引としても、欠測母集団由来の値の集合としても全数ではない。

   - `15 認証単位` は登録された 15 variant を認証単位へ写した構造数であり、238 反復や欠測 attempt から導いた値ではない。計画自身も [91](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/artifacts/plan-out.md:91) でそう認めている。
   - `84.4 マイクロ秒/commit`、相関 `0.9991 / 0.4044`、係数 `-0.309` も同じ 238 反復母集団から出ている。[trace insight:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:148) と [186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:186) に実在する。
   - read-heavy の別外挿「約 23 時間」は [archive 1187:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1187.md:11) にあり、計画は同じ行群を「約 25 時間」の出現箇所として扱って数値差を落としている。
   - balanced の「約 6 時間半」も、未完 attempt の legacy 1 回を含む 6 時間 wall を完了 14 variant で外挿した値で、[design:115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/b10-multinode-formal-run-design.md:115) と [archive 1190:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1190.md:300) にある。
   - 「約 7 倍」も別に漏れている。詳細は後述する。
   - 放置時の成果物影響: balanced の投入可否、read-heavy の予算、検査並列化の費用見積りに使われる値が一覧外に残る。
   - 直し方: 一覧単位を「文書」ではなく「数値主張とその母集団」に定義し直し、構造数を分離し、上記の派生値を全数台帳へ追加する。各値への追記可否はこの検査では決めない。

5. [trace insight:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:171)、[D1489:46501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:46501) — 23 分の帰属と `max` が誤っている。

   一次資料は所要を、ベンチ本体、トレース書き出し、数え直し、解析、直列化可能性検査、一時 dir 操作、WAL 書き込みを含む「混合区間」であり、「検査器そのものの費用ではない」と明記する。一方、D1485、D1489、A-6、T-2191 は「直列性検査 1 回」と帰属している。また観測帯は [trace insight:194](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:194) の `1346.9-1465.6 秒`、すなわち最大約 24.43 分であり、D1489 の「max 23 分」は反証される。10 回なら 3.83 時間でなく約 4.07 時間、12 時間との比は約 3.1 倍でなく約 2.95 倍になる。なお plan の [92](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/artifacts/plan-out.md:92) がこの全帯を `constant-mu2` の帯と断定する根拠は、投影された一次資料にはない。

   - 放置時の成果物影響: A-6 の walltime 値自体は変わらない可能性が高いが、台帳の費用帰属、3.83 時間、約 3.1 倍という根拠値が誤る。
   - 直し方: D1489 と A-6 insight を追記訂正し、測定量を混合区間として扱い、`max` を用いるなら観測最大値で再計算する。

6. [plan:89](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/artifacts/plan-out.md:89) と [parent findings:28](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/parent-independent-findings.md:28) — file:line 監査には次の食い違いがある。

   | 計画または親のアンカー | 検算 |
   |---|---|
   | `trace:179` | 表見出し。値は [181-184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:181)。 |
   | `trace:204` | T-2191 への遷移文。15 認証単位は [207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:207)。 |
   | `1189:442` | 22-24 分の行。15 認証単位は [445](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1189.md:445)、70.0-87.0 は [447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1189.md:447)。 |
   | `1187:9`, `1187:431` を 23 分の位置とする | 逐語はそれぞれ 5 時間 5 分と T-ID 見出し。23 分は [13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1187.md:13) と [432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1187.md:432)。 |
   | `D1485:46378`, `D1489:46501`, `D1489:46503`, `A-6:100` | いずれも実在し、逐語と一致する。 |
   | `formal-run:150` を 5 時間 5 分の位置とする | 行 150 は「5 時間」。5 時間 5 分は同文書に無く、archive 1186 と設計文書にある。 |
   | `D1489:46501` を 5 時間外挿の位置とする | 行 46501 は 23 分。5 時間・3/15 は [46502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:46502)。 |
   | `formal-run:147`, `1186:58`, `1187:9`, `1189:38` を 1690 万の位置とする | 数値本体は順に [148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-08-31_t1905-b10-formal-run/README.md:148)、[60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1186.md:60)、[13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1187.md:13)、[39](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1189.md:39)。 |
   | `trace:194`, `trace:200` を 1690 万の位置とする | 194 は約 7 倍。1690 万は [201](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:201)。236 は `16.90M` の具体例で、同じ表記ではない。 |
   | brief の L4 | [brief:60](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/brief.md:60) は「正式走 insight」と呼びながら trace insight:201 を指す。元の正式走 insight は `2026-08-31...README.md:148`。 |
   | 親の `23 分`、`5/25 時間`、`1690 万` の全数表 | 引用行は実在するが全数ではない。欠落箇所は次節の表のとおり。 |

   - 放置時の成果物影響: 実装者が別の記述へ訂正を当てたり、レビュー台帳が根拠行を再現できなくなる。
   - 直し方: 行を実際の値の行へ更新する。将来残す規範文書では行番号でなく節名と識別子も併記する。

7. [plan:13](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/artifacts/plan-out.md:13) と [parent findings:49](/home/SFC/tanab/.claude/jobs/48609c35/tmp/wave-t2201-b10-denominator/parent-independent-findings.md:49) — 親の P1-a 更新が計画へ反映されていない。

   親の独立検査は H2 直後の blockquote へ差し替えたが、計画は依然 EOF の H3 を実装案にしている。archive 規約は [archive README:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/README.md:3) と [worklog:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/worklog.md:55) で訂正注記を許す。見出しを足さない blockquote なら H2 制約にも `NEXT_ACTION_RE` にも触れない。

   - 放置時の成果物影響: 値や受理集合は変わらないが、訂正が約 450 行後ろへ隠れ、誤った本文だけが参照されやすい。
   - 直し方: 計画を親の更新済み案へ同期し、H2 直後の訂正注記に一本化する。

## 派生記述の一覧の検算

自己索引である entry 1198、missing-scope insight の一覧、T-2202 定義、逐語複製、値を持たない carry-forward は、下流での再利用ではないため除外した。

| 4 件の記述 | 出現箇所の全数 | 母集団 | 欠測の掛かり方 |
|---|---|---|---|
| T-2191 の回帰単価・認証単位 | 直接集計: [trace:148-156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:148)、[177-208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:177)。下流: [1189:31-36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1189.md:31)、[442-448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1189.md:442)。 | performance 238 反復 = 75 + 75 + 70 + 18。 | read-heavy 18 のうち 3 反復が未 commit `constant-mu2` attempt。回帰値、84.4、相関値には掛かる。15 認証単位は登録構造なので掛からない。 |
| 1 回 23 分、22-24 分、および判断への利用 | 元観測: [trace:173-175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:173)、[194-198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:194)。下流: [1187:9-13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1187.md:9)、[431-433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1187.md:431)、[1189:442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1189.md:442)、[D1485:46378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:46378)、[D1489:46501-46504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:46501)、[A-6:96-104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_paper-story-a6-certification/README.md:96)。 | read-heavy の高 commit 帯の 3 秒 performance 反復。ただし計測量は検査器単体でなく WAL 時刻差の混合区間。 | 高 commit 3 点の一つが、5 回中 3 回だけ観測された未 commit attempt。23 分を `max` とする一般化は成立しない。 |
| read-heavy の 5 時間系と外挿 | [formal-run:68-72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-08-31_t1905-b10-formal-run/README.md:68)、[140-152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-08-31_t1905-b10-formal-run/README.md:140)、[1186:14-17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1186.md:14)、[1187:9-13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1187.md:9)、[design:16-31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/b10-multinode-formal-run-design.md:16)、[115-122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/b10-multinode-formal-run-design.md:115)、[183-196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/b10-multinode-formal-run-design.md:183)、[314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/b10-multinode-formal-run-design.md:314)、[D1480:46276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:46276)、[D1489:46502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:46502)、[D1509:47044](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:47044)、[design insight:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_t1905-b10-multinode-design/README.md:32)、[A-6:98-103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_paper-story-a6-certification/README.md:98)。 | request `965996` の job wall と、commit 済み 3 variant。外挿は約 23 時間と約 25 時間の二系統。 | wall には未 commit 4 番目の legacy 1 + performance 3 も含む一方、除数は完了 3 variant。残り 2 performance と未開始 11 variant は無観測。 |
| read-heavy の 1690 万 commit | [formal-run:147-151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-08-31_t1905-b10-formal-run/README.md:147)、[1186:58-62](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1186.md:58)、[1187:9-13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1187.md:9)、[1189:38-41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/archive/worklog-phase3-0902-1189.md:38)、[trace:194-202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:194)、[235-236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:235)。 | read-heavy の飽和した 3 point の performance 反復。15-point 格子全体の集計ではない。 | 3 point の一つは未 commit `constant-mu2` attempt の n=3。平均 16.928M が 1690 万への丸めに含まれる。 |

この4行以外に、同じ選択規則なら「約 7 倍」と balanced の約 6 時間半が追加対象になる。したがって、計画と親の表を「全数」とは評価できない。

## 親 provisional への評価

- **(P1-a) 訂正注記の追記位置:** brief の EOF H3 案には不同意。親の独立検査で更新された、archive H2 直後の見出しなし blockquote 案には同意する。機械契約を乱さず、本文を読む前に訂正へ到達できる。計画が古い案のままなのが問題である。
- **(P1-b) 報告様式の宿り先:** 同意。設計文書 §6 (4) は全 job 終端後の一回集約を定義し、D1509 も集約側を規則の宿り先にしている。ただし文書規約であり、現行 `_write_reports` を機械強制したことにはならない。
- **(P1-c) 派生記述 4 件の束ね方:** 不同意。T-2191 を文書単位で1件と呼ぶこと自体は可能だが、70.0-87.0 と15認証単位は欠測への帰属が逆である。さらに約7倍とbalanced約6時間半が漏れるため、「欠測母集団由来4件」という閉包にはならない。

## 親の純増 2 件の裏取り

- **D1489 の「23 分」: real。** [D1489:46501-46504](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/docs/decisions.md:46501) は同じ 23 分を明記し、10 回を 3.83 時間へ換算して `12:00:00` の数量根拠に使っている。A-6 insight も同じ計算を再掲する。ただし唯一の理由ではなく、attempt 全損の非対称性なども理由である。また `max 23 分` という限定は観測最大約24.43分に反している。
- **「約 7 倍」: real。** [trace insight:194-198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-trace-truncation/README.md:194) に主張があり、[missing-scope insight:191-203](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2201-b10-denominator/output/insights/2026-09-02_b10-missing-iterations-scope/README.md:191) が 6.83-7.22 倍を再現する。3 point の一つが未 commit `constant-mu2` の n=3 なので、欠測 attempt を含む母集団由来であり、4件一覧から漏れている。

## 総括

数式 `270 / 197 / 73`、`294 / 287 / 7`、`360 / 287 / 73` は、母集団を固定すれば整合する。  
ただし `197` は異なる campaign 集合で同値になっており、ID の明記が必要である。  
294 の誤用は archive だけでなく trace insight にも残るため、2ファイル計画では閉包しない。  
派生4件は全数でなく、15認証単位の帰属、約7倍、balanced約6時間半を再整理する必要がある。  
23分は実在する下流入力だが、検査器単体への帰属と `max` の一般化は成立しない。  
テスト・実走は行わず、静的な文書・コード・成果物検査だけを実施した。