---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-17
wave: dev-wave-t987-floor-rebind
seq: 1
title: 床値 v2 の束縛緩和は目的を達成できないと実測し、実装せず裁定パッケージへ返した — 阻んでいるのは緩和対象の束縛ではなく未裁定の official 承認束縛方式と再凍結 consumer だった (docs、branch worktree-dev-wave-t987-floor-rebind)
---

## 本文

[T-987] の確定済み裁定 (2026-08-16 /rulings 全件 第 3 回) は「再測定は世代移行 wave と同一
chain でのみ実施する」という条件を記録基準へ緩めよと定めていた。段 1〜4 を回した結果、
**そのとおり実装しても裁定の目的 (現 gitlink で床値を再測定して v2 を作る) は達成できず、
実施すると下流 [T-750] を後退させる**ことが実測で確定したため、実装せず段 4 で
裁定パッケージへ返した。実装差分ゼロ。

**裁定が閂として挙げた 2 点は、裁定時点で既に成立していなかった。**

- 「sanctioned な発行経路が存在しない ([T-478] (d))」は偽。AI 再封印 issuer が
  `orchestrator/campaign/s8b_floor_campaign.py` に実在し (commit 230fc757、2026-08-16 14:27 JST)、
  `reseal-protocol` CLI サブコマンドから実行できる。
- 「待つ相手が保留確定の機構であり事実上の無期限凍結になる」も偽。待つ相手である世代移行は
  2026-08-17 08:16 以降のユーザー指示で稼働中であり (wave `dev-wave-t657-activation-rebuild`)、
  target pair (`1346c20b`, `511c9538`) まで算出済みで未発行なだけだった。

**束縛の実体は台帳の文言ではなくコードであり、層は 4 つある。** 実測 (親 + 段 3 敵対 2 レンズが
独立に確認):

1. protocol 解決 — 世代移行なしに再封印すると候補が 2 件になり
   `resolve_current_floor_protocol()` が `count=2` で拒否する。既存テスト
   `orchestrator/tests/test_s8b_protocol_builder.py` の
   `test_current_floor_protocol_resolver_rejects_two_current_contract_matches` が
   まさに再封印後の状態を組み立てて pin している。
2. holdout 受入 — `orchestrator/campaign/s8b_holdout_admission.py` の `_authority()` が
   固定 legacy path の HEAD blob と渡された protocol の byte 一致を要求する。
   世代移行が着地しても解消しない (両レンズが独立に blocker 判定)。
3. **official mode の無条件拒否** — `s8b_floor_campaign.py` の `_assert_official_permitted()`
   が「§8 (承認束縛方式) 未裁定」を理由に core で拒否する。**これはユーザー裁定待ちであり、
   [T-987] が緩めよと裁定された束縛ではない。**
4. **v2 再凍結 consumer** — `orchestrator/campaign/s8b_holdout_freeze.py` の
   `_validate_floor_inputs()` が固定 legacy protocol を読み、result に `mode == "official"`、
   `eligible_for_refreeze is True`、`protocol_sha256` 一致を要求する。
   pilot の result も versioned protocol で測った result も必ず落ちる。

層 3・4 により、**束縛を記録基準へ緩めても v2 は作れない**。さらに
`s8b_holdout_admission._key_fields()` は key に `mode` を含まないため、新 pin で pilot を
1 度成功させると将来 official が必要とする one-shot key を先に焼く — 裁定どおり実施すると
[T-750] (床値 v2 実凍結) を不可逆に後退させる。

段 2 プランは「専用の記録付き再測定 lane」(production 9 file、環境変数 marker で受入経路を切替)
を提案したが、段 3 レンズ A が **NO-GO** を返した (blocker 5 件)。うち決定的なのは
「versioned protocol の測定結果を受け取る v2 consumer が存在しない」= 消費者のいない producer を
作ることになる、という所見である。レンズ B は wave 存続を支持しつつ、記録を足すだけでは
fail-closed にならない・記録が成果物へ束縛されない・記録入力が第三者再構成に不足、を blocker /
must-fix で挙げた。両レンズの所見は段 4 で全件 real 裁定した。

**親の実測 1 件を誤りとして取り下げた。** 「`reseal_protocol()` の production caller はゼロ」は
偽で、原因は親の grep が `grep -v "^orchestrator/campaign/s8b_floor_campaign.py"` により
同一 file 内の CLI dispatcher を自分で除外していたこと。段 3 レンズ B が refuted し、親が
再確認して確定した。F370 と同型のため同エントリへ再発として記録する。

逐語一式 (brief / plan / lensA / lensB / 裁定 / 親の実測 / 親の対案) =
`output/insights/2026-08-17_t987-floor-rebind/`。

段 8 の自己改善は候補 1 件を検出したが、段構成の義務を変える変更にあたるため
`docs/skill-self-improvement.md` の「段構成…の変更は実装せず裁定パッケージへ送る」に従い
実装せず新規タスクとして起票した (下記)。dev-wave docs は編集していない。

## 次の一手差分

### 更新

- [T-987] **P1・ユーザー裁定待ち (2026-08-17、束縛緩和では目的を達成できないと実測)**:
  2026-08-16 第 3 回の裁定 (条件を記録基準へ緩める) は、そのとおり実装しても
  「現 gitlink で床値を再測定して v2 を作る」を達成しない。阻んでいるのは緩和対象の束縛ではなく、
  (3) official mode の無条件拒否 (理由 = §8 承認束縛方式が未裁定) と
  (4) v2 再凍結 consumer の固定 legacy protocol 束縛である。さらに one-shot key に `mode` が
  入らないため、裁定どおり pilot を実施すると [T-750] が必要とする権利を焼く。
  裁定が閂とした前提 2 点 (発行経路の不在・待ち相手の無期限凍結) はいずれも実測で偽。
  **問**: 床値 v2 を実在させるにはどれを開くか。
  **択 (α)** §8 承認束縛方式を裁定して official mode を開く (本命だが費用が最大、(4) も別途要解決)。
  **択 (β)** v2 再凍結 consumer の protocol 束縛を resolver 経由へ張り替える (単独では不十分)。
  **択 (γ)** [T-419] / t657 の世代移行の着地を待って残 gate を再測する (単独では何も解けない)。
  **択 (δ)** 床値 v2 を諦め、現行 g1 床値表のまま 8b oracle 本走を進める (**親の推奨**)。
  推奨理由 = 既定方針 3 本 (凍結チェーン検証は保留確定 / 論文主張には粗い provenance で足りる /
  研究最優先・プロトタイプ基準) の下では、床値 v2 の実在は 8b oracle 本走の必要条件でない。
  失うのは「床値が現 gitlink で測られていること」だけで、verdict の faster / no-difference
  境界は旧表のまま固定される。詳説と file:line は
  `output/insights/2026-08-17_t987-floor-rebind/verbatim/s4-adjudication.md` §4。
  base: e1be17c3463dbb5484b0b1d8b7f8a2bf307ab24fcb34f8263234123f32b35aeb

### 新規

- {{T:dev-wave-goal-reachability-gate}} **P2・新規 (2026-08-17 [T-987] wave の段 8 自己改善、
  段構成の変更のためユーザー裁定へ送る)**: dev-wave の段 1 brief に
  「実装した場合に成果物が実際に変わるか」を確かめる義務がない。`DW-G05` は
  **実装しない**場合の成果物影響を 1 行で書かせるが、その鏡像 (実装が目的の artifact へ
  到達する consumer 連鎖を終端まで辿れるか) は要求していない。実測: [T-987] wave は
  段 1〜3 を回してから、裁定の目的である床値 v2 が consumer 側 (`official` mode の無条件拒否と
  v2 再凍結 builder の固定 legacy protocol 束縛) の理由で到達不能だと判明した。
  段 1 で consumer 連鎖を辿っていれば、plan 子と敵対 2 本を起動する前に停止できた。
  **問**: `DW-S01` または `DW-G05` へ「目的到達性の consumer 連鎖を brief で辿る」義務を
  追加してよいか。dev-wave docs は 3 層とも予算が逼迫しており、追加は予算審査を伴う。
  代替案 = 義務を新設せず、段 3 の敵対レンズ既定項目 (`DW-S03`) に
  「成果物が目的へ到達するか」を含める (`DW-S03` は既に gate 新設 wave について
  「成果物が実際に効く全層が scope に入るか」を要求しており、その一般化にあたる)。
