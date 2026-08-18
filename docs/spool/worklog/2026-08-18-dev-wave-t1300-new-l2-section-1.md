---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-18
wave: dev-wave-t1300-new-l2-section
seq: 1
title: 予算で差し戻され続けた実測是正 10 件を新規 L2 節 DW-C01 へ収容した — 空き番は削除済み ID しか無く、core.md 側の未使用 ID と条件 26 で通した (docs + コード + テスト、branch worktree-dev-wave-t1300-new-l2-section)
---

## 本文

- **「新規 L2 節を 1 つ」はほぼ不可能に見えたが、番号の選び方だけで通った。** operations.md の
  空き操作番号は `DW-O07` と `DW-O15` の 2 つだけで、どちらも削除済み ID であり
  復活には新規裁定が要る (`tools/check_docs.py` の `_OPERATION_NUMBERS` 付近の注記が正本)。真に未使用の `DW-O26` は
  段 5・6 の `|C|` 行へ singleton で入るため +20 bytes かかり、追加圧縮 96 bytes を
  全部使っても命令入口が 58 bytes 超過する (実測 9558 / 9500)。
  **`docs/dev-wave/core.md` へ未使用 ID `DW-C01` を置き、条件 21/22/24 が core を指す
  既存パターンに倣って条件 26 を明示登録する形**だけが上限内に収まった (最終 9492 / 9500)。
- **段 2 プランの「機械強制済みだから落とす」判定を段 3 が反証した。** プランは D271 の
  鏡像 3 条件を根拠に (a) `--lane` と (e) 変異 baseline 緑と (j) Web 検索禁止を落とす案を出したが、
  レーン B が「ユーザーの明示裁定は D271 に優先する」「[T-1348] と [T-1320] の裁定文自身が
  機械強制の存在を書いた上で収容を裁定している」と反証した。(j) は
  `tools/codex_worker_launch.py` の argv に Web 無効化 flag が実在せず移送先が無いことも実測した。
  **命令が名指しした 10 項を収容した** (節 991 / 1000 bytes)。詳細は {{D:dw-c01-admission}}。
- **[T-1313] の「`DW-O20` からポインタを残す」裁定と、親 brief が置いた「既存節を 1 byte も
  変えない」不変条件が衝突した。** 裁定文自身が「必ず失敗する命令を残すのは無い方がまし」と
  述べているため、誤った `git submodule update --init` を `DW-C01` ポインタへ置換する形を採った
  (996 → 984 bytes)。`DW-O20` 以外の既存節 slice は 1 byte も動いていない (実測)。
- **条件 13 (`DW-O13`) の最遅読了段を踏み外し、自分で巻き戻した。** 本 wave は checker の
  受理形を増やす = 検証の新設に当たり、条件 13 の最遅読了段は段 2 プラン前だった。段 4 で成立に
  気づき、入口の巻き戻し規則に従って round 1 の段 2・3 成果物 (プラン 1 本 + 敵対 2 本) を
  invalidate し、段 2 から再実行した。旧成果物は入力に使っていない。工数はプラン 21 分 +
  敵対 2 本 18 分ぶんを捨てた。
- **変異は runner scope の穴を露わにした。** 事前登録 8 件のうち m1〜m4
  (条件行削除・trigger 改変・参照先すげ替え・本文空化) は runner scope
  (`test_check_docs.py`) では SURVIVED だった。`test_real_repo_clean` が変異 container で
  実行されないためで、skipif は無い。`DW-M02` に従い実効 gate へ再照準し、統合 commit 後の
  一時変異 + `check_docs.py` 直呼びで 4 件とも rc=1 (違反 2 / 1 / 2 / 1 件) を実測した。
  初回結果は erratum として残し、実測 node で m5〜m8 を再登録して再走した。
- **背景 Bash と待ち手が約 10 分で空返りする環境だった。** `tools/dev_wave_wait.py producer` が
  出力 0 bytes・rc=0 で早期に返る事象を 3 回観測し、いずれも producer は生存していた。
  pid file 実在を確認してから張っており ([T-1348] の是正どおり) それでも起きた。
  以降は `.done` と pid で判定し、テスト実行も codex 子と同じく `.sh` へ外出しして detach した。
  この作法は F355 の再発として記録した (F355 で未特定だった根本原因を本 wave で特定した)。

## 次の一手差分

### 完了

- [T-1139] worktree の submodule 初期化の再帰化と transport 設定を `DW-C01` へ収容した。
  remaining: none
  base: a159a821379e3edbf4e986f23b65d7244d8b968e416748df531a128698a27da6
- [T-1144] 取り込みの合成監査を `DW-C01` へ収容し、条件 26 で dispatch した。
  remaining: none
  base: 74b0eb6833d0dc0ec60768787bdbe3979b57c81bb3e3334c0172b7483d90dadc
- [T-1159] 段 6 fix 契約の受理・拒否条件の書き方を `DW-C01` へ収容した。
  remaining: none
  base: c8420e6f3ebedc87e5dfa9aec8b13304b334391504d1f8083f2eed5b457250c7
- [T-1260] `--lane` が consult 段専用である旨を `DW-C01` へ収容した。
  remaining: none
  base: 8faa5326016ae50a76179eaddc70a566bab68001901f93039d21584d58d203b3
- [T-1265] 親が merge・子は競合解決だけという分担を `DW-C01` へ収容した。
  remaining: none
  base: af3768c7f7becf797ceffc27a6327ec229192dcf5a05f4889728bbab9f2bae6a
- [T-1300] L2 単節予算が是正を拒む件を、上限を上げず新規 L2 節で閉じた。
  remaining: none
  base: deb627e299a3e9807cffcc85d882cdf4749b082c5c2c1543650957096159fa9a
- [T-1313] `DW-O20` の誤った submodule 命令を `DW-C01` ポインタへ置換した。
  remaining: none
  base: 425951c948932b77e603eebffe8cab8e023dc37828555b7d95a8239cfc63d4f7
- [T-1320] 変異 harness の baseline 緑要求と `--deselect` の根拠記録を収容した。
  remaining: none
  base: 5bdc9ba8ec7302fb6691c19d3937bb7103fd97ff1f7a310db0a4f6d964e239bc
- [T-1335] 隔離 worktree の detach を `.sh` へ外出しする作法を収容した。
  remaining: none
  base: 49b20d23671eed78051bccc186f932dc29ebca247efb8979cb9b5a71d80068b8
- [T-1342] 複数起点の判別テストへの正値注入規則を収容した。
  remaining: none
  base: 0d93595e31423c68a60680b81b3166f516951cae81124f99bd8442e0aacbc750
- [T-1346] `--lane` の是正先を `DW-C01` に定めて収容した。
  remaining: none
  base: d3580944bbad2e8b1f70df9cabc56dc7f5d2cefe7428cf13cddc5743f5b2d412
- [T-1348] 待ち手の pid file 実在確認と `--lane` の 2 件を `DW-C01` へ収容した。
  remaining: none
  base: 5cb9e3bb3738de5996b1dc78f2922476724af8b4d761f4f240c8717e7e6e8b42

### 更新

- [T-1245] **P2・未収容**: 本項の実体は予算で入らなかった是正 **3 件**
  ((a) `DW-O09` の pin 閉包から成果物側を除外しない、(b) `DW-S01` へ不在主張の探索範囲を書く、
  (c) `DW-S05-C` へ実走経路が子の環境で塞がっているなら親が測ると prompt に書く) であり、
  **1 件も収容していない**。親は本項を「[T-1260] / [T-1265] / [T-1273] の束ね項」と誤読した。
  `DW-C01` は 991 / 1000 bytes で残り 9 bytes、上限を上げない指示のため 3 件とも入らない。
  収容先の再裁定が要る。段 6 の敵対レビューが検出した。
  base: 762d4d6dcf4c45ed2158d2f43247977509d55780fc77b7e5115e9dd9ddbd05ab
- [T-1273] **P2・部分収容**: 子への Web 検索禁止は `DW-C01` へ 1 行で収容したが、
  裁定が主とした機械移送は**未実施**である。`tools/codex_worker_launch.py` の argv に
  Web 無効化 flag が実在しないことを実測した。flag と負例テストの新設が残件。
  base: 094d841f2eb7fe06c7ffd9064a300e390b647dbc3b88478d74a45f9e9f4d5cc8

### 新規

- {{T:startup-diagnostics-lack-recursive}} **P2・新規 (本 wave の明示残余)**:
  `tools/check_wave_startup.py` と `tools/run_tests.py` の診断文は今も
  `git submodule update --init` を `--recursive` 無しで案内し、その逐語が
  `orchestrator/tests/test_check_wave_startup.py` と
  `orchestrator/tests/test_run_tests_preflight.py` でそれぞれ pin されている。`DW-C01` は docs 側を
  是正したが、この executable consumer には届かない。**submodule 手順は全面修正されていない。**
- {{T:dev-wave-condition-triggers-near-tautological}} **P3・新規**:
  条件 26 を含む既存条件の多くが実質恒真 (条件 01・02・20 はほぼ毎 wave 発火する) で、
  L1 / L1.5 の層予算が「読了量の上限」として機能しているかを再点検する余地がある。
  段 3 のレーン A が指摘した。
- {{T:dw-c01-lacks-positive-examples}} **P3・新規**:
  `DW-C01` の 10 規則は予算 (残り 9 bytes) のため通る正例を添えられていない。
  `DW-S04` は gate の禁止に正例 1 つを求める。優先順は e > g > c / i / b (段 3 レーン B の順位付け)。
- {{T:mutation-runner-scope-misses-real-repo-clean}} **P2・新規**:
  変異 container で `test_real_repo_clean` が実行されない。skipif は無い。実 repo を読む
  検査を変異で守れないため、docs の受理集合を変える変異が runner scope 内では静かに生き残る。
