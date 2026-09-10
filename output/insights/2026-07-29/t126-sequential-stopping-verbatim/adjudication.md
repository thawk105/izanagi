authority: none
default_effect: no-state-change

# [T-126] 段 4 裁定 — 実装しない・新事実付き再裁定待ち

## 結論

本 wave ではコード・テストを実装しない。2026-07-27 の「設計 v2 を採用し実装へ進む」という
ユーザー裁定は取り消さず、裁定時点で未見だった N1〜N4 を添えて再裁定へ返す。段 5・6 は
`DW-S04` に従いスキップする。

## 新事実

1. **N1 — 現 tracked input は formal headline source になれない。**
   実在発火例 `p3-s8a-trigger-sweep-balanced-sweep-c2d838b8` の committed pair は、
   親の再計算で faster +3.417%、`p=0.0121858`、`near_floor=True` を満たす。しかし D47 は
   8a 軸提案 sweep を headline の入力から除外しており、SPRT が reproduced でも formal headline
   へ昇格できない。
2. **N2 — 設計 §8 の live positive control と production admission が両立しない。**
   既知の非再現 pair は floor 内であるため、通常の near-floor headline admission を通らない。
   formal headline へ昇格不能な qualification-only series は、承認済み設計に存在しない。
3. **N3 — gate の正式 consumer が未確定。**
   planner の sidecar `layer3_promotion` 案は、現 formal Layer3/headline producer の必須 consumer
   ではない。単に sidecar を追加しても、gate を通らない既存経路を止められず恒真な保証になる。
4. **N4 — 現環境では live qualification を閉じられない。**
   現 host は Pegasus login node で重い perf 計測を行えない。Pegasus env contract は
   `allow_resume=false`、既存 S8a driver は linux-baremetal 固定であり、planner の
   「1 round / process + resume」案をそのまま実行できない。

N1〜N4 は 2026-07-27 の採用裁定 package に存在しなかった。N1 の数値自体は親と統計レビューが
独立に再現し、攻撃を refute した。

## 所見の裁定

| 所見 | 裁定 | 採否・scope |
|---|---|---|
| tracked pair は +3.417% / `near_floor=True` ではない | refuted | 実 WAL と現 comparator で再現済み |
| D47 由来 pair を formal headline positive input にできる | real / BLOCKER | source eligibility の追加裁定が必要 |
| known non-repro pair を通常 admission へ投入できる | real / BLOCKER | qualification-only namespace なしでは不可 |
| sidecar gate だけで formal promotion を止められる | real / BLOCKER | authoritative consumer が必要 |
| code landing と activation の prose 分離で qualification hold になる | real / BLOCKER | machine-readable hold が必要 |
| observed boot-id が 2 種以上という述語は設計より過剰 | refuted | 設計の multi-boot 条件と同値 |
| `>`→`>=` / `<`→`<=` は有効な SPRT 境界 mutation | refuted | 有限系列で等価なため F28 を満たさない |
| exact order / 30 分間隔は片側 timestamp だけで検査できる | real | 両 COMMIT timestamp と seed permutation が必要 |
| variant identity だけで series identity を閉じられる | real | full src token、BUILD refs、provenance SHA が必要 |
| append-only ledger は単純な sidecar append で十分 | real | round FSM、transaction lock、capability 境界が必要 |

統計相談は real 6 / refuted 2、proof/consumer 相談は real 10 / refuted 3。上表は重複を統合し、
実装停止または将来 plan の修正に効く項目だけを抜粋した。

## plan v2

1. 本 wave は docs のみとし、production code、test、mutation matrix、受入全走を変更対象にしない。
2. 推奨する再裁定は **qualification-first amendment**:
   - formal headline へ構造的に昇格できない専用 qualification series を定義する。
   - 既知の非再現 pair で live positive control を取得する。
   - qualification receipt を machine-readable hold の解除条件にする。
   - production gate と authoritative consumer は別 wave で実装する。
3. 代案は、headline-eligible な 8b near-floor artifact が自然発生するまで待つ。
4. D47 の eligibility と formal Layer3/headline authority まで同時に拡張する案は、受理集合と
   proof authority を同時に変えるため非推奨。採る場合は D96 の新判断と境界テストが必要。

## 変異

実装しないため本 wave では事前登録しない。planner の境界演算子 mutation は有限系列で
出力が変わらず、単一理由性を持たない。将来 GO 後に新しい brief / plan / review から再登録する。
