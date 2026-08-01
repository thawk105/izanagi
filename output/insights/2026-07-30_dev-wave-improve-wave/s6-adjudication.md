# dev-wave-improve 段6 review 裁定

時刻: 2026-07-30 13:12 JST

対象は統合前固定 patch
`/home/SFC/tanab/.codex/dev-wave-improve-wave/s6-integrated-pre-review.patch`
(SHA-256
`94e548112d7de7d062b38843465d2c2e406188d8a97b8e64938d75070869234d`)
である。reviewer A/B はともに rc=0、`check_codex_output.py` green、NO-GO
だった。pytest / build / qsub は未実走であり、green と扱わない。

## reviewer artifact

- A:
  `/home/SFC/tanab/.codex/dev-wave-improve-wave/s6-review-scheduler/output.md`
- B:
  `/home/SFC/tanab/.codex/dev-wave-improve-wave/s6-review-contract/output.md`

## 採用

### U1

- unrelated host + non-NQSV PBS は OTHER とし、Pegasus-like / bnode の
  fail-closed と分離する。
- OTHER で affinity API がない場合だけ `os.cpu_count()` fallback を許す。
- OTHER の既存 xdist `-n auto/logical` 受理集合を変えない。
- pytest が収集し得る `test_default_workers` / `test_default_jobs` 公開名を廃し、
  build job と誤読されない API 名にする。

### U2

- 既存 provenance-bound `tools/pegasus/policy.json` を byte-exact に戻し、
  test dispatch の資源設定を別正本へ分離する。U2 が新正本を所有する。
- snapshot manifest は少なくとも実行する runner / submitter / job script /
  selected tests と policy の path、mode、symlink 状態、SHA-256 を束縛し、
  worker 開始直前と runner 終了後に再検証する。job script の root 外
  symlink は拒否する。
- source local Git config / `.git/info/attributes` による login 上の code
  execution と checkout filter を許さない。
- snapshot projected aggregate、全 regular file の per-file 上限、copy 後
  再検査、partial cleanup、bounded spool / retention を実装する。
- NQSV accounting は stderr の安定後 epilogue を exact job ID と
  Started / Ended / Elapse で検証し、qstat rc=0 を accounting としない。
- qstat は exact state allowlist、回復可能 transient、qsub 時刻からの
  absolute deadline を持つ。runner-result の存在だけで disappearance としない。
- qsub 直前から final までを一つの補償状態機械にし、timeout は
  `SUBMIT_UNKNOWN`、既知 ID 後の例外 / signal は qdel、resume は WAL から照合し
  自動再 qsub しない。
- runner-result / final の outcome 別 exact schema と status domain を一元化し、
  incomplete final や負 rc を成功へ倒さない。
- exact qsub argv/env、policy/job-script/manifest、stdout/stderr/rc、
  accounting、journal prev-hash を receipt chain へ入れる。
- worker は closed env、`PYTHONNOUSERSITE=1`、dependency-aware interpreter
  selection を使う。hostname / affinity / environment receipt と task-run
  durable event を final まで束縛する。
- safe な `PYTEST_ADDOPTS` と core `-h` 等は解析・束縛して既存受理集合を維持し、
  external plugin/path/argsfile は拒否する。
- qsub resource flags を policy と exact 比較し、fake tests を raw file /
  canonical JSON / real branch に寄せる。

### U3

- 段6で新たに実在consumer欠落が確定したため、U3 ownershipへ
  `orchestrator/campaign/s8a_trigger_freq.py` を明示追加する。これはreview後・
  統合前のowner再裁定であり、事後の無記録追認にはしない。
- canonical `pegasus_policy` は `<repo>/tools/pegasus_policy.py` の resolved
  path と module identity を検証し、`sys.path` / `sys.modules` poison を拒否する。
- `s8a_trigger_freq` を含む 4 direct coverage consumer は pin / patch /
  tempdir / subprocess より前に main gate を通す。
- 4 helper を直接呼ぶ mutation test を設け、login は副作用前拒否、
  compute / OTHER は mock subprocess の `-j16` 到達まで確認する。

### U4

- `env -S` / `env --split-string` payload を再 tokenize し、direct pytest /
  build bypass を拒否する。不正 payload は login で fail-closed。

## 却下または限定採用

- OS-level network namespace の新設は今回の entrypoint scope を越えるため却下する。
  closed env、proxy 削除、既存 no-network test 契約は維持し、「system-wide network
  isolation」とは記録しない。
- manifest に repository 全 tracked bytes を常に列挙する要求は、実行 closure と
  staged tests の束縛へ限定採用する。snapshot 全体は source manifest / aggregate
  digest で束縛し、実行時に読む closure は個別 hash で強化する。
- qlogin markerless execution、buildcache v3 receipt、任意 shell / Codex /
  compiler の system-wide enforcement は段4どおり defer のまま。
- U1 alias の問題は reviewer B では LOW だったが、小さい公開 API 汚染であり
  U1 fix に同梱する。

## 再 review / live 投入 gate

1. U1〜U4 の各 owner が自分の元 worktreeだけを修正する。
2. 親は owner patch のみを統合し、current bytes で focused adversarial
   re-review を行う。
3. must-fix を closed / partial / regressed 表で裁定する。
4. GO 後にのみ、Pegasus runbook §8 を再読して qstat / pegasusinfo /
   rbudgetcheck / quota を確認し、計算ノードで targeted test、full test、
   mutation、acceptance を行う。
