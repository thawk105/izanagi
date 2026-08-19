# 段4 親裁定 — [T-619] D230 統一述語を既定監査へ導入する

基準: 段2プラン (`s2/plan.md`)、段3 レンズA (`s3/lensA.md`)・レンズB (`s3/lensB.md`)。
両レンズに矛盾所見なし。全件 real、全件 scope 内 (2件は明示的に scope 外の existing-issue confirmation)。

## 裁定表

| # | 出所 | severity | 判定 | 採否 | scope | 処置 (plan v2 への反映) |
|---|---|---|---|---|---|---|
| A1 | lensA | blocker | real | 採用 | 内 | `_ledger_policy_is_visible` の呼び出し箇所 (`_known_violation_audit` を呼ぶ側、`_audit_history` 内) へ `authoritative=authoritative` を明示配線する。実装子はこの1呼び出しを diff で明示すること (plan本文の「1720-1724から渡す」という言及だけで終わらせない)。専用テスト必須: `authoritative=True` かつ `authoritative` を配線し忘れた変異で `333605d6` の扱いが変わることを確認する (mutation registrable にする、レンズB所見3の単一理由性と合わせて設計) |
| A2 | lensA | must-fix | real | 採用 | 内 | `_normal_commit_audit(ancestry=None, authoritative=True)` の組み合わせは production では発生しない (`_audit_history` は常に実 ancestry を渡す)。**oracle 側の二重実装は追加しない (規律5、盛らない)。** 代わりに `ancestry is None and authoritative` を **fail-fast で拒否** する (`RuntimeError`)。等価性テスト (`test_ancestry_pickaxe_mask_matches_per_commit_oracle`) は `_normal_commit_audit` を経由せず `ancestry.has_cab_policy(commit, authoritative=True)` を直接呼び、素の `_is_descendant` で書いた inline oracle と比較する形 (plan 686-699 の形) を維持する — この形なら `ancestry=None` を通らないため矛盾しない |
| A3 | lensA | must-fix | real | 採用 | 内 | CAB seed 集合が空 (=CAB 規則がこの repo に一度も導入されていない) のとき、統一述語の第2項は数式上は空虚な真になるが、**意図する挙動は「規則が存在しないなら適用しない」= False を維持する**。`_Ancestry.has_cab_policy` の実装 (`cab_policy_mask` が 0 のとき早期 `return False`) をそのまま採用し、コード中コメントと該当テストにこの例外を明記する。scope/implementation 層も同型 (`epoch is None` なら `applies_epoch` は `False` — plan の実装は既にこの分岐を持つので変更不要、確認テストだけ足す) |
| A4 | lensA | nit | real | 採用 (nit) | 内 | HEAD drift の rc=2 優先、graft 非存在/空ファイルの区別、複数 replace ref を扱う境界テストを追加する。blocker ではないため段5 実装の最低要件ではなく、段6 fix 予算に余裕があれば拡充する |
| B1 | lensB | must-fix | real | 採用 | 内 | **regression 確認済み。** explicit `--range` 経路でも `_scope_policy_commit(None)` / `_implementation_policy_commit(None)` のように**明示的に `None` を渡す**と、既存テストの zero-arg monkeypatch (`test_forward_correction_merge_base_rc128_fails_closed_with_rc2` 含む) が `TypeError` になる。**修正: `authoritative` が False のときは新関数を**引数なしで**呼ぶ (`_scope_policy_commit()` / `_implementation_policy_commit()`)。`authoritative` が True のときだけ `head=head` を渡す。三項演算子で `None` を明示的に渡す形にしない** |
| B2 | lensB | must-fix | real | 採用 | 内 | HEAD pin 伝播の専用テスト不足 (A4 と同一問題、統合して扱う) |
| B3 | lensB | must-fix | real | 採用 | 内 | `test_authoritative_epoch_predicate_covers_merged_side_branch` は scope 違反と Codex author 欠落を同一 fixture に同居させており `DW-M01` の単一理由性に反する。**scope-only の side branch fixture と implementation-only の side branch fixture に分割**し、各々が単一 finding だけを主張するテストにする。shallow/graft/replace/非一意 policy add/HEAD drift/CAB/ledger 欠落も個別の単一理由 fixture にする (段4 変異事前登録の入力として下記に列挙) |
| B4 | lensB | must-fix | real | 採用 | 内 | 台帳 ruling 文字列 `"worklog(299) 2026-08-07 /rulings"` は T-614 時代の記法で entry 299 は既に archive 済み。**確定 literal**: `"2026-08-07 [T-619] docs/archive/worklog-phase3-0807-299.md entry 299 (/rulings 第5回、D230 統一述語 5点採用)"`。実装子はこの逐語をそのまま使う (裁定済み、変更しない) |
| B5 | lensB | must-fix | real | 採用 | 内 (段7) | **D230 は書き換えない** (歴史的 decision、「本waveは実装しない」という記述自体が当時の正しい記録)。段7 で新しい canonical D を追記し、D230 の実装 wave であること・entry 299 の5点・`333605d6`・docs byte 改訂を参照付きで記録する。新 worklog entry も追加。旧 archive・insight package (`output/insights/2026-08-07_t619-provenance-range-permanent-design/`) は無改修 |
| B6 | lensB | nit | real | 採用 (nit) | 内 | `tools/check_docs.py` の検査項目棚卸しに provenance dispatch contract と bounded file-map 構築の2件を追加する (段2プランの記録漏れ、実装への影響なし) |
| B7 | lensB | nit | real | 採用 (confirmed) | **外** | `_scope_policy_commit` の `-S "scope="` 非一意性 (B2/design、T629 相当) は対象外のまま。プランの境界は適切 — 変更不要 |
| B8 | lensB | nit | real | 採用 (confirmed) | **外** | `_build_ancestry` の ARG_MAX/bitset scaling (B4/design、T630 相当) は対象外のまま。プランの境界は適切 — 変更不要 |

段2プラン由来で無条件採用 (レビュー対象外・両レンズとも異論なし): `authoritative` フラグの全体設計、
`_policy_commit()` の非一意検査を `--diff-filter=A` hit 数で行う修正 (brief の `-S` という誤記を
プラン自身が是正済み)、shallow/graft/replace の git plumbing、既知違反台帳への `333605d6` 追加
(kind=`MISSING_CODEX_AUTHOR`、note不要)、契約文書の−168 bytes 等価縮約 (2 レンズが独立に byte 数を
検算し一致)。

## gate 新設の禁止署名 (`DW-O13`)

既定監査 (`--range`/`--message-file` 無し) は、次のいずれかが成立すれば findings を出力せず rc=2 で
拒否する: (a) shallow repository、(b) `.git/info/grafts` が非空、(c) `git replace --list` が1行以上、
(d) `docs/ai-provenance.md` への `--diff-filter=A` hit が2件以上、(e) 監査開始時と終了時で `HEAD` の
full SHA が異なる。上記いずれも成立しなければ、この gate は監査を一切妨げない。

**通る正例 (実測・2レンズ独立確認済み):** 現在の HEAD `f5677a66` は shallow=false、grafts ファイル
非存在、`git replace --list` 空、`docs/ai-provenance.md` の `--diff-filter=A` hit は `50c1ef4e...` の
1件のみ。既定監査は監査開始から終了まで HEAD を動かさない限り、この gate で rc=2 にならず
findings 判定(新規違反1件 `333605d6` を台帳吸収、rc=0)まで到達する。

## 段5 実装分割

単一 Codex `role=author` 実装単位のまま (`P1` 維持、レンズ2本とも分割の必要性を指摘せず)。
対象: `tools/check_ai_provenance.py` + `orchestrator/tests/test_check_ai_provenance.py`。

## docs 契約文改訂 (親が docs-only 権限で直接実施、`P2`)

段4 裁定確定を受け、この直後に親が実施する (段5 Codex 実装と並行してよい。ファイル集合が
disjoint なため競合しない)。確定文言はレンズA/Bが独立に byte 数を検算済み:
- `docs/ai-provenance.md`: 4箇所 (348B) → 統合1文 (180B)。net −168B。6270B→6102B
- `docs/provenance/audit.md` (`PR-A02`): 「導入 commit から HEAD まで」の記述を統一述語の意味へ更新
- family: 8977B → 8809B (cap 9000B に対し slack 191B)

## `DW-M01` 変異事前登録 (段6 で使う。B3 を受けて単一理由 fixture に分割)

以下を個別に登録する。各々「無効化時の赤理由が一つに絞れる」ことを実装後にコードで確認してから
本登録する (未確認の項目は登録せず実効 gate へ再照準)。

1. 選択集合: plain range 化 (`_commit_range` の `--ancestry-path` 削除) — 既定監査が side-branch
   commit を含むかどうかの単一 diff
2. scope epoch 第2項 (`applies_epoch` の scope 版) — scope-only fixture (Codex author 欠落なし)
3. implementation epoch 第2項 (`applies_epoch` の implementation 版) — implementation-only fixture
   (scope 違反なし)
4. CAB seed 第2項 (`has_cab_policy` の authoritative 分岐)
5. HEAD 一度解決・終了時 drift rc=2
6. shallow rc=2
7. graft rc=2
8. replace rc=2
9. 非一意 policy add rc=2 (`_policy_commit` の `len(commits) != 1`)
10. 既知違反台帳 `333605d6` entry (finding 吸収)
11. `_ledger_policy_is_visible` の `authoritative` 配線 (A1 blocker の再発防止)
12. 明示 `--range` 経路が上記 1-11 のいずれの影響も受けないことを示す否定側 (regression 側、
    「変えない」ことの正例として重要)

## 未確定のまま実装子へ渡す判断 (段5 prompt に明記する)

- A2 の fail-fast 拒否は RuntimeError とし、rc=2 (`main` の既存 except 節で拾う) にする。新しい
  例外型は作らない
- B1 の修正は、`_audit_history` 内で `if authoritative: scope_epoch = _scope_policy_commit(head)
  else: scope_epoch = _scope_policy_commit()` のように**明示的に2分岐**する (三項演算子で `None` を
  渡す書き方を禁止する。同じ理由で `_implementation_policy_commit` も同様)
