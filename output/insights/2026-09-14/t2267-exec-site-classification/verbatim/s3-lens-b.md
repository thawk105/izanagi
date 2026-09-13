## 総括

最大の問題は、条件の異なる pytest scope の観測を「T-2267 の §7.0 分類実測」と集約できてしまう記録設計です。
must-fix は **3 件**：正式測定との区別、cap 別の反復管理、`base` の取得元。
静的検査と入力 SHA-256 の再照合のみ実施し、pytest・受入検査の緑は主張しません。

## 所見

以下、`plan` は指定 `stage2-plan.md`、`brief` は指定親 brief、`逐語` は指定 `verbatim/` 配下を指します。repo 相対パスは指定 worktree 基準です。

1. **主張：今回の値を「§7.0 手順で実測した」と書けない。記録の見出し・表にも適用することが must-fix。**

   **根拠：** `tools/run_tests.py:152`、`:1958` は各ループで 5 ms sleep、`:2014`→`:2027` は起動後の sampler 開始。逐語 `runbook-7.0.md:53`、`:63` は先行 sampler と間隔 ≪1 ms。`plan:53` 自体は差を正しく認めているが、`brief:9` の「7 項目が埋まる」という完了条件だけでは測定方式の適否を区別できない。

   **判定：real。** 5 ms は実サンプル間隔の上限でもない。読み取り処理・スケジューリング遅延が加わり、開始前の空白もある。ピークの持続時間・増加速度を観測していないため、下振れ量を数値で限定できない。3 反復でも、25%／128 MiB の margin で吸収できる保証はない。

   **成果物への影響：** 小さい観測値と「分類実測」の見出しが結び付くと、テスト自身または model 本走を軽い側へ倒せる。

   **推奨：** 見出しを「既存 pytest scope の参考観測（正式分類には不使用）」、本走欄を「未実測・unknown」とする。断り書きは次の逐語を提案する。

   > 以下は既存 `tools/run_tests.py` による専用 bounded scope の `memory.current` 観測値である。sampler は scope 起動後に開始し、各ループで 5 ms 待機するため、§7.0 の先行 sampler・間隔 ≪1 ms の手順による実測ではない。開始直後およびサンプル間のピークの取り落とし量は未評価であり、規定 margin で吸収できることも確認していない。正式な certified peak は未確定で、この値から資源 class を変更しない。観測対象は記載した pytest argv・fixture の実行であり、凍結入力による model 本走は未実測、unknown のままである。

   「最大値＋margin」を参考計算する場合も、**certified peak 欄には入れない**。対象 model の 5 files／297,814 bytes を pytest の入力欄に転記しない。`-n 0` と 32 worker の実 argv も別に残す。

2. **主張：cap が異なる 3 走を、同一条件の 3 反復として認証できない。must-fix。**

   **根拠：** 逐語 `runbook-7.0.md:90`〜`:95` は測定の効力を argv・入力に限定し、**cap 変更時の再測定**を要求する。`plan:77` は実効値と予算値を区別するが、cap 別の集計条件は未指定。

   **判定：real。** 提示値は次のように分ける必要がある。

   | 走行 | 提示された cap（bytes） | 観測ピーク（bytes） |
   |---|---:|---:|
   | `-n 0` rep1 | 3,940,686,240 | 159,653,888 |
   | `-n 0` rep2 | 1,073,741,824 | 156,565,504 |
   | `-n 0` rep3 | 1,073,741,824 | 161,529,856 |
   | 32 worker | 本依頼の提示情報にはなし | 2,834,767,872 |

   **成果物への影響：** 161,529,856 bytes は「異なる cap を含む観測集合の最大」であり、共通条件を認証する最大値ではない。

   **推奨：** cap 別には 1 走／2 走と記録する。短命実行の 3 回要件へ合算しない。cap は reclaim・終了挙動に影響し得るため、「観測値が cap より小さい」だけでは cap 非依存と判定しない。

   また `tools/run_tests.py:1824`〜`:1833` は要求値とページ丸め後の値の両方を受理する。rep1 の値が予算表示由来なら、**実効 `memory.max` の実読値とは書けない**。各走の元ログで出所を区別する。

3. **主張：指定 insight path が、配置違反だけで `check_docs.py` の赤になるという攻撃は成立しない。**

   **根拠：** `output/README.md:82`〜`:85` は新規資料を日付ディレクトリへ置く規約。一方、`tools/check_docs.py:2654`〜`:2670` の insight 列挙は直下 Markdown と exact 日付ディレクトリ直下の Markdown を対象にしており、旧形式ディレクトリを配置違反として拒否する処理ではない。

   **判定：refuted（機械的な赤）。real（通常配置との不整合）。**

   **成果物への影響：** 検査が通っても配置規約への適合や、この README 本文の検査網羅性を証明しない。

   **推奨：** 通常規約に沿う配置は次である。

   `output/insights/2026-09-14/t2267-exec-site-classification/README.md`

   親 brief 自身が検査対象なので、親が今回指定したパスを理由に「既存の凍結資料・固定パス実験の継続」という `output/README.md:85` の例外を自動適用しない。なお、実ファイル未作成・checker 未実走のため、成果物全体の rc は判定していない。

4. **主張：`base` をどの作業木から取るかが欠落している。must-fix。fragment の基本形式と T-2267 の更新扱いは整合する。**

   **根拠：** `plan:98` は「現本文 digest」とだけ指定。`docs/spool/worklog/README.md:83`〜`:91` は **carry 鎖を遡った実体 item**、かつ **land 先 local main の現物**から取得すると明記する。

   **判定：real。** 指定 worktree や carry stub の文字列を直接 hash する方法では契約を満たさない。

   **成果物への影響：** 古い `base` は fold を停止させる。`check_docs.py` の成功では検出できない（`docs/spool/README.md:76`）。

   **推奨：** land 先 local main を cwd として、既存の読取専用 lookup `python3 tools/spool_fold.py --base-digest '[T-2267]'` で取得する旨を追記する。親の `--dry-run --show-diff` を残す。

   worklog の H2 2 本、decisions の `{{D:...}}`、命名・frontmatter は計画どおりでよい。ただし `title` は worklog のみ、decisions 見出しに日付を付けない（`docs/spool/README.md:44`、`docs/spool/decisions/README.md:30`）。T-2267 は `更新`、変更しないなら carry とし、調査 wave の終了を T-2267 の `完了`へ転記しない（`docs/spool/worklog/README.md:64`）。

5. **主張：凍結入力の repo 内複製を一律禁止する根拠はない。ただし入力発見は永続的な再現性確保とは別である。**

   **根拠：** `output/README.md:53`〜`:66`、`hooks/README.md:138`〜`:144`、`hooks/guard_write.py:59`〜`:76`。保護対象は WAL・lock・build cache 等であり、全 JSON の複製禁止ではない。`tools/t2216_backoff_walk_model.py:1408` は入力 bytes の SHA-256 を検証する。`plan:151`〜`:155` は外部入力の発見・復元を述べる。

   **判定：refuted（一律複製禁止）。real（保存寿命の限界）。** 指定された外部 2 本の SHA-256 を本段でも再計算し、両方とも pin `f46cebdd2691e3012c4632d3d6e82a050bb262aa43a0e8dd3aa6ffd66d604931` に一致した。

   **成果物への影響：** job ディレクトリが消えれば、path と hash だけから 269,108 bytes を復元できない。

   **推奨：** 「調査時点で完全一致入力を発見、保存継続は未確認」と記録する。repo 内へ保存する場合も、元 path・digest・由来を保持する再現資料であり、official campaign の WAL／lock／certified 材料へ昇格させない。保護対象へ直接復元する案は不可。

   引用・原文 path・完全 digest・サイズ・照合日は**発見の監査記録には足りる**が、将来の再実行保証には足りない。外部 root が使い捨てであるという `output/README.md:60` の制約を、bytes 一致だけで解消済みとしない。

6. **主張：仕様書を作っても実行経路は有効にならない。裁定パッケージに適用外の層を明示する必要がある。**

   **根拠：** `plan:106`〜`:123` は成立条件と裁定衝突の記述。実際の admission は `hooks/guard_bash.py:614`、`:1205`、正本との集合比較は `tools/check_docs.py:4453`〜`:4462`。逐語 `runbook-7.0.md:106` は非 `tools/pegasus/` path の `local-ok` 登録も拒否する。

   **判定：real（適用範囲の明記不足）。**

   **成果物への影響：** docs-only の受入成功を「対象本走が認可済み bounded 経路で動く」と読み替えられる。

   **推奨：** 裁定パッケージに次を列挙する。

   | 層 | 本 wave の扱い |
   |---|---|
   | hook admission | 変更・新経路の発火検証は scope 外 |
   | admission registry 正本 | 登録変更・class 昇格は scope 外 |
   | runbook §7.0 投影表 | 分類変更の反映は scope 外 |
   | `check_docs.py` 集合完全一致検査 | 既存検査の実行は親の検証。検査変更は scope 外 |
   | 新経路の受入全走 | 未実装なので未実施。docs-only の受入と区別 |

   裁定候補は「D180 の受理集合・族再設計との扱い」「D210 の entry point 内限定との整合」「対象 path と現行 registry 制約の扱い」。今すぐの実装案としては返さない。

   D1938 が保つ資源上限・全子孫の charged memory・記録・unknown・迂回禁止・共有差分／RSS 不採用について、プランに明示的な緩和は見つからない。上記 1・2 の記録上の省略で緩和した結果にならないようにする。

## 棄却した攻撃

- テスト fixture の成功・低ピークから model 本走を分類できる：`plan:44`〜`:53` が明確に否定している。
- 32 worker の値を 32 で割れば逐次実行や model のメモリ量になる：cgroup charge の構成も実行内容も異なり、根拠にならない。
- insight の旧形式配置は必ず checker の赤になる：その配置拒否を現物に確認できない。
- 凍結 pin 一致 JSON は repo へ一切複製できない：指定規約にその禁止はない。
- `--help` が通る、dispatcher が `local-ok`、docs 検査が通ることが本走の認可・実測証拠になる：いずれも保証する範囲が異なる。

## 読めなかった資料

なし。指定必読資料は読取可能だった。親のメモリ実測値は依頼本文の提示値として評価しており、元の stdout・stderr・rc の独立再検証は行っていない。