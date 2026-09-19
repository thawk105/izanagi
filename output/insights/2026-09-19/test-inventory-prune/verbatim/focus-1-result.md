## 対応表判定

以下、`R` は `output/insights/2026-09-19/test-inventory-prune/`、test file は `orchestrator/tests/` 相対。

| 行 | 判定 | 根拠 |
|---|---|---|
| 1 | **closed（手順差の記録として）** | README:67・152 と mutation-summary:3 が独立 clone でなかった事実を明記。4 本の結果 JSON は、内部の baseline・各変異も含め、probe=`657e1e5a7860a0ff77fd02ab37a6cb58b64cc78c`、post=`0917fc400b00c9a83df9e01f508dbfb15614e9ee` で一致する。「再走不採用」は親の裁定として受け入れ、誤った準拠表示の是正は閉じたと数える。ただし独立 clone 手順を事後充足した、または両経路の同等性を実証したという意味ではない。 |
| 2 | **partial** | 純粋な定数 pin 7 関数の分離は正しい。しかし README:100 の「9 関数は同じ関数で production 関数や shell を通す」と、:114 の「2 file に pin だけの test と実挙動検査が併存」は、plan の代表確認と test 本文に一致しない。詳細は新規所見。 |
| 3 | **closed（抽出検算の範囲）** | blob の改行数を独立計数。`test_p3_s4_loop.py` は削除前後で 9,681→9,666、`test_s8b_holdout_freeze.py` は 3,268→3,268。commit 差分もこの 2 file のみで純減15行。着手時からの増分は `test_paper_story_a2_certification.py` の 5,823→5,851（+28）で確認し、592,832→592,860→592,845 と整合する。391 file の総和自体は再集計していない。 |
| 4 | **closed** | 両文書が queue 待ち込みの実行期間と runner 時間を区別。各結果 JSON に異なる dispatch job を5本確認。H baseline の stdout は35.04秒／35.39秒で、記載の35.0秒／35.4秒と整合する。 |
| 5 | **closed** | README:124 は、収録済み6 node の削除により coverage が僅かに下がる説明へ訂正済み。増減方向は正しい。 |
| 6 | **closed** | 削除 commit は指定2 file、+3/−18行。結果 JSON の集合差を再計算し、H は6→5・6→5、L は23→22・20→16、減少分は指定削除 node だけ。post は登録期待集合と完全一致し、E1 は前後とも失敗0。本文に要求外の機構追加や一般的な検出力保存への拡張はない。 |
| 7 | **closed（参照先を含む）** | 7件すべての関数名・定数名を test 本文と照合し一致。記載された schema、4096／65536、5／5、version literal も一致。tuple は本文への参照、family root は省略表記であり、literal 全文を転載した表ではない。実際の root は `88d68f9127b31df5aafc3d59607896626a1652e8`。 |
| 8 | **closed** | README:13 は意味確認した候補の範囲に限定し、:15・133 は取りこぼしを明記。:25・81・125・148–150 で wall 短縮、検出力の一般保存、網羅的な不在証明を主張していない。 |
| 9 | **closed** | README:9 に裁定 #13 の成果物影響、台帳換算 worker 秒、earliest-eligible 選択違反／value-literal 帰属が明記された。 |

## 新規所見

**1. real / must-fix — (D) の修正で、異なる検査を「実挙動併存」へ一括分類している。**

対象は `R/README.md:13,100,114,151`。純粋な定数 pin 7件への縮小は妥当だが、残りの分類説明が正確ではない。

| 確認した関数 | 本文から確認できる検査 |
|---|---|
| `test_paper_story_a1_paired.py:903` `test_legacy_frozen_bytes_have_independent_literal_goldens` | 実ファイルの SHA256 literal とファイル集合の固定。production 関数や shell の実行はない。 |
| `test_skip_classification.py:315` `test_readme_conditional_unrun_census_names_all_nodes` | README の節を抽出し、既定 nodeid の記載を確認。production 関数や shell の実行はない。 |
| `test_t1434_t1222_science_slice.py:409`、`test_t189_oracle_wiring_slice.py:132` の `test_pinned_jobs_requirements_are_exact` | test 内 helper が資料から導出した path 集合を literal tuple と比較。これを production の挙動検査とする根拠はない。 |
| `test_plot_b10_static_tail_formal.py:414` `test_landed_fig8_repo_closure_and_caption_when_present` | 成果物の存在・production の closure 検査・caption 整合。固定 literal への exact pin と一括するのは不適切。 |
| `test_plot_a1_sized_paired.py:388,471` | 両代表とも production の closure 検査を含む。「pin だけの test」の代表ではない。 |
| `test_spool_fold.py:500,1753` | 前者は `spool_fold.plan_fold` の番号導出、後者も helper 経由で同 production 関数の byte-exact 挿入挙動を検査する。両代表とも静的 pin だけではない。 |

plan の表はこれらを個別に区別しており、「9件すべてが実挙動併存」「2 file に pin だけの test がある」とは確定していない。関数単位で「資料・派生値 pin」「pin と挙動検査の併存」「挙動検査」を分け、冒頭・§2・§5・§9 を一致させる必要がある。未確認246関数への分類拡張や追加削除は不要。

wall 短縮・検出力の一般保存・suite 全体への結論について、新たな過大主張は確認しなかった。

## GO/NO-GO

**NO-GO — 対応表2が partial。(D) の関数単位の分類説明を修正してから成果物を確定する。**

## 総括

9行中8行を closed、1行を partial と判定した。残る阻害点は (D) の報告分類であり、今回の照合で削除実装や登録変異の検出集合に新たな問題は認めなかった。読み取り専用で実施し、pytest・変異の再走およびファイル変更は行っていない。