## 総括

修正・自己検査・実データ再走査を完了しました。変更は `t_inv_scanner/` 内の次の4ファイルのみです。

- [scan_tests.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/tinv-scanner/t_inv_scanner/scan_tests.py)
- [test_scan_tests.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/tinv-scanner/t_inv_scanner/test_scan_tests.py)
- [inventory.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/tinv-scanner/t_inv_scanner/out/inventory.json)
- [inventory.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/tinv-scanner/t_inv_scanner/out/inventory.md)

各要求への対応：

1. 合成 fixture 指標による不在 literal の抑制を実装。`suppressed` に理由・証拠を保持。module 不在証拠は抑制対象外です。
2. fingerprint に decorator を追加。本文だけの一致は集計外の `notes` に移動。
3. `production_targets` と、保護対象を除く A/B/C の対象別件数を追加。
4. Markdown に B1 全メンバー、B2 重複行、C 全件、D pin先別上位30件を追加。
5. `unresolved` の kind 別件数を追加。

新旧集計です。各セルは「旧 → 新」、保護対象を含みます。

|分類|関数|行数|nodeids|台帳秒|
|---|---:|---:|---:|---:|
|A|384 → 114|13,096 → 3,045|608 → 155|654.531 → 49.991|
|B|63 → 36|959 → 431|312 → 148|185.028 → 125.970|
|C|1 → 1|16 → 16|1 → 1|0.002 → 0.002|
|D|297 → 297|10,397 → 10,397|362 → 362|296.410 → 296.410|

保護対象を除いた集計：

|分類|関数|行数|nodeids|台帳秒|
|---|---:|---:|---:|---:|
|A|381 → 112|12,806 → 2,961|605 → 153|654.504 → 49.964|
|B|62 → 35|947 → 419|311 → 147|185.028 → 125.970|
|C|1 → 1|16 → 16|1 → 1|0.002 → 0.002|
|D|291 → 291|10,099 → 10,099|356 → 356|225.392 → 225.392|

全体は変更なく、333対象ファイル・14,416関数・345,321関数行・21,882 nodeids・15,587.593秒。除外は30ファイル・67,920行、台帳欠落949 nodeids、errors・collect未対応はともに0件です。

新設の抑制集計は **273関数・510証拠**（path 389、flag 90、heading 31）。未解決5,215件の内訳は flag-source 3,880、非path文字列4、parametrize容器133、row 1,198です。

以下を実走し、双方終了コード0でした。自己検査は各分類と新設の抑制・decorator差異・通常参照を残す対照例を含みます。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -c 'from t_inv_scanner.test_scan_tests import test_scan; test_scan()'

PYTHONDONTWRITEBYTECODE=1 python3 t_inv_scanner/scan_tests.py \
  --repo-root /work/1/SFC/tanab/izanagi/.codex/worktrees/tinv-scanner \
  --collect-file /work/1/SFC/tanab/dev-wave-jobs/dev-wave-test-inventory-prune/collect.txt \
  --exclude-file /work/1/SFC/tanab/dev-wave-jobs/dev-wave-test-inventory-prune/excluded-suites.txt \
  --out-json /work/1/SFC/tanab/izanagi/.codex/worktrees/tinv-scanner/t_inv_scanner/out/inventory.json \
  --out-md /work/1/SFC/tanab/izanagi/.codex/worktrees/tinv-scanner/t_inv_scanner/out/inventory.md
```

限界：合成指標による抑制は真の不在も落とし得ます。動的参照・helper経由・名前の再束縛は追跡せず、AST一致も削除可能性を保証しません。所有外 caller・共有fixture・consumer への組込み変更はありません。

pytest・受入全走・変異検査・docs/provenance checker は未実走です。`git add`／`git commit`、所有外編集、repo外書込みは行っていません。