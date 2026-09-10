## 所見一覧

1. **real — 親 brief の A〜G は閉包を尽くしていない。**

   - 根拠: [test_codex_agents.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:123) の 2 個の `== 13`、[.codex/agents/README.md:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/.codex/agents/README.md:1) の current count、同 `:13-14,87` の static/blocked/direct/mediated 件数。
   - 放置時: pytest の件数 assertion が赤になり、README は current state を 13 件と誤記する。
   - brief の後追い H はテスト assertion を回収したが README は回収していない。段2プラン `:361-363` は両方を回収している。

2. **real — brief の D は policy の変更面を過少列挙している。**

   - 根拠: deny token 表だけでなく、入力 family/set と axis map [policy.py:337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:337)、出力 family/set と axis map [policy.py:470](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:470)、backoff grammar/value branch [policy.py:485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/policy.py:485) への追加が必要。
   - 放置時: checker は緑になり得る一方、K2 role だけ planner axis、confidence、literal-only/value 一致検査を通らず、不正な `implementation` を受理する。
   - 段2プラン `:357` はこの欠落を正しく回収している。

3. **refuted — 段2プランまで合わせた mandatory な実装閉包に、さらに別の role-key 更新箇所が残るという欠陥は見つからない。**

   - 根拠: inventory/ledger/policy/adapter/parity/test count/README を段2が列挙済み。hook は glob 由来で動的に新 role を含む [test_hooks.py:4522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_hooks.py:4522)、launcher も role 名を引数から解決する [launcher.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/launcher.py:352)。
   - 放置時: 段2プランをそのまま実装する限り、追加の既存 inventory/count gate が理由で赤になる箇所はない。

4. **refuted — `load_role_specs` に関する親の実測値は正しい。**

   - 根拠: `*.md` glob は [spec.py:320](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/spec.py:320)、manifest 対 inventory の set 等号は `:532-537`、5 ledger 表との等号は `:538-541`。
   - 放置時: source、manifest、5 ledger のいずれかに K2 key が無ければロードが失敗する。

5. **refuted — `EXPECTED_ROLE_COUNT = 13` の実測値は正しい。**

   - 根拠: [review_ledger.py:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/review_ledger.py:10)、強制点は [spec.py:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/spec.py:542)。
   - 放置時: 14 role が全表で整合していても count floor で拒否される。

6. **refuted — Claude role と adapter の全単射・rendered byte parity という親の説明は正しい。**

   - 根拠: expected/actual path 集合比較と role stem 照合は [check_codex_agents.py:216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/tools/check_codex_agents.py:216)、strict parse と rendered parity は同 `:234-245`。
   - 放置時: K2 adapter の欠落・余剰・symlink・byte drift のいずれも checker が拒否する。

7. **refuted — adapter 再生成 CLI が無いという親の説明は正しい。**

   - 根拠: `--write` は [check_codex_agents.py:346](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/tools/check_codex_agents.py:346) で明示拒否。repo 内検索で見つかるのは `render_adapter()` API [spec.py:803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/spec.py:803) と runtime launcher だけ。
   - 放置時: `check_codex_agents.py --write` を生成手段にすると rc=1 になり、ファイルは作られない。

8. **real — `guard_agent.py` の説明は無条件には正しくない。**

   - 根拠: 呼出し側に `model` があれば frontmatter を見ず許可する [guard_agent.py:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/hooks/guard_agent.py:74)。frontmatter pin が必要なのは model 無指定の named-role 呼出し `:82-96`。例外時は fail-open `:110-117`。
   - 放置時: 「named role は常に frontmatter model pin が無いと hook が拒否する」という過大な説明になる。
   - ただし project role 全体の model/effort pin は別の glob テスト [test_hooks.py:4522](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_hooks.py:4522) が強制するため、新 role の予定 frontmatter は必要。

9. **refuted — B〜F の各項目が既存 checker を緑に保つ必須閉包だという一般化は、項目単位では正しい。**

   - B: manifest/source set 等号 — `spec.py:532-537`
   - C: 5 ledger set＋count — `spec.py:538-548`
   - D: role 別 deny token exact 比較 — `spec.py:625-636`
   - E: adapter inventory exact 比較 — `check_codex_agents.py:216-245`
   - F: direct ledger 集合と parity 集合の exact 比較 — [check_codex_agents.py:296](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/tools/check_codex_agents.py:296)
   - 放置時: B〜F のどれを一つ欠いても既存 loader/checker が拒否する。特に F は任意ではない。

10. **real — 「変更面に含めたものは全部 gate-green に必須」という拡張解釈は誤り。**

   - 根拠: policy の診断文 `:498,508,512` の `spec.name` 化は受理集合を変えない。テスト名・docstring・古い「11件」コメント [test_codex_agents.py:1383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:1383)、K2 を negative helper tuple に足す `:1270-1286` も、現在の正例を緑にするだけなら不要。
   - 放置時: checker/pytest の正例は緑になり得るが、診断の正確さ・K2 に対する負例検出力・文書の真実性が落ちる。
   - これらは妥当な保守変更だが、「既存 gate を緑にする必須閉包」ではない。

11. **real — 段2の adapter writer は sandbox 上は可能だが、Codex の編集手順としては不適切。**

   - 根拠: target は repo 内であり、`get_role_spec()` は adapter inventory を読まない [spec.py:725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/spec.py:725) ため、workspace-write sandbox 自体には適合する。一方、段2プラン `:420-423` は `Path.write_bytes()` で直接編集する。
   - 放置時: repo 外書込みや pytest は不要なので sandbox では成功するが、Codex の「編集は apply_patch」契約に違反する。

   tmp を使わない実行可能な代案は、renderer から patch 本文を stdout へ出し、その出力を Codex の `apply_patch` tool に渡すこと。

   ```bash
   PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
   from pathlib import Path
   from orchestrator.codex_roles import spec

   root = Path.cwd().resolve()
   name = "coder-v4-autonomous-k2"
   rendered = spec.render_adapter(spec.get_role_spec(name, root), root)

   print("*** Begin Patch")
   print(f"*** Add File: .codex/role-adapters/{name}.json")
   for line in rendered.splitlines():
       print("+" + line)
   print("*** End Patch")
   PY
   ```

   その stdout 全体を `apply_patch` へ渡した後、次で exact parity だけ確認できる。

   ```bash
   PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY'
   from pathlib import Path
   from orchestrator.codex_roles import spec

   root = Path.cwd().resolve()
   name = "coder-v4-autonomous-k2"
   target = root / ".codex" / "role-adapters" / f"{name}.json"
   expected = spec.render_adapter(spec.get_role_spec(name, root), root).encode("utf-8")
   assert target.read_bytes() == expected
   PY
   ```

12. **refuted — ledger hash に循環依存はない。**

   - 根拠: source hash は raw role bytes `spec.py:583`、description は parsed string `:584-586`、schema hash は [spec.py:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/spec.py:437)、manifest hash は role entry の canonical JSON `:566`。adapter は最後にこれらを読むだけ `:803-873`。
   - 放置時: source＋manifest確定 → 5 hash算出 → ledger/policy更新 → adapter render の順で未確定値を hash する必要はない。
   - source または manifest を hash 算出後に再編集した場合だけ再算出が必要。

13. **real — brief の「`git diff --stat` が 0」は既存 bytes 不変の検証コマンドとして不正確。**

   - 根拠: brief `:51-54` は全体の `git diff --stat` と読めるが、本 wave は意図的な変更・新規ファイルを持つ。段2 `:438` は既存13ファイルへ scope を絞っている。
   - 放置時: global stat は必ず非ゼロとなり、不変条件の成否を判定できない。

   deletion と staged 新規ファイルも混同しない確認は次が安全。

   ```bash
   git diff --exit-code HEAD -- \
     ':(glob).claude/agents/*.md' \
     ':(glob).codex/role-adapters/*.json' \
     ':(exclude).claude/agents/coder-v4-autonomous-k2.md' \
     ':(exclude).codex/role-adapters/coder-v4-autonomous-k2.json'
   ```

14. **refuted — 段2の限定生成手順なら既存13 role/source・adapter の bytes は維持できる。**

   - 根拠: adapter の digest/render は role-local source、manifest entry、role-local ledger、定数化された policy version を使う [spec.py:745](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/spec.py:745)。`EXPECTED_ROLE_COUNT`、他 role の entry、parity 集合、README、テストは既存 adapter bytes に入らない。
   - 放置時: target を K2 の新規 adapter だけに限定し、既存 pin・`POLICY_VERSION`・developer template を変えなければ既存13 adapter の期待 bytes は変わらない。
   - bulk rewrite、共有 template/version の変更、formatter の全 adapter 適用は別経路なので行わないこと。

15. **real・scope 外 — K2 の policy routing には独立した負例テストがない。**

   - 根拠:既存 literal/value テストは K0 role 固定 [test_codex_agents.py:913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/tests/test_codex_agents.py:913)。checker が policy について束縛するのは deny token 表まで `spec.py:625-636` で、`policy.py:470-513` の family membership は網羅検査しない。
   - 放置時: 実装子が K2 を scalar branch へ入れ忘れても既存 checker と段2予定テストが緑になり得る。
   - 新しい検査・テストは wave scope 外なので、**実装せず裁定パッケージへ**送るべき所見。

## 閉包の全走査結果

| 面 | key 側の強制点 | 判定 |
|---|---|---|
| A 新 role source | `load_claude_inventory()` の `*.md` glob、filename/name 一致 [spec.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/codex_roles/spec.py:254) | real・段2収載済み |
| B manifest | `set(roles) == set(inventory)`、role entry 11 key exact | real・段2収載済み |
| C review ledger | `EXPECTED_ROLE_COUNT`＋5 role-key 表 | real・段2収載済み |
| D policy | deny token 表、入力 family/map、出力 family/map、scalar branch | real・段2収載済み。brief 単体は不足 |
| E adapter | expected path 全集合、strict JSON、rendered parity | real・段2収載済み |
| F parity role set | direct ledger 集合との exact equality `check_codex_agents.py:306-314` | real・必須。任意ではない |
| G architecture doc | [agent-architecture.md:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/docs/agent-architecture.md:95) | 成果物要件。gate-green 閉包ではない |
| H test count | `STATIC_ADAPTERS == 13`、`roles == 13` | real・段2収載済み |
| active count doc | `.codex/agents/README.md:1-14,87` | real・段2収載済み。brief A〜H には未収載 |
| source-parity negative tuple | `test_codex_agents.py:1270-1286` | 段2収載済み。正例 green には任意だが負例検出力に有効 |
| project role pin test | `test_hooks.py:4522-4547` が directory を動的列挙 | refuted・literal/count 更新不要 |
| generic Codex launcher | `get_role_spec(role)` で動的解決 | refuted・role literal 追加不要 |
| campaign の既存 role literals | backoff/sort/trigger の既存実行配線 | refuted・K2 は `consumer:null`／手動起動という scope により更新不要 |
| `t080_freeze_migration.py` の exact 13 | 13 role ではなく `_KNOWN_REPIN_ROWS` 12＋holdout 1 [t080_freeze_migration.py:90](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/orchestrator/campaign/t080_freeze_migration.py:90) | refuted・無関係なので変更禁止 |
| 歴史文書の 13 件 | D56 当時の静的移植数 | refuted・歴史的事実として維持 |

結論として、**brief 単体には real な取り残しがあるが、段2プランは mandatory な実装閉包を回収済み**。残るのは policy routing の独立テスト不足という scope 外の保証問題である。

## 変異事前登録の候補

静的検査のみであり、kill は実測していない。

- **候補 M1 — K2 source parity の role-specific bypass。**

  - 変異: [check_codex_agents.py:195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2200-k2-role/tools/check_codex_agents.py:195) に `coder-v4-autonomous-k2` だけ早期 return する条件を入れる。parity set 自体は変えない。
  - 期待赤: 段2どおり K2 を tuple に加えた `test_codex_agents.py::test_planner_and_coder_source_output_wrapper_shape_parity_is_enforced` の1 nodeだけ。
  - 単一理由性: 通常 source は整合済みなので production 正例と set equality は緑のまま。負例 test が作る flattened K2 output schema だけが素通りする。
  - 判定: **real・登録候補**。

- **候補 M2 — K2 を backoff scalar branch から外す。**

  - 変異: 段2実装後の `policy.py:485` の membership から K2 名だけ除く。
  - fixture: schema-valid な K2 出力で `implementation = "double now_backoff = 20; helper();"`、`value = 20` とする。
  - 単一理由性: schema は `implementation` を単なる string として受理し、axis/value/confidence も正しいため、拒否理由は backoff grammar branch だけ。
  - 判定: **real だが現行予定テストでは SURVIVED**。K2 を既存 `test_coder_v4_output_semantics_requires_literal_only_single_statement_value_match` に通す変更が必要で、検査追加は **scope 外・裁定パッケージへ**。

次は候補から除外する。

- K2 を manifest・ledger・count から削る変異: set equality、count floor、件数 assertion が重複して赤。
- F から K2 を削る変異: coverage drift に加え、段2予定の source-wrapper negative test も赤。
- K2 source/schema/hash を単独破壊する変異: source/full-manifest/schema pin、source parity、adapter parity が重なる。
- K2 adapter の削除・内容破壊: inventory/byte parityに加え、adapterを直接読むテストや launcher parity が重なる。

## 総括

判定は次のとおりです。

- 親 brief A〜G、さらに後追い H だけでは閉包不足。README 件数と policy semantic routing が欠けるため **real**。
- 段2プランは、その mandatory な閉包を実装箇所として回収しており、追加の must-fix key/count 箇所は **refuted**。
- B〜F はすべて既存 checker を緑に保つ必須閉包で、特に F は明確に必須。
- hash に循環はなく、既存13 role/source・adapter bytes も限定生成と明示 pathspec 検査で保証可能。
- adapter の repo 内生成自体は sandbox 上可能だが、Codex 子では `write_bytes()` ではなく renderer stdout → `apply_patch` を使う。
- policy の K2 scalar routing を単一理由で殺すテストだけは不足している。これは **real・本 wave scope 外なので裁定パッケージへ**。

pytest、checker、docs checkerはいずれも実走しておらず、緑は主張しません。