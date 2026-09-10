## 総括

**brief の二原因は確認できました。ただし P1 は、そのままでは成立しません。** 現行 A-1 は実ビルドにも未 patch の submodule を渡しています。関門だけを patched source に変えると測定対象とずれ、patched source を実ビルドにも渡すと、既存の canonical pinned-clean 検査で拒否されます。

したがって、**「A-1 driver／関連テストだけ」「既存の拒否を維持」「policy・patch bytes 不変」の全条件を満たす、attempt-0004 投入までの実装プランは現物から確定できません。** 以下は、確定できた最小配線と、親へ返す具体的な成立阻害点です。編集・commit・submit・pytest 実走はしていません。

**コードで確認した事実**

| 箇所 | 確認結果 |
|---|---|
| `orchestrator/campaign/paper_story_a1_paired.py:6748` | 関門の source は `external/ccbench`。`:6752` の capture は configure 引数なし。 |
| 同 `:6901`、`:6993`、`:7022` | 検証済み dependency-prefix は `run_campaign` にだけ渡る。関門には渡らない。 |
| 同 `:7022` → `loop.py:347` → `buildcache.py:614` | `ccbench_dir` を指定しないため、実 build も既定 submodule を使う。この呼出し列に patch 適用はない。 |
| `patchharness.py:346`、`:247` | 既存 API は `checkout()` と `applied()`。前者は隔離した clean tree、後者は patch 適用から revert までの寿命を管理する。 |
| `loop.py:755` → `pipeline.py:1942`、`:1082` | balanced 経路は各 trace/perf build 直前に、**実際の `ccbench_dir`** の canonical HEAD と tracked-clean を要求する。patch を当てた tree は `:1129` で拒否される。 |

canonical pin `511c9538…` の `include/backoff.hh` と `cmake/Options.cmake` を `git show` で直接確認しました。前者に marker／固定量 decoder はなく、後者にも `BACKOFF_FIXED` の供給定義がありません。既存 patch が両方を追加します。これは単なる marker の読み違いではありません。

**最小の file:line 配線案**

1. **依存と configure 引数の配線**

   [paper_story_a1_paired.py:6734](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2397-a1-attempt4/orchestrator/campaign/paper_story_a1_paired.py:6734) の関門に、検証済み `dependency_prefix` と実 build の compiler 情報を渡す。呼出し変更は同 `:6993`。

   configure の基準は `buildcache.py:1922` の `_v2_commands()`。Release、sanitizer OFF、C/C++ compiler、明示 prefix、arm flags、`CCBENCH_TRACE=0` を揃える。既存組立 API の出力を使い、関門自身が持つ `-S/-B`、C++ compiler 指定と重複させない。

   **`CCBENCH_BACKOFF_FIXED` は capture の共通引数から除く。** requested/default/stock の値は `condition_meaning_gate.py:1664` が供給する。共通引数に残すと、stock configure に未使用変数を持ち込み、比較も汚染する。

2. **arm ごとに capture する**

   同 `:6744` の値だけの反復を、`genomes(policy, workload)` の各 genome を保持する形にする。`BACK_OFF` は variant が 1、baseline が 0 なので、全 arm に共通の capture では実 build と揃わない。

   固定量は各 workload の `10/5/2`、baseline は `-1`。baseline の `stock_comparison=True` と `STOCK_ADAPTIVE_BRANCH` を維持する。両 arm の supply／meaning を全部評価してから、既存 family admission を一度呼ぶ。

3. **source の配線――ここが未成立**

   使用する既存 API は、canonical pin の独立した stock checkout と、もう一つの checkout に対する `patchharness.applied()`。capture は bytes の完全コピーではなく root と identity を保持するため、**両 evaluator の完了まで context を生かす**必要がある。

   実 build と同じ source を保証するなら、patched context は同 `:7022` の `run_campaign(..., ccbench_dir=patched_root)` まで保持する必要がある。しかし、これは上記 pinned-clean 検査に必ず抵触する。

   **関門終了時に revert して未 patch source を build する案、clean 検査だけ別 root に向ける案、dirty 拒否を削る案は採らない。** 前二者は測定対象との束縛を失い、後者は既存の拒否を変える。現 scope でこの矛盾を閉じる既存 A-1 materializer は確認できなかった。

4. **T-2514 はそのまま維持**

   同 `:6704` の保存関数、`:6819` 以降の拒否時保存、`evidence_root=raw_root` を保持する。赤で途中打切りせず、green を含む全 arm record と admission を保存する。保存失敗で元の拒否を消さず、成功時に拒否記録を追加しない。

**関連テスト・consumer・変異候補**

| 対象 | 必要な検査 |
|---|---|
| `orchestrator/tests/test_paper_story_a1_paired.py:4093` | 3 workload を対象に、patched root・distinct stock・arm 別 flags・prefix・source 寿命を検査。現テストは未 patch source を期待しており修正が必要。 |
| 同 `:4191` 以降、`:4470` | T-2514 fixture を既存 materializer の context に対応させ、全記録、元の拒否、書込み失敗、例外伝播、raw-root 配線を維持。 |
| `orchestrator/tests/test_condition_meaning_gate.py:626`、`:1736`、`:2142`、`:2167` | stock preprocess 同一性、stock 不一致、marker 重複、decoder 改変の既存負例を維持。 |
| `orchestrator/tests/test_campaign.py:13463`、`:13472` | canonical clean 正例と HEAD／tracked 差分の負例を維持。patched source を実 build に渡した際の衝突を検出する。 |
| `paper_story_a1_paired.py:4893` | `_trace0_commands_match()` は実 build argv を厳密比較する consumer。関門固有の export 引数などを実 build に追加しない。 |
| 同 `:7364`、`:8520`、`:6687` | source binding、raw 再収集、非認証 observation consumer を維持。関門の green だけで測定・verify の証拠を代替しない。 |

追加変異は、①prefix 脱落、②未 patch root への差戻し、③baseline に variant の `BACK_OFF=1` を流用、④stock 比較の無効化、⑤最初の赤で残り arm を省略、⑥capture 後に context を閉じる、⑦関門だけ patched／build は stock、を具体候補とする。⑦を検出できない mock 正例だけでは、今回の修正を受け入れない。

**freeze pin の影響**

- pilot policy SHA は `ed1c942f…`、preregistration SHA は `8f8d2ad3…` と静的確認済み。変更不要。
- `test_paper_story_a1_paired.py:903` の既存 frozen bytes、patch bytes、canonical pin、過去 attempt は変更しない。
- driver の変更は新 attempt の source binding に反映される。過去成果物の hash を更新して現行 driver に合わせない。
- `test_paper_story_a1_headline.py:1232` の non-touch 検査は固定された過去 commit 間を検査するため、今回の変更を理由に更新しない。

**実行用 probe**

成立阻害点の解消後、既存 dependency staging を使う計算ノード上の使い捨て probe で、production 関門を各 workload 一度ずつ呼ぶ。新 CLI／汎用 gate は不要。さらに既存 campaign 経路で、関門の source が各 trace/perf build に届き、canonical 検査と verify を通ることを確認する。関門単体の成功を attempt-0004 の投入可能性と同一視しない。

親へ返す論点は一つです。**D1936 項3の「実際に測る patch 適用後 source」と、現行 balanced build の「実 build tree が canonical tracked-clean」という契約をどう両立させるか。** ここを未解決のまま、関門だけの修正を二原因の閉鎖として扱うことはできません。