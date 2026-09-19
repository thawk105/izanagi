---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: dev-wave-test-inventory-prune
seq: 1
title: 低価値テストを 4 分類で棚卸しし意味確認で確定した重複 6 node を削除した (コード + docs、branch worktree-dev-wave-test-inventory-prune)
---

## 本文

- ユーザー依頼 (背景 job 151d1045): `orchestrator/tests` を (A) 死んだ対象 / (B) 冗長 / (C) 撤回済み機構 / (D) 派生値 pin の 4 分類で棚卸しし、(A)(B)(C) は Codex author が削除して変異 harness で冗長性を示す、(D) は削除せず裁定パッケージで返す。verifier・hooks・check_docs・provenance・受入 launcher の test 30 file は最初から除外。scope 外 = production 変更・hold 方針変更・新 gate。
- 結果: 静的 scanner (Codex author、fix 1 巡) の候補 A 112 / B 35 / C 1 / D 291 関数を read-only plan で意味確認し、相談 2 本 (正しさ境界 / 過剰・削除不足) で攻撃した。削除できると確定したのは重複 6 node だけ (`test_s8b_holdout_freeze.py` の parametrize 重複 1 row、`test_p3_s4_loop.py` の同値関数 1 + 同値 row 4)。(A)(C) は 0 件、(B) の AST 同一 7 組は同名 alias が別 module を指し非重複、B2 の 26 row は型境界 (`1`/`1.0`/`True`)。相談 B が scanner 外で p3_s4_loop の 5 件を発見した (通常関数 ⊂ parametrize row、別 decorator 間の同値 row は scanner が拾えない)。
- 削減は台帳換算 33.005 worker 秒 (17,958.848 → 17,925.843 s、−0.18%)、収集 node 25,381 → 25,375、行数 592,860 → 592,845。受入 wall の短縮は主張しない。
- 変異 (module ごと 1 spec、負例 2 + 対照 1): 変更前 commit で probe して失敗 node 完全集合を採り、削除後 commit で S_post = S_pre − Del を KILLED 登録して本走。両 module とも matching 3/3 (H: 6→5、6→5; L: 23→22、20→16; 対照は前後とも赤 0、drift mask なし)。erratum: 実行元は DW-M07 の独立 clone でなく主 repo の登録 worktree へ harness を直接当てた (fresh clone は submodule 供給 URL が非 local で初期化 tool が拒否)。
- (D) は 41 file の代表 45 関数を読み、関数単位で純粋な定数 pin 7、資料・派生値 pin 5、pin と挙動検査の併存 3、読んだ代表が挙動検査 (D でない) 26 file と分けた。246 関数は未確認。裁定パッケージは insight README §5。
- レビュー 2 本 (正しさ境界 / 過剰・削除) は削除実装と変異結果を妥当と判定し、報告の正確さ (D の件数分離・行数の基底・erratum・所要と外側 wall の区別) を must-fix/should 9 件、親が docs-only で是正した。焦点再レビュー 1 巡目は 8/9 closed・1 partial (D を関数単位で分けよ)、再修正後の 2 巡目で GO (nit 1 = manifest の path 数、反映済み)。refuted 6 件 (検出集合喪失・登録簿見落とし・削除漏れ・要求外機構・母数混同・規律 2 の間接弱化)。
- 並行 wave `dev-wave-acceptance-worker-time-trim` の所有 6 file は削除対象から除いた。受入・land は並行 land 調停役 (manager session、18 wave) の列に登録し、PREP→GO の順序に従う。
- codex 子 10 本 (scanner author/fix、plan、相談 2、author、レビュー 2、焦点 2)、全段 gpt-6-astra / medium、model call 104、CLI reported tokens 757,480。段 8 の自己改善候補は 1 件 (DW-M07 の「独立 clone」文言と、隔離 worktree へ harness を直接当てる DW-M05 経路の関係。fresh clone は submodule 供給 URL が非 local で `dev_wave_submodule_init.py` に拒否される) で、dev-wave docs の byte 予算が満杯のため docs は変えず裁定パッケージ候補として報告する。一次資料 = `output/insights/2026-09-19/test-inventory-prune/README.md` と同 dir の inventory / mutation / verbatim。

## 次の一手差分

### 新規

- {{T:test-d-pin-ruling}} **P3・ユーザー裁定待ち**: (D) 派生値 pin の確認済み 15 関数 (純粋な定数 pin 7、資料・派生値 pin 5、pin と挙動検査の併存 3) と未確認候補 246 関数を維持するか削るかを裁定する。材料 = `output/insights/2026-09-19/test-inventory-prune/README.md` §5 と `inventory/list-D.txt`。DW-O18/O25 の exact pin は意図された防壁なので既定は維持。
