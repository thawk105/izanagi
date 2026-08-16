# [T-403] 孤児 job の後始末を fail-closed にした wave の一次資料

wave: `dev-wave-t403-orphan-job-hold` / branch: `worktree-dev-wave-t403-orphan-job-hold`
base: `478a4138` / 実装 commit: `2f6e1af9` → `94ee9fe1` / 実施日: 2026-08-16

## 何を変えたか

D142 の qdel gate が取消を見送った job は孤児として計算ノードに残り得る。変更前は receipt と
stderr 1 行の警告だけで、次回投入・変異 source の復元・変異 worktree の廃棄・受入 probe の
掃除のいずれも止まらなかった。create-only の latch
(`output/pegasus-dispatch/orphan-hold.json`) を導入し、この 4 経路を fail-closed で止める。
latch を書けなかった場合は、変異 harness が書く停止記録 `<--out>.orphan-stop.json` が権威になり、
次回起動 (fresh / `--resume` の双方) を止める。
設計判断の正本は decisions 台帳、経緯は worklog。**qdel を実行する経路は増やしていない。**

## この wave が保証しないこと

- latch は latch であって相互排他 lock ではない。
- qsub 前の永続 claim を作らないため、SIGKILL と request ID 照会中の再 signal の窓は残る。
- 保護範囲は `dispatch_compute` 経由の dispatch と変異 harness / 変異 worktree / 受入 checker に限る。
  直接 qsub する `tools/pegasus/submit_*.sh`、`orchestrator/campaign/patchharness.py` の
  checkout 復元・worktree 強制削除、local 実行経路は対象外。

## ファイル

| path | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief。親が brief 前に取った実測 3 点を含む |
| `s4-ruling.md` | 段 4 裁定 (plan v2、変異事前登録、scope 外の裁定パッケージ) |
| `s6-fix-ruling.md` | 段 6 fix 第 1 巡の裁定 (must-fix 6 件、変異登録の改訂) |
| `s6-fix2-ruling.md` | 段 6 fix 第 2 巡の裁定 (焦点再レビューの land 阻止所見への対応) |
| `verbatim/s2-plan.md` | 段 2 プラン起草 (codex, read-only, reasoning=max) |
| `verbatim/s3-lens-a-correctness.md` | 段 3 敵対相談 レンズ A (正しさ境界) |
| `verbatim/s3-lens-b-scope.md` | 段 3 敵対相談 レンズ B (整合・実効性・運用) |
| `verbatim/s5-impl.md` | 段 5 実装子の報告 |
| `verbatim/s6-review-a.md` | 段 6 敵対レビュー A (正しさ境界) |
| `verbatim/s6-review-b.md` | 段 6 敵対レビュー B (検出力・波及) |
| `verbatim/s6-fix.md` | 段 6 fix 第 1 巡の報告 |
| `verbatim/s6-focus.md` | 段 6 焦点再レビュー (land 阻止所見を出した) |
| `verbatim/s6-fix2.md` | 段 6 fix 第 2 巡の報告 |
| `mutation-spec-v3-probe.json` | 変異 spec 第 3 版 (probe)。期待集合が古かった |
| `mutation-spec-v4.json` | 変異 spec 第 4 版 (権威)。sha256 = `4dc2686c1721b28c26262e5847175aad2ea82edd9eb21e3397fe9d55a0fead9d` |
| `mutation-ledger-run4.json` | 権威ある変異台帳。15/15 KILLED、MISMATCH 0、baseline PASSED |

## 変異 matrix

`tools/mutation_worktree.py` の使い捨て worktree で `--runner-mode dispatch` により走らせた。
runner 範囲は変更 4 test file (`test_pegasus_dispatch_compute.py`, `test_mutation_harness.py`,
`test_mutation_worktree.py`, `test_check_acceptance_reds.py`)。

| id | 変異 (wave 前の形へ戻す) | 結果 |
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
| M13 | 停止記録による起動 gate を削除 | KILLED |
| M14 | wrapper の孤児分類から停止記録の項を落とす | KILLED |
| P1c | ハーネス検出を常時成立へ (過剰拒否の正例) | KILLED |

**erratum:** 権威走 (run4) の前に 3 度走らせている。

1. run1 (13 変異、spec v1): 否定 12/12 KILLED、正例 1 本が MISMATCH。期待ノードは落ちたうえで
   6 件多く落ちており、殺せていないのではなく期待集合が不完全だった。
   wrapper は matrix 完走後の evidence 退避だけ EXDEV で失敗した (`--out` が `/home`、
   scratch が `/work` で別 device)。この知見は `docs/dev-wave/mutation.md` の `DW-M07` へ入れた。
2. run2 (13 変異、spec v2、完全集合): 13/13 KILLED、wrapper rc=0。
3. run3 (15 変異、spec v3、fix 第 2 巡の M13 / M14 を追加): 12 KILLED / 3 MISMATCH。
   3 件とも「期待より多く落ちた」側で、殺せなかった変異はゼロ。fix 第 2 巡が足した検査が
   同じ分岐を共有し始めたため、run2 時点の期待集合が古くなっていた。
4. run4 (15 変異、spec v4、run3 の観測値から完全集合を再導出): **15/15 KILLED、MISMATCH 0**。

期待 node は fix 後の最終 commit で `--junitxml` の権威一覧 (349 node) から再導出した (DW-M08 / F33)。
node ID は 2 空間ある (pytest は非 ASCII param をエスケープし、harness は backslash を `/` へ潰す)
ため、突き合わせは harness 側の正規化に揃えている。

**登録しなかった変異:** 過剰拒否の正例のうち dispatch 署名・dispatch 検出・worktree 検出・
受入検出の 4 面は、影響が正常経路のテスト全体へ広がり完全集合を静的に確定できなかったため
登録していない (DW-M01 の「確認できなければ登録せず実効 gate へ再照準する」)。
進行停止だけを狙う変異も、同形の分岐が 3 箇所あり単一理由の一意 anchor を作れなかったため
登録していない。いずれも worklog の新規項へ検証 backlog として登録した。

## 焦点走の実測

- 実装 commit `2f6e1af9` 時点: 変更 4 file + 波及候補 10 file = **1493 passed / 0 failed**
  (計算ノード、request 913414)。
- fix 第 2 巡 `94ee9fe1` 時点: 変更 4 file = **349 passed / 0 failed**
  (計算ノード、request 913702)。JUnit の権威 node 数も 349。
