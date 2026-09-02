## 所見

- **重大: `analysis_commit` の除去は、単なる HEAD-only 拒否の撤去を超え、解析・検証コードの実効的な閉包束縛を失わせる。**
  - **主張:** `analysis_commit` 自体は事前登録時に固定された値ではないが、現行実装では分割実行間の repo 全体の commit 束縛として働いている。`analysis_code_sha256` が覆うのは `ANALYSIS_REL` の 1 ファイルだけであり、その外側に結果値と verifier 受理集合を変える実依存がある。
  - **根拠:** 事前登録文書は解析コード SHA を lock、`BUILD_START`、block record に束縛すると定める (`docs/b10-backoff-shape-preregistration.md:60-65`)。しかし `ANALYSIS_REL` は 1 ファイルだけで (`orchestrator/campaign/b10_backoff_shape_sweep.py:90`)、SHA の計算範囲もその bytes のみである (`orchestrator/campaign/b10_backoff_shape_sweep.py:1378-1386`)。一方、throughput 解釈と安定性判定は外部の `benchparse` と `noise_floor` を実行する (`orchestrator/campaign/b10_backoff_shape_sweep.py:37-43`, `orchestrator/campaign/b10_backoff_shape_sweep.py:2250-2259`, `orchestrator/calibrator/benchparse.py:53-63`, `orchestrator/calibrator/analyze.py:208-232`)。correctness gate も外部 verifier を呼ぶ (`orchestrator/campaign/pipeline.py:33-39`, `orchestrator/campaign/pipeline.py:1471-1515`)。build-admission policy の identity は pin と registry だけで、これらのコード SHA を含まない (`orchestrator/campaign/build_admission.py:458-466`)。
  - **成果物影響:** 変更後は B-10 本体が同じまま `benchparse.py`、`analyze.py`、`pipeline.py`、verifier を変更した commit でも binding と campaign ID が同じになる。既存 WAL の terminal variant は current verifier を通らず skip される (`orchestrator/campaign/loop.py:426-452`, `orchestrator/campaign/loop.py:522-527`)。過去 block row も proposed comparison removal 後は同じ束縛として受理され、別 workload の row と集約される (`orchestrator/campaign/b10_backoff_shape_sweep.py:2381-2401`, `orchestrator/campaign/b10_backoff_shape_sweep.py:3047-3063`)。その結果、異なる parser、安定性判定、verifier 受理集合で作られた `median_tps`、`unstable`、`correctness_certified` が同じ judgement に入り (`orchestrator/campaign/b10_backoff_shape_sweep.py:1655-1668`, `orchestrator/campaign/b10_backoff_shape_sweep.py:1734-1789`)、報告値や `different`、`not-detected`、`indeterminate` が変わりうる。JSON records には各 commit が残るが、Markdown 表は行ごとの commit を示さず、上部には再開時の解析 commit だけを表示する (`orchestrator/campaign/b10_backoff_shape_sweep.py:2641`, `orchestrator/campaign/b10_backoff_shape_sweep.py:2653-2661`)。これは絶対規律 2 の即時 reject を直接削除しない一方、同一 campaign 内で旧 verifier の受理結果と current verifier の結果を混在可能にする。
  - **確度:** 高。

- **重大: テスト計画は 3 個の比較除去を検出できるが、上記の正しさ境界を検査しない。**
  - **主張:** planned tests は `analysis_commit` だけ違う synthetic binding と、`analysis_code_sha256` だけ違う binding を使うため、局所的な intended predicate は検査できる。しかし「B-10 本体 SHA は同じで、外部の判断コードだけが変わった」組み合わせを作らず、campaign identity、terminal WAL skip、report 集約まで通さない。このため閉包束縛喪失があっても予定テストは通る。
  - **根拠:** WAL テスト計画は直接構築した 2 binding と M17 同形の lock／`BUILD_START` を使う (`/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_b10-analysis-commit-unbind/context/s2-plan.md:102-109`)。その基線 M17 は lock decode と WAL read を stub し、実体として通すのは `assert_resumable_binding()` の比較部分である (`orchestrator/tests/test_b10_backoff_shape_sweep.py:805-824`)。block test も直接構築した binding と row に限定される (`/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_b10-analysis-commit-unbind/context/s2-plan.md:111-116`, `orchestrator/tests/test_b10_backoff_shape_sweep.py:341-385`)。`config_for()`、`ident.campaign_id()`、`loop` の replay skip、外部解析依存の drift はテスト計画にない。
  - **成果物影響:** テストが予定どおり成功しても、異なる解析／verifier semantics の WAL と block row が同じ campaign と report に入り、上記の受理集合と報告値の変化を検出できない。したがって予定テストの成功は「commit-only drift を許した」ことは示すが、「事前登録の解析束縛を維持した」ことは示さない。
  - **確度:** 高。

## 反証できたもの

- **除去対象が事前登録時に固定された commit ID だという疑いは反証できた。** `analysis_commit` は `load_preregistration()` が実行時の current HEAD を取得して代入する (`orchestrator/campaign/b10_backoff_shape_sweep.py:1348-1354`, `orchestrator/campaign/b10_backoff_shape_sweep.py:1387-1395`)。`source_commit` も submission receipt の値を current HEAD と照合して得る (`orchestrator/campaign/b10_backoff_shape_sweep.py:466-472`)。従って両値は事前登録 commit の一部ではない。

- **brief の二つの逐語的事実は正しい。** 事前登録文書 §1 は `analysis_commit` を列挙せず、解析コード SHA を列挙する (`docs/b10-backoff-shape-preregistration.md:60-65`)。`registration_rules` v4 の閉集合も binding field を扱わない (`orchestrator/campaign/b10_backoff_shape_sweep.py:848-878`)。ただし、これらから「1 ファイル外の解析依存も束縛済み」とは導けず、brief の結論は過剰一般化である。

- **変更前に作られた旧 schema 成果物が、変更直後の新 campaign へ自動混入する経路は確認できなかった。** 旧 binding は `analysis_commit` key を含み、新 binding は含まないため exact dict 比較で不一致になる (`orchestrator/campaign/b10_backoff_shape_sweep.py:213-229`, `orchestrator/campaign/b10_backoff_shape_sweep.py:1565-1585`)。binding を含む search config は campaign identity に入る (`orchestrator/campaign/b10_backoff_shape_sweep.py:1478`, `orchestrator/campaign/ident.py:196-235`)。build admission と cache digest にも新しい binding digest が伝播する (`orchestrator/campaign/build_admission.py:507-527`, `orchestrator/campaign/buildcache.py:2527-2574`)。問題になるのは変更後に作られる、B-10 本体は同じで外部依存だけが異なる成果物である。

- **絶対規律 2 の即時 reject 自体を直接削る変更ではない。** current verifier が実際に実行され、非 certified または anomaly を返した場合の abort は維持される (`orchestrator/campaign/pipeline.py:1484-1515`)。問題は resume skip により current verifier が実行されない既存 terminal stateとの混在である。

- **planned negative predicates は恒真ではない。** WAL 負例は `analysis_code_sha256` の差によって exact binding／commitment 比較を失敗させる。block 負例は row 内の binding を current 値にそろえた上で、独立した明示的 `analysis_code_sha256` 比較だけを失敗させる計画である (`/work/1/SFC/tanab/dev-wave-jobs/2026-09-02_b10-analysis-commit-unbind/context/s2-plan.md:104-116`)。局所機構の検査としては有効である。

## 総括

最も重い所見は、`analysis_commit` が担っていた repo-wide の分割実行束縛を、1 ファイルだけの SHA で代替できていない点である。  
値は事前登録時に固定された commit ではないが、実効上は解析・verifier semantics の混在を防いでいた。  
このままでは同じ campaign、WAL、report に異なる parser、安定性判定、verifier 受理集合の結果が入りうる。  
brief の逐語的前提は正しいが、「ゆえに事前登録に反しない」という結論は成立しない。  
静的検査のみであり、pytest は実走していない。