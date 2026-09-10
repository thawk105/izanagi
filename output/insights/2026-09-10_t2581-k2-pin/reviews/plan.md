静的調査の結果、最小変更は4ファイルです。brief記載外では、B4 closed-criticのcampaign goldenもpin依存でした。

### 最小plan

1. [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2581-k2-pin/orchestrator/campaign/p3_s4_loop.py:111)

   - `PIN`を指定された完全SHA `511c9538e4e8efa54b45cda62e72389ed3b706ec` のliteralへ変更する。
   - `pin.CURRENT_PIN`参照にはしない。
   - この1定数がcampaign identity、patch適用、pinned-clean検査、隔離checkoutへ流れる箇所は同ファイルの1513、1891、1903、2725、2741行。
   - 他driverのpinは変更しない。

2. [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2581-k2-pin/orchestrator/tests/test_p3_s4_loop.py:573)

   pinを含むcanonical preimageから再導出したgoldenへ更新する。

   - 589-603行: 通常onを`8cf3efb9`、offを`93d98106`へ。
   - 5066-5082行: 同じ2値へ。
   - 6445-6473行: パラメータgoldenを同じ2値へ。
   - 直接`L.PIN`を消費するテストは2533、3946、4014、4135、4197、8622、8663、8713、8842行にもあるが、期待値は動的導出なので編集不要。関連consumerとして実行対象には含める。

3. [test_p3_b4_closed_critic.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2581-k2-pin/orchestrator/tests/test_p3_b4_closed_critic.py:3081)

   briefのアンカー外で見つかった直接依存goldenを更新する。

   - base driverのmarked onを`p3-s4-loop-s4-autonomous-47062c3f`へ。
   - marked offを`p3-s4-loop-s4-autonomous-6e844e5b`へ。
   - sortとtriggerの期待値は不変。

4. [p3_s4_loop_pegasus.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2581-k2-pin/tools/pegasus/p3_s4_loop_pegasus.sh:231) と [test_p3_s4_loop_job_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2581-k2-pin/orchestrator/tests/test_p3_s4_loop_job_contract.py:1153)

   - job bodyの234-235行を、既存7桁を保ちつつ完全40桁も受理する形式検査へ変更する。
   - その後の`rev-parse`、完全HEAD比較、prefix比較は40桁を既に扱えるため変更不要。
   - テストhelperの1180行と1234行を新しい完全SHAへ変更する。
   - 既存のK2実行テスト1312-1338行と1341-1355行が、40桁pinを通過して実driver argvまで届く正例になる。
   - job bodyの登録はpath単位なので、`tools/pegasus/admission_registry.json`の更新は不要。

### 識別子とK2材料の静的結論

- Pegasusの新規fixture campaignは`p3-s4-loop-s4-autonomous-ca474b9f`、同じwal-only K2 manifestを束縛した新規campaignは`p3-s4-loop-s4-autonomous-409e13f8`と導出された。過去の`1145eb11`、`1bebed32`などとは分離される。
- live codeに固定variant ID `8a84a7b00103`のgoldenは存在しない。variantは[pipeline.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2581-k2-pin/orchestrator/campaign/pipeline.py:136)でgenomeと`src_token`だけから導出され、pin文字列自体は直接入らない。
- 旧pinから新pinまでの対象source差分は`cc/silo/transaction.cc`の`TRACE`配下だけで、通常source identityは`TRACE=0`で正規化される。同じ値20と同じ骨格なら、静的導出上は`src_token=4a826c66...`とvariant `8a84a7b00103`を維持する。一方、campaign IDとbuild cache identityは新pin側へ分離される。
- 前回の`knowledge-manifest-wal-only.json`は、commit `2fa13a26...`の6687 bytesのWALをSHA-256まで再解決でき、manifest digestは`396cd559...`で一致した。
- `proposal-wal-only.json`も既存K2 schema、semantic検査、instruction-like検査、backoff文法、値20との帰属整合をすべて通った。両材料は無変更で再使用可能。
- 新pin現物はgitlinkとHEADが指定40桁に一致し、`patches/silo-backoff-fixed.patch`も`git apply --check`成功。静的にはjob bodyの7桁限定検査だけが既知の投入前阻害点。

### Scope境界と検証

- `output/campaigns`、過去insight、凍結snapshot、`legacy_admission_overlay_v1.json`、旧campaignを参照するknowledge-manifest系テストは変更しない。
- [acceptance_duration_ledger.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2581-k2-pin/orchestrator/tests/acceptance_duration_ledger.json:1181)の旧hash入り2キーは検索で検出したが、台帳は明示scope外なので変更しない。
- 実装後は親が`tools/run_tests.py`経由で、少なくとも`test_p3_s4_loop.py`、上記B4 base golden test、`test_p3_s4_loop_job_contract.py`を実行する。今回はpytestも実測も行っていない。

## 総括

実装対象は`PIN`、通常campaign golden、見落とされていたB4 marked golden、Pegasusの40桁受理と既存正例fixtureの4単位です。前回K2材料とvariantは再使用でき、過去campaignや凍結成果物、新gate、台帳への変更は不要です。