---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-29
wave: dev-wave-t2067-floor-selection-rule
seq: 1
title: [T-2067] 床値の使用測定を事前登録した決定的な選択規則で固定した (code + tests + insight、branch worktree-dev-wave-t2067-floor-selection-rule、変異 9/9 KILLED)
---

## 本文

- D1243 の規則を実装した。規則と層の配置は {{D:floor-selection-earliest-eligible}} と
  {{D:floor-selection-layer-placement}}、主張上限は {{D:floor-selection-claim-ceiling}}。
- 段 2 の初版は earlier result の自己申告 `eligible_for_refreeze` を集合 membership の権威に
  していた。段 3 レンズ A が real と判定し、親が採用して共有 admission 台帳からの再導出 bit へ
  差し替えた。選ばれなかった run の 1 field を書き換えるだけで required run が動く穴だった。
- 親は一度「最も早い result.json をそのまま必須にする」単純化を検討したが、D1124 の逐語を読んで
  却下した。resume した run は official path に result.json を書きつつ適格ではなく、resume は
  D1124 が守った復旧経路である。却下理由は正例変異 `treat-all-earlier-eligible` で機械的に守る。
- 段 3 レンズ A が「candidate は launch certificate を検証しない」と指摘し、親が現物で確認した
  (既存 fixture は certificate に `{}` を書いていた)。レンズ A の処方 (主張を下げる) は採らず、
  全史検証が既に持つ同じ束縛を candidate へ再利用した。
- 段 6 の must-fix 3 件は、nofollow が check-then-use だったこと、D1124 の正例が導出関数の
  monkeypatch stub で機構を通っていなかったこと、選択層と導出層をつなぐ引数配線が未検証だったこと。
  すべて fix 子が closed にした。
- 親は「`_validate_floor_inputs` の 6 tuple → 7 tuple は契約違反」という所見を **refuted** とした。
  module private で caller 1 件、返す値は関数内で既に計算済みの同一オブジェクトであり、再 parse は
  run-id の解釈を 2 か所へ増やす。
- 焦点走が oracle の g1 fixture 24 件の既存の内部矛盾を可視化した。合成定数で凍結床値を上書きし、
  同じ文書が記録する source と無関係にしていた。fixture を正規形へ直した。期待値の緩和ではない。
  この 24 件は変更した test file だけの焦点走では出ず、DW-O26 に従って consumer test を
  参照関係で引いたために出た。
- 親の argv 誤りで段 6 review 子 2 本が rc=2 即死した (`--lane` は consult 段専用)。別名と
  別 job-id で再投入して復旧した。
- 焦点走の dispatch は 2 回 `queue-wait-timeout` で子が起動しなかった。`--force-dispatch` は
  使わず §7.0.0 の自動判定のまま投げ直した。
- 動機の射程を訂正した。2026-08-28 の A-2 実走は s8b holdout floor を消費していない。
  同 insight の「floor」は A4 noise floor で別概念であり、s8b floor の消費例に引いてはならない。
- official floor run は現 repo に 0 件である。T-1942 の実測によれば床値実測の投入の主経路は
  D1192 未実装により無条件で赤であり、これが 0 件の理由を与える。本 wave の正例・負例は
  すべて合成 fixture である。
- floor 本走、oracle / 8c 本走、性能測定、qsub、push、次 wave 起動は行っていない。
- 一次資料は `output/insights/2026-08-29_t2067-floor-selection-rule/`。

## 次の一手差分

### 更新

- [T-2067] **P1・一部完了**: 選択規則と投影 equality を実装し landed した。残るのは
  D1241 の上限を解除できない 5 残余 (削除された earlier run を戻す authority、g2 以降の選択・投影、
  load-only consumer への選択強制、起動証明書の実時間性、s8c の production final claim 配線) の
  裁定である。とくに前 2 者は設計択一なのでユーザー裁定へ返す。
  base: dd2a9a1c0687f7e3092bc5b19ac3f9acd4631763c64883c1f8e5abfda320b512
