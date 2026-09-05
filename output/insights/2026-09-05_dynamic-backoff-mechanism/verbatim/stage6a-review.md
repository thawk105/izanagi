## 判定

**NO-GO** です。静的レビューで **must-fix 7 件、nit 2 件**を確認しました。特に、実診断 JSON が report generator に読めないこと、既発行 group receipt の再検証後に未束縛パスを再帰削除できることは、計測投入前に直す必要があります。

## Must-fix 1 — counter snapshot と時刻の観測点が一致していない

**位置:** [patches/cicada-adaptive-dynamic.patch:448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/patches/cicada-adaptive-dynamic.patch:448)、同 `:451-456`、[external/ccbench/include/backoff.hh:114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/external/ccbench/include/backoff.hh:114)

**指摘:** K>0 経路は `now = rdtscp()` を counter scan より前に取り、その後で全 thread の commit 数を読み、scan 前の `now` と scan 後の `sum_committed_txs` を `update_backoff_at()` に渡しています。stock は counter scan 後に `update_backoff()` 内で時刻を取るため、動的経路だけ numerator と denominator の端点が scan 時間だけずれ、scan 時間の変動が throughput gradient、trace の `window_us`、ceiling/step 遷移へ混入します。

**受理の含意:** このまま受理すると、thread 数や contention に依存する scan 時間の変動を controller の勾配として学習する可能性があります。  
**拒否の含意:** 早期 return 判定用の時刻は scan 前に維持しつつ、commit scan 後に改めて時刻を取り、その同じ時刻を check/update/trace に使う必要があります。

**成果物への影響:** certified binary の直列化判定自体は残るものの、性能選択と機序レポートを事前登録した count-window controller の効果として解釈できません。

**修正案:** `gate_now` で「経過 < update_us」を判定し、scan 後の `sample_now = rdtscp()` と `sum_committed_txs` を `check_update_backoff_at()` / `update_backoff_at()` に渡してください。leader 経路を通す driver test で、counter snapshot より後の timestamp が使われることも固定します。

## Must-fix 2 — probe と report generator の診断 schema が全面的に不一致

**位置:** [t2187_adaptive_const_probe.py:2920](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:2920)、[plot_dynamic_backoff.py:397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/plotting/plot_dynamic_backoff.py:397)、[test_plot_dynamic_backoff.py:132](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/tests/test_plot_dynamic_backoff.py:132)

**指摘:** 実 producer は `median_tps`、`trace_events`、`trace_summary`、`directional_success.successes` を出し、trigger/parity を `"count"`・`"cap"`・`"time"`、`"none"`・`"decrement"`・`"increment"` に変換します。一方 generator は `throughput_diagnostic_only`、`events`、`summary`、`directional_success.hits` と整数 trigger/parity を要求し、test fixture は producer を使わず generator 側の架空 schema を直接生成しています。

**受理の含意:** 実診断 job が正常終了しても、generator は最初の欠落 field で停止し、3 枚目の図と provenance を生成できません。  
**拒否の含意:** v2 の単一 schema を producer/consumer/test で共有し、実 producer payload をそのまま generator に渡す round-trip test が必要です。

**成果物への影響:** 必須の診断図・機序レポート・8 入力 provenance が生成不能です。

**修正案:** producer の現行 field 名を正本にするか、producer を generator 契約へ揃えてください。fixture の手書き `_diagnostic_document()` は廃止または producer helper から生成し、`none=-1` を含む parity と文字列 enum も実形式で検査します。

## Must-fix 3 — diagnostic exact bundle が空 trace と任意 rep index を受理する

**位置:** [t2187_adaptive_const_probe.py:801](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:801)、同 `:2282-2301`、[dynamic-backoff-preregistration.md:115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/docs/dynamic-backoff-preregistration.md:115)

**指摘:** `_parse_backoff_trace()` は `updates=0 retained=0 dropped=0` の summary だけでも成功し、`_validate_backoff_trace_contract()` は cells/workloads/threads/reps/extime を固定する一方で `rep_index` を固定しません。事前登録の「診断 1 job」を逸脱した複数 rep や、controller 更新が一度も観測されていない JSON が正式な diagnostic v2 として完了できます。

**受理の含意:** 都合のよい診断反復を後から選ぶことと、計装が動作していない run を診断証拠として残すことを防げません。  
**拒否の含意:** 診断は `rep_index=0` の exact 1 job に固定し、各 18 run で少なくとも 1 event、summary 整合、drop 0 を producer 側で必須にする必要があります。

**成果物への影響:** 診断台帳と機序レポートの選択規則が事前登録に閉じません。

**修正案:** exact contract に `args.rep_index == 0` を追加し、`events` が空なら `_parse_backoff_trace()` を fail-closed にしてください。

## Must-fix 4 — 既発行 group receipt の再検証が弱く、未束縛パスを削除できる

**位置:** [t2187_adaptive_const_probe.py:1990](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:1990)、同 `:2072-2121`、同 `:2140-2150`、同 `:2217-2225`

**指摘:** 新規 group 作成時は `_validated_certification_row()` を通しますが、既存 group の `_validate_published_group()` は result JSON の内容を再検証せず、row hash と一部 identity だけを比較します。さらに row の `trace_dir` を result JSON や専用 namespace に束縛しないまま、検証成功後に `_remove_group_traces()` が任意の文字列パスへ `shutil.rmtree()` を実行します。

**受理の含意:** stale・破損・改変された published receipt を complete と認め、receipt 内の任意ディレクトリを再帰削除し得ます。  
**拒否の含意:** published receipt の全必須 field と result 内容を再照合し、削除対象は新規発行時に検証済みの専用 trace root に限定する必要があります。

**成果物への影響:** certified group receipt の真偽、認証台帳、保存すべき raw trace の完全性を保証できません。

**修正案:** `_try_finalize_group()` は「既存 group が正当」と「この呼出しが新規発行した」を別の戻り値にし、trace 削除は後者だけで行ってください。削除前には canonical path が exact certify root の子であること、symlink でないこと、result JSON の `trace_directory` と一致することを再検証します。

## Must-fix 5 — `repo_head` が実際に実行した repo bytes を識別しない

**位置:** [t2187_adaptive_const_probe.pbs:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:37)、同 `:42-48`、[t2187_adaptive_const_probe.py:649](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:649)、[dynamic-backoff-preregistration.md:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/docs/dynamic-backoff-preregistration.md:150)

**指摘:** PBS と driver は `git rev-parse HEAD` の一致だけを確認し、repository の tracked-clean、probe/PBS bytes、実行 argv を記録しません。したがって probe や PBS が未 commit 編集されていても、receipt は変更前 commit の `repo_head` を記録し、事前登録 §8 の「probe/pbs の実行 argv」も満たしません。

**受理の含意:** 同一 `repo_head` で異なる driver/PBS bytes が性能・診断・認証 receipt を生成できます。  
**拒否の含意:** 実行前に対象 repo を tracked-clean と確認するか、少なくとも driver/PBS の SHA-256、dirty 状態、exact argv を receipt に束縛する必要があります。

**成果物への影響:** 全 JSON、certified group、report provenance を実際に走った実装へ一意に帰属できません。

**修正案:** PBS の prologue で `git status --porcelain --untracked-files=no` を fail-closed に検査し、driver でも再照合してください。`driver_sha256`、`pbs_sha256`、`driver_argv` を performance/diagnostic/certification/group の全 schema に追加します。

## Must-fix 6 — dynamic certification の書込み namespace と performance artifact identity が閉じていない

**位置:** [t2187_adaptive_const_probe.pbs:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.pbs:137)、同 `:154-167`、[t2187_adaptive_const_probe.py:931](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/tools/pegasus/probes/t2187_adaptive_const_probe.py:931)、同 `:1442-1474`、同 `:2304-2335`

**指摘:** dynamic cell の現在の `--out` だけは専用 prefix に制限されますが、`group_receipt_out` と 24 個の `group_result_path` は absolute であればよく、group receipt を凍結済み namespace など任意位置へ作成できます。また performance artifact は caller が渡した SHA と schema/kind/not-certified だけを確認し、同じ repo/prereg/patch stack、exact 7-cell grid、認証対象 cell の存在を検証しません。

**受理の含意:** 別 wave の performance v2 を dynamic certification に結び付けたり、dynamic group receipt を旧 evidence directory に作成したりできます。  
**拒否の含意:** certification の全 writable/read binding を用途別の dedicated root と共通 identity に閉じる必要があります。

**成果物への影響:** certified 選択、性能レポート、認証台帳の lineage が別 artifact/namespace と混在します。

**修正案:** dynamic cell では group receipt/result paths を `dynamic-backoff/certify/`、performance artifact を `dynamic-backoff/perf/` の canonical child に限定してください。performance artifact 本文も `repo_head`、`prereg_sha256`、A+B stack、exact cell/grid を再検証します。

## Must-fix 7 — M1〜M12 は「単一理由」の変異台帳になっていない

**位置:** [stage4-ruling.md:120](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-dynamic-backoff-mechanism/stage4-ruling.md:120)、[test_dynamic_backoff_transitions.py:406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/tests/test_dynamic_backoff_transitions.py:406)、[test_t2187_adaptive_const_probe.py:1403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/tests/test_t2187_adaptive_const_probe.py:1403)、[test_condition_meaning_gate.py:2390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/tests/test_condition_meaning_gate.py:2390)

**指摘:** 静的に各変異を追うと次の結果になります。

| 変異 | 静的な歯 | 判定 |
|---|---|---|
| M1 `#if`→`#ifdef` | transition の D14 test と probe の patch 静的 test の双方が赤。transition 内でも regex と `-E` が重なる | 多重理由 |
| M2 `>=K`→`>K` | `test_count_window_fires_at_k_boundary_not_k_minus_one` | 単一 |
| M3 `||`→`&&` | K exact も cap-only も false になり、K 境界 test と cap 単独 test が赤 | 多重理由 |
| M4 step 上限 clamp 削除 | step 列が `...4,8...` となり adaptive-step test が赤 | 単一 |
| M5 floor 50→0 | `floor_after=31` となり floor test が赤 | 単一 |
| M6 負勾配で ×2 | ceiling 200→400 と 62→124 の双方に効き、単調 test と floor test が赤 | 多重理由 |
| M7 K=0/cap 非0 guard 削除 | parameterized `M7-k-zero-cap-nonzero` | 単一 |
| M8 certify 3 値化 | `args.cells` literal gate、`CERT_CELLS`、`CERT_CLAIMS` の複数編集が必要。部分編集と整合編集で赤になる test が変わる | 変異未定義 |
| M9 A SHA 照合削除 | expected-A-SHA test | 単一 |
| M10 DefineSpec 1 件削除 | supply domain literal、dynamic specs/default、screening key 集合、spawn cross-product 件数が複数赤 | 多重理由 |
| M11 t→1.96 | 新 generator は shared helper を importしており、変更場所となる old literal が新 file にない。shared helper を変えれば旧 plot suite にも波及 | 変異未定義／多重 |
| M12 OUT_DIR guard 削除 | exact block 削除なら文字列存在 test が赤。ただし条件を恒偽化し error 文字列を残す同値な緩和は緑 | 意味変異を未検出 |

加えて stock 同値 test は gradient=0 の parity 例しか比較せず、K=0 の leader が counter を読まないこと、正負 gradient、ceiling 正方向倍増、更新後 ceiling への clamp 順序を固定していません。`-E` 検査も trace token の有無だけで、A 単独と B-default の前処理結果全体の一致は比較していません。

**受理の含意:** 「M1〜M12 が各 1 test・1 reason で kill される」という変異台帳を事実として発行できません。  
**拒否の含意:** old/new bytes、対象 occurrence、唯一許される failing nodeid を変異ごとに固定し、実際の mutation harness で failure set を照合する必要があります。

**成果物への影響:** 変異台帳と acceptance の「正しさ境界に歯がある」という主張が成立しません。

**修正案:** M3 は cap 項だけを無効化する変異、M6 は floor case を変えず単調 case だけを壊す変異へ再定義してください。M1/M10 は防御層が複数あることを正直に台帳へ記録し、M8/M11/M12 は exact old/new と target occurrence を先に確定します。

## Nit 1 — `static_assert` が public define surface の関係制約を閉じていない

**位置:** [patches/cicada-adaptive-dynamic.patch:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/patches/cicada-adaptive-dynamic.patch:81)、同 `:97-113`

**指摘:** 個々の非負・整数・toggle・step bounds は検査しますが、K>0 で非0 cap が `update_us` 以上であること、STEP_ADAPT 時の `kStepMin > 0`、`kStepMax * 4` の unsigned overflow は閉じていません。probe の exact 7 cell は有効値なので今回の予定成果物には直ちに発火しません。

**受理の含意:** generic Genome や将来の driver は、意味上の「最小間隔／最大間隔」が逆転した値を build まで通せます。  
**拒否の含意:** parser だけでなく C++ 側にも同じ関係制約を置くことになります。

**成果物への影響:** 今回の exact grid には影響しませんが、登録済み define の将来利用で意味の異なる binary を生成し得ます。

**修正案:** `cap==0 || cap>=update`、`!STEP_ADAPT || kStepMin>0` を追加し、`kStepMax <= 50/4` の除算形で overflow を避けてください。

## Nit 2 — 登録簿の module claim が 25 define のまま

**位置:** [condition_meaning_gate.py:12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-dynamic-backoff-mechanism/orchestrator/campaign/condition_meaning_gate.py:12)

**指摘:** 7 define の追加後、実際の supply domain と test literal は 32 件ですが、module docstring は「25 patch-derived defines」のままです。実行時 registry と `_CONDITION_DEFAULTS` の exact 集合は更新されています。

**受理の含意:** 人間が docstring を正本として読むと登録数を誗認します。  
**拒否の含意:** 説明を 32 に更新するか、変動件数を文中から除くことになります。

**成果物への影響:** certified 選択・レポート・台帳の機械判定には影響しません。

**修正案:** `25` を `32` に更新してください。

## 確認できた境界

- patch B は `#include` 行を追加しておらず、A 単独との include 列を維持しています。
- trace の field・関数・static state・文字列は数値 `#if BACKOFF_TRACE` 内にあり、`#ifdef BACKOFF_TRACE` はありません。
- `last_backoff_` は `uint64_t` のまま、代入位置、stock parity、stock clamp の文は維持されています。親の A 単独対 A+B 既定 build の命令列一致もこの確認と整合します。
- A の SHA-256 は expected literal と一致し、B SHA は `eb6669c514628686a48e837a6fd7e7c80ec40d7d2ec45c1bd99ba5c8781f18af`、ordered stack digest の定義も裁定どおりです。
- `_applied_patch_stack()` は A の context cleanup で tracked な A+B を戻し、B が A と同じ既存 2 pathだけを触ることを確認しています。
- perf/diagnostic の `nm`・`strings` 判定は subprocess failure を含め fail-closed です。certify の exact 2 cell と cell→claim 写像、新規 row/group 作成時の cell identity は維持されています。
- PBS の `+` transport、legacy 5-field の従来出力既定、dynamic current output の prefix 検査は実装されています。`bash -n` は rc=0 でした。
- 7 define の `DefineSpec`、`_CONDITION_DEFAULTS`、独立 literal test、deferred sink の owner/reason/行番号は統合 commit 時点で揃っています。`patches/ledger.json` を変更していない点も裁定どおりです。
- pytest/build/計測は依頼どおり実行していません。

## 総括

- **must-fix: 7 件**
- **nit: 2 件**
- **段3 must-fix 1〜13 のうち閉じていないもの:** **4、5、10、11、13**
  - MF4: count-window の counter/time 観測点が一致しない
  - MF5: 診断 schema が report まで閉じていない
  - MF10: published group の再検証が row/group identity を維持しない
  - MF11: group receipt 等の dynamic output namespace が閉じていない
  - MF13: M1〜M12 の単一理由・変異仕様・transition coverage が未完成
- **親裁定自身の成果物影響ありの誤り:** M3 と M6 は裁定記載の変異そのものが複数の予定 test を壊すため、「単一理由」という指定と両立しません。また段6の全緑は、producer と異なる診断 fixture を使う plot test では実運用の schema 接続を証明していません。
- **GO / NO-GO:** **NO-GO**