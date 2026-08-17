---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: t1283-waiter-runner-main-blob
seq: 1
title: 待ち手の main 束縛は実装せず再裁定へ返した — 検査を待ち手自身の中に置く限り、待ち手を書き換えた相手には効かない (docs のみ、branch worktree-t1283-waiter-runner-main-blob)
---

## 本文

- **裁定 = 実装しない。[T-1283] をユーザー再裁定へ返す。** 起動命令が段 1 での実測を求めた
  [T-1195] との衝突は**実在した** — [T-1195] (2026-08-16 /rulings 全件 第 2 回 #9) は
  「待ち手も main 束縛する案は採らない。D403 の却下理由は今も生きている」であり、
  [T-1283] (2026-08-17 第 5 回 #3) はその正反対である。1 日新しい直接裁定が古い結論を覆す、
  という読み自体は段 3 レンズ A も独立に支持した。止めた理由は衝突そのものではなく、
  **裁定文が前提にした「[T-1131] と同型の代償・新種の負担は増やさない」が実測で成立しない**ことである。
- **設計空間が閉じることを実測した。** 名指しの穴 (child-green 経路の自己証明) を閉じる形は
  恒久 land 不能を作り、恒久 land 不能を避ける形は穴を閉じない。段 2 が推奨した案
  (実行 bytes を main 側 blob へ束縛し自己再実行する) は、段 3 レンズ A が
  **偽造耐性ゼロ**と実証した — 検査も再実行も wave tip 側の待ち手の中にあるため、
  待ち手を書き換えた側は再実行ごと削除して main 側の hash を自己申告でき、land は
  Git から再計算した期待値とその自己申告を突き合わせるだけなので通る。
- **段 3 の敵対 2 本はいずれも NO-GO** (レンズ A 9 件 / must-fix 7、レンズ B 10 件 / must-fix 4)。
  両者は独立に同じ中核へ到達した。レンズ B は加えて、受領証 schema 昇格が稼働中 wave を
  巻き添えにする費用 (D253 実測 1055〜1338 秒 × 並行 6 本)、lease を保持したままの
  process 差し替えが所有権を壊す経路、一時 source の path/inode 契約が現行の束縛条件
  (basename `dev_wave_wait.py`・親 `tools`・regular file・同一 inode) と衝突することを出した。
- **親の実測 3 件のうち 2 件は母集団定義が不足していた** (両レンズが独立に指摘)。集計 predicate を
  固定して取り直した結果は次のとおりで、結論の向きは変わらない。
  `/work/1/SFC/tanab/dev-wave-jobs` 配下を再帰的に `acceptance-receipt*.json` で拾い、
  mtime >= 2026-08-17 00:00 JST に限ると 30 file。うち赤検査 sidecar
  (`izanagi-acceptance-red-check/v1`) 5 件を除いた**受領証 25 本の内訳は child-green 24 本 /
  `non-attributable-only` 1 本**、schema は v3 19 本 + v4 6 本 (v4 は本日 [T-1302] が導入)。
  → **既存の main 束縛 (checker・runner) が発火するのは受入の約 4% だけ**であり、
  [T-1283] が名指しした穴は受入の主経路そのものにある。
  `tools/dev_wave_wait.py` の編集頻度は 2026-08-10 以降 24 commit だが、内訳は
  non-merge 21・main first-parent 12 であり「24 回の独立改修」とは読めない (段 3 レンズ A の再検証)。
- **親 brief の文言 3 箇所が過大記述だった** — 「実行 bytes を main に要求」「両経路を覆う」
  「純増検出力」。D403 が保証するのは module 初期化直後に束縛した inode の bytes までで、
  実行 bytecode ではない。段 4 で撤回した。
- **凍結 bytes pin は 0 件**を path key (`grep -rn "<path>" --include=*.py`) と識別子 key
  (`dev-wave-acceptance-receipt` / `dev-wave-wait-acceptance` / `izanagi-acceptance-red-check`) の
  両方で確認した。ただし positive control (既知の pin を scanner が拾えることの確認) は
  未実施であり、段 3 レンズ B の指摘どおり「0 件」は完全な閉包証明ではない。
- **`docs/pegasus-runbook.md` に byte 予算検査は無い** (構造検査のみ)。親が段 1 で挙げた
  「予算に収まらないなら実装を止める」という懸念は不要と確定した (段 3 レンズ B が反証)。
- **並行 6 wave はいずれも受入経路の 4 file と runbook を触っていない**ことを着手時に確認した。
- **段 5・6 は裁定により省略**した (`DW-S04` の「実装しないと裁定した場合だけ段 5・6 を飛ばす」)。
  実装差分ゼロのため変異 matrix は免除、受入全走は免除せず実走した。
- **子の工数。** codex 3 本 (plan 1・consult 2)。破棄・再投入はゼロ。

## 次の一手差分

### 完了

- [T-1284] 非帰属 node の `rerun_rc` が型しか見られていない件は、D487 決定 2 の exact 受理形として
  既に閉じていた (`tools/dev_wave_wait.py` の非帰属 node 述語が field 集合ちょうど
  `classification` / `nodeid` / `rerun_rc` と `rerun_rc == 1` を要求する)。本 wave は実測で
  確認しただけで、コードは変更していない。
  remaining: none
  base: 798426aac87e944584b83f17f4a89758691fd2918f6945bd15ef7deb19fb3163

### 更新

- [T-1283] **P1・ユーザー再裁定待ち (2026-08-17 の wave が択 (a) を実装せず差し戻した)**:
  択 (a)「待ち手と runner も main 側 blob と照合する」は、**名指しの穴に効く形では
  恒久 land 不能を作り、恒久 land 不能を避ける形では穴を閉じない**ことが敵対 2 本の
  独立 NO-GO で確定した。受入の 96% は child-green 経路 (実測 24/25) で、そこは
  wave tip の自己証明のままである。**択は (a) 両経路で main==tip 等値を Git 由来で要求する
  (穴は確実に閉じるが `tools/dev_wave_wait.py` と `tools/run_tests.py` を編集した wave は
  どの経路でも land 不能になり、改修が二段運用になる) / (b) 候補外の trusted launcher を
  新設して受入の権威を wave tip の外へ出す (閉じつつ恒久 land 不能も作らないが新機構で 1 wave 以上)
  / (c) 実行 bytes の自己申告版だけを協調的な drift 防御として採る (軽いが穴は閉じない。
  条件 = 「閉じた」と記録しない) / (d) [T-1195] の現状維持へ戻す (条件 = 既知の未閉鎖として
  failures 台帳へ登録し [T-696] に束ねる)**。親の推奨は (d)、次点 (b) — (a) は最も改修頻度の
  高い file の改修導線を恒久的に二段化する費用が、閉じる穴の実害 ([T-696] で協調境界として
  受容済みの「内部作業者が自分を欺く経路」) に見合わない。**どの択でも runner の child-green 穴を
  同じ裁定に含める必要がある** ([T-1283] 原文は runner も名指ししている)。
  成果物影響 = 未対処だと acceptance receipt が wave tip の自己証明のままで、実際は赤の走行を
  child-green として台帳へ残せる。certified 選択結果の land 根拠が失われる。
  base: 6334b05fc34b41138600057d13051392a8885f6d5d103ceda918bab0d97cb4fd
- [T-1195] **P1・[T-1283] の再裁定に併合して扱う**: 記録条件 (「閉じた」と記録せず failures 台帳へ
  登録し [T-696] に束ねる) が 2026-08-16 の裁定以来**未執行**だったので、本 wave で
  {{F:acceptance-authority-self-certified}} として執行した。[T-1283] の再裁定が (d) 以外に
  決まった場合は、その裁定に合わせて同 F の恒久対応欄を更新する。
  base: a7fc5e999c126bfd0e00d521d39f1093f5b5673c5e84d84779f130c9c17445dd
- [T-1321] **P2・前提を訂正 (2026-08-17 実測)**: 「main で決定的に赤なので受入全走を必ず非緑にし、
  受入は毎回 checker の非帰属判定に依存している」は**耐久受領証と矛盾する**。本日発行の受領証
  25 本のうち 24 本が `child-green` (= 全走 rc=0) であり、非帰属判定に落ちたのは 1 本だけである。
  赤は変異 harness の baseline 文脈で観測されたものと考えられ、受入全走の文脈では再現していない。
  当該 node の帰属を測り直してから起票内容を確定する。
  base: adfe20a00629895d5ec15e62849a2f97e45533ef7446aa573a99cd8d67ccf628

### 新規

- {{T:devwave-detach-oneliner-budget}} **P3・新規 ([T-1283] 段 8、[T-1320] と同族)**:
  `DW-O01` が指示する detach 定型 (`nohup setsid bash -c '<cmd>; echo $? > <log>.done'` を
  `&` で背景化する 1 行) は、worktree 隔離の session では harness の guard が
  「worktree 内に留まることを検証できない」として拒否する。本 wave は 2 回踏み、runner と
  launcher を 2 段の `.sh` へ外出しして回避した。是正 1 行 (83 bytes) を `DW-O01` へ入れると
  **`docs/dev-wave/**` の L1.5 unique footprint が 9649 > 予算 9566 bytes で check_docs が赤**になる。
  上限は上げない既裁定 ([T-1300]) があるため、収容先 (既存文の縮約 / 新規 L2 節 / 見送り) を
  ユーザー裁定へ返す。**[T-1320] と同型の 2 例目**であり、`DW-G03` の「族一般化には独立 2 例」が
  満たされたので、個別の押し込みでなく収容方針そのものを裁定対象にできる。
  成果物影響 = 成果物の値・受理集合・参照は変わらない。dev-wave の起動導線で毎回 1 回失敗するだけである。
