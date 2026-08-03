---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-03
wave: dev-wave-t296-layer-c-calibration
seq: 1
title: [T-296] 層 C 量の取得は 2 つに割れた — 較正点は 8b H1/H2 限定で継承、floor は [T-011] の重複で [T-088] 待ち (docs のみ、branch worktree-dev-wave-t296-layer-c-calibration、影響テスト = Pegasus gen_S 計算ノード request 881854 で 350 passed、provenance 監査 = request 881853 で 813 件違反なし、実装差分なしのため変異 matrix と受入全走は対象外)
---

## 本文

- **段 1 の前提実測で T-296 の前提が 2 件とも覆った**ため、取得を実装せず段 4 で「実装しない」と
  裁定して `4→7→8→9` を辿った。実装差分がないので変異 matrix と受入全走は射程外である
- **段 3 の敵対レンズが NO-GO を返し、親の scope の一般化を 2 件止めた。** 結論 (今は取得しない) は
  支持されたが、根拠づけが誤っていた。親は全指摘を file:line で裏取りして 4 件を採用した
- **較正点の継承は「8b H1/H2 限定の例外」であって恒久却下ではない (親の初出案を撤回)。**
  `docs/phase3-8b-descriptor-design.md:6-10` の 2026-07-16 承認は、H1/H2 を採り H3/H4 を落とした理由を
  「校正動作点 (skew=0.9, rmw=0 で確定した records/threads) の前提が変わり交絡する」と書くので、
  H1/H2 が 1M/48 を継承すること自体は成立する。**しかし汎用契約は較正点を
  `(env, thread, 代表 workload)` でキーする** — D13 の改訂注記は「当初は『入力完全非依存』としていたが、
  飽和点が skew に依存すると実測で判明したため署名付きで分ける」であり (`docs/decisions.md:180-186`、
  `docs/roadmap.md:309`)、ファイル署名も rratio/rmw を含む。「rratio では分けない」は**慣行であって
  契約の禁止ではない**ので、一般規則へ格上げしない
- **holdout の危険は「永久汚染」ではなく「launch certificate の clean scan 失敗」だった。**
  規約 (file-level conjunction、`excluded_paths=["output/s8b-freeze/"]`、4932 ファイル) で数え直すと
  **H1 rr80 = 0 / H2 rr20 = 0 / positive control rr50 = 67**。親が最初に出した 2/2/316 は行数で、
  2 行は除外対象の freeze 自身だった。0 件要求は v1 までで `s8b_ratified_freeze.py:1403-1406` は
  v2 で課さない。**一方 official floor の launch certificate は `clean_scan_digest` が
  発行時点の hit 0 件 scan を fail-closed で証明する**ので、closure の外に rr80/rr20 の実測値を置くと
  **floor の起動自体が止まる**。あわせて `frozen_at_head=2e20d441` は履歴書換えで dangling であり
  ([T-068] 裁定 2026-07-21 で参考情報へ格下げ済み)、生きた anchor として引いてはいけない
- **between-run floor 側は「未起票」ではなく [T-011] の重複だった。** [T-011] (科学レーン floor 実測) が
  残 gate を「[T-096] → [T-088] → 段階 3・4 → 実行 revision 束縛」と既に書いており、本 wave が独立に
  辿った連鎖と一致する。人間手番はすべて済 (protocol 実凍結 `c8cbd17`、予測封印実走、§5-(viii) 受諾が
  いずれも 2026-07-24)。塞いでいるのは official guard の二重拒否
  (`s8b_floor_campaign.py:194-204` core / `:3435-3444` CLI) で、実機で job `873225` が rc=2 を返している。
  **pilot は代替にならない** — pilot artifact は `eligible_for_refreeze: false` (同 `:43`, 強制 `:2330-2333`)
- **floor の取得義務は畳まない。** `docs/phase3-8c-preregistration.md:93-124` の実走前提 12 項の第 7 項が
  「対象別 between-run floor が H1 / H2 について再実測され §5 に記入されている」であり、§5 の表にも
  未記入欄が残る。T-296 は「不要になった」のではなく「依存の下流へ移った」項目なので項自体は残す。
  [T-088] には床値実測後まで塞がった条件待ちが 8 件
  ([T-085]/[T-112]/[T-114]/[T-011]/[T-122]/[T-103]/[T-089]/[T-090]) ぶら下がる
- **派生所見 (floor 既定 dir の env 盲目) は新規起票せず [T-333] へ統合した。**
  `screening_driver.py:31-32` の `_default_calibration_dir` が linux-baremetal 固定で、
  sweep driver 群 (`backoff_sweep.py:97` / `s6_sort_sweep.py:260` / `s8a_trigger_sweep.py:307`) が
  floor dir を渡さないと別 env の floor が compare の丸め閾値に効く。**同じ欠陥は [T-333]
  「loader も `env_tag` を読まない … 実 consumer に環境が伝わっていない」が既に起票済み**であり、
  親は記号名で台帳を検索したため概念で書かれた既起票を取り逃がしていた。発火する計測 ID は
  `output/campaigns/` / `output/exploration/` を含めた検索でも 0 件
- **8b 非依存の一般用途 floor は実在するが Pegasus 未対応。** `between_run_floor.py:45-62` が
  `p2_2.py:40-47` から `ENV_TAG="linux-baremetal"` / `CLK=1800` / `numactl --interleave=all` を定数継承し、
  動作点も rr5/rr50/rr95 固定、書き出しも `env_scope_dir(ENV_TAG)/calibration` 固定 (:112-120)。
  Pegasus は TSC 2100・単一 NUMA
- **手続き上の逸脱を正直に記録する。** 実装面が無く成果物が docs 本文と裁定だけのため段 2 (プラン起草) を
  行わず、段 3 の敵対レンズ 1 本だけを立てて親 brief の事実主張そのものを攻撃させた。既起票タスクの
  前提を覆す wave であり `DW-C00` の「独立の敵対検証子を省かない」に該当すると判断した。
  レンズは read-only の静的検査のみで pytest を実走していない
- **受入は実装差分がないため影響テストに絞った。** `tools/check_docs.py` 違反なし、
  影響テスト (`test_check_docs.py` + `test_spool_fold.py`) は Pegasus gen_S 計算ノード
  request `881854` で **350 passed** (elapse 11s)、provenance の full-history 監査は
  request `881853` で **813 件・違反なし**。ログインノードは `python3 -m pytest` を hook が機械拒否するため、
  いずれも `tools/pegasus/dispatch_compute.py` 経由で計算ノードへ dispatch した。
  **投入前は「gen_S に 177 件待ち」を見て受入を `check_docs.py` だけに絞る判断をしていたが、
  実際の待ちは 13 秒だった** — キュー長を待ち時間の代理に使った推定が外れたので、実測してから絞る
- **dev-wave の運用で 1 件踏んだが、段 8 で不採用にした。** 背景 job から codex 子を投げるとき、
  `&` と harness の `run_in_background` を併用すると子が親シェル終了で落ち、`.done` が残らず
  log だけ途中で切れる。1 回目の投入で実際に起きて再投入した。**ただし `DW-O01` の既存規則
  (完了は `.done` の存在と exit code だけで判定し、ログ本文の grep も harness の完了通知も
  完了判定にしない) が実際に効いて、途中で切れた log を完了と扱わずに済んだ** — 壊れたのは
  投入方法であって規律ではない。単発事故は局所修復が既定 (`DW-G03`) であり、
  `docs/dev-wave/operations.md` の余裕も 44 bytes (ディレクトリ合計では 2 bytes) しかなく、
  予算上限は上げない方針なので reference を変更しない。事故の記録は本エントリに留める
- エージェント工数: 親 1、子 1 (段 3 敵対レンズ)。実測はすべて親が行った
- 一次資料 = `output/insights/2026-08-03_t296-layer-c-calibration/` (brief / 敵対レンズ逐語 / 裁定)

## 次の一手差分

### 更新

- [T-296] **P2・依存へ繋ぎ替え → 保持 (取得は下流)**: 起票時の「層 C 量の取得が未起票」は実測で
  2 つに割れた。**(a) rr80/rr20 の較正点**は 8b H1/H2 が校正動作点 (1M/48) を継承する設計であり
  (2026-07-16 承認)、この系列に限っては追加取得が要らない。**ただし汎用契約は較正点を
  `(env, thread, 代表 workload)` でキーする (D13/D15) ので、恒久却下の一般規則にはしない**。
  **(b) between-run floor** は [T-011] (科学レーン floor 実測) の重複で、残 gate は [T-011] が書いた
  とおり [T-096] → [T-088] 段階 3・4 → 実行 revision 束縛。8c 事前登録 §6 項 7 が H1/H2 の対象別 floor を
  実走前提としているので**取得義務は畳まず本項を残す**。**未裁定として残るのは
  「Pegasus を正式計測の claim env へ昇格させるか」の 1 問だけ** — D59 (1) は正本 env-tag を
  `linux-baremetal` に据え置いており、昇格には roadmap §5 の 4 条件が要る。
  「floor を取るか」自体は既裁定 (2026-07-27 = 廃止ではなく順序の後退) なので択一に戻さない
  base: 0aedf9a1f17a1e55907637e97e7c3f8d3dfeaeb4c3dec4aee039cfed13e203d3
