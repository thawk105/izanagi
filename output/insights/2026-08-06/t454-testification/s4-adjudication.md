# 段 4 裁定 — [T-454] テスト化 pass

親が段 2 プランと段 3 レンズ A / B の全所見を real / refuted に裁定し、plan v2 を確定する。

## 0. 所見の裁定 (real / refuted)

段 3 の所見は **A-01〜A-10、B-01〜B-10 の 20 件すべて real** とする。refuted は 0 件。
親前提の判定も両レンズの結論を採る。

| 前提 | 親の当初 | 裁定 | 根拠 |
|---|---|---|---|
| P1 (docs を 1 byte も変えない) | real | **refuted (ただし採用)** | ユーザー発話から「全 Markdown 凍結」は導けない (A-10, B-07)。ただし段 7 の worklog / insights fragment は書く。`docs/dev-wave/**` を触らないという**運用上の選択**として維持する |
| P2 (待ち手 3 条は tool 機械強制で足りる) | real | **refuted** | tool 利用が強制されず、`condition_id` が論理条件でない (A-01, B-06) |
| P3 ((d) は追加不要) | real | **refuted** | strict-superset vector が未固定。`==` → `<=` 変異が既存テストで生存する (A-08, B-09) |
| P4 (新規 file 1 本に閉じる) | real | **refuted** | 既存 `tools/codex_worker_launch.py` (2,591 行) の二重投資、D100 / T-184 と所有衝突 (B-04) |
| P5 (受入は dispatch 経路) | real | **real** | 両レンズ一致 |
| P6 (S4 を byte 会計へ組替え) | real | **real (未履行)** | 段 2 は 0-byte 節棚卸しで終わり、O01/M05 の提案 diff を出していない。**親が段 4 で履行する** |
| P7 (tool が DW-O01 を丸ごと吸収) | real | **refuted** | 4 文中 (i) は 1 文だけ。採用条件と log/通知禁止は自己申告に残り、wrapper 形は壊す (A-04) |
| P8 (O04 / O10 の削除提案をしない) | real | **real** | 両レンズ一致 |
| N1 (3 回目の棚卸しは無駄) | real | **real (一般化は refuted)** | 全件三巡は冗長だが、前回 anchor 以後の delta 監査は必要。O10 は監査後に実発火した (A-09) |
| N2 (機械化だけが恒久的に空ける) | real | **refuted** | 先行 wave の機械化対象節は実測 **+70 bytes** だった。機械化は削減の必要条件であって十分条件でない (B-03) |
| N3 (先行 wave が O01/M05 を名指し) | real | **refuted** | R3 の名指しは M08 / O11 / O20 / O23 であり O01・M05 pgrep ではない (B-10) |
| N4 (S2 は先行判断の反転) | real | **real** | 両レンズ一致 |

## 1. 中核の裁定 — S1 / S2 は実装しない

**両レンズが独立に同じ blocker へ到達した (A-01 / B-02)。** 新 tool を追加しても、
現行 `DW-O01` (`docs/dev-wave/operations.md:6-12`) が raw `codex exec` 手順を正規として残し、
dispatcher も特定 tool の使用を要求しないため、受理集合は `旧経路 ∪ 新経路` のまま縮まらない。
prose を pointer へ畳む根拠が立たず、**回収 bytes は 0 のままである。**

新 tool を権威経路にするには次の 3 つが同時に要る。

1. `docs/dev-wave/operations.md` の `DW-O01` 本文の置換 (= **削除実施**)
2. 「新規 dev-wave 子は必ず新経路」という長期 interface の決定 (= **新 D 発効**)
3. D100 / T-184 が所有する既存 launcher の `DW-O01` 結線との調停
   (`docs/decisions.md` D100、`docs/phase3.md:683-695`)

**(1) と (2) はユーザーが本 wave で明示的にまとめ裁定へ留保したものそのものである。**
したがって親は S1 を実装せず、択一を裁定パッケージへ返す。**「任意 helper として作る」案も採らない** —
lens A が指摘するとおり、その場合は機械化・prose 吸収・byte 回収を一切主張できず、
既存 launcher の機能を重複実装するだけの純損失になる (B-04)。

S2 (harness 生死 probe) も同じ理由で実装しない。加えて固有の欠陥がある。

- probe は point-in-time であり、lock 版 ABA (harness A 終了 → 別 wave の B が同 lock を取得 →
  probe は 0 のまま) を防げない (A-05)。
- cross-node では `tempfile.gettempdir()` の lock namespace が分かれ、生きた harness を
  死亡と判定しうる (A-03、D130 が未実測と警告済み)。
- shared probe の連打で本走を starvation させられ、「probe は本走を拒否してはならない」を
  無条件に満たそうとすると `LOCK_EX|LOCK_NB` の fail-closed が fail-open へ倒れる圧力になる (A-06)。

S2 の価値は `DW-M05` の pgrep 3 行を pointer へ畳めることに尽きるが、それも (1)(2) を要する。
**設計択一として裁定パッケージへ返す。**

## 2. 実装する唯一の面 — (d) strict-superset test

`tools/mutation_harness.py:1193` は `failed_keys == expected_keys` の完全一致で KILLED を決める。
既存テストは互いに素な集合 (`expected={one}`, `failed={two}`、
`orchestrator/tests/test_mutation_harness.py:341-350`) しか固定していない。
したがって `failed_keys == expected_keys` → `expected_keys <= failed_keys` の弱化変異は
**既存テスト全部を通過して生存する**。

- 親の段 1 実測「純増検出力ゼロ」は誤りだった。誤りの型は
  「既存実装 + 既存テストがある」を「その性質が固定されている」と読み替えたことで、
  これは `DW-S01` の「機構名でなく性質で検索する」義務への直接違反である (B-10)。
- この面は docs 変更も新 D も要さず、他タスクとの所有衝突もない。
- 実装は `orchestrator/tests/test_mutation_harness.py` へのテスト追加のみ。
  **production コードは変更しない。**

### gate の禁止 (署名 + 通る正例)

- 禁止する挙動: `_observed_status(*, result, failed, expected, repo) -> str`
  (`tools/mutation_harness.py:1177-1193`) が、
  **実失敗集合が期待集合の真上位集合のときに `"KILLED"` を返すこと。**
- 通る正例: `expected = failed = {"tests/test_gate.py::test_gate[one]"}`、`rc=1` →
  `"KILLED"` のまま。この正例が壊れたら過剰拒否である。

### 成果物影響 (`DW-G05`)

実装しない場合: 期待 node をすべて含む余分な赤を伴う変異を KILLED と認定でき、
**変異台帳の `status` と、それを引用する worklog の「n/n KILLED」件数が実行と対応しなくなる。**
実際 (244) と (254) の両 wave で「実赤 node が事前登録の上位集合」の MISMATCH が発生しており、
そこで `<=` 実装だったなら偽の KILLED として通っていた。

## 3. plan v2

| 単位 | 所有 | 内容 |
|---|---|---|
| U1 | `orchestrator/tests/test_mutation_harness.py` のみ | (d) strict-superset test の追加。production 不変 |

- 単位は 1 本のみ。段 2 が求めた U1→U2 直列化は S2 を実装しないため不要になり、
  lens B の B-08 (dogfood のための直列化は損) も同時に解消する。
- 段 5 は Codex `role=author`、`reasoning=high`、`sandbox=workspace-write` を 1 本。
- 段 6 は敵対レビュー 2 本 (`DW-S06-A`)。
- S4 (byte 会計・提案 diff・候補分類) は**親が docs 外の insights 成果物として作る**。

## 4. 変異事前登録 (`DW-M01` / `DW-M08`)

本 wave は**テスト強化だけの wave** なので、`DW-M08` に従い
「新テスト」と「変更前 HEAD 版テスト」の双方へ同じ変異を走らせ、差分を示す。

| ID | 位置 | old → new | 期待 status | 期待 node | 単一理由性 |
|---|---|---|---|---|---|
| MU-1 | `tools/mutation_harness.py:1193` | `failed_keys == expected_keys` → `expected_keys <= failed_keys` | KILLED | 新設 node (段 5 確定後に実 nodeid で登録) | collection preflight は `expected ⊆ collected` しか見ず実失敗集合を見ない。他層に同入力を拒否する gate なし |
| MU-2 | 同上 (**変更前 HEAD のテスト版で再走**) | 同上 | SURVIVED | (空) | 新テストだけが検出することの実証。`DW-M08` 要求 |
| MU-3 | `tools/mutation_harness.py:1193` | `return "KILLED" if ...` → 常に `"MISMATCH"` | KILLED | 既存 KILLED 系 node (実測後に登録) | 過剰拒否を検出する**正例** (`DW-M01`)。等集合が KILLED であり続けることを固定 |

- 期待 node は段 5 完了後に collection の実 nodeid (parametrize 接尾辞込み) で確定してから登録する。
  実赤が期待の上位集合になった場合は `DW-M02` / `DW-M08` に従い初回台帳を erratum として残し、
  実測 node で取り直す。
- 変異走行は統合 commit 後 (`DW-O19`)。走行中は tree へ書かない。

## 5. 裁定パッケージへ返す項目 (段 7 で insights に凍結、実施しない)

| # | 項目 | 種別 |
|---|---|---|
| R1 | `DW-O01` を単一経路 (新 tool / 既存 `codex_worker_launch.py` 拡張 / 現状維持) のどれへ結線するか。T-184 / D100 との所有調停込み | 設計択一 |
| R2 | R1 で単一経路化する場合の `DW-O01` 置換本文と **−159 bytes** | 削除実施 (要裁定) |
| R3 | `DW-M05` の pgrep 3 行を probe pointer へ置換する本文と **−48 bytes**。前提として S2 の ABA / cross-node / starvation を設計で閉じること | 設計択一 + 削除実施 |
| R4 | 待ち手規約 3 条を docs へ入れるか、R1 の tool 側へ入れるか | 設計択一 |
| R5 | 回収見込み −207 bytes に対し、既知の追記待ちは 274 bytes (242-244) + 142 bytes (237) + F112/F124 + T-505 で**依然不足**。優先順位と見送り分の確定 | 予算裁定 |
| R6 | 本 wave の brief から脱落していた T-454 既割当分 (T-505 の削除リストと新 D 起草、F112/F124 の `DW-S06-B` 追記、`DW-S01`/`DW-S02` 撤回 142 bytes) の扱い | scope 復旧 |
| R7 | L2 削除候補は 3 度目もゼロ。今後は全件棚卸しでなく「前回 anchor 以後の delta 監査」へ変える | 手順変更 |

## 6. 段の遷移

実装面が存在する (U1) ため `4→5→6→7→8→9` を通常どおり通る。
S1 / S2 を実装しないことは scope の縮小であって、段の省略ではない。
