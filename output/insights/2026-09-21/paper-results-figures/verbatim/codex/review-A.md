## 所見

パスは審査対象 worktree 相対。既知の pytest 依存 4 件は以下に重複計上しない。

| # | 重大度 | 対象 (file:line / README 節) | 内容 | 根拠 (file:line・一次資料の逐語・計算) | 推奨 |
|---|---|---|---|---|---|
| 1 | must-fix | `tools/plotting/README.md:514` | **Fisher・commit 数平均の照合先を誤記している。**「k / m / CP / 片側 Fisher / commit 数平均を計算して `summary.json` と照合」は、後二者にも独立照合があると読める。 | 外部 `summary.json` に Fisher・commit 平均はない。生成器 `plot_mocc_witlight_four_arm.py:208–215` の照合対象にもない。稿 `2026-09-20-mocc-witlight-four-arm.md:307–308` は summary と親の会計を区別し、figures README `:1998–1999` も「Fisher p と commit 数平均は summary.json に無い」と正しく記載している。 | summary に存在する量の照合と、Fisher・平均・曝露比の稿との test による照合を、別文にする。生成器の変更は不要。 |
| 2 | must-fix | `docs/paper-story/figures/README.md:1894,2003` | **自己参照回避の根拠として追加した F36 参照が別内容を指している。** | `docs/failures.md:2002` の F36 は「受入・検査の結果欄をプレースホルダのまま記録 commit」。本文も実測欄の空証明と事後補完禁止についてであり、稿と provenance の相互 hash の規則ではない。今回の brief にも同じ取り違えがあるが、成果物側の引用を正当化しない。 | 新規節の F36 参照を削除するか、自己参照回避を実際に定めた正本へ置換する。凍結された既存成果物の改訂は不要。 |
| 3 | should | `orchestrator/tests/test_plot_mocc_witlight_four_arm.py:244–281` | **曝露比の可視注記を削除・誤表示しても、artist 検査が検出できない。** F623／F653 型の未被覆箇所が残る。 | 生成器 `:307–308` の `exposure_notes` 描画だけを削除しても、`:313` の内部系列は残る。test `:254–263` が読む実 artist は点・区間・`numeric-column` のみで、`:275–280` の必須可視文字列にも曝露比はない。caption／provenance 閉包は内部系列の一致なので、この描画欠落を検出しない。 | 2 本の曝露比注記を可視 `Text` と照合し、各注記の削除または値の変更を検出する負例を追加する。静的に判定した穴であり、変異実走済みとはしない。 |

## 変異 M0〜M13 の kill 見込み

以下は静的見込み。既知 4 件を修正して baseline を緑にした後の判定を想定する。

| 変異 | 見込み・根拠 |
|---|---|
| M0 | **SURVIVED 見込み**。生成器コメントは数値・caption に影響せず、生成時の source hash を現行 source の pin として比較していない。現 baseline は既知 4 件が赤なので、そのまま「全 test 緑」とは言えない。 |
| M1 | **KILLED 見込み**。既存 `test_variance_plan_breach_true_is_rejected` が、整合した true を scope 拒否まで到達させる。 |
| M2 | **KILLED 見込み**。`test_attempt2_pinned_input_hashes_match_results_document` が凍結稿の hash と直接比較する。 |
| M3 | **KILLED 見込み**。既存 fig9 着地閉包が保存済み caption と現行生成器の caption を完全一致で比較する。 |
| M4 | **KILLED 見込み**。attempt2 caption test にプール・比較禁止文の独立 literal がある。 |
| M5 | **KILLED 見込み**。breach 表示 test は実際の `ax.get_title()` と可視 `Text` を独立に組み立てた題と比較する。 |
| M6 | **KILLED 見込み**。`test_production_pins_match_results_document` が稿 §5.1 の summary hash と直接比較する。 |
| M7 | **KILLED 見込み**。smoke entry 追加後に summary を再封印するため、hash 拒否に隠れず exact inputs 検査の除去を識別できる。 |
| M8 | **KILLED 見込み**。CP test は生成器から作らない数値 literal を `atol=1e-14` で比較する。 |
| M9 | **KILLED 見込み**。`[[0,60],[1,59]]` の期待値 `.5` と行反転時の `1.` が片側方向を識別する。 |
| M10 | **KILLED 見込み**。commit test は G2 走の commit 数も変え、arm 別生値の独立総和を **60** で割って比較する。 |
| M11 | **KILLED 見込み**。必須開示 test が可視 `Text` 内の `exposure, not performance` を要求する。 |
| M12 | **KILLED 見込み**。caption と可視 `Text` の禁止句走査が題の `equivalent` を検出する。ただし既知の例外文比較を先に修正する必要がある。 |
| M13 | **KILLED 見込み**。正常データの実 Figure に重なりだけを追加し、`_publish_outputs` の layout 拒否を要求する。呼出しを除けば拒否されず赤になる。 |

## 探したが所見なしの項目

- **追加の pytest／plain runner 差:** 両 test file の `except AssertionError` と `str(exc)` 比較を探索した。完全一致依存は既知の 4 件だけ。既存 fig9 の比較は `startswith`、入力拒否 helper は部分文字列比較であり、同型の追加箇所は見つからなかった。
- **fig9 の不変性:** commit 差分と AST 比較で、既存 **28 test の本文・期待値に変更なし**。attempt1 の返却 9 key、caption 本文、描画分岐、既定 CLI と記録 argv を維持している。着地 provenance の構造・caption と矛盾する変更は見つからなかった。
- **attempt 選択の拒否:** fig14 の `attempt` 欠落は attempt1 の `tracked_inputs` と不一致になる。未知 attempt、pin key 集合の交差、attempt2 に attempt1 の caption_source を記録した provenance も、loader／全 data key の閉包比較で拒否される。attempt1 の breach true 拒否は残っている。
- **fig15 の受理集合:** exact inputs、再封印した smoke 追加、failure／indeterminate、回転、witness・pin・TRACE・BACK_OFF・workload argv の検査経路を確認した。外部 root 存在時に file 欠落を skip する経路はない。
- **主張の境界:** 両 caption、描画コード、provenance、README 新規節を照合した。attempt 間の値の混入・プール・差・比・再現判定、breach の原因帰属、非有意から同等性への飛躍、曝露量の性能扱い、G2 の根因同定は見つからなかった。
- **数値・日時・所在:** 外部 W1〜W4 を読み、各 60 走、host、開始終了時刻、G2 の W1 ordinal 18／round 5 と W3 ordinal 5／round 2 を確認した。commit 総和は順に `36,824,488 / 42,639,565 / 47,333,137 / 56,017,308`。60 で割った平均と曝露比 `0.8636 / 0.8450` は稿・provenance と一致する。
- **CP／Fisher:** CP の分位と境界処理、Fisher の片側和は適切。0/60 上限 `0.059629492286…`、1/60 区間 `[0.000421874452…, 0.089399050057…]`、Fisher `0.500` は整合する。summary 照合の絶対許容差 `1e-12` は表示精度より十分小さい。
- **閉包の射程:** fig15 の repo 側は保存統計の自己整合、外部側は 5 原本からの再導出という区別が figures README に明記されており、そこに過大な保証は見つからなかった。

## 総括

**must-fix 2 件、should 1 件。判定は条件付き GO。**
must-fix は、README の照合先の誤記と F36 の誤参照である。
現在の図・caption・provenance の主要数値に誤りは見つからなかった。
曝露比の可視注記には、描画欠落を見逃す test の穴が残る。
M1〜M13 は静的には kill 見込みだが、登録外のこの穴まで保証しない。
親の log は `800 passed / 4 failed / 3 skipped` であり、全緑とは扱っていない。
既知 4 件の修正、上記 docs 訂正、関連検査の確認を経て確定するのが妥当である。
本レビューでは file 書込み・作図・テスト・変異実走を行っていない。