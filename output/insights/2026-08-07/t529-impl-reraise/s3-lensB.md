静的検査のみ実施した。pytest・実機試験は実行しておらず、緑は主張しない。

## must-fix

### 1. 段 2 の全面 NO-GO は過大。少なくとも E の共有 leaf 化は今すぐ実装可能

段 2 は「land 可能な実装部分集合なし」とするが、E を活性化全体と束ねたのが誤りである。[s2-plan.md:3–5](/work/1/SFC/tanab/dev-wave-jobs/t529-impl-reraise/s2-plan.md:3)

現在の依存辺は `env_attestation → env_contract` であり、`env_contract` の初期化中に将来の authority loader が `env_attestation.load_verified_calibration()` を呼ぶ設計が循環を作る。[env_attestation.py:22–25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:22) しかも `_env_contract` の使用箇所は loader の型注釈・型検査だけである。[env_attestation.py:1060–1067](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:1060)

実装可能な狭い E は次である。

- 較正 bytes の path confinement・SHA・schema・env・clock・policy 検査を、`env_contract` を import しない共有 leaf へ抽出する。
- 現行 `env_attestation.load_verified_calibration()` は型境界を維持する wrapper とし、共有 leaf に委譲する。
- 将来の authority loader は `env_attestation` ではなく共有 leaf を使う。
- authority state の実 load を CLI 解析後へ移す部分は、loader が未実装なので後続へ残す。

これは恒真実装では通らない。既存試験には成功例、SHA 不一致、policy 不一致、duplicate key、env/clock 不一致、repo escape が既にある。[test_env_attestation.py:1057–1077](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_attestation.py:1057)、[test_env_attestation.py:1107–1165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_attestation.py:1107) これらを共有 leaf にも直接当て、wrapper の委譲を固定すれば、無条件 pass・leaf 未配線の双方を検出できる。

D も、権威として数えない純 data-layer 述語に限定すれば実装候補になる。D176 自身が、1 世代中は production で発火しない遷移述語を純関数試験だけで先行配置することを明示的に許している。[decisions.md:8691–8696](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/decisions.md:8691) `skip`・`downgrade`・全 env 不変を拒否し、少なくとも 1 env が `+1`、他が据置の例だけを受理する表駆動試験なら、無条件 `True` は通らない。ただし入口被覆・活性化権限としては数えてはならない。

A(b) は別である。production historical resolver は現在、全登録世代 index を直接引くだけで、ever-active chain が存在しない。[s8b_ratified_freeze.py:2783–2800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:2783) A(b) 単独を production に結線するには activation chain が必要であり、現時点の独立部分集合とはしにくい。

**成果物影響:** E を残すと g2 活性化時に authority load が入口到達前の import で失敗し、certified 選択結果・レポート・試行台帳の受理集合が空になり、activation 参照自体が発行されない。

### 2. 94a4 は「登録済み g2」ではなく、有力な prospective g2。登録操作を省略してはならない

必要な操作は以下である。

| # | 必要な操作 | 根拠 | 担当 |
|---|---|---|---|
| 1 | 実在 artifact を固定する。path は `output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json`、SHA は `94a4…c5a9` | artifact は Pegasus/2100、accepted、v2、policy 2.0。[artifact:1493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:1493)、[artifact:1568–1602](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:1568)、[artifact:1637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:1637) | 実機取得は既に完了。新規実機走行は不要 |
| 2 | `_build_registry()["pegasus"]` に `generation=2` を追加し、g1 の全 field を維持して `calibration_ref.path/sha256` の対だけを 94a4 へ変更する | 現行 g1 定義。[env_contract.py:256–274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:256) successor は path/SHA の双方が変わる場合だけ有効。[env_contract.py:202–228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:202) | AI が実装可 |
| 3 | g2 が連番、env 一致、全環境で contract hash 一意、g1 の正当 successor であることを検査する | [env_contract.py:278–313](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:278) | AI が試験作成可。実走は親 |
| 4 | 94a4 を loader に通す。repo-relative・存在・root confinement・一回読取・bytes SHA・v2 schema・env・clock・policy を全て満たす必要がある | [env_attestation.py:1068–1117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:1068) | AI/親のローカル検証。実機不要 |
| 5 | loader が要求しない `quality.status=="accepted"` と canonical registered path も activation evidence 側で要求する | 現 loader は accepted を明示要求しない。一方、既存 registry 試験は canonical path と accepted を要求する。[test_env_contract.py:721–776](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_contract.py:721) | AI が実装可 |
| 6 | fuse を単純削除せず、候補列と active 選択を分離する。初期 g1 record、g2 選択 record、A(b)、D、E、active-state 由来の `REGISTRY`、入口 receipt が必要 | 現在は複数世代を拒否し、通れば末尾を current にする。[env_contract.py:316–352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:316) | コードは AI。権威化は maintainer |
| 7 | g2 contract hash を独立計算し、世代 golden を追加する。g1 hash は上書きせず履歴 golden として残す | [test_env_contract.py:69–75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_contract.py:69)、[test_env_contract.py:341–349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_contract.py:341) | AI が実装可 |
| 8 | maintainer が activation issuer を明示実行し、diff と calibration receipt をレビューして commit する | 凍結設計は自動活性化を禁じ、maintainer review/commit を要求する。[activation s2-plan.md:64–75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/insights/2026-08-06_t529-activation-authority/s2-plan.md:64) | 人間の手番 |
| 9 | 活性化後に official 入口の receipt と「最初の書込み前」を Pegasus compute node で受入確認する | loader 自体は artifact reader で、live hardware probe ではない。[env_attestation.py:1060–1117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:1060) | 実機実行。登録 source edit そのものには不要 |

94a4 の PBS job と publish 記録は存在する。[job-result.json:3–6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/job-staging/0:892707.nqsv/job-result.json:3)、[published-self-comparison.json:2–8](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/calibration/attempts/0_892707.nqsv/published-self-comparison.json:2) ただし loader はこれら別ファイルを読まない。従って「実機記録を持つ候補」とは言えるが、静的検査だけで「登録済み g2」「loader 合格」とはまだ言えない。

**成果物影響:** fuse だけ外して g2 を追記すると `sequence[-1]` により g2 が無権威に current となり、certified 成果物の `contract_sha256` と proof 参照が一斉に変わる。逆に追記だけなら import が失敗し、受理集合は空になる。

### 3. D の「据置または +1」だけでは no-op record を拒否できない

前裁定は `skip / downgrade / no-op` の全てを問題としている。[s4-adjudication.md:59–60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/insights/2026-08-07_t529-activation-impl/s4-adjudication.md:59) しかし確定文言は「各 env は据置または +1」だけであり、全 env 据置の record も条件を満たす。[s1-brief.md:11–12](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/insights/2026-08-07_t529-impl-reraise/s1-brief.md:11)

実装条件は少なくとも次の積で固定すべきである。

```text
全 env の delta ∈ {0, 1}
かつ
少なくとも 1 env の delta == 1
```

**成果物影響:** no-op を受理すると contract は同じまま `activation_serial/state_sha256` だけが動き、レポート・試行台帳の activation 参照が意味なく分岐する。

### 4. [T-607] の従属裁定は維持できない。2 つの active は別機構

env 契約は現在、静的 `GENERATIONS` の末尾から `REGISTRY` を作るだけで、freeze active pointer を参照しない。[env_contract.py:344–352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:344)

一方 freeze v2 は独自 namespace の generation・approval・active pointer を列挙する。[s8b_ratified_freeze.py:1079–1165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:1079) pointer がなければ `no-active` で落ちる。[s8b_ratified_freeze.py:1214–1256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:1214) approval/pointer は非 merge かつ逐語 `AI-Agent: none` の人間 commit が必要である。[s8b_ratified_freeze.py:525–549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_ratified_freeze.py:525)

production call path自体は既にあり、`load_ratified_freeze()` の後に `reverify_published_freeze()` が呼ばれる。[s8b_oracle_report.py:1744–1759](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/s8b_oracle_report.py:1744) 従って [T-607] は T-529 ではなく「freeze v2 generation の導入 + 人間 approval/active-pointer commit」に従属する。現 worklog の記述は訂正が必要である。[worklog.md:2974–2976](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/worklog.md:2974)

**成果物影響:** 訂正しないと report subcommand は `no-active` のまま `reverify_published_freeze` に到達せず、published freeze を参照するレポートと certified 選択 proof 参照が生成されない。

## should-fix

### 5. (P4) の docs 内訳は「既存 2、必要 1、欠落あり」

| P4 項目 | 判定 |
|---|---|
| (i) A/D/E の設計メモ | **既存。** A〜E の内容は既存 freeze と worklog に記録済み。[activation README.md:69–75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/insights/2026-08-07_t529-activation-impl/README.md:69)、[worklog.md:2895–2902](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/worklog.md:2895) 単なる再掲は不要。ただし 94a4 実測結果と E/D の実装境界を統合する差分メモは有用 |
| (ii) C(a) の新規タスク | **不要。** T-609 が既に存在する |
| (iii) T-607 項の訂正 | **必要。** 現項は別機構を混同している |
| P4 が落としたもの | **E の共有 leaf 実装・試験、限定的な D 純述語、94a4 prospective g2 の親実測結果の記録** |

したがって「実行可能な成果物は docs のみ」という P4 は成立しない。

**成果物影響:** P4 のまま閉じると、次回 activation wave でも同じ循環依存を再発見し、入口到達前失敗によってレポート・台帳の受理集合が空のままになる。

## nit

### 6. T-609 は C(a) を過不足なく覆っている。新規起票すると重複する

T-609 は、元の `env_contract=None` 迂回に加え、C(a) が送った floor/T-126 の Python 前 write を明記している。[worklog.md:867–874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/worklog.md:867) 追加の (a) は余計な scope ではなく、そもそもの certified-writer 閉包欠陥である。[authority README.md:63–69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/insights/2026-08-06_t529-activation-authority/README.md:63)

C(a) との差分は 0。必要なのは T-609 の再起票ではなく参照である。

**成果物影響:** certified 選択値・レポート・試行台帳の受理集合は変わらないが、重複起票すると閉包完了を指す task 参照が二重化する。

## 総括

1. **実装可能な部分集合は YES。** E の共有 leaf 抽出は現行 loader と負例群に直結し、fuse・入口活性化から独立する。[env_attestation.py:1060–1117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:1060)

2. 誤りは **P1 と P4**。P1 は E/D の独立部分集合を落とし、P4 は既存 T-609 を再起票しつつコード成果物を落としている。[worklog.md:867–874](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/docs/worklog.md:867) P2 の狭い現行 registry 評価と P3 は維持できる。

3. 親はまず prospective g2 の contract hash、`is_valid_successor`、94a4 の `load_verified_calibration` 完走を実測し、共有 leaf の正負試験を `tools/run_tests.py` 経由で走らせるべきである。活性化後の入口保証だけは Pegasus compute node で実測する。