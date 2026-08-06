# [T-244] P3 critic 後置 (U-8) — wave 記録

8c 自律 trial の critic 呼び出しを、cell の Layer 3 admission 確定後へ後置した wave の逐語記録。

## 何を実装したか

裁定 U-8 (2026-08-05 /rulings 批准) は「critic を Layer 3 admission・ledger seal・proof 書き込みの
後へ移す」である。**このうち 8c に実在する anchor は Layer 3 admission だけ**であり、
ledger seal は D201 が結線しないと裁定済み、proof 書き込み (origin-proofs sidecar / report v3) は
前 wave が却下済みである。よって本 wave の射程は Layer 3 admission への後置に限る。

実装は 2 段化である。

1. generation ループは planner / coder / auditor / harness までを担い、critic 用の最小情報
   (generation 番号・common payload・outcome・metrics・raw variant の 5 key) を cell の私有 key へ
   積んで返す。`_run_workload` の**引数は 1 つも増やしていない**。
2. workload ごとに、その cell の admission を確定した後で pending critic をまとめて呼ぶ。
   復元 cell も append 直後に同じ二相処理を通し、推測による後始末は行わない。

例外境界は 2 種に分けた。admission finalizer の失敗は回復させず伝播させ report を publish しない。
pending critic 側の失敗は従来どおり `supervisor-error` へ回復する。
report 構築の直前に、pending の消費漏れと admission decision の欠落を止める fail-closed 検査を置いた。

## 受理集合の変更 (D96 の対象)

- **承認済み唯一の運転である 1 世代の受理集合は不変**である。
- generation 上限を上げて多世代を回した場合だけ、journal の role attempt 順が report の平坦化順と
  食い違い、完了性検査が report publish 前に fail-closed で止める。境界テスト
  `test_multi_generation_deferred_critic_fails_closed` を同じ変更単位に含めた。
- direct `_run_workload` は critic を呼ばなくなる。critic は gate ではなく recipient なので
  正しさ防壁は弱まらないが、入口の contract 変化なので
  `test_direct_run_workload_defers_critic_to_finish_trial` で固定した。

## 名乗りの上限 (重要)

**本 wave は U-8 を完了させていない。** 名乗ってよいのは
**「8c 非認定 pilot の critic 呼び出しを cell の Layer 3 admission 確定後へ後置した」**までである。

名乗ってはならない — U-8 完了 / commit-reveal を閉じた / P3 充足 / 漏洩ゼロ /
certified 選択・cap・D114 上限の変化。ledger seal、proof issuance、
proposal と raw response の seal 後公開はいずれも未実装である。
critic は依然 ledger seal / proof issuance より前に metrics を受け取る。

## wave の経過 (段ごと)

| 段 | 成果物 | 要点 |
|---|---|---|
| 1 | `brief.md` | 3 anchor のうち実在は Layer 3 admission だけと実測。承認上限 1 世代では critic 出力の consumer が記録だけであることも実測 |
| 2 | `s2-plan.md` (job dir) | 新 journal event + schema v4 + 新 generation cap を提案 |
| 3 | `s3-lensA.md` / `s3-lensB.md` (job dir) | 両レンズ独立に NO-GO。3 提案はいずれも裁定射程外かつ不要と判定 |
| 4 | `s4-adjudication.md` + erratum v3 / v4 / v5 | 3 提案を全部落とし、最安案へ。実装子が 3 回矛盾を検出し、うち 1 回は親の記述ミス |
| 5 | 実装 commit | `+909 / -64` (実装 + テスト) |
| 6 | `s6-adjudication.md`、review R1 / R2、refocus | must-fix 4 件 → fix 2 巡で全 closed。新所見 N1 も closed |
| 7〜9 | worklog fragment、D fragment、land | — |

## 段 4 で落とした 3 提案と理由

1. **新 journal event `critic-admission-barrier`** — 裁定射程外の新設統治であり、かつ同一 producer 由来の
   自己申告なので durable な順序を証明しない (両レンズが独立に指摘)。
2. **role/trial schema の v3→v4 bump** — 当該定数は全 role の payload と共用されており、上げると
   全 role の入力 bytes と payload hash が変わり、既存 v3 artifact が verifier・台帳の受理集合から外れる。
   barrier を作らないなら bump も不要。
3. **新定数 `MAX_POST_ADMISSION_CRITIC_GENERATIONS`** — D114 の「上限は 1 定数」と衝突し、
   cap-lift 後に承認外の過剰拒否になる。**新定数なしでも既に fail-closed** である
   (多世代では journal 順不一致で report publish 前に止まる) ことを親が実測した。

## 段 6 で閉じた must-fix

| # | 所見 | 対応 |
|---|---|---|
| F1 | 例外境界が広すぎ、critic 準備の失敗まで report 不在にしていた | finalizer だけを回復境界外へ。closed |
| F2 | pending 残留検査が通常経路では発火せず恒真だった | 人工 seam と発火テストを追加。closed (seam の限界は docstring に明記) |
| F3 | 変異 M2 / M3 が狙ったテストでなく完了性検査に殺されていた | completeness を経由しない direct テストへ照準変更。closed |
| F4 | 新設テストの値固定が緩く、逆順・key 欠落・finalizer no-op が緑だった | exact 順・exact 5 key・実 finalizer 化。closed |
| N1 | admission decision を消す変異が、推測による後始末で復元され生存していた | 後始末ループを廃止し cell ごとに 1 回だけ処理 + 欠落検査。closed |

## 実測

- 対象 2 file: 209 passed (実装直後) → 214 passed (fix 1 巡目) → 215 passed (N1 fix)。
  いずれも計算ノードで実測。ログインノードは実行基盤の attest 失敗で 2 回落ちたため計算ノードへ回した。
- **変異 matrix: 7/7 KILLED、baseline PASSED、rc=0** (`mutation-ledger.json`)。
  初回走行は 7 変異すべてが赤くなったが、事前登録の期待 node が各 1 件と狭すぎたため
  harness は MISMATCH を返した。規約どおり初回を `mutation-ledger-run1-erratum.json` として凍結し、
  期待 node を実測集合 (2〜30 件) へ訂正して再走した。変異内容そのものは 1 byte も変えていない。
  M7 は承認外の過剰拒否を検出する正例で、既存正常系 30 件を赤にした。
- **受入全走: 7098 passed / 20 skipped** (計算ノード、land する tip で実測)。
  途中の tip (main 再取り込み前) では 7078 passed / 20 skipped だった。差は取り込んだ main が
  持ち込んだテストの増加であり、本 wave の差分によるものではない。
