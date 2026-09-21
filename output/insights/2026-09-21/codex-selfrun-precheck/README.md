# Codex 実装子 (author / fix) の login self-run precheck — 裁定パッケージ (2026-09-21)

authority: none
default_effect: no-state-change

wave: `dev-wave-codex-selfrun-precheck` (背景 job、ユーザー直接起動の precheck、T 番号なし)。起点 local main `5efd69367` (fresh worktree、開始 gate rc=0、07:44 JST)。実装・docs の変更は無い (本 README と worklog fragment のみ)。依頼逐語は `verbatim/origin.md`。

## 0. 結論 (3 行)

- **子は login sandbox で test file の自走 harness を実行できる** — hook は拒否せず (静的判定 rc=0、live gate rc=0)、probe の author 子は指定 3 file をいずれも rc=0 で実走した (3 / 22 / 38 件、1.6〜3.3 秒、35〜57 MB、codex 10 call / 128.9 秒)。作業 repo の tracked / index / HEAD は不変。
- **ただし「hook が拒否しない」と「login で走らせてよい」は別である。** 全 test file 369 本中 232 本 (約 63%; 自走 harness を持つ 314 本を分母にすると約 74%) の自走 harness は `pytest.main([__file__])` へ委譲する in-process pytest で、`tools/run_tests.py` の admission (空きメモリ判定 + cgroup 上限 scope) を通らない。guard が見ないのは script file 越しだからで (D103 決定 (5))、許可ではない。この境界 (`DW-M08` の「login 実行が許される file」) は D2195 でも明文でなく、本 wave は定義しない。
- **裁定対象は案 A (条件付きで prompt に self-run を足す) と案 B (足さない、現状の未実走) の択一。** 親の推奨は、裁定が下りるまで案 B を既定とし、案 A は「名指しの 1 file・1 回・子の自己検証に限る狭い条件付き許可」をユーザーが明示裁定した場合だけ適用する候補として返す (`DW-M08` の一般境界は定義しない、§4)。案 C (`python3 -c "…pytest.main…"`、T-2810 / T-2814 が実際に使った形) は不採用を推奨、案 D (`run_tests.py` の sandbox 対応) は今回の対象外。self-run は計測でも受入でもない。

## 1. 依頼と読み替え

- 依頼: 子が「実装済み・未実走」で返し親が焦点走を dispatch してから fix 巡へ戻す往復 (T-2792 / T-2796) を減らせるか、自走 harness を子が login で実行できるか (hook 拒否対象か・rc・所要) を実装差分ゼロの probe で実測し、裁定パッケージで返す。
- 依頼文の「D289 / rc=16」: D289 は「独立な計算ノード job は既定で並行投入」の裁定で pytest と無関係。login の pytest 直叩き禁止の正本は **D103** (一次 = `run_tests.py` の fail-closed admission、二次 = `guard_bash` の literal 拒否、三層 = 規律) で、rc=16 は `run_tests.py` の dispatch 経路の rc (`_PEGASUS_DISPATCH_RC = 16`)。本 wave はこれらを動かしていない。段 3 相談は「依頼の禁止を綴りだけの禁止へ狭めない」と指摘した (§5 所見 1)。
- 現行の login 実行方針は runbook §7 (2026-08-06、T-300): テスト・ビルドは空きメモリが足りれば login で**上限付き** (`systemd-run --scope` の `MemoryMax`) に実行、判定量はメモリ (§7.0)。
- 先例: D2195 (2026-09-21) は変異の期待 node 観測を**親の login self-run** (自走 harness) 既定にした。「self-run は観測法であって判定ではない」。

## 2. 実測 (すべて login node pegasus02、HEAD `5efd69367`、2026-09-21 JST)

### 2.1 hook の静的判定 (07:46、`guard_bash.py` に Claude / Codex 同型の payload を流した rc、`verbatim/guard-verdicts-all.md`)

| # | command (cwd = wave worktree) | rc | 備考 |
|---|---|---|---|
| 01 | `PYTHONPATH=. python3 orchestrator/tests/test_t1259_scan_bound.py` | 0 | 自走 harness |
| 02 | `python3 orchestrator/tests/test_t1259_scan_bound.py` | 0 | PYTHONPATH 無し |
| 03 | `python3 -m pytest orchestrator/tests/test_t1259_scan_bound.py -q` | **2** | 「interpreter の baseline 重量対象 (pytest) を拒否します: Pegasus ログインノードでは重い処理を実行できません」 |
| 04 | `pytest orchestrator/tests/test_t1259_scan_bound.py -q` | **2** | 「pytest による test 実行 を拒否します」 |
| 05 | `python3 tools/run_tests.py orchestrator/tests/test_t1259_scan_bound.py -q` | 0 | sanctioned 入口 (実行時の admission は別) |
| 06 | `PYTHONPATH=. python3 -c "import sys, pytest; sys.exit(pytest.main([…]))"` | 0 | guard の射程外 (`python3 -c` の内側は見えない、D103 決定 (5)) |
| 07 | `python3 -m pytest --collect-only -q …` | 0 | `_pytest_nonexecuting` |
| 08 | `cd <wave> && PYTHONPATH=. python3 orchestrator/tests/test_t1259_scan_bound.py` | 0 | `cd` 付き |

補足: `cd <unit> && timeout 180 python3 tools/run_tests.py …` (09) と `cd <unit> && PYTHONPATH=. /usr/bin/time -f … python3 <test>.py` (10) も rc=0 (`verbatim/guard-verdicts-all.md` の 09・10、payload の cwd は unit worktree)。静的判定は `main()` が payload の `cwd` を判定へ渡さないので cwd 差は見ていない (段 3 所見)。開始 gate の rc=0 は親の shell で観測した値で、log (`verbatim/startup-gate.log`) には `OK:` 行だけがある。

### 2.2 hook の live 発火 (08:02、`python3 tools/check_codex_hooks.py`、`verbatim/check-codex-hooks.log`)

`OK: Codex PreToolUse live gate (apply_patch + Bash; allowed + protected)`、rc=0、codex-cli 0.155.0、47 秒。Codex 子の Bash は `.codex/hooks.json` → `hooks/codex_guard.sh` → 同じ `guard_bash.py` を通る (hooks/README.md 「Codex へ配線済」)。この gate は allowed / protected control の発火を測るもので、pytest 綴りの拒否そのものは 2.1 の静的 rc=2 が示す。子に拒否される綴りを試させることはしなかった (不発火時に pytest が実走してしまう設計を避けた、段 3 所見 5)。

### 2.3 親の login 対照走 (07:48、D2195 が親の変異観測に採ったのと同じコマンド形、`verbatim/parent-control-all.md`、`/usr/bin/time` の WALL / MAXRSS)

対照走の授権は依頼 (probe の実測) と親の判断による。D2195 の適用条件 (node 集合一致・parametrize 等の除外) を満たした実行ではなく、(c) は parametrize ありで D2195 の適用外。時刻 07:48 は親の shell の `date` (生 log には無い)。

| 対象 | harness の形 | 結果 | WALL | MAXRSS |
|---|---|---|---|---|
| (a) `test_t1259_scan_bound.py` | `_run()` → `pytest.main([__file__])` | 3 passed | 2.01 s | 47.8 MB |
| (b) `test_floor_pair_job_contract.py` | `_run()` が test 関数を手動列挙 | 22 passed, 0 failed | 1.51 s | 35.4 MB |
| (c) `test_b5_contrast_launch.py` | `pytest.main([__file__, "-q"])`、parametrize あり | 38 passed | 3.35 s | 57.3 MB |
| (d) `test_auditor_gate.py` (pytest 専用 allowlist、`__main__` なし) | — | 出力なし、rc=0 | 0.22 s | 28.0 MB |

(d) は 16 の test 関数が 1 件も走らない**偽緑** (`test_plain_runner_coverage.py` の docstring が言う型)。MAXRSS は単一 process の per-process ピーク RSS で、runbook §7.0 が admission の判定量に使う cgroup charged memory の代理値ではない (多重 process では過小評価)。本表は「既存 3 harness における tmp・git・subprocess を含む実行例」であり、新設 test file 一般の所要を代表しない (段 3 所見 2・6)。

### 2.4 自走 harness の形の分布 (HEAD `5efd69367`、`orchestrator/tests/test_*.py` 369 本)

分類 (file 単位の文字列判定): `__main__` を含まなければ「なし」、含んで `pytest.main(` か `_pytest.main` を含めば「委譲」、それ以外を「手動列挙」。結果: `pytest.main` 委譲 232 / 手動列挙 82 / `__main__` なし (allowlist) 55。2026-09-20 に追加された test file 8 本 (`git log --diff-filter=A`): 委譲 6 (`test_b5_contrast_launch`、`test_b5_generator_contrast_report`、`test_b5_generator_contrast`、`test_plot_k2_loop_flow`、`test_plot_arc_status`、`test_t1259_scan_bound`) / 手動列挙 2 (`test_plot_b10_waiting_grid_forest`、`test_plot_b7_fixed5_regression`)。2026-09-17〜20 の 14 本では委譲 7 / 手動列挙 7 (残り 6 本: 委譲 `test_cleanup_remove_dirs`、手動列挙 `test_mocc_template_proof`、`test_plot_a1_sized_paired`、`test_floor_pair_job_contract`、`test_mocc_mutation_proof`、`test_agent_outputs`)。**全 test file の 63% (自走 harness を持つ file の 74%) の自走 harness は in-process pytest** であり、admission の scope を通らない点で `python3 -c "…pytest.main…"` と効果が同じ。

### 2.5 probe (段 5、Codex author 子、sandbox=workspace-write、unit worktree `.codex/worktrees/selfrun-probe-unit` @ `5efd69367`、prompt `verbatim/s5-probe-prompt.md`、報告 `verbatim/s5-probe-author.md`)

08:04〜08:07 JST に detach 起動 (`--max-model-calls 150`)、`.done` = 0、codex model call 10、launcher の wall 128.9 秒 (`receipt.json`)。子の報告 (固定欄) から:

| # | 対象 | started | process_rc | wall_s | maxrss_kb | executed_count | failed | 備考 |
|---|---|---|---|---|---|---|---|---|
| 2 | (a) `test_t1259_scan_bound.py` | true | 0 | 1.87 | 47,564 | 3 | [] | `3 passed in 0.86s` |
| 3 | (b) `test_floor_pair_job_contract.py` | true | 0 | 1.62 | 34,964 | 22 | [] | `22 passed, 0 failed` (PASS 22 行) |
| 4 | (c) `test_b5_contrast_launch.py` | true | 0 | 3.29 | 57,076 | 38 | [] | `38 passed in 1.99s` |
| 5 | (d) `test_auditor_gate.py` (allowlist) | true | 0 | 0.37 | 27,684 | null | [] | 出力なし、`grep -n __main__` rc=1 → **test 未実行の偽緑** |

- `hook_verdict` は子から観測できず全件 `null`。「拒否されなかった」は hook 判定の直接観測ではなく、4 process が起動して終了したことからの推定。
- 作業 repo: 開始・終了とも HEAD `5efd69367…`、status (`--porcelain=v1 --untracked-files=all`) は空 (rc=0)。開始時に無かった ignored の `.pytest_cache` と `orchestrator/tests/__pycache__` が生成された (削除・修正なし)。launcher receipt は `launcher_rc=0` / `codex_exit_code=0`、待ち手の `--commit-worktree` 検査は `worktree-commit: clean` (`verbatim/s5-probe-author.wait.log`、終端 commit なし)、`.done` の内容は `0` (mtime 08:06:55、2 bytes、`verbatim/done-files.md`)。
- 環境: `pegasus02`、uid 31609、Python 3.10.12、`/usr/bin/time` 利用可。
- 親の対照走 (2.3) との差: wall は (a) −0.14、(b) +0.11、(c) −0.06 秒、MAXRSS は −252 / −404 / −200 KB。各 1 回で、親 07:48 と子 08:04〜08:07 は並走負荷・cache の条件を揃えていないので、sandbox に起因する増減は判定できない。

author と fix の起動 argv は `tools/dev_wave_codex.py --dry-run` で stage 名と job-id 由来の path 以外が同一 (`--sandbox workspace-write`、`--max-model-calls 100` 既定; `verbatim/dryrun-author-vs-fix.diff.txt`)。fix 子の probe は走らせていない — 同木・同 file の fix は役割別の再現確認であって独立 2 例ではなく (段 3 所見 9)、sandbox が同一なので author 1 本を最小 probe とした。

### 2.6 同時刻証拠 (引用、本 wave の実測ではない)

- T-2814 (2026-09-21、`dev-wave-t2814-cleanup-command/codex/s5-author.md`): author 子は親の指示で `PYTHONPATH=. python3 -c "…pytest.main([…])"` を login で実走し、`test_check_docs.py` 全件 **580 passed / 302.33 秒**、他 3 走。
- T-2810 (2026-09-21、`output/insights/2026-09-20/t2810-g1-launch-validation/verbatim/s5-author.md`): 同じ経路で新規 63 ケース + 既存負例 1 件 = 64 passed、既存回帰の全件走は sealed snapshot の socket 送信が `PermissionError: Operation not permitted` で「検査本体を通せていない」、広い meta 走は git rc=128 の setup error。
- T-2792 / T-2796 / T-2803 (2026-09-20): prompt が sandbox 内の実走形を指示しておらず、子は「実装済み・未実走」(`run_tests.py` は `qstat -Q preflight rc=1` → rc=16、`child_started=false`)。
- 親の運用記憶 (2026-09-05 dynamic-backoff wave): fix 子 5 本が自走 harness (`PYTHONPATH=. python3 <test file>`) で全件実走できた。**能力の初発見ではない。** 本 wave が新たに測ったのは、現在の launcher・sandbox・対象での rc / 所要 / 作業 repo の変更有無と、hook の静的判定・live 発火である (段 3 所見 9)。

## 3. 何が「迂回」で何がそうでないか (親の整理、段 3 所見 1・3 を反映)

- guard_bash の射程 (D103 決定 (5)): 直接 literal な重量コマンド (`pytest`、`python3 -m pytest`、`cmake --build`…) を拒否する二次層。**script file 越し・`python3 -c`・変数展開・subprocess の内側は原理的に見えない**と正本が明記する。したがって「自走 harness も `-c pytest.main` も guard を通る」は迂回の成否ではなく射程の外にあるという事実である。
- 一次層 (admission) は `tools/run_tests.py` にしか無い。自走 harness も `-c pytest.main` も admission を通らない。**この点で両者は同じ**であり、「自走 harness は契約された形だから許される」とは言えない (`test_plain_runner_coverage.py` は `__main__` 以後に文字列 signal があるかを見る構造検査で、実行成功・網羅・login 許可を保証しない、段 3 所見 4)。
- 両者の差は用途と先例にある: 自走 harness は D2195 が**親の変異観測**のコマンド形として採った形 (適用条件付き、§4 案 A の「前提の位置づけ」) で、file 単位 (自分の test file 1 本)。先例があることは子への許可根拠ではない。`-c pytest.main` は任意の file 集合・任意の `-k` を login に載せられる綴りで、T-2814 では 1 file 580 件 302 秒になった。F121 が「pytest 拒否の迂回」として閉じたのは `-m pytest.__main__` / `-m _pytest.main` であり、`-c` を裁定した資料は無い (同族という表現は親の推論)。
- 依頼の「pytest の login 実走禁止を動かさない」を、親は「guard の拒否と admission を変えない」と読んだ。段 3 は「禁止を綴りだけの禁止へ無断で狭められない」と指摘した。**子に in-process pytest の自走 harness を許すかは、この読みの裁定そのものであり、ユーザーへ返す。**

## 4. 裁定パッケージ

裁定対象は **A か B の択一**。C は不採用の推奨、D は今回の対象外 (将来の択として記録)。全件そのまま投げられる形にしてある。

### 案 A — 条件付き: author / fix prompt に「返す前に、自分が新設・変更した test file の自走 harness を 1 回」を足す

prompt に足す文 (親案、段 3 の修正を反映):

> 返す前に、自分が新設・変更した test file のうち **親が本 prompt で名指しし、その file と実行形を覆う明示裁定 (下記「許可根拠」) を引用したものだけ**を `cd <repo root> && PYTHONPATH=. python3 orchestrator/tests/<file>.py` で 1 回走らせ、rc・実行された件数・失敗した test 名 (pytest の nodeid、手動列挙なら関数名 — 混同しない)・未実行の範囲を報告に書く。この自走は多くの file で **in-process pytest** であり、`tools/run_tests.py` の admission (メモリ判定と cgroup 上限 scope) を通らない。hook が拒否しないこと・自走 harness の契約があること・過去に軽かったことは、いずれも実行してよい根拠ではない。名指しと裁定の引用が無い file、`__main__` を持たない pytest 専用 allowlist file、build・大きな fixture・資源量不明の subprocess を含む file は走らせず「未実走」と書く。1 file という単位は資源上限ではない。`python3 -m pytest` / `pytest` は hook が拒否する。`python3 -c` / `tools/run_tests.py` は使わない。赤は自分の差分への帰属を根拠付きで確認できたものだけ直す (test を甘くしない、F27。期待値変更・skip / xfail 化で緑にしない)。統合前の既知の期待赤・原因未確定・実行環境の拒否 (socket の `PermissionError`、git rc=128 など) は内訳を報告し、test も production も変えない。**この自走は計測でも受入でもなく、親の焦点走 (計算ノード) と受入全走を代替しない。** 親は子の緑を理由に焦点集合・consumer 検査を縮めない。

- **許可根拠の定義と、案 A でユーザーに諮る裁定の中身:** 許可根拠とは「対象 file と実行形を覆う明示裁定を親が prompt に引用できること」で、hook 非拒否・`test_plain_runner_coverage.py` の harness 契約・本 wave の軽量実績・D2195 の先例はいずれも許可根拠にならない。案 A で諮るのは、次の**狭い条件付き許可**である: 「Codex author / fix 子が、親が prompt で名指しした**自分の新設・変更 test file 1 本** (pytest 専用 allowlist 外、build・大きな fixture・資源量不明の subprocess を含まない) を、`PYTHONPATH=. python3 orchestrator/tests/<file>.py` の自走 harness (多くは admission を通らない in-process pytest) で login 上 **1 回**走らせてよい」。これは用途 (子の自己検証)・主体 (Codex 子)・対象 (名指しの 1 file)・回数 (1 回) を固定した許可であり、**`DW-M08` の「login 実行が許される file」の一般境界を定義するものではない** (一般境界は本 wave の対象外のまま)。A が裁定された場合、親は各 prompt で file を名指しし本裁定を引用する — 名指しと引用の無い file は許可されない。A の裁定が無い間は案 B の運用 (未実走) を続ける。
- 前提の位置づけ: D2195 は**親**が変異の期待 node を観測する用途に自走 harness の**コマンド形**を採ったもので、適用条件 (自走の node 集合が `--collect-only` と一致し login 実行が許される file に限る。pytest 専用 allowlist・parametrize・conftest / autouse fixture・環境変数・import 副作用に依存する test は除外) が付く。案 A はこのコマンド形を、**別の用途 (子の自己検証) と別の主体 (Codex 子) へ、適用条件を新たに定めて**広げることに当たり、D2195 の適用条件はそのまま子へ写らない (probe の対象 (c) は parametrize ありで D2195 の適用外)。
- 根拠: hook は拒否しない (2.1、2.2)、probe で author 子が指定 3 file を rc=0 で実走 (1.6〜3.3 秒 / 35〜57 MB、作業 repo の HEAD / status 不変、2.5)、対照走は 1.5〜3.4 秒 / 35〜57 MB (ただし新設 file 一般へ一般化できない、2.3 の限定)。
- 期待効果 (限定): 変更 test 自身で再現する fixture / assert 誤り (F76 型、T-1851 で 2 度) を親の dispatch 前に子が見つけられれば、修正往復を減らせる**可能性がある**。頻度・削減時間は未測定。焦点走 (DW-O26 の consumer + inventory 4 群) と受入全走は残り、T-2810 の焦点走 1 の赤 (既存 consumer test) や T-2797 の受入赤 (inventory test) は self-run では出ない型。参考値: 焦点走・変異 probe の dispatch 1 走は 7〜26 分 (T-2796 の attempt 2 = 7 分、D2195 の変異 probe 平均 20.7 分・最大 26.4 分) で、これは別走種の待ち込み所要であって本案の効果量ではない。
- docs への収容: `DW-S05-C` は 2026-09-03 時点で L1.5 予算満杯 (同型の恒久対応 149 bytes が `check_docs` を赤にし、台帳側は `docs/failures.md` F76 の「再発: 2026-09-03」に記録、親の記憶 `verbatim/memory-selfrun-section.md`)。現在の残量は本 wave で測っていない。採用時は当面「親が prompt に書く運用」で、予算の裁定は別。
- ユーザーが A を選んだ場合に親が次にすること: (1) 以後の author / fix prompt に上の文を入れ、名指し file と本裁定の参照を書く、(2) `DW-S05-C` への収容は予算の裁定パッケージを別に出す、(3) T-2810 / T-2814 型の `python3 -c` 指示を止める。B を選んだ場合: (3) だけ行い、prompt は現状 (「実装済み・未実走」) のまま。

### 案 B — 足さない (現状: 子は「実装済み・未実走」、親が焦点走を dispatch) — **裁定が下りるまでの既定**

- 根拠: admission 外の login 実行を子に許す形を増やすと、`DW-M08` の「login 実行が許される file」の境界を暗黙に広げる。境界の定義は本 wave の scope 外。
- 費用: 往復 1 巡 (7〜26 分の参考値) は wave 平均 153.5 分 (12 wave、impl 7 本では 169.6 分; `output/insights/2026-09-21/dev-wave-wall-decomp/README.md` の平均行) の 4.6〜16.9% に相当するが、self-run で減る往復の頻度は未測定。

### 案 C — `python3 -c "…pytest.main([…])"` を prompt で指示する (T-2810 / T-2814 の現行の形) — 不採用を推奨

- 理由: guard の射程外で通るだけで、任意の file 集合を admission 無しで login に載せられる (T-2814: 580 件 302 秒)。依頼の「hooks の拒否を迂回しない」に最も近い形の綴り替え (F121 が閉じた `-m pytest.__main__` と同族というのは親の推論)。allowlist file を子に走らせたい需要は親の dispatch で満たす。**案 A / B のどちらでも、この形の指示は止めるのが親の推奨。**

### 案 D — `tools/run_tests.py` を sandbox 内で使えるようにする — 今回の対象外

- admission 台帳 (`/run/user/<uid>/`) と `qstat` socket の sandbox 制約を解く実装・gate 変更で、依頼の scope 外。将来の択として記録するに留め、設計は展開しない。

## 5. 段 3 相談・段 4 裁定・段 6 レビュー (逐語は `verbatim/s3-consult-out.md`、`verbatim/s4-adjudication.md`、`verbatim/s6-*.md`)

read-only codex 1 本 (gpt-6-astra / medium) が所見 11 件 (高 5) を返し、現行草案の live probe を NO-GO とした。親は 11 件すべてを real と裁定して採用した: (1) 案 A の「迂回でない」根拠不足 → 案 A を条件付き候補に、既定は案 B、(2) 「1 file・数秒・数十 MB」の一般化不可 → 資源除外文、(3) probe のコマンド 7 (`run_tests.py`) は local scope / dispatch へ進みうる → 削除、(4) 「契約上保証」は meta-test の射程超え → 置換、(5) コマンド 6 (子に `-m pytest`) は証拠設計が弱く不発火時に実走 → 削除し live gate で代替、(6) fixture の代表性は部分的、(7) 「編集ゼロ」は tracked / index / HEAD に限定し ignored (pyc / cache) 不変は主張しない、(8) 「往復 1 巡削減」は断定が強い → 置換、(9) fix probe 不要、(10) 案 A〜D の排他を明記、(11) 報告を固定欄に。(P1) conditional / (P2) refuted / (P3)〜(P5) conditional。

段 6 (逐語は `verbatim/s6-review-1.md`、`s6-focus-1.md`、`s6-focus-2.md` と各 prompt): read-only review 1 本 (gpt-6-astra / medium) が must-fix 4 / should 2 / nit 1 (修正後 GO) — (1) 案 A の「許可根拠」が未定義、(2) D2195 の適用除外を落として先例を許可根拠に近づけた、(3) 「自走 harness 369 本中の 63%」の分母誤り、(4) T-2810 の「新 test 64 件」は新規 63 + 既存 1、(5) 一次資料の不足 (09・10 の verdict、平均 154 分、149 bytes、`.done`)、(6) 「sandbox による所要増加は観測されない」は言い過ぎ、(7) 128 秒の丸め。親は全件を real として README を修正した。焦点再レビュー 1 巡目は closed 5 / partial 1 (`.done` の証拠) / regressed 1 (「案 A を選ぶ裁定そのものが明示裁定」が「境界は定義しない」と矛盾)、2 巡目は 3 件とも closed・新所見なし・GO (提示について。案 A の実行許可ではない)。

## 6. 限界

- 本 wave が測ったのは既存 3 file の自走 harness で、新設 file 一般・socket・`/run/user` の sandbox 制約は未測定 (T-2810 の `PermissionError` は引用)。
- 静的 hook 判定は payload の `cwd` を判定に渡さない。live gate は allowed / protected control で、pytest 綴りの拒否そのものは live で観測していない。
- probe の所要は親の対照走で pyc が温まった後の値になりうる (別 worktree なので同一とも断定しない)。cold start の所要は主張しない。対照走と probe は各 1 回 (n=1) で、並走負荷・cache の条件を揃えていない。
- 子の `hook_verdict` は観測不能で、「拒否されなかった」は process の起動・終了からの推定。子の exact な経路で hook が発火したことの証明は live gate (別 clone への投影) とは別に取っていない。
- probe 子は `--max-model-calls 150` で起動した (author の通常既定は 100)。sandbox・repo-root・stage は通常の author と同じ。
- 「編集ゼロ」は tracked / index / HEAD の不変で、ignored bytes (`__pycache__`、`.pytest_cache`) の不変は主張しない。
- 案 A の効果量 (往復の頻度・削減時間) は未測定。「往復 1 巡の削減」は達成として書いていない。
- 「拒否の理由と代替」(依頼の不可能側): 本件は「実行できる」側だが、pytest 専用 allowlist の 55 本は自走 harness を持たず子には走らせられない (偽緑になる)。その代替は親の dispatch (焦点走) で、案 A / B のどちらでも変わらない。

## 7. 記録

- 一次資料: 本 README、`verbatim/` (依頼、brief、静的判定、対照走、live gate、consult、裁定、probe prompt と報告、author/fix argv 差分)。実行可能 script は insight に写していない (launcher は job dir、`.md` 逐語のみ)。
- worklog: fragment 1 本 (`docs/spool/worklog/`)。decisions / failures の新設なし (裁定パッケージ)。F76 (子の新設 test の fixture 誤り) / F121 (pytest 拒否の綴り替え) は既存型の参照で、台帳編集はしない。
- 受入全走と land は README commit 時点で未実施 (実施後に §8 として追記する)。逐語 2 file の行末空白・末尾改行の可逆最小正規化は `verbatim/NORMALIZATION.md` (原文 hash・byte 数・復元法)。

## 8. 受入と main 取り込み

- 記録 commit `6b1b8f51a` (本 README と worklog fragment)。全履歴 provenance 監査 rc=0 (12,262 件、新規違反なし)。
- 受入全走 (門番付き、`dev_wave_wait.py acceptance` + `run_tests.py`、3 shard): 08:37 JST 投入 → 他 wave の受入 leader 2〜4 本で 24 分待ち → 09:01 に窓が開いて local main `21641fee7` を wave 木へ取り込み (post-claim merge、tip `8f6ecb264`) → 09:12 に **child-green** (26,739 passed / 69 skipped、赤 0・flake 0、attempt 1、受領証 `acceptance-receipt-final-1.json`、tested main `21641fee7` / tested tip `8f6ecb264`)。
- 取り込んだ main 4 commit には別 wave (`dev-wave-dwm08-selfrun-probe`) の `DW-M08` 改訂が含まれる — **親**が変異の期待 node を login self-run で観測する手順の詰め書きで、適用外の列挙に `skip` が加わり、復元時に `--porcelain` 空の照合が明記された。本 README が引く「login 実行が許される file」の文言は残っており、本 wave の実測・案 A〜D の結論は変わらない (子への許可は依然として未裁定)。
