## 所見 1 — P1 は D895 の明示裁定と衝突する

- **所見**: 「任意 argv の汎用 task は作らない」という P1 と plan の結論は、後発のユーザー裁定 D895 に反する。
- **なぜ real か**: brief は不採用も候補にする (`brief.md:50-55`)、plan も `generic` / `shell` / `command` task を追加しない (`s2/plan.md:295-333`)。しかし D895 は「任意のコマンドを計算ノードで実行する汎用 task を足す」と明記する (`docs/decisions.md:32719-32729`)。D842 の「同じ wave で扱う」だけなら「作らない」も論理上あり得るが、D895 がその択一を既に閉じている。現用途も、sanctioned 経路がなければ停止する現行規定 (`docs/pegasus-runbook.md:565-574`) と、7 本へ増えた `submit_*.sh` family、任意 argv を exec する既存の compute 内部部品 (`tools/pegasus/exec_calibrate.py:12-44`) に現れている。
- **壊れ方**: plan どおり mutation profile だけ実装して wave を完了扱いにする → D895 の汎用 task は未実装のままなのに、D842 を「扱った」と解釈して裁定済み backlog を欠落させる。
- **重大度**: 受理集合
- **提案**: 段 4 で D895 を入力へ戻す。作らないなら D895 を supersede する新裁定が必要。作るなら、shell string ではなく `shell=False` の非空 argv、clean env、stdin=`DEVNULL`、repo cwd、子 rc 伝播、二重 compute-site gate を契約にする。

## 所見 2 — generic 経由は hook を通る場合と通らない場合があり、無効化数は歴史的 13 本中 11 本である

- **所見**: plan の「sanctioned dispatcher なら inner argv は常に未検査」という説明は誤りだが、歴史的 13 経路のうち 11 本は generic の後ろへ置くと実際に許可へ反転する。
- **なぜ real か**: 現 hook の literal 重量拒否は次を持つ。

  - `pytest` / `py.test` と `python* -m {pytest, pytest.__main__, _pytest.main}` (`hooks/guard_bash.py:321-324,1003-1012,1232-1241`)
  - `cmake --build`、並列 `make`、`ninja`、`ctest` (`hooks/guard_bash.py:1015-1017,1024-1030,1243-1262`)
  - `perf stat/record`、`build-variants` 配下実行体、`ycsb_*.exe` (`hooks/guard_bash.py:346-350,1263-1268`)
  - `bash` / `sh` / `zsh -c` の再帰解析 (`hooks/guard_bash.py:1216-1224`)
  - raw `systemd-run` (`hooks/guard_bash.py:1186-1189`)
  - 未登録・非 `local-ok` admission 実行体 (`hooks/guard_bash.py:1200-1210`)

  ただし `_interpreter_residual_violation()` は sanctioned 判定より先に走り、argv 全域の `-m pytest` を拾う (`hooks/guard_bash.py:1106-1176,1212-1230`)。静的に `GB.decide()` を当てると、次は拒否のままだった。

  ```text
  python3 tools/pegasus/dispatch_compute.py --task generic -- python3.10 -m pytest -q
  ```

  一方、`-- pytest`、`py.test`、venv pytest、shell `-c`、cmake、make、ninja、ctest、perf、`build-variants` 実行体は許可へ反転した。D103 の一次資料では 13 本中 1 本が既存 `run_tests.py` dispatch、12 本が hook-only であり (`output/insights/2026-07-30_pegasus-compute-node-dispatch/adv_b.md:15-65`)、そのうち `python3.10 -m pytest` だけが現コードで残る。したがって無効化は **11/13**。現在の hook は D103 当時より綴りを増やしているので、「現に止めている経路は exact 13 本」という前提自体も古い。
- **壊れ方**: `dispatch_compute ... -- pytest -q` → outer target が sanctioned と判定され、直接 pytest 拒否へ到達しない。一方、同値な `-- python3 -m pytest -q` → residual scan だけが発火して拒否される。generic task が綴り依存で「任意」でなくなる。
- **重大度**: 正しさ防壁
- **提案**: generic task の exact CLI 境界を hook に認識させ、D895 の正規形だけは inner argv の重量判定対象外にする。`pytest` と `python -m pytest` の双方を正例にし、未知 task、直接 trampoline、壊れた registry は負例のまま固定する。歴史的件数は 11/13 と記録する。

## 所見 3 — P1 は compute transport と login-side trampoline を同一視している

- **所見**: generic task が hook の字句拒否を通ることは事実だが、それだけで D103 が退けた login-side `exec_calibrate.py` と同じ穴とは言えない。
- **なぜ real か**: `dispatch_compute.py` は admission 上も「login-side compute dispatcher with a self-gated job mode」である (`tools/pegasus/admission_registry.json:34-38`)。job script は bnode 以外で子を起動しない (`tools/pegasus/dispatch_compute.py:602-605`)。`_job_run` も独立に bnode を要求する (`同:675-724`)。対して `exec_calibrate.py` は呼ばれた process 上で直ちに任意 argv を `os.execv` する (`tools/pegasus/exec_calibrate.py:32-44`)。
- **壊れ方**: 両者を同一視して generic を不採用にする → 二重 hostname gate、receipt、会計照合を持つ compute transportまで、login で任意 exec する部品と同じ理由で拒否し、D895 の正規用途を失う。
- **重大度**: 受理集合
- **提案**: D103 から維持する性質を「任意 argv を login で実行しない」に限定する。generic は compute-only transport とし、任意 env、shell 展開、stdin、caller cwd は許可しない。D103 の「exact path に任意 trampoline を載せない」を文字どおり維持する必要があるなら、D895 との衝突を段 4 の裁定へ返す。

## 所見 4 — drift 検査は新 task の closed policy に対して恒真になり得る

- **所見**: `check_docs.py` は task 名と `child_script` しか比較せず、`env_mode`、`argv_policy`、親子双方での validator 発火を何も証明しない。
- **なぜ real か**: AST 抽出は `_TaskSpec` の `child_script` keywordだけを読む (`tools/check_docs.py:3451-3492`)。比較対象も `{task: child_script}` だけである (`同:3515-3553`)。静的 probe では次が finding なしで抽出された。

  ```python
  TASKS = {
      "mutation": _TaskSpec(
          child_script=("tools", "mutation_worktree.py"),
          argv_policy="allow-all",
      ),
  }
  ```

  結果は `{"mutation": "tools/mutation_worktree.py"}`、findings は空だった。plan の argv 負例は「qsub 前」の親側だけで (`s2/plan.md:383-384`)、forged request に対する子側 argv policy の独立テストも無い。
- **壊れ方**: mutation 行と runbook 行だけを追加し、`argv_policy="allow-all"` または子 validator 呼出しを欠落させる → `check_docs.py` は緑、親側テストも通るが、forged request は子側から selector・plugin・`--force-dispatch` を実行できる。
- **重大度**: 正しさ防壁
- **提案**: D117 の否定文はそのまま維持する。最小修正は、親と `_job_run` それぞれへ同じ不正 argv を入れる負例を追加すること。drift 検査にも責務を持たせるなら、表と AST を `{child_script, env_mode, argv_policy}` まで比較する。ただし、それでも validator の実発火までは保証しないと明記する。D117 決定 6 の否定文は task 追加後もなお正しい。

## 所見 5 — `TASKS` と表が食い違ったまま検査を通る実在構文がある

- **所見**: M4 の「alias 経由も赤」は false で、container 経由の alias mutation は AST 検査を通過する。
- **なぜ real か**: alias 判定は assignment RHS が直接 `Name("TASKS")` の場合だけである (`tools/check_docs.py:3357-3362`)。後続書込みも、その AST subtree 内に `Name("TASKS")` がある場合だけ拾う (`同:3383-3390`)。次の静的 probe は runtime では generic を追加するが、extractor は `tests` だけを返し findings は空だった。

  ```python
  (alias,) = (TASKS,)
  alias["generic"] = _TaskSpec(
      child_script=("tools", "generic.py"),
  )
  ```

  既存負例は直接 alias `alias = TASKS` までである (`orchestrator/tests/test_check_docs.py:2557-2582`)。さらに、表が一致していても runbook の「2 taskだけ」「第3 task未実装」という prose は検査対象外である (`docs/pegasus-runbook.md:565-574,588-597`)。
- **壊れ方**: container alias で runtime task を追加し表を更新しない → dispatcher は generic を受理するが checker は旧2 taskと旧表を一致と判定する。別経路では、literal mutation 行と表だけ更新して prose を残す → checker は通るが運用文書は第3 task不在を主張する。
- **重大度**: 実効性
- **提案**: assignment RHS の subtree に `TASKS` load が含まれる alias escape、function default capture、container unpackを拒否し、対応負例を足す。runbook の task 数 prose は削除して表だけを正本にするか、現行語句の不在を検査する。

## 所見 6 — mutation task を足しても canonical 本走は旧 transport のままである

- **所見**: plan は task の producer を作るが、通常の変異本走 consumerを切り替えていないため、D842 の効果が発火しない。
- **なぜ real か**: canonical 手順は依然 `--runner-mode dispatch` と runner の `--force-dispatch` を要求する (`docs/dev-wave/mutation.md:43-50`, `docs/pegasus-runbook.md:1157-1172`)。これは変異ごとの inner dispatch である。plan の runbook変更は exact task 表と周辺 proseだけ (`s2/plan.md:335-361`)。fanout callerへの配線は条件付き (`同:182,429-446,473`) で、直接 wrapper を outer taskへ送る canonical recipe の更新も integration test も無い。
- **壊れ方**: `TASKS["mutation"]` を landし、既存 DW-M07 recipe で次 wave の変異を実行 → harness は login に残り、各 collection/baseline/mutation が従来どおり別 PBS jobになる。新 task は未使用の装飾になる。
- **重大度**: 実効性
- **提案**: 最低1本の canonical consumerを同じ scope に入れる。fanoutを採らないなら、`mutation_worktree.py --runner-mode local` 全体を `--task mutation` で包む直接 recipeを `DW-M07` と runbook §7.4 に固定し、「outer request 1、inner request 0」を検査する。

## 所見 7 — D131 scope は #1〜#5 を払う一方、fanout 部分だけが未裁定のまま肥大している

- **所見**: direct wrapper transportには #1〜#5 が必要だが、local attempt sidecarと fanout merger 全面改修は D433 を開かない限り必須ではない。

- **なぜ real か**:

  | D131 | plan の扱い | 判定 |
  |---|---|---|
  | #1 lock | wrapper固定、artifact envelope (`s2/plan.md:28-32`) | 必須 |
  | #2 永続証拠 | outer root、local sidecar、fanout contract (`同:47-64`) | outer証拠は必須、per-attempt/fanoutは条件付き |
  | #3 login local拒否 | harness・wrapper双方 (`同:75-80`) | 必須 |
  | #4 canonical argv | task policyを親子で検査 (`同:94-102,178-181`) | 必須 |
  | #5 env/stdin/cwd/rc | clean env、DEVNULL、rc分類 (`同:104-122,264-293`) | 必須 |
  | #6 deadline/qdel | production変更なし (`同:124-137`) | 現行の狭い契約では済み |

  wrapper receipt はすでに child rc、lock、ledger終端、dispatch evidence pathを持つ (`tools/mutation_worktree.py:998-1027`)。一方、現 fanout contract は各 inner requestを全行へ要求し、総数を `変異数 + 2N + history` に固定する (`tools/mutation_fanout_contract.py:1309-1405,1470-1474`)。D433 は fanout admissionをこの機体で恒偽と確定し、schema v2 は別のユーザー裁定事項としている (`docs/decisions.md:18009-18027`)。
- **壊れ方**: fanoutを scope 外としながら local sidecar・merger・request-count schemaまで変更 → 使われない証拠モデルに多数ファイルとテストを費やし、1 waveで終わらない。逆に P2 の shard単位を採りながら fanoutを切る → taskは実 consumerを失う。
- **重大度**: 実効性
- **提案**: 段 4 で二択にする。推奨は direct wrapper 1 invocation = 1 jobを先に完成させ、outer receiptを wrapper receiptへ一度だけ束縛する形。fanout、local per-attempt sidecar、merger request-count v2 は D433 の別裁定へ残す。shard単位を必須と裁定するなら、D433 redesign は閂なので scope 外にできない。

## 所見 8 — M6 の「走行中 job への qdel 禁止」は反例が正本に明記済みである

- **所見**: qdel gate が保証するのは fresh snapshot が QUE/HLDだったことまでで、qdel時点の非RUNは保証しない。
- **なぜ real か**: 実装 docstring が qstat と qdel は非atomicであると明記する (`tools/pegasus/dispatch_compute.py:1803-1808`)。D142 も「qdel時点で対象が RUNでないことは保証しない」と明記する (`docs/decisions.md:6928-6931`)。brief M6 の「走行中 jobへの qdel禁止」 (`brief.md:42-45`) はこの限定を落としている。
- **壊れ方**: qstatでQUEを観測 → 直後にschedulerがRUNへ遷移 → `_best_effort_qdel` が発行され、走行中jobを消す可能性がある。それでも receipt 上は正規の fresh-snapshot gate通過になる。
- **重大度**: 正しさ防壁
- **提案**: コード変更は不要。M6 と plan の「完全充足」を「fresh snapshot がRUNなら発行しない。qstat/qdel間遷移は保証外」に修正する。atomicな非RUN保証へ広げるなら別設計である。

## 総括

### (a) must-fix

- D895 を無視して generic task を不採用にする plan。
- hook の実順序と 11/13 の無効化を誤認した P1/plan。
- 子側 argv policy の独立負例欠落。
- `TASKS` container aliasで drift検査を通る穴。
- mutation taskを canonical 本走へ結線しない実効性欠落。
- fanoutを採るか切るかを決めず、関連 schemaだけを広げる scope不整合。
- M6 の qdel保証の過大表現。

### (b) 親が段 4 で裁定すべき論点

- D895 が D103 の「任意 trampolineをsanctionしない」をどの範囲で supersedeするか。
- generic taskの最小契約を「直接 argv、clean env、stdin閉鎖、repo cwd、compute-only、rc伝播」とするか。
- mutation transportを direct wrapper 1 jobで閉じるか、D433 redesignを含めて shard fanoutへ結ぶか。
- `check_docs.py` の責務を child path同期だけに維持するか、policy literalの同期まで広げるか。

### (c) 攻撃したが破れなかった箇所

- plan は `TASKS` をliteral source定義に保ち、runtime registryを導入しない。通常の entry追加が「コード変更なし」でできる経路は見つからなかった。
- 通常のliteral entry追加と exact表の片側更新は、現 checkerが正しく赤にする。
- D117 決定 6 の否定文は task追加後も正しい。検査が保証するのは公表 mappingの同期だけである。
- `_job_script` と `_job_run` の二重 bnode gateは実在し、generic transportを直ちに login-side execと同一視する根拠にはならない。
- RUN初観測からのdeadline rebaseと fresh-qstat gate自体は実在する。破れたのは M6 の保証表現であり、D142の狭い実装契約ではない。
- pytestは実走していない。上記はコード読解と `check_docs` extractor / hook判定関数への静的 probeだけで、緑の主張はない。