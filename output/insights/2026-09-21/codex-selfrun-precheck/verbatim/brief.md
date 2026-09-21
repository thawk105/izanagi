# 段 1 brief — codex 子の login self-run precheck (2026-09-21、親 = Claude、wave `dev-wave-codex-selfrun-precheck`)

起点: local main `5efd69367` (fresh worktree、HEAD == main、開始 gate rc=0、`startup-gate.log`)。依頼逐語は `origin.md`。

## 研究前進 (土台)

止めているもの: impl wave の段 5→6 で、Codex author / fix 子が「実装済み・未実走」で返し、親が計算ノードへ焦点走を dispatch (queue 待ち込みで 8〜26 分) してから fix 巡へ戻す往復。直近の実測は T-2792 (`output/insights/2026-09-20/t2792-a1-sized-rerun-authorization/README.md` §4)、T-2796 (`t2796-docs-carry4/README.md` §5)、T-2803 (`t2803-receipt-attributes-fingerprint/reviews/s5-author.md` 冒頭「実装済み・pytest は未実走」)。完了判定: 裁定パッケージ (insight README) が「子は self-run を実走できるか」を実測 (hook 判定・rc・所要) 付きで答え、可能なら prompt 改訂案、不可能なら理由と代替を提示する。

## scope

- 入: (1) 各綴りの hook 判定を親が静的に実測 (済、`guard-verdicts/`)、(2) 親の login 対照走 (済、`parent-control/`)、(3) Codex author 子 1 本 + fix 子 1 本の probe (fresh unit worktree @ main、編集ゼロ、実行して報告するだけ)、(4) insight README (裁定パッケージ) + spool fragment (worklog)。
- 出: gate・台帳 (decisions / failures の新設)・一般化・docs 変更・実装・hooks の変更。pytest 直叩き禁止 (guard 二次層) と `run_tests.py` の admission (rc=16) は動かさない。

## 確定済みユーザー裁定と正本

- login の重量処理拒否の正本は **D103** (決定 (5): 一次 = `run_tests.py` の fail-closed admission、二次 = `guard_bash` が直接 literal を拒否、三層 = 規律。**script file 越し・`python3 -c` は原理的に見えない**と明記)。依頼文の「D289」は「独立 job の並行投入」の裁定で pytest と無関係 — 依頼の意図 (禁止を動かさない) は D103 で読む。
- 現行の login 実行方針は runbook §7 (2026-08-06、T-300): テストは空きメモリが足りれば login で「上限付き」実行 (`run_tests.py` の cgroup scope)。判定量はメモリ (§7.0)。
- **D2195** (2026-09-21): 変異の期待 node 観測は親の **login self-run** (自走 harness) が既定。self-run は観測法であって判定ではなく、KILLED 判定 (dispatch final) は不変。
- F121: `python3 -m pytest.__main__` / `-m _pytest.main` は「pytest 拒否の迂回」として閉じた。
- 依頼の制約: hooks の拒否を迂回しない / self-run は計測でも受入でもない / 規律 2 を緩めない。

## brief 前の前提実測 (親、login pegasus02、HEAD 5efd69367、07:47〜07:49 JST)

- hook 判定 (guard_bash に payload を流した静的判定、`guard-verdicts/*.verdict.log`): `PYTHONPATH=. python3 orchestrator/tests/<test>.py` rc=0 (PYTHONPATH 無し・`cd` 付きも rc=0)、`python3 -m pytest <test>` rc=2 (拒否: interpreter の baseline 重量対象 (pytest))、`pytest <test>` rc=2、`python3 tools/run_tests.py <test>` rc=0 (sanctioned)、`python3 -c "…pytest.main([…])"` rc=0 (射程外)、`python3 -m pytest --collect-only` rc=0。
- 親の対照走 (`parent-control/*.log`、`/usr/bin/time` の WALL / MAXRSS): (a) `test_t1259_scan_bound.py` (pytest.main 委譲型) 3 passed、2.01 s、47.8 MB / (b) `test_floor_pair_job_contract.py` (手動列挙型) 22 passed、1.51 s、35.4 MB / (c) `test_b5_contrast_launch.py` (T-2797 が足した pytest.main 委譲型) 38 passed、3.35 s、57.3 MB / (d) `test_auditor_gate.py` (pytest 専用 allowlist、`__main__` なし) 出力なし rc=0、0.22 s = 16 関数が走らない偽緑。
- 自走 harness の形の分布 (369 file): `pytest.main` 委譲 232 / 手動列挙 82 / `__main__` なし (allowlist) 55。**self-run の 63% は in-process pytest** であり、guard が見ないのは script file 越しだからで、admission (メモリ上限 scope) は通っていない。
- 同時刻証拠: T-2814 (2026-09-21) の author prompt は子に `python3 -c "…pytest.main([…])"` で `test_check_docs.py` 全件を走らせ、子は 580 passed / 302 秒を login で実走した (`dev-wave-t2814-cleanup-command/codex/s5-author.md` §実走結果)。記憶 (2026-09-05 dynamic-backoff wave) では fix 子 5 本が自走 harness を実走できた。
- login の状態: 回収不能 5.34 GiB (天井 14 GiB)、load 5.7。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) 子は自走 harness を hook 拒否なしに実走できる (静的判定 rc=0 + 同時刻証拠)。残る未知は sandbox 固有の要因 (cwd、PYTHONPATH、`/run/user` 不可、socket 不可、tmp) が rc≠0 や所要増を起こすか — probe で測る。
- (P2) prompt に足す形は「新設・変更 test file だけを自走 harness で 1 回」に限る。根拠: D2195 が親に許した観測法と同じ形、1 file は数秒・数十 MB (対照走)、`test_plain_runner_coverage.py` が全 test file に自走 harness を義務付けている。**self-run は計測でも受入でもなく、親の焦点走 (計算ノード) と受入全走を代替しない。**
- (P3) `python3 -c "…pytest.main([…])"` は prompt に載せない。guard の射程外で通るが、F121 が閉じた `-m pytest.__main__` と同族の「pytest 拒否の綴り替え」で、T-2814 では 580 件 / 302 秒を admission 無しで login に載せた。allowlist file (55 本) は自走できないので親の dispatch に残す。
- (P4) 期待効果は往復 1 巡の削減であって全廃ではない: 減るのは子の新設 test 自身の fixture 誤り型 (F76 型、T-1851 で 2 度) と literal / assert の綴り誤り。consumer 回帰・meta-test・xdist/conftest 依存の赤は self-run では出ない (DW-O26 の焦点走は残る)。
- (P5) 「login 実行が許される file」(DW-M08) の境界は D2195 でも明文でない。本 wave は境界を定義せず、裁定パッケージで「1 file・数秒・数十 MB」の実測を根拠に提示する (一般化は scope 外)。

## 不変条件

- 実装差分ゼロ: 子は repo を編集しない (prompt に明記)、親も repo 内の実装面・docs を編集しない。probe script を repo へ入れない。
- 迂回しない: 子に拒否される綴り (`python3 -m pytest`) を試させるのは拒否を観測するためで、通す別綴りを探させない。
- rc=16 (`run_tests.py` の admission) と guard の pytest 拒否は不変。self-run は計測でも受入でもない。

## 成果物

- `output/insights/2026-09-21/codex-selfrun-precheck/README.md` (裁定パッケージ: 実測表・推奨案・不採用案・限界) + `verbatim/` (guard 判定 log、対照走 log、子の報告と prompt の逐語)。
- `docs/spool/` の worklog fragment 1 本。D / F の新設なし (裁定パッケージ)。

## 分割方針 (軽量版 + 診断 wave の型)

段 3 相談 1 本 (read-only、brief と probe 設計への攻撃) → 段 4 裁定 → 段 5 probe: author 子 1 本 (unit worktree @ main、`--stage author`、workspace-write) → 同木で fix 子 1 本 (`--stage fix`、独立 2 例目) → 親の README → 段 6 read-only review 1 本 + 焦点再レビュー → 段 7 記録 → 段 8 → 段 9 (受入 1 走 + land)。段 2 は省く。
