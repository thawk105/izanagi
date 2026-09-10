# [T-2406] 段 6 レビュー所見の裁定 (review A = 受理集合、review B = 実効性・docs)

統合 commit `96b8d0c2f` に対するレビュー。job body の実行経路には両レビューとも機能欠陥を認めず (A: 「A4 は閉じている」、B: 「許可された移植差以外の機能欠陥を認めない」)。所見は契約テストの受理集合と docs に集中した。

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A-1a | コメント行中の偽 heredoc opener (`# <<true`) が以後の行を検査面から消す | real、ただし `_shell_body_without_heredocs` の**既存挙動** (本 wave 以前から全検査に共通) | **採用 (安価)**: コメント専用行 (`^\s*#`) では opener を探さない |
| A-1b | 行末コメントで marker 文字列を満たしつつ実行を消せる (`true # timeout 60 ...`) | real、既存 marker 全部に共通の型。同一主体が gate と検査を変えられる限り完全防壁ではない (D387) | 不採用 (scope 外の tokenizer 新設)。裁定パッケージ候補に記録 |
| A-2 | `export -n` / `env -u` / 綴り難読化で (d) の保持を破れる | real、本 wave が新設した保持契約の穴 | **採用**: 実行面で `CMAKE_PREFIX_PATH` を含む行は exact 3 行 (sanitize の unset、glog configure の `-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR` 行、exact export) だけを受理し、他は全て拒否。難読化綴り (`PAT\H`) は A1 と同型で対象外と明記 |
| A-3 | driver 2 分岐が prebuild より後という位置関係が未検査 | real | **採用**: prebuild 呼出し位置 < driver 2 出現の両方 |
| A-should | `dependency-policy-path` / `glog-install-timeout` を parametrize に登録 | refuted: 段 4 の「登録外」は**変異 matrix** についてであり、parametrize の「最初に欠ける label は 1 つ」は成立 | 不採用 (記録) |
| A-nit | 文字列中の `CMAKE_PREFIX_PATH` を偽拒否 | 受容 (job body は自前) | 不採用 |
| B-1 | heredoc 内の required fragment はコメントアウトしても raw source に残る | real | **採用**: `job-body-comment` 以外の required fragment はコメント専用行を除いた raw source で照合 |
| B-should-1 | README §7 末尾の F660 文が stale | real | **採用済み (親 docs)** |
| B-should-2 | `driver_rc` が job body 全体の rc であることの説明が無い | real | **採用済み (親 docs)** |
| B-nit | 出典コメントの行番号差 | 意図どおり | 不採用 |

## fix 単位 (1 本、Codex fix 子、編集対象 = 契約テストのみ)

job body は変えない。契約テストへ次を入れる。
1. `_shell_body_without_heredocs`: `^\s*#` の行では opener を探さない (heredoc 内部の判定は従来どおり)。
2. `_assert_static_job_contract`: `job-body-comment` 以外の required fragment は、コメント専用行を除いた raw source (heredoc は残す) にも存在することを要求 (欠けたら同じ `job contract missing: <label>` 署名)。
3. `_assert_forbidden_job_constructs`: 実行面で `CMAKE_PREFIX_PATH` を含む行 (strip 後) の多重集合が exact 3 行 {`unset CMAKE_PREFIX_PATH CMAKE_TOOLCHAIN_FILE`, `-DWITH_UNWIND=OFF "-DCMAKE_PREFIX_PATH=$GFLAGS_INSTALL_DIR"`, `export CMAKE_PREFIX_PATH="$GFLAGS_INSTALL_DIR:$GLOG_INSTALL_DIR"`} と一致しなければ `forbidden-cmake-environment-injection`。既存の unset / export の位置・回数検査は残す。
4. 同 helper: `"$PY" - "$prebuild_receipt"` の位置が driver 2 出現の両方より前。
5. 負例テスト: `export -n CMAKE_PREFIX_PATH` を export 直後に挿入 / driver 行を `env -u CMAKE_PREFIX_PATH "$PY" ...` に置換 / `# <<true` + `unset CMAKE_PREFIX_PATH` + `true` を export 直後に挿入 / driver 分岐を prebuild 呼出しの前へ移動 / `    "gflags_source_path",` と `    dependency_prefix=...` をコメントアウト。正例: 現行 job body が全 helper を通る。

## 変異事前登録の追加 (DW-M01、fix 前に登録)

| id | 置換 | 期待 |
|---|---|---|
| m14-export-n | export 行の直後に `export -n CMAKE_PREFIX_PATH` | KILLED |
| m15-comment-out-prefix | `    dependency_prefix=";".join(...)` → `    # dependency_prefix=";".join(...)` | KILLED |
| m16-fake-heredoc-unset | export 行の直後に `# <<true` / `unset CMAKE_PREFIX_PATH` / `true` | KILLED |
