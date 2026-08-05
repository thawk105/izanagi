---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t520-measurement-turn
seq: 2
title: 資源分類の実測をユーザー端末の手番として明文化した — 計算ノード対応の改訂は不採用と本文に固定し、bounded surface の比較は族再設計へ残す (docs のみ、branch worktree-dev-wave-t520-measurement-turn、実装差分なしのため変異 matrix は対象外)
---

## 本文

- **ユーザー裁定 (2026-08-05 /rulings、発話「推奨通りで」) の (a) を実装した。**
  一次控えは `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md`
  §24。裁定は (a) 即時明文化 + (b) 比較を族再設計へ同梱 + (c) 不採用の 3 点で、本 wave は (a) と
  (c) の記録だけを行い、(b) の設計には手を付けていない。設計判断は {{D:pegasus-measurement-turn}}。
- **(c) を「採らない」と本文へ書き残す方を選んだ。** 裁定の不採用は台帳にしか残らないと、
  §7.0 だけを読んだ将来のセッションが「計算ノードで測れるようにすればよい」と再提案する。
  前提が実測で否定されている旨を §7.0 側に置き、再提案には新しい実測を要求する形にした。
- **scope 判断 (段 1 の (P1))**: §7.0 の `legacy-admitted` 段落は末尾が「実測へ移すか許可を撤回
  するかは裁定待ちである」で終わっており、[T-522] の裁定 (grandfather 追認) 後は事実として古い。
  本 wave の明文化と同じ段落なので、事実だけを是正した。**registry を machine-readable 正本へ移す
  作業自体は [T-522] の実装 wave が所有する** — §7.0 の「admission registry が正本」という記述は
  現状 (`hooks/guard_bash.py` 内) のまま残してある。
- **敵対レビューを受けて scope を 1 件広げた。** `tools/README.md` の「分類 registry も、実行直前に
  未分類を拒否する gate も存在しない」は [T-481] 以後の事実と食い違う。親は当初これを [T-522] 所有の
  scope 外所見として置いたが、レビューが must-fix と判定した — 同じファイルの 2 行上を編集しながら
  隣の虚偽を残す形になるためである。同 wave 内で是正した。**registry を machine-readable 正本へ
  移す作業自体は [T-522] のまま**で、§7.0 の「admission registry が正本」という記述も現状
  (`hooks/guard_bash.py` 内) のまま残してある。
- **予算の扱い**: `tools/README.md` は 3000 bytes 予算で、追記だけでは 79 bytes 超過した。
  安全義務 (分類前に走らせない / `unknown` は fail-closed / sanctioned 経路が無ければ止める /
  変更時は再分類 / 読まない実行面は止まらない) は削らず、理由節の言い回しだけを縮約して
  2961 bytes に収めた。予算引き上げは提案していない。
- **敵対レビュー 3 巡はいずれも NO-GO で、2・3 巡目の must-fix には前巡の fix が生んだ欠陥が
  含まれた。** 1 巡目 = 3 must-fix (registry 不存在の虚偽 / supersede 不記載 / 実行面の再列挙)。
  2 巡目 = 3 must-fix で、うち 1 件は親の 1 巡目 fix が作った過大限定 (「機械強制は
  `tools/pegasus/` 配下だけ」— テストと provenance 監査の login 拒否を不存在扱いする)、1 件は
  decisions fragment 側の依頼項目不足、1 件は本 fragment 自身が「`tools/README.md` には触って
  いない」と虚偽を書いていたことである。3 巡目 = 2 must-fix で、両方とも 2 巡目の fix が残した
  もの — 限定の掛け方がまだ狭すぎたことと、本 fragment が未実施の commit 後検査を完了事実として
  書いていたことである。**`DW-O16` の 3 巡上限に達したため、この 2 件は親が real と裁定して
  是正し、4 巡目は回していない** (docs-only につき変異での裏取り対象は無い)。
  **docs-only の wave でも親の単独編集は信用に足りない**という具体例として記録する。
- **部分不採用 1 件 (real だが採らず)**: レビューは worklog の「迂回 4 系統 (cwd 非追跡 /
  `env -S` / 3 段ネスト打ち切り / `systemd-run`)」も抜け道目録として抽象化せよと求めたが、これは
  既存台帳 item の本文であり、削ると台帳から閉鎖対象の同一性が失われる。規範本文
  (runbook) 側だけを抽象化し、台帳側は保持した。2 巡目のレビューもこの境界を妥当と判定した。
- **受入の射程**: docs のみで実装差分が無いため変異 matrix は対象外。受入全走は計算ノードへ
  dispatch して **6453 passed / 20 skipped (rc=0)**。fix のたびに 3 回走らせ、3 回とも同数である。
  最終走の後に変わったのは docs の散文だけで、その面の機械検査は `tools/check_docs.py` と
  `spool_fold.py --dry-run` が担う — commit 直前に両者の緑を実測した。
- 段 2・3 は DW-C00 の軽量版として省略した (docs-only につき実装子なし)。段 1 で受理集合・
  正しさ防壁・設計択一のいずれにも触れないことを確認した上での省略である。
- **段 8 候補 2 件のうち 1 件は起票しなかった。** 「新規 worktree の submodule 未初期化で
  `check_wave_startup.py` が必ず赤になるのに `DW-O20` が触れていない」は本 wave でも実測したが、
  land 直前に取り込んだ local main で、並行 wave が同じ事実を [T-432] の 4 件目として既に
  記録していた。独立再観測の価値より重複起票の害が大きいので、[T-432] へ寄せた。

## 次の一手差分

### 更新

- [T-520] **P2・(a)(c) 実装済み → 残余は (b) のみ**: 資源分類の実測がユーザー端末の手番である
  ことを `docs/pegasus-runbook.md` §7.0 と `tools/README.md` 命令 1 に明文化し、(c) 計算ノードで
  動く測定手順への §7.0 改訂は不採用として本文に固定した ({{D:pegasus-measurement-turn}})。
  **残余は (b) 測定専用 bounded surface の比較**で、admission registry の族再設計
  ([T-518] / [T-522] と同じ単位) に同梱して決める。正規の測定面が hook の管轄外に確定した結果、
  hook 面で `systemd-run` 経由を塞いでも測定経路は失われないことが確定し、[T-518] (d) の
  測定経路への従属は解消した
  base: f5fedf93133ccb4d34905329dab40d50833894562f2ae2821dfc6891491161fe
- [T-518] **P2・裁定済み ([T-520] 従属が解消) → [T-481] 族再設計の入力へ**: 迂回 4 系統
  (cwd 非追跡 / `env -S` / 3 段ネスト打ち切り / `systemd-run`) はすべて [T-481] の
  allowlist / denylist 再設計の入力に含めて閉じ方を決める。(d) `systemd-run` は [T-520] が
  測定面をユーザー端末に確定したため、hook 面で塞いでも正規の測定経路は失われない — 族再設計では
  「塞ぐか否か」だけを決めればよく、測定経路の裁定を待つ必要はない
  base: 1bd2b913aef2674166cea7798e4509a7cbeed578018ac99439f7bc3355747dd5

### 新規

- {{T:dev-wave-docs-only-contract}} **P3・新規 (ユーザー裁定待ち)**: docs-only wave の契約が
  2 点欠けている。(a) 入口の段 4 は「実装しないと裁定した場合」だけ段 5・6 を飛ばすと書き、
  `DW-M01` は無条件に変異の事前登録を求めるため、**docs を実際に編集する wave** の変異・受入
  射程がどこにも書かれておらず、親が worklog の前例から推定している。(b) `DW-C00` は
  「docs-only は子ゼロでよい」と書くが、本 wave では敵対レビュー子 1 本が 3 巡連続で real な
  must-fix (虚偽の事実記述・未実施検査の完了記録) を出し、うち 3 件は親自身の fix が作った
  欠陥だった。(b) は段構成と軽量版の境界に触るため実装せず裁定へ返す。(a) は
  `docs/dev-wave/mutation.md` の既存節へ 1 文で入るが、`docs/dev-wave/**` の byte 予算があり
  [T-521] と同じ交換制 ([T-505] 恒久機構) の適用と、[T-432] が数える予算残の解消が前提になる
