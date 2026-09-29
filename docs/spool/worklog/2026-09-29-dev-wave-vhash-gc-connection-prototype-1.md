---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-gc-connection-prototype
seq: 1
title: VHash の forwarding 試作を Cicada の GC 回収境界へつないだ (構成 E)。前進が成り立つ skew 0 では回収境界の遅れ −54%・版の保持時間 −47%、zipf 0.9 では「今」への前進がほぼ成り立たず効果なし。モデルの公開手順を写す途中の下限更新が待機中の既読版を回収させる誤りを保持版検査で見つけて直した (patch + driver + 登録 + insight、branch dev-wave-vhash-gc-connection-prototype)
---

## 本文

- 依頼: 並行 VHash wave の md_14 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_14.txt`、U0 の実物での確認)。途中でユーザーから「続けて」の指示のみ。正本: `output/insights/2026-09-29/vhash-gc-connection-prototype/README.md`、設計判断は {{D:vhash-gc-connection-prototype}}、失敗は {{F:model-refs-vs-implicit-floor}} と F683 の再発。
- md_11 (Cicada の較正) が段 5 の投入直前に local main へ着地したので、依頼項 6 に従い比較の Cicada 設定を md_11 の観測最良 (BACK_OFF=0・INLINE_VERSION_OPT=1・INLINE_VERSION_PROMOTION=0・REUSE_VERSION=1・WRITE_LATEST_ONLY=0) に改めた (段 4 裁定の追補)。
- 段 2 plan の「待機位置を write の前へ移す」「tx 境界で begin() を GC flag 待ちにする」は不採用。段 3 相談 A の弱メモリの指摘 (rts の CAS と版列の再観測の store-buffering 型) は、stock の validation が同じ順序付けに依存し計算ノードは x86 なので E 固有の弱化ではないと裁定し、限界に記した。段 6 焦点再レビューの「待機ループの桁あふれで極端に長い sleep」は、sleep が min(残り, slice) で有界なので must-fix としては棄却した。
- 段 4 の親の仮裁定 P5 (安全点で読み取り下限を最新の MinWts−1 へ上げる) が誤りで、smoke 4 の保持版検査が E-hb 159 / 3,938 の既読版の変化を出した。段 3 の 2 本・段 6 の 2 本・焦点再レビューは反例にしなかった。修正後は全 run で 0。
- 段 6 の fix は単位 A (C++ と登録) 4 巡・単位 B (driver・起動器・作図) 7 巡。うち実機でだけ出た不具合 (dependency build 抜け、`#line` のずれ、-Werror の未使用引数、検査起動器の dependency build 抜けと旧 genome、作図の文字の重なり) が 6 件。fix 1 巡目の単位 B は、F6 (必須 job の揃い) が同じ wave の新設テストの期待と衝突し、prompt の「既存テストの期待値を変更しない」に従って停止した。親が従属する期待を列挙していなかったのが原因で、2 巡目で許可範囲を列挙して通した。
- base 035fc11fa にあったテストの期待で変えたのは、条件 gate の 3 macro 登録に伴う件数・集合の追随だけ (D2288 と同じ足跡)。
- 変異: 10 件 (MG1・MG2・MD1〜MD5・MF3・MF6・MS1) を束ね経路 (D842) で。probe 35659、final 35801 (KILLED 9・MISMATCH 1)、MF6 の erratum 再走 35814 (KILLED)。MF6 の期待 node は probe が skew 軸を足す前の commit だったため古く、新設の parametrize テスト 6 件が殺していた。段 6 の real 所見の変異 (MF3・MF6・MS1) は fix の後に登録した (DW-M01 は fix の前を求める、記録のみ)。
- セッション異常 (実害なし): EnterWorktree は name 形が filter driver の読取エラー、path 形が worktree list の 10 秒上限で失敗し、手作りの worktree を絶対 path で使った。最初の worktree add は Lustre の EINTR で最後の index reset が失敗し、残骸を撤去して --no-checkout → reset --hard に分けて作り直した。16:2x〜16:3x はユーザーの git push のため land 調整役の依頼で git 書き込みを止めた。焦点走 1 回は待ち行列の上限 900 s に当たり子が起動せず (上限を延ばして再走)。親の報告 2 回が英語になった。
- 段 8 (自己改善) の候補 4 件: モデルの保護の取り違えは failures へ新規で送った。変異の事前登録の遅れは DW-M01 が既に求める内容の見落としで文書は変えない。「同 wave の新設テストの期待に従属する fix は変えてよい期待を裁定に列挙する」(DW-S06-B) と「子の成果物を repo のテストから参照させない」(DW-C01) の 2 文は、足すと L1.5 の予算 (9,801 > 9,696 byte) と DW-C01 の単節予算・exact 契約を超えるので見送り、次の dev-wave 文書の整理で扱う。
- エージェント工数: Codex plan 1・consult 3 (うち 1 本は未作成の成果物 path を必読と誤読して停止し再投入)・author 2 (うち単位 A は model 呼び出し上限 100 で最終報告の前に停止)・review 2・focus 1・fix 11 (いずれも gpt-6-sol / medium)。子の worktree `.claude/worktrees/vhash-gcp-author-a` / `-b` (branch codex-vhash-gcp-a・-b・fix1〜fix7) と dispatch 用の detached 木 7 本。計算ノード: smoke 5・検査 2・本計測 6 (6 台同時)・焦点走 6・変異 3、Elapse 合計 4,564 s (約 1.27 node 時間、受入の全走を除く)。

## 次の一手差分

### 完了

- [T-2900] VHash の C++ 試作の GC 接続を確かめ、回収境界の前進と回収を実測した ({{D:vhash-gc-connection-prototype}}、一次資料 `output/insights/2026-09-29/vhash-gc-connection-prototype/README.md`)。
  remaining: none
  base: 6ecb3b6d6e8a4d75c835676278dfcb73039fc92c71f0612c90877d70f015c70f

### 新規

- {{T:vhash-forward-target-choice}} **P2・新規**: VHash の GC 接続 (構成 E) の前進先の選び方を比べる。md_14 は「今」の時刻へ前進し、zipf 0.9 では既読のどれかが待機中に上書きされて前進の 99.7% 以上が失敗した (効果なし)。既読の可視区間に収まる最大の時刻 (最も早い上書きの直前) へ前進する方策などを、同じ driver・同じ主比較 (E 対 E-hb) で比べる。根拠: `output/insights/2026-09-29/vhash-gc-connection-prototype/README.md` §4.3・§8。
