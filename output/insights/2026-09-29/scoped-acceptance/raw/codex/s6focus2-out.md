## 対応表

判定は commit `88fa8f1f1` の静的検査による。

| 対象 | 判定 | 根拠 |
|---|---|---|
| 前回 partial：r1#2、MS5 の単一理由性 | partial | dir 鍵の層を丸ごと外す裁定には沿うが、祖先 path 鍵だけの欠落を独立に検出する例はない。 |
| 前回 partial：r1#3、MS6 の lock 内再導出 | partial | 偽装した選択を拒否する例はある。同じ検証を lock 前にも行うため、lock 内だけを外す変異の検出は示さない。 |
| 前回 partial：r2#1、汎用名の過剰除外 | partial | `README.md` の偶然一致は避けられる。入れ物を読む参照の見逃しは残る。 |
| 前回 partial：r2#2、固定集合の大きさ | partial | 集合は維持。所要比較は今回の静的検査では判定できない。 |
| 前回 partial：r2#3、合成 repo 構築費用 | partial | 構築は維持。全受入への時間寄与は未判定。 |
| 前回 partial：wiring probe の赤 | closed | 親資料は未 commit docs を原因とし、焦点走 2 の緑を記録している。fix2 の変更対象でもない。 |
| 前回 partial：実在 land の分類と残る見逃し | partial | fix2 後は **4/10** が縮小可。見逃しの反例は下記のとおり残る。 |
| 前回の新所見：入れ物 reader | partial | 一覧外の完全一致文字列は検出するが、入れ物の下位 path や分割文字列は検出しない。 |
| fix2 対応 1：insight の深さ 3 の鍵 | closed | `2026-01-01_slug` 型の祖先を鍵に加え、分割参照の例もある。ただし純粋な日付 dir の参照は対象外。 |
| fix2 対応 2：点検済み 7 reader と一覧外検出 | partial | 7 path の列挙は一致。一覧外でも `"docs/spool/worklog"` などは検出しない。 |
| fix2 対応 3：選択 S5 | partial | `docs/spool` が連続する test は選ぶ。`"docs" / "spool"` と組み立てる test は選ばない。 |

根拠は [分類・選択器](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/scoped_acceptance.py:123)、[分類器テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/orchestrator/tests/test_scoped_acceptance.py:228)、[land テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/orchestrator/tests/test_scoped_acceptance_land.py:117)。

## 新たな所見

**縮小受入で門入力を見逃す構成可能な反例が残る。** `docs/spool/worklog/unique-fragment.md` を追加し、production reader が `"docs/spool/worklog"` を列挙する場合、鍵は full path と basename だけで、入れ物検出も引用符の直前に `worklog` が続くため一致しない。実際、[既存の正例](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/orchestrator/tests/test_scoped_acceptance.py:202)はこの形を適格と期待する。S5 は連続した `docs/spool` を持つ test を選ぶが、`"docs" / "spool" / "worklog"` と組み立てる consumer test は漏れる。fold と直接 gate が検査する性質以外の consumer 固有の意味検査には穴となる。

insight でも、純粋な日付 dir `output/insights/2026-01-01` を列挙して配下の `README.md` を読む reader は、当該 dir と汎用 basename が鍵から外れ、入れ物検出の完全一致文字列にも当たらない。対応する test に完全な path や単独の引用形 `"insights"` がなければ選択から漏れる。[鍵と入れ物判定](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/scoped_acceptance.py:123)から導ける反例であり、既存の特定 reader による実害を確認したものではない。

## 検算

[親の fix2 分類原データ](/work/1/SFC/tanab/tmp/scoped-acceptance-2026-09-29/probe/classify-fix2.txt)は **True 4 件、False 6 件**。したがって「4/10」は正しいが、「False 5 件」は fix1 の数である。True 行の選択数は **14、14、19、14 file** で、「14〜19 file」も正しい。

False 6 件のうち 3 件は `docs/archive`、1 件は `docs/archive` と `docs/failures.md`、1 件は許可外 `.log` と production 参照を含むため、全受入は規則どおり。残る 1 件は `tools/insights_date_layout.py` の `container-reader` 判定である。当時の file は `output/insights/` 配下を列挙・照合しており、保守的に全受入へ倒す理由は妥当。ただし一回限りの移行道具なので、継続する正しさの門かどうかまではこの判定から言えない。

現行 tree の該当する入れ物文字列は [裁定](/work/1/SFC/tanab/tmp/scoped-acceptance-2026-09-29/stage4-ruling.md)に挙がる **7 file** と一致した。うち `check_docs.py` と `spool_fold.py` は production candidate の走査対象から元々除外される。

`d26ee8605..88fa8f1f1` の [land 差分](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-scoped-acceptance/tools/dev_wave_land.py:904)では、`_verify_forward_main_runner_blob` は元の **3 引数**で、v5 の二つの呼び出しも 3 引数のまま。scoped の blob 比較は別関数に分岐し、v5 の exact field 検査と共通検証を緩める変更は見つからなかった。

## 総括

fix2 は深さ 3 の実在 reader の見逃しを塞いだ。一方、**下位の入れ物 path と分割された path を読む production reader、および対応 test を同時に見逃す入力が残る**。静的検査のみ行い、テストは実行していない。