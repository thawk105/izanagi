# 段 6 裁定 1 (計算前レビュー s6-review.md への裁定、2026-09-29 15:1x JST)

レビュー判定: NO-GO (所見 9)。親の気づき P-1〜P-3 (parent-checks.md) を含む。

| 所見 | 裁定 | fix の中身 |
|---|---|---|
| F1 (= P-1) must-fix | real・採用 | fix job は trace build・走行・判定を先に完了し、その後に CI 相当の build を行う。CI 相当の build の失敗は例外で止めず、rc・所要・log 末尾を result.json に記録して続行する。 |
| F2 (= P-2) must-fix | real・採用 | CI 相当の configure は上流 `external/ccbench/.github/workflows/build.yml` と同じ意味にする: `-DCMAKE_BUILD_TYPE=Release -DENABLE_SANITIZER=OFF` だけ (genome の define・`CCBENCH_TRACE` を渡さない)。compiler と依存物の供給 (FETCHCONTENT_SOURCE_DIR_*・CMAKE_PREFIX_PATH) は計算ノードで build するための環境として残し、その差を result.json に `ci_equivalence_notes` として書く。build.yml が実際に打つ command を読み、同じ target 範囲 (全体) にする。 |
| F3 must-fix | real・採用 | 起動器は run ごとに事前登録 (s4-ruling.md の「事前登録」) の条件を評価し、`result.json` の `prereg` に job・workload ごとの `expected`・`observed`・`match` を書く。終了値: 全 run が完走し照合器の到達可能性が pass で全 prereg が match → 0。照合器の到達可能性が pass でない run がある → 3。到達可能だが prereg と不一致 → 4。build・run・判定器の失敗 → 1。(c) は計数だけで期待は「D2b の違反 ≥ 1 の予想」を `expected` に書くが、不一致でも rc は 4 にしない (調査の計数)。 |
| F4 should | real・採用 | D2b(ii) の発生条件を「書き (W・M) のある取引」にする。複数回の書きの取引数は別の発生件数として残す。 |
| F5 should | **refuted** | `include/trace.hh` の `#if TRACE` は pin の 25 行〜124 行 (`#endif // TRACE`) で、追加の `#include <vector>` は 31 行 = 枝の内側。子の枝除去の bytes 一致とも整合。変更しない。 |
| F6 should | real・採用 (一部) | 自走 test は repo root を `--repo-root` 引数 (既定は従来どおり親 dir) で受ける。照合器は abort した試行を見る入力を持たない (Q は commit 後にだけ出る) ので、`test_valid_and_abort_attempt_excluded` を「abort を除外した」と主張しない名前に改め、abort の非混入は計装 patch の性質として報告に書く。 |
| F7 should | real・採用 | 起動器は build ごとの所要秒を result.json に残す (既存)。見積りは親が一次資料に書く (本 fix では変更不要)。 |
| F8 (= P-3) should | real・採用 | tar.gz を作り sha256 を採った後、trace dir を消す (tar の中身の file 一覧と各 file の byte 数を result.json に残す)。 |
| F9 should | real・採用 (強める) | 注記で済ませず、据えた値の刻印の tag `S` を、判定器 (`orchestrator/verifier/`) と CCBench の全 trace・witness 出力 (`include/trace.hh`・`cc/*/transaction.cc` の `#if TRACE` の中の出力行) で未使用の 1 文字 tag に改名する。第 1 候補 `V`、使用中なら `Z`。`Q` も同じ範囲で未使用であることを確かめ直す。 |
