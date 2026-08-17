# 段 1 brief — [T-1283] 待ち手の権威を tested main 側 blob へ束縛する

wave = `t1283-waiter-runner-main-blob` / branch = `worktree-t1283-waiter-runner-main-blob`
worktree = `/work/1/SFC/tanab/izanagi/.claude/worktrees/t1283-waiter-runner-main-blob`
main HEAD (着手時) = `2a3b5055`

## scope

[T-1283] 択 (a) の**未実装の残り**を実装する = 待ち手 `tools/dev_wave_wait.py` 自身の権威を
tested main 側 blob へ束縛する。runner `tools/run_tests.py` は D487 で非帰属経路だけ実装済み。

## 確定済みユーザー裁定

- **[T-1283]** (2026-08-17 /rulings 全件 第 5 回 #3、択 (a)): 待ち手と実行器も本流側 blob と
  照合する。[T-1131] と同型の代償は受け入れる。正しさの門なので「防御的堅牢化は既定で見送り」の
  例外側。台帳 = archive `worklog-phase3-0817-622.md:579`。
- **[T-1195]** (2026-08-16 /rulings 全件 第 2 回 #9、択 (a) 現状維持): 待ち手も main 束縛する案は
  **採らない** — 待ち手は改修頻度が高く恒久拒否の代償が checker より重い、D403 の却下理由は今も
  生きている。条件 = 「閉じた」と記録せず failures 台帳へ登録し [T-696] に束ねる。
  台帳 = archive `worklog-phase3-0816-584.md:547`。**この記録条件は未執行** (failures に該当 0 件)。
- **[T-696]** (同 #10): 「審査される側が審査する道具を書き換えられる」構造は協調境界として受容。
  ただし**安く塞げる入口は個別に塞ぎ続ける**。

→ [T-1195] と [T-1283] は同一対象について正反対。1 日新しい [T-1283] を controlling とする (P1-1)。

## 段 1 実測 (一次資料)

- **M1 実装現況。** 待ち手 = tip 束縛のみ (D403、`tools/dev_wave_wait.py:773`)。
  checker = tested main の bytes を実行 + main==tip 等値 (`:2273-2312`)。
  runner = main==tip 等値 (`:2315-2338`)。**後 2 者は `_verify_red_check_receipt` (`:3310-3372`)
  の内側だけ = `non-attributable-only` 経路限定。** land 側も同形 (`tools/dev_wave_land.py:743-805`)。
  D487 は「child-green の受理集合は変えない」と明記。
- **M2 経路の実分布。** 2026-08-17 の acceptance receipt 23 本のうち **child-green 22 本 /
  non-attributable-only 1 本** (最新 = 22:17 `rulings-full6-20260817`)。
  → 既存の main 束縛が発火するのは受入の約 4%。[T-1283] 原票が名指しした穴 (child-green の
  自己証明) が受入の主経路そのものである。
- **M3 編集頻度** (2026-08-10 以降の commit 数): `dev_wave_wait.py` 24 / `dev_wave_land.py` 13 /
  `check_acceptance_reds.py` 8 / `run_tests.py` 4。→ [T-1195] の却下理由は実測で裏付く。
- **M4 [T-1321] の訂正。** 「main で決定的に赤、受入全走を必ず非緑にする」は耐久受領証と矛盾する
  (child-green 22 本はいずれも全走 rc=0)。段 7 で訂正を記録する。
- **M5 [T-1284] は既に閉じている。** 非帰属 node の `rerun_rc == 1` は D487 item 2 で実装済み
  (`tools/dev_wave_wait.py:3135-3137`)。段 7 で台帳を閉じる。
- **M6 DW-O09 pin 閉包。** 凍結 bytes pin は 0 件 (`FROZEN_MANIFEST` を持つ 6 file のいずれも
  本 4 file を参照しない)。規範側の pin は `docs/pegasus-runbook.md` §7.3 と
  `tools/check_docs.py:320` の `DEV_WAVE_WAITER_TARGET`。

## 不変条件

- **I1** 正しさの門を緩めない。既存の受理集合を広げない。
- **I2 恒久 land 不能を新設しない。** 待ち手を編集した wave が「どの経路でも land できない」形は
  [T-1283] 裁定の前提 (「[T-1131] と同型」「新種の負担は増やさない」) を外れる。
- **I3** 恒真ゲートを「守っている」と書かない。D487 の述語表と同じ様式で narrowing と防御深度を分ける。
- **I4** self-report と Git 由来を混同しない。land が独立検証できるのは Git 由来値だけである。

## (P1) 親の provisional 裁定 — 攻撃対象

- **(P1-1)** [T-1283] は [T-1195] を supersede する。段 4 で覆すのは裁定時の未見事実だけ。
- **(P1-2)** 採る形は γ = 「受入を実行する待ち手の**実行 bytes** が
  `tested_main:tools/dev_wave_wait.py` の blob 内容であること」を要求し、不一致なら main 側 bytes で
  self-bootstrap して再実行する。**main==tip 等値要求 (β) は I2 に反するので採らない**
  (待ち手を編集した wave が両経路とも塞がれる)。
- **(P1-3)** γ は待ち手の入口で効くので **child-green / non-attributable の両経路**を覆う。
  これが M2 に対する純増検出力である。
- **(P1-4)** runner の child-green 束縛は land の argv exact pin
  (`argv == ["python3","tools/run_tests.py"]`、`resolved_runner_path`) と衝突しうる。
  段 2 で実在を確認し、衝突するなら scope 外にして裁定パッケージへ返す。
- **(P1-5)** D403 の却下項「receipt に実行 bytes の sha256 を field 追加するのは冗長」は
  **tip 束縛下**の判断である。main 束縛下では tip != main がありうるので冗長でない。段 2 で検証する。

## 純増検出力 (性質での既存被覆)

- 既存 = 「実行 bytes == その走行の tip blob」(D403) / 「checker・runner の main==tip 等値」
  (T-1131・D487、非帰属経路のみ)。
- 純増 = 「受入を実行した待ち手の bytes が **tested main 版であること**」。child-green を含む
  全走行に効く。既存のどの検査もこれを含意しない。

## 成果物の形

実装 (`tools/dev_wave_wait.py`、`tools/dev_wave_land.py`、対応テスト) + `docs/pegasus-runbook.md`
§7.3 の改訂 + D 記録 + worklog fragment。実装しない裁定になった場合は裁定パッケージと fragment のみ。

## 成果物影響 (DW-G05)

未対処だと acceptance receipt は wave tip の自己証明のままで、実際は赤の走行を child-green として
台帳へ残せる。certified 選択結果の land 根拠 (「受入が緑だった」という主張) が失われる。

## 分割方針・環境

実装面は Codex `role=author` 1 単位 (待ち手・land・テストは相互依存が強く所有を素集合に割れない)。
docs は親。受入は Pegasus (計算ノード dispatch)。焦点走は `tools/run_tests.py`。
