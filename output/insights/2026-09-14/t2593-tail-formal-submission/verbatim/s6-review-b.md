## 1. 正規化で末尾の改行が消え、別の探索 campaign を渡せる

- **所見:** `realpath` の出力を `$(...)` で受けるため、解決先の名前が改行で終わると、その改行を除いた別ディレクトリへ参照が変わる。
- **根拠（読解、未実測）:** `tools/pegasus/submit_b10_backoff_grid.sh:74` の検査後、`:80` の command substitution が末尾改行をすべて除去し、`:81` は変質後の文字列を検査する。`:123` と job 側 `tools/pegasus/b10_backoff_grid.sh:249` も変質後の参照を検査する。テスト `orchestrator/tests/test_b10_backoff_grid_submit.py:201` は名前の途中に改行を置くため、この経路を覆わない。
- **成果物への影響:** 指定した探索 campaign と異なる campaign から correctness mode を取得し、同じ mode なら参照の取り違えが検出されず進む。
- **再現条件:** repo 外に `/outside/explore` と、名前が改行で終わる `/outside/explore<LF>` を用意し、`/outside/alias` を後者への symlink とする。新系列に `--explore-campaign /outside/alias/.` と他の妥当な引数を渡す。末尾の `/.` により leaf の `! -L` を通過し、転送値は `/outside/explore` になる。**競合は不要。**
- **深刻度:** **must-fix**。正規化結果の末尾改行を保存した状態で文字集合を検査する必要がある。

## 2. 集団 report の既存ディレクトリに関する説明が実装より厳しい

- **所見:** 文書の「既存の出力先へは再実行できない」は、driver が拒否する対象を正確に表していない。
- **根拠（読解、未実測）:** `docs/b10-backoff-static-tail-submission.md:72` に対し、`orchestrator/campaign/b10_backoff_static_tail_formal.py:648` は `exist_ok=True` でディレクトリを作り、`:650`–`:651` は所定の成果物 3 パスの存在だけを拒否する。
- **成果物への影響:** 実装では受理される出力先を、操作手順が使用不可と案内する。
- **再現条件:** 既存の空ディレクトリ、または対象 stem の 3 成果物がない既存ディレクトリを、§4 の `--output-root` に指定する。
- **深刻度:** **nit**。文書を「対象の成果物が既に存在する場合は拒否」に合わせる。

## 3. 投入成功と出力 root の作成時点が文書で混同されている

- **所見:** qsub の投入成功時点では、文書が説明する workload ごとの出力 root はまだ存在しない場合がある。
- **根拠（読解、未実測）:** `docs/b10-backoff-static-tail-submission.md:42`–`:43` は投入成功で出力 root 等が作られると説明するが、submit の `tools/pegasus/submit_b10_backoff_grid.sh:255`–`:269` は qsub と receipt 記録までであり、root の作成は job 側 `tools/pegasus/b10_backoff_grid.sh:283` にある。
- **成果物への影響:** 台帳が参照する出力 root の不在を、待機中ではなく投入失敗と誤認しうる。
- **再現条件:** 3 本とも qsub が成功し、job がキュー待機中、または root 作成前の入力検査で停止する。
- **深刻度:** **nit**。投入 receipt と job 開始後の出力作成を区別して記述する。

## 総括

重い順に、①末尾改行による探索 campaign の参照変更（must-fix）、②report 出力先の受理条件の文書誤り、③出力 root 作成時点の文書誤り。編集・テスト・投入は実施していない。

読解では、`PY` は job の `:211` で設定・`:215` で確認済み、`REPO_ROOT` は `:239` で設定済み。新 heredoc の衝突、`SystemExit(2)` や sweep 非ゼロの握り潰し、argv の parser 不一致、転送変数名の不一致は見つからなかった。正規化後の文字列検査があるため、競合で解決先が変わっても新 2 値からコンマを直接注入する経路は見つからない。

旧系列にも追加の条件評価は入るが、新しい外部 command は実行されない。事前 help loop 撤去後も `--run-kind extended --explore-campaign /x -h` は旧 rc=2 から rc=0 になる。ただしこれは親裁定 §2(h) の help 順序の許容と同型であり、独立した must-fix には数えなかった。

親の実測では、①末尾改行の例で **qsub に渡る参照先そのもの**、②既存の空 report directory の受理、③qsub 成功・job 未開始時の receipt と root の存在を確認してほしい。