# 段 1 brief — [T-2273] 受入 shard-0 候補 (a) 前倒しの写しの効果を対照診断で測る

as-of = 開始 gate 2026-09-26 20:05 JST (`startup-gate.log`)、wave 木 `/work/1/SFC/tanab/izanagi/.claude/worktrees/t2273-shard0-precopy` (branch `t2273-shard0-precopy`、HEAD = local main `265cce13c`)。依頼の逐語 `verbatim/T-2273-origin.md`、裁定 `verbatim/D2243-head-item1-2.md` 項 2・`verbatim/D2242.md`・`verbatim/D1936-item35.md`・`verbatim/D357.md`。

**研究前進:** 受入 5 分上限 (D1894) は開発ループ全体の律速で、CC 合成の反復速度を縛る。本 wave の完了判定 = 候補 (a) の効果 (shard-0 の O_max・W_0 の短縮) を事前登録した隣接対で測り、「(a) を実装する / (b) へ移る」のどちらかを数値付きで推奨すること。

**scope:** repo の実装面は 1 byte も変えない (D1936 項 35)。probe (runner / plugin / analyzer) は Codex author が子 branch に書き、repo 外 (job dir `probe/`) で実行し、repo には逐語 .md と集計だけ置く。出発点は第 4 回 probe (`author-t2273-probe-fix2` の `7f38ac7fd`、`tools/t2273_replica_{runner,plugin,analyze}.py`)。(c) (D2242 実装の land) は採らない。gate・台帳・一般化は足さない。

**親の provisional 裁定 (攻撃対象):**
- (P1) **pre を実受入に揃える。** 第 4 回 replica の pre 128.8〜130.2 秒は実受入 (59〜66 秒) の約 2 倍。親の見立て: replica は clean 木 + `PYTHONDONTWRITEBYTECODE=1` で bytecode / assertion-rewrite cache が常に冷 (48 並列 collection は温 18.4 / 冷 84.6 秒、T-2243 insight `output/insights/2026-09-20/t2243-collection-contention/README.md`)。実受入は login の `_collect_login_universe` (`tools/run_tests.py`、書込み禁止なし) が走行元木に pyc を書く。前倒しの写しは collection 窓と重ねる案なので、pre が 2 倍だと効果が楽観側に歪む。→ 各 job 投入前に login で wave 木を 1 回温め (bytecode 書込みあり)、job 内で pre を記録。A の pre が 55〜80 秒の外なら外れと明記して読む (無効にはしない)。
- (P2) **P 条件 (前倒しの写し) の形:** 既存の早期 memo prewarm (D2061 / D2062、`orchestrator/tests/conftest.py:2583` `pytest_configure_node` → `:2388` `_start_early_memo_job` が controller で `threading.Thread` を起こす) と同じ点・同じ形に寄せる。probe plugin の controller 側 `pytest_configure_node` で最初の 1 回だけ背景 thread を起こし、`node.workerinput["testrunuid"]` から worker 側と同じ identity (`test_s8b_oracle_driver.py:974` `_t080_join_shared_bases` の sha256([str(ROOT), run_id])) の共有置き場の下へ、実関数 `_copy_git_visible_output(ROOT, <snapshot>/output)` を 1 回呼ぶ。完成 marker を pending → rename。builder の複製呼出し (`test_s8b_oracle_driver.py:1458`、source_root == ROOT のときだけ) を「marker を待ち (待ち時間を span に記録)、`shutil.copytree(<snapshot>/output, dest)` (copy2)」に差し替える。複製側は D2242 実装 (`eb65d322f` の `copy_visible_output`) と同じ。写し生成失敗・未完は P を無効にする (fallback で隠さない)。
- (P2') **早期 memo 待ちとの干渉は P の費用に数える。** 写しは早期 memo prewarm と同じ窓で Lustre を読む。前回 wave の infra 失敗 2 走は早期 memo 待ち (上限 120 秒) の超過だった。P の走で早期 memo 待ち超過が起きたら infra でなく **P に帰属する失敗**として数え (A で起きたら infra)、両条件で早期 memo の所要を記録する。
- (P3) **比較の形:** 計算ノード 3 job を逐次 (同時投入しない、D357・第 4 回 C6)。各 job = smoke → 2 条件を同一 node で隣接。順序 job1 A,P / job2 P,A / job3 A,P。A = 第 4 回 A2 と同じ観測のみ。
- (P4) **発行 subprocess の内訳は A・P の両方に対称に入れる** (別 job を足さない)。builder の発行 (`test_s8b_oracle_driver.py:1564` の child、`:1712` の `subprocess.run`) を観測 wrapper で包み、child の中で import / git basis / draft_receipt / validate_draft / finalize_receipt / git add・commit / verify_receipt / gate_check の壁時間と CPU 時間を記録する。実関数へ同じ引数を 1 回渡すだけ (DW-O14)。(b) の判断に使うのは (a) が乏しい場合だけ、(a) が効く場合は「(a) 後の次の律速」として読む。

**事前登録 (段 4 で確定):** 有効性 = 第 4 回 R2 と同じ全項目 (rc 0、outcome 集合一致、builder ごとの複製結果の集合 digest・件数が A と P で一致、clean、others 0、record-error 0) + P の写し完成 marker あり。判定量 Δ_i = W_0(A) − W_0(P)。**効果あり = 有効 3 対すべて Δ_i > 0 ∧ 対率中央値 ≥ 10 %**、それ以外は「乏しい」。併記: O_max・L・pre・写しの開始/完成時刻と最初の builder 開始時刻の差・builder の待ち時間、条件別中央値、P の W_0 中央値と 300 秒の比較。

**不変条件:** production・test・conftest・台帳・既存検査は不変。受理集合不変 (規律 2)。走行中に wave 木へ書かない (第 4 回 R2' の停止原因)。

**受入・実測環境:** 計算ノード (Pegasus、`tools/pegasus/dispatch_compute.py --task generic`、walltime 00:50:00)。受入全走は記録前に 1 回。費用見積り (単価 = 第 4 回 R2'' の job Elapse 1,046 秒 / smoke + 2 走 + staging): 1 job ≈ 1,100 秒 × 3 = 0.92 node 時間 + 受入 0.25 + 取り直し 1 job 0.31 ≈ 1.5 node 時間 < 2 → ユーザー確認不要。取り直しが 2 job を超えたら再見積り。

**分割:** 段 3 = read-only 相談 2 本 (レンズ A 計測の妥当性・(a) の実装形への忠実さ、レンズ B 過剰・削除・費用)。段 5 = Codex author 1 単位 (probe 3 file)。段 6 = 独立レビュー 2 本 + fix。変異 matrix は実装面差分ゼロで免除 (DW-S04)。
