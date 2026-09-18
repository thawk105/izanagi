# [T-2691] rescue の landed checker 待機に終了余裕定数 1 つを足し、子の期限 JSON (`assessment-timeout`) を親が回収できるようにする

- authority: none
- default_effect: no-state-change
- 日付: 2026-09-18
- wave: dev-wave-t2691-rescue-checker-timeout-grace (branch `worktree-dev-wave-t2691-rescue-checker-timeout-grace`、軽量版 + 段 2/3/6 の敵対子)
- 起点: ユーザー依頼 [T-2691] (P2、起票 entry 1542 = [T-2639] wave の残件)。依頼文の「`audit_dangling_commits.py` の rescue」は起票時の要約ずれで、実体は `tools/check_branch_rescue.py::_landed_assessment` ↔ 子 `tools/check_branch_landed.py` (`_audit()` の子は deadline 引数を持たず理由 JSON も出さないので同値問題が成立しない)
- 基準: local main `c8e8dc06f` (wave 開始時、fresh worktree) → 記録前に `ed4363204` (21 commit、重なる file なし) を非 ff で取込 (`53e5743c2`)。実装 commit = `f076c6f7f`、docs = `d00246b4e` + `b38442a98`
- job dir (prompt・log・patch・変異台帳の原本): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2691-rescue-checker-timeout-grace/`

## 0. 結論

- **定数 1 つ + 1 行で直した。** `CHECKER_EXIT_GRACE_SECONDS = 2.0` を足し、`_landed_assessment` の外側 `subprocess.run(timeout=...)` を `min(子予算 + 2.0, overall_remaining)` にした。子へ渡す `--timeout-seconds`、受理する JSON の形・schema・rc↔verdict 対応、`overall_remaining` の cap、`_empty_landed` の理由集合は 1 bit も変えていない (設計判断は本 wave の decisions fragment `rescue-checker-exit-grace`、fold 後に D 番号が付く)。
- **受理集合の含意:** JSON 検証述語は不変。変わるのは「時間内に回収できる契約準拠の報告」の範囲で、期限で書かれる `indeterminate/assessment-timeout` (rc=2、`proof_units` と `summary` 付き) に加え、旧期限後に届く `landed` / `not-landed` も回収される (D498 と同型の「宣言した子予算への是正」)。緩和ではない。
- **実 repo での対照 (§2, §4):** 修正前は T=1 / T=8 で 0/2 (`checker-timeout`、`checker_rc=None`)。修正後は期限に達した 4 事例 (2 OID × T=1, 4) が 4/4 で `assessment-timeout` / `checker_rc=2` / 未証明 unit 0 件・詳細射影 complete。
- **変異 matrix (§5):** baseline PASSED、m1〜m4 KILLED (期待 node 完全一致)、等価 m5 SURVIVED、MISMATCH 0。m4 の kill 根拠は待機区間の時間契約 (elapsed 下限) であって JSON 受理の変化ではないので、集計は「m1〜m3 (受理・打切り) 3 本」+「時間契約 pin m4 1 本」に分ける。
- **限界 (裁定済み、追加実装しない):** (a) 2.0 s は login node 12 走 (load 24〜35) の観測に基づく暫定値で、共有 FS 高負荷 (load 60 超) や計算ノードは未測定。超えれば従来どおり `checker-timeout` に戻るだけで受理集合は緩まない。(b) 総待機の上限は `max_assessments × (子予算 + 2 s)` へ伸びる (沈黙 checker が続く仮定で 512 → 640 s、300 s 予算内の判定件数は概算 37 → 30 件)。`--timeout-seconds` の cap は残るが、`overall_remaining` は残時間取得後の準備・後処理を含まないので厳密な wall 上限ではない (既存の限界、実害の観測なし、scope 外 real として記録のみ)。(c) 子の per-command 45 s 上限 (`check_branch_landed.py` `COMMAND_TIMEOUT_SECONDS`) による早期 `assessment-timeout` は別契約で、本 wave は触らない。(d) 改善が効くのは `--branch` / `--retire-worktree` を伴う preview 経路だけで、`--ledger-check` 単独は `_landed_assessment` を通らない。親の返却は reason・unit 詳細への射影で、子の phase outcome 全文は返さず、台帳 file も自動更新しない。(e) 新規 3 本は時間依存 test (正例の親期限 2.5 s に対し公称 0.8 s、m4 検出は 2.0 s vs 下限 2.8 s の差 0.8 s)。極端な遅延で偽陰性の余地は残る。受入で赤なら DW-O18 で判定する。

## 1. 変更面

| file | 変更 |
|---|---|
| `tools/check_branch_rescue.py` | 定数 `CHECKER_EXIT_GRACE_SECONDS = 2.0` (comment に根拠 4 点: 観測 12 走・wall−T max 0.134 s・約 15 倍・高負荷未測定)、`_landed_assessment` の `timeout=min(timeout + CHECKER_EXIT_GRACE_SECONDS, overall_remaining)` |
| `orchestrator/tests/test_check_branch_rescue.py` | helper `_make_timed_fake_landed(path, *, silent=False)` (argv の `--timeout-seconds` T を読み、`T + 0.3` 眠って contract 準拠の期限 JSON + `proof_units` 1 件を書き rc=2 / `silent` は 60 s 眠って無出力)、test 3 本: `test_landed_checker_timeout_json_is_collected_within_exit_grace` (T=0.5、overall 100)、`test_landed_checker_silent_child_is_cut_at_budget_plus_exit_grace` (T=1、下限は定数参照)、`test_landed_checker_overall_remaining_caps_the_wait` (T=5、overall 0.5、上限 3.0 s) |
| `docs/unreachable-object-ledger.md` | rc 説明を「期限報告を回収できれば `assessment-timeout`、親が min(子予算 + 終了余裕 2 秒, 全体残時間) で打ち切れば `checker-timeout`」に、待機見積りを「判定件数 × (子予算 + 終了余裕)」に (親、docs-only) |

既存 test の期待値変更 0、`_make_fake_landed` 不変、monkeypatch 型 timeout test 不変。

## 2. 段 1 で実測した事実 (DW-O13 の入力、`verbatim/probe-*.txt`)

- 子単体 `check_branch_landed.py --timeout-seconds T` (login node): OID 9de7385a6 の T=1 ×6 + T=8 ×2 (load 24〜27)、OID 81e0f9f64 の T=1 ×4 (load 34〜35) の **12 走全部が rc=2 `indeterminate/assessment-timeout`**、wall − T = **0.087〜0.134 s** (子の `total_elapsed − T` は 0.002〜0.030 s、残りは interpreter 起動 + JSON 書出し + 終了。内訳は独立計測していない)。
- 親 `_landed_assessment(repo, checker, oid, T, 100)` (修正前、共有 checkout): T=1 / T=8 とも `checker-timeout`、`checker_rc=None` → **0/2**。
- 機序: 子の期限起点は `Git(repo, time.monotonic() + timeout_seconds)` (`assess()` 内、interpreter 起動後)。親の期限は `communicate(timeout=…)` 起点で同値。通常の起動順序では子の期限が親より後になり、子の JSON は kill に間に合わない (段 3 の指摘で「必ず」「100%」は観測 2 走に限定)。
- `_audit()` の子 `audit_dangling_commits.py` は deadline 引数を持たず text 報告 + rc を返す (`audit-timeout` は別成果物)。

## 3. 段 2〜4 — plan と敵対相談が親 brief を直した点 (`verbatim/s2-plan.md`, `s3-a.md`, `s3-b.md`; 裁定は job dir `s4-ruling.md`)

- レンズ sol: 「親の timer は Popen 前」「必ず」「100%」は成立しない (期限は `communicate()` 起点、観測は 2 走) → 記録を限定。時間を含む受理集合は広がる (旧期限後の `landed`/`not-landed` も回収) → 「受理集合不変」と書かない。正例に未証明 unit 1 件を入れて回収を検証 → 採用。m4 は `min(max(T, G), overall)` 形で cap を残す → 採用。`--ledger-check` 単独は経路外 → 報告を限定。
- レンズ luna: 自己検査 test は負例 2 本に統合済で削除。正例だけ T=0.5 (公称合計 4.8 → 4.3 s) → 採用。overall 負例の上限 1.5 → 3.0 s → 採用。m4 の kill 帰属は elapsed だけ → 別枠集計。docs 2 行 → 採用。GRACE 2.0 は暫定値として維持し高負荷保証を書かない → 採用。等価変異は追加しない → 不採用 (harness の SURVIVED 検出の正例として 1 本登録)。
- 段 4 で所見 19 件を裁定 (real 13 / 疑い 4 / 一部採用 3 / 不採用 2)。scope 外 real: overall の厳密 wall 上限化 (A4) — 実害の観測なしで insight 記録のみ。

## 4. 段 5〜6 — 実装とレビュー (`verbatim/s5-author-1.patch`, `s5-author-1.md`, `s6-review-a-1.md`, `s6-review-b-1.md`; 親の実測は job dir `s6-parent-measurements.md`、裁定は `s6-ruling.md`)

- author (Codex、13 calls、accepted): 裁定プラン v2 と patch が完全一致 (2 file +92/−1)。sandbox で pytest 不可のため「実装済み・未実走」。変異 anchor 3 種は `grep -Fc` 各 1。
- 親実測 (patch 適用後、wave 木): 実 checker の期限事例 **4/4 回収** — (9de7385a6, T=1) `assessment-timeout` rc=2 elapsed 1.078 / (81e0f9f64, T=1) 1.076 / (9de7385a6, T=4) 4.087 / (81e0f9f64, T=4) 4.092、いずれも `unproven_unit_details.missing_reason=None`・`unproven_count=0` (`summary.files_enumerated=True`、列挙後の phase で期限)。T=8 は wave 木では 3.827 / 7.815 s で完走し `landed` (`branch-closure-empty`) なので期限事例でなく、共有 checkout の修正前 T=8 (子単体 8.03 s で期限) とは repo 状態が違い同条件対照にならない。
- 焦点走 (login node bounded local): `test_check_branch_rescue.py` + `test_branch_rescue_ledger.py` + `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` → **127 passed / 68.44 s、rc=0** (g5 が 64.5 s)。新規 3 本の call 所要 = 3.02 + 0.84 + 0.50 = **4.36 s** (公称 4.3 s)。既存 test は AST 不変なので file の増分 ≈ 新規分だが、同条件の変更前 baseline 走は取っていない。`tools/check_docs.py` 違反なし。
- レビュー 2 本: production / test の must-fix 0。採用した nit = 親実測記録の「列挙前に期限」の誤り (訂正)、docs の「2 秒」重複 (`b38442a98`)、受入 wall 増分は未立証 (記録を限定)。不採用 = 定数 comment の観測内訳削除 (DW-O13 の母集合明示のため残す)、m5 削除 (裁定維持)。fix 子・焦点再レビューは起動していない (コード変更を要する所見なし)。

## 5. 変異 matrix (container `.codex/worktrees/t2691-mutcontainer` @ `b38442a98`、`tools/mutation_harness.py` 直接、dispatch、runner = `run_tests.py --force-dispatch orchestrator/tests/test_check_branch_rescue.py -q -rf -p no:cacheprovider`、`verbatim/mutation-spec.json` / `mutation-run-1.json`、15:41:41 → 15:46:28 JST、rc=0)

| 変異 | 内容 (`tools/check_branch_rescue.py`) | 期待 | 結果 | 失敗 node | 所要 |
|---|---|---|---|---|---|
| m1 | `CHECKER_EXIT_GRACE_SECONDS = 2.0` → `0.0` | KILLED | KILLED | `test_landed_checker_timeout_json_is_collected_within_exit_grace` | 27.0 s |
| m2 | `min(timeout + G, overall_remaining)` → `timeout + G` (cap 除去) | KILLED | KILLED | `test_landed_checker_overall_remaining_caps_the_wait` | 37.3 s |
| m3 | 子へ `str(timeout)` → `str(timeout + G)` | KILLED | KILLED | `test_landed_checker_timeout_json_is_collected_within_exit_grace` | 32.2 s |
| m4 | `min(timeout + G, overall)` → `min(max(timeout, G), overall)` | KILLED | KILLED | `test_landed_checker_silent_child_is_cut_at_budget_plus_exit_grace` | 32.2 s |
| m5 | `min(timeout + G, overall)` → `min(overall, timeout + G)` (等価) | SURVIVED | SURVIVED | — | 52.8 s |

baseline PASSED (32.2 s)、matching 5/5、MISMATCH 0、anchor 件数は各 1、各変異の `injection_diff_sha256` 非空 (注入実在)。**集計: 受理・打切りの kill = m1〜m3 の 3 本、時間契約 pin = m4 の 1 本 (kill 根拠は elapsed 下限だけで JSON 受理の変化ではない)、等価 SURVIVED = m5**。

## 6. 受入全走

(受入は記録 commit の後に `run-acceptance-gated.sh` で投入する。結果は本 README には書けず (記録 commit は受入前に凍結される)、worklog fragment と最終報告に載せる。)

## 7. 工数

codex 子 6 本 (plan 1、consult 2、author 1、review 2)、親の probe 6 種、焦点走 2 走、変異 6 走。wave 開始 14:52 JST → 記録 commit 15:5x JST。

## 8. verbatim 一覧 (本 dir `verbatim/`)

`mutation-spec.json`、`mutation-run-1.json`、`probe-overshoot-T1.txt`、`probe-overshoot-T8.txt`、`probe-overshoot-T1-oid2.txt`、`probe-parent-repro.txt` (修正前)、`probe-parent-repro-after.txt` (修正後)、`s2-plan.md`、`s3-a.md`、`s3-b.md`、`s5-author-1.md`、`s6-review-a-1.md`、`s6-review-b-1.md`。author の patch は複製せず、実装 commit `f076c6f7f` (`git show f076c6f7f`) が原本 (job dir に `s5-author-1.patch` 5,493 bytes)。

可逆最小正規化 (DW-S07、`git diff --check` の行末空白抵触、可視文字不変): 行末の空白を除去した。復元法は該当行の行末へ空白 2 個 (markdown の改行) を戻す。
- `s3-b.md`: 原文 sha256 `af086d864b4bd1479289c3bf204086ff7ca11147fa796aeed74f39ccaf11bb75` (11,781 bytes、行末空白 1 行) → 正規化後 `257480cba1dee731141ebc78b31f17d20211754bc911d513a02c435a632af301` (11,779 bytes)。
- `s6-review-a-1.md`: 原文 sha256 `8638f8488c543e6a3a427544abfc65c975dcbca9737e30d844d54e91f35c1331` (7,196 bytes、行末空白 2 行) → 正規化後 `d4e8d32b9d2a133d1266bb876b3de4277b5aa897d02314015313b26d8ab24dcd` (7,192 bytes)。
原文は job dir `artifacts/dev-wave-t2691-rescue-checker-timeout-grace/` にそのまま残る。
