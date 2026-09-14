---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t2593-tail-formal-submission
seq: 1
title: [T-2593] 静的 tail 本走の投入経路へ走行種別 t2500-tail-formal を配線した (コード + docs、branch worktree-dev-wave-t2593-tail-formal-submission)
---

## 本文

- **配線までを行い、本走は投入していない。** 依頼が投入を scope 外と明示している。
  成果物と生証拠 = `output/insights/2026-09-14/t2593-tail-formal-submission/`。
- **親 brief の不変条件を段 3 の敵対相談が壊し、契約を書き直した。** brief は
  「既存 3 系列の観測可能な挙動を 1 bit も変えない」と書いたが、投入 script が job へ渡す
  環境変数には job script 自身の SHA-256 が入る。job script を編集する以上この値は必ず変わるので、
  bytes 完全一致の比較は書いた瞬間に赤か、値を潰して恒真かのどちらかにしかならない。
  **可変値を消さずその場で検証する**契約へ改めた。決定は {{D:legacy-argv-invariance-verifies-variable-fields}}。
- **段 6 のレビューが実挙動の欠陥を 1 件見つけ、親が対照つきで実測した。** 探索走の path を
  `realpath` で正規化する際、出力を `$( )` で受けていたため末尾の改行が落ちていた。
  名前が改行 1 文字で終わる directory を渡すと、**要求したのとは別の directory** が計算ノードへ
  渡る。leaf の symlink 検査も `.../link/.` で回避できる。修正前の版は同じ入力で探索走の検査を
  通過し、修正後は rc=2 で拒否することを親が実走で確かめた。番兵を 1 文字足して改行を保つ形に直した。
- **同型の穴が既存 `--output-parent` の正規化にも在るが直していない。** 旧 3 系列の受理集合を
  変えるため。新規項目として起票した。
- **集団報告の入口は新しい Pegasus 実行体を作らず、手順文書 + CLI 束縛テストで置いた。**
  `tools/pegasus/` へ実行体を置くと admission registry へ実行場所の分類を宣言する必要が生じるが、
  本 wave には集団報告を走らせる材料が無く実測で裏づけられない。置き場所をずらして inventory
  検査を避ける案は採らなかった。決定は {{D:cohort-entry-without-new-pegasus-executable}}。
  段 6 のレビュー B はこれを must-fix として出したが、上の理由で不採用にした。
- **段 6 の fix 子 1 名が、指示された修正と同じ wave のテスト期待値の衝突を報告して停止した。**
  「既存テストの期待値を変更しない」契約に従い、何も編集しなかった。親がその期待値を誤りと裁定し、
  変更を許可する範囲を名指しして投げ直した。握り潰されていれば、旧 3 系列の終了コード集合を
  広げる変更 (未知引数の後ろの `--help` が rc=2 から rc=0 へ) が黙って land していた。
- **段 6 の焦点再レビューは closed 4 / partial 2 / regressed 0。** partial 2 件は親が裁定して
  閉じた。(a) job script の中間区間はどのテストも実行しない — PBS と実測が要るため。
  **この穴は本 wave 以前から同型で存在し**、既存 2 系列のテストも同じ形で断片を抜いている。
  新しい 2 環境変数がその区間で壊されないことの静的検査で補った。
  (b) group id の PID 部が実 PID かは検査していない — 一意性は保たれ receipt 衝突は起きないので
  成果物影響を 1 行で書けず、nit とした。
- **変異は 11 件を事前登録し、本走で 11/11 KILLED・MISMATCH 0・SURVIVED 0。** 基底も PASSED。
  過剰拒否の正例を 1 件入れた (妥当な 40 桁 commit を弾く変異) ところ、正常経路のテスト 3 本と
  負例 1 本が反応した。probe 走 (全件 SURVIVED 登録) で観測 node を集めてから本登録した。
- 実測: 基底 523 件緑 1 skip → 配線後の焦点走 685 件緑 1 skip → 段 6 fix 後 702 件緑 1 skip。
  受入全走は `verdict = child-green` (red 0 / flake 0)。
- Codex 子 11 本 (plan 1 / consult 2 / author 2 / review 2 / fix 3 / focus 1)。すべて `gpt-6-astra`。
  **段 5 の実装子 2 名と段 6 の fix 子 3 名は、いずれも sandbox に scheduler の実行 file が無く
  `rc=16` でテストを走らせられず、5 名とも「実装済み・未実走」と正直に申告した。**
  実走はすべて親が行った。F964 と同じ型である。

## 次の一手差分

### 完了

- [T-2593] 投入 script と job script が走行種別 `t2500-tail-formal` と新しい 2 入力を受理し、
  job が本走 driver を起動し、完了確認が新しい成果物を見るようにした。3 走を 1 集団として
  報告する手順を文書 + CLI 束縛テストで固定した。本走の投入は依頼どおり行っていない。
  remaining: none
  base: fc64d6268a50d93ec24ec6c5107b69ce92e8f39fe0efc1128722db4f46976c7d

### 新規

- {{T:output-parent-realpath-newline}} **P3・新規**: `tools/pegasus/submit_b10_backoff_grid.sh` の
  `--output-parent` も、`realpath` の出力を `$( )` で受けているため末尾の改行が落ちる。
  名前が改行で終わる出力親を渡すと別 directory へ書く。新しい探索走の入力では番兵で塞いだが、
  こちらは既存 3 系列の受理集合を変えるため本 wave では触っていない。同型の穴が他の投入
  script にもあるかを併せて見る。
