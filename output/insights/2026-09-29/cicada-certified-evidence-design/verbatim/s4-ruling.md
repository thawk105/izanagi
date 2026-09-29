# 段 4 裁定 — md_24 (Cicada の certified 証拠面の設計と推奨)

入力: s1-brief.md、plan.md (段 2)、consult-a.md (実装する側)、consult-b.md (しない側)。裁定前の再走査: local main = 8fe87f852 (wave 開始から不変)、docs/spool の worklog / decisions / failures に未 fold fragment 0 件、[T-2874] を触る fragment 0 件。

## 所見の裁定

| ID | real / refuted | 採否 | 反映先 |
|---|---|---|---|
| A1 U が片方向 (公開版 → W 行の被覆なし) | real (具体列: 公開後 emit 前に write set から落とすと巡回が消える) | 採用 | 必須面 U を「設置・公開の台帳 ↔ W 行」の双方向照合に改める |
| A2 B の窓 | real | 採用 | B = 退役・再利用を消えない事象として TRACE 専用台帳に積み、read 登録から tx 終了までに当該版の事象があれば違反。ver_ を再読しない。CCBench の workload (ycsb.hh:120-143、tpcc.hh:102-114) は commit 前に body を使い終えるので tx 終了での照合が消費区間を覆う (前提として明記)。REUSE_VERSION=0 は対象外 |
| A3 API intent・集合遷移・R/W の双方向 | real | 採用 (段階を分ける) | write intent (I) と read の成功 API ↔ read set の照合を「certified 化するなら必須」に置く。Silo の現行連言 (I 無し) より強いが、forwarding が read 経路を触るので要る。中間案では read 側だけ入れる |
| A4 版順・終状態 | real | 採用 | P1 を「観測した読みについての 1SR」に限定。終状態は主張しない |
| A5 H の件数一致は恒真 | real | 採用 | 親 P4 を撤回。H は発火の証拠と呼ばない。発火の証拠は各分岐の壊し patch だけ |
| A6 / B-1 文面検査は header を読まない | real | 採用 | certified 化には header を含む source snapshot か site ごとの call path 評価の設計が先に要る。.cc の薄い wrapper で「在る」を満たす形は却下 |
| A7 壊し patch の設計 | real | 採用 | B = 退役事象がカウンタへ届く最小列 (異常終了を成功扱いにしない)、U = 公開漏れ 1 件を後続待機なしで作る、P = 比較の内側で壊す |
| A8 全層の列挙 | real | 採用 | 案 A の完了条件に全層を列挙 |
| B-2 certified でも一般命題にならない | real | 採用 | 論文の文を「一般論証 / 実装の観測履歴 / 未証明条件」の 3 層で並べる |
| B-3 しない案の盲点 | real | 採用 | 案 B の弱点として明記 |
| B-4 判定器変更の隠れた費用 | real (親が照合: campaign_lock.py:47-73 の exact 96 path closure に verifier 7 file) | 採用 | 案 A の費用に lock 再批准・fixture・capacity baseline・変異・受入を加える |
| B-5 見積りの別欄化 | real | 採用 | 算術の見積りと未測の項目を分ける |
| B-6 P7 の根拠不足 | real | 採用 | 親 P7 (案 A を推奨) を撤回 |
| plan の B (Version 外の世代台帳) | real | 採用 | A2 と統合 |
| plan の診断 J/K/L/N | real (帰属に有用) | 設計に記載・実装推奨には含めない | 未知 tag は ParseError なので、出すなら parser 対応が先 |

refuted: なし。親 brief の (P4)・(P7) は撤回、(P1) は限定付きで維持。

## 推奨の確定

**中間案 M を推奨する** (段 3 の 2 レンズが独立に一致)。
- M = 既存の out-of-tree 計装を広げ、B (読み束縛: 退役・再利用の事象台帳、tx 全区間) と U (設置・公開 ↔ W 行の双方向) と read 側の API 照合を `#if TRACE` 内で実装し、repo 外起動器の合否に入れる。壊し patch 2 本 (B・U) で発火を示す。判定器の production と campaign は変えない。YCSB point read / update、REUSE_VERSION=1、INLINE_VERSION_OPT=0 に限る。
- 案 A (certified 化) は M の後に、izanagi の campaign で Cicada を certified の門に通す具体的な登録が現れたときだけ選ぶ (DW-G04)。
- 案 B (今のまま) は論文の核心 U0 の典型的な失敗を見逃しうるので推奨しない。

## 実装面・変異・受入

この wave は docs-only (一次資料 + fragment)。実装面の差分 0 → 変異 matrix 免除。受入全走は免除せず段 7 の記録前に走らせる。段 5 は無し、段 6 は一次資料から事実を再抽出する docs-only なので独立 read-only レビュー 1 本を残す (DW-C00、md_24 の注意)。

## 一次資料の構成 (plan v2)

1. 依頼と結論 / 2. 現行の X・P・I と certified の意味 / 3. Cicada の忠実性の脅威と証拠面 (必須・診断・不要) / 4. 観測者効果 / 5. 費用 (算術と未測を分ける) / 6. campaign 供給の要点 / 7. 3 案と論文に書ける文の差 / 8. 推奨とユーザーの判断点 / 9. 確かめたこと・確かめていないこと / 10. 工程と逐語。
