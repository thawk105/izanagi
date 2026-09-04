# T-2111 沈黙防壁の復帰 — 変異による実効性の実証

歴史 corpus 消失で沈黙していた `orchestrator/tests/test_codex_reasoning_ab.py` の防壁 24 node を
合成入力で復帰させた変更について、**復帰した検査が実際に production の欠陥を捕まえるか**を
変異で測った記録。

## 何を測ったか

10 の変異はすべて `tools/codex_reasoning_ab.py` の防壁述語を壊す。復帰した test がそれぞれを
検出できるかを見る。同じ spec を**変更後と変更前の両方**に当て、検出力の差を出した
(`DW-M08` の新旧両走)。`tools/codex_reasoning_ab.py` は両 commit で byte 一致なので、
差は test 側だけに由来する。

## 結果

| | 旧側 `adec65e56` (変更前) | 新側 `31d5e336b` (変更後) |
|---|---|---|
| baseline | PASSED (rc=0, 52.604s) | PASSED (rc=0, 93.629s) |
| KILLED | 0 | **10** |
| SURVIVED (見逃し) | **8** | 0 |
| 部分検出 | 2 | 0 |
| 期待 node 完全一致 | — | 10 / 10 |

**変更前は、防壁を壊す 10 通りのうち 8 通りがテストを素通りしていた。** 残る 2 通りも
部分的にしか捕まらず、復帰した test がそれぞれ 1 node ずつ検出力を足している
(`test_m1_snapshot_head_pin_is_independent`、
`test_material_replay_rejects_task_manifest_exchange_at_digest_consumers`)。

## erratum — 初回 probe で外した 2 件 (`DW-M02`、消さずに残す)

- `MUT-T2111-GIT-ENV-SCRUB-GUARD` は **SURVIVED**。supervisor 側の
  `if any(key.startswith("GIT_") ...)` は**冗長 gate**で、洗浄自体は `_clean_environment` の
  `ENV_ALLOWLIST` が構造的に担っている。単独変異の証拠から外し、実効 gate へ再照準した。
- `MUT-T2111-SCHEDULE-MANIFEST-DIGEST` は復帰 node ではなく既存の
  `test_m15_supervise_pair_rejects_schedule_manifest_exchange` に先に捕まった (**他層の mask**)。

再照準後 (`t2111-mutation-spec-probe2.json`) は両方とも狙いの復帰 node を殺した。
前者は 3 層同時変異 (additions への `GIT_DIR` 注入 + `_clean_environment` の除去条件反転 +
supervisor 関門の無効化)、後者は `_require_task_manifest_sha256` の不一致枝そのもの。

## 置換数の変異が示すこと

`MUT-T2111-PROMPT-REPLACEMENT-COUNT` は `[0]` と `[10]` だけを殺し、正例 `[9]` を殺さない。
**負例だけが落ちる**のが正しい挙動で、合成 fixture の下でも正例が恒真になっていないことの裏付け。

## 走らせ方

初期化済みの固定 commit checkout に対して
`python3 tools/mutation_harness.py --repo . --runner-mode dispatch --detached`、
runner argv は `python3 tools/run_tests.py --force-dispatch orchestrator/tests/test_codex_reasoning_ab.py -p no:randomly -q -rf`。
wave の作業ツリーは一度も変異させていない。

使い捨て container は submodule を再帰初期化しないため、初回の baseline は
`submodule is not initialized: external/ccbench/third_party/shirakami` で赤になった。
`--resume` は記録済みの赤 baseline を再走しないので回復せず、初期化済み checkout へ
新しい `--out` で当て直した。

## この記録が保証しないこと

- 変異は列挙であって網羅ではない。10 通り以外の壊し方は測っていない。
- 復帰した経路では期待値を入力と同じ処理から作るため、**歴史内容に対する独立 oracle ではなく
  自己整合性検査へ縮退している。** 失われるのは D1382 が「復元しない」と定めた歴史 anchor の
  主題であり、防壁の主題ではない (段 6 の敵対レビューが全箇所を二分して確認)。
- 所要は測った checkout に束縛される。同じ入口 (`tools/run_tests.py`) で揃えた焦点走は
  変更前 16.06 秒 / 変更後 59.26 秒。dispatch 経由の baseline 値 (52.604s / 93.629s) とは
  母数が違うので混ぜない。

## ファイル

- `t2111-mutation-spec-final.json` — 本走 spec (期待 KILLED、期待 node は完全集合)
- `t2111-mutation-spec-old.json` — 旧側の観測用 spec (全件 SURVIVED 登録で観測 node を集める)
- `t2111-mutation-spec-probe.json` — 初回 probe spec (erratum の対象)
- `t2111-mutation-spec-probe2.json` — 再照準 probe spec
- `results-summary.json` — 4 走の baseline・summary・変異ごとの status と失敗 node
