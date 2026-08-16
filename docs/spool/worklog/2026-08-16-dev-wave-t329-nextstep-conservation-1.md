---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t329-nextstep-conservation
seq: 1
title: 「次の一手」保存則を参照先の実在と archive 主張の一致まで広げた — 敵対レビューが検査を丸ごと迂回する穴を 2 度出した (コード + テスト、branch worktree-dev-wave-t329-nextstep-conservation、変異 matrix = 9/9 KILLED)
---

## 本文

- 裁定 (115) の択 (a) を実装した。ID の存在・遷移だけを見ていた D70 の保存則へ、carry 参照先
  entry の実在照合と、archive のファイル名・README が名乗る entry 範囲と実体集合の一致検査
  (範囲内の欠番も赤) を足した。設計判断は {{D:archive-name-positional-grammar}}。
- **親の provisional 裁定 (P1) は敵対検証で撤回した。** 「4 桁 token は日付、それ以外は entry 番号」
  という規則は `worklog-phase3-0722-0724.md` を entry 範囲と誤読する。親自身の診断 script が
  この規則で重複 entry 番号 22 件の偽陽性を出して実証した。正しい判別鍵は**先頭ゼロ**で、
  日付 token は `0724` のように先頭ゼロを持ち、entry 番号は先頭ゼロを持たない。
- **敵対レビューが「検査を丸ごと迂回できる名前」を 2 度出した。** 1 度目は
  `worklog-phase3-106-110.md` (MMDD を外す)、2 度目は `worklog-broken-106-110.md` (phase を外す)。
  どちらも「entry 範囲を名乗らない」に落ちて filename 範囲・README 範囲・全域 entry universe
  登録・archive 内 carry 収集のすべてを免れ、README にファイル名さえ載っていれば到達性検査も通った。
  2 度とも fix で malformed 側へ倒した。**所見ゼロで land していたら、この gate は
  名前を 1 文字変えるだけで無効化できる状態だった。**
- レビューは他に、末尾注記付きの旧書式 carry を採番 archive 内で 3 件取りこぼすこと、
  20 万件の carry を list 保持すると履歴比例のコストが純増することを出し、いずれも fix した。
- **実 corpus の欠陥を 1 件見つけたが、裁定された scope では赤にならない。** エントリ (77) の
  `[T-208]` `[T-209]` `[T-210]` `[T-211]` は `変わらず ((73) 参照)` と書いているが、これらの実体は
  エントリ (74) で起票され (76) が正しく (74) を指している。(73) は実在するが 4 ID を 1 つも
  含まない — **参照番号の書き誤り**である。裁定 (115) は「参照先エントリが実在するか」までなので
  これは受理される。より強い述語へ広げるかは {{T:carry-substance-preservation}} で裁定へ返す。
- 段 2 のプラン子を 1 度失った。子が `nl -ba orchestrator/tests/test_check_docs.py | sed -n
  '4540,4885p'` でテストファイルの範囲を raw 表示し、その中の**意図的な分解形 `プ` (フ + U+309A)**
  が event 行に載って evidence が全損した。930 秒・19,127 bytes の成果物が不受理になった。
  型は {{F:codex-evidence-nfc-echo}}。
- 段 6 の変異 matrix は **9/9 KILLED** (MISMATCH 0、SURVIVED 0、TIMEOUT 0)。negative 5、
  過剰拒否を検出する positive 3、両層同時 1。1 巡目の probe では 5 件が MISMATCH で、
  期待 node の過不足を実失敗集合から再導出して本走した。
- 実測 (最終 tip): `docs/archive/worklog-*.md` 425 件のうち採番 416 / 非採番 9 / malformed 0、
  carry 行 201,856、宙吊り 0、全域 entry 番号の重複 0、README 解析不能 0、主張不一致 0。
  `orchestrator/tests/test_check_docs.py` 443 passed、`orchestrator/tests/test_spool_fold.py`
  158 passed、`python3 tools/check_docs.py` rc=0。
- 工数: codex 子 8 本 (plan 2 = うち 1 本は evidence 全損、consult 2、author 1、review 2、fix 2、
  focus 1)。親は計算ノードで焦点走 4 回・変異 harness 2 回。

## 次の一手差分

### 完了

- [T-329] 「次の一手」保存則へ carry 参照先の実在照合と archive 主張の一致検査を入れた。
  変異 matrix 9/9 KILLED、既存 canonical は緑のまま。
  remaining: none
  base: 5629a860bb24b801f9f610365ffc383fe00ff2036e8e1820d2e422abc176a7a1

### 新規

- {{T:carry-substance-preservation}} **P1・ユーザー裁定要**: carry の検査を「参照先 entry が
  実在するか」から「参照先 entry の次の一手に**同じ ID がある**か」まで広げるか。実 corpus に
  違反が 4 件ある (エントリ (77) の 4 項目が (73) を指すが (73) は該当 ID を持たない。実体は (74))。
  択 (a) 広げる — 受理集合はさらに狭まり凍結 archive が 4 件赤になるので、訂正注記か erratum の
  運用手当てが同時に要る。択 (b) 実在検査に留め 4 件は記録だけ残す (親の既定)。
  択 (c) 広げるが既存 4 件を既知違反として台帳登録し、新規発生だけを赤にする。
- {{T:spool-fold-checker-closure}} **P2・ユーザー裁定要**: producer (`tools/spool_fold.py`) を
  新 checker の受理集合へ閉じるか。(i) 公式 land は fold 適用後・commit 前に `check_docs.py` を
  走らせて赤なら rollback するが、`spool_fold.py` の直接 CLI にはこの postcondition が無い。
  (ii) `spool_fold` は欠番のある global ordinal を受理するため、欠番を挟む entry を同時に
  ローテーションすると producer は連続範囲を名乗り checker が欠番として拒否する。
  択 (a) T-329 は公式 land の postcondition gate と明記し、直接 CLI は別タスクへ送る (親の既定)。
  択 (b) 同 wave で producer 側にも範囲 postcondition と producer テストを足す。
- {{T:devwave-nfc-echo-guard-budget}} **P2・ユーザー裁定要 (段 8 の自己改善が予算で止まった)**:
  {{F:codex-evidence-nfc-echo}} の恒久対応を dev-wave の reference 節へ入れるか。入れ先は
  `docs/dev-wave/operations.md` の `DW-O02` (prompt・job artifact を作る直前に読む節) が唯一
  意味の合う場所だが、同節は段 2・3 の preflight で常時読むため L1.5 に数えられ、
  最短の文言を足しても `docs/dev-wave/**` の L1.5 予算を 171 bytes 超過して `check_docs.py` が
  赤になった (実測)。自己改善契約の「予算に収まらなければ変更を止めて裁定へ返す」に従って
  変更を revert した。択 (a) memory と failures だけで運用し reference へは入れない (親の既定)。
  択 (b) L1.5 の陳腐化した節を削って枠を作る。択 (c) 予算値そのものを独立審査にかける。
