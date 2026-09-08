---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2401-evaluator-reason
seq: 1
title: [T-2401] 評価器例外の理由を fail-closed のまま構造化して残した — 変異走行が「歯の立たないテスト」を 3 件暴いた (コード + テスト + insight、branch worktree-dev-wave-t2401-evaluator-reason、変異 26 件全件 KILLED)
---

## 本文

- **本 wave の主眼は診断の追加だが、実際に一番の収穫は変異走行が暴いた 3 件のテスト欠陥だった。**
  段 3 の敵対相談 2 本と段 6 の焦点再レビュー 1 本は、3 件とも検出していない。
  いずれも「テストが緑になる経路」しか読んでおらず、**テストが落ちたときに走行系がどうなるか**を
  誰も見ていなかった。詳細は {{F:hostile-fixture-breaks-failure-reporting}} と
  {{F:guard-test-cannot-observe-the-guard}}、逐語は
  `output/insights/2026-09-08_t2401-evaluator-reason/README.md` の §3。
- **変異走行に 4 回の走行が要った。** 1 回目は敵対 fixture が pytest の失敗報告経路を壊して
  rc=3 で停止、2 回目は `KeyboardInterrupt` を負例にしたため pytest が session 中断と解釈して
  rc=2 で停止、3 回目で 2 件が生存して CLI guard の恒真テストを暴き、4 回目で全件が検出に転じた。
  観測 node を完全集合として登録した本走で 26 件全件 KILLED・完全一致。
- **親 brief の誤りを 1 件、段 3 の敵対レビューが訂正した。** brief は
  「`ActivationReport` に field を足すと台帳が全件不一致になる」と書いたが、正しくは
  「**非 null の activation digest を束縛した registered-effective の成果物**が不一致になる」で、
  exploratory と formal non-certifying は digest が `None` なのでこの理由では変わらない。
  field を足さない不変条件自体は変わらない。
- **親の手続きの漏れが 1 件。** 焦点走で `test_plain_runner_coverage.py` の陳腐化検出が赤になり、
  親が `orchestrator/tests/README.md` の pytest 専用 allowlist から 1 行を外した。
  この編集を段 6 裁定の scope 表へ書き落としていたため、焦点再レビューが「裁定外の変更」として
  指摘した。指摘は事実として正しい。差分は戻していない (戻すとメタテストが赤に戻る)。
- **scope 外と裁定した real 所見が 2 件。** (a) gate report CLI は診断を持たない旧 API を呼ぶため
  F631 が閉じていない。(b) 判定器 CLI の外側 catch は `str(exc)` を stderr へ出しており、
  repo path や環境依存の git エラー文が混ざりうる。どちらも本 wave が入れた経路ではなく、
  同型の catch の修正ではなく機能追加・既存挙動の変更に当たる。次の一手へ登録した。
- **fix は 5 巡した。** 内訳は段 6 レビュー由来が 2 巡、親が変異走行で実測した blocker 由来が 3 巡。
  後者は `DW-O16` の 3 巡上限とは別枠 (親の実機 blocker)。
- 設計判断と却下案は {{D:evaluator-diagnostic-outside-report-digest}}。
- **受入全走を 3 回投入した。** 1 回目は 48 error + 2 failed。うち 1 件だけが本 wave 起因で、新設 test の Python 起動 4 箇所に bytecode guard が無かった (F521 の再発)。残りは `git ls-files --others --exclude-standard` が受入の並列負荷下で 30 秒 timeout に当たったもので、同じコマンドを単独実行すると 1.6 秒・untracked 0 件、当該 node の単独走も3 passed だった。2 回目は本 wave 起因の赤が消えて残り 1 件、3 回目が `child-green` (22066 passed / 68 skipped / 赤 0)。**この記録 commit の後にもう 1 度投入した最終受入が land 対象である** (受入後の記録 commit は land できない契約のため)。
- **段 8 の自己改善は 1 件を候補にし、実装は見送った。** F521 の恒久対応は failures 台帳にしか書かれておらず、dev-wave が受入前に読む節には無い。`DW-O26` (焦点走の対象選定) へ 1 行統合すれば読み経路に入るので、既存の理由説明を F ポインタへ圧縮して 992 bytes (上限 1000) に収まることまで確かめた。**しかし `DW-O26` は `tools/check_docs.py` の `DEV_WAVE_DW_O26_SECTION_LITERAL` に節全体が byte 単位で pin されている。**docs と checker の結合変更になり Codex author が要るため、受入直前に単独判断で入れず{{T:dw-o26-repo-wide-checker-line}} として登録した。
- **安い関門を先に通す作法が効かなかった回でもある。** `check_docs` と provenance は回したが、`--repo` を取る checker の棚卸しをせず、受入 1 走を 1 件の違反発見に使った。F521 の恒久対応の再掲。

## 次の一手差分

### 完了

- [T-2401] 評価器例外の理由を fail-closed のまま構造化して残した。fail-closed の終端
  (status、reason_code、evidence、effective、CLI stdout の bytes、report digest) は 1 bit も
  変えていない。受理集合は広がっていない。
  remaining: none
  base: 16c004ba2fc2e14e9b528e413e818bd9f4b640480fe317bceffb356df011dd14

### 新規

- {{T:s8c-gate-report-diagnostics}} **P3・新規**: gate report CLI は診断を持たない
  `activation_report_at` を呼ぶため、評価器例外の理由が同 CLI からは読めない。
  露出させるかを裁定する。露出させるなら gate report JSON の形が変わるので単独の変更単位にする。
- {{T:s8c-cli-outer-catch-detail}} **P3・新規**: 判定器 CLI の外側 catch が
  `print(str(exc), file=sys.stderr)` を実行しており、`PreregistrationError.detail` 経由で
  repo path や環境依存の git エラー文が stderr へ出る。本 wave が足した 3 field の診断とは
  別経路である。変えると既存 CLI の stderr 出力が変わるため、受理集合の観点で裁定する。
- {{T:dw-o26-repo-wide-checker-line}} **P3・新規**: 焦点走は参照関係で対象を引くため、repo 全体を走査する checker 系 test を集められない。F521 はこの型で 2 回踏んでおり、恒久対応 (受入前に `--repo` を取る checker を叩く) は failures 台帳にしかない。`DW-O26` へ 1 行足すと読み経路に入るが、同節は `tools/check_docs.py` の `DEV_WAVE_DW_O26_SECTION_LITERAL` に byte 単位で pin されているため docs と checker の結合変更になる。入れるかを裁定する。
