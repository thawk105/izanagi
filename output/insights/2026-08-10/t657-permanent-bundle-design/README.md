# [T-657] 較正と凍結の権限束 — 恒久設計を起票した (2026-08-10)

wave = `dev-wave-t657-permanent-bundle-design` /
branch = `worktree-dev-wave-t657-permanent-bundle-design` / 起点 main = `81249ca2`。
親の裁定要約は worklog の該当エントリ。

## 射程 (これを越える引用を禁じる)

本 wave は **実装差分ゼロの設計起票 wave** である。land したのは設計文書と逐語だけで、
**権限束の resolver も、環境候補の record も、consumer の移行も 1 行も実装していない。**

- 「[T-657] が解決した」と書いてはならない。したのは**制約と択一の確定**だけである。
- 設計の正本は `docs/calibration-freeze-authority-bundle-design.md` (第 1 設計段、裁定待ち)。
  同書 §12 が未裁定の一覧であり、**§12 が閉じるまで実装 wave の開始条件は成立しない。**
- **pegasus 第 2 世代は `registered-inactive` のまま**であり、本 wave は活性化していない。
- 旧 branch `worktree-dev-wave-t657-t660-g2-activation` は **merge していない**。
- floor protocol の復元は**ユーザー確認のみの手番**であり、本 wave は実行していない
  (手順は `output/insights/2026-08-10_t657-restore-redesign/restore-floor-protocol.md`)。

## 成果物

- 設計正本は repo の `docs/calibration-freeze-authority-bundle-design.md` (本 dir には複製しない)。
- `verbatim/s1-brief.md` — 段 1 brief (provisional 裁定 P1〜P3、実測 M1〜M5)
- `verbatim/s2-plan.md` — 段 2 codex プラン (sol / max / read-only、rc=0)
- `verbatim/s3-lensA.md` — 段 3 レンズ A / 恒久機構の成立性 (sol / max、**NO-GO**、real 10)
- `verbatim/s3-lensB.md` — 段 3 レンズ B / 先送りの漏れと実装したふり (luna / max、**NO-GO**、real 10)
- `verbatim/s4-adjudication.md` — 段 4 親裁定 (採用 13 / ユーザー裁定へ返す 4 / refuted 6)
- `verbatim/s6-lens1.md` — 段 6 レビュー 1 / 所見の反映と恒真 (sol / max、**NO-GO**、must-fix 7)
- `verbatim/s6-lens2.md` — 段 6 レビュー 2 / 裁定違反と正本二重化 (sol / max、**NO-GO**、must-fix 12)
- `verbatim/s6-refocus1.md` — 焦点再レビュー 1 巡目 (対応表。closed 10 / partial 7、残 must-fix 9)
- `verbatim/s6-refocus2.md` — 同 2 巡目 (luna。型 1=2 / 型 2=3 / 型 3=1)
- `verbatim/s6-refocus3.md` — 同 3 巡目 (**型 1 = 0 件**。残 3 件は親裁定で本文修正して閉じた)

## この wave が実際に変えたもの

1. 親 brief の前提 2 件を段 3 が反証した。(a)「承認と pointer が同一 commit」は**現行実装の事実**で
   あって恒久設計の制約ではない (承認済み第 2 設計段は既に別 commit と規定)。(b)「有効 head の
   literal 除去が必須」は成立しない (literal を残す topology の反例が構成された)。
2. 親の当初方針「凍結側正本を一切改訂しない」を撤回した。敵対レンズ 2 本が独立に正本二重化の
   経路を構成したため (`DW-G03`)。R1..R16 本文は変えず、適用範囲と precedence の注記だけ追記した。
3. 初版の**虚偽を 1 件除いた** — 「束の識別子を持たない成果物の拒否」を「保存すべき既存の拒否」と
   書いていたが、現行ではそれが正常な形である。新設側へ訂正した。

## 引用時の注意

- レビュー本文の file:line は**本 wave 時点の worktree 上の値**である。実装 wave で再確認すること。
- 逐語中の絶対 path は wave 実行時の作業 dir を指す。repo 内の相対 path として読み替えないこと。
- 段 3 / 段 6 の指摘のうち親が **refuted** と裁定したものは `verbatim/s4-adjudication.md` §3 と
  `verbatim/s6-refocus3.md` にある。real として引かないこと。
