単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order

必読事項の射影:

- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s4-ruling.md` — **親の段 4 裁定。これが確定仕様である。** 読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s1-probe.md` — 親の実測値 (期待値の出所)。読めなければ即停止。
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s2-plan.md` — 段 2 のプラン。**裁定と食い違う箇所は裁定が勝つ。** 読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/verifier/dsg.py` — 変更対象。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_verifier.py` — テストを足す先。読めなければ即停止。

上記はすべてこの worktree または job dir の絶対パスである。**あなたが編集するのは
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order` 配下だけである。**

## 依頼

verifier の理由列挙が実行のたびに順序を変えるため、同じ trace から違う要約値が出る。
これを直す。**親の段 4 裁定 (`s4-ruling.md`) の第 9 節「plan v2 (確定)」が仕様の正本である。**
そこに書かれた 2 つの変更だけを行う。

## 現行の受理・拒否挙動 (変えてはならない基準線)

親が実測した現行挙動である。**この値を 1 つも変えてはならない。**

- 対象の合成 trace (6 key の 2 transaction lost-update) に対し、
  `verdict = "non-serializable"`、`serializable = False`、`certified = False`、
  `anomaly_count = 1`、`total_cycles = 1`、`anomalies[0].phenomenon = "G2"`、
  `anomalies[0].cycle = [0, 1]`、`anomalies[0].length = 2`。
- これらは `PYTHONHASHSEED` を変えても同じである。変わるのは辺 `0->1` の ww 理由の**順序だけ**。
- **anomaly の検出条件を変えてはならない** (このプロジェクトの絶対規律 2)。
  理由の**集合**は不変で、順序だけを決めること。

## 編集してよい path (これ以外は 1 byte も触るな)

1. `orchestrator/verifier/dsg.py` — `_reasons()` の WW 交差の走査 1 箇所だけ。
2. `orchestrator/tests/test_verifier.py` — テスト関数を 1 本足すだけ。

## 禁止事項 (すべて明示的に禁じる)

- **`git add` / `git commit` を絶対に実行しない。** commit は親が行う。
- **docs を編集しない。** `docs/` 配下への file 作成 (handoff を含む) も禁止。
- `orchestrator/tests/fixtures/` へ file や directory を足さない。
- `orchestrator/tests/acceptance_duration_ledger.json` を変更しない。
- `orchestrator/verifier/` の他の file (`model.py`、`parse.py`、`report.py`、`core.py`) を変更しない。
- 既存テストの期待値を変えない。既存テストを xfail 化しない。
- 新しい test file を作らない。
- gate・検査・台帳・互換層を新設しない。
- 期待値へ揮発する値 (working tree の hash、時刻、絶対 path など) を焼き込まない。
- fixture へ現行 hash を差し込むなど、テストを甘くして緑にしない。
- probe や使い捨て script を repo 内へ置かない。

## 実装 1 — `orchestrator/verifier/dsg.py`

`_reasons()` の中の

```python
for k in u_writes.keys() & v_writes.keys():
```

を、共通 key を**文字列の昇順**で走査する形へ変える。整列 key は key 文字列そのものとする
(版を含むタプルにはしない。親が「同一 key に複数の WW 理由は構成できない」ことを確認済み)。
**この 1 行以外、この file を変更してはならない。**

## 実装 2 — `orchestrator/tests/test_verifier.py`

関数名は `test_multi_ww_reason_report_is_hash_seed_deterministic` とする。
`test_structured_report_has_edge_detail()` の直後あたりに置く。仕様は次のとおり。

- key は `0000000000000001` から `0000000000000006` までの 6 個。
- trace は既存 helper `_tmp_trace()` で一時生成する。**1 file に 2 transaction** を置く。
  中身は次の形にする (親が実測に使ったものと同一)。

```
C 0 0 1 1 6 6
R 0 <key> 1 0        (6 key ぶん)
W 0 <key> U 1 1      (6 key ぶん)
E 0
C 1 1 1 2 6 6
R 1 <key> 1 0        (6 key ぶん)
W 1 <key> U 1 2      (6 key ぶん)
E 1
```

- `PYTHONHASHSEED` を `"1"` と `"777"` に設定した subprocess を 2 本立てる
  (`sys.executable` を使い、`cwd` は module 冒頭の `_REPO`)。
  各 subprocess は `verify_trace_dir(<trace dir>, workers=1)` の結果を `result_to_dict()` し、
  `json.dumps(..., sort_keys=True, separators=(",", ":"))` を stdout へ書く。
- assert するのは次だけである。
  1. 2 本の stdout の **bytes が完全に一致する**こと。
  2. 各 report で、辺 `0->1` の理由列が `[("ww", key) for key in keys]` (key 昇順) と一致すること。
  3. 各 report で `verdict == "non-serializable"`、`serializable is False`、
     `anomaly_count == 1`、`total_cycles == 1`、`anomalies[0]["phenomenon"] == "G2"` であること。
- **`certified` を assert してはならない。** この合成 trace では protocol の proof-surface
  metadata が無いため `integrity.clean()` が False になり、`certified is False` は
  「cycle があるから」と「integrity が unclean だから」の 2 つの独立な理由で成立する
  (過剰決定)。**この理由を 1 行の comment としてテスト内に残すこと。**
- **SHA-256 の比較 assert を置いてはならない。** bytes 一致から数学的に従うので冗長である。
- `finally` で一時 trace directory を `shutil.rmtree(..., ignore_errors=True)` で消すこと。
- module 冒頭には `hashlib` `json` `os` `subprocess` `sys` がすでに import されている。
  `shutil` は関数内 import で足りる (既存テストと同じ流儀)。
- テストは既存 file の**素の自走 runner** (file 末尾) が拾えるよう、**引数を取らない**
  `test_` 関数にすること。

## 走らせ方 (この sandbox の制約)

- **`tools/run_tests.py` と `python -m pytest` は使えない** (前者は dispatch preflight で rc=16、
  後者は guard が拒否する)。
- 走るのは `PYTHONPATH=. python3 orchestrator/tests/test_verifier.py` の自走 harness だけである。
  worktree root を cwd にして走らせること。
- **重要 — 未 commit 由来の赤を実装の回帰と読むな。** `orchestrator/verifier/dsg.py` は
  campaign の enforcement source closure に入っており、未 commit の変更があると
  `contract-loader-drift` (記録 commit blob と disk bytes の不一致) を出す検査が**発火しうる**。
  これが出たら、それは本実装の回帰ではない。**赤の nodeid と失敗 reason をそのまま報告し、
  自分で回避しようとしないこと。** commit は親が行う。
- テストを足したら、**新設テストの制約 meta-test を自分で洗い出して走らせること。**
  親の名指しを網羅と見なさない。少なくとも同 file 内の
  `test_all_v2_fixture_files_have_clean_framing` と、素の自走 runner の網羅検査に
  掛からないかを確認せよ。

## 報告に必ず含めること

- 変更した file と行の一覧 (diff そのものを貼ってよい)。
- **実走した nodeid と結果。** 実走できなかったものは「実装済み・未実走」と正直に書く。
  **実走していないものを緑と書いてはならない。**
- 赤が出た場合はその内訳。未 commit 由来か実装由来かの区別も書く。
- 所有外の呼び手・共有 fixture・consumer test への波及可能性の静的な列挙。
- 指示外の受理集合変更を一切していないことの確認。

## その他の制約

- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。
  作業ツリーの差分は残るので、途中まででも「どこまでやったか」を必ず書け。
- 結合文字 U+0300〜U+036F を出力に使ってはならない。
- 日本語で書け。

## 出力形式

次の見出しをこの順で、すべて `##` (H2) で書く。`###` を使ってはならない。
最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。

## 変更した file と diff
## 実走した nodeid と結果
## 赤の内訳
## 波及可能性の静的列挙
## 総括
