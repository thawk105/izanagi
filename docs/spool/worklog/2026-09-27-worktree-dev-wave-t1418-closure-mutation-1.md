---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-27
wave: worktree-dev-wave-t1418-closure-mutation
seq: 1
title: [T-1418] 変異 harness に commit 注入モード (--inject commit) を足し、contract-loader 閉包の member の変異を値の層で観測できるようにした。loop.py の実 dispatch で、file-swap では等価変異も drift で owner を落とし、commit モードでは等価変異 SURVIVED・値変異は owner だけ KILLED (コード + test + docs、branch worktree-dev-wave-t1418-closure-mutation)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`、逐語 = `output/insights/2026-09-27/t1418-commit-injection/verbatim/request.md`): harness 側か fixture 側のどちらに閉包を横断する安全な変異経路を持たせるかを段 1 で決めて実装する。本題の実装だけ。設計判断は {{D:mutation-commit-injection}}、F424 の記述訂正は failures fragment、測定と経緯は同 insight の README。
- 起点 = local main `ad114fba0` (fresh worktree、開始 gate rc=0)。段 1 で harness 側に決めた: fixture 側の opt-out は D1712 が規律 2 違反として却下済みで、F424 が名指しした fixture は b4ff38f6b で既に no-op だった。
- 段構成は軽量版にしなかった (段 2 plan 1・段 3 相談 2・段 5 author 1・段 6 review 2・fix 1・焦点再レビュー 1)。harness は正しさ gate の歯を示す計器で、誤った KILLED / SURVIVED は変異台帳の値を変えるため。
- 段 3: 正しさ境界 NO-GO (残留した変異 commit を fresh が固定 HEAD として受理する等)、過剰・削除は条件付き GO (ledger v5・wrapper 中継・変異 commit SHA の台帳は削れる)。段 4 で v4 据え置き (policy 文言でモード束縛)・wrapper / fanout 不変・残留 commit の起動拒否を裁定した。
- 段 6: review 2 本とも NO-GO、共通 must-fix = runner 後の再検査が dispatch の orphan 判定より先。fix 1 巡で直した。焦点再レビューは 7 所見中 closed 4・裁定で直さない nit 2・partial 1 (HEAD 照合単独の負例が無い、should)。partial は親裁定で fix 巡を足さず backlog にした (変異 M9 は再検査ブロック全体で検出、HEAD だけ動く状況は runner が作らず成果物影響を示せない)。
- 段 4 の erratum 1 (実行前に訂正): 変異と dogfood の置き場を独立 clone から主 repo の登録 detached worktree (`.codex/worktrees/t1418-mut`) へ変えた (新規 clone は submodule URL が非 local で初期化 tool に拒否される)。
- 焦点走 (計算ノード): 変更 test file 単独 (M1) 170 passed (実装後) → 173 passed (fix 後)。consumer 10 本 + DW-O26 の inventory 4 群 + `test_ccbench_spawn_sites.py` で 1804 passed・8 skipped (実装後)。
- 変異 (final、commit 54d472756、harness 直当て): harness 自身の M1〜M9 は 9/9 KILLED で期待と完全一致、probe では 9 件とも狙いの test 以外の赤 0。dogfood (loop.py): commit モードで等価 SURVIVED・値変異 KILLED (owner 1 node)、file-swap で両方 KILLED (drift)。
- 全史 provenance 監査 (実装 commit 後) は 12970 件で新規違反なし。三軸語走査は rc=1 だが hit は既存の `output/env/pegasus/calibration/` の file (rr80 で 3 件) だけで、本 wave の file は 0 件。
- 段 8: 候補は「閉包 member の変異は `--inject commit` で drift 層を外す」を dev-wave の変異手順へ 1 文足すこと。main 取り込み後の版で DW-M03 に足すと L1.5 が 9777 > 9696 bytes、DW-M01 に足すと L1 が 10684 > 10625 bytes で、同節の空白削減 (約 19 bytes) でも収まらない。段 8 契約 (予算の変更は実装しない) と D730 に従い docs は変えず、参照点は F424 の supersede と {{D:mutation-commit-injection}} に置いた。
- 前進 merge: 段 8 の編集を main の現行版へ当てるため、local main `09ffaed18` を merge した (両親の変更 path に重なり無し、自動 merge)。
- 受入全走は本記録の commit 後に最終 tip で 1 回だけ投入するため、この fragment には結果を書かない。
- scope 外: T-458・T-626 (D2172 項 10 の「次に同 file を触る wave で相乗り」) は、ユーザー指示「本題の実装だけ」により相乗りしていない。
- セッションの出来事: 段 5 の unit worktree 作成時に checkout で `.gitattributes` 1 件へのアクセスが「システムコール割り込み」の警告を出したが、作成後の作業木は clean だった。起動器の終端 commit 後、待ち手が `worktree-commit: clean` を出す (commit の後の状態を見ている) ので、起動器 log の `committed <sha>` で commit を確かめた。
- 工数: Codex 8 本 (plan 1・consult 2・author 1・review 2・fix 1・focus 1)、Explore (sonnet) 1 本。計算ノード: 焦点走 3 job、変異 harness の起動 6 回 (dogfood probe 2 モード・harness probe・harness final・dogfood final 2 モード)。

## 次の一手差分

### 完了

- [T-1418] `tools/mutation_harness.py --inject commit` で閉包 member の変異を値の層で観測できるようにし、実 dispatch の dogfood で等価 SURVIVED・値変異 KILLED を示した。設計は {{D:mutation-commit-injection}}、記録は `output/insights/2026-09-27/t1418-commit-injection/README.md`。
  remaining: none
  base: c5b698e43ae4e729b562cbb56de949bf63c2638a0c273e3bdb897c1a859bb89b
