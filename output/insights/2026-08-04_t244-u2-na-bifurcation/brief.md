# 段 1 brief — [T-244] U2: D121 決定 (7) の「非適用」を二分する

> **erratum (段 4 で訂正):** 下記「前提実測」の **(3) 択一 3 は未裁定** は**誤り**である。
> 択一 3 は 2026-08-03 (126) で「必須にする」と裁定済みで
> (`docs/archive/worklog-phase3-0803-125-126.md:322`)、その帰結として P4 は無条件義務へ移る。
> よって親の provisional (P1) の三分と (P4) の実効性条項は撤回した。詳細は `s4-adjudication.md` §1。
> 本文は当時の記録として残す。

**scope:** 新 D を 1 本書く (docs のみ)。D121 決定 (7) の一文「(iii) を採らない場合の P4、座標 cut を
主張しない場合の P6 は**非適用**として扱い、cap-lift の失敗には数えない」だけを supersede し、
非適用を「免責される種」と「FAIL とする種」へ二分する。10 件の前提条件列挙、無条件義務の集合、
P8 の射程、D121 の他の決定は変えない。fold は既存 D を改変できないため supersede 範囲を新 D 本文に書く。

**確定済みユーザー裁定 (worklog (153) U2):** 「主張しないゆえの非適用」だけを免責し、「実装が無いゆえの
非適用」は FAIL とする。cap 永久解除不能の懸念はこの二分で回避される。改訂は実装 wave が新 D で書く。

**前提実測 (段 1 前):** (1) D121 決定 (7) を改訂した D は存在しない (`grep -n D121 docs/decisions.md`
= 5781/6720/6733/6764 のみ、6764 は D138 決定 (5))。U2 は未実装。(2) cap-lift に機械 gate は無い —
`MAX_APPROVED_GENERATIONS = 1` 定数と `>` validator だけで、P1〜P10 の判定器は存在しない。
(3) 択一 3 (軸 (iii) の扱い) は未裁定 (D121 決定 (2) が裁定へ返して以降、裁定記録なし)。
(4) `docs/decisions.md` は `FROZEN_MANIFEST` に無く byte pin されていない (`check_docs.py` の
budget 対象外・D 見出し一意性のみ、`test_hooks.py` の閾値は追記で不変)。(5) D138 決定 (5) が
`NOT_IMPLEMENTED`=FAIL / `NOT_CLAIMED`=免責を P6 文脈で既に定式化済み。本 wave はこれを条件付き義務
一般へ広げて確定させる。

**親の provisional 裁定 (攻撃対象):**
- **(P1)** 二分では足りず三分が要る。`NOT_TRIGGERED_BY_RULING` (発火条件の否定が cap-lift 申請
  より前の独立裁定で固定) / `NOT_CLAIMED` (機構は実装・検査済みだがこの運転では主張しない) は免責、
  `NOT_IMPLEMENTED` (主張できない理由が契約の未実装) は FAIL。二分のまま P4 へ適用すると、軸 (iii) を
  採らない構成にも batch-freeze の実装を要求し、D121 が避けた「cap 永久解除不能」を再導入する。
- **(P2)** 判定子は「機構の実在 witness」= 実装 path + それを固定する検査 ID の対。提示できなければ
  `NOT_IMPLEMENTED`。witness の中身の妥当性は本 D で定義せず P6 契約 (D138 決定 (3)) に委ねる。
- **(P3)** 宣言なし・根拠不足・依存する択一が未裁定なら判定保留とせず FAIL (fail-closed)。よって
  現時点で P6 は `NOT_IMPLEMENTED`、P4 は択一 3 未裁定ゆえ免責を主張できない。
- **(P4)** (P1) の第三種は新しい穴を開ける — 「座標 cut は採らない」と裁定すれば P6 が免責され、
  D138 決定 (1) により還流の限界効果がゼロのまま cap が解除できる。免責後に残る義務集合が
  「還流の実効性 > 0」を支えることを免責の条件に加えて塞ぐ。塞げなければ裁定パッケージへ返す。

**`DW-O13` (gate 入力の実在):** cap-lift 申請は実成果物として存在せず、判定入力を持つ field は
1 つも無い。よって本 D は人間 gate の判定規則であり機械 gate を作らない。識別子は D138 決定 (5) の
`NOT_IMPLEMENTED` / `NOT_CLAIMED` を継承し、第三種は変異 matrix の観測値 `NOT_APPLICABLE`
(`output/insights/2026-07-29_t145-join-dichotomy-wave/`) と二義化しないよう
`NOT_TRIGGERED_BY_RULING` とする。

**不変条件:** `MAX_APPROVED_GENERATIONS = 1` を変えない。cap-lift を結線しない。機械 gate を新設しない
(`DW-G04`: 発火 artifact が 1 件も書けない。本 D は人間 gate の判定規則であり、D121 決定 (7) 自身が
「10 件すべてが機械検査可能とは主張しない」と書いている)。`docs/phase3-main-experiment.md` を変えない
(S-1 freeze が bytes を pin)。canonical 3 台帳を直接編集せず `docs/spool/` fragment で書く。
コード・テストを変更しない (実装面ゼロ → 段 5 の Codex 実装子なし、変異 matrix は対象外)。

**成果物影響 (`DW-G05`):** 放置すると、P6 を 1 行も実装しないまま「非適用」宣言だけで
`MAX_APPROVED_GENERATIONS > 1` が承認され、多世代 campaign が試行台帳の行数と certified 選択の探索
範囲を変える一方、proof chain は実体のない `P6=NA` を参照する。すなわち受理集合が「還流ゼロなのに
多世代」へ広がる。

**成果物の形:** `docs/spool/decisions/` に fragment 1 本 (新 D)、`docs/spool/worklog/` に fragment 1 本。
逐語は `output/insights/2026-08-04_t244-u2-na-bifurcation/`。

**受入環境:** 計測なし。login ノードで `python3 tools/check_docs.py` と docs 影響テスト
(`tools/run_tests.py` の受入形) を走らせる。

**分割方針:** 段 2 = codex plan 1 本。段 3 = 2 レンズ (A: 恒真化・迂回経路・宣言の自己申告性、
B: 過剰拘束・cap 永久解除不能の再導入・P4 側の非対称性)。段 5 = 親が docs 本文を書く。
段 6 = codex 敵対レビュー 2 本。
