## P1 凍結する bytes

**P1 は採用する。凍結対象は、式 v2 導入直前の v1 blob `f7a54445764025112317151106712bb9d97678ab` とする。ただし「旧3 WAL を生成した patch bytes」とは記述しない。**

実行した次のコマンドで履歴と blob を確認した。

```sh
git log --format='%h %ad %s' --date=short -- patches/silo-backoff-fixed.patch
git rev-parse 93c32cf38:patches/silo-backoff-fixed.patch
git rev-parse b97ee9153:patches/silo-backoff-fixed.patch
git rev-parse 30c66880b:patches/silo-backoff-fixed.patch
git rev-parse 4f7bb3c76:patches/silo-backoff-fixed.patch
git rev-parse 4dfd3785b^:patches/silo-backoff-fixed.patch
```

| 導入 commit・日付 | blob | 内容・位置付け |
|---|---|---|
| `93c32cf38`・2026-06-22 | `476a128266bb50489d7a7d4936f6cf21fd621727` | 静的 backoff 初版。旧 sweep 生成期の候補 |
| `b97ee9153`・2026-06-29 | `24c8373bf225faa0c15eacd6625258e3ba8ef764` | `BACKOFF_NOINLINE` を追加 |
| `30c66880b`・2026-06-30 | `90e83b5b8159074810b59d738a871fbdd81093e2` | EVOLVE-BLOCK マーカー・コメントを追加 |
| `4f7bb3c76`・2026-07-02 | `f7a54445764025112317151106712bb9d97678ab` | `BACKOFF_FIXED` 未供給時の `#error` を追加。v2 直前までこの版 |
| `4dfd3785b`・2026-08-26 | `06d272b…` | hole の式を v2 に変更 |
| `91a5bfca3`・2026-09-07 | `eb319d8fd856de0799b0134d24122ba8f031a438` | 現行 v3 |

`git diff 476a128 24c8373`、`git diff 24c8373 90e83b5`、`git diff 90e83b5 f7a5444` で上表の差分を確認した。v1 系4版の式はすべて次である。

```cpp
double now_backoff = static_cast<double>(BACKOFF_FIXED);
```

さらに `git diff f7a5444 06d272b` は、この式1行の変更だけだった。したがって、射影の `verbatim-ruling-package-A2.md` にある「合成枝の式が v1 から v2 へ変わった」、`verbatim-s6-reviewB-8pins.md` の v2 更新に対する旧版保存という文脈には、**差分の直接の前像である f7a5444** が最も合う。

一方、476a128 を採る合理性は「旧 sweep 生成期の patch を保存する」場合にある。しかし、それでは v2 直前の骨格に存在した noinline・マーカー・供給漏れ拒否を含まない。今回の保存対象には f7a5444 を選び、476a128 との違いを README に明記する。残る2版は中間段階であり、今回それらを選ぶ根拠はない。

`git show <blob> | sha256sum` の実測値は次のとおり。

| blob | SHA-256 |
|---|---|
| `476a128…` | `bc59c9a8f43be8ab901045cac6537b0ac5cfe9777b85ddd9d6520c47a3c739ea` |
| `24c8373…` | `36f40b029441366bc9bec24580219c7d26b42e3bad8d4a6da7fd3c445ebf1a3f` |
| `90e83b5…` | `f275bd3ce3822707f9f35f0ea870c75945fec1efc4c47dbc34968b7efa1224fe` |
| **`f7a5444…`** | **`35237d314df708c6a6cb6fece0a8a59cd199bb57337013f95f6ed50ea2a2f911`** |

旧成果物から読み取れる範囲は区別する。

- 旧 lock は `ccbench_commit="6656e93"`、workload・grid・trial 等を記録する。patch blob/SHA は記録していない。例：`output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e/campaign.lock:1`。
- WAL の先頭は variant・genome・時刻・`env_tag="linux-baremetal"` を記録する。これだけから patch bytes やホスト名 cygnus は確定できない。各旧 WAL の `:1` を確認した。
- 凍結3 file の8 object は **WAL の path+SHA と driver の path+SHA** を記録する。patch の pin ではない。根拠：`measurement_freeze.json:166,438,710`、`known_axes_freeze.json:147,373,599`、`holdout_freeze.json:152,419`。
- 親 brief F2 の「旧3 WAL は2026-06-22生成」は訂正が必要。read-heavy の先頭 timestamp は `1782624851.233902`。`date -u -d @1782624851.233902` は **2026-06-28 05:34:11 UTC**、同 WAL の `git log` は `2c59dc3d3 2026-06-28` の追加を示した。476a128 はその日にも該当する版である。

適用前像については、次の読取りで `6656e93` と `511c953` の双方が一致した。

```sh
git -C external/ccbench rev-parse \
  6656e93:cmake/Options.cmake 511c953:cmake/Options.cmake \
  6656e93:include/backoff.hh 511c953:include/backoff.hh
```

結果は Options が `b9a3c740…`、backoff が `3db8c08f…`。f7a5444 の patch header の前像と一致する。ただし、これは適用・build・再現実験の実行結果ではない。

## P2 別名 path と reader 棚卸し

**P2 は `patches/silo-backoff-fixed-v1.patch` を採用する。** 同名は `rg` 検索で見つからなかった。既存名との対応と式の版が読み取れ、直下 `.patch` の既存検査にも入る。

`patches/silo-backoff-v1.patch` も下記の検査結果は同じだが、元ファイル名との対応が弱い。`.diff` やサブディレクトリは直下 `glob("*.patch")` から外れるため、今回選ぶ理由がない。提案名で赤を予測していないので、検査回避の命名変更は不要である。

検索は `patches/`、`.patch`、`glob`、`rglob`、`iterdir`、`listdir`、`walk` に加え、`excluded_paths`、ledger scope、保護対象、実装面分類、docs 検査を追った。以下は確認できた読取り・分類経路である。

| reader／分類器 | 判定式・根拠 | 新 file 追加時の予測 |
|---|---|---|
| patch の define 在庫 | `test_ccbench_spawn_sites.py:632` の `patch_paths = sorted(patch_dir.glob("*.patch"))`。`:661,679` の `sources.setdefault(macro, set()).add(patch_rel)` | **集計対象に入るが緑維持**。既存の `BACKOFF_FIXED`、`BACKOFF_NOINLINE` の供給元集合に新 path が増える |
| define 登録簿との照合 | 同 `:2676` の `assert frozenset(patch_sources) == frozenset(condition_meaning_gate.DEFINE_SPECS)`、`:2686` の `if spec.patch_rel not in patch_sources[macro]` | 新 macro key は増えず、既存の登録 path も集合に残る。供給元集合の完全一致は要求していない |
| define×build sink 検査 | 同 `:2693,2815,2854,2870,2967,2994`。渡す値は `frozenset(patch_sources)` | macro key 集合が不変なので、cross-product と件数は不変 |
| 裸 `IZANAGI_` token 在庫 | `test_p3_s4_loop.py:7842` の直下 glob、`:7847` の `r"\bIZANAGI_[A-Z0-9_]+\b"`、`:7871` の `if macros and relative not in registered:` | **集計対象に入るが緑維持**。f7a5444 に該当 token はない |
| ledger 読取り | `silo_ladder_rung1_contract.py:511` の scope 比較、`:517` の `if len(entries) != 1:` | **無反応**。ディレクトリ在庫ではなく登録 entry を読む。新 entry を足すと逆に契約違反 |
| projection policy | `projection_guard.py:200` の `document["scope"] != "registered-entries-only"`、`:206` 以降の entry 走査、`:398,405` の token/path 照合 | **無反応**。`patches/ledger.json:38` の除外集合は rung1 関連。提案 path・保存 bytes にその字面はない |
| Write/Edit hook | `guard_write.py:58` の WAL/lock/build-cache 判定、`:315` の s8b-freeze、`:324` の external subtree 判定、`:334` の `return True, ""` | 通常の新 regular file は**保護対象に分類されない**。既存凍結物への変更許可を意味しない |
| Bash hook | `guard_bash.py:81` の `_LEAF_RE`、`:87` の `_TREE_LITERAL_RE`、`:2540,2560` の保護判定 | 新 path は WAL・campaign・external・hooks 等の保護集合に該当しない。hook 発火の実測はしていない |
| provenance | `check_ai_provenance.py:78` の suffix 集合に `.patch`, `.diff`。`:1589` の `if normalized.endswith(IMPLEMENTATION_SUFFIXES): return True` | **実装面に入る**。Codex author を記録すればこの変更由来の違反なし。AI 関与 commit にそれがなければ `:1631` の違反 |
| docs 検査 | `check_docs.py:128` の `LIVING_DOCS`、`:169` の docs runbook glob、`:6694` の走査 | 新 `.patch` は本文検査対象外。`patches/README.md` も当該列挙にない。内容・SHA の正しさを docs checker が保証するとは言えない |
| docs 内 path 存在検査 | `check_docs.py:1120` の `PATH_REF`、`:6754` の走査 | 対象文書から新 path を参照した場合、存在することで条件を満たす。patch 内容は検査しない |
| condition gate | `condition_meaning_gate.py:76,141` の `patch_rel="patches/silo-backoff-fixed.patch"` | **無反応**。新 file は registry に追加されず、現行 path を維持 |
| source identity | `source_digest.py:85` の `EVOLVE_BLOCK_SOURCES`、`:97` の `ALLOWLIST` | **無反応**。対象は CCBench 内の固定ソース集合。repo の patch 在庫追加では適用後ソースが変わらない |
| 固定 path の実行 consumer | `backoff_sweep.py:435`、`backoff_repro.py:68`、`backoff_profile.py:98`、`p3_s4_loop.py:128`、`backoff_extended_sweep.py:119`、`b10_backoff_shape_sweep.py:93` | **無反応**。配線を変えない限り現行 patch を読む |
| source pin・probe | `paper_story_a1_source.py:16`、`paper_story_a1_source.v1.json:6`、`paper_story_a2_certification.py:691`、`t316_sandbox_backend_probe.py:2356` の `_BOUND_RELATIVE_PATHS` | **無反応**。固定リストに新 path はない |

shell/probe 側も `paper_story_a1_paired.sh:78,454,988`、`submit_b10_backoff_shape.sh:114`、`t1683_rr5_cost_probe.py:238`、`t316_sandbox_backend_probe.pbs:55` は現行名の明示参照だった。新 file を自動適用する経路は見つからなかった。

Git の変更 path を列挙する一般的なツールには当然新 file が現れる。これは patch を新たに実験入力として選ぶこととは異なる。特に provenance 分類は上表のとおり実装面として扱う。

## P3 旧 consumer の再走経路

**P3 の「配線し直さない」は採用する。ただし「別名保存により旧 consumer が自動的に v1 を使う」とは説明しない。**

共通の根拠は次の4点である。

1. `ident.py:203` は `if ADMISSION_POLICY_SEARCH_KEY not in cfg.search_config:` で identity 生成を拒否する。
2. `ident.py:96` の `bind_admission_policy` は `search_config={**cfg.search_config, ADMISSION_POLICY_SEARCH_KEY: expected}` を返す。
3. `ident.py:227` は正準 preimage の SHA-256 先頭8桁を用い、`:232` は slug・search tag と組み合わせる。出力先は `layout.py:248` の `os.path.join(root, "campaigns", cid)`。
4. 短縮 hash が衝突しても、`ident.py:141` の `if actual != expected:` と `:373` の `if cur != decoded.identity_preimage:` が旧 lock を拒否する。`ident.py:484` はこの照合を WAL repair より先に行う。`loop.py:553` も recovery 前にこの関所を通る。

したがって、**「preimage が違うから8桁 hash も必ず違う」ではなく、実測した ID 相違と完全な lock 照合を分けて根拠とする。**

| 旧 consumer | 現行経路と旧 pin への追記判定 |
|---|---|
| `backoff_sweep.py` | `:264` の config、`:419` の admission bind、`:435` の patch 指定。親 probe は3 workload とも旧 ID と不一致。現行実行はさらに site 設定を `:413` で反映する。旧 lock に admission がないため、旧3 WAL への通常 resume は拒否される |
| `backoff_repro.py` | `:102` は `backoff-repro-silo-{tag}` / `repro` / `p2-backoff-repro`。`:159` で admission bind。現行 pin は `:49` の `dff0f1e`、旧 balanced lock は `6656e93` で admission なし。旧 repro WAL にも通常 resume できない。`:180` の結果読取りも束縛済み cfg から layout を導出する |
| `backoff_profile.py` | `:98,368` で現行 patch を適用。campaign WAL writer ではなく、`:1099` の `env_scope_dir(env_tag)/profile` 配下へ JSON/MD を出力する。旧3 sweep WAL・repro WAL に追記する経路ではない |
| `backoff_overthrottle.py` | 旧版は patch 適用済みソースを前提とする診断 build consumer。現行は `:417` で template を適用し、`:390` で参照 campaign の binding を得るが、出力は `:392` の `reports/b10-backoff-overthrottle-{tag}.jsonl` と manifest。WAL 追記ではない。「campaign 配下の全 file が不変」とまで一般化しない |
| `p3_s4_loop.py` | `:128,1891,1903` で template を適用。`:1508` の slug は `p3-s4-loop`、search tag は `s4-autonomous`、`:1517` で admission bind。旧 sweep/repro と namespace が異なる |
| `s1_direct_comparison.py` の backoff cell | 旧 `4dfd3785b^:…:659` で `loop_axis.TEMPLATE_PATCH` を使用。現行 `:910,965` も同じ。identity は `:520` の `s1-direct-{role}` / `direct-comparison`、trial は `s1-direct-v2`、`:534` で admission bind。旧 sweep/repro WAL の writer ではない |

履歴検索は `git grep … 4dfd3785b^ -- orchestrator/campaign tools` で実施した。注意点として、当時の sweep/repro/profile/overthrottle は現在と異なり、コード内で現行 patch 名を直接指定せず、適用済みソースを消費する経路を含んでいた。path literal の検索だけで消費者なしとは判定していない。

関連する別 patch の consumer も区別した。

- `p3_kickoff.py:64,65` は `variant-noop-else-copy.patch` と `variant-backoff-static50.patch`。
- `p3_s4_red.py:80` は `variant-backoff-red-1e9.patch`。
- `p3_autonomous_workload_trial.py:1957` は trigger template。

これらは frozen copy の自動消費者ではない。kickoff/red の identity もそれぞれ別 slug、admission bind あり（`p3_kickoff.py:111,145`、`p3_s4_red.py:126,200`）。

holdout の repro 参照も整理が必要である。`holdout_freeze.json:95–105` に相当する内容は `positive_control.hit_paths` の検索記録であり、旧 sweep WAL の `sources` にある8件の SHA pin と同じ形式ではない。それでも旧 repro WAL を変更してよいことにはならない。本 plan は変更を提案しない。

D1098 の「別名で凍結すれば旧消費者はそのまま動き」は、今回の実装で自動的に保証される挙動ではない。**今回実現するのは、歴史的 v1 を明示参照できる固定 path の保存**である。最新の依頼「対象は既存 v1 の保存に限定する」と brief I3 が consumer 配線変更を除外しているため、再配線は行わない。

## P4 README

**P4 は修正して採用する。警告を残すだけでなく、その適用範囲を限定する。**

`patches/README.md:216–219` の「同じ campaign に別 ID が積まれる」は、今回確認した現行 sweep/repro の通常経路の説明としては正確でない。旧 lock に admission policy がなく、再走先の identity が分離され、lock 照合もあるためである。親 probe の3 IDだけで全 consumer の安全を主張するのも避ける。

編集位置は次の2箇所に限定する。

- `:216–219`：v1/v2 で source identity が異なる事実と、旧 campaign への resume 禁止を維持し、現行経路の説明を追加する。
- `:220`、`BACKOFF_NOINLINE` 節の直前：別名凍結の小節を追加する。

警告部分の文面骨子：

> v1 と v2 では同じ静的値でも preprocess 後ソースと variant identity が異なる。旧凍結 campaign に異なる式の結果を混在させてはならない。現行の backoff_sweep / backoff_repro は build-admission policy を campaign identity に束縛し、policy のない旧 lock を resume 時に拒否する。「同じ campaign に別 ID が積まれる」は、これらの現行通常経路で起きるという意味ではない。

凍結節の文面骨子：

> `silo-backoff-fixed-v1.patch` は、2026-08-26 の式 v2 導入直前の v1 patch を bytes のまま保存したもの。導入 commit `4f7bb3c76325b7f97a9efda071b92a84732d375e`、取得元 `4dfd3785b^:patches/silo-backoff-fixed.patch`、blob と SHA-256 は上記の完全値。  
> 静的式、noinline、EVOLVE-BLOCK、定義漏れ拒否を含む。旧 sweep 生成期の `476a128…` と patch bytes は同一ではない。用途は歴史的 v1 ソースの参照・明示的な再適用であり、旧実験の完全再現や現行 consumer の v1 使用を保証しない。  
> 現行 patch、consumer の参照先、凍結成果物、WAL、ledger は変更しない。D1098 / D1281 に基づく保存である。

README に旧3 WAL の生成日を一括で「6月22日」と書かない。数値 ID の実測詳細は insight に置き、README は長期的な由来と用途を中心にする。

## 実装子への指示案

Codex author 子の変更対象は **新 patch 1 file のみ**。README は brief の分担どおり親が編集する。子は commit しない。

書込み可能な author 環境で、親 worktree を cwd とし、対象が未存在であることを確認してから次を実行する。

```sh
git cat-file -t f7a54445764025112317151106712bb9d97678ab
test ! -e patches/silo-backoff-fixed-v1.patch
test ! -L patches/silo-backoff-fixed-v1.patch
```

`blob` と未存在を確認した後、既存 file を上書きしない設定で bytes を取り出す。

```sh
(
  set -o noclobber
  git show f7a54445764025112317151106712bb9d97678ab \
    > patches/silo-backoff-fixed-v1.patch
)
```

エディタでの貼付け、改行正規化、コメント追加、patch の再生成はしない。作成コマンドが失敗した場合、残った途中 file を完成品として扱わない。

検証：

```sh
sha256sum patches/silo-backoff-fixed-v1.patch
git hash-object patches/silo-backoff-fixed-v1.patch
git show f7a54445764025112317151106712bb9d97678ab |
  cmp - patches/silo-backoff-fixed-v1.patch
```

期待値は SHA-256 `35237d31…a2a2f911`、Git blob `f7a54445764025112317151106712bb9d97678ab`、`cmp` は rc=0。完全な SHA-256 は P1 に記載した値と比較する。`git hash-object` に `-w` は付けない。

親は統合後、変更 path が新 patch・README・所定の記録に限定されることと、I1/I2 の不変を確認する。本調査時の実測値は次のとおり。

| 保護対象 | SHA-256 |
|---|---|
| 現行 patch | `a5e0710c3f76744755b58ec66024c277daba00e49ce3cbf3d6d263cd7228580a` |
| measurement freeze | `203de36b9749b9021d1b944d26fad4c8ed617a0fdd1438435cb67e90a0efcf7a` |
| known_axes freeze | `354f4b875a3c8106169252afc71cee1fd08df83b0f3024c72bda0a791e11f516` |
| holdout freeze | `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688` |
| balanced sweep WAL | `8ac3f47e55274fada20e6518eea9cbb0e822170eeda1b424df99e76e11fd789c` |
| write-heavy sweep WAL | `9c179331a7171969ac6f4ed2b1d09e4afbf52378cfbac7bd133696a6589fe926` |
| read-heavy sweep WAL | `c74d5837a4facd071704a515f905d1d638463878850661cf217b96cd694774dc` |

実装 provenance は `docs/ai-provenance.md:44` の契約に従い、親の commit に Codex `role=author` を記録する。子が commit を作る必要はない。

## 既存テストへの影響予測

**以下は静的予測であり、テストは実行していない。既存期待値の変更は不要と予測する。**

実在 patch 在庫を読む helper の呼出しを `rg -n '_patch_added_define_interfaces'` で追った結果、該当する node は次の7件だった。先頭 path はすべて `orchestrator/tests/test_ccbench_spawn_sites.py::`。

| node | 予測根拠 |
|---|---|
| `test_patch_define_inventory_matches_condition_gate_registry` | `:2676` の macro key 集合一致、`:2679` の non-TU 集合一致、`:2686` の既存 path 包含をすべて維持 |
| `test_define_sink_cross_product_has_no_unreviewed_ungated_member` | `:2696` の `assert failures == []`。入力 macro 集合不変 |
| `test_define_sink_cross_product_rejects_synthetic_member_without_gate` | `:2818` の期待 failure list 不変。既存 macro の集合を渡すだけ |
| `test_define_sink_cross_product_rejects_gate_with_only_one_arm` | `:2856` の期待 `("IZANAGI_BREAK_PERMUTATION", "reachable")` 不変 |
| `test_define_sink_cross_product_does_not_defer_unlisted_member` | `:2872` の `BACKOFF_FIXED` failure 包含条件不変 |
| `test_define_sink_cross_product_classifies_t2155_production_sinks_exactly` | `:2979` 以降の `Counter({"covered": 4, "proven-unreachable": 34})`、`Counter({"covered": 38})` 不変 |
| `test_define_sink_cross_product_t2520_certify_entry_removal` | `:3007` の `assert len(expected_macros) == 14`、後続の deferred 14 / unreachable 24 不変 |

追加でもう1件：

```text
orchestrator/tests/test_p3_s4_loop.py::test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted
```

`test_p3_s4_loop.py:7842` で新 file を読むが、`:7871` の `if macros and relative not in registered:` の前提となる `macros` が空なので、`:7878` の `assert not unregistered` は維持される。

projection 同期テスト `test_p3_s4_loop.py:7738` は ledger と rung patch を読むだけで、新 file に反応しない。現行 patch を明示参照するテスト群も bytes・配線不変のため、この追加から結果変更は予測しない。

受入は親が brief 指定の `tools/dev_wave_wait.py acceptance` で行う。上記 node 群を重点確認し、赤が出た場合は期待値を変更せず原因を調べる。新 path の pin テスト追加は I5 により行わない。

## 変異の事前登録候補

**既存 suite が保存 bytes の一致を保証しないことを、事前登録に明記する。**

変異対象は隔離した実装後コピーだけとし、現行 patch・凍結物・WAL は変異させない。

| 候補 | 既存テストでの期待 | 根拠・限定 |
|---|---|---|
| M1：新 patch の既存の追加コメント1行へ `IZANAGI_FREEZE_PROBE` を追記。行数・条件指令・CMake 定義は変えない | **KILLED 予測**。期待 node 完全集合は `{orchestrator/tests/test_p3_s4_loop.py::test_all_naked_izanagi_macro_patches_are_registered_or_allowlisted}` | `:7847` の全文 token regex にだけ新規該当。define 在庫は追加コメントを条件指令として扱わず、macro mapping も不変（`test_ccbench_spawn_sites.py:650–682`）。赤理由は未登録 `IZANAGI_` token |
| M2：新 patch の式を `static_cast<double>(BACKOFF_FIXED) + 1.0` に変更 | **SURVIVED 予測** | 在庫 macro 集合不変、`IZANAGI_` token なし。新 path を適用して式を検証する既存 consumer/test がない |
| M3：新 file 全体を `476a128…` の bytes に置換 | **SURVIVED 予測** | 現行 patch が両 macro を引き続き供給するため union の macro key は不変。保存版そのものの pin テストがない |
| M4：新 file を削除 | **SURVIVED 予測** | 直下 glob は必須 filename 集合を要求しない。既存 consumer は現行名を読む。README も当該 docs lint 列挙外 |
| M5：README の新 SHA-256 記載だけを1文字変更 | **SURVIVED 予測** | 確認した checker に README 記載 SHA と新 file を照合する経路がない |

M1 の単一拒否層という主張は、**既存テスト suite に対してのみ**成立する。P1 の bytes 比較まで同じ変異評価へ含めれば M1〜M3 は SHA/blob 比較でも拒否され、M4 は存在確認でも拒否される。その評価集合では M1 を「拒否層が1つ」と登録してはならない。

したがって、事前登録には「既存 suite の期待 node」と「保存作業の bytes 一致確認」を別々に記載する。全受入層を通じて単一拒否を要求する場合、M1 は条件未達として扱う。これを解消するための新 gate・pin test は追加しない（brief I5）。

## scope 外

射影 brief の確定裁定と不変条件により、次は実装しない。

- **8 WAL SHA pin の張替え、campaign identity 移行、旧 WAL/lock/freeze の再生成**：D1098・D1281、I2。
- **現行 `silo-backoff-fixed.patch` の変更、v3 の改名**：I1。今回の成果物は別名追加。
- **consumer を v1 へ再配線、v1/v3 の自動選択機構**：I3、最新依頼「既存 v1 の保存に限定する」。
- **既存テストの期待値・allowlist の変更**：I3。提案名・bytes では必要なしと予測。
- **grammar、verifier、condition gate、certified 受理集合の変更**：I4、規律2。
- **新 pin test、gate、ledger entry、一般化した patch 台帳**：I5。既存 ledger は registered entries のみ、entry 数1の契約である。
- **追加の歴史版 patch 保存**：新 file 1本という scope を超える。476a128 等は由来説明に留める。
- **external への適用、build、性能測定、旧実験の再走**：この plan の read-only 制約と保存限定 scope。
- **T-2647 等の他 wave への修正**：親の overlap probe は編集面の重複なしと報告。今回触る必要がない。

## 未確認事項

- テスト、受入、build、patch 適用、hook の live 発火は一切実行していない。緑／赤は上記コードに基づく予測である。
- f7a5444 と旧生成期 patch の実行結果・preprocess 出力・binary の一致は実証していない。式と前像の一致を、実験全体の再現性へ拡張しない。
- 旧 WAL が実際に使用した patch bytes は WAL/lock に記録されていない。476a128 は履歴上の生成期候補であり、WAL 自身による証明ではない。
- cygnus というホスト帰属は親 brief の記述として読んだ。今回確認した WAL 先頭の `linux-baremetal` だけではホストを確定できない。
- repro の現行 campaign ID の具体的な8桁値は再計算していない。旧 lock の admission 欠落、pin 相違、完全 preimage 照合に基づいて resume 拒否を判定した。
- 全 repo の任意動的コード・外部利用者まで含む reader 不在の形式的証明はしていない。P2 は実施した path/key 検索と呼出し追跡の棚卸しである。
- 親 overlap probe は提供時点の結果であり、その後の他 worktree の変更は再確認していない。
- M1 の期待 node 集合は静的予測。実際の mutation run が別 node も落とした場合は、その結果を記録し、単一理由成立と報告しない。

## 総括

**新規 `patches/silo-backoff-fixed-v1.patch` に f7a5444 の bytes を保存し、README に由来・用途・限界を書くプランを推奨する。consumer、既存期待値、gate、ledger、凍結物は変更しない。**

親案への修正点は、①保存版を旧 WAL 生成時 bytes と同一視しない、②read-heavy WAL の生成期は6月28日、③現行 sweep/repro の旧 campaign resume 警告は admission/lock 照合に即して限定する、の3点である。

確認した既存検査は追加後も緑を維持すると予測するが、新 file の誤版・式改変を検出する pin はない。完了判定の中心は **元 blob との bytes 一致、保護対象の不変、親の受入実行結果** とする。