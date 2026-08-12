# 段 4 裁定 — dev-wave-freeze-chain-hold

親が段 3 の所見を real/refuted・採用/不採用・scope 内/外に裁定し、プラン v2 を確定する。

## 裁定 0 — 本 wave は実装しない (`4→7→8→9`)

**理由 (3 つとも独立に成立):**

1. **保留機構が存在しない。** 相乗り先の `orchestrator/tests/growth_test_holds.py` は
   `worktree-dev-wave-growth-tests` にまだ無い (親が `git show` で確認)。同 wave は段 5 稼働中。
   **無い module へ entry は書けない。**
2. **二重機構の禁止。** 自前で台帳を作れば peer 合意 (「機構は 2 つ作らない」) に反し、
   conftest が衝突する。
3. **positive control が作れない。** sol MUST-FIX 1 が要求する 3 点 (env 無指定で理由付き skip /
   exact env で収集・実行 / 無効 env では解除されない) は、解除機構が land してからでないと書けない。

**したがって本 wave の成果物は「確定した 4 entry の仕様 + 実測 + 裁定パッケージ + 記録」とする。**
entry の投入は growth-tests 台帳の land 後に、`1 行 + pin の件数・digest 更新`の小さな差分で行う
(同 wave の contract。conftest には触れないので衝突面ゼロ)。

**免除の扱い:** 実装差分ゼロなので変異 matrix は免除 (`DW-S04`)。**受入全走は免除しない。**
本 wave の変更は `docs/spool/` 配下の fragment のみだが、実 repo を読む docs 不変条件 node が
実在するため、段 7 の記録前に焦点走で実走し結果を worklog へ書く ([T-648] fallback、
`record-acceptance-exemption-evidence`)。

## 裁定 1 — sol BLOCKER 1〜6

| # | 判定 | scope | 処置 |
|---|---|---|---|
| 1 typed hold の fail-open | **real** | **外** (t816 所有) | 全文を t816 へ送付済み。t816 は「例外契約を変えず、保留対象を実行しないだけ。held marker は registry へ」で解く方針を返答。**親が追加で穴 2 件を指摘済み** (下記 裁定 2) |
| 2 known-axes の S-1b flags 同一性 (`:859`, 実体 `:677-707`) | **real** | **外** | t816 が行単位化を受諾。保留は `:863-879` のみ |
| 3 holdout の `:865` 未承認世代 admission と `:974-978` `variant_binding` 再導出 | **real** | **外** | t816 が keep 集合へ明示 |
| 4 frozen-artifacts の 23 件一括 node に blind selector 証拠 14 件 | **real・最重** | **外** | t816 のアンカー表から既に除外済みと確認。**保留しない**で合意 |
| 5 protocol pin seal の入口は防壁自己完全性だった | **real** | **内 (親 brief の誤り)** | **本 wave の誤りとして訂正。** brief `:44` の表 7 行目を撤回。t816 へ訂正送付済み (実害ゼロ = 向こうの表に元々無かった) |
| 6 T-080 gate が receipt provenance と正しさ検査を同時実行 | **real** | **外** | t816 が `verify_receipt` / `static_gate_adapter` のまるごと保留を撤回 |

**族の型として記録する価値がある:** 6 件中 5 件が同型 =
**「保留対象の bytes/pin 検査と、対象外の測定公正・admission・防壁が同じ関数に同居している」**。
`DW-G03` の「族一般化には独立 2 例」を大きく超える 5 例が、**異なる 4 モジュール**
(`s1_known_axes_freeze` / `s8b_holdout_freeze` / `test_frozen_artifacts` / `t080_freeze_migration`)
で独立に出た。**failures 台帳の型として登録する。**

## 裁定 2 — 親が段 3 の後に独立に見つけた所見 (t816 の修正案への攻撃)

t816 の「held marker を **process 内** registry へ積む」案に穴 2 件。**real・scope 外・送付済み。**

- **穴 1: CLI subprocess 境界で registry が消える。** `s8b_holdout_freeze` の
  `verify_cli_with_t080_receipt` / `main`、`s1_known_axes_freeze.py:907-922` の `main`、
  oracle driver の CLI 経路は**別 process**。子の registry は親から見えず、
  親の終端要約が**「何も保留していない」と表示する**。可視性という唯一の防波堤が抜ける。
- **穴 2: xdist 48 worker がそれぞれ別 registry。** worker → controller の集約経路が無いと
  終端要約は最後の 1 worker 分か空になる。

**なお「保留対象を実行せず成功経路を不変にする」意味論そのものは正当**と裁定する
(保留とは、その検査で止めないことなので)。**それゆえ可視性だけが唯一の防波堤**であり、
到達しない経路が 1 つでもあれば裁定要求 (可視な skip 印) を実質破る。

## 裁定 3 — luna BLOCKER / MUST-FIX

| # | 判定 | scope | 処置 |
|---|---|---|---|
| B1 鎖外 node へ `xdist_group("real-repo")` を付けると `test_real_repo_serialization.py:567-615` の golden が赤 | **real** | **内** | **採用。プラン v2 で訂正**: 順序規則 (`xdist_group` を先に付けてから skip) は**鎖に居る node にだけ**適用する。当方の 4 function は全部鎖外なので **group を付けず skip marker だけ**。growth-tests へも警告済み (同 wave の 29 entry のうち 24 が鎖外) |
| B2 production hold と test skip の対応・positive control 未定義 | **real** | 内外にまたがる | **裁定 0 で解消** (本 wave は実装しない)。3 wave 統合後の対応表が要る = luna M3 と同根。**ユーザーへ返す** |
| B3 解除 env が計算ノード allowlist に無い | **real** | **外** (growth-tests 所有) | 同 wave が実装で塞ぐと明言。当方の entry も同経路に乗る |
| B4 `correctness_gate` の bool 型検査が無い | **real** | **外** | 同 wave が型検査を入れる |
| M1 鎖外なので wall 削減ゼロ = 純損失 | **real だが不採用 (保留を続行)** | 内 | **判定基準は速度でなく構造。** D320 は「使途の無い保証に維持費を払わない」であり、wall 短縮を要件にしていない。growth-tests との議論で同じ基準に揃えた。**ただしユーザー報告では wall 効果ゼロを明記する** |
| M2 `0.179 秒` は無効と宣言した並列 junit 由来 | **real** | 内 | **採用。** 直列焦点走 (`-n 0`、request `906477.nqsv`) で測り直し中。**並列由来の値は保留一覧に載せない** |
| M3 3 wave 統合の hold manifest が無い | **real** | 内外にまたがる | **採用。ユーザーへ返す** (下記 裁定 5) |
| M4 整合検査が O(1) でない (O(T+H)) | **real だが軽微** | **外** | growth-tests が不変条件の文言を「成長軸に対して O(1)、収集 test 数に対して O(T)、新規走査ゼロ」へ訂正済み |
| N1 `basename::function` が parametrize suffix を捨てる | **real** | 内 | **採用。** 保留一覧に「1 entry = N node」を明記。当方は `test_committed_non_prefix_ledger_history_is_rejected` が 2 node なので **4 entry = 5 node** |

## 裁定 4 — hold 集合の確定

**4 function (= 5 node) を保留対象として確定する。** sol が 1 件ずつ確認して全部妥当と判定し、
親が `orchestrator/publication/ledger.py` の**非 test caller ゼロ**を grep で独立検算した。

```
test_t793_publication_ledger.py::test_duplicate_root_kind_ordinal_identity_is_rejected
test_t793_publication_ledger.py::test_unchanged_ledger_bytes_across_merge_history_are_accepted
test_t793_publication_ledger.py::test_committed_non_prefix_ledger_history_is_rejected   (2 node)
test_t793_publication_ledger.py::test_committed_delete_and_recreate_is_rejected
```

共通 field: `hold_axis: provenance-chain` / `ruling:` = 第 4 束 `{{D:freeze-verification-hold}}` +
D320 / `correctness_gate: false` / `release_condition: explicit-user-command-only` /
`measured_seconds:` = 直列焦点走の実測 (`906477.nqsv`)。

**根拠**: [T-793] R2 (原子性・`(root, ordinal)` 一意性・予約 writer) が [T-499]「手番が不要に
なったもの」に入っている。**消える検出力は実在する** (4 件とも唯一検出者) が、これは裁定された縮小。

**保留しない** (段 2 が `keep` とした 18 function): F1 の trust-root 不在宣言、F2 の land/spool
commit 束縛 14 件 (全部 live admission・防壁)、F3 の identity literals・canonical 正例・
primary disjoint (R3 を恒真にしないため)、`test_alpha_reservation_commit_must_remain_unpinned`
(pin 再導入を拒否する D320 整合検査そのもの)。sol の逆方向監査でも過剰 keep は見つからなかった。

## 裁定 5 — ユーザーへ返すもの (裁定パッケージ)

1. **判定に迷った test 4 件** (保留しない。ご指示どおり一覧で返す)。
2. **[T-902] の裁定衝突** — 第 4 束が同じ 2 行を「保留対象そのもの」と書きつつ、実体は
   holdout 漏洩検出器 (測定の公正 = 対象外)。**推奨 = 保留でも除去でもなく最適化。**
3. **「新規 T 起票」の前提が覆った件** — `{{T:freeze-chain-hold}}` が既起票。
4. **3 wave 統合 hold manifest の不在** (luna M3 / B2)。3 層 (t816 = production 検査点、
   growth-tests = test skip 台帳、本 wave = 同台帳への相乗り) に保留が散り、
   **ユーザーが「今なにが保留中か」を 1 箇所で読めない**。解除も 2 経路 (定数の人手編集 / env)。
   **恒久保留の解除がユーザー明示命令のみである以上、読めないことは運用上の欠陥。**
   推奨 = 3 wave の land 後に統合 manifest を作る follow-up タスクを起票する。
5. **裁定文と実測の乖離** — 第 4 束の「v1 凍結証拠テスト 4 本」は実測 1 本 (t816 が記帳)。
