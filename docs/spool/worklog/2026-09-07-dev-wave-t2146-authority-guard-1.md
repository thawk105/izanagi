---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-07
wave: dev-wave-t2146-authority-guard
seq: 1
title: "[T-2146] 発行主体 subtree を hooks の書込み防護対象へ足した — 敵対レビューが既存防護の弱体化を 1 件見つけ、直して 8/8 KILLED (コード + テスト + docs、branch worktree-dev-wave-t2146-authority-guard)"
---

## 本文

- **依頼が引いた手順 (D374) は現行 main では実行不能だった。** 段 2 と段 3 の両レンズが独立に
  倒し、親も実測で確かめた (`hooks/` 配下は Write / Edit / apply_patch / Bash のどれからも
  編集できない)。正本は {{D:d427-guard-edit-route}} が既に定めていた D427 (有効化前 commit を
  base にした第 2 worktree + merge)。D428 の反転検査も同時に発火する。段 1 brief の N1 は誤り
  だったので段 4 で差し替えた。
- **着手前の実測 — 発行主体 root は完全に無防備だった。** Write、redirect 書込み、`rm -rf` が
  すべて許可されていた。着地後は同じ probe で全部拒否へ反転し、読取りだけ許可のまま。
- **段 6 の敵対レビュー 2 本がどちらも NO-GO を出した。最も重いのは既存防護の弱体化。**
  単位 A1 が `perf` の出力先へ発行主体判定を足した際、出力値を後段の既存判定から除外したため、
  末端でない既存の防護対象 (official / exploration campaign tree、namespace marker、`hooks/`
  配下、ccbench) が `perf` の出力先として通るようになっていた。実測での退化は 6 形。
  **親が最初に回した 61 件の反転検査 corpus はこの形を含んでおらず取り逃していた。**
  規律 2 に直接触れるので最優先で直し、恒久テストも足した ({{F:perf-output-weakened-existing-trees}})。
- **祖先判定の filesystem root 漏れ**も採用済み項目の取りこぼしとして閉じた。
- **段 6 の fix1 子は作業場の施錠に当たって適用できず、正しく「未適用」と報告して止まった。**
  直前の単位が現行版の `guard_write` を入れたことで第 2 worktree 自身も施錠されていた。
  親は `guard_write` に判定が入る前の commit から fix 用 branch を作って作業場を復活させた。
  この運用知見は `hooks/README.md` の「guard 自身の保守境界」へ 3 点として記録した
  ({{F:second-worktree-locks-itself-after-guard-write}})。
- **変異 M2 は独立した位置になっていなかった** (段 6 レビュー A)。apply_patch も共通の判定を
  使うため等価変異になる。DW-M01 / F28 に従い登録から外し、`perf` 退化を狙う変異へ再照準した。
- **既存テストの赤の帰属**は両レビューが「実装は正しく期待値が新設計を反映していないだけ」で
  一致。ただしレビュー A が「単に 2 へ書き換える案」を不採用とし、root ごとの走査回数を個別に
  見る形へ改めた (元テストが守っていた「候補ごとの再走査を禁じる」性質を保つため)。
- **親の実測 (すべて親が実行)。** 焦点走は fix 前 1158 passed / 1 failed → fix 後
  **1163 passed / 0 failed / 4 skipped**。D428 反転検査は子の 61 件 corpus で `deny → allow` 0 件
  (`allow → deny` 9 件、すべて発行主体関連)、親が独自に書いた 32 件 corpus (レビューが見つけた
  `perf` の 6 形入り) でも `deny → allow` 0 件 (`allow → deny` 7 件)。変異本走は baseline PASSED、
  **8/8 KILLED**、MISMATCH 0、TIMEOUT 0、等価変異 1 件のみ SURVIVED。provenance 全史監査
  3112 件で新規違反なし。`check_docs` 違反なし。
- **主張の上限を README へ明記した。** 書込みを閉じただけでは受領証の偽造不能性は主張できない
  — 秘密鍵の読取りは通り、読める主体は署名を作れる。0700 は同じ利用者として動く AI を隔離
  しない。言える上限は「信頼済み PreToolUse が観測する直接書込み面から発行主体 subtree を
  追加で除外した」まで。「完全ロック」「D906 を満たした」とは書いていない。
- **エージェント工数。** codex 子 11 本 (plan 1 / consult 2 / author 3 / review 2 / fix 3)。
  うち fix1 は施錠で未適用のまま完了し、fix1b として作業場を作り直して再投入した。
  fix2 は正常完走したが runner の外側が落ちて完了印が書かれず、成果物を attempt file から
  回収した (F23 の再発として記録)。
- **裁定パッケージをユーザーへ返す。** (1) D906 の実効層 — 真正性を機械的に主張するには鍵と
  署名実行権限を AI から分離した別 principal / 別 host / hardware signer が要る。本着地は
  D906 の完了根拠に数えない。(2) shell 状態模型 (`pushd` / `env --chdir` / subshell / 条件実行の
  cwd 追跡) はどの防護対象でも成立しておらず、閉じるなら全対象へ同時に入れる独立 wave が要る。
  (3) 既存欠陥 2 件 (`perf` の密着短 option、読むだけの `cp` が拒否される非対称)。

## 次の一手差分

### 完了

- [T-2146] 発行主体 subtree を hooks の書込み防護対象へ足した。段 6 の敵対レビューが見つけた
  既存防護の弱体化 1 件と祖先判定の取りこぼし 1 件を直し、変異本走 8/8 KILLED・焦点走
  1163 passed / 0 failed・D428 反転検査 2 系統とも `deny → allow` 0 件で閉じた。
  remaining: none
  base: 1caa4c0ba75187e7ac17b5e093f7eb5a5be6ab6f79a9c713a7fa4d03e697eccb

### 新規

- {{T:d906-effective-boundary}} **P1・ユーザー裁定待ち**: D906 の真正性を機械的に主張するための
  実効層を決める。鍵と署名実行権限を AI から分離した別 OS principal / 別 host / hardware signer
  のいずれを採るか。現状の書込み防護は「直接書込み面の縮小」までで、秘密鍵の読取りは通る。
- {{T:shell-state-model-for-all-guarded-trees}} **P2・新規**: `pushd` / `env --chdir` / subshell /
  条件実行の cwd 追跡を、発行主体だけでなく全防護対象へ同時に入れる独立 wave を設計する。
  現状はどの防護対象でも成立していない。
- {{T:perf-attached-short-option-and-copy-out}} **P3・新規**: `perf` の密着短 option (`-oFILE`) が
  専用分岐に認識されない件と、読むだけの `cp` が拒否されるのに `cat` は通る非対称を直す。
  どちらも発行主体に限らない族の問題。
