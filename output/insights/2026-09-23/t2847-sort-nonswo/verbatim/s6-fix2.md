[起動器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:371) の焦点レビュー所見 2 件を修正しました。所有ファイル以外は変更せず、commit もしていません。**実装済み・計算ノードでは未実走**です。

- 空でない、または準備できない out-dir では、その dir に JSON を書かず、理由を stderr に出して rc=2 で終了します。空判定を通過した後の失敗では、両 JSON の保存を試みます。
- `finally` で `result.json` と `meta.json` を個別に保存します。片方でも失敗すれば、元の rc が 0 の場合は 1 にし、保存できた JSON に `json_save_failures` を残すよう試みます。

自己検査は **33 ケース・34 アサーションすべて成功**しました。内訳は分類 A〜D の既存 27 例、前巡の 4 分岐、今回の 2 ケースです。今回の検査では、空でない out-dir の既存 2 ファイルが不変で rc=2、`meta.json` 保存失敗の注入で rc=1、残った `result.json` に失敗記録があることを確認しました。`py_compile`、`git diff --check`、`check_codex_agents.py`、`check_docs.py` も成功しました。

prereg の分類 A〜D、W(16)／W(17)、120 秒、patch、build argv は変更していません。`s5` の private 関数の呼び方と、`SORT_VARIANT` gate の静的根拠も前巡から変更していません。依存物準備、gate、build、R1〜R4、verifier の実走結果は未確認です。

## 総括

| 焦点所見 | 状態 | 変更行 |
|---|---|---|
| 空でない out-dir の既存成果物を上書きする | **closed** | [空判定と保存許可](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:371)、[finally](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:478) |
| JSON 保存失敗でも rc=0 を返しうる | **closed** | [個別保存・rc・失敗記録](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2847sn-launcher/t2847_launch/launch_sort_nonswo.py:479) |