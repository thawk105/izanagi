# 段 4 裁定 (親) — plan v2

入力: brief.md、codex/s2-plan.md (plan)、codex/s3-consult.md (相談 1 本、2 レンズ)。裁定 inbox に wave 開始後の T-2847 関連の新しい裁定は無い (2026-09-22 第 31 回まで確認)。

## 所見の裁定

| 所見 | 判定 | 採否・内容 |
|---|---|---|
| plan P3 部分的 (all_pass=false は変異 4 本の check だけから) | real | 採用。brief (P3) を訂正 |
| plan P4 部分的 (SORT_VARIANT は gate 登録済み) | real | 採用。未実走理由を「gate 未登録」にしない |
| plan P5 (stock の buildcache.build も依存物を供給しない、既定 compiler g++-13 が計算ノードに無い) | real | 採用。起動器で依存物と compiler を供給 |
| plan P6 (出力先を driver のローカル束縛差し替えで job dir へ) | real | 採用。tracked JSON の上書き・復元案 (brief P6) は撤回 |
| A1 must-fix (checks の真偽だけでは分類できない、verifier の全出力が要る) | real | 採用。driver が呼ぶ verifier の出力 (stdout JSON 全文・stderr・rc) を、driver の返却値と判定を変えずに受動保存する |
| A2 should (差し替えの到達性は成立) | real | 採用。差し替えは下記 6 種と verifier 出力の受動保存だけに限定 |
| A3 should (evidence は同じ cxx で生成すれば整合) | real | 採用 |
| A4 must-fix (CMake 3.21 以上の確認を投入前提に) | real | 採用。起動器の冒頭で実行前提を確認し、満たさなければ build 前に rc≠0 で停止 |
| A5 should (masstree の config.h 事前生成が要る) | real | 採用。既存 silo_policy_coverage._prepare_build_dependencies をそのまま使う (masstree_build target だけにする最適化はしない) |
| A6 should (Python 版は import 前、compiler は policy 照合、s2 は numactl と /usr/bin/time、t152 の host_role 固定値) | real | 採用。t152 の host_role は表で注記し、起動器が hostname を別に記録 |
| B1 should (s3/s5 は main 維持) | real | 採用 (stock control を残す = 誤検出の切り分けに要る) |
| B2 should (依存準備の反復は削減余地) | real | 不採用 (初回は job ごとに準備。pilot の Elapse で準備費が支配的なら再裁定) |
| B3 should (t152 の abort/BOMB は既存 main の契約として残す) | real | 採用。説明を「既存 main を使うため残す」にする |
| B4 should (sort の未実走理由) | real | 採用。理由 = 「既存 driver の build 経路 (-DCMAKE_CXX_FLAGS=-D<macro>=1) と gate の供給経路 (-DCCBENCH_SORT_VARIANT=1) が一致せず、既定 workload (max_ope=5) も記録済みの hang 条件 (write set 16 要素以上) に届かない。対応は新しい実行経路の追加にあたり今回の範囲外」。「実行できない」とは書かない |
| B5 must-fix (110 分を 2 node 時間未満の根拠にしない) | real | 採用。下記「計算」 |
| C1 must-fix (4 分類の意味) | real | 採用。下記「分類」 |
| C2 must-fix (all_pass=false は盲点の証拠でない) | real | 採用 |
| C3 should (P6 撤回) | real | 採用 |

## plan v2

1. **起動器** (repo 外: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2847-patch-verify/launch_patch_verify.py、Codex author が wave worktree 内の一時 path に書き、親が job dir へ退避する)。引数: `{s3,s5,t152,s2}`、`--third-party-cache <abs>`、`--out-dir <abs>`。
   - 実行前提の確認 (repo module import 前に Python 版、その後 CMake ≥ 3.21、s3_mocc_lock_coverage の policy・toolchain 解決、s2 は numactl と /usr/bin/time)。不成立なら build 前に rc=2 相当で停止し、理由を out-dir に書く。
   - 依存物: s3_mocc_lock_coverage._load_policy / _resolve_toolchain / _prepare_dependencies、silo_policy_coverage._prepare_build_dependencies (masstree の config.h)。FETCHCONTENT_SOURCE_DIR_{MASSTREE,MIMALLOC,GOOGLETEST} を書いた CMake ファイルを out-dir 配下に生成し、環境変数 CMAKE_TOOLCHAIN_FILE と CMAKE_PREFIX_PATH (gflags・glog install) を起動器の中で設定する。マクロ・TRACE・最適化・判定条件はこのファイルに書かない。
   - 差し替えは次だけ: s2.PIN ← pin.CURRENT_PIN / s2・s3・s5 の buildcache 参照の DEFAULT_CC・DEFAULT_CXX ← policy 照合済み compiler (委譲 proxy) / s3・s5 の buildcache.build 呼び出しに明示 cc・cxx・cache_root (out-dir 配下の新しい cache) / s3・s5 の source_digest.resolve_evidence に明示 cxx / s3・s5・t152 の repo_output_root ← out-dir / s3・s5 の ENV_TAG ← "pegasus"。t152 は既存の環境変数 IZANAGI_T152_CCBENCH_SHA (= 現 submodule HEAD の 40 桁)・IZANAGI_T152_CC/CXX・CMAKE_PREFIX_PATH で設定する。
   - verifier 出力の受動保存: driver が verifier を起動する subprocess 呼び出しの結果 (argv・rc・stdout 全文・stderr) を out-dir に run ごとに保存する。driver に返す値・判定・checks は一切変えない。保存に失敗しても driver の結果を変えず、保存失敗を記録する。
   - s2: s2 の既存 preflight (_assert_single_tenant、_assert_free_disk、assert_pinned_clean、_preflight_condition_gates) を呼んでから `_broken_build_and_verify(NORW, …, {"s2": (S2_FLAGS, 3), "legacy": legacy})` と `_broken_build_and_verify(HIGHKEY, …, {"s2": (S2_FLAGS, 3), "legacy": legacy})` を呼ぶ (norw にも legacy を足す: 2026-06-18 の記録に近い小規模条件)。既存 gate3 の述語 (s2:411-419) を同じ形で評価して JSON に書く。「較正」「all_pass」とは称しない。
   - s3・s5・t152: driver の main() を呼ぶ (t152 は _entrypoint 相当の例外処理を保つ)。driver の rc と出力 JSON を out-dir に残す。
   - 起動器は hostname・日時・pin・compiler・python・cmake 版を out-dir の meta JSON に記録する。性能値は取らない。
2. **投入**: `tools/pegasus/dispatch_compute.py --task generic --walltime <HH:MM:SS> -- /usr/bin/python3.10 <起動器> <driver> --third-party-cache /work/1/SFC/tanab/izanagi-thirdparty-cache --out-dir <job dir>/runs/<driver>-<n>`。wave worktree から直列に投げる。順序 s3 (pilot) → s5 → t152 → s2。
3. **分類** (表は run ごとに条件・verdict・cycles・X/P/I 件数・integrity の主要項・既存 checks・分類理由を並べる。併発する層を落とさない):
   - 期待どおり: (a) 期待した層で検出 / (b) 盲点の行 (V09〜V12) で S かつ I 行 0 件 (動的に改竄が起きたことまでは主張しない)
   - 別の層で検出: 期待と違う層の counter が非 0 (根拠の counter を書く)
   - 未発生: 期待した異常が有限の走で観測されない (S のまま)
   - その他: 未実走 (理由つき)・build/gate の失敗・timeout・原因情報不足・stock 対照の異常 (= §4.6 の誤検出を含む)
4. **計算**: 実測単価の無い新種 job なので上限は walltime で数える。pilot (s3) を walltime 00:20:00 で投げ (0.33 node 時間、確認線未満)、その job Elapse と残り build/run 数から「既消費 + 残り (s5・t152・s2) + 受入 1 回 (実測単価 ≈ 0.25 node 時間)」を再見積りし、2 node 時間以上ならユーザー確認を取ってから残りを投げる。
5. **変異 matrix**: repo 内の実装面の差分がゼロなので免除 (DW-S04)。受入全走は記録 commit の後に 1 回行う。
6. **成果物**: insight output/insights/2026-09-23/t2847-patch-verify/README.md (表・分類・限界) と raw/ (driver JSON と verifier 出力の要約。巨大なものは置かない)、verbatim/ (段 1〜6 の逐語)、worklog fragment。
7. **段 6**: review 1 本 (起動器の差し替えが判定を変えていないか + 表の分類と生出力の 1 対 1 照合)。

## brief の訂正

- (P3): 「各 check が偽」→「変異 4 本の check が偽の見込み。stock・abort・BOMB の check は I 行を要求しない」。
- (P4): 「condition_meaning_gate に未登録の可能性」→ 撤回 (SORT_VARIANT は登録済み)。未実走理由は上記 B4。
- (P6): 撤回 (出力先の差し替えで tracked JSON を書かない)。
