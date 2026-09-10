# T-2518 — A+B+C inert supply 比較の既存経路 precheck

authority: none
default_effect: no-state-change

## 結論

**今回照合した既存入口では、依存供給と A+B+C 適用木／clean stock の CLI 比較が接続していない。**
実装差分ゼロという依頼範囲では実測を起動せず、inert の緑／赤は未判定として残した。
これは比較の失敗ではない。汎用 dispatch 自体は実在し、専用 launcher の新設が不可避だとも主張しない。
不足しているのは、下記部品を当該入力で連続実行する既存の接続である。

正本は D1936 項17、`docs/archive/worklog-phase3-0909-1398.md` の T-2518、
`output/insights/2026-09-09/t2213-probe-condition-gate/README.md`。
初回確認は `8ca260c3de0898f4af4db4ba544d04cd05c57804`、再開時の照合は
`d85bbb21196f503440ef9641e3dec095e3b43844`。再開時に T-2417 の既存変更を取り込んだうえで確認した。

## 既存部品と接続

| 部品 | 現物と確認結果 |
|---|---|
| 条件 CLI | `orchestrator/campaign/condition_meaning_gate.py` の CLI は `--source-root`、`--stock-root`、`--macro`、`--requested-value`、`--configure-arg` を受け取る。実 CMake configure と owner TU の前処理を行う |
| inert 要求 | 同モジュールの `DEFINE_SPECS` は `BACKOFF_MAX_US=1000` を inert と登録。`_configured_define_compile_commands` と supply 評価は別の clean stock を比較対象にする |
| A→B→C | `tools/pegasus/probes/t2187_adaptive_const_probe.py` の `_applied_patch_stack` は params → dynamic → counterfactual の3 patchを既定pinへ順に適用する。ただし CLI と独立した probe 内の context manager |
| 依存ソース | `tools/pegasus/policy.json` の gflags/glog は、初回確認時に現物 HEAD と pin が一致し status 空。第三者 cache に masstree/mimalloc/googletest が実在。source の所在は install prefix の供給完了を意味しない |
| T-2187 PBS | 依存を /scr へ build/install し prefix を export するが、終端は同 probe の performance/certify 固定。probe の mode は2値で、condition CLI の呼出しはない |
| T-2228 PBS | 同様の依存供給はあるが、実行対象は s1/repro/sweep の専用 liveness probe 固定。当該 A+B+C と inert 要求の入口ではない |
| calibration | `tools/pegasus/certify_calibration.sh` の `run_condition_gate` は既存の結線例だが `BACKOFF_FIXED=-1` と専用 source の比較。任意 macro/patch stack の切替口ではない |
| source 取得 | `tools/pegasus/fetch_third_party.py` の fetch/hydrate/verify/verify-deps は source を扱う。gflags/glog を install して当該 CLI へ渡す入口ではない |
| 計算ノード dispatch | `tools/pegasus/dispatch_compute.py` の generic task は非空 argv を計算ノードで実行できる。clean env・repo cwd での実行機構であり、依存 build や A+B+C 適用を自動で行わない |

欠ける接続は、**計算ノード内で依存 prefix と FetchContent の供給を完了し、A+B+C を適用した木と
別の pinned-clean stock を既存 CLI の supply 比較へ渡す実行入口**である。
既存 PBS の prologue だけを切り出すこと、終端 driver を差し替えること、新しい実行 script を書くことは
本 precheck では行わない。将来接続を作る場合も既存 CLI／patch 適用処理／generic dispatch を再利用でき、
13macro の witness や production gate の新設は必要条件としていない。

## 何を測っていないか

T-2213 の保存済み CLI 出力は supply が `red/configure-failed`、detail が gflags 不足、
runtime meaning が `unestablished/meaning-witness-undeclared` だった。
`stock-inert-mismatch` の赤でも、実行時意味が不正という判定でもない。
今回も configure/build/probe を起動していないため、新しい supply 判定・性能値・certified 結果はない。
規律2、witness registry、family admission、T-2417 所有 probe を変更していない。

## 作業環境の復旧と確認

- 初回は同名 worktree なし、T-2417 の受入稼働を観測。再開時は同名稼働プロセスを観測しなかった。
  今回は計算資源を測定用に確保せず、他 wave の output や probe を編集していない。
- 初回の専用 submodule 初期化は、入れ子の googletest の HEAD が存在しないローカル master を指し停止。
  直接 checkout は guard_bash に拒否された。再開時、空の専用 clone に欠落したローカル参照を既定pinで作成し、
  標準 submodule update の再帰初期化で復旧した。共有main・remote refs・hook設定の変更はない。
- 既存 `dev_wave_submodule_init.py` と `check_wave_startup.py --mode resume` は復旧後 rc0。
- 記録前の関連テストは `run_tests.py` 経由で condition_meaning_gate／ccbench_spawn_sites の
  **164 passed、38.00秒**。bounded local の観測ピークは 2497552384 bytes。
  これは既存テストの結果であり、上記の未実測 A+B+C 比較を緑にする証拠ではない。
- テストケースの新設・変更・無効化は0件。実装差分ゼロなので変異 matrix は適用しない。
- 最終受入の初回は23047 passed / 68 skipped / 21 error。21件は既存snapshot fixture準備で
  googletestの未到達object2788件を検出した。同じ専用cloneに、初回中断時のfetch-packが作った
  `.keep` が残っており、snapshotへコピーされた後のrepackもそのpackを保持していた。
  保持マーカーの本文は `fetch-pack 1897167 on pegasus02`。processの終了を確認して
  orphanなマーカー1件だけを除去した。pack/idxや共有cloneを削除せず、テスト除外で済ませていない。
  欠落HEADだけを直して残骸を見落とした親の復旧漏れとして扱う。
- マーカー除去後の焦点テストは bnode033 / 991675.nqsv で **1 passed、17.05秒**、
  compute結果のchild_rc=0。ログイン側は当時の予算1901953936bytesに達して自動dispatchした。
  Pre-running待ちを親が早まって中断したためwrapperはrc16でholdを残したが、ジョブ自体はその後正常終了。
  requestの不在・結果のjob IDを照合してから、sourceのclean/HEAD確認とhold解除を行う手順とした。
  成功したchildと中断したwrapperの結果を混同せず、最終受入は別途再走する。
- dev-wave 改善候補は、初期化失敗の元 Git stderr を確認しやすくする既存診断導線の見直し。
  handoff に記録しただけで、改善実装・次wave起動・push は行わない。
