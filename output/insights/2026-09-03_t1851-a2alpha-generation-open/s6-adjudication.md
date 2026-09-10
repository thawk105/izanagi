# 段 6 レビュー所見の裁定 — [T-1851] A2α

2026-09-03 JST。HEAD `69497db66`。材料 = レビュー C (所見 22)、レビュー D (所見 7 + 変異 16 件の独立判定)。

## 親が実測した検査 (レビュー時点では未実施だったもの)

- `python3 tools/check_ai_provenance.py` (全史): rc=0。
- `orchestrator/tests/test_attempt_registry_core_s8b_profile.py` 単独走: **89 passed**、rc=0。
- `orchestrator/tests/test_s8b_attempt_registry.py` 単独走: **82 passed**、rc=0。
- consumer 閉包の焦点走: 実行中。
- いずれも D612 の opt-in 上書き (`IZANAGI_DISPATCH_QUEUE_WAIT_TIMEOUT_OVERRIDE=3600`、
  `IZANAGI_DISPATCH_OVERALL_GRACE_OVERRIDE=600`) を付けて計算ノードへ投入した。
  上書き前の rc=16 は `queue-wait-timeout` の infra 失敗であって赤ではない。

## real・採用 (fix する)

### F1 (must-fix) — v2 の start-only resume に TOCTOU 窓がある

[レビュー D 所見 4 の一部] marker を lock 内で検証した後、lock の外で `classify_attempt()` を呼ぶ。
**この窓は本 wave が新たに作り込んだものである。** A1'/B1 が引き継いだ journal の窓とは別。

**裁定: 閉じる。** 同じ lock interval 内で分類まで到達できないなら、**v2 の start-only resume を
fail-closed で拒否する**方を採る。窓を開けたまま「capability に束縛されている」と読める状態を残さない。
拒否を選ぶなら exact 署名と正例対照を置く。

成果物影響: 放置すると、予約後に失効した権限でも分類 claim と receipt を台帳へ追加でき、
台帳行と後続参照の受理集合が広がる。

### F2 (must-fix) — v2 mutation の marker 束縛範囲が申告されていない

[レビュー D 所見 4 の残り] 予約と観測は `marker.use()` 経路だが、分類 claim / row と回復 row は
素の `_atomic_update()` を通る。

**裁定: 分類・回復を marker 経路へ移さない。** 前 wave が固定した E4 の境界 signature は
`_atomic_update_with_consumption_marker` と reserve / resume の marker 引数だけを名指しており、
分類・回復の束縛を要求していない。v1 も同じく素の `_atomic_update()` を使うので、v2 が v1 より
広くなるわけではない。**要求外の防壁を足さない (DW-G05)。**

**ただし部分的な閉包を「閉包」と読める状態で残さない。** 次を行う。

1. **どの v2 mutation が marker に束縛され、どれが束縛されていないかを exact に pin する test を置く。**
   束縛される側 (reserve / observation) と束縛されない側 (classification claim / row、recovery row) の
   両方を名指しし、現状を固定する。
2. 束縛されていない集合を「開いた窓」として報告に書く。**閉じたと書かない。**
3. 分類・回復まで marker で囲むかどうかは裁定パッケージへ送る (D1533 の「防いでいない範囲を明記する」形)。

成果物影響: 明記しないと、材料レポートが「v2 の全 mutation が capability に束縛されている」と
誤読され、実際には束縛されていない行が台帳へ入る。

### F3 (must-fix) — D1522 が S7/S8 (symlink 四層) で不充足

[レビュー C 所見 15 / レビュー D 所見 2] 新設 test の symlink は空 directory を指すため、
publisher 自身の既存世代分岐と「不完全世代」拒否で止まり、`_read_regular_bytes` /
`_ensure_durable_directory` / `_write_staging` / admission guarded writer まで到達しない。

**裁定: 下層の実体へ到達する直接検査へ作り直す。** D1522 の 3 条件をすべて満たすこと。

- 下層の実体を直接呼び、symlink に対して専用の例外を送出することを検査する。
- 上流を通る正常な入力で下層の実体を差し替え、その例外が下層の拒否 code へ写ることを検査し、
  **差し替えが実際に呼ばれたことを assertion で固定する。**
- 差し替えなしで成功する正例対照を同じテストに置く。

symlink の target は**完全な世代** (`registry.jsonl` を持つ real directory) にするか、
mkdir 後に symlink へ差し替える形にして、不完全世代拒否に mask されないようにする。

成果物影響: 四層を落とした変異がマスクされ、symlink alias による台帳参照のすり替えと
横断予算の二重計上を「防御済み」と誤認証する。

### F4 (must-fix) — D1522 が S11 (lock 生存 guard) で不充足

[レビュー C 所見 16] `_atomic_update_locked()` の live-lock guard を直接拒否検査していない。
唯一の直接呼出しは正常 lock の正例だけで、高位 test の差し替えは `marker.use()` 側の先行 guard で止まる。
`s8b_attempt_registry.py:1447` を消しても現行 node は赤にならない。

**裁定: F3 と同じ 3 条件で直接検査を置く。**

成果物影響: 下層 guard の退行を見逃すと、将来の直接 consumer から lock 外更新が可能になり、
試行台帳の順序と chain head が競合で変わりうる。

### F5 (must-fix) — fail-closed 防壁を `assert` 文で書かない

[レビュー D 所見 3 から派生] marker 必須の下流拒否が `assert consumption_marker is not None` に
なっている。**`assert` は `python -O` で除去される。** 防壁を `assert` で書くと、最適化実行で
防壁が消える。

**裁定: 防壁として機能している `assert` を明示的な例外送出へ直す。** 内部の型不変条件を表す
`assert` (レビュー C 所見 17 の codec 後 slot-type guard 4 箇所) はこの対象外で、そのままでよい。
**どれが防壁でどれが内部不変条件かを実装子が判定し、報告に列挙すること。**

成果物影響: `-O` 実行で marker なしの v2 予約が通り、capability に束縛されない start row が台帳へ入る。

### F6 (must-fix) — 変異事前登録 4 件の期待と fixture を直す

[レビュー D 所見 1・2・3・5] 段 4 で登録した M6 / M7b / M8 / M13 が実効的でない。**登録を直す。**

- **M6**: 単層を `SURVIVED` へ変更する。`_publish_registry_generation_create_only` の早期拒否、
  `_publish_create_only` の事前拒否、link race 拒否を**同時に**消す `M6b` を `KILLED` として追加する。
- **M7b**: F3 の test 作り直し後に再照準する。symlink target を完全世代にし、不完全世代拒否・
  既存 destination 拒否・enumerator の mask を変異定義へ明記する。**再照準しても kill node を
  名指しできないなら `SURVIVED` へ変更し、erratum を残す (DW-M02)。**
- **M8**: 期待は `KILLED` のままでよい。ただし fixture が measurement ordinal から
  `schedule_row_sha256` を作り直しているため、二 payload が schedule-row digest でも異なってしまう。
  **二 slot の `schedule_row_sha256` を同値に固定し、measurement ordinal だけが異なる形にする。**
- **M13**: 単層を `SURVIVED` へ変更する。早期 guard と F5 で直す下流拒否を**同時に**消す `M13b` を
  `KILLED` として追加する。marker なしの予約で start row が実際に追加されることを観測する。

成果物影響: 実効的でない変異を KILLED と記録すると、材料レポートが実在しない防壁を認証する。

### F7 (nit だが直す) — test 名と public annotation が実態とずれている

[レビュー C 所見 20 / レビュー D 所見 6]

- `test_v2_profile_is_rejected_by_public_mutation_but_slot_lookup_is_five_axis` は canonical v2 でなく
  validator を除去した forged profile の拒否を検査している。**実態に合う名前へ改名する。**
- `create_attempt_registry()` と `read_attempt_registry()` の public annotation が v1 slot / profile
  限定のまま。runtime は v2 を受理する。**annotation を実態へ合わせる。**

成果物影響 (annotation): 型検査付きの production caller が正当な v2 呼出しを表現できない。

## real・不採用 / 記録のみ

- [レビュー C 所見 17] codec 選択後の slot-type guard 4 箇所は production から発火不能。
  **裁定: 内部の型不変条件として残す。防壁と数えず、変異を登録しない。** コード変更なし。
- [レビュー D 所見 7] 規模が 1,329 changed LOC で段 4 の見積り上限 1,030 を 299 行超過した。
  **裁定: 受け入れる。** 超過はほぼ test 側 (production 710 / test 619) で、方向は正しい。
  ただし**見積りが下振れしたのは A1' から数えて 2 回連続**であり、insight に実測として記録する。
  fix 子には追加の予算を与えるが、上限を明示する。
- [レビュー D 所見 7 の後半] 新設が 9 個の大型複合 node に集中している。
  **裁定: fix で分割を強制しない。** ただし F3 / F4 で新設する D1522 の直接検査は、
  複合 node へ足さず独立 node にすること。変異の帰属が mask されるため。

## refuted

- [レビュー C 総括] 「非 land の A2α checkpoint としての blocker はなし」。**F1 は blocker 相当である。**
  新たに作り込んだ TOCTOU 窓は、land しないことを理由に残してよい不完全さではない。
  A1'/B1 が引き継いだ既存の窓とは性質が違う。
- [レビュー D 所見 4 の全体] 「v2 classification/recovery が marker を迂回する」を単一の blocker と
  する読み。**分割して裁定した (F1 = 採用、F2 = 束縛範囲の明記へ変更)。**
  分類・回復の marker 束縛は前 wave の境界 signature が要求しておらず、v1 と同等である。

## fix 子への予算

- 追加は **250 changed LOC 以内**を目安とする。超えるなら理由を報告に書いて止める。
- **F1〜F7 以外を直してはならない。** scope 外の改善・整理・一般化をしない。
