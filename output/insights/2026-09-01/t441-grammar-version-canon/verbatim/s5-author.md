## 現行挙動

実装前は、`20`、`20.0`、`1e2`、`001`、`0x14`、`024`、`0b10100`、`2'0`、`0x1.4p4`、`0xFF` を既存13段で受理しますが、材料化 source は raw 表記のままでした。`double now_backoff = 20; (void)0;` は従来どおり `statement-count.v1` で拒否されます。

## 実装した変更

- [backoff_hole_grammar.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-author/orchestrator/campaign/backoff_hole_grammar.py:47)
  - `BACKOFF_GRAMMAR_VERSION = 1` と共有 key を追加。
  - 13段通過後だけ十進整数1文へ変換する canonicalizer を追加。拒否規則と `.v1` rule ID は不変です。

- [p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-author/orchestrator/campaign/p3_s4_loop.py:225)
  - quarantine の受理後に canonical source/diff を再材料化。
  - config/module 版の exact gate、campaign config への版注入、reject identity の版束縛を追加。
  - duplicate reader を `_validate_attempt_topology()` に接続。拒否候補の raw 表記正準化（R-12）は実装していません。
  - 禁止された import block は未編集です。

- [loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-author/orchestrator/campaign/loop.py:238)、[pipeline.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-author/orchestrator/campaign/pipeline.py:880)、[source_digest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-author/orchestrator/campaign/source_digest.py:2108)
  - campaign 由来の版を keyword-only で伝播。
  - 非-stock token を `grammar + raw source digest` で domain separation。stock は `"stock"` のままです。

- [buildcache.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-author/orchestrator/campaign/buildcache.py:2860)
  - build 出口の SourceEvidence 再照合にも同じ版を伝播。
  - legacy/v2 cache pre-image自体は変更せず、bound tokenを既存 `src` / `src_token` に使用します。旧key fallbackは追加していません。

- [wal.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-author/orchestrator/campaign/wal.py:618)
  - versioned lock配下の `BUILD_START` のみに版を記録。
  - 欠落・異値検査を `_validate_attempt_topology()` 内へ配置。版keyのないlegacy lock/WALは不変です。

- [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-author/orchestrator/tests/test_p3_s4_loop.py:159)
  - legacy/versioned lock fixtureを分離。
  - R-1〜R-11の正例・負例、raw digest非alias、legacy/v2 cache分離、WAL writer/reader/duplicate、`value=20 → raw 0x14 → source 20 → BACKOFF_FIXED=20` を追加。
  - `buildcache` はテスト内local importです。top-level import群は未編集です。
  - R-5で許可された4 campaign IDだけ更新しました。

docs、指定された歴史固定値、既存期待値は変更していません。commit/add/pushも未実施です。

## 呼び出し規約の変更

- `run_campaign`、`pipeline.evaluate`、`resolve_evidence`、`resolve`、`src_token` に keyword-only・既定 `None` を追加しました。
- AST集計では `run_campaign` の実callは73件／23 files。productionのp3 callと負例テストだけが版を明示し、他は既定経路です。
- `resolve_evidence` は28実call／23 files、文字列出現43件でHEADから件数不変。`source_digest.resolve(...)` は35件でHEADから不変です。
- 既定経路は conditional kwargs、`bind(raw, None) == raw`、stock先行判定、legacy WAL exact-byteテスト維持によりbytes不変と確認しました。

## 実走した検査

- `python3 -m py_compile`：変更した7 code filesと2 test files、exit 0。
- `git diff --check`：exit 0。
- pure diagnosticで全10受理表記の十進正準形、`statement-count.v1` の固定拒否、`None` token不変を確認。
- 規定 runnerによる以下のpytestは実走できていません。
  - `test_p3_s4_loop.py::test_quarantine_passes_clean_backoff_value`
  - 新設12テストを選ぶ `test_p3_s4_loop.py -k ...`
  - いずれも Pegasus dispatch前検査の `qstat -Q` 失敗、rc=16、`child_started=false`。緑とは申告しません。

## meta-test の洗い出し

新規test fileや改名はなく、plain-runnerのfile集合・命名登録は不変です。新規nodeidに波及するのは [test_acceptance_schedule_order.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t441-author/orchestrator/tests/test_acceptance_schedule_order.py:660) のduration-ledger 90% coverage検査です。ledgerは網羅表ではなく、追加12 nodeidで閾値を割る可能性は低いものの、runner障害により未実走です。

flaky/growth hold検査は登録済nodeidの欠落を検査する面で、新規nodeid追加には登録更新不要と静的確認しました。

## 波及可能性

- `run_campaign`、`pipeline.evaluate`、source resolver、`build/build_v2` の所有外callerは既定 `None` のままです。
- `backoff_extended_sweep`、`b10_backoff_shape_sweep` など同じpathを触る別producerは版を渡さないため、identity/cacheは変わりません。
- `artifact_admission` は既存の `_validate_attempt_topology()` 呼出しからversioned WAL欠落を拒否します。
- shared `_critic_view()` は明示legacy lock、production-shapedテストは版ありlockをWALより先にseedします。
- criticはbound `src_token`をopaqueに消費します。歴史artifact、overlay ledger、backoff-sweep ID、golden SHAは未変更です。

## 赤の内訳

実pytestの赤は観測していません。child未起動のためです。

ただし静的に、既存 `test_quarantine_passes_clean_backoff_value` の「返却 `edited_text` に `20.0` が残る」という期待は、R-1の「受理後に `20` へ正準材料化」と直接衝突します。既存期待値の編集は禁止されているため触っていません。予見されるfinding集合はこの1 nodeidです。

また、指定された親 `.claude/worktrees/dev-wave-t441-grammar-version-canon` はsandboxで書込み拒否されたためcleanのままです。変更はdispatch環境の書込み可能な `.codex/worktrees/t441-author` にあります。

## 総括

R-1〜R-11のコードとテストをauthor worktreeへ実装しました。  
受理・拒否集合と固定rule bytesは維持し、accepted sourceだけを正準化しています。  
版はcampaign、reject identity、source/cache、WALへ同じ値を束縛します。  
静的検査は通過しましたが、pytestはPegasus障害のため未実走です。  
既存1 nodeidと正準化裁定の期待値衝突、および親worktree未反映が残件です。