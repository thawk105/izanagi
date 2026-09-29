---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-29
wave: dev-wave-vhash-forwarding
seq: 3
---

## 再発

### F39

- **再発: 2026-09-29** — [T-2879] (VHash md_6) wave で、新 patch の 3 macro を条件 gate の許可ドメインへ登録した段 5 の単位 B2 に、先例 3867e6ec5 の足跡のうち `orchestrator/campaign/screening_driver.py` の `_CONDITION_DEFAULTS` (鍵集合が DEFINE_SPECS と完全一致) と `orchestrator/tests/test_screening_driver.py` を渡さなかった。親の登録関連の焦点走にも test_screening_driver.py を入れていなかった。並行 wave (md_2) の受入実測をマネージャーが共有して判明し、受入前に fix で足した (land 前、実害なし)。恒久対応は F39 の運用 (位置・鍵を台帳に持つ test を閉包と焦点走に入れる) から変えない。先例 commit の変更 file 一覧を閉包の起点にすれば防げた。

### F42

- **再発: 2026-09-29** — [T-2879] wave で新規 `orchestrator/tests/test_vhash_forwarding_prototype.py` (pytest 専用) を `orchestrator/tests/README.md` の pytest 専用 allowlist に載せずに統合した。受入前の DW-O26 焦点走で `test_plain_runner_coverage.py` を含める段で気づき、allowlist に足した (受入全走の前、実害なし)。恒久対応は F42 のまま。

### F139

- **再発: 2026-09-29** — [T-2879] wave で、静的レビューと login の pytest を通った計測 driver が計算ノードの smoke で 6 回止まった: Cicada は 4 target で同じ TU を compile し compile entry が 4 件、masstree の config.h は build 時にしか生成されず configure だけの木と gate の前処理で 2 回、gate へ渡す configure 引数に検査対象 macro の CXX_FLAGS が入り重複 define、patch の行挿入で `__LINE__` がずれ inert 比較が不一致、検査木に gate 登録が無い。どれも先例 (silo_policy_coverage の `_prepare_build_dependencies` と gate 呼び出し、instr-mocc-lock-coverage の `#line`) に既に答えがあった。smoke は 1 回 20〜100 秒と安く、実害は時間だけ。恒久対応は F139 のまま (実機の書式・生成物は先例の実装か最安の生死確認で確かめてから driver に書く)。
