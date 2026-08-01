# 段4 mutation事前登録

各変異はcompute nodeのisolated committed test snapshotで一件ずつ行い、前段maskを
ordered trace / fatal sentinelで除外する。login/live branchを要するものはfake unitだけで
完遂扱いにせず、live control receiptも要求する。

| ID | 単一変異 | 期待する赤 | 前段maskを避ける正例 |
|---|---|---|---|
| M1 | unknown NQSV hostnameをOTHERへdowngrade | policy unknown-PBS exact cause | known other + no PBSは受理 |
| M2 | canonical hostnameのlowercase/末尾dot処理を除去 | short/FQDN equivalence | evil suffixは拒否のまま |
| M3 | compute default workersを32固定 | affinity48 default argv | explicit `-n0` はserial受理 |
| M4 | explicit workerがaffinity超過でも受理 | oversubscription exact cause | explicit 7は受理 |
| M5 | login dispatchをpreflight後へ移動 | ordered trace違反 | compute markerでpreflight一回 |
| M6 | absolute targetを元repoのまま渡す | worker target root mismatch | snapshot-relative targetは受理 |
| M7 | cached patchを`--index`なしで適用 | staged deletion/status mismatch | unstaged modificationを保持 |
| M8 | argsfileまたは外部plugin pathをhashなしで受理 | external-input exact cause | repo内通常targetは受理 |
| M9 | local `--collect-only`をno-execution扱い | pytest/plugin sentinelがloginで発火 | wrapper自身の`--help`はqsub/pytest 0回 |
| M10 | qsub前journal fsyncを除去 | transition order / missing WAL | valid pre-submit→qsub path |
| M11 | qstat rc1をterminal disappearance扱い | transient retry trace | true disappearance + log grace |
| M12 | runner-result不在をchild rc=0扱い | missing-child-result exact cause | real rc0 receiptは受理 |
| M13 | cancel後のlate successへ反転 | cancellation monotonicity | normal successは受理 |
| M14 | qdel retryを除去 | transient qdel failure trace | first-attempt qdel success |
| M15 | task-runをdispatch success正本にする | accounting failure + task-run green | full final receipt + event有無両方 |
| M16 | v2 login miss gateを`os.makedirs`後へ移動 | write-before-refusal sentinel | valid cache hitはloginで受理 |
| M17 | login cache hitまで拒否 | valid-hit positive control | missはconfigure/build 0回で拒否 |
| M18 | coverage helper gateをconfigure後へ移動 | subprocess-before-refusal sentinel | compute/otherは現行`-j16` |
| M19 | guard heavy gateをprotected-path fast path後へ移動 | direct pytest/build command test | qsub/runner/configureは許可 |
| M20 | policyを別module名で二重load | Enum/type identity import test | python `-I`, hook, direct campaignの4形 |

凍結/provenance control:

- cache key、contract、completion exact keys、BuildResult field集合の既存goldenは不変。
- `FROZEN_MANIFEST` 23件、protocol、selector、v1 freezeのSHA比較を正例として登録する。
- `build_argv` actual化、official cached拒否、v3 field追加の変異は今回の実装に存在しないため
  登録せず、裁定パッケージの次waveへ送る。
