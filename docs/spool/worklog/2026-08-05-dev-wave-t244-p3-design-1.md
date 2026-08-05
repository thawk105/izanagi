---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t244-p3-design
seq: 1
title: [T-244] P3 の (1)(2)(3) を設計裁定パッケージとして起草した — bootstrap と世代移行が不可分と実測し、択一 10 件を裁定へ返す (docs のみ、branch worktree-dev-wave-t244-p3-design、実装差分なしのため変異 matrix と受入全走は対象外)
---

## 本文

- **依頼は worklog (200) のユーザー裁定で委任された (1)(2)(3) の設計起草 + D163 の起動不能の解消案。**
  裁定は「実装しない」で段 5・6 を飛ばし `4→7→8→9` とした ({{D:t244-p3-design-package}})。
  依頼が設計起草なので実装しないこと自体は前提どおりだが、あわせて**設計案をそのまま実装 wave として
  起票してはならない**と裁定した。段 3 の敵対 2 レンズが独立に NO-GO を返している。
- **承認済み裁定の前提が 2 件動いていた (段 1 前提実測)。** (a) D163 が見た ledger は v1 で、間に
  P4 wave (`61fc5202`、D166) が land して v2 になっており、**(198) の裁定パッケージが引く file:line は
  すべて stale**。(b) batch の distinct 制約が候補平文でなく commitment に掛かる形へ変わり、
  **同一候補 1 点の反復でも合法 batch が成立する** — (198) の「複数候補にしないと batch を作れない」は
  この意味で崩れていた。
- **親が D163 より強い事実を 2 件実測した。** production runtime の初期化は入口の欠落ではなく
  `_initialize_locked` 冒頭の**明示的な禁止**である。かつ genesis が authority の全 entry を焼き込み
  origin 追加 event が無いため、**最初の genesis が origin 集合を永久に固定する**。
  したがって bootstrap と世代移行は不可分であり、世代移行を決めずに最初の genesis を打てない。
- **親の provisional 裁定 3 件が反証された (段 3)。** 「単一候補 × R replicate が予算束縛を実体化する」は
  撤回 (予算 counter が動くのは batch commit 受理時だけで、それを呼ぶ production caller が無い)。
  「世代移行は既存型の適用で新機構を発明しない」は言い過ぎ。manifest preimage の分類は
  「既存 3」でなく「既存 2」(CCBench commit OID は full 40hex 必須だが現行 pin は 7 文字 prefix)。
  最後の 1 件は段 2 と両レンズが**独立に同じ訂正**を出した。
- **レンズ A の中心所見を採用した** — ledger の `cardinality` は member row 数であって候補数ではなく、
  単一候補 × replicate をそのまま記録すると将来の P4 consumer が候補 1 点を 2 点以上と誤認する。
  散文の断りでは機械的誤認を防げないため、行数と候補数を別 field にする形を推奨に格上げした。
- **レンズ B の会計を採用した** — 全案を実装しても埋まるのは 11 層のうち機構面で最大 6 層、
  第 1 層 (authority 値・発行) が空で正の artifact path も無いため**成果として閉じる層は 0**。
  同レンズが提示した「既存 E 段 CLI を使う 100 行以内の生死実験」を推奨の段取りに採った。
- **択一 10 件 (U-1〜U-10) と scope 外 real 所見 6 件を裁定パッケージへまとめた。** 正本は
  `output/insights/2026-08-05_t244-p3-design/README.md` §9。U-1〜U-4 は互いに独立でない。
- **手順違反 1 件 (自己申告)**: 段 2 の子を投入した直後に上記 2 件の実測を得たため、
  前提未確定のまま子を走らせる `DW-S01` 違反を是正すべく子を停止し brief ごと投入し直した。
  ところが**停止が効いておらず 2 子が同じ `-o` path へ並行出力していた** — 先に完走した
  更新後 brief 版を採用済みで、後から上書きした旧 brief 版は別名で保存した。採用側の同一性は
  内容 (N13/N14 の判定節の有無) で確認できる。順序が逆なら誤った成果物を採用していた。
  {{F:concurrent-codex-same-output-path}} に記録した。
- 子の工数: 段 2 が約 55 分 (停止し損ねた重複子を含む)、段 3 の 2 本が並列で約 20〜30 分
  (いずれも codex `gpt-5.6-sol`、`reasoning=max`、`sandbox=read-only`)。セッション異常なし。
- **受入は実装差分ゼロのため全走を射程外とした。** docs 変更に影響する検査
  (`check_docs.py` と spool の dry-run) のみ実施した。
- **段 8 自己改善: 候補 2 件を検討し、いずれも本 wave では実装せず既存 [T-432] へ集約した。**
  (1) `DW-O01` の起動形 — worktree 隔離の背景 job では inline `bash -c` が guard に拒否され、
  launcher script を Write して `nohup setsid bash <script>` で起動する必要がある。
  worklog (219) の段 8 が同じ実測をしており、**本 wave が独立 2 例目**で `DW-G03` の族一般化条件を
  満たす。(2) `DW-O01` の中止手順と `DW-O02` の再投入時 path 一意性 ({{F:concurrent-codex-same-output-path}} の
  恒久対応 (3))。**両方とも `docs/dev-wave/operations.md` の予算残 35 bytes (8365/8400) に入らない。**
  予算引き上げは独立審査事項であり本 wave では扱わない。[T-432] は既に「`DW-O01` へ背景 job の
  detach 必須を足す」を所有しているため、新しい T を起こさず同項へ集約した。
- 逐語の正本 = `output/insights/2026-08-05_t244-p3-design/`
  (README = 裁定パッケージ正本、brief / s2-plan / s3-lensA / s3-lensB / s4-adjudication を同梱)。
  段 2 の重複子の出力は `s2-plan-stray-aborted-child.md` として分離保存した。

## 次の一手差分

### 更新

- [T-244] **P1・P2 は実装差し戻しでユーザー裁定 5 件待ち。P3 は (1)(2)(3) の設計パッケージが
  ユーザー裁定待ち ((4)(5) は裁定済み)。P4 は ledger 側契約に適合 (充足は未達)。P5 残余は U-2。
  未着手は P7・P9 の 2 件**:
  **P3**: 設計 wave が (1)(2)(3) を起草し、**択一 10 件 (U-1〜U-10) をユーザー裁定へ返した**
  ({{D:t244-p3-design-package}})。正本 = `output/insights/2026-08-05_t244-p3-design/README.md` §9。
  推奨の骨子 = preimage の trust root は捕捉 commit の名前付き artifact bytes (非自己参照 topology 必須) /
  production 初期化の明示禁止は boolean でなく authorization 型で条件解除し二相 crash-idempotent に /
  世代移行は epoch router (bootstrap と不可分) / 予算束縛は pre-query reservation event (D96 の射程) /
  wiring host は 8c (pilot 限定)・生死実験の宿主は E 段 loop の既存 CLI /
  単一候補 × replicate は「候補 batch」と記録しない。
  **未確定でユーザーの情報が要るもの** = U-7 (evidence artifact の linux-baremetal 再測定が可能か。
  現候補は clocks・pin・numactl・build_admissions・workload cell の 5 点で不適格と確定)。
  **原理的に閉じない残余** = 予算 root の同一性 (別 clone・全削除・履歴書換えで作り直せる。
  git-common-dir 束縛が塞ぐのは同一 clone 内の worktree 回避だけ)。
  scope 外 real 所見 6 件 (full manifest の sink 束縛 / rep_evidence の自己申告性 /
  reservation・seal・sidecar の crash recovery / recipient schema の恒真化 risk /
  別 origin の global CAS 妨害 / epoch router の並行性契約) も同パッケージに含む。
  **P3 は依然 FAIL**、cap-lift も FAIL、D114 の上限 1 は不変。
  **P1**: 変わらず機械部品のみで未充足。**P2**: D164 で設計メモ凍結。
  **P4**: D153 の W1〜W5 を ledger 側で実装完了 (D166)。**P4 充足は名乗らない**。
  **P5**: U-1 実装済み、残余は U-2 のみ。**未着手**: P7・P9。
  base: 7e91370a2e352694ae2a54bf0f91a9c4493edcfc028d97bc059ae493fd48bf66
- [T-432] **P2・`DW-O01` / `DW-O02` の是正 3 件が同じ予算残に阻まれている**: `DW-O01` へ背景 job の
  detach 必須を、`DW-M05` の照合規則へ「並行 wave の子に一致しないこと」を足す (根拠 F103 / F104)。
  2026-08-05 に**加筆対象が 2 件増えた** — (a) worktree 隔離の背景 job では inline `bash -c` が
  guard に拒否されるため launcher script + `nohup setsid bash <script>` が要る
  (worklog (219) と本 wave の独立 2 例、`DW-G03` の族一般化条件を満たす)、
  (b) detach した子の**中止手順**と、再投入時の出力 path 一意性 ({{F:concurrent-codex-same-output-path}})。
  **いずれも `docs/dev-wave/operations.md` の予算残 35 bytes (8365/8400) に入らない。**
  予算引き上げは独立審査事項であり、陳腐化ルールの削除・テスト化で空ける経路も未着手。
  base: 30f340d6cd45be04e035624b6936cad789bb5f6665635ad4206d1819b763820a
