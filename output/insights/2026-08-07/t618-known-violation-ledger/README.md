# [T-618] 既知違反台帳へ `3f2c43d7` を注記つきで追加した — dev-wave 逐語凍結

wave: `dev-wave-t618-provenance-known-ledger` / branch `worktree-dev-wave-t618-provenance-known-ledger`
起点 local main `bb824d8b` / 実装 commit `2327210a` / merge commit `4fc48604`

この README は本 wave の**結論と実測値**を持ち、各段の生成物は `verbatim/` と本ディレクトリ直下へ
逐語で凍結してある。可変状態 (次の一手、未了項目) の正本は `docs/worklog.md` であって本書ではない。

## 何を決めて何をしたか

ユーザー裁定 (worklog 293、2026-08-07 /rulings 第 3 回、択 (b)) に従い、
`3f2c43d7580b8c26724d90278589862057508965` を `tools/check_ai_provenance.py` の
`KNOWN_PROVENANCE_VIOLATIONS` へ 7 件目 (`missing-ai-agent`) として注記つきで追加した。
履歴は書き換えていない。台帳 schema を 3 要素から 4 要素へ拡張した設計判断は、本 wave の
decisions fragment (slug `known-violation-note-field`) に置いた。D 番号は land 時の fold が採る。

## 裁定の前提を一次資料で確認した

`3f2c43d7` の commit message は次の形である (`git log -1 --format=%B … | cat -A` で確認)。

```text
AI-Agent: product=claude; model=claude-opus-5-1m; reasoning=default; role=manager; scope=t503-disposable-worktree$
$
Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>$
```

`git log -1 --format='%(trailers)'` が返すのは `Co-Authored-By:` 行だけである。間の空行によって
`AI-Agent:` 行が最終 trailer block から切り離されている。一方その `AI-Agent:` 行の payload は
`docs/ai-provenance.md` の必須形式を満たす。**帰属の欠落ではなく書式の崩れ**という裁定の前提は成立した。
変更 path は 3 件とも `.md` (docs/spool の fragment と insights README) で docs-only のため、
Codex author 契約 (D95) の対象外であり `missing-codex-author` は立たない。
段 3 レンズ 1 が独立に同じ検証を行い同じ結論に達した (`verbatim/s3-lens1-correctness.md` の refuted 1・2)。

## 実測値

| 測定 | 対象 commit | 結果 |
|---|---|---|
| 既定 full 監査 (台帳追加前) | `bb824d8b` | 1702 件中 **新規 1 / 既知 6 / rc=1**。新規は `3f2c43d7580b` の `missing-ai-agent` 1 件のみ |
| 既定 full 監査 (実装後) | `2327210a` | 1703 件・**新規違反なし / 既知 7 / rc=0** |
| 既定 full 監査 (main 取り込み後) | `4fc48604` | 1713 件・**新規違反なし / 既知 7 / rc=0** |
| 対象テストファイル単走 | `2327210a` | 238 passed / rc=0 (計算ノード) |
| 変異 baseline (正例 control) | `2327210a` | 238 passed / rc=0 |
| 変異 matrix | `2327210a` | **5/5 KILLED**、観測 node が事前登録と完全一致 |
| 受入全走 | `4fc48604` | **7177 passed / 20 skipped / rc=0** (18 分 15 秒、計算ノード) |

実装後の stdout に出る 7 件目の行は次のとおりである。

```text
check_ai_provenance: known-violation sha=3f2c43d7580b8c26724d90278589862057508965 finding=missing-ai-agent note=trailer は本文に実在するが、AI-Agent 行と Co-Authored-By 行の間の空行で trailer block 不成立
```

**`known-violations=7` 付きの rc=0 を緑と読んではならない** (`PR-A02`)。この規範は機械化されていない
— 下の「未解決」を参照。

## 段 3・段 6 が実際に変えたこと

段 2 のプランは概ね妥当だったが、**段 3 レンズ 2 が本 wave で最も価値のある 2 件**を出した。

1. **rc=1 側だけ検証されない穴。** プランは注記の stdout を rc=0 側でしか pin しておらず、
   rc=1 側の出力ループだけ旧 formatter のまま残しても計画どおりのテストが素通りする状態だった。
   裁定で rc=1 合成テスト (既知 1 件 + 新規 1 件を同一 range に置く) を追加し、その穴を狙う変異 M3 を
   事前登録した。本走で **M3 は新設テスト 1 本だけを赤にして KILLED** になり、穴が塞がったことを
   変異で裏取りできた。
2. **改行拒否の contract とテストの食い違い。** プランは「LF・CR・Unicode line separator を一括拒否」と
   書きながら LF 1 例しか pin していなかった。実装を `"\n" in note` へ弱めてもそのテストは
   識別できない。裁定で 5 case の parametrize にし、変異 M5 (改行検査だけ削除) が
   **改行 4 case だけを赤にし `non-str` は型検査に救われて緑のまま**という予測どおりの切れ方を実測した。

段 6 のレビュー 2 本は code の must-fix ゼロだった。裁定が固定した注記逐語・ruling・guard の
predicate と位置、`_KNOWN_VIOLATION_RULING` と `_known_spec()` の未変更、既存 stdout テストの
未変更を AST 比較で確認している (`verbatim/s6-review2-integration.md` の一致表)。
**所見ゼロは変異で裏取りするまで緑と数えない**規約に従い、変異 5 本を本走してから閉じた。

## 変異事前登録と本走結果

spec は `mutation-spec.json`、台帳は `mutation-ledger.json` (repo_head `2327210a`、
runner mode `dispatch`)。

| ID | 変異 | 結果 | 観測された赤 node |
|---|---|---|---|
| M1 | 台帳 7 件目 entry を削除 | KILLED | 事前登録の 4 本ちょうど |
| M2 | `_known_violation_line()` の note suffix を無条件に落とす | KILLED | rc=0 側・rc=1 側の 2 本 |
| M3 | **rc=1 側の出力ループだけ** helper を迂回し旧式で出す | KILLED | 新設 rc=1 テスト **1 本のみ** |
| M4 | note guard 2 本 (型 + 改行) をまとめて削除 | KILLED | `test_broken_registry_note_is_rc2` の 5 case すべて |
| M5 | 改行検査**だけ**を削除 | KILLED | 改行 4 case のみ (`non-str` は型検査に救われ緑) |

**登録から外した候補と理由** (`DW-M01` の「単一理由性を確認できなければ登録しない」に従う)。

- **型検査だけを削除** — `note=None` で改行 predicate が `None.splitlines()` を呼び `AttributeError`
  になる。`main()` の `except` は `(OSError, RuntimeError, UnicodeError)` だけを捕捉する
  (`tools/check_ai_provenance.py` の当該 except 節を親が実読して確認) ため例外は素通りし、
  fail-closed のまま受理集合が変わらない。診断だけの赤は kill にしないため M4 へ吸収した。
- **SHA drift** — registry validator (full SHA / 重複) が先に rc=2 にするため、変異が台帳照合層へ届かない。
- **stale raise 削除** — 本 wave の差分でない既存層で、同じ層を 5 本の既存 node が要求する。
  本 wave の検出力を測らない。
- **`note` 既定値を非空へ変更** — 既存 6 entry と 13 箇所の `_known_spec()` 呼び出しへ同時に波及し、
  赤理由が分散する。

M1 は当初「単独帰属する」と提案されたが、段 3 レンズ 2 が 4 経路の同時不成立を指摘したため、
単独帰属の主張を撤回して integration 変異として期待 node 4 本を全列挙した。

## 過去記録の supersede

次の 2 つは**書き換えない**。worklog(293) の再裁定によって運用状態が置き換わったことを、
本 wave の worklog エントリで記録する。

- `docs/worklog.md` (289) の「7 件目 `3f2c43d7` は台帳に入れなかった。実装後も既定監査は
  既知 6 / 新規 1 / rc=1 のまま残る。これは設計どおりの期待値であって緑ではない」
- `output/insights/2026-08-07_t614-known-violation-ledger/README.md` の同じ観測

以後「既定監査の赤を手で 1 件差し引く」運用は不要である。

## 未解決 (本 wave の scope 外、いずれも既起票)

- **[T-621]** — 自動 dev-wave 層 (`tools/dev_waves/cli.py` → `tools/dev_waves/checker.py` →
  `tools/task_run_check.py`) は checker の stdout/stderr を捨てて rc だけで pass を決める。
  `PR-A02` の「`known-violations=N` 付きの rc=0 を緑と読むな」は機械化されていない。
  結果として、自動 receipt からは「どの 7 SHA を、どの注記で既知扱いしたか」を復元できない。
  **このため本 wave の受入証拠には自動 receipt を使わず、post-commit の権威 full 監査の生 stdout を
  採った。**
- **[T-619]** — 既定監査の範囲が `--ancestry-path` であるため、policy 導入前から分岐した branch 上の
  違反 commit を後日 merge すると既定監査から落ちる。本 wave の tip では plain range と
  ancestry-path がともに同数で no-op だが、範囲式の変更は brief が明示的に scope 外にしている。

## 凍結物

| ファイル | 内容 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief (scope、不変条件、provisional 裁定 (P1)〜(P4)、成果物影響) |
| `verbatim/s2-plan.md` | 段 2 codex プラン (file:line 粒度) |
| `verbatim/s3-lens1-correctness.md` | 段 3 敵対レンズ 1 (正しさ境界) |
| `verbatim/s3-lens2-integration.md` | 段 3 敵対レンズ 2 (整合・実効性・層の網羅) |
| `s4-adjudication.md` | 段 4 裁定 (所見の裁定表、plan v2、gate 署名と正例、変異事前登録) |
| `verbatim/s5-implementation.md` | 段 5 実装子 (Codex role=author) の完了報告 |
| `verbatim/s6-review1-correctness.md` | 段 6 敵対レビュー 1 (正しさ防壁・reward hack) |
| `verbatim/s6-review2-integration.md` | 段 6 敵対レビュー 2 (裁定適合・層の網羅・陳腐化) |
| `mutation-spec.json` | 変異事前登録 spec (`spec_sha256` は台帳側に記録) |
| `mutation-ledger.json` | 変異本走の台帳 (baseline 含む) |
