# 段 4 裁定 — dev-wave-t1721-noncertifying-a1

base = local main `dd66213978d3d30eed567484ec013216bff6926b` (裁定時の main = `a0a0cdf46`)

## 裁定 0 — 遷移

**実装しない。** `DW-S04` に従い段 5・6 を飛ばし `4→7→8→9` とする。
実装面の差分がゼロなので `DW-S04` により変異 matrix を免除する。**受入全走は免除しない。**

## 裁定 1 — 昇格経路 (段 2 の停止根拠)

**real。親が一次証拠を独立に再現した。**

親 probe (`probe_rewrap.py`、repo 外の temp dir にだけ書く read-only 検査) の実測:

```
captured closure commit = dd66213978d3d30eed567484ec013216bff6926b
closure paths           = 25
inner identity declares non-certifying = non-certifying
activation serial = 1
activation state_sha256 = f78072854651b316e1f2d78c2dfc58bfd995160515ed721a80a267ced54cd3ed
environment contract sha256 = 1b2ee85346a4c867754bda497b23d649e66027011167cfb0f9c7f9a1a5fa1dc7
v2 re-wrap ACCEPTED the non-certifying inner identity = True

LOCK-ONLY CERTIFIED GATE: PASSED
  state       = E1
  reason_code = recorded-closure
  epoch       = E1:ab51c89f52ff51fe61e81 ...
```

- **公開情報だけで組める。** closure は `contract_loader_binding.capture_contract_loader_binding()`
  が批准を検査せずに返す。activation state は `env_contract.verified_current_activation_state()`
  が公開関数で返す。非認証 run に固有の秘密も発行 capability も要らない。
- **schema 層は中身を見ない。** `campaign_lock.py:154 _validate_identity` は identity の
  exact 5 key と型だけを検査し、`search_config` には `dict` であることしか要求しない。
  `artifact_class` も `promotion_prohibited` も拒否しない。
- **consumer 層の lock-only 経路は批准を見ない。** `artifact_admission.py:868
  require_campaign_verifier_epoch` は campaign.lock だけを読み、記録 map と現在 map の
  equality だけで E1 を出す。批准台帳を 1 度も参照しない。
- 段 3 lens A が別 context で得た値 `E1:ab51c8...` と親の値が一致した。**2 独立実行で同値。**

## 裁定 2 — 第 3 の接ぎ目

**存在しない (real)。** 決定的なのは lock-only E1 経路である。この経路は
`campaign_lock.py` / `contract_loader_binding.py` / `artifact_admission.py` の 3 file だけで
判定が閉じており、編集可能面 (`ident.py` / `wal.py` / `env_contract*.py` / `pipeline.py` /
`loop.py` / `layout.py` / `replay.py`) を 1 つも通らない。3 file はいずれも稼働中
`dev-wave-t1629-ratification-broker` の所有である。

部分的に `ident.py` / `wal.py` だけへ拒否を入れる案は**採らない**。full admission 経路は
閉じるが lock-only 経路が開いたまま「閉じた型がある」という表示だけが立つため、
現状より危険になる (lens A の指摘。親も同意)。

## 裁定 3 — D1038 の着手条件

**満たせない。したがって作らない。**

D1038 の逐語は「認証済みの consumer へ昇格できないことを鍵・記録・schema・consumer の全層で
固定できること。field の除去や付け替えで昇格できる作りしか取れないなら、作らない」である。

- 鍵層: v2 authority に署名鍵も非公開 capability も無い → 固定できない
- 記録層: WAL に hash chain が無く (`wal.py:14-15` に明記)、COMMIT の `contract_sha256` は
  公開値なので付け戻せる → 固定できない
- schema 層: 閉集合は編集禁止 file の中 → 固定できない
- consumer 層: lock-only E1 と view 発行は編集禁止 file の中 → 固定できない

**これは D1028 の不採用ではない。D1038 が自ら定めた停止条件の発火である。**
D1028 は「型と投入器を同じ変更単位で作る」と定めたが、D1038 は「作れないなら作らない」を
先行条件として置いている。本 wave は後者を実行した。

## 裁定 4 — D1028 との関係 (親は承認済み裁定を覆さない)

`DW-S04` に従い、承認済み裁定を親が不採用にはしない。本 wave が止めた根拠は
**裁定時に見えていなかった新事実**である。次を確認した。

- `docs/decisions.md` / `docs/failures.md` / `docs/worklog.md` の全文検索で、
  「非認証宣言つき identity を v2 で包み直すと lock-only certified gate を通る」という事実は
  **1 件も記録されていない**。近いのは `decisions.md:8681` の一般論だけで、本経路の記述ではない。
- D1028 の本文は「型と consumer を同時に作ると、型が実際に昇格不能かを consumer 側で検査できる」
  と書いている。**検査した結果が「昇格不能にできない」だった**という事態は想定されていない。

したがって新事実を添えて**ユーザー再裁定待ち**へ戻す。

## 裁定 5 — 終端の選択

**(ii) を採る。** ただし「t1629 が本件を解くまで待つ」ではなく、**所有解除のための順序待ち**である。

- (i)「型を作らない」で確定させるのは**早い**。所有解除後も 4 層固定が不可能だという証拠は無い。
  今わかったのは「編集禁止面を触らずには不可能」であって「原理的に不可能」ではない。
- (iii)「今できる部分だけ進める」は成立しない。投入器のみは D1028 違反、型の一部のみは
  D1038 の 4 層条件未達、provenance の先行更新は最終 hash 未確定で不可。
- D1028 が却下したのは「D905 の着地を解決策として待つだけ」である。本件は稼働 wave の
  land 待ち (時間単位の順序制約) であり、却下の射程外と裁定する。

## 裁定 6 — 再開時の scope (段 2 の A/B 分割は破棄)

段 3 lens B が、段 2 の A/B 分割では端から端まで経路が通らないことを示した。**採用する。**
再開 wave は次を **1 land 単位**にまとめる。

1. 非認証成果物型 (鍵・記録・schema・consumer の 4 層)
2. **A-1 の campaign config への型の結線** — 現行 `paper_story_a1_paired.py:692
   campaign_config()` は新 class を設定しない。これが無いと A-1 は既定 certified のまま
   批准 gate で止まる
3. 投入器 (submit script + acquisition receipt producer)
4. **新 terminal stage への collector 対応** — 現行の集計器は stage 列の末尾を
   `STAGE_COMMIT` に固定している (`paper_story_a1_paired.py:1706`、`:2120`)
5. **scheduler completion receipt の producer** — tracked tree の全数検索で **0 件**。
   materializer は exact 10-field の completion document を必須にする (`:1095`)
6. **materialize の起動手** — `run_materialize()` の呼び手が存在しない (`:3312`)
7. 非認証結果を限定付き観測として読む reader / pointer
8. 波及する凍結 provenance の再生成 — `artifact_admission.py` の bytes は
   fig4 の validator SHA として再導出される (`fig4 provenance:58`、
   `test_s1_9pair_figure_provenance.py:667`)

## 所見の裁定表

| # | 所見 | 出所 | 判定 | 採否 | scope |
|---|---|---|---|---|---|
| 1 | v2 再包装で非認証 identity が certified view を得る | 段 2 / lens A / 親 probe | **real** | 採用 | 内 (停止根拠) |
| 2 | lock-only E1 経路は編集可能面を通らない | lens A / 親 | **real** | 採用 | 内 |
| 3 | 第 3 の接ぎ目は無い | lens A | **real** | 採用 | 内 |
| 4 | (P1) 既存閉包 file 内だけで閉じる | 親 brief | **refuted** | 撤回 | 内 |
| 5 | (P2) 判定の座は `ident._capture_current_loader_binding` | 親 brief | **refuted** (批准 producer の座としては real、再包装 consumer の座ではない) | 撤回 | 内 |
| 6 | (P3) 宣言を campaign 同一性へ入れる | 親 brief | **real だが不十分** | 条件付き採用 (再開 wave の必要条件) | 外 |
| 7 | 親 M5 の「`declared_use_class` は pipeline と layout にしかない」 | lens A | **一部 refuted** — `loop.py:242-263`、`buildcache.py:2009-2071`、複数 driver にもある | 訂正 | 内 |
| 8 | 親 M8 の「予約 key で id が変わらない」 | lens A | **表現が不正確** — key を持つ campaign の id は変わる。既存凍結 campaign が不変なのは real。正しい形は条件付き serialization | 訂正 | 内 |
| 9 | A/B 分割では端から端まで通らない (3 箇所の切断) | lens B | **real** | 採用 | 外 (再開 scope へ) |
| 10 | acquisition receipt の述語表に 5 件の落ち | lens B | **real** | 採用 | 外 (再開 scope へ) |
| 11 | qsub contract が driver と job body で二重定義 | lens B | **real** | 採用 | 外 (再開 scope へ) |
| 12 | `submit_host` を `hostname` と `hostname -f` のどちらで作るか未定 | lens B | **real** | 採用 | 外 (再開 scope へ) |
| 13 | fig4 provenance の validator SHA 再生成が scope から漏れ | lens B | **real** | 採用 | 外 (再開 scope へ) |
| 14 | 段 2 の「禁止 2 file を編集すれば十分」 | lens A | **根拠不足** — marker を inner identity から除去して v2 を再生成できるため、署名された identity 束縛か改変不能な外部台帳まで要る | 採用 (再開 wave の前提) | 外 |

## 変異事前登録

実装面の差分がゼロのため `DW-S04` により免除する。
段 2 が挙げた M-CERT-OVERALLOW / M-SUB-* は本 wave では登録しない。
**再開 wave が同じ候補から事前登録をやり直す** (単一理由性の再確認を含む)。

## 成果物影響 (DW-G05)

- **止めた場合:** A-1 の値、レポート行、submission / completion 台帳はいずれも 0 件のまま。
  paper-story の A-1 系列は前進しない。これは既に現状であり、本 wave が悪化させるものではない。
- **止めずに部分実装した場合:** certified 選択の受理集合が開いたまま「閉じた非認証型がある」
  という表示だけが立つ。実測を伴う本物の campaign を貼り替えるだけで certified になるため、
  偽造の費用が下がる。規律 2 に直接抵触する。
