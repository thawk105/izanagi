## 所見

1. [must-fix] A-2'' の再観測が version 全文を保持せず、gate 後の下位行 drift を受理する

初回 gate は `stdout + stderr` の全文を取得し、receipt と全文比較しています（[s8b_floor_campaign.py:1095](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:1095)、[toolchain_binding.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/toolchain_binding.py:88)）。

しかし `_bind_current_toolchain` が `build_v2` へ返す manifest は `version_first_line` だけです（[s8b_floor_campaign.py:1068](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:1068)）。`build_v2` の再観測も先頭行しか保持せず（[buildcache.py:200](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/buildcache.py:200)、[buildcache.py:230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/buildcache.py:230)）、その縮約値だけを比較してから実 build します（[buildcache.py:660](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/buildcache.py:660)、[buildcache.py:720](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/buildcache.py:720)）。

具体的な新規受理入力は次です。

- Pegasus compute で旧 `gcc-13`/`g++-13` が不在。
- 初回 gate 時点では site 解決された `gcc`/`g++`/`cmake` が receipt と全文一致。
- その後、同じ realpath と同じ version 先頭行を保ったまま、cc/cxx/cmake の version 下位行が変化。
- `build_v2` の比較は一致し、変更後の toolchain で build または cache hit が通る。

段4の「全文束縛」と「gate と実 build 間の drift を閉じる」を同時には満たしていません。

成果物影響: receipt の authority と全文不一致の compiler/cmake による binary が床値測定へ入り、その値から certified 選択・レポートが作られ得ます。

2. [should] helper 比較の変異は殺せるが、wrapper の投影配線を弱める変異が殺せない

pure helper は各 mismatch を検査していますが、`_bind_current_toolchain` が正しい値を helper へ渡したかを各脚ごとに検査していません。例えば次の一行変異は現行テストを生存する見込みです。

- [s8b_floor_campaign.py:1159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:1159) を `live_cc_realpath=receipt.toolchain.compiler_path` にする。
- [s8b_floor_campaign.py:1162](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:1162) を `live_cxx_version=observed["cc"].version` にする。
- [s8b_floor_campaign.py:1163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:1163) を receipt の cmake version にする。

helper の mismatch テストは wrapper を通らず（[test_toolchain_binding.py:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/tests/test_toolchain_binding.py:168)）、wrapper 側は cc の下位行 drift だけを拒否確認しています（[test_s8b_floor_campaign.py:795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/tests/test_s8b_floor_campaign.py:795)）。既存 campaign テストの大半では autouse fixture が実 gate を置換します（[test_s8b_floor_campaign.py:135](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/tests/test_s8b_floor_campaign.py:135)）。

期待値反転・skip・削除・現行 hash 差し込みはありません。ただし上記 fixture により、helper と wrapper の結線変異は M01/M04/M05 の射程外です。

## 受理集合と境界監査

対象である Pegasus compute の fresh build では net で拡大です。旧経路は `gcc-13`/`g++-13` 不在で全拒否でしたが、新経路は次を新たに受理します。

- receipt と一致する site compiler：意図した拡大。
- 初回一致後、先頭行以外だけ drift した toolchain：所見1の未被覆拡大。
- 同じ path/version 表示を持つ別 bytes、異なる `module_list`、同一 version の別 cmake path、receipt にない cxx identity：段4で既知・scope 外とされた拡大。

一方、receipt 不在・不一致や旧 default compiler だけが存在する仮想入力は新たに拒否されるため、全環境を一つの集合として比較すると旧新は包含関係ではありません。

その他の確認結果です。

- bool 述語の例外処理は fail-closed です。`floor_toolchain_matches` は例外時に `False`（[toolchain_binding.py:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/toolchain_binding.py:95)）、caller はそれを拒否へ倒します（[s8b_floor_campaign.py:1156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:1156)）。`None` も明示拒否です。
- `silo_toolchain_matches` は例外を握りつぶさず、上位で `EvidenceFailure` になります（[silo_ladder_rung1.py:3564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/silo_ladder_rung1.py:3564)、[silo_ladder_rung1.py:3659](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/silo_ladder_rung1.py:3659)）。
- official 無条件拒否は維持されています（[s8b_floor_campaign.py:209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:209)）。`run_campaign` の公開引数と注入拒否列挙も基準 commit から不変です（[s8b_floor_campaign.py:2883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/s8b_floor_campaign.py:2883)）。
- `expected_toolchain_manifest=None` は追加条件を短絡するだけで、既存経路を変えません。非 `None` は不一致時に raise するだけなので narrowing-only です（[buildcache.py:661](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/campaign/buildcache.py:661)）。
- gate 全削除は恒真な緑ではありません。`build_cells` の binding 呼出し・manifest 伝播テストが赤になります（[test_s8b_floor_campaign.py:862](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t783-toolchain-binding/orchestrator/tests/test_s8b_floor_campaign.py:862)）。
- 正例が helper と wrapper の双方にあり、静的には恒真な赤ではありません。live version は先頭行でなく全文を取得しています。

pytest・変異 harness は依頼どおり実行していません。既知の2赤は所見に数えていません。

## 総括

- **NO-GO** — blocker は所見1。
- 受理集合は対象の Pegasus compute fresh-build 経路で net **拡大**。登録一致入力に加え、下位行 TOCTOU drift が未被覆。
- live version 全文取得: **yes** — `s8b_floor_campaign.py:1095-1115`。
- 殺せない変異あり: `s8b_floor_campaign.py:1159,1162,1163` の wrapper 投影配線。
- 未確認前提: pytest/変異は未実走、compute 上の実 `gcc`/`g++` realpath・version は未実測。