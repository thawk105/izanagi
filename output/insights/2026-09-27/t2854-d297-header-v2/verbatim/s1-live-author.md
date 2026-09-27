## 実装の要点

指定の [liveness.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-live/output/runs/t2854-hv2/live/liveness.py) を 200 行で作成しました。

- [17–69 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-live/output/runs/t2854-hv2/live/liveness.py:17): JSON の逐次保存、25 分制限、compile argv の整理、`-MG` を使わない依存列挙を実装しました。
- [70–123 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-live/output/runs/t2854-hv2/live/liveness.py:70): TRACE ごとの変更 header、完全展開と include 活性の比較、bundle からの source 展開と third-party hydrate を記録します。
- [124–167 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-live/output/runs/t2854-hv2/live/liveness.py:124): 3 構成 × old/new の configure、masstree 生成物、依存列挙、TRACE 実効値、compile database と前処理の比較、および段ごとの秒数を記録します。
- [168–200 行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-live/output/runs/t2854-hv2/live/liveness.py:168): 必須 CLI、bnode 判定、構成ごとの例外記録、終了コードを実装しました。

## 未確定・懸念

計算ノードでは未実行です。依存列挙は `os.cpu_count()` 件を同時実行し、前処理比較は最大 8 件です。完全展開の出力はメモリに保持します。root の正規化はパス文字列の置換なので、実行結果で差分を確認してください。

## 総括

指定された AST 構文検査は通りました。`liveness.json` の実測結果は、親による bnode 実行後に得られます。