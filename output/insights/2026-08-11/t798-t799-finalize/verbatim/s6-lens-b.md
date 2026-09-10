## 総括

静的検査のみです。pytest、checker、commit identity の実走は行っておらず、「緑」とは判定していません。

**NO-GO** です。must-fix は 4 件あります。

- finalize の state unlink 後は成功応答前の crash/rc 30 から自動復旧できない。
- standalone と land の競合では transaction ID 検査が TOCTOU で、別 transaction の state を削除・上書きできる。
- commit identity は手動生成 commit を排除できず、author の実装も exact equality ではない。
- noop は canonical/FOLDED の検査より前に確定し、land の早期 return と合わせて検査を飛ばせる。

### 段 3 所見の対応表

| 段 3 所見 | 判定 | コード根拠 |
|---|---|---|
| LUNA-P5-01 | **closed** | applied + fold child は [dev_wave_land.py:2403](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:2403) から recovery B に入り、[dev_wave_land.py:2110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:2110) で mark を修復して finalize する。 |
| LUNA-P5-02 | **partial** | exact tree/path/blob gate は入ったが、author は prefix 比較（`spool_fold.py:3098-3100`）。また公開情報だけで同じ tree/author/message の手動 commit を生成できる。 |
| LUNA-RB-03 | **partial** | state unlink 後の dir fsync は追加（`dev_wave_land.py:1828-1829`）。ただし update-ref/read-tree/restore 途中の残骸は自動復旧不能。 |
| LUNA-FIN-04 | **partial** | finalize は rollback try の外（`dev_wave_land.py:2076-2088`）になった。一方、unlink 後の crash/rc 30 は state 無しの成功曖昧相を残す。 |
| LUNA-RACE-05 | **partial** | transaction ID は確認するが、read/check と unlink/replace が原子的でなく、競合時には保証が破れる。 |
| LUNA-CLOSURE-07 | **partial** | resume preflight は追加されたが、porcelain の index 側 1 文字目しか拒否せず、unstaged の `" M"` は通す（`spool_fold.py:2917-2920`）。 |
| LUNA-VERIFY-08 | **closed** | mark と finalize の双方が commit identity を必須化（`spool_fold.py:3161-3162,3186-3187`）。recovery B も先に identity を検査する。 |

## 所見

### LUNA-S6-RACE-01 — state の ID 検査は unlink/replace の CAS になっていない

**real / must-fix**

- 根拠: [tools/dev_wave_land.py:1806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/dev_wave_land.py:1806)、`1811-1828`。rollback は ID を読んだ後、別 syscall で unlink する。
- 同じ穴が mark の `spool_fold.py:3156-3167`、finalize の `3181-3188` にもある。
- standalone の `apply_fold` は land lock を取らず、state 不在確認 `spool_fold.py:2938-2950` と atomic replace `2963-2964` の間にも CAS がない。
- 競合例:

  1. land と standalone が state 無しを観測する。
  2. land が state L、standalone が state S を順に `os.replace` する。
  3. 両者が `spool_fold.py:2972-2995` で異なる target/FOLDED bytes と GC を書く。
  4. land rollback が S を読む前なら L の ID を確認し、その直後に standalone が S を replace する。
  5. land の `unlink()` は S を削除する。standalone は state 無しのまま書込みを続ける。

- land/standalone では receipt の `base` 等が異なるため（`spool_fold.py:2405-2415`）、同じ fragment でも target bytes は同一とは限らない。

**成果物影響:** 別 transaction の journal が消え、canonical の ID/receipt と削除済み fragment の対応が崩れて、台帳値・proof-chain 参照・受理集合が writer の順序で変わる。

### LUNA-S6-FIN-02 — finalize unlink 後は成功応答前の crash から再開できない

**real / must-fix**

- 中断点: [tools/spool_fold.py:3188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:3188) の unlink 直後、`3189` の directory fsync 前・失敗時・成功後の return 前。
- 残る形は `tree=after/GC absent, state=absent, main=verified fold child`。
- active recovery は state が存在するときだけ `dev_wave_land.py:2358-2462` に入る。
- state が無い再試行では wave 側から同じ non-noop plan を再構築するが、`apply_fold` は HEAD が `origin.tested_tip` であることを要求する（`spool_fold.py:2923-2929`）。HEAD は既に fold child なので再 apply できない。
- したがって fsync が成功していても、応答前に process が死ぬだけで結果通知を冪等に再取得できない。

**成果物影響:** main ref と台帳 bytes は fold 済みなのに再試行の受理集合から外れ、land 成功記録・peer 通知・後続 certified 作業が停止する。

rc 30 後の現行運用は次の二分です。

- state が `committed` で残っていれば、同じ land request を再実行して recovery B から finalize できる。
- state が無ければ、現行 code に対応 command はない。main を巻き戻さず、wave から plan を再構築して commit identity/postcondition を手動照合したうえで停止するしかない。state-absent の verified fold child を `already-landed` と認識する経路、または durable completion receipt が必要。

### LUNA-S6-ID-03 — 5 条件を満たす手動 commit を作れる

**real / must-fix**

- parent の単一性は `spool_fold.py:3096-3097`、message bytes は `3101-3102`、tree/path/mode/blob は `3104-3124` で検査される。
- `diff-tree -z --no-renames` の解析は NUL 境界で、重複 path も拒否する（`3018-3051`）。path の空白・改行による出力注入は見つからない。
- expected blob OID も repo の object format で `git hash-object --stdin` から導出しており、ここにも抜け道は見つからない。
- しかし 5 条件は全て公開情報である。state の after bytes から tree を作り、parent、exact author、exact message を設定すれば、任意の committer identity/time を持つ別 SHA の手動 commitが全条件を満たす。transaction ID は commit に束縛されていない。
- さらに実装上、author は equality でなく `startswith`（`3098-3100`）。raw commit object の author header を `FOLD_AUTHOR_IDENTITY + 追加 bytes` としてもこの比較自体は通る。
- 別 wave/別 plan でも、parent・結果 tree・metadata が同じなら受理される。同一 bytes の別 plan は ledger 値を変えないが、「どの transaction が作った commit か」は証明できない。

**成果物影響:** canonical bytes が同じでも、手動生成された別 SHA/author header が certified proof-chain の正規 fold commit 参照として受理される。

### LUNA-S6-NOOP-04 — fragment 0 件で canonical/FOLDED 検査を飛ばせる

**real / must-fix**

- `plan_fold` は fragment が無いだけで [tools/spool_fold.py:2235](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t798-t799-finalize/tools/spool_fold.py:2235) から noop を返す。
- canonical の `_read_required` は `2242-2249`、FOLDED record の parsing は `2282` 以降なので到達しない。closure digest も空文字になる（`2238-2240`）。
- land は noop では no-fold commit shape だけを検査（`dev_wave_land.py:2501-2518`）し、既に tested tip なら `2543-2544`、FF 後なら `2615-2616` で返る。
- 認識済み fragment が残っていれば `pending_candidate` 比較 `2480-2484` があるため、単純な見落としは止まる。
- ただし tested wave 内で fragment を全て削除し、同時に `FOLDED.md` や canonical ledger を壊せば、fragment 0 件の正規 noop としてこの検査経路を通せる。

**成果物影響:** malformed receipt や不正 canonical を含む wave tip が no-fold として main ref に入り、台帳の受理集合とレポート参照が拡大する。

### LUNA-S6-RB-05 — rollback の主要 3 中断点は依然自動復旧不能

**real / backlog**（段 4 で `[T-800]/[T-801]` scope と裁定済み）

- `update-ref` 後（`dev_wave_land.py:1788-1797`）: `main=rollback_ref, state=applied/committed, tree=after`。次回は rollback ref を fold commit と扱って identity gate で拒否する。
- `read-tree` 後（`1798-1803`）: tracked target は before、GC は missing のため `_transaction_shape` の第三状態拒否 `spool_fold.py:2811-2814` に入る。
- `_restore_fold_paths` 後、state unlink 前（`1804-1828`）: tree は before/GC present に戻るが main は rollback ref、state は残るため recovery A/B のどちらでもない。
- unlink 後・dir fsync 前は process crash ならほぼ clean rollback だが、電断で state が復活すれば上記残骸へ戻る。

**成果物影響:** main ref・canonical・fragment・state の世代が分離し、次 wave が台帳を fold/受理できなくなる。

### LUNA-S6-CLOSURE-06 — resume clean preflight は外部 rollback を識別しない

**real / backlog**

- resume は `_git_clean_preflight(..., resume=True)` を通る（`spool_fold.py:2947-2949`）。
- しかし porcelain の 1 文字目だけを検査するため、tracked file の unstaged change `" M path"` は `line[0] == " "` として許可される（`2917-2920`）。
- target を after から stored before bytes へ外部 actor が戻しても `_transaction_shape` は正規 before と分類し、closure は target の stored `before_sha256` を使用する（`2825-2831`）。
- その後の resume は古い transaction の after bytes を再び書く。

**成果物影響:** 外部 writer が戻した canonical 値を古い transaction が上書きし、台帳値と receipt/proof-chain の世代が変わる。

## 中断点の再列挙

| 中断位置 | 残る tree / state / ref | 復旧 |
|---|---|---|
| state temp 作成・write・file fsync 中 `spool_fold.py:2472-2480` | before / absent / tested tip。temp が残り得る | 再試行可能 |
| state replace 後・dir fsync 前 `2481-2486` | before / applied または電断時 absent / tested tip | どちらも再計画・resume 可能 |
| target atomic write 各回 `2972-2980` | before/after 混在 / applied / tested tip | `apply_fold` resume は可能。land の complete-shape gate `dev_wave_land.py:2380-2388` は直接は拒否 |
| GC unlink 各回 `2987-2995` | after / GC present/missing / applied / tested tip | `apply_fold` resume は可能。land 単独 recovery は全 GC missing まで拒否 |
| GC parent fsync `2996` | after / GC missing / applied / tested tip | recovery A |
| stage 後・commit 前 `dev_wave_land.py:1972-2007` | after / applied / tested tip、index staged | resume preflight が staged 状態を拒否し、land rollback 後の再試行が必要 |
| commit 直後・mark 前 `2012-2013` | after / applied / fold child | recovery B が mark を修復 |
| mark の検査中 `spool_fold.py:3156-3162` | after / applied / fold child | recovery B |
| mark atomic temp write/fsync 中 `3163-3167` | after / applied または committed / fold child | 両 phase とも recovery B |
| postcondition 中 `dev_wave_land.py:2018-2026` | after / committed / fold child | recovery B |
| finalize 検査中 `spool_fold.py:3181-3187` | after / committed / fold child | finalize 再試行可能 |
| finalize unlink 後・dir fsync前 `3188-3189` | after / absent / fold child | **現行 protocol では自動復旧不能** |
| finalize fsync 後・成功応答前 | after / durable absent / fold child | **結果再取得不能。state-absent recovery が必要** |
| rollback update-ref 後 `dev_wave_land.py:1788-1797` | after / applied・committed / rollback ref | **自動復旧不能** |
| rollback read-tree 後 `1798-1803` | tracked before・GC missing / state 残存 / rollback ref | **第三状態で自動復旧不能** |
| rollback restore 後 `1804-1805` | before・GC present / state 残存 / rollback ref | **A/B 外で自動復旧不能** |
| rollback state unlink 後・fsync前 `1828-1829` | before・GC present / absent / rollback ref | process crash は再 land 可。電断時の state 復活は未処理 |
| rollback fsync 後 | before・GC present / durable absent / rollback ref | 再 land 可 |

## phase・HEAD・state の矛盾行列

| phase / main / payload shape | 現挙動 |
|---|---|
| applied / tested tip / partial before-after | state load は可能だが land の complete-shape gateで拒否。`apply_fold` の先行 resume が必要 |
| applied / fold child / complete | identity → mark repair → finalize。closed |
| committed / fold child / complete | identity → finalize。closed |
| committed / tested tip / complete | recovery A が applied を要求して拒否。ref durability failure時の残骸 |
| applied または committed / unrelated child | commit identity の parent/tree gateで拒否 |
| 別 transaction state | parser が transaction ID を payload から再計算し、mark/finalize も ID 不一致を拒否。ただし競合 TOCTOU は残る |
| 別 wave の同じ parent/tree/meta commit | commit 自体は wave_ref/transaction ID を持たないため受理可能 |
| 同じ result bytes を作る別 plan | transaction ID は異なり得るが、commit identity は同じ equivalence classを受理する。canonical 値は同じだが provenance 上の transaction 識別は失われる |

以上より、path/blob/mode の構造検査自体は堅い一方、**lifecycle の終端冪等性、state CAS、手動 commit 排除、noop 時の canonical gate**は land 前に閉じる必要があります。