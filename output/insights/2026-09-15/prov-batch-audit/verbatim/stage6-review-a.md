## 所見

**R-1 — nit：I-4 はテストを赤くできるが、受理集合差による kill の証拠が不足している。**

- **file:line:** [test_check_ai_provenance.py:7331](/work/1/SFC/tanab/izanagi/.codex/worktrees/prov-batch/orchestrator/tests/test_check_ai_provenance.py:7331)
- `commits = list(messages)` という変異は、重複した `outside` の finding が消えるため、この assertion で赤くなる。しかし残った2件も違反なので、拒否は維持される。これだけでは裁定 §4 の「受理集合を変える変異を KILLED」の証拠にならない。
- **受理集合への影響:** 現実装の変化は発見していない。変異側では、同じ correction OID を二重に含む監査列を重複排除すると、`candidate_count` が2から1になり、拒否から前方訂正による受理へ動く可能性がある（[checker:2166](/work/1/SFC/tanab/izanagi/.codex/worktrees/prov-batch/tools/check_ai_provenance.py:2166)、`:2181`）。
- **成果物への影響:** 現実装の certified 選択・台帳への影響は未検出。現状の赤だけを受理集合差の kill と報告すると、変異レポートが検証範囲を過大表示する。
- 固定 correction fixture の同一 OID を二重に選び、旧拒否→変異受理を検査すると、この区別を閉じられる。

## 群 I 変異の kill 対応表

以下は**コードから判断した検出対応であり、変異実走の KILLED 報告ではない**。テスト名はすべて `orchestrator/tests/test_check_ai_provenance.py` 配下。

| 変異 | 赤くするテストと根拠 |
|---|---|
| I-1 | `test_batch_messages_match_show_bytes`（`:7174`）が OID ごとの値の交換を検出。`test_batch_subprocess_counts_and_selected_order[False]`（`:7304`）も、正常／違反 commit の帰属変更を固定 findings で検出する。 |
| I-2 | `test_batch_trailing_whitespace_changes_acceptance_if_stripped`（`:7339`）。末尾 VT を保持すると拒否、`rstrip()` 後は受理となることを明示し、一括監査と旧取得を比較する。 |
| I-3 | `test_batch_invalid_output_discards_every_record[terminal]` 等（`:7206`）。先頭の違反 OID に正常 message を注入しており、部分採用すると実違反が消える。単なる欠落の検査に留まっていない。 |
| I-4 | `test_batch_subprocess_counts_and_selected_order[False]` が重複 finding の消失で赤くする。ただし、この fixture では**受理集合差としては殺せない**。R-1参照。 |
| I-5 | `test_batch_invalid_output_discards_every_record[log-error/decode-error/os-error]`。空監査で続行すれば固定の違反1件・rc=1に反する。単に `{}` を返す変異でも辞書参照が例外となり赤いが、その場合は拒否→受理の証拠とは区別が必要。 |

## 反証できなかった点

- **S-1 の対応ずれ:** [checker:1223](/work/1/SFC/tanab/izanagi/.codex/worktrees/prov-batch/tools/check_ai_provenance.py:1223) が同じ Git record に `%H/%s/%B` を出し、`:1235` が同じ3フィールドを分解、`:1242` がその record の OID に格納する。`:2156` は監査対象自身の OID で参照する。要求列と結果列を位置で結合する処理はない。集合一致だけに依存した対応付けではない。
- **全廃 fallback:** 取得・decode 例外、終端／件数／OID 検証失敗はすべて `None`。途中の辞書は公開されず、全件が `:1955` の旧 `show` 経路へ戻る。取得辞書への `.get()` はない。空辞書は空要求だけで返り、空監査は取得前に終了する。
- **oracle の独立性:** `:2148` が `ancestry is None` の場合に一括取得を呼ばず、注入値も `None` になる。oracle テストは `%s/%B` 各4回・一括取得0回を固定している。
- **parser 無改変:** `_ai_agent_values` と `_isolated_parsed_trailers` は、HEAD版と現物の関数ソース文字列が完全一致した。
- **公開出力・例外順:** 新しい公開診断・rc 分岐はない。一括取得の例外を全廃 fallback に変換した後、従来の `pool.map` が入力順に例外を送出する。明示 LF は decode 前に付加され、message 自体に strip はない。
- **恒真性:** accept-all は固定の違反 findings／rc=1、reject-all は `[accepted]` の rc=0、一括取得の常時無効化は取得値比較と subprocess 数 assertion で赤くなる。
- **成長比例・揮発期待値:** 新設テストは固定規模の一時 Git repo を使用する。実 repo の HEAD・履歴件数・ファイル件数に比例する新設テスト、working tree hash・現在時刻・実測件数の焼き込みは見つからなかった。

## 総括

実装差分から、受理集合を動かす blocker は発見しなかった。  
OID 対応、全廃 fallback、oracle 分離、parser 無改変は静的検査で確認した。  
I-4 の赤は現状では重複 finding の差であり、受理集合差による kill と区別する必要がある。  
pytest・変異・全史比較は実行していない。独立した変更前コードとの比較は、親の受入検査として残る。