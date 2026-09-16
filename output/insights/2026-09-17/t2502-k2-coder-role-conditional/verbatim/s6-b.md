## 登録面と受入全走の赤候補

**1. 新規3 test による台帳・固定集合の不一致**

- **所見:** N・P・F は所要時間台帳に未登録だが、それだけでは受入全走は赤にならない。台帳は23,145 entriesで内部件数と一致する。未知 node は既定コストで並べ替えられ、収集集合から除外されない。台帳の固定集合検査が対象とする8 suite に `test_p3_s4_loop.py` は含まれない。
- **仮判定:** refuted。
- **根拠 file:line:** `orchestrator/tests/conftest.py:1675`、`:1735`、`:1753`、`orchestrator/tests/test_update_acceptance_duration_ledger.py:306`、`:364`。
- **推奨:** 本変更に必須の台帳更新はない。実測値を登録する場合は親が実測 JUnit を使い、`python3 tools/update_acceptance_duration_ledger.py <JUnit...> --add-only` を実行する。`--coverage-against` は網羅率の表示であり、未登録 node 自体を拒否する gate ではない（同 tool `:494`、`:535`）。未実測値の合成や台帳全体の再生成は不要。

**2. real-repo 登録・xdist group・checkpoint 列挙への追加漏れ**

- **所見:** 新規3本は tmp repo を使用し、共有 submodule の検査を代役に置き換える。既存 checkpoint node の登録対象とは異なる。conftest は登録済み node にだけ access vector と group を付け、serialization test も登録外 node の存在を許している。collection config に今回の3本を含む全関数集合・総件数の固定は確認できない。
- **仮判定:** refuted。
- **根拠 file:line:** `orchestrator/tests/conftest.py:329`、`:492`、`:2145`、`orchestrator/tests/test_real_repo_serialization.py:1711`、`:1720`、`orchestrator/tests/test_pytest_collection_config.py:173`、`orchestrator/tests/test_p3_s4_loop.py:7173`、`:7223`、`:7281`。
- **推奨:** 登録表・checkpoint 列挙の変更は不要。列挙された機構について、新規3本の追加だけで赤になる候補は見つからなかった。受入全走の成功を静的確認からは主張しない。

## 所見

**3. fixture 名・tmp path・計算ノード環境の衝突**

- **所見:** `_resolved_knowledge_fixture` は渡された `tmp_path` 内だけに repo と manifest を作る。N・P・F は別 test の `tmp_path` を受け取り、名前もそれぞれ異なる。P の共通 helper の `main-loader-campaign` も test ごとの tmp 配下である。通常の pytest/xdist 実行でこれらが共有 path に衝突する構造はない。site は既存 autouse fixture が正規化する。
- **仮判定:** refuted。
- **根拠 file:line:** `orchestrator/tests/test_p3_s4_loop.py:1014`、`:1024`、`:1043`、`:7169`、`:7211`、`:7249`、`:7274`、`orchestrator/tests/conftest.py:239`。
- **推奨:** 修正不要。Git executable と commit 可能な環境への依存は既存 helper の条件として残るが、今回追加された並列衝突ではない。

**4. F の簡略な戻り値で後続処理が失敗する懸念**

- **所見:** `--run-iteration` が無いため、`:2807` の run 専用表示・checkpoint 判定には入らない。fixture 分岐は新規 state の iteration を1とし、代役の `dry-pass` により digest生成・admission・whiteboard検査をスキップする。prepare が作るのは receipt であり WAL レコードではない。存在しない WAL は空リストとなるため、`1 != 0`、停止理由の検査、digest 不在の検査が成立し、`return 0` に到達する。
- **仮判定:** refuted。
- **根拠 file:line:** `orchestrator/campaign/p3_s4_loop.py:1554`、`:2818`、`:2833`、`:2844`、`:2862`、`:2870`、`:2891`、`orchestrator/campaign/wal.py:1653`、`orchestrator/tests/test_p3_s4_loop.py:7285`。
- **推奨:** 修正不要。F は fixture 経路の受理を検査する正例であり、実 iteration の成果物生成を証明する test とは扱わない。

## 実効性の全層

**5. 起動経路によって新しい拒否が迂回される懸念**

- **所見:** 直接起動では emit の return 後、run 用 context・prepare 前に拒否する。Pegasus は manifest env が指定されれば role env も先に必須とするため、role 欠落は shell が拒否し、新しい driver guard まで到達しない。空 sources でも shell の対指定要件は変わらない。B-4 launcher の base 登録は同じ `main` を指すが、現行 `_driver_argv` は knowledge manifest 自体を渡さないため、この guard の対象にならない。
- **仮判定:** refuted。
- **根拠 file:line:** `orchestrator/campaign/p3_s4_loop.py:2713`、`:2714`、`:2725`、`:2739`、`tools/pegasus/p3_s4_loop_pegasus.sh:73`、`:78`、`:581`、`orchestrator/campaign/p3_b4_launcher.py:141`、`:186`。既存 job 契約 test は `orchestrator/tests/test_p3_s4_loop_job_contract.py:1092`、`:1336`。
- **推奨:** 修正不要。job 経路の結果を driver guard の発火証拠には数えない。

**6. 親の runbook 追記案には境界の省略がある**

- **所見:** 趣旨は実装と一致するが、「`--run-iteration` 経路」は emit 併記時に実行されない。また `sources: [] / completed_empty` は同義に読めるが、parser が保証するのは空 sources ⇒ completed_empty の方向である。裁定本文はこの点を既に認識している。
- **仮判定:** real。
- **根拠 file:line:** `s4-ruling.md:60`、`orchestrator/campaign/p3_s4_loop.py:2689`、`:2713`、`orchestrator/campaign/knowledge_manifest.py:324`、`:329`、`docs/phase3-s4b-runbook.md:41`。
- **推奨:** **nit**。親の段7追記を次のように限定する。

  > driver で `--emit-planner-context` を指定せず `--run-iteration` を実行する場合、manifest の `sources` が非空なら `--coder-role coder-v4-autonomous-k2` が必須。妥当な空取得 manifest（`sources: []`）では従来どおり role 省略を許す（D1878）。

**7. B-4 closure hash の変更と既存 pin**

- **所見:** 生 bytes を含むため、closure hash は **base・sort・trigger の全3種で変わる**。旧 closure を宣言した admission は live 照合で拒否される。一方、確認した test golden は現行 file bytes から hash を計算し、旧値を固定していない。事前登録文書も3種の値を未登録と明記している。
- **仮判定:** real（hash 変更）、refuted（確認範囲で既存固定値により test が赤になる懸念）。
- **根拠 file:line:** `orchestrator/campaign/p3_b4_closed_critic.py:635`、`:658`、`:668`、`:687`、`orchestrator/tests/test_p3_b4_closed_critic.py:604`、`:2025`、`docs/phase3-b4-reflux-ablation-preregistration.md:1002`。
- **推奨:** 裁定どおり互換性の限定を記録し、gate は緩めない。`git grep` では旧 production 単体 SHA-256 の一致は0件だったが、これは**単体 SHA の pin 検索結果に限定**する。path 検索には registry や過去の記録が実際にあり、「path 検索0件」「凍結成果物が全て無関係」とは主張しない。確認した registry の参照は path・parser 登録である（`orchestrator/codex_roles/manifest.json:964`）。

## 報告の検算

**8. author 報告の件数・行番号・変更範囲・anchor**

- **所見:** 指摘対象の数値に誤りは見つからなかった。
  - `L.main(` は **16箇所**。行番号は報告表と全て一致する。
  - `--knowledge-manifest` は **5箇所**。6541、6640、7198、7238、7292。
  - 変更対象外 consumer 候補は **30 file**で、同じ文字列検索結果と一致する。
  - 変更前との AST 比較では、新設は N・P・F、既存関数の変更は I のみ。
  - M1〜M5 の提示した逐語 anchor は、実 production 内でそれぞれ **1箇所**。提示された行番号とも一致する。
- **仮判定:** refuted。
- **根拠 file:line:** `s5-author-out.md:54`、`:72`、`:76`、`:124`、`:164`、`orchestrator/tests/test_p3_s4_loop.py:6585`、`:7206`、`:7246`、`:7269`、`orchestrator/campaign/p3_s4_loop.py:2713`。
- **推奨:** 報告の訂正は不要。ただし30候補から collection 関連2 file を除くと28 fileになる。「consumer 焦点走29 file」は別の選定集合なので、親は実際の runner argv と対応づけて記録する。件数差だけから漏れとは判定しない。

## 総括

**GO — 静的レビュー上の must-fix は0件、nit は1件。**

登録面・fixture 後続処理・起動経路に実装を阻害する問題は見つからなかった。親による6 node の成功は提示済み事実として扱い、本レビューでは再実走していない。変異 matrix・consumer 焦点走・受入全走の合格は、この GO には含めない。