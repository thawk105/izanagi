# 段 4 裁定 — silo-intra-txn-fix-line、2026-09-30 12:40 JST

入力: 段 1 brief (`s1-brief.md`)、段 3 相談 (`consult-a.md`、rc=0、check_codex_output rc=0)。段 4 直前の再走査: [T-2905]・[T-2885]・[T-2917] の未 fold fragment なし (`docs/spool/` の grep 0 件)、同じ item を扱う並走 session なし (ListAgents)。

## 所見の裁定

| ID | 裁定 | 採否 | 反映 |
|---|---|---|---|
| C1 (計装 patch が `#line 658` を文脈に含み新 tip に当たらない) | real | 採用 | R5 |
| C2 (起動器が直接の親 = F を固定) | real | 採用 | R4・R5・R6 |
| C3 ((b) に `--expect-paths` の 4 path) | real | 採用 (検査器の `_validate_expected_paths` は差分 path 集合の厳密一致を足すだけで、判定を緩めない) | R4 |
| C4 ((a) は証拠を増やさない) | real | 採用 ((a) と 7e5fa528→新 tip は回さない。前回の (a) を参照する) | R4 |
| C5 (主 checkout 取り込み script が同名 ref・親 = F で止まる) | real | 採用 | R7 |
| C6 (「#line untouched」が新 commit 後に偽) | real | 採用 | R3・R8 |

## プラン v2

- **R1 土台と commit:** 土台 = `7e5fa528037805dfc0459c742e4a21d6114c9799` (主 checkout の submodule の `refs/heads/izanagi-silo-intra-txn-fix`)。commit 直前に同 ref が 7e5fa528 のままかを再確認し、変わっていたら commit せず停止。wave 木の submodule git dir に同名 local branch を 7e5fa528 から作り (現在 local には無く remote-tracking のみ)、1 commit。file 変更と英語 message は Codex author、commit は親 (`commit -F`)。trailer 3 行 (Codex author・Codex reviewer・Claude manager、前回と同形式)、commit 直前と直後に本裁定と行単位で照合 (F1040)。commit は段 6 レビューとその fix の後、計算の前。
- **R2 変更:** `cc/silo/transaction.cc` の `#line 635`→`638`、`#line 658`→`661`、`#line 679`→`682`、`#line 700`→`703` の 4 行だけ。`git diff --stat` 1 file・4 insertions・4 deletions。`#line 365`・`#line 381` は変えない (update より前)。
- **R3 message:** subject は上流の流儀 (`fix(silo): ...` 型、72 字以内)。本文: 直前の commit が update に 3 行を足したため、後ろの 4 本の `#line` (trace の整形で変わった行数を打ち消して untraced source の論理行番号を保つもの) がその 3 行まで打ち消し、TRACE=0 の `__LINE__` (`ERR` の表示) が「trace 無し + 修正」と食い違った / 4 本を +3 して一致させた / 実行の意味は変わらない (診断の行番号だけ)。trailer は書かない (親が足す)。
- **R4 D297 (事前登録):** (b) だけを回す。合成 P′ = 前回の `d078f0f05b7fc4b668d65f4a5d37f7f5af2e693c` (親 pin `68106660`、tree = pin + 修正案)、P‴ = 親 P′・tree = 新 tip の tree (作者・日時固定、job dir の使い捨て clone だけ、branch にしない)。検査器は wave 木の `tools/check_trace0_preprocess_identity.py` (sha256 `bcd46b29…`)、header 4 引数、`--expect-paths cc/mocc/transaction.cc cc/silo/transaction.cc include/tpcc.hh include/trace.hh`、GCC 11 と GCC 12 を別ノードの別 job。**期待 = 両方 rc=0。** 拒否したら記録して原因を調べ、push 依頼に結果をそのまま添える (結果を見て基準を変えない)。job 内照合: P‴ の親 = P′、P′ の親 = pin、P‴ の tree = 新 tip の tree、bundle の head。(a) F→新 tip と 7e5fa528→新 tip は回さない (C4)。
- **R5 trace (事前登録、前回 R5 と同じ):** 1 job、対照 = F + `instr-silo-gate-witness-F.patch` (前回の patch、sha256 を記録)、修正 = 新 tip + 新 tip 用の計装 patch (Codex author が作る。意味は F 用と同じで、`#line` の文脈だけ新 tip に合わせる)。各 patch は土台に厳密適用 (fuzz なし) で当たり、`#if TRACE` 枝を除くと土台と bytes 一致。2 build × W-rmw・W-blind (U0 と同じ flags・1 秒)。対照: 到達可能性 pass、D1 a・b1・b2 = 0、D2b (i)+(ii) 違反 ≥1。修正: 到達可能性 pass、D1 = 0、D2b (i)・(ii) 違反 0 **かつ** 各条項の発生条件 ≥1 (0 なら判定不能、合格にしない)、判定器 serializable・certified・取引数 = commit 件数。起動器 v3 の照合: control-oid = F、fix-oid の直接の親 = 引数 `--fix-parent-oid` (= 7e5fa528)、その親 = F、F..fix-oid の変更 path = `cc/silo/transaction.cc` だけ。
- **R6 CI:** format = 新 tip の clean checkout で login clang-format 14.0.0 と image :latest、対照 7e5fa528 を同じ手順で (login、親の launcher)。build = 計算ノードで image :ci、`run_ci_build_v2.sh` に PARENT_OID = 7e5fa528 (bundle head = 新 tip、親照合)。build は (b) GCC 11 と同じ job に束ねる。
- **R7 主 checkout への取り込み (段 9、land 後・撤去前):** 主 checkout の submodule で既存 `refs/heads/izanagi-silo-intra-txn-fix` = 7e5fa528 (または既に新 tip) を確かめ、新 tip の親 = 7e5fa528 を照合し、bundle から非 force の `git fetch <bundle> refs/heads/<br>:refs/heads/<br>` で fast-forward。別 OID なら止まる。submodule の HEAD と gitlink は動かさない。取り込み後に push を依頼する。
- **R8 記録:** 一次資料 `output/insights/2026-09-30/silo-intra-txn-fix-line/README.md` に、commit の中身、予測 (probe) と D297 (b)・CI・trace の結果と生出力の所在、push 依頼文 (branch 名・新 tip の完全 SHA・CI 結果・上流へ送る説明文の下書き。前回下書きの「#line untouched」に当たる記述を新しい事実へ直す)。spool worklog fragment: [T-2905]・[T-2885] 更新、[T-2917] の前提を新 tip へ書き直す。
- **R9 変異・受入:** repo の実装面の差分 0 (commit は insight と spool だけ) なので変異 matrix は免除 (DW-S04)。受入は land 側の規定に従う。
- **R10 計算:** job 1 = CI build + (b) GCC 11 (約 17 分)、job 2 = (b) GCC 12 (約 17 分)、job 3 = trace (約 4 分)。合計 約 0.65 node 時間、2 node 時間の線の下。3 job を同時に投げる。

## 段構成

段 5 author 1 本 → 段 6 read-only review 1 本 (過剰・削除レンズを含む 2 レンズを 1 本で) → fix → commit → format (login) → 計算 3 job → 段 7 記録。
