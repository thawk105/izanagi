---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2766-pairing-adopt
seq: 1
title: [T-2766] 受入 shard 内 pairing を既定 on にして main へ入れる — 待ち手経由の実受入 A/B 隣接対 3 組で 3 対とも B が短く (対差 145.8 / 86.3 / 57.3 秒、対率中央値 19.6 %)、事前登録 (i) で land (コード + docs、branch worktree-dev-wave-t2766-pairing-adopt)
---

## 本文

- **依頼 = D2172 項 1 (択 (a)、2026-09-20 ユーザー裁定「推奨通りで」)。** opt-in 実装 (branch `impl-t2766-pairing-optin`、`0eabe67ba`) を cherry-pick (X1 `715bf37b7`) し、Codex author (gpt-6-astra / medium) が env gate・token・allowlist 行を撤去して既定 on にした (X2 `2404642c3`、main に対する正味差分は `conftest.py` と `test_acceptance_schedule_order.py` の 2 file +319 −7)。property 4 種 (scope / rank / partner / worker) は残した (P1)。opt-out は足していない。受理集合は不変 (順序と追加 property だけ)。一次資料は `output/insights/2026-09-20/t2766-pairing-adopt/README.md`、設計判断は {{D:pairing-default-on-adopted}}。
- **軽量版 (DW-C00) で段 2・3 を省き、段 6 は read-only レビュー 2 本 (過剰・削除 / 正しさ・整合)。** 本番 patch への must-fix は両レビューとも無し。must-fix 3 件はすべて集計器の入力契約 (段 4 の略記が古く、親の生成器とは一致していた — 前 wave の A session を流用した接続確認で閉じた) と、bytecode env の除外条件の事前登録漏れ (結果を見る前に launcher の env 契約として追加)。should は A/B の定義 (各走の tested_main に対する採用前 / 採用後)、門番観測の記録、測定量の限定、P1 の費用限定、cardinality 検算の nodeid 一意性という境界。code fix 0 件。
- **焦点走 (計算ノード、11 file): 1210 passed / 7 skipped。変異 matrix (独立 clone、X2、5 変異): baseline 緑、5/5 KILLED、期待 node 完全一致。** M3' (pairing 呼び出し削除) の kill 10 node はレビュー B の予測と一致。
- **A/B 実受入 (待ち手経由、A = 採用前 main の木、B = wave 木、順序 A,B / B,A / A,B、門番 leader ≤ 1 ∧ load < 60、14:47〜18:11 JST): 6 走とも child-green。** 最遅 shard (全走 shard-0) の JUnit wall の対差 ΔW = 145.8 / 86.3 / 57.3 秒、対率 29.1 / 19.6 / 12.6 %、対差の中央値 86.3 秒、対率の中央値 19.6 %、条件別中央値差 100.8 秒 → 事前登録 (i) 方向一致・閾値以上 → land。B の witness (被覆 100 %、rank 48〜95 = partner、多重集合の独立再計算、worker 復元) は 9 shard すべて true、A は property 0 件。
- **限定 (一般化しない):** 効果は前 wave (101.7〜144.3 秒、同一 tip の直接投入) より小さく対ごとに縮み、対 3 は閾値に近い 12.6 % (06-B は e2e 単体が 266 秒と遅い)。全対で main が動いた (対 1 は s8b_holdout_admission の test +615、対 2 は T-2800 の test 13 本削除など 31 file、対 3 は docs fold のみ)。A の tip 3 本は tested_main と tree 一致、B の tip 3 本は tested_main + 採用差分だけ (git で検証)。機序は未同定のまま (A 側 witness は取っていない)。
- **property の費用の実測:** junit.xml が受入 1 走あたり約 +13 MB (A 0.7 / 1.8 / 1.6 MB → B 2.4 / 6.2 / 6.4 MB、3.4 倍)。前 wave の「数百 KB / shard」より大きい。時間費用は分離していない。縮約・撤去は別裁定 ({{D:pairing-default-on-adopted}} の再訪条件)。
- **競走型の再試行 2 回 (子は走らず走表に含めない):** 03-B の `claim-self-unverified` は 02-B 成功後に B wave の lease (land 用、TTL 40 分) が保持されたままだった親の launcher の欠陥 → `wave_land_window.py release` で free にし、launcher へ「取得済みの走だけ終端で release」を追加。04-A の `postcheck` は merge 後に main が動いた競走 (verifier-capacity の land と衝突)。
- **main は測定中に少なくとも 10 回前進した** (peer 通知: T-2610、T-2796、T-2792、B-10 results、fig11、T-2800、T-2724、verifier-capacity、T-2153、T-2795)。各走の tested_main / tip は README §6。
- 工数: codex 子 3 本 (author 1、review 2)。計算ノード job: 焦点走 1、変異 probe + final (baseline 各 1 + 変異各 5 = 12)、受入 6 走 (3 shard) + 最終受入 1 走。

## 次の一手差分

### 完了

- [T-2766] 受入 shard 内 pairing を既定 on にして main へ入れた (X2 `2404642c3`)。待ち手経由の実受入 A/B 隣接対 3 組で 3 対とも B が短く (対差 145.8 / 86.3 / 57.3 秒、対率中央値 19.6 %)、事前登録 (i) で land した。効果の限定・条件差・property の費用は `output/insights/2026-09-20/t2766-pairing-adopt/README.md` §1・§6・§7。
  remaining: none
  base: d13fe763b710abacf66a6134e11a83fb78466133bd1cc5ae3e09d2c447b80c18
