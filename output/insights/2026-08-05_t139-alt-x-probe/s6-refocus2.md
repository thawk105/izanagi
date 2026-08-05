| 所見 | 判定 | 根拠 |
|---|---|---|
| G1 共有起点・固定終端 | `partial` | 実装は process-wide の function-local static を一度だけ初期化し、`[0,1500ms)` / `[1500,3000ms)`、以後無出力を実装している。全体が `ADD_ANALYSIS` 内なので性能 build には入らない: `tools/pegasus/probes/t139_positive_control.patch:64-117`。起点は barrier 自体ではなく、解放後に最初の worker が `makeProcedure()` を経て `begin()` に到達した時点: `external/ccbench/common/runner.hh:189-193,294-299`、`external/ccbench/include/ycsb.hh:102-113`。さらに preregistration が「共有単一起点」と「各 worker の初回試行起点」を同時に記しており未閉鎖: `output/insights/2026-08-05_t139-alt-x-probe/preregistration.md:64-66,90-93`。 |
| G2 qsub 時点 commit 束縛 | `closed` | 40桁の期待 commit を必須化し、job 開始時 HEAD と exact 比較した後、その commit の blob だけを展開する: `tools/pegasus/probes/t139_positive_control_probe.pbs:46-70,105-121`。未指定・queue 中の HEAD 移動はいずれも pre-performance failure になる。 |
| G3 canonical path exact 比較 | `closed` | repo 相対 path 全体を literal exact 比較し、その commit 内から読む: `tools/pegasus/probes/t139_positive_control_probe.pbs:101-123`。実ファイルの path と study literal は一致する: `output/insights/2026-08-05_t139-alt-x-probe/preregistration.md:1,6`。 |
| G4 Git object snapshot | `regressed` | `read-tree` と `checkout-index` 自体は一時 index と pin を正しく使う: `tools/pegasus/probes/t139_positive_control_probe.pbs:157-205,267-286`。しかし snapshot 全体を read-only 化し、その属性を保持して書込み consumer に渡したため、pre-performance failure を新設している: PBS`:204,265`、driver`:370-373,376-382`。 |
| G5 早期 EXIT trap | `closed` | scheduler の二変数から `OUT` を確定後、`run_commit=unavailable` と trap を設置し、その後に必須 env/HEAD を検査する: `tools/pegasus/probes/t139_positive_control_probe.pbs:8-50`。既存 terminal state は保持される: PBS`:15-39`。科学的 false は明示的に `verdict_false` を書いて rc=0 で終わる: driver`:559-568`。 |
| G6 直列 cap | `closed` | 前段は `33 + 25 + 10 + 90 + 10 + 150 + 10 + 90 + 420 = 838` 秒。driver 内部は `150 + 6×(60+180+10) + 6×30 + 30×15 = 2280` 秒で、全体の `2400` 秒 cap 内に入る。したがって支配 cap は `838 + 2400 = 3238 ≤ 3300`: PBS`:304-309`、driver`:367-372,399-409,443-495`。driver 内部 2280 を外枠 2400 に重ねて加算する誤りはない。 |

`closed` は静的な実装判定であり、計算ノード E2E の緑を意味しない。

## 新規所見

[blocker] [G4 fix が object snapshot を書込み不能のまま consumer へ渡している。`chmod -R a-w` 後の CCBench を `cp -a` し、そのコピーへ patch を適用する。また masstree は同じ read-only source 内で `config.h`・object・archive を生成する] [根拠: `tools/pegasus/probes/t139_positive_control_probe.pbs:193-205,252-265`、`tools/pegasus/probes/t139_positive_control_probe.sh:370-382`、`external/ccbench/cmake/ThirdParty.cmake:57-75`] [成果物影響: patch または最初の masstree build が性能段より前に失敗し、allocation と長い queue 待ちを丸ごと失う。さらに read-only tree は trap の `rm -rf` でも残置し得る: PBS`:34-35`] [最小の直し方: immutable object snapshot は保持し、patch/build 用に別の writable job-local copyを作る。`src-probe` と masstree consumer をその copy へ向け、cleanup 前に stage を owner-writable に戻す]

[blocker] [1巡目の P-A/P-C が canonical preregistration に残っている。共有単一起点と per-worker 起点が矛盾し、数値境界も未記載。加えて pre-qsub receipt の列挙から dependency tree SHA が欠落する] [根拠: `output/insights/2026-08-05_t139-alt-x-probe/preregistration.md:64-76,90-93`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/s4-adjudication.md:78-80,116-121`] [成果物影響: liveness の受理集合を走行後に一意に解釈できず、事前登録済み study identity として結果を採用できない] [最小の直し方: 実装に合わせて「全 worker 共通で最初の `begin()` を起点、`[0,1500ms)` / `[1500,3000ms)`、以後無出力」と一意に書き、receipt 必須項目へ dependency tree SHA を追加する。barrier 起点を意図するなら文書でなく実装を直す]

[nit] [`<root>/gflags`・`<root>/glog` の非 symlink 検査は `realpath` 後の path に対して行われるため、子 directory が symlink でも受理する] [根拠: `tools/pegasus/probes/t139_positive_control_probe.pbs:162,210-226`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-alt-x-probe/s4-adjudication.md:100-102`] [成果物影響: 今回 direct directory を渡す限り成果物影響はないが、別の env 値では裁定より広い入力を受理する] [最小の直し方: `realpath` 前の `"$DEPENDENCY_ROOT/$name"` に `-d && ! -L` を適用する]

## 回帰・state 確認

- F1 は `closed` 維持。transaction/result/util の exact-one と macro exact 検査は残る: `tools/pegasus/probes/t139_positive_control_probe.sh:50-94,399-418`。
- F3 は `closed` 維持。main と各 source の `git status` 非0を拒否する: PBS`:80-91,159-175`。
- F7 は `closed` 維持。TPS を先に primary へ確定し、副次診断欠落は `NA` に限られる: driver`:499-551`。
- terminal state の二重発行・未発行・上書きは、scheduler 自体の二変数欠落を除き見当たらない。trap は既存 state を保持する: PBS`:15-39`、driver`:311-323`。
- `verdict_false` は rc=0 なので、qstat success は pass ではない。state 名は明確だが、親は必ず `terminal-state.tsv` と `verdict.tsv` を突き合わせる必要がある。

## Refuted

- non-`thread_local` magic static が worker ごとに初期化される懸念は refuted。C++ の thread-safe static initialization により一度だけ初期化され、競合 thread は初回だけ待つ。しかも全コードが `ADD_ANALYSIS` 内なので性能 build への影響はない: patch`:64-117`。
- submodule の `.git` gitdir file により `git -C` / `cat-file` が失敗する懸念は refuted: `external/ccbench/.git:1`、PBS`:179-199`。`--no-replace-objects` の位置と一時 `GIT_INDEX_FILE` の scope も正しい。read-only 制約のため `read-tree`/`checkout-index` の書込み fixture 自体は再実行していない。
- G6 のループ数・入れ子による cap 超過は refuted。支配 cap は 3238 秒。
- F1/F3/F7 の回帰、および terminal state の二重発行は refuted。

静的検査のみ実施した。`bash -n`、`git diff --check`、CCBench に対する `git apply --check` は rc=0。build・pytest・qsub・書込みを伴う object checkout は実行しておらず、緑とは判定していない。

## 総括

- (a) 投入: **NO-GO**
- (b) blocker: **2件**
- (c) regressed: **1件（G4）**
- (d) refuted: magic static の worker 別初期化／性能 build 混入、submodule gitdir による Git command 不成立、G6 cap 数え落とし、F1/F3/F7 回帰、terminal state 二重発行
- (e) 親が投入前に手で確認すべきこと:

  - 上記2 blockerを修正し、object snapshot → writable consumer copy → patch → masstree build の経路を計算ノードで実測する。
  - copy/chmod 追加後も driver 外枠を含む直列 cap が `≤3300` 秒か再計算する。
  - probe 3ファイルと修正済み preregistration を同一 commit に含める。
  - qsub 前の append-only receipt に期待 commit、3 blob hash、policy hash、canonical path、各 root/pin、dependency tree SHA を固定する。
  - qsub で `IZANAGI_T139_EXPECTED_COMMIT` ほか必須 env を明示し、6 source が投入時にも direct directory・clean・pin一致であることを再確認する。
  - 実走後は PBS rc ではなく `state/terminal-state.tsv` と `verdict.tsv` を照合し、全 submission ID を記録する。