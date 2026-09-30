# 段 6 裁定 — 道具 (単位 B) の fix

入力: smoke 実走 (request 36271.nqsv、Elapse 93 S、evidence/smoke/)、レビュー A (`out/s6-review-A.md`、修理 hunk に所見なし・message 2 件 → 親が修正済み、commit X に反映)、レビュー B1 (`out/s6-review-B1.md`)、B2 (`out/s6-review-B2.md`)。

| # | 出典 | 所見 | 判定 | 処置 |
|---|---|---|---|---|
| S6-1 | smoke 実走 (親) | runner 587 行 `defines = {**BASE_DEFINES, 'CCBENCH_TRACE': str(arm['trace'])}` が arm 定義の `"trace": true` を `True` にし、T arm の compile 命令が `-DTRACE=True` になった。`#if TRACE` で未定義識別子 `True` は 0 に評価されるので T arm は実質 TRACE=0、trace_*.log が 0 本、verifier rc=2 (`no trace_*.log files`)、T の 6 走が R0 判定不能 (success=false で fail-closed に止まった) | real, must-fix | fix: `CCBENCH_TRACE` を `1`/`0` で渡す。build 後に各 arm の実 compile 命令 (compile_commands) の `-DTRACE=` が arm の trace と一致 (`1`/`0`) することを確かめ、違えば停止 |
| S6-2 | B1 must | run_judge.sh の `result_name` が失敗理由に依らず常に「D297 不合格 (意図した修理差分)」 | real, must-fix | fix: 両 compiler の `expected_failure` が真のときだけその名、他は「D297 不合格 (理由未確定)」。**実走結果 (evidence/judge/) は両方 expected_failure=true だったので記録の値は変わらない**が、fix 後の script で取り直す (Elapse 9 S) |
| S6-3 | B1 should | D297 の成果物に F→X の source diff と修理 hunk の照合が無い | real | fix: `git diff F X` を保存し、変更 path 数・hunk 数を report に記録 |
| S6-4 | B1・B2 should | F 側対照の成立表示 (`T_F_G2_control_established`・`F_class_a_control_established`) が R0 不成立・verifier 判定不能の走を合算しうる | real | fix: 対照の件数と成立判定は R0 を通った有効な F 走だけ、無効走は別件数 |
| S6-5 | B2 nit | 未使用の `legacy_selftest()` | real (nit) | fix で削除 (呼ばれていない関数だけ) |
| S6-6 | B2 must | build・D297・trace の結果が射影に無い | refuted as code defect (記録段の義務) | 記録段で一次資料・最終報告に全結果を載せる。push 依頼は本走の判定後 |
| S6-7 | B2 should | format の通過を CI 全体と言い換えない、棚卸しは適用可否に限る | real (記録) | 記録段で守る (build は CI build 36272 の結果を独立に書く、棚卸しは静的意味判定を別欄) |

## 追記 — fix 後 (fix 子 `out/s6-fix-B.md`、焦点再レビュー 1 巡 `out/s6-focus-1.md`)
- S6-1・S6-3・S6-4・S6-5 closed (焦点レビュー)。S6-1 は fix 子が「最初の smoke の N_X も `-DTRACE=False` だった」ことを実物で見つけた (親の投げ文は N_X を正例と誤記。N・P arm も真偽値の文字列化で `False` になり、`#if` で偶然 0 と同じ意味だった)。fix 後の実 build での確認は smoke2 (36299) で行う。
- S6-2 partial の残り「両 compiler rc=0 のとき `D297 合格`」は **refuted (親裁定)**: 親の fix 投げ文がこの枝を明示指示しており、両方 rc=0 は検査器の判定として実際に合格なので名前は正確。上表の「他は理由未確定」の書き方が不正確だった。取り直し judge2 (36298、Elapse 9 S) は両 compiler とも `expected_failure=true`・`result_name`=「D297 不合格 (意図した修理差分)」・F→X の差分 1 path・1 hunk で、この枝は実走に現れない。焦点レビューはこれで閉じる (2 巡目は起動しない)。

smoke の観測 (TRACE=0 相当で計器は動作): X は commit 側 class A 0・recheck_abort 775、F は class A 101。見積りは T の verify が走っていないので使えない → fix 後に smoke を取り直す。
変異: izanagi 実装面の差分 0 は不変 (道具は repo 外)。
