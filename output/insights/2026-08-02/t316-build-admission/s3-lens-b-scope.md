## 判定

このプランでは T-316 は閉じない。(b) は Pegasus で使える隔離 backend と投入経路が未確認であり、(a) は三つの `run_one_iteration()` の内側にしか置かれず、下位 API・sweep・手動 patch 経路を素通しする。

本レビューは `rg`、ファイル閲覧、行数・byte 数確認だけの静的検査である。pytest、build、実行検証は行っておらず、緑は主張しない。

## 所見

### 1. [致命的] 親 P2 は、実装可能性が証明されていない (b) を主柱にしている

**claim:** `(b) credentialless・network 無し sandbox` は repo 内変更だけでは実効化できず、DW-G04 の実装開始条件も満たしていない。親 P2 の load-bearing 裁定は成立しない。

**evidence:** 親は (b) を load-bearing とするが、plan 自身が `perf`・NUMA・hardware counter と namespace の両立をサイト依存として認めている（[brief.md:36-40](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/brief.md:36)、[s2-plan.md:247](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:247)、[s2-plan.md:389](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:389)）。`docs/pegasus-runbook.md` 全体を `bubblewrap|bwrap|unshare|seccomp|landlock|rootless|network namespace|mount namespace|user namespace|sandbox` で grep した結果は 0 件だった。記載があるのは spoof 可能な PID namespace の「host 判定」だけであり（[pegasus-runbook.md:480-481](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/docs/pegasus-runbook.md:480)）、計算ノードには外部到達可能な proxy もある（[pegasus-runbook.md:492-503](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/docs/pegasus-runbook.md:492)）。さらに campaign dispatch は未実装で、build/run 自体が T-277 により拒否中である（[pegasus-runbook.md:540-551](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/docs/pegasus-runbook.md:540)）。brief の二つの artifact path は既存 loop の実走を示すだけで、sandbox backend の発火成功を示さない（[brief.md:30-31](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/brief.md:30)）。これは DW-G04 の条件に反する（[core.md:57-60](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/docs/dev-wave/core.md:57)）。

**impact:** 本 wave で得られる certified 候補・`median_tps`・材料レポートには sandbox containment の根拠が付かず、P1 の test-only で閉じれば受理集合は「任意 C++」のまま残る。

**suggested_fix:** (b) は capability 測定 ID が得られるまで設計メモへ戻す。Pegasus 用の別 wave で、計算ノード上の rootless user/network/mount namespace、cgroup kill、perf/NUMA、PBS staging と sanctioned dispatch を実測・runbook 化する。それまでは repo 側の共通 pre-build 境界で coder-derived build を明示停止する。

### 2. [致命的] semantic gate は下位入口を閉じず、driver 内の飾りになる

**claim:** plan の gate 配線は三つの `run_one_iteration()` に限定され、`pipeline.evaluate()`、sweep、screening、手動 patch 適用から build/run へ到達できる。

**evidence:** 最小実装は三 driver 内での再実行しか指定していない（[s2-plan.md:347-365](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:347)）。一方、`run_campaign()` は working tree から `src_token` を作り、そのまま `evaluate()` を呼ぶ（[loop.py:107-149](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/loop.py:107)）。`evaluate()` の引数には semantic admission/receipt がなく（[pipeline.py:418-431](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/pipeline.py:418)）、直接 build へ進む（[pipeline.py:557-598](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/pipeline.py:557)）。`patchharness.applied()` も任意 patch を適用するだけで gate receipt を要求しない（[patchharness.py:234-251](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/patchharness.py:234)）。sort/trigger sweep は raw implementation を書いた後、直接 `run_campaign()` または screening へ渡している（[s6_sort_sweep.py:300-331](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s6_sort_sweep.py:300)、[s8a_trigger_sweep.py:346-378](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s8a_trigger_sweep.py:346)）。

**impact:** 同じ coder 由来 bytes を別入口から materialize すれば BUILD_DONE、COMMIT、fitness まで進めるため、semantic gate 実装後も実効受理集合は変わらない。

**suggested_fix:** `run_campaign()`／`pipeline.evaluate()` の共通 pre-build seam で、全 non-stock source に provenance class を必須化する。coder-derived class は `{axis,input_digest,normalized_ir_digest,rendered_source/src_token,template_patch_digest,gate_version,renderer_version}` に束縛した再検算可能な receipt を要求し、手動 patch・machine sweep・frozen candidate は別の明示的 provenance class にする。直接 `evaluate()`、両 sweep、screening、manual patch を negative integration test に含める。

### 3. [高] sandbox 外の trace consumer が攻撃者制御 path を追う

**claim:** subprocess だけを sandbox に移しても、trace の取り出しが trusted parent 側で symlink/FIFO を無検査に開くため、filesystem・resource containment は閉じない。

**evidence:** plan は candidate の trace dir を writable にし、trace subprocess の sandbox 化だけを統合点としている（[s2-plan.md:224-242](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:224)）。現実装は candidate 実行後、parent namespace で `trace_*.log` を通常の `open()` に渡している（[pipeline.py:218-230](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/pipeline.py:218)）。sandbox 内で作った symlink の target は、後から parent namespace で解決される。

**impact:** host path の間接読み取り、FIFO/device による parent の停止、偽 `ncommit` による verifier 判定変更が可能で、sandbox receipt があっても certified 値の containment を証明できない。

**suggested_fix:** copy-out 境界を設計対象に加え、`openat2(RESOLVE_BENEATH|NO_SYMLINKS)` 相当または `O_NOFOLLOW|O_NONBLOCK`、`fstat` regular-file 検査、件数・単体/総 byte 上限、所有 dir の inode 固定を行う。stdout/stderr も `capture_output=True` の無制限蓄積ではなく、parent 側で上限付きに読む。

### 4. [高] semantic reject は writer だけ増え、既存 consumer が情報を落とす

**claim:** 新 reject を既存 diff-quarantine WAL に相乗りさせても、gate/IR/renderer digest は loader で消え、別 reason にすれば loader 自体が拾わない。

**evidence:** plan は `gate version`、入力 digest、正規化 IR digest、renderer version の記録を要求する（[s2-plan.md:167-168](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:167)）。既存 `DiffQuarantineRejection` にはその field がなく（[digest.py:161-182](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/critic/digest.py:161）、loader は `reason == diff-quarantine` のみを拾って固定 field に縮退する（[digest.py:325-359](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/critic/digest.py:325)）。renderer の既定分岐は semantic reject まで「フレーム/hole 逸脱」と誤表示する（[digest.py:630-655](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/critic/digest.py:630)。さらに汎用 `--campaign-dir` report は `load_diff_rejections()` を渡しておらず（[digest.py:683-699](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/critic/digest.py:683)）、`p3_s4_red` の report も同様である（[p3_s4_red.py:180-186](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_red.py:180)）。

**impact:** critic は拒否原因を再利用できず、材料レポートの reject 集合と gate-version 参照が WAL より小さくなるため、同じ不受理提案の再生成と proof chain の欠落が起きる。

**suggested_fix:** `SemanticRejection` を別型・別 reason として設け、専用 loader、renderer、critic 射影、CLI、全 report generator を更新する。record→WAL→loader→critic/report の往復で全 digest field が exact に残るテストを必須にする。

### 5. [高] sandbox receipt が campaign・cache・COMMIT に束縛されていない

**claim:** plan は receipt を発行すると書くだけで、どの測定・binary・cache entry がどの sandbox policy で得られたかを固定する実装点を持たない。

**evidence:** `native_sandbox.py` は policy/namespace/mount/toolchain receipt を返す想定だが（[s2-plan.md:217-222](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:217)）、最小実装一覧には schema、campaign identity、cache consumer、report の更新がない。plan 自身も、束縛しなければ sandboxed/unsandboxed run が混在すると認めている（[s2-plan.md:371-381](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:371)）。現行 BUILD_DONE は binary hash/command のみ（[pipeline.py:604-611](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/pipeline.py:604)）、COMMIT は fitness/verify 情報のみである（[pipeline.py:854-869](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/pipeline.py:854)）。

**impact:** 同じ variant・`median_tps`・cache binary が legacy unsandboxed build と新 policy 下で同一参照に混在し、report は containment 条件を判別できない。

**suggested_fix:** receipt digest を測定 epoch/campaign identity、BUILD_DONE、COMMIT、binary SHA、実行 argv に束縛する。cache hit は保存済み build receipt が現 policy と一致する場合だけ許し、legacy は `unsandboxed` として certified 集合から分離する。

### 6. [高] 「schema 互換 gate」は producer 契約と非互換で、pin 回避のため探索を潰している

**claim:** role hash を変えないため consumer だけを狭める案は、互換 gate ではない。特に sort の finite exact allowlist は合成を既知候補選択へ変える。

**evidence:** plan は backoff を exact literal、sort を有限 canonical comparator に限定する（[s2-plan.md:349-359](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:349)）一方、backoff role は `<式>` を許可する（[coder-v4-autonomous.md:52-63](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/.claude/agents/coder-v4-autonomous.md:52)）。sort role は `rcdptr_`、既存 silo API の straight-line code、複数行の raw `sort(...)` を契約上許可する（[coder-v4-autonomous-sort.md:78-101](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/.claude/agents/coder-v4-autonomous-sort.md:78)、[coder-v4-autonomous-sort.md:105-114](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/.claude/agents/coder-v4-autonomous-sort.md:105)）。producer を実際の受理言語へ合わせれば、人間レビュー時だけ更新可能な role manifest pin に触れる（[review_ledger.py:31-34](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/codex_roles/review_ledger.py:31)）し、schema/source drift は checker が拒否する（[spec.py:565-592](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/codex_roles/spec.py:565)、[spec.py:654-670](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/codex_roles/spec.py:654)）。これは brief の「role hash を更新しない」と両立しない（[brief.md:46-50](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/brief.md:46)）。

**impact:** safe positive control 一件だけ通しつつ実 role の有効提案を大量拒否でき、sort の certified 集合・選択・median は「LLM 合成」ではなく事前 allowlist の結果になる。

**suggested_fix:** 緊急 wave では sort build を停止して「互換実装済み」と称さない。typed IR 導入は別の人間レビュー wave とし、role source、manifest/schema、該当台帳、`.codex/role-adapters` を同時更新してから再開する。

### 7. [高] 推奨 (c) は一 wave の実装量ではない

**claim:** 三軸 parser/renderer、全入口の admission receipt、全 consumer、sandbox backend、Pegasus 投入契約、cache/report migration を一 wave で完了するのは非現実的である。

**evidence:** 最終経路は parser から sandboxed preprocess/build/trace/perf、certification までを一鎖にする（[s2-plan.md:284-301](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:284)）。sandbox だけでも preprocess、configure/build、`nm`、trace、perf、legacy/v2 の全 subprocess を変更する（[s2-plan.md:224-245](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:224)）うえ、その実行環境と dispatch は未成立である。

**impact:** 段 4 author が driver gate、receipt consumer、site integration のいずれかを省略しても「(c) 実装」と見えるため、未閉鎖の受理集合と不完全な proof chain が完成扱いされる。

**suggested_fix:** 以下の三 wave に分ける。

1. Repo containment wave: 共通 pre-build receipt、backoff/trigger の実証済み grammar、sort build-stop、全入口・consumer・preview の配線。
2. Site sandbox wave: Pegasus capability probe、PBS staging/dispatch、backend、copy-out、perf/NUMA 実測と runbook。
3. Contract migration wave: 人間レビュー付き typed IR、台帳・manifest・adapter 更新、legacy artifact の再分類/再実走。

### 8. [中] preview/dry-run と本 build の受理集合が一致しない

**claim:** `--preview-diff` と sweep の candidate identity 経路には semantic gate がなく、auditor が「passed」と見た bytes を本 build が後から拒否する。

**evidence:** sort preview は `quarantine(write=False)` の結果だけを返し、その `passed` で exit code を決める（[p3_s4_loop_sort.py:331-378](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop_sort.py:331)）。trigger preview も同型である（[p3_s4_loop_trigger_gating.py:525-577](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/p3_s4_loop_trigger_gating.py:525)）。sort/trigger sweep の `_candidate_ref()` も raw code を書いて `src_token` を発行する（[s6_sort_sweep.py:282-297](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s6_sort_sweep.py:282)、[s8a_trigger_sweep.py:327-343](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/campaign/s8a_trigger_sweep.py:327)）。

**impact:** preview の受理集合と build の受理集合、ならびに candidate `src_token` 参照が分裂し、auditor budget と artifact reference が実行不能候補へ消費される。

**suggested_fix:** parse→render→structural quarantine→receipt 発行を一つの `admit_and_materialize(write=...)` に集約し、preview、dry-run、candidate-ref、本 build の全てに使う。同一入力で verdict と digest が一致する統合テストを置く。

### 9. [中] 三軸一般化は brief の証拠だけでは DW-G03 を満たさない

**claim:** brief の五 payload は同じ `DiffQuarantine.validate()` consumer に対する一事故族であり、三種類の typed gate を制度化するための独立二例になっていない。

**evidence:** 実測 1〜5 は単一 consumer とそのテスト不足を示すだけである（[brief.md:13-25](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/brief.md:13)）。既存 campaign dir は loop 実走の証拠にすぎない（[brief.md:30-31](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/brief.md:30)）のに、plan はそこから backoff/sort/trigger 三 spec へ一般化している（[s2-plan.md:132-146](/home/SFC/tanab/.claude/jobs/31b3fbdf/tmp/wave-t316/s2-plan.md:132)）。DW-G03 は異なる producer/consumer での独立二件を要求する（[core.md:52-55](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/docs/dev-wave/core.md:52)）。

**impact:** 実 artifact で発火を示していない sort/trigger の受理集合まで変更し、三 parser 分の実装費と既存 certified 候補の再分類を根拠なく発生させる。

**suggested_fix:** sort と trigger について、実 role proposal→各 driver→build spy の独立 positive/negative artifact を二件提示する。揃わなければ本 wave は実測済みの局所軸と共通 build-stop に限定し、他軸は設計メモに留める。

## pin・生成物閉包

| 面 | 判定 |
|---|---|
| 4 台帳・`manifest.json`・adapter | consumer-only gate は直接発火しないが、producer 契約を受理言語へ合わせる typed IR 移行は source/manifest/schema pin と adapter を発火させ、人間レビュー境界に当たる。 |
| `FROZEN_MANIFEST` | 新 module/test 自体は 23 path に含まれず直接発火しない（[test_frozen_artifacts.py:38-85](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_frozen_artifacts.py:38)、[同:141-153](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/orchestrator/tests/test_frozen_artifacts.py:141)）。既存 frozen report の書換えで migration してはならない。 |
| `tools/check_docs.py` | repo code/runbook だけなら dev-wave 予算は直接発火しない。DW-G03/G04 本文を追記するなら aggregate ceiling は 24,000 bytes（[check_docs.py:246](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/tools/check_docs.py:246)、[同:2640-2645](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-t316-role-gate/tools/check_docs.py:2640)）で、静的 `wc -c` の現値は 23,986 bytes、余裕は 14 bytesしかない。 |

## 総括

- **最大の取り残し:** semantic gate が三 driver 内に閉じ、`pipeline.evaluate()`、sweep、screening、manual patch、preview を通る下位経路が無防備である。
- **実装不能点:** Pegasus runbook には利用可能な rootless network/filesystem sandbox も campaign dispatch も記載がなく、(b) を本 wave の load-bearing 成果にはできない。
- **分割提案:** まず共通 pre-build receipt と build-stop、次に Pegasus sandbox 実測・投入契約、最後に人間レビュー付き typed IR/pin migration の三 wave に分ける。