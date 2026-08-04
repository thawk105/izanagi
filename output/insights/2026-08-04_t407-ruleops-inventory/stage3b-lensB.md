## 赤が消えるかの検証 (行を引く)

- [real] 先頭の deterministic red は、プランどおりなら静的には消える。

  - root exact assertion は共通定数を読むため、[_INVENTORY_ROOT_KEYS](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:52) と [output root](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:684) を同時に5 keyへ変えれば [1731](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1731) は成立する。
  - `items` は空にならない。[1733-1736](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1733) が UTF-8 の direct test を positive control として要求し、この path は [_TEST_PATH_RE](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:44) に入る。4件の insight を落としても [1732](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1732) は成立する。
  - `kind` は `_scoped_kind` の結果をそのまま item へ入れるため、[650-659](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:650)、[672-682](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:672) から [1737-1742](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1737) も壊れない。
  - 成果物影響: initial inventory の rc=2 は解消する見込みだが、静的検査なので緑は未確認。

- [real] clone 側では inventory は一度も走らない。clone 後の RuleOps 実行は次の2経路だけである。

  - `inspect`: [1814-1829](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1814)。strict decode するのは指定された UTF-8 candidate target だけで、[_inventory_item](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:1006) は全 inventory を組み立てない。
  - `check`: [1917-1918](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1917) → [_preflight_ruleops](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/run_tests.py:540) → `ruleops.py check`。CLI dispatch も [2212-2213](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:2212) で `validate_candidate_ledger` へ直行する。
  - clone に入る4 blob は tree snapshot には存在するが、inspect/check に全 scoped payload を strict decode する経路はない。
  - 成果物影響: clone 側の observed/pickaxe、candidate package、preflight の受理集合は今回の `build_inventory` 変更では変わらない。

- [real] 受入 preflight は変更されない。acceptance 分類は [_is_acceptance_run](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/run_tests.py:399)、実 command は [546-552](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/run_tests.py:546) の `check` だけである。`INVENTORY_SCHEMA` は inventory output の [688](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:688) でしか使われない。

  - 成果物影響: production ledger preflight の値・受理集合・rc=15 翻訳は不変。

- [real] `build_inventory` を直接呼ぶ既存テストは、対象テスト以外では次が全件である。

  - 成功形: [literal scope/exact keys](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:302)、[symlink/gitlink](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:320)、[dirty worktree](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:338)、[byte identity/sort](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:356)、[Git env](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1344)。
  - fail-closed 形: [missing promised blob](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1357)、[HEAD movement](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1486)、[history boundary](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1521)、[graft created](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1544)、[replace ref](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1674)、[grafts](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1685)、[shallow](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1695)。
  - root literalを持つのは先頭の `test_m1_m2...` だけで、プランは更新対象に挙げている。他は `items`、自己比較、または output 作成前の例外だけを見る。
  - 成果物影響: プラン未記載の root-key 起因の赤は見つからなかった。

## 被覆と恒真性

- [攻撃したが破れなかった] 16セルから10セルへの削減理由自体は破れなかった。direct test は `^orchestrator/tests/test_[^/]+\.py$` に限定されるため、direct `.md/.json/.raw` は production scope に存在しない（[ruleops.py:44-45](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:44)）。

- [real] mutation (a)(b)(c)(e)(f)(g)(h) は計画した assertion で殺せる。

  - (a)(b): 5つの非 UTF-8 path と test/insight count を固定する [plan:113-126](/work/1/SFC/tanab/dev-wave-jobs/t407-ruleops-binary-blob/stage2b-plan.md:113)。
  - (c): UTF-8 control 5 path の存在と format map が殺す。
  - (e): matrix 呼出しの例外に加え、real CLI が `check=True` で inventory を実行する [1719-1729](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1719)。
  - (f): exact root、key access、型、値が殺す。
  - (g): `all/test/insight == 5/1/4` が kind 外加算を殺す。
  - (h): 非 UTF-8 5 path が同じ `b"\xff\n"`、すなわち同一 OIDなのに count 5を要求する [plan:95-103](/work/1/SFC/tanab/dev-wave-jobs/t407-ruleops-binary-blob/stage2b-plan.md:95)。
  - 成果物影響: これらの誤実装による inventory items・count・rc の変化は予定テストで拒否される。

- [real / must-fix] (d) は「固定定数」しか殺せず、「実際の skip 数と無関係な counter」全体は殺せない。`_base_repo` の既存 selected は5件（[115-145](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:115)）、matrix 後は all/test/insight が15/4/11件、追加後は16/4/12件になる。誤実装

  `all=len(selected)-10, test=len(selected)-3, insight=len(selected)-7`

  は payload を一切見ずに `5/1/4 → 6/1/5` を完全通過する。

  - 成果物影響: `skipped_non_utf8` が実際の欠落 item 数と乖離し、人間が inventory の不完全性を誤認する。

- [real / must-fix] 「strict decode 不能だけ」を固定する control が不足している。

  - 先例は UTF-8 判定前に NUL を binary 扱いする [257-267](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/campaign/s8b_holdout_freeze.py:257)。`if NUL or decode failure: skip` という誤移植は、提案された10セルを通る。strict UTF-8 として有効な NUL-bearing control が必要。
  - `_INSIGHT_PATH_RE` は suffix を限定しない一方、matrix は `.py/.md/.json/.raw` だけである。`artifact_format in {"python","markdown","json","other"}` のときだけ skip する実装は通り、`.patch/.sh/.txt` で rc=2を残せる。既存分岐は [579-588](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:579)。
  - scope 外の非 UTF-8 blobを数える誤実装も、synthetic fixtureに scope 外の非 UTF-8 controlがないため通る。
  - 成果物影響: scoped `.sh/.txt/.patch` の受理集合、または root counter が裁定と異なる。

- [real / must-fix] `S=B`、すなわち選択された item が全件非 UTF-8 の境界がない。既存 base/control が必ず残るため、「skip後に `items` が空なら再び拒否する」変異が生き残る。これはプラン自身の `items=S\B` 契約 [158-162](/work/1/SFC/tanab/dev-wave-jobs/t407-ruleops-binary-blob/stage2b-plan.md:158) に反する。

  - 成果物影響: 全件非 UTF-8 の repo が裁定どおり受理されず、inventory の受理集合が狭いまま残る。

- [攻撃したが破れなかった] 新規テストは `tmp_path` repo、自前 bytes、自前 commitだけを使い、real probe hash・日時・実件数には依存しない。既存 `test_ruleops.py` は plain-runner allowlist 済み [README:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/README.md:136) なので、新規ファイル追加を伴わない本案は meta-test に抵触しない。

## 効く全層と整合

- [real] active consumer は `tools/ruleops.py` と `test_ruleops.py` に閉じている。`ruleops-inventory/v1` literal は [定義](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:25) 以外に無く、保存 inventory JSON・JSON Schema・shell consumer は見つからなかった。

  - ただし凍結された歴史材料には旧4-key shapeが焼き込まれている（[T-143 stage2 plan:43-48](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/output/insights/2026-07-29_t143-ruleops-wave/s2-plan.md:43)）。これは実 consumer ではなく履歴資料なので編集対象にしてはならない。
  - 成果物影響: v2 bumpで壊れる active consumer はない。歴史資料の参照内容だけが旧設計のまま残る。

- [real / must-fix] `docs/ruleops.md` は提案箇所以外にも修正が要る。

  - [36-38](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/docs/ruleops.md:36) は全対象について identity、last-change、markerを出すと読める。変更後は「retained itemだけ」に限定しないと嘘になる。
  - lifecycle の [152](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/docs/ruleops.md:152) は inventory/inspect で対象 metadataを採取できるとするが、skip pathは一覧に出ず、inspectは非 UTF-8 targetを拒否する [1006-1012](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:1006)。
  - 「既知限界」を `--kind test` だけに限定する [plan:194-196](/work/1/SFC/tanab/dev-wave-jobs/t407-ruleops-binary-blob/stage2b-plan.md:194) のは不足。まず全 kind について positive counter は一覧が不完全と書き、その上で test kind 固有の correctness 解釈を加える必要がある。
  - 成果物影響: 人間が `items` を対象全集合と解釈し、退役候補の受理・参照調査を誤る。

- [real / must-fix] D99 には追記が必要。D99(2) は対象を両族の tracked regular blob とする [4395-4399](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/docs/decisions.md:4395)。selection 自体は維持されるが、inventory item外延とschemaが変わるため、長期 interface 決定を運用文書だけに閉じてはいけない。

  追記内容は次の3行で足りる。

  > D99(2)追記: selection scopeは従来の二族を維持する。  
  > selectedのうちstrict UTF-8 decode不能なpath/itemだけをitemsから除外し、kind-filter後の件数をrootの`skipped_non_utf8`へ常時出す。pathは出さない。  
  > inventory schemaは`ruleops-inventory/v2`とし、inspect・ledger・receiptのfail-closed境界は変えない。

  - 成果物影響: 追記なしでは D99 の「対象」と v2 `items` の外延が二義化し、将来の人間裁定・consumer実装の参照が割れる。

- [攻撃したが破れなかった] 先例との粒度は整合する。先例も rel-path ごとに counter を増やす [318-343](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/campaign/s8b_holdout_freeze.py:318)。一方、先例の `skipped_binary_count` は NULまたはdecode失敗、かつ `search` object内 [345-375](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/campaign/s8b_holdout_freeze.py:345)。今回の名前は条件を狭く正確に表すため、docsで差を明記すれば人間を誤らせない。

## 親の実測と scope 裁定への反証

- [real] brief の「1,659件 / 40,345,708 bytesを scoped全体として走査」は過大一般化である（[brief:76-78](/work/1/SFC/tanab/dev-wave-jobs/t407-ruleops-binary-blob/brief.md:76)）。同じ `b1b1a12` に [_TEST_PATH_RE と _INSIGHT_PATH_RE](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:44) を適用した静的列挙では、1,659件/40,345,708 bytesは insight族だけだった。direct test 124件/4,648,588 bytesを足した全 scope は1,783件/44,994,296 bytesである。

  - ただし全1,783 pathのstrict走査でも非 UTF-8 は4件だけで、結論自体は破れなかった。
  - 成果物影響: 実装・synthetic期待値は実件数をpinしないため不変。briefの証拠母集団だけが誤っている。

- [攻撃したが破れなかった] `artifact_format` の値を読む production consumer は `_markers` のみ [622-639](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:622)。現テストは key存在しか見ない [53-57](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:53)。

- [攻撃したが破れなかった] activeな v1 pin consumerはゼロ。旧4-key shapeは歴史資料にあるが、機械 consumerではない。

- [攻撃したが破れなかった] 受入preflightは本当に `check` だけで、inventory call graphはない [540-552](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/run_tests.py:540)。

- [real / backlog] D63違反は親の指摘どおり存在する。対象testは直接 `xdist_group(name="real_repo")` を付ける [1709](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1709) 一方、D63はdecorator不使用・canonical `"real-repo"`を要求する [2406-2417](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/docs/decisions.md:2406)。収集監査も kwargsを見ず、args内の `"real-repo"` だけを抽出する [419-439](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_real_repo_serialization.py:419)。

  - T407の deterministic red原因ではないためコードscope外は維持できる。ただし [status before/after](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:1713) はwriterと競合し得るので、受入緑を並行干渉耐性の証拠にはできない。
  - 成果物影響: certified値は不変だが、受入runのpass/failがraceで反転し得る。

- [real / backlog] Git stderr、direct-test candidate decode、receipt負例欠如も実在する。

  - allowed rcのstderrを捨てる [359-365](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:359)。
  - direct candidateはblob pinだけでdecodeしない [2051-2065](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:2051) が、insightはdecodeする [1967-1972](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:1967)。
  - receiptはstrict decodeする [1307-1324](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/tools/ruleops.py:1307) が、既存非 UTF-8負例はledgerだけ [382-403](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/orchestrator/tests/test_ruleops.py:382)。
  - いずれも production ledger空の今回の受入preflightには到達せず、T407実装の必須条件にはならない。
  - 成果物影響: certified値は不変。将来の非空candidate package受理集合または診断境界だけが変わり得る。

- [real / must-fix] scope外候補のIDが衝突している。briefはD63所見をT-409、Git stderrをT-410とする [58-67](/work/1/SFC/tanab/dev-wave-jobs/t407-ruleops-binary-blob/brief.md:58) が、現行worklogではT-409がEVOLVE-BLOCK hole、T-410がsort integrity witnessに割当済み [1349-1356](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t407-ruleops-binary-blob/docs/worklog.md:1349)。

  - 成果物影響: そのまま起票するとタスク台帳の所有・参照が別問題へ誤接続される。

## must-fix (成果物影響つき)

1. [real] counter testを「ファイル追加」だけでなく、同一path・同一kind・同一suffixの内容を非 UTF-8↔UTF-8へ変更する差分検査へ直す。selected cardinalityを固定したまま count と membership が同時に変わることを要求する。

   - 成果物影響: payloadと無関係なcounterが通ると、inventoryの欠落件数が虚偽になる。

2. [real] strict条件の境界を追加する。最低限、UTF-8-only時のcount=0、strict UTF-8として有効なNUL-bearing itemの保持、scope外非 UTF-8を非加算、全 selected が非 UTF-8でもrc=0/items空/count=Nを固定する。suffix独立を主張するなら `.patch/.sh/.txt` branchも含める。

   - 成果物影響: inventoryの受理集合またはcountがユーザー裁定と異なる。

3. [real] `docs/ruleops.md` の retained-item限定と lifecycle不能条件を明記し、D99へ上記3行のinterface追記を入れる。

   - 成果物影響: 人間の退役候補受理集合・参照解釈がJSON実体と食い違う。

4. [real] scope外所見のT-409/T-410番号を再利用せず、記録時に新しいsemantic ID割当を受ける。

   - 成果物影響: canonicalタスク台帳の参照先が破損する。

## nit / backlog

- [real / nit] briefの1,659件という母集団はinsight族だけだった。非 UTF-8 4件という結論は独立全scope走査で維持されたため、実装blockerではない。

  - 成果物影響: 値・受理集合は不変。監査記録の精度だけが落ちる。

- [real / backlog] D63 canonical group違反、allowed-rc stderr、direct candidate decode非対称、receipt非 UTF-8負例は別waveへ送れる。ただしT-409/T-410は使用済みである。

  - 成果物影響: 今回のproduction ledger/certified成果は不変。将来packageまたはacceptance flakeへ効く。

- [real / nit] 歴史材料の旧4-key記述は残る。正本ではないため更新すると逆に過去計画を書き換える。

  - 成果物影響: active consumerは不変。歴史参照時だけv1設計であることを識別する必要がある。

## 攻撃したが破れなかった点

- root key更新後のreal assertion、`items`非空、`kind`全称は成立する。
- clone側にinventory実行はなく、inspect/checkは非 UTF-8 probe全件decodeへ到達しない。
- 受入preflightは`check`だけで、今回の変更面から独立している。
- 既存`build_inventory`テストのうち、追加root keyで修正が必要なのはプラン記載済みのexact-root testだけである。
- direct testの非 `.py` セルを作らない判断は正しい。
- mutation (a)(b)(c)(e)(f)(g)(h) は予定assertionで破れる。
- 新規テストはreal evidence、固定hash、日時、実件数に依存せず、plain-runner allowlistにも抵触しない。
- activeなv1 schema consumer・保存inventory JSONはない。
- 先例とのpath単位countは整合し、異なる名前は異なるskip条件を正確に示している。

## 総括

実装擬似コード自体は固定裁定を満たす。しかしプランはこのまま段4へ通せない。最大の穴は、`5/1/4 → 6/1/5` がcounterと実skipの因果を証明せず、NUL・scope外・全件skipの境界も固定していないこと。加えて運用正本/D99とタスクID衝突を閉じる必要がある。

read-only静的検査のみで、pytestは実行しておらず、緑は主張しない。