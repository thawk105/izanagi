# [T-785] legacy buildcache.cache_key の既定 toolchain 省略による偽 hit — 再現と手当て

- authority: none
- default_effect: no-state-change

可変状態の正本ではない。可変状態の正本は `docs/worklog.md` 末尾と現行 phase doc である。
本書は wave `dev-wave-t785-legacy-cache-key` の一次資料を凍結したものである。

- 観測日時: 2026-09-16 17:30〜19:05 JST (変異 matrix 完了 19:03 JST)
- 機体: `pegasus02` (login node)。焦点走と変異 matrix は計算ノード (dispatch)
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t785-legacy-cache-key`
- base: `0c292eff6f39d797afac7481b89c94de43c07386`、実装 commit: `6022f70d7a87cc7518990c9a1c7c1de5f7b9c2ba`
- job dir (probe 本体・JSON・子の生成物の原本): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t785-legacy-cache-key/`

## 結論

**legacy `buildcache.cache_key` は、要求 toolchain が可変の `DEFAULT_CC`/`DEFAULT_CXX` と等しいとき
toolchain を key から省いていた。既定を替えると、前処理出力が一致する compiler 組では新既定の要求が
旧既定で作った entry と同じ key に当たる。この偽 hit を production `build()` を通して実測で再現し、
省略条件を歴史的既定の literal 組 (`"gcc-13"`, `"g++-13"`) へ切り離す 1 行の修正で、同条件が miss に
なることを確認した。**

到達範囲 (段 6 レビュー B の書き換え案を採る):

> Pegasus login node 上で、実 ccbench checkout の source evidence と stock admission を用い、cmake 実行を
> 極小 C++ ELF の生成に置き換えた production legacy `build()` probe を実施した。`silo|BACK_OFF=1`・
> `trace=False` について、既定を gcc-12/g++-12 から gcc/g++ へ替え、receipt が一致する条件で、修正前は
> 旧 compiler 製 ELF への偽 hit、修正後は key 分離と新 compiler による再生成を確認した。

**確認していないこと:** 各 CLI 全体の実走、`trace=True`、生成物 (非 stock) admission、実 CCBench binary の
build・実行・性能値・certified 選択への影響。要求名が同じまま実体・版が替わる場合 (PATH・symlink 更新) は
legacy key の対象外のまま (build_v2 は toolchain manifest で保護済み)。s1/s2/s3/s5 と非 Pegasus の
`between_run_floor` は evidence 側に独立の `"g++-13"` 既定を持ち、本 wave は触っていない。

## 1. 欠陥の機序 (現物)

- `orchestrator/campaign/buildcache.py:622` `DEFAULT_CC, DEFAULT_CXX = "gcc-13", "g++-13"` (`9cde78124`、2026-07-02 以来不変)。
- 修正前の `cache_key` (`:639`) は `tc = "" if (cc, cxx) == (DEFAULT_CC, DEFAULT_CXX) else ...` と
  **呼出時の module global** と比較していた。`build()` (`:3410-3411`) の引数既定 `cc=DEFAULT_CC, cxx=DEFAULT_CXX`
  は定義時束縛なので、既定変更後に新 process で起動した caller は新既定を要求し、その要求は key から省かれる。
- stock admission の receipt (`build_admission.py:615-675`) は nonce も toolchain 名も含まないが、
  `source_bytes_sha256` (要求 compiler の `-E -P -nostdinc` 出力の digest、`source_digest.py:2408-2410`) を含む。
  したがって衝突は**前処理出力が compiler 間で byte 一致するときだけ**起きる。「既定変更で必ず偽 hit」ではない。
- hit 経路 (`buildcache.py:3474-3512`) は sidecar・source evidence・trace diff・trace symbol を検査するが
  toolchain は見ないので、key 衝突はそのまま hit になる。

## 2. legacy `build()` の production caller (段 3 で訂正済みの表)

| caller | compiler の渡し方 |
|---|---|
| `s1_verify_extime_calibration.py:390` | 省略 (定義時既定)。generator receipt 付きの生成物 build であり stock control ではない |
| `s2_verify_calibration.py:354-355` | 省略 |
| `s3_lock_coverage.py:258` | 省略 |
| `s5_permutation_coverage.py:293` | 省略 |
| `pipeline.py:2002` (legacy 分岐) | **省略**。compiler を載せた `common` は `:2010` 以降の build_v2 分岐だけが使う |
| `backoff_profile.py:857` | `runtime.cc/cxx` (site 解決) を明示 |
| `between_run_floor.py:316-324` | Pegasus 分岐だけ site 解決を明示、それ以外は省略 |
| `pegasus_floor_scoping.py:214-218` | site 解決組を明示 |

`compilers_for_current_site()` (`buildcache.py:1861-1865`) は compute で `gcc/g++`、それ以外は module の `DEFAULT_*` を返す。
`tools/pegasus/probes/t2187_adaptive_const_probe.py:3925,4346` は `cache_key` を直接呼ぶが、対応する build と同じ
明示 cc/cxx を渡す。修正はいずれの caller も変更しない。

## 3. 再現 (修正前、base `0c292eff6`)

probe = job dir の `t785_legacy_cache_probe.py` (Codex `role=author` 作、15,588 bytes、
sha256 `5bc493ec6dcdcb706d0f6db19a8c86b1f1bed2370ca23b15eba453ca92d5a251`。**repo へは入れない**)。
差し替えるのは cmake を起動する `buildcache._run` だけで、configure argv が要求した compiler で
`#include <cstdio>` / `int main(){std::puts(__VERSION__);}` を実コンパイルし `<build dir>/cc/silo/ycsb_silo.exe` へ置く。
evidence・admission・sidecar・source 再検証・trace diff・trace symbol 検査・copy/publish は production のまま。

evidence 走査 (変異なし): `g++-12` (12.3.0) と `g++` (11.4.0、実体 `x86_64-linux-gnu-g++-11`) で
`source_bytes_sha256` `6454d9f3…` と receipt `c6a616c2…` が一致。`clang++` (14.0.0) は不一致 (`5c4a51fc…`)。
`g++` と `g++-11` は同一実体なので別 compiler と数えない。`g++-9` は `BUILD_FLAGS` の `-std=c++20` を受けない。

親の手順 (`DW-O19`): `DEFAULT_*` の 1 行を Edit で実編集 → `git diff --numstat` が `1 1` の 1 行 → probe →
`git checkout --` → blob hash が HEAD と一致 → porcelain 空、を相ごとに繰り返した。

| 相 | 既定 | key | cached | `_run` 呼出 | binary sha256 | ELF `.comment` |
|---|---|---|---|---|---|---|
| seed | gcc-12/g++-12 | `silo_fed9a86c14_t0` | false | configure, build | `8ca3a7c8…` | GCC 12.3.0 |
| hit | gcc/g++ | `silo_fed9a86c14_t0` | **true** | **0 回** | `8ca3a7c8…` (同一) | **GCC 12.3.0** (configure argv は `g++`) |

`reproduced_false_hit=true` (`probe/before-hit-gcc.json`)。receipt は両相で一致。

## 4. 修正 (commit `6022f70d7`)

`orchestrator/campaign/buildcache.py:641`: `tc = "" if (cc, cxx) == ("gcc-13", "g++-13") else f"|cc={cc}|cxx={cxx}"`
と docstring 3 行。現行既定はこの literal 組と等しいので、現行の全入力で key は 1 bit も変わらない
(golden `_T816_GOLDEN_CK0` 不変)。`build()`・`build_v2`・`_v2_identity`・hit 時の検査・caller は変更しない。

回帰テスト `orchestrator/tests/test_campaign.py::test_cache_key_default_toolchain_change_does_not_alias_historical_key`
(1 本、`test_cache_key_separates_compiler_request_name` の直後)。module の `DEFAULT_*` を差し替え、cc/cxx を明示して
(a) 歴史キー H、(b) 新既定要求が H と異なり互いにも異なる、(c) 既定変更中でも `gcc-13/g++-13` は H、を検査する。

## 5. 修正後の確認 (commit `6022f70d7`、同じ compiler 組・新しい cache root)

| 相 | 既定 | key | cached | 実コンパイル | binary sha256 | ELF `.comment` |
|---|---|---|---|---|---|---|
| seed | gcc-12/g++-12 | `silo_6c154d405d_t0` | false | g++-12 | `8ca3a7c8…` | GCC 12.3.0 |
| hit 相 | gcc/g++ | `silo_f368efad6c_t0` | **false** | **g++ (11.4.0)** | `68b4d6c9…` | **GCC 11.4.0** |

`fix_demonstrated=true` (`probe/after-hit-gcc.json`)。receipt は修正前と同じ `c6a616c2…`。

## 6. 検査 (親が実走した値だけ)

| 検査 | 範囲 | 結果 |
|---|---|---|
| 焦点走 | `test_campaign.py` の 4 node (新規 1 + 既存 cache_key 2 + golden 1) | 4 passed (計算ノード `1600.nqsv`) |
| provenance | `check_ai_provenance.py` message-file / full | rc=0 / 新規違反なし |
| 変異 matrix | §7 (計算ノード dispatch、`repo_head=6022f70d7`) | baseline PASSED・**3/3 KILLED**・SURVIVED 0・MISMATCH 0・期待 node 完全一致 |
| 受入全走 | `dev_wave_wait.py acceptance --lease-optional` | **本 commit の時点で未実施。** 実走後に worklog エントリへ結果を書く (本書は amend しない) |

## 7. 変異事前登録と matrix

段 4 で登録 (`s4-ruling.md` §7、erratum で完全集合を 4 node 走行に限定)。対象は修正後 `buildcache.py:641` の `tc` 行 (一意)。

| ID | 変異 | 期待 KILLED (4 node 内の完全集合) |
|---|---|---|
| M1 | 比較先を `(DEFAULT_CC, DEFAULT_CXX)` へ戻す | 新規テスト |
| M2 | 常に `|cc=..|cxx=..` を付ける | golden テスト |
| M3 | 常に `""` | compiler 名分離テスト、新規テスト |

段 6 レビュー A の指摘: M2 は 4 node 外の `test_p3_s4_loop_sort.py::test_sort_contract_none_preserves_preexisting_identities`
も破る (静的判定)。完全集合は 4 node 走行に限った記録であり、全 suite の集合ではない。

本走 (`mutation-final-out.json`、`repo_head=6022f70d7`、4 run): baseline PASSED、M1 KILLED (失敗 node = 新規テストのみ)、
M2 KILLED (golden テストのみ)、M3 KILLED (compiler 名分離テスト + 新規テスト)。summary は
`KILLED 3 / MISMATCH 0 / SURVIVED 0 / TIMEOUT 0 / matching 3 / registered 3`。等価変異 (SURVIVED 正例) は
登録していない — 3 変異とも恒等写像ではなく、レビュー B が不要と判定した。

## 8. 段 6 レビューの裁定

- RA-1 (SHOULD、レンズ A): 新規テストは cc/cxx を同時に変えるため `cxx == "g++-13"` だけの片側比較へ退行しても緑
  (cc だけの片側は既存テストが捕まえる)。**real・不採用** — 成果物影響は仮想 (レビュー自身が実測なしと明記) で、
  依頼の「仮想リスク向けの検査追加は scope 外」と `DW-G05` に従う。次の一手に残す。
- RB-1 (NIT、レンズ B): 記録の文言を実測範囲に限定し、brief 初版の誤記 (pipeline の compiler 伝播、s1 の stock control、
  between_run_floor の全分岐 site 解決、研究停止の広い表現) を転記しない。**採用** (本書 §結論・§2)。
- MUST 0 件。fix 子は投入していない。

## 9. 収録物

- `verbatim/s1-brief.md`、`verbatim/s2-plan.md`、`verbatim/s3-consult-{sol,luna}.md`、`verbatim/s4-ruling.md`、
  `verbatim/s5-author-{probe,fix}.md`、`verbatim/s6-review-{a,b}.md`
- `probe/evidence-{g++-12,g++,clang++}.json`、`probe/before-{seed-gcc12,hit-gcc}.json`、`probe/after-{seed-gcc12,hit-gcc}.json`
- `mutation-spec-final.json`、`mutation-final-out.json`
- probe 本体は job dir にだけ置く (実装面を repo へ入れない)。同定は上記 sha256 と byte 数。
