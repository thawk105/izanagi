## 所見

### RB1

- **主張:** allowlist は現 Pegasus の Git 2.34.1/ext4 相当の出力だけを固定しており、Git が正当に生成する `core.ignorecase` や `core.symlinks`、template 由来 key を誤拒否する。
- **根拠:** `tools/codex_reasoning_ab.py:1349-1362,1905-1920`。`git-config(5)` は `git init` / `git clone` が filesystem probe により両 key を設定すると明記する一方、`test_codex_reasoning_ab.py:2955-3003` は現在の key 集合との完全一致しか試していない。`git init` は `init.templateDir` 内の非 dot file をコピーするため、template の `config` も任意 key を導入できる。
- **深刻度:** must-fix
- **影響:** 同じ commit と canonical checkout bytes でも、filesystem・Git version・system template の違いだけで snapshot 受理集合が縮み、過去 snapshot の replay が `RC_SNAPSHOT` になる。

### RB2

- **主張:** source 用 allowlist は builder transport key だけを許すため、内容同一性に影響しない開発者 local config まで正当な source CCBench の拒否条件にしている。
- **根拠:** `tools/codex_reasoning_ab.py:715-743,1358-1362`。例えば `user.name`、`user.email` や安全な `submodule.<name>.update=checkout` は拒否される。後者は通常の `git submodule init` が `.gitmodules` からコピーしうる key である。
- **深刻度:** must-fix
- **影響:** source の commit、index、worktree bytes が同一でも、過去 wave や開発者が残した無害な config だけで `build-snapshot` の受理集合が縮む。

### RB3

- **主張:** config preflight の早期 `raise` は、`verify_snapshot` が複数の独立理由をまとめて返す既存挙動を壊す。
- **根拠:** `tools/codex_reasoning_ab.py:2060-2069` は config 理由が一件でもあれば即時送出し、後続の HEAD・branch・dirty・numstat・file・closure 理由収集 `:2085-2158` に到達しない。誤った `expected["head"]` と forbidden local config を併置すれば、HEAD mismatch が消える。
- **深刻度:** must-fix
- **影響:** 受理集合自体は変わらないが、CLI JSON、supervisor failure、replay 診断に残る `failure_reasons` 集合と順序が変わり、複合破損の参照可能性が失われる。

### RB4

- **主張:** `...preserves_canonical_oracle_bytes` は恒真ではないが、変更前 producer との bytes 不変を証明していない。
- **根拠:** `test_codex_reasoning_ab.py:2447-2472` は同じ変更後実装を、identity helper を無効化した状態と有効化した状態で比較するだけである。oracle schema、inventory 出力、manifest 構築が同じ差分で変わっても両側に共通して入り、テストは通る。hash 二本の比較は canonical bytes equality に包含される。
- **深刻度:** must-fix
- **影響:** `snapshot_manifest_sha256`、`submodule_manifest_sha256`、`manifest_sha256` が変更前から drift しても検出できず、凍結済み schedule の replay 参照が失敗しうる。

実 repo 経路については所見なし。fixture の skip 条件は historical sessions 不在だけである (`test_codex_reasoning_ab.py:350-384`)。`_derive_snapshot_from_base` → `_finish_snapshot_case` → `verify_snapshot` → `_git_closure_reasons` → identity helper が必ず通る (`tools/codex_reasoning_ab.py:1988,1944,2133-2144,1845`)。初回走では未初期化 Shirakami が実際に setup error になり、recursive init 後の同じ焦点走が `603 passed / 21 skipped` になっている (`focus1.log:197,372,547`、`focus2.log:24`)。したがって緑は builder と新 gate を通った緑である。

meta-test の更新漏れも見つからなかった。新設 41 test function はすべて固定 `tmp_path` synthetic で、`benchmark_snapshots` の新 consumer はない。既存 real-repo 17 node の台帳は `test_real_repo_serialization.py:82-98` と `conftest.py:227-244` で一致し、growth hold 一覧にも新規追加が必要な node はない。

## 偽拒否リスク

実 builder が書く key の棚卸しは次のとおり。

- `git init`: 通常は `core.repositoryformatversion`、`core.filemode`、`core.bare`、`core.logallrefupdates`。filesystem により `core.ignorecase`、`core.symlinks` も生成する。`init.templateDir` があれば追加 key は任意。
- `index-pack` / `update-ref` / `git apply`: 通常は local config を書かない。
- `checkout -B`: この明示 commit 起点では通常 branch config を書かない。`init.defaultBranch` は直前の unborn HEAD 名だけを変え、ここでは `-B` に上書きされる。
- submodule 初期化: 親に `submodule.<name>.url|active`、子に core 5 key、`remote.<name>.url|fetch`、`branch.<name>.remote|merge`。filesystem probe key はここにも追加されうる。
- seal: remote・branch upstream・submodule section は現 Git では除去されるが、`core.ignorecase` や `core.symlinks`、template 由来 key は残る。

現物確認では Git は 2.34.1、system/global の `init.defaultBranch` と `init.templateDir` は未設定だった。live source の三層はいずれも現在の source allowlist 内である。

- CCBench: core 5、remote 2、branch 2、Shirakami の `url|active`
- Shirakami: core 5、remote 2、branch 2、googletest の `url|active`
- googletest: core 5、remote 2、branch 2

親 repo 自身には `user.*` と `extensions.worktreeconfig` があるが、source root は `:738-742` の検査対象外なので今回の builder は拒否しない。

## 費用

### RB5

- **主張:** 一 campaign 当たりの全 file hash 回数と preflight subprocess 数が、親記録の単純な「各段一回」より大きい。
- **根拠:** 10 trial では snapshot finish 2 回 (`:1944`)、5 pair の supervisor precheck 5 回 (`:2931`)、各 trial pre/post 20 回 (`:2666,2827`)、final replay 10 回 (`:5340-5346`) で合計 37 verify。replay cache は一意な oracle path を key にするため trial 間で共有されない。
- **深刻度:** nit
- **影響:** oracle 値・受理集合は変わらないが、timeout 内に完了できる run 数が減りうる。

実三層は合計 1,438 tracked file、11,111,504 bytes。37 verify では約 53,206 file read、411,125,648 bytes、CCBench の 0.124 秒を entry/bytes 比例すると約 16〜22 秒である。さらに preflight は `:2061` と identity helper 内 `:1645` で二重実行され、root と三 submodule なら合計 592 preflight Git subprocess、その半分の296回が重複する。

新設テスト自体は固定サイズ synthetic repo に比例し、commit history や output artifact 量には比例しない。私は pytest を実走しておらず、上記の緑は親ログの静的確認である。

## 総括

must-fix は3系統、証拠不足が1系統ある。  
最大の偽拒否は、Git 自身が filesystem や template に応じて生成する local config を列挙できていない点である。  
現 Pegasus の三層 source は通るが、無害な開発者 config と異環境 snapshot は通る保証がない。  
焦点走は実 builder と新 gate を実際に通っており、skip に隠れた緑ではない。  
oracle bytes は実装上不変に見えるが、現テストは変更前 bytes との独立比較へ差し替える必要がある。