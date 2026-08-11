---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-11
wave: dev-wave-t798-t799-fold-window
seq: 1
title: fold transaction の 2 つの窓を実測し裁定パッケージを返した — 本番コードは未変更 (docs のみ、branch worktree-dev-wave-t798-t799-fold-window)
---

## 本文

- **依頼は実測と裁定パッケージであり、本番コードの編集はユーザーが明示的に scope 外にした。**
  したがって段 4 の裁定は「実装しない」で、段 5・6 を飛ばして `4→7→8→9` とした。
  実装差分は 0 で、変更したのは docs (worklog fragment) と `output/insights/` だけである。
- **両方の窓を再現した。** [T-798] は本番 land を窓の内側で実際に SIGKILL して測った。
  注入点は本番が subprocess 起動する `tools/check_docs.py` で、land 本体へ monkeypatch は当てていない。
  [T-799] は本番 `apply_fold` に state を書かせ (plan 構築後に fragment を 1 行増やすと GC 照合で
  止まり state だけが残る)、tree を清浄に戻してから HEAD を動かして測った。
- **[T-798] の実害は「復旧用の道具が黙っていること」だった。** crash 後に残るのは
  canonical・`FOLDED.md`・fragment GC が反映済みで fold commit も journal も無い tree である。
  ここで正規の復旧 CLI (`python3 tools/spool_fold.py`) は **rc=0 / `status=noop`** を返す。
  land を再投入すると rc=20 `main tracked/index/submodule dirt is forbidden` で止まるが、
  この理由語は fold を一言も指さない。運用者が取る自然な次手 `git checkout -- docs` は
  適用済みの fold を捨て、代わりに手で commit すると `verify_declared_fold_commit`・
  fold author・`AI-Agent:` trailer のどれも通らない commit が main に載る。
- **窓の幅は「pre-commit 部分の代替小計で約 2.83 秒、大半が `check_docs.py`」までしか言えない。**
  当初の「窓は 2.83 秒・96%・land 1 回ごと」は敵対レンズ A の指摘で**撤回した** —
  `git commit` と postcondition を含んでおらず、`git add` は clean tree の `git status` で
  代替しており、fragment 0 件の land は窓へ入らない (露出の分母は non-noop fold の回数)。
- **[T-799] の核は HEAD ではなく plan 入力 closure の未束縛だった。** state が hash で束縛するのは
  plan の **target** だけで、採番の入力 (`docs/archive/worklog-*.md`、`docs/phase3.md` の見送り台帳、
  `tools/check_docs.py` の `WORKLOG_ROTATE_BYTES`) は target でない限り一切現れない。
  **archive worklog へ別 wave が同じ番号を確定させてから resume させると、古い採番を適用して
  重複 T 番号ができた** (`[T-052]` が worklog と archive の両方に存在。再計画なら `[T-053]`)。
  これは敵対レンズ A の所見から親が追加実測したもので、**[T-799] を帰属の問題から値の問題へ
  格上げする。**`check_docs` の T 重複検査は 1 エントリ内に閉じており archive を跨がない (静的確認)。
- **state が束縛する field は 8 個で、HEAD・land 起源・base・tested tip はどれも入らない。**
  `transaction_id` にも入らない。resume 経路は新規 apply が通る `_git_clean_preflight` を
  通らず、**resume の方が弱い**。`_verify_supervised_fragment_wave` は
  `refs/heads/dev-wave/dw-` 以外で no-op なので、`worktree-dev-wave-*` の通常 wave には
  wave 同一性の束縛が一切かからない。**standalone は land lock も取らない** (静的確認)。
- **2 つの窓は連結している。** standalone resume は commit を作らないので、成功した瞬間の tree は
  [T-798] の crash 残骸と `git status` が 1 文字も違わない。
  つまり [T-799] の resume 経路には**成功しても正しい終端が無い。**
- **敵対レンズ 2 本 (sol / luna) が親の主張を 8 件崩し、親は追加実測 3 本でそれを裏取りした。**
  撤回・縮小したのは (i) 窓幅の数値と一般化、(ii) 「(b) は新しい recovery 機構を要らない」、
  (iii) 「新 field は省略可能として読む」(fail-open)、(iv) 「(a) で proof chain が durable になる」、
  (v) 「発火条件は process 死のみ」(通常例外 + rollback 失敗の二重故障でも起きる)、
  (vi) 「[T-766] が増やす state と同じ形」(測ったのは pre-mutation state)、
  (vii) 「C2 は帰属が壊れた欠陥」(測った C2 は正常動作で、実害は採番入力の未束縛の方)、
  (viii) 「standalone resume は必ず残骸に着地」((b) 採用後は健全な反例ができる) である。
- **とくに (ii) は追加実測で確認した。** (b) は窓を消さず「commit 済み・state 残存」へ**移す**だけで、
  その形から land を再投入すると **rc=10 `stale-main`** で止まる。閉じられるのは standalone CLI
  だけで、それは Q2 (b) が封鎖したい経路である。したがって (b) には land 側の finalize 経路が要る。
- **親の見積りの誤りも 2 件、実測で正した。** テスト pin の数は親「5 行」もレンズ B「9 行」も誤りで、
  **(b) が実際に壊す pin は 1 本だけ** (`test_interrupted_transaction_resumes_before_and_after_targets`)、
  land 側だけ挙動を分ける実装なら 0 本である (親は dry-run のテストを誤って数え、レンズ B は
  rollback と dry-run の pin を含めていた)。もう 1 件は probe の恒真な検査で、
  `probe_post_apply_resume.py` の「canonical は不変」が同じ `git status` を 2 回呼んで比べていた。
  適用後の bytes を捕まえる形へ直して再走し、結論は変わらなかった。
- **「(a) で proof chain が durable になる」が過大だった点は独立の問に切り出した。**
  state は成功時に消え、`FOLDED.md` の receipt は wave / seq / content_sha256 / allocation しか
  持たないので、束縛値を残す durable な場所が現状どこにも無い。
- **(b) の冪等性は難しい plan でも成り立った。** ローテーション発火・failures の再発挿入・
  supersede 追記・見送り追記を含む plan でも、再適用は書込み 0 の `resumed` で全 target が
  byte 単位で不変、二重挿入ゼロだった。機序は変換の再実行ではなく content-addressed な収束である。
- **[T-799] C 節には採用しなかった初回測定がある (erratum)。** 権威は `probe_t799c.log` (rc=0) で、
  先行する `probe_t799.log` の同じ節は rc=20 を返していた。原因は本番挙動ではなく fixture の誤りで、
  2 本目の wave worktree を作った後に main で `git add -A` したため `.codex/worktrees/two` が
  tracked に入り main が dirty になっていた。**初回 log は消さずに残している。**
- **一次資料と全 5 問は `output/insights/2026-08-11_t798-t799-fold-window/`。**
- **セッション事象:** 段 1 の前提実測で、fixture の `tools/check_docs.py` stub を
  module 直下の `raise SystemExit(0)` にしたところ、`_load_rotate_limit` の `exec_module` が
  land process 内でそれを走らせ、**land が出力ゼロ・rc=0 で静かに消えた**。
  `except Exception` は `SystemExit` を捕まえない。実物は `if __name__ == "__main__":` で
  囲っているので現状は発火しないが、形としては実在するので {{T:exec-module-systemexit}} に起票した。

## 次の一手差分

### 更新

- [T-798] **P2・実測済み / ユーザー裁定待ち**: `apply_fold` は canonical 書込みと fragment GC の
  直後に transaction state を消すが、land はその後に docs 検査・stage 検査・commit・postcondition を
  走らせる。**窓を実際に SIGKILL して再現した** — canonical・`FOLDED.md`・fragment GC が反映済みで
  fold commit も journal も無い tree が残り、正規の復旧 CLI は rc=0 / `noop` を返す。
  窓の幅は実 repo で約 2.83 秒 (96% が `check_docs.py`)。選択肢は据え置き
  ((a) land 専用 journal / (b) state 削除を postcondition 後へ + `validate_spool_tree` の
  active-aware 化 / (c) 現状維持)。**親推奨 = (a) と (b) を別案にせず、既存 state へ phase と
  起源を持たせて削除を postcondition 後へ移し、finalize は land だけが行う単一 protocol にする。**
  (b) 単独は窓を「commit 済み・state 残存」へ移すだけで、その形を land は閉じられない (実測 rc=10)。
  一次資料は `output/insights/2026-08-11_t798-t799-fold-window/`。
  base: 12ded6f8211f38448ee8ec37419b4bb406f9cacf1c62c3487820747586dc5cba
- [T-799] **P2・実測済み / ユーザー裁定待ち**: fold transaction state は land 起源・base・
  tested tip を束縛しない (field 8 個、`transaction_id` にも HEAD は入らない)。
  **核は HEAD ではなく plan 入力 closure の未束縛だった** — state が hash で束縛するのは plan の
  target だけなので、archive worklog へ別 wave が同じ番号を確定させてから resume させると
  **古い採番を適用して重複 T 番号ができた** (実測)。`check_docs` の T 重複検査は 1 エントリ内に
  閉じており archive を跨がない (静的確認)。resume は新規 apply が通る `_git_clean_preflight` も
  通らず、standalone は land lock も取らない。選択肢は据え置き ((a) 起源・base・tested tip・
  rollback ref の束縛 / (b) land 由来 state の standalone apply 拒否 / (c) 現状維持)。
  **親推奨 = (a) を採り、束縛対象に「plan 入力 closure の hash」を足す。束縛値は申告値でなく
  観測値にして `transaction_id` にも含める。(b) は代替の lock-aware finalize command と
  セットでのみ採る** — standalone は (b) 案の残余窓を今唯一閉じられる経路でもあるため。
  schema は厳格側を既定とし、旧 state の扱いは別問で裁定する。
  base: 4a24b91989b230b957ec484c5a0515c7ab0bf23ff5d5d8e12329588d111e2db3

### 新規

- {{T:exec-module-systemexit}} **P3・新規**: `_load_rotate_limit`
  (`tools/spool_fold.py`) は `tools/check_docs.py` を land process 内で `exec_module` する。
  `except Exception` で囲っているが `SystemExit` は `BaseException` なので抜ける。
  本 wave の probe で、`check_docs.py` が module 直下に `raise SystemExit(0)` を持つと
  **land process が出力ゼロ・rc=0 で静かに消える**ことを実測した (fixture 上)。
  実物は `if __name__ == "__main__":` で囲っているので現状は発火しない。
  選択肢 = (a) `except BaseException` へ広げ、`SystemExit`/`KeyboardInterrupt` を
  `SpoolValidationError` へ畳む / (b) `exec_module` をやめて定数を静的に読む /
  (c) 現状維持。成果物影響 = (c) のままなら、fail-closed に囲ったつもりの層が
  rc=0 = 成功に見える形で land を終わらせうるので、land 結果の rc を信じる上流
  (受入・land 監査・報告) が「成功した land」と誤認しうる。同型が他にあるかは未測定。
- {{T:fold-provenance-durable-artifact}} **P2・新規**: [T-799] (a) を入れても、
  束縛値 (base・tested tip・wave ref) を残す **durable な場所が無い**ことを実測した。
  transaction state は成功時に削除され、`FOLDED.md` の receipt は `wave` / `seq` /
  `content_sha256` / allocation しか持たず、fold commit の message は固定文言である。
  選択肢 = (a) `FOLDED.md` の receipt へ base / tested tip / wave ref を足す /
  (b) fold commit message へ構造化 trailer で書く / (c) 両方 / (d) 実行時検査だけで足りるとする。
  成果物影響 = (d) のままなら、実行時の受理集合は狭まっても「この fold commit がどの main 状態に
  対して採番されたか」を台帳から言えず、certified 選択の proof chain を main 履歴へ帰属させる
  依頼の動機自体が満たせない。親推奨 = (a) ([T-799] と同時に裁定するのが望ましい)。
