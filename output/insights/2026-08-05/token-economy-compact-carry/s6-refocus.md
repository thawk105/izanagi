## 総括

**GO**。must-fix は 0 件。  
8 所見は **closed 7 / partial 1 / regressed 0**。  
partial はレビュー A NIT-1 の到達不能 guard のみで、成果物影響なしの nit。  
親実測は 366 passed / 0 failed・`check_docs.py` 違反なし。こちらでは pytest を実行していない。

## 所見ごとの対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| A MF-1 — M08 が kill 不能 | **closed** | regex の冗長な `$` が除かれ、`fullmatch` は維持。[spool_fold.py:1151](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1151)。複数行入力で `fullmatch` と `match` の挙動が分かれ、[test_spool_fold.py:764](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:764) が M08 を kill する。 |
| A NIT-1 — ordinal 排他 branch が到達不能 | **partial (nit)** | 将来の regex 改変用 guard と明記されたが、現 regex では依然ちょうど一方の capture だけが非 `None` となり、条件は到達不能。[spool_fold.py:1166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1166)。現受理集合・成果物への影響はない。 |
| A NIT-2 — legacy 未来参照テストなし | **closed** | current `(2)` から archive `(3)` を指す旧書式負例を追加し、共通の過去参照 gate まで固定。[test_spool_fold.py:697](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:697)、[spool_fold.py:1181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1181)。 |
| B MF-1 — tail-only reader が compact stub を解釈不能 | **closed** | producer が全新規見出しへ固定凡例を付ける。[spool_fold.py:1386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1386)。凡例と carry は byte-exact test で固定され、見出しに T-ID がないことも検査。[test_spool_fold.py:554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:554)。 |
| B MF-2 — `prior_ordinal` 契約と正本が曖昧 | **closed** | 描画済み書式の正本、N の意味、初回=current tail、同一 fold 後続=直前生成、`ordinal-1`/global max 導出禁止まで一意化。[worklog.md:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/worklog.md:16)、[worklog.md:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/worklog.md:27)、[spool/README.md:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/spool/README.md:86)。 |
| B MF-3 — D70 rotation fixture が非発火 | **closed** | entry (1) を増量し、entry (2) を短縮。rotation、current `<=320`、archive が元 entry (1) の exact bytes であることを検査し、分割点 `(1)｜(2)` を維持。[test_spool_fold.py:1914](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:1914)、[test_spool_fold.py:1940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:1940)。 |
| B MF-4 — ordinal-gap apply が dirty canonical で停止 | **closed** | gap canonical を commit 後に fragment を作り、実 apply と次 fold まで到達。[test_spool_fold.py:812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:812)、[test_spool_fold.py:822](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:822)、[test_spool_fold.py:831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:831)。 |
| B MF-5 — rotation-chain 第2 entry が収容不能 | **closed** | limit 400 に対し「(1) だけ移動では超過」「(1),(2) 移動なら収容」を独立に固定し、archive `[1,2]` / current `[3]` と第2 fold を検査。[test_spool_fold.py:916](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:916)、[test_spool_fold.py:940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:940)、[test_spool_fold.py:948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:948)。 |

## fix による回帰検査

### F1 の受理集合

fix 前は末尾が `\n$`、現差分は `\n` で、呼び出しは双方とも `carry_re.fullmatch(item.block)` である。

```regex
^- (?P<id>\[T-(?:0(?:0[1-9]|[1-9][0-9])|[1-9][0-9]{2,})\]) (?:変わらず \(\((?P<legacy_ordinal>[1-9][0-9]*)\) 参照\)|\((?P<compact_ordinal>[1-9][0-9]*)\))\n
```

fix 前はこの末尾に `$` が付く。[pre-fix-snapshot.patch:578](/work/1/SFC/tanab/dev-wave-jobs/token-economy/codex/pre-fix-snapshot.patch:578)、現行呼び出しは [spool_fold.py:1163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1163)。

`fullmatch` 自体が入力終端までの消費を要求するため、`$` の削除で受理集合は変わらない。追加 LF、suffix、複数行 continuation はいずれも現行 `fullmatch` で不一致になる。したがって F1 は regressed ではない。

### rotation と期待値

F5 の entry (2) 短縮はテスト意図を変えていない。production は先頭側から、残る current が limit 以下になる最初の分割点を選ぶ。[spool_fold.py:1661](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1661)

- entry (1) の filler は全体を 320 超へ戻す。
- entry (2) の短縮は、凡例を含む `(2)+(3)` を 320 以下に保つ fixture 調整。
- archive が変更前 entry (1) の exact slice と等しいため、entry (2) まで移す実装なら赤になる。[test_spool_fold.py:1944](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:1944)

2 巡目の `len(archive)+len(current)>320` は自己矛盾ではない。`moved` と `rotated` は projected bytes の非重複 partition なので、和は rotation 前サイズになる。ただし `rotation_path is not None` も超過を含意するため、独立検出力はない冗長 assertである。これは成果物影響なしの **nit**。分割点は後続の exact assert が実効的に固定している。

既存 assert・skip・xfail の削除や緩和はない。real-corpus golden も変換件数 `215`、active/item 件数、最終 UTF-8 bytes の完全一致を維持する。[test_spool_fold.py:2087](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/orchestrator/tests/test_spool_fold.py:2087)

新設・変更テストで、対応する実装を壊しても緑のままになるものは見つからなかった。例外は前述の冗長 assert と到達不能 guard で、いずれも成果物影響のない nit である。

## M01〜M09 の再帰属

以下は静的な kill 帰属であり、mutation harness はこちらでは実走していない。

| ID | 現差分で kill する nodeid |
|---|---|
| M01 | `orchestrator/tests/test_spool_fold.py::test_n08_all_carries_preserve_order_and_count` |
| M02 | `orchestrator/tests/test_spool_fold.py::test_generated_next_action_heading_and_compact_carry_are_byte_exact` |
| M03 | `orchestrator/tests/test_spool_fold.py::test_compact_and_legacy_carry_chain_resolves_substantive_base` |
| M04 | `orchestrator/tests/test_spool_fold.py::test_legacy_carry_future_reference_is_rejected` |
| M05 | `orchestrator/tests/test_spool_fold.py::test_compact_carry_uses_explicit_prior_across_ordinal_gap` |
| M06 | `orchestrator/tests/test_spool_fold.py::test_two_worklog_fragments_use_immediate_prior_ordinals` |
| M07 | `orchestrator/tests/test_spool_fold.py::test_compact_carry_missing_entry_rejects_before_stub_digest`、`::test_compact_carry_missing_task_rejects_before_stub_digest` |
| M08 | `orchestrator/tests/test_spool_fold.py::test_multiline_compact_prefix_item_uses_full_substantive_digest` |
| M09 | `orchestrator/tests/test_spool_fold.py::test_compact_and_legacy_carry_chain_resolves_substantive_base`、`::test_compact_stub_digest_cannot_satisfy_mutating_base`、`::test_four_digit_compact_carry_chain_resolves_ordinal_1000` |

M08 の到達可能入力は次である。

```text
- [T-001] (1)
  詳細
```

`_split_top_items` は continuation を同じ `item.block` に保持する。[spool_fold.py:312](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:312)

- baseline `fullmatch` は continuation のため不一致となり、複数行全体を substantive item として扱う。
- M08 の `match` は先頭行 `- [T-001] (1)\n` に prefix 一致し、entry (1) の digest へ遡る。
- fixture が渡す base は複数行全体の digest なので、[spool_fold.py:1349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1349) の base 比較で赤になる。

したがって M08 は現在は等価変異ではなく、登録を維持できる。

## 見出し凡例の副作用

固定凡例は次のとおり。

```text
### 次の一手 — 「(番号)」だけの項は、その番号のエントリ (archive 含む) から変わらない持ち越し
```

- `spool_fold`: suffix 許容 regex が受理し、item は heading 終端後から抽出。[spool_fold.py:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:54)、[spool_fold.py:1004](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1004)
- `check_docs.py`: `(?:[ \t][^\n]*)?` が suffix を受理し、凡例は body capture に入らない。[check_docs.py:537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:537)、[check_docs.py:765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:765)
- `tools/dev_waves/checker.py`: 同じ suffix 許容形で、ID は heading 後の list item のみから抽出。[checker.py:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/dev_waves/checker.py:41)、[checker.py:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/dev_waves/checker.py:153)
- daemon は checker の抽出器をそのまま使用。[daemon.py:1148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/dev_waves/daemon.py:1148)
- `dev_wave_land.py` は独自 parser を持たず、同 checkout の `spool_fold` に plan/apply を委譲。[dev_wave_land.py:1196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/dev_wave_land.py:1196)、[dev_wave_land.py:1800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/dev_wave_land.py:1800)
- class 3 の grep は `^### 次の一手` prefix なので一致し、rulings も stub の参照先を辿る契約を持つ。[CLAUDE.md:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/CLAUDE.md:38)、[rulings.md:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/.claude/commands/rulings.md:13)

凡例には `[T-...]` token がないため、worklog/archive/見送り台帳を `TASK_RE` で走査する採番母集団へ入らない。[spool_fold.py:1209](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1209)。また entry ordinal regex は H2 `##` 限定なので、H3 の凡例は entry 採番にも影響しない。[spool_fold.py:46](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:46)。