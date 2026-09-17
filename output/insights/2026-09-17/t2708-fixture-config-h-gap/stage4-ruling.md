## 段 4 裁定 (2026-09-17 22:58 JST、親)

### 所見の裁定

レンズ A (正しさ境界、11 件) とレンズ B (整合・実効性、12 件) の所見を real / refuted / 判定不能で受理し、採否を決めた。

| # | 所見 | 裁定 | 採否・扱い |
|---|---|---|---|
| A1, A9, A11, B11 | 「射影集合との差」は実 repo 全体への忠実性一致を保証しない。419/418/1 と untracked 0 は再確認できたが、「untracked 0」は非 ignored に限る (ignored は 9 件、全部 `__pycache__/*.pyc` で copytree 除外) | real | 採用。本 wave の主張を「config.h の追加的な可視性回復」に限定し、集合比較は fixture 側 3 集合 (index / `enumerate_repository_files` / scan 除外後) と期待集合 E の差で報告する。brief の記述を訂正 |
| A2, A3, A4 | copytree の名前除外・basis 上書き・submodule pin・receipt/draft 除外は fixture と実 repo の scan 集合を別方向にずらす構造 | real (現在の欠落は反証なし / 判定不能) | scope 外。裁定パッケージの「関連する観察」に載せ、実装しない |
| A5, B5 | 現在の config.h (三軸語 0 件) を basis commit 前に追加して新規発行する限り、受理・拒否が変わる経路なし。13 scan は検算一致 | refuted (反証なし) | 採用。判定不変の主張は「現在の bytes・正しい basis 再導出に限定」と書く |
| A6, B6 | basis / HEAD / receipt bytes の束縛は存在し、index 切替 probe は発行 A/B の代替にならない。「取り込み + 13 × scan 差」は部分モデル | real | 採用。probe の主張範囲を「列挙・scan の差と所要、取り込み操作の所要」に限定し、発行全体の wall は未測定と明記 |
| A7 | 既存の可視性検査は取り込み削除変異を殺さない | real (静的) | 採用。採用 wave の変異事前登録は新規 membership assert に依存すると明記 |
| A8 | config.h に将来 conjunction が入る現実性は判定不能 | 判定不能 | 採用。DW-G05 を「実 repo の既存成果物は不変 / fixture の report・basis・receipt bytes は変わる / 将来の検出力差は機械的には real、現実性は判定不能」の 3 つに分けて書く |
| A10, B10 | login node での所要測定は runbook §7.0.0「性能測定は常に計算ノード」に反する。「ms 級」は未証明 | real | 採用。**実走場所は計算ノード (generic dispatch)**。login 先行の 2 段案は採らない。brief の実測環境と P3 を訂正 |
| B1, B2, B3 | index 切替は保存した A/B index の復元で行う。config.h は index から外すと ignored untracked になり列挙から消える (期待どおり)。`GIT_INDEX_FILE` 回避は正しい | real / refuted / real | 採用。probe は A/B の `.git/index` を fixture 外へ保存して復元し、timed 区間は `search_repository(root)` だけ。probe 起動環境から `GIT_*` を除く |
| B4 | N=20 対で分離できる根拠なし。分離できなければその事実を成果とする | 判定不能 | 採用。warm-up 2 対 + N=20 対を事前固定し、対差の中央値・IQR・min/max・正負の数・順序別対差・生データを返す。「増分を分離できなかった」も正の成果と扱う |
| B7 | 一般解 419 path は必ずしも再 hash しない。hard-code (1 path) との差は測る価値あり。A index は commit 後なので採用位置 (add -A 直後・commit 前) と cache 状態が違う | real | 採用。取り込み操作は一般解と hard-code の両方を各 N_add=10 回 (A index 復元 → timed)、初回と反復を分けて記録。限界を明記 |
| B8, B9 | 直接 import は静的に成立可能、退避後の `-m tools.<probe>` は namespace package で解決可。実成功は未確認 | 判定不能 / refuted | 採用。probe は `__file__` の解決先・source HEAD を出力に記録。親が実走で確認 |
| B12 | 一般解は 1 行でない、hard-code は snapshot 不要、D2086 の 10% は転用不可 | refuted (plan は妥当) | 採用 |
| B (時間許容値) | critical path への追加 1 秒以内を費用許容値の提案とする。13 scan 換算で 77 ms/scan が目安 | 提案 | 採用 (裁定パッケージの提案値。既存裁定ではないと明記) |

### プラン v2 (probe 仕様、段 5 の Codex author へ)

- 置き場: worktree 内 `tools/t2708_fixture_gap_probe.py` (author が書く)。親が実行前に job dir `probe/tools/` へ退避し worktree を clean に戻す。repo へは commit しない。
- 起動: `python3 -B -m tools.t2708_fixture_gap_probe --source-root <worktree 絶対 path> --work-root <repo 外の書込可能 dir> --out <json path> [--pairs 20] [--warmup 2] [--add-repeats 10] [--selftest]`。cwd = worktree root、`PYTHONPATH=<job dir>/probe`。
- probe 自身が最初に環境を整える: `GIT_DIR` / `GIT_WORK_TREE` / `GIT_INDEX_FILE` 等 `GIT_*` を除去、`TMPDIR` / `TEMP` / `TMP` を `<work-root>/tmp` に、`PYTEST_XDIST_TESTRUNUID` を除去。その後に `orchestrator.tests.test_s8b_oracle_driver` を import する (それ以前に `tempfile` を呼ばない、conftest を import しない)。
- 手順: (1) 記録 (source HEAD、git / python version、config.h の sha256 と size、2 本の `.gitignore` の sha256、probe の `__file__`)。(2) `_build_t080_stub_free_e2e_repo(work_root/..., issue_receipt=False)` を 1 回 (所要は参考値)。(3) A index (`.git/index`) を fixture 外へ保存。(4) 集合: fixture の `git ls-files -s -z` regular 集合、`enumerate_repository_files(root)`、`search_repository` の除外後集合 (`search.file_count`)、期待集合 E (source の `orchestrator/` 実体 regular file から `__pycache__` / `*.pyc` を除いたもの ∪ `_git_visible_output_paths(source)` − receipt/draft ∪ basis 上書き path ∪ `.gitmodules`)。E − A、A − E を列挙。(5) 取り込み操作の所要: 一般解 (source で `git ls-files -z -ci --exclude-standard -- orchestrator output` → fixture で `git add -f --pathspec-from-file=- --pathspec-file-nul`) と hard-code (`git add -f -- orchestrator/tests/fixtures/sort_swo_masstree/config.h`) を各 N_add 回、毎回 A index を復元 (timed 外)、列挙・add・一連 wall を別々に `perf_counter_ns` で。初回と反復を分ける。存在しない path が pathspec に入った場合は失敗として記録 (黙って捨てない)。(6) B index を保存し、B − A == {config.h}、A − B == ∅ を確認。(7) scan 対比較: warm-up 2 対 + N 対、AB / BA 交互、各回 index 復元 (timed 外) → `search_repository(root)` (timed)。A/B の report で `match_convention` / `holdouts` / `positive_control` と `_live_scan_sha256` が同一、`search.file_count` が +1 であることを確認 (不一致は失敗として記録)。(8) JSON 出力: 生データ全件、対差、順序別対差、中央値、IQR、min / max、正負の数、取り込み所要の統計、集合差、記録項目。
- `--selftest`: 小さい合成 git repo (tracked-and-ignored file 1 件を含む) で「index の保存 / 復元で `ls-files` 集合が往復する」「集合差計算が期待どおり」「存在しない path の force-add が失敗として記録される」の 3 点だけを検査する。builder は呼ばない。
- 主張範囲の限定 (出力 JSON と親の記録に書く): 発行 A/B ではない (B index は staged addition で `M:1833` の clean 条件を満たさない)。取り込み費用の A index は commit 後で採用位置と cache 状態が違う。所要モデル「取り込み + 13 × scan 差」は部分モデル。
- 実走場所: 計算ノード。runbook §7 の generic dispatch で、command は上記の起動形。work-root は job 側の書込可能領域 (計算ノードから見える `/work/1/SFC/tanab/dev-wave-jobs/<wave>/` 配下)。
- 変異 matrix: 実装面の差分ゼロ (probe は commit しない) で免除。受入全走は免除しない (段 7 の記録後、land 前に 1 回)。

### 採否の判定基準 (結果を見る前に固定)

- 忠実性の増分 = B − A が {config.h} だけであり、E − B が E − A より 1 件少ないこと。判定不変 = A/B の semantic report と `_live_scan_sha256` が同一。
- 所要増分 = 「一般解 or hard-code の取り込み操作 (反復中央値) + 13 × scan 対差の中央値」を換算値として提示し、費用許容値の提案 1 秒と比べる。ただし区間 (IQR) が許容値をまたぐ、または非 scan 項が結論を左右するなら「費用上限未確認」と書く。分離できなかった場合は「分離できなかった」と書き、ms 級とも秒級とも断定しない。
- 採否はユーザー裁定へ返す (本 wave は実装しない)。推奨は測定後に書く。

### brief の訂正

- 実測環境: login node → 計算ノード (generic dispatch)。
- P3: 「ms 級」→ 未測定。一般解は 419 path を処理する。
- P4: 「1 手・件数非依存」→ 一般解は NUL 転送・空集合・非コピー対象 (receipt/draft、`*.pyc` が将来 tracked-and-ignored になった場合) の扱いが要り 1 行ではない。hard-code は snapshot を要しない。
- DW-G05: 「レポート・台帳は変わらない」は実 repo の既存成果物に限る。fixture の report (`file_count`)、basis OID、receipt は変わる。
- 「untracked 0 件」→ 非 ignored untracked 0 件、ignored 9 件 (全部 pycache で copytree 除外)。
