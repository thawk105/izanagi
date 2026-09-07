# [T-2356] 段 4 loop の事前構築成果を driver が消費する seam

段 4 loop 用 Pegasus job body (`tools/pegasus/p3_s4_loop_pegasus.sh`) が scratch へ用意した
FetchContent 事前構築成果を、同 job が起動する driver (`orchestrator/campaign/p3_s4_loop.py`) の
build が実際に消費するようにした wave の一次資料。D1679 (seam だけ起票)、D1524 (共有経路へ引数を通す。
別経路を作らない)、D1689 (通す引数は 4 本でなく 5 本) に従う。

## 何が壊れていたか

job body は `buildcache.prepare_masstree_fetchcontent` を呼び `masstree-prebuild-receipt.json` を
create-only で残していたが、**その直後の driver 起動 argv は base も source dir も receipt も
渡していなかった。** 事前構築は実行経路へ 1 bit も届かず、loop 本体の build は proxy 経由の
FetchContent clone に依存していた。D1679 の言う「死んだ経路」である。

## 何が変わったか

- `tools/pegasus/p3_s4_loop_pegasus.sh`: third-party source の複製先を
  `<base>/<name>-src` に変え、`fetchcontent_base_dir` を `$prebuild_source_root` に統一した。
  driver 起動の proposal / fixture 両分岐へ `--fetchcontent-prebuild-receipt "$prebuild_receipt"` を足した。
  qsub の `-v` と required env は変えていない。
- `orchestrator/campaign/p3_s4_loop.py`: receipt loader (`_load_masstree_prebuild_receipt`) を新設。
  receipt を non-symlink regular file として `O_NOFOLLOW` + inode 固定で読み、top-level 10 field の
  exact key 集合、`schema_version` の exact 照合、`fetchcontent_base_dir` と `source_root` の
  canonical・非 symlink・equality、`sources` の exact 名集合と 40 hex HEAD、
  `config_h_path` が `source_root/masstree-src/config.h` と一致すること、`config_h_sha256` を
  **現物 bytes から再計算して照合**することを要求し、5 値 (base / source dir 3 本 /
  `{masstree_head, config_sha256}` の 2 key receipt) を原子的に返すか例外を投げる。
  CLI は `--fetchcontent-prebuild-receipt` の 1 本で、`--no-build` / `--emit-planner-context` との
  併用は build 経路へ入る前に rc=2 で拒否する。receipt があれば site に依らず `env_contract` と
  5 値を `campaign_options` へ入れる。
- `orchestrator/campaign/loop.py` / `orchestrator/campaign/pipeline.py`: 5 引数を素通しし、
  `_validate_fetchcontent_prebuild_inputs` で all-or-nothing と `env_contract` 必須を
  **authorization / layout 作成 / WAL recovery / source identity 解決より前**に検査する。
- `orchestrator/campaign/buildcache.py` は変更していない。消費側 (`-DFETCHCONTENT_BASE_DIR=` と
  `-DFETCHCONTENT_SOURCE_DIR_*` の組み立て、dependency receipt の exact 2 key 検査) は既存実装のままである。
- `tools/pegasus/README.md` §7 の job body 記述を実体に合わせ、R1 の運用注記を足した。

## 構成

- `s1-brief.md` — 段 1 brief (親)。割れうる前提 P1〜P5
- `s4-adjudication.md` — 段 4 裁定 (親)。採用 C1〜C10、scope 外 R1〜R3、refuted F1/F2、変異事前登録 14 件
- `mutation-spec-probe.json` — probe に使った spec (全件 SURVIVED 登録で観測 node を集める)
- `mutation-spec-final.json` — 本走 spec (期待 KILLED + probe の観測 node)
- `mutation-ledger-probe.json.gz` / `mutation-ledger-final.json.gz` — 台帳全文
- `verbatim/` — codex 子の出力逐語 ([T-686] により placeholder guard・三軸語検査の対象外)
  - `s2-plan.md` (plan)、`s3-lens-a.md` / `s3-lens-b.md` (敵対相談)
  - `s5-author.md` (実装)、`s6-review-a.md` / `s6-review-b.md` (敵対レビュー)、`s6-fix.md` (fix)

## 実測で覆した前提

1. **引数が指定した編集面 2 file では閉じない (brief P1)。** 消費側は `buildcache` に全部あるが、
   driver から build までの配線が無い。経路は `p3_s4_loop → loop.run_campaign →
   pipeline.evaluate → buildcache.build_v2` で、D1524 が別経路を禁じているので `loop.py` と
   `pipeline.py` の素通しが要る。実装は production 4 file + test 2 file に閉じた。
2. **job body の source 配置も変えなければ build が必ず落ちる (段 2 plan の発見、親が現物で確認)。**
   `buildcache.py` の `_build_v2_impl` は `dependency_receipt` を渡した build で実効 masstree
   source root が `os.path.join(canonical_fetchcontent_base, "masstree-src")` と exact 一致する
   ことを要求し、不一致は `BuildCacheError` にする。旧配置 (`prebuild-sources/masstree` +
   別 `fetchcontent-base`) のままでは fresh build 後に必ず拒否される。argv を足すだけでは足りない。
3. **引数の前提「稼働中の T-2294 wave も `test_p3_s4_loop.py` を触っている」は成立しない。**
   起動時に 103 branch × 7 file の三点 diff と 95 worktree の未 commit 差分を走査し、
   触っている wave は 0 本だった。T-2294 は worklog 1296 で着地済みで worktree も残っていない。
4. **契約テストの driver 起動 pin には穴があった。**
   `test_p3_s4_loop_job_contract.py` の driver fragment は substring 照合なので、
   起動行へ option を 1 本挿入しても赤にならない。receipt option と後続 option の
   連続 fragment を pin する形へ補強した (段 4 裁定 C8)。

## 保証範囲 (主張の限界)

- **本 wave では Pegasus へ 1 度も投入していない。** 確認したのは login node での
  「production `buildcache._v2_commands` の configure argv まで 5 値が届く」ところまでで、
  実 compute node での build 成立、CMake が事前構築物を実際に再利用すること、
  attestation の exact 照合は未実測である。
- **既に terminal な variant は receipt を渡しても消費しない (R1)。** 同じ `REPO_ROOT` へ
  同じ fixture 値で 2 度目を投入すると、campaign WAL の terminal record により
  `run_campaign` が `evaluate` より前に skip し、build に到達しない。塞ぐには campaign identity か
  duplicate の意味論を変える必要があり、どちらも受理集合・identity を動かすので本 wave の
  scope 外とした。`tools/pegasus/README.md` §7 に運用注記を書き、裁定へ返す。
- **receipt の `pbs_jobid` は非空 str の schema 検査だけで、job 束縛ではない (R2)。**
  別 job の整合した receipt を渡せば通る。`PBS_JOBID` との一致を要求すると login node の
  生死確認が成立しなくなるため採らなかった。D1679 が見送った bytes 級 provenance の側である。
- **FetchContent 依存の内容は build identity を完全には束縛しない (R3、D1690)。**
  base/source の path と mimalloc・googletest の内容は digest に入らない。cache hit 時に
  記録される configure argv が、その binary を実際に作った過去の argv と異なる余地も残る。
  D1690 が「本 wave では是正しない」と裁定済み。
- 契約テストの harness は stub (`hostname` / `git` / `qstat` / `cmake` の sentinel) で job body を
  login node で走らせたものであり、実機の挙動を一般化しない。

## 変異の結果 (14/14 KILLED、期待 node と完全一致)

- 手順 (DW-M07): 事前登録 14 件を probe (全件 SURVIVED 登録) で走らせて観測 node を集め、
  期待 KILLED + 観測 node の spec を機械生成して本走した。baseline は両走とも PASSED。
  本走 spec sha256 `171fae5473c1287b083e7c45b605a9a2aa543733d4e74c3710643355858aa183`、
  repo HEAD `e9ca6dfa0`、schema `izanagi-dev-wave-mutation-spec/v1`、rc=0。
- **runner は本 wave が所有する test へ絞った** —
  `tools/run_tests.py --force-dispatch orchestrator/tests/test_p3_s4_loop.py
  orchestrator/tests/test_p3_s4_loop_job_contract.py -k "prebuild or fetchcontent" -rf`。
  `loop.py` と `pipeline.py` は `campaign_lock.CONTRACT_LOADER_RELATIVE_PATHS` の束縛対象なので、
  repo 全体を走らせると M10〜M14 の赤が `contract-loader-drift` に化けて所有 test の証拠にならない
  (同じ mask を、commit 前の焦点走が 48 赤という形で実測した)。絞った選択では
  drift 由来の node は 1 件も観測されていない。
- **M1〜M4 が同じ 3 node を落とすのは冗長 gate による。** 選択された 3 つの fragment mutant case は
  いずれも「production 側の欠落 + 試験 mutant」で 2 件の静的失敗を観測して赤になるため、
  job body のどの fragment を壊しても同じ集合が落ちる。どの fragment が消えたかは assertion 本文が
  区別するが、node 集合は区別しない。

| 変異 | 内容 | 殺した test |
|---|---|---|
| M1 | copy destination を `${source_name}-src` から `$source_name` へ戻す | fragment mutant 3 case |
| M2 | `fetchcontent_base_dir` を別 root へ戻す | 同上 |
| M3 | proposal 分岐の receipt option を削除 | 同上 |
| M4 | fixture 分岐の receipt option を削除 | 同上 |
| M5 | receipt の `config.h` hash 再照合を恒真化 | `..._loader_rejects_config_hash_mismatch` |
| M6 | top-level exact key 集合を包含判定へ緩める | `..._loader_rejects_nonexact_top_level_keys[extra]` |
| M7 | receipt file の symlink 拒否 3 点 (lstat / `O_NOFOLLOW` / inode 照合) を外す | `..._loader_rejects_symlink_receipt_file` |
| M8 | receipt 指定時の `env_contract` 注入を Pegasus 分岐内へ戻す | production build_v2 正例 (fixture / proposal) |
| M9 | `--no-build` との併用拒否を無効化 | `..._cli_rejects_routes_without_a_build[no-build]` |
| M10 | `run_campaign` 冒頭の all-or-nothing 検査を削除 | `test_run_campaign_rejects_invalid_prebuild_tuple_before_side_effects` 2 case |
| M11 | `run_campaign` の `evaluate_options` 追加を無効化 | production build_v2 正例 (fixture / proposal) |
| M12 | pipeline の `common` 追加を無効化 | 同上 |
| M13 | validator の 2 つの raise を無効化 | loop 側 2 case + pipeline 側 2 case |
| M14 | 既定時にも新 key を `evaluate_options` へ出す | `test_default_prebuild_values_do_not_enter_loop_evaluate_options` |

## 段 6 レビューの結果

敵対レビュー 2 本 (到達性 / 受理集合と scope) はいずれも**実装の must-fix 0 件**とした。
レビュー B の must-fix 3 件は親担当の docs 同期で、`tools/pegasus/README.md` §7 の更新として閉じた
(worklog は本エントリ)。レビュー A の nit 4 件は fix 子がテスト側だけを直した — 既定互換 spy が
production `evaluate` 到達を主張していなかった件、恒真な要素数 assert、実行へ渡されていない
`tmp_path` の空検査、`count(fragment) <= 1` で「元から 0 件」でも緑になる変異証人の 4 件である。
