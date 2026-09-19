## 総括

実装・自己検査・実データ走査を完了しました。変更は次の新規4ファイルだけです。既存ファイルの編集、`git add`、commit は行っていません。

- [scan_tests.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/tinv-scanner/t_inv_scanner/scan_tests.py)
- [test_scan_tests.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/tinv-scanner/t_inv_scanner/test_scan_tests.py)
- [inventory.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/tinv-scanner/t_inv_scanner/out/inventory.json)
- [inventory.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/tinv-scanner/t_inv_scanner/out/inventory.md)

実在ファイルは **363件**でした（brief は391件）。除外30ファイル・67,920行を除き、対象は333ファイル・510,327行、**14,416関数・345,321関数行・21,882 nodeids・台帳15,587.593秒**です。台帳欠落949 nodeids は0秒として集計しています。

下表は「保護対象を含む／除く」。分類内は関数単位で重複排除し、分類間には重複があります。

|分類|候補関数|行数|nodeids|台帳秒|
|---|---:|---:|---:|---:|
|A|384 / 381|13,096 / 12,806|608 / 605|654.531 / 654.504|
|B|63 / 62|959 / 947|312 / 311|185.028 / 185.028|
|C|1 / 1|16 / 16|1 / 1|0.002 / 0.002|
|D|297 / 291|10,397 / 10,099|362 / 356|296.410 / 225.392|

保護対象は634関数・21,114行・918 nodeids・4,969.357秒。`errors` は0件、除外対象外の collect 未対応関数も0件です。別枠は always-skipped 0関数、unresolved 5,215件、parametrize 評価不能1,198行・133容器です。

実走した自己検査とCLI（双方終了コード0）：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -c 'from t_inv_scanner.test_scan_tests import test_scan; test_scan()'

PYTHONDONTWRITEBYTECODE=1 python3 t_inv_scanner/scan_tests.py \
  --repo-root /work/1/SFC/tanab/izanagi/.codex/worktrees/tinv-scanner \
  --collect-file /work/1/SFC/tanab/dev-wave-jobs/dev-wave-test-inventory-prune/collect.txt \
  --exclude-file /work/1/SFC/tanab/dev-wave-jobs/dev-wave-test-inventory-prune/excluded-suites.txt \
  --out-json /work/1/SFC/tanab/izanagi/.codex/worktrees/tinv-scanner/t_inv_scanner/out/inventory.json \
  --out-md /work/1/SFC/tanab/izanagi/.codex/worktrees/tinv-scanner/t_inv_scanner/out/inventory.md
```

限界：動的なパス・import、fixture/helper 経由、継承テスト、class/module の skip 指定などは取りこぼします。複数行のパス風文字列は unresolved に記録します。AST一致や撤回番号への参照だけでは削除可能と確定できません。

pytest・受入全走・変異検査・docs/provenance checker は未実走です。既存 caller・共有fixture・consumer への組み込み変更はありません。