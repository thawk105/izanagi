---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-19
wave: dev-wave-t1355-c04-c07-decider-bump
seq: 3
---

## 新規

### {{F:mutation-xdist-group-node-id}}. 変異 harness が `xdist_group` 付きテストの node ID を扱えない [手順漏れ]

- 事象: `tools/mutation_harness.py` の変異事前登録で、`@pytest.mark.xdist_group(name=...)` 付き
  テスト2件 (`test_candidate_freeze_matches_contract_and_generation_chain`,
  `test_repository_tip_binds_current_decider_version_without_activation`) の `expected_nodes` を
  どちらの形式で書いても一致しなかった。素の node ID (`path::test_name`) は harness の
  collection-preflight (`--collect-only` 出力を解析) を通るが、実行結果 (`_failed_nodes` が
  parse する pytest 標準の "FAILED " summary 行) はこの2件に限り
  `path::test_name@<xdist_group名>` の形式で報告される。pytest-xdist の `loadgroup` scheduler が
  実行時のみ group suffix を付与するため (collection 単独では xdist 分散が発生せず scheduler が
  "serial" になり suffix が出ない)、`_normalize_node` (単純なパス正規化のみ、suffix は非対応) を
  介しても一致する単一の文字列表現が存在しない。
- 根本原因: `tools/mutation_harness.py` の node ID 正規化が pytest-xdist の `loadgroup`
  scheduler 固有の実行時 suffix 付与を考慮していない。collection フェーズと実行フェーズで
  同一テストの報告形式が変わりうるという前提が harness に欠けている。
- 恒久対応: 未実装 (harness 自体の改修は本 wave の scope 外)。本 wave は runner argv へ
  `--deselect "<path>::<test>"` でこの2 test を mutation harness の実行対象から個別に除外する
  workaround で回避した (この2 test は統合 commit 後の焦点走で別途緑を確認済み、wave 全体の
  カバレッジからは除外していない)。
- 再発検知: 未実装。`@CANDIDATE_XDIST_GROUP` (または同種の `xdist_group` marker) を持つテストを
  変異 harness の対象に含める次の wave が、同じ collection/実行の representation gap を踏む
  可能性が高い。恒久対応としては `_normalize_node` に xdist group suffix の除去を追加するのが
  妥当と考えられるが、本 wave では実装しなかった。

## 再発

### F37

- **再発: 2026-08-19** — 親が統合 commit 後の `check_ai_provenance.py` full-history 監査を
  `python3 tools/check_ai_provenance.py 2>&1 | tail -40; echo "RC=$?"` で投げ、報告された
  exit code 0 が `tail` のものだった (真の rc=1、新規違反1件を看過)。統合 commit の AI-Agent
  trailer 不備 (`role=author` が2製品にまたがるのに一方に `scope` が無い) を一時的に見逃したが、
  後続の別目的の再監査でパイプを外し `; echo $?` で直接確認したところ真の rc=1 に気づき、是正
  (`git reset --hard` → amend → merge 再実行) した。誤った trailer が main へ着地することはなく、
  偽緑の実害は無かった (near miss)。恒久対応は F37 既存のとおり変わらない。
