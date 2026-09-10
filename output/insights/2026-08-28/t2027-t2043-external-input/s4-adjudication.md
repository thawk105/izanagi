# [T-2027]/[T-2043] 段 4 裁定

## real / refuted

- real: v1 manifest の FetchContent 31件は消滅する staging absolute path を保持し、receipt 発行時の strict validation を止める。
- real: non-sort cell の `BuildResult.fetchcontent_base_dir` は空だが、対象 production floor は sort_best を含み、run 前に検証済み shared masstree root を既に保持する。
- real: new manifest は producer origin root と使用時 current canonical root を別 context として扱う必要がある。
- real: root component の symlink を解決後 `lstat` だけで検査するのは不十分で、未解決 component の no-follow 検査が要る。
- refuted: 旧 completion の `fetchcontent_dependency.source_root_sha256` を migration authority にする案。対象2件に field 自体が無い。
- refuted: 952615 と 952631 が同一 cache entry という brief の表現。full build digest はそれぞれ `dbbcb195...` と `87aa2e6a...`。
- 裁定: T-2027 と T-2043 は1件へ束ねず別IDのまま扱う。ただし D1192 の同じ最小修理が双方の共通 validator defect を解消する。

## 採否

- 採用: nested manifest `s8b-compiler-input/v2`。entry は exact `{root,path,sha256}`、path は root-relative POSIX。
- 採用: root は今回の実測に限り `snapshot`、`fetchcontent-masstree`、`filesystem`。masstree 以外の FetchContent root は暗黙分類せず停止する。
- 採用: policy は `snapshot-and-external-hashes/v1` のまま、manifest schema を descriptor-bound cache preimage に追加する。
- 採用: v2 request は旧 v1 completion を選ばず fresh buildする。これは invalid entry の cache miss 降格ではなく、schema が異なる新しい identity である。
- 採用: v1 completion/receipt bytes は不変。旧 identity の validation は absolute path の実在・hash を従来どおり要求し、欠落時に停止する。
- 採用: fresh は CMake metadata から取得した実効 masstree rootを producer origin とし、現 run の検証済み shared rootへ再束縛して全 hashを確認する。
- 採用: hit と receipt は同じ run-scoped shared rootを current canonical baseとして渡す。sort_best の D424 oracle/build same-tree 追加制約は維持する。
- 不採用: suffix/basenameによる v1 migration、strict=False、missing input許容、cache entry削除、fresh fallback、absolute baseのidentity投入。
- scope外: masstree以外のFetchContent root一般化。独立実測なしで族へ広げない。

## plan v2

1. `s8b_compiler_input.py`: v1 structural compatibilityを残し、v2 root-tagged entry、origin分類、current-base strict再束縛、root canonicality、symlink component拒否を実装する。
2. `buildcache.py`: manifest schemaをpreimageへpinし、fresh collectorへorigin/current root、hit validatorへcurrent rootを渡す。selected v2 validation失敗からbuildへfallbackしない。
3. `s8b_floor_campaign.py`: 既存 `dependency_binding.source_root` を全cellのcompiler-input current rootとしてbuild/receiptへ渡す。non-sortをoracle authorityへ昇格させない。
4. `s8b_binary_admission.py`: issuerはcurrent rootでlive再検証し、portable validatorはv1/v2のexact structureとdigestだけを検証する。
5. 焦点テストはfresh v2、base A→B hit、receipt再検証、旧v1 fail-closed、missing/hash/symlink/root偽装、fallback不在を固定する。

## gate署名と通る正例

- 禁止: root tagだけで別treeの同名fileへ付け替えない。current baseの同じrelative pathが実在し、non-symlink regularで、recorded hashと一致するときだけ通す。
- 正例: base Aの`masstree-src/include/x.hh`をrecorded hash Hでv2 completionへ保存し、次runの検証済みbase Bの同relative pathが同じHならcache hitとreceipt発行を通す。
- 負例: base Bのfile欠落、hash差、leaf/ancestor symlink、filesystem tagによるsnapshot/FetchContent偽装はすべて停止する。

## job再投入条件

- 焦点検査、関連全走、事前登録変異の全kill、docs/codex/provenance検査が緑になった後だけ行う。
- 再投入前にT-1908/T-2048の重複差分を再確認する。実装面に重複が出たら停止する。
