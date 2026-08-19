---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-task-inventory-cleanup
seq: 1
title: タスク棚卸し — worklog carry 15件クローズ・見送り台帳2件転記・rulings-inbox 18件整理 (docs のみ)
---

## 本文

- ユーザー指示 (「タスクの棚卸し。next-tasks 使用時に『もう対応済み』『裁定で見送り』の候補が頻発して困る。一度全て確認して抹消し、優先度を研究/実験優先へ再定義してほしい」) を受けて、next-tasks が読む 3 系統 (rulings-inbox 未fold 30件、worklog active carry の P1/P2/P3、計 536 件) を並行 fork 4 本で監査した。
- **rulings-inbox**: 30 件中 18 件が内容ベースで確認すると既に canonical へ反映済み(folded-confirmed) だった。`dev-wave-jobs/rulings-inbox/folded/` へ移動した(repo 外・git 対象外のため本 commit には含まれない)。残り 12 件は部分反映 5・真に未裁定 4・要フォロー 3 のまま維持する。
- **worklog active carry (536 件)**: P1 45 件・P3 自己申告済み完了語 41 件・P2 同 108 件を個別監査した。P2 は close-now **0 件** — 「裁定済み」ラベルは「決定フェーズ完了」だけを意味し「実装フェーズ完了」ではないため、実装待ちの正当な backlog だった (深掘り検証 13/108、残りは同一 label 文型からの高確度パターン判定)。P3 は 41 件中 close-now 7 件。P1 は 45 件中 close-now 9 件、見送り相当だが転記漏れ 1 件 ([T-184])。本 fragment はこの合計 15 件の完了と 2 件の見送りを反映する ([T-1168] は F352 との突合せを本 wave が追加実施して条件充足を確認)。
- **land 時の学び**: [T-184] は当初 `docs/phase3.md` の「Codex dev-wave 資源効率化」節へ見送り転記する形で fragment 化したが、land の fold 検証で ID 重複エラーになった (同節は「## 見送り台帳」の下に `### ` で吊り下がっており、`次の一手` 側の T-184 本文自体が同節内に既存の bullet として既に存在していたため)。`spool_fold.py --dry-run` は この重複を検出しない (dry-run が省く検証があるという実測)。是正として [T-184] は 見送り台帳へ触れず `完了` (次の一手からの除去のみ) へ変更した。
- **構造的な発見**: P1 45 件のうち CC 自動合成 / Phase 3 実験 (variant 合成・8b/8c campaign 実走) に直結する項目は **0 件**。全件が dev-wave 自体の基盤整備 (受入ゲート・freeze/世代機構・受領証 schema・worker 資源・docs 機械化) だった。次-tasks の「CC 自動合成の実験タスクを最優先する」既定方針は、優先順位の付け方でなく**候補の不在**によって発動していない。T-1391 (H1/H2 workload定義、entry 698) と T-1352 (between-run floor 撤去、entry 696) が本日 land したため、`docs/phase3-8c-preregistration.md` の正式系列着手条件が満たされたかの確認が次の一手として有力。これは本 wave の scope 外 — Phase 3 の技術判断としてユーザーへ返す。
- **横断所見 (rulings-inbox fork より)**: 「段 8 自己改善候補が docs/dev-wave 予算満杯で見送り」というパターンが最低 4 件のファイルに渡って個別に「ユーザー裁定待ち」のまま止まっている(t657stage0 候補 2・t956budget・t665waiter・旧 t396waiver 分)。予算運用方針そのものを一括裁定すれば束ねて解消しうる。本 wave では未着手 — 裁定はユーザーへ返す。
- entry (693) が同日に発見した「rulings-inbox の未fold判定は個票 basename しか見ておらず、round 集約ファイル (`rulings-fullN-*.md`) との two-hop 突合せを欠いていた」という教訓をrulings-inbox 監査 fork へ追加指示として展開し、同型の誤判定を再発させずに済ませた。

## 次の一手差分

### 完了

- [T-1390] 「含めない (現状維持)」で決着。実装アクションは無い。
  remaining: none
  base: e89ebb711d80ff6f827d3b510c2ef01af668b93b57db60355e5aed8e5d2794fc
- [T-1358] 「恒久経路は新設しない」で決着。waiver 反復運用の現状維持を続ける終端決定。
  remaining: none
  base: f431a61153c71d4fa571c168f78c7184f97c70aeda2a4bdd2e454cd716217091
- [T-1301] 「広げない」で決着。scope 拡大を却下する終端決定。
  remaining: none
  base: 9272ff595f30c0c433ce71a1b31d992330d60992ea2472b2e800873c91b9b093
- [T-1246] 「保留を維持する」で決着。現状の一時停止を継続するだけの終端決定。
  remaining: none
  base: 738efe6cf0be95616783cf52083eda237d27936d97f4489d1e86554f64625c5f
- [T-1235] 「含めない」で決着。local 実行経路を対象外とする終端決定。
  remaining: none
  base: f0d8a70f70955d762a439019cf429385e7e3b7e24ce8d3c7cd4a3498bc121330
- [T-1387] 裁定 = 現状維持。凍結本文・`DECIDER_VERSION` とも変更しない。
  remaining: none
  base: bccbab270b5cee65dfdd6cb04c363ba09f1fcc2cb8473bc9e48131b61ed09a71
- [T-848] 「実装面は D502 で決着済みにつき本項は本裁定で終端する」と本文が自己宣言。
  remaining: none
  base: f521c1333044a5ce75d2ed291ee33b382832d68c5f2e64dbc2cb60674fff8e5e
- [T-362] 「追記のみ」。D130 条件 3 の実体は [T-471] → [T-486] → [T-503] へ完全移管済み。
  remaining: none
  base: 400bc76a8612ab626255206fb28473e72dd4a0d13baf97ca56598c719fa1df84
- [T-971] 残件 (a) は完了、(b) は [T-1094] へ従属と明記。T-971 自体に残作業はない。
  remaining: none
  base: 646b7e0770dda0e169c577f09da225d3db30798e17d7ca152a1997e5c930ab6d
- [T-805] [T-657] の世代交代・恒久 freeze 機構へ合流と裁定済み。暫定状態もユーザー承認済みで単独残作業なし。
  remaining: none
  base: 5da2fb61c5f3231a46f6e9935a405030653e0af608c1cedfd31934358b412b2f
- [T-531] [T-478] の A′ 世代移行機構へ統合裁定済み。次回 refreeze はこの統合の完了が前提で単独作業はない。
  remaining: none
  base: 9a1bda69f602f4a5c3a7b74882ff950d137285a6676410651530747844b92739
- [T-181] 「完了 → [T-184] へ引き渡し可」と自己宣言。引き渡し先の [T-184] は本 fragment が別途完了とする。
  remaining: none
  base: 81d0935ed247d9fa9777ac0a98ea1cfaed5ffc0478c596cb021daa2769c8cac5
- [T-184] 「Codex dev-wave 資源効率化」節に既存の bullet (P1・reasoning 面は採用済み、再発 (cap 誤爆) を発火条件に sweep 設計は保留のまま保持する、との記載) が既にあり、その保留状態の記述自体が本項の現状を正しく表しているため、見送り台帳への新規挿入は行わない(新規挿入すると同節内で ID が重複する)。次の一手からは落とし、能動的な残作業は無いとする。
  remaining: none
  base: 377ed41302ca0e9421d44b92b39283932e394ad69736825486d8586cde045898
- [T-1336] 後継 [T-1352] が main へ既に land 済み (`0127144e` ほか、`de9c63f1` で取り込み確認)。T-1336 自体に残作業はない。
  remaining: none
  base: 4646a7f2c91355b87998566cc81d3bb488779d9bb3be3fc1bf5a884d92367b26
- [T-350] commit `1db670ae` (docs/spool 機構の実装) で実現済み。`docs/spool/README.md` として現行 main で稼働中。
  remaining: none
  base: 04fbfc16065f2d9981bfad514d09f535bbbf60c97c97b34cae1c5d11f413f566

### 見送り

#### プロセス文書系

- [T-1168] 理由: 2026-08-16 /rulings 全件 第 2 回、択 (d) 見送り。`DW-O01` への 1 文追記は行わない — 追記しようとした文言そのものが同 wave 中に反証されたため。条件付きだった「背景 task の完了通知が producer 稼働中に発火する実測を failures 台帳へ記録すること」は F352 (2026-08-16、6 件以上の実例と DW-O01 既定規則の実証記録) で充足済みと本 wave が確認した。再訪条件 = 同型の見落としが F352 の 3 点照合を経てなお再発したとき。
  base: 50131f48e2c01dc680401abd67be4d76aace28d96bf2ea48c95ef589f7cea340

#### 外部環境系

- [T-1090] 理由: 2026-08-15 /rulings 全件、着手保留。1 dispatch job で複数 node を扱う設計は [T-1116] の実装後に再評価する — 既知赤 registry が入ると再走回数の見積りが無効になるため。有界並列化の不採用は変わらない。再訪条件 = [T-1116] の実装完了 (本 wave 時点で worklog/decisions/phase3.md のいずれにも land 記録なし、条件は未充足)。
  base: 895f9a86e2eff0471d616b99c241e4d651eb4bc72063dbc77f37cfa8c149cf6f
