単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-b

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/stage4-ruling.md — **段 4 裁定とプラン v2 の差分 (本作業の正本)。plan と食い違う箇所はこちらが優先**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s2-plan-r2.md — 段 2 プラン (§6 と §7 の caller test、§9 の C1〜C5 が本作業)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/codex/s3-consult-B.md — 段 3 相談 B (説明文の限定・test 重複の背景)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2632-b4-evidence-carrier/verbatim/insight-t2632-s2.2-2.3.md — caller の欠陥の一次資料 (§2.3)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-b/orchestrator/campaign/p3_b4_prerun_caller.py — **所有 file 1 (編集対象)**。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-b/orchestrator/tests/test_p3_b4_prerun_caller.py — **所有 file 2 (編集対象)**。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-b/orchestrator/campaign/campaign_lock.py — 既存 codec (読むだけ、編集しない)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-b/orchestrator/tests/campaign_lock_test_support.py — v2 lock fixture helper (読むだけ、編集しない)。読めなければ即停止

## 作業 (プラン v2 の caller 側)

所有 2 file だけを編集し、次を実装する。

1. `collect_scheduled_batch` の lock 読取りを `campaign_lock.decode_campaign_lock_bytes` 経由にし、`trial` を `decoded.identity.get("trial")` で取る (plan §6)。
   codec の例外は既存の catch (`ValueError` 派生) で `CampaignInputUnreadable` へ写す。v1 / v2 の独自救済分岐・fallback を足さない。
2. 説明文の限定 (裁定 §3.4): module docstring と `collect_scheduled_batch` の docstring、`# All twelve sources are absent in the current storage format.`
   を「この caller が読む checkpoint (whiteboard 5 field) と lock だけでは構成できない静的な不足分類」と限定する。`_MISSING_SOURCES` の値と件数は変えない。
3. test (裁定 §3.3 の caller 部分): 既存 `_campaign` fixture を v2 lock (`campaign_lock_test_support.build_v2_campaign_lock` に canonical identity 文字列を渡す) にし、
   既存 test (success-only・mixed・minimal rejected・fail row・publication root・unreadable の parametrize) をそのまま v2 で通す。
   `broken == "trial"` は valid v2 identity 内の trial を未知値にして再 encode する形へ。追加は次だけ —
   `test_v1_campaigns_remain_readable` (tracked 3 campaign と同形の top-level trial を持つ v1 lock を各 driver で読める)、
   v1 の trial 欠落が `campaign_input_unreadable` になる test、invalid lock の parametrize への non-certifying lock・非 canonical v2・壊れた authority・
   invalid UTF-8 の追加と issuer 未呼出しの assert。`test_v2_campaigns_reach_empty_issuer` / `test_unknown_v2_trial_is_campaign_input_unreadable` は作らない (既存 test と重複)。
   v2 lock の binding は module 単位で 1 回だけ作る (test ごとに HEAD blob を読み直さない)。

## 制約 (すべて守る)

- **`git commit` を一度も実行しない。** 残差の commit は起動器が行う。
- **docs を編集しない。** 所有 2 file 以外の file を作成・編集しない。`campaign_lock.py`・`campaign_lock_test_support.py`・issuer・`p3_s4_loop.py` には触れない。
- **テストを走らせない** (`tools/run_tests.py`、`python3 -m pytest`、test file の自走 harness のいずれも使わない)。親が計算ノードで焦点走を行う。
  報告は「実装済み・未実走」と書く。静的検査 (`python3 -m py_compile` の 2 file) は行ってよい。
- 変更前の受理・拒否挙動を報告の冒頭に明記する (v1 top-level trial は受理、v2 は `unknown trial: None` で `campaign_input_unreadable`、など)。
  変更後に受理が広がるのは v2 だけで、旧 `json.loads` が受理していた不正な v1 (duplicate key・非有限値) が拒否側へ移ることは裁定の範囲内として報告に書く。それ以外の受理集合を変えない。
- 新設・改名した test が既存の制約 meta-test に触れないかを**自分で洗い出して静的に確認する** (親の名指しを網羅と見なさない)。
  少なくとも: `orchestrator/tests/acceptance_duration_ledger.json` の nodeid 目録を検査する test の有無、test file 集合を列挙する meta-test の有無。他にもあれば挙げる。
- テストを甘くして緑にしない (期待値の緩和、`in` 検査への置換、既存 assert の削除をしない)。期待値に揮発値 (HEAD の commit SHA・blob digest) を焼き込まない。
  issuer は既存 fixture どおり実物を通し、stub しない。
- 予算が尽きそうなら、途中までの内容を下記の報告形式どおりに書いて終える。

## 報告形式

1. 変更前の受理・拒否挙動
2. 変更した file と箇所 (関数名・行)
3. 静的検査の結果 (実行したコマンドと rc)
4. 洗い出した meta-test と、それぞれが今回の変更で影響を受けるか
5. 所有外の caller・共有 fixture・consumer test への波及の静的列挙
6. 未実走であることの明記と、親が走らせるべき nodeid の候補 (新設・変更 test の完全な nodeid)
7. 裁定 §4 の変異 C1〜C5 について、実装後の位置 (一行) と、同じ入力を拒否する層が前後・内側に無いかの自己点検
最後に `## 総括` を置く。
