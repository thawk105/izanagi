## 前巡所見の対応表

| 所見 | 判定 | v1 → fix 後の根拠 |
|---|---|---|
| 1. build 照合失敗時の記録消失 | **closed** | 記録を照合前に `builds` へ入れ、失敗と取得済みの Cache・flags・hash を残す。[v1:188–228](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.v1.py:188) → [現行:188–265](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:188) |
| 2. 10 field の C 行を数えない | **closed** | 7／10 field を受理し、どちらも field 6 を読む。[v1:261](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.v1.py:261) → [現行:303–307](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:303) |
| 3. run 起動例外を完了扱いする | **closed** | `run_error` を記録して停止し、verifier・分類を呼ばず rc=1 とする。[v1:407–414](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.v1.py:407) → [現行:441–444](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:441)、[現行:471–473](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:471) |
| 4. 出力先準備失敗時の JSON・rc | **partial** | 準備は `try` 内、両 JSON の書込みも個別になった。一方、空でない出力先の既存 JSON を上書きし、書込み失敗を rc に反映しない。[v1:320](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.v1.py:320) → [現行:373–377](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:373)、[現行:475–482](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:475) |
| 5. C 行形式の報告 | **closed** | 実装が両形式に対応し、[fix 報告:3](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/codex/s6-fix1.md:3) でも訂正された。[現行:303–307](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:303) |

## 所見

1. **must-fix — 空でない出力先の既存成果物を上書きする。** [現行:375–376](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:375) で空でないことを検出しても、`finally` の [現行:477–479](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:477) が既存の `result.json`・`meta.json` を `"w"` で開く。**修正案:** 空判定に失敗した場合は既存ファイルへ書かず、stderr と rc=2 で終了する。新規の空ディレクトリを準備できた後の失敗だけ、そのディレクトリに JSON を残す。

2. **must-fix — JSON 保存に失敗しても rc=0 を返しうる。** [現行:461](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:461) で完了 rc を設定した後、[現行:477–482](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:477) は `OSError` を表示するだけで rc を維持する。`result.json` または `meta.json` が欠けても成功と報告し、[実装依頼:35](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/codex/prompt-author.md:35) の出力契約を満たさない。**修正案:** 両方の保存を試みたうえで、いずれかが失敗したら非0の rc と `meta["launcher_rc"]` を一致させる。保存済み JSON も失敗状態を示すよう更新する。

**固定条件の照合:** 分類 A〜D は差分なし。[現行:119–176](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:119)。build argv と照合値、W(16)／W(17)・120秒、R1→R4、同じ `applied` 文脈での gate と2 build も変更されていない。[現行:21–24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:21)、[現行:180–187](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:180)、[現行:431–439](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-sort-nonswo/launch_sort_nonswo.py:431)。prereg の条件変更は見つからなかった。

## 総括

**NO-GO。** 前巡所見は 1・2・3・5 が closed、4 が partial。新たに、既存成果物の上書きと JSON 保存失敗時の成功 rc という2件の must-fix がある。結論は静的検査によるもので、計算ノードでの実走結果は含まない。