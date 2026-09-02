## 発効閉包の照合

real — 親 brief の「4 箇所」は不足しており、実際には少なくとも 5 編集箇所が必要である。pilot policy を束縛すると、将来の sized policy fixture が pilot policy をコピーして `study_id` だけを変更するため、pilot の非 null `preregistration` を引き継ぐ（[test_paper_story_a1_paired.py:1018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_paper_story_a1_paired.py:1018)）。そのまま [test_paper_story_a1_paired.py:1074](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_paper_story_a1_paired.py:1074) の loader を呼ぶと、sized policy には sized module pins を要求する照合（[paper_story_a1_paired.py:1377](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1377)）で失敗する。既存機構で閉じるには、fixture 内で `sized["preregistration"]` を `V3_SIZED_PREREGISTRATION_RELATIVE_PATH/_SHA256` から作り直す編集を追加する。

refuted — brief に挙げられた既存 4 箇所に不要なものはない。JSON の binding は module pins と完全一致しなければならず（[paper_story_a1_paired.py:1374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1374)）、JSON bytes は `_policy_identity` が返す `V3_PILOT_POLICY_SHA256` と照合され（[paper_story_a1_paired.py:743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:743)、[paper_story_a1_paired.py:1440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1440)）、README bytes も JSON の hash と照合される（[paper_story_a1_paired.py:1446](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1446)）。したがって JSON、module prereg pins、policy hash pin、未凍結正例の更新はいずれも必要である。

refuted — これら以外の runtime pin は不要である。`_require_policy_ready_for_execution` 自体は path/hash の非 null だけを見るが（[paper_story_a1_paired.py:1472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1472)）、実行経路は先に `load_policy`/`validate_policy` を通り、module pins、policy bytes、README bytes を上記の順で検証する（[paper_story_a1_paired.py:1456](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1456)）。

## 束縛後に赤へ転じる assertion の全列挙

1. real — `policy["preregistration"] == {"path": None, "sha256": None}` は束縛後に偽となる（[test_paper_story_a1_paired.py:1386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_paper_story_a1_paired.py:1386)）。

2. real — `V3_PILOT_PREREGISTRATION_RELATIVE_PATH is None` は exact path を設定した時点で偽となる（[test_paper_story_a1_paired.py:1387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_paper_story_a1_paired.py:1387)）。

3. real — `V3_PILOT_PREREGISTRATION_SHA256 is None` は README hash を設定した時点で偽となる（[test_paper_story_a1_paired.py:1388](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_paper_story_a1_paired.py:1388)）。

4. real — `_require_policy_ready_for_execution(policy)` が `"not frozen by the parent"` を投げるという `pytest.raises` 期待は、束縛後には例外が出ず失敗する（[test_paper_story_a1_paired.py:1389](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_paper_story_a1_paired.py:1389)）。

real — 上の明示 assertion 4 件とは別に、`test_v3_loader_accepts_future_sized_policy_shape` も assertion 到達前の loader 呼出しで赤になる（[test_paper_story_a1_paired.py:1018](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_paper_story_a1_paired.py:1018)、[test_paper_story_a1_paired.py:1074](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_paper_story_a1_paired.py:1074)）。段 2 プランの「1351–1390 だけ更新」は全 failing test を閉じない（[s2-plan.md:221](/home/SFC/tanab/.claude/jobs/c99c0cba/tmp/t1777-pilot-prereg/artifacts/t1777-pilot-prereg/s2-plan.md:221)）。

## 追加だけで赤になる検査

refuted — `test_frozen_artifacts.py` は新しい insights directory の census を取らない。検査対象は `FROZEN_MANIFEST` の列挙済み path だけで（[test_frozen_artifacts.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_frozen_artifacts.py:41)、[test_frozen_artifacts.py:171](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_frozen_artifacts.py:171)）、23 件 assertion も manifest 自体の形を固定するものに限られる（[test_frozen_artifacts.py:234](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_frozen_artifacts.py:234)）。README 追加だけでは赤にならない。

refuted — `test_artifact_admission.py` の real-tree exact assertions は `output/campaigns` または `campaign.lock` だけを対象にする。commit census は `output/campaigns` 限定（[test_artifact_admission.py:830](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_artifact_admission.py:830)）、dirty-byte 検査も同じ（[test_artifact_admission.py:853](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_artifact_admission.py:853)）、全 output 走査は basename `campaign.lock` のみ（[test_artifact_admission.py:877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_artifact_admission.py:877)）である。新 README は受理規則へ入らない。

refuted — `check_docs.py` の placeholder guard は `output/insights/*.md`、すなわち直下 Markdown だけを `Path.glob("*.md")` で列挙する（[check_docs.py:2611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/tools/check_docs.py:2611)、[check_docs.py:2649](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/tools/check_docs.py:2649)）。新しい directory 配下の `README.md` は走査されないため、追加だけでは赤にならない一方、「check_docs が本文の placeholder 不在を証明した」とは報告できない。

refuted — 計測先との接頭辞共有は、射影された検査では問題にならない。paired test の唯一の `rglob` は別の headline preregistration directory を exact root とする（[test_paper_story_a1_paired.py:925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_paper_story_a1_paired.py:925)）。artifact admission も prefix 比較ではなく `output/campaigns` または `campaign.lock` を選別している（[test_artifact_admission.py:877](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_artifact_admission.py:877)、[test_artifact_admission.py:898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/tests/test_artifact_admission.py:898)）。

## 工程分割の境界

refuted — 本文を local main へ着地させるだけでは発効の既成事実化にあたらない。線は「候補 README の bytes が存在するか」ではなく、「policy の preregistration と module pins/policy hash を一致する非 null 値で commit し、execution readiness を開いたか」である（[decisions.md:44017](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/docs/decisions.md:44017)、[decisions.md:44163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/docs/decisions.md:44163)、[paper_story_a1_paired.py:1472](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1777-pilot-prereg/orchestrator/campaign/paper_story_a1_paired.py:1472)）。

real — 発効手順全体は現状のままでは曖昧さなく完遂できない。hash 算出と pin 更新の順序は明確だが、テスト更新範囲が不足し、さらに「focused tests」「full acceptance」が具体的コマンド/nodeid なしの総称になっている（[s2-plan.md:218](/home/SFC/tanab/.claude/jobs/c99c0cba/tmp/t1777-pilot-prereg/artifacts/t1777-pilot-prereg/s2-plan.md:218)、[s2-plan.md:221](/home/SFC/tanab/.claude/jobs/c99c0cba/tmp/t1777-pilot-prereg/artifacts/t1777-pilot-prereg/s2-plan.md:221)、[s2-plan.md:222](/home/SFC/tanab/.claude/jobs/c99c0cba/tmp/t1777-pilot-prereg/artifacts/t1777-pilot-prereg/s2-plan.md:222)）。

refuted — hash 算出には複合 shell 判定器は埋め込まれていない。README と policy JSON に対して独立した固定 path の `sha256sum -- <path>` が各 1 コマンドとして示されており、各コマンドから採用すべき digest は一意である（[s2-plan.md:211](/home/SFC/tanab/.claude/jobs/c99c0cba/tmp/t1777-pilot-prereg/artifacts/t1777-pilot-prereg/s2-plan.md:211)、[s2-plan.md:214](/home/SFC/tanab/.claude/jobs/c99c0cba/tmp/t1777-pilot-prereg/artifacts/t1777-pilot-prereg/s2-plan.md:214)、[s2-plan.md:220](/home/SFC/tanab/.claude/jobs/c99c0cba/tmp/t1777-pilot-prereg/artifacts/t1777-pilot-prereg/s2-plan.md:220)）。

## hash の脆さ

refuted — 「人間が本文を編集すると親算出 hash が無効になる」脆さ自体はプランで扱われている。最終 bytes の確認、人間編集時の発効 commit への包含、README hash の再計算、その値を使った JSON/module pin 更新、変更後 JSON hash の再計算という順序が明記されている（[s2-plan.md:211](/home/SFC/tanab/.claude/jobs/c99c0cba/tmp/t1777-pilot-prereg/artifacts/t1777-pilot-prereg/s2-plan.md:211)–[s2-plan.md:220](/home/SFC/tanab/.claude/jobs/c99c0cba/tmp/t1777-pilot-prereg/artifacts/t1777-pilot-prereg/s2-plan.md:220)）。親の報告値も「本 wave が着地させた bytes に対する値」と限定する設計である（[s1-brief.md:56](/home/SFC/tanab/.claude/jobs/c99c0cba/tmp/t1777-pilot-prereg/s1-brief.md:56)）。

## その他の所見

real — 機構上必要な成果物 B が段 2 プランから落ちている。brief は wave insight に発効手順と README hash を残すと定めるが（[s1-brief.md:19](/home/SFC/tanab/.claude/jobs/c99c0cba/tmp/t1777-pilot-prereg/s1-brief.md:19)）、プランは「成果物は README 1 ファイルだけ」としている（[s2-plan.md:3](/home/SFC/tanab/.claude/jobs/c99c0cba/tmp/t1777-pilot-prereg/artifacts/t1777-pilot-prereg/s2-plan.md:3)）。発効手順を ephemeral な段 2 artifact のみに置かず、brief 指定の wave insight へ残す必要がある。

refuted — テスト実測による緑の確認は行っていない。本所見は指定された read-only 射影に対する静的検査だけである。

## 総括

- 発効閉包へ future-sized fixture の `preregistration` リセットを第 5 編集箇所として追加する。
- 未凍結 assertion 4 件を exact path/hash と readiness 成功の正例へすべて更新する。
- README hash → binding → policy hash の単純な再計算順序と「着地 bytes 限定」の注記は維持する。
- brief 指定の成果物 B を復活させ、発効手順・provisional hash・具体的受入コマンドをそこへ残す。
- `check_docs.py` は nested README を走査しないため、その本文を検査したとは報告しない。