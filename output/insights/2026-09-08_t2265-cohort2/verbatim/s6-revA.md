## 所見 1 — terminal 非閉鎖が producer で成果物になる前に拒否される

- 所見: producer は terminal なしの raw v3 を必ず拒否するため、事前登録どおり `terminal_not_closed` を返す経路が到達不能であり、cohort 1 の再生成も同じ理由で壊れる。
- 根拠: [t2187_adaptive_const_probe.py:1285](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/tools/pegasus/probes/t2187_adaptive_const_probe.py:1285) は `terminal_positions != [len(events) - 1]` を `ValueError` にする。一方、[cohort 2 解析器:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:198) は「`Zero terminals is the preregistered non-closure outcome`」、[事前登録:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/docs/backoff-counterfactual-cohort2-preregistration.md:300) は terminal 非閉鎖を主判定全体の `inconclusive` と定める。また [test_dynamic_backoff_transitions.py:1774](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/orchestrator/tests/test_dynamic_backoff_transitions.py:1774) は `flushes=0` の実 emitter 出力を同 parser に渡すので、現物上は静的に例外になる。
- 実害: terminal 非閉鎖 seed は「12 件を保持して inconclusive」ではなく artifact 未生成になり、terminal 無効の cohort 1 再走も artifact を生成できない。
- 提案: raw v3 は terminal 0 件または末尾 1 件だけを受理し、0 件なら exact summary を `updates=len(events), retained=len(events), dropped=0, flushes=0` とする。plot の v4 consumer も同じ非閉鎖例外を受理させる。

## 所見 2 — terminal define の要求が trace 無効 build に漏れている

- 所見: terminal の実行状態と記録処理はコンパイル時除去されるが、`BACKOFF_TRACE_TERMINAL_US` の必須定義契約は規律 1 の外へ漏れている。
- 根拠: [patch C:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/patches/cicada-adaptive-counterfactual.patch:53) の `#ifndef BACKOFF_TRACE_TERMINAL_US` は、後続の [patch C:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/patches/cicada-adaptive-counterfactual.patch:67) の `#if BACKOFF_TRACE` より外にある。さらに [patch C:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/patches/cicada-adaptive-counterfactual.patch:28) は universal definitions に同 macro を追加する。契約は [impl-contract.md:63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/impl-contract.md:63) で terminal 計装を `#if BACKOFF_TRACE` 内へ完全に収めるとしている。
- 実害: patch C 適用後は trace 無効を含む全 build が新 define を要求し、従来の直接 compile 経路は `#error` で失敗する。標準 CMake 経路でも全 target の compile input が変わる。
- 提案: `#ifndef` と値域検査を `#if BACKOFF_TRACE` 内へ移し、trace 無効時は CMake の compile definitions にも terminal macro を出さない。trace 無効の検査は同 define を供給せずに compile/preprocess する。

## 所見 3 — terminal 後に制御器まで永久停止する挙動は事前登録されていない

- 所見: terminal 記録後は trace 記録だけでなく controller、LCG、割当の更新が run 終了まで停止する。
- 根拠: [patch C:348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/patches/cicada-adaptive-counterfactual.patch:348) は `terminal_recorded_` のとき `return true`、[patch C:412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/patches/cicada-adaptive-counterfactual.patch:412) はその真値で caller 全体から `return` する。[patches/README.md:314](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/patches/README.md:314) は「以後 controller を更新せず」と記すが、凍結済み [事前登録:177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/docs/backoff-counterfactual-cohort2-preregistration.md:177) は terminal 自身が backoff を更新せず、以後の event を記録しないことまでしか定めていない。
- 実害: 記録済み terminal 以前の推定量には遡及しないが、run 末尾約 1 秒は固定 backoff で走り、trace-enabled run の `median_tps` と末尾状態が変わる。性能 build には影響しないが、診断 throughput は上振れまたは下振れしうる。
- 提案: terminal を記録した呼出しだけ更新を止め、以後は controller と LCG を進めつつ trace record の追加だけを抑止する。

## 所見 4 — published group receipt の再受理が exact ではなく、受理後の削除面も危険である

- 所見: certification の初回 group payload は exact だが、既存 published receipt の再検査は重要 field と row の `trace_dir` を検査せず受理する。
- 根拠: [t2187_adaptive_const_probe.py:2640](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/tools/pegasus/probes/t2187_adaptive_const_probe.py:2640) は `expected_requests=24`、`terminal_requests=24`、exact `claim_limitations`、`performance_values_remain_uncertified=True` を生成する。しかし [同:2724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/tools/pegasus/probes/t2187_adaptive_const_probe.py:2724) の再検査は `certified_requests` だけを確認し、これらの field、row の certified 状態、`trace_dir` を確認しない。[同:2890](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/tools/pegasus/probes/t2187_adaptive_const_probe.py:2890) はその receipt を受理し、[同:2975](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/tools/pegasus/probes/t2187_adaptive_const_probe.py:2975) は receipt 内の任意の文字列 `trace_dir` を `shutil.rmtree` に渡す。
- 実害: claim limitation や件数を改変した receipt が certified group として再受理され、改変された `trace_dir` の削除まで発火しうる。
- 提案: published receipt でも top-level 件数、limitations、未認証 marker、各 row の certified 状態と元 result JSON との一致、exact namespace 内の `trace_dir` を再検証してから `group_complete` を返す。

## 所見 5 — cohort 1 metadata 分岐は新しい引数軸に対して緩んだ

- 所見: `_artifact_contract_metadata` の cohort 1 条件は文字列上は維持されたが、新設された terminal 引数を無視するため意味的な受理集合が広がった。
- 根拠: [t2187_adaptive_const_probe.py:3100](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/tools/pegasus/probes/t2187_adaptive_const_probe.py:3100) で `backoff_trace_terminal_us` が追加されたが、cohort 1 分岐 [同:3110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/tools/pegasus/probes/t2187_adaptive_const_probe.py:3110) には `backoff_trace_terminal_us == 0` がない。公開 `main` は別の exact gate で防ぐため、現行 caller 全体では遮断される。
- 実害: helper 単体では cohort 1 exact axesに terminal 値を足した near-miss にも cohort 1 の事前登録 SHA を付与でき、将来の直接 caller で誤束縛になる。
- 提案: cohort 1 分岐へ `and backoff_trace_terminal_us == 0` を追加し、その 1 軸だけを変えた負例を足す。

## 所見 6 — certification の cell 拡張自体は exact だが説明が旧状態のままである

- 所見: raw allowlist、parsed membership、cell 別 extime、claim、namespace、row、group construction、PBS は exact な閉表であり、指定 near-miss は落ちるが、README は「exact 2 cell 契約は不変」と誤記している。
- 根拠: [t2187_adaptive_const_probe.py:331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/tools/pegasus/probes/t2187_adaptive_const_probe.py:331) の `CERT_CELL_BY_TEXT` は exact 4 literal、[同:1373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/tools/pegasus/probes/t2187_adaptive_const_probe.py:1373) は raw lookup を parsed 比較より先に行い、[同:1392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/tools/pegasus/probes/t2187_adaptive_const_probe.py:1392) は cell 別 extime を exact 比較する。PBS も [t2187_adaptive_const_probe.pbs:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:183) の exact `case` と [同:199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:199) の extime 比較を持つ。したがって cap が `9223372036854775806` の literal は raw lookup で拒否され、prefix、任意の正 extime、parsed 値だけでは通らない。一方 [patches/README.md:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/patches/README.md:323) は「認証の exact 2 cell 契約...1 byte も変えていない」と記す。
- 実害: cell の実受理集合は意図した exact 2 本だけ増えているが、説明を信じる監査者は拡張を見落とす。
- 提案: README を「exact 2 cell から exact 4 cell への制御された拡張」と訂正する。受理コードの一般化は不要。

## 所見 7 — 凍結 bytes は保たれたが、解析器は aggregate stack hash を検査しない

- 所見: 凍結文書と cohort 1 の禁止対象は不変で、個別 patch pin も実物に一致するが、cohort 2 解析器は `patch_stack_sha256` の欠落または不一致を受理する。
- 根拠: 実測 SHA-256 は cohort 2 文書 `8b4127...a9e9`、cohort 1 文書 `526d93...495a`、patch A `9b2153...54b`、B `f3fe6b...824`、C `b5649b...d5f`、stack `790a6e...fdb8` で、[cohort 2 解析器:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:20) と [同:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:27) の pin に一致した。cohort 1 文書、解析器、test は `HEAD` と同一 bytes だった。ただし [同:121](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:121) の `expected` に `patch_stack_sha256` がなく、事前登録 [§9:351](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/docs/backoff-counterfactual-cohort2-preregistration.md:351) は `patch_stack と各 sha256` の記録を要求する。
- 実害:コード bytes は exact でも、自己矛盾した aggregate hash を持つ artifact が解析対象に入り、参照 provenance が壊れる。
- 提案: pinned 3-entry stack から exact aggregate SHA を定数化して top と全 row で検査し、欠落と 1-bit drift の負例を加える。

## 所見 8 — §7 の解析順序と残存集合基準は正しい

- 所見: producer 非閉鎖問題を除けば、位置除外、0 commit 走査、terminal following、block 再採番は凍結 §7 と一致する。
- 根拠: [cohort 2 解析器:455](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:455) で最初に `analysis_events = events[1:]`、[同:461](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:461) で terminal を含む 0 commit を membership より前に走査する。[同:459](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:459) は terminal を current から除き、[同:483](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:483) は最後の通常 event と terminal を対に含める。block は [同:759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:759) で残存 current 件数を使う。
- 実害: この部分による推定値、位置 index、4 分割のずれはない。
- 提案: 変更不要。producer から terminal 0 件を到達可能にした後も、この順序を保持する。

## 所見 9 — 新設 test には歯のあるものと、到達不能 fixture だけを見るものが混在する

- 所見: count closure と assignment 負例は実装へ届くが、非閉鎖、terminal define、cohort 2 certification の一部 test は統合面を殺さない。
- 根拠:
  - [test_missing_terminal...:367](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/orchestrator/tests/test_backoff_counterfactual_cohort2_analysis.py:367) は正規化 JSON から terminal を直接消すため、実 producer parser の先行拒否を通らない。
  - [test_terminal_define_is_present_only...:1507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/orchestrator/tests/test_t2187_adaptive_const_probe.py:1507) は `genome.flags` だけを見ており、CMake universal define と外側の `#ifndef` を見ない。
  - trace 無効前処理検査は actual patch-applied header と実 `g++ -E` を使うが、[test_dynamic_backoff_transitions.py:1695](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/orchestrator/tests/test_dynamic_backoff_transitions.py:1695) で terminal define を必ず供給するため、必須定義漏れを検出しない。
  - count closure は [同:638](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/orchestrator/tests/test_dynamic_backoff_transitions.py:638) から actual patch header の `leaderBackoffWork` を呼ぶので、実際の C++ seam を行使している。ただし二回目も更新停止する現在の未登録挙動を正解として固定している。
  - assignment 負例は [cohort 2 test:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/orchestrator/tests/test_backoff_counterfactual_cohort2_analysis.py:254) で `inversion_realized=0` の event の bit だけを反転し、full `_load_artifact` で LCG 検査まで到達するため、別 schema 検査への誤帰属はない。
  - `test_public_certification_accepts_each_exact_cell...` と `test_cohort2_certification_is_exact...` は `_certification_contract` を直接呼ぶだけで、cohort 2 の row、group、published receipt、PBS round-trip を通さない。
- 実害: local analyzer や request gate が正しくても、producer、CMake、published group が壊れた現状を緑に見せうる。
- 提案: raw v3 terminal 0 件の emitter-to-parser-to-analyzer 正例、trace 無効かつ terminal define 欠落の compile 正例、cohort 2 の full certification group round-trip、published receipt 改変負例を追加する。

## 所見 10 — 実装後の現物から誤りと判定できる親裁定がある

- 所見: 親裁定の terminal 保証、既存挙動不変、3 unit、49 job は現物と一致しない。
- 根拠:
  - [s4-ruling.md:79](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/s4-ruling.md:79) の「1 秒の余裕」で terminal が必ず入るという裁定は、[patch C:350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2265-cohort2/patches/cicada-adaptive-counterfactual.patch:350) が count 閾値到達も要求するため誤り。
  - [s4-ruling.md:40](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/s4-ruling.md:40) の「既存 cell の挙動は変わらない」は正の `clocks_per_us_` に限れば正しいが、段 5 が [s5-unitA.md:26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/s5-unitA.md:26) で到達可能と確認した値 0 では、旧式の即時発火から新式の永久 false へ変わる。
  - [s4-ruling.md:112](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/s4-ruling.md:112) は「3 unit」としたが、現物には Unit D の 4 file が追加されている。
  - [s4-ruling.md:151](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2265-cohort2/s4-ruling.md:151) の「認証 49 job」は、実装された 2 cell x 3 workload x 8 slot からは 48 job であり、追加 1 job の実行機構は見当たらない。これは現物からの推測である。
- 実害: terminal 非閉鎖の扱い、回帰主張、投入数、所有境界の handoff が誤る。
- 提案: fix 段で裁定の後継記録を訂正する。凍結済み事前登録 bytes は変更しない。

## 総括

- 着地前に必ず直すべき所見: 1. terminal 0 件を producer から解析へ通す、2. terminal macro の trace 無効 build への漏れを除く、3. published group の exact 再検査と削除対象を閉じる、4. terminal 後の controller 停止を除く、5. cohort 1 metadata の新軸を閉じる、6. aggregate patch-stack SHA を検査する。
- 規律 1 / 2 が緩んでいるか: 規律 1 は runtime state と文字列の除去、ランタイム分岐禁止、CC-native cap の分離は保たれるが、terminal define 必須契約が trace 無効 compile 面へ漏れている。規律 2 は primary cell、extime、claim、namespace の入口では exact だが、published group receipt の再受理で緩んでいる。
- 判定不能・情報不足で結論できなかった点: pytest、build、benchmark は実走していない。実 v4 artifact が無いため、terminal 後の throughput 変化量と実際の terminal 非閉鎖頻度は判定不能。