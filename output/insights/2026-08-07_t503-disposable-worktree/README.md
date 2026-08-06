# [T-503] 変異復元耐久化 第一 slice — 使い捨て専有 worktree

- `authority: none`
- `default_effect: no-state-change`

可変状態の正本ではない。可変状態は `docs/worklog.md` 末尾と現行 phase doc が正本である。
設計の正本は `docs/mutation-restore-durability-design.md` (本 slice の射程は同書 §9.3)。
本書は 2026-08-07 の実装 wave (branch `worktree-dev-wave-t503-disposable-worktree`) の
実測と裁定を凍結する。

逐語は `verbatim/` — `s1-brief.md` (親の段 1 brief)、`s2-plan.md` (段 2 プラン)、
`s3-lensA.md` / `s3-lensB.md` (段 3 敵対相談)、`s4-ruling.md` (段 4 裁定)、
`s5-impl.md` (段 5 実装子)、`s6-revA.md` / `s6-revB.md` (段 6 敵対レビュー)、
`s6-fix.md` / `s6-fix2.md` (段 6 fix)。codex 子はいずれも `gpt-5.6-sol`、
`tools/check_codex_output.py` rc=0。段 2/3/6-rev は `reasoning=max` / `sandbox=read-only`、
段 5 と段 6-fix は `sandbox=workspace-write` (`reasoning=high`、fix2 のみ `low`)。

## 何を作ったか

`tools/mutation_worktree.py`。固定 commit から repo 外の scratch root へ detached worktree を作り、
その中で既存の `tools/mutation_harness.py` を `--repo` として走らせ、完走時だけ木と
**自分の worktree admin dir だけ**を消す wrapper。`mutation_harness.py` は 1 byte も変えていない
(`--repo` は既存の第一級 seam であり、U-10 (a) の no-touch 明示解除は不要だった)。

## 何を主張しないか (ここを読み違えてはならない)

- **設計 §9.1 の必須 6 点の充足は 0/6。** journal・原子的置換・`clean` capability・
  metadata admission・quiescence 証明・legacy drain gate のいずれも実装していない。
  `T-503 complete`、D130 条件 3 `closed`、[T-486] `closed` とは書けない。
- **V-3 / V-4 / V-5 は発火面が存在しないため未実装。** arm も `clean` も in-place 復元も無い。
  放棄ではなく、in-place 復元経路を作る後続 slice へ持ち越す。
- **L-B (物理ノード死・client eviction 後の永続性) は `UNKNOWN` のまま。** 本 slice が主張するのは
  共有木の観測点間で `git status` / `git submodule status` の stdout bytes が不変であることだけで、
  file bytes 全体の不変でも物理永続性でもない。
- **旧 direct 経路は残っており機械的 admission は無い。** 全 wave へ効かせるには別 slice の
  activation package が要る。本 slice は shadow prototype の位置づけで land した。
- **SIGKILL 後の人間待ちは消えていない。** 共有 checkout の汚染が消え、待ちが repo 外へ移り、
  `--resume` で再開できるようになっただけである。自動 GC は無い。

## 実測 (2026-08-07、Pegasus)

| 対象 | 値 |
|---|---|
| 使い捨て木での受入全走 | **6806 passed / 20 skipped** (929.73 s)。共有木の同時点の値と一致 |
| provision | `git worktree add --detach` 10.10 s + `submodule update --init` 1.45 s、**134 MB** |
| teardown | `rm -rf` 4.90 s |
| 範囲限定 admin 削除 | `<common>/worktrees/<name>` の直接削除で登録 9→8、`prunable` 0 件、他 7 worktree と共有 submodule は無傷 |
| harness seam | `mutation_harness.py --repo <使い捨て木> --plan-only` rc=0 |
| hook / filter 攻撃面 | この repo では **発火しない** — hook 0 個、LFS 追跡 file 0 件、partial clone でない |
| 本 wave の受入全走 (merge 後) | **7077 passed / 20 skipped** (1361.96 s) |

`output/pegasus-dispatch` を repo 外への symlink にする案も実測したが、`.gitignore` の
`output/pegasus-dispatch/` が末尾スラッシュ付きで **symlink を ignore しない**ため
clean gate に 1 行として映り、不採用とした。代わりに完走時の rename 退避を採る。

## 変異 matrix

事前登録 = `mutation-spec.json` (MW-01〜MW-14)、台帳 = `mutation-ledger.json`。
`repo_head = c4bfdf5e`、runner は dispatch。

**14 件記録 / 9 KILLED / 5 MISMATCH / SURVIVED 0 / TIMEOUT 0。**
**MISMATCH の 5 件 (MW-07〜MW-11) を含め、全 14 件で事前登録した test node が赤になった** —
帰属は成立している。MISMATCH は「登録 node に加えて他の node も赤くなった」ことによる。
これは wrapper の主経路 (teardown・rc 選択・terminal 判定) に置いた述語を壊すと、その経路を
通る他のテストも落ちるためで、**親の事前登録が影響範囲を過小に書いていた**。
`DW-M02` に従い結果は書き換えず、この記述を erratum とする。

`mutation-ledger-run1-erratum.json` は第 1 走の台帳である。MW-06 が **rc=16・stdout 0 byte** で
止まり、harness が F71 どおり「rc≠0 で failed node 0 件」を fail-closed 停止 (`PARSE_ERROR`) にした。
実装差分の赤ではない。

**親は当初これを計算機の queue 混雑と誤診断した。** 待ち行列を見て投げ直す運用で完走させたが、
一次資料を読み直すと **F148 / F149 の再発**である。変異適用中の tree は必ず dirty なので、
`run_tests.py` の local 試行から dispatch への fallback が「tree が clean なら」の条件で拒否され、
receipt 行が出ないまま止まる。**混雑は相関であって原因ではない** — 待ち 142 件のままでも
完走した走行がある。恒久策は `mutation_harness` が D209 決定 10 の `--force-dispatch` を
渡すことで、本 wave の scope 外として新規 task に起票した。

## 段 3 / 段 6 の所見の扱い

段 3 は両レンズが段 5 進行 **NO-GO** を返した。親は「縮小して GO」と裁定した (`verbatim/s4-ruling.md`)。
閉じ方は 4 つ。(a) 大域 `git worktree prune` を廃止して自分の admin dir だけを消す、
(b) lock を `--out` へ束縛して同一台帳の後勝ち上書きを塞ぐ、(c) dispatch evidence の退避と
未完了 container の保持、(d) 「必須化」と「§9.1 充足」の主張を縮める。
残る blocker (機械 admission、legacy drain、実行場所分類) は harness 改変か人間手番を要するため
scope 外とし、裁定パッケージへ回した。

段 3 の A-2 (「64 テストからの一般化は破れる」) は上表の全走一致で **refuted**。
A-8 / B-13 (段 1 probe に `pipefail` が無く報告 rc が `tail` の rc だった) は **real** であり、
pipe を外して測り直した。

段 6 は must-fix 18 件。対応は closed 20 / backlog 2 / regressed 0 (`verbatim/s6-fix.md` の対応表)。
主な型は**テストが helper を直接呼ぶだけで本番の結線を検査しておらず、事前登録した変異を
殺せない**こと (MW-05 / 09 / 11 / 12 / 14)。fix 後は `main` を通す形へ作り直した。

## 裁定パッケージ (ユーザーへ返す)

| # | 軸 | 選択肢 | 親の推奨 |
|---|---|---|---|
| V-7 | 旧 direct 経路の閉じ方 | (a) harness に isolation admission を足し legacy drain receipt と consumer 拒否まで含む activation package を次 slice で作る / (b) prose-only の既定手段のままにする / (c) shadow prototype と位置づけ活性化を L-B 実機受入まで凍結する | **(a)** を独立 wave として。本 slice は (c) の位置づけで land した |
| V-8 | `tools/mutation_worktree.py` の実行場所分類 | (a) ユーザー端末で cgroup charged memory を実測して確定する / (b) 測らず `unknown` = `dispatch-required` のまま運用する | **(a)**。測るまでは (b) で安全側に倒す |
| V-9 | 未完了 container の retention | (a) 手動削除と `--resume` のみ (本 slice の実装) / (b) owner record + exclusive lock による自動 GC を次 slice で作る | **(a)**。実残骸 path を観測してから (b) を設計する (`DW-G04`) |

## この wave が主張しないこと

- 段 3 の NO-GO が誤っていたとは主張しない。指摘の大半は real であり、設計変更と主張の縮小で閉じた。
- 使い捨て worktree 方式が journal 方式より優れているとも主張しない。本 slice が示したのは
  「共有木を触らない」という一点だけである。
- 変異 matrix の MISMATCH 5 件を「実質 KILLED」と数え直してはいない。台帳の値は台帳のままである。
