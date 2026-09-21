# 段 4 裁定 — [T-2826] (2026-09-21 14:2x JST、計算ノード job の結果を見る前に確定)

入力: 段 1 brief `s1-brief.md`、段 3 相談 `codex/s3-consult-out.md` (codex gpt-6-astra / medium / read-only、lane sol、rc 0、`check_codex_output.py` rc 0)。
裁定 inbox の再走査 (14:2x): wave 開始 (14:03) 後の更新なし。第 29 回 (13:34) の項 10「非帰属の赤 3 件の test 競走は既存の受入律速診断へ渡す」は渡し先を特定せず、test 実行中の競走で collection 期の本件と主題が別 — ユーザー起動引数「本題の計測だけ」に従い本 wave へ取り込まない。

## §1 所見の裁定 (9 件、全件 real・採用、refuted 0)

| # | 重大度 | 裁定 | 反映先 |
|---|---|---|---|
| 1 閉包式の二重計上・符号付き残差 | 高 | real・採用 | §4 R1 (排他的な葉だけを加算、inclusive は別掲、`median(|残差|)`、全 worker と W_w を決めた worker の残差を併記。2 秒 / 5 % は診断上の許容値で精度保証と呼ばない) |
| 2 短縮量に計器差が混ざる | 高 | real・採用 | §3 (主比較 = 同計器の S3-f − S3-cf、S3-u は観測者効果の対照だけ、公開・待ちの境界は全セル共通) |
| 3 memo の公開時刻と ε | 高 | real・採用 | §3 計時点 C (endpoint の prewarm 復帰 = 公開の近似、barrier 終了は別)、§4 R6 (ε は符号付き実測残差、2 秒は適合判定の閾値) |
| 4 有効セル判定 | 高 | real・採用 | §3 有効セル条件 |
| 5 `os.times()` の帰属過剰 | 中 | real・採用 | §3 計時点 B (大区間の境界で `RUSAGE_THREAD`、process CPU は別列、per-call の CPU syscall なし) |
| 6 memo 化の同値の限定と照合手段 | 中 | real・採用 | §3 反実仮想 (「固定した collection 中の、成功した実 resolve 結果の再利用」)、§4 R4 |
| 7 poll の Lustre 負荷の断定は不可 | 中 | real・採用 (brief と相談 prompt の記述を撤回) | §3 (TMPDIR と memo path の配置を各セルで記録)、§4 R6 (M の変化原因は識別しない) |
| 8 外乱の検知 | 中 | real・採用 | §4 R8 |
| 9 新事実の読みの限定 | 中 | real・採用 | §2 |

反実仮想セルの判定: 相談の **(c) 条件付きで scope 内** を採る。条件 = probe 内の 1 条件の診断に限る、縮約方式の採用・恒久実装・一般的同値性の主張へ進まない、測定は同計器の S3-f / S3-cf、集合一致と実 resolve への委譲を維持、T-2617 §4 の字句化とは別物で既裁定の撤回を提案しない。満たせなければ関数時間は「観測費用」としてだけ報告し、依頼の「別々に測る」は未達と書く。

## §2 brief の訂正 (所見 7・9)

- 「単独 process 値と 48 並列値の食い違い」→ **条件が異なる既存観測** (T-2617 = login 単独 process、T-2817 = 計算ノード 48 worker)。
- N2 の「約 12 metadata syscall」は通常の component 経路の概算で、Lustre RPC 数・`intent_lock` 数と対応づけない。
- N1 の ledger 変更は選択集合が**変わり得る**根拠で、変わったかは集合照合で見る。
- 「48 worker の `.pending` poll が Lustre 負荷を足す」は撤回 (memo cache は cell の node-local TMPDIR、待ちは flock 再試行を含む)。
- 新しく測ると言える量 = 同一 tip・48 worker の関数内訳 (排他的な葉)、resolve の回数と wall、計装下の条件差 (S3-f − S3-cf)、memo の公開時刻と worker の待ち。開始 gate の as-of (14:08:04) と各 cell の実行時刻は分けて書く。T-2825 land 後の別 tip の最終受入は参考観測。旧値・旧裁定は無効化しない。

## §3 プラン v2 — 計算ノード 1 job (1 node、同 checkout = wave 木 `d99c556df`、walltime 00:40:00)

**セル (11) と順序:** `warm` (温めだけ、比較に使わない) → a: `S1-a`, `S2f-a`, `S3u-a`, `S3f-a`, `S3cf-a` → b: `S3cf-b`, `S3f-b`, `S3u-b`, `S2f-b`, `S1-b`。
- `S1` = T-2817 S1 (xdist `-n 48 --dist loadgroup --no-loadscope-reorder`、shard plugin なし)。同 tip で Δ21 を確かめる補助で、純粋な plugin 費用の対照とは呼ばない。
- `S2f` = T-2817 S2 (+ `-p tools.acceptance_shards` + shard 0/3 spec、`--no-loadscope-reorder`) + 関数計時 (B)。
- `S3u` = T-2817 S3 (受入 argv 形) + 共通計時 (A + C) だけ。観測者効果の対照。
- `S3f` = S3 + 関数計時 (B)。
- `S3cf` = S3f + 反実仮想 (resolve memo)。
- collection-only の scheduler は T-2817 の形を保つ (collection 一致検査と失敗通知を残し配布だけ省く)。

**計時点:**
- A (全 xdist セル共通、T-2817 の計器): worker の t_import / configure / sessionstart / collection 入口出口 / 最初と最後の itemcollected / cf wrapper 入口 (`cf_entry`) と出口 (`cf_exit`) / sessionfinish、shard plugin の `collection_finished_epoch_s`; controller の sessionstart / configure_node / node_collection_finished 入口出口 / all_collected / first nodedown / sessionfinish; config 事実; Lustre client stats・loadavg・MemAvailable・単独性 (cell 前後)。
- C (全 xdist セル共通、新規): controller の早期 memo の receipt / oracle 各 prewarm の開始と正常復帰の epoch (復帰直後に conftest が `.pending` を unlink する = 公開の近似。conftest module global の `_prewarm_receipt_memo` / `_prewarm_oracle_environment_memo` を委譲 wrapper で包む)、`_run_memo_prewarm_barrier` の終了 epoch (hook 別)、worker の `_wait_early_memo_job` の入口・出口、cell の TMPDIR と memo cache path。
- B (f / cf セル、新規): 排他的な葉の区間を worker ごとに記録する —
  - E0 = 最後の itemcollected → modifyitems hook の最外 impl の入口 (最後の module と祖先の collectreport 等)。
  - modifyitems の実登録 impl / wrapper を `get_hookimpls()` で列挙し、各 `HookImpl.function` を委譲 wrapper に差し替えて (argnames・順序・wrapper 種別を保つ) 入口出口を取る。conftest の wrapper は generator の `next()`→最初の yield (前段 = hold 処理) と `send()/throw()`→終了 (後段) を分けて取る。後段の内訳 = `_validate_real_repo_shard_state` / `_strip_real_repo_loadgroup_suffix` (累積) / `_reorder_acceptance_items_by_duration` / 残り。
  - shard plugin impl の内訳 = `records_from_items` (inclusive: pass-1 の `_canonical_item` 累積、その中の resolve 累積 (回数・wall)、残り = sort と重複検査) / `allocate` / 選択 (pass-2 の `_canonical_item` 累積とその resolve、分配の loop、`pytest_deselected` 呼出し) / state 構築 (`_records_payload` / `_digest`) / impl 内の残り。
  - 他 plugin の impl (mark の deselect、xdist remote の group suffix 付与、`pytest_deselected` の各 impl) は実登録に存在するものだけを測る。
  - E4 = modifyitems の最外 impl の出口 → `cf_entry`。
  - resolve は thread-local の「`_canonical_item` 実行中」flag で限定し (元の `Path.resolve` を保存、flag は `finally` で復元)、回数と wall だけを取る (per-call の CPU syscall なし)。`Path.cwd().resolve()`・spec 解決・conftest の growth hold resolve は対象外。
  - CPU: 大区間 (conftest 前段、shard impl 全体、records_from_items、allocate、選択、state、conftest 後段) の境界で `resource.getrusage(RUSAGE_THREAD)` の user / sys を取り、process の `os.times()` は別列に保持する。
- 計器の自己費用の見積り (時計の読取り約 10.6 万回 / worker、0.05〜0.53 秒は見積り) は実測値と呼ばない。実測の観測者効果は S3u / S3f で見る。

**反実仮想 (S3cf だけ):** `_canonical_item` 実行中の `Path.resolve(strict)` を process 内で `(os.fspath(self), strict)` をキーに memo 化する — **固定した collection 中の、成功した実 resolve 結果の再利用**。例外は memo しない。初回は必ず元の resolve へ委譲する。conftest・他の resolve には漏らさない。

**有効セル条件 (集計器が判定、常設 gate ではない):** rc 0、`complete=true` (48 worker の payload 回収)、全 worker に必須の計時点 (A、f / cf では B の全境界) が揃う、`collection_mismatch=false`、probe errors 0・node error 0、S2 / S3 は report.json が存在し §4 R4 の集合照合が成功。失敗 attempt は残し、有効セルの速度差に混ぜない。

**書込み:** cell ごとの `session_root` (node-local → job dir へ回収)、create-only report、node-local TMPDIR、`PYTHONDONTWRITEBYTECODE=1`、`-p no:cacheprovider`、`IZANAGI_TASK_RUN_AUTO_RECORD=0` を維持。計測中に checkout・`output/` へ書かない。

## §4 読み方の事前登録 (結果を見る前、以後変えない)

- **R1 閉包 (S2f / S3f / S3cf の各セル):** 加算は排他的な葉だけ (E0、conftest 前段、他 impl、shard impl の葉 = resolve pass-1 / canonical 残り pass-1 / records 残り / allocate / resolve pass-2 / canonical 残り pass-2 / 選択 loop 残り / `pytest_deselected` / state / impl 残り、conftest 後段の葉 = validate / strip / reorder / 残り、E4)。残差_w = modify_w − Σ 葉_w。判定: `median_w(|残差_w|)` ≤ max(2 秒, 0.05 × median_w(modify_w)) なら「閉じた」。全 worker の残差の分布と、W_w を決めた worker の残差も併記。閉じなければ「未閉包」と書き、測った葉の値だけを示す。
- **R2 帰属:** 葉ごとの median_w / max_w の wall と、大区間の thread user / sys。share = 葉 median / modify median。**「主因」と書いてよいのは、ある葉の share が有効な f セル 4 つ (S2f ×2、S3f ×2) すべてで ≥ 0.5 の場合だけ**。それ以外は「最大の区間」と書く。process 群の sys (T-2817 の +2027 秒) と thread sys の合計は同じ量ではないと明記する。
- **R3 観測者効果 (half ごと、S3u vs S3f):** Δmodify_median、ΔW_w、Δpre を出す。3 つとも |値| ≤ 2 秒なら「計器の影響は判定閾値内」。超えたら f / cf の値を「計装下の値」とし、無計装の短縮量へ外挿しない。
- **R4 反実仮想の集合同値 (S3cf の有効条件):** 同 half の S3f・S3u と、(a) 全 48 worker の `izanagi_acceptance_shard` payload の `records_digest` と `selected_digest` がセル内で一意かつセル間で一致、(b) gw0 の `records` / `selected` が一致、(c) report の `observed_universe` / `selected` が canonical serialization で一致。1 つでも不一致なら S3cf は無効 (短縮量を書かない)。これは観測標本の一致であり一般的同値の証明ではない。
- **R5 主比較 (half ごと、S3f vs S3cf):** ΔW = W_w(S3f) − W_w(S3cf)、Δmodify = modify median の差、Δpre = pre_junit(S3f) − pre_junit(S3cf)、ΔM = M(S3f) − M(S3cf) を**別々に**書く (W_w = max_w(cf_entry) − junit timestamp、pre_junit = max_w(cf_exit) − junit timestamp、M = max(receipt 公開, oracle 公開) − junit timestamp)。
- **R6 `pre` の構造 (全有効 S2 / S3 セル):** 残差_pre = pre_junit − max(W_w, M) を符号付きで出す。|残差_pre| ≤ 2 秒を「max 式に適合」、超過は「不適合」として値を書く。**S3cf の予測 (結果を見る前に登録)**: (i) S3cf も max 式に適合する、(ii) W_w(S3cf) < M(S3cf) なら Δpre は ΔW より小さく pre(S3cf) ≈ M(S3cf) となり worker の待ち (`cf_exit − cf_entry`) が伸びる、W_w(S3cf) ≥ M(S3cf) なら Δpre ≈ ΔW。予測の成否をそのまま書く。M の変化 (ΔM) の原因は識別しない (早着 worker の CPU / local IO、resolve 削減による Lustre 負荷の変化などは候補)。
- **R7 Lustre・CPU:** セル前後の `md_stats:intent_lock` 差・process 群の user / sys を S3f と S3cf で並べる (記述のみ、閾値なし)。
- **R8 外乱:** 受入共有 root の session のうち作成時刻が [cell 開始 − 15 分, cell 終了] のものを候補にし、その junit timestamp と report の `collection_finished_epoch_s` で collection 区間を得て cell 区間との重なりを判定。区間が取れなければ「重複不明」。主比較の対 (同 half の S3f / S3cf) に「重複あり」が出たら、その half の 5 セルを同順序で 1 度だけ別 job で取り直し、再度重なれば結論を限定する。他 node・他ユーザーの MDS 負荷は検知できないと明記する。
- **比較の限定:** 順序反転 2 走は記述的診断で、外乱除去・効果確立の証明ではない。T-2817 の S2 / S3 値は tip 差 (台帳 +434 行) があるので参照に留める。

## §5 変異・受入

- 実装面 (D95 決定 2) の repo 差分はゼロ (probe は job dir、repo には逐語 `.txt`・insight・spool fragment だけ) → **変異 matrix は免除** (DW-S04)。
- 受入全走は免除しない。記録 commit の後に `tools/dev_wave_wait.py acceptance` で 1 走し child-green を land 条件にする。その shard-0 `pre` は別 tip (post-claim merge 後) の参考観測として書く。
- probe の正しさは段 5 の author が合成入力で正例・負例 (有効セル判定、R1 閉包判定、R4 集合照合、R6 適合判定) を走らせて示し、親が login の生死確認 (narrowed、`-n 2`) で A / B / C の計時点と反実仮想の配線を実データで確かめる。

## §7 追補 1 (2026-09-21 14:36 JST) — Codex 不可用による再裁定: 本 wave は「実装しない」(4→7→8→9)

- 事実: 段 5 の author 子 (launcher 起動 14:24:40 JST = 14:24:45 の `ps` で経過 5 秒、job-id `t2826-s5-author`) は Codex の利用上限で停止した。receipt: `codex_exit_code=1`、`failure_class=f45_missing_output`、`model_calls=9`、`output_bytes=0`、`wall_clock_s=513.95` (receipt 14:33:16、`.done`=1 は 14:33:42)。events の停止本文 (逐語): `You’ve hit your usage limit. Visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Sep 26th, 2026 7:35 PM.` 他に `"type":"error"` を含む 2 行は `item.completed` 内の `item.type:"error"` で、起動器が付ける `--dangerously-bypass-hook-trust` に対する Codex CLI の警告 (`--dangerously-bypass-hook-trust` is enabled…)。`model_calls=9` は観測値 (`model_calls_semantics=observed_token_count_events`)。待ち手は `stage=producer-files rc=70`。
- 起動器は子 worktree の残差を `31894443efd6c662f9e257d1055a0da0d15ca375` (branch `author-t2826-probe`) として commit した。3 file (probe.sh 178 行 / plugin 530 行 / aggregate 584 行) は**書きかけで未検査** (子は検査も報告もしていない)。job dir `partial-author/` へ退避 (sha256 は元と一致)。
- 扱い: D582 (即時通知・自動再試行しない・再試行の判断はユーザー) と `docs/ai-provenance.md` (Codex 実行不能なら Claude は代行せず停止、免除は D105 の waiver = ユーザー裁定) に従う。ユーザーへ端末通知を送った (PushNotification、携帯への push は Remote Control 無効で未送信。送信時刻は前後の `date` 実測 14:34:32 と 14:36:47 JST の間)。親は probe を書かない。従量経路へ切り替えない。
- 再裁定: 本 wave は「実装しない」として段 5・6 を飛ばし 4→7→8→9 の docs-only で閉じる。計測は行わない。記録するのは段 1 brief・段 3 相談・段 4 裁定 (§1〜§5 の事前登録を**結果を見る前の凍結**として)・停止の証拠・再開の手順。**land より前にユーザーからアカウント切替の返信があれば、新しい `--job-id` で段 5 を再投入する** (`--job-id` を省くと wave 名と prompt の sha256 から id が作られる — `tools/dev_wave_codex.py`)。
- 再開 wave の扱い: 入口の「裁定後に別 context が段 4 から再開する型は、変更面の骨格が同一なら前 wave の段 2・3 成果物を流用でき、再検査は段 6 レビューへ寄せる」に当たる。段 3 相談を流用し、段 4 で本裁定 §3 / §4 を変えずに採り直してから段 5 へ進む。段 5 の prompt は wave 固有の値 (子 worktree の path と branch、仕様 file の置き場、既定の出力先、tip が進んでいれば行番号) を差し替える。書きかけ 3 file は参考資料 (未検査) としてのみ渡す。
- 訂正注記 (2026-09-21 14:55 JST): 本 §7 の「段 5 から始める」「prompt bytes を変えて再投入 (F411: job-id は prompt hash で決まる)」「起動器の定型警告」「通知済み」の 4 文を、段 7 の事実照合 (insight `verbatim/s7-review-out.md` 所見 2・4・8・9) に従って上の形へ直した。

## §6 scope 外 (記録のみ、起票しない)

- 縮約方式の設計・採否、実受入の隣接対、T-2617 §4 の再判定の提案 — 起動引数で外。
- 第 29 回 項 10 (test 競走) — 主題が別。
