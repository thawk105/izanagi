## 変更内容

変更と生成物はすべて `output/runs/silo-fix` 配下です。tracked file、repo の `patches/`、変異 patch は編集せず、commit も残していません。

| File | 内容 | SHA-256 |
|---|---|---|
| [run_ci_then_judge.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-fix-a/output/runs/silo-fix/scripts/run_ci_then_judge.sh) | 2 つの子 script を `bash` で起動 | `3a26d657c75934c5a2308b62e80b96ae5548c93082d5ab6d1341593e5a13e90c` |
| [launch_gate_liveness_v2.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-fix-a/output/runs/silo-fix/scripts/launch_gate_liveness_v2.py) | 対照の D2b 条件を違反件数の合計で判定し、有効な発生条件を observed に記録 | `9c2cf740dbb1646156c31918bbd10fff2b8aaa92b2c7a0fbbb9d51feffa053c5` |
| [inventory_silo_patches.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-fix-a/output/runs/silo-fix/scripts/inventory_silo_patches.py) | 重ね順の出典、stock define、前処理失敗の分類、任意の PIN 列、F→TIP 変化一覧を修正 | `3c060a6fb45eebf65cd75787a5f2c118d9b9ac092a9244c2f20ca64a6ac76b56` |
| [inventory.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-fix-a/output/runs/silo-fix/inventory-selfrun-f1/inventory.json) | 自己走の詳細 | `4a8c781da408ba6e4b61b2ba1e4706a2f9cb21b898c0128ffdc13c633e7584c9` |
| [inventory.md](/work/1/SFC/tanab/izanagi/.codex/worktrees/silo-fix-a/output/runs/silo-fix/inventory-selfrun-f1/inventory.md) | 自己走の表と変化一覧 | `e460759cf17b42fd492f071a804cf65780827b0a34f8be2adcc4f20c7e6804ba` |

## 所見ごとの対応

- **R01 closed:** 実行権限に依存しない `bash <script>` に変更。片方が失敗しても両方を走らせ、各 rc を保存・表示する流れは維持しました。
- **R02 closed:** 対照は D1 の 3 件が 0、かつ発生した D2b 条項の違反件数合計が 1 以上なら match。発生条件が両方 0 なら indeterminate。修正側の条件は維持しました。
- **R05 closed:** trigger 計装の出典を README の「骨格の上に重ねる」記述へ、misattr の出典を driver の実際の適用行へ変更しました。
- **R06 closed:** `_head_defines` で base commit の stock 定義を取得し、patch 適用後は同じ定義取得系の `_worktree_defines` で patch が追加した CMake 既定値を含めました。既存定義が変われば理由付きで E、取得不能も理由付きで E、前処理失敗は `preprocess-error` です。裸の変異マクロは追加していません。
- **5 closed:** 任意の `PIN=<oid>` は適用可否だけを表示し、A〜E の判定には使いません。
- **6 closed:** inert・適用・重なりの F→TIP 判定差を JSON と Markdown に別掲しました。

## 棚卸しの自己走

44 本を検査し、**A=39、C=2、D=3、E=0、preprocess-error=0** でした。F→TIP で判定が変わったのは `broken-silo-repeat-update-buffer.patch` と `broken-silo-stale-read-own-write.patch` です。D のうち `broken-silo-corrupt-write-payload.patch` と `broken-silo-published-version-mismatch.patch` は PIN に適用可能でした。

一時 TIP の実測 OID は `f8a3245b6e4d442825624656bbf563f1ce20d595`。終了後、ccbench は F `25898d00b9a6bbf09329ff8e8318c77d4f08b46e` の detached HEAD に戻り、worktree は元の修正 1 file の未 commit 状態です。一時 worktree は残っていません。

## 実走した command と rc

- `bash -n output/runs/silo-fix/scripts/run_ci_then_judge.sh` — rc=0
- `python3 -m py_compile output/runs/silo-fix/scripts/{inventory_silo_patches,launch_gate_liveness_v2}.py` — rc=0
- 手製辞書による `prereg('control', …)` 3 ケース — rc=0。`(i)=0,(ii)=5` は match、違反 0 で発生ありは mismatch、発生条件が両方 0 は indeterminate。
- 一時 commit を作成して実測 TIP OIDを取得後、`python3 output/runs/silo-fix/scripts/inventory_silo_patches.py --repo-ccbench "$R/ccbench" --repo-root "$PWD" --base "F=$F" --base "TIP=$TIP" --base "PIN=$PIN" --out-dir "$R/inventory-selfrun-f1"` — rc=0
- 一時 commit の解除、元の file blob hash 照合、HEAD・worktree 確認 — rc=0

## 未実走・残る懸念

計算ノードの CI・D297・trace job は実走していません。この段の確認は script の構文、prereg の指定ケース、棚卸しの自己走までです。

## 総括

依頼された 6 項目を R 配下で修正し、棚卸しの自己走と clone の復元まで完了しました。