## 所見

consumer/meta-test の指定を確認するため、射影外では `p3_b4_floor_artifact_issuer.py`、その test、受入時間台帳生成器、関連 meta-test に限って追加参照した。

1. 外部 consumer の synthetic summary が `source_commit` を `loaded_head` として残している

   - **主張:** driver fixture は `source_commit=C="b"*40`、`loaded_head=H="d"*40` に分離されたが、`_synthetic_source` は summary の `loaded_head` を旧値 `"b"*40` のまま生成する。consumer は spec を `H` で load しながら両者を比較せず、誤った値を authority artifact へ転記する。テスト失敗ではなく silent false-positive である。
   - **file:line:** `orchestrator/tests/test_floor_pair_driver.py:26-28,338-352`、`orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:50-66,104-110`。consumer は `orchestrator/campaign/p3_b4_floor_artifact_issuer.py:847-870` で spec を load した後も summary 値をそのまま採り、同:906-914 で成果物へ転記する。共有 helper の consumer は test file 内の 15 call site (`:257`、`:282`、`:301`、`:315`、`:334`、`:375`、`:395`、`:423`、`:436`、`:485`、`:504`、`:556`、`:577`、`:622`、`:651`)。
   - **これが real なら成果物がどう変わるか:** `test_authority_issue_is_create_only_exact_and_loadable` 等が作る authority artifact の `source_summary.loaded_head` は、実際に spec を検証した `H="d"*40` ではなく親 `C="b"*40` になる。
   - **提案する対処:** fixture の `loaded_head` を `driver_tests.HEAD` にし、既存 consumer test で `summary["loaded_head"] == parsed_spec.loaded_head` を直接確認する。production への一般 gate 追加は不要。
   - **real / refuted の自己判定:** **real**。

2. 追加された受入所要時間は、この段の実走証拠と結び付いていない

   - **主張:** 台帳は JUnit から時間を生成する契約だが、この差分は `test_floor_pair_driver.py` の209 nodeidへ具体的な秒数を追加している一方、射影された実装報告では collection を含む全試行が test 開始前の `rc=16` で、consumer/meta-test も未実走である。提供資料内に、追加値を生成した成功 JUnit はない。
   - **file:line:** `orchestrator/tests/acceptance_duration_ledger.json:3` から同`:211`、同`:19754`。生成契約は `tools/update_acceptance_duration_ledger.py:2,235-270`。未実走報告は `author.md:24-38`。
   - **これが real なら成果物がどう変わるか:** production の floor 成果物は変わらないが、受入スケジューラが未立証の時間値を実測値として使用し、台帳自体が検証済み受入証拠に見える。
   - **提案する対処:** test が実行可能になった時点で `tools/run_tests.py` が生成した成功 JUnit から台帳を再生成し、現在値との一致を確認する。
   - **real / refuted の自己判定:** **real（機能欠陥ではなく受入証拠の欠陥）**。

## 発行手順の書き下し

以下で `C` はコード・固定入力を含む source commit、`H` は spec だけを追加する freeze commit、`S` は spec の repository-relative path とする。

1. `C` を作る。

   production code、calibration、build receipts、fresh checkout で必要な binary、全 output 親 directory を再構成する tracked sentinel（例: `out/.gitkeep`）を commit する。その後:

   ```bash
   C=$(git rev-parse HEAD)
   git status --short
   ```

   落ちる条件:

   - output 親を再構成する tracked file がないと、fresh checkout で `floor_pair_driver.py:524` の「parent が存在しない」になる。
   - binary が再構成されない、または hash が違うと同`:1173-1179`。
   - calibration/build receipt が未追跡、欠落、宣言 hash・blob と不一致なら同`:651-673`。

2. `provenance.source_commit=C` とした spec `S` を作る。

   exact schema/key、参照 path/hash、output path を確定し、期待 hashを計算する。

   ```bash
   EXPECTED=$(sha256sum "$S" | cut -d' ' -f1)
   ```

   落ちる条件:

   - `source_commit` が40桁 lowercase hexでなければ `:703-705`。
   - schema/key/type/cross-reference/output path が不正なら `:1280-1313`。
   - `EXPECTED` が実 bytes と違えば `:1267-1273`。

3. `S` だけを追加した唯一親 commit `H` を作る。

   ```bash
   git add -- "$S"
   git diff --cached --name-only -- "$S"
   git commit -m "freeze floor-pair spec"
   H=$(git rev-parse HEAD)
   git show -s --format=%P "$H"
   git diff-tree --no-commit-id --name-only -r -z --no-renames "$C" "$H"
   ```

   親出力は `C` だけ、changed path の NUL 列は `S` だけでなければならない。

   落ちる条件:

   - merge、root、または `source_commit` と異なる親なら `:1322-1325`。
   - spec 以外の変更、変更なし、rename の第二 path があれば `:1326-1331`。
   - `S` が commit blob と作業 tree で違えば `:1274-1278`。

4. `H` の fresh checkout を作る。

   ```bash
   git worktree add --detach /path/to/floor-freeze-checkout "$H"
   ```

   落ちる条件:

   - `out/` 等が `C` から再構成されなければ step 1 の parent 検査。
   - spec・calibration・receipt・binary が checkout 後に変更されていれば bytes/hash検査。
   - checkout の HEAD が `H` でなければ lineage/blob 検査が別 commit を対象にして拒否する。

5. checkout 自身から load する。

   ```bash
   cd /path/to/floor-freeze-checkout
   python3 -m orchestrator.campaign.floor_pair_driver \
     --repo-root . \
     --spec "$S" \
     --expected-sha256 "$EXPECTED" \
     --validate-only
   ```

   成功時は `source_commit=C`、`loaded_head=H` の spec と plan が得られる。

   落ちる条件:

   - HEAD 解決・Git raw出力不正は `:558-648`。
   - tracked blob、hash、calibration admission 不一致は `:651-673,1159-1231,1263-1278`。
   - load 後、window 実行前に HEAD が動けば `:2268-2273`。
   - window header の `loaded_head` / `runtime_head` が `H` でなければ finalizer が `:2733-2761` で拒否する。

## 破れなかった箇所

producer 内の意味は次のとおり一貫していた。

| 面 | `source_commit` | `loaded_head` / `runtime_head` | file:line |
|---|---|---|---|
| loader | freeze commit の唯一親 `C` | 冒頭で一度解決した `H` | `floor_pair_driver.py:1234-1249,1322-1348` |
| `run_window` | 比較対象にしない | 現在 HEAD が `H` と一致必須 | 同`:2268-2287` |
| finalizer | header に期待しない | 両 field とも `H` | 同`:2733-2741` |
| summary | spec 経由で保持 | `loaded_head=H` | 同`:3094-3100` |

- spec・calibration・receipt の全 blob query は解決済み `H` を使用しており、symbolic HEAD への逆戻りはなかった (`:538-555,651-673,1274`)。
- 実 Git 3 test は `_install_git` を呼ばず、保存した元の `subprocess.run` を使う。monkeypatch は calibration verifier のみである (`test_floor_pair_driver.py:29,391-400,495-553`)。
- positive test は `out/.gitkeep` を親 commit に含め、detached fresh worktree で存在を確認している (`:403-417,495-512`)。
- production の process site は実際に5件 (`floor_pair_driver.py:540,560,583,616,1662`)。追加2件は inventory の `test_ccbench_spawn_sites.py:115,117` と一致した。AST inventory の observed/expected 差分も双方空だった。
- module 名による consumer grep では `test_floor_pair_driver.py` と `test_p3_b4_floor_artifact_issuer.py` の2本だけだった。前者の直接 assertion/status 更新に未修正参照は見つからなかった。
- 新設 test file はない。既存 `test_floor_pair_driver.py` には自走 harness (`:3315-3316`) があり、台帳には同 file の209 nodeidが登録され、`nodeid_count=19750` と実 entry 数も一致した。
- proof-limit 文言は loader の実保証と一致する。changed path exact 検査が spec 以外の tree 同値を保証し、OID 同値や実行中 module bytes は保証していない (`floor_pair_driver.py:22,86,1322-1331,3117-3120`)。

## 総括

spec-only child `H` を作って fresh checkout から load する中核経路は成立する。  
producer 内の `C` / `H` 意味、spawn inventory、実 Git fixture、proof-limit は整合している。  
残る実欠陥は外部 consumer の silent な `loaded_head=C` fixture と、実走に結び付かない時間台帳である。  
pytest の成功実走は確認できていないため、このレビューから緑とは報告しない。