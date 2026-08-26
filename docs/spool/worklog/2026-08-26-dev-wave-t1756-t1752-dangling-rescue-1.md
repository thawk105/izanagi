---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-26
wave: dev-wave-t1756-t1752-dangling-rescue
seq: 1
title: [T-1756] [T-1752] 到達不能 commit 20 件を親子関係ごと救出し、隔離復元まで実測した (docs、branch worktree-dev-wave-t1756-t1752-dangling-rescue)
---

## 本文

- **救出物は `/work/1/SFC/tanab/dangling-rescue-20260826/`。** canonical は
  `dangling-rescue-20260826.bundle` (135,247,714 bytes、sha256
  `957748e18b152b7d65a9098c606eb85c00bb04d71c49da961d7c80ee5a93e7ee`)。20 head を持つ
  自己完結 bundle で、prerequisite ゼロ。復元手順と件数の正本は同 dir の `MANIFEST.md`。
  検索語は「到達不能 commit / 救出 / 復元 / dangling / unreachable commit / git bundle /
  dangling-rescue-20260826 / cleanup-20260825」。
- **head は 20 件。** [T-1756] の `indeterminate` 3 件 (`15b5c389` / `fe56f5f7` / `500f47a6`) と、
  [T-1752] の外部控え皆無 17 件。`landed` の 4 件と [T-1752] の対象外 11 件は head にしていない。
  merge の必要祖先 `dec2faa2` / `166b0f9c` は head ではなく bundle 内の祖先として保存した。
- **[T-1756] の 3 件は記録でなく判定器の実走で確定した。** `tools/check_branch_landed.py` を
  7 件全部へ回し、landed 4 / indeterminate 3 を得た。件数は worklog 961 の記録と一致する。
- **「3 件を親子関係ごと」は 3 件だけでは足りない。** `git rev-list <3 tips> --not --all` は 5 件を返し、
  `500f47a6` の未到達祖先に merge 2 件が入る。ただしこの 5 は「計測時点の未到達差分」であって
  自己完結 bundle の閉包ではない。bundle が含む commit は 5,844、object は 57,224 である。
  この 4 つの数を混ぜないことを manifest の表で分けた。
- **[T-1752] の救出物は 2026-08-25 に既に作られていた。** `cleanup-20260825/dangling-28.bundle` に
  28 件が入っており、裁定が要求する「別の場所で復元できることの確認」だけが欠けていた。
  本 wave でその確認を通したうえで、head を裁定対象へ絞った新 bundle を発行した。
  既存 bundle は原本として残す (対象外 11 件はそこにしか無い)。
- **段 3 の最重要 blocker は「17 件が独立に同定されていない」だった。real と裁定し、実測で解いた。**
  既存 bundle と `dangling-28-shas.txt` は互いに整合するだけで、28 件一覧そのものが誤りなら
  全検査が緑のまま対象を失う。そこで bundle とも SHA file とも独立な一次記録として
  2026-08-25 の監査全出力 (21,130 行) を使い、commit ごと・path ごとの外部控え注記から
  分類を再構成した。**全 path 外部 = 6、一部だけ外部 = 5、外部控え皆無 = 17** で、裁定文の
  6 と 17 に完全一致した。subject から機械生成・一時を数えると 11 でこれも一致する。
  17 件は 28 件の真部分集合であることを `comm` で確認した。
- **監査を独立に回し直して裏を取った。** `tools/audit_dangling_commits.py --offrepo-root
  /work/1/SFC/tanab/dev-wave-jobs` を本 wave で再走すると rc=1 / 要確認 47 commit を返し、
  2026-08-25 の 28 件は **28/28 が今も要確認**、救出対象 17 件も **17/17 が要確認**だった。
  刈られた件はゼロで、対象集合が本 wave 開始時点でも生きていることを確認した。所要は 539 秒で、
  worklog 980 が記録した独立 3 走の最大 283 秒より長い。login node の混み具合が違い、
  `--repo` も別 checkout を渡しているため、同一条件の比較ではない。
- **要確認 47 件のうち 19 件は、どちらの裁定にも入っていない新しい到達不能 commit である。**
  2026-08-25 以降に増えた分で、本 wave の救出対象ではない。裁定が要る。
- **[T-1756] の 3 件は監査の 47 件に入っていない。** `audit_dangling_commits.py` は
  「既存ファイルへの変更・削除・同名別内容・gitlink 更新」を検出対象外と明記しており、
  branch 削除で取り残された commit はこの穴に落ちる。判定器を分けて使う必要がある。
- **裁定文の「11 件と 6 件は対象外」は排他的な内訳ではない。** 11 は 3 区分を横断する別軸のラベルで、
  6 + 17 + 5 = 28 が実際の分割である。救出対象は「外部控え皆無の 17 件」と読む。
- **git 2.34.1 は生 SHA から bundle を作れない。** ref を持たない隔離 repo で実測すると、位置引数も
  `--stdin` も `Refusing to create empty bundle`、`<sha>:<ref>` も失敗する。bundle には ref が要る。
  そこで **source repo の ref DB へは一切書かず**、alternates で source の object store を読む
  staging repo にだけ temp ref を作った。source の `for-each-ref` は変化していない。
- **最終 bundle の生成時点では source を参照していない。** 既存 28 bundle と T-1756 の seed bundle を
  alternates 無しの union staging へ unbundle し、そこから作った。alternates 依存は seed 作成の
  一瞬だけに局所化した。
- **検証は 3 段で行った。** (a) 復元先の隔離条件 (alternates / http-alternates / commondir /
  grafts / shallow / symlink / partial clone / promisor の不在、object 0、ref 0、`env -i`)、
  (b) `fsck --full --strict` と OID+type+size の inventory の完全一致、
  (c) head の `%H|%T|%P|%s` が生成側・復元側・**source 側**の 3 者一致。(c) は bundle と SHA 一覧だけで
  閉じる循環を断つために入れた。`--connectivity-only` は blob 内容を見ないので合格根拠から外した。
- **manifest の復元手順を逐語で 1 回通した。** 20 ref を復元し、`fsck` 緑、救出 commit から
  `docs/roadmap.md` 476 行を実際に読み出せた。`unbundle` は ref を作らないため、手順に
  `update-ref` まで含めないと使えない。
- **保管の failure domain は 1 個である。** `/work` と `/home` は同じ lustre であり、
  両方に置いても独立した控えにならない。**冗長保管済みとは書けない。** 別 cluster か
  管理された backup 基盤の secondary は未確定で、裁定へ返す。
- **破棄に能動的操作は要らなかった。** 対象は既に到達不能であり、放置が破棄である。
  手動 gc・`git prune`・`git repack`・branch 削除・source への ref 作成は一切していない。
- **段 2 の plan 子を 1 本捨てた。** 最初の子が Web 検索を始めたため停止した。
  dev-wave の子は Web 検索を使うと成果物が全損する。親 prompt に禁止を書いていなかったのが原因で、
  禁止と親の実測記録を渡して投げ直した。この義務は入口にも reference にも無く、
  prompt 生成側の機械強制も無い。
- 実装差分ゼロの docs-only wave のため段 5・6 の子は立てず、変異 matrix は免除した。
  救出物の生成と検証は repo 外の一回限りの運用操作で、repo の受理集合を変えない。

## 次の一手差分

### 完了

- [T-1756] 2026-08-25 深夜の branch 削除で到達不能になった 7 commit のうち `indeterminate` の 3 件を、
  親子関係ごと `/work/1/SFC/tanab/dangling-rescue-20260826/` の自己完結 bundle へ救出し、
  object を共有しない隔離 repo で復元できることを実測した。`landed` の 4 件は救出していない。
  remaining: none
  base: b4487b7341356a518a2027f5715c14ff0a0b83be33dbfeeaa0c083f5d4958c2a
- [T-1752] 到達不能 28 commit のうち外部控えが皆無の 17 件を、監査全出力からの再構成で同定し、
  親子関係を含む自己完結 bundle へまとめて取り出して隔離復元まで実測した。既存
  `cleanup-20260825/dangling-28.bundle` は原本として残した。破棄は放置で足りる。
  remaining: none
  base: f0afe808451e76fd85700120029e3c1a49da91d0551dcf744d8d841764bacb25

### 新規

- {{T:rescue-secondary-failure-domain}} **P1・ユーザー裁定待ち**: 到達不能 commit の救出物の
  secondary 保管先を決める。現在 `/work/1/SFC/tanab/dangling-rescue-20260826/` と
  `cleanup-20260825/` はどちらも同じ lustre 上にあり、failure domain は 1 個である。
  別 cluster か管理された backup 基盤の指定が要る。AI が場所を勝手に選べない。
- {{T:offrepo-artifact-index}} **P2・新規**: repo 外に置いた救出物・退避物の恒久索引。
  現在は worklog 本文だけが手掛かりで、半年後の第三者が directory 名を知らないと到達できない。
  論理 ID・検索別名・現在地・checksum・retention・移動履歴を持つ最小の索引を検討する。
- {{T:branch-delete-rescue-gate}} **P1・新規**: branch 削除前の rescue gate。削除前に tip と
  到達不能閉包を列挙し、`indeterminate` を裁定または救出なしでは削除させない。
  [T-1756] の事故そのものの再発防止で、現在は削除後に人が気づく構造しかない。
- {{T:dangling-expiry-ledger}} **P2・新規**: 到達不能 object の期限付き台帳と通知。
  ref 消失を記録し、自動 gc の窓が閉じる前に未裁定の対象を知らせる。
  今回は窓が開いているうちに間に合ったが、それは偶然である。
- {{T:rescue-base-plus-thin-bundle}} **P3・新規**: 共通 base bundle と薄い rescue bundle の
  保管・復元方針。現行は救出のたびに main 履歴を丸ごと複製し、1 件あたり 100 MB を超える。
  base を固定して薄い bundle を積む構成の得失を、復元順序と prerequisite の危険まで含めて評価する。
- {{T:dangling-47-remainder}} **P1・ユーザー裁定待ち**: 本 wave で再走した監査が返した要確認
  47 commit のうち、2026-08-25 の 28 件に入っていない **19 件**の救出/破棄を裁定する。
  [T-1752] と [T-1756] のどちらの裁定にも含まれず、自動 gc の窓の中にある。
  内訳 (機械生成・一時 / 外部控えあり / 外部控え皆無) は未分類で、
  `reconstruct-classification.py` と同じ手で監査出力から出せる。
- {{T:codex-child-web-search-ban}} **P2・新規**: dev-wave の子 prompt へ Web 検索禁止を
  必ず入れる義務の機械化。本 wave で子が Web 検索を始めて成果物を捨てた。
  現在は `DW-C01` の 1 行だけが防壁で、prompt 生成側の検査が無い。
