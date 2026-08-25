---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: worktree-dangling-audit-speed
seq: 3
title: 到達不能 commit 監査を 2 時間 23 分から 4 分 43 秒へ短縮した — 要確認 47 commit は不変 (コード + docs、branch worktree-dangling-audit-speed)
---

## 本文

- 依頼は「掃除の必須ゲートである到達不能 commit 監査の所要を 56 分から 5 分以内へ落とす」。
  派生物の除外、fork の畳み込み、実測、掃除ゲートへの所要上限、stdout 進捗の 5 項目。
  計算ノードへの分散と監査そのものの廃止は明示的に scope 外とされた。
- **結果は 2:22:57 (8,577 秒) → 独立 3 走の最大 283.27 秒。** 壁時計 30 倍、CPU 9,330 秒 →
  約 70 秒で 133 倍。maxrss 627 MB → 389 MB。**要確認は修正前後とも 47 commit で一致**し、
  抑止 292 対・除外 13,488 対も 4 走すべてで同値だった。判定は段 4 で決めた手順どおり
  warm-up 1 走を捨てた独立 3 走の最大で行い、最大/最小 = 1.138 < 1.5 なので追加走はしていない。
- 設計判断は {{D:regenerable-artifact-exclusion}} と
  {{D:audit-duration-limit-binds-acceptance-not-deletion}}。
- **依頼が名指しした 2 つの律速は消えたが、5 分に入れたのは名指しされていない 2 つの修正である。**
  commit ごとの 2 fork を bulk `git log` 1 回へ畳む段は 327 秒 → 3.4 秒、派生物除外で要確認対は
  14,104 → 616 になった。しかしそれだけでは 543 秒だった。残りを削ったのは
  (a) landed 参照の owner 重複除去が list 線形探索で二次化していたのを set にしたこと
  (pattern 出現 255 万で爆発していた)、(b) landed 参照の grep pattern を受理済み探索根だけに
  したこと (全 pattern は探索根で始まるので得られる file 集合は上位集合であり、既存の境界付き
  token 照合が同じ抑止集合へ落とす。grep batch 72 → 1、同段 255.6 秒 → 11.2 秒) である。
- **依頼の前提のうち 1 つは、後半で成り立たなくなる。** 「CPU は 10 分経過で 10 秒 (1.5%) しか
  使わず、律速は fork と I/O」は最初の 10 分については正しい。しかし修正前の全走を `/proc` で
  追うと 115 分時点で CPU 87 分に達しており、途中から CPU 律速へ変わる。最初の観測窓だけで
  律速を決めない。
- **並列化は実測で否定した。** repo 外走査を単一 thread 157.98 秒 / 4 thread 141.83 秒 /
  8 thread 132.56 秒 / 16 thread 125.80 秒で測り、改善は 20% どまりだった。依頼の
  「I/O 律速だから並列化は効かない」という前提は、プロセス内スレッドについても正しい。
  段 4 で決めた判定表 (律速が walk や fsck なら並列化しても効かないので実装せず裁定へ返す) に従い、
  commit 単位の並列化も走査の並列化も実装していない。
- **残った律速は探索根の規模そのものである。** 最終走 248.9 秒の内訳は repo 外走査の列挙 181.8 秒
  (73%)、候補比較 45.6 秒、landed 参照 11.1 秒、fsck 5.3 秒、bulk log 3.4 秒。
  探索根 `dev-wave-jobs` は実測 1,299,504 inode で、最大の 1 dir だけで 681,891 を占める。
  これは tool の性質ではなく環境の性質であり、これ以上詰めるなら探索根の縮小 (運用) か
  index 化 (別 wave) になる。裁定パッケージとして残す。
- **段 3 の 2 レンズは 19 件の real を返し、親はすべて採用した。** sol (正しさ) は
  「除外は将来の救出対象を無条件に隠す」を最重要として挙げ、親の provisional 裁定を
  「沈黙でなく開示」へ変えさせた。luna (性能・運用) は「除外で減らない fsck と全 root walk が
  最終予算を支配しうる」を挙げ、これは実測で的中した (走査 73%)。
  親の provisional 裁定 4 件のうち 2 件は維持、1 件は修正、1 件は一部取り下げになった。
- **段 6 は fix を 11 本要した。** レビュー A が fail-closed の欠陥を 3 件 (path block 欠落の
  zero-path 誤認、`close()` の deadlock、fsck の malformed 行の黙殺)、レビュー B が
  性能・契約の must-fix を 8 件返した。加えて実走とプロファイルで 4 件を見つけている。
  そのうち 3 件は台帳へ送った ({{F:progress-interval-doubles-as-poll-timeout}}、
  {{F:review-finding-closed-per-instance-leaves-twin}}、
  {{F:fail-closed-branch-not-measured-against-real-distribution}})。
- **fix が新しい赤を作った回が 3 回ある。** (a) record 区切りを NUL の個数で分ける初版が
  変更パス 0 本の commit で落ち、F119 の control が捕まえた。(b) その修正が「path 列は LF で
  始まる」と厳格化して combined diff の merge を壊した — git は diff 種別で区切りを変える。
  (c) 同一実体の重複除去で hardlink の 2 path が 1 つに畳まれ、抑止の受理集合が縮んだ。
  いずれも「読む回数は減らし、返す path は減らさない」「実 git を回す fixture を持つ」で閉じた。
- **1 回は実装が正しくテストが誤っていた。** 新設された境界テストが `=` を path 境界と仮定して
  いたが、D248 は境界 byte を明示列挙し、それ以外は path を延長する。既存実装と突き合わせて
  実装側が正しいことを確認し、テストを直した。
- **掃除 command の予算が 1 byte まで埋まった。** 3 つの義務を §1 へ足すため既存文面を意味等価に
  縮約して 3,949 → 3,999 bytes (予算 4,000) にしたところ、`test_check_docs.py` の変異テスト 8 件が
  赤になった。変異が byte を足して予算違反を巻き込み、`_violation_count == 1` が破れる。
  変異 fixture が単一理由でない過剰決定であり、予算中立な変異へ直した。
- **`check_worktree_occupancy.py` の 2 行契約を一度壊した。** 縮約の過程で
  `check_docs.py` が exact literal で固定している 2 行に触れてしまい、復元して別箇所で
  埋め合わせた。予算の縮約は逐語 pin の閉包を先に調べる。
- 実測の一次資料は `dev-wave-jobs/dangling-audit-speed/` の `measure-baseline.txt`、
  `measure-r1.txt`、`measure-r2.txt`、`measure-r3.txt`。修正前 tool の写しも同 dir に置いた
  (sha256 `df95e4b9f5780782ce31a495c51079d246bc8e086f0330ed68d611e0df060944`)。
- **変異 matrix は本体 11 件が 11/11 一致で閉じた。** 最終 commit `8ecb9325` に対する本走で
  KILLED 10 件がいずれも期待 node の完全集合と一致し、MISMATCH 0。M05 だけは SURVIVED 期待で、
  `git log --no-walk` の出力が `--root` の有無で byte 同一 (480 bytes) であることを実測して
  等価変異と確定した。probe は全件 SURVIVED 期待で回して観測 node を集め、本走で
  KILLED 期待へ差し替える DW-M07 の手順に従っている。
- **busy-spin の変異 (M12) は本体から分離した。** これは D560 が未閉鎖残件として記録済みの
  構造的非互換で、hang する変異は PBS に強制終了されるため正常完了マーカーを残せず、
  walltime 値に関わらず毎回 orphan-hold に落ちる。D560 は同型の変異を matrix から除外して
  閉じており、本 wave も同じ扱いにした。検出力そのものは実測で確認できている —
  独立 2 走 (948690 / 948747) がいずれも 144 件中ちょうど 1 件を落としており、
  {{F:progress-interval-doubles-as-poll-timeout}} の control が発火する形と整合する。
  ただしその 1 件がどの test node かは、pytest が SIGKILL されて短縮サマリを書けないため
  出力から特定できていない。**この 2 走に約 2 時間を費やしたのは親の手順漏れである**
  ({{F:hang-mutation-orphan-limit-relearned-by-experiment}})。
- **走行中に auto-gc が到達不能 object を刈ることを実測した。** 監査中に pack が書き直され、
  probe が `fatal: bad object` で止まった。到達不能 commit 数は同じ 20 分で 2,782 → 2,780 → 2,781 と
  動く。遅い監査ほど「報告される前に消える」窓が広く、高速化はこの意味でも効く。

## 次の一手差分

### 新規

- {{T:dangling-audit-offrepo-walk-scale}} **P2・新規**: 到達不能 commit 監査の残る律速は
  repo 外探索根の走査 (最終走 181.8 秒、全体の 73%) であり、探索根 `dev-wave-jobs` の
  実測 1,299,504 inode がそのまま所要になる。並列化は実測で否定済み (16 thread で改善 20%)。
  選択肢は (a) 探索根の縮小 = 古い wave 成果物の退避という運用側の変更、(b) 探索根の index 化と
  無効化条件の設計、(c) 現状維持と上限の再裁定。**ユーザー裁定を仰ぐ。**
- {{T:dangling-audit-landed-blob-size-bound}} **P3・新規**: landed 参照が読む main 側 blob に
  size 上限が無い。修正前の `git show` も同じだったので回帰ではないが、main の最大 blob は
  実測 31,401,866 bytes (29.95 MiB) で `MAX_BLOB_SIZE` (32 MiB) に近い。超過を
  reference failure (抑止しない側) にする案がある。
- {{T:dangling-audit-metadata-batch-fork-scale}} **P3・新規**: finding path の metadata 取得は
  commit ごとの argv 上限つき batch なので fork 数が finding 規模に比例する。現行規模では
  51 commit / 616 対で 51 本程度であり実測 300 秒の中で支配項ではないが、規模が伸びれば効く。
  commit 横断の常駐 batch へ寄せる案がある。

- {{T:hang-mutation-settlement-under-dispatch}} **P3・新規**: hang する変異を dispatch 経路で
  清算できるようにする。D560 が未閉鎖残件として記録した構造的非互換
  (PBS 強制終了 job は正常完了マーカーを残せず毎回 orphan-hold) が本 wave で再発し、
  該当変異は 2 wave 続けて matrix から除外されている。案は (a) walltime 超過による
  終了を harness が TIMEOUT の終端証拠として受理する、(b) `hang_risk` の変異だけ
  `IZANAGI_DISPATCH_WALLTIME_OVERRIDE` を自動で短く設定して孤児の占有を最小化する、
  (c) 現状維持として DW-M06 に「dispatch では hang 変異を本走に載せない」と明記する。
  (c) だけでも {{F:hang-mutation-orphan-limit-relearned-by-experiment}} の再発は止まる。

### 見送り追記

- [T-1000] 2026-08-26 に再訪条件が成立し、本 wave が所要を 2:22:57 から独立 3 走の最大 283.27 秒へ短縮して解消した。rc=124 の手順は `timeout` で打ち切らない方針を決定へ明記したため不要になった。
