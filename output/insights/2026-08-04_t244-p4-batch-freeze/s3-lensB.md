## 所見一覧

- **B-01 / real / blocker — U-D 第一級 batch と結合面が矛盾している**

  根拠: U-D は `batch-committed` 相当 event に cardinality と全候補 digest を固定する裁定である（[s4-adjudication.md:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/output/insights/2026-08-04_t244-p3-origin-ledger/s4-adjudication.md:118)、[docs/worklog.md:1333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/worklog.md:1333)）。一方プランは結合面を `batch_commitment_sha256` 一本としつつ、次行では ledger が canonical bytes・digest・cardinality・policy を格納すると書き、さらに裁定済みの「非第一級」分岐も残している（[s2-plan.md:37](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:37)、[s2-plan.md:39](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:39)、[s2-plan.md:40](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:40)）。brief erratum はこの矛盾を解かず、互換性を宣言しただけである（[brief.md:67](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/brief.md:67)）。

  放置時の影響: ledger の受理対象が「再検算可能な第一級 batch event」か「不透明 digest」かで分裂し、canonical member・cardinality・policy の値と proof-chain 参照が実装ごとに変わる。

- **B-02 / real / blocker — `batch=set`・一 member 一結果・最大 32 は未裁定の batch identity を既成事実化する**

  根拠: プランは重複拒否・辞書順 set、`1 < minimum_cardinality <= 32`、member ごと一結果を固定する（[s2-plan.md:7](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:7)、[s2-plan.md:67](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:67)、[s2-plan.md:83](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:83)）。しかし予算裁定は `Q >= 1 + 32R + E_min` であり、replicate/query ordinal の identity は裁定されていない（[worklog-phase3-0804-161.md:24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/archive/worklog-phase3-0804-161.md:24)）。プラン自身も、その形では反復測定や全 query slot を表せず別裁定が必要と認めている（[s2-plan.md:226](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:226)）。

  放置時の影響: replicate/query ordinal を含む正規 batch が拒否または同一 member に潰れ、cardinality・commitment digest・受理集合が裁定前に 32 distinct wire へ縮小される。

- **B-03 / real / blocker — trusted ledger の結果を公開用二値へ早期縮退し、evidence/proof 参照を失う**

  根拠: `"accepted" | "rejected"` は active window の公開 API alphabet であり、詳細は control ledger 側に残す契約である（[README.md:245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/output/insights/2026-08-01_t244-reflux-design/README.md:245)、[README.md:270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/output/insights/2026-08-01_t244-reflux-design/README.md:270)）。旧 P3 設計も `result_ref_sha256` を持つ（[P3 s2-plan.md:77](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/output/insights/2026-08-04_t244-p3-origin-ledger/s2-plan.md:77)、[P3 s2-plan.md:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/output/insights/2026-08-04_t244-p3-origin-ledger/s2-plan.md:289)）。本プランは outcome と任意 class hash だけを保持し、receipt に結果も evidence digest も含めない（[s2-plan.md:25](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:25)、[s2-plan.md:94](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:94)）。

  放置時の影響: 異なる verifier evidence が同じ terminal 値へ潰れ、consumer は結果の根拠を再導出できず、proof chain が未裏付け outcome を受理しうる。

- **B-04 / real / blocker — `abort()` が seal 非公開を早期 terminal channel と fresh-session で迂回できる**

  根拠: frozen 後は結果数に関係なく abort でき、部分結果を破棄して `aborted` receipt を公開できる（[s2-plan.md:33](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:33)、[s2-plan.md:95](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:95)）。さらに別 `BatchSession` の開始を防げないことも認めている（[s2-plan.md:228](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:228)）。元設計は early stop 時も残 slot を tombstone 化して公開 transcript 長を固定する（[README.md:279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/output/insights/2026-08-01_t244-reflux-design/README.md:279)）。また `record_result()` の caller が outcome 自体を渡すため、trusted producer と観測者の境界も未定義である（[s2-plan.md:83](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:83)）。

  放置時の影響: 部分結果に条件付けた abort の有無・時刻・terminal kind が結果 bit を運び、次 session の候補受理集合を適応的に変えられる。

- **B-05 / real / major — origin-total policy を caller 選択の session-local policy にしている**

  根拠: `Imax/Qmax/Kmax` は origin ごとの総予算である（[README.md:270](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/output/insights/2026-08-01_t244-reflux-design/README.md:270)）。D147 も値は authority が入れるとしている（[docs/decisions.md:7208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/decisions.md:7208)）。プランは I/Q だけを origin-total と除外し、Kmax と floor は任意に生成できる `BatchPolicy` へ置く（[s2-plan.md:21](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:21)、[s2-plan.md:24](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:24)）。authority receipt や一 origin 一 batch の強制はない。

  放置時の影響: session を作り直すたび floor/Kmax 値と disclosure 枠が新品になり、origin-total の受理上限を超える batch/class が受理される。

- **B-06 / real / major — class reference の自己申告により Kmax 検査が恒真化する**

  根拠: class referent の実在・意味・完全性を明示的に保証外としながら、caller が渡す 64hex tuple の件数だけで `<= Kmax` を判定する（[s2-plan.md:27](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:27)、[s2-plan.md:28](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:28)、[s2-plan.md:90](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:90)）。空 tuple や無関係 hash で常に下回れる。これは D150 が未定義のまま残した「実装のふりをした非適用」に該当する形である（[docs/decisions.md:7436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/decisions.md:7436)）。

  放置時の影響: disclosure tuple の値・参照集合を空または架空にでき、実際の公開 class 数を変えずに Kmax 検査だけ PASS する。

- **B-07 / real / major — DW-O13 の「実在 field」判定と全層 scope が成立していない**

  根拠: brief は wire member を実在 field とする一方、発火 production path は存在せず test だけが consumer とも書く（[brief.md:32](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/brief.md:32)、[brief.md:56](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/brief.md:56)）。静的検索でも `reflux_ir` の production 参照は同 module 自身だけで、canonical state も production 到達性ゼロとしている（[docs/worklog.md:1321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/worklog.md:1321)）。producer・第一級 ledger・driver・consumer/P7・proof chain は全て scope 外である（[s2-plan.md:47](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/s2-plan.md:47)、[docs/decisions.md:7202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/docs/decisions.md:7202)）。不足層は列挙されるだけで、所有・順序・受理条件を持つ裁定パッケージになっていない。

  放置時の影響: 現行 production 値は何も変わらない一方、非発火 leaf が P4 の実装参照として残り、将来 ledger FSM との二重実装または cap-lift の誤算入を誘発する。

- **B-08 / real / minor — 「純増検出力＝本 wave のテスト全部」は過大一般化**

  根拠: exact な P4 非公開検査は見つからないが、T-126 には member order の事前固定、全二 member 完了前の terminal 拒否、terminal suffix 拒否が既にある（[series.py:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/qualification/series.py:142)、[series.py:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/qualification/series.py:177)、[test_t126_qualification_driver.py:215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_t126_qualification_driver.py:215)）。duplicate initial submission の既存検査もある（[test_t126_qualification_artifacts.py:495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/tests/test_t126_qualification_artifacts.py:495)）。したがって brief の「全部」は fault-class 会計として成立しない（[brief.md:49](/work/1/SFC/tanab/izanagi-jobs/c0d1a028/t244-p4-batch-freeze/brief.md:49)）。

  放置時の影響: production の受理集合は変わらないが、検出力・独立系譜の記録値が水増しされる。

## 反証不能だった主張

- **反証不能:** U-A〜U-G が裁定済みで、U-D が batch 第一級、U-G が producer/P7 まで含める、という brief erratum の状態訂正自体は正しい。
- **反証不能:** `reflux_ir.parse_wire()` / `encode_wire()` は実在し、exact 5 ASCII bit wire、固定 `RefluxIRError`、cause/context 非開示という契約を持つ（[reflux_ir.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_ir.py:19)、[reflux_ir.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_ir.py:47)、[reflux_ir.py:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/reflux_ir.py:99)）。プランの固定例外方針はこの慣行と整合する。
- **反証不能:** campaign package に exact な P4 batch-freeze 実装は存在しない。見つかった `batch` は git `batch-check` と CCBench の batch commit counter で別物だった。
- **反証不能:** exact な「候補集合を commit し、全結果を seal まで API から返さない」E2E テストは既存 tree に見つからなかった。ただし B-08 の部分重複はある。
- **反証不能:** 現時点で `main...HEAD = 0/0`、submodule は初期化済み、host は `pegasus02`。歴史的な `check_wave_startup rc=0` 自体のログは job artifact に無いが、現在値は一致した。
- **反証不能:** `MAX_APPROVED_GENERATIONS = 1` は不変である（[p3_autonomous_workload_trial.py:133](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p4-batch-freeze/orchestrator/campaign/p3_autonomous_workload_trial.py:133)）。本プランは cap-lift・凍結成果物を編集しないため、D150 の境界テスト同時更新義務はこの wave ではまだ発火しない。
- **反証不能:** 「prototype」「P4 未充足」「production 到達性ゼロ」という限定文言は明示されている。ただし文言だけでは B-01〜B-07 の実効性欠如を閉じない。
- **反証不能:** floor/Kmax に既定値を置かない方針自体は裁定境界に沿う。問題は値の literal ではなく、B-02・B-05 の identity、authority、適用範囲である。

## GO・NO-GO

**NO-GO。現行 `s2-plan.md` を採用して実装段へ進めてはならない。**

少なくとも次を裁定パッケージへ戻す必要がある。

- standalone leaf を許すなら pure commitment codec までに限定するか、P3 再起票 wave 内の第一級 batch reducer/event FSM として作るか。
- member identity を distinct wire とするか、query/replicate ordinal を含めるか。
- result evidence、abort/tombstone、固定 transcript、origin 内再開始禁止をどう表すか。
- Kmax の authority・origin-total 計数・class referent 完全性をどの層が検証するか。
- producer、ledger、driver、consumer/P7、proof chain の結線順と正負の受理条件。

## 総括

brief erratum は「U-D は裁定済み」という事実訂正には成功したが、独立 FSM leaf という旧 scope を正当化していない。codec 部分には再利用可能性がある一方、lifecycle・policy・result schema は第一級 origin ledger と分離すると二重実装または非発火 prototype になる。特に set/32 制約、evidence 消失、途中 abort、session-local Kmax は裁定境界と実効性の双方で採用阻止級である。

検査は静的読取りのみ。pytest・ビルド・編集は実施していない。