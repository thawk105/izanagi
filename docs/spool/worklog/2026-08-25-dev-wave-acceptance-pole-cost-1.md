---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-acceptance-pole-cost
seq: 1
title: 受入全走の律速は shard 不足でなく real-repo 直列 pole だと実測し、その最大 node を 92 秒から 42 秒へ縮めた (コード + docs、branch worktree-dev-wave-acceptance-pole-cost、変異 matrix = baseline PASSED・3/3 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- ユーザー依頼は「受入全走のボトルネックを見つけ、改善する。計算ノードの待ち時間は勘案せず、
  分割した方が速そうなら分割する」だった。**分割は効かないという結論を実測で返した。**
- 律速は `/work/1/SFC/tanab/.izanagi-acceptance-shards/*/shard-*/report.json` 12 session から
  完全に再現する形で確定した。受入全走は既に K=2 shard + 各 48 xdist worker で走っており、
  shard-0 の 48 worker のうち 46 本は 119〜121 秒で揃う。wall を決めているのは
  `real-repo` loadgroup を 1 本で抱える gw0 で、12 session すべてで 227〜240 秒だった
  (ideal = busy/48 は 97〜153 秒)。shard-1 の pole は 71〜96 秒で 181 秒早く終わる。
- したがって **K=3 でも shard balance 是正でも wall は変わらない**。`real-repo` は
  「親 repo status と共有 ccbench worktree の reader/writer を 1 loadgroup へ閉じ込める」
  正しさ防壁であり、直列性は緩めない。費用側だけを下げる方針を {{D:acceptance-pole-cost-only}} に置いた。
- pole 238.6 秒のうち 194.5 秒が `test_codex_reasoning_ab` の 20 node、その最大単体が
  `test_verify_replays_complete_fake_codex_experiment` だった。`_full_manifest` は
  T-1263 (`24348da8`、2026-08-25 04:38) が `memoize_construction_snapshots` を導入済みで、
  3 呼び手のうち同 commit が追加した 2 本だけが opt-in していた。**残る 1 本への遡及漏れ**である。
- **親の brief が 3 箇所で誤っており、段 3・段 6 の敵対レビューがすべて訂正した。**
  (i)「残余 86 秒は collection/起動 overhead」は帰属の根拠が無く、正しくは非 phase residual
  (schedule 通信・protocol 間隙・controller 処理・finalization を含み、12 session で 57.34〜93.00 秒と変動)。
  (ii)「次の pole は単体 165.8 秒」は誤りで、実際は gw1 の 2 item 合計 176.789 秒。
  (iii)「K=3 はどの worker 数でも無効」は過剰一般化で、`IZANAGI_TEST_NPROC=16` では
  K=2 の shard-0 平均下限 368.7 秒に対し K=3 は 252.3 秒になる。
- **12 session は 48 worker で揃うが 18 の物理 hostname へ分散**しており、同一機体ではない。
  一般化の射程としてこれも段 3 が訂正した。
- 段 6 レビューは「件数不変 (459 passed / 2 skipped) を検出力不変の根拠にするな」を must-fix にした。
  採用し、根拠を変異の kill 証拠へ差し替えた。
- **対象 node は `REAL_REPO_SERIAL_NODES` に属し、変異 harness が期待 node として表現できない
  (F95、恒久対応 T-417 は未実施で本 wave が 3 例目)。** F95 の台帳指示どおり runner argv へ
  `--deselect` を足し、期待集合を非 real-repo の兄弟 node へ再照準した。失う検出力の補償として、
  親が pole.m01 と同じ変異を一時注入して**対象 node 単体が赤になること**を計算ノードで直接実測した
  (`1 failed in 56.45s`、失敗 assert は "generated session row set mismatch" の照合そのもの)。
  注入と復元は `DW-O19` に従い、復元後 `git status --porcelain` 空を確認した。
- 副次観測として、M5 を無効化しても tamper 自体は `receipt canonical replay mismatch` /
  `rollout path mismatch` で拒否される。**拒否は冗長で、この node が pin しているのは拒否理由の
  同一性**である (`DW-M03` の diagnostic sensitivity pin に近い)。kill 判定はこの但し書きつきで数えた。
- 本 wave は既存 T-1564 (`verify_snapshot` の呼出し扇形縮約、1 node 47 回 = fixture 2 / supervisor 25 /
  replay 20) を**部分的に前進させた**。memo 適用で supervisor 側 25 回が cache hit になり、
  残るのは replay の 20 回である。T-1564 の残 scope は変わらないため carry のままとした。
- campaign 成果物 (certified 選択・材料レポート・試行台帳) の値は一切変えていない。
  変わるのは着地 1 回の所要時間と、永続する snapshot 不整合の失敗位置
  (construction から replay へ移る) である。
- 工数: codex 子 6 本 (plan 1、consult 2、author 1、review 2)。fix 子は不要だった
  (段 6 レンズ A が must-fix 0、レンズ B の must-fix 4 件はすべて親の報告の書き方に関するもので
  コード修正を要さなかった)。変異は probe 1 走 + 本走 1 走。
- 親が 2 度 argv/spec を誤って 1 走ずつ無駄にした。いずれも fail-closed で実害は再投入のみ。
  (i) `tools/dev_wave_codex.py --reasoning` は plan/consult で必須・author/fix/review/focus で
  指定不可という段別の逆制約がある。(ii) 変異 spec は `schema` と `timeout_seconds` が必須で、
  欠くと harness が rc=2 で止まる。
- 段 8 は候補 3 件を検討し、**2 件を不採用、1 件を採用した。**
  (i) `--reasoning` の段別逆制約を `DW-C01` へ書く案は不採用。同節は exact 契約で pin されており、
  追記すると単節予算 1000 bytes を 61 bytes 超過する。加えて `DW-O01` の
  「effort は段 5 / 6 が docs 権威から導出。caller 指定は不可」が禁止側は既に述べている。
  (ii) 変異 spec の必須 field を `DW-M05` へ書く案も不採用。最短の表現 (78 bytes) でも
  `docs/dev-wave/**` の L1.5 footprint 予算 9566 bytes を超える。**予算は満杯で、
  予算値の引き上げは通常の自己改善の対象外**であるため本文を変更しない。両件とも
  fail-closed で実害が再投入のみに留まったことも不採用の根拠にした。
  (iii) F95 の 3 例目と、再照準が「変更した real-repo node の検出力」を構造的に測れないという
  新事実は、失敗台帳の再発として採用した。

## 次の一手差分

### 新規

- {{T:acceptance-shard-count-k3-measurement}} **P1・ユーザー裁定待ち**: 受入全走を K=3 で
  一度実測してよいか諮る。現行 48 worker・duration 固定 model では K=3 の shard busy 平均は
  84.1 / 42.0 / 73.6 秒で pole 238.7 秒を大きく下回り短縮は見込めないが、**K=3 の実走は
  artifact root の 241 report 中 0 件で一度も測られていない**。同居 work が 2,661 node 減ることで
  pole 自体が縮む二次経路は否定できない。実走には受入 lease の消費と `env_projection` の変更を
  伴い受領証 pin へ触れるため、AI 側で勝手に実施しない。worker 数 (N) の再裁定は [T-1563] が
  別に持っており、本項は shard 数 (K) 側である。
- {{T:acceptance-duration-ledger-refresh}} **P2・新規**: `orchestrator/tests/acceptance_duration_ledger.json`
  を変更後の実測で再生成する。対象 node は台帳で 94.0 秒だが実測は約 42 秒になった。
  台帳は shard 割付の助言にしか使われず wall の律速ではないため本 wave では触っていない
  (値を byte で pin する test は無いことを実測で確認済み)。再生成には変更後の全走 junit が要る。
- {{T:acceptance-nonphase-residual-attribution}} **P2・新規**: shard wall のうち
  test phase に入らない残余 (12 session で 57.34〜93.00 秒、critical path の 2 割弱) の内訳を
  collection / worker 起動 / schedule 通信 / controller / finalization へ分解する。
  現状は引き算でしか捉えられておらず、親が 1 度この帰属を誤った。
