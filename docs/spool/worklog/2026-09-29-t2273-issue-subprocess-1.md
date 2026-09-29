---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: t2273-issue-subprocess
seq: 1
title: [T-2273] [T-2560] 受入 shard-0 の律速 (b) 発行 subprocess を縮めた — 発行 child の CPU の 99 % を占めた三軸走査の正規表現照合を軸 literal の出現近傍の窓に局所化し (report の bytes は不変)、発行 child は約 86 秒 → 約 32 秒。実受入の隣接 3 対で W_0 が 16.5〜40.5 秒 (対率中央値 9.1 %) 縮み、事前登録の区分 (ii) 小さい改善として land する。5 分上限は B の W_max 中央値 276.1 秒で達成 (コード + test + insight、branch worktree-dev-wave-t2273-issue-subprocess)
---

## 本文

- **依頼は (b) 発行 subprocess の短縮。** 開始 gate 2026-09-28 07:53 JST (HEAD = local main `51f896352`)。insight `output/insights/2026-09-29/t2273-issue-subprocess/README.md`、判断は {{D:t2273-issue-subprocess-land}}。実装 commit `56f8e97c0` + fix `ad8c91ecf` (Codex author、子 branch `author-t2273is-impl` / `fix-t2273is-impl-1`)。
- **律速を先に実測した:** 計算ノードで受入の L node を単独走し py-spy で発行 child を採ると、CPU の 99 % が三軸走査 `search_repository`、その 54 % が正規表現 search 1 行だった。generic dispatch で py-spy + pytest を走らせるには、`<abs>/pytest` を `/usr/bin/python3.10` で起動し (計算ノードで shebang が 3.9 に解決される)、`-o pythonpath=.` を付ける (直起動では repo root が import 経路に無い) 必要があった。py-spy は子が落ちても rc=0 を返す。
- **Pegasus 保守 (9/28 09:00〜21:00) で中断:** 保守中に投入した再 profile は overall-timeout (計測値なし)。前 session はここで終わり、9/29 02:2x にユーザーの「続けられる？」で再開した。保守明けの queue 滞留 (gen_S QUE 70〜88) で温め B・変異 probe・final が queue 待ちで何度も打ち切られ、待ち上限を 14,400 秒へ延ばした (判定量は job 内の worker 占有なので不変、全走に同じ値)。変異 final は待ち上限と spec の外側 timeout の整合検査、resume 不能 (evidence 未生成)、Lustre の EINTR で 3 回止まり、新しい scratch・出力 path で 4 回目に完走した。
- **計算量のユーザー確認:** 再 profile の結果 (発行 child 36.7 %) と見積り 合計約 2.35 node 時間を示し、9/29 02:4x JST に「3 対で投入 (推奨)」の回答を得た。その後ユーザーは就寝し、マネージャーセッションから「判断は codex と賛否 2 立場で決めて進める」との連絡があった。実績 2.26 node 時間 (系列 8 走 24 job 1.95、変異 0.08、profile・焦点走・provenance・温め 0.23)。記録後の受入 1 回が別に加わる。
- **段 3 相談 2 本 (修正後 GO)** で MAXREPEAT の分岐を不採用、共通判定の発火回数の番人と単一 alternative の単軸 fixture を追加。**段 6 レビュー 2 本**: 過剰・削除は所見なし、正しさは must-fix 1 件 (`MappingProxyType` の背後書換えで共通判定 cache が別の式に古い判定を再利用する) を text object の identity で直した。str subclass と `sre_parse` 非推奨の 2 件は refuted / scope 外。
- **E1 の erratum:** 系列の対 1 の後、旧 E1 (A/B 共通 node の 3 shard 割付の完全一致) が新設 8 node による shard-1 / 2 の再分割で構造的に不成立と分かった。shard-0 の共通 node 集合は完全一致。W を見る前に codex の賛否 2 本に諮り、割付一致を shard-0 に限定する erratum E1' を 07:29 JST に固定し、集計器を Codex fix で改訂した。旧 E1 での判定は `undetermined` として並記。失敗型は {{F:t2273-e1-shard-partition}}。
- **赤 1 件の分類:** 04-A (A 木) の `test_env_contract_activation.py::test_historical_calibration_is_verified_only_when_resolved_in_source_stage[modified]` は実 repo の `git archive` が 30 秒 timeout を超えた環境由来の赤で infra と分類し、対 2 を対ごと取り直した。
- 計測中に local main が `43a239294`・`1887f56e4` へ進んだ (別 session の land)。受入・対象 file に触れていないことを確かめ、記録前に `1887f56e4` を取り込んだ (merge `9f11c1716`)。
- 受入全走は記録 commit の後に 1 回走らせる。
- 工数: codex 子 11 本 (plan 1、consult 2、author 2、review 2、fix 2、E1 の賛否 consult 2)。計算ノード job 54 本。

## 次の一手差分

### 完了

- [T-2273] 受入 shard-0 の律速 (a) 可視 output の写し (D2271) に続き、(b) 発行 subprocess を三軸走査の係数削減で縮めて land した ({{D:t2273-issue-subprocess-land}}、insight `output/insights/2026-09-29/t2273-issue-subprocess/README.md`)。隣接 3 対で W_0 対差 +32.3 / +40.5 / +16.5 秒 (区分 (ii))、5 分上限は B の W_max 中央値 276.1 秒で事前登録の判定を満たした。02-B の 1 走は shard-1 が 349.4 秒で 300 秒を超え、shard-1 の伸びの原因は計器が無く分けていない (insight §7)。
  remaining: none
  base: dcc91d18745c00a6bd5b62f13392e72f4ca5b6fa46ad945ddc8d0ece6de7c979
- [T-2560] D1936 項 35 のとおり実測で律速を選び、(a) (D2271) と (b) ({{D:t2273-issue-subprocess-land}}) を実受入の隣接対で確かめて land した。受入全走の 5 分上限は事前登録の判定 (B の W_max 中央値 276.1 秒) で満たした。
  remaining: none
  base: 90211d563af694152a9e214db33f0d4b650d22ce166f79466e2aa2b1ba71fd3e
