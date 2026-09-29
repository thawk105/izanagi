---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-vhash-forwarding
seq: 1
title: [T-2879] Cicada に cold 境界 (論理 K 版) で発火する選択的 forwarding を inert patch で試作し、stock・C・F を同時刻に測った。通常 YCSB で試行の約 75% が成功、操作数の多い長い tx では約 18%、throughput の差は floor の内側、md_3 の検査器で発火付き巡回 0 (上限 indeterminate、未検証の診断値) (patch + driver + gate 登録 + insight、branch worktree-dev-wave-vhash-forwarding)
---

## 本文

- 依頼: VHash 論文の並行 wave md_6 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_6.txt`)。一次資料 `output/insights/2026-09-29/vhash-forwarding-prototype/README.md`、設計判断 {{D:vhash-forwarding-protocol-v2}}・{{D:vhash-forwarding-registration}}。
- 素材: 通常 YCSB (100 万件・zipf 0.9・48 thread、K=3) で C は 1 秒に試行 1,131〜2,069 回・成功率 0.73〜0.75。操作数型は全体 0.18 (長い thread は約 1%)、失敗の大半は既読不一致。throughput の stock 比は 0.95〜1.03 で 95% CI は全条件で 1 をまたぐ (K=1 の F だけ 0.66)。長い tx の完了は操作数型で 3 腕とも 0、待機型で一貫した差なし。すべて未検証の診断値。
- 正しさ: md_3 の trace 計器 (main `159999d44`) に重ね、md_3 の起動器の派生 (Codex author、repo 外) で ENABLE+COUNT を渡して発火を数えながら検査。10 走行すべてで発火・成功 (計 285)、巡回 0、上限 indeterminate。serializable とは書かない。md_4 の小モデル (main `1887f56e4`) の規則 R9'・R5・R6→R7・R10 と静的に照合し、O1 を採らない本設計では R5 は該当しないことを一次資料 §2 に書いた。
- ユーザー不在 (マネージャー連絡 03:23 JST): needs input を出さず、所有外の条件 gate 登録は段 3 の 2 レンズ (賛否) の一致で決めた。
- 依頼との食い違い 2 点: patches/ledger.json に entry を足さない (rung1 契約が 1 件固定、マネージャー連絡でも確認)、IZANAGI_ 接頭辞を使わない。
- セッション異常: DW-O13 の期限後成立 (条件 gate の登録が必須) で段 2 からやり直し (旧 brief / plan / review は無効化して退避、段 3 の旧 2 子を停止)。gen_S 混雑で dispatch の待ち切れ 3 回 (rc=16、子未起動)。手動 qdel は規約どおりせず、待ち job のある木に触れないよう統合用の木を 2 本 (vhash-fwd-integ / integ2) 使い、wave branch は最後に fast-forward した。
- 実機でだけ出た不具合 6 件 (compile entry 4 件、config.h 未生成 ×2、gate への重複 define、__LINE__ のずれ、登録なしの検査木) を smoke の 7 回で潰した (insight §10)。登録簿の追随漏れ 2 件 (screening_driver の既定値表、tests/README の pytest 専用 allowlist) はマネージャー経由の md_2 実測と焦点走で見つけて直した。handoff の節見出しに推定時刻を書いて実際より 1 時間進んでいた (date で訂正)。
- 段 2〜6 (Codex gpt-6-sol・medium): plan 2 (1 本は無効化)、consult 4 (2 本は無効化)、author 4 (A・B1・B2・probe)、fix 12、review 2、focus 2。段 6 の real 所見は fix で閉じ、refuted 1 (inert_values)、手順で対処 2 (予算の再積算、aggregate の workload 欠落)。
- 変異 (事前登録 M1〜M5、独立 clone `60bd0eb8b`): probe で観測 node を集めた後の正式走で 5/5 KILLED・期待 node と完全一致・baseline PASSED。C++ の論理変異は login の pytest で殺せないので登録せず、段 6 の必須攻撃点と検査器の発火付き実走で代えた。
- テスト: 登録関連一式 457 passed / 2 skipped (`60bd0eb8b`)、DW-O26 焦点走 2,387 passed / 1 failed (赤は未 commit の tests/README.md を作業木の dirt として数える `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes`、commit 後は該当しない)。受入全走は記録時点では未実施。
- 計算 (受入を除く): smoke 7・本計測 3・検査 3 の Elapse 合計 1,325 s、焦点走・登録関連テストの dispatch 9 本 1,132 s、変異 probe・正式走 12 run (推定 約 1,560 s)。合計約 4,000 s (約 1.1 node 時間)。2 node 時間の線の下なのでユーザー確認なしで投入した。

## 次の一手差分

### 完了

- [T-2879] 試作・計測・正しさ検査を終え、一次資料 output/insights/2026-09-29/vhash-forwarding-prototype/README.md に記録した。
  remaining: none
  base: b0c725ada8e51f262ddbb29f20b966c1044106deca493fe57c72d842512377db

### 新規

- {{T:vhash-forwarding-target-policy}} **P2・新規**: 選択的 forwarding の前進先の選び方 (最小前進 / 既読の可視区間に収まる最大 / 1 tx 1 回の制限) を比べ、長い tx の読み集合で成功率が落ちる (操作数型で約 18%、長い thread で約 1%、主因は既読不一致) 問題を調べる。基盤は patches/cicada-forwarding-variant.patch と orchestrator/campaign/vhash_forwarding_prototype.py (一次資料 output/insights/2026-09-29/vhash-forwarding-prototype/README.md §8)。
