Must-fix 2 件を確認したため NO-GO。安定した静止入力については裁定どおりですが、lock の競合更新防壁と、その回帰を殺す M8 テストが不足しています。本レビューでは pytest・変異実走は行っておらず、親提示の「100 passed」は基準実装の対象 2 ファイルに限る事実として扱いました。

## 所見

### F1 / 終端 lock 再照合の削除は read-once の必然ではなく、競合更新検査の消失 / severity: must-fix

- 根拠: lock の hash・意味解析は同じ `lock_raw` に統一されていますが、歴史枝と post-policy 枝の終端は WAL しか再照合しません。[artifact_admission.py:534](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:534)、[artifact_admission.py:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:614)、[artifact_admission.py:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:696)。返却値は live path を公開し、receipt にその path と最初の bytes の hash を載せます。[artifact_admission.py:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:150)、[artifact_admission.py:627](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:627)
- 攻撃・失敗シナリオ: admissible な lock A を `read_bytes()` した後、WAL parse 中に別プロセスが path を trigger lock B へ atomic replace する。現在の実装は A の hash・分類で `AdmittedCampaign` を発行する一方、返却時の `lock_file` は B を指す。旧終端照合なら A/B 不一致を検出した。A→B→A の旧 ABA 問題は、終端再読を分類に使わず拒否専用にすれば再発しない。
- 成果物影響: raw view の受理集合に「receipt は A、参照 path は B」の campaign が加わり、certified 選択の前段が異なる workload identity を参照できる。Layer3 は独自の再照合で現在は拒否するため、同経路の材料レポートと試行台帳は発行されない。[layer3_report.py:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/layer3_report.py:424)
- 提案: 614 行・697 行の終端条件へ lock hash 比較を戻す。ただし parse・分類・receipt は引き続き `lock_raw` のみを使う。`wal.read_records_checked` を monkeypatch して、その実行中に tmp campaign の lock を A→B へ置換し、`ArtifactAdmissionError` を要求する境界テストを追加する。

### F2 / M8 は生存し、「決定論的注入路がない」という事前登録の前提は成立しない / severity: must-fix

- 根拠: 裁定は M8 の生存を既知穴としていますが、`read_bytes()` と hash は別の Python 呼び出しとして観測可能です。[s4-adjudication.md:112](/work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/s4-adjudication.md:112)、[artifact_admission.py:534](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:534)。追加テストは静止 corpus と helper の真理値表だけで、この間への注入がありません。[test_artifact_admission.py:299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:299)、[test_artifact_admission.py:358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:358)
- 攻撃・失敗シナリオ: tmp campaign の `Path.read_bytes` を、A を読み取った直後に path へ B を置いてから A を返すよう monkeypatch できる。正しい実装の `lock_sha` は A、M8 の `_sha256_file(lock_path)` は B になる。M8 では A の admission policy を検査しつつ、B の hash を receipt に記録できる。
- 成果物影響: Layer3 は B を再読して receipt の B hash と一致すると判断し、A で admission 済みという `classification` と、B 由来の `workload` を同じ材料レポートに載せられる。[layer3_report.py:392](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/layer3_report.py:392)、[layer3_report.py:461](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/layer3_report.py:461)、[layer3_report.py:468](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/layer3_report.py:468)。試行台帳の `cell["admission_decision"]` もその receipt をコピーするため、certified 選択・材料レポート・台帳の三者が同じ誤結合を継承する。[p3_autonomous_workload_trial.py:1165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/p3_autonomous_workload_trial.py:1165)
- 提案: F1 の終端照合を戻したうえで、上記 `Path.read_bytes` 注入に対して拒否を要求する。このテストでは正実装は A/B 不一致で拒否し、M8 は hash B と終端 B が一致して誤受理するため、決定論的に M8 を殺せる。

### F3 / 21 件の正例は現在は完全だが、将来の receiptless artifact 追加を黙って見逃す / severity: nit

- 根拠: 正例は固定 literal 21 件を parameterize するだけで、repo の receiptless campaign 集合との等値検査がありません。[test_artifact_admission.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:88)、[test_artifact_admission.py:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:383)
- 失敗シナリオ: 新しい歴史 artifact を snapshot に追加しても、この parameterize 集合は増えず、テストは壊れない。新 artifact だけを過剰拒否する実装でも既存 21 件は通る。
- 成果物影響: 将来追加された非 trigger 歴史 campaign の raw view・Layer3 材料・そこを参照する台帳だけが `legacy-unclassified` へ誤縮小されても、当該 corpus テストは検出しない。現在の repo では問題なし。
- 提案: `output/campaigns/*/campaign.lock` から独立に列挙した receiptless 集合と、overlay 3 件＋trigger 6 件＋正例 21 件の union が等しいことを確認する maintenance sentinel を追加する。

## R1 検証結果

静止 repo の受理集合は裁定 §3.1 / §3.2 と一致しています。

- helper は lock dict、`search_config` dict、axis 一致だけを条件とし、形状を限定していません。[artifact_admission.py:384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:384)
- 歴史枝だけで status を変更し、classification は維持しています。[artifact_admission.py:618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:618)
- tracked campaign.lock 30 件は、overlay 3 件、旧 trigger 6 件、正例 21 件に過不足なく分割されていました。6 件の lock/WAL SHA literal も実 bytes と一致し、全 lock が trigger axis を持っています。[test_artifact_admission.py:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:56)
- 将来追加時は F3 のとおり、固定 21 件側が壊れるのではなく追加分を見逃す方向です。

変異は実走せず、テストコードから静的に判定しました。

| 変異 | 判定 | 検出点 |
|---|---|---|
| M1 | kill | 真側 3 行、反例 6 件、Layer3 拒否 |
| M2 | kill | 偽側 4 行、正例 21 件 |
| M3 | kill | 非 trigger axis 行と sort 歴史正例 |
| M4 | kill | proposal 形状・未知形状の真側 |
| M5 | kill | 反例の exact status／raise と Layer3 |
| M6 | kill | 反例の `CampaignNotAdmitted` 要求と既存 overlay テスト |
| M7 | kill | post-policy machine sweep が `admitted` のままという既存検査。[test_artifact_admission.py:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:471) |
| M8 | **survive** | read/hash 間の書換え注入がない。F2 のテストで kill 可能 |

真理値表は lock 非 dict、search 非 dict、axis 不一致、axis 一致の各分岐を実際に通しており、恒真ではありません。corpus テストが helper と歴史枝の結線を、Layer3 テストが exact error と出力不存在を検査するため、M1〜M7 に対する空虚な追加テストもありません。

初回 lock 読み取りの `OSError`、strict JSON 破損、未証明 receiptless artifact は例外になり安全側です。[artifact_admission.py:534](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:534)、[artifact_admission.py:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:217)、[artifact_admission.py:605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:605)。`search_config` 欠落・非 dict は exact Git snapshot が証明された歴史 bytes だけ従来どおり admitted、それ以外は拒否されます。新 helper は例外を捕捉しておらず、異常を飲み込む経路はありません。ただし初回読取り後の unreadable/replacement は F1 の穴です。

## 総括

**NO-GO — must-fix 2 件、nit 1 件。**