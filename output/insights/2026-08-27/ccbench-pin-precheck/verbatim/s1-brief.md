# 段 1 brief — ccbench-pin-precheck-20260827

## scope

CCBench submodule の pin を上げた場合の影響範囲を実測し、択一をユーザー裁定へ返す。
**実装差分ゼロ。pin を動かす編集は行わない。** 成果物は裁定パッケージ + 記録のみ。

## 確定済みユーザー裁定 (引数由来)

- 実際に pin を動かしてはならない
- 影響範囲と「上げる / 上げない / 条件付きで上げる」の択一を返すところまでが scope

## 前提の実測結果 (DW-S01 に従い brief 前に実測。1 件は前提を覆した)

引数は「上流 master から 3 本ぶん古い」としていたが、実測で**誤り**と判明した。
pin `511c9538` は master の祖先ではなく、izanagi 専用 branch の tip である
(`merge-base` = `7e268f2a`、`511c9538..master` = 16 commit、`master..511c9538` = 8 commit)。
master には izanagi の TRACE 計装が一切無い。詳細は `findings.md` F1/F2。

→ 択一の形自体が変わる。段 4 で再裁定する。

## 不変条件 (緩めない)

1. **絶対規律 1 / 3**: verifier の入力である TRACE 計装を失う経路を推奨しない。
   `CCBENCH_TRACE` と `TRACE=${CCBENCH_TRACE}` が消える変更は D14 契約の土台を壊す
2. **decisions.md:3552**: `EXPECTED_SOURCE_LINES` の literal は
   「pin bump 時のみ裁定つき更新」。AI が独断で更新しない
3. **D444 決定 3**: 床値 protocol の不変 16 field は byte-exact 継承。承認定数から再導出しない
4. **D471 / D491**: resolver の `C`/`E` 契約を変えない。
   D491 が却下した「pin を選択条件から外す」型の resolver 改造を推奨しない
5. **既存の凍結 bytes を 1 件も上書きしない** (床値 protocol は追加のみ)
6. `freeze_verification_hold.HELD` の解除条件は `explicit-user-command-only`。
   この wave では触れない

## 判断が割れうる前提 (親の provisional 裁定 = 攻撃対象)

- **(P1)** 推奨は「master を izanagi-trace branch へ merge して re-pin する」型である。
  根拠: 競合ゼロで通り、TRACE が残り、凍結行のずれが 5 行→1 行に減る (F3/F4)。
  攻撃点: merge commit を上流 branch に積むと push (人間手番、D16) が要る。
  未 push の pin を指す gitlink は clone 不能になる (`pin.py` docstring)。
- **(P2)** 床値 protocol の再発行は再計測を伴わない、と読んでいる (D444 決定 3 の byte-exact 継承)。
  攻撃点: 16 field の中に環境依存の値があり、実際には再計測が要るのではないか。
- **(P3)** pin 照合系 9 件は `HELD=True` に守られるので追加コストはゼロ、と読んでいる (F9)。
  攻撃点: 保留の対象外の経路 (F4 golden / F6 resolver) を数え漏らしていないか。
- **(P4)** E1-stale は 0 件、と結論した (F8)。
  攻撃点: 25 path 以外に受理集合を動かす epoch 束縛が無いと言い切れるか。
- **(P5)** 「上げない」を選んでも既存の受理集合・凍結 bytes は 1 bit も動かない、と読んでいる。
  攻撃点: SS2PL の SIGSEGV が別経路で成果物を汚していないか。

## 成果物の形

1. `docs/` へ入れる裁定パッケージ (択一・各案の費用・不変条件・実測表)
2. spool fragment (worklog / decisions は fragment、insights は直接) 
3. 実測証拠 `output/insights/` 配下

## 成果物影響 (DW-G05)

この wave が何も出さなかった場合: pin bump の可否が測られないまま残り、
(a) SS2PL を使う materials campaign が着手できない (YCSB 入口が無く tpcc は落ちる)、
(b) 誰かが pin を動かした瞬間に床値 admission が fail-closed で止まり、
    `s8b_holdout_admission` / `certified_writer_admission` 経由の certified 選択結果が
    新規生成できなくなる。復旧手順が裁定済みであることも知られないまま止まる。

## 並列分割方針

実装面が無いため段 5 の実装子は起動しない (`4→7→8→9`)。
ただし設計択一が割れ、正しさ防壁 (TRACE) に触るため **DW-C00 の carve-out により
段 3 の敵対検証子は省かない**。read-only codex 2 本、異なるレンズで (P1)〜(P5) を攻撃する。
段 2 のプラン起草は実装が無いため行わない。

## 環境

- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-pin-precheck-20260827` (locked)
- branch: `worktree-dev-wave-ccbench-pin-precheck-20260827`、base = local main `b7f66232`
- 受入: `tools/dev_wave_wait.py acceptance` (Pegasus 計算ノード。login node では pytest が guard 拒否)
