---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-insights-date-layout
seq: 1
title: insights の日付別配置と全件閲覧を整備する（branch worktree-dev-wave-insights-date-layout）
---

## 本文

- ユーザー依頼は同階層1000件超によるGitHub閲覧障害の改善。基準c68d08d9eの直下1077件を調べ、
  588directoryを43日へ移動した。適用直後534件。全17328既存fileのblob/modeを移動時と独立再走で照合した。
- 現役の固定参照と、歴史的なcopytree呼出しログを区別した。後者2pathだけの名前出現をpinと数えず、
  元ログは保持した。旧単独file・実行資材・固定参照・壊れる既存リンクを持つ資料は旧位置に残した。
- 深部raw1422/1424件は動かさず500件以下の計6pageへ全leafの直接リンクを作った。
  方針は {{D:insights-date-layout}}。一次資料は `output/insights/2026-09-10/insights-date-layout/README.md`。
- 最初のauthorはF728の非NFC読取ログで未受理。親が原因を調べず正式停止し、ユーザーへ再開を要求したのは誤りだった。
  ユーザーの「自力で進められる状況で止まらない」「自己改善プロンプトも」の指示で同じbranchを再開した。
  原記録は保持し、ASCII escape表示のauthorが残差分を独立監査して正常受理された。検査器は緩めていない。
- 実資料の数式をリンクと誤認した不具合、過大な名前照合、歴史観測の過剰保留を局所修正し、各焦点レビューを通した。
  新規設計や機械認証へ一般化していない。CC合成・性能測定は新規実施していない。
- 親の関連走: helper最終62pass、check_docs単独574pass/既存保留3skip、登録関連159pass。
  移動後のfrozen/ruleops/plain-runnerは158pass/1fail/1skipだったが、新pytest専用fileの文書登録を補い、
  plain-runner再走3pass。既存テスト期待値・skip・凍結hashは変更していない。
- 変異はanchor7d1194601固定、bnode146でbaseline3pass、3件すべて期待失敗node完全一致、復元完了。
  harness初回のdetached指定漏れは未実走のrc2として残し、新しい出力先と実detachで実行した。
- 実装commit後の全史provenanceは9444件、新規違反なし（既知台帳は維持）。文書検査とCodex agent検査も通した。
  自己改善は {{D:recoverable-failures}} に従い既存必読節へ反映し、専用commitに分けた。
  早計な終了は {{F:premature-recoverable-stop}}、非NFC読取ログはF728の再発として記録する。

## 次の一手差分
