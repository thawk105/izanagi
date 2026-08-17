1. **severity: critical — REAL: (P1a) は現状のままでは二重に発火不能**

   C01 は committed source の静的条件を通過しても、最終結果は `SATISFIED` ではなく `EVIDENCE_UNDEFINED` です。[`_evaluate_c01`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/s8c_preregistration_evidence.py:1414) と [`SATISFIABLE_CONDITION_IDS == empty`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/tests/test_s8c_preregistration_predicates.py:1827) のため、C01 遷移自体は保証ではありません。しかし formal 経路は次の二関門で実際には動きません。

   - `load_ratified_freeze` は live pointer 不在で `no-active`。[s8b_ratified_freeze.py:1271](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/s8b_ratified_freeze.py:1271)
   - plan が例示する `--workload-profile formal --workloads rr80` は manifest を渡さず、unregistered admission に入り、holdout を拒否されます。[s2-plan.md:79](/work/1/SFC/tanab/dev-wave-jobs/t1310-formal-workload-profile/artifacts/s2-plan.md:79)、[p3_autonomous_workload_trial.py:744](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/p3_autonomous_workload_trial.py:744)、[trial_registry.py:1268](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/trial_registry.py:1268)

   最小の非恒真形は、P1a を「未発効の配線」と明記したうえで、valid g1、approval、active pointer、committed manifest/registry を作るテスト repo から、公開 loader と登録済み admission を本当に通して三 sink を発火させる positive test を置くことです。wrapper の直接生成や loader monkeypatch では不足です。現 repo で今すぐ動かすなら、v2 発効か後述の明示 legacy 選択が別途必要です。

   **成果物影響:** 未修正では C01 snapshot だけが `completion-proof-not-machine-checkable` に変わり、実 report と正式受理集合は空のままです。

2. **severity: critical — REAL: formal の意味が campaign 以外へ伝播しない**

   plan は `FORMAL_PILOT_SCOPE` と formal campaign identity を追加しますが、role payload と report は変更対象に入れていません。[s2-plan.md:12](/work/1/SFC/tanab/dev-wave-jobs/t1310-formal-workload-profile/artifacts/s2-plan.md:12)

   現 producer は全 payload を `exploratory-ycsb-abc`、全 report を `exploratory wiring pilot` と固定しています。[p3_autonomous_workload_trial.py:1589](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/p3_autonomous_workload_trial.py:1589)、[同:2296](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/p3_autonomous_workload_trial.py:2296)。さらに generation projection と completeness がその探索値を exact 照合します。[s8c_generation_projection.py:621](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/s8c_generation_projection.py:621)、[autonomous_trial_completeness.py:539](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/autonomous_trial_completeness.py:539)

   したがって現 plan では、正式 scale を走らせても成果物は探索 pilot と記録します。producer だけ formal 表示へ直せば、今度は二 validator が拒否します。少なくとも profile-aware な payload、validation receipt、report claim scope を同じ scope に入れる必要があります。`scientific_claim=False` と non-certifying は維持できますが、探索と称してはいけません。

   **成果物影響:** 未修正では `report.json.claim_scope` と role validation receipt が実走 profile と食い違い、正式結果の参照可能性が壊れます。

3. **severity: high — REAL: bare `RatifiedFreeze` は live repo scan 済み実走 capability ではない**

   `RatifiedFreeze` は静的な世代検証結果です。実走前の full scan、active chain 再解決、列挙 digest は `LaunchValidatedFreeze` 側の責務です。[s8b_ratified_freeze.py:782](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/s8b_ratified_freeze.py:782)、[同:2876](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/s8b_ratified_freeze.py:2876)、[同:3402](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/s8b_ratified_freeze.py:3402)

   plan は bare loader の結果から `holdouts` と `sha256` だけをコピーし、`generation_number`、`activation_head`、`generation_commit` を捨てます。[s2-plan.md:21](/work/1/SFC/tanab/dev-wave-jobs/t1310-formal-workload-profile/artifacts/s2-plan.md:21)。development-time repo scan test は、実走直前に追加された untracked hit や active 世代変更の代替になりません。

   `launch_validate` は oracle 固有の floor/binary closure も要求するため、そのまま再利用できないなら、formal workload 用の縮小 admission capability を新設する設計裁定が必要です。bare 型を暗黙に実走権限へ昇格させるべきではありません。

   **成果物影響:** 未修正では campaign/report が freeze SHA だけを持ち、どの承認世代、HEAD、live scan digest で走ったかを再構成できません。

4. **severity: high — REAL/REFUTED: (P1b)/(P1c) が scale を偽るという親理由は、そのままでは不正確**

   正式な v2 は transition table にない holdout axes、records、threads を v1 から変更できません。[s8b_ratified_freeze.py:126](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/s8b_ratified_freeze.py:126)、[同:1035](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/s8b_ratified_freeze.py:1035)。三 sink の `1_000_000/48` 照合も計画どおり実装されれば、正規 loader 間で records/threads が食い違う経路はありません。

   一方、P1b は「ratified identity を得る」なら `no-active` で止まるので、v2 未発効でも走るという定義自体が矛盾します。P1c の安全な最小形は、明示 selector で [`load_legacy_freeze`](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/s8b_ratified_freeze.py:1376) を使い、source kind を `legacy-v1`、SHA を legacy と記録し、non-certifying に固定することです。`load_verified_freeze(..., expected_hash=None)` は任意の working-tree bytes を受けるため不適切です。[s8b_freeze_io.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/s8b_freeze_io.py:41)

   **成果物影響:** naive fallback では v1 SHA を `ratified_freeze_sha256` と誤記でき、workload axes と provenance が偽になります。proper legacy path なら scale は不変ですが正式承認済みとは扱えません。

5. **severity: medium — REAL: C01 の「sink 関数内 literal」一般化は半分だけ正しい**

   `_integers` は値伝播をせず、`ast.Constant` の int だけを集めるため、非 literal の module 定数、import、helper 戻り値では満たせません。[s8c_preregistration_evidence.py:319](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/s8c_preregistration_evidence.py:319)

   ただし `ast.walk(FunctionDef)` 全体なので、実行される関数本体に限りません。default 引数、annotation、decorator、nested function、`if False` 内の整数でも通ります。さらに `.holdouts` と `.sha256` は到達 graph 全体の属性名集合であり、同一 ratified object への参照とは検査しません。[同:1264](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/s8c_preregistration_evidence.py:1264)

   plan の各 sink mismatch test は必要ですが、C01 snapshot を実射影の証明として扱ってはいけません。

   **成果物影響:** runtime test が無いと、未使用 literal だけで C01 reason が変わり、三 sink の出力値は探索 scale のままでもよくなります。

6. **severity: none — REFUTED: 新設 test 自身の repo-scan hit は plan が見落としていない**

   scanner は同一 file の三軸 conjunction で、除外は `output/s8b-freeze/` のみです。[s8b_holdout_freeze.py:492](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/s8b_holdout_freeze.py:492)、[同:530](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/s8b_holdout_freeze.py:530)。plan は比率を文字列連結または helper から生成すると明記しています。[s2-plan.md:170](/work/1/SFC/tanab/dev-wave-jobs/t1310-formal-workload-profile/artifacts/s2-plan.md:170)

   現 HEAD の read-only scan probe は rr80/rr20 とも 0 hit、陽性対照 82 hit、除外 path は指定の一つだけでした。pytest は実行していません。docs/golden を後から追加した場合も、段 7 は docs commit 後の再 scan を要求します。[dev-wave/core.md:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/docs/dev-wave/core.md:87)

   **成果物影響:** plan の回避形を守れば `conjunction_hits` は両方 `[]` のままです。完全な三軸表記を test、fixture、golden、docs の一ファイルへ置けば、その path が直ちに追加されます。

7. **severity: high — REAL: pin を「現在発火する防壁」とみなす親前提は誤り**

   `holdout_freeze.json` 自体の SHA は `FROZEN_MANIFEST` と v1 定数に一致しており、plan の no-touch 変更から壊れる経路はありません。[test_frozen_artifacts.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/tests/test_frozen_artifacts.py:41)

   ただし artifact 内の generator SHA は現在の generator source SHA と既に異なり、generator bytes と frozen-artifact manifest の検査は `HELD=True` で保留中です。[holdout_freeze.json:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/output/s8b-freeze/holdout_freeze.json:13)、[freeze_verification_hold.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/freeze_verification_hold.py:14)、[test_frozen_artifacts.py:162](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/tests/test_frozen_artifacts.py:162)。したがって「pin test が事故を止める」とは主張できません。

   再同期はこの wave の scope 外です。凍結 bytes や期待 SHA を現 source に合わせて更新するのは誤りで、generator 編集が必要になった時点で新世代・承認を含む別裁定へ戻すべきです。

   **成果物影響:** plan どおりなら frozen bytes と manifest 値は不変ですが、hold 中の accidental edit は pin test が failure ではなく held として扱います。

8. **severity: high — REAL: 親実測から支えられない一般化が残る**

   - M1 の 137 tests は現 snapshot を支えるだけで、正式 scale の runtime 射影を支えません。
   - M3 の `no-active` は現 HEAD の live pointer 不在だけを示し、loader が将来も発火不能とは示しません。
   - M6 は登録済みコード経路の存在を示すだけです。現 worktree には default registry/manifest がなく、formal launch の実在を示しません。
   - M9 は descriptor 単体の値域を支えますが、固定探索値を要求する role projection、completeness、report、8c acceptance までの受理を支えません。
   - M7 は正しく、むしろ plan が未処理です。
   - M8 の 0-hit 結論は現 HEAD について支持されました。

   **成果物影響:** これらを一般化すると、C01 snapshot だけを進めながら formal report、登録 launch、8c receipt が成立したと誤記します。

9. **severity: high — REAL: 六層中、実装 scope に入るのは二層だけ**

   | 層 | plan の扱い |
   |---|---|
   | producer | 編集対象 |
   | C01 evaluator | scope 外、静的弱点は残る |
   | C01 snapshot | 編集対象 |
   | repo scan | 実走対象だが実装は no-touch |
   | 凍結検証 | bare loader を利用するだけ。live admission は scope 外 |
   | 8c 受入 | scope 外。現在も ratio/campaign ID だけを見て `certifying=False` |

   8c acceptance は records、threads、freeze source、Layer-3 chain を検査せず、最終 receipt も非 certifying です。[trial_registry.py:2408](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/trial_registry.py:2408)、[同:2608](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/trial_registry.py:2608)、[同:2688](/work/1/SFC/tanab/izanagi/.claude/worktrees/t1310-formal-workload-profile/orchestrator/campaign/trial_registry.py:2688)。

   裁定パッケージ候補は、(a) v2 発効まで dormant wiring とするか、typed legacy opt-in を許すか、(b) formal payload/report schema、(c) live repo-scan admission capability、(d) generation identity の artifact binding、の四件です。8c Layer-3 必須化と certifying 化は [T-822] 後続として scope 外のまま明示すべきです。

   **成果物影響:** 現 scope のまま正しく land できるのは producer 配線と C01 gap reason の変更までで、正式 acceptance verdict や certified 受理集合は変わりません。

## 総括

plan as-is は **NO-GO** です。repo scan 回避と凍結 no-touch は妥当ですが、formal CLI は admission まで到達せず、role payload/report は探索表示のまま、実走前 live scan と世代 identity も失われます。

P1a を採るなら「未発効の配線」と限定し、real loader と registered admission を通す positive fixture を必須にしてください。現 repo で実走可能にする最小候補は、`load_legacy_freeze` を使う明示的かつ non-certifying な P1c ですが、ratified と誤記せず、別裁定を要します。pytest は実行しておらず、緑は主張しません。ファイル変更もありません。