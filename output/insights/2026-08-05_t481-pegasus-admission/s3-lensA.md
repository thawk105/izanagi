結論は **NO-GO** です。静的読解のみで、pytest は実行しておらず、緑は主張しません。

## 境界判定と親主張

`OTHER` / `PEGASUS_COMPUTE` については、プランどおり変更を重量判定の閉包内に限定する限り、受理 bit が動く経路は見つかりませんでした。`_heavy_command_violation()` は [`guard_bash.py:947`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:947) で login/suspect のときだけ呼ばれ、site 正本も OTHER/COMPUTE を拒否集合から外しています（[`site_policy.py:74`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/orchestrator/campaign/site_policy.py:74)）。ただし、これは構造による保証であり、18 entry の正例テストだけによる悉皆保証ではありません。

親の4主張への判定は次のとおりです。

| 親主張 | 判定 |
|---|---|
| (i) 族欠陥が3例 | 部分的に成立。`collect_receipt`、`collect_t126_qualification`、`submit_t126_qualification` の3本は login 手順だが、`make_acquisition_receipt.py` は compute job 内 helper（[`certify_calibration.sh:633`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/certify_calibration.sh:633)）なので4本目としては refuted。3例という下限は残る。 |
| (ii) `-mpytest <sanctioned>` が迂回 | 実測自体は正しい（[`probe_attached_m.json:58`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/probe_attached_m.json:58)）。ただし root cause の一般化が不足し、後述 R3〜R6 が残る。 |
| (iii) `collect_receipt.py` は `unknown` | 正しい。しかも stderr だけでなく JSON 全読込と manifest 全件 materialize も無界。 |
| (iv) [T-482] は (c) | CLI cap 方向は必要。ただし「stderr summary だけ cap」は不十分で、そのままでは `local-ok` にならない。 |

## Real 所見

### R1 — real: 追記後の分類契約が段2プランへ反映されていない

(a) 根拠 — 追記は `login-ok` を「hard cap + cap 下の実測」に限定し、他 entry は `unknown` のまま deny としています（[`brief-addendum.md:48`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/brief-addendum.md:48)）。一方プランは有限 fixture の実測だけで `collect_t126_qualification.py` と `submit_t126_qualification.sh` を `login-ok` にでき（[`s2-plan.md:11`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:11)、[`s2-plan.md:16`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:16)）、二値表しか持ちません（[`s2-plan.md:52`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:52)）。これは runbook の `local-ok / dispatch-required / unknown` 契約（[`pegasus-runbook.md:358`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/docs/pegasus-runbook.md:358)）も失います。

既存 sanctioned の `submit_silo_ladder_rung1.sh` は runbook 上明示的に `unknown`（[`pegasus-runbook.md:400`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/docs/pegasus-runbook.md:400)）なのに、プランは grandfather か測定かを未裁定のまま残しています。

(b) 再現綴り —

```bash
python3 tools/pegasus/collect_t126_qualification.py collect --repo-root /work/1/SFC/tanab/izanagi --attempt-id 0000000000000000000000000000000000000000000000000000000000000000 --submission-receipt /tmp/submit.json --stdout /tmp/job.o1 --stderr /tmp/job.e1 --accounting /tmp/accounting.txt
tools/pegasus/submit_t126_qualification.sh --dry-run
tools/pegasus/submit_silo_ladder_rung1.sh --dry-run
```

有限 fixture の測定だけで前2本を ALLOW にすると P1' 違反、P1' を既存 entry に厳格適用すると3本目が ALLOW→DENYになります。

(c) 修正案 — 段2プランを破棄して v2 を作る。表は少なくとも「実行場所」と「資源証拠状態」を別軸にし、`unknown` を `compute-only` と混同しない。hard cap のない新規2本はこの wave では deny。既存 grandfather は明示裁定なしに維持・撤回しない。

(d) 成果物影響 — 未修正なら LOGIN 受理集合の3 bitが裁定なしに動き、分類レポートの `unknown` が偽の `login-ok/compute-only` に置換される。

### R2 — real: `collect_receipt.py` の stderr cap だけでは有界にならない

(a) 根拠 — stderr 全読込（[`collect_receipt.py:147`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/collect_receipt.py:147)）以外にも、3 JSON の `json.load`（[`collect_receipt.py:33`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/collect_receipt.py:33)）と、`sorted(rglob("*"))`・全 record list（[`collect_receipt.py:76`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/collect_receipt.py:76)）が無界です。段2プラン自身もこれを認識しています（[`s2-plan.md:5`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:5)）が、追記 P2' は会計 summary だけを修正対象にしています。

(b) 再現綴り —

```bash
python3 tools/pegasus/collect_receipt.py --attempt-dir /tmp/collector-fixture/attempt-million-files --job-staging /tmp/collector-fixture/staging-million-files --stdout /tmp/collector-fixture/job.o1 --stderr /tmp/collector-fixture/job.e1
```

fixture の receipt/log を正当にし、attempt/staging に大量の微小ファイルを置けば、stderr が小さくても `sorted(rglob)` と manifest が入力件数比例になります。巨大な submit/job-result JSON でも同型です。

(c) 修正案 — stderr bytes/保持行数、各 JSON bytes、各 manifest の file 件数をすべて cap する。`rglob` を先に全 materialize せず `cap + 1` 件で fail-closed にし、その有界集合だけを sort する。cap 境界・1超過・巨大 JSON・大量微小ファイルのテスト後、cap 最大入力で測定する。

(d) 成果物影響 — 未修正なら `final-receipt.json` の参照は作れても `collect_receipt=local-ok` という分類根拠が偽になり、Pegasus env contract 登録レポートの provenance が §7.0 非準拠になる。

### R3 — real: `-m` 固定が現在 DENY の `cProfile` 実行を ALLOW にする

(a) 根拠 — 現行の attached 形では最初の非 option が compute-only path なので [`guard_bash.py:484`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:484) から Pegasus 拒否へ入ります。プランは `-m` があれば後続 path を候補から全面除外します（[`s2-plan.md:83`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:83)）。しかし `cProfile` は後続 script を読み、compile・実行します（[`cProfile.py:169`](/usr/lib/python3.10/cProfile.py:169)）。

(b) 再現綴り —

```bash
python3 -mcProfile tools/pegasus/exec_calibrate.py /tmp/calibrate-argv.json
```

現行は DENY、プランどおりなら `cProfile` 自体に重量判定がなく ALLOW、その後 `exec_calibrate.py` が任意 argv を `os.execv` します（[`exec_calibrate.py:32`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/exec_calibrate.py:32)）。

(c) 修正案 — 「`-m` 後続は常に data」を撤回する。`py_compile` など明示的に検証済みの静的-reader moduleだけ後続 path を data 扱いし、`cProfile`、`pdb`、`trace`、coverage 系など script-executor module は実行対象 path を分類する。分離形・密着形の双方を固定する。

(d) 成果物影響 — compute-only entry の LOGIN bit が DENY→ALLOWとなり、T-483 完了レポートと分類台帳が実受理集合を誤記する。

### R4 — real: `pytest.__main__` で pytest 拒否を迂回でき、プラン後も残る

(a) 根拠 — pytest 判定は module が文字列 `"pytest"` と完全一致する場合だけです（[`guard_bash.py:506`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:506)）。`pytest.__main__` は `_PYTHON_MODULE_RE` 上有効ですが、repo 内 target ではなく、pytest 分岐にも入りません。計画テストも `-mpytest` だけです（[`s2-plan.md:170`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:170)）。

(b) 再現綴り —

```bash
python3 -m pytest.__main__ orchestrator/tests/test_hooks.py
python3.10 -mpytest.__main__ -q
```

現行コードの行に基づけば両方とも hook を通り、pytest package の `__main__` が test を実行します。

(c) 修正案 — executor identity を `pytest` と `pytest.__main__` の閉集合で正規化し、分離・密着・数値版付き・絶対 interpreter path・wrapper 内の全形を同じ分岐へ送る。

(d) 成果物影響 — T-483 を閉じたと記録しても LOGIN の pytest 実行 bit が開いたままで、受入レポートの実行場所保証が偽になる。

### R5 — real: `env -S` の実 grammar と `shlex.split` の差で重量 head を隠せる

(a) 根拠 — guard は GNU `env -S` の分割を `shlex.split` で代用します（[`guard_bash.py:329`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:329)、[`guard_bash.py:365`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:365)）。GNU env は unquoted `\_` を引数区切りにしますが、`shlex.split` は `_` の escape として単一 token にします。

(b) 再現綴り —

```bash
env -S 'pytest\_-q'
sudo -n env -S 'python3\_-mpytest\_tools/run_tests.py'
```

実 env はそれぞれ `pytest -q`、`python3 -mpytest tools/run_tests.py` として実行します。guard 側は `pytest_-q` または1個の非重量 head と解釈して ALLOW します。

(c) 修正案 — GNU env grammarを再現できない escape・変数展開を含む split-string は fail-closed にするか、同 grammar の専用 parser を実装する。最低限 `\_`、`\c`、`${...}` の回帰を追加する。

(d) 成果物影響 — wrapper 経由の LOGIN pytest bitが開いたままになり、`-m` 修正の検収レポートが偽陽性になる。

### R6 — real: Python/shell option の分離値が実 script path を隠す

(a) 根拠 — `_script_target()` は option が取る値を理解せず「最初の `-` で始まらない token」を script とします（[`guard_bash.py:484`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:484)）。プランはこの候補生成を維持したまま `-m` 分岐だけを追加します。

(b) 再現綴り —

```bash
python3.10 -W ignore tools/pegasus/exec_calibrate.py /tmp/calibrate-argv.json
bash -O extglob tools/pegasus/certify_calibration.sh
```

guard は `ignore` / `extglob` を script target と誤認して ALLOWします。実 interpreter はその次の Pegasus script を実行します。

(c) 修正案 — Pythonでは `-W` / `-X` 等の値を消費し、`-c` / `-m` / `--` / 最初の script で停止する faithful prefix parser を使う。shell側も `-O` / `-o` / `--rcfile` 等の値を認識する。wrapper、数値版付き head、分離・密着 option の matrix を追加する。

(d) 成果物影響 — compute-only 分類 row が通常の interpreter option 1個で無効化され、分類レポートの受理集合が実際より狭く記録される。

### R7 — real: `cd`、`../`、symlink alias が exact-path 分類を迂回する

(a) 根拠 — `_invocation_path()` は lexical `normpath` だけで cwd と realpath を解決しません（[`guard_bash.py:411`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:411)）。重量判定の segment loopにも cwd 状態がなく（[`guard_bash.py:660`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:660)）、後段の防護 tree 用 `cd` tracking（[`guard_bash.py:980`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:980)）は重量判定へ効きません。

(b) 再現綴り —

```bash
cd hooks && python3 ../tools/pegasus/exec_calibrate.py /tmp/calibrate-argv.json
bash -lc 'cd tools/pegasus && python3 exec_calibrate.py /tmp/calibrate-argv.json'
python3 /tmp/pegasus-alias/exec_calibrate.py /tmp/calibrate-argv.json
```

3本目は `/tmp/pegasus-alias` が repo の `tools/pegasus` への既存 symlink の場合です。いずれも実体は compute-onlyですが、現行行に基づけば lexical path が表に一致せず ALLOWです。

(c) 修正案 — segment間の cwd を追跡して repo-relative pathを解決する。symlink aliasは canonical login-okへ正規化して許可するのではなく、lexical exact pathでない aliasとして denyする。`lstat` と realpath の双方を検査する。

(d) 成果物影響 — exact-path 表の拒否集合が cwd/symlink spelling を含まず、台帳の「compute-only exact enforcement」が偽になる。

### R8 — real: bootstrap が閉じておらず、runbook の測定 wrapper 自体が fail-open

(a) 根拠 — 追記は「測定には allowlist が必要、allowlist には測定が必要」という循環を明記しています（[`brief-addendum.md:31`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/brief-addendum.md:31)）。プランは「実装前に測る」とだけ書き、誰がどの許可面で行うかを定めません（[`s2-plan.md:36`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:36)）。

さらに runbook の測定は `systemd-run ... -- <command>`（[`pegasus-runbook.md:331`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/docs/pegasus-runbook.md:331)）ですが、`systemd-run` は wrapper 集合にありません（[`guard_bash.py:119`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:119)）。guard はその子 command を解析しません。

(b) 再現綴り —

```bash
systemd-run --user --scope -q --unit=izprobe -p MemoryAccounting=yes -- pytest -q
nice -n 5 taskset -c 0 systemd-run --user --scope -q --unit=izprobe2 -- python3 tools/pegasus/exec_calibrate.py /tmp/calibrate-argv.json
```

どちらも現行 guard の head は `systemd-run` となり、子 pytest/compute-only pathへ到達しません。これを測定に利用するのは bootstrap の解決ではなく防壁迂回です。

(c) 修正案 — wave を「cap 実装 → 親が明示した人間端末または専用の bounded bootstrap surfaceで測定 → 証拠記録 → login-ok分類」の順にする。actorと成果物 pathを plan v2 に明記する。一般の `systemd-run` は `--` 後を再帰解析し、測定用例外を任意 command trampoline にしない。

(d) 成果物影響 — 未修正なら測定証拠が作れず entry は `unknown` のままか、迂回測定を根拠に偽の `local-ok` がレポートへ載る。どちらでも final-receipt 経路の正規参照が閉じない。

### R9 — real: 悉皆 meta-test は inventory 同期だけで、分類根拠を一切 gate しない

(a) 根拠 — 提案する3検査は実体 key一致、二値 domain、sanctioned集合との一致だけです（[`s2-plan.md:180`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:180)）。新規 file と `login-ok` row を同時追加すれば緑になることをプラン自身が認めています（[`s2-plan.md:190`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/s2-plan.md:190)）。

赤になる変更は「fileだけ追加」「rowだけ追加/削除」「不正 value」「derived sanctioned集合の不一致」。赤にならない改悪は「危険な file + login-ok rowを同時追加」「既存 login-ok の内容を任意 `os.execv` へ変更」「symlink entryを login-ok登録」です。

(b) 再現例 —

```text
tools/pegasus/new_exec.py: 任意 argv を os.execv
_EXECUTION_CLASSES["tools/pegasus/new_exec.py"] = "login-ok"
python3 tools/pegasus/new_exec.py /tmp/argv.json
```

file集合と表集合は一致し、valueも正当、sanctioned集合も自動導出されるため、提案 meta-test は赤くなりません。

(c) 修正案 — meta-test の保証名を「inventory同期」に狭める。`login-ok` には独立した証拠 row（hard-cap test、測定 artifact ID、測定 commit）を必須化し、固定された期待分類テストを表から導出しない。`lstat` で symlinkを明示拒否する。変異には「新規危険 entry + login-ok row」を追加し、証拠 gateだけが赤になることを確認する。

(d) 成果物影響 — 未修正なら分類表と実体は同期していても危険な entry が sanctioned になり、meta-testを根拠にした land レポートの保証文だけが恒真化する。

### R10 — real: shell command string は3段ネストで再帰上限を越える

(a) 根拠 — shell `-c` の再帰は `depth < 2` の間だけです（[`guard_bash.py:652`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:652)）。深さ2でさらに shell command stringが現れると、拒否せず `None` を返します。

(b) 再現綴り —

```bash
bash -lc "bash -lc 'bash -lc \"pytest -q\"'"
```

外側2段までは再帰しますが、3段目の `pytest -q` は解析されず ALLOWです。

(c) 修正案 — 深さ上限で shell `-c` が残った場合は fail-closed にする。上限はDoS対策として維持してよいが、「解析を止めて許可」にはしない。2段正例・3段拒否・非 command-string shell正例を固定する。

(d) 成果物影響 — LOGIN pytest受理集合に直接実行可能な spelling が残り、T-483/重量防壁の完了記録が不正確になる。

### R11 — real: 明示的な非実行形を過剰拒否する

(a) 根拠 — pytest の非実行 flag は long form 3個だけです（[`guard_bash.py:502`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:502)）。`-h` と pytest の `--co` alias がありません。また compute-only class は per-entry `--help` を見る前に拒否される設計です。`run_probe.py` は argparse が `--help` で `run()` 前に終了します（[`run_probe.py:103`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/tools/pegasus/run_probe.py:103)）。

(b) 再現綴り —

```bash
pytest -h
python3 -m pytest --co
python3 tools/pegasus/run_probe.py --help
python3 -c 'print("static")' -m pytest
```

最後の形は Pythonでは `-c` 後の `-m pytest` が単なる `sys.argv` ですが、module parserは `-c` 後も走査し（[`guard_bash.py:433`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t481-pegasus-admission/hooks/guard_bash.py:433)）、pytest実行と誤認します。

(c) 修正案 — pytestの正規 alias `-h` / `--co` を追加する。compute-only entry の `--help` は、そのCLIが確実に早期終了することを個別表で確認してから許可する。Python parserは `-c`、script、`--` で option走査を止める。

(d) 成果物影響 — certified値は変わらないが、LOGIN受理集合が正当な静的検査・CLI確認について不必要に縮み、開発 preflight の可用性が落ちる。

なお、`python3 -m py_compile <file>`、long formの pytest `--collect-only`、provenanceの `--message-file`、計算ノード上の全操作は、プランどおりの閉包なら維持できます。ここは過剰拒否を新設する所見なしです。

## 疑わしい / nit

### N1 — nit: 「stderr の2〜3倍程度」という増幅率は根拠がない

短い行を大量に含む入力では、`str`・list要素・slice・JSON encoderのオブジェクト overheadにより単純なbyte倍率を大きく超え得ます（[`brief-addendum.md:14`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t481-pegasus-admission/artifacts/brief-addendum.md:14)）。`unknown` という結論自体は変わらないため成果物影響はなく、倍率表現を削って「入力比例・上限なし」に留めればよい nit です。

## 総括

real 所見は **11件**、nit は **1件**です。最重要3件は次です。

1. **R1/R2:** 親追記の `hard cap + 実測` がプランに反映されず、stderrだけのcapでも `collect_receipt.py` は有界にならない。
2. **R3:** `-m` 実行体固定が `python3 -mcProfile <compute-only script>` を新たに DENY→ALLOWへ反転する。
3. **R8:** 分類 bootstrap が未定で、runbookの測定用 `systemd-run` 自体が現行guardの未解析launcherとしてfail-openしている。