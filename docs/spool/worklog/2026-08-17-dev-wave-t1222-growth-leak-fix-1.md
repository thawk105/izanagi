---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t1222-growth-leak-fix
seq: 1
title: 成長比例の既知漏れ 4 件を判定し、実際に成長していた 1 件だけを直した — 30 日の成長率実測が 4 件中 2 件の前提を覆し、レビュー関門は repo 自身の非 NFC fixture で塞がった (コード + テスト + docs、branch worktree-dev-wave-t1222-growth-leak-fix、変異 matrix = 5/5 KILLED)
---

## 本文

ユーザー裁定 (2026-08-17 /rulings 全件 第 4 回) は「4 件を恒久保留へ登録する案を却下。
各件についてテスト側か対象側かを判定し、該当する側を直す」だった。判定の結果、
**実装したのは 1 件だけ**である。残り 3 件は「欠陥なし」1 件と「新事実つきでユーザー裁定へ返す」2 件になった。

### D463 が要求する成長率を実測したら、4 件中 2 件の前提が覆った

`git ls-tree -r -l` を 30 日前・14 日前・7 日前・現在の 4 時点へ適用した。

| 入力集合 | 30 日前 | 現在 | 倍率 |
|---|---|---|---|
| `.claude/agents` | 13f/84,264B | 13f/83,157B | 1.0 (微減) |
| `.codex/role-adapters` | 13f/171,155B | 13f/172,000B | 1.0 |
| `test_dev_waves_integration.py` | 不在 | 119,456B (14 日前から不変) | 1.0 |
| `tools/task_runs` | 不在 | 7f/138,785B (14 日前から不変) | 1.0 |
| `docs` 全体 | 2,047,235B | 14,999,488B | 7.3 |
| `docs/archive` | 674,988B | 9,979,917B | 14.8 |
| commit 総数 | 487 | 4,192 | 8.6 |

**実際に成長しているのは項目 3 (docs) と項目 4 (commit 履歴) だけだった。**
項目 1 と 2 の入力集合は、repo が 7〜15 倍になる間まったく増えていない。

### 4 件の判定

- **項目 1 (`test_codex_agents.py` 7 node) = 欠陥なし。** D463 第 3 区分
  「比例だが設計上限のある固定用途集合」。テストは全 role の全称命題を検査しており、
  入力を縮めると未検査 role が生じる。production も全単射を fail-closed に検査する必要がある。
  実装差分なし。**「非比例」ではない** — 親は当初そう判定しかけたが、両レンズが独立に
  D463 の語義違反だと指摘し、撤回した。
- **項目 2 (`test_dev_waves_integration.py` 1 node) = test-side の欠陥は実在。ユーザー裁定へ返す。**
  1 関数のために 2,726 行の test module 全体を fresh subprocess が import している。
  ただし (a) その比例軸は実測 0.214 秒 (node 全体 4.23 秒の約 5%、支配項は copytree/git/daemon)、
  (b) 入力集合は 14 日間不変、(c) 期待赤 node を同 file に no-group で置くと
  `test_dev_waves_isolation_contract.py` の AST 伝播検査が赤になり、`xdist_group` を付けると
  D452 (c) で変異登録が無効になるため**検出力の証明が構造的に不能**、(d) child 閉包は
  `_run_long_path_serve_harness` → `_isolated_process_environment` / `_temporary_repo` /
  `_supervisor` / `_ServeSelectProxy` / `daemon_mod` に達し小さくない。
  この 4 点を踏まえて大きな refactor を打つ価値があるかを裁定へ返す。**保留ではない。**
- **項目 3 (`test_s8c_preregistration_invariant.py` 1 node) = target-side。本 wave で直した。**
- **項目 4 (`test_check_ai_provenance.py` 2 node) = 直さない。ユーザー裁定へ返す。**
  全史走査は無駄ではなく**権威境界そのもの**だった。
  `test_known_violation_off_head_policy_guard_is_stale_rc2` は、policy 導入 commit が HEAD から
  到達できない木で rc=2 と `reason=policy-epoch-not-visible non-authoritative-invocation` を
  固定している。段 2 プランどおり selected commit の祖先閉包から epoch を探すと、
  この防壁が発火せず **rc=2 が rc=0 へ反転する**。同型の fail-open は 2026-08-07 に一度作られて
  却下された経緯がある。memoize では比例が消えず (呼び出しは 1 監査 1 回)、resolver の引数化は
  zero-argument の既存 monkeypatch を TypeError で壊す。実コストは git 単体 0.034 秒 / 4,192 commit。
  受理集合を変える改修なので新しい裁定が要る。

### 項目 3 の真因は「同じ file を 2 通りの newline で読んでいた」ことだった

段 2 プランは `LIVING_DOCS` の singleton 化を提案したが、親の実測で **削減 0.9%** しかなく
(4.794 → 4.753 秒)、さらにレンズ A が「`assert injected` が自己充足になり、
実 `LIVING_DOCS` が複数件のときだけ 8c 文書を飛ばす reward-hack 変異が緑で通る」と指摘したため却下した。

真の比例源は `check_docs.main()` が同じ file を `newline=None` と `newline=""` の
2 通りで読んでいたことである。物理 `Path.open` は **1,141 回 / distinct 673 file / 468 file が 2 回**
だった。`main()` 1 回の内側にだけ生きる読取 cache を入れ、物理読取だけを共有した。

- 物理 open: **1,141 → 673 (平均 1.695 → 1.000、2 回開かれた file 468 → 0)**
- `main()` median: **4.539 → 4.173 秒**
- テストは 1 行も変更していない。よって当該 node は実 `main()` を end-to-end で走らせ続け、
  **実 `main()` を既定で走らせる最後の node** という性質が保たれた
  (`test_check_docs.py::test_real_repo_clean` は恒久保留済み)。

**「比例が消えた」とは書かない。** 消えたのは重複 open/decode であり、安全検査 (約 462 回) と
本文の二重走査は残る。node は依然 `Θ(corpus bytes)` である。

### レビューが「壊れても誰も気づけない」と判定し、テストを足して閉じた

段 6 の敵対レビュー 2 本が独立に同じ must-fix を出した。cache の正しさを守る既定走行 node が
1 つも無く、**cache を丸ごと無効化しても既存テストは全部通っていた**。規律 3 の直撃である。
検査を減らさず、4 node を新設して閉じた。

さらにレビュー B が「cache hit は `main()` 実行中の regular file 差し替えを見逃す」と指摘した。
`lstat()` は cache 参照より前に毎回呼ばれているので、その結果から
`(st_mtime_ns, st_size, st_ino, st_dev)` を entry に持たせて照合する形にした。**追加 syscall はゼロ。**
4 値が一致したまま本文だけ変わる差し替えは既知の残差として残す。

### そのテストにも穴があり、レビューがそれを見つけた (第 2 巡)

第 1 巡の 4 node に対して変異 5/5 が KILLED になったが、**それでも不十分だった。**
段 6 の最終レビューが「本 wave が直した比例源そのものに専用の防壁が無い」と指摘し、
親が実測で再現した。

`raw = cache.get((path, ""))` を `raw = None` にする変異 (cross-mode 共有だけを無効化) は、

- 新設 4 node を **全通過** (4 passed)
- `Path.open` を **673 → 1,140**、2 回開かれる file を **0 → 467** に戻す

**wave の改善を丸ごと消す変異が誰にも検出されない状態だった。**
既存 node は「同じ newline mode を 2 回読む」形で、cross-mode 経路を見ていなかった。

同じレビューが 2 件目の実在欠陥も出した。identity が `st_mode` を含まないため、
初回読取の後に `chmod 000` すると:

| | 2 回目の戻り値 | finding |
|---|---|---|
| 旧挙動 | `None` | `PermissionError` を出す |
| 第 1 巡時点 | **cached text** | **なし** |

**実行中に読取不能になった文書を旧版は拒否し、新版は黙って受理していた。**
親が `parent-verification.md` に書いた「受理集合が変わっていない」は、この経路で誤りだった。
第 2 巡で identity へ `st_mode` と `st_ctime_ns` を足して塞ぎ、記録も訂正した。
どちらも取得済みの `path_stat` から取るので**追加 syscall はゼロ**である。

さらに identity の fixture が過剰決定 (size・inode・mtime を同時に変える) だったため、
inode のみ / mtime のみを変える node へ分離した (DW-M03)。

新設 node はすべて `tmp_path` と `REPO` monkeypatch だけを使い実 corpus へ到達しないので、
**成長比例テストを新設していない** (D335)。保留台帳は 59 のままで新規登録ゼロ。

### 親が自分の証拠を 2 か所訂正した

- 「物理読取 1,133 → 673」は `_safe_read_text` 呼び出し数と `Path.open` 数を混ぜた比較で、
  **同一計測面ではなかった** (レンズ A)。同じ計測器で測り直して 1,141 → 673 に改めた。
- 差分検査は `sorted()` した行を比べており、**finding の順序不変を証明していなかった** (レンズ B)。
  raw stdout 比較へ直して取り直し、順序込みで一致することを確かめた。

### 台帳の「7 件」は grep では再現しない

権威ある閉包は先 wave の逐語 `output/insights/2026-08-16_t1222-growth-hold-sweep/verbatim/s3-lensA.md`
にあり、`test_codex_agents.py:121-124, :127-150, :164-213, :216-230, :233-249, :511-519, :1300-1307`
の 7 個だった。親が grep で数えた 9 個も、段 2 プランが挙げた 7 個も別集合だった。
**件数を書く前に権威ある閉包を探すべきだった。**

### 段 6 のレビュー関門が repo 自身の非 NFC fixture で塞がった ({{F:codex-evidence-nfc-fixture}})

`--stage review` 3 本と `--stage fix` 1 本が `accepted=False` / `evidence_status=invalid` になった。
子はいずれも正常完走 (`codex_exit_code=0` / `validator_rc=0` / `termination_verified=True` /
出力 4.6〜10.5 KB / `## 総括` あり) で、**内容の問題ではない**。

根本原因は `orchestrator/tests/test_check_docs.py:4718, 4741` が NFC 検査用に持つ
**意図的な非 NFC 行** (`プ` を `フ` + U+309A の結合列で書いたもの) である。段 6 の子はこの file を
読むのが仕事なので、その行が codex の stdout event 列へ載り、launcher の `parse_jsonl` が
「JSONL は Unicode NFC でなければならない」で拒否 → `stdout_invalid` → 不受理、という連鎖になる。
成功した plan / consult×2 / author はこの領域を読んでいない。

親は `turn_context` の model/effort 一致、`session_meta` の cwd 一致、`session_meta_count`、
`context_count`、rollout と events の parse 可能性、rollout 重複、4 MiB 行長、job dir 資料の NFC を
順に潰したうえで、launcher の `parse_jsonl` を各子の event 列へ適用して拒否行を特定した。
**回避策**: 子に当該領域を読ませず、NFC 清潔と確認済みの `git show <commit>` で差分を監査させる。

## 次の一手差分

### 更新

- [T-1222] **P1・部分完了 (項目 2 と 4 はユーザー裁定へ返す)**: 成長比例の既知漏れ 4 件を判定した。
  30 日の成長率実測 (`git ls-tree -r -l` 4 時点) で、実際に増えているのは項目 3 (docs 7.3 倍 /
  archive 14.8 倍) と項目 4 (commit 8.6 倍) だけだと分かった。**項目 3 を直した** —
  `check_docs.main()` が同じ file を `newline=None` と `newline=""` の 2 通りで読んでおり、
  物理 `Path.open` が 1,141 回 / distinct 673 file (468 file が 2 回) だった。`main()` 1 回限定の
  読取 cache で **1,141 → 673 回、median 4.539 → 4.173 秒**。テストは変更せず、実 `main()` を
  既定で走らせる最後の node の性質を保った。段 6 レビューの must-fix (cache の正しさを守る
  既定走行 node がゼロ) を 4 node 新設で閉じ、変異 5/5 KILLED。**項目 1 は欠陥なし**
  (D463 第 3 区分、実装差分なし)。**残件** = 項目 2 (test-side の欠陥は実在するが、比例軸 0.214 秒・
  入力 14 日不変・変異検証が構造的に不能・閉包が大きい) と項目 4 (全史走査は権威境界そのもので、
  変えると却下済みの off-HEAD fail-open が復活する) の 2 件をユーザー裁定へ返す。
  母集合の未閉包も引き続き未了。
  base: 55b713e8272d189120c39e5cad8e01d4592de6adede819d74f213eb08b7d5181
