# [T-403] 孤児 job の後始末を fail-closed にした wave の一次資料

wave: `dev-wave-t403-orphan-job-hold` / branch: `worktree-dev-wave-t403-orphan-job-hold`
base: `478a4138` / 統合 commit: `2f6e1af9` / 実施日: 2026-08-16

## 何を変えたか

D142 の qdel gate が取消を見送った job は孤児として計算ノードに残る。変更前は receipt と
stderr 1 行の警告だけで、次回投入・変異 source の復元・変異 worktree の廃棄・受入 probe の
掃除のいずれも止まらなかった。create-only の latch
(`output/pegasus-dispatch/orphan-hold.json`) を導入し、この 4 経路を fail-closed で止める。
設計判断の正本は decisions 台帳、経緯は worklog。**qdel を実行する経路は増やしていない。**

## この wave が保証しないこと

- latch は latch であって相互排他 lock ではない。
- qsub 前の永続 claim を作らないため、SIGKILL と request ID 照会中の再 signal の窓は残る。
- 保護範囲は `dispatch_compute` 経由の dispatch と変異 harness / 受入 checker に限る。
  直接 qsub する `tools/pegasus/submit_*.sh`、`orchestrator/campaign/patchharness.py` の
  checkout 復元・worktree 強制削除、local 実行経路は対象外。

## ファイル

| path | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief。親が brief 前に取った実測 3 点を含む |
| `s4-ruling.md` | 段 4 裁定 (plan v2、変異事前登録、scope 外の裁定パッケージ) |
| `s6-fix-ruling.md` | 段 6 fix 裁定 (must-fix 6 件、変異登録の改訂) |
| `verbatim/s2-plan.md` | 段 2 プラン起草 (codex, read-only, reasoning=max) |
| `verbatim/s3-lens-a-correctness.md` | 段 3 敵対相談 レンズ A (正しさ境界) |
| `verbatim/s3-lens-b-scope.md` | 段 3 敵対相談 レンズ B (整合・実効性・運用) |
| `verbatim/s5-impl.md` | 段 5 実装子の報告 |
| `verbatim/s6-review-a.md` | 段 6 敵対レビュー A (正しさ境界) |
| `verbatim/s6-review-b.md` | 段 6 敵対レビュー B (検出力・波及) |
| `verbatim/s6-fix.md` | 段 6 fix 実装子の報告 |
| `mutation-spec-v1-probe.json` | 変異 spec 第 1 版 (probe)。正例の期待集合が不完全だった |
| `mutation-spec-v2.json` | 変異 spec 第 2 版 (権威)。sha256 = `d73135bdda68679d6fd32d3b1de1bec9f55af41d937e34d1a6675ff0715d01dc` |
| `mutation-ledger-run2.json` | 権威ある変異台帳。13/13 KILLED、MISMATCH 0、baseline PASSED |

## 変異 matrix

`tools/mutation_worktree.py` の使い捨て worktree で `--runner-mode dispatch` により 2 回走らせた。
runner 範囲は変更 4 test file (`test_pegasus_dispatch_compute.py`, `test_mutation_harness.py`,
`test_mutation_worktree.py`, `test_check_acceptance_reds.py`)。

| id | 変異 (wave 前の形へ戻す) | run2 |
|---|---|---|
| M1 | hold 署名を常に不成立 | KILLED |
| M2 | 投入前 hold 検査を削除 | KILLED |
| M3 | 「投入結果不明」を qsub の後に立てる | KILLED |
| M4 | 変異 source の復元を無条件に戻す | KILLED |
| M5 | 孤児条件から timeout 項を落とす | KILLED |
| M12 | 孤児条件から receipt 項を落とす | KILLED |
| M7 | `_should_teardown` の hold 項を削除 | KILLED |
| M8 | plan-only 例外 fallback の gate を削除 | KILLED |
| M9 | 受入 probe 掃除の保全を削除 | KILLED |
| M9b | 受入成果物掃除の保全を削除 | KILLED |
| M10 | cleanup から latch 呼出しを外す | KILLED |
| M11 | 判定不能 (lstat 例外) を不在扱いへ倒す | KILLED |
| P1c | ハーネス検出を常時成立へ (過剰拒否の正例) | KILLED |

**erratum:** 第 1 走 (`mutation-spec-v1-probe.json`) では P1c が MISMATCH だった。期待ノードは
落ちたうえで 6 件多く落ちており、殺せていないのではなく期待集合が不完全だった。
第 1 走を probe と明記し、完全集合で再登録して第 2 走を権威とする (DW-M08)。
第 1 走の wrapper は matrix 完走後の evidence 退避だけ EXDEV で失敗した (`--out` が `/home`、
scratch が `/work` で別デバイス)。第 2 走では出力先を scratch と同一デバイスへ置き、
teardown まで rc=0 になった。

**登録しなかった変異:** 過剰拒否の正例のうち dispatch 署名・dispatch 検出・worktree 検出・
受入検出の 4 面は、影響が正常経路のテスト全体へ広がり完全集合を静的に確定できなかったため
登録していない (DW-M01 の「確認できなければ登録せず実効 gate へ再照準する」)。
進行停止だけを狙う変異も、同形の分岐が 3 箇所あり単一理由の一意 anchor を作れなかったため
登録していない。

## 焦点走の実測

計算ノード (request 913414) で変更 4 file + 波及候補 10 file = **1493 passed / 0 failed**。
JUnit の権威 node 数は変更 4 file で 343。
