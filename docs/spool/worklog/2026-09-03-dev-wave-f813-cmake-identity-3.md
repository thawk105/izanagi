---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-03
wave: dev-wave-f813-cmake-identity
seq: 3
title: F813 の恒久対応を実装した — 束縛は記録であって拒否ではないと正本へ固定し、安全にする変更が検査対象集合を縮める型を新しく見つけた (コード + テスト + docs、branch worktree-dev-wave-f813-cmake-identity)
---

## 本文

- ユーザーが F813 の「未実装」と明記された恒久対応の実装を直接指示した。scope は本題の実装だけで、
  仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外、既存の受理集合を狭める方向だけ、と
  裁定済みで開始した。
- **起動時に稼働 wave との編集面重複を再実測してゼロを確認した。** 全 branch tip の三点 diff と
  全 worktree の未 commit 差分の双方を対象 2 file の pathspec で走査し、hit 0 件・走査失敗 0 件。
- **段 3 のレンズ A が本 wave で最も重い所見を返し、親が採用した。** 「identity を記録することと、
  未承認の実体を拒否することは別である」。安定した wrapper は変更後も green を返す。
  拒否には承認済み CMake identity の権威が要るが repo に存在しない (`admission_registry.json` に
  64hex pin ゼロ、`FROZEN_MANIFEST` に該当なしを実測)。**実装せず裁定パッケージへ送り、
  この wave が「F813 の穴を塞いだ」と書かないよう、主張してよいことを 4 項目へ限定して裁定文に固定した。**
  正本は {{D:cmake-identity-bound-to-green-record}}。
- **親の実測がレンズ A の別の所見を一部反証した。** `strip --strip-all` と `--strip-unneeded` は
  symbol 表を空にし (rc=0・stdout 0 行)、新しい empty check が閉じる。`--strip-debug` は
  trace symbol を残すので既存 grep が捕まえる。`objcopy --strip-symbol=` の狙い撃ちだけが
  symbol 表非空のまま残り、`main` も残るため **anchor symbol 検査を足しても捕まらない**。
  恒真な検査を入れないと決め、残る経路を限界として明記した。
- **段 6 のレンズ B が、他のレビューも親も見ていなかった 4 つ目の機構を見つけた。**
  実体を絶対 path 変数へ固定した結果、build sink 走査がその file を静かに見失った。
  消費側の検査は赤にならず縮んだ集合に対して通る。新しい失敗型として
  {{F:sink-scanner-loses-target-on-path-variable}} に記録した。
- **段 6 のレビュー 2 本が返した must-fix 3 件は、いずれも実装の欠陥ではなく親の変異事前登録の
  帰属不成立だった。** M1 は `required` から field を消しても `KeyError` になるだけで
  「旧形式を受理する」変異にならない。M3 は 3 層に mask されている。M2 / M4 は production 層と
  validator 層のどちらを指すか二義的だった。初回登録を erratum として残し、受理権威である
  record validator へ再照準した。層の扱いの正本は {{D:record-validator-is-the-acceptance-authority}}。
- **親が必須にした「過剰拒否の正例」が初回焦点走で赤になり、実測で原因を確定した。**
  `reason_code` は `preprocess-output-empty`。compile-time branch 用の合成 root は owner TU が
  条件分岐だけなので default 側の preprocess 出力が空になる。**CMake 検査による過剰拒否ではなかった。**
  fix 子は `condition_meaning_gate.py` を 1 行も触らず、正例を既存の supply-green fixture の上へ建て直した。
- **変異は 3 attempt かかり、経緯を全て残した。** probe で N3 が SURVIVED し
  (record validator の arm 内 drift 検査を殺すテストが 1 本も無かった)、実際の検査漏れとして
  fix 2 で塞いだ。同じ probe で N10 が PARSE_ERROR になったが、これは親が書いた spec の span が
  閉じ括弧を 1 行落としていたためで、コードの欠陥ではない。spec 生成器へ括弧の均衡検査を足した
  (放置すると全件が偽の KILLED になる型)。attempt 2 は N1 / N9 が MISMATCH になったが、
  観測 node が期待より 1 本多いだけで欠落はゼロ、その 1 本は fix 2 が probe の後に足した負例だった。
  2 件の集合を訂正し、他の 8 件を変えずに attempt 3 で完全一致を確認した。
  最終は **10 / 10 KILLED、期待 node 完全一致**。詳細は
  `output/insights/2026-09-03_f813-cmake-identity-binding/README.md`。
- **N6 と N7 を別々のテストが殺した。** strip 前 (symbol 表非空・trace symbol あり) と
  strip 後 (symbol 表が空) の 2 段負例が、grep 削除と empty-check 削除を分離して殺す。
  段 6 レビュー B の must-fix がこれを要求していた。
- 実装子は 2 単位とも、fix 子も、テストを 1 件も実走できなかった。子の sandbox から
  `qstat -Q` が `EACCTAUTH Unknown user-id` で弾かれ計算ノードへ dispatch できない。
  実走は全て親が行った。子の未実走を緑と数えていない。
- 計算ノードの混雑で `queue-wait-timeout` (child 未起動、rc=16) を 2 回踏んだ。D612 の
  opt-in 上書き (queue-wait 3600 / overall-grace 600) で通した。
- 子の工数: 段 2 プラン 1 本、段 3 レンズ 2 本、段 5 実装子 2 本、段 6 レビュー 2 本、fix 子 1 本。
  全て `accepted`。単位 B 実装子は 36 model call / 685 秒。

## 次の一手差分

### 新規

- {{T:approved-cmake-identity-authority}} **P2・新規・ユーザー裁定待ち**: 承認済み CMake identity の
  権威を作り、未承認の CMake を拒否するか。これが F813 の穴を実際に閉じる唯一の道だが、
  登録簿・更新手順・機体差の扱いの新設が要る。判断は
  {{D:cmake-identity-bound-to-green-record}} の「却下した選択肢」を読んでから行う。
- {{T:nm-identity-bound-to-receipt}} **P3・新規**: calibration の `nm` の内容 hash を receipt へ
  束縛するか。本 wave は絶対 path 固定と `nm.path` / `nm.version` の記録までで止めた。
  新しい台帳項目になるため scope 外とした。
- {{T:compile-commands-post-capture-toctou}} **P3・新規**: CMake identity の after capture 後に
  `compile_commands.json` を差し替える経路と、capture 間の swap-and-restore は検出していない。
  検出に見合う機構があるかを設計メモとして評価する。
- {{T:targeted-symbol-removal-detection}} **P3・新規**: `objcopy --strip-symbol=` による狙い撃ちの
  symbol 除去は名前ベースの検査では原理的に捕まらない (親が実測)。期待 symbol 数の下限や
  section 単位の検査など、別の手段が要るかを評価する。
