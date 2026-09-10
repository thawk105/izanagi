# 段 1 brief — [T-209] プロセス系凍結の解除条件付替えと研究側 routing の決着

- wave: `dev-wave-t209-freeze-repoint` (背景 job `eff60885`、worktree `.claude/worktrees/dev-wave-t209-freeze-repoint`)
- 基準 commit: `8b81cf81a5ccbd0dc0ed81573e62560956d23fb4` (= local main tip、startup gate green)
- 種別: **docs-only** (実装面が生じたら Codex `role=author` 必須 = D95)

## 確定済みユーザー裁定 (逐語要旨)

1. (74) #1 — **[T-193] 前段は択 (a)**: `tools/pegasus/dispatch_compute.py` を正本にし、
   `dev-wave-improve` の `test_dispatch.py` / `submit_tests.py` / `run_tests_job.sh` は
   **取り込んだうえで削除する**
2. (74) #2 — **プロセス系凍結の付替えは択 (a)**: 解除条件を「床値実測の開始」から
   **「[T-193] の閉鎖」**へ変え、**その次の 1 wave は研究側にする**
3. (80) — T-193 の選択肢提示に対し **「main を正本にする」**

## 段 1 前提実測 (F35 stale 照合、すべて本 wave で実測)

- M1: T-209 の**第 1 節 (解除条件の付替え) は既に着地済み**。`docs/phase3.md` の
  「2026-07-31 改訂 (`/rulings` ユーザー裁定 = 推奨案 (a) 採用)」段落。導入 commit = `27b2813`
- M2: 凍結条件の記述は repo 内で `docs/phase3.md` の 1 箇所だけ (`git grep` / 他 worktree の複製を除く)
- M3: T-193 は (80) で決着済み。正本 = `output/insights/2026-07-30_dev-wave-improve-wave/s9-t193-ruling.md`。
  ただし worklog (80)(81)(82) の次の一手では**今も「変わらず」**で、閉鎖が台帳に無い
- M4: main の `tools/pegasus/` に `test_dispatch.py` / `submit_tests.py` / `run_tests_job.sh` は
  **存在しない** (`git ls-tree` で branch `codex/dev-wave-improve` 側にだけ在ると確認)。
  よって裁定 1 の「削除」面は main に対して **no-op**
- M5: 裁定 1 の「取り込む」面 = accounting footer の `Group Name` exact 束縛は
  **[T-222] (P1・新規) へ分離済み・未実施**
- M6: 既使用 T 番号の最大は **T-233** (全 `refs/heads` + `refs/remotes` + 全 worktree の docs を実測)

## 起点の訂正 (段 2 planner が反証、親が再実測して追認)

段 2 planner が「local main は既に前進しており brief の M6 / P3 は成立しない」と指摘した。
親が独立に実測して**追認**する (実測は wave worktree で `git show main:...` 直読み)。

- 訂正 1: local main は `8b81cf8` → **`4a4e7ed`** へ 3 commit 前進 (`/cleanup-branches` の (83) 3 commit)
- 訂正 2: worklog 末尾は (82) → **(83)**。bytes は 92,778 → **93,960**。
  ローテーションが起き `docs/archive/worklog-phase3-0731-76.md` が新設された
- 訂正 3: **M6 は誤り**。既使用 T 番号の最大は T-233 ではなく **T-234** (= (83) が起票した
  handoff 回収漏れの項)。よって **P3 の採番 [T-234]/[T-235] は使えない**
- 訂正 4: (83) は本 wave の前提を 1 つ補強した — u1〜u5 worktree の未コミット差分が
  `codex/dev-wave-improve` tip と md5 一致で、「[T-193] が main 側採用で決着させたため
  **二重に superseded**」と記録して破棄側に置いた。台帳の他エントリも T-193 の裁定を
  執行済みとして扱っている
- 訂正 5: `DW-O08` は「freeze 族の初期化 (= submodule init)」であり、プロセス系 freeze とは
  別物である (planner の懸念は誤読)。本 wave では起動時に初期化済みで startup gate rc=0
- **最終採番と bytes は段 7 の統合直前に再実測して確定する** (F58: 並行 wave が
  `worktree-dev-wave-axis-env-contract` / `worktree-dev-wave-network-split` として稼働中)

## scope

- S1: **[T-193] の閉鎖判定を確定**し、worklog 台帳へ閉鎖として記録する
- S2: **プロセス系 freeze の再発効**を `docs/phase3.md` へ 1 段落追記する (既存改訂段落は書き換えない)
- S3: **次の 1 wave を研究側にする routing** を台帳へ固定し、受け皿の T 番号を新規起票する
- **scope 外**: 研究側 wave の実行そのもの、[T-222] の移植実装、`codex/dev-wave-improve` branch /
  worktree の掃除、roadmap 本体と絶対規律の改訂

## 不変条件

- 絶対規律・roadmap 本体を変更しない。phase3 の既存改訂段落は追記のみで書き換えない
- push / remote 操作をしない。local main 取り込みは段 9 の `DW-O23` 経路だけ
- 他 wave 所有の handoff / branch / worktree (T-126 は「作業中」= 稼働中の可能性) に触れない

## 親の provisional 裁定 (すべて攻撃対象)

- **(P1) T-193 は閉鎖と扱う。** 根拠 = 正本選択は (80) のユーザー裁定で確定、削除面は M4 により
  main で no-op、移植面は M5 のとおり [T-222] へ分離済み。**反論の余地** = 裁定 1 の「取り込んだ
  うえで削除する」の「取り込む」が未了なので閉鎖と呼べない、という読み
- **(P2) 凍結の再発効は 2026-08-01 ((80) の裁定日) 付**とし、(81)(82) を遡及して違反認定しない。
  根拠 = (80) が閉鎖を台帳へ書かなかったため発効が可視化されていなかった
- **(P3) 研究側の受け皿を新規起票する** — [T-234] 変異軸をデータ構造水準へ、
  [T-235] 既知解までの距離で能力を測る評価設計 (phase3 2026-07-27 改訂 (3) が根拠)。M6 より衝突なし
- **(P4) 本 wave 自身は凍結対象外**。凍結条件そのものを確定するメタ作業であるため
- **(P5) 第 1 節は再実装しない** (M1)。本 wave は第 2 節 (閉鎖 → 再発効 → 研究側 routing) だけを閉じる

## 成果物影響 (DW-G05)

実装しない場合、台帳 (worklog 次の一手) の [T-209] が「実施待ち」のまま残り、freeze の発効状態が
未確定であるため、**次 wave の受理集合 (着手してよい作業種別) が道具・運用へ開いたまま**になる。
certified 選択・レポート・proof chain の数値と参照は変わらない (docs-only)。

## 成果物の形と受入

- 差分は docs のみ: `docs/phase3.md` (+1 段落)、`docs/worklog.md` (新エントリ + 次の一手)、
  必要に応じ `docs/decisions.md`
- 受入 = `python3 tools/check_docs.py` rc=0 + docs 関連テスト。実行環境は Pegasus 計算ノード
  (T-188 により login からの `tools/run_tests.py` は gen_S へ自動 dispatch)
- 変異 matrix と受入全走は「実装差分なし」のため対象外 (`DW-S04` の射程明記に従う)

## 並列分割

実装面が無いため子は read-only のみ: 段 2 planner 1 本、段 3 敵対レンズ 2 本 (A = 裁定忠実性・
正本整合、B = 到達性・副作用・台帳の一貫性)。段 5・6 の実装子は起こさない見込み。
