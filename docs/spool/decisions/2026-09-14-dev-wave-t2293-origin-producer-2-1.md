---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-14
wave: dev-wave-t2293-origin-producer-2
seq: 1
---

## {{D:origin-evidence-rendezvous}}. 起点試行の証拠の所在と bytes は呼び手に申告させず producer が導出する

**決定:** 起点試行の formal terminal が消費する 33 件の result-evidence record について、
置き場と中身を呼び手入力から外す。

- envelope の member ごとの `evidence_path` は、capability の origin id、run plan の attempt 0 batch id、
  query ordinal から `reports/reflux-result-evidence/<origin_id>/<batch_id>/<q>.json` の規則で導出する。
  `OriginMemberPlanInput.evidence_path` を廃止する。
- formal consumer へ渡す evidence root は origin runtime の campaign output root に固定する。
  `OriginProducerInputs.evidence_root` を廃止する。
- record bytes は runtime root 配下の導出 path から query ordinal 昇順に読む。
  `OriginProducerInputs.result_record_bytes` を廃止する。
- 回収は fail-closed とし、件数 exact 33、ordinal 0..32 昇順、path 相異、symlink を追わない
  regular file、record schema 検査、record から再導出した path と member の宣言の一致を要求する。
  1 件でも欠ければ formal 評価へ進まず既存の失敗境界へ返す。

**名乗りの上限を決定に含める。** 閉じるのは supervisor 経由の bytes 注入経路と path 申告だけである。
同じ場所へ整合 bytes を置ける主体は排除していない。create-only は writer 認証ではなく、整合的な
lock / WAL の後置きも拒否できない。唯一 writer 性は trusted harness の運用前提であり、本決定が
与える保証ではない。formal consumer を直接呼ぶ経路の受理集合は変わらない。

**理由:**
- 変更前は、envelope が宣言した場所に存在しない bytes でも、呼び手が引数で渡せば起点試行の
  formal terminal が成立しえた。判定が実行と無関係になる自己申告型であり、8c 結線設計 §10 が
  却下した「issuer 文字列を権限証明にする」案と同型である。
- D1747 は「起点 consumer は錠前の場所を計算し、呼び手に申告させない」と定めた。record の所在にも
  同じ規律を当てるのが一貫している。
- 33 本を実行する executor を将来置いたとき、executor はこの導出先へ書けばそのまま結線される。
  待ち合わせ点を先に固定しておくと、executor が呼び手申告で迂回されることがなくなる。

**却下した選択肢:**
- 呼び手申告の bytes を残したまま disk の現物と照合する互換期間を設ける — 迂回経路が残る。
- 導出規則を result-evidence 側の公開関数に一本化する — 公開関数は完全な record の検証を要求し、
  envelope 構築時点では record がまだ存在しない。規則の重複は 1 関数に閉じ込め、回収後の照合には
  公開関数を使う形にした。

## {{D:origin-producer-wiring-blocked}}. 33 本を実行する executor は現行の制約下では結線せず、障害を構造化して返す

**決定:** 起点試行の 33 本の物理 campaign run を実行する executor は本 wave では実装しない。
結線に必要な次の 4 件を、それぞれ理由を付けて scope 外とし、裁定パッケージとして返す。

1. **証拠発行器の受理型に探索 layout を加えること。** 現在の exact-type gate は探索 layout を拒否する。
   解除は producer の発行可能集合を広げる変更であり、D1670 が実装 wave へ渡した 3 写像に含まれない。
   未裁定の受理拡大を親が単独で入れない。
2. **台帳の予約から封印までを行う production 機構。** consumer は sealed member の evidence digest と
   record の一致を要求するが、その遷移を行うのは現在 test helper だけである。
3. **q の候補を実 source へ適用する起点専用の物理 entry point。** 既存経路は template 適用・検疫・
   auditor veto・condition gate を通す。迂回して campaign を直呼びすると、従来拒否していた入力が
   実行され証拠が発行される。規律 2 に抵触するので採らない。
4. **completion と report の起点分岐。** 単数 campaign root 前提、positive cell admission、
   completeness と Layer-3 chain がいずれも単一 campaign 前提である (D1668 の起点専用 completion と
   設計 §J 受入要件 18 の範囲)。

**理由:**
- 1 と 3 は受理集合または正しさ防壁に触れる。2 と 4 は依頼が限定した範囲を超える大型機構である。
  どれも親の裁定で片付けてよい種類の選択ではない。
- 段 2 plan と段 3 の 2 レンズが独立にこの 4 件を挙げ、両レンズとも plan 作り直しと判定した。
  親が現物で裏取りして同じ結論に達した。
- 発行 3 条件は 0/3、本番 authority は 0 件のままであり、実装しないことで certified 選択・
  材料レポート・試行台帳の現在値が変わることはない。

**却下した選択肢:**
- 探索 layout の受理を親裁定で追加して executor を通す — 未裁定の受理拡大である。
- 検疫と auditor veto を通さない直呼び経路で executor を作る — 規律 2 を緩める。
- executor の配線だけ先に置く — 発火しない機構を置くことになる。

## {{D:origin-collection-gate-effectiveness}}. 今回足した実効的な新設ゲートは 1 本だけだと変異で確かめ、恒真な検査を gate と数えない

**決定:** 起点証拠の回収に置いた検査のうち、**変異で実効性を確かめられたのは
「record から再導出した path が member の宣言と一致すること」1 本だけ**である。
件数 exact 33、ordinal 昇順、path 相異の 3 検査は、recovery envelope の member 検査が
既に保証しており後段では必ず真になる。これらを独立した正しさゲートとして数えない。
入力欄の削除は型レベルの縮小であって、変異で測れる gate ではない。

**理由:**
- 段 6 のレビューが envelope 側の member 検査を読んで恒真性を指摘し、親が現物で確認した。
  事前登録した 5 変異のうち 3 つはこの理由で単一理由性が立たず、DW-M01 と F28 に従って
  登録から外し実効 gate へ再照準した。
- 再照準後の本走は baseline PASSED、4/4 KILLED、期待 node 完全一致だった。一致検査の変異は
  観測 node がちょうど 1 件で、単一理由性が実測で成立した。
- 検査の本数を保証の強さとして提示すると、恒真な検査を数に入れて実際より強い主張になる。

**却下した選択肢:**
- 3 検査を冗長 gate として登録したまま KILLED を数える — 偽の KILLED を台帳へ残す。
- 恒真だからと検査自体を削る — envelope 側の保証が将来変わったときの防壁として残す価値があり、
  削る理由にはならない。数え方だけを正す。
