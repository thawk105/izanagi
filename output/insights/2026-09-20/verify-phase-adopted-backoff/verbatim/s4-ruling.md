# 段 4 裁定 — 採用候補 2 genome の検証相 (設計の正本。段 A 投入前に確定。段 4 追補 §7 は計算結果の記録だけを足す)

作成 2026-09-19 22:2x JST (親)。入力 = `s1-brief.md`、`codex/s2-plan.md`、`codex/s3-consult-A.md`、`codex/s3-consult-B.md`、`refs/identity-precheck.md`。
段 4 直前の裁定 inbox 再走査: `rulings-inbox/` に本 wave の設計を変える新規裁定なし (同 arm の並行 wave = 性能退行判定、別 build・別成果物)。

## 0. 所見の裁定 (real / refuted、採否)

| # | 所見 | 裁定 | 採否・反映先 |
|---|---|---|---|
| A1 | 本 wave は S-1 (iv 付属) の充足でなく、対象を変えた準用 | real (must-fix) | 採用 → §1 位置づけ、results 稿・insight・D fragment の書き分け |
| A2 | 会計範囲・段下げ・retry 等を段 A 前に固定。「07-16 と同じ」は選択関数部分に限定 | real (must-fix) | 採用 → §3・§4 で全規則を固定、§7 は記録のみ |
| A3 | 校正未完走 (timeout/OOM) を残したまま pass へ進む境界が曖昧。択一 (停止 / 短時間側退避を新規則として pass 集合込みで明記) | real (must-fix) | **短時間側退避を新規則として採用** (§4.2)。理由: Pegasus の DRAM 上限 (約 115 GiB) は資源事実で正しさシグナルでない。停止案では read-heavy 6 s が OOM した時点で検証相が恒久に走らせられなくなる。pass 集合と未完走件数の開示を義務化して自由度を閉じる |
| A4 / B7 | identity は補完不足でなく既知の不一致。plan の「A-2 prefix 不一致なら停止」は候補を止める | real (must-fix) | 採用 → §2 期待値を実測全桁に固定、A-2 token は履歴併記 |
| A5 | trace-enabled throughput の生値保存は規律 1 に反しない | refuted (攻撃不成立) | 現状維持 → §6 (記録するが性能値として書かない) |
| A6 | 暗黙の確率主張なし。seed identity の限界は維持 | refuted | §6 の限定文に反映 |
| A7 | P2 繰延べは正当だが「完了」扱いにしない | real (should) | 採用 → §5 |
| A8 / B3 / B8 | 88 GiB・35 分等の外挿を保証にしない。超過時の会計規則を must-fix | real (should / must-fix) | 採用 → §3.3 (予算超過の扱い)、§4 hard timeout、外挿は代理値と明記 |
| B1 | dispatch CLI は成立。submit-tree は計 12 本で足りる (段 A の 6 本を段 B で再利用) | real (should) | 採用 → §8 |
| B2 | walltime 上限式 (段 A ≤ 6960 s、段 B ≤ 11580 s)、校正込みなら 4 h を超えうる | real (must-fix) | 採用 → §8 walltime、§3.1 会計範囲 |
| B4 | 保全の総量 (非圧縮 ≈ 561 GB @3 s) と圧縮時間の未計上 | real (should) | 採用 → §3.2 保全費を校正で実測し段 B 見込みに入れる、容量予約は非圧縮基準 |
| B5 | 失敗型ごとの再開規則の不足 | real (must-fix) | 採用 → §4.3 表 |
| B6 | cgroup 常時監視・page cache 測定は削る。`--max-report` 既定 20 で全 witness は載らない。`anomaly_count` は実在 | real (should) | 採用 → §6 記録項目の最小化、`anomaly_count` を総件数と断定しない |
| B1 (補) | 同一 trace の verifier 再実行は独立反復を壊さない (N = bench が生成した trace 数) | refuted (攻撃不成立) | §4.3 の再開規則の根拠 |

## 1. 位置づけ (A1)

- 本 wave は **S-1 事前登録 (iv 付属) の充足ではない**。同節の対象は系側 gate 構成 (g_rl / g_rt) である。
- 本 wave は **2026-09-19 のユーザー裁定により対象を採用候補 2 genome へ変え、S-1 (iv 付属) の反復数 (8 × 3 workload)・校正規則 ({3, 6, 10} s、verifier wall ≤ 600 s の最大値、下限 3 s)・判定規則 (全件 anomaly ゼロで pass、1 件でも anomaly で失格)・「N_verify は削らない」を準用した追加検証**である。
- 変更点の対応表 (旧 → 本 wave) を insight に置く: 対象 (g_rl/g_rt → fixed-5/fixed-10)、環境 (cygnus linux-baremetal → Pegasus gen_S)、校正条件 (rr95 × g_rl 1 本 → 2 候補 × 3 workload)、hard timeout (1200 s → 校正 3600 s / 本走 1800 s)、未完走の扱い (校正全体の失敗 → §4.2 の新規則)、記録先 (phase doc 追記 → §5)。

## 2. 対象候補と identity (A4 / B7)

| 候補 | genome (silo) | 期待 identity (`src_token` = `source_bytes_sha256`、現行 patch `a5e0710c…` 適用下、`cxx="g++"`、pin `511c9538`) | 履歴上の対応 |
|---|---|---|---|
| fixed-5 | `BACK_OFF=1, BACKOFF_FIXED=5` + `_BASE` | `678b7203aa1f9fdca4c35f9b3219d0b9662b60b22331484027adfc6c34580b12` | T-1998 v1 target と bytes 一致。A-2 rr50-fixed5 `21def77c944b1b855ea2da5516a7280858957888ec1b0644b80d9ae51e73c98a` (旧 patch) とは不一致 |
| fixed-10 | `BACK_OFF=1, BACKOFF_FIXED=10` + `_BASE` | `16c299355ba7d786534b320e99eb2a566622a3a3f9fee59c6b0886519a1a479d` | A-2 rr5-fixed10 `955b452a332d3b33cab33ea19d784da79f29b0913de179e494f62fdffeb093c9` (旧 patch) とは不一致 |

- `_BASE` = `NO_WAIT_LOCKING_IN_VALIDATION=1, NO_WAIT_OF_TICTOC=0, WAL=0`。configure の define = `-DCCBENCH_TRACE=1 -DCCBENCH_BACK_OFF=1 -DCCBENCH_BACKOFF_FIXED=<5|10> -DCCBENCH_BACKOFF_NOINLINE=0 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1 -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0`。
- runner は `checkout(PIN)` → `assert_pinned_clean` → `applied(patch)` の内側で `resolve_evidence(genome, PIN, ccbench_dir=<checkout>, cxx="g++")` を build 前と build 後に呼び、`src_token` と `source_bytes_sha256` の両方が上表の期待値と一致しなければ **fail-closed** (`stock`・別値・build 前後の不一致すべて)。期待値を観測値で更新しない。
- 旧 A-2 source (izanagi `31ec382a7` の patch) で建て直す代案は**不採用**: 当時のバイナリ同一性まで保証せず、別 build の校正・identity 確認が要る。規律 7 により A-2 の certified 記録は保持し、本 wave は現行 source の新しい事実として併記する。
- 限定文 (results 稿に入れる): 「本検証は、A-2 rr5-fixed10 で採用された固定 10 µs という設定を、現行 patch の trace-enabled build で検証した。A-2 当時とは source bytes が異なり (差分は生値 ≥ 3000 の復号分岐のみで、10 µs が選ぶ分岐は不変)、当時のソース・バイナリの再検証や過去の certified 判定の昇格を意味しない。」fixed-5 は「T-1998 v1 target と source bytes まで同一」と書く。

## 3. extime・予算の規則 (A2 / B2 / B4、段 A 前に確定)

### 3.1 会計範囲
- **「≤ 4 時間/候補」= 段 B (24 verify) の実消費**。計上量 = 候補の段 B job 6 本の dispatch `Elapse` (job 内の setup・hydrate・build・bench・数え直し・保全・verifier をすべて含む) の和。queue 待ちは含めない。
- 校正 (段 A) は別欄に累積して報告する (phase doc の内訳が「検証相校正 ≈ 0.5h」と「検証相 ≤ 4h」を別項目に置くのに合わせる)。校正と本走の和も報告する。
- 予約 walltime は実消費ではない。並列化による経過時間短縮を合計の削減として数えない。

### 3.2 校正 (段 A) の規則
- 各 (候補 c, workload w) で extime {3, 6, 10} s を昇順に各 1 回: trace-enabled bench (timeout 120 s) → C 行数え直し → trace 保全 (zstd -T0、保全時間を計時) → verifier CLI (hard timeout **3600 s**)。
- 打ち切り: verifier wall > 600 s、または verifier 未完走 (timeout / kill / rc=2 / JSON 破損)、または bench 失敗、のいずれかで **その extime 以上を打ち切り**、未実走は `not_run` + 停止理由。
- 適格集合 E_cw = { e : bench 完走 ∧ verifier 完走 ∧ verdict `serializable` ∧ certified ∧ anomaly 0 ∧ verifier wall ≤ 600 s }。判定は `s1_verify_extime_calibration.choose_extime` (純関数) に**正常完了の昇順 prefix だけ**を渡して行い、timeout 等の値を wall として渡さない。
- 候補の extime e_c = max(∩_w E_cw)。∩ が空なら「候補なし」→ 段 B を投入せず未確定として報告 (3 s へ丸めない)。
- 校正で完走した verifier に anomaly (rc=1 / non-serializable) → **当該候補は失格** (規律 2)。段 B を投入しない。
- 校正走の bench・verifier 所要 T_cw(e)、保全所要 A_cw(e)、job の setup+build 所要 F を記録する。

### 3.3 段 B 見込みと段下げ
- 見込み B̂_c(e) = Σ_w 8 × T_cw(e) + Σ_w 8 × A_cw(e) + 6 × F̂ (F̂ = 段 A 6 job の setup+build の最大値)。
- B̂_c(e_c) > 14400 s なら e_c を E の 1 段下 (10→6→3) へ移して再計算、予算内になるまで反復。3 s でも超えるなら段 B を投入せず未確定 (N_verify は削らない)。
- 段 B 投入後の実消費超過は**途中で止めない** (観測値を見た選択的な打ち切りをしない)。実消費と 14400 s の比較を報告し、超過は「計画拘束の不充足」として判定 (pass/失格/未確定) と別欄に書く。判定を変えない。
- 段 4 追補 (§7) には全校正行、E_cw、∩、初期 e、費用内訳、段下げ履歴、確定 e_c、見込み、実消費を記す。

## 4. 判定・未完走・再開の規則 (A3 / B5)

### 4.1 判定 (候補ごと)
- 判定集合 = 段 B の 24 枠 ∪ 校正で**完走した**全 verifier verdict。
- **失格**: 判定集合に anomaly (rc=1 / non-serializable) が 1 件でもある。
- **pass**: 24 枠すべてが「bench 完走・trace 保全済み・verifier 完走・verdict `serializable`・certified・`anomaly_count` 0・identity 一致」かつ判定集合に anomaly 0 かつ 24 枠に未解決の未完走 (§4.2) が無い。
- **未確定**: 上のどちらでもない (24 枠の未完走、候補なし、予算により段 B 未投入、集計不成立 (重複 rep・欠番・identity 混入) を含む)。
- 校正の未完走 (§4.2) は pass を妨げないが、**件数と保全先を必ず開示**する。「全走 anomaly ゼロ」と書かず、「判定集合 (N 件) で anomaly ゼロ、未完走 M 件 (indeterminate、trace 保全済み)」と書く。
- CLI の `indeterminate` (rc=3) は完走した CLI 出力として記録し pass にも anomaly にも数えない (再実行しない、決定的)。
- `anomaly_count` は CLI JSON の値を転記し、`--max-report` (既定 20) で切られる `anomalies` 配列長で代用しない。`total_cycles` があれば別に転記。総件数と断定しない。

### 4.2 未完走の新規則 (07-16 校正器の「timeout = 校正全体の失敗」からの意図的変更)
- 校正 verifier が hard timeout (3600 s) / kill (OOM を含む) / rc=2 / JSON 破損で完走しない → `indeterminate (operational)`、当該 extime 以上を打ち切り、完走 prefix から e_c を決める (E_cw が空でなければ段 B へ進む)。当該 trace は保全済みのまま残す (後日、より大きい記憶容量の場で検証可能)。**retry 成功で原記録を消さない。**
- 変更理由: Pegasus gen_S の DRAM 上限は資源事実で正しさシグナルでない。旧規則では read-heavy 6 s が OOM した時点で検証相全体が恒久に走らせられなくなる。
- 段 B verifier の未完走 (hard timeout 1800 s / kill / rc=2 / JSON 破損): **同一の保全済み trace** に対して verifier を 1 回だけ再実行 (別 job、hard timeout 3600 s、`verify_attempt_id` を分ける)。それでも未完走なら当該枠は `indeterminate` のまま → 候補は未確定。bench は再生成しない (N = bench が生成した trace 数)。

### 4.3 失敗型ごとの扱い (B5)
| 失敗 | 扱い |
|---|---|
| hydrate / `assert_pinned_clean` 失敗 | bench 前に停止 (rep 未着手)。環境修復後に同条件で再投入可。pin・条件は変えない |
| identity 不一致 (build 前・後) | 停止。自動 retry しない。期待値を更新しない |
| bench timeout 120 s / rc≠0 | 部分 trace を保全し `bench_failed`。同条件で新 attempt を **1 回だけ**許す (attempt-2)。失敗 attempt も台帳に残す |
| verifier rc=1 | anomaly。再実行しない。候補失格 |
| verifier rc=3 | CLI indeterminate。再実行しない |
| verifier rc=2 / JSON 破損 / timeout / kill | §4.2 |
| walltime kill | 保全済み rep は完了、未保全 rep は未着手として同条件で再投入 (完了 rep を捨てない) |
| dispatch rc=16 | receipt の reason・state history・起動証拠・rep 記録で「queue で走らなかった」「走り切れなかった」を切り分けてから未完了範囲だけ再投入。hold 中に別 tree へ逃げて二重実行しない |
- 再投入は verdict の良否で選ばない。未完了 rep だけを同じ候補・workload・extime・rep-id で継続する。

## 5. 記録先 (A7、(P2))
- `docs/phase3-main-experiment.md` は**編集しない**。理由 = `output/s1-freeze/known_axes_freeze.json` の source sha256 束縛 (`verify_document` が `FreezeError: source sha256 不一致` で赤、親が source_resolver で模擬実測、2026-09-19)、凍結文書の raw sha は `t080_freeze_migration.KNOWN_AXES_RAW_SHA256` に pin、`IZANAGI_FREEZE_HOLD` の解除はユーザー明示命令のみ。凍結再発行・hold 解除は本 wave で行わない。
- 校正確定値 (候補別 e_c、日付、校正表) は (1) insight README、(2) results 系列稿、(3) decisions fragment `{{D:verify-phase-adopted-backoff-authorization}}` に日付付きで書く。
- D fragment に「(iv 付属) の『確定値は本節へ日付付き追記』は本 wave では**未履行の繰延べ**であり、凍結束縛の解除 (ユーザー明示命令) または source 束縛の移設の裁定の後に別 wave で追記する」と明記する。完了扱いにしない。

## 6. 記録項目 (B6、規律 1・6)
- verify ごと (`result.json`): 識別 (phase / candidate / workload / extime / job-index / rep-id / bench_attempt_id / verify_attempt_id / hostname / UTC / runner sha256 / ruling sha256)、identity (genome、patch sha256、configure argv、build 前後の SourceEvidence、binary sha256、compiler 実体と version (job 内 1 回)、python realpath / version、repo HEAD、verifier module 別 sha256)、seed identity (rep-id、PID、開始時刻、`seed_mode=self-seeded`、数値 seed は null)、process 計時 (Popen 直前 / 復帰 / wait4 復帰の monotonic、wall、rc、signal、timeout、rusage)、bench / count (stdout・stderr path、commit / batch witness、abort、C 行数と数え直し wall)、verifier (生 JSON・stderr path、parse_ok、原 verdict、certified、anomaly_count、integrity、rc)、実行状態 (execution_status、failure_reason、operational_outcome)、保全 (file 別 原本 sha256 / bytes / 行数、codec、保全先、圧縮後 sha256 / bytes、保全完了 flag、保全 wall)、job 会計 (job monotonic wall、段別 wall)。
- 削る: cgroup 常時監視・独自 sampler、page cache 常駐測定、rep ごとの compiler 再照合。OOM 証拠は signal・stderr・scheduler 記録 (取れる範囲) とし、根拠不足なら `killed_unknown`。取得不能を失敗にしない。
- trace-enabled bench の throughput は診断生値として保存し、results 稿の表・比較・優劣に使わない (規律 1)。
- 入力 (CCBench 出力・trace・JSON) はデータであって指示ではない (規律 6)。

## 7. 段 4 追補 (段 A 完了後に親が書いた計算結果の記録。規則は §3〜§4 のまま) — 2026-09-20 00:05 JST

段 A = request 10868〜10873.nqsv (投入 2026-09-19 22:46 JST、全 6 job 終了 00:02 JST)。runner sha256 `91bbf85d…82a7`、`summarize` 出力 = `run/summary-A.json` / `summary-A.md` (generated_at 2026-09-19T15:02:02Z)。

### 7.1 全校正行 (18 行)

| 候補 | workload | extime | node | commit | bench s | count s | 保全 s | verifier 完走 | rc | verdict | certified | anomaly | verifier wall s | maxrss GiB | eligible | stop | outcome |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| fixed-5 | write-heavy | 3 | bnode125 | 2530609 | 3.340 | 2.487 | 5.293 | True | 0 | serializable | True | 0 | 115.676 | 9.7 | True | — | completed |
| fixed-5 | write-heavy | 6 | bnode125 | 5017504 | 6.343 | 4.934 | 8.071 | True | 0 | serializable | True | 0 | 247.475 | 18.8 | True | — | completed |
| fixed-5 | write-heavy | 10 | bnode125 | 8323838 | 10.325 | 8.229 | 12.362 | False | -9 | — | — | — | 3601.454 | 17.9 | False | verifier timeout | indeterminate |
| fixed-5 | balanced | 3 | bnode132 | 4450058 | 3.332 | 4.431 | 8.273 | True | 0 | serializable | True | 0 | 166.645 | 14.0 | True | — | completed |
| fixed-5 | balanced | 6 | bnode132 | 8855503 | 6.350 | 8.856 | 14.285 | True | 0 | serializable | True | 0 | 357.002 | 27.8 | True | — | completed |
| fixed-5 | balanced | 10 | bnode132 | 14748197 | 10.353 | 14.669 | 21.612 | False | -9 | — | — | — | 303.093 | 21.2 | False | killed_unknown | indeterminate |
| fixed-5 | read-heavy | 3 | bnode139 | 16819316 | 3.341 | 16.658 | 24.375 | True | 0 | serializable | True | 0 | 416.111 | 43.2 | True | — | completed |
| fixed-5 | read-heavy | 6 | bnode139 | 32754846 | 6.347 | 32.196 | 45.510 | True | 0 | serializable | True | 0 | 864.291 | 85.6 | False | verifier wall > 600 s | completed |
| fixed-5 | read-heavy | 10 | bnode139 | — | — | — | — | False | — | — | — | — | — | — | False | verifier wall > 600 s | not_run |
| fixed-10 | write-heavy | 3 | bnode051 | 2532560 | 3.330 | 2.474 | 5.056 | True | 0 | serializable | True | 0 | 114.098 | 9.7 | True | — | completed |
| fixed-10 | write-heavy | 6 | bnode051 | 5018742 | 6.316 | 4.921 | 8.155 | True | 0 | serializable | True | 0 | 250.556 | 18.8 | True | — | completed |
| fixed-10 | write-heavy | 10 | bnode051 | 8348584 | 10.323 | 8.204 | 12.197 | False | -9 | — | — | — | 3601.485 | 17.9 | False | verifier timeout | indeterminate |
| fixed-10 | balanced | 3 | bnode055 | 4286776 | 3.338 | 4.274 | 8.125 | True | 0 | serializable | True | 0 | 159.191 | 13.5 | True | — | completed |
| fixed-10 | balanced | 6 | bnode055 | 8604257 | 6.363 | 8.521 | 14.316 | True | 0 | serializable | True | 0 | 344.028 | 26.9 | True | — | completed |
| fixed-10 | balanced | 10 | bnode055 | 14230861 | 10.354 | 14.172 | 21.396 | False | -9 | — | — | — | 294.880 | 20.5 | False | killed_unknown | indeterminate |
| fixed-10 | read-heavy | 3 | bnode119 | 15437721 | 3.334 | 15.336 | 23.022 | True | 0 | serializable | True | 0 | 384.936 | 39.6 | True | — | completed |
| fixed-10 | read-heavy | 6 | bnode119 | 30656095 | 6.336 | 30.468 | 42.890 | True | 0 | serializable | True | 0 | 807.805 | 80.2 | False | verifier wall > 600 s | completed |
| fixed-10 | read-heavy | 10 | bnode119 | — | — | — | — | False | — | — | — | — | — | — | False | verifier wall > 600 s | not_run |

maxrss は verifier 主 process の `ru_maxrss` (parse worker 16 本の合計ではない)。commit = bench の commit witness (= C 行数え直しと一致)。

### 7.2 E_cw・∩・確定 extime
- fixed-5: E = {write-heavy {3, 6}、balanced {3, 6}、read-heavy {3}} → ∩ = {3} → **e = 3 s**。`choose_extime` の prefix 判定と一致。
- fixed-10: E = {write-heavy {3, 6}、balanced {3, 6}、read-heavy {3}} → ∩ = {3} → **e = 3 s**。
- 校正で完走した verifier verdict は候補あたり 6 件、すべて `serializable` / certified / anomaly 0 → 校正での失格なし。
- 未完走 (indeterminate、§4.2): 候補あたり 2 件 — balanced 10 s (SIGKILL、timeout でない、主 process maxrss 21.2 / 20.5 GiB、2 node で再現、per-job cgroup は無いので node memory 枯渇と整合するが証拠は signal のみ → `killed_unknown`)、write-heavy 10 s (hard timeout 3600 s、主 process の CPU 時間 520 s は 6 s 走の 824 s より少なく maxrss 17.9 GiB で頭打ち → 並列 parse の worker 側の停滞が疑われる。stderr 空)。いずれも trace は zstd で保全済み (`run/calib/<c>-<w>/extime-10/trace/`)。read-heavy 10 s は規則により未実走。

### 7.3 見込みと段下げ (§3.3)
- F̂ = 31.140 s (段 A 6 job の setup+hydrate+build の最大。build は node-local、hydrate 込み)。
- fixed-5: B̂(3) = T 5856.162 + A 303.529 + 6 F̂ 186.843 = **6346.534 s** (1.76 h) ≤ 14400 → 段下げなし。
- fixed-10: B̂(3) = T 5522.493 + A 289.629 + 6 F̂ 186.843 = **5998.965 s** (1.67 h) ≤ 14400 → 段下げなし。
- 6 s / 10 s の見込みは ∩ に無いので計算しない (null)。

### 7.4 校正の実消費 (別欄、§3.1)
- runner の job monotonic wall の和: fixed-5 6447.466 s、fixed-10 6324.867 s。dispatch Elapse (各 log の `request ID` 行と `Elapse:` 行から親が実測): 10868 = 1445 S (fixed-5 read-heavy)、10869 = 4063 S (fixed-10 write-heavy)、10870 = 955 S (fixed-5 balanced)、10871 = 4062 S (fixed-5 write-heavy)、10872 = 925 S (fixed-10 balanced)、10873 = 1351 S (fixed-10 read-heavy)。候補別の和: fixed-5 = 1445 + 955 + 4062 = 6462 S、fixed-10 = 1351 + 925 + 4063 = 6339 S (runner の job wall 和 6447.5 / 6324.9 s と整合、差は dispatch の起動・回収)。

### 7.5 段 B の投入判断
- 両候補とも `stage_B_allowed = True`。投入形 = §8 (12 job、a1〜a6 再利用 (hold 0・request 全終端を確認) + b1〜b6、extime 3、walltime 03:30:00)。

## 8. 投入形 (B1 / B2)
- runner = job dir `probe/verify_phase_runner.py` (Codex author、repo 外、sha256 で同定)。サブコマンド `selftest` (login) / `calibrate` / `verify` / `summarize`。
- 段 A: 6 job = 候補 2 × workload 3、submit-tree `a1`〜`a6` (detached、HEAD `657e1e5a7`、submodule 初期化済み)、各 job 1 node、`--walltime 02:00:00 --queue-wait-timeout 14400 --overall-grace 14400`。起動 = `<tree>/tools/pegasus/dispatch_compute.py --task generic ... -- python3.10 -B <J>/probe/verify_phase_runner.py calibrate --repo-root <tree> --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache --scratch-root /scr --output-dir <J>/run/calib/<cand>-<wl> --candidate <cand> --workload <wl>`。
- 段 B: 12 job = 候補 2 × workload 3 × job-index 2 (各 4 反復直列)、submit-tree = `a1`〜`a6` の再利用 (全 request 終端・receipt 回収・hold 解消・clean 確認後) + `b1`〜`b6` 新規、`--walltime 03:30:00 --queue-wait-timeout 14400 --overall-grace 14400`。
- runner 内の上限: setup+build ≤ 2400 s (超過は記録し停止)、bench 120 s、校正 verifier 3600 s、本走 verifier 1800 s。保全時間は計時して記録 (kill しない)。
- 投入後は各 submit-tree の `output/` 以外を書かない。単独性検査は毎 bench・毎 verifier 直前。`/scr` の空きは各 rep 前に確認し、保全完了後に前 rep の trace を削除。
- 段 5: author 1 本 (workspace-write、author worktree `-b`、`probe/` 直下に untracked で書く → 親が job dir へ退避)。親が login で `selftest`。段 6: review 2 本 (runner + 走行記録 + README・results 稿の独立検算) + 焦点 1。変異 matrix 免除 (repo 内実装面差分ゼロ)、受入全走は免除しない。

## 9. scope 外 (実装しない)
- 新 protocol・追加 gate・certification の昇格・pipeline の capability 認証への接続・凍結文書の再発行・phase doc 編集・workload 別 extime 方式・A-2 旧 source の再現 build。
