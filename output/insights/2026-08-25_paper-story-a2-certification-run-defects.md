# paper-story A-2 — 実走が暴いた certification 実装の 3 欠陥

- 日付: 2026-08-25
- wave: `dev-wave-t1647-a2-cert-run`
- 統合 tip: `9405a080a8158dafde60042f29f27cf846d4c9db`
- 対象実装: `orchestrator/campaign/paper_story_a2_certification.py`、
  `tools/pegasus/paper_story_a2_certification.sh` (worklog entry 910 で land)
- **4-cell certification の実走は本文書の時点では完了していない。** 本文書は「実走を試みた結果
  land 済み実装が終端不能と判明し、3 欠陥を直した」までの記録である。

## この wave が始めたこと

worklog entry 910 が land した A-2 driver で 4-cell certification を実走する依頼だった。
実装差分ゼロで終わる想定で始めたが、1 回目の実走が 6 秒で失敗し、
**land 済み実装のままでは certification が原理的に終端しない**ことが判明した。
以後は 3 欠陥の修理 wave として進めた。

## 実走 1 回目 (attempt `t1647-20260825`、request `945411.nqsv`、bnode007)

`driver_rc=1`、経過 6 秒。`scheduler/job.stderr` の逐語は次のとおり。

```
File ".../orchestrator/campaign/source_digest.py", line 113, in <module>
    @dataclass(frozen=True, slots=True)
TypeError: dataclass() got an unexpected keyword argument 'slots'
```

interpreter は
`/system/apps/ubuntu/20.04-202210/oneapi/2022.3.1/intelpython/latest/bin/python3` (3.9.13)。

この失敗は job body の後半で起きたため、**それより前の関門はすべて計算ノードで成功していた**。
負の証拠として記録する: compute-only host 判定、必須 env 6 本、attempt root の新鮮性、
`qstat -f` による予約観測と `(Per-Req) Elapse Time Limit = Max: NNNS` の parse、
`reservation.json` の書き出し、worktree での `git rev-parse HEAD` と clean 検査、
submodule の pin 検査、`/scr/$USER` 配下の scratch 作成、依存 prefix の staging。

## 欠陥 1 — job body が interpreter を固定していなかった

計算ノードの既定 `python3` は oneAPI の Python 3.9.13 で、`dataclass(slots=True)` (3.10 以降)
を読めない。job body は素の `python3` で driver を起動していた。

**これは既登録の再発である。** `docs/failures.md` の F46 (login node の interpreter 挙動を
計算ノードへ一般化して floor 実機初走が死んだ) と F84 (手書き投入器が `_job_script` の
環境正規化を写さず、逐語で同じ `TypeError` が出た) が同型で、F84 の恒久対応は
「`tools/pegasus/dispatch_compute.py` の interpreter 選択・version/module probe・PATH 先頭化を
逐語で写すか `_job_script` 自体を再利用する」と明記していた。A-2 の job body はこれを写して
いなかった。**独立 3 例目**である。

修正は canonical な候補列 (`python3.10` / `/usr/bin/python3.10` / `/bin/python3.10`)、
版数 3.10 以上**かつ A-2 module の実 import** による候補判定、
`export PATH="$(dirname "$selected"):$PATH"`、全 python 起動 (driver 4 本 + inline heredoc 2 本)
の絶対 path 統一、解決不能時の fail-closed。

PATH 先頭化が必須である根拠は実測で取った。probe `945524.nqsv` で、PATH 先頭化の前後で
`cmake` が oneAPI 版から `/bin/cmake` 3.22.1 へ切り替わる。CCBench の configure は
`Found Python3: /bin/python3.10` を記録しており、GoogleTest の `find_package(Python3)` が
PATH から interpreter を解決することも裏付いた。**driver を絶対 path で呼ぶだけでは足りない。**
別 probe `945707.nqsv` で、PATH 先頭化後も `qstat` は `/opt/nec/nqsv/bin/qstat` のまま
解決されることを確認した (先頭化が scheduler 照会を壊さない)。

## 欠陥 2 — 投入時の可視性述語が実 scheduler で満たせなかった

driver は `Request State = QUE|RUN` の行を要求していたが、実 NQSV の `qstat -f` は
その行を一度も出さない。本 wave が実測した状態行は次のとおり。

| 観測時点 | 行 |
|---|---|
| 投入直後 (945411) | `Current State           = Staging` / `Previous State          = Queued` |
| 実行中 (945413) | `Current State           = Running` / `Previous State          = Pre-running` |

終端側 (`_NQSV_DISAPPEARED_RE`、`_TERMINAL_STATE_RE`) は実形式を既に受理しており、
**投入側だけが非対称**だった。

受理集合を新しく発明する必要は無かった。`tools/pegasus/dispatch_compute.py` に
canonical な NQSV 状態語彙が既にあり、`Current State` の `staging` を `QUE` へ、
`running` を `RUN` へ正規化する。これを stdlib-only の共有 module
`orchestrator/scheduler_nqsv.py` へ移し、campaign と dispatcher の双方から使う形にした。
**語彙の定義は 1 箇所に保ち、receipt の `state` と schema version
`paper-story-a2-submission-receipt/v3` は据え置いた。**

移設にあたり `_target_bound_qstat_state` の 4 条件をすべて維持した — request ID が
ちょうど 1 つ、state field が各々高々 1 つ、併存時に正規化後が一致、対象 ID より前に
認識可能な state が無い。敵対レビューはこの 4 条件を落とすと
「別 request の block を貼った stdout」と「矛盾する複数 state」が通ることを、
具体的な突破文字列付きで示した。

同レビューはさらに 2 件の穴を実証した。(1) `Ended Request Time` の検査が
`findall` の 0 件で `any()` が False になり素通りする。(2) 可視 block と request 消滅署名を
連結した自己矛盾 stdout が通る。どちらも別々の署名で拒否するよう直した。

## 欠陥 3 — `PBS_JOBID` のコロンが build を殺す

NQSV の `PBS_JOBID` は `0:945411.nqsv` で必ずコロンを含む。job body は
`scratch=$scratch_base/${PBS_JOBID}` として依存 prefix をその下に作っていた。

計算ノードで 4 arm の対照実験 (probe `945528.nqsv`、各 arm は fresh な FetchContent base を持ち
warm cache を共有しない) を行い、因果を確定した。

| arm | コロンを含む path | configure | build | 失敗の逐語 |
|---|---|---|---|---|
| A | 依存 prefix (`CMAKE_PREFIX_PATH`) | rc=0 | **rc=2** | `cc/silo/CMakeFiles/ycsb_silo.exe.dir/build.make:130: *** target pattern contains no '%'.  Stop.` |
| B | FetchContent base | rc=0 | **rc=2** | `CMakeFiles/Makefile2:66: *** target pattern contains no '%'.  Stop.` |
| C | build dir | rc=0 | rc=0 | — |
| D | 全部 | rc=0 | **rc=2** | `CMakeFiles/Makefile2:67: *** target pattern contains no '%'.  Stop.` |

make は依存 path のコロンを rule 区切りと解釈する。`find_package` が返す
`libgflags.a` / `libglog.a` の絶対 path と FetchContent の source path が link 依存として
`build.make` へ焼き込まれるため、そこにコロンがあると build が必ず落ちる。
**build dir 自身のコロンは無害である** (arm C)。

放置すれば 4 cell すべてが `build-error` になり、certification 結果は毎回 indeterminate に
なっていた。修正は path 生成だけをコロン無しにし、証拠として使う `PBS_JOBID` の逐語利用
(`IZANAGI_RESERVATION_JOB_ID`、`IZANAGI_RESERVATION_NONCE`、`compute-result.json` の
`pbs_jobid`、`qstat_jobid=${PBS_JOBID#0:}`) は 1 文字も変えない。

## probe が反証した懸念

敵対レンズ B は「次の実走で落ちる箇所」を 6 件挙げた。cold build probe 2 本で 5 件を反証した。

| 懸念 | 実測 |
|---|---|
| FetchContent が GitHub へ出られない | 計算ノードから `git ls-remote https://github.com/microsoft/mimalloc.git v2.3.2` が rc=0 で SHA を返した |
| env contract の attestation が落ちる | `site = PEGASUS_COMPUTE`、`lookup("pegasus")` = clocks_per_us 2100 / numactl ()、`authorize` OK、policy 読込 OK |
| `TMPDIR` 未設定で trace が溢れる | `tempfile.gettempdir()` = `/tmp`、**空き 128.4 GB**。`/scr` は 5.4T |
| `nm` / `pgrep` / `realpath` 等が不在 | 14 command すべて `/bin` に実在 |
| 統合依存 prefix が compute で link しない | 完全 build が **19 秒**で rc=0、`ycsb_silo.exe` 701,728 bytes を生成 |

依存 prefix は gflags と glog の install を 1 つへ統合した dir
(`/work/1/SFC/tanab/izanagi-a2-deps`) を使う。login node の configure probe で
`FIND_PACKAGE_MESSAGE_DETAILS_gflags = .../izanagi-a2-deps/lib/libgflags.a` を確認し、
compute での完全 build でも同じ prefix から解決された。

## 変異台帳 (逐語)

- harness: `tools/mutation_harness.py`、`--runner-mode dispatch`、`--detached`
- runner argv: `python3 tools/run_tests.py --force-dispatch -rf` +
  `orchestrator/tests/test_paper_story_a2_certification.py`
  `orchestrator/tests/test_paper_story_a2_job_contract.py`
  `orchestrator/tests/test_pegasus_dispatch_compute.py`
- spec SHA-256: `5d8d3d787cdbe9a37e223d6f1b96c4796e75041780273a4268d9c87430aceaf7`
- repo head: `1b703335eca7747a44bb7ff0f8c6918de049bd8a`
- baseline: `PASSED` (319 passed、全走で一度も赤なし)
- 集計: `KILLED 16 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0 / PARSE_ERROR 0`

| ID | 単一変異 | 判定 | 期待 node 数 |
|---|---|---|---:|
| `M1` | request ID が「ちょうど 1 つ」の条件を「1 つ以上」へ緩める | KILLED | 1 |
| `M2` | state field の重複検査を無効化する | KILLED | 1 |
| `M3` | state field 併存時の一致検査を無効化する | KILLED | 4 |
| `M4` | 対象 ID より前の state の拒否を無効化する | KILLED | 2 |
| `M5` | 投入時の受理集合へ `HLD` を足す | KILLED | 3 |
| `M6` | `Ended Request Time` の値が `(none)` である検査を無効化する | KILLED | 1 |
| `M6b` | `Ended Request Time` の不在検査を無効化する | KILLED | 1 |
| `M6c` | request 消滅署名の排他検査を無効化する | KILLED | 1 |
| `M6d` | receipt の state と canonical state の一致検査を無効化する | KILLED | 1 |
| `M7` | job body の PATH 先頭化を削る | KILLED | 4 |
| `M8` | interpreter 解決失敗時に bare `python3` へ落とす | KILLED | 1 |
| `M9` | resolver 呼出しを最初の Python 使用より後ろへ移す | KILLED | 5 |
| `M10` | 候補判定から A-2 module の import 検査を落とす | KILLED | 5 |
| `M12` | 共有 parser の語彙表から `staging` を落とす | KILLED | 36 |
| `M13` | scratch path の sanitize を外し `PBS_JOBID` をそのまま入れる | KILLED | 3 |
| `M14` | `compute-result.json` の `pbs_jobid` を sanitize 済み値へ差し替える | KILLED | 1 |

### erratum — 非帰属フレークによる MISMATCH

本走 16 件のうち M3 / M4 / M5 / M14 が MISMATCH になった。4 件とも意図した node は観測集合に
含まれており、差分は**同一の余分 node 1 件**
(`test_pegasus_dispatch_compute.py::test_control_lock_allows_peer_after_pending_hold_is_durably_released`)
だけだった。同 node は `threading.Event.wait(5)` を使う並行性テストで、48 worker の負荷下で
間欠的に timeout する。

帰属を否定した根拠は 3 点。(1) 単独再走が緑 (1 passed)。(2) M14 の変異対象は job body の
`printf` 引数であり、dispatcher の control lock に影響しえない。(3) 全 33 変異走行のうち
5 走でしか現れず決定的でない。M3 / M4 / M5 の再走と M14 の単独再走はいずれも
意図した node だけで KILLED になり、集計は 16/16 で閉じた。初回の MISMATCH はこの
erratum として残す。

### 期待 node 数が大きい 2 件について

`M12` (語彙表から `staging` を落とす) は 36 node に膨らむ。実 qstat fixture が
`Current State = Staging` を持つため、submission receipt bundle を作る全テストが連鎖的に落ちる。
`M9` と `M10` が 5 node なのは、job body の逐語 fragment 集合が複数の契約テストから
参照されているためである。期待 node は推測でなく probe の観測集合をそのまま完全集合として pin した。

## 親自身の失敗

変異 probe の実行中に main の merge を commit し、HEAD を動かした。harness は
`run 中に HEAD が変化` で fail-closed 中断し、orphan hold が残った。
hold の recovery 手順どおり request `945769` の終端 (`child_rc=0`、scheduler 上で消滅) と
木の clean / HEAD を確認したが、hold file は harness 自身が既に撤去していた。
**変異走行中の禁止事項は「tree へ書かない」だけでなく「HEAD を動かさない (commit しない)」
まで含む。**

## 成果物が主張しないこと

- **4-cell certification の実測値をまだ含まない。** 本 wave は実装の欠陥を閉じただけで、
  certified 選択・性能値・correctness 判定は 1 つも生成していない。
- **rr5 (write-heavy) の実コストは未測定である。** 6 時間の walltime に 4 cell が収まるかは
  判定不能のままである。同一 workload の full-scale trace 実測値 (539MB / 16.9M 行、
  verifier 141 秒 / RSS 7.7GB) は rr50 の値であり、rr5 へ転移しない。
  cold build は 19 秒と実測できたので、walltime のほぼ全部を correctness と performance に
  使える。資源・timeout・trace 完全性のいずれかが欠けた cell は indeterminate として記録する。
- **job body の実走は修正後もまだ検証されていない。** 修正は静的検査と変異でのみ裏取りした。
