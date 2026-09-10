# 段 1 brief v2 — dev-wave-red-suite-20260809

v1 (`s1-brief.md`) の前提 1 件が段 3 で refuted されたため改訂する。**v1 の (P1)(P2) と
不変条件 4 は無効。** 赤の全数調査・実測・並行所有の節は v1 のまま有効。

## v1 からの訂正

- **訂正 1 (B-08、blocker)**: 「DW-O09/DW-O10 は成立しない」は**誤り**。
  `prepare_revision` は `s8c_preregistration.py:1688` で `validate_condition_freeze_at` を呼び、
  その成功後に `:1713-1725` で `gN.json` を exclusive-create して書く。
  旧 `git-timeout` が新実装で通れば**旧来作られなかった generation が作られうる**。
  よって validator の受理集合に触る案は凍結成果物の producer write path に到達する。
- **訂正 2 (A-所見 3)**: 親の外挿「3 path で約 2 秒」「10,000 commit で約 9 秒」は
  **refuted**。warm・login node・単一 path の線形外挿である。
  real なのは直接観測 (全走負荷下で 15 秒超) と、cardinality が `commits × paths` であることだけ。
- **訂正 3 (A-所見 1、B-01/B-07)**: 段 2 プラン (chunk 分割 + 旧 invocation ごと 15 秒据え置き) は
  **赤を閉じない**。両レンズとも NO-GO。段 5 へ渡さない。

## 段 3 で確定した 4 案の評価

| 案 | 内容 | レンズ A | レンズ B | 判定 |
|---|---|---|---|---|
| 段 2 案 | chunk 分割 + 総締切 15 秒据え置き | 第 3 位 (赤を閉じない) | NO-GO (framing reason code が変わる等) | **棄却** |
| B | `validate_condition_freeze_at` に timeout 引数を足しテストが 180 秒を渡す | **Critical・最下位** (public 迂回口) | B-14 refuted / B-15 real (無制限なら opt-out) | **棄却** (A の Critical を採る) |
| C | 要求数から内部算出する上限付き比例予算 | **第 1 推奨 (条件付き)** | 択一として親へ | **ユーザー裁定へ回す** |
| D | 台帳へ 7 回目の再発を追記して終端 | 第 2 推奨 (停止案) | — | C の裁定が下りるまでの既定 |

C が裁定を要する理由: (i) `B(R) > 15` の領域で従来 reject された実行が成功するため
**wall-clock 受理集合が明確に広がる**、(ii) 訂正 1 により**凍結成果物の生成条件が変わりうる**。
どちらも親が単独で決めてよい範囲を超える。

## v2 の scope — 案 E だけを実装対象にする

**案 E: production を 1 byte も変えず、実 repo invariant テストだけが
一過性の `git-timeout` を吸収する。**

- production の `GIT_TIMEOUT_SECONDS = 15.0`、`validate_condition_freeze_at` の signature、
  reason code、受理集合、`prepare_revision` の write path — **すべて不変**。
  よって訂正 1 の DW-O09/O10 は「到達しない」ことが構造的に保証される (production 差分ゼロ)。
- 代案 B との違い: production API に引数を**足さない**。したがって A の Critical
  (public 迂回口)、B-15 (無制限 timeout) はいずれも構造的に成立しない。
- F57 の明示方針「production wall-clock gate を緩めず **test fixture を harden する**」に
  文字どおり従う唯一の案であり、先例 [T-327] と同型である。

## 親の provisional 裁定 (v2、攻撃対象)

- **(Q1)** 吸収の形は「同一 assert を保ったまま、`PreregistrationError("git-timeout")`
  **に限って**有限回だけ再試行する」。他の reason code は 1 度で赤にする。
- **(Q2)** 再試行は**確率的な緩和**であって根治ではない。再試行間に短い待機を挟んでも
  競合は自己相関するため、残存確率はゼロにならない。この事実を worklog へ明記する。
- **(Q3)** 恒常的に 15 秒を超える状態 (履歴成長による真の劣化) は**検出力を保つ** —
  全試行が timeout すれば赤になる。ここが「テストを甘くする」との分界線である。
- **(Q4)** 再試行回数と待機は定数とし、環境変数・CLI で外から変えられるようにしない。
- **(Q5)** E は [T-553] を**閉じない**。C の裁定が下りるまでの緩和であり、
  worklog と failures には「緩和であって恒久対応ではない」と書く。

## 不変条件 (v2)

1. `orchestrator/campaign/s8c_preregistration.py` を**編集しない** (production 差分ゼロ)。
2. テストの assert を 1 つも削除・反転・緩和しない。`xfail` / `skip` を使わない。
3. 恒常的 timeout は赤のままにする (規律 2 の分界線)。
4. 実装面は Codex `role=author` が書く。親は直接編集しない。

## 成果物影響 (DW-G05)

E を実装しない場合: 受入全走は次回以降も約 20% の頻度で 1 failed となり
(台帳既載 6 回 / 概ね 30 走)、land 前受入の再走に 1 走 20〜25 分が積み上がる。
段 8c の発効判定そのものは E では改善しない (C の裁定事項)。
