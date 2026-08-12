# [T-725] + [T-694] — 受入 lease 待ち手の安全配線を閉じた wave の一次資料

branch `worktree-dev-wave-t725-t694-lease-clean`、統合 commit は worklog エントリを参照。
台帳の正本は `docs/worklog.md` の該当エントリで、ここは逐語と機械可読な台帳だけを置く。

## 何をした wave か

2026-08-12 の一括裁定 45 件のうち [T-725] (受入 lease 取得後の behind main を待ち手内
`--no-ff` merge で解消してよい + 安全配線 3 点必須) と [T-694] (待ち手を `tools/` の正本
wrapper にする) を実装する wave として起票された。

**着手時の実測で、両項の実体は [T-732] / [T-740] として 2026-08-10 に裁定され、
2026-08-11 に main へ land 済みであることが判明した。** 裁定は止めず、`docs/failures.md` の
F191 が定める「安全配線 3 点」と `tools/dev_wave_wait.py` の実装を逐条照合し、
**未充足だった 2 点だけ**を実装した。

- 点 2 (provenance preflight): `check_ai_provenance.py --message-file` を merge の後・
  commit の前に通す段 (`stage=merge-message-provenance`) を新設した。
- 点 3b (走行前の clean 検査): 受入 command 投入の直前に木が clean であることを確認する段
  (`stage=prerun-clean`) を新設した。

## ファイル

- `verbatim/` — 段 1〜6 の子の出力をそのまま凍結したもの。
  - `s1-brief.md` 親 brief (段 4・段 6 で 6 箇所が撤回・訂正されている。撤回内容は
    `s4-adjudication.md` の「撤回する親 brief の主張」節と worklog が正本)
  - `s2-plan.md` 段 2 プラン (codex plan、reasoning=max、read-only)
  - `s3-lensA.md` / `s3-lensB.md` 段 3 敵対相談 (sol / luna、reasoning=max、read-only)
  - `s4-adjudication.md` 段 4 裁定 (親。実測 E1〜E7 と変異事前登録 M1〜M6、裁定パッケージ 4 束)
  - `s5-impl.md` 段 5 実装子の報告 (codex author、reasoning=high、workspace-write)
  - `s6-revA.md` / `s6-revB.md` 段 6 敵対レビュー 2 本 (codex review、read-only)
  - `s6-fix1.md` 段 6 fix 子の報告と所見対応表
- `mutation-spec.json` — **本走 (2 走目) の spec**。期待 node は完全集合。
- `mutation-ledger.json` — 本走の台帳。**6/6 KILLED、SURVIVED 0、MISMATCH 0**、baseline 緑。
- `mutation-spec-round1.json` / `mutation-ledger-round1-erratum.json` — **1 走目の erratum**。

## 変異 1 走目の erratum (DW-M02)

1 走目は M3 / M4 / M5 / M6 の 4 件が MISMATCH だった。**変異はすべて検出されており
(SURVIVED 0)**、原因は親が事前登録した期待 node が実測失敗集合の**部分集合**だったことである。
`orchestrator/tests/test_dev_wave_wait.py` の `_FakeEffects` は登録した argv 列を exact に
照合するため、共有 argv を変える変異は焦点テスト以外も広く赤にする (M3 = 60 件、M6 = 20 件)。

[T-709] が 2026-08-12 に裁定した「部分集合一致 (期待 node が実測失敗集合に含まれる) の判定枠」は
`tools/mutation_harness.py` に**未実装**であることを実測したため、**事前登録 node が全 6 変異で
実測失敗集合に含まれることを機械検査したうえで**完全集合を再導出し、2 走目を走らせた。
1 走目の台帳は消さずここに凍結してある。

## この wave が保証しないこと (正直形)

`prerun-clean` が保証するのは「`git status` を実行したその時点で tracked 木が HEAD と
一致していた」ことだけである。20〜40 分走る受入 command の**走行中**に入った変更は覆わない。
また述語は `--untracked-files=no --ignore-submodules=none` であり、**untracked は拒否しない**。
どちらも裁定パッケージへ返した (worklog の新規 4 項)。
