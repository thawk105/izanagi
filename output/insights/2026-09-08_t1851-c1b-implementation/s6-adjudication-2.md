# [T-1851] C1b 段 6 裁定 (2 巡目) — 焦点再レビューの所見を裁く

対象 commit は `2cb24ead5` (fix 1 巡目まで含む)。逐語は
`/work/1/SFC/tanab/dev-wave-jobs/2026-09-08_t1851-c1b/s6-rereview.md`。

**判定 `no-go`。R-1〜R-8 は closed 7 件・partial 1 件 (R-3)・regressed 0 件。**
再レビューは **fix 自身が入れた新規所見 4 件** (blocker 1 / must-fix 3) を出した。
**全件 real と裁定し、全件 fix する。**

## 1. 1 巡目の成果は保つ

R-1・R-2・R-4・R-5・R-6・R-7・R-8 は closed。**この 7 件を壊す変更をしてはならない。**
再レビューが「攻撃したが破れなかった」と明記した性質も不変条件として保つ。

- legacy の公開 3 引数 sealer は遅い snapshot を許すが、正当な launcher-origin capability を
  持たないので公開 adapter から publish できない (契約 6.4 の除外内)
- stateful `Mapping` の `get()` と iteration を分ける R-4 攻撃は、launcher と sealer が同じ
  canonical campaign-record bytes を読むため再現しない
- launcher 所有の protocol / opened source の snapshot はすべて builder より前にある
- R-8 の条件変更は pre-probe competing だけを追加受理し、通常 capture の座標検査を緩めていない
- v1 terminal key は exact 24 のまま、retryable reason は空、既定 reason field は `failure_reason`。
  R-7 の正規化は v1 へ漏れていない
- 3 commit 全体で、許可した 2 箇所以外の期待値の反転・緩和・skip・xfail・削除・golden 更新は無い

## 2. 新規所見の裁定

| # | 出所 | 内容 | 裁定 |
|---|---|---|---|
| **S-1** | 新規 1 + R-3 partial | **`external_evidence_sha256` が canonical evidence に保存されず、durable replay で再照合されない。** 発行時 (`s8b_attempt_registry.py:3157-3169`) にしか照合が無い。正当な evidence file の `probe_before_sha256` だけを偽 digest へ変え、canonical bytes と row の `terminal_evidence_sha256` / `event_sha256` を作り直せば、probe summary・E1 projection・契約 7 の 11 項目・binding・durable identity をすべて保ったまま replay に受理される。**observation していない source digest が proof chain に入る。private issuer は不要** | **real・blocker。** R-3 を partial から closed へ進める修正と同一である。契約 7 が守ろうとした「crash 後の権威」を replay 側で完成させる |
| **S-2** | 新規 2 | **検査より先に JSON 往復させるので exact-type gate が source object に対して発火しない。** rep sink の `rep_index` / `returncode` に `int` subclass や `IntEnum` を入れると、旧経路では `type(v) is int` が偽で rep integrity failure だったものが、canonical 復元で通常の `int` になり `rep_integrity_failures == 0` の `observed` が作れる | **real・must-fix。** **v2 の受理集合を意図せず広げている。** 規律 2 に抵触するので必ず閉じる |
| **S-3** | 新規 3 | **F1 と F3 の変異テストが単一理由に帰属しない。** どちらも `_RecorderRegistry.record_sealed_attempt_terminal()` (無条件に送出する fake) を使うため、対象 gate を外しても後段の fake が必ず拒否する。**冗長 gate による見かけの kill** | **real・must-fix。** `DW-M01` / `DW-M03` の要求そのもの。**この状態で変異 matrix を走らせても意味がないので、変異走の前に必ず直す** |
| **S-4** | 新規 4 | **F2 の変異が実効 gate を狙っていない。** builder 前 snapshot が権威なので、builder へ元 sink を共有しても攻撃は成立しない。mutant が赤になるのは防御多重化の assertion によるもので、受理可否は変わらない | **real・must-fix。** `_snapshot_opened_source()` の削除・builder 後への遅延・sealer による builder-exposed sink 再読のいずれかへ再照準する |

## 3. 変異事前登録の改訂 (DW-M01)

F4・F5・F6・F7 は**単一帰属を確認済み**なのでそのまま登録を維持する。

- **F4** — 発行の 3 負例が実 slot 検査を直接狙い、replay 側にも独立した 3 負例がある
- **F5** — leaf の capture/count 正負対が `_assert_mutual_consistency()` を直接通る。replay 負例もある
- **F6** — helper 直呼びで legacy 名と v2 基底名を別々に比較する
- **F7** — test seam が全 method を real adapter へ転送し、origin gate を外すと real terminal publish へ到達する

**F1・F2・F3 は登録を取り下げ、次へ再照準して登録し直す。**

| ID | 再照準後の変異 | 単一理由にするための条件 |
|---|---|---|
| F1' | 副作用前 snapshot でなく `reservation.protocol` を builder 後に再読する形へ戻す | **accept-only な fake recorder** (sealed draft を保存して正常 return する) を使い、mutant では偽 draft が最後まで到達して観測できる形にする。または private reservation snapshot を直接 sealer へ渡す**純関数 test** へ分離する |
| F2' | `_snapshot_opened_source()` を削除する / builder 後へ遅らせる / sealer が builder-exposed sink を再読する | 同上。mutant で偽 terminal が accept-only recorder まで到達すること |
| F3' | `campaign_record` の単一 snapshot を外し launcher/sealer の二重読みへ戻す (SplitRecord 攻撃) | 同上 |
| **F8** | **S-1 の修正で足す replay 側の external evidence 再照合を削除する** | replay 負例だけが赤になること |
| **F9** | **S-2 の修正で足す canonical 化前の exact-type 検査を削除する** | `int` subclass / `IntEnum` の負例だけが赤になること |

**「元 sink が変わっていない」といった防御多重化の assertion は構造テストとして残してよいが、
単一理由の security kill には数えない。**

## 4. 停止条件 (1 巡目と同じ)

- 既存テストの期待値を変更しない。許可した意味変更 2 箇所を超えない。
- v1 の受理集合を 1 bit も変えない。
- 1 巡目で closed になった R-1・R-2・R-4・R-5・R-6・R-7・R-8 を壊さない。
- 所有外 file に変更が要ると判明したら実装せず報告する。
- **`DW-O16` により fix は 3 巡が上限。本巡は 2 巡目である。**
