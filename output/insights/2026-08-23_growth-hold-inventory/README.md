# 成長比例保留 16 件の棚卸し — 判定を秒数から承認済み例外へ移した回

wave: dev-wave-growth-hold-inventory / 2026-08-23 / base main 4cbaf041

対象は `orchestrator/tests/growth_test_holds.py` の `_HOLD_ROWS` のうち
`test_codex_reasoning_ab.py` の 16 件に限定する。数値はこの対象内の値を示す。

## 裁定 — 再導入 14 / 削除 0 / 保留継続 2

判定は実行秒数で行っていない。既定は D335 (成長比例テストは恒久保留、削除は却下済み) で、
外したのは次の承認済み例外が実際に成立する node だけである。

- **D451**: 保留すると当該防壁を守る既定走行 node がゼロになる。
- **D452**: 変異事前登録の期待 node として正本に名指しされている。

逆に、安いことは外す根拠にしていない。保留継続の 2 件は 0.01 秒と 6.91 秒だが、
防壁が既定側に残るため保留を維持した。

## 引数の前提 2 件は実測で否定された

| 引数の前提 | 実測 |
|---|---|
| snapshot corpus の不在 | corpus は実在。セッション開始時 5,482 file / 5.13 GiB、約 50 分後に 5,505 file |
| 理由は corpus 不在 / rollout 待ち | 登録 reason の本文はどちらも成長比例コスト。前提は変数名からの推測 |

corpus が 50 分で 23 file 増えたのは、本 wave 自身が起動した codex 子が rollout を
書いたためである。D463 の「repository の通常運転で単調に増える集合」を実地で観測した形になる。

さらに、既定で走る `test_real_rollout_collector_golden_is_source_bound` が
固定 rollout を無防備に読むため、**corpus が無ければ既定スイートが落ちる**。
「corpus の不在」は二重に成り立たない。

## 親の実測 (すべて本 worktree、2026-08-23)

| 測定 | 値 |
|---|---|
| corpus `rglob("rollout-*.jsonl")` | 0.045 秒 / 5,505 file |
| tip index `git ls-files --stage -z` | 0.031 秒 / 13,908 entry |
| `derive_independent_golden` (pin 有り) | 0.139 秒 |
| `_find_rollout` (pin 有り) | 0.036 秒 |
| `_find_rollout` (pin 無し、cold) | 329.754 秒 |
| 16 件 opt-in 実走 | 20 items 全 PASS / 544.05 秒 |
| 既定走行の基準線 (保留有効、同 file 単独) | 347 passed / 20 skipped / 135.45 秒 |
| `benchmark_snapshots` fixture setup | 15.32 秒 |

すべて同一ノードで取得した一点観測であり、一部は他の走行と同時に実行している。
**恒久値として引用してはならない。** cold 329.754 秒と warm 約 18.5 秒から
成長率を外挿してはならない (傾き・反復分散・page cache 条件を測っていない)。

外部照合として、並行セッションが取得した受入全走 junit では同 module 367 件の合計が
74.0 秒だった。同じ item 数に対する親の直列実測 135.45 秒に対し、**受入環境は約 1.8 倍速い**。
親の worktree 実測を受入予算へ持ち込むと保守側に振れる。

## 裁定を決めた 2 つの構造的矛盾

秒数を数えていては出てこない所見である。

### 1. 部分保留が費用を 1 秒も節約していなかった

`benchmark_snapshots` は module scope である。consumer 18 本のうち 14 本が保留されていたが、
残る 4 本 (`test_snapshot_submodule_object_store_is_recursive`,
`test_validate_schedule_legacy_different_arm_same_model_pair_remains_valid`,
`test_git_answer_object_reinjection_is_rejected`,
`test_supervisor_launches_pair_and_scrubs_git_environment`) は既定で走る。
よって fixture は既定走行で必ず構築され、setup 15.32 秒は保留と無関係に支払われていた。
D451 が「部分保留は検出力だけを削って費用を残す純損失」と述べた形が再現していた。

### 2. 変異期待 node の正本と保留 registry が矛盾していた

`orchestrator/tests/test_codex_reasoning_ab.py` の module docstring は
`DW-M08 expected mutation nodes` の正本であり、「親の mutation harness はこの一覧を
期待 node 正本として新旧双方を突き合わせる」と明記する。そこで名指しされた node のうち
**7 件が保留中**だった。

| 変異 | 期待 node の状態 |
|---|---|
| M1 | 1 件すべて保留 |
| M2 | 1 件すべて保留 |
| M3 | **4 件すべて保留** |
| M5 | 2 件中 1 件が保留 |

M1 / M2 / M3 は既定で走る期待 node が 1 件も無く、変異は必ず SURVIVED になる状態だった。
D452 が 2026-08-16 に名指しした失敗モードが、別の場所で現に再発していた。
変更後、保留されたままの期待 node はゼロになった。

## 代替防壁の非等価性 — 実行しない検査は防壁ではない

段 2 は `test_verify_replays_complete_fake_codex_experiment` (171.83 秒) の保留継続を
提案し、代替として `test_m5_generated_session_rows_require_set_equality` を挙げた。
段 3 の敵対 2 レンズが揃って real 判定し、親も独立に確認して撤回した。

- 代替候補 (L9138-9141) は production source に文字列が 2 本あることしか見ない。何も実行しない。
- 保留候補 (L6205-6237) は 10 run の完全な実験を構築し、`verify_manifest` の正例
  (rc=0・判定台帳 3/3・resource ledger 10・reader agreement 10/10・POS_PRIMARY) を確かめ、
  そのうえで rollout 行を 1 本注入して負例 (`RC_AGGREGATE` と固有の failure reason) を確かめる。

絶対規律の監査項目が名指しする「恒真な保証 (謳うだけで発火しない assert)」に該当し、
D451 の代替として数えられない。

## 比例源の除去 — 当初案を捨てた

`test_prompt_replacement_count_zero_expected_and_excess` は `_find_rollout` を
pin 無しで呼び、5.13 GiB 全走査へ落ちていた。

当初案は呼出しへ `pinned_label="POS"` を渡すことだったが、段 3 luna の指摘で捨てた。

- `rglob` が残るので D463 上の比例性が消えない。
- fast path の成立条件を外れると**沈黙して**全走査経路へ戻る。遅くなるだけで緑のまま通る。
- 速度が保たれたことを検査する assertion が無い。

採ったのは固定定数 `_REAL_ROLLOUT` の直接参照と `_verify_rollout_sha` である。
`F(t)` が固定 path になり D463 の非比例へ移った。source identity は SHA 検証により強くなる。

**実測 250.68 秒 (3 param) → 2.28 秒。**

失う検出力は「実 corpus に対する pin 無し一意解決」の既定実行である。pin 無し経路の意味論は
既定走行の約 40 本が合成 corpus で検査しており (同 file L4915-6032)、意味論としては失われない。
これは段 4 が明示的に採った交換である。

## 親の誤りと、それを直した経路

本 wave は親の誤りを 3 件、子とレビューが是正している。

1. **予算前提の誤り。** brief は「全走 5 分が絶対上限」と書いたが、権威元は D312 で
   「達成目標であって合否判定ではない」「設計択一を閾値の跨ぎで決めない」である。
   段 3 luna が権威元の欠落を指摘した。この誤りのまま進めば 171.83 秒の node を
   「遅いから保留継続」と裁定していた。
2. **`F(t)` の取り方の誤り。** 親は body だけを見て「非比例」と分類した。
   段 2 が node 単位で取るべきと是正し、段 3 sol が fixture 経由で tip の index 列挙まで
   閉包に入ることを file:line で示した。
3. **pin 閉包の漏れ。** 識別子 grep で 3 箇所を挙げて閉包を取ったと判断したが、
   `test_hold_inventory.py` が期待表を literal で複製しており grep に掛からなかった。
   段 5 の実装子が実際に import して発見し、親の焦点走が赤 2 件として顕在化させた。
   段 3 の敵対 2 レンズも挙げられなかった。

## 保留を継続する 2 件の記録形式

`GrowthTestHold` の `measured_seconds` は契約テストが全行 `None` を要求するため使えない。
実測値は reason 文字列へ入れ、機械可読部は house style の sentinel で埋めた。

```
IZANAGI_HOLD_REEVAL_V1 {"advisory":"...","barrier_nodes":[...],"measured_on":"2026-08-23","observed_call_seconds":...}
```

`advisory` には**この sentinel を評価する既定走行の主体が存在しない**ことを明記した。
敵対レビューが「条件を書いても評価主体が無ければ運用上の恒真で、台帳には
『再評価条件あり』と表示される一方で受理集合は永久に変化しない」と指摘したためである。
注記ではなく payload 自身に書いたのは、`tools/hold_inventory.py` が reason を
そのまま外部出力するので、注記は一緒に運ばれないからである。

評価主体の新設は gate 新設にあたり、条件 dispatch の最遅読了段を過ぎていたため
本 wave では実装せず、裁定パッケージへ送った。

## 変異 matrix — 再導入の検出力を実証した

repo_head `a8d5db97` / spec_sha256 `5f9a2a01…` / baseline PASSED (365 passed / 2 skipped / 402.76 秒)。
集計は KILLED 2 / SURVIVED 0 / MISMATCH 0 / PARSE_ERROR 0 / TIMEOUT 0。

| 変異 | 内容 | 殺した node |
|---|---|---|
| MUT-1 | `derive_independent_golden` の 2 経路一致比較を `return dict(route_a)` へ退化 | `test_m2_production_golden_requires_both_routes` |
| MUT-2 | 期待 session 行の構築を actual と一致させる (grep 対象文字列は不変) | `test_verify_replays_complete_fake_codex_experiment` |

両方とも失敗 node が期待集合と完全一致し、余計な node は 1 件も落ちていない。

MUT-1 は元関数が一致時に `dict(route_a)` を返すため、**返り値が同一のまま比較だけが消える**。
fixture を含む他の consumer は誰も気づかず、比較が呼ばれたことを assert する node だけが検出する。
MUT-2 は grep 対象の 2 文字列を変えないため、静的 node が mask しない設計にした。

両 node とも変更前は既定 skip なので、旧側では同じ変異が SURVIVED する。
これが `DW-M08` の求める新旧差分である。

本走は `--runner-mode local` で行った。`DW-M07` は dispatch を既定とするが、その理由は
runner の実行経路を変異させると runner が自壊し収集段が rc=16 になることである。
本 wave の変異対象は runner の実行経路ではないためこの失敗モードに当たらない。

## 段 8 — 自己改善は 1 件も統合できなかった

本 wave は実測に基づく候補 5 件を起こしたが、**統合は 0 件**である。

| 統合先 | 実測 | 予算 | 判定 |
|---|---|---|---|
| L1.5 層 (集約) | 9,776 byte | 9,566 byte | **210 byte 超過** |
| `DW-O18` (単節) | 1,000 byte | 1,000 byte | 余裕ゼロ |
| `DW-O26` (単節) | 688 byte (追加後) | 1,000 byte | 単節は収まるが集約で超過、かつ exact 契約 pin に抵触 |
| `DW-M05` (単節) | 976 byte (追加後) | 1,000 byte | 単節は収まるが集約で超過 |

段 8 の子は超過を自分で検出し、逆パッチで追加のみを除去して clean tree で終えた。
自己改善契約が「予算のために安全義務を削除・弱化してはならない」「予算値を上げる変更は
通常の自己改善に含めず、理由付きの独立審査対象にする」と定めるためである。

**実測に基づく候補が 5 件あって 1 件も入らないのは、契約が想定した状態ではない。**
事象と根本原因は failures 台帳側に残るので失われないが、手順書側の是正が働かない。
予算そのものを裁定項目として返す。

## 裁定パッケージ (ユーザーへ返す。本 wave では実装しない)

1. 保留行の再評価 sentinel を評価する既定走行の主体を作るか。
   `_validate_hold_rows` を拡張して `barrier_nodes` が保留集合に入っていないことを
   検査すれば、既存の import 時 enforcement 点を使って非恒真にできる。
2. 変異期待 node の正本と保留 registry の整合を機械検査するか。
   本 wave では 7 件の矛盾が人手の読みでしか見つからなかった。
3. `_find_rollout` の pin 無し全走査に上限か警告を設けるか。
   production も pin 無しで呼ぶ経路を持ち、corpus が伸び続ける以上いずれ顕在化する。
4. dev-wave reference の L1.5 予算をどうするか。実測に基づく自己改善候補 5 件が
   1 件も入らなかった。予算値を上げるか、L1.5 の既存節を L2 へ移すか、
   自己改善の routing 先を変えるか。予算値の変更は独立審査対象と契約が定めている。
