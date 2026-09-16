---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2228-screening-liveness
seq: 2
---

## {{D:screening-liveness-entry-form}}. screening 関門の生死確認は generic dispatch + job dir の最小 launcher から正規 CLI を起動する形で行い、投入元への CLI の一時 patch は正規挙動として許容する

**決定:** `backoff_sweep` の screening 関門の生死確認 (D1784 の再訪条件) は、既存の
`tools/pegasus/dispatch_compute.py --task generic` から、repo 外 (job dir) に置いた最小 launcher
(bash 1 本、Codex author が書き、敵対レビュー 2 本と焦点再レビューを通す) 経由で、現行の正規 CLI
`python3.10 -I -B -u orchestrator/campaign/backoff_sweep.py write-heavy --screening --screening-fixed-us 2`
を 1 回起動する形で行う。A-5 job body (`tools/pegasus/a5_second_boot_backoff_sweep.sh`) は改修しない。
launcher の責務は、前提検査 (HEAD・CCBench pin・tracked-clean・official root 未存在・`/scr`)、
割当ノード上の単独性の観測と拒否、A-5 と同値の env 供給 (固定 PATH・unset 群・`TMPDIR` を `/scr` の
`mktemp -d`・job 固有 bench lock・official root・gflags/glog prefix・proxy)、正規 CLI の 1 回起動、
終了後の tree 状態の出力に限る。clone による実行木の隔離は行わず、CLI が投入元 submodule へ
`patchharness.applied` (pinned-clean 検査 → `git apply` → revert) と stock checkout の一時 worktree
登録・撤去を行うことを **CLI の正規挙動として許容**する。代わりに、投入から終了まで親は wave worktree に
git 操作・test 実走・編集を行わず (worktree は lock 済み)、launcher が起動前に両 tree の HEAD/pin と
tracked-clean を検査し終了後に status と worktree list を出力し、親が終了後に login で同じ検査を再実測する。

launcher は generic dispatch の clean env (`HOME LANG LANGUAGE LC_ALL LC_CTYPE LOGNAME PATH TZ USER`) だけを
前提にし、`PBS_JOBID` を要求しない。job の帰属は dispatcher の result / receipt が持つ。

**理由:**
- 依頼は「現行の正規入口 (CLI の `screening_fixed_us`、tools/pegasus の投入 script) から」「実装差分は
  既定でゼロ」「本題の 1 走だけ」を求めた。A-5 job body は `--screening` を渡さず finalize が 8 genome 全 commit を
  要求し、submitter は 2 workload 固定なので、最小 screening を A-5 経由で走らせるには実装差分が要る。
  generic dispatcher から現行 `main` を起動する形は、production 無編集で CLI 入口を通る (段 3 レンズ A が
  「A-5 改修は不要」と裁定)。
- CLI 単体は環境 (official root・prefix・proxy・TMPDIR) を要求し、generic の clean env では届かない。
  最小 launcher は env 供給と単独性の観測のためだけに要り、D1786 (probe 投入 script を repo へ実行体として
  置かない) に従い repo 外に置いて `.txt` の写しだけを証拠に残す。
- 独立 clone で実行木を隔離する形 (前回 probe・A-5) は launcher を膨らませ clone 所要と失敗面を増やす。
  CLI の in-place patch は pinned-clean 検査と revert を伴う正規挙動であり、専用 worktree を lock して
  親が触らなければ source identity は保たれる。異常終了時は親が終了後検査で dirty・dangling を検出して復旧する。
- generic の clean env に `PBS_JOBID` が無いことは、段 6 の敵対レビュー 2 本が独立に見つけた。親の author 仕様が
  brief で clean env の鍵集合を書きながら `PBS_JOBID` を必須にした誤りで、DW-O13 (gate 入力の実在) の型である。

**却下した選択肢:**
- A-5 へ screening option を足す — 実装差分 (job body・submitter・finalize・sha 束縛の再計算) と Codex author・
  受入が要り、依頼の「実装差分は既定でゼロ」に反する。
- `env` 前置だけで launcher を置かない — 単独性の観測 (依頼の「単独性を確認してから投入」) と `TMPDIR` の job 固有化・
  終了後の tree 状態の記録ができない。
- launcher で独立 clone を作る — 上記のとおり最小性に反する。

## {{D:screening-liveness-green-record}}. screening 関門の緑は baseline の新規 WAL record と会計照合済み rc=0 による間接証拠として記録し、arm record・meaning 腕・成功 reason の限定を明記する

**決定:** `backoff_sweep` の screening 関門 (`screening_driver._run_condition_gate_for_genome`) について
「緑になった」と名乗る条件を、次の証拠組をすべて満たすこととする。
1. 未使用の official root と今回の dispatch request が対応する。
2. `campaign.lock` が対象 workload・`screening_fixed_us`・実行契約を示す。
3. baseline の `build-start.payload.genome` が `BACK_OFF=0, BACKOFF_FIXED=-1` を示す。
4. 同じ variant・同じ `build_attempt_id` に新規 `bench-done` と後続 `commit` があり、`build-done`
   (toolchain・binary hash・configure/build argv) も保存されている。
5. dispatch の `result.stage=child`・`child_rc=0`、receipt の `outcome.kind=child`・`rc=0`・会計照合済み。
6. stdout の campaign ID・結果と WAL が一致し、production file・dispatcher・launcher の sha256 を記録している。

これは**間接証拠**である。production 経路は関門の arm record を作って捨て (`evaluate_candidate` が
戻り値を破棄し、赤は try/except の外で例外として process を止める。D1912 が `backoff_sweep.py` を名指し)、
緑を直接記録する仕組みは無い。「関門が走った」ことは、その実行コードの制御フロー — 対象 baseline は
request 非空 (`BACKOFF_FIXED=-1`、stock 比較) かつ `force=True` で、関門呼び出しが build・bench の前に
あり、拒否は process を止める — からの推論で支える。

README には次の限定を必ず書く: baseline の meaning 腕は `unestablished / meaning-witness-undeclared`
(`_backoff_fixed_declarations` は非負値にしか declaration を作らない)、成功 supply reason
(`stock-inert-preprocess-identical` / `stock-inert-preprocess-root-location-only`) は WAL からは識別できない、
family admission は supply 全件緑 + meaning 緑または unestablished で通る既存条件である、rc=0 は候補の
`screen-slower-than-floor` と両立する、被覆は 1 workload・2 genome・1 走で、通常 7 値 family・他 workload・
他 driver・将来 HEAD・adaptive の実行時動作・A-5 環境との等価性を保証しない。
候補段で赤でも baseline の関門通過は否定しないが、「CLI 全体正常終了」の完了条件は未達とする。

**理由:**
- 段 3 レンズ B が、空 request・`force=True`・WAL replay・stock checkout 失敗の握り潰し・空 preprocess・
  既存成果物の更新の 6 経路を file:line で検査し、今回の baseline に限れば恒真経路が無いことを裏取りした。
- 環境供給 (official root・prefix・proxy・TMPDIR・PATH) は関門の判定式・既定値を変えないが到達性を変える。
  D1784 の「制御された拡張」を環境も含めた不変性へ読み替えない (規律 2)。
- 記録される緑は「当時・そのコード・その道具」の事実であり、現行主張と分ける (規律 7)。

**却下した選択肢:**
- `strace` / Python `trace` による関門実行の直接痕跡の採取 — `trace` と `cProfile` は `SystemExit` を捕捉して
  CLI の rc を壊し、`strace` は計測に干渉する。仮想リスク向けの観測追加であり本 wave の scope 外。
- arm record の永続化を `backoff_sweep` へ横展開 — D1912 が DW-G03 (独立 2 例) で保留中。裁定パッケージ候補として残す。
