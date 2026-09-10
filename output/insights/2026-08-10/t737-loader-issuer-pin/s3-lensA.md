現プランのまま段 5 へ進むのは **NO-GO**。静的レビューのみで、pytest 実走・編集はしていない。

なお、計画どおり実装される限り、合成 G/P 負例が `_validate_document`・catalog 照合・chain 検査で先に拒否される masking は見当たらない。g3 は catalog 登録済みであり、対象入力は [env_contract_activation.py:365–401](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/campaign/env_contract_activation.py:365) の transition gate まで到達する設計である。ただし未実走。

### A-01 — real / blocker — 「production loader」を通していない

file:line: [s1-brief.md:15–18](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t737-loader-issuer-pin/s1-brief.md:15>)、[s1-brief.md:74–78](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t737-loader-issuer-pin/s1-brief.md:74>)、[s2-plan.md:51–95](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t737-loader-issuer-pin/s2-plan.md:51>)、[env_contract.py:519–548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/campaign/env_contract.py:519)、[test_env_contract_activation.py:1544–1564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:1544)

追加予定 node は `activation.load_activation_state()` を直接呼ぶため、`_load_authority_snapshot()` 固有の次の処理を一切通らない。

- `_repository_root()` と authority directory の解決
- `ActivationRecordError` → `EnvContractError` の wrapping
- load 後の `GENERATIONS` 再解決・hash 再照合
- `_verify_entry_calibration`
- current mapping・`_VERIFIED_CONTRACT_SHA256S`・snapshot の構築

既存 bridge test も head と predicate identity しか固定せず、catalog identity と directory positional argumentを見ていない。実 2 env のときだけ正しく、M env では catalog を切る wrapper でも、既存 bridge と新 leaf pin は同時に通り得る。したがって合成証明は成立しない。

**放置時:** レポートと台帳の `layer1=production loader covered` が偽になり、certified 選択が参照する loader 経路に未検査の受理差が残る。

修正案: G/P の負例は synthetic globals/head/directory を設定して `ec.current_activation_state()` または `_load_authority_snapshot()` から呼ぶ。負例は transition で止まるため calibration ファイルは不要。正例は、実 calibration を用意するか calibration stub を明記するか、leaf 正例と正直に名乗るかを裁定する。

### A-02 — real / partial blocker — issuer は production E2E ではなく synthetic-main integration

file:line: [s2-plan.md:114–147](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t737-loader-issuer-pin/s2-plan.md:114>)、[issue_env_contract_activation.py:159–216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/tools/issue_env_contract_activation.py:159)

| patch 属性 | production で置換・迂回する経路 |
|---|---|
| `ec.GENERATIONS` | import-time 検証済み registry、exact env 集合、generation lookup、adapter の entry 解決 |
| `ec._REGISTERED_CONTRACT_CATALOG` | production registry から構築済みの catalog trust root |
| `ec.current_activation_state` | authority loader、source head、既存 chain、calibration、cache の全経路 |
| `ec._ACTIVATION_DIRECTORY` を絶対 path 化 | repo-root-relative authority 束縛 |
| `issuer.__file__` | tool の repo root、import root、handoff の relative path |
| `ec.is_valid_successor` | P node で実 successor 意味論を fault predicate に置換 |

一方、parser、env 集合検査、row/record 構築、既存 record 読込、`validate_activation_records`、writer は実物なので「骨格だけ」までの退化ではない。しかし証明できるのは「合成依存を注入した `main()` の candidate-validation/publish 結線」であり、production authority を含む E2E ではない。

また `issuer.__file__` の差替えにより `main():162` が一時 path を `sys.path` へ恒久追加する。monkeypatch はこの list 変更を復元しない。影響発生は未実走だが、副作用自体は real。

**放置時:** レポートの `issuer production path covered` 参照が過大になり、実 registry・root・current authority の拒否集合は未検査のままになる。

修正案: 負例では到達しない `issuer.__file__` patch を外す。正例では `sys.path` を明示復元する。成果物名は `synthetic issuer.main integration` とし、E2E を名乗るなら別の実 authority bridge を追加する。

### A-03 — real / high — N=1,2,3 の純増検出力はゼロ

file:line: [s1-brief.md:43–45](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t737-loader-issuer-pin/s1-brief.md:43>)、[RULING-PACKAGE.md:47–59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/output/insights/2026-08-09_t673-transition-quantifier-ruling/RULING-PACKAGE.md:47)、[mutation-spec-A-focal.json:5–64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/output/insights/2026-08-09_t673-transition-quantifier-ruling/mutation-spec-A-focal.json:5)

既存 77 node は既に次を殺す。

- G-N1/G-N2/G-N3: [test_transition_rejects_fourth_env_downgrade:571](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:571)
- P-N1: second changed env、[line 921](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:921)
- P-N2: third changed env、[line 939](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:939)
- P-N3: fourth changed env、[line 966](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:966)

したがって登録済み 14 mutant 中、全 suite の純増 status は既存 SURVIVED の G/P-N4,N8,N63,N64、計 **8 mutant** だけである。N1–3 の新 node の赤は「新しい層でも発火する」という layer-specific 証拠にはなるが、純増検出ではない。

**放置時:** mutation ledger の `net-new kills` が 8 から 14 に水増しされ、レポートの純増 frontier の帰属が誤る。

修正案: 「全 suite の純増 8」と「新 node 単独の layer reach 14」を別 matrix にし、expected failing nodeids まで事前登録する。

### A-04 — real / medium — 両層を一つにした正例は mutation 帰属を mask する

file:line: [s2-plan.md:165–175](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t737-loader-issuer-pin/s2-plan.md:165>)

正例は loader を先に実行し、その後 issuer を実行する一 node である。共有 gate を reject-all にする変異では loader で停止し、issuer 正例は未実行になる。それでも node 全体は赤なので、「両層の positive control が変異を検出した」と誤記できる。

これは baseline が通れば両方を実行した証拠にはなるが、変異の層別帰属には使えない。

**放置時:** ledger の issuer 側 positive-control 検出欄が、実際には未到達なのに `KILLED` と記録され得る。

修正案: loader 正例と issuer 正例を別 nodeid に分ける。

### A-05 — real / low — 親の被覆件数は単位が混在している

file:line: [s1-brief.md:32–47](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t737-loader-issuer-pin/s1-brief.md:32>)、[test_env_contract_activation.py:346](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:346)、[test_env_contract_activation.py:1356–1396](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:1356)

`load_activation_state` は 3 call site だが 2 test node であり、「既存テスト3件」は node 数ではない。また「遷移違反拒否はすべて `_validate` helper」という断定には、filesystem record を直接 `validate_activation_records` へ渡す [line 1248–1260](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/tests/test_env_contract_activation.py:1248) や issuer node が含まれない。

baseline の保存ログには 77 items / 4.38 秒の記載があり、静的にも 74 test function + parametrization 純増3で77と整合する。ただし本レビューでは未実走であり、同ログ自身も受入全走ではないと明記している。

外部検索では、live Python consumer・現 SHA/blob pin・role-name key は 0。一方、docs 1 ファイルと output 59 ファイルに path/nodeid 参照がある。これらは歴史記録であり追記を拒否する live pin ではないため、「外部 pin 0」は検索範囲を明記すれば成立する。

**放置時:** レポートの既存被覆件数と `external pin=0` の意味が再現不能になり、参照台帳の分類が曖昧になる。

修正案: call site / test node / live pin / historical reference を別々に数えて記録する。

### A-06 — real / medium — N≥65 は program-equivalent ではない

file:line: [s1-brief.md:71–73](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t737-loader-issuer-pin/s1-brief.md:71>)、[s2-plan.md:151–163](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t737-loader-issuer-pin/s2-plan.md:151>)、[env_contract_activation.py:257–263](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t737-loader-issuer-pin/orchestrator/campaign/env_contract_activation.py:257)

`[:N]` の N≥65 が同値なのは、長さ65の今回 fixture に対してだけである。関数は任意長の tuple を受けるため、66 env なら `[:65]` は非同値である。brief は「族は閉じない」と正しく書いているが、「equivalent mutation」は無限定で不正確。

**放置時:** ledger が N≥65 を `EQUIVALENT` と除外し、将来66 env以上で受理集合を変える生存 mutant を見落とす。

修正案: `TEST-EQUIVALENT AT M=65 / SURVIVED BEYOND FIXTURE` と記録し、frontier は「固定 fixture・登録 slice 族の64」と限定する。

## 総括

(a) 最も重い所見は **A-01**。leaf pin と実2-env bridge の合成では、選択肢 G が要求する production loader 層を固定できない。

(b) 段4の裁定までは進めてよいが、現プランのまま段5実装へ進むのは **NO-GO**。

(c) 親の択一は、推奨: **G/P負例を `_load_authority_snapshot` / `current_activation_state` まで上げる**。それを採らないなら、成果を leaf-only partial と改称し、T-737/選択肢Gを完了扱いしない。