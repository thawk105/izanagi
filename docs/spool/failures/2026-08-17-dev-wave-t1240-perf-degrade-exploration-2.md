---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-17
wave: dev-wave-t1240-perf-degrade-exploration
seq: 2
---

## 新規

### {{F:grep-count-over-authoritative-closure}}. 集合の大きさを grep で断定したが、その閉包を pin するメタテストが同じ repo に実在した [手順漏れ] [テスト代表性]

- 事象: 段 1 brief に「degrade できない直接呼び手は `screening_driver.py` の 1 本」と書き、
  その前提で段 2 のプラン子を起動した。実際は 4 本で、権威ある閉包は
  `orchestrator/tests/test_campaign.py` のメタテストが
  `campaign.pipeline.evaluate` の呼び手をちょうど 5 本、`campaign.loop.run_campaign` の
  呼び手をちょうど 15 本として pin していた。走行中の子を停止し brief を作り直した。
- 根本原因: `grep` は識別子を直接書いた行しか見つけず、`evaluate_fn` のような別名束縛を落とす
  (実際 `s1_direct_comparison.py` と `s8b_oracle_driver.py` は `evaluate_fn` 経由で呼んでおり、
  素の `evaluate(` 検索には出なかった)。既存の
  memory `complete-search-not-truncated-for-absence` は「切らずに検索する」を要求するが、
  本件の検索は切っていない — **検索した空間そのものが違った**。
  `pin-closure-search` は凍結 pin の探し方であって呼び手閉包を扱わない。
- 恒久対応: memory `authoritative-closure-before-counting` — brief に「N 箇所」「唯一の」
  「これだけ」と書く直前に、その集合を pin する既存のメタテスト
  (`expected_inventory` / `closed-world` / `exact` を名前に含むもの)・凍結 artifact の
  path 集合・台帳を検索する。見つからなければ「grep 由来の暫定値」と明記して
  敵対レンズの攻撃対象に指定する。
- 再発検知: 段 3 の敵対レンズへ「閉包の正しさ」を明示レンズとして渡すと検出できる。
  本 wave では sol レンズが独立に「15 対 5 は現行直接構文の snapshot であって権威ある閉包ではない
  (再 export 二段経路は resolved にも UNRESOLVED にも入らない)」と、親が正本と呼んだ台帳の
  限界まで指摘した。

## 再発

### F31

- **再発: 2026-08-17** — 起票文が引く条件「official mode では no-perf を拒否する非対称を保つ」を
  brief の scope に入れ、その方向で段 2 の子を起動した。**要約と本文は一致していた**
  (起票文・archive 本文・裁定控えの三者一致を親が確認済み) が、翌日に**別 ID の [T-1253] が
  同じ主題を逆向きに裁定**しており、実装しようとしていた向きが裁定と正反対だった。
  F31 の恒久対応 (要約が参照する decision 本文を開く) は満たしていたので発火せず、
  段 2 の codex 子が worklog を辿って fail-closed で停止するまで判明しなかった。
  並行セッションも独立に同じ罠へ落ち、archive の旧「新規」エントリを読んで
  「未裁定」と報告してきた。**新しい情報は、F31 の対応が「同じ ID の本文」までしか
  射程を持たず、別 ID による supersede を捕まえないこと**である。恒久対応は
  memory `ruling-lookup-discipline` (同日 /next-tasks が同じ [T-1253] の実例で更新済み) を
  正本とし、新設しない。`DW-S01` への統合は dev-wave docs の byte 予算が 3 層とも満杯のため
  行わず、段 8 の候補としてユーザーへ返す。

### F24

- **再発: 2026-08-17** — 正本の待ち手 `tools/dev_wave_wait.py producer` が、**producer 生存中に
  rc=0 で偽完了**した。変異 probe の待ち手が 02:49:57 に rc=0・出力ゼロで返ったが `.done` は不在、
  producer pid は経過 32 秒で生存しており、実際の完了は約 10 分後だった。2026-08-12 の
  「待ち手自身が偽 green を返す」と同型で、恒久対応 (`.done` 出現と producer 死の両方で判定し
  待ち手の rc を信じない) がそのまま効いた。追加事実は**同一 wave 内で同じ待ち手が 2 度
  偽完了した**点で (段 6 レビュー B でも成果物 flush 前に rc=0 が返り再読で解消)、
  偽完了が単発事故ではなく常態であることを補強する。
