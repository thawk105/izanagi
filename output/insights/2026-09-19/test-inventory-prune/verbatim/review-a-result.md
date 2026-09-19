## 所見

以下、`I/` は `output/insights/2026-09-19/test-inventory-prune/` を指す。

1. **real / must-fix — 裁定と異なる実行元を DW-M07 準拠としている。**
   `I/verbatim/adjudication.md:34` は独立 clone を指定するが、`I/mutation/mutation-summary.md:3` は主 repo の登録 worktree と記録している。実際に `tinv-mut-h/.git:1` は主 repo の `.git/worktrees/tinv-mut-h` を指す。`I/README.md:64` の「DW-M05/M07」準拠表記は成立しない。
   **推奨処置:** 手順差を erratum に明記し、`docs/dev-wave/mutation.md:44` が要求する独立 clone で必要な検証を補う。既存結果は消さず、観測事実と手順適合を分ける。

2. **real / must-fix — 「確認済みの純粋な pin 16関数」が一次資料と食い違う。**
   `I/README.md:12,97` は実挙動を含む代表も確認済み(D)へまとめている。例えば `orchestrator/tests/test_floor_pair_job_contract.py:91` は shell の `select_pin` を実行し、`test_plot_b10_static_tail_formal.py:414` は production の `validate_repo_closure` を呼ぶ。plan もそれぞれ「docs 派生値＋実挙動」「literal hash 固定だけではない」と記録している（`I/verbatim/plan-result.md:333,340`）。
   **推奨処置:** 純粋な pin と実挙動を含む代表を分離し、冒頭・分類表・裁定パッケージの件数を揃える。未確認246関数を確認済みへ広げない。

3. **real / must-fix — 削除後の総行数が異なる基底から算出されている。**
   `I/README.md:19` の `592,832 → 592,817` は、途中で取り込んだ main 前進を反映していない。Git blob の改行数を独立集計した結果は次のとおり。

   | commit | `*.py` | `test_*.py` | 総行数 |
   |---|---:|---:|---:|
   | `a99425b66` | 391 | 363 | 592,832 |
   | `657e1e5a7`（削除前） | 391 | 363 | 592,860 |
   | `0917fc400`（削除後） | 391 | 363 | 592,845 |

   **推奨処置:** 削除前後を `592,860 → 592,845` に訂正する。着手時の592,832は時点付きで保持してよい。

4. **real / should — 所要時間・dispatch件数の記録が不整合。**
   `I/README.md:79` と `I/mutation/mutation-summary.md:20` は起動から完了までの時刻幅を「所要」とするが、DW-O12（`docs/dev-wave/operations.md:95`）は queue 待ちを含む外側wallとの区別を要求する。また summary の「各4 dispatch job」に対し、各結果JSONには collection・baseline・変異3件の**異なる5 job**がある。
   **推奨処置:** 時刻幅を「待ち時間込みの実行期間」と明記し、所要は Elapse または runner 報告値で記録する。job数を5へ訂正する。

5. **real / nit — 台帳coverageの増減方向が逆。**
   `I/README.md:121` は「削除で割合は上がる」とする。しかし検査式は `covered / len(rows)`（`orchestrator/tests/test_acceptance_schedule_order.py:705`）で、今回の6 nodeは全件台帳に存在する。未収録nodeが残る状態で収録済みnodeを除くと割合はわずかに**下がる**。
   **推奨処置:** 増加の説明を削除する。余剰entryを許容する点と区別する。

6. **refuted / must-fix該当なし — 指定外変更・ids対応ずれ・scope逸脱。**
   `orchestrator/tests/test_p3_s4_loop.py:3238,3258`、`test_s8b_holdout_freeze.py:2381` を確認した。author patch は削除commitの差分と完全一致し、変更は指定2 file・6 nodeだけ。test名集合は289→288、108→108で、削除名は指定1件のみ。残存関数本文のAST変更はなく、row/idsは5/5・2/2で対応する。production・conftest・台帳・hold・gateへの変更もない。
   **推奨処置:** 削除実装の修正は不要。

7. **refuted / must-fix該当なし — 変異の検出集合喪失・診断文字列だけのkill。**
   `I/README.md:68` 以下を結果JSONと埋込みstdoutで照合した。HのM1/M2は各6→5、LのM1は23→22、M2は20→16で、すべて **`S_post = S_pre − Del`、非空、登録期待集合と完全一致**。E1は全前後走で赤0。runnerのcommand/file集合も前後一致した。赤理由は例外不送出、不正値の後段到達、受理・拒否の反転であり、診断文だけの赤は確認されなかった。probeをS_preとする工程も裁定に一致する。
   **推奨処置:** この有限変異に対する検出保存の結論は維持できる。

8. **refuted / must-fix該当なし — 主要な台帳数値の混同・wall短縮の過大主張。**
   `I/README.md:20,21,30,45,119` の母数区分・分類集計は一次資料と整合する。collectionは25,381、台帳は24,379 entry・17,958.848秒、削除6 nodeは33.005秒と独立検算した。wall短縮も明示的に主張していない。総行数の誤りは所見3のとおり。
   **推奨処置:** 時点を区別した数値表現を維持する。

## GO/NO-GO

**NO-GO — 削除実装と登録変異の検出保存は妥当だが、所見1〜3の是正が必要。**

## 総括

削除による検出力喪失は確認されなかった。阻害点は実行手順の適合と成果物の正確さである。レビューは読み取り専用で実施し、pytestは再実行していない。親の焦点走ログでは670 passed・2 skipped・child rc=0を確認した。