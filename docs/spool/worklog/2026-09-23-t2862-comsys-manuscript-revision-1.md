---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-23
wave: t2862-comsys-manuscript-revision
seq: 1
title: [T-2862] ComSys 2026 投稿原稿を採用時点 8fd2a2f5c 以後の着地に合わせて改訂した — K2 の同 job pair 成立と 4 巡目 (4.7 節・7 節 (d))、TPC-C の段 1 → 段 2 の順と段 1 の実装状況 (7 節 (a))、関数単位の軸の段階 C (7 節 (b))、SI の検出件数の時点 (3.3 節)、合成ループの小構成 (限界節) (docs のみ、branch worktree-t2862-comsys-manuscript-revision)
---

## 本文

- 依頼 (ユーザー直接起動の `/dev-wave`): 原稿 `output/insights/2026-09-22/comsys2026-manuscript/manuscript.tex` に entry 1823 と D2219 項 2 を反映し、entry 1819〜1826 の他の着地は食い違う箇所だけ直す。主張は増やさない、[T-2860] は待たない、著者・所属・頁数・ADRS は差し込み欄のまま。記録 = 同 dir の `README.md` §9。
- 段構成は軽量版 (段 2・3・5 なし、実装面ゼロで変異免除、段 6 は一次資料の再抽出を含むので read-only レビュー 1 本)。起点 = local main `3886a1fd3` (entry 1830 まで)、開始 gate rc=0。
- **親の provisional 裁定 (P1):** 依頼の列挙は entry 1826 までだが、着手時の main には 1827〜1830 も着地していた。「採用時点より後の着地を反映」の趣旨で照合に含め、7 節 (a) (TPC-C 段 1 の実装と構造確認の 1 走、存在履歴の検査まで certified にしない、CCBench 側は固定版に未取込み) と (b) (段階 C の手書き方策の生死確認、LLM 生成は未実施) の「設計の段階」「未実装」を直した。1822・1824・1826・1827 は原稿と食い違わないので変えていない。
- 追加で見つけた食い違い 2 件: 3.3 節の SI 3,576 件を時点なしで書いていた (entry 1821 の射程文により 2026 年 6 月の判定器での値と明記)、限界節の「48 スレッドに限った」が 4.7 節の合成ループ (3 巡とも 4 スレッド・100,000 レコード) と改訂前から食い違っていた (段 6 レビュー 1 回目の M1)。
- **段 6 レビュー 1 回目は不受理:** codex は完走したが、子が PDF を文字抽出し参考文献の「Vũ」が結合文字 U+0303 の非 NFC 列で event に載り、起動器が evidence invalid で捨てた。出力は artifact dir に残り、所見 (must-fix 1・should 1) を親が一次資料で確かめて real と裁定し直した (`efa6112f6`)。2 回目は prompt に PDF の文字抽出の禁止と経緯を足し、別 job-id で投げた。
- 段 6 レビュー 2 回目 (`efa6112f6` 対象): **GO**、must-fix 0・should 0・nit 1 (7 節前置きの「評価は行っていない」の対象を限る) を採った。refuted = pair の過大主張、TPC-C・関数方策の範囲、48 スレッドの矛盾 (修正済み)、還流回数の時点、(P2) の取り残し。
- commit: `2c1103189` (改訂本体)、`efa6112f6` (レビュー 1 回目の所見 2 件)、記録 commit (nit・README・本 fragment・phase3)。組版は前 wave の手順 (job dir の `build-final.sh`) で platex rc=0・警告 0・Overfull 0、**15 頁** (初版 14 頁から 1 頁増、頁数はユーザー手番)。`grep -n "^%.*．"` は 0 件 (F1042)。
- 凍結前の検出語走査 (`s8b_holdout_freeze search`) は rc=1 だが、hit は既存の較正記録 3 file (`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/`) だけで、本 wave の変更 file は 0 件。
- 工数: Codex read-only レビュー 2 本 (1 本は不受理)。計算ノードの使用は受入だけ。

## 次の一手差分

### 完了

- [T-2862] ComSys 原稿を採用時点 8fd2a2f5c 以後の着地 (entry 1819〜1830、D2219 項 2) に合わせて改訂した。記録 = `output/insights/2026-09-22/comsys2026-manuscript/README.md` §9。著者・所属・頁数・ADRS は下の新規項へ移した。
  remaining: none
  base: 528dc02bbdb8a9d221ec89403e475a16fcba857333982d9f895da0cca1e972f8

### 新規

- {{T:comsys-user-inputs}} **P2・ユーザー手番 (docs、ComSys 原稿)**: 著者・所属 (`\affiliate` / `\author` の差し込み欄)、頁数 (改訂後 15 頁、縮めるなら削る対象)、
  ADRS と位置づけの 1 文の扱いをユーザーが決めたら同じ原稿へ入れて再組版する (`output/insights/2026-09-22/comsys2026-manuscript/README.md` §6)。
  発表申込 10/16、原稿締切 10/30。[T-2860] の結果 (4 巡目の還流) が着地したら 4.7 節の「4 巡目の critic と記録の取込みは未了」も同じ改訂で直す。
