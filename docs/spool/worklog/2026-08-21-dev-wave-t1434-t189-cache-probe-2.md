---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1434-t189-cache-probe
seq: 2
title: '[T-1434] T-189 provider cache 制御可能性を実測し、制御不可能と確定した (docsのみ、branch worktree-dev-wave-t1434-t189-cache-probe)'
---

## 本文

- T-1434 総括 未解決点(3) (`docs/phase3-t189-model-routing-preregistration.md:734-736`) に着手した。
  scope は実測と docs 記録のみ (command 指示どおり)。他の未解決点 (1)(2)(4)(5)(6)(7) は scope 外、
  特に (1) power simulation は (6) task catalog 凍結に構造的従属するため単独では触れていない。
- `codex exec --help`/`codex exec resume --help`/`codex exec fork --help`/`claude --help` を
  全走査し、provider cache の reset/namespace/cold-warm 制御に該当する CLI 引数が存在しないことを
  確認した。
- Codex 8 回・Claude 3 回、計 11 回の実 CLI 呼出しで直接実測した。独立に新規作成した `CODEX_HOME`
  (`tools/codex_reasoning_ab.py:3419-3424` と同じ auth.json コピー方式) や `--no-session-persistence`
  付き独立プロセスは provider 側 cache に一切影響しないことを一貫して確認した。Codex は同一 thread
  を `codex exec resume` で継続した場合だけ前 turn の内容が cache から読まれる (97.2%)。Claude は
  逆に、一度送信した内容が完全に独立した後続プロセスから 100% cache 読み出しされる
  (既定 cache tier は `ephemeral_1h`)。
- 段4裁定: {{D:t189-cache-control-measured-infeasible}} — §9 の blocker (段6所見 B5) を実測により
  確定し、resource 指標 `not-applicable` の既定を維持する。実装変更は行わない
  (§12 gate 評価器が未実装のため、D640 がすでに却下した「未使用の飾り」を避ける、規律5)。
  段5・段6は「実装しない」裁定により skip、4→7→8→9 で進めた。
- `docs/phase3-t189-model-routing-preregistration.md` §9・総括の該当箇所へ実測結果への参照を
  追記した (estimand・分析計画・margin 等の設計面は変更していない)。§9 が引用していた
  `tools/codex_reasoning_ab.py` の行番号 (`:2625-2646` 等) は T-1434 Wave D (本日、同日先行 land)
  でファイルが約3000行増えた後の現在の行番号と一致しない陳腐化を発見したが、本 insight の結論は
  独立した生実測に基づくため影響を受けない。
- 傍論として、`codex exec --json` の実イベント名 (`thread.started`/`turn.started`/
  `item.completed`/`turn.completed`) が `tools/codex_reasoning_ab.py` の検証コードが期待する
  イベント名 (`token_count`/`task_started`) と異なる可能性を実測観測した。live codex 呼出しパスへの
  実害は未検証 (本 wave の scope 外)。装置所有者への follow-up 候補として insight に記録した。
- 一次資料: `output/insights/2026-08-21_t1434-t189-cache-control-probe/README.md`
  (生ログ 11 件・呼出し対応表は同ディレクトリ `raw/`)。
- 他 wave からの周知 2 件 (main 受入が `external/ccbench` gitlink pin (511c9538→ef9328a3) と
  `CCBENCH_FULL_SHA`/provenance trailer の不一致で赤、t-1458 セッションが対応中) を受信した。
  本 wave は該当ファイルに触れておらず、受入投入前に main を再確認する。

## 次の一手差分

### 更新

- [T-1434] **P1・ユーザー裁定待ち (継続)**: 未解決点(3) provider cache 制御可能性の実測が完了し
  制御不可能と確定した ({{D:t189-cache-control-measured-infeasible}}、詳細は
  `output/insights/2026-08-21_t1434-t189-cache-control-probe/`)。並行 wave が (5) のうち stage2 側を
  完了し stage5 側は [T-1480] へ分離済み。残るのは (1) power simulation・(2) 独立 custodian 実現方式・
  (6) task catalog 実データ+独立分類者確保・(7) price snapshot 実データ取得の4論点であり、
  引き続き未着手のまま着手要否・優先度・担当 wave はユーザー裁定を要する。
  `routing_evidence_status` は `inconclusive` のまま。
  base: 09695ff1458d9b47a581b66065372d3a364899ed1a55266f3c490ec85d2c17d2
