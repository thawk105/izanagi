結論は **NO-GO**。静的検査のみで、pytest は実行していない。

## 受理集合

| 層 | 現行 | 計画後 | net |
|---|---|---|---|
| 現在の official | core で無条件拒否 | 同じ | 不変・空集合 |
| pilot / 将来の post-permit build | `gcc-13` / `g++-13` 必須 | system GCC と metadata gate | 拡大 |
| refreeze consumer | report なしの既存 schema | 新 report が extra key | 縮小・実質空集合 |

実 Pegasus compute で `gcc-13` / `g++-13` が無いことは過去の compute probe でも確認できるため、意図した system GCC 11 の正例は新たに通る。一方、A-2 が覆わず新たに通る入力は次。

- registered と異なる `module_list`
- CC/CMake の `--version` が先頭行だけ同じで後続行が異なる実体
- registered CXX path と同じ文字列だが、version・bytes・由来が異なる CXX
- version だけ一致する任意の CMake realpath
- 同一 realpath/version 表示だが bytes が異なる compiler
- attempt を省いた pilot
- caller が作った matching `ToolchainSnapshot` を「attempt 実測」として渡す経路

### [must-fix] 1. receipt に実在する authority を捨て、穴を二つだけと偽っている

プランは authority を「列挙した field だけ」とする一方、`ToolchainReceipt` に実在する `module_list` を落としている。[out-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:7) [schema_v2.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/calibrator/schema_v2.py:389) 登録値は `intelpython/2022.3.1` である。[calibration JSON](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:58)

さらに receipt producer は compiler/CMake の完全な version 出力を保存するが、計画は三者とも先頭行へ縮約する。[certify_calibration.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/tools/pegasus/certify_calibration.sh:577) [out-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:34) M-6 が必要とするのは argv0 の正規化であり、後続行の廃棄ではない。

それにもかかわらず成果物の `known_unbound_fields` は `cmake_realpath` と `cxx_version` だけである。[out-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:142)

**成果物影響:** 未登録の module 環境や version 後続行の異なる tool が床値を生成しても、manifest/result は `status="matched"` と記録し、certified floor の受理集合を拡大する。

### [must-fix] 2. P6 の「混用不可」は成立しない

親 brief は build argv の二つの path 一致で「同一 toolchain 由来」を固定できるとする。[brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/brief.md:110) しかし計画自身が末尾で「P6 は証明できない」と refute している。[out-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:869)

具体的な通過例は、CC が登録済み GCC 11、CXX が同じ `/usr/bin/x86_64-linux-gnu-g++-11` というパス文字列にある別 version・別 bytes の frontend である。現 gate は CXX について executable・非空 version を得るだけで、登録値との version 比較をしない。[buildcache.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/buildcache.py:199) CMake はその CXX path を実際の build に使う。[buildcache.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/buildcache.py:505)

計画の `mixed_compiler_pair[cc-only|cxx-only]` は片側のパス不一致しか攻撃せず、「両パス文字列は一致するが由来が違う」例を殺さない。[out-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:714)

**成果物影響:** mixed C/CXX で生成した binary が matching report を持つ floor binary として保存され、床値と後続 certified 選択を汚染する。

### [must-fix] 3. attempt 脚は実測 provenance ではなく caller 注入値である

計画は plain な `ToolchainSnapshot | None` を public `run_campaign` / core 引数へ追加し、`attempt is None` だけから `"provided"` を導出する。[out-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:525) [out-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:162) 任意の directory を CLI で指定できる一方、PBS job ID・submission nonce・execution receipt・raw file hash との束縛はない。[out-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:572)

さらに現行 official wrapper は非 default 引数をすべて injection として拒否する。[s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:2763)

- `attempt_toolchain` を injection 集合へ入れると、将来の正規 official は必須値を渡しただけで必ず赤。
- 入れないと、任意に構築した matching snapshot が正規 attempt として通る。
- プランは wrapper から core への `attempt_toolchain` forwarding も file:line 手順に明記していない。

job-result も leaf 名しか記録せず、driver が読んだ bytes の hash を残さない。[out-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:629)

**成果物影響:** copied/fabricated snapshot に対して manifest/result/試行台帳が `attempt_leg="provided"` を記録するか、逆に正規 official が恒真な赤となって floor 参照が空のままになる。

### [must-fix] 4. 新 report は authoritative refreeze consumer で恒真な赤になる

プランは manifest と result の top-level に `build_toolchain_binding` を追加するが、所有範囲に `s8b_ratified_freeze.py` がない。[out-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:505) [out-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:841)

authoritative consumer は manifest/result の key 集合を exact に固定している。[s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_ratified_freeze.py:189) [s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_ratified_freeze.py:199) extra key は必ず拒否される。[s8b_ratified_freeze.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_ratified_freeze.py:1439)

加えて、必須 field を増やすのに schema ID は v2 のまま据え置くため、旧 v2 と新 v2 が同名で非互換になる。[out-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:562)

**成果物影響:** guard 解禁後の正規 manifest/result が全件 `schema-keys` で拒否され、certified 選択・再凍結の受理集合が空になる。

### [must-fix] 5. A-3 の dependency-pin predicate は変異未帰属

現行 silo predicate は compiler 比較より前に `registered_dependency_pins != dependency_pins` を拒否する。[silo_ladder_rung1.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/silo_ladder_rung1.py:3574) 計画もこの行を残すが、新規 predicate matrix が担当するのは helper 内の compiler 四条件だけである。[out-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:337) [out-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:709)

既存 test は「現在の policy と calibration が一致する」という正例だけで、production predicate を削除する変異を殺さない。[test_silo_ladder_rung1_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/tests/test_silo_ladder_rung1_driver.py:989)

したがって、次の一行削除が未帰属である。

```python
if registered_dependency_pins != dependency_pins:
    raise DriverError(...)
```

**成果物影響:** 将来 policy dependency pins が calibration と異なる状態でも silo evidence が binding-valid となり、既存 consumer の受理集合が拡大する。

### [should] 6. M-1〜M-8 の一般化範囲が過大

- M-1〜M-4 はコード上の静的事実で、node 差はない。
- M-5 の親自身の login 測定だけでは compute を証明しない。ただし別の compute probe は bnode005 で `gcc-13` / `g++-13` 不在を記録しており、現時点の結論は補強される。[probe.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/output/env/pegasus/t293-perf-site/0_881960.nqsv/probe.json:74)
- M-6 の argv0 差は login 実測だけで、現在の compute 全体では未確認。
- M-7 の gen1/gen2 同値は現在の二ファイルに限る。将来 generation の同値性は導けない。
- M-8 は login の事実。過去の bnode005 は CMake 3.25.0 を記録しており、compute では逆の結論である。[probe.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/output/env/pegasus/t293-perf-site/0_881960.nqsv/probe.json:97)

したがって plan の「未確認のまま残した前提: なし」は refuted。[out-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:873)

**推測される成果物影響:** 現在の compute node pool に version drift があれば、正規 run が build 前に恒真な赤となり floor 参照が空のまま残る。

### [should] 7. 確定裁定の手順書更新が計画にない

S-2 は穴を「手順書と成果物へ」明記する裁定だが、段 5 所有一覧に runbook/README 更新がない。[brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/brief.md:22) [out-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t783-toolchain-binding/out-plan.md:841) 段 7 で行うなら、その対象と記述する全穴を plan v2 に列挙すべきである。

## 裁定パッケージ候補

### [裁定パッケージ候補] 完全な toolchain identity

CXX version、C/CXX/CMake bytes hash、CMake path を authority に足すには calibration 再発行が必要で、現 scope 外である。選択肢は「A-1 前に再発行して混用を閉じる」か、「P6 を撤回し、metadata-pair 一致に主張を縮小して全穴を成果物へ載せる」。

### [裁定パッケージ候補] floor artifact schema と consumer

`build_toolchain_binding` を top-level 必須 field にするなら、manifest/result の schema 改版、`s8b_ratified_freeze` の独立照合、manifest ↔ result ↔ calibration の一致検査を同じ land に含める必要がある。

### [裁定パッケージ候補] attempt provenance

A-4 を証拠脚と呼ぶなら、snapshot を current PBS job・nonce・execution receipt・raw file hashes へ束縛する必要がある。そこまで広げない場合は A-4 を「caller-provided observation」に降格し、official protection として数えない。

## 総括

- **NO-GO** — blocker 1〜5。
- 受理集合は pilot/post-permit では **拡大**、現在の official だけは無条件拒否により不変・空集合。
- refuted: authority は列挙 4 項だけ、P6 の混用閉鎖、穴は 2 件だけ、未確認前提なし。
- 最も危険な恒真 gate: caller 作成 snapshot を実測と扱う attempt 脚の **恒真な緑**。
- 未確認: 現在の compute node 全体の GCC/CMake実体・version、および attempt 引数の公式 provenance 境界。