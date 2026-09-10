## 所見別判定

| 所見 | 判定 | 根拠 |
|---|---|---|
| R1-F1 | closed | 最初の `lock_raw` から hash を固定し、歴史枝・post-policy 枝の双方で live lock/WAL を拒否専用に再照合している。[artifact_admission.py:534](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:534)、[artifact_admission.py:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:614)、[artifact_admission.py:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:696)。両枝の置換テストもある。[test_artifact_admission.py:418](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:418) |
| R1-F2 | closed | A を返す直前に live path を B へ変更し、注入発火と最終 bytes を明示確認する。[test_artifact_admission.py:438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:438)、[test_artifact_admission.py:450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:450)。M8 は `lock_sha=B` となって終端 B と一致し、`raises` が成立しないため静的に kill される。[mutation-spec.json:127](/work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/mutation-spec.json:127) |
| R1-F3 | closed | snapshot の全 `campaign.lock` 集合と overlay 3件＋旧 trigger 6件＋正例21件の和集合を完全一致で比較する census が追加された。[test_artifact_admission.py:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:300)、[test_artifact_admission.py:316](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:316) |
| R2-1 | closed | validator SHA が全 decision receipt で変わること、調査範囲で persisted receipt が0件だったこと、他 filesystem が未探索であることを新 D が明記する。[decision fragment:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/docs/spool/decisions/2026-08-05-dev-wave-t474-legacy-trigger-admission-1.md:57) |
| R2-2 | closed | 従来から分類値は存在したが、raw-view capability が status だけで決まり、consumer に分類分岐を強制しなかった、と記述が限定された。[decision fragment:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/docs/spool/decisions/2026-08-05-dev-wave-t474-legacy-trigger-admission-1.md:40)、[artifact_admission.py:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:95) |
| R2-3 | closed | supersede 対象を D160 決定5の「機械 sweep 6件の遡及被害ゼロ」という raw-admission 結果だけに限定し、binding 遡及要求の却下維持を逐語で明記した。[decision fragment:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/docs/spool/decisions/2026-08-05-dev-wave-t474-legacy-trigger-admission-1.md:29) |
| R2-4 | closed | R1-F3 と同じ census により、trusted snapshot 拡張時の literal 追随漏れは assertion failure になる。[test_artifact_admission.py:300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:300) |

## 新規所見

### N1 / 新 D の「read-once」が拒否専用の終端再読を明記していない / severity: nit

- 根拠: D は「lock を read-once にする」「hash・parse・分類・snapshot・receipt を同一 bytes に由来させる」と記すが、実装は歴史枝と post-policy 枝で live lock を再読している。[decision fragment:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/docs/spool/decisions/2026-08-05-dev-wave-t474-legacy-trigger-admission-1.md:25)、[artifact_admission.py:614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:614)、[artifact_admission.py:696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:696)。
- 失敗シナリオ: 後続保守者が D の “read-once” を物理的な一回読みに解釈し、終端照合を再び削除する。
- 成果物影響: 現行コードへの影響はない。将来削除された場合は R1-F1 の receipt=A／live path=B の raw view が再発しうる。
- 提案: 「権威となる読取りは一回。終端では live lock/WAL hash を拒否専用に再照合し、再読 bytes は分類・receipt に使わない」と D に明記する。

## 退行確認

- 並行書込みのない通常経路では、最初の `lock_raw` と終端の同一ファイルから同じ digest が得られるため、新再照合による偽陽性拒否は認めない。非 trigger 歴史21件と post-policy 機械 sweepについて、受理継続を要求するテストも残っている。[test_artifact_admission.py:407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:407)、[test_artifact_admission.py:535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:535)

- `Path.read_bytes` monkeypatch は `_sha256_file` が使う `Path.open` を差し替えないため、初回 snapshot と終端 oracle は独立している。[artifact_admission.py:227](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:227)。B は末尾改行だけで JSON の意味は同じなので、このテストが直接証明するのは workload 差ではなく byte identity である。任意の semantic B も同じ不一致条件に含まれるため、M8/M9 の検出には十分である。

- `_is_proven_pre_policy_artifact=True` は歴史 parameter だけの分岐隔離であり、実 artifact の Git path/hash ancestry や trigger 性を代表しない。[test_artifact_admission.py:422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:422)。ただし post-policy parameter はこの固定を使わず、それ単独でもM8を殺す。実歴史 artifact の性質は別の6件負例・21件正例で検査される。[test_artifact_admission.py:382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:382)

- census は snapshot pointer の拡張・削除・renameでは安全側に失敗し、明示分類を要求する。pointer を変えず現行 tree に campaign を追加した場合は census は壊れないが、その artifact は Git snapshot 三点照合を通らず拒否される。[artifact_admission.py:371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:371)、[artifact_admission.py:605](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:605)。WALだけの孤児は census 対象外だが、production が lock/WAL の双方を要求するため受理されない。[artifact_admission.py:528](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/artifact_admission.py:528)

- N1 の記述精度を除き、新 D の適用範囲、status、freeze grandfather、validator SHA drift は実装と一致する。freeze consumer は引き続き旧 provenance／known-axes freeze を直接読む。[s1_known_axes_freeze.py:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/s1_known_axes_freeze.py:471)、[s8b_holdout_freeze.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/s8b_holdout_freeze.py:524)

## 変異事前登録

各置換の `old` 署名は HEAD `643c191` に一意に存在した。以下は実走ではなく静的予測である。

| 変異 | `expected_nodes` の妥当性 | 静的予測 |
|---|---|---|
| M1 | 負例6件、Layer3、真理値表はいずれも helper の真側を観測する | KILLED |
| M2 | 正例21件と真理値表の偽側が定数 True を拒む | KILLED |
| M3 | 真理値表の非 trigger axis、および正例中の sort-axis 4件が失敗する | KILLED |
| M4 | proposal 形状・未知形状は machine predicateでは偽になる。[wal.py:663](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/campaign/wal.py:663) | KILLED |
| M5 | 負例の exact status／`CampaignNotAdmitted` とLayer3拒否が失敗する | KILLED |
| M6 | 負例6件、Layer3、既存 overlay の各 `raises` が成立しなくなる | KILLED |
| M7 | post-policy machine sweep の `admission_status == admitted` が失敗する。[test_artifact_admission.py:535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t474-legacy-trigger-admission/orchestrator/tests/test_artifact_admission.py:535) | KILLED |
| M8 | A返却後にBへ置換すると、変異版だけ `lock_sha=B`・終端Bとなり拒否しない | KILLED |
| M9 | 登録変異は歴史枝のlock比較だけを削除する。歴史 parameter は snapshot gate を固定しているため、WAL不変のまま返却し `raises` が失敗する | KILLED |

M8 は裁定 §4 の「生存見込み」を §7 が明示訂正しており、実 spec の `expected_status: KILLED` と整合する。[s4-adjudication.md:143](/work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/s4-adjudication.md:143)、[mutation-spec.json:127](/work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/mutation-spec.json:127)。

M9 は登録上、歴史枝だけを変異する。[mutation-spec.json:143](/work/1/SFC/tanab/dev-wave-jobs/t474-legacy-trigger-admission/mutation-spec.json:143)。post-policy 側の削除は matrix では独立変異されないが、同じ parameterized test の post-policy ケースが静的にはそれを検出する。登録済み9変異に生存見込みはない。

本レビューでは pytest・変異 matrix を実走していない。fix後113 passedは親提示の実測としてのみ扱い、進行中matrixの結果は未確定である。

## 総括

**GO（静的レビュー）— 残 must-fix 0件、nit 1件。**

R1/R2の7所見はすべて closed。land 前には進行中matrixが9件すべて KILLED になることを確認し、生存が出た場合は再判定を要する。