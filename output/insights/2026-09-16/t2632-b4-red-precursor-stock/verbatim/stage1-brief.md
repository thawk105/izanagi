# [T-2632] B-4 の適格な赤 precursor の在庫確保

- 目的: 適格な赤 precursor の在庫を 0 件から増やす。得られなければ不成立を結果として記録する。
- 状態: 進行中 (段 1)
- 最終更新: 2026-09-16 JST
- 基準コミット: d97c423bdd14e0b416cb4f585d350e6c2b251287 (local main)
- wave worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2632-b4-red-precursor-stock
- wave branch: worktree-dev-wave-t2632-b4-red-precursor-stock

## 完了した中間成果 (段 1 前の実測)

- クラス 3 起動手順、DW-C00 / DW-C01 / DW-STOP / DW-S01 / DW-G01〜G05 / DW-S04 / DW-S07〜S09 /
  DW-CTX、DW-O01 / O02 / O08 / O09 / O10 / O20 / O23 / O25 / O26 / O27 / O28 を読了。
- 現行 worklog 末尾は entry 1544 ([T-2636])。T-2632 は「次の一手」に 5 期連続で残る未了項目。
- 在庫を現物で再実測した。tracked な `loop_state.json` は 3 件のみ。whiteboard は合計 7 行で
  すべて `result=success`、`rejected` は 0 行。2026-09-14 の観測と一致する。
- 全木走査でも新しい供給源は 0 件。hit した他 `loop_state.json` は全部 worktree 内の同一 3 file の複製。
- 別 campaign `p3-s4-red-s4-red-consumer-9a1897c4` は `s4_rejections_digest.txt` に赤 3 件を持つが
  `loop_state.json` を持たない。1 件は `src_token=fixture`。供給源を変えないので算入しない。

## 段 1 brief

- **研究前進**: B-4 (reflux ablation) は Phase 3 の機序主張実験である。§5 の「赤 precursor の母集合」
  欄が未記入で適格な赤 precursor が 0 件のため、§5.1.1 の選択関数が `design_not_feasible` を返し
  実走できない。本 wave は在庫を 0 から増やす経路が現行機構で実在するかを実測し、実在すれば調達する。
  完了判定は (a) 適格性述語の第 1 項を満たす行を 1 件以上得る、または (b) 得られない構造的理由を
  実測で確定し insight へ記録する、のいずれか。
- **scope**: 在庫確保の可否判定と、可能な場合の調達。それだけ。
- **scope 外**: 供給源の変更。適格条件の変更。成功例への置換。母集合を作るための追加基盤。
  n の切り下げ。仮想リスク向けの gate・検査・台帳・一般化の追加。
- **確定済みユーザー裁定**: D1936 項 8 (合成ループから得た適格な少数の赤 precursor を使い、供給源と
  適格条件を黙って変えない。**成功例への置換・固定 201 だけの無言の削減・母集合を作るための追加基盤は
  採らない**)。D1880 の 201 行。§5 の `n = 201`。§5.1.1 の一括凍結。
- **引数の前提訂正 (段 4 で再裁定する新事実)**: 依頼文の「成功例への置換と母集合を作る作業であり」は、
  台帳 T-2632 の原文 (`docs/archive/worklog-phase3-0915-1500.md:695-697`) にある
  「成功例への置換と母集合を作るための追加基盤は D1936 項 8 が不採用にしている」の切れた写しである。
  原文と D1936 項 8 に従い、本 wave はどちらも行わない。
- **不変条件**: 規律 2 を緩めない。適格条件を緩めない。無理に数を作らない。§5.1.1 の bytes を変えない。
  凍結文書の記入済み欄を先に現物で読む (entry 1544 で 4 者が同じ誤認をした型の再発を避ける)。
- **成果物**: insight 1 件 (成立・不成立いずれでも逐語と結論)。worklog fragment。実装面の差分は最小。
- **(P1-a)** 現行実装では `whiteboard.result == "rejected"` は diff 検疫 reject だけを指す
  (`p3_s4_loop.py:1877,1899,1911` の 3 箇所がいずれも `record_diff_reject` 経由)。
  verify / liveness 赤は `fail` になる (`:1792`, `:1968`)。よって §5.1.1 第 1 項を満たしうるのは
  diff 検疫 reject だけである。親の provisional 裁定であり攻撃対象。
- **(P1-b)** 第 2 項 (校正済み `PerfConfig` の workload 所属) と第 3 項 (固定 bootstrap 集合所属) は
  §5 の該当欄が未記入で評価できない。よって今日作った行を「適格」と確定できない可能性が高い。
- **(P1-c)** 在庫を増やす許容経路は、既存 driver で合成ループを実走し赤の自然発生を記録することだけ。
  手作り proposal で検疫を落とすのは母集合製造にあたり不採用。
- **(P1-d)** 実 LLM は `main()` が呼ばず、メインセッションが planner-v4 / coder-v4-autonomous を
  spawn して proposal JSON を渡し `--run-iteration` を呼ぶ (`p3_s4_loop.py:2542-2547` の docstring)。
  実走は CC 合成 campaign の実行であり、本 command の「開発ループであって合成 campaign の実行ループ
  ではない」という枠と衝突する。段 4 で裁定する。
- **DW-G05 成果物影響**: 在庫 0 が続くと B-4 は実走できず、材料レポートの B-4 機序証拠が空欄のまま
  固定される。
- **DW-G01**: 専用機構を作らず既存 driver で最安の生死確認をする。
- **分割方針**: 設計択一が割れ凍結契約の読みに触るので軽量版の免除は使わない。段 2 plan 1 本 +
  段 3 敵対 2 レンズを起こす。実装面が出れば段 5 は Codex author (D95)。
- **受入・実測環境**: 実測は Pegasus login node の read-only 検査まで。build / campaign 実走は
  段 4 裁定後にだけ判断する。

## dev-wave 改善候補

- (未記入。段 8 で埋める)

## 落とし穴・気づき

- `git worktree add` が共有 FS 上で 11 分超かかる (worktree 114 本)。timeout を掛けない。
- `find` を repo 全体へ掛けると 120 秒を超える。`git ls-files` で引ける対象はそちらを使う。
