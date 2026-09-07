## 黙って捨てられる経路

- `receipt + --no-build` → プランどおり入口で組合せ検査すれば rc=2 で明示停止する。検査が遅いと、既存の `do_build=False` 分岐は `run_campaign` 前に `dry-pass` を返すため、必ず early-return より前に拒否する必要がある。[s2-plan.md:97](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2356-s4-prebuild-seam/codex/t2356-s4-prebuild-seam/s2-plan.md:97) [p3_s4_loop.py:1495](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:1495)

- `receipt + --emit-planner-context` → 同じく rc=2 で明示停止が必要。現行の planner-context 分岐は build 系処理より前に正常終了するため、組合せ検査をこの分岐より後へ置くと完全に黙殺される。[s2-plan.md:123](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2356-s4-prebuild-seam/codex/t2356-s4-prebuild-seam/s2-plan.md:123) [p3_s4_loop.py:2175](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:2175)

- `receipt + fixture --value` → `main` から `_run_one_iteration_resolved` へ直接入る。[p3_s4_loop.py:2305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:2305) `receipt + --run-iteration`、および有効な `--b4-reflux-ablation` → `drive_iteration` を経由する。[p3_s4_loop.py:2267](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:2267) プランは両方へ5本を追加しており、ここに経路欠落はない。[s2-plan.md:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2356-s4-prebuild-seam/codex/t2356-s4-prebuild-seam/s2-plan.md:14)

- `receipt + --run-iteration` で checkpoint が既に停止条件を満たす → `ran=False, outcome=stopped-before` となり build には到達しない。stdout には出るが、`main` はこれを正常な結果として rc=0 を返す。したがって「明示停止」ではなく「可視だが正常終了」である。[p3_s4_loop.py:2043](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:2043) [p3_s4_loop.py:2285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:2285)

- `receipt + --isolate-worktree` → worktree と cache root の選択だけが変わり、絶対 path の base/source 5本を捨てる分岐ではない。[p3_s4_loop.py:2226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:2226)

- `receipt + OTHER site` → 現行の `campaign_options` は Pegasus 分岐内でしか `env_contract` を入れない。この形へ5本を単純にネストすると OTHER では legacy `build()` が選ばれ、receipt は configure argv に届かない。[p3_s4_loop.py:1525](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:1525) [pipeline.py:1268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:1268) プランの「receipt があれば site 非依存で `env_contract` と5本を入れる」はこの欠陥を正しく避けている。[s2-plan.md:85](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2356-s4-prebuild-seam/codex/t2356-s4-prebuild-seam/s2-plan.md:85) unknown site は `_admit_env_contract` が明示例外にする。[p3_s4_loop.py:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:137)

- valid receipt でも candidate が terminal duplicate → `run_campaign` は `evaluate` より前に skip するため5本は buildcache へ届かない。[loop.py:527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/loop.py:527) driver は duplicate outcome と既存 variant をログへ出すので黙ってはいないが、やはり rc=0 になり得る。[p3_s4_loop.py:1392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:1392)

- grammar/preflight、quarantine、condition gate、source/admission failure → receipt は configure へ届かない。前二者は structured reject、condition gate は例外、pipeline admission は abort WAL とログになる。[p3_s4_loop.py:1478](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:1478) [p3_s4_loop.py:1510](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:1510) [pipeline.py:1059](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:1059) いずれも無記録ではないが、abort は driver/job の非零終了を保証しない。

- **欠陥:** 5本のうち1本を loop→pipeline で落とした入力 → pipeline の検査例外は `run_campaign` の広い `except Exception` に捕まり、variant の `eval-exception` abort に変換される。[loop.py:590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/loop.py:590) [loop.py:602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/loop.py:602) さらに driver は aborted outcome でも rc=0 を返し得る。[p3_s4_loop.py:2285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:2285) つまり配線欠落はログ/WALには出るが、production job を明示停止しない。

## 同値条件

- base だけ、または receipt だけ → `_build_v2_impl` が `bool(base) != (receipt is not None)` で拒否する。[buildcache.py:2435](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/buildcache.py:2435) [buildcache.py:2444](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/buildcache.py:2444)

- source dir が1～2本だけ → `_normalize_fetchcontent_source_dirs` が拒否する。3本あって base が空 → `_build_v2_impl` と `_v2_commands` の双方が拒否する。[buildcache.py:848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/buildcache.py:848) [buildcache.py:1952](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/buildcache.py:1952)

- プランの値、すなわち truthy な canonical base、3本すべての source dir、non-`None` の2-key receipt → 上記同値条件を満たし、configure には base 1本と source define 3本が入る。[buildcache.py:1965](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/buildcache.py:1965)

- **欠陥:** 共有APIは5引数を独立 optional として受け、all-or-nothing 検査は pipeline core にしか置かない計画である。[s2-plan.md:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2356-s4-prebuild-seam/codex/t2356-s4-prebuild-seam/s2-plan.md:21) [s2-plan.md:28](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-jobs/dev-wave-t2356-s4-prebuild-seam/codex/t2356-s4-prebuild-seam/s2-plan.md:28) このため片側だけの中間状態は作れる。non-terminal candidate なら abort に変換され、terminal duplicate なら pipeline 検査自体を通らず generic skip になる。新規5引数の整合検査は `run_campaign` 入口でも行わないと、配線ミスを campaign configuration error として明示停止できない。

## 既定経路の非変更

- seam 未指定 → `run_campaign` の新値を `evaluate_options` へ入れず、pipeline の `common` にも入れない計画なので、legacy/v2 選択は現在どおり `env_contract is None` だけで決まる。[loop.py:536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/loop.py:536) [pipeline.py:1224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:1224)

- その条件を守れば、`backoff_sweep`、`paper_story_a2_certification`、`s8b_floor_campaign` および既存 test の呼出し式は編集不要である。`buildcache` は receipt が `None` なら preimage field を追加せず、base が空なら configure define も追加しないため、cache key・configure argv・WAL の既存語彙は変わらない。[buildcache.py:1343](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/buildcache.py:1343) [buildcache.py:1940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/buildcache.py:1940)

- 「optional 引数だから変わらない」だけなら恒真に近く根拠にならないが、プランの default spy は `evaluate_options`、core `common`、`build_v2` kwargs に新keyが存在しないことを観測するので、自己証明ではない。[s2-plan.md:183](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2356-s4-prebuild-seam/codex/t2356-s4-prebuild-seam/s2-plan.md:183) ただし「呼出し形」に Python の公開関数 signature 自体まで含めるなら、5 optional parameter の追加により文字どおりの1-bit不変は成立しない。守れるのは既存 caller の呼出し式と downstream kwargs である。

## receipt 検査の実効

- schema version 違い → exact version 検査で明示拒否する。producer は固定値を直接書くため正規 job receipt は通る。[s2-plan.md:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2356-s4-prebuild-seam/codex/t2356-s4-prebuild-seam/s2-plan.md:42) [p3_s4_loop_pegasus.sh:409](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/p3_s4_loop_pegasus.sh:409)

- `config_h_sha256` と現物が不一致 → loader が現物 bytes を hash して拒否する。fresh build 後にも buildcache が実効 source の HEAD/config hash を再取得して receipt と比較する。[s2-plan.md:48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2356-s4-prebuild-seam/codex/t2356-s4-prebuild-seam/s2-plan.md:48) [buildcache.py:2808](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/buildcache.py:2808)

- base dir が既に消滅 → loader の directory 検査で拒否し、すり抜けても `_canonical_fetchcontent_base` が拒否する。[s2-plan.md:43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2356-s4-prebuild-seam/codex/t2356-s4-prebuild-seam/s2-plan.md:43) [buildcache.py:750](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/buildcache.py:750)

- base/source_root/config path または導出した source dir が symlink → プランの field 検査、または buildcache の source-dir canonicalization で拒否される。[s2-plan.md:43](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2356-s4-prebuild-seam/codex/t2356-s4-prebuild-seam/s2-plan.md:43) [buildcache.py:823](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/buildcache.py:823)

- **欠陥:** CLI で指定した receipt file 自体が symlink → プランは receipt path の `lstat`/non-symlink regular-file 検査を記載していない。通常の `Path.open` なら symlink を辿り、内容とfield pathが正しければ通る。job producer 側は fresh-path 検査と `"x"` 作成で symlink を防いでいるため、consumer helperにも同じ対象を明記しないと要求を満たしたとは言えない。[p3_s4_loop_pegasus.sh:361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/p3_s4_loop_pegasus.sh:361) [p3_s4_loop_pegasus.sh:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/p3_s4_loop_pegasus.sh:425)

- **欠陥:** 別 job のまだ存在する receipt を渡し、その receipt の base/source/config が互いに整合している → `source_root == fetchcontent_base_dir`、hash、path 検査はすべて通り、別 job の source が実際に build へ使われる。`pbs_jobid` は非空だけを検査し、現在の `PBS_JOBID` と比較しない計画だからである。[s2-plan.md:44](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2356-s4-prebuild-seam/codex/t2356-s4-prebuild-seam/s2-plan.md:44) [s2-plan.md:52](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2356-s4-prebuild-seam/codex/t2356-s4-prebuild-seam/s2-plan.md:52) producer は required env の `PBS_JOBID` をそのまま記録するため、「非空」は正規 producer に対して恒真であり、job 取り違え検査にはなっていない。[p3_s4_loop_pegasus.sh:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/p3_s4_loop_pegasus.sh:17) [p3_s4_loop_pegasus.sh:423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/p3_s4_loop_pegasus.sh:423)

## 生死確認の成立

- 提案された OTHER/login-node fixture probe → receipt reader、site 非依存の `env_contract` 注入、driver直通 fixture経路、`run_campaign`、`evaluate`、pipeline `common`、`build_v2`、`_v2_commands` までの正の到達性を反証できる。receipt が途中で落ちれば `_build_v2_impl` の同値条件で `_v2_commands` 前に止まるため、4 define の捕捉は receipt 到達の間接証明にもなる。

- cache hit → `_v2_commands` が呼ばれない、とはならない。hit 側も `_v2_result` が現在の5引数から configure argv を再構成するため、この probe は fresh cache を必須としない。[buildcache.py:2628](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/buildcache.py:2628) [buildcache.py:2105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/buildcache.py:2105)

- probe sentinel を `_v2_commands` から投げる → pipeline が `RuntimeError` を `build-error` abort に変換するため、sentinel は `main` の外へは伝播しない。[pipeline.py:1300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:1300) probe は例外伝播や driver rc ではなく、wrapper が保存した実 argv を直接 assert しなければならない。

- 既存 terminal と同じ fixture value → duplicate skip により `_v2_commands` wrapper は一度も呼ばれない。[loop.py:527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/loop.py:527) プランには fresh/non-terminal candidate を保証する条件がなく、生死確認が過去の campaign 状態に依存する穴がある。

- fixture probeだけ → shell の proposal/fixture両分岐へのCLI追加、`--run-iteration` の `drive_iteration` 配線、B4、`--isolate-worktree`、実 Pegasus site、別job receipt拒否は反証できない。また configure subprocess 前で止めるため、事前構築物がCMakeで実際に再利用されたことまでは証明しない。ただし今回の受入点である「production `_v2_commands` の argv まで届く」ことの生死確認としては有効である。[s2-plan.md:187](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2356-s4-prebuild-seam/codex/t2356-s4-prebuild-seam/s2-plan.md:187)

## 総括

正常系の5本配線は、プランどおり receipt を唯一の trigger とし、OTHER site でも `env_contract` を同時注入すれば `_v2_commands` まで届く。source配置を base 直下の `*-src` に変える判断も、build後の実効root検査と一致している。

実装前に直すべき欠陥は3点ある。

- 5本の整合検査が pipeline にしかなく、配線欠落が duplicate で未検査、または `eval-exception` abort と rc=0 に化ける。`run_campaign` 入口でも新規5本と `env_contract` の整合を拒否する必要がある。
- receipt の `pbs_jobid` 非空検査では別job receiptを拒否できない。
- receipt file 自体の symlink 拒否がプランにない。

生死確認は正のargv到達性を反証できるが、fresh/non-terminal candidate の保証と、sentinelがpipelineで吸収されることを踏まえたassertが必要である。静的読解のみで、テスト・実測は行っていない。