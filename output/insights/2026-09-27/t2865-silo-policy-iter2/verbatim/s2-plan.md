## 修正の形の比較と推奨

**推奨は (i)、既存の `transaction.cc` hunk 内で `TxExecutor::begin()` が初回だけ seed を設定する形**です。[骨格 patch](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/patches/silo-function-policy-variant.patch:74) の `thread_local random_state` を未初期化の印を持つ状態に変え、`thid_` から決定的な splitmix64 系の値を作ります。値が 0 なら固定の非 0 値を使い、以後の `begin()` では再設定しません。`begin()` には既に variant 側の分岐があり、`thid_` は executor のメンバーです。worker は `make_tx(thid, …)` により executor を構築します（[transaction.hh:45,68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/external/ccbench/cc/silo/include/transaction.hh:68)、[runner.hh:172–193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/external/ccbench/common/runner.hh:172)、[ycsb_silo.cc:33–38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/external/ccbench/cc/silo/ycsb_silo.cc:33)）。

| 案 | touch set と波及 | 再現性・判定 |
|---|---|---|
| (i) `begin()` で初回 seed | patch の既存 2 file のまま。`axis_silo_function_policy.py` の定数、template の touch set 期待値は維持 | 同じ `thid` と呼出し回数なら同じ系列。推奨 |
| (ii) constructor で seed | `cc/silo/include/transaction.hh` が patch の 3 file 目になる。[template test:79–84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/tests/test_silo_function_policy_template.py:79) の期待と patch の適用範囲を変更する必要がある | 決定的だが変更が広い |
| (iii) TLS address／`std::thread::id` の hash | 2 file に収められる可能性はある | 実行間の系列を保証できず不採用 |

(i) は seed 処理を `#if SILO_POLICY_VARIANT` 内に置き、stock 側のソース bytes を変えません。EVOLVE-BLOCK の hole、API header、受理契約、`after_abort`・`on_lock_conflict`・`on_commit` の呼出し点、1000 µs／50 µs／32 周回の上限も変更しません（[patch:42–110,119–136,152–177,230–236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/patches/silo-function-policy-variant.patch:42)、[axis:11–13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/axis_silo_function_policy.py:11)）。`TRACE` に依存しない分岐なので trace build と perf build で同じ seed 規則です。原型 stock 評価は patch を適用せず、方策 flag も除きます（[run_stock_control:369–383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/p3_s4_loop_policy.py:369)）。既存 template test も variant=0 の source token が `STOCK` であることを検査しています（[test:241–262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/tests/test_silo_function_policy_template.py:241)）。

## 変更アンカー表

| 担当 | file:line | 変更内容・依存 |
|---|---|---|
| Codex author | [patch:74–86,128–137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/patches/silo-function-policy-variant.patch:74) | TLS の初回 seed 関数と `begin()` 呼出しを追加。先頭 hunk の追加行数を数え直し、後続 hunk の新側開始行を同じ増分だけ更新する。 |
| Codex author | [test_silo_function_policy_template.py:36–51,201–239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/tests/test_silo_function_policy_template.py:36) | 実 patch を pinned source に適用する既存 fixture を使い、seed の worker ID 束縛と挙動を検査する。 |
| 親 | [runbook:65–143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/docs/phase3-silo-policy-runbook.md:65) | 系列 B の予算、critic 入力、条件記録を追記。実装後の確定値を反映する。 |
| 親 | [段階 F insight:3.4](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/output/insights/2026-09-27/t2865-silo-policy-stage-f/README.md) を参照する新 insight | A/B の HEAD、submit checkout、骨格 patch SHA-256、各 iteration の pair と critic、計算量を記録する。 |

patch は現在 2 file、`transaction.cc` の先頭 hunk が `@@ -8,6 +8,88 @@` です（[patch:1–26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/patches/silo-function-policy-variant.patch:1)）。追加行数を `N` とすれば `+8,88+N` とし、以降の新側開始行に `N` を加えます。author は最終 patch に対し pinned CCBench clone 上で `git apply --check` と実適用を確認します。**この plan 段階では修正も適用検査も未実施**です。

patch の利用箇所は、実適用する [driver:404,499,623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/p3_s4_loop_policy.py:404) と [coverage:568,625–626](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/silo_policy_coverage.py:568)、bytes と touch set を読む [template test:22,79–84](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/tests/test_silo_function_policy_template.py:22)、hole 本文を読む [compile test:48–58](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/tests/test_silo_policy_compile.py:48) と [grammar test:42–45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/tests/test_silo_policy_grammar.py:42)、path と inert 値を持つ [condition meaning gate:80–85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/condition_meaning_gate.py:80) です。案 (i) なら定数・hole 抽出・touch set の期待値変更は不要です。coverage の既存記録には旧 patch SHA-256 が残りますが（[coverage JSON:10559](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/output/env/pegasus/calibration/silo_function_policy_coverage.json:10559)）、driver はその記録を照合しません。併用する probe／broken patch は同じ `transaction.cc` の文脈に当たるため、author の適用確認対象に含めます。

## test と変異の事前登録候補

最小集合は次の二つです。

1. [template test の実 patch 適用 fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/tests/test_silo_function_policy_template.py:36) から生成した source の**実際の seed 関数と `next_random()`**を小さい単独 TU に取り込み、異なる二つの worker `thid` の初回値が異なること、同じ `thid` で再実行すると一致すること、`begin()` 相当の再呼出しで系列が巻き戻らないことを確認する。テスト自身が計算した seed 同士だけを比較しない。
2. 同じ実適用 fixture で、`begin()` の variant 分岐が `thid_` を渡して初回 seed を呼ぶこと、variant=0 の stock token、API bytes、hole、上限と hook の既存検査を実行する（[template test:79–139,201–262](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/tests/test_silo_function_policy_template.py:79)）。

[既存 compile test:31–45](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/tests/test_silo_policy_compile.py:31) の `compile_policy` は候補の *hole 本文*を単独 TU で検査する手段なので、hole 外の骨格 seed の動作検査にはそのまま流用できません。コンパイラ選択と一時 TU 実行の方式は参考になります。login node で CCBench 本体は build しません。既存テストの数値期待値を変える理由はありません。

| 変異 | 壊す箇所 | 落ちる test・単一理由 |
|---|---|---|
| M1 | seed の `thid_` を固定 0 にする | 二つの `thid` の初回値比較。worker 差だけを消す。 |
| M2 | 初回限定の印を外し、毎 `begin()` で再 seed | 再呼出し後の系列継続。巻戻しだけを起こす。 |
| M3 | `begin()` の seed 呼出しを削る | `begin()` 束縛検査と実 seed 動作。実経路から切り離す。 |
| M4 | 0 の代替処理を削る | seed 関数の非 0 契約検査。0 状態の永久固定だけを起こす。 |

## P1〜P5 の判定 (real / refuted / 要修正、根拠 file:line)

| 暫定案 | 判定 | 根拠と裁定案 |
|---|---|---|
| **P1** 旧 A を budget-walltime で閉じ、新 B を始める | **real** | 旧 `loop_state.json` は `iteration=1`、`start_wall=1790494325.7026846`。`MAX_WALLTIME_S=3600`（[loop:187–189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/p3_s4_loop.py:187)）経過後、`drive_iteration` は増分前に `check_stop` して `stopped-before` を返す（[policy driver:444–452](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/p3_s4_loop_policy.py:444)、[check_stop:1372–1382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/p3_s4_loop.py:1372)）。D2256 項 3 の停止条件は予算のみ。旧 state と定数は編集しない。 |
| **P2** seed を直す | **要修正** | 修正自体は妥当。ただし constructor 案は header を touch set に足す。`begin()` 案なら既存 2 file に収まる（[patch:128–137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/patches/silo-function-policy-variant.patch:128)）。 |
| **P3** A の bootstrap 2 scalar を B の初回に再使用し、bootstrap stock job を省く | **要修正** | stock *build* は原型 source で同一（[policy driver:369–383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/p3_s4_loop_policy.py:369)）。しかし B の初回 coder 入力に A の実測値を使うと条件が混ざる。B 用 bootstrap stock を新 checkout の別 campaign で取り、以後は直前 pair の stock を使う（[runbook §1(0)](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/docs/phase3-silo-policy-runbook.md:65)）。各 iteration の同 job stock は維持する。 |
| **P4** campaign identity は変えず checkout と insight で区別 | **要修正** | identity の preimage に patch bytes／superproject HEAD は無い（[ident:195–235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/ident.py:195)、[policy cfg:128–143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/p3_s4_loop_policy.py:128)）。A/B は別 checkout の `output/` に同じ campaign ID の directory を持ち得る。一方、候補の preprocessed source は `src_token` に入り、WAL の `BUILD_START`、variant ID、build cache key は変更を反映する（[source_digest:2325–2335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/source_digest.py:2325)、[pipeline:141–147,1984–2000](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/pipeline.py:141)、[buildcache:625–645](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/buildcache.py:625)）。**生の patch bytes は直接 identity に入らず**、stock の `src_token` は従来どおり `stock`。checkout と patch SHA-256 を insight に明記し、campaign dir を共有・合算しない。 |
| **P5** critic に B の digest 本文だけを渡す | **要修正** | 段階 F の実 digest には候補の throughput・abort 率と verify abort 率がある一方、候補コード、同 job stock、設計選択間の差、LLC/IPC の実値がありません。したがって「どの設計選択が効いたか」という [critic role:9,24–37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/.claude/agents/critic.md:9) の帰属を digest だけからは断定できません。B の自系列 digest に、当該 iteration の候補実装（justification を除く）と同 job stock 結果だけを添え、欠測は `uncertainty` に書かせる案を推奨します。`--critic-output` は入力本文をそのまま渡すのでなく、[policy driver:581–586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/p3_s4_loop_policy.py:581) が [4 個の exact な H2 見出し](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/agent_outputs.py:36) を抜き、SHA-256 と境界を加えた 6 文字列 field に変換します（[loop:1267–1289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/p3_s4_loop.py:1267)）。role 本文は変更しない。 |

## 系列 B の実走手順と見積り

1. seed patch と test を commit した **その HEAD** から、段階 F の [`make-submit-tree.sh`](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-stage-f/make-submit-tree.sh) と同じ手順で、AI worktree 外に新しい detached submit checkout を 1 本作る。B 用 job dir／tree 名に変え、submodule 初期化、pinned-clean 確認、third-party hydrate、worktree lock を行う。段階 F の `trees/e2e` とその `output/` は使わない。投入 script も B 用 evidence／archive root に変更し、`EXPECTED_HEAD` は B の commit を指す（[submit-policy.sh](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2865-stage-f/submit-policy.sh)、[runbook §0.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/docs/phase3-silo-policy-runbook.md:22)）。
2. B 専用 bootstrap stock job を 1 回取り、`fitness_tps` と `abort_rate_pct` を初回 (a) に使う。以後は直前 pair の stock 値を使う。
3. 各 iteration は runbook §1 の (a) `--campaign-env pegasus --emit-coder-input`、(b) C++ coder、(c) preview／必要なら record-reject、(d) auditor（閉じた出力形を prompt に明記）、(e) `{coder,auditor}` proposal、(f) pair job、(g) 停止判定と critic の順。2 回目以降の (a) に直前 critic の file を `--critic-output` で渡す（[runbook §1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/docs/phase3-silo-policy-runbook.md:55)）。
4. pair は実測 Elapse 765 秒。PBS 要求は前処理と変動を含め **`elapstim_req=00:30:00`** を計画値とし、実際の Elapse で計算量を記録する。trace は各 job に異なる repo 外の `IZANAGI_TRACE_ARCHIVE_ROOT` を渡し、candidate と stock の inventory を保全する（[runbook §3.2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/docs/phase3-silo-policy-runbook.md:156)）。

3600 秒の起点は初回の `drive_iteration` が作る `LoopState(start_wall=time.time())` です。preview／emit は作らず、先行する `record-reject` は作ります（[policy driver:444–452,490–515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2865-iter2/orchestrator/campaign/p3_s4_loop_policy.py:444)）。pair 765 秒と LLM 約 6〜8 分なら 1 回約 1125〜1245 秒なので、queue・操作時間を除いても **2〜3 iteration が現実的**です。brief の「最大 4」はこの単価では成立しません。停止前に残予算を確認し、足りなければ投入せず記録します。

3 pair の実測単価は `3×765=2295` 秒、**0.64 node 時間**。B bootstrap の段階 F 単価 300 秒を加えると **0.72 node 時間**です。4 pair なら bootstrap 込み **0.93 node 時間**ですが、walltime 予算上は見込まない。検査 job を含む総見積りを投入直前に更新し、2 node 時間以上となる場合は依頼どおり親がユーザー確認を取ります。

## runbook 追記案

- §0／§3: `MAX_WALLTIME_S=3600`、起点は初回 `loop_state` 作成。765 秒 pair と LLM 6〜8 分では系列あたり通常 2〜3 iteration と明記し、投入前に残予算を見る。
- §1(0): 骨格変更後の新系列 B は専用 checkout の別 bootstrap stock を測る。A の値を B 初回の入力に流用しない。
- §1(g): critic には **B の当該 campaign** の digest、当該候補実装（justification を除く）、同 job stock 結果だけを渡す。ほかの campaign、偵察、小比較、再測は読ませない。出力は `## attribution`、`## recommend`、`## avoid`、`## uncertainty` を各 1 回、exact な H2 見出しで要求し、欠測による帰属不能を明記させる。
- §3: A/B それぞれの submit checkout、HEAD、骨格 patch SHA-256 と campaign dir を insight に記録する。同じ campaign ID でも checkout を跨ぐ結果を同一系列として扱わない。

## 未確定点 (親の裁定が要るもの)

- **P3:** B 専用 bootstrap stock を取る案。追加単価は段階 F 実測で約 300 秒です。
- **P5:** critic に B 自系列の候補実装と同 job stock 結果を添える案。digest のみでは方策の設計選択への帰属ができません。

## 総括

推奨実装は、既存 patch の `begin()` で `thid_` 由来の seed を初回だけ設定する 2 file 内の修正です。旧 A は walltime 予算で終了し、修正 commit の新 submit checkout で B を始めます。B は専用 bootstrap と各 iteration の pair stock を取り、現実的な見込みは 2〜3 iteration です。親には P3 の bootstrap 再測と P5 の critic 入力範囲の裁定を求めます。