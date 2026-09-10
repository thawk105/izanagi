## 所見

1. P1 — [p3_b4_raw_record_producer.py:1583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/orchestrator/campaign/p3_b4_raw_record_producer.py:1583): admission sidecar の `admission_record_repository_path` は key の存在しか検査されず、[pair_common_ok](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/orchestrator/campaign/p3_b4_raw_record_producer.py:1601) でも driver の required path と比較されない。launch sidecar は record hash のみを照合し、terminal receipt にも path は無いため、他の永続証拠による補完もない。従って、他欄を保ったまま path を旧値 `admission.json` へ変えた canonical sidecar でも `protocol_ok` を満たせる。raw producer テストにもこの欄の負例が無い。
   成果物への影響: raw arm-source が `protocol_ok=true` のまま、実際の required path と矛盾する admission sidecar を証拠として記録できる。

2. P2 — [test_p3_s4_loop.py:85](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/orchestrator/tests/test_p3_s4_loop.py:85)、[test_p3_s4_loop_sort.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/orchestrator/tests/test_p3_s4_loop_sort.py:47)、[test_p3_s4_loop_trigger_gating.py:67](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:67): 親の焦点走 5 file から、shared helper の間接 consumer 3 file が漏れている。各 file は `_production_launch_context` を import し、その helper は [変更された admission fixture](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/orchestrator/tests/test_p3_b4_closed_critic.py:121) を driver ごとに生成する。静的には赤と断定しないが、consumer-complete な焦点走ではない。
   成果物への影響: base・sort・trigger の実 driver 経路で、required path から生成した launch context、launch sidecar、WAL COMMIT の回帰を記録前に検出できない。

問題なしと判定した点:

- Spawn site は変更前後とも `_git_call` 内の `subprocess.run` 1 箇所だけ。pin の `1` と他の inventory 値に変更要因はない。
- Projection 閉包は両列挙で完全一致した。base は共通 12 member、sort・trigger は各 driver module を 1 件追加するだけで、member 増減はない。現在の hash も二経路で一致した。base `3332345a...`, sort `bf683cb9...`, trigger `12f8361c...`。この完全 hash を literal pin する場所は repository 内に無い。
- closed critic の 2 呼び手は driver kind を渡して再検証しており、変更不要。launcher も `prepare_launch` の最初に検証する。
- CLI に repository 内の別の regular file を渡すと [path gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1784-admission-single-path/orchestrator/campaign/p3_b4_admission_record.py:714) で `B4AdmissionRecordError("[admission-record] record repository path is not the path required for driver_kind")`。repo 外、欠落、symlink、非 regular path はその前に `"[admission-record] record is unavailable"`。いずれも `main` では未捕捉で、driver・sidecar・artifact 作成前に終了する。
- Admission sidecar の生成値とテスト期待値は新 path に追随している。launch context と terminal receipt は repository path 自体を持たず、前者は record hash・commit、後者は driver・projection を保持するため、古い path literal との不一致はない。ただし、これが所見 1 の検証欠落を残す。
- Production 差分は mapping、固定署名、path gate、限定的な非保証 docstring のみ。台帳、一般 resolver、互換 flag、schema 昇格、将来用抽象は無い。
- 事前登録文書は commit 差分なし。命名は `REQUIRED`、docstring は mapping が preregistered source of truth でないと明記しており、文書規範を先取りしていない。

## consumer 全件

検索方法は `orchestrator/**/*.py` 全体に対する次の三系統の `rg`。

- module・API・型・field: `p3_b4_admission_record`, `verify_b4_admission_record`, `VerifiedB4AdmissionRecord`, `B4AdmissionRecordError`, `B4_PROJECTION_DRIVER_KINDS`, `admission_record_repository_path`
- shared fixture: `_committed_admission_fixture`, `_production_launch_context`
- 内容走査 consumer: literal `p3_b4_admission_record.py`

定義 file 自身を除く production consumer:

- `orchestrator/campaign/p3_b4_closed_critic.py`
- `orchestrator/campaign/p3_b4_launcher.py`
- `orchestrator/campaign/p3_b4_raw_record_producer.py`

親の焦点走 5 file:

- `test_p3_b4_admission_record.py`
- `test_p3_b4_closed_critic.py`
- `test_p3_b4_launcher.py`
- `test_p3_b4_raw_record_producer.py`
- `test_ccbench_spawn_sites.py`

親の 5 file との差分となる間接 test consumer:

- `orchestrator/tests/test_p3_s4_loop.py`
- `orchestrator/tests/test_p3_s4_loop_sort.py`
- `orchestrator/tests/test_p3_s4_loop_trigger_gating.py`

これ以外の consumer は検索されなかった。

## 総括

- 最大の問題は、raw producer が sidecar の required path を意味検証せず、矛盾した証拠を `protocol_ok=true` で通せる点。
- 加えて、焦点走から shared fixture 経由の driver test 3 file が漏れている。
- Spawn pin、projection 二重列挙、呼び手、CLI 失敗位置、過剰実装、文書非変更には問題を認めない。
- pytest は実走しておらず、緑とは判定していない。
- 所見 1 の修正と負例追加、追加 consumer 3 file の実測までは記録段へ進めない。