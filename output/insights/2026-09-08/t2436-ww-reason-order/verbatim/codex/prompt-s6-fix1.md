単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order

必読事項の射影:

- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_verifier.py` — 修正対象。`test_multi_ww_reason_report_is_hash_seed_deterministic` は 1592 行目付近。読めなければ即停止。
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2436-ww-reason-order/s6-review-B.md` — 所見の逐語 (「環境依存」節の 2 件)。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/orchestrator/tests/test_pytest_collection_config.py` — 141-152 行目に `timeout=120` の先例がある。読めなければ即停止。
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order/output/insights/2026-09-08_t2436-ww-reason-order/verbatim/s4-ruling.md` — 親の段 4 裁定。読めなければ即停止。

**あなたが編集するのは
`/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2436-ww-reason-order` 配下だけである。**

## 状況

verifier の理由列挙を key 順に整列する変更は **commit 済み** (HEAD = `c3f130e34`)。
実装 (`orchestrator/verifier/dsg.py` の 1 行) と新テスト 1 本が入っている。
段 6 の敵対レビュー 2 本のうち 1 本が、**新テストの運用面に must-fix を 2 件**出した。
親はこの 2 件を採用した。**あなたはこの 2 件だけを直す。**

## 直す対象 (これ以外は 1 byte も触るな)

`orchestrator/tests/test_verifier.py` の
`test_multi_ww_reason_report_is_hash_seed_deterministic` だけ。

## 修正 1 — subprocess の timeout を 120 秒へ上げる

現在 `timeout=30` になっている。共有 login node の高負荷時に、正しい実装が負荷だけで
偽赤になる。この repo には「負荷の高い login node が短い timeout の subprocess テストを
落とす」実績があり、同種の subprocess テストの先例は **120 秒**である
(`orchestrator/tests/test_pytest_collection_config.py:141-152`)。

`timeout=120` にする。健全時の所要は変わらない (親の実測で 2 process 合計 0.22 秒)。

## 修正 2 — 失敗したときに原因が読めるようにする

現在 `check=True` で `stderr=subprocess.PIPE` を使っているため、子が非ゼロ終了しても
例外の文字列に stderr が出ず、**import 失敗・verifier の失敗・環境異常を区別できない**。

次のように直す。

- `check=True` をやめ、`check=False` (既定) で受ける。
- `returncode == 0` を **assert する**。assert message には少なくとも
  **seed、returncode、stdout の末尾、stderr の末尾**を載せる。
  stdout / stderr は長くなりうるので、**末尾を一定 byte 数で切って**載せること
  (切る長さは適当な定数でよい。値をテスト外の設定にしない)。
- `subprocess.TimeoutExpired` も捕捉し、**その例外が保持している stdout / stderr を
  assert message に載せて**失敗させる。timeout が握り潰されて別の場所で分かりにくく
  落ちる形にしない。

## 変えてはならないもの

- **検査の中身を 1 つも弱めない。** 現在の assert
  (2 本の stdout の bytes 一致、辺 `0->1` の理由列が ww 昇順、`verdict`、`serializable`、
  `anomaly_count`、`total_cycles`、`phenomenon`) を**すべてそのまま残す**。
  緩める・削る・skip する・xfail にすることを禁じる。
- **`certified` を assert しない。** 過剰決定なので親が意図的に外している。comment もそのまま残す。
- **SHA-256 の比較 assert を足さない。** bytes 一致から従うので冗長である。
- seed は `"1"` と `"777"` のまま。増やさない。key も 6 個のまま。
- **既存テストの期待値を 1 つも変えない。** 反転・緩和・skip・削除を禁じる。
  もし赤になったら実装側が誤りである。期待値のほうが誤りだと判断したら、
  **実装を変えず、報告して止めること。**
- `orchestrator/verifier/dsg.py` を変更しない。
- trace の中身 (key 数、transaction、行の形) を変えない。
- 一時 trace の `finally` での削除を外さない。

## 禁止事項 (すべて明示的に禁じる)

- **`git add` / `git commit` を絶対に実行しない。** commit は親が行う。
- **docs を編集しない。** `docs/` 配下への file 作成 (handoff を含む) も禁止。
- `orchestrator/tests/fixtures/`、`orchestrator/tests/acceptance_duration_ledger.json`、
  `orchestrator/verifier/` のいずれも変更しない。
- 新しい test file を作らない。gate・検査・台帳・互換層を新設しない。
- 期待値へ揮発する値 (hash、時刻、絶対 path) を焼き込まない。
- probe や使い捨て script を repo 内へ置かない。

## 走らせ方 (この sandbox の制約)

- **`tools/run_tests.py` と `python -m pytest` は使えない** (前者は rc=16、後者は guard が拒否)。
- 走るのは `PYTHONPATH=. python3 orchestrator/tests/test_verifier.py` の自走 harness だけである。
  worktree root を cwd にして走らせること。
- 直したあと、**わざと失敗させて assert message に seed / rc / stderr が載ることを
  自分で確かめること。** 確かめ方は自由だが、**その確認のために repo の file を
  恒久的に変更してはならない** (確認後に必ず元へ戻すこと)。戻したことを報告に書け。
- 実走できなかったものは「実装済み・未実走」と正直に書く。
  **実走していないものを緑と書いてはならない。**

## 報告に必ず含めること

- 変更した箇所の diff。
- 実走した nodeid と結果。
- 失敗時 message の確認方法と、確認後に元へ戻したことの明示。
- 検査を 1 つも弱めていないことの確認 (残した assert の列挙)。
- 予算が尽きそうなら途中結論を出力形式どおりに書いて終われ。無出力が最悪である。
- 結合文字 U+0300〜U+036F を出力に使ってはならない。
- 日本語で書け。

## 出力形式

次の見出しをこの順で、すべて `##` (H2) で書く。`###` を使ってはならない。
最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。

## 変更した箇所の diff
## 実走した nodeid と結果
## 失敗時 message の確認
## 残した assert の列挙
## 総括
