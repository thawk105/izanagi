## 偽の緑

- **refuted / nit** — `config.h` 欠落時の skip や preprocess 省略は入っていない。manifest 非 `None` 時も prepare 後に通常どおり capture、supply、meaning、admission を通る。[screening_driver.py:189-240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:189)
- 非 stock 入力が緑になる条件は、依存 closure が一致し、requested/control の preprocess bytes が異なる場合のままである。[condition_meaning_gate.py:2606-2621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/condition_meaning_gate.py:2606)
- 現在の唯一の赤は `configure-failed` であり、偽の緑ではない。

## 判定式の同一性

- **refuted / nit** — 変更前後を空白無視でも照合した。次はすべて同一である。

  - request 空判定と build-route 検査: [screening_driver.py:183-186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:183)
  - supply evaluator と meaning evaluator の引数・反復順: [screening_driver.py:212-223](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:212)
  - `use_class="raw"` を含む family admission: [screening_driver.py:224-226](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:224)
  - red record の抽出条件、例外型、reason code、detail 文言: [screening_driver.py:227-237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:227)
  - stock 比較述語と checkout 引数: [screening_driver.py:249-264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:249)

- 既存 call の唯一の意味上の変更は、capture へ渡す configure args に同じ一時 base を追加できるようにした箇所である。[screening_driver.py:188-210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:188)

## 正例の load-bearing 性

- **refuted / nit** — 正例が恒真という懸念は反証できる。owner TU は fixture 内にない header を必須 include し、CMake は一時 base だけを include path にする。[transaction.cc:1-7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/fixtures/condition_meaning_gate/prepared-base-required/cc/silo/transaction.cc:1) [CMakeLists.txt:8-9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/fixtures/condition_meaning_gate/prepared-base-required/CMakeLists.txt:8)
- prepare stub は受け取った base に header を実際に作る。capture、CMake configure、supply evaluator は本物であり、requested/control の argv と dependency closure がその header を含むことまで検査する。[test_screening_driver.py:293-329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:293)
- prepare 呼び出し、base 転送、または両者の同一性を壊すと header を解決できず、正例は緑まで到達しない。
- **real / nit** — 負例単独は供給本体を削除しても緑になるが、これは意図した counterfactual である。同じ fixture の prepare を no-op にして `preprocess-failed` を要求し、上の正例と対になっているため検査全体は恒真ではない。[test_screening_driver.py:332-349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:332)

## 恒真な検査

- **real / nit** — 新しい API signature を残して供給 branch の本体だけを削除した場合、次の新規 test は緑のままになる。

  - `test_screening_condition_gate_fails_without_prepared_base_side_effect` — 失敗側の counterfactual。[test_screening_driver.py:332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:332)
  - `test_screening_condition_gate_without_manifest_preserves_unsupplied_path` — manifest `None` の非発火契約。[test_screening_driver.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:352)
  - `test_screening_condition_gate_no_requests_does_not_prepare_with_manifest` — request 空の早期 return 契約。[test_screening_driver.py:389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:389)

- これらは供給の存在証明ではなく非発火境界または負例である。供給本体の削除は、prepare exact 回数、load-bearing 正例、stock 入れ子、canonical root 一致、prepare 例外境界の各 test が検出する。[test_screening_driver.py:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:227) [test_screening_driver.py:410](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:410) [test_screening_driver.py:1016](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_screening_driver.py:1016)

## 例外境界と資源

- **refuted / nit** — 通常の例外経路で一時 base が残る経路は見つからない。TemporaryDirectory は prepare より前に `ExitStack` へ登録され、prepare、capture、supply、meaning、admission、return のいずれでも stack を抜ける際に削除される。[screening_driver.py:187-240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:187)
- prepare の configure/build timeout と失敗は `MasstreeFetchContentError` へ変換されるため、同じ stack 巻き戻しを通る。[buildcache.py:2068-2079](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/buildcache.py:2068)
- stock 経路では checkout が外側、一時 base が内側であり、成功・例外の双方で base cleanup が stock checkout 終了より先になる。[screening_driver.py:258-264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:258)
- prepare は `evaluate_candidate` の candidate-abort `try` より前にあるため、失敗や timeout は偽の関門赤や WAL abort にならず評価全体へ伝播する。[screening_driver.py:588-596](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:588)

## 親の診断の検証

- **real / must-fix** — 親の診断を支持する。`effectuation-ignored/CMakeLists.txt` は現在 `FETCHCONTENT_BASE_DIR` を一度も参照しない。[CMakeLists.txt:1-7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/fixtures/condition_meaning_gate/effectuation-ignored/CMakeLists.txt:1)
- screening test は同変数を `-D` で渡すため、CMake の未使用 CLI 変数警告が stderr に出る。関門は成功 rc でも stderr があれば `configure-failed` とする。[condition_meaning_gate.py:1574-1582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/condition_meaning_gate.py:1574) この failure は supply red record へ変換される。[condition_meaning_gate.py:2548-2565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/condition_meaning_gate.py:2548)
- D1666 の先行 fixture は同じ理由への対処として既に無害な参照を持つ。[supplied/CMakeLists.txt:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/fixtures/condition_meaning_gate/supplied/CMakeLists.txt:3)
- must-fix は、親提案どおり `effectuation-ignored/CMakeLists.txt` の `project(...)` 後へ次の 1 行を追加することである。既存 test の期待値変更は不要。

  ```cmake
  set(_condition_gate_fetchcontent_base "${FETCHCONTENT_BASE_DIR}")
  ```

- 他の 2 consumer は configure args を渡さない。直接 gate test は空 args で capture し、backoff helper も既定が `configure_args=()` である。[test_condition_meaning_gate.py:600-605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/tests/test_condition_meaning_gate.py:600) [backoff_sweep.py:90-108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/backoff_sweep.py:90) したがって追加行は空の通常変数を設定するだけで、両 test の compile definitions、target、判定結果を変えない。

## 裁定の遵守

- **refuted / nit** — 裁定 0 違反はない。docstring は受理集合不変とは書かず、未供給だけで停止していた呼び出しが変更していない judgment へ進むと記述する。[screening_driver.py:175-181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:175) 実装報告も「制御された受理集合の拡張」と明記する。[s5-author.md:56-63](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-screening-gate/artifacts/dev-wave-t2228-screening-gate/s5-author.md:56)
- **refuted / nit** — 裁定 1 違反はない。manifest は現行 call graph 上の route proxy であり、供給権限ではないと明記されている。[screening_driver.py:177-179](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:177)
- **refuted / nit** — 裁定 5 違反はない。caller 数などは「静的列挙」に置かれ、20 秒を本 wave の実測とは記録していない。[s5-author.md:100-109](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-screening-gate/artifacts/dev-wave-t2228-screening-gate/s5-author.md:100)
- **refuted / nit** — 裁定 7 違反はない。`site=None` は関門ごとの `current_site()` 再観測と表現され、「driver 段と同じ解決」とは書かれていない。[screening_driver.py:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-gate/orchestrator/campaign/screening_driver.py:181)
- production 差分は `screening_driver.py` の 3 関数に閉じ、`backoff_repro`、`s1_direct_comparison`、pin、freeze へ拡張していない。[s5-author.md:102-109](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-screening-gate/artifacts/dev-wave-t2228-screening-gate/s5-author.md:102)

## 総括

- **real / must-fix** — must-fix は `effectuation-ignored/CMakeLists.txt` の無害な 1 行追加だけである。これにより現在の `configure-failed` を除き、既存の `preprocess-bytes-identical` 拒否まで到達させる。
- **refuted / nit** — 関門の判定式弱化、skip 相当の偽緑、load-bearing 正例の無効化、例外時の通常資源漏れ、裁定表現違反は見つからなかった。
- このレビューではテストを実行していない。親の実測は現時点で **1 failed, 48 passed** であり、修正後の緑はまだ確認されていない。[s6-parent-measurement.md:6-18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-screening-gate/s6-parent-measurement.md:6)