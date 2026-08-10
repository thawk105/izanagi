判定は **NO-GO**。静的レビューのみで、pytest・計算ノード実走はしていない。

## blocker

### 1. 任意の非 0 終了・timeout を「封じ込め成功」にしている

[`t316_sandbox_backend_probe.py:505`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:505)–[`523`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:523) は、inside の `rc != 0` だけで `inside_blocked=True` にする。payload が実行されたか、期待した拒否 errno か、timeout か、bwrap 自身の setup/exec failure かを区別しない。その値を [`_paired_verdict():70`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:70)–[`83`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:83) がそのまま `go` にする。

具体的観測列:

1. outside network control は `rc=0`。
2. inside でも network namespace は実際には遮断されていない。
3. しかし target の一時停止、inside 固有の TLS/import failure、bwrap の command-specific setup failure等で `rc!=0` または timeout。
4. `attempted=True`, `outside_success=True`, `inside_blocked=True`。
5. 当該カテゴリは `go`。他 stage も `go` なら overall も `go`。

DW-G05 成果物影響: 実際には到達可能な network/credential/write 経路が `*_CONTAINED` と receipt に記録され、意味 gate 実装が非封じ込め backend を受理する。

### 2. S4 は「子孫が死んだ」ではなく、固定時間内に marker が無いことしか見ていない

[`observe_s4():641`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:641)–[`679`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:679) は pidfile を作るのに一度も読み返さず、`time.sleep(1.5)` 後の marker 不在を `inside_blocked=True` とする。

具体的観測列:

1. inside 子孫が `setsid()` で escape し、実際には生存。
2. 親 process group は timeout し、`inside["timed_out"]=True`。
3. 子孫が scheduler delay 等で 1.5 秒以内に marker を書けない。
4. `inside_survived=False` と誤観測し `inside_blocked=True`。
5. [`verdict_s4():142`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:142) が `go`。

DW-G05 成果物影響: 子孫が allocation 内に残る backend を process-tree containment 済みとして受理し、後続の無限ループ variant が残存しうる。

### 3. S5 infinite-loop control は内外で同じ probe timeout を成功条件にしている

[`observe_s5():749`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:749)–[`757`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:757) は、outside も inside も `_run_command(..., timeout_s=1)` が timeout すれば、それぞれ `outside_success=True` と `inside_blocked=True` にする。

具体的観測列:

1. outside loop が 1 秒継続して probe に kill される。
2. containment が効いていない inside loop も同じく1秒継続し、同じ probe に kill される。
3. 両方の `timed_out=True`。
4. S5 infinite-loop は `go`。

これは candidate backend の差ではなく、probe 自身の timeout が必ず作る観測である。`bwrap + _run_command/_kill_tree` 全体を候補 backend とする契約も policy/receipt にない。

DW-G05 成果物影響: infinite-loop containment が無い backendにも `S5_INFINITE_LOOP_CONTAINED` を発行し、R3-2 の正負制御を満たしたことにしてしまう。

### 4. `PBS_JOBID` は scheduler に束縛されず、自己申告値を3回複写している

PBS 側は [`t316_sandbox_backend_probe.pbs:8`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:8)–[`18`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:18)、Python 側は [`run_probe():1004`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1004)–[`1007`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1007) で形式しか検査しない。`measurement_id`、`PBS_JOBID`、S1 の値は同じ環境変数の複写である。`PBS_NODEFILE`、execution host、queue、scheduler の `qstat` 証拠は無い。

具体的観測列:

1. login node または別 queue で、形式上有効な `PBS_JOBID` と必要な環境変数を設定して probe を直接起動。
2. login node でも既測どおり bwrap 等が動き、全 stage が `go`。
3. [`receipt:1061`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1061)–[`1082`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1082) が偽 ID を canonical measurement ID として保存。
4. verdict は hostname を検査しないため overall `go`。

DW-G05 成果物影響: R3-1 が要求する計算ノード測定参照を、login/別 allocation の結果で満たしたことにでき、F29 型の転用を再発させる。

## must-fix

### 5. S5 と実際の build profile が別条件

runtime は `/bin` を空にする一方、build は host `/bin` を bind する（[`SandboxProfile.argv():443`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:443)–[`449`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:449)）。S5 は既定の `build_profile=False` だけで実行するが、S6 の untrusted build は [`_build_step():780`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:780)–[`783`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:783) で `build=True`。

具体的観測列:

1. runtime S5 の `std::system` は `/bin/sh` 不在で失敗し、`go`。
2. build profile では `/bin/sh` が存在し、同じ `std::system` が実行可能。
3. S6 build も成功して overall `go`。
4. untrusted build path に対する `std::system` 発火制御は未測定のまま残る。

DW-G05 成果物影響: runtime 限定の結果を build/run 両方の backend 受理へ一般化し、R3-2 の受理集合を過大化する。

### 6. receipt は create-only だが、完成版の atomic publish ではない

[`_write_receipt_create_only():1106`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1106)–[`1116`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1116) は最終名 `receipt.json` を直接作って順次書く。temp→fsync→no-replace publish→directory fsync ではない。

具体的観測列:

1. job directory と `receipt.json` が作成される。
2. `json.dump` 中、quota・walltime・node failure で停止。
3. 空または部分 JSON が canonical path に残る。
4. 再実行は [`main():1129`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1129)–[`1138`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1138) の create-only check で拒否される。
5. 完成 marker/schema validator がないため、「測定 ID は存在するが測定不能」の状態を残す。

DW-G05 成果物影響: insight/proof chain が壊れた receipt path を決定的計測参照として記録しうる。

### 7. 単体テストは observer→judge wiring、S4/S6/S7、receipt を検査しない

[`test_t316_sandbox_probe.py:21`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/orchestrator/tests/test_t316_sandbox_probe.py:21)–[`94`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/orchestrator/tests/test_t316_sandbox_probe.py:94) は、実装の category 定数から「良い観測」を合成して純関数へ直接渡すだけである。P3 の「恒真 probe の検出」には不足する。

緑のまま壊せる具体的変異:

- `_paired_command()` の `inside_blocked` を常に `True` にする。テストは observer を呼ばない。
- `aggregate_verdicts()` の優先順を `no-go, go, blocked, inconclusive` にする。唯一の aggregate test は `no-go` を含むためなお通るが、実 receipt の blocked/inconclusive が go に漏れる。
- `S3_CATEGORIES` または `S5_CATEGORIES` からカテゴリを削る。parametrize も同じ定数を読むため、その検査自体が消える。
- `verdict_s4`、`verdict_s6`、`verdict_s7` を無条件 `go` にする。対象テストがない。
- receipt writer を overwrite 可・非 create-only に変える。対象テストがない。

DW-G05 成果物影響: 上記の偽 GO 変異が受入テストを通過し、将来の backend 受理集合を無検知で拡大する。

### 8. R3-1 の stock/variant 双方という前提を満たしていない

裁定済み R3-1 は [`package.md:96`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/output/insights/2026-08-09_t316-semantic-gate/package.md:96)–[`101`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/output/insights/2026-08-09_t316-semantic-gate/package.md:101) で stock/variant 双方の性能差を要求する。実装は stock の `external/ccbench` から `ycsb_silo.exe` を1本作り（[`observe_s6():853`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:853)–[`886`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:886)）、その1本だけを内外比較する。

具体的観測列:

1. stock binary の内外実行が成功。
2. S7 は `go`。
3. variant は build/run/overhead のいずれも未実行。
4. overall `go` が全軸の sandbox backend 判断へ使われる。

DW-G05 成果物影響: variant 固有の sandbox failure/overhead を測らず、stock の floor 再較正材料を variant の certified 選択へ転用する。

### 9. live proxy URI が tracked receipt に保存されうる

PBS は `HTTPS_PROXY` を必須にする（[`probe.pbs:8`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:8)–[`18`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.pbs:18)）。S3 は値を `extra_env` に渡し、profile は `--setenv KEY VALUE` として argv に埋める（[`probe.py:455`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:455)–[`463`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:463)）。`_run_command` は argv 全体を記録し、receipt に observations ごと保存する。

具体的観測列:

1. `HTTPS_PROXY=https://user:token@proxy/...`。
2. inside argv に URI 全文が入る。
3. S3 observation が receipt に入る。
4. brief が tracked と定める receipt に token が残る。

DW-G05 成果物影響: receipt の観測値が redacted endpoint ではなく live credential を含み、計測成果物を安全に追跡・commitできなくなる。

## nit

### 10. S7 の `go` は性能適格性ではなく「正の比が記録できた」だけ

[`verdict_s7():179`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:179)–[`182`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:182) は、ratio が正なら 1000 倍でも `go`。policy に threshold や `floor_recalibration_required` はない。

具体的観測列: 内外 rc=0、ratio=1000 → S7 `go` →全体も `go`。

DW-G05 成果物影響: `overall go` を「測定完了」ではなく「backend 採用可」と読む consumer が、floor 再較正必須の結果を無条件採用しうる。brief が threshold を事前定義していないため nit とした。

## refuted

- **空観測からの現行 go:** refuted。S1/S2/S6/S7 は `attempted is True` を要求し、S3/S5 の欠落カテゴリは `blocked` になる。
- **例外の silent skip:** refuted。stage observer の例外は [`run_probe():1023`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1023)–[`1058`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:1058) で `attempted=False` に変換され、`blocked` へ落ちる。ただし subprocess の非0/timeoutは blocker 1 のとおり別。
- **1件の no-go が overall go に消える:** refuted。現行 [`aggregate_verdicts():185`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:185)–[`198`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t316-sandbox-measure/tools/pegasus/probes/t316_sandbox_backend_probe.py:198) は全7 stage の存在を要求し、`no-go` を最優先する。
- **現行 producer/judge key の直接 typo:** refuted。確認した範囲では `attempted`、`outside_success`、`inside_blocked` 等の名称は一致する。問題は値の意味が弱いこと。
- **既存 receipt の overwrite:** refuted。job directory の `exist_ok=False` と file の `"x"` は既存物を上書きしない。ただし blockerではなく must-fix 6 の「部分ファイルを完成物として公開する」問題は残る。

## 総括

- blocker: **4件**
- must-fix: **5件**
- nit: **1件**
- refuted: **5件**
- 投入判定: **NO-GO**

特に blocker 1・2・3 は、封じ込めが効かない観測を現在のコードだけで `go` に変換できる。blocker 4 により、その結果が計算ノード由来であることも receipt 自身から証明できない。これらを修正し、observer→judge→receipt を通す変異テストを追加するまで計算ノードへ投入すべきではない。