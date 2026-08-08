---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-08
wave: dev-wave-t665-t662-launch-binding
seq: 1
title: 起動値の機械束縛 ([T-665] + [T-662]) の設計択一を裁定へ返した — 実装はしていない (docs のみ、実装差分なし、受入は再走待ち、変異は免除、branch worktree-dev-wave-t665-t662-launch-binding)
---

## 本文

- **ユーザー裁定 (2026-08-08、`rulings-inbox/2026-08-04-rulings-session-5rulings.md` §47) に基づく設計 wave。**
  「[T-665]/[T-662] = 束ねた設計 wave 起票可 (launcher 集約か receipt 事後検査かをパッケージで返す)」。
  **実装差分ゼロ**で終端し、段 5・6 を飛ばして `4→7→8→9` を通った (`DW-S04` の「実装しない」裁定)。
  変異 matrix は同条項で免除。裁定パッケージと逐語は
  `output/insights/2026-08-08_t665-t662-launch-binding/`。
- **段 3 の敵対 2 レンズはいずれも NO-GO** (レンズ A = sol / must-fix 7、レンズ B = luna / must-fix 8)。
  両者が独立に一致した中核は 3 点。(i) 段 2 プランの推奨 A+ が挙げる採用条件
  「raw `codex exec` を契約違反にする」は**契約文を足すだけなら docs pin と同じ強度**で、
  本 wave が解こうとしている問題の再演である。(ii) 純粋な事後検査案は既存の壊れた段分類を
  再利用するため viable でない。(iii) stage matrix の所有は [T-184] にあり、本 wave が
  新規定義してはならない。
- **親が 1 件を refuted に裁定した。** レンズ B は「既存決定 D60 が『現用 Codex 相談は launcher を
  経由しない』と決めている」として移行境界を must-fix にしたが、D60 の「この launcher」は
  `orchestrator/codex_roles/` の **role runtime launcher** (pinned Codex + bwrap を要求する休眠
  サブシステム) を指しており、争点の `tools/codex_worker_launch.py` ではない。
  レンズ B 自身が同 report 内で両者を別物として引用していた。**D60 は launcher 集約案の障害にならない。**
- **親自身の実測を 1 件訂正した。** 段 1 で「`turn_context` は 1 session あたり 1 件」と書いたが、
  レンズ A の指摘を受けて再測したところ **109 session 中 14 件 (12.8%) が 2 件持ち**だった
  (ただし 14 件とも model / effort は不変)。検査は「最初の 1 件」ではなく全 `turn_context` を
  対象にしなければならない、という不変条件へ書き換えた。
- **決め手は「trust の強さ」ではなく「取りこぼし率と docs 予算」だと実測で確定した。**
  過去 wave ([T-181]) を遡って走査すると、13 session のうち **6 本 (46%) が wave worktree 以外の
  cwd** で走っており、[T-665] が名指しする段 6 fix 子 4 本が全部そこに入る。これは
  `DW-S05-A` / `DW-S06-B` が実装子・fix 子を別 worktree へ隔離する**契約どおりの挙動**である。
  時刻窓で補うことはできない — 同じ時間窓に 70 session / 14 cwd が存在し、当該 wave は 13 本だけ
  (5.4 倍の過剰包含)。
- **収集層は既に存在し、production で使われていないことを再測で確認した。**
  `tools/codex_worker_ledger.py` が rollout から model / reasoning を決定的に集計し、
  `--manifest` の exact selector まで持つ。`tools/codex_worker_launch.py` を参照する非 output
  ファイルは自テストのみ ([T-595] 裁定 3-1 の再測)。**欠けているのは権威と突き合わせる層だけ。**
- **その段分類は既に drift で無効化していた。** 段の判定は prompt 先頭行の正規表現 ([T-179] 当時の
  英語 role 語を要求) で、実測 33 session 中 30 が `unclassified`。現行 wave の prompt 先頭行は
  自由文で 10 種類以上あり、規則に合致するものは 1 件も無い。**失敗台帳 fragment は書いていない** —
  `docs/spool/failures/README.md` が恒久対応に実体へのポインタを要求するのに対し、本 wave は
  実装ゼロで宣言だけの恒真な対応にしかならないため。機構が入る実装 wave で起票する。
- **三案とも docs 予算に収まらない。** aggregate 残 16 bytes に対し純増は概算 350〜1,200 bytes。
  レンズ B は worktree 命名規約だけでも 91 bytes (裸 ASCII でも 53 bytes) と実測した。
  したがって本 wave の裁定は「どれを選ぶか」に加えて「**[T-664] の予算捻出を先に置く**」という
  順序の判断を含む。
- **受入を 2 走した。** 1 走目 (request 896121、1176 秒、7394 passed / 20 skipped、rc=0) は
  peer (t627) の land で main が `4816049f` へ進む前の tip を測っていた。計算ノードへ投入済み
  だったため中断せず完走させ、取り込み後に land する tip そのもので再走した。
- **段 8 の改善候補は 1 件。** `DW-O01` の実行雛形を worktree 隔離セッションで逐語のまま inline 実行
  すると harness の隔離 guard が拒否する (本 wave で 2 回)。起動 command を wave 専用
  subdirectory の `.sh` へ書けば通り、これは `DW-O02` の置き場義務と同型である。
  **本文編集は byte 予算不足のため見送り、[T-664] 後へ寄せた** (台帳記録のみ)。

## 次の一手差分

### 更新

- [T-665] **P2・ユーザー裁定待ち**: 段 6 の子が指定 effort で実際に起動することの機械保証。
  設計択一を `output/insights/2026-08-08_t665-t662-launch-binding/package.md` の R1〜R5 として返した。
  [T-662] と同一機構で同時に閉じる。実装の前提条件は [T-664] (docs 予算) と [T-184] (stage matrix 所有)。
  base: 23cff820f53d659479c81928dc4291d09580d95e6a1af41f76b2d9b072521907
- [T-662] **P2・ユーザー裁定待ち**: codex の `-m` 実引数と `DW-O01` 権威行の機械照合。
  [T-665] と束ねて同じ R1〜R5 で裁定する。純粋な事後検査案は段分類の drift により viable でないと
  裁定済み。served model の attest は [T-189] の所有のまま。
  base: c2055d74d450150a2e840902761c3299030df45926141ddb50615f849c419c9d
