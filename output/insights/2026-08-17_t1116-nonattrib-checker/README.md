# [T-1116] 受入の非帰属 checker — 8a2b735b は checker 層だけを直し、消費層を取り残していた

wave: `dev-wave-t1116-nonattrib-checker` / 2026-08-17 / branch
`worktree-dev-wave-t1116-nonattrib-checker` / base `7c83eeac`

## この材料が答えたこと

依頼は「commit `8a2b735b` が [T-1116] 裁定 (択 2) とユーザー裁定 R2 をどこまで果たしたかを
実測で確定し、残る穴を閉じる」であった。

**結論: checker 層だけを果たし、end-to-end では 1 mm も果たしていない。**
したがって台帳は終端できない。穴を閉じる = 受理集合を広げることであり、独立 2 レンズが
別々の根拠で NO-GO に到達したため、`DW-S04` に従い**実装せず裁定パッケージへ返した**。

## 実測 1 — checker 層は直っている (本 wave の一次資料)

2026-08-15 に旧 checker が `attributable` と判定して受入全走 1 本を捨てた**実履歴の log**
(`dev-wave-jobs/dev-wave-t989-t932-snapshot-cost/acceptance-child-2.log`) を、
現 main の `tools/check_acceptance_reds.py` へかけ直した。

- node: `orchestrator/tests/test_dev_wave_wait.py::test_public_main_real_signal_after_success_uses_restored_handler`
- 結果: `classification=flake` (`main_rerun_rc=0` / `wave_rerun_rc=0`)、
  status `non-attributable-only`、rc=0
- 受領証: `probe2-receipt.json` (本 directory)

**この実測の限定**: `--tested-main` と `--wave-tip` に同一 SHA を渡しているため、
両 probe は同じ tree を別 worktree で走らせただけである。
「現 checker が実履歴の signal 赤を `flake` に分類する」ことの証拠であって、
実運用 (両者が異なる) での分類差の証拠ではない。

## 実測 2 — 消費層が取り残されている (穴の所在)

`tools/dev_wave_wait.py:2803-2812` は checker 受領証の**全 node** に次を要求する。

    set(node) == {"classification", "nodeid", "rerun_rc"}
    node["classification"] == "non-attributable"

`flake` node は 5 field (`classification` / `main_rerun_rc` / `nodeid` / `rerun_rc` /
`wave_rerun_rc`) なので `_StageFailure` になり、**受領証は発行されない**。
実測: 上記 `probe2-receipt.json` の node を同述語にかけて REJECT。

裏付け: 文字列 `flake` の出現数は
`tools/dev_wave_wait.py` = 0、`tools/dev_wave_land.py` = 0、
`orchestrator/tests/test_dev_wave_wait.py` = 0、`orchestrator/tests/test_dev_wave_land.py` = 0。
`8a2b735b` が変更した file は `tools/check_acceptance_reds.py` と
`orchestrator/tests/test_check_acceptance_reds.py` の 2 本だけである。

**したがってユーザー裁定 R2「確率的なフレークで受入全走を何度も無駄にする構造は
全てのセッションに対して許さない」は一度も発効していない。**
`8a2b735b` の commit body は「既存の呼び手は壊れない」を root field と `--wave-tip` flag だけで
確認しており、node 形の exact 検査を見落としている。規律 6 が監査発火条件に挙げる
**consumer 取り残し**の型である。

## 実測 3 — 受入証拠の連鎖は checker 以外すべて wave tip の自己証明である (新規・重大)

[T-1131] は非帰属判定の**実行体**を tested main へ束縛した。しかし隣接 2 層は束縛されていない。

| 層 | 待ち手側の検査 | land 側の検査 | main と照合するか |
|---|---|---|---|
| `tools/check_acceptance_reds.py` | `_verified_red_checker_source` が main blob と tip blob の一致を要求 (`tools/dev_wave_wait.py:1975-1985`) | `tested_main:` と `tested_tip:` の blob 一致 (`tools/dev_wave_land.py:647-680`) | **する** |
| `tools/dev_wave_wait.py` | `_verify_waiter_source_bytes` は running bytes と **tip** blob の一致だけ (`tools/dev_wave_wait.py:1584-1663`) | receipt の `waiter_blob_sha` と `tested_tip:` の一致だけ | **しない** |
| `tools/run_tests.py` | — | `tested_tip:` に存在することだけ (`cat-file -e`) | **しない** |

したがって wave は待ち手または runner を書き換えるだけで、実 child rc=1 を
`child_rc=0 / verdict=child-green` として land できる。
**[T-1131] が塞いだ穴と同型が、隣接する 2 層で開いたままである。**

## 実測 4 — (P3)「test file 非接触」は非帰属の十分条件ではない

親 brief が第一候補にした「`tested_main..wave_tip` の差分が当該 node の test file を
触っていないなら `flake`」は、段 3 の 2 レンズが独立に反証した。
production code / `conftest.py` / 共有 fixture / pytest plugin のいずれかだけを変更しても、
全走限定の赤を作れる。単独再走は main / wave tip 双方で緑になるので `flake` のままである。

親が最初に出した「過去 89 赤のうち接触は 4 件 (4.5%) なので R2 の救済の 95.5% が残る」は
**撤回した**。分母 89 は旧 checker の分類であり、wave 単独 rc を 1 件も測っていないため、
85 件が `flake` になるとは言えない。**支持されるのは上界だけである** —
(P3) は 89 件のうち最大 4 件にしか作用しない。

## 親自身の誤りとして訂正した点

1. 親 brief (P2)「残る穴は `flake` の過剰受理」は**向きが逆**だった。
   全 flake が消費層で拒否される以上、過剰受理は成立しえない。正しい問題は**過少受理**であり、
   R2 が一度も発効していないことである。段 2 プランが指摘し、親が独立に実測して確認した。
2. 「95.5% が救済される」は無根拠だった (上記)。段 3 レンズ A が指摘し、親が撤回した。

## 一次資料

- `probe2-receipt.json` — 実運用で出た唯一の `flake` 受領証
- `verbatim/brief.md` — 親 brief (末尾の「brief v2」節が訂正後の前提)
- `verbatim/s2-plan.md` — 段 2 プラン (消費層の取り残しを最初に指摘)
- `verbatim/s3-lensA.md` / `verbatim/s3-lensB.md` — 段 3 敵対 2 レンズ (双方 NO-GO)
- `verbatim/s4-adjudication.md` — 段 4 裁定と裁定パッケージ全文
- `ruling-package.md` — ユーザーへ返す 4 択

## レンズと所見の数

段 3 = 2 レンズ。所見 15 件のうち **real 14 / nit 1 / refuted 0**。
親 brief 側の誤り 2 件はどちらもレンズが正しく、親が撤回した。
