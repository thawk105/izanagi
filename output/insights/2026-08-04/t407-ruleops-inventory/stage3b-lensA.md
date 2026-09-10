## fail-open の射程 (行を引く)

- **[real] 緩和されるのは `build_inventory` の selected blob payload だけ。** scope・`--kind`・regular mode を先に絞り、全 selected path の batch object と履歴を検査した後で strict decode している [ruleops.py:642–668](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:642)。プランはこの例外だけを `counter += 1; continue` にする [stage2b-plan.md:19–56](/work/1/SFC/tanab/dev-wave-jobs/t407-ruleops-binary-blob/stage2b-plan.md:19)。snapshot 再検査は残る [ruleops.py:684–691](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:684)。

  成果物影響: certified 選択・研究レポート・試行台帳は不変。変わるのは inventory の受理集合、`items`、schema、`skipped_non_utf8` だけ。

- **[real] `inspect` / `check` は inventory を consumer にしていない。** `inspect` は明示 path を `_inventory_item` へ渡し、target 自身を strict decode する [ruleops.py:1006–1012](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:1006)、[ruleops.py:1048–1074](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:1048)。`check` は ledger 内の明示 path を regular blob/OID と照合する [ruleops.py:2020–2065](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:2020)。repo 全体の `build_inventory` call site を追ったが、production call は CLI dispatch だけだった [ruleops.py:2200–2216](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:2200)。受入 preflight も `inventory` でなく `check` を呼ぶ [run_tests.py:540–559](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/run_tests.py:540)。

  成果物影響: 「inventory に無い = 存在しない」と機械解釈する consumer は確認できなかった。漏れが効くのは人間の候補発見・網羅性判断であり、`check` の機械的受理集合ではない。

- **[real] 変更後も拒否される非 UTF-8／非 ASCII 境界は `build_inventory` と独立している。**

  | 入力 | 拒否位置 |
  |---|---|
  | `inspect` target | [ruleops.py:1006–1012](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:1006) |
  | ledger JSON | `_strict_json` の [ruleops.py:191–217](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:191)、caller の [ruleops.py:2026–2034](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:2026) |
  | receipt JSON | [ruleops.py:1307–1324](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:1307)、[ruleops.py:1666–1677](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:1666) |
  | insight candidate target | [ruleops.py:1967–1973](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:1967) |
  | evidence / replacement-node blob | 共通 `_blob_text` の [ruleops.py:524–528](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:524) |
  | `ls-tree` metadata/path | [ruleops.py:387–397](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:387) |
  | batch header | ASCII strict の [ruleops.py:494–515](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:494) |
  | last-change history token | [ruleops.py:549–575](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:549) |
  | grep / pickaxe path | [ruleops.py:721–731](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:721)、[ruleops.py:808–831](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:808) |
  | receipt の merge-base / tree / epoch token | [ruleops.py:1550–1600](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:1550)、[ruleops.py:1615–1663](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:1615) |

  成果物影響: プランどおり局所変更なら `inspect`・ledger・receipt の受理集合は不変。共有 helper 経由の結合は見つからなかった。

## test 族が消えることの危険

- **[real] PEP 263 の実行可能な Latin-1 test は、pytest の収集対象になりつつ inventory から消せる。** runner の既定 target は `orchestrator/tests` [run_tests.py:46–48](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/run_tests.py:46)、pytest command はその directory を渡す [run_tests.py:290–308](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/run_tests.py:290)。`pytest.ini` も同じ tree を収集する [pytest.ini:12–14](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/pytest.ini:12)。`conftest.py` は収集 item に group marker を加えるだけで、encoding filter はない [conftest.py:123–139](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/conftest.py:123)。in-memory の静的 probe でも Latin-1 cookie 付き非 UTF-8 bytes は `iso-8859-1` と検出され、compile 可能だった。

  成果物影響: targeted pytest では実行される correctness guard が inventory `items` から消え、RuleOps の人間向け一覧・参照集合だけが欠落する。

- **[real—ただし全走防壁あり] clean な通常全走では、その Latin-1 file は別メタテストが赤にする。** `test_plain_runner_coverage.py` は直下の全 `test_*.py` を列挙 [test_plain_runner_coverage.py:44–46](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_plain_runner_coverage.py:44)し、各 file を `encoding="utf-8"` で読む [test_plain_runner_coverage.py:30–32](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_plain_runner_coverage.py:30)、[test_plain_runner_coverage.py:60–74](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_plain_runner_coverage.py:60)。一方、targeted runner はこのメタテストを含めず、RuleOps preflight も発火しない [test_run_tests_preflight.py:307–311](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_run_tests_preflight.py:307)。

  成果物影響: clean 全走を経た certified 選択には直ちに漏れないが、targeted 検査・RuleOps package・人間レビュー段階には漏れ得る。緑は実測していない。

- **[real] 件数だけでは退役裁定の完全性警告として不十分。** 固定 inventory file は持たず、通常追加への追随もない [ruleops.md:36–38](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/docs/ruleops.md:36)。retirement lifecycle は段階1で単に `inventory` と `inspect --draft` を使う [ruleops.md:150–164](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/docs/ruleops.md:150)。default `all` の counter は test/insight の内訳も identity も持たない。

  具体例: related-test だけを回す退役準備で、operator が default inventory の非ゼロ件数を既知の raw insight と解釈する。実際には PEP 263 test も1件消えており、その test が候補 test の helper に依存している。宣言済み replacement node だけの advisory receipt と ledger は構造上通り得るため、段階4〜5の人間裁定が誤る。段階7の clean 全走は後で止め得るが、候補 ledger と承認判断は既に誤っている。

  成果物影響: certified 選択は後段全走で保護され得る一方、候補 ledger の参照集合、review report、ユーザー裁定が不完全な census に基づく。

- **[real] direct test candidate の `check` は target 本文を無条件 decode しない。** target は regular blob/OID まで [ruleops.py:2051–2065](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:2051)で、test branch は evidence 検査へ進む [ruleops.py:2145–2154](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:2145)。したがって `inspect` は拒否するが、手書き ledger は信号配置次第で構造上受理し得る。これは brief も T-411 候補として認識済み [brief.md:66–70](/work/1/SFC/tanab/dev-wave-jobs/t407-ruleops-binary-blob/brief.md:66)。

  成果物影響: candidate ledger の `structurally_valid` 受理集合には既存の非対称が残る。今回の inventory schema/counter 変更による新規差分ではない。

## schema v2 の影響

- **[real] `"ruleops-inventory/v1"` の現行 pin は `tools/ruleops.py` の定義1件だけ。** tracked file、hidden/ignored を含む working tree、text 扱いした insight/JSON を exact literal 検索したが [ruleops.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:25) 以外は0件だった。`t362-artifact-inventory/v1` は別 namespace である。

  成果物影響: repo 内 consumer の拒否集合は変わらず、inventory 自身の `schema_version` だけが v2 になる。

- **[real] 凍結材料には旧4-key shape の歴史記録はあるが、v1 literal の現役照合 pin はない。** 旧 plan は root を4 keyと記録する [T-143 s2-plan.md:43–49](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:43)。mutation ledger は当時の nodeid・結果・受入記録である [mutation-ledger.json:14–47](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/output/insights/2026-07-29_t143-ruleops-mutation-ledger.json:14)、[mutation-ledger.json:170–178](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/output/insights/2026-07-29_t143-ruleops-mutation-ledger.json:170)。`check_docs` 自身も insights を追記型の歴史記録として living docs から分ける [check_docs.py:29–33](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/check_docs.py:29)。

  成果物影響: 過去受入記録はその当時の commit に対する記録として残り、現在の v2 出力を拒否する consumer にはならない。

- **[real] v2 literal の変更だけで赤になる現行 test は見つからない。** 現行 test は schema 値でなく root key 集合を検査する [test_ruleops.py:52–57](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:52)、[test_ruleops.py:302–317](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:302)。新 key を足せば synthetic/real の exact-root assertion が赤になるため、定数更新は必要 [test_ruleops.py:1730–1742](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1730)。新規 matrix の v2 literal assertionが初めて schema 値を固定する [stage2b-plan.md:111–122](/work/1/SFC/tanab/dev-wave-jobs/t407-ruleops-binary-blob/stage2b-plan.md:111)。

  成果物影響: test 更新後の固定対象は5-key v2 outputとなる。候補 ledger・receipt schema は別定数のまま不変。

- **[real] v1 のままにすべき実コード上の根拠はない。** `INVENTORY_SCHEMA` は output 生成以外で参照されない [ruleops.py:684–689](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:684)。モジュールや運用文書の「RuleOps v1」は workflow 世代であり [ruleops.py:2–6](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:2)、inventory schema の v1 固定ではない。

  成果物影響: root shape を変えながら v1 を維持する方が同一版名の二形を作る。v2 引き上げに反対する根拠は破れなかった。

## テストプランの穴

三軸 matrix の事前登録変異 [stage2b-plan.md:198–207](/work/1/SFC/tanab/dev-wave-jobs/t407-ruleops-binary-blob/stage2b-plan.md:198)を攻撃した結果は次のとおり。

| 変異 | 判定 | 殺す assertion |
|---|---|---|
| (a) `.raw` だけ skip | 殺せる | 他 suffix の非 UTF-8 で例外、または path 不在/count 5が失敗 |
| (b) insight だけ skip | 殺せる | direct test cell と test count 1 |
| (c) 全 item を skip | 殺せる | UTF-8 control 5 path と format map |
| (d) 定数／実 skip と無関係な counter | **部分的** | 単純定数・unique OID は死ぬが、path名や特定bytesを数える実装は生きる |
| (e) 現行どおり raise | 殺せる | matrix 呼出し自体が例外 |
| (f) counter 無し／増分無し | 殺せる | exact root、key access、値5 |

成果物影響: (d) の survivor を残すと、inventory の不完全性件数だけが嘘になり、candidate ledger/certified 選択は直接変わらない。

- **[real] zero case が固定されていない。** `_base_repo` の selected file は UTF-8 だが [test_ruleops.py:109–150](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:109)、既存 inventory test は root set と items しか見ない [test_ruleops.py:302–317](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:302)。プラン本文は「0」と説明するだけで assertion を追加していない [stage2b-plan.md:150–154](/work/1/SFC/tanab/dev-wave-jobs/t407-ruleops-binary-blob/stage2b-plan.md:150)。`max(1, actual)` 型が通る。

  成果物影響: 完全な inventory でも `skipped_non_utf8=1` と報告し、人間が存在しない欠落を前提に判断する。

- **[real] scope 外／non-regular を counter に入れない契約が未被覆。** matrix の非 UTF-8 は全て selected scope 内 [stage2b-plan.md:95–103](/work/1/SFC/tanab/dev-wave-jobs/t407-ruleops-binary-blob/stage2b-plan.md:95)。既存 symlink/gitlink test は item 不在だけを検査し、counter を見ない [test_ruleops.py:320–335](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:320)。scope 外の binaryを数える実装、excluded entry を「落ちた item」と数える実装が生きる。

  成果物影響: `items` は正しくても counter が selected inventory の欠落数でなくなり、report の値が kind/scope と不整合になる。

- **[real] strict-decode-only 条件の fixture が相関しすぎる。** 全 invalid payload は同じ `b"\xff\n"`、全 path は `non_utf8`、全 control は `utf8` と命名される [stage2b-plan.md:95–105](/work/1/SFC/tanab/dev-wave-jobs/t407-ruleops-binary-blob/stage2b-plan.md:95)。`raw == b"\xff\n"`、`b"\xff" in raw`、path名判定は全期待値を満たす。また valid UTF-8 の NUL control がないため「decode failure または NUL」を skip する拡張条件も通る。direct test cell も Python として実行不能な bytes で、最優先の PEP 263 risk を固定しない。

  成果物影響: UTF-8 として読める blobまで消す、または別形の不正UTF-8を再び全体拒否する実装が受入可能になる。inventory の item集合・counter・人間向け参照集合が誤る。

- **[real—穴なし] BOM JSON control の意図は成立する。** `EF BB BF` は strict UTF-8 decode を通り U+FEFF になることを静的 probe で確認した。`.json` は `artifact_format="json"` [ruleops.py:579–588](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:579)、`_strict_json` は BOM を `bom-json` で拒否 [ruleops.py:191–203](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:191)するが、`_markers` がそのエラーを握って `(None, None)` を返す [ruleops.py:622–639](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:622)。したがって item には残る。

  成果物影響: JSON 妥当性を skip 条件へ誤拡張する実装は control path の存在 assertion で赤になる。

- **[real] `_INVENTORY_ROOT_KEYS` 更新自体は弱体化ではない。** equality assertion は継続し、未知 key と欠落 key の双方を拒否する [test_ruleops.py:302–305](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:302)。item exactness も独立 [test_ruleops.py:313–317](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:313)。

  固定され続けるもの: root の exact 5 key、v2 literal、item exact key、retained path/order、scope/kind、非 UTF-8 path 不在、非ゼロ counter の型と値。

  固定されなくなるもの: 旧4-key/v1 shapeのみで、これは意図した schema 変更。新たに固定できていないものは zero、scope外/non-regular、任意のinvalid-byte形、valid NULである。

  成果物影響: path列など第6のroot keyを加える実装は引き続き赤。今回の裁定どおり根の追加は1 keyに閉じる。

- **[real—穴なし] fixture は実 repo payload に依存せず、恒真でもない。** `_base_repo` は repo作成・Git user設定 [test_ruleops.py:109–115](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:109)、helper は親directory作成 [test_ruleops.py:87–96](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:87)、commit helper は add/commit済み [test_ruleops.py:99–102](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:99)。skip分岐を削除して decode を残せば例外、decodeごと削除すれば invalid path不在 assertionと counter 5が赤になる [stage2b-plan.md:113–122](/work/1/SFC/tanab/dev-wave-jobs/t407-ruleops-binary-blob/stage2b-plan.md:113)。

  成果物影響: real probe件数や揮発OIDの変化で新規テストの受理集合は変わらない。

## must-fix (成果物影響つき)

1. **[real] counter 境界の3 assertionを追加する。** 全selected UTF-8 repoで `0`、scope外の非 UTF-8 regular blobを追加しても不変、in-scope non-regular entryを加えても不変、を固定する。

   成果物影響: 未実装なら inventory report の `skipped_non_utf8` が実際の欠落 item数でなくなり得る。certified 選択・候補 ledger の機械受理集合は不変。

2. **[real] strict-decode-only fixture の相関を壊す。** direct test payloadを実行可能な PEP 263 Latin-1 sourceにし、同一OID複数pathの被覆は維持する。追加commit側は異なる不正UTF-8列・期待を示さないpath名にし、UTF-8 controlの1件には NUL を含める。

   成果物影響: 未実装なら特定bytes/pathだけの skip、NULまで落とす binary heuristic、実行可能な非UTF-8 testだけ拒否する実装が通り、inventory の item集合と人間レビュー参照が誤る。

3. **[real] `docs/ruleops.md` の「既知限界」だけでなく retirement lifecycle 段階1・4にも警告を置く。** default `all` の件数は test/insight の内訳ではなく、`--kind test` が非ゼロなら「全 direct test を列挙済み」という根拠に使えない、と明記する。出力形式・path列・scopeは変えない。

   成果物影響: 未実装なら構造上validな candidate ledgerと人間 review reportが不完全inventoryを全数調査と誤認し、誤ったユーザー裁定へ進み得る。certified 選択は後段全走で別途保護される。

## nit / backlog

- **[real / backlog、既知 T-411]** direct-test candidate targetの本文を `check` がdecodeしない非対称は残る [brief.md:66–70](/work/1/SFC/tanab/dev-wave-jobs/t407-ruleops-binary-blob/brief.md:66)。

  成果物影響: 一部の非 UTF-8 direct candidateが `structurally_valid` になり得る。今回の inventory 差分ではない。

- **[real / backlog、既知 T-412]** receipt固有の非 UTF-8 negative testはない。ただし receipt は ledger と共通の `_strict_json` を通り、既存 ledger negativeが共通helperの緩和を殺す [test_ruleops.py:382–403](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:382)。

  成果物影響: 現実装の受理集合は不変。将来 receipt callerだけを緩める変異は検出されない。

- **[real / backlog、既知 T-410]** Git stderr は不許可rcのときだけstrict decodeされる [ruleops.py:359–365](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:359)。許可rcの非 UTF-8 stderrは捨てられる。

  成果物影響: 現在は stdout由来のinventory/check値を変えないが、診断情報の欠落を検出できない。

## 攻撃したが破れなかった点

- **[real—破れず]** 同一OID複数pathでも path/item単位counterは実装可能で一意。raw取得だけがOIDでdedupされる [ruleops.py:471–482](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:471)一方、item loopはselected pathごと [ruleops.py:649–663](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:649)。同bytesを5 pathに置くmatrixはunique-OID countを殺す。

  成果物影響: 正しく実装すれば `items` から実際に落ちた path数とcounterが一致する。

- **[real—破れず]** kind内だけ数える定義は selection 順序で閉じる [ruleops.py:649–659](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:649)。`5/1/4`、追加後`6/1/5`は単純定数とkind外countを拒否する [stage2b-plan.md:124–126](/work/1/SFC/tanab/dev-wave-jobs/t407-ruleops-binary-blob/stage2b-plan.md:124)。

  成果物影響: `--kind test/insight` の report値は各出力から落ちたitem数として解釈できる。

- **[real—破れず]** batch/history integrity は decode skip前に全 selected pathについて実行される [ruleops.py:660–668](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:660)。壊れたobject/header/historyを「binaryだから」と読み飛ばす経路はない。

  成果物影響: repository integrity failure の拒否集合は不変。

- **[real—破れず]** BOM JSON control は itemに残り、markerだけNoneになる。JSON妥当性をskip条件へ広げる変異を殺せる。

  成果物影響: UTF-8 decode可能な `.json` の inventory item集合は維持される。

- **[real—破れず]** schema v2を拒む現役consumer、保存inventory、JSON Schema、凍結 insight 内のv1 literal pinは確認できなかった。

  成果物影響: v2引き上げで赤くなるrepo内consumerはなく、旧記録は歴史記録のまま。

- **[real—破れず]** PEP 263 testが clean通常全走まで黙って通る経路は、現行 `test_plain_runner_coverage` により破れなかった。

  成果物影響: clean全走を必ず踏む最終landではLatin-1 testの存在自体が赤になる。ただしtargeted reviewの欠落は残る。

## 総括

**NO-GO。** 裁定済みの「非 UTF-8 scoped blobを読み飛ばし、根に整数件数を出す」方針を覆す新事実はない。schema v2、局所的な `build_inventory` 修正、BOM control、inspect fail-closed負例は成立する。

ただし段2プランのままでは、counterの zero／scope／non-regular 境界と、strict-decode-only 条件を殺すfixtureが不足する。また件数だけの警告は human retirement census として不十分なので、lifecycle上の明示が必要である。この3点を plan v2 に入れるまで実装へ進めるべきでない。

read-only 静的検査のみで、pytest・受入全走は実行しておらず、緑は主張しない。