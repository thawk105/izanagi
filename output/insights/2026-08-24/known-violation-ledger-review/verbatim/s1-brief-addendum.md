# 段 1 brief 追補 — 親の実測が親自身の provisional 裁定を覆した

この追補は `brief.md` より新しい。矛盾する箇所は**この追補を優先**する。

## 覆った裁定

`brief.md` の **(P3)「本 wave の述語は D721 の射程外である」は反証された。**

親は 3 つ目の実測を行った (`measure_mergefile.py`)。missing-codex-author の merge 11 件について、
finding 対象 path ごとに merge base / 親1 / 親2 の blob を取り出し `git merge-file -p --diff3` で
3-way merge を再計算し、実体と突き合わせた。結果:

- **novel 行 0 の 10 件は、いずれも該当 path で実際に競合していた** (`git merge-file` の rc は
  競合 hunk 数。rc=1〜5)。自動解決ではなく、**人が手で解決した merge** である。
- 自動解決と bytes 一致した path は 1 つだけ (`311d463f89` の
  `orchestrator/campaign/s8b_oracle_driver.py`) で、その commit の他 2 path は競合していた。
- D721 の「combined diff の最終形からは自動解決と手解決を区別できない」という論点は、
  再計算という別経路でも「手解決だった」と確認された。**D721 の判断は実測に支持される。**

注: `git merge-tree --write-tree` による tree 単位の再計算は、この機体の git 2.34.1 が
非対応のため使えない (`fatal: unknown rev --write-tree`)。上記は per-path の代替経路である。

## 述語を強めた場合の実測収量

`measure_subseq.py` で、より強い述語「novel 行 0 **かつ** 両親の版がそれぞれ結果の subsequence
(＝取捨選択も並べ替えも無い純粋な interleave)」を測った。

- 強い述語を満たす: **4 件** (`5823caf328` `3eaf2038ec` `0c0f3e71b3` `bf92f327ca`)
- novel 0 だが片方の親の行を実際に**捨てている**: 6 件
  (`a5b7045b12` `311d463f89` `8440a14850` `e39a8d4656` `387a1daab0` `e86d363a87`)。
  取捨選択は判断を伴う編集であり、D721 の却下理由がそのまま当たる。
- 弱い述語 (novel==0 のみ) の収量 10 件は、この 6 件を誤って通す。**採ってはならない。**

⇒ checker 側の是正で減らせるのは最大 **4 件 / 53 件 (7.5%)**。しかも D721 を覆す必要がある。

## 新たに判明した本当の生成器

`measure_mergefile.py` の出力で、**競合が起きた path は 11 件すべてで
`tools/check_ai_provenance.py` と `orchestrator/tests/test_check_ai_provenance.py` だけだった**
(非台帳 path で唯一現れた `s8b_oracle_driver.py` は自動解決で一致)。

つまり **merge 由来の missing-codex-author 11/11 は、台帳そのものの競合が原因である。**

構造はこうなっている。
1. 全 wave が `KNOWN_PROVENANCE_VIOLATIONS` という単一 Python tuple の末尾へ追記する。
2. 逐語ミラーテスト `test_known_violation_ledger_matches_literal_entries` の `expected` タプルにも
   同じ内容を追記する。**衝突面が 2 file に倍化している。**
3. 並行する 2 wave は必ずこの末尾で競合する。親が手で解決する。
4. その手解決が「Codex author なしの実装面編集」になり、**新しいエントリを生む。**
5. エントリが増えるほど tuple が長くなり、衝突確率と解決の手間が上がる。

自己増殖ループである。直近 21 件のうち、merge 由来 11 件はこれ、
manager の直接 commit 由来 3 件 (`25614f868c` `94815c5797` `3a5e5feb5f`) も
「台帳登録そのものが `tools/` 配下の実装面編集だから」であり、同じ根を持つ。**合計 14/21。**

## 影響閉包 (親が全数検索で確認)
`KNOWN_PROVENANCE_VIOLATIONS` を参照する code は `tools/check_ai_provenance.py` と
`orchestrator/tests/test_check_ai_provenance.py` の 2 file だけ (docs/failures.md,
docs/decisions.md は散文言及)。checker CLI の呼び手 (`dev_wave_land.py`, `dev_wave_wait.py`,
`pegasus/dispatch_compute.py`, `hooks/guard_bash.py` 等) は定数を触らない。

## 段 3 が裁くべき択一

- **案 A — 述語を強める。** 収量 4 件。D721 を覆す必要。正しさ gate に触る。
- **案 B — 台帳の格納形を変える。** 収量 0 件 (既存は減らない) だが、生成器 14/21 を止める。
  エントリを 1 件 1 file のデータ (例: `docs/provenance/known-violations/<sha>.json`) にすれば
  別 wave の追加は別 file になり競合しない。さらに `docs/` 配下は実装面の定義に含まれないため、
  **登録 commit 自体が docs-only になり Codex author を要しなくなる**。
  checker の意味は一切変えない (格納場所だけ)。
- **案 C — 逐語ミラーテストを畳む。** `expected` タプルは `ruling` / `note` という**説明文**まで
  逐語 pin しているが、受理集合に効くのは `commit` / `expected_finding_kind` /
  `expected_finding_value` の 3 つだけである。説明文の pin は受理集合を守っていない一方で
  衝突面を倍化している。ただしテストを畳むのは gate を弱める方向であり、慎重な検討が要る。
- **案 D — 実装せず、監査と先送りタスクだけを出す。**

案は排他ではない。B と C は組み合わせられる。
