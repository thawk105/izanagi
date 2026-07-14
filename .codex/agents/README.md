# Codex custom agent adapter

`.claude/agents/*.md` の role 本文を意味契約の正本とし、Codex で安全側に近似できる
role だけを、このディレクトリの TOML profile として有効化する。同期と分類の機械的な正本は
`tools/check_codex_agents.py`、設計判断は D54。

project の `.codex` layer を信頼した Codex client で読み込む。定義を追加・更新した後は新しい
session で role 名と設定を確認してから使う。

## 有効化する初期集合

| role | model | reasoning | sandbox | 用途上の条件 |
|---|---|---|---|---|
| `auditor` | `gpt-5.6-sol` | high | read-only | 元の人間 gate と併用。D38 と同等の Bash 非付与ではない |
| `critic` | `gpt-5.6-sol` | high | read-only | digest だけを呼出側から渡す |
| `verifier` | `gpt-5.6-sol` | high | read-only | trace だけを呼出側から渡す |

いずれも**起動直前に親 turn の実効 sandbox を read-only にし**、毎回 `fork_turns="none"` で
起動する。子も開始時に実効 read-only を確認し、確認不能・不一致なら `ADAPTER-REFUSED` で停止する。
workspace-write / danger-full-access の親からは起動しない。Codex profile には fresh context や
tool allowlist のフィールドがなく、`read-only` は書込みを止めるだけで読取面や Bash 面を
Claude と同じ形にはできない。親 turn の live permission override が profile より優先される
場合もあるため、研究上の証拠に単独採用しない。

root `AGENTS.md` の通常ブートは親の担当であり、この 3 role の子は CLAUDE/worklog/phase/handoff を
読まない。auditor は明示した監査射影、critic は inline digest、verifier は明示した trace と
検査コードだけを扱う。とくに critic は共有 role 本文にある `digest.py` 自走許可を使わない。

## fail-closed で保留する role

- `axis-proposer` / `planner-v4` / `coder-v4-autonomous*`: `tools: []` による
  file-read 経路不存在と Model Y のリーク遮断を再現できない。
- `coder`: EVOLVE-BLOCK の合成枝だけに編集面を限定できない。
- `critic-experiment`: `guided.py` だけを許す Bash-only の実験境界を再現できない。
- `calibrator` / `profiler`: 書込みが必要だが、成果物の宛先だけに write 面を限定できない。

これらは専用 harness/API 境界ができるまで `.codex/agents/*.toml` を作らない。置くと Codex が
発見可能になるため、checker は存在そのものを拒否する。

## 更新手順

1. role の意味変更は対応する `.claude/agents/*.md` へ入れる。
2. `python3 tools/check_codex_agents.py --write` で対応 profile を再生成する。
3. `python3 tools/check_codex_agents.py` と
   `python3 orchestrator/tests/test_codex_agents.py` を通す。

Python 3.10 で checker を動かす場合は TOML round-trip 検査用の `tomli` が必要。Python 3.11
以降は標準 `tomllib` を使う。parser がなければ checker は検査を省略せず失敗する。

Codex の自動移行に依存しない。Claude の `model: opus|sonnet` と `tools` 制限は Codex TOMLへ
同値に移らず、`#` を含む未引用 YAML description も移行時に切断され得るためである。
