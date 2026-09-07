## 編集面

現行行番号基準の最小閉包は production 4 file + tests である。`buildcache.py` の実装変更は不要だが、job 内の source 配置変更は必要になる。

- [tools/pegasus/p3_s4_loop_pegasus.sh:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/p3_s4_loop_pegasus.sh:323)

  - `prebuild_source_root` と `fetchcontent_base_dir` を同じ canonical directory にする。
  - source 3 本を `masstree-src` / `mimalloc-src` / `googletest-src` へコピーする。
  - 434–444 行の driver 2 分岐へ receipt CLI を追加する。

- [orchestrator/campaign/p3_s4_loop.py:1413](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:1413)

  - receipt reader を定数群の後、概ね 168 行付近へ追加する。
  - `_run_one_iteration_resolved` の 1413–1423 行へ 5 引数を追加し、1525–1539 行で非既定時だけ `campaign_options` へ入れる。
  - proposal 経路用に `drive_iteration` の 1937–1950、2053–2059 行へ同じ 5 引数を通す。
  - `main` の 2098–2134 行へ CLI、2135–2165 行付近へ組合せ検査と receipt 解決、2267–2278 と 2305–2309 行へ引数を追加する。
  - CLI が直接使わない公開 wrapper `run_one_iteration`（1558–1607 行）は、最小案では変更不要。

- [orchestrator/campaign/loop.py:239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/loop.py:239)

  - `run_campaign` に 5 個の optional keyword-only 引数を追加する。
  - 536–600 行の `evaluate_options` へ、各値が非既定の場合だけ追加する。balanced/non-balanced の両分岐が同じ dict を使うため、分岐別実装は不要。
  - 型注釈用に 22 行の import へ `Mapping` を足す。

- [orchestrator/campaign/pipeline.py:883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/pipeline.py:883)

  - `_prepare_evaluation_core` の 883–913 行と `evaluate` の 1810–1839 行へ 5 引数を追加する。
  - 968 行付近で「5 本 all-or-nothing、かつ `env_contract` 必須」を build/WAL より前に検査する。
  - 1224–1260 行の `common` へ非既定時だけ 5 本を加え、既存の `buildcache.build_v2` へ渡す。
  - `evaluate` から core への 1867–1891 行も、非既定値だけ補助 dict に入れて展開する。

より少ない production file 数にするには driver から `build_v2` を直接呼ぶか、環境変数で注入するしかなく、どちらも D1524 に反する。したがって P1 の 4 file は最小である。

一方、[buildcache.py:2792](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/buildcache.py:2792) は実効 masstree root を `fetchcontent_base_dir/masstree-src` と照合する。現在の `prebuild-sources/masstree` と別の `fetchcontent-base` をそのまま渡すと、2804–2807 行で fresh build 後に必ず拒否される。このため shell の source 配置変更は argv 追加と同じく必須である。ここを一般化するために `buildcache.py` を変える案は採らない。

## receipt の読み口

新しい局所 helper を、例えば `_load_masstree_prebuild_receipt(path: Path) -> Dict[str, object]` とする。top-level は job が現在書く 10 field の exact 集合にする。

| field | 使用・検査 |
|---|---|
| `schema_version` | exact `p3-s4-loop-masstree-prebuild/v1` |
| `fetchcontent_base_dir` | canonical、絶対、non-symlink directory として検査し、共有経路の `fetchcontent_base_dir` に使う |
| `source_root` | 同じ path 条件を検査し、`fetchcontent_base_dir` と exact equality を要求する |
| `sources` | 3 要素、name は masstree/mimalloc/googletest の exact 集合、重複なし、各 record は `{name, head_commit}`、commit は lowercase 40 hex |
| masstree の `head_commit` | `{masstree_head: ...}` へ射影する |
| mimalloc/googletest の `head_commit` | schema/type のみ検査。live HEAD 再観測や build identity への追加は D1690 の scope 外 |
| `config_h_path` | canonical regular non-symlink file かつ `source_root/masstree-src/config.h` と一致することを検査 |
| `config_h_sha256` | lowercase SHA-256 を要求し、`{config_sha256: ...}` へ射影する。load 時にも `config_h_path` の bytes と照合する |
| `configure_argv` / `build_argv` | `list[str]` として検査するが、再実行や configure 構築には使わない |
| `toolchain_manifest` | 既存 `toolchain_compilers_from_manifest` 相当の schema 検査だけ行い、共有経路へは渡さない |
| `pbs_jobid` | 非空 str として検査するが、環境との一致 gate や site 判定には使わない |

`fetchcontent_dependency_receipt` は次の exact 2 key へ変換する。

```python
{
    "masstree_head": sources_by_name["masstree"]["head_commit"],
    "config_sha256": record["config_h_sha256"],
}
```

これは [buildcache.py:717](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/buildcache.py:717) の `_validate_fetchcontent_dependency_receipt` が要求する `{masstree_head, config_sha256}` と完全一致する。build 後には同ファイル 938–984、2808–2816 行で実効 source の HEAD と `config.h` が再観測される。

source dir 3 本は次のように `source_root` から導く案を採る。

```text
masstree_source_dir   = source_root / "masstree-src"
mimalloc_source_dir   = source_root / "mimalloc-src"
googletest_source_dir = source_root / "googletest-src"
```

job 側は概ね次の配置へ変える。

```bash
prebuild_source_root=$scratch/prebuild-sources
fetchcontent_base_dir=$prebuild_source_root
destination=$prebuild_source_root/${source_name}-src
```

receipt に source dir 3 本を直接追加する案は却下する。理由は、既存 3 path から導出可能な値を重複記録して不一致状態を増やし、schema・producer・pin の変更面も広げるためである。また現在の別 root 配置を維持するには `buildcache.py:2801–2807` の意味まで変える必要があり、本 seam の範囲を越える。

## 発火条件

P4 の「receipt が渡されたときだけ」を採る。ただし、[p3_s4_loop.py:1525](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/campaign/p3_s4_loop.py:1525) では次の点が重要である。

- `resolved_site == PEGASUS_COMPUTE` の既存分岐はそのまま維持する。
- receipt がある場合は site に関係なく `env_contract=contract` と 5 引数を `campaign_options` に入れる。
- これにより login-node/`OTHER` の DW-G01 でも legacy `build()` に落ちず、v2 `build_v2()` が選択される。
- receipt がない `OTHER` caller は従来どおり legacy build、receipt がない Pegasus caller も従来の呼出し形のままである。
- `dependency_prefix` の現行 site 条件は変更しない。

既存 `dependency_prefix` は 1526–1529 行で Pegasus 以外では非空でも捨てられる。receipt seam に同じ条件をコピーすると「CLI で渡したが site 判定が偽なので無視」が生じるため不適切である。

receipt を指定しても build が発火しない組合せは残るが、すべて明示的な停止にする。

- `--no-build` または `--emit-planner-context` との併用: CLI error、rc=2。
- unknown/non-admitted site、invalid receipt、build authority 不足: 明示例外。
- `--run-iteration` の入口停止: `outcome=stopped-before`。
- grammar/preflight、quarantine、condition gate、admission での拒否: correctness gate を維持して build 前停止。
- `run_campaign` の terminal recovery skip や identity failure: summary/WAL/log で可視化され、黙って捨てない。

つまり「build 対象まで到達した accepted candidate」については site にかかわらず発火し、規律 2 が止めた候補だけが非発火になる。

## CLI の形

driver の新 CLI は 1 本だけとする。

```python
ap.add_argument(
    "--fetchcontent-prebuild-receipt",
    type=Path,
    metavar="PATH",
    default=None,
)
```

source dir 3 本や base dir を別 CLI にしない。receipt reader が 5 個の共有 API 引数へ展開する。

相互作用は次のとおり。

- 省略時 `None`: 現行動作と完全同一。
- `--no-build` と併用: receipt を受け取って使わない経路を作らないため拒否。
- `--emit-planner-context` と併用: build 経路へ入らないため拒否。
- `--run-iteration` と fixture `--value` の双方: 使用可能。
- `--isolate-worktree`: 独立に使用可能。source/base は job scratch、CCBench worktree と build cache の扱いは従来どおり。

job body の 2 分岐、[p3_s4_loop_pegasus.sh:434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/tools/pegasus/p3_s4_loop_pegasus.sh:434) と 440 行へ同じ形で追加する。

```bash
--fetchcontent-prebuild-receipt "$prebuild_receipt" \
```

新しい qsub 環境変数は不要で、receipt path は job 内の 361 行ですでに確定している。required env の 17–21 行も変わらない。したがって `tools/pegasus/README.md` §7 の tagged qsub command、`docs/pegasus-runbook.md` §7.0 の投影行は変更不要である。

## 既存 pin への影響

driver argv に一行追加するだけでは、現行 test は赤にならない。[test_p3_s4_loop_job_contract.py:293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop_job_contract.py:293) は module、authority、isolation、proposal/value の各 substring しか見ておらず、その間へ新しい option が増えても通る。これは pin の穴なので補強が必要である。

更新内容は次のとおり。

- 251–260 行の source path fragment を `masstree-src` / `mimalloc-src` / `googletest-src` に更新する。ここを更新しない場合、334–335 行の `test_job_body_static_contract` が赤になる。
- 293–297 行付近へ proposal 分岐と fixture 分岐それぞれについて、receipt option と後続 option の連続 fragment を追加する。
- 403–464 行の fragment mutant 群へ、次の削除変異を追加する。

  - proposal 分岐だけ receipt option を削除。
  - fixture 分岐だけ receipt option を削除。
  - `fetchcontent_base_dir=$prebuild_source_root` を別 root に戻す。

- 338–362 行の stage-order test は `prebuild_source_root=` が 1 回のまま、driver が receipt sync 後のままなので変更不要。
- 381–400 行の rc=2 文言 test は shell の refusal 文言を増減しないため変更不要。
- 480–494 行の `--no-build` mutant も変更不要。
- 928–934 行の shell syntax test は引き続き有効。

`tools/pegasus/admission_registry.json` は path/classification/primary gate のいずれも変わらない。[同 test:895](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2356-s4-prebuild-seam/orchestrator/tests/test_p3_s4_loop_job_contract.py:895) の exact entry と `orchestrator/tests/test_hooks.py` の golden 2 箇所は変更不要である。

## テスト設計

正例の署名は次とする。

```text
valid p3-s4-loop-masstree-prebuild/v1 receipt
+ --allow-coder-derived-build
+ --fetchcontent-prebuild-receipt RECEIPT
+ build-producing fixture/proposal
⇒ production orchestrator.campaign.buildcache.build_v2 が呼ばれ、
   kwargs に base + source dir 3 本 + exact 2-key dependency receipt が存在する
```

両層 stub で通る試験にしないため、`p3_s4_loop`、`loop.run_campaign`、`pipeline.evaluate`、`buildcache.build_v2` は production 実体を通す。OS build だけ止める必要がある unit test では、`buildcache.build_v2` を `wraps` で観測し、その下の `_build_v2_impl` を probe 例外で止める。assert 対象を「任意の downstream callable」ではなく production `orchestrator.campaign.buildcache.build_v2` と、その exact kwargs に固定する。

拒否例は D1689 を直接 pin する。

```text
env_contract + fetchcontent_base_dir + source dir 3 本
+ fetchcontent_dependency_receipt=None
⇒ pipeline._prepare_evaluation_core が build/WAL 前に拒否し、
   buildcache.build_v2 は呼ばれない
```

逆方向として、receipt があるが source dir が 2 本しかない場合も同じく拒否する。これは現行 `buildcache` の受理集合より緩める変更ではなく、共有 pipeline seam を 5 本 all-or-nothing に狭める負例である。

加えて default 互換 pin として、5 引数すべて既定値のとき `evaluate_options`、core の `common`、`build_v2` kwargs に新 key が一つも現れないことを spy で固定する。

## 生死確認

DW-G01 は test/probe 本体 100 行以内で成立する。ただし、driver を最後まで走らせると benchmark に進むため、login node probe は configure argv 生成直後で止める。

最小形は次である。

1. 一時 root に 3 source を `*-src` 名で用意し、同じ root を base として production `prepare_masstree_fetchcontent` を一度実行する。
2. job と同じ schema の receipt を作る。
3. production `buildcache._v2_commands` を wrapper し、元関数を実行して configure argv を捕捉した直後に `RuntimeError` 派生の probe sentinel を投げる。
4. production `p3_s4_loop.main` を receipt CLI と fixture `--value` で呼ぶ。
5. 捕捉した argv に以下が各 1 本であることを assert する。

```text
-DFETCHCONTENT_BASE_DIR=
-DFETCHCONTENT_SOURCE_DIR_MASSTREE=
-DFETCHCONTENT_SOURCE_DIR_MIMALLOC=
-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=
```

元の `_v2_commands` 自体を実行するので、手書き argv を検査する自己証明にはならない。sentinel は configure subprocess より前に止めるため、driver 側の trace/perf build、verify、bench は走らない。

Pegasus login node では probe を pytest 化し、直接 pytest/cmake を起動せず `tools/run_tests.py` 経由で実行場所とメモリを決めさせる。今回の read-only 段では実行していない。

## 親の provisional 裁定への異議

- P1: file 集合への異議なし。ただし job の変更は末尾 argv だけでは閉じず、323–360 行の source/base 配置も変える必要がある。
- P2: 異議なし。使用するのは 2-key `fetchcontent_dependency_receipt` であり、`post_oracle_dependency_binding` ではない。
- P4: 異議なし。ただし receipt 指定時は `OTHER` site でも `env_contract` を明示して v2 build を選ばないと、login-node DW-G01 が成立しない。
- P5: 「完全な既存 driver 実走」を意味するなら異議あり。benchmark まで進むため login-node 生死確認として過剰である。production `_v2_commands` を実行して configure 直前で止める上記 probe なら、100 行以内かつ必要十分である。

## 総括

最小実装は job、driver、`loop.py`、`pipeline.py` の 4 production file と対応 test の変更で閉じ、`buildcache.py`、admission registry、hooks golden、qsub/runbook 投影は変更しない。

重要な追加結論は、現在の `prebuild-sources/masstree` と別 `fetchcontent-base` のまま 5 引数を渡すだけでは `buildcache.py:2804` で拒否される点である。job source を共有 base 直下の `*-src` へ揃え、receipt を唯一の明示 trigger として 5 本を共有 pipeline に通す必要がある。静的読解のみで、テストや実測は実行していない。