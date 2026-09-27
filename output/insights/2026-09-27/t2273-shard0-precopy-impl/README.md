# [T-2273] [T-2560] 受入 shard-0 の候補 (a) を実装した — 可視 output の写しを受入 controller が collection 中に作り、共有 base builder は写しから複製する。実受入の隣接 3 対で W_0 が 46.0〜55.4 秒 (対率中央値 12.7 %) 縮み事前登録の land 条件を満たしたが、5 分上限は未達 (B の W_max 中央値 317.2 秒)。次は (b) 発行 subprocess (2026-09-27)

wave `dev-wave-t2273-shard0-precopy-impl` (branch `t2273-shard0-precopy`)。依頼の逐語は `verbatim/T-2273-origin.md`、判断は D2253 (形) と本 wave の決定 (decisions fragment)。段 1 brief・段 4 / 6 裁定・Codex 子の prompt と出力・開始 gate は `verbatim/`、計測の集計は `analysis/`、変異は `mutation/`、投入台帳と計測 tip は `runs/`。
標本の時点 = 開始 gate 2026-09-27 14:40:04 JST (`verbatim/startup-gate.log` の mtime、HEAD = local main `ad114fba0`)。

## 結論 (最初に読む)

1. **事前登録の land 条件 (段 4 裁定「計測の事前登録」5): 満たした。** 有効 3 対の shard-0 W_0 の対差 Δ = W_0(A) − W_0(B) は +55.355 / +46.001 / +47.740 秒 (3 対すべて正)、対率は 15.7 / 12.7 / 12.4 %、中央値 12.7 % (基準 ≥ 10 %)。対差の中央値 47.740 秒。親が原データから再計算して集計器の出力と一致した。
2. **5 分上限 (別判定): 未達。** B の W_max (3 shard の最大) は 296.137 / 317.194 / 336.973 秒、中央値 317.194 秒 > 300 秒 (3 走中 1 走だけ 300 秒未満)。事前登録 8 の区分は「段階的改善として land し、5 分未達・次は (b) = 発行 subprocess と記録して止める」。
3. **次の一手は (b) 発行 subprocess。** D2253 項 4 の診断で共有発行 key の builder に残る発行 child は約 87 秒 (CPU 支配、finalize_receipt 26.5・draft_receipt 20.4・validate_draft 19.8・gate_check 13.2・verify_receipt 6.6 秒)。本実装で B の O_max は 218.4〜234.5 秒 (A 275.9〜308.1 秒) まで下がり、最遅 shard は 6 走とも shard-0 のまま。
4. **B で shard-1 と pre が伸びた走がある (原因は分解していない)。** W_1 は A 228.6〜230.8 秒に対し B 232.9 / 313.0 / 267.8 秒、pre は A 65.6〜66.5 秒に対し B 67.4 / 77.2 / 72.9 秒。写しは 3 shard の controller すべてで作られる (shard の割付は worker の collection で決まるため、段 1 (P3))。shard-1 の伸びが写しの背景 I/O によるか外乱かは計器が無く分けられない。03-B では W_1 313.0 秒が W_0 317.2 秒に迫った。5 分に届かせるには (b) に加え、この伸びも見る必要がありうる。
5. **正しさの側は閉じている。** 実関数 `_copy_git_visible_output`・`_git_visible_output_paths`、全件性の検査 2 か所、`_T080SharedBases`、早期 memo の挙動は不変で、受理規則は変えていない (写しの時点が configure_node 時の 1 点になる意味の差だけ、段 4 A3)。事前登録の変異 M1〜M7 は全件 KILLED (期待 node と完全一致、P0 SURVIVED)。B の実受入 3 走が緑であることが、本番 controller での test module の import と ROOT 一致の実走確認になった (段 6 A3、T1 の射程外の部分)。

## 1. 依頼と不変条件

依頼 (逐語 `verbatim/T-2273-origin.md`): D2253 項 2 の形 (早期 memo prewarm と同じ controller の `pytest_configure_node` で背景 thread、実関数を session で 1 回だけ実 repo に呼んで session 所有の写し、builder は完成を待って写しから局所複製、D2242 の「最初の builder が作る」形は流用しない) を実装し、land 条件を段 4 で実受入の隣接対 (D357) として事前登録し、5 分上限は同じ実受入で別判定する。届かなければ次は (b) と記録して止める。計算は job Elapse の実測単価で見積もり、検査込み 2 node 時間以上ならユーザー確認。[T-2604] (同 test file の fixture 絞り) は触らない。規律 2 を緩めない。仮想リスク向けの gate・検査・台帳・一般化は scope 外。

守ったこと: 上の不変条件 (結論 5)。[T-2604] の fixture は触っていない。gate・台帳・一般化・環境変数は足していない。

## 2. 実装 (commit `677ea17b6` + fix `6041d2f28`、計測 B は main `a0bf57976` を取り込んだ `163c5eeb7`)

変更 3 file、+179 / −4 (Codex author、子 branch `author-t2273pi-impl` / `fix-t2273pi-impl-1` から所有 path 限定 patch で統合)。

- **controller (`orchestrator/tests/conftest.py`):** `pytest_configure_node` の `_start_early_memo_job(node)` の直後 (同じ `_early_memo_selected` の分岐) で `_start_t080_visible_output_snapshot(node)` を呼ぶ。session で 1 回だけ、同期で dir `tempfile.gettempdir()/izanagi-t080-visible-output-<sha256([str(ROOT), testrunuid])>` を `mkdir(exist_ok=False)` し、非 daemon thread で test module を import して `module.ROOT` と conftest の root の一致を確かめ、実関数 `_copy_git_visible_output(ROOT, dir/output)` を 1 回呼ぶ。終わりに `result.json` (`{"ok": true}` / `{"ok": false, "error": ...}`) を pending → rename で置く。終了は `_finish_memo_sessions` (pytest_unconfigure から、worker 全終了後) で join → dir 削除、生成エラーを優先して伝播。
- **builder (`orchestrator/tests/test_s8b_oracle_driver.py`):** 旧 1458 行 `_copy_git_visible_output(ROOT, root / "output")` を helper `_t080_copy_visible_output(destination)` に置換。`PYTEST_XDIST_TESTRUNUID` と `str(ROOT)` から同じ式で dir を導き、dir があれば `result.json` を最長 180 秒待って `shutil.copytree(dir/output, destination)`、失敗・超過は例外。dir が無い走 (単独走・絞り込み・受入でない xdist 走) は従来どおり実 repo から直接複製。
- **意味の差 (段 4 A3):** 写しは configure_node 時の 1 時点で、session 中の output/ の変更は fixture に反映されない。受理規則は不変 (D2242 段 4 A1 と同じ扱い、docstring に明記)。
- **変えていないもの:** `_copy_git_visible_output`・`_git_visible_output_paths` の本体、全件性の検査 2 か所、`_T080SharedBases`、`_t080_join_shared_bases`、早期 memo の挙動、既存 test の期待値。環境変数は新設していない (path は既存の共有 base と同じ識別子から導出)。
- **test:** 新規 T1 `test_t080_visible_output_snapshot_starts_once_and_preserves_copy` (小さい git repo へ conftest を複写して読み込み、同じ config の別 node 2 本で本物の hook を呼ぶ。helper を呼ぶ前に `result.json` が ok で現れる、実関数が 1 回、写しからの 2 回の複製が変更前の直接複製と集合・bytes・mtime・mode で一致、終了で dir が消える)。既存 T2 `test_t080_shared_base_builds_real_builder_once_across_processes` に helper 呼出し回数 == builder 呼出し回数の assert。既存の模擬 hook fixture `_early_memo_cache_probe` で新起動関数を no-op 化。
- **T1 の射程 (段 6 A3):** T1 は複写した conftest と `importlib` で取り直した test module を使うので、pytest が収集した module 状態との一致までは示さない。本番 controller での import 成功と ROOT 一致は実受入 (写しが失敗すれば共有 base の builder が赤になる) で確かめる。

## 3. 段 2〜6

- 段 2 plan (`verbatim/s2-plan-*`)、段 3 相談 2 本 (レンズ A 正しさ・整合・実効性、レンズ B 過剰・削除・計測設計、どちらも修正後 GO)。段 4 裁定 (`verbatim/s4-ruling.md`): 正例が実 builder の分岐と hook 起動を通らない (A1 / B1) → T1・T2、環境変数の継承 (A2) → 環境変数を新設しない、時点差 (A3) → 受理規則は不変と明記、発火順序 (A4) は refuted、無期限 join (A5) は早期 memo と揃える、marker 3 種 (B3) → 結果 file 1 つ、E1 定数 (B4) → 投入前に固定する入力 file。
- 計算量: 見積り 2.0〜3.1 node 時間でユーザー確認 → 「3 対で投入 (推奨)」(上限目安 3.1、取り直し 4 走まで)。
- 段 6 (`verbatim/s6-ruling.md`): レビュー 2 本 (どちらも修正後 GO) → B1 (T1 が同じ node で 2 回) must-fix、A1 (削除失敗が生成エラーを覆う)・A2 (mode 未比較)・A4 (probe の collection fallback) を fix。焦点再レビュー 1 本 (条件付き NO-GO、新所見 F1・F2 = M4・M6 が登録した assert より前で落ちる) は、親が変異の実測 (観測 node = 登録 node、落ちた行は変異の欠陥そのもの) で閉じ、落ちる assert を erratum E3・E4 に記録。
- 焦点走: focus-1 (tip `677ea17b6`) 353 passed / 7 skipped、focus-2 (tip `6041d2f28`、`-rfs`) 353 passed / 7 skipped (skip は既存の成長 hold 6 件と toolchain 前提 1 件、T1・T2 は skip されていない)、どちらも失敗 0。Elapse 295 / 398 秒。
- 全史 provenance: 12,970 件 (実装後) / 12,995 件 (merge 後)、新規違反なし。

## 4. 変異 (`mutation/`)

独立 clone (D1009) の固定 commit `6041d2f28`、`tools/mutation_worktree.py --runner-mode dispatch`。期待 node は初回 dispatch probe (全件 SURVIVED 期待) で観測し、登録 (段 4 + erratum) との完全一致を確かめて final を走らせた。

| ID | 変異 | 最初に落ちた行 (probe の本文) | final |
|---|---|---|---|
| P0 | docstring 1 語 | — | SURVIVED |
| M1 | builder が helper を経ず実 repo から直接複製 | helper 0 回 ≠ builder 1 回 (T2) | KILLED |
| M2 | 写しがあっても helper が実 repo から複製 | 変更後の bytes が混入 (T1 signature) | KILLED |
| M3 | 写し → destination を `copy_function=shutil.copy` | mtime 不一致 (T1 signature) | KILLED |
| M4 | 1 回性 guard を外し `exist_ok=True` (erratum E1) | 2 本目の thread が同じ dir へ二重に複製して失敗し `result.json` の ok が False (T1、erratum E3) | KILLED |
| M5 | 実関数の代わりに `shutil.copytree(ROOT/output, ...)` | 実関数 0 回 (T1 spy) | KILLED |
| M6 | hook から起動呼出しを外す (erratum E2) | `result.json` が現れず読取りで FileNotFoundError (T1、erratum E4) | KILLED |
| M7 | 終了で dir を消さない | 終了後も dir が残る (T1) | KILLED |

## 5. 隣接対の実受入

測定形 (段 4 事前登録、`verbatim/s4-ruling.md`): A = `a0bf57976` (測定準備時の local main、clean worktree `t2273pi-base-a`)、B = `163c5eeb7` (A + 実装 3 file、wave 木)。`IZANAGI_ACCEPTANCE_SHARDS=3 python3 tools/run_tests.py` の直接投入、順序 A,B / B,A / A,B、門番 = 他 session の受入 leader ≤ 1 ∧ load1 ≤ 60。温めは両 tree で collect-only を 1 回 (A 07:24〜07:34 UTC、B 07:34〜07:37 UTC、どちらも rc 0・HEAD 不変・clean)。E1: 受入と同じ関数 (`_collect_login_universe`、受入時の恒久除外) で取った login collection は A 27,817 / B 27,818 件、差は B の新規正例 T1 の 1 件だけ (A only は空、`runs/expected-added-nodes.json`)。集計器 `t2273pi_ab_analyze.py` (前回 probe の移植、Codex author、逐語 `verbatim/probe-source.md`)。測定中に自分の他 job は走らせていない。

**投入 6 走、infra 失敗 0、有効 3 対。** 系列 2026-09-27 16:38:05 → 18:33:16 JST (`runs/series.log`)。

| 対 | W_0 A | W_0 B | Δ = A − B | r | W_max B | O_max A / B | pre A / B |
|---|---:|---:|---:|---:|---:|---|---|
| 1 (01-A / 02-B) | 351.492 | 296.137 | +55.355 | 15.7 % | 296.137 | 275.859 / 218.429 | 65.579 / 67.448 |
| 2 (04-A / 03-B) | 363.195 | 317.194 | +46.001 | 12.7 % | 317.194 | 287.317 / 219.901 | 65.755 / 77.170 |
| 3 (05-A / 06-B) | 384.713 | 336.973 | +47.740 | 12.4 % | 336.973 | 308.140 / 234.535 | 66.488 / 72.923 |

- 対差の中央値 47.740 秒、対率の中央値 12.7 %。W_1 は A 228.606 / 229.669 / 230.841、B 232.923 / 312.981 / 267.803 秒。W_2 は A 219.000 / 220.804 / 219.956、B 221.254 / 222.917 / 225.250 秒。post は 6 走とも 10.03〜10.07 秒。
- 6 走とも最遅 shard は shard-0 (W_max = W_0)。L の node は全走 `test_t080_failed_launch_preserves_receipt_refusal` (gw40)。
- A の W_0 は前回 (D2242) の実受入 A 344.8〜367.5 秒と重なるが、本系列の 05-A は 384.7 秒で上に外れた。対は隣接投入なので対差で比べ、絶対値を系列間で比べない。
- 前回の対照診断 (D2253) の replica の対差 +45.7〜+81.3 秒 (中央値 18.0 %) より小さい。replica は受入の外側 dispatch・shard-1 / 2・login collection を再現していない (D2253 却下 1)。

## 6. 計算量

見積り 2.0〜3.1 node 時間でユーザーが「3 対で投入 (推奨)」と回答 (上限目安 3.1、取り直し 4 走まで)。実績 (dispatch 受領証の NQSV Elapse、request ID で重複除去): 系列 18 job 5,273 秒 (1.46 node 時間)、焦点走 2 回 693 秒、変異 (probe + final、26 job) 668 秒、温め 2 回 111 秒、計 6,745 秒 = 1.87 node 時間。記録前の受入 1 回が別に加わる (worklog に記す)。取り直し 0。

## 7. 限界・言わないこと

- 3 対は同一 node・同一 allocation ではない (固定 2 tree の隣接逐次投入)。有意差判定ではない (事前登録の基準の成否だけ)。
- 実受入に写しの計器は無い。写しの生成所要・builder の写し待ち・shard-1 の伸びの原因は測っていない (計器を足すのは scope 外、段 4 B 事前登録 7)。
- 5 分は B 3 走の中央値で判定した。02-B は 296.1 秒で 300 秒未満だったが、中央値は 317.2 秒。
- T1 は小さい git repo へ複写した conftest と取り直した test module で本物の hook を通す正例で、pytest が収集した module 状態との一致までは示さない (段 6 A3)。本番での import と ROOT 一致は B の実受入 3 走の緑で確かめた。

## 8. この dir の中身

`verbatim/` 依頼・段 1 brief・段 2 plan・段 3 相談 2 本・段 4 / 6 裁定・段 5 author 2 本・段 6 レビュー 2 本・fix 2 本・焦点再レビューの prompt と出力・開始 gate・probe 逐語 (`probe-source.md`)・行末空白の可逆な正規化の記録 (`NORMALIZATION.md`、5 file)。`analysis/analysis.md` 走表と対表 (集計器の出力そのまま)、`analysis/analysis-compact.json` 集計 JSON の要約 (全文 44.8 MB は job dir)。`mutation/` final の spec・観測 node・probe / final の結果要約。`runs/` 投入台帳・系列 log・計測 tip・E1 の追加 node。job dir は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2273-shard0-precopy-impl/` (repo 外)。
