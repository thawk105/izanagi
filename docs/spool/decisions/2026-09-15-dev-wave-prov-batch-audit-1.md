---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-15
wave: dev-wave-prov-batch-audit
seq: 1
---

## {{D:provenance-batch-message-fetch}}. 全史 provenance 監査の message 取得だけを一括化し、検査範囲は一切変えない

**決定:** `tools/check_ai_provenance.py` の正常 bitset 経路で、commit ごとの
`git show -s --format=%s` / `--format=%B` を `git log --no-walk=unsorted --stdin -z
--format=tformat:%H%x00%s%x0a%x00%B%x0a` 1 回の一括取得へ置き換える。取得は終端 NUL・
`3N` フィールド・OID の形式 / 一意性 / 要求集合との exact 一致を検査し、いずれかが崩れたら
**部分結果を一切使わず全件を既存 `show` 経路へ戻す**。取得結果は OID を鍵にした辞書で引き、
要求列と出力列を位置で結合しない。注入は `ancestry` と別の keyword-only 引数とし、
逐次 oracle 経路 (`ancestry is None`) には渡さない。
`_ai_agent_values` と `_isolated_parsed_trailers` は変更しない。

**検査対象 commit 集合・判定・findings・rc・公開出力は 1 bit も変えない。**

**理由:**
- D908 は「全史監査は削るな。速くするなら取り込み差分だけを対象とする独立監査を先に設計し、
  被覆が現行と等価であることを示してから置き換えよ」と裁定している。本決定は**範囲を変えない**ので
  その条件に触れず、定数だけを下げる。D274 が不採用とした「定数上限の引き上げ」にも当たらない。
- 被覆等価は「対象集合の一致」だけでは成立しない。件数・順序・OID 検証がすべて一致しても、
  OID と message の対応がずれれば拒否が受理へ動く。OID を鍵にした辞書引きがこれを構造的に塞ぐ。
- 実測 (2026-09-15、login node): 全史 10443 件で提案コマンドと現行 `show` の subject / message が
  **mismatch 0**。同一 worktree・同一 range (6378 件)・同一経路で child stdout が
  **22591 bytes 完全一致**。commit 後の全史監査は 10105 件・新規違反なし・known-violations=56。
- 所要は同条件の交互 2 ラウンドで **1.5355 倍 (34.79 % 減、旧 224.8 秒 → 新 145.4 秒)**。
  **「成長比例問題を解消した」とは言えない。** 一括化後も trailer 解析の per-commit subprocess、
  隔離 parse の tempdir、実装 path 取得、祖先索引が残り、O(履歴) の構造そのものは変わらない。

**却下した選択肢:**
- **`_ai_agent_values` の `%(trailers)` 置換** — 取り分の小ささではなく**証明面を拡大しない**ため
  見送る。`--parse` は `--only-trailers --only-input --unfold` の別名だが `%(trailers)` に
  `--only-input` 相当の option がない。実 commit へ `trailer.inject.*` を与えても差は出なかったが、
  全設定の等価性は未証明である。
- **範囲限定 (incremental 監査)** — 本決定の scope 外。受領証という新しい攻撃面を作り、
  D908 が要求する被覆等価の論証を別途必要とする。定数削減で足りるうちは先に定数を下げる。
- **streaming 化** — 全 message 10.4 MB の常駐を避ける設計。32 worker はスレッドで辞書を共有し、
  48 個の全史 checker が同時に走る証拠もないため、費用に見合わない。
- **取得失敗を新しい公開診断にする** — 公開出力の不変を壊す。失敗は既存経路へ戻し、
  既存の例外・順序・rc をそのまま再現する。

## {{D:cost-reduction-prefers-constant-over-scope}}. 成長比例コストは、範囲を削る前に定数を下げる方を先に試す

**決定:** repo 成長に比例する検査コストを下げるとき、**検査範囲の限定より先に、同じ範囲を
同じ規則で検査したまま定数を下げる道を探す**。範囲限定は、定数削減で足りないことを実測で
示してから設計する。

**理由:**
- 範囲限定は「どこまで検査済みか」の受領証を導入する。受領証を書く主体と検査する主体が同じである
  限り改竄への完全な防壁にならず (D387 と同型の限界)、被覆等価の論証も必要になる (D908)。
  定数削減にはどちらも要らない。
- 本 wave の実測が具体例である。全史監査 133.6 秒のうち **84.7 % が per-commit の `git show` 起動**で、
  同じデータは `git log` 1 回・0.49 秒で取れた。範囲を 1 件も減らさずに 35 % 短縮した。
- ただし定数削減は O(履歴) を消さない。**次に同じ問題が戻ってくる**ので、
  「解消した」と記録してはならない。

**却下した選択肢:**
- **常に範囲限定を先に検討する** — D274 (RuleOps pickaxe) は範囲限定が正解だったが、
  あれは定数削減の余地が先に尽きていた事例である。順序を逆にすると、安く済む場合にも
  受領証と等価性論証の費用を払うことになる。
- **履歴そのものを短くする (squash / shallow / 新 repo)** — checker は
  `--is-shallow-repository` / `info/grafts` / `git replace --list` を起動時に検査して
  これらを拒否する。provenance の証拠を失うことと引き換えに検査を軽くする形であり、
  規律 2 が禁じる方向である。commit SHA を束縛している tracked file は実測 243 件ある。
