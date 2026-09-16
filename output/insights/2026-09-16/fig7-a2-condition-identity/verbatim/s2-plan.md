## 総括

**legacy caption の一律変更では旧 fig5 の検証を緑に保てないが、訂正を新 prefix に限定する実装なら、旧 3 file の bytes 保持と両立できる。**
現行コードには訂正版の分岐がなく、追加実装が必要である。
新図は既存の legacy 入力と pin を使って生成でき、`CANONICAL_SHA256` の追加は不要。
(P3) の改訂稿を `tracked_inputs` に追加する案は、現行 schema `v1` と closure 検証の下で成立する。
推奨は fig7 専用の caption 訂正と出所記録に限定し、旧 fig5・fig6、数値、cell identity を保持する案である。
以下の行番号は対象 worktree の現行ファイルを指す。確認は静的読解のみで、編集・生成・pytest 実走はしていない。

## 実装プラン

**作業単位 A — Codex author：新図だけに訂正 caption を適用する。**

対象は [tools/plotting/plot_a2_certification.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig5-a2-identity-reissue/tools/plotting/plot_a2_certification.py:618)。

- `:618` の `_caption` で、既存 current-full 分岐 `:622` と legacy 本文 `:653` を保持する。
- legacy 本文を局所変数へ組み立て、`prefix.name == "fig7_a2_builtin_backoff_onoff_reject"` かつ `measurement_conditions["attempt"] == "t2022-20260828c"` の場合だけ、後述の条件記述を訂正して返す。current-full は既存の先行 return のままとする。
- 訂正文は生成器内の固定文言にする。caption 引数、caption file 引数、図番号引数は追加しない。図番号は引き続き `:603` の `_figure_number` から得る。
- 対象はこの一枚だけとし、prefix 登録表や caption 版管理の一般機構は作らない。

旧 fig5 が通る経路は次のとおり。

1. `orchestrator/tests/test_plot_a2_certification.py:1511` が旧 provenance を読み、`:1521` で `validate_repo_closure` を呼ぶ。
2. 生成器 `:859` が `outputs[0]` を `:609` の `_caption_prefix` に渡す。結果は旧 `fig5_a2_certification_reject`。
3. `_caption` の新図専用条件は偽になり、従来の legacy caption を同じ文字列で返す。
4. 生成器の source 変更だけでは旧 provenance は失格にならない。`:839` が明記するとおり、`generator.sha256` は生成時の記録であり、現行 source との一致は要求されない。
5. README の旧 caption を保持すれば、テスト `:1522` の逐語収録条件も維持できる。

したがって、**旧 fig5 に適用される caption 自体を変える場合は両立不能**である。新図だけを訂正する上記案では、その変更を旧 fig5 に適用しないことで両立する。検証を迂回・緩和する変更は不要。

**作業単位 B — Codex author：caption の最小訂正。**

生成器 `:660`–`:661` の条件を述べる部分だけを、新図について次のように変える。以下は現行 provenance の数値を含む完成文字列の変更前後であり、実装では既存の `effects` と `.4f` の式をそのまま使う。

変更前：

```text
Median effects copied from certification are rr5 fixed 10 us -46.3902% and rr50 fixed 5 us -65.9080%.
```

変更後：

```text
Median effects copied from certification are rr5 built-in adaptive backoff enabled (BACK_OFF=1) versus disabled (BACK_OFF=0) -46.3902% and rr50 built-in adaptive backoff enabled (BACK_OFF=1) versus disabled (BACK_OFF=0) -65.9080%. The labels fixed 10 us / fixed 5 us and cell IDs rr5-fixed10 / rr50-fixed5 identify requested genomes, not effective fixed-backoff conditions; BACKOFF_FIXED did not affect the build.
```

これは改訂稿 `docs/paper-story/results/2026-09-07-a2-certification-reject.md:63`、`:81`、`:94` が述べる、要求量・実効条件・適応機構の区別に対応する。図番号以外の残りの caption、限定、abort 率の説明、protocol status は保持する。

label は次を区別する必要がある。

- **cell identity と artist label**：生成器 `:476`、`:681`–`:686` が権威由来の `cell_id` を引き継ぐ。ここは変更しない。`cells`、`genome`、`_artist_series` はそのまま。
- **目盛に表示する文言**：実際の x 軸は `:726` の `"no backoff"` と `f"fixed {adopted['genome']['BACKOFF_FIXED']} us"` であり、`cell_id` そのものではない。これを変えるだけで `_artist_series` の一致が自動的に壊れるわけではない。

今回の最小案では目盛も保持し、上記 caption で要求 genome のラベルだと明示する。これは「label は残して caption の条件記述だけ訂正する」範囲に収まる。

**作業単位 C — Codex author：改訂稿を新図の `tracked_inputs` に記録する。**

対象は生成器 `:775` の `build_provenance`、特に `:787`。

- `data["tracked_inputs"]` のコピーを作り、作業単位 A と同じ新図・attempt の条件に限り、改訂稿の一行を追加する。
- パスは repo 所有の固定値 `docs/paper-story/results/2026-09-07-a2-certification-reject.md`。caller から受け取らない。
- 行は `kind: "caption_source"`、固定相対 `path`、現物の `sha256`、`authority_scope: "condition description only; not measurement values or protocol status"` とする。
- hash は既存 `:84` の `_sha256` で生成時に取得する。certification / raw manifest の二行は保持する。
- `load_measurements:592` の入力二行は変えず、図を特定できる `build_provenance` で付加する。

(P3) が成立する理由：

- schema 名は `:30` の `v1`。`validate_repo_closure:837` はその一致を要求する。
- `:840` は全 tracked input の現物と hash を検証するが、kind を二種類に制限していない。
- `:845`–`:847` の件数制約は **`raw_manifest` が一行**であることだけ。
- `_load_tracked_authority:141` の二種類制約は、権威 JSON を読む関数の契約である。改訂稿をこの関数へ渡してはいけない。
- 既存テスト `orchestrator/tests/test_plot_a2_certification.py:1457` の二行 assertion は `fig5_fixture` の生成結果を検査する。新図だけに追加すれば維持できる。

したがって別の top-level field を発明する必要はない。測定値の権威を改訂稿へ置換せず、**条件説明の出所として追加する**。

**作業単位 D — 親：既存 legacy 権威から新図を生成する。**

pin 追加なしで通る経路は次のとおり。

| 箇所 | 動作 |
|---|---|
| 生成器 `:63`–`:66` | `DEFAULT_ROOT`、`DEFAULT_CERT`、`DEFAULT_MANIFEST` は旧 attempt 用 |
| `:47`–`:50` | legacy certification path と二つの SHA-256 が既に登録済み |
| `:117`–`:128` | certification の repo 相対 path から pin を引く。出力 prefix は key に使わない |
| `:507`–`:510` | 二つの入力 bytes を検証し、`_profile` を決定 |
| `:154`–`:161` | legacy schema の組から `"legacy"` を選ぶ |
| `:603` | `fig7_` から図番号 `"7"` を得る |
| `:862`–`:880` | CLI 入力を解決し、既存 loader、作図、publish に渡す |
| `:874`–`:876`、`:798` | 展開した再現 argv を provenance に記録する |

親は対象 worktree の repo root、計測機外の login node で以下を実行する。

```bash
python3 tools/plotting/plot_a2_certification.py \
  --measurement-root /work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2022-20260828c \
  --certification output/insights/2026-08-24_paper-story-a2-certification/certification.json \
  --raw-manifest output/insights/2026-08-24_paper-story-a2-certification/raw-manifest.json \
  docs/paper-story/figures/fig7_a2_builtin_backoff_onoff_reject
```

現行コードでもこの新 prefix の選択自体は可能だが、caption は未訂正のままになる。作業単位 A・C の後に実行する。既存の統計照合処理・値の算出方法・判定式には変更を加えない。

**作業単位 E — 親：README、生成物、記録、commit。**

対象は [docs/paper-story/figures/README.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fig5-a2-identity-reissue/docs/paper-story/figures/README.md:534)。

- 一覧 `:21` の fig6 行の後へ fig7 の行を追加する。
- fig6 節の末尾 `:611` の後へ新図の独立節を追加する。既存の図別構造に合わせ、README 内では **H1 の図名、H2 の小節**とする。fig6 の H2 小節として入れない。
- 新節に、旧 attempt の条件記述訂正版であること、旧判定の歴史説明であること、採用静的 backoff の結果ではないこと、再現コマンド、入力の役割、生成された caption の逐語を収録する。
- fig5 の追補 `:434`–`:444` を書き換える必要はない。旧 bytes と旧 caption を保持する案なので、その記述と矛盾しない。旧 caption 正文 `:516` 以下も保持する。
- 新図の caption は生成 JSON からそのまま転記し、途中で改行を挿入して文字列を分断しない。
- 親が新三成果物、docs、worklog / insights fragment を扱い、受入後に commit する。Codex author の担当は生成器と必要な既存テストファイルの変更まで。

## 親の brief への不同意

**(P1)〜(P4) の採用方針には不同意なし。ただし二点、根拠の限定・訂正が必要。**

- brief「新事実4」の「caption 訂正と凍結 bytes 保持は両立しない」は、**既存 legacy caption の一律変更**には正しい。新 prefix にだけ固定訂正文を適用する分岐まで不可能とはいえない。根拠は生成器 `:609`、`:618`、`:859`。
- (P4) の label 保持は採るが、「図中 label はすべて cell_id なので変更すると artist 整合が崩れる」という説明は現物と異なる。x 軸文言は `:726` で別に設定されている。今回は scope と最小差分を理由に保持する。

(P3) は成立する。ただし追加行を `_load_tracked_authority` に通す解釈は採らない。

## 受入で走るテスト

production file の参照を検索すると、Python の直接 consumer は `orchestrator/tests/test_plot_a2_certification.py`。`:55`–`:61` の `_plot()` が対象生成器をロードし、`:1393`–`:1397` の `_run_script()` が同ファイルを subprocess で呼ぶ。**受入対象はこのテストファイル全体**とする。

変更箇所に直接関わる既存テストは以下。

| テスト名（同ファイル内） | 行 | 参照関係・確認対象 |
|---|---:|---|
| `test_landed_fig5_repo_closure_and_caption_when_present` | 1511 | `validate_repo_closure` と README の逐語一致 |
| `test_m9_caption_distinguishes_correctness_from_performance` | 1359 | `_caption` の限定文 |
| `test_current_gate_copy_is_receipt_observation_not_legacy_fixed_copy` | 1168 | current-full の `_caption` |
| `test_caption_uses_figure_number_from_output_prefix` | 1400 | `main` → publish → caption |
| `test_output_prefix_without_figure_number_is_rejected` | 1410 | `main` → `_figure_number` |
| `test_cli_writes_complete_provenance_with_repo_relative_argv` | 1445 | `main` → `build_provenance`、schema・入力件数・argv |
| `test_m7_outer_status_is_copied_into_provenance` | 1341 | `build_provenance` の status 転記 |
| `test_m8_artist_baseline_is_stock_median_with_stock_genome` | 1351 | `_artist_series` の identity と基準値 |
| `test_real_size_figure_passes_layout_and_artist_contract` | 1366 | `make_figure`、実寸 layout、artist |
| `test_m10_layout_failure_publishes_no_outputs` | 1377 | `_publish_outputs` の保存前検査 |
| `test_cli_has_no_caller_selected_hash_options` | 1182 | CLI の pin 所有境界 |
| `test_cli_rejects_exact_bytes_at_certification_path_missing_from_pin_table` | 1189 | 未登録 path の拒否 |
| `test_current_cli_reads_repository_owned_pin_table` | 1200 | `main` → repo pin |
| `test_tracked_authority_literals_and_run_readme_record_agree` | 1470 | pin 二件と権威 bytes |
| `test_real_external_inputs_when_available` | 1502 | legacy 外部入力の読込み |

author は同じテストファイル内で、次の受入対象を既存の枠に追加する。

- fig7 caption の訂正、旧 fig5 caption の保持、数値・限定文の保持。
- fig7 の `tracked_inputs` が権威二行＋改訂稿一行となり、既存 `validate_repo_closure` を通ること。
- `:1238` の既存 `_assert_named_landed_bundle` を使う fig7 着地テスト。これは helper であり、それ単独では pytest に収集されないため、呼ぶテストが必要。

新たな production 検査層は追加しない。親が既存の受入経路で実走し、外部入力不足による skip を実測成功として数えない。

## 未解決・裁定が要る点

- `fig7_a2_builtin_backoff_onoff_reject` は引き続き親の暫定名。採用する場合、新図専用分岐・出力名・README・着地テストを同じ名前に揃える。
- 本案は目盛の `fixed 10 us / fixed 5 us` を残し、caption で要求条件だと明示する。画像単体でも有効／無効を読めることまで要求するなら、`:726` の表示文言訂正を範囲に含めるかが残る。その場合も cell identity の変更は不要。
- 外部 root の完全性、新出力名の衝突、実データ生成と受入結果は未確認。実走は親の担当であり、このプランをもって緑とは報告しない。