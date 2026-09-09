# 段 4 裁定 — [T-2354] A-5 job body の共有 gitdir prune 撤去

裁定時点の local main = `cbcdb6c91bd2eced76bd6a82650204c357c1b299` (wave 開始時から不変)。
裁定 inbox の再走査: main に新規 commit なし。T-2354 / prune に関する新しい裁定なし。

## 所見の real / refuted と採否

| # | 出所 | 判定 | 採否 | 根拠 |
|---|---|---|---|---|
| A1 | レンズ A 1 | **real** | **不採用 (scope 外)** | receipt 書き込みの `\|\| true` は現行コードに既に在り、本 wave が持ち込む退行ではない。`cleanup_rc` へ合成すると、依頼が求めていない新しい失敗経路を job rc へ足すことになる。限界として insight に明記する。 |
| A2 | レンズ A 2 | **real** | **採用 (must-fix)** | 失敗 fixture が「登録されていない path」を渡すと、実装が入力をそのまま書き戻すだけでも緑になる。実際に登録が残る形にしないと D1700 の「残置を明示」を挙動として証明できない。 |
| A3 | レンズ A 3 | **一部 real** | **一部採用** | 静的契約に remove 逐語の `count(...) == 1` を足すのは、依頼の 1 点 (prune 正例 → prune 不在) を超えて受理集合を狭める。**静的は prune の実行可能な不在だけを固定し、remove が実際に起きることと receipt 書式は runtime で固定する。** |
| A4 | レンズ A 4 | **real** | **採用 (変異設計を変更)** | M1 は静的 gate と runtime gate に同時に殺される。M1 は完全 node 集合で登録して冗長 gate と明記し、静的 regex を通過する M1b を足して runtime gate 単独の検出力を示す。 |
| A-推測1 / B2 | 両レンズ | **real (波及)** | **採用 (コード変更なし)** | job body の bytes が変われば `script_sha256` が変わり、T-1998 consumer の `launcher-script-identity-mismatch` に掛かる。ただし `launcher_script_sha256` は外部から渡る事前登録値で、repo 内に旧 digest を持つ live な事前登録は無い (旧 sha の hit は insight の歴史記録のみ)。T-1998 の正式測定は未実施なので既存成果物は壊れない。**着地後の新 digest で事前登録を作り直す**必要があることを worklog / insight と次の一手へ記録する。 |
| B1 | レンズ B 1 | **real** | **採用 (must-fix)** | F902 の実測どおり、main 側の被覆 gate の余裕は 1 node 未満。node を足す wave はどれでも 90% を割る。`tools/update_acceptance_duration_ledger.py --add-only <実走 JUnit>` で登録する。**実装 file は 3 件** (job body / 契約テスト / 台帳)。 |
| B3 | レンズ B 3 | **real** | **採用** | plan の `rekt:126` は `tools/pegasus/a5_second_boot_backoff_sweep.sh:126`、`test_a5 rospector:249-270` は `orchestrator/tests/test_a5_second_boot_job_contract.py:249-270` と読み替える。 |
| A-brief 反証 1・3 / B-nit | 両レンズ | **real (親 brief の誤り)** | **訂正** | 旧 sha の hit には T-1998 裁定の逐語も含まれる。また A-5 の receipt を実行時に読む consumer は現時点でゼロで、契約テストは producer の printf 逐語を静的に見ているだけ。追加する runtime test が最初の consumer になる。 |
| B-推測 (collect_receipt / 外部 collector) | レンズ B | **refuted (根拠なし)** | 不採用 | `collect_receipt.py` に A-5 からの callsite は無く、`env/ccbench-worktree-prune.*` を要求する repo 内根拠も無い。 |
| A-nit (rc 伝播は切れていない) | レンズ A | — | 確認済み | `|| command_rc=$?` 捕捉 + 明示 `return "$cleanup_rc"` で伝播は保たれる。 |

## プラン v2 (実装子への確定指示)

### 1. `tools/pegasus/a5_second_boot_backoff_sweep.sh`

- `remove_worktrees()` から `local remove_rc=0` (:126)、`local prune_rc=0` (:127)、
  および `remove_rc=$cleanup_rc` から prune ブロック末尾までの `:155-166` を撤去する。
- 自 path remove 2 本 (ccbench 側 `:130-141`、repo 側 `:142-154`) は**そのまま残す**。
  どちらも当該 job が作った自 path であり、D1700 が問題にしている共有 gitdir 走査ではない。
- receipt 書式を次にする (逐語)。

```bash
  {
    printf '%s\n' "$cleanup_rc"
    [[ -z "$JOB_CCBENCH" ]] || \
      printf 'remaining_ccbench_path=%s\n' "$JOB_CCBENCH"
    [[ -z "$JOB_REPO" ]] || \
      printf 'remaining_repo_path=%s\n' "$JOB_REPO"
  } >"$OUTPUT_ROOT/env/worktree-remove.rc" || true
  return "$cleanup_rc"
```

- `WORKTREE_CLEANUP_CAP_S` を含む cap 定数は変えない (budget assert を再計算しない)。
- `|| true` は現行どおり残す (A1 は scope 外)。

### 2. `orchestrator/tests/test_a5_second_boot_job_contract.py`

- `:297-298` の 2 assert を**次の 1 つだけ**へ置換する。

```python
    assert re.search(r"\bworktree\s+prune\b", normalized_job) is None
```

- `count(...) == 1` の remove 逐語 pin、`"prune_rc" not in job`、
  `"ccbench-worktree-prune." not in job`、receipt の printf 逐語 pin は**足さない** (A3)。
  remove が実際に起きることと receipt の中身は下記 runtime test が固定する。
- 実 git fixture の test を 2 本足す。既存 self-run harness (`:374` 以降) が引数なしの
  `test_` 関数を直接呼ぶので、`pytest` の `tmp_path` fixture は使わず
  `tempfile.TemporaryDirectory()` を使う。helper は B-10 (`test_backoff_extended_sweep.py:46-88`)
  と同型のものを本 file 内に置く (B-10 module から import しない)。

  - **`test_a5_job_exit_cleanup_preserves_missing_sibling_worktree_registration`**
    (job rc 0 / 23 の 2 通りを 1 関数内で回す)
    - superproject 用と ccbench 用の 2 つの git repository を作り、`$JOB_REPO` と
      `$JOB_CCBENCH` を detached worktree として登録する。
    - 同じ ccbench repository に**兄弟 job の worktree**を登録し、その directory だけを
      `shutil.rmtree` で消す (別ノードにあって手元には無い状態の再現)。実行前に
      `git worktree list --porcelain` に兄弟 path が現れることを assert する。
    - job body から `remove_worktrees` と `cleanup_worktrees` を抽出し、
      `trap cleanup_worktrees EXIT` を張った snippet を走らせる。
    - assert: 終了 rc == 入力 job rc / 自 path 2 つの directory と登録が消える /
      **兄弟登録が残る** / `env/worktree-remove.rc` が `"0\n"` / 失敗 receipt stub 未呼出し。

  - **`test_a5_cleanup_failure_records_remaining_paths_and_preserves_exit_precedence`**
    (job rc 0 / 23 の 2 通り)
    - **A2 の是正**: 「登録されていない path」ではなく、**実際に登録された自 path 2 つを
      `git worktree lock` して remove を失敗させる**。`git worktree remove --force` は
      locked な worktree を消せないので、登録も directory も残る。
    - assert: receipt 1 行目が非 0 / 続く行が
      `remaining_ccbench_path=<path>` と `remaining_repo_path=<path>` /
      **その 2 path が実行後も `git worktree list --porcelain` に残っている** /
      job rc 0 のときは終了 rc が receipt 1 行目と一致し失敗 receipt stub が
      `worktree_cleanup` stage で 1 回呼ばれる / job rc 23 のときは終了 rc が 23 のままで
      stub は呼ばれない。
    - `write_failure_receipt` は snippet 内の stub で観測する。呼び手の同定は
      抽出した `cleanup_worktrees` の逐語が担うので、機構を stub で置換したことにはならない。

### 3. `orchestrator/tests/acceptance_duration_ledger.json`

- 追加した test node を `python3 tools/update_acceptance_duration_ledger.py --add-only <実走 JUnit>`
  で登録する。手で JSON を編集しない。**local main を取り込んだ後に 1 回だけ**行う
  (取り込み前だと `nodeid_count` 行で必ず衝突する)。

### 段 6 の焦点走に含める file

`orchestrator/tests/test_a5_second_boot_job_contract.py`、
`orchestrator/tests/test_acceptance_schedule_order.py`、
`orchestrator/tests/test_t1998_launcher_contract.py`、
`orchestrator/tests/test_t1998_stock_inline_pair.py`、
`orchestrator/tests/test_backoff_extended_sweep.py`、
`orchestrator/tests/test_hooks.py`、
`orchestrator/tests/test_official_perf_closure.py`。

## 変異事前登録 (DW-M01、実装前に確定)

対象 anchor は実装後の最終 commit で `DW-M07` に従い再検証する。

| ID | 位置 (実装後) | old 逐語 | 変異 | 期待 KILL node (完全集合) | 単一理由性 |
|---|---|---|---|---|---|
| M1 | `tools/pegasus/a5_second_boot_backoff_sweep.sh` の `remove_worktrees` 末尾 | `  return "$cleanup_rc"` | 直前へ `  timeout "$remaining" git -C "$CCBENCH_BASE" worktree prune --expire now || true` を挿入 | 静的 prune 不在 node + runtime 兄弟保存 node の**両方** | **冗長 gate**。2 層が同時に赤になるので、単独 gate の証拠には使わない (`DW-M03`)。 |
| M1b | 同上 | `  return "$cleanup_rc"` | 直前へ `  timeout "$remaining" git -C "$CCBENCH_BASE" worktree "pr""une" --expire now || true` を挿入 (静的 regex `\bworktree\s+prune\b` を通過する) | runtime 兄弟保存 node のみ | 静的層を通過するので、**runtime gate 単独**の検出力を示す。 |
| M2 | 同上 | `  return "$cleanup_rc"` | `  return 0` | runtime 失敗 node のみ | 掃除の失敗を成功へ変える唯一の変化。静的層はこの逐語を固定しない。 |
| M3 | 同上 (ccbench remove ブロック) | `    [[ "$command_rc" -eq 0 ]] && JOB_CCBENCH=""` | `    JOB_CCBENCH=""` | runtime 失敗 node のみ | 残置 path の記録だけを落とす。rc 伝播自体は残るので赤理由が残置明示の欠落に絞れる。 |
| M4 | `cleanup_worktrees` | `  if [[ "$original_rc" -eq 0 && "$cleanup_rc" -ne 0 ]]; then` | `  if [[ "$cleanup_rc" -ne 0 ]]; then` | runtime 失敗 node (job rc 23 側) のみ | 元 rc が非 0 の job の終了 rc を上書きする一変更。兄弟保存・静的層に影響しない。 |

M1 と M1b は同じ位置への挿入なので、`DW-M04` に従い**別々の走行**として適用する (累積しない)。

## 不変条件 (再掲・実装子へ)

- 既存テストの期待値を反転・緩和・skip・削除しない。今回意図する受理形の変更は
  「prune 正例 → prune の実行可能な不在」の 1 点だけ。
- 汎用の掃除機構・新しい gate・互換層・登録簿 schema を足さない。
- B-10 job body、投入器、`admission_registry.json` を変更しない。
- cap 定数と budget assert を変えない。

## この wave がやらないこと (記録して次へ渡す)

1. receipt 書き込み失敗の `|| true` を rc へ合成すること (A1)。
2. T-1998 の事前登録を新 digest で作り直すこと (人間認可を伴う別手番)。
3. Pegasus への計測投入 (D1700 は A-5 を再投入しないと明記)。
