## 変更内容

[launch_cicada_run_g.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-b/output/runs/md19-cicada-fix/scripts/launch_cicada_run_g.py) に `--job DIAG` を追加しました。既定は従来どおり `ALL` です。DIAG は3 build の source OID・patch SHA256・compile/flag binding を `result-DIAG.json` に記録し、D1 の交互実行と D2 の TRACE=0 実行を行う構成です。予測との比較値も記録し、最終的な合否は親が判断します。D3 の PROMO_Y・K・1反復目の raw trace は、DIAG で必須の `--keep-trace-dir` に残します。

[restore-promotion-dup-emplace.patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-b/output/runs/md19-cicada-fix/scripts/restore-promotion-dup-emplace.patch) は指定の1行置換だけです。編集は `R/scripts/` 配下のみで、commit はしていません。

## 実走した command と rc

- `python3 -m py_compile …/launch_cicada_run_g.py`: **rc=0**
- G の `transaction.hh` に対する `git apply --check …/restore-promotion-dup-emplace.patch`: **rc=0**
- `launch_cicada_run_g.py --job DIAG --keep-trace-dir /tmp/md19-diag-dry-b4/witness --dry-run`（G と G.bundle を指定）: **rc=0**。PROMO_Y、PROMO_DUP_Y の順次 patch 適用と、patch なしの PROMO_T0 を確認しました。
- DIAG の3 build の TRACE 値を確認する Python assertion: **rc=0**

## 未実走・残る懸念

3 build と benchmark は計算ノード部分のため**実装済み・未実走**です。verdict、異常終了、raw trace 保存の実行時結果はまだ確認していません。

## 総括

D1〜D3 の DIAG job を追加し、ログインノードで可能な構文・patch 適用確認を完了しました。