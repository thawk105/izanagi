---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: dev-wave-t2724-chain-land-2
seq: 1
title: [T-2724] 保存枝 chain (X1'/X2) と G を merge し三軸走査 hit 4/4・焦点走 8 file 0 failed を実測したが、受入全走が B-10 の freeze-tree byte pin 1 node で赤になり chain は land せず記録だけを land した (docs のみ、branch worktree-dev-wave-t2724-chain-land-2、merge 済み状態は branch t2724-chain-land-2-saved、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2724] 保存枝 chain/X2/G を main へ取り込み受入・land する。着手直前の local main から fresh worktree を作る。取り込み対象 = branch `worktree-dev-wave-t2724-freeze-g1-gen` (tip `229982652`)、chain の保存枝 `freeze-g1-chain-t2724` (`4d8fb93b7`)・`freeze-g1-chain-t2724-merge-prepared` (`b227d0d91`)・`freeze-g1-gen-t2724` (`32ba8cae4`)・`scratch-t2724-chain-check` (`8298f7430`)。正本 = D2154・D2120 項 2、insight t2724-t080-defer-active-v2 と t2724-freeze-g1-chain-land。受入が赤なら land せず原因を記録して終端 (規律 2 を緩めない)。人間手番の A / X の発効と W-5 実走は本 wave に含めない。実装面の変更が要れば Codex author (D95)。本題の取り込みだけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- 軽量版 (DW-C00): 設計択一なし・実装面差分ゼロのため段 2・3・5・6 の子は起動せず、merge の整合は blob OID 照合・三軸走査・焦点走・受入全走の実測で担った。一次資料は `output/insights/2026-09-19/t2724-chain-land-2/README.md` (evidence: 走査射影・焦点走要約・受入赤の junit 抜粋)。
- 取り込み形: 着手直前 main `2ba400087` から fresh worktree → merge 1 `3440c6620` (= main + G wave 保存 commit `229982652`、21 file 全追加) → merge 2 `87dcbe5a4` (= + X2 `4d8fb93b7`、候補 1 file)。凍結成果物 8 file の blob OID は保存枝と全件一致、gitlink 不変、競合なし。provenance 8 件違反なし、記録 commit `b217b24a7` 後の全史監査 11,625 件・新規違反なし。`merge-prepared` と `scratch` は merge 元にしていない。
- 実測 (login): 三軸走査 (権威 CLI) は merge 後の木で rc=1、rr80 / rr20 とも hit 4 (official 床値 run dir の 3 file + 候補)、positive control 218 — D2120 項 2 (a)(d) の設計どおり。実測 (計算ノード request 10715.nqsv): chain + G + X2 の木で焦点走 8 file (oracle_driver / floor_campaign / ratified_freeze / holdout_freeze / frozen_artifacts / oracle_manifest / t080_freeze_migration / real_repo_serialization) が **1211 passed / 12 skipped / 0 failed、369.23 秒**。前回 wave の非 hold 45 node の赤は A-3 + fixture 切離し (entry 1683) 後の main では X2 候補を含む木でも再現しない。
- G wave の未 fold fragment 3 片は dry-run が `[T-2724]` の base-mismatch で赤になったため、削除せず内容を改めた (worklog 片は本文末尾に現況 1 項 + 次の一手差分を空に、decisions 片は末尾に現況 3 行)。改訂後 dry-run rc=0。**改訂は保存枝に入っており main には未着地。**
- **受入全走 attempt 1 (claimed main `a99425b66`、merge `0a799da6c`) は赤: 1 failed / 25311 passed / 69 skipped。** 赤 = `test_backoff_extended_sweep.py::test_b10_freeze_tree_bytes_match_the_wave_local_gate` 1 node = B-10 job script (`tools/pegasus/b10_backoff_grid.sh` 22 行) が事前登録した freeze tree (`output/s1-freeze` + `output/s8b-freeze` 全 file) の bytes digest `c405c742…` の固定 pin。G の `output/s8b-freeze/holdout_freeze.v2.g1.json` 追加で `6a4ee1ef…` に変わった (親と相談子 B が独立に検算: G の 1 file を除くと旧値に戻る)。gate の拒否は正しく、hold / skip / 条件付き assert は採らない。段 1 の pin 閉包は成果物 file 名の grep だけで directory 全体 digest の pin を取り逃した (F30 の再発として failures 台帳へ記録)。
- 裁定 (ユーザー委任「codex と相談して決める」に従い read-only 2 レンズ、逐語は job dir `artifacts/…/s3-a.md` / `s3-b.md`): レンズ A = 択 3 (pin 更新は将来の B-10 起動契約の変更で D2120 (b) の射程外、brief と依頼の scope 外。事前登録の書き換えには当たらず絶対規律の必然的違反でもない)、レンズ B = 択 1 (2 file・3 literal の更新で足り、複数値受理・prefix 除外・hold は refuted、変異 2 件と受入外 consumer の追記が要る)。**親は択 3 を採り、chain を land せず記録だけを land した。** pin 更新は次 wave の段 1 で別 context・独立レビュー付きで行う (設計は insight §7)。
- 保存: merge 済み状態 (main `2ba400087` + 2 merge + 記録 + 受入 merge) は branch `t2724-chain-land-2-saved` = `0a799da6c`。wave branch は main `657e1e5a7` へ戻し、本 insight と fragment 2 片だけを積む (entry 1640 と同型)。
- 受入 attempt 2 (docs-only) は起動前検査の dispatch が、親が同じ worktree で背景実行していた全史 provenance 監査の pending hold に当たり rc=70 (orphan-hold、木の内容と無関係、DW-C00 の直列規則を親が破った)。監査終了後に attempt 3 を直列投入し、その受領証を land に使う。
- 工数: codex 子 2 本 (相談 A / B、`gpt-6-astra` / medium)。親の実走は insight §8。専用 handoff は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2724-chain-land-2/HANDOFF.md`。

## 次の一手差分

### 更新

- [T-2724] **P1・chain/X2/G の merge は済み受入赤 1 node で未 land → 次 wave: B-10 freeze-tree pin を Codex author が更新 (新 D + 変異 2 件 + 負例 + 独立レビュー) → chain/X2/G を受入・land → 人間手番 A / X → W-4 spec (T-750 P-1) → W-5**: 保存枝 `t2724-chain-land-2-saved` (`0a799da6c` = main `2ba400087` + X1'/X2/G の merge 2 本 + 記録 + 受入 merge) を着手直前の main へ固定 SHA で merge し、`orchestrator/tests/test_backoff_extended_sweep.py` 1671 / 2025 行と `tools/pegasus/b10_backoff_grid.sh` 22 行の freeze-tree digest literal を G を含む tree の値 (着手時に再計算、2026-09-19 時点 `6a4ee1ef…`) へ更新する (算法・比較・除外集合は不変、複数値受理・prefix 除外・hold は不採用)。変異 (test literal だけ旧値 / job 定数だけ旧値) と負例 (別 file 追加・1 byte 変更・G 削除を拒否) を実測し、decisions に「B-10 の起動契約を D2120 項 2 (b) の G を含む tree へ更新、旧測定の解釈は不変 (規律 7)、新 phase の事前登録成立ではない」を記録、`docs/b10-backoff-static-tail-submission.md` と `docs/phase3-8b-restart-runbook.md` に chain 導入後の注意 1 行、results 稿と provenance.json の旧値は不変。その後 A / X はユーザーが保存枝の `output/insights/2026-09-18/t2724-freeze-g1-gen/README.md` §5 の手順で commit。設計の正本 `output/insights/2026-09-19/t2724-chain-land-2/README.md` §6〜§7。(e) T-1851 残件と保存枝の削除はユーザー指示時のみ。
  base: dbbbfbd852f3bc3cb804255505982227ab8327d59fce746d2f0a607ce253f207
