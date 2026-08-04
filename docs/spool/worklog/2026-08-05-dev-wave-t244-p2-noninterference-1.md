---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t244-p2-noninterference
seq: 1
title: [T-244] D121 P2 の非干渉検査は実装を差し戻す — 現行 critic payload が既に 5 bit を可逆に運び、payload 不変の字面検査は恒真になる (docs のみ、branch worktree-dev-wave-t244-p2-noninterference)
---

## 本文

- **依頼の前提 1 件を実測で反証した。** 依頼は P2 を「無条件義務 8 件で唯一の未着手」としたが、
  worklog の実体エントリは「P2 / P7 / P9 は未着手」と書いており、以降のエントリはすべて carry である。
  **未着手は P2・P7・P9 の 3 件**である。対象を P2 とする方針は変えず、記録のみ行った。
- **本 wave の中心前提も実測で反証された。** 「payload の field も値も変更せずに P2 の payload
  射影面を閉じられる」は成立しない。現行 production の critic payload `harness_result.variant` は
  候補述語 (5-bit wire の正準関数) を preimage に含む 12 hex であり、候補 universe が 32 点しかない
  ため表引きで wire へ一意復号できる。親・段 3 レンズ A・レンズ B が独立に 32 点を静的列挙し、
  **ID は 32/32 すべて一意、ID 中に自分自身の wire 字面が現れるものは 0/32** で結論が一致した。
  したがって payload 不変のまま書ける検査は字面 tripwire に限られ、**現行 baseline の実漏洩に
  対して一度も発火しない**。詳細と裁定は {{D:t244-p2-literal-tripwire-remand}}。
- **段 3 の敵対 2 レンズはいずれも NO-GO** を返した (レンズ A = BLOCKER 4、レンズ B = BLOCKER 3、
  所見計 19 件)。親は 19 件すべてを real/refuted に裁定し、real 14 件・refuted 4 件・縮小採用 1 件とした。
  段 2 プランの「現行 baseline は赤にならないので GO」は字面モデルでのみ成立するとして refuted。
- **親の provisional 裁定 4 件のうち 3 件が反証された。** (P1) auditor へ実効 diff と digest を渡して
  よいは D121 の recipient matrix に反し、かつ検査の期待値を被検査 producer から取る自己参照だった。
  (P3) 「許可入力 = 現行 key 集合」は循環していた。(P2) 「32 点 digest は常に 5 bit 漏洩」は過大で、
  `I(W;ID | 公開 codebook) <= H(W) <= 5 bit` へ縮小して採用した。
- **親の手順違反を 1 件記録する。** 段 1 brief の環境記述「login ノードで pytest」は正本違反である
  (ログインノードでの pytest は単一 nodeid も含めて禁止、親が計算ノードへ dispatch する)。
  本 wave は実装差分ゼロで pytest を走らせなかったため実害は生じなかった。
- **ユーザー裁定待ちが 5 件ある** (U-1 critic recipient policy、U-2 auditor declassification の定義、
  U-3 「IR schema SHA」の preimage、U-4 実装 wave の再起票可否、U-5 dev-wave 予算の飽和)。
  U-1〜U-4 はいずれも payload の field か値の変更を伴い、親の裁量外である。裁定パッケージの正本 =
  `output/insights/2026-08-05_t244-p2-noninterference/s4-adjudication.md`。
- **段 8 の自己改善が予算で実施不能だった。** 実測に基づく改善候補 2 件 (段 1 の環境確定に
  テスト実行場所と dispatch 経路を含める / 段 2 の prompt で brief の判定基準を狭めない) を記録したが、
  `docs/dev-wave/**` の合計予算は本 wave 開始時点で 25,196 / 25,200 bytes と残り 4 bytes しかなく、
  必要な +142 bytes が入らないため**両方とも撤回した**。既存の安全義務を削って捻出することはしていない。
  予算そのものの扱いは裁定 U-5 として返す。
- 工数は codex 子 3 本 (段 2 プラン 1 本、段 3 敵対 2 本、いずれも read-only・reasoning=max)。
  実装子と fix 子は起動していない。

## 次の一手差分

### 更新

- [T-244] **P1・P2 は実装差し戻し。ユーザー裁定 4 件待ち。未着手は P2・P7・P9 の 3 件**:
  **P2**: payload 射影面の非干渉検査を新規 leaf として実装するために起票したが、
  段 3 の敵対 2 レンズが独立に NO-GO を返し、**実装せず設計メモとして凍結した**
  ({{D:t244-p2-literal-tripwire-remand}})。決め手は 3 件 — (i) 現行 critic payload が既に
  wire へ可逆な 12 hex を運んでおり payload 不変の字面検査は恒真になる、(ii) 是正は critic の
  recipient policy (D121 の未解決択一)・auditor declassification・IR SHA preimage の 3 裁定に
  依存し親の裁量外、(iii) `_invoke` 冒頭の fail-closed raise は build mode で terminal report を
  作れない経路を残す。**P2 は依然 FAIL** で、無条件義務 8 件のうち充足は P10 の 1 件のみ、
  D114 の上限 1 も不変。実装差分がないため変異 matrix と受入全走は対象外。
  **ユーザー裁定待ち U-1〜U-5** = critic recipient policy (推奨 (i) 不透明 ID 置換、受理集合に
  波及するため D96 手続)、auditor declassification の定義 (推奨 (ii) 現状を明示的 declassification
  として会計し reflux-control 実装時に戻す条件を同時固定)、「IR schema SHA」の preimage
  (推奨 = emitter source + 32 golden の複合)、実装 wave の再起票可否 (推奨 = U-1〜U-3 確定後)。
  **U-5** = `docs/dev-wave/**` の予算飽和 (残 4 bytes) で段 8 の自己改善が実施不能である件
  (推奨 = 陳腐化節の棚卸しと L2 のテスト移管を別タスクで行う。予算値の引き上げは提案しない)。
  確定後に実装すべき形も記録した — secret を候補 wire、公開入力を固定して provider へ渡る
  serialized bytes の同一性を見る indistinguishability 検査であり、planner/coder は PASS、
  auditor は明示 declassification、**critic は FAIL になる**と予測済み。
  **依頼が前提とした「無条件義務 8 件で唯一の未着手」は誤りで、未着手は P2・P7・P9 の 3 件**である。
  P1・P3・P4・P5 の状況と逐語の所在は前エントリのまま変わらない。
  本 wave の逐語 = `output/insights/2026-08-05_t244-p2-noninterference/`
  base: 90a545202dce7e61e08d3c1b7830e95468ce4c8625b9514dcf272505814be10b
