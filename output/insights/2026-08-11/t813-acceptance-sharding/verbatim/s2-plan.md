# 段 2 起草結果

必読資料はすべて読めた。静的調査だけを行い、実装・編集・commit・テスト／性能測定は行っていない。

結論は、現状の suite では M1 型のシャーディングは I1 を満たさない。F-9 は測定誤差ではなく、分割によってテストの意味が変わる反例である。直近の推奨は M4、将来のノード横断候補は M5 とする。

## 親 provisional 案への判断

| 親案 | 判断 | 修正 |
|---|---|---|
| P1: file 単位 | 条件付き支持 | argv と manifest の分割単位には妥当。ただし file は意味論的独立単位ではない。F-9 が反例。 |
| P2: group-atomic | 必要だが不十分 | `real-repo` 13 file の固定表だけでなく、collection hook 後の全 `xdist_group` の同名閉包を一つの shard に置く。 |
| P3(a): collection の集合一致 | 否定 | 順序・重複・collection error・post-hook marker を含む「順序付き多重集合」が必要。 |
| P3(b): nodeid exactly once | 支持・強化 | nodeid 文字列ではなく canonical ordinal を主鍵にし、report phase と receipt まで一意に束縛する。 |
| P3(c): 各 shard が gate を通る | 否定 | acceptance の主体は coordinator。594/632 は合成走行で一回、705 は execution root ごと、1677 は shard の非受入性を示す。 |
| P3(d): `max(rc)` | 否定 | rc は順序尺度ではない。型付き結果ベクトルと fail-closed な boolean 集約が必要。 |
| P3(e): 分割不変性 | 支持 | manifest の帰結ではなく事前条件。現状は成立していない。 |
| P4: manifest 証明 | 必要だが不十分 | collection 被覆は証明できても、session/import 副作用や outcome 同値性は証明できない。`--tx` allowlist だけで済むという後半は否定。 |
| P5: 本 wave は実装しない | 支持 | 確定裁定 (d) は直列維持を要求しており、この wave で受理意味論を変更してはならない。[裁定原本:71–107](/work/1/SFC/tanab/dev-wave-jobs/question-lease-serialization/ruling-package.md:71) |

## I1 — 「分割後も受入の受理集合を保つ」の定義

固定入力 `X` を次で定義する。

- tested main SHA、tested wave tip SHA、HEAD
- tracked／untracked／index／recursive submodule の状態 fingerprint
- default target、pytest config、plugin 集合、Python・pytest・xdist version
- selection に影響する環境変数と、許容された実行環境クラス

既定 target を canonical 形で一回走らせる判定を `A0(X)`、partition `p` と host 配置 `h` を使う合成判定を `AM(X,p,h)` とする。I1 は次である。

```text
すべての許容 X, p, h について:
    AM(X, p, h) = A0(X)

かつ、partition や host の違いだけで同じ X の受理／棄却が変わらない。
```

ここで `A0` は pytest の rc だけではなく、受入 preflight、collection、実行結果、artifact 完全性を含む。

### 必要な契約

1. **同一 snapshot**

   全 shard／worker が同じ `X` を参照する。既存の tree・submodule fingerprint は [run_tests.py:1537–1609](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:1537) にあるが、manifest では SHA、config、interpreter、plugin も束縛する。

2. **canonical collection の順序付き多重集合一致**

   canonical collection を

   ```text
   C = [(ordinal, nodeid, source_file, post_hook_xdist_groups), ...]
   ```

   とし、各 shard は `C` の部分列を持つ。全 shard を canonical ordinal で併合した列が、重複数も含めて `C` と完全一致しなければならない。collection error、collection skip、marker 異常も manifest の結果に含める。

   `conftest.py` は collection 中に `real-repo` marker を自動付与し [conftest.py:238–248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/conftest.py:238)、collection finish で順序を変更する [conftest.py:270–282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/conftest.py:270)。したがって、pre-hook の file 集合だけでは証明にならない。

   現行 task-run digest は nodeid を `set` に入れ、sort して hash するため、順序と重複を失う [pytest_stats.py:24–52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/task_runs/pytest_stats.py:24)。また `_suite_identity` は wrapper 引数だけを見る [run_tests.py:783–800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:783)。いずれも M1 の証明には使えない。

3. **collection／session 意味論の保存**

   collection の被覆だけでなく、module import、`sys.path`、`sys.modules`、環境変数、session fixture、plugin hook の結果が partition に依存しないことが必要。F-9 はこの条件への反例である。

4. **group closure**

   同じ post-hook `xdist_group` を持つ item はすべて同じ scheduler invocation に置く。D63 は排他を単一 runner invocation 内に限定している [decisions.md:2406–2418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/docs/decisions.md:2406)。P2 の13 file固定ではなく、実 collection marker から閉包を導出する。

5. **結果・artifact の完全性**

   期待 shard、PBS request、hostname、worker ID、rc、JUnit、stdout/stderr、digest が一対一に対応すること。欠落、重複、改竄、未終端はすべて受入拒否とする。

6. **rc は型付きで集約**

   規範結果は shard ごとの rc ベクトルと失敗種別であり、数値の最大値ではない。

   - 全 global gate が pass、全 receipt が存在し、全 shard rc が 0 のときだけ `accepted`
   - 594/632/705 の拒否は既存 rc 13/15/14を保存
   - receipt 欠落、timeout、signal、bootstrap failure、pytest rc 2–5 は `incomplete/infra` として外側 rc 16
   - 完全な実行で一つ以上の pytest failure/error がある場合は `test-rejected`、外側 rc 1
   - 元の全 child rc は結果 JSON に残す

### 受入専用 gate の正しい scope

親 I2 の「4箇所が全体として1回以上発火」は、canonical 実行自身とも一致しない。submodule が既に初期化済みなら705へ到達せず [run_tests.py:669–705](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:669)、canonical 受入では1677の警告は出ないからである。

| gate | 分割後の保証 | scope |
|---|---|---|
| 594 未 stage 削除 | `X` に対する fail-closed な検査証明を作り、fan-out 前に通す [run_tests.py:591–626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:591) | **合成走行で exactly once** |
| 632 RuleOps | 同じ `X` に対して一回だけ実行し、timeout／実行不能も rc 15 にする [run_tests.py:629–666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:629) | **合成走行で exactly once** |
| 705 submodule | 各 distinct execution root で initialized predicate を満たす。共有 root なら一回初期化後に全 worker が確認し、rsync copy なら copy ごとに必要 [run_tests.py:698–763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:698) | **root ごと。shard ごとではない** |
| 1677 非受入警告 | shard を単独の受入結果と誤認させない。別 invocation 型なら各 shard に警告または構造化 `non-standalone` marker、単一 invocation の M2/M5 なら警告ゼロ [run_tests.py:1667–1682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:1667) | **各 targeted invocation の分類保証** |

## 機構案

### 比較

| 案 | I1 | I2 | I3 | I4 | 受理集合への影響 | 規模 |
|---|---:|---:|---:|---:|---|---|
| M1 manifest shard coordinator | 現状×、hermetic 化後△ | ○ | ○ | △ | 現状は canonical-green を shard-red にする | 大 |
| M2 `--tx`／`--rsyncdir` allowlist | 提案どおりでは× | △ | △ | × | 実際には remote 実行せず、rsync 版は repo 意味論も変える | allowlistだけなら小、成立形は大 |
| M3 `-b k`＋単一 pytest process | ○ | ○ | ○ | ○ | leader だけなら不変だが高速化ゼロ | 中 |
| M4 非分割で固定部分を短縮 | ○ | ○ | ○ | ○ | 同値な最適化なら影響なし | 中 |
| M5 allocation-aware 単一 xdist controller | 条件付き○ | ○ | ○ | ○ | 単一 collection／scheduler を維持できる | 特大 |

### M1 — manifest の和で acceptance を証明

coordinator が canonical collection、snapshot、group closure、shard割付け、artifact期待集合を manifest に固定し、全 shard の完了後に証明を再検査する案である。

変更面は少なくとも次になる。

- runner-only option の消費面 [run_tests.py:149–156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:149)
- argv形状判定 [run_tests.py:388–426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:388)、[run_tests.py:505–563](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:505)
- preflight orchestration [run_tests.py:1784–1792](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:1784)
- collection marker／順序の出力 [conftest.py:238–282](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/conftest.py:238)
- task-run identity／digest
- N request の dispatch、receipt、JUnit 併合

ただし manifest の集合証明だけでは F-9 を直せない。canonical collect を行った coordinator の `sys.path` 副作用は、別プロセスの shard へ移らない。したがって現状の M1 は I1 を満たさず、suite hermeticity 修正後の候補に限る。

### M2 — xdist 多ホストを allowlist する

提案どおりの「allowlist に2項目追加」では成立しない。

- runner は明示 `-n` が無ければ必ず `-n <default>` を足す [run_tests.py:367–385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/run_tests.py:367)。
- 現環境の xdist は `numprocesses` が非ゼロなら、指定済み `--tx` を同数の local `popen` で上書きする [xdist/plugin.py:318–328](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/plugin.py:318)。
- `--rsyncdir` は xdist 4.0 で削除予定 [xdist/plugin.py:291–295](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/plugin.py:291)。さらに既定 ignore は `.*` なので `.git` を送らず [xdist/workermanage.py:44–46](/home/SFC/tanab/.local/lib/python3.10/site-packages/xdist/workermanage.py:44)、git history・submodule を読む suite の実行環境を変える。
- 現 dispatcher は一ノードしか確保しない。

したがって allowlist だけなら remote worker は一台も増えない。`-n` 組立て、PBS allocation、transport、shared checkout、per-root submodule、worker→host receipt まで変更すると、それは実質 M5 である。

### M3 — PBS 複数ノード＋単一 pytest process

Pegasus/NQSV では `select=k` ではなく `-b k` が正しい [pegasus-runbook.md:115–122](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/docs/pegasus-runbook.md:115)。

現 dispatcher は job script、qsub、receipt のすべてが一ノード固定である。

- `#PBS -b 1` [dispatch_compute.py:450–455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/pegasus/dispatch_compute.py:450)
- qsub `-b 1` [dispatch_compute.py:1472–1486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/pegasus/dispatch_compute.py:1472)
- receipt `"nodes": 1` [dispatch_compute.py:1356–1367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/pegasus/dispatch_compute.py:1356)
- default walltime 40分 [dispatch_compute.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/pegasus/dispatch_compute.py:28)

`-b k` の既定 `distrib` は同じ script を各ノードで起動する [decisions.md:6892–6896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/docs/decisions.md:6892)。単純に値だけ変えると、複数 process が同じ `result.json` と marker を書く。一方、一台だけを leader にして単一 pytest process を動かせば、残り `k-1` 台の CPU は使われず、ポイントは概ね `k` 倍になる。よって意味論上は安全にできても、短縮機構にはならない。

### M4 — 分割せず占有時間の固定部分を削る

受入全走546秒、lease占有900–1500秒なら、非テスト部分は354–954秒である。テスト部分だけ理想的に4分割しても総占有は490.5–1090.5秒で、短縮率は約27–46%に留まる。

M4では、外部 timestamp で次を分解してから最大成分を別 wave で最適化する。

- lease取得後の main 取込み
- dispatch queue／bootstrap
- pytest
- result回収
- provenance
- land／fold／release
- holder解放から次holder取得までの空隙

注意点は二つある。

- poll は lease取得前だけであり [dev_wave_wait.py:607–628](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/dev_wave_wait.py:607)、holder の占有時間ではない。handoff空隙として別集計する。
- main merge は取得後に行う正しさの機構 [dev_wave_wait.py:811–865](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/dev_wave_wait.py:811)。取得前へ移してはならない。
- provenance は既に land lock の外で実行され、再取得後に fingerprint を再照合している [dev_wave_land.py:2131–2191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/dev_wave_land.py:2131)。単なる「lock外へ移す」は既実装である。cache化するなら tip、checker bytes、履歴範囲、fingerprint を証明する別設計が必要。
- 受入全走の隣で provenance／dispatch 等の writer を走らせない [pegasus-runbook.md:942–953](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/docs/pegasus-runbook.md:942)。

### M5 — allocation-aware 単一 xdist controller

将来 cross-node を行うなら最も妥当な案である。

- PBSで `-b k` を一回だけ確保
- allocation 内で leader を一つ選び、pytest controller も一つだけ起動
- deprecated rsync を使わず、全 worker が同じ Lustre checkoutを参照
- scheduler が割り当てた host だけへ sanctioned transport で worker を起動
- 最初は総worker数48、k=4なら各node 12 worker。いきなり192 workerへ増やさない
- collection、session hooks、JUnit、`loadgroup` scheduler は一つ
- `real-repo` group は全hostを通じて一workerへ置く
- gateway ID、hostname、interpreter、worker rc を receipt に記録

xdist worker は各自がスイート全体を collect するため、F-9 の provider module も各workerで読み込まれ、M1より意味論を保ちやすい。ただし transport可否、共有checkoutの整合、workerごとのsubmodule確認、receipt拡張を実測するまで I1 を宣言できない。

## 評価 protocol

現行 `k4count` は既に意味論反例を出したため、速度推定の正当な acceptance arm ではない。「壊れた場合にどれほど速いか」は採否根拠にしない。

### 共通条件

- 同一 commit／tree fingerprint／submodule／interpreter／pytest・xdist version
- acceptance 隣接 writer、provenance、別 acceptance を置かない
- stdout、stderr、JUnit、manifest、receipt は request ごとの repo外 namespace
- arm順は時間 block 内でランダム化し、各blockに canonical controlを入れる
- 現在の15本の履歴値は記述統計だけに使い、同一tipのpaired controlにはしない
- semantic mismatch が一件でも出た案は、性能反復へ進めない

### arm

| arm | 目的 |
|---|---|
| `C48` | 既定target・一invocation・一node・総48worker。I1のcanonical基準 |
| `base-files48` | 親実施済みの全163 file列挙・一job。canonical shapeとの差を分離 |
| `K4count-48` | 親実施済み。4 shard×各48worker＝総192worker |
| `K4seq-48` | 同一nodeの一job内で4 shardを順番に実行。partition意味論だけを検査 |
| `K4local-12` | 一node上で4 invocationを同時実行、各12worker。総worker数48でmulti-invocation干渉を測る |
| `K4node-12` | 4node×各12worker。総worker数を48に固定してnode分散効果を測る |
| `K4-LPT-12` | 独立したtraining runのfile時間からLPT割付け。group bundleは不可分 |
| `X4-12` | M5外部prototype。4node・単一controller・総48worker |
| `M4-trace` | canonical commandを変えず、lease各区間だけをtimestamp化 |

partition は少なくとも固定seed 3種を用意し、F-9 provider と consumer が同居する形／分離する形を含める。LPT の学習値と評価値を同じ走行から取らない。

semantic screening通過後の性能比較は、各contrastを同一tipで最低5 paired block。ノード差については4 shard×4 nodeのLatin squareを最低1巡、可能なら2巡する。

### 測定量・推定量・反証条件

| 問い | 測定量 | 推定量 | 反証条件 |
|---|---|---|---|
| 分割の決定性 | worker別の順序付きcollection、marker、collection error、`(ordinal,nodeid,when,outcome)` | collection差分数、outcome不一致率、partition間不一致率 | 欠落・余分・重複・順序違反、またはcanonical-green/shard-redが一件でも出る。F-9で現状は既に反証済み |
| rc集約 | gate結果、期待shard集合、各child rc、signal、timeout、receipt、JUnit | false-accept数、false-reject数、artifact完全率 | 非0／欠落を含むのに合成0、全0なのに理由なく非0、元rcベクトルを復元不能 |
| ポイント | PBS accountingの実Elapseとallocated nodes、queue wait、lease時間 | `P=Σ(nodes_i×Elapse_i)`、speedup `C48_wall/arm_wall`、point ratio `P_arm/P_C48` | 「ポイント不変」を主張する場合、事前登録した±10%同値区間に比率CI全体が入らない |
| xdist干渉 | collection/startup、worker crash、CPU/I/O、総worker数、invocation数、host数、group配置 | 同worker数での1対4 invocation差、1対4 node差、critical path | 同worker数でmulti-hostが速くない、failure率上昇、collection不一致、同一groupが複数hostへ割れる |
| fail帰属 | manifest ID、shard ID、request ID、PBS ID、hostname、gw ID、rc、JUnit/log digest | attribution完全率、ambiguity数 | orphan failure、二重帰属、失敗shard不明、欠落receiptを成功扱い |
| M4固定費 | acquire、merge完了、submit、PBS start/end、result回収、provenance、land、release | 各区間中央値・裾、除去可能比率 | poll待ちをholder占有に混ぜる、またはgateを省いた値で短縮を主張する |

rc評価用にはrepo外のsynthetic mini-suite／偽receiptを使い、少なくとも `all 0`、rc 1、pytest rc 2–5、gate rc 13/14/15、infra 16、signal、timeout、receipt欠落、異種二重失敗を個別に注入する。

## F-9 の帰属と潜在範囲

原因は `test_reflux_ir.py` のcollection時副作用である。

- 同fileは `_HERE`、repo root、`orchestrator/` を `sys.path` に挿入する [test_reflux_ir.py:15–17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_reflux_ir.py:15)、[test_reflux_ir.py:120–128](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_reflux_ir.py:120)。
- full collectionではこのfileが先にimportされるため、後続fileから top-level `tests` と `codex_roles` が見える。
- `test_s8b_approved.py` 自身はrepo rootしか追加せず、collection時に `tests.skiputil` をimportする [test_s8b_approved.py:20–31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_s8b_approved.py:20)。
- `test_profiler_directive.py` もrepo rootしか追加せず [test_profiler_directive.py:20–24](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_profiler_directive.py:20)、test実行時にtop-level `codex_roles` をimportする [test_profiler_directive.py:335–343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_profiler_directive.py:335)。full runでは全module collection後にtestが始まるので成功する。
- k4ではproviderがshard 0 [shard-k4count-0.txt:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/shard-k4count-0.txt:24)、二つのconsumerがshard 3 [shard-k4count-3.txt:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/shard-k4count-3.txt:18)、[shard-k4count-3.txt:22](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t813-shard-eval/shard-k4count-3.txt:22) に分かれたため失敗した。

同型の静的下限は、5 consumer file・6 import context・9 import文である。確認済み2件に加え、次が潜在例である。

- `codex_roles` の関数内import [test_p3_s4_loop.py:1139–1145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_p3_s4_loop.py:1139)
- `tests.*` の関数内import二箇所 [test_real_repo_serialization.py:823–827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_real_repo_serialization.py:823)、[test_real_repo_serialization.py:900–910](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_real_repo_serialization.py:900)
- `tests.*` のmodule-level import [test_s8b_protocol_builder.py:30–38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_s8b_protocol_builder.py:30)

これらは今回providerと同じshard 0に偶然置かれ、赤が隠れている。

総数の見積りは、単純grepではなく次で行う。

1. module-levelの `sys.path`、`sys.modules`、cwd、環境変数変更をproducerとしてAST抽出
2. repo rootだけでは解決しないtop-level importをconsumerとして抽出
3. session fixture、pytest hook、module global cache、`campaign.*`／`orchestrator.campaign.*` の二重identityも抽出
4. file単独collection、最小provider-consumer pair、file順序 permutationを実行
5. 複数partition seedでprovider除去時のcollection／outcome差を測る

現在の「5 file・9文」は下限であり、suite hermeticityの完了値ではない。

## [T-810] への条件付き依存

[T-810] は現在、同一CC binary／workloadをN nodeで測る新規protocolとして記録されている [worklog:624–628](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/docs/archive/worklog-phase3-0811-418.md:624)。これは設計原則を再利用できるが、CC結果をpytest shardの補正値にはできない。runbook自身もpytest wallはCC throughputの代理ではないとしている [pegasus-runbook.md:958–982](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/docs/pegasus-runbook.md:958)。

静的検索で、受入suiteには少なくとも次の実wall依存面がある。

| test | wall gate |
|---|---|
| RuleOps実checkout | 実 `monotonic` で `<60s` かつ `<45s` [test_ruleops.py:3444–3451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_ruleops.py:3444) |
| codex worker launcher | subprocessへ既定 `--max-wall-clock-s 3` [test_codex_worker_launch.py:949–960](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_codex_worker_launch.py:949)、production判定 [codex_worker_launch.py:1402–1419](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/tools/codex_worker_launch.py:1402) |
| s8c preregistration | test git timeout 180s [test_s8c_preregistration_invariant.py:28–65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_s8c_preregistration_invariant.py:28)、production動的15–300s [s8c_preregistration.py:925–958](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/campaign/s8c_preregistration.py:925) |
| dev-waves protocol | slow-byte dripに対して `<0.15s` [test_dev_waves_protocol.py:256–312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_dev_waves_protocol.py:256) |
| dev-waves worker | stop／timeoutに `<5s`、`<2s` [test_dev_waves_worker.py:188–198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_dev_waves_worker.py:188)、[test_dev_waves_worker.py:378–385](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_dev_waves_worker.py:378) |
| dev-waves checker | active check timeout `<1s` [test_dev_waves_checker.py:304–317](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_dev_waves_checker.py:304) |
| login headroom | lock deadline `<0.5s` [test_login_headroom.py:982–1001](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_login_headroom.py:982) |
| dev-wave land | lock-busy `<2s` [test_dev_wave_land.py:1223–1245](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/test_dev_wave_land.py:1223) |

特にRuleOps nodeは `real-repo` groupに含まれる [conftest.py:182–184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t813-shard-eval/orchestrator/tests/conftest.py:182)。M1ではgroup bundleとnodeが一対一に対応し、M5ではgroup workerのhostがcritical pathとwall gateを同時に支配する。

したがって性能評価は、4 shard×4 nodeを同時実行するLatin squareで各shardを各nodeへ一度ずつ回し、例えば次を推定する。

```text
log(wall) = arm + shard + node + time_block + error
```

一処置一nodeの配置やhostname記録だけではnode差とshard差を分離できない。T-810がCC専用のままなら、T-813側に固定pytest workloadを用いた同型protocolが別途必要である。

なお、I1の否定自体はT-810を待たない。F-9だけで現状のM1は反証済みである。T-810への依存は、M5の速度・ポイント・wall-flake率を採否判断する段階に限る。

## 総括

- 推奨機構: **M4**。直列受入と受理集合を保ったまま実占有の固定部分を削れ、cross-node が必要になった場合だけ単一collectionを維持する **M5** を次候補とする。
- 実装判断: **現時点では実装してよくない**。suite hermeticity、型付き結果併合、完全なfail帰属、sanctioned multi-node transport、pytest固有のnode-block評価を満たし、ユーザー裁定を得ることが前提。
- 親briefの否定点: **P3(a)(c)(d) と P4後半を否定**し、P1/P2は必要条件に限定、P3(e)とP5は支持する。