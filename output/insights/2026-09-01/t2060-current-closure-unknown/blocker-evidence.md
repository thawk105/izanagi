# 受入全走を止めている環境失効 — 親の実測

## 事象

[T-2060] wave の受入全走が赤で終わった。受領証は発行されていない。

```
21 error, 5 failed, 19043 passed, 67 skipped
```

**赤は全件 `orchestrator/tests/test_codex_reasoning_ab.py`** である。本 wave の編集面は
`orchestrator/campaign/artifact_admission.py` / `layer3_report.py` / `layer3_schema.json` /
`autonomous_trial_completeness.py` とそれらの test であり、接点は無い。

## 赤の本文 (junit.xml から抽出。署名でなく本文で判定した)

- `[error] x21` — `failed on setup with "codex_reasoning_ab_under_test.ValidationError:
  session 019fac6b-4f74-7a03-aa4d-8a9de22b352c rollout count is 0, expected 1"`
- `[failure] x4` — `FileNotFoundError: [Errno 2] No such file or directory:
  '/home/SFC/tanab/.codex/sessions/2026/07/29/rollout-2026-07-29T15-49-14-019faca2-6e1f-7601-bfc7-be27edcfb4ba.jsonl'`
- `[failure] x1` — `codex_reasoning_ab_under_test.ValidationError: session 019fac6b-... rollout count is 0, expected 1`
  (`test_m2_production_golden_requires_both_routes`)

## 依存の実体 (file:line)

- `orchestrator/tests/test_codex_reasoning_ab.py:128`
  `_HISTORICAL_SESSIONS = Path("/home/SFC/tanab/.codex/sessions")`
  — **repo 外のホーム配下を絶対 path で焼き込んでいる。**
- 同 `:3137-3140` `_REAL_ROLLOUT = _HISTORICAL_SESSIONS / "2026/07/29/rollout-2026-07-29T15-49-14-...jsonl"`
  — module 読み込み時に決まる定数。
- 同 `:788-789` module scope fixture `benchmark_snapshots` の先頭に
  `if not _HISTORICAL_SESSIONS.is_dir(): pytest.skip("historical rollout root is unavailable")`
  — **既に「使えなければ skip する」というガードが存在する。**
- 同 `:800`, `:817`, `:825` が `_prepare_snapshot_case` / `_derive_snapshot_from_base` /
  `render_prompt` へ `_HISTORICAL_SESSIONS` を渡す。
- 同 `:3140` `TOOL.derive_independent_golden(_ROOT, _HISTORICAL_SESSIONS)`。

## 環境の実測

- `/home/SFC/tanab/.codex/sessions/2026/` の直下は `08` と `09` **だけ**。`07` は存在しない。
- `/home/SFC/tanab/.codex/sessions/2026/` の mtime は **2026-09-01 00:54:20 JST**
  (directory の mtime は entry の追加削除で動くので、07 が消された時刻である)。
- 受入全走の投入は **2026-09-01 01:52 JST**、つまり削除の約 1 時間後である。
- `08` には 31 日分 (01〜31) が残っている。**保持は日ごとに失効が進む形である。**

## ここが要点

**既存ガードは粒度が合っていない。** `_HISTORICAL_SESSIONS.is_dir()` は root の有無しか見ない。
root (`.codex/sessions`) は 08 / 09 が残っているので**存在する**。したがってガードは発火せず、
その先で「参照している 2026-07-29 の記録が無い」ことによる setup error と FileNotFoundError になる。

## 契約上の制約

- 受入の赤の扱いの正本は `docs/dev-wave/operations.md` の `DW-O18`。
  逐語は `dw-o18.md` に射影した。**要点は「再赤・決定的赤は main 既存 F を証拠に
  Codex role=author が `orchestrator/tests/flaky_test_holds.py` へ登録する。F 不在は登録せず
  裁定送り」**である。
- `orchestrator/tests/flaky_test_holds.py` の `evidence_id` は `^F[0-9]+$` に限られ、
  `docs/failures.md` に実在する F を要求する。**本件に該当する既存 F は親の検索では見つからない。**
- 親はテストの弱体化、証拠なき hold 登録、決定的な赤への受入再走、受領証なしの land を
  いずれも行っていない。

## 影響範囲

**特定 wave の問題ではない。** 00:54 以降に受入全走を投げるすべての wave が同じ赤を受け取る。
今夜それ以前に着地した wave が緑だったのは、失効前だったためである。

## 検討中の選択肢 (親の暫定案。これ自体を検査対象とする)

1. **既存ガードの粒度を、実際に参照する記録の実在へ合わせる。** root ではなく
   `_REAL_ROLLOUT` と各 case が要求する session の実在を見て、無ければ skip する。
   ガードの意図 (`historical rollout root is unavailable` で skip する) は既に在り、
   粒度だけが合っていない、という読み。
2. **`flaky_test_holds.py` へ hold 登録する。** 契約が要求する既存 F が無いため例外が要る。
3. **失効した記録を人手で復元する。** repo 外のホーム配下の実データであり AI からは触れない。
