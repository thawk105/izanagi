単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2

必読事項の射影 (いずれも絶対パス。読めなければ即停止し、その旨を出力に書いて終わること):

- 作業 root (read-only): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2`
- **裁定 2 の原文 (本相談の主題)**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c2-derivation/ruling-package.md`
- **契約の正本**: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md`
- 契約の追記訂正: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c2-derivation/contract-v3.1-erratum-1.md`
- 直前単位 C2 の記録: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-08_t1851-unit-c2-derivation/README.md`
- 6 単位分割の正本: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-01_t1946-t2107-registry-wiring-design/s4-adjudication-r2.md`
- 同 wave の README: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/insights/2026-09-01_t1946-t2107-registry-wiring-design/README.md`
- 裁定台帳: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/decisions.md` (D1341, D1660, D1661, D1675, D1703 を引くこと)
- 共通規律: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/CLAUDE.md`

# 段 consult — [T-1851] 次に走らせる単位を 1 つ選ぶ

作業 root は read-only である。**書込み可能な tmp は無い。** したがって
**pytest 緑を要求しない。静的読解と grep による実測だけで結論を出す。**
テストの実走は親が行う。**走らせていないものを緑と書かないこと。**

**file を 1 つも作れない。** 成果物は**最終メッセージの本文へ全文を書く**こと。
「file へ書いた」と述べても親には届かない。

予算が尽きそうなら、**途中結論を下の出力形式どおりに書いて終わること** (無出力が最悪)。

## ユーザーの指示 (逐語)

> [T-1851] 単位 D2 ... など、裁定 2 の結論に沿って単位を選んでください。branch
>     worktree-dev-wave-t1851-unit-c2 を継承します。
> 判断に迷うところはcodexに相談して決めてください

単位の選択はユーザーが親へ委任し、迷う点は codex へ諮ると明示している。**本相談がその諮りである。**

## 親が実測した事実 (2026-09-09 07:10 JST)

- 継承 branch `worktree-dev-wave-t1851-unit-c2` の tip は `38aed135f`。
  local main は `cbcdb6c91` で、branch より 115 commit 先。
- branch 上で済んでいる単位 (commit subject の実測): B1、A1'、A2α、A2β、
  B2 / D1 の非 terminal 部分、C1a、C1b、C2。
- 未済: 裁定 2 の (a) が新設を提案する C3 (配線 + 実値域)、および D2 (consumers/fixtures)。
- **裁定 1・裁定 2 に対するユーザー裁定は `docs/decisions.md` に未記録**
  (親が `grep` で 0 件を確認)。C2 wave 自身が D1341 により未 land だからである。
- local main の取り込みは競合 2 件で止まる:
  `orchestrator/tests/acceptance_duration_ledger.json` (53 hunk) と
  `orchestrator/tests/test_backoff_extended_sweep.py` (1 hunk)。先例では codex author 子が解く。

## 問い

**次に走らせる単位を 1 つ選び、その根拠を書け。** 候補は少なくとも次の 2 つで、他案があれば挙げてよい。

- **C3** — 裁定 2 (a) が新設を提案する単位。`launch_floor_attempt()` を production の呼び手へ配線し、
  契約 9 節が要求する「実環境の値域」を供給する。C2 の README 5 節は見積りを
  「5 file / 350-550 行、7-key schema が先に無いと組めない」と書いている。
- **D2** — 6 単位分割の最後の単位 (consumers/fixtures)。

判断で必ず扱うこと:

1. **依存順。** 契約 9 節と 6 単位分割の依存順から、C3 と D2 の間に強制順序があるか。
   あるなら根拠 file:line を示せ。
2. **1 wave に収まるか。** 選ぶ単位の実装面 (file・行数・test node) を静的に見積もれ。
   収まらないなら、収まる下位単位への割り方を提案せよ。
3. **実測の要否。** 「実環境の値域」を供給するのに、計算ノードでの実 campaign 走行が要るか、
   それとも既存の記録済み成果物・fake でない producer 経路で足りるか。
   要るなら何をどこで測るのかを書け。**要らないと言うなら、その根拠を file:line で示せ。**
4. **裁定 2 が未記録である影響。** ユーザー裁定が decisions.md に無い状態で C3 を新設単位として
   走らせてよいか。親の provisional 裁定として進めて後で追認する形が D1341 / D1703 と整合するか。
5. **反対意見。** 自分の推奨に対する最強の反論を 1 つ書き、それでも推奨を変えない理由を書け。

## 禁止

- **実装しない。** patch も diff も出さない。file を作らない。commit しない。
- 走らせていない test を緑と書かない。読解で得た事実と実測で得た事実を区別して書く。
- 正しさゲートを緩める方向 (検証を甘くして先へ進む) の提案をしない。
- 契約・裁定の本文を書き換える提案を「親の独断で実施できる」と書かない。単位分割はユーザー裁定の対象である。

## 出力形式

```
## 総括
(3-5 行。選んだ単位と、その 1 行根拠)

## 依存順の実測
(file:line つき)

## 選んだ単位の scope 境界
(実装面の file と概算行数、test node の目安)

## 実測の要否
(要る / 要らない と、その根拠)

## 裁定未記録の扱い
(D1341 / D1703 との整合)

## 最強の反論と応答

## 却下した案
```
