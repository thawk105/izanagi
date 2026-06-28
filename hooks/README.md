# hooks — 機械的防壁 (Python)

絶対規律1・2 を書き込み時点で機械執行する最小限の hook。auditor の事後監査に加えた第二防壁。

ECC のように大量の hook は持たない。下記2つだけ。

> **⚠ 実装ステータス: 未実装 (placeholder)。`.claude/settings.json` の PreToolUse/PostToolUse 配線は 0 件。**
> CLAUDE.md「hooks」節はこの2防壁を前提に書かれているが、実体はまだ無い (Phase 1 完了監査 2026-06-28 で明示)。
> **段階導入 (規律5) として Phase 3 (LLM が C++ variant を生成する) の着手直前に実体化する。** 現 Phase 1-2 は
> variant が**ビルド時フラグの組合せのみ**でコード変異が無いため、`#ifdef TRACE` 越境も verifier 迂回も構造的に
> 起こらず、第二防壁が空でも実害はない (規律1 はソース層の `#if TRACE` + buildcache の symbol assert、規律2 は
> verifier の最下層 indeterminate + pipeline の fails-closed が一次防壁として効いている)。LLM がコードを書く瞬間に
> 初めてこの第二防壁が load-bearing になる。

## hook 1: 観測者効果違反の検出

variant コードが `#ifdef TRACE` の外に検証専用メタデータを書こうとしたら警告する。CC のデータ構造に trace 専用フィールドが常駐しようとしていないかチェックする。

→ 絶対規律1 (観測者効果の分離) の執行。

## hook 2: verifier 迂回の阻止

verifier を経由せずに性能数値だけを更新しようとしたら止める。正しさゲートを通さずに variant を「採用」状態にしようとしたら止める。

→ 絶対規律2 (正しさゲートを緩める変異を許さない) の執行。

## 実装メモ

- Python で実装する (orchestrator と言語を揃え、依存を増やさないため)
- Claude Code の hook 設定で PreToolUse / PostToolUse に紐付ける
- 具体的な配線 (どのファイルパターンで発火するか等) は Phase 1 タスク1 以降、CCBench のビルド構成と trace-hook の場所が固まってから詰める

現時点ではプレースホルダ。CCBench 解剖 (Phase 1 タスク0) と trace-hook 実装 (タスク1) の後に具体化する。
