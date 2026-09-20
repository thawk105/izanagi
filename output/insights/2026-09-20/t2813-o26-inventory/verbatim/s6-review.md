## 所見

1. **レンズ C／nit：4 群の追加は T-2292 全体の解消にはならない。**
   新句は裁定どおりだが、process 起動一覧の `test_ccbench_spawn_sites.py` と subprocess guard の `test_check_subprocess_bytecode_guard.py` は指定 4 群に含まれない。完了報告では、この残件を本 wave の scope 外として区別するのが適切。新しい gate・検査の追加は求めない。
   **放置時の成果物影響：** T-2292 全体を解消済みと扱うと、process site 追加時に両検査が焦点走集合から漏れる余地を残す。
   **根拠：** `verbatim/T-2292-origin.md` の「process 起動一覧と subprocess guard も落ちる」、`docs/dev-wave/operations.md:189–192`、`orchestrator/tests/test_ccbench_spawn_sites.py:2836`、`orchestrator/tests/test_check_subprocess_bytecode_guard.py:223`。

**must-fix はゼロ。以下を確認した。**

- **A：旧→新の義務対応**

  | 旧本文の義務 | 新本文の対応・判定 |
  |---|---|
  | 変更 test と参照関係で引く consumer | 冒頭に保持。「名前の推測でなく」の削除でも選定基準は変わらない |
  | private symbol を symbol 名で production 全体から grep | 保持。探索対象を特定 file に限定する文言は追加されていない |
  | 同一 worktree の dispatch 全種直列 | 明示的に保持 |
  | 変更 test file の受入全走前単独走 | 「受入前に単独走」で保持。受入開始後の実行を許す記述にはなっていない |
  | 新規 test file のメタテストを焦点走に収載 | 節の対象集合と直前の「焦点走に含める」を受ける「も含める」として保持 |
  | 並行 wave の相乗り・受入後に足さない | 条件と禁止を保持 |

  根拠は累積差分の旧本文と `docs/dev-wave/operations.md:187–194`。「初回実測でも」「全走緑は file 単独緑を含意しない」は理由説明で、削除後も実行義務は残る。「焦点走対象 file 集合」→「焦点走 file 集合」も集合を変えない。

- **B：byte 整合**
  正本・docs・production literal・合成 fixture は、読み取り専用の計算で **全て 998 bytes、完全一致、NFC、末尾 LF 1 個**。行折返し・全角半角も一致。`== 998` は正しい。attack 文字列は各本文の **1 行内に 1 回**存在する。根拠：`tools/check_docs.py:618`、`orchestrator/tests/test_check_docs.py:178,7147,9486`。

- **B：M8 と参照閉包**
  M8 の削除対象は本文に 1 回。削除後は **939 bytes**。H2・改行構造・登録集合を変えず、実 bytes と分類済み bytes が同量減るため、静的には exact 不一致だけが成立する。単一所見の期待値も維持されている（`test_check_docs.py:9625`、`check_docs.py:1894,5267,5292`）。
  DW-C00 の rc=16 説明と DW-O26 の直列義務は参照として成立する（`core.md:17–18`）。旧断片の探索で追加の実行可能な依存は見つからず、残存引用は failures・archive の歴史記録だった。

- **C：変更範囲**
  新規義務は D2186 項 5 の 1 句のみ。provenance 監査の候補句は混入していない。4 basename は `git ls-files` で各 1 件、全て `orchestrator/tests/` 直下。prefix・読点・括弧の変更による対象の変化はない。単節上限 1000、exact 登録集合、他節の pin、L1／L1.5 予算は不変。check_docs は新本文を固定する置換で、任意の縮約を受理する変更ではない。

## 親裁定への反証

段 4 §2 の結論を覆す反証はない。D782／D961 の既存記述削減で収容できており、安全義務の削除は確認できなかった。

ただし、削減表の「すべて根拠説明」という分類は厳密ではない。「受入前」「production を grep」「も含める」は義務文そのものの短縮である。今回の文脈では義務を保持しているため、分類の粗さを must-fix とはしない。

## GO / NO-GO

**GO。** 必須修正はなく、既存 6 義務・裁定の追加句・3 者の pin 整合を確認した。

## 総括

静的レビュー結果は **must-fix 0、nit 1**。998 bytes の一致を独立確認した。T-2292 の process／subprocess 検査まで解消したとは扱わないこと。書込み・pytest・checker 実行は行っておらず、author 報告の実走結果を再実測したものではない。