---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2627-runbook-child-green-only
seq: 1
title: [T-2627] pegasus-runbook §7.3 の受入節から、機構から外れた受理経路 (赤の帰属判定器による旧経路 (ii)) の記述を消し、受理は child-green の 1 本だけ (D690 決定 2) に揃えた — 8 箇所 +19/−39 行 (docs のみ、branch worktree-dev-wave-t2627-runbook-child-green-only、変異 matrix 免除 = 実装面差分ゼロ、子ゼロ)
---

## 本文

- ユーザー依頼は「[T-2627] (P2、entry 1497) docs/pegasus-runbook.md の受入節から、機構から外れた受理経路の記述を消す (docs のみ) —
  tools/check_acceptance_reds.py は file として実在するが tools/dev_wave_wait.py からの参照は 0 件で、受入は child-green だけを
  受理する。runbook の該当記述を現行機構 (child-green のみ) に揃える。check_acceptance_reds.py の削除や廃止語検査の追加はしない。
  着手直前の local main から fresh worktree を作る。規律 2 を緩めない。本題の記述訂正だけ。仮想リスク向けの gate・検査・台帳・一般化の
  追加は scope 外」。
- **閉じた。** 一次資料は F588 (再発 2026-09-14) と D690 決定 2、揃える先の文言は `DW-O18` 末尾「受理は`child-green`だけ、赤の受領証禁止」。
  decisions fragment 0 (新しい設計判断なし)、failures fragment 0 (F588 の再発検知が言うとおり「消し忘れは検索で消す」を実施しただけ)。
- 前提の実測 (2026-09-18 10:40 JST、main 24ede1d11): `tools/check_acceptance_reds.py` は実在 (74,836 bytes)、
  `grep -c check_acceptance_reds tools/dev_wave_wait.py` = 0。待ち手は `normalized_child_rc != 0` なら rc=1 でも
  `acceptance-command` 失敗として返し、`verdict = "child-green"` の代入は 1 箇所だけ。launcher への completion は常に
  `"red_check": None` で、launcher は rc=0 + `red_check` 無しのときだけ `child-green` 受領証を書く。`--log-file` の現行用途は
  受領証の log hash の照合 (launcher が書いた log を待ち手が独立に読み直す)・実効 scheduler の attestation・判定なし終了の再試行証拠であり、
  旧記述の「非帰属判定の素通り防止」ではない。
- 変更 8 箇所 (すべて §7.3「受入 lease の待ち手」): (A) 受領証の発行条件「下の受理 2 経路のいずれか」→「受入 command が rc=0
  (`child-green`)」、(B) `--log-file` を待ち手自身が捕獲する理由を現行用途へ、(C) log は「非帰属判定の一次資料」→「赤の帰属を人・AI が
  判定する一次資料 (`DW-O18`)」、(D) 「受理は 2 経路ある」段落 (checker の exact 2 形・`flake` の定義・`status = "green"` の扱いを含む
  18 行) →「受理は `child-green` の 1 本だけ (D690 決定 2)」8 行、(E) 「この照合は `child-green` にも掛かる (99.0%、103 本中 102 本)」
  → 現行形、(F) 「checker を変更した wave は経路 (ii) だけ使えない」bullet を削除、(G) checker の timeout / heartbeat / process group の
  「既知の限界」bullet を削除、(H) 「rc=0 は receipt 発行」の段落を child-green 前提 (`red_nodeids` / `flake_nodeids` は空) へ。
  checker の file 名は runbook 本文に残していない (F588 恒久対応の禁止語と同じ語彙。runbook への禁止語検査の追加は依頼どおり行わない)。
- scope 外に残したもの: `tools/dev_wave_land.py` と `tools/acceptance_launcher.py` に残る `non-attributable-only` の検証枝
  (権威経路から到達不能。撤去は [T-2011] / D1159 の別タスク)、checker file の削除 (D690 が編集面外と明記)。
- 段構成: 軽量版・子ゼロ (`DW-C00` docs-only)。段 2・3・6 の codex 子は省略、親が file:line の plan と裁定 (P1 = `--log-file` の理由を
  消すのでなく現行用途で置き換える、P2 = rc=0 の意味を child-green 前提へ、ともに採用)。変異 matrix は免除 (実装面差分ゼロ)。
  開始 gate `check_wave_startup.py --mode fresh --external-handoff` rc=0、`tools/check_docs.py` rc=0 (違反なし)。wave 開始後に
  local main が 24ede1d11 → 386fc515c へ進んだので、初 commit 前に `--ff-only` で揃えた (runbook は非接触)。受入全走は fragment
  commit 後・land 前に 1 回投入する (結果は land の受領証)。
- 工数: codex 子 0 本。親のみ (待ち手・launcher・land の現物検算、runbook の置換 script は job dir、repo 外)。
- 同じ節で見つけた別の食い違い (本 wave では直さない、本題外): runbook §7.3 は「`--merge-message-file` は待機を始める前に
  用意しておく。behind が判明した時点で必須になり、無ければ投入せず止まる」と書くが、現行の待ち手は省略時に self-report
  (`merge main` + `role=integrator`、`_self_reported_merge_message_copy`) を使い、止まるのは message file の検証に失敗した
  ときだけ (`stage=merge-message`)。argparse help も「省略時は self-report を使い」と書く → {{T:runbook-merge-message-file-optional}}。

## 次の一手差分

### 完了

- [T-2627] runbook §7.3 の受理経路の記述を現行機構 (child-green のみ) に揃えた。
  remaining: none
  base: e3e43ad81e8cef7203224d3f2a80cf95d242584210c454238d1143830681cb36

### 新規

- {{T:runbook-merge-message-file-optional}} **P3・新規**: `docs/pegasus-runbook.md` §7.3 の「`--merge-message-file` は
  behind 判明時に必須、無ければ投入せず止まる」を現行機構 (省略時は self-report の integrator message、止まるのは
  `stage=merge-message` = message 検証失敗のときだけ) に揃える (docs のみ)。同節の F588 型の消し忘れ。
