推奨は、**現役 consumer・path pin・移動で壊れる相対参照を持つ対象を旧位置に保留し、それ以外を日付階層へ移す限定移行**です。全1075件の即時移動は不要ですが、移動集合の閉包確認と移行後件数の確定を実装前の条件にします。

静的調査のみ実施しました。ファイル変更・pytest・完了 checker は実行していません。

1. **比較と移動対象**

   直下1077件を再確認しました。日付付き1075件の内訳は、ディレクトリ783、Markdown 205、gzip 52、JSON 34、patch 1です。

   | 案 | 直下件数 | 判断 |
   |---|---:|---|
   | 全1075件を移動 | 約76件。72日＋既存非日付2件＋案内2件 | path pin の変更が広がるため非推奨 |
   | 散文中心の限定移行 | 一次候補142件なら979件 | incoming link・output 内 pin 未確認。余裕も小さい |
   | 保留条件を満たすものだけ残し、ディレクトリも移動 | 閉包確定後に算出 | 推奨 |

   追加の保守的な文字列検索でも139件・48日、計算上988件となる候補が残りました。ただし圧縮内容、組み立てたパス、参照元との閉包は未確認です。**どちらの候補数も移動承認済み件数ではありません。**

   移動は `2026-07-26_foo → 2026-07-26/foo`。ディレクトリは内部を一切書き換えず丸ごと移します。移動先衝突、symlink、未追跡の実体混在は保留します。

2. **保留すべき実在の参照**

   以下は一括置換対象にしません。表のほかにも、確定候補ごとに完全パス・basename・役割名・digest を検索します。

   | 分類 | 実在箇所 | 最小方策 |
   |---|---|---|
   | 凍結 bytes と独立 key 集合 | `orchestrator/tests/test_frozen_artifacts.py:41`, `:98`, `:126`, `:243` | 7月16日の5文書を旧位置に保留。manifest・独立集合・hash を変更しない |
   | 現在の実体を読む consumer | `orchestrator/campaign/s1_known_axes_freeze.py:67`, `:69`, `:571` | recon・sort insight を保留 |
   | 現在の実体を読む consumer | `orchestrator/campaign/s6_proposal_rounds.py:36`, `tools/pegasus/t141_region_profile.sh:1293` | N1 provenance を保留 |
   | canonical path と hash の束縛 | `tools/plotting/plot_a2_certification.py:48`, `:65` | A2 certification の該当ディレクトリを保留 |
   | 事前登録・出力先の束縛 | `orchestrator/campaign/paper_story_a1_headline.v1.json:2`, `paper_story_a1_paired.v2.json:43`, `paper_story_a2_certification.v2.json:9`, `paper_story_a6_certification.v2.json:9` | 登録済み study の素材・出力先を保留 |
   | placeholder の path 単位の例外 | `tools/check_docs.py:227`, `:241`, `:2715` | 該当2文書を保留。例外集合を変更しない |
   | commit と旧パスで履歴を取得 | `orchestrator/publication/approval_d291.py:62`, `tools/codex_reasoning_ab.py:3340` | `commit:path` を維持。現在の配置に合わせて変更しない |

   `git show <固定commit>:<旧path>` は、その commit の名前空間です。現在のファイル移動とは別に扱います。一方、同じパスを HEAD でも読む箇所があれば、その対象は保留します。

   output 内外の manifest、review ledger、generator source hash、schema の全 field hash も確認対象です。durable manifest の再発行が必要になる対象は今回保留し、既存 hash を更新して通す案にはしません。

3. **相対リンクと旧記録**

   実在例として、`output/insights/2026-09-02_cicada-adaptive-three-constants.md:54` は同階層の figures を相対参照します。本文だけ移すと画像が壊れます。また `output/insights/2026-08-11_t813-acceptance-sharding/verbatim/s3-luna-out.md:31` は上位階層へ抜ける参照を持ち、ディレクトリ丸ごとの移動でも解決先が変わります。

   判定は次のとおりです。

   - ディレクトリ内部で完結するリンクは、内部配置を維持して移動可能。
   - 境界を越えるリンク、別日付へのリンク、画像、参照形式リンク、HTML、symlink は移動前後の解決先を比較。
   - 旧記録の本文変更が必要なら、リンクの両端を保留する。新規破損と既存の破損は区別する。
   - 生きた案内文書の参照だけ、確定した移動先へ個別修正する。
   - 過去記録の旧パス文字列は保持し、新設の対応表から現在位置をたどれるようにする。

   対応表はクリック可能な旧名→新パスと、保留対象・理由を掲載します。旧 URL の自動転送にはならないため、外部の旧リンクが全件そのまま開けるとは主張しません。

4. **最小の実装箇所**

   - [output/README.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-insights-date-layout/output/README.md:68)
     新規配置を `insights/YYYY-MM-DD/topic.md` または `insights/YYYY-MM-DD/topic/` に変更。`:89` の sidecar 例も合わせる。登録済み study の旧出力先は例外として維持する。

   - 新設 `output/insights/README.md` と対応表
     README から日付フォルダ、保留資料、対応表へリンクする。日付フォルダ内にも必要なら短い README を置く。一覧を作るだけで直下1000超を残す実装にはしない。

   - [tools/check_docs.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-insights-date-layout/tools/check_docs.py:2591)
     `:2654` の直下限定 `glob` を、旧直下 Markdown と新しい日付直下 Markdown を検査する形に局所修正する。日付ディレクトリの symlink・読取不能も既存同様に失敗させる。無条件の `rglob("*.md")` で従来対象外の深い逐語記録まで検査範囲を広げない。既存 debt の2パスは保留する。

   - [.claude/commands/next-tasks.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-insights-date-layout/.claude/commands/next-tasks.md:150)
     新しい順の列挙を、日付ディレクトリと旧直下の両方を見る説明へ変更する。

   - 一回限りの移行処理
     確定した明示的な移動表を入力にし、衝突確認後に移動するだけとする。既存の実験 consumer に汎用 resolver を追加しない。

   `tools/ruleops.py:507` は再帰的な Git tree inventory、`:72` は階層を許すパス判定です。配置変更だけを理由とする機能追加は不要です。

   新規出力は日付階層を使います。ただし既存 study の再実行・継続出力は、上表の登録済み旧パスを維持します。新規 producer のパス指定まで旧形式が残らないよう、可変の作成手順・テンプレートを確認します。

5. **移行テストと実体保存の確認**

   実装者が以下を実施します。

   - 移行前の tracked file 全件について、パス・Git mode・blob OID・サイズを採取する。移行後は対応表を逆適用して完全一致を確認する。gzip は再圧縮せず、圧縮 bytes 自体を比較する。
   - 保留対象はパス・bytes とも不変。新規案内以外の既存資料に本文差分がないこと、消失・重複・衝突がないことを確認する。
   - Git tree 基準で insights 直下と新しい日付階層の件数を確認し、少なくとも直下を1000未満にする。README から移動・保留の全件へ到達できることを確認する。
   - 相対参照の解決先を前後比較し、新規のリンク破損を検出する。
   - `orchestrator/tests/test_check_docs.py:5132`, `:5536`, `:5730`, `:6274` 周辺に、新階層の正常入力・未許可 placeholder・symlink・読取不能の回帰ケースを追加する。旧 debt の別パスへの replay が拒否される性質を維持する。
   - 固定 commit の旧パス取得、保留した frozen manifest、影響する consumer を回帰確認する。測定値・受理集合の期待値は変更しない。

   テストは `tools/run_tests.py` 経由。その後 `check_codex_agents.py`、`check_docs.py`、commit 後の `check_ai_provenance.py` を実施します。本段で緑を確認したものはありません。

## 総括

**推奨方針:** path pin と現役参照を旧位置に残し、参照の閉包が確認できたファイル・ディレクトリを bytes 不変で日付階層へ移す。変更は案内、新規作成規約、文書 checker の列挙、個別の生きた参照に限定します。

**未解決 blocker:** 最終移動集合、incoming link・圧縮内容・非パス key を含む pin 閉包、保留後の直下件数が未確定です。142件→979件は一次試算に留まります。閉包確認で1000未満を達成できなくなる場合は、安全なディレクトリ移動を追加し、索引だけの案には後退しません。
