# 段 6 fix3 裁定 — md_22 [T-2911] (2026-09-30 00:4x JST)

smoke1 (commit 1fad6942b、36427.nqsv、bnode140、job 内 19 秒、raw `raw/smoke1.json`): rc=1、build 0 件・run 0 件で停止。
`raw["error"]`: `condition gate rejected IZANAGI_CICADA_ROGC_WORKLOAD` — supply `preprocess-failed`・meaning `compile-time-branch-preprocess-failed`。
stderr: `cc/cicada/ycsb_cicada.cc:3` → `include/common.hh:10` → `include/masstree_wrapper.hh:20: fatal error: config.h: No such file or directory`。
帰属: 本 wave の driver。workload macro の owner TU `ycsb_cicada.cc` は masstree の `config.h` を include し、この file は CCBench の build の途中でしか生成されない。driver は gate を build より先に呼ぶので、新しい source copy では前処理が必ず失敗する。
先例: `orchestrator/campaign/vhash_forwarding_prototype.py` の `MACROS["dependency"] = ()` (macro なしの build を gate の前に 1 回)、`orchestrator/campaign/silo_policy_coverage.py` の `_prepare_build_dependencies` (「Hydration supplies fresh per-job sources, not masstree's generated config.h. Complete one ungated stock build before either mode can enter a case gate.」)。記憶の既知の罠 (condition gate の 2 例目) と同じ。

- **FB-9:** driver の各 source copy (smoke の trace・vlife の別 copy を含む、gate を呼ぶ全 source) について、gate を呼ぶ前に macro なし・gate なしの build を 1 回行い、`config.h` など build 時生成物を作ってから gate と本 build に進む。先例と同じく、この依存物 build は診断用で性能値の出所にしない (materializer 登録は既存の `_build_variant` の登録で足りるか、新しい関数に `"--build"` の字面が入るなら登録簿と `test_p3_build_authority_cli`・spawn-site の分類も更新する)。依存物 build の所要を raw に記録する。
- 先例 driver の test (`test_vhash_forwarding_prototype.py` 等) にある「依存物 build が gate より先」の検査の形に倣い、本 driver でも順序を検査する test を足す (呼び出し順を記録する代役で、実物の gate・build 関数の名前を名指しする)。
- 既存テストの期待値は変えない。
