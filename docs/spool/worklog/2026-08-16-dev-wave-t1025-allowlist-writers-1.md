---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t1025-allowlist-writers
seq: 1
title: read-only allowlist に残る実 writer を閉じ、hooks/ が自分自身の保護で編集不能な構造を D374 の経路で解いた (コード + テスト、変異 8/8 KILLED、branch worktree-dev-wave-t1025-allowlist-writers)
---

## 本文

- **起票時の 6 形はすべて現行 main で素通りすることを親が実測で再確認した。** 親が repo 外に
  置いた判定 runner で 93 ケースの期待表を作り、着手前の基準値は `total=93 pass=47 fail=46`。
  fail 46 件がすべて「保護対象を書けるのに read-only と判定されている」形である。
  台帳の 6 形に加えて同族を実測で追加発見した — awk の `>>` / `printf` / pipe / `system()`、
  sed の `s///w` と `e`、`git log/show --output=` と `--ext-diff` / `--textconv` と pager 経由、
  `sort --temporary-directory=` と `--compress-program`、`xxd IN OUT` (第 2 位置引数)、
  `less -o`、`file -C`、`nm --plugin`、`rg --pre`。
- **台帳外の非対称を 1 件見つけた。** `dd if=… of=hooks/guard_bash.py` は通り、
  `of=<WAL>` は拒否される。dd 分岐だけが呼び出し側と別述語を使っていた。
- **hooks/ は wave 開始時点でどのツールからも編集できなかった。** `apply_patch` / `Write` /
  `Edit` のすべてが拒否される (例外は exact `hooks/README.md`)。[T-956] の自己保護が入って
  以降 hooks/ のコードは一度も変更されておらず、D374 手順 5 を実際に行う必要が生じた。
  経路と却下した代替案は {{D:hooks-edit-route}}。実装子は有効化前 commit を base にした
  第 2 worktree で guard 本体だけを書き、テストは wave worktree 側の別の実装子が書いた。
- **段 3 の敵対レンズ A は 2 回とも出力ゼロで死んだ。** 1 回目は guard 自身が測定手段を拒否し、
  2 回目は上流分類器が「cybersecurity risk」として拒否した (828 秒・model call 16 が全損)。
  防御目的は prompt 冒頭に明記していた。詳細と対策は
  {{F:adversarial-lens-classifier-refusal}}。段 3 は成功したレンズ B 1 本で裁定し、
  レンズ A の観点は段 6 レビューへ中立な適合性検査として畳み込んだ。
- **レンズ B が親 brief の一般化を 1 件倒した。** 親は「repo 内の awk 呼び出しに比較演算は
  存在しない」と書いたが、全件検索で 1 件実在した (保護対象との交差は 0 件)。
  同レンズは親の不採用理由 3 つのうち 1 つ (「D374 の統合手順が保護 path 入り commit を
  必要とする」) も誤りとして倒した — 実際には path-free の統合で足りる。親は訂正を受け入れ、
  残る 2 つの理由で不採用を維持した。
- **段 2 プランの拡張 3 件を親が不採用にした。** (a) `git add` / `git commit` を read 判定から
  外す、(b) `git status` に `--no-optional-locks` を必須化する、(c) `git log/diff/show` の
  未知 option を一律 deny する。いずれも保護対象**そのものの中身**を書き換えない操作であり、
  既存 runbook 3 件とテスト 2 件を壊す。head の丸ごと除去も、現ホストに実体が無く判定不能な
  `ag` / `yq` / `most` の 3 つに絞り、`ldd` / `more` / `zmore` / `rg` / `less` / `zless` /
  `xxd` / `file` / `nm` は head を残して書き込み・任意実行 option だけを deny した。
- **段 6 の敵対レビュー 2 本が独立に NO-GO を出し、実装を 2 巡直した。** 最も重い所見は
  **単調性違反**で、`sed 'p' -i <WAL>` が wave 前 deny から wave 後 allow へ反転していた
  (GNU sed は script positional の後ろでも option を解釈するのに走査が止まっていた)。
  期待表 93 件は全件緑のままだったため、表だけでは検出できない向きの後退である。恒久対応は
  {{D:acceptance-set-reversal-check}}。次に重い所見は**運用破壊**で、
  `git diff --cached --output=/tmp/f -- <所有パス>` (dev-wave の標準必須経路) が拒否されていた。
  option の値と保護対象を対応付けず「どこかに保護対象」「どこかに writer option」を結合して
  いたためである。出力先を持つ option は値が保護対象のときだけ拒否し、任意 command を実行し得る
  option は値に関わらず拒否する形へ分けた。加えて短 option cluster・長 option の最短省略形・
  `--` 以降・awk の字句文脈 (regex と文字列の中の `|` `>` を無視) を直した。
  1 巡目の fix が過去に潰した false positive を 2 件戻した件は
  {{F:predicate-widening-revives-fixed-false-positives}}。
- **ccbench source への writer は scope 外と裁定した。** 両レビューが blocker として挙げたが、
  これは親の実装契約 §3 の誤りだった (実装節は末端層の対象集合を広げると書いていないのに、
  テスト節が ccbench source を deny 直積へ入れていた)。親の実測では、wave 前の main でも
  ccbench tree と campaign dir の**非末端 path** は `echo x > …` を含むあらゆる writer が
  通る領域であり、`sed -n 'w'` だけが特別に抜けているのではない。閉じるには末端層が守る
  対象集合そのものを広げる必要があり、build 経路と干渉しうるため別課題とした。
  現状の境界は allow 回帰テストで明示した。
- **段 8 で dev-wave 本文への統合を試みて止めた。** 反転検査の義務を `DW-M01` の既存節へ
  1 文で統合しようとしたが、`check_docs` の L1 unique footprint が 10719 bytes で予算
  10625 bytes を 94 bytes 超えた (実測)。予算引き上げは行わない方針であり、同 byte 数を
  意味等価に空ける余地も過去 2 wave の棚卸しで否定されているため、自己改善契約の
  「予算に収まらなければ変更を止めてユーザー裁定へ返す」に従い本文編集を撤回した。
  義務は {{D:acceptance-set-reversal-check}} に残る。dev-wave 本文への反映はユーザー裁定を待つ。
- **検証。** 期待表は最終的に 135 件 (基本 93 + レビュー由来の追加 42) で全件一致。
  wave 前実装との反転検査は 131 コマンドで `WIDENED=0`。
  `orchestrator/tests/test_hooks.py` は 452 passed / 1 skipped / 0 failed。
  変異は 8 件登録して **8/8 KILLED・MISMATCH 0**、期待 node は解析導出した完全集合が
  全変異で一致した。8 件のうち 7 件は各分岐を wave 前の実コードへ戻す negative、
  1 件は xxd を常に拒否させて過剰拒否を検出する positive control である。

## 次の一手差分

### 完了

- [T-1025] read-only allowlist に残る実 writer を閉じた。台帳の 6 形と実測で見つけた同族、
  および dd の非対称を、末端層が保護する全対象 (WAL / campaign.lock / build-variants /
  namespace marker / exploration の末端 / hooks subtree) で拒否する。対応する純読み形と、
  出力先が保護対象でない writer 形 (dev-wave の標準 patch 作成を含む) は維持し、実在する
  read 呼び出しを回帰で固定した。flag / env の逃がし道は置いていない。
  remaining: none
  base: a49bca09afee339295018c8e88156f42e764d37a80da11e2b9041416af404772

### 新規

- {{T:leaf-layer-target-set}} **P3・新規**: 末端層が保護する対象集合に、ccbench tree と
  campaign dir の**非末端 path** を含めるかを裁定する。現状これらは `echo x > <path>` を
  含むあらゆる writer が通る (実測)。含めると variant identity の素材である ccbench source を
  Bash から直接書き換える経路が閉じるが、`cmake` の build-variants 生成や patch 適用と
  干渉しうるため、影響範囲の実測が先に要る。起票資料 = 本エントリと `hooks/README.md`
  「既知の限界」の該当項。
