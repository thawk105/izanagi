---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-r29-items4-9-diagnosis
seq: 1
title: [T-2842] 第 29 回 /rulings 項 4・項 9 を診断した — 置換で満たせない単独走は延べ 10〜20、t2797 型 7 本を別 job で払うと固定費 1,208 秒 (うち 1 本の待ち 1,050 秒)、項 9 の 2 例は既裁定 [T-2820] が覆う (insight のみ、実装 0 行、branch worktree-dev-wave-r29-items4-9-diagnosis)
---

## 本文

- D2206 項 4 ([T-2842]) と項 9 ([T-2843]) を 1 wave で診断した。軽量版 + 診断 wave の最小 (段 2 plan 1 本、段 3 相談 1 本、段 6 独立 read-only レビュー 1 本、実装面 0 行、変異免除)。
  結果と表は `output/insights/2026-09-21/r29-items4-9-diagnosis/README.md`。標本の as-of は開始 gate の 2026-09-21T14:06:02+09:00、(a) の標本は前回診断と同じ 07:38 固定の 12 wave。
- **段 3 相談 (20 所見、real must-fix 7) が総括「現状のまま再提示は不可」を返し、親の計画を 3 点で縮めた。** (1) generic 1 job に束ねる腕 C は、inline の `bash -c` でも
  反復・計時・rc 集約を新しく実装しており依頼の「新しい harness を作らない」に反する (file を作らないことは理由にならない)、(2) 腕 C / S の 1 対は node・cache・時刻・環境差を分離できず
  D289 決定 (2) の条件も満たさないので束ねの効果を識別できない、(3) 親の事後試算「残件 16〜20」は候補の列挙で下限の証明になっていない。親は全件採用し、腕 C と 2 本目の worktree を取りやめ、
  既存 runner だけの直列 10 job (集合 21 → 単独 7 → 集合 23 → 集合 21) に縮め、(a) は構造上の上下限 (1 job = 1 invocation、集合走は各 wave に最低 1 本残る) だけで出した。
- **段 1 で見つけた新事実:** (i) 項 9 の 2 例 (受入赤 5 node) はすべて `test_ccbench_spawn_sites.py` で、2026-09-21 に裁定済み・未実装の [T-2820] (D2194 項 8) が両 wave で発火する。
  第 29 回の材料 (索引 項 9) はこの既裁定を引いていなかった。(ii) D325 の理由欄「Pegasus では実行を伴う焦点走は必ず計算ノードへ dispatch」は現行 runner の login bounded local と合わない
  (別 process 義務は変わらない)。(iii) pegasus02 の他ユーザーの `/tmp/.git` (2026-09-07 作成) は本 wave 中も現存し、login local の layout 系 test の偽赤型が残っている。
- **再提示 ([T-2842] の更新):** [T-2832] (i) の実現手段は M1 置換 + M3 別 job で今すぐ運用に戻し、runner 改修 R2 は今は実装しない、を推奨として返した (insight §6)。
  本試行の単独 job 7 本の固定費は 6 本が 1 本 18〜26 秒で、費用の 88 % は長い待ちの帯 (17 分半) に入った 1 本だった。その帯の頻度は推定していない。
- 計算ノード job 10 本 (14:35:24〜15:23:31 JST、rc 0 が 10 本、赤 0) の長い待ち 2 本 (1,064 秒・1,050 秒) は、前回診断の長待ち 3 本 (1,007 / 1,020 / 1,020 秒) と同じ帯にある (観察のみ、原因は未帰属)。
- 計測後、記録の前に local main `bea98c67d` へ `--ff-only` で揃えた (本 wave の commit 0 の時点、衝突 path 0、submodule 差 0)。
- 受入全走は記録 commit を含む最終 tip に land 前に 1 回投入し、受領証は job dir と land の記録が持つ。
- 工数: codex 子 = plan 1 + consult 1 + review (段 6) の read-only のみ (gpt-6-astra / medium)、親の計算ノード job 10 本 (chain 2,887 秒)。

## 次の一手差分

### 完了

- [T-2843] 焦点走から漏れた exact 目録 test の既知 2 例 ([T-2737] の define 目録、[T-2797]) は、受入赤 5 node がすべて `orchestrator/tests/test_ccbench_spawn_sites.py` で、
  既裁定・未実装の [T-2820] (D2194 項 8、DW-O26 inventory 群 4 → 6) が両 wave (どちらも production を変更) で発火して同 file を集合に載せる。新しい択は不要で、実装は [T-2820] が担う。
  追加実行時間は同じ計算ノードで連続した 1 対で集合 21 file に対し RUN +13 秒 (pytest +11.58 秒)、同 file 単独は RUN 80 秒。現行の module 名探索は fix 前の tip で同 file を引けない (git grep hit 0)。
  列挙型探索 (130 file) は局所策にならない。根拠は `output/insights/2026-09-21/r29-items4-9-diagnosis/README.md` §5。
  remaining: none
  base: 67e1ef5a7618a73f521b595707585d8be293d4557fe303f3366c77167c993e6e

### 更新

- [T-2842] **P3・ユーザー裁定待ち (D2206 項 4 の再提示)**: [T-2832] (i) (変更 test file ごとの別 process 単独走) の実現手段の択一。
  (a) 07:38 固定の 12 wave で未確認 20 のうち、既存の集合走 1 本を単独走 1 file に置き換える形で覆えるのは構造上最大 10、置換で満たせない残件は延べ 10〜20 (上端寄り)。
  (b) runner 改修 R2 の最小案は焦点走専用の複数 invocation 入力で、dispatcher の task 追加・DW-O26 の pin 変更は不要、費用の中身は invocation ごとの env・rc・結果記録・途中失敗、
  規模は設計仮説で本番 250〜450 行 + test 200〜400 行。改修なしの既存経路は generic 1 job (命令列は実装面で Codex author の launcher が要る) と login bounded local (pegasus02 の `/tmp/.git` の偽赤型が残る)。
  (c) 1 試行: t2797 の変更 test 7 file を 1 file = 1 job で直列に投げると wall 1,336 秒 = RUN 128 秒 + 固定費 1,208 秒 (うち 1 本の待ち 1,050 秒、他 6 本は 1 本 18〜26 秒)。
  束ねる手段が消せるのは固定費で、束ねた job の待ち・内側 RUN の変化は未測定。推奨 = M1 置換 + M3 別 job で (i) を今すぐ運用に戻し、R2 は今は実装しない。
  R2 を再提示する目安は、M3 の単独 job が長い待ちの帯に入る例が複数 wave で出たとき、または held 診断を同じ job に入れる需要が再発したとき。
  根拠は `output/insights/2026-09-21/r29-items4-9-diagnosis/README.md` §2〜§4・§6。
  base: 8f812a9d730315ad6406cda58d8df3f469b591141186affdbf79e25f1a6a2747
