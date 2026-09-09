---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2273-accwall-maxocc
seq: 1
title: [T-2273] shard-2 の最大 worker 占有を 308.57 → 146.54〜177.0 秒へ削り wall を 300 秒未満へ入れた — 依頼が名指しした床 (t080) は最遅 shard の床ではなく、最遅は shard-0 へ移った (コード + 実測 + insight、branch worktree-dev-wave-t2273-accwall-maxocc、変異 4/4 検出・撤回 2 件、受入 5 走目で緑)
---

## 本文

- **依頼と D1894 の前提が実測で覆った。** 依頼は「現在の床は `test_t080_*` 群」を前提にし、
  D1894 は「着手前に床が t080 群へ移ったことを実測で確かめる」を要求していた。
  2026-09-09 の 9 走を測った答えは**否**である。最遅 shard は 9 走中 8 走で shard-2 で、
  その最大 worker 占有は xdist group `p3-b4-material-report` だった。t080 は shard-0 の
  占有の担い手にすぎない。詳細は {{D:slowest-shard-floor-is-material-group}}。
- 親は D1894 を不採用にせず、決定本体 (対象は最大 worker 占有) に従って
  「実測で最遅である shard の最大 worker 占有」と読み替えて実装した。
  **この読み替えの追認と、単位 B の起票可否をユーザー裁定へ返す。**
- **段 2 の plan 9 項目のうち 7 項目を段 4 で不採用にした。** 段 3 の敵対相談 2 レンズと
  親の独立検証が一致して「速くするために検査を消す」形と判定したためである。
  特に `_assert_replicas_match_real_except_identity` の除去は、外すと sidecar の
  `launch_context_sha256` を別の有効な 64 hex へ書き換える変異が material 経路を通過する。
  不採用の結果 **production コードの差分はゼロ**になった。
- **単位 B (t080 base の collection prewarm) は実装しなかった。** 段 3 レンズ B が、
  prewarm を collection と重ねられるのは worker の collection 完了時差だけで約 51 秒の
  collection 全体ではないこと、t080 を全部消しても shard-0 の床が `277.84 + P` 秒で
  `P < 22.16` 秒という未立証の条件が要ることを示した。D104 決定 3 に従い land しない。
- **親 brief の誤りを段 3 が 5 件挙げ、全件受け入れた。** 残余範囲 (56.24→55.75 秒始まり)、
  host 台数 (9 走で 8 台)、「t080 上位 10 node は同じ base」(実際は 4 key)、
  「総仕事量 25% 減」(t080 全所要比であって除去可能な base 費用ではない)、
  「単位 A だけでは未達」(未走行の反実仮想)。
- **変異は 4 件を走らせ全件 baseline 緑からの rc=1 で検出、2 件は走らせる前に撤回した。**
  撤回は DW-M01 の再照準で、pair_id 正規化と guard 到達不能により SURVIVED と
  段 3・段 6 が独立に判定したためである。
- **変異 harness の射程外を実測した。** oracle が fixture の中にあると kill が pytest ERROR で出て、
  `FAILED ` 行だけを読む抽出器が 0 件を返し `PARSE_ERROR` になる。
  検出は rc と `errors=N` で確定している。{{D:fixture-owned-oracle-kills-are-parse-error}}。
- 実装子は Pegasus dispatch の `qstat -Q` が `Unknown user-id` で pytest を 1 件も実走できず、
  「実装済み・未実走」で戻した。実走はすべて親が行った。
- **受入全走は 5 回投入して 5 走目で緑**になった (`22319 passed, 68 skipped`)。
  1 回目は親が走行中に insight と fragment を書いて untracked を作り `prerun-clean` rc=70 で
  拒否された (親起因)。2〜4 回目の赤はすべて差分から到達不能で単独再走は緑、
  赤の node 集合が走ごとに移動した。この型は F57 に既載であり、緑が取れたので hold は登録していない。
- **shard-2 の wall は 3 走とも 300 秒未満 (218.92 / 277.80 / 222.32 秒)** になり、
  group は shard-2 の最大 worker 占有ではなくなった。
  **一方で最遅 shard は shard-0 へ移り (484.82 / 367.11 / 339.05 秒)、
  目標「最遅 shard を 5 分以内」自体は未達である。**

## 次の一手差分

### 更新

- [T-2273] **P1・単位 A 着地・目標は未達 → 次の手番は shard-0**: 受入全走の最遅 shard を
  5 分以内へ入れる作業。単位 A (shard-2 の group `p3-b4-material-report` の
  module fixture が作る replica 200 組を sidecar replay へ) を land した。
  group の worker 占有は 256.93〜308.57 → 146.54 / 177.0 / 153.3 秒、
  shard-2 の wall は 313.27〜365.94 → 218.92 / 277.80 / 222.32 秒になり、
  group は shard-2 の最大 worker 占有ではなくなった。
  paired 焦点走でも material module は 241.06 → 134.10 秒 (−106.96 秒、−44.4%)。
  **ただし最遅 shard は shard-0 へ移り (変更後 3 走で 484.82 / 367.11 / 339.05 秒)、
  目標そのものは未達である。** shard-0 は上位 worker がほぼ横並びの仕事量律速に近く、
  単一 node の短縮では閉じない。次の手番は shard-0 の最大 worker 占有の分解である。
  base: 0caffca2cd2caf79343117d6e6560e5348b318411a25b1e47a2a93c57e5dd803
- [T-2495] **P2・訂正**: 「受入の現在の床は `test_t080_*` 群」は *shard-0 の* 床としては
  正しいが *最遅 shard の* 床ではない。9 走の実測で最遅は 8 走が shard-2 だった。
  t080 の 11 consumer は 5 key に分かれ、上位 10 node は 4 key にまたがるので
  「同じ base を 10 回払う」でもない。短縮対象としての優先度は
  {{D:slowest-shard-floor-is-material-group}} の実測に従って決め直す。
  base: cbee9f6e1fdce7a6ea6f525470b8607039bb6c19b45bccc375d043089242c192

### 新規

- {{T:t080-prewarm-effect-separation}} **P2・新規**: t080 base の collection prewarm を
  起票するかを決める前に、(a) 重複検査除去による per-base 短縮量と
  (b) prewarm の非重複 tail `P` を**分けて**測る。D1708 が残した唯一の未検証方向だが、
  段 3 レンズ B の見積りでは重ねられるのが worker の collection 完了時差だけで、
  t080 を全部消しても shard-0 の床は `277.84 + P` 秒、目標には `P < 22.16` 秒が要る。
  効果が示せなければ D104 決定 3 に従い land しない。
- {{T:d1894-target-reinterpretation}} **P1・ユーザー裁定待ち**: D1894 は対象を
  「最大 worker 占有」と定め、前提として「床が `test_t080_*` 群へ移ったこと」の実測確認を
  要求した。実測は否だったので、親は決定本体に従い対象を「実測で最遅である shard の
  最大 worker 占有」と読み替えて実装した。この読み替えを追認してよいか。
- {{T:material-group-tail-8-nodes}} **P2・新規**: group `p3-b4-material-report` の
  残り 48 node のうち 8 node が 10.76〜12.72 秒ずつ (計約 90 秒) を占める。
  単位 A 後の group はこの帯が支配する。短縮するなら次はここだが、
  最遅 shard が shard-0 へ移っているなら優先度は下がる。
