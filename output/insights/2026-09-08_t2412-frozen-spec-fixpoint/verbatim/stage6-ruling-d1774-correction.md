# 段 4 裁定の訂正 — D1774 に合わせる

## 何が起きたか

段 1 で承認済みユーザー裁定を実測せずに brief を書いた (DW-S01 違反)。依頼文と insight の
一次資料だけを見て、`docs/worklog.md` の T-2412 項と `docs/decisions.md` の D1774 を引かなかった。

D1774 (ユーザー裁定、2026-09-08) は次を決めている。

> `provenance.source_commit` を **spec を著した時点の commit (spec を含む commit の親)** とし、
> spec load 時は **HEAD がその commit の子孫であること**を要求する。HEAD との完全一致要求は外す。
> spec bytes と HEAD tracked blob の byte 一致検査は**残す**。
> 直すときは、偽の VCS ではなく**実 VCS を通す正例**と、**spec 改変・別 HEAD を通す負例**を同時に足す。

却下欄には「source_commit を親 commit へ束ね、HEAD 一致は残す」がある。

## 現行実装との差

現行実装は `parents(loaded_head) == (source_commit,)` かつ
`changed_paths(source_commit, loaded_head) == (spec relpath,)` を要求する。これは
「HEAD が source_commit の子孫」より**狭い**。

狭すぎることの実害は具体的である。**freeze commit の後に 1 つでも commit が乗った時点で、
その spec は二度と load できない。** 本 wave の最中だけで local main は 8 commit 進んだ。
これは T-2412 が閉じようとしている失敗 (spec が使えない) と同じ型を作り直すことになる。
D1774 の理由欄も「子孫関係へ緩めれば構造的に消え」と、緩める方向を明示している。

## 裁定

**D1774 に合わせる。** 親が段 4 で採った狭い形は撤回する。

- loader は `source_commit` が `loaded_head` の**真の祖先**であることを要求する
  (`git merge-base --is-ancestor`、かつ `source_commit != loaded_head`)。
  等値を許すと不動点が戻るため、真の祖先とする。
- `parents(...) == (source_commit,)` と `changed_paths(...) == (spec relpath,)` の 2 判定は外す。
  これに伴い `_git_changed_paths` と `--ignore-submodules=none` も外す。
- 残すもの: spec bytes と `loaded_head` の blob の byte 一致、`expected_sha256`、
  `loaded_head` の単一解決と全 blob 比較のその OID への束縛 (段 6 レビュー A-1)、
  実行時と finalizer の `loaded_head` 統一、status の改名、実 git の正例・負例。
- proof-limit 文言は実際の保証へ書き直す。**tree の同値はもう保証しない。**
  保証するのは「spec の bytes が `loaded_head` の tracked blob と一致する」「`source_commit` が
  `loaded_head` の真の祖先である」の 2 つで、その間に何の変更が入ったかは制限しない。

## 裁定パッケージへ返すもの (実装しない)

1. **狭い形 (唯一の親 + spec 1 path 差分) の方が保証は強い。** 本 wave で実装し、敵対レビュー 2 本と
   変異 9 件で検証済みである。ただし freeze commit の後に commit が乗ると spec が load 不能になる。
   D1774 を撤回して狭い形を採るかはユーザーの判断であり、親は決めない。
   逐語と変異台帳は insight に残す。
2. 段 6 レビュー A の submodule 所見 (RA-1) は、狭い形を採る場合にだけ意味を持つ。
   祖先形では tree 同値を主張しないため発火しない。
3. `--no-replace-objects` (段 3 レンズ A) — 仮想リスク向けの検査追加として scope 外のまま。
4. issuer が `summary["loaded_head"]` を検証せず転記する (段 6 レビュー B) — 本 wave 以前からの
   もので、production への比較追加は新設 gate のため scope 外のまま。

## 変異の再登録 (DW-M01)

祖先形へ変えると M01 / M02 / M07 / M08 は対象が消える。次を登録し直す。

| ID | 位置 | 変異 | 期待 |
|---|---|---|---|
| N01 | 祖先判定 | `is_ancestor` の結果を無視する | KILLED (別系統 HEAD の負例) |
| N02 | 祖先判定 | 真の祖先要求を等値許容へ緩める | KILLED (source == loaded の負例) |
| N03 | spec blob 比較 | bytes 一致検査を除去 | KILLED |
| N04 | 実行時 | `runtime_head != loaded_head` の拒否を除去 | KILLED |
| N05 | finalizer | 期待 `runtime_head` を `source_commit` へ戻す | KILLED |
| N06 | blob query の OID | 解決済み OID を symbolic `HEAD:` へ戻す | KILLED |
| N07 | `_read_tracked_bound` | blob query を除去 | KILLED |
