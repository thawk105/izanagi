---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t244-p3-producer-wiring
seq: 1
title: [T-244] P3 producer 結線は実装を止めた — prototype が production で起動できないと実測し、予算束縛・commit-reveal・発火 gate が同時に不成立と確定した (docs のみ、branch worktree-dev-wave-t244-p3-producer-wiring、実装差分なしのため変異 matrix と実装後の受入全走は対象外)
---

## 本文

- **裁定は「実装しない」** ({{D:p3-producer-wiring-blocked}})。段 5・6 を飛ばし `4→7→8→9` とした。
  4 つの独立な情報源が収束した — 親の段 1 前提実測、段 2 プラン (codex read-only, NO-GO)、
  段 3 敵対レンズ A (正しさ境界, 実装停止)、レンズ B (実効性・会計, 実装しない)。
- **段 1 で実測した決定的事実:** prototype の runtime genesis は private test seam の 1 点だけで、
  公開 API 3 本はいずれも `create=False` で入る。親が production 経路で公開 API を呼び
  `cannot open authority lock` を確認した (runtime dir は作られないまま)。
  **prototype は現状 production では起動できない。**
- 実際に行った工程: worktree 作成 → submodule init → `check_wave_startup.py --external-handoff` OK →
  段 1 前提実測 (M1〜M11) → 受入ベースライン取得 → 段 2 codex プラン → 段 3 敵対レンズ 2 本並列 →
  段 4 裁定 → 段 7 記録。実装子 (段 5) と fix・レビュー子 (段 6) は起動していない。
- **受入は 2 回とも緑。** 起点 main 55c2e84 の worktree で 5900 passed / 19 skipped, rc=0
  (計算ノード request 889217、448.90s)。local main e93cd9b を取り込んだ tip でも
  5900 passed / 19 skipped, rc=0 (request 889278、481.75s)。**いずれも実装前の環境健全性確認
  および取り込み後の非破壊確認であって、実装差分の受入ではない** (差分は docs のみ)。
  provenance 全履歴監査は取り込み後 1185 件で違反なし、`check_docs.py` も違反なし。
- **親の段 1 記述を 4 点訂正した。** (1) 代案 (P1') を撤回 — E 段 loop の proposal file schema は
  auditor verdict と diff digest を必須にするため、複数候補を評価前に用意できない
  (レンズ A の反証を親が実ファイルで裏取り)。(2) 「現行 caller はどれも合法 batch を作れない」を
  「**実候補から**合法 batch を作れる production caller が無い」に狭めた — ledger 側は任意の
  commitment tuple を受け、commitment が実 query 由来かを検査しない (これ自体が別の real 所見)。
  (3) pin 閉包の「0 件」は本 wave (成果物ゼロ) にのみ妥当で、bootstrap 以後の authority 世代移行へ
  一般化しない。(4) startup gate の緑を production liveness の証拠から外した。
- **レンズ B の用語 1 点を親が訂正した** — 正式系列の arm 名は `on/off/swapped` であり、
  `rr80/rr20` は holdout (H1/H2) の workload である。実質の指摘 (production 8c driver は
  pilot の ycsb-a/b/c しか回せず正式 holdout を回せない) は実ファイルで確認して real とした。
- **ユーザー裁定へ返す 5 件**を裁定パッケージにまとめた (下記「次の一手」参照)。互いに独立でなく、
  origin authority の実体化の帰結が bootstrap 契約と結線先の形を決める。
- **親の手順逸脱を 1 件記録する** — 段 2 の子を段 1 前提実測の完了前に投入した (`DW-S01` の
  「未確認で子を起動しない」に反する)。実害ゼロ (子は独立に同じ閉塞点を発見し、段 3 の 2 レンズは
  M9〜M11 を含む同一の最新 brief を読んでいる)。段 8 は既存命令が誤っていたのではないと裁定し、
  単発ゆえ `DW-G03` に従って新しい F も contract 変更も起こさなかった。
- 逐語の正本 = `output/insights/2026-08-05_t244-p3-producer-wiring/`
  (brief / s2-plan / s3-lensA / s3-lensB / s4-adjudication / s8-self-improvement)。

## 次の一手差分

### 更新

- [T-244] **P1・P3 は producer 結線の実装を止め、裁定パッケージ 5 件がユーザー裁定待ち。P1 は機械部品のみ、P4 実装 wave 起票可、P5 残余は U-2**:
  **P3**: 本 wave が producer 結線を試み、**実装しない**と裁定した
  ({{D:p3-producer-wiring-blocked}})。prototype は production で起動できず (runtime genesis が
  private test seam の 1 点のみ、実測で `cannot open authority lock`)、予算束縛・commit-reveal・
  DW-G04 の発火 gate が同時に不成立である。**P3 は依然 FAIL** で、cap-lift 上限 1 (D114) も不変。
  再起票には次の 5 件のユーザー裁定が要る —
  (1) **origin authority の実体化** (manifest 13 field の preimage 規則、とくに axis semantics と
  verifier policy。`authority_series_id` の発行主体、予算値、stock certification と
  structural-zero evidence の選定。現候補の coverage artifact は clocks 2100 で
  現 registry の linux-baremetal 1800 と食い違い、そのままでは採用不能)、
  (2) **production runtime bootstrap と authority 世代移行の主体・契約** (公開 authority reader、
  `OriginSnapshot` に manifest / cell key / budget policy / open batch を載せるかを含む)、
  (3) **結線先と batch 形状** (8c は pilot workload のみ、E 段は proposal に auditor verdict を含む。
  候補生成前に予算を確定する reservation event を FSM へ足すか、caller の制御流を batch 先行へ
  作り替えるかの択一)、
  (4) **P7 との面の切り方** (origin proof の durable cross-reference を producer 側で今出すか。
  出さないと P7 は遡って信用できない)、
  (5) **受理集合の変更手続** (複数候補を通すなら report v3 + completeness + trial registry +
  新 D + 境界テストを同一変更単位にする D96 手続を踏むか、単一候補のまま batch を諦めるか)。
  scope 外 real 所見 8 件 (A-2 / A-5 / A-6 / A-7 / A-8 / A-13 / B-4 / B-6) も同パッケージに含む。
  **P1**: 変わらず機械部品のみで未充足。**P4**: 実装 wave 起票可 (D153 の W1〜W5 裁定済み)。
  **P5**: U-1 実装済み、残余は U-2 のみ。
  base: 90a545202dce7e61e08d3c1b7830e95468ce4c8625b9514dcf272505814be10b
