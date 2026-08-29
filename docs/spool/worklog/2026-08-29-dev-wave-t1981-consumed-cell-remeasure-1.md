---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-t1981-consumed-cell-remeasure
seq: 1
title: [T-1981] 床値の残件を塞ぐ T-2043 が未解消と実測し、床値 job を投入せず停止した (docs のみ、branch worktree-dev-wave-t1981-consumed-cell-remeasure、変異 matrix 免除)
---

## 本文

- ユーザー裁定: T-1981 の残件は「消費済み 12 cell が再測定を妨げない」の実機証明 1 点に絞る。
  着手前に塞ぎ要因の現況を実測し、解消していれば投入、未解消ならその実測を記録して停止する。
- ユーザー裁定: `dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal` 配下の
  fix-1 / impl-a / impl-b の未 commit 差分は統合対象ではなく作業くずとして扱い、取り込まない。
  対応 branch がいずれも main の祖先であることが根拠。
- ユーザー裁定: 新しい機構・署名・台帳を足さない。
- codex との不一致の決着: codex は「3 worktree の未 commit 差分を監査・統合してから実機確認へ」を
  推した。監査の結果、統合部分は成立しない。3 worktree の未 commit 差分は
  いずれも main より古い中間状態であり、main に無い内容を 1 件も含まなかった。
  fix-1 の差 2 file は取り込めば着地済みの検査 2 件と walltime 内訳コメントを巻き戻す。
  impl-a の作業木には測定世代の識別子を作る 3 関数が無く、置き換え前の状態だった。
  impl-b の差は claims / consumed の旧 directory 名を使う点だけだった。
  ユーザーの「作業くず」判定を実測が支持した。表に出す差はない。
- 塞ぎ要因の実測 (2026-08-29 09:44 JST): 台帳が指す [T-2043] は未解消である。
  D1192 が定めた根相対 path と使用時の canonical base 再束縛を実装した branch は
  main の祖先ではなく、main の `_external_entry()` は `resolve(strict=True)` のまま。
  失敗 job の compiler input manifest 588 件のうち 38 件が現時点で解決できず、
  内訳は job scratch 配下の gflags/glog header 7 件と、publish 時に改名される staging
  directory 配下の FetchContent masstree source 31 件だった。後者は同一 job 内で必ず消える。
  31 件は D1192 本文の実測件数と一致する。
- 床値 job は投入しなかった。投入しても binary admission receipt の発行段で同じ本文で落ち、
  gen_S の枠を捨てるだけで「消費済み 12 cell が再測定を妨げない」の証拠にならない。
- T-2043 の修正は本 wave で肩代わりしなかった。別 wave が現に進行中であり
  (branch tip は 2026-08-29 09:39 JST の受入準備 merge)、同じ編集面を二重に触れば衝突する。
- 実装面の差分はゼロ。段 2・3・5・6 の子は起動せず、変異 matrix を免除した。受入全走は免除していない。
- 台帳の持ち越し stub は塞ぎ要因の現況を語らない。T-2043 の本文はエントリ 1053 から一度も
  更新されておらず、現況は branch の祖先関係と tip 時刻を見て初めて確定した。

## 次の一手差分

### 更新

- [T-1981] **P1・実装完了、実機確認が残件**: 予約の可否を決める経路から一回性 key の照合を外し、
  測定世代へ置き換えた。承認 flag と env 伝播も floor 経路から撤去した。実機投入で
  「承認なしで投入できる」「`already consumed` が出ない」までは確認済み。
  **残件は「消費済み 12 cell が再測定を妨げない」ことの実機証明だけである。**
  2026-08-29 09:44 JST に塞ぎ要因を実測した。塞いでいるのは一回性ではなく [T-2043] の
  ビルド段の欠陥で、**未解消のまま**である。D1192 を実装した branch は main の祖先ではなく、
  `s8b_compiler_input.py` の `_external_entry()` は `resolve(strict=True)` のまま残る。
  失敗 job の manifest 588 件中 38 件が現時点で解決できない (job scratch の header 7 件、
  publish 時に改名される staging directory 配下の FetchContent source 31 件)。
  そのため床値 job は投入していない。T-2043 が着地したら床値を再投入して本項を閉じる。
  実装面の証明は旧 claim 12 件・旧 marker 96 件を配置した統合テストと、それを壊す変異 2 件
  (91 node / 6 node) が担っている。
  残骸 3 worktree の未 commit 差分は監査済みで、いずれも main より古く取り込む内容は無い。
  base: e3c2cb5e743129ffbd296a289501c28a8cf8b39014ec07f94d1d6e9c791d1b83
