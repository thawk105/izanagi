## 総括

Y1 / Y2 の修正を指定2ファイルだけに実装しました。  
ただしテスト runner が2回とも `qstat` 障害で起動できなかったため、両項目とも「実装済み・未実走」の `partial` とします。  
構文解析、差分検査、変更範囲、結合文字不在の静的確認は完了しています。commit はしていません。

## Y1 / Y2 の対応表

| 項目 | 状態 | 対応 | 根拠 |
|---|---|---|---|
| Y1 | partial | `partial` 時に、任意位置の `campaigns` component、および復元済み campaign root の親との三方向関係を拒否。適用状態を report の boolean に追加。兄弟 directory の無書込み負例も追加。 | [p3_b4_material_report.py:782](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix3/orchestrator/campaign/p3_b4_material_report.py:782)、[p3_b4_material_report.py:1112](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix3/orchestrator/campaign/p3_b4_material_report.py:1112)、[test_p3_b4_material_report.py:278](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix3/orchestrator/tests/test_p3_b4_material_report.py:278) |
| Y2 | partial | `below` と symlink の出力名を分離。共有実体を触る各 node は前状態を検査し、`finally` で必ず清掃。清掃前の残留集合も assertion して zero-write 検査を維持。 | [test_p3_b4_material_report.py:599](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix3/orchestrator/tests/test_p3_b4_material_report.py:599)、[test_p3_b4_material_report.py:622](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix3/orchestrator/tests/test_p3_b4_material_report.py:622)、[test_p3_b4_material_report.py:671](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-fix3/orchestrator/tests/test_p3_b4_material_report.py:671) |

## 実走結果

コマンド:

```text
python3 tools/run_tests.py orchestrator/tests/test_p3_b4_material_report.py
```

- 初回: `rc=16`、test process 未起動、0 passed / 0 failed、0.07秒
- 許可された再試行: `rc=16`、test process 未起動、0 passed / 0 failed、0.04秒
- 原因: `qstat -Q preflight rc=1`
- 実走 nodeid: なし
- 静的確認: 2ファイルの AST parse 成功、`git diff --check` 成功、U+0300〜U+036F なし

## 順序依存が無いことの確認方法

逆順実走は再試行上限到達のため未実走です。静的には、問題だった `below` と symlink が異なる実体出力先を使い、さらに拒否 assertion が失敗しても `finally` が exact 3成果物を清掃します。清掃前の残留も検査するため、zero-write 期待値は弱めていません。

## 受理・拒否挙動の変化

- `partial` かつ path に `campaigns` component があれば拒否。
- `partial` かつ出力先が復元済み campaign root の親と一致・配下・祖先なら拒否。
- `complete` の既存三方向検査、symlink 拒否、それ以外の `partial` 出力は変更なし。
- 一般化した official-root admission は追加していません。

## 未完・未解決

- ファイル全走と逆順 node 走はインフラ障害により未実走です。
- コード上の未実装事項はありません。