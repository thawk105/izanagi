結論は **NO-GO** です。実装の狙い自体は妥当ですが、実効 pin を迂回でき、呼出し辺もテストされていません。

### RB-1 — must-fix: `[T-595]` の前進と記録してはならない

**成果物影響:** `[T-595]` の進捗値・A/B 台帳・材料レポートだけが偽に前進し、certified 選択の実値は何も変わっていない。

**確認:** 依頼は paired・blind・非劣性評価です（[brief.md:8](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/brief.md:8)）。しかし段4で採用されたのは latch 1件だけ（[s4-ruling.md:25](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s4-ruling.md:25)）で、装置・endpoint ledger・campaign は scope 外です（[s4-ruling.md:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s4-ruling.md:42)）。また、指定された実装報告は「296 passed」ではなく、pytest 未実走・rc=16 と明記しています（[s5-impl.md:26](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s5-impl.md:26)、[s5-impl.md:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s5-impl.md:42)）。別の親実走があるなら、実装子報告と混同せず別証拠として帰属させる必要があります。

**最小修正:** worklog／裁定パッケージへ次を逐語相当で入れる。

> 本 wave は `[T-595]` の paired・blind・非劣性 A/B を実装も実走もしておらず、max→high の非劣性・引下げ可否を示す evidence は 0 件である。

> 実装したのは `workers.md` の現行 max 記述を守る docs adoption latch のみであり、評価装置、protocol、endpoint ledger、campaign は未実装である。この latch は served model／実効 effort を attest しない。

> `[T-595]` は完了・前進・一部実証と記録しない。certified 選択、材料レポート、試行台帳の評価値は不変である。

> A-4/A-5/A-6/A-10/A-11/B-3/B-4/B-6/B-7/B-9 は real だが未実装ゆえ未発火であり、refuted／closed／resolved ではない。campaign 設計 wave へ全件 carry する。

現行の段4文言自体は最後の区別を正しく書けています（[s4-ruling.md:66](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s4-ruling.md:66)）。「全所見を閉じた」「残件0」も同じ理由で不可です。F70型の記録過大主張に該当します（[failures.md:1633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/failures.md:1633)）。

### RB-2 — must-fix: raw literal count は実命令の `high` 化を迂回できる

**成果物影響:** 段2/3を実際には `high` にした文書が `check_docs` を通り、敵対検出力低下により certified 選択・材料レポートの受理集合が広がり得る。

**確認:** 検査は節本文の生文字列で `` `reasoning=max` `` が1件か数えるだけです（[check_docs.py:3390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:3390)）。次の S02 は実命令が `high` でも finding 0 になりました。

```md
codex `reasoning=high` で起動する。
<!-- `reasoning=max` -->
```

S03を正規の `max` にした入力へ helper を適用した実測結果は `[]` です。不可視コメントや code fence を除く既存 parser は既にあります（[check_docs.py:995](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:995)）。現テストは単純な置換・削除だけで、decoy を試していません（[test_check_docs.py:4807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4807)）。F9の恒真ゲート型です（[failures.md:115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/failures.md:115)）。

**最小修正:** 不可視領域を除いた節から全 `reasoning=<value>` を抽出し、値列が厳密に `["max"]` の場合だけ受理する。実命令 `high`＋コメント／fence内 `max` の負例を両節へ追加し、変異事前登録にも decoy 変異を足す。

### RB-3 — must-fix: private 検査の呼出し辺が未固定

**成果物影響:** `_check_command_docs_guard()` から委譲1行を消すだけで無断 `high` が受理され、RB-2と同じ成果物受理集合拡大が起きる。

**確認:** production の委譲は [check_docs.py:3560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:3560) の1箇所です。一方、新規負例はすべて private helper を直接呼びます（[test_check_docs.py:4795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4795)）。従って委譲行を削除しても新規4テストはそのまま緑です。これは F127 の直接再発です（[failures.md:3022](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/failures.md:3022)）。

**最小修正:** helper を spy に置換し、`_check_command_docs_guard()` が実 `workers_text` で exactly once 呼ぶテストを追加する。加えて `_build_min_repo()` の S02 を `high` にして `main()` の rc=1と対象 finding を確認する統合負例を置き、委譲削除を独立変異にする。

### RB-4 — should-fix: finding が検査していない時系列事実を断定する

**成果物影響:** A/B完了・採用後にも「A/B未充足」と誤報して rc=1になり、承認済み文書変更の受理集合と材料レポート上の状態を誤らせる。

**確認:** 文言は「A/B 未充足」と断定します（[check_docs.py:266](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:266)）が、検査が読むのは `workers.md` だけで、A/B台帳や後継裁定は読みません。D207は「A/Bだけが可否を決める」としており（[decisions.md:9891](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/decisions.md:9891)）、永久に未充足とは決めていません。さらにテストは finding 定数自身を期待値に使うため、文言要件を独立に固定していません（[test_check_docs.py:4811](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:4811)）。F122/F27型の説明・oracle 同期漏れです。

**最小修正:** 時不変の文言へ変える。

> D207 に基づく現行 adoption pin と不一致 — 変更には paired・blind・非劣性 A/B に基づく採用裁定と pin の同時更新が必要

解除が自動でないこと自体は設計欠陥ではなく、意図した fail-closed です。正しい解除手順は次の3行です。

1. paired・blind・非劣性 A/Bを完了し、対象段と採用値を明記した後継裁定を記録する。  
2. 同一変更で `workers.md`、節別 pin、finding、独立テスト、変異 spec を裁定どおり更新する。  
3. 統合負例・関連テスト・`check_docs`・provenanceを再走し、契約と latch を原子的に land する。  

`max` 廃止時も silent default へ落とさず停止し、A/B不能なら人間の後継裁定でD207を supersedeします。F56が示すとおり、docs pin は実効 effort の attestation ではありません（[failures.md:1281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/docs/failures.md:1281)）。

### RB-5 — nit: 構造違反では finding 件数・順序が重複する

**成果物影響:** certified／材料／台帳の受理集合とrcは不変で、`check_docs` の違反件数・表示順だけが変わる。

**確認:** S02/S03が欠落・重複すると pin 検査が finding を追加し（[check_docs.py:3391](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:3391)）、後段の既存 H2 一意性検査も追加します（[check_docs.py:3614](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:3614)）。従来1件だった構造違反が2件になり、pin finding が先に出ます。rcは従来どおり1です（[check_docs.py:4215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:4215)）。

**最小修正:** 節数が1でない場合は既存構造検査へ委ね、literal検査は一意な節にだけ適用する。

### RB-6 — nit: 同値定数は節別独立性のためだが、その意図が表現されていない

**成果物影響:** 一方の定数と対応する文書だけを変えると、S02とS03で異なる effort を受理する集合になる。

**確認:** 定数値は同一です（[check_docs.py:264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/tools/check_docs.py:264)）が、段4は節別独立検査を要求しています（[s4-ruling.md:77](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t595-reasoning-ab/s4-ruling.md:77)）。一方だけ定数変更・文書未変更ならその節だけ赤、一方の文書も同時変更すれば非対称値を受理します。これは段別裁定を可能にする意図なら妥当です。

**最小修正:** 共通定数へ潰さず、節別 mapping として明示し、名前を値非依存の `..._REASONING_LITERAL` にする。非対称更新は段別A/B裁定がある場合だけ行う旨をコードコメントへ短く置く。

## 静的な回帰・予算確認

- snapshot patch と実作業木の差分は同一でした。
- 合成 `workers.md` には両 literal が注入されています（[test_check_docs.py:565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t595-reasoning-ab/orchestrator/tests/test_check_docs.py:565)）。`_build_min_repo()` の183 call siteについて、`workers.md` を触る既存経路は S06 文言変更か追記 paddingであり、pinを消しません。したがって既存 clean fixture・finding集合・rcへの新規赤は静的にはありません。
- `docs/dev-wave/*.md` は変更されておらず、実測合計は **25,187 / 25,200 bytes** のままです。修正対象もコード・テストだけで済みます。この latch 自体が将来の docs 追記を強制する経路はありません。
- 新しい `x or default` 型はありません。`workers_text is None` では helperを飛ばしますが、読取失敗・不在は先行 finding により fail-closedです。F149型の共有 fixture consumer取り残しも現差分では確認しませんでした。
- pytestは本レビューでは実行していません。静的検査と上記の副作用なし helper probeだけです。

## 総括

must-fix は **3件（RB-1〜RB-3）**。  
現状の land は **不可**。  
docs予算と既存fixture回帰は blockerではありません。  
decoy拒否・呼出し辺固定・正直な記録を入れ、変異matrix後に再レビューが必要です。