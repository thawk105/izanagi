---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-20
wave: worktree-dev-wave-t1431-floor-measurement
seq: 1
---

## 新規

### {{F:source-digest-mocc-supplied-macro-gap}}. source_digest.py が mocc protocol の実供給マクロを認識せず床値実測がbuild段階で全滅した [ドリフト] [テスト代表性]

- 事象: [T-1431] (2026-08-20) の床値pilot実測で、`s8b_floor_campaign.py` driver が
  `build_cells` → `prepare_cell` (`orchestrator/campaign/s1_direct_comparison.py:716`) →
  `source_digest.resolve()` → `assert_conditional_macros_covered()`
  (`orchestrator/campaign/source_digest.py:557`) で `RuntimeError` を投げ、投入45秒で
  rc=1 終了した。`cc/mocc/transaction.cc` の条件指令が参照する `MQLOCK`/`RWLOCK`/
  `TEMPERATURE_RESET_OPT` が「実TU供給マクロ・先行する#define・CONTEXT_MACROS・builtinの
  いずれでもない」と判定され、fails-closed で停止した (T-148 の設計どおりの挙動、
  ガード自体は正しく発火した)。stock_configuration (LLM変異を含まない基準構成) で発生した。
- 根本原因: `source_digest.py` の `parse_supplied_macros()` (269-291行) は
  `_SUPPLY_RE = re.compile(r"(\w+)=\$\{CCBENCH_(\w+)\}")` という正規表現だけで実TU供給
  マクロ集合を静的抽出する。`external/ccbench/cc/mocc/CMakeLists.txt` の
  `OPTIONS` は `RWLOCK` (裸オプション、`=${CCBENCH_...}` を伴わない) と
  `TEMPERATURE_RESET_OPT=${CCBENCH_TEMPERATURE_RESET_OPT}` (形式上マッチするはず) を含むが、
  両方とも「未知」と判定された。前者は正規表現の構造的な非対応、後者は
  `parse_supplied_macros(options_text, protocol_cmake_text)` へ渡る `protocol_cmake_text`
  自体が mocc の CMakeLists.txt を指していない疑いが強い (呼出し元の特定は未実施、
  一次資料未確認)。ccbench 側のソース/CMakeLists 構造 (または mocc protocol が
  `source_digest.py` の想定パーサ形式に一度も適合しないまま存在し続けていた状態) と
  `source_digest.py` のパーサ実装の drift が原因。`MQLOCK` は現行
  `cc/mocc/CMakeLists.txt` の OPTIONS に存在せず (grep で確認、ccbench 全体でも
  `-DMQLOCK` を注入する経路なし)、現行ビルド設定では死コードの可能性が高い
  (transaction.cc:635-637 のコメントが RWLOCK/MQLOCK を排他的な選択肢として扱っている
  ことを示唆)。
- 検出: [T-1431] の床値pilot実投入 (request 926261.nqsv) で偶然発見した。`test_s8b_floor_campaign.py`
  等の既存テストはこの経路を実exercise していない — `docs/phase3-8b-restart-runbook.md` §1 の
  「実ビルド canary 3本。cmake/gcc-13/g++-13/nm が揃わないと skip し、Pegasus には
  g++-13 が無い…実ビルド経路はこの緑に含まれない」が同じ穴を既に指摘していたが、
  `source_digest.resolve()` 自体の macro-supply 解決が対象だとは特定されていなかった。
- 恒久対応: {{T:fix-source-digest-mocc-supplied-macros}} で (1) `protocol_cmake_text` の
  実体を呼出し元まで遡って確認、(2) 裸オプションの扱い方針を設計 (単純な正規表現緩和で
  「実TU供給集合」の正確性を保てるか要検証)、(3) MQLOCK 死コード判定の確定、(4) mocc
  (または全protocol) に対する `source_digest.resolve()` の実運用相当テストを追加
  ([テスト代表性] gap の再発防止) の4点を行う。未着手 (2026-08-20 時点)。
- 再発検知: 現状は lint 化なし。(4) の実運用相当テストが追加されれば、mocc protocol への
  今後の変更が CI/受入で自動検知される。それまでは Pegasus 実機での床値/s8b系campaign
  投入時に同じ traceback (`assert_conditional_macros_covered` からの RuntimeError) が
  出た時点で顕在化する。
