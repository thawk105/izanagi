# [T-2826] 受入 `pre` の worker 側 modify 複合区間 (約 45 秒) の関数別計時 — 計測は未実施: Codex の利用上限で段 5 の probe 実装が止まったため、結果を見る前の計測設計と読み方の事前登録だけを凍結して閉じる (2026-09-21)

wave `dev-wave-t2826-shard-plugin-modify-timing`。依頼の逐語は `verbatim/T-2826-origin.md`、一次資料は `output/insights/2026-09-21/t2817-acceptance-bottleneck-3/README.md` §5 (b)。
**本 wave は本題 (modify 複合区間の関数別計時) の計測値を 1 つも出していない。** 計算ノード job は投入していない。repo の実装面 (D95 決定 2) の差分はゼロ。

## 結論 (最初に読む)

1. **止まった理由:** 段 5 の Codex author 子 (probe の runner / plugin / 集計器を書く) が、観測できた model 呼出し 9 回 (receipt の `model_calls_semantics=observed_token_count_events`、実数はこれを上回りうる)・514 秒の時点で Codex の利用上限により終了した (`codex_exit_code=1`、`failure_class=f45_missing_output`、出力 0 byte)。停止本文は逐語で `You’ve hit your usage limit. ... try again at Sep 26th, 2026 7:35 PM.` (`verbatim/s5-author-stop-evidence.md`)。入口の凍結境界 (`.claude/commands/dev-wave.md`) と `docs/ai-provenance.md` (Codex が実行不能なら Claude は代行せず停止) により親は probe を代行せず、従量経路へも切り替えない。D582 に従いユーザーへ端末通知を送り (携帯への push は Remote Control 無効で未送信。送信時刻は前後の `date` 実測 14:34:32 と 14:36:47 JST の間)、自動の再投入はしていない。
2. **残したもの:** 段 1 brief (`verbatim/s1-brief.md`)、段 3 の read-only 相談 (`verbatim/s3-consult-prompt.md` / `s3-consult-out.md`)、段 4 裁定 (`verbatim/s4-ruling.md`)。**段 4 裁定 §3 (計測設計 v2) と §4 (読み方 R1〜R8) は計算ノード job を 1 本も投げる前に確定した事前登録**であり、再開する wave は段 4 でこれを変えずに採り直す (§6)。段 5 の author prompt (`verbatim/s5-author-prompt.md`) は再開時の雛形になるが、wave 固有の値 (子 worktree の path と branch、既定の出力先、仕様 file の置き場、tip が進んでいれば行番号) の差し替えが要る。
3. **書きかけの probe:** 子 worktree に書きかけの 3 file (計 1,292 行) が残り、起動器が終端 commit `31894443e` (branch `author-t2826-probe`) にした。子は検査も報告もしていないので**未検査**。repo へは入れず wave 専用 dir `partial-author/` に退避した (§5)。
4. **再開の手順:** Codex が使える状態になってから (上限の解除表示は 2026-09-26 19:35、またはユーザーがアカウントを切り替えた後)、fresh な wave で段 4 から再開し (本裁定 §3 / §4 を変えずに採り直す)、段 5 へ進む (§6)。

## 1. 依頼と scope

- 依頼 (起動引数の要点): 受入 `pre` の worker 側 45 秒 (shard plugin を載せた段の modify 複合区間、process 群の sys +2027 秒、Lustre `intent_lock` 11.7 倍) を関数別に計時する。対象 = `tools/acceptance_shards.py` の `records_from_items` / `_canonical_item` の `Path.resolve()` (全 item に 2 回) / `allocate` / 選択、conftest の `_validate_real_repo_shard_state`。T-2817 の S2 / S3 形の段階載せで内訳を閉じ、`pre` ≈ max(worker 側, 早期 memo prewarm 44〜54 秒) の構造を事前登録し、worker 側の短縮量と `pre` の変化を別々に測る。短縮の実装は含めない (D1936 項 35)。probe は job dir、Codex author。T-2825 と比較測定の区間を重ねない。標本の時点を固定。
- 起票時の本文 (entry 1777) は縮約方式の設計と実受入の隣接対まで含むが、起動引数は「短縮の実装は含めない」「本題の計測だけ」で、それらは本 wave の外 (`verbatim/T-2826-origin.md` §3)。
- 標本の時点: 本 wave は計測 tip = wave 基点 `d99c556df` (開始 gate の時点の local main)、as-of = 開始 gate の時刻 2026-09-21 14:08:04 JST (`verbatim/s1-brief.md` 1 行目。gate の出力 `verbatim/startup-gate.log` は時刻を含まない) と定めた。計測に使われていないので再開 wave へは引き継がず、再開 wave の開始 gate で改めて固定する (§6)。

## 2. brief 前の前提実測 (段 4 裁定 §2 の訂正後)

- N1. T-2817 の計測 tip `2afb39768` → `d99c556df` で `tools/acceptance_shards.py`・`orchestrator/tests/conftest.py`・`tools/run_tests.py` の差分は 0 行、所要台帳 `orchestrator/tests/acceptance_duration_ledger.json` だけ +434 行 (`b820bbaa7`)。`allocate` は台帳の値を重みに使うので shard-0 の選択集合は**変わり得る** (変わったかは集合照合で見る。本 wave では見ていない)。
- N2. python3.10 の `Path.resolve()` は `os.path.realpath` (path の component ごとに `lstat`) の後に `stat` を 1 回呼ぶ。受入 worktree の test path は 11 component。「1 回約 12 metadata syscall」は通常の component 経路の概算で、Lustre の RPC 数・`intent_lock` 数とは対応づけない。`orchestrator/tests/` の test file は 369 本。
- N3. 早期 memo prewarm は controller の thread で走り (最初の `pytest_configure_node` 起点)、worker は conftest の `pytest_collection_finish` の中の `_wait_early_memo_job` で待つ。memo cache は cell の node-local TMPDIR にあり、待ちには flock の再試行が含まれうる (段 3 所見 7)。T-2817 は memo の公開時刻を直接測っていない (`receipt_memo_s` のみ)。
- N4. 既存値 (条件が異なる既存観測として引用する。食い違いとは呼ばない): T-2817 (計算ノード 48 worker) の S2 worker modify median 45.66 / 45.55 秒、S3 44.68 / 44.79 秒、process 群の sys 80 → 2108 秒、`intent_lock` 5.2 M → 60.9 M; T-2617 §3.2 (login 単独 process) の plugin あり − なし = user CPU +1.74 秒 (sys 1.37 → 3.09 秒)。
- N5. T-2825 は 13:55 JST 時点で比較測定 (7 走) を終え、最終受入 → land の段にあった (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2825-ledger-refresh-ab/handoff.md`)。本 wave は計測をしていないので区間の重なりは生じていない。
- 付随の観測: 計算ノード job の準備として wave 木の pyc を login で温めた (`python3 tools/run_tests.py orchestrator/tests --collect-only -q -p no:cacheprovider`、14:25:10〜14:26:34 JST、rc 0、`27033 tests collected in 57.34s`、pyc 784 / pytest 書換え 370; `verbatim/pyc-warm-wave.times`、`pyc-warm-wave.log.tail`)。collection 件数は T-2817 の 26,407 と同じ条件の比較ではない (login・単独 process・別 tip)。

## 3. 段 3 相談の所見と段 4 の裁定

相談 1 本 (codex gpt-6-astra / medium / read-only、lane sol、2 レンズを 1 本; rc 0、`check_codex_output.py` rc 0)。所見 9 件 (高 4・中 5)、**全件 real・採用、refuted 0**、判定「修正後 GO」。高 4 件:

1. 閉包式が入れ子の関数時間を二重に数え、符号付き残差の基準では誤った分解も通る → 加算は排他的な葉だけ、inclusive は別掲、`median(|残差|)`、W_w を決めた worker の残差も併記 (裁定 §4 R1)。
2. 短縮量 `S3-u − S3-cf` に計器の差が混ざる → 主比較を同計器の `S3-f − S3-cf` に替え、S3-u は観測者効果の対照だけにする (裁定 §3・§4 R3 / R5)。
3. memo の公開時刻を thread の終了で代用し、ε ≤ 2 秒を既知の上限としていた → receipt / oracle の各 prewarm の正常復帰 (直後に `.pending` が unlink される) を公開の近似とし、ε は符号付きの実測残差、2 秒は適合判定の閾値にする (裁定 §3 C・§4 R6)。
4. 雛形の有効セル判定 (`complete` と JUnit の存在だけ) では失敗セルから結論を出せる → rc、計時点の欠け、collection 不一致、error、集合照合を条件に入れる (裁定 §3)。

中 5 件 (`os.times()` の帰属過剰 → 大区間の `RUSAGE_THREAD`、memo 化の同値の限定と照合手段、poll の Lustre 負荷の断定の撤回、外乱検知の区間照合、新事実の読みの限定) も全件採用。反実仮想セル (probe 内だけで resolve を memo 化する条件) は相談の「(c) 条件付きで scope 内」を採った。条件と詳細は `verbatim/s4-ruling.md` §1。

## 4. 計測設計 v2 と読み方の事前登録 (結果を見る前に確定、`verbatim/s4-ruling.md` §3 / §4 が正本)

- 計算ノード 1 job・1 node・同 checkout で 11 セル: `warm` → `S1-a S2f-a S3u-a S3f-a S3cf-a` → `S3cf-b S3f-b S3u-b S2f-b S1-b` (順序反転)。S1 = shard plugin なし、S2f = S2 + 関数計時、S3u = 受入 argv 形 + 共通計時だけ、S3f = S3 + 関数計時、S3cf = S3f + resolve の memo 化 (固定した collection 中の、成功した実 resolve 結果の再利用)。
- 計時点: A = T-2817 の計器、C = 早期 memo の各 prewarm の開始・正常復帰と worker の待ちの入口・出口 (全 xdist セル共通)、B = modifyitems の全 impl を `HookImpl.function` の委譲差し替えで囲み、conftest の wrapper は前段・後段に分け、shard plugin の helper と `Path.resolve` (`_canonical_item` 実行中だけ) を委譲 wrapper で包む排他的な葉 (f / cf セル)。
- 読み方: R1 閉包 (`median(|残差|)` ≤ max(2 秒, 5 %))、R2 帰属 (「主因」は有効な f セル 4 つすべてで share ≥ 0.5 のときだけ)、R3 観測者効果 (S3u vs S3f の 3 量が 2 秒以内)、R4 反実仮想の集合同値 (worker payload の両 digest、gw0 の records / selected、report の `observed_universe` / `selected`)、R5 主比較 (ΔW・Δmodify・Δpre・ΔM を別々に)、R6 `pre` ≈ max(W_w, M) の適合と S3cf の予測、R7 Lustre・CPU の記述、R8 外乱 (他 wave の受入の collection 区間との照合)。
- 変異 matrix: repo の実装面差分がゼロなので免除 (DW-S04)。

## 5. 停止の事実と書きかけの probe

- 段 5 は子 worktree `author-t2826-probe` (基点 `d99c556df`、`git worktree lock` 済み) で起動した。投入直前の midflight gate は 1 回目が submodule 未初期化で rc 1 (`verbatim/s5-midflight-gate.log`)、`tools/dev_wave_submodule_init.py` で初期化した後の 2 回目が rc 0 (`verbatim/s5-midflight-gate-2.log`)。
- 子は 14:24 JST 頃に起動し、14:33 JST に上記の利用上限で終了した。起動器は子 worktree の残差を終端 commit `31894443efd6c662f9e257d1055a0da0d15ca375` にし、待ち手は `stage=producer-files rc=70` を返した。証拠の逐語と 3 file の sha256 は `verbatim/s5-author-stop-evidence.md`。
- 書きかけの 3 file は子が検査・報告をしていないので、動くかどうか、裁定 §3 を満たすかどうかは分からない。**再開 wave は参考資料としてだけ渡し、完成物として扱わない。** 原本は wave 専用 dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2826-shard-plugin-modify-timing/partial-author/`、branch の履歴は段 9 の撤去で evidence bundle へ退避される。

## 6. 再開の手順 (Codex が使える状態になってから)

1. local main から fresh worktree を切り、submodule を初期化し、開始 gate を打つ。標本の時点 (計測 tip と as-of) は**再開 wave の開始 gate で改めて固定する** (本 wave の `d99c556df` / 14:08:04 は計測に使われていない)。
2. 入口の「裁定後に別 context が段 4 から再開する型」(前 wave の段 2・3 成果物を流用でき、再検査は段 6 レビューへ寄せる) に当たる。段 3 相談を流用し、段 4 で本 insight の `verbatim/s4-ruling.md` §3 / §4 を変えずに採り直してから段 5 へ進む。tip の差で N1 の前提 (対象 3 file の差分 0 行) が崩れていたら段 1 から。
3. 段 5 の prompt は `verbatim/s5-author-prompt.md` を雛形にし、wave 固有の値 (子 worktree の path と branch、必読資料と仕様 file の置き場、既定の出力先 `OUT_ROOT`、tip が進んでいれば `acceptance_shards.py` / `conftest.py` の行番号) を差し替え、書きかけ file の所在 (参考資料・未検査) を足す。新しい `--job-id` を付けて投入する (`--job-id` を省くと `tools/dev_wave_codex.py` が wave 名と prompt の sha256 から id を作る)。
4. login の生死確認 (`T2826_WORKERS=2`・全収集) → 計算ノード job 1 本 → 集計 → README → 段 6 review 1 本 → 受入 → land。

## 7. 限界・言わないこと

- 本題の計測値は 1 つも無い (§2 の付随の観測は pyc の温めの記録だけ)。modify 複合区間の内訳、`Path.resolve()` の寄与、`pre` の構造 (max の式) の成否について、本 wave は何も主張しない。T-2817 の「有力な解釈」は解釈のまま。
- 独立の敵対検査を受けたのは段 1 brief (段 3 相談) だけである。段 4 裁定と段 5 prompt は相談の所見を反映して親が書いたもので、その後の独立検査は受けていない (段 6 review が走っていない)。本 insight と worklog fragment は段 7 で Claude の read-only 子 1 本 (opus) の事実照合を受け、所見 13 件 (must-fix 2 = 再開手順の文言、should 2、nit 9) をすべて real と裁定して反映した。数値・hash・逐語・件数の不一致は 0 件だった (`verbatim/s7-review-out.md`)。
- 「Sep 26th, 2026 7:35 PM」は Codex の表示をそのまま写したもので、時間帯の表記は無い。F411 の取り消し追記 (2026-08-20、D582) のとおり、アカウント切替でそれより早く使える場合がある。表示どおりに復帰するかは確かめていない。
- T-2617 §4 の判定 (resolve の字句化は不可、2 回目の置換は採らない) と T-2817 の値は無効化しない (規律 7)。

## 8. この dir の中身

- `README.md` — 本文。
- `verbatim/T-2826-origin.md` — 依頼の逐語 (起動引数と起票本文) と両者の差。
- `verbatim/s1-brief.md` — 段 1 brief (N1〜N5 と (P1)〜(P5) の原文。訂正は裁定 §2)。
- `verbatim/s3-consult-prompt.md` / `s3-consult-out.md` — 段 3 相談の prompt と出力 (出力は行末空白 42 行を可逆に除いた写し。原文 hash・行番号・復元法は `verbatim/trailing-whitespace-normalization.md`)。
- `verbatim/s4-ruling.md` — 段 4 裁定 (§1 所見の裁定、§2 brief の訂正、§3 計測設計 v2、§4 読み方の事前登録、§5 変異・受入、§7 追補 1 = Codex 不可用による再裁定、§6 scope 外)。
- `verbatim/s5-author-prompt.md` — 段 5 author 子への prompt。
- `verbatim/s5-author-stop-evidence.md` — 停止の証拠 (receipt・events・log の逐語、書きかけ 3 file の sha256)。
- `verbatim/startup-gate.log`、`s5-midflight-gate.log`、`s5-midflight-gate-2.log` — gate の出力。
- `verbatim/pyc-warm-wave.times`、`pyc-warm-wave.log.tail` — pyc の温めの記録。
- `verbatim/trailing-whitespace-normalization.md` — 逐語の行末空白の可逆正規化の記録 (DW-S07)。
- `verbatim/s7-review-out.md` — 段 7 の事実照合 (Claude opus、read-only 子 1 本) の報告の逐語。
