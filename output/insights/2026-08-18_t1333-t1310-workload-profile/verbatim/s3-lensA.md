静的レビューのみです。pytest・実走は行っていません。

### A-01 / 正式 selector は実環境で到達不能なまま

- **根拠**
  - [s2-plan.md:335](/work/1/SFC/tanab/dev-wave-jobs/t1333-t1310-workload-profile/s2-plan.md:335) は「実装後も status は正しく `UNSATISFIED`」とする一方、同 [266 行](/work/1/SFC/tanab/dev-wave-jobs/t1333-t1310-workload-profile/s2-plan.md:266) で「formal selector でも registry / manifest gate は従来どおり必須」とする。
  - [s8c_preregistration.py:1730](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/s8c_preregistration.py:1730) は `all_satisfied = ... all(item.status is PredicateStatus.SATISFIED ...)`、1753 行は `effective` に `all_satisfied` を必須化する。
  - [trial_registry.py:1440](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/trial_registry.py:1440) の登録経路は `EffectivePreregistration` を要求し、1465 行で `require_effective_preregistration` を呼ぶ。manifest 無し経路は [1390 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/trial_registry.py:1390) で holdout を拒否する。
  - 裁定正本 [README.md:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/output/insights/2026-08-17_t1310-formal-workload-profile/README.md:26) は「ratified v2 世代が未発効」「登録済み manifest も無い」と記録し、現 tree に既定 `output/s8c-trial-registry/registry.jsonl` も存在しない。
  - プランが再利用する fixture は [test_p3_autonomous_workload_trial.py:5349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/tests/test_p3_autonomous_workload_trial.py:5349) で `effective=True` の偽 report を作り、5365〜5375 行で capability と `effective_at` を注入する。テスト成功は実在する発火 path の証拠にならない。
- **深刻度**: must-fix
- **成果物影響**: brief が主張する non-certifying 正式 run は一件も起動せず、台帳の受理集合は空のまま変わらない。
- 段 4 では、legacy 用の別 non-certifying admission capabilityを追加するか、manifest／registry 発行を別裁定パッケージへ送り、brief の「起動可能」を撤回する必要がある。

### A-02 / 最初の正式 run 自身が repo scan の 0-hit を壊す

- **根拠**
  - [s8b_holdout_freeze.py:117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/s8b_holdout_freeze.py:117) は「同一ファイルが rratio/skew/rmw の三軸正規表現すべてに一致した場合だけ 1 hit」と定義する。
  - 同 [543 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/s8b_holdout_freeze.py:543) は tracked file に加えて ignore されていない untracked file も列挙する。
  - プラン [s2-plan.md:79](/work/1/SFC/tanab/dev-wave-jobs/t1333-t1310-workload-profile/s2-plan.md:79) は正式三軸を `campaign.search_config["ycsb"]` へ射影する。一方、CLI の既定出力は [p3_autonomous_workload_trial.py:3764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/p3_autonomous_workload_trial.py:3764) の `output/exploration/...` で、root `.gitignore:17-26` は同 directory を除外していない。
  - `campaign.lock` は [campaign_lock.py:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/campaign_lock.py:129) の compact canonical JSON で identity を保存するため、三つの検索字面が同一 file に現れる。
  - プラン [s2-plan.md:163](/work/1/SFC/tanab/dev-wave-jobs/t1333-t1310-workload-profile/s2-plan.md:163) の検査対象は「producer file 本文だけ」であり、新設テスト、fixture、生成 artifact を検査しない。
- **深刻度**: must-fix
- **成果物影響**: 正式 run 後の `conjunction_hits` が非空となり、holdout freeze／将来の ratified proof chain が拒否され、certified 選択の参照閉包を作れなくなる。
- 正式 selector では run root と campaign root を repo 外へ強制するか、別途裁定された exact exemption が必要。producer-only scan では不足する。

### A-03 / 「第三の scale authority を消す」と言いながら runtime literal gate を残す

- **根拠**
  - [s2-plan.md:71](/work/1/SFC/tanab/dev-wave-jobs/t1333-t1310-workload-profile/s2-plan.md:71) は「三つ目の scale authority を作りません」と断言する。
  - しかし同 [88〜98 行](/work/1/SFC/tanab/dev-wave-jobs/t1333-t1310-workload-profile/s2-plan.md:88) は三 sink 各々で `records != 1_000_000 or threads != 48` を runtime rejection に使う。literal は単なる C01 token ではなく受理集合を決める authority である。
  - legacy 文書との四 key 比較も [189 行](/work/1/SFC/tanab/dev-wave-jobs/t1333-t1310-workload-profile/s2-plan.md:189) に残り、oracle は引き続き [s8b_oracle_driver.py:747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/s8b_oracle_driver.py:747) で freeze 文書から scale を読む。
- **深刻度**: must-fix
- **成果物影響**: module／legacy 文書が一致していても一つの sink literal がずれれば正式 run が拒否され、逆方向では producer と oracle の記録 scale が分岐し得る。
- β 経路では literal authority を捨てて C01 を従来 reason のまま残すか、C01 自体を dataflow 検査へ直す必要がある。oracle 共通 helper への族一般化は独立した欠陥二例がなく `DW-G03` を満たさないため、scope 拡張の裁定候補である。

### A-04 / source record は存在するが、consumer 検査は自己整合に留まる

- **根拠**
  - [s2-plan.md:207](/work/1/SFC/tanab/dev-wave-jobs/t1333-t1310-workload-profile/s2-plan.md:207) は producer が `load_legacy_freeze` を呼ぶので、完全な空 field ではない。
  - しかし新 completeness 検査は [240 行](/work/1/SFC/tanab/dev-wave-jobs/t1333-t1310-workload-profile/s2-plan.md:240) の「run-start、report、campaign search config で byte 同値」に留まり、[314 行](/work/1/SFC/tanab/dev-wave-jobs/t1333-t1310-workload-profile/s2-plan.md:314) も「producer の単一 entry と report に記録された source recordだけ」を使う。
  - loader の戻り値または sealed launch authority から consumer が期待 source を独立再導出する記述がない。三コピーを同じ偽値へ変える変異は runtime checker を通る。
- **深刻度**: must-fix
- **成果物影響**: non-certifying run 自体は受理されながら、report／campaign identity／台帳が誤った `source`、path、sha256 を正しい provenance として保存する。
- source record を launch admission の sealed record に束縛し completeness が比較するか、consumer が legacy bytesを独立検証する必要がある。

### A-05 / frozen artifact pin は現在 held であり「緑」は不変証拠ではない

- **根拠**
  - [test_frozen_artifacts.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/tests/test_frozen_artifacts.py:46) に hash pin はあるが、同 [119〜124 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/tests/test_frozen_artifacts.py:119) で holdout freeze は `HELD_FROZEN_MANIFEST_KEYS` に属する。
  - [freeze_verification_hold.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/freeze_verification_hold.py:14) は `HELD: bool = True`。テストは held 時、[test_frozen_artifacts.py:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/tests/test_frozen_artifacts.py:165) で KEEP 側しか hash 照合しない。
  - brief [s1-brief.md:51](/work/1/SFC/tanab/dev-wave-jobs/t1333-t1310-workload-profile/s1-brief.md:51) の「pin は緑のまま」は正確には「held」である。
- **深刻度**: should-fix
- **成果物影響**: JSON と `V1_FREEZE_SHA256` の協調再 pin を見逃すと、source hash、formal campaign ID、manifest 参照が一括して別 bytesへ移る。
- 計画上の再生成経路は見つからなかったが、land 前に基準値 `315b...688` と両 path の非変更を直接確認する acceptance が必要。

### A-06 / 親 M4 の「同一 object」は四 key 全体には成立しない

- **根拠**
  - brief [s1-brief.md:26](/work/1/SFC/tanab/dev-wave-jobs/t1333-t1310-workload-profile/s1-brief.md:26) は「同一 object 同一性が取れる」と一般化する。
  - プラン [s2-plan.md:59](/work/1/SFC/tanab/dev-wave-jobs/t1333-t1310-workload-profile/s2-plan.md:59) は producer entry を新しい dict として作り、`is` を保つのは `ycsb` だけで、records／threads は値コピーである。
- **深刻度**: nit
- **成果物影響**: 四 key canonical 比較が実装される限り成果物差はない。親 brief の表現だけを「ycsb object identity」に狭めるべきである。

### 反証済みの攻撃

- C01 は実際に [s8c_preregistration_evidence.py:1423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/s8c_preregistration_evidence.py:1423) で literal の存在しか見ない。ただしプランの synthetic scale 射影と formal tamper rejection [s2-plan.md:151](/work/1/SFC/tanab/dev-wave-jobs/t1333-t1310-workload-profile/s2-plan.md:151) は sink dataflow を反証可能にする。C01 自体も SATISFIED を主張しない。
- non-certifying 漏れは見つからない。[trial_registry.py:1480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/trial_registry.py:1480) が `certifying=False` を発行し、[autonomous_trial_completeness.py:1574](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/autonomous_trial_completeness.py:1574) と [s8c_acceptance_receipt.py:275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1333-t1310-workload-profile/orchestrator/campaign/s8c_acceptance_receipt.py:275) が再強制する。
- T-1349 の二経路は完全な同一関数呼出しではない。producer は `project_from_search_config`、arm resolver は `descriptor_for_holdout` を呼ぶ。ただし後者も同じ projector へ降りるため、独立性は固定 digest pin が担う。提示された rr80／rr20 digest は読取 probeでも一致した。
- 親 M3 の四 key 同値と上位集合、M6 の C01 判定順序は現 HEAD の実コードと一致する。

**全体判定: NO-GO**

## 総括

最大の穴は、C01 を UNSATISFIED に保ったまま effective preregistration／manifest を必須にし、正式経路を実 artifact 上で発火不能にしている点である。  
次に、最初の正式 run が repo 内へ三軸を生成し、守るべき 0-hit を自分で破壊する。  
scale literal の第三 authority と、source record の自己整合検査も land 前に解消が必要である。  
trial admission と repo 外出力は現 scope 外なので、段 4 の裁定パッケージへ返すべきである。