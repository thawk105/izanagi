---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-16
wave: dev-wave-t936-rollout-identity
seq: 1
title: rollout の自己同一性で親 session を解決した — 敵対レビューが凍結式の昇格反例を 2 度出し、実測の水準も差し戻した (コード + テスト + docs、branch worktree-dev-wave-t936-rollout-identity、変異 matrix = 8/8 KILLED、実 corpus 3,649 file で全 id 一意)
---

## 本文

- **ユーザー一括裁定 (2026-08-16) #41 = 「全走査を維持したまま判定式を直す ([T-886] と矛盾しない形で)」の実装。**
  走査範囲を狭める方向は採らず、pin 無し経路の `rglob("rollout-*.jsonl")` 全走査を 1 行も変えていない。
- **親が撤回した主張が 2 件ある。**
  (i) brief の不変条件「受理集合は現行の真部分集合、緩和ゼロ」は誤りだった。候補述語は確かに
  真部分集合だが、`_find_rollout` の成功条件は「候補ちょうど 1 件」なので候補の縮小は
  resolver の成功を**広げる**。段 3 の両レンズが独立に同じ指摘をした。以後は
  「候補述語の受理集合」と「resolver の成功集合」を分けて書く。
  (ii) 改名 (P4) の根拠に引いた D75 は freeze 族恒久設計であり命名規則ではない。段 2 の
  plan 子が指摘した。ただし D75 本文は同名混同の事故を記録しており `DW-O13` も
  「D75 の趣旨」として引いているため、根拠を本 wave の根本原因そのものへ置き換えて採用した。
- **敵対レビューが凍結した判定式の昇格反例を 2 度出した。** 段 3 レンズ A が
  「同一 P/P の file 2 本の片方へ 1 行追記するだけで、そちらを無効化して他方を一意に昇格させられる」
  を構成し、親は `first_owns_X` (先頭の自己宣言行からは同一性を剥奪しない) を足して閉じた。
  段 6 レビュー A が**同型の穴が「同一性を確定できない行」の経路で再び開いている**ことを示し
  (`{"id": null, ...}` が先頭にあると先頭判定が偽になり、その行自身が子孫宣言として数えられる)、
  判定式を再確定した。**2 度とも「1 行の追加で他方を昇格させられる」という同じ攻撃型である。**
- **fix は 2 巡した。** 1 巡目は未確定判定を `id` key が存在する枝にだけ置いたため、
  `{}` や `{"session_id": 7}` の行が「確定できた行」として数えられ同じ昇格が残っていた。
  親が repo 外 probe (`check_gap.py`) で 6 形を実測して差し戻し、2 巡目で両枝へ一様に適用して閉じた。
  **子の報告ではなく親の実測が差し戻しの根拠である。**
- **段 5 の 1 走目は「実装せずに止まる」が正解だった。** 実装子が裁定内の矛盾 (型 B 逆順の期待値と
  片側 veto の負例が同形で両立しない) を検出し、コードを 1 byte も触らずに報告して停止した。
  原因は親が判定式に `first_owns_X` を足した後、テストの期待値を再導出しなかったことである。
  判定式は凍結どおり変えず、期待値の側を正して erratum E1 とした。
- **親の実測が水準を満たさず差し替えになった。** 段 6 レビュー B が、親の実 corpus 測定を
  (i) `_session_meta_rows` を memo 化し候補を絞ったため production の全走査経路を通っていない、
  (ii) 同 helper が読取・parse 失敗を内部で捨てるので「例外 0」が異常の不在を意味しない、
  (iii) 旧述語との返り path 完全一致を測っていない、
  (iv) 2 走の間で corpus digest が変わっており live corpus の安定性が未確認、
  として不合格にした。**初回測定は erratum として保存し land 根拠にしていない。**
  第 2 版は 4 点をすべて塞ぎ、これを確定根拠とした。詳細は
  `output/insights/2026-08-16_t936-rollout-identity/README.md`。
- **全 id への `_find_rollout` 直接呼出しは実行不能である。** O(id 数 × file 数) の file I/O で
  単走 225 秒 × 3,649 id = 約 9.5 日になる。第 2 版は「差分 id + pin + 対象 2 id は絞り込みも
  memo もせず直接呼ぶ」「無作為 30 id で絞り込みの正しさを全 file 評価と突き合わせる」で代替し、
  **この不可能性を測定 JSON 自身に記録した。**
- **実害の範囲は限定して記録する。「完全に消えた」とは書かない。** 消えたのは
  thread_spawn / subagent 型 (`019fd52d…`) で、親 file の `session_meta` は 1 行なので
  消費側の件数検査と identity 検査も通る。compaction / resume 型 (`019f690c…`、meta 4 行) は
  `_find_rollout` が成功しても消費側が拒否し続けるため {{T:rollout-multi-meta-consumer}} として返す。
- **標本は薄い。** 実 corpus の fork / subagent file は 4 件、親 2 系統、producer 2 系統
  (`codex_vscode 0.144.2` / `codex_exec 0.146.0`) で、親行コピーを持つ 3 file は同一親由来の
  兄弟である。**4 件は回帰 fixture の由来として記録し、「fork は必ず親行コピーを持つ」という
  普遍規則としては記録しない。** 判定式は意図的に行順へ感受性がある。
- **[T-886] は「全走査と普遍的に同値」ではない。** SHA 認可付きの限定 fast path であり、
  既存テスト `test_find_rollout_pinned_rglob_reaches_arbitrary_depth` が差を固定している。
- **変異は probe → 本走の 2 段。** probe (round 1) は KILLED 3 / MISMATCH 5 / SURVIVED 0 で、
  期待 node が親の推測と 5 件ずれた。ずれは検出力の欠落でなく推測の誤りである。観測から
  完全集合を再導出した本走が **8/8 KILLED、SURVIVED 0、MISMATCH 0、TIMEOUT 0**。
  probe の台帳も削除せず insight に残す。
  M06 / M07 は既存テストが先に殺す shared 変異、型 B 逆順 / 片側 veto / 真の重複の 3 本は
  wave 前実装でも通るため、いずれも新規テストの純増検出力には数えない。
- **codex 子の evidence を 2 度全損させた。** いずれも本体と無関係な NFC 事故である。
  1 度目は子が pytest を走らせ、repo の tracked fixture が持つ分解形の文字が
  `attempt-*.events.jsonl` へ流れて `evidence_status=invalid` になった (613 秒 / 15,723 bytes 喪失)。
  2 度目は**親がその事故を handoff へ記録する際に同じ文字を貼り**、prompt が名指ししていない
  job dir を子が読んで踏んだ (978 秒 / 11,395 bytes 喪失)。詳細と恒久対応は
  {{F:codex-evidence-nfc-from-repo-and-parent}}。
- 段 5・段 6 の実装子・fix 子はいずれも sandbox の socket 制約で pytest を起動できず
  (`qstat -Q` rc=1 / `run_tests.py` rc=16)、**実走はすべて親が行った**。
  子の非実走は緑と記録していない。

## 次の一手差分

### 完了

- [T-936] `_find_rollout` の pin 無し経路が subagent の親 session を `RC_SESSION` で拒否する件を
  判定式の修正で閉じた。実 corpus 3,649 file / 3,649 id で新述語の解決件数はすべて 1、
  旧述語が一意に解けていた id で返り path が変わったものは 0 件、新旧で解決集合が異なるのは
  対象の 2 id だけ。変異 matrix 8/8 KILLED。
  remaining: none
  base: 6bd14e496d77d2fd7ba8bb27c85c77f0257f6d12e6522e66c11d460158444727

### 新規

- {{T:rollout-multi-meta-consumer}} **P2・新規**: `tools/codex_reasoning_ab.py` の消費側は
  `session_meta` 行数が 1 でない rollout を拒否する。compaction / resume で複数行になる親
  (実在: `019f690c…`、4 行) は `_find_rollout` が直っても拒否され続ける。
  選択肢 = (a) 現行 fail-closed を維持、(b) 完全一致する重複行だけ 1 行として扱う、
  (c) 先頭行を権威とする。**(b)(c) は受理集合を広げるので独立の敵対検証を受入条件にすべき。**
- {{T:rollout-scanner-indeterminate}} **P2・新規**: `_session_meta_rows` は decode 失敗と
  `OSError` を silent skip するため、読めなかった file は「一致しない」として扱われ
  不確実性が消える (`MATCH` / `NO_MATCH` / `INDETERMINATE` の 3 値でない)。
  破損した重複候補があると別 file が一意に昇格しうる。閉じるには既存テスト 2 本
  (`..._scanner_ignores_decode_errors_and_non_objects`、`..._ignores_unreadable_file_before_match`)
  の期待反転が要るため、裁定を経ずに触らない。
- {{T:rollout-pin-sha-fallback}} **P2・新規**: pin fast path が `_verify_rollout_sha` の失敗を
  握り潰し、その後の全走査が同じ file を SHA 未検証で返しうる。既定 caller は後段で再検証するが
  `verify_source_sha=False` 系の seam では防壁がない。[T-886] の範囲。
- {{T:devwave-nfc-rule-budget}} **P2・ユーザー裁定待ち**: 段 8 で
  {{F:codex-evidence-nfc-from-repo-and-parent}} の恒久対応を `DW-O02` へ足そうとしたが、
  **L1.5 予算に収まらなかった** (最小 3 行でも unique footprint 9,808 bytes > 予算 9,566 bytes)。
  予算は上げず、削除可能な節も尽きている ([T-127] 裁定、先行 2 wave が実証) ため入口編集を見送り、
  memory と repo 外 probe だけを恒久対応とした。選択肢 = (a) 現状維持 (memory 依存のまま)、
  (b) L1.5 の他節を縮約して枠を作る、(c) この規律を L2 節 (合計上限なし) へ置く、
  (d) 予算値そのものを独立審査する。**(d) は自己改善の範囲外なのでここでは選ばない。**
