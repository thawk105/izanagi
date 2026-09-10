# 段 4 裁定 — [T-1851] 台帳配線 3 task 閉包 / 実装単位 A

2026-09-02 20:50 JST。branch `worktree-dev-wave-t1851-unit-a`、HEAD `821c7ecfa`。
材料 = 段 2 plan、段 3 レンズ A (所見 11 + 親 brief 6 + 分割 4)、レンズ B (規模 5 + 変異 5 + 層 5 + 親 brief 11)。
裁定 inbox 再走査: 本 wave 開始後に main が `24b31d2a3` へ進み D1507-D1516 が着地したが、
台帳配線閉包に関わるものは無い。承認済み裁定を覆す新事実も無い。

## 結論 — 実装する。ただし単位 A を A1' と A2' へ分割し、本 wave は A1' だけを積む

`4→5→6→7→8→9` で進む。**段 9 で land しない** (D1341)。

## 1. (P1-a) は反証された — 分割する

[実測] 段 2 plan とレンズ B が独立に、単位 A 全体が 1 wave に収まらないと測った。
直接 test 面は parametrize 展開後 153 node、consumer 参照閉包を足すと **172 node**、
production 差分は約 1,250-1,500 changed LOC である。

**親の誤りを 2 件訂正する。**

- 親 brief は「単位 A 単体の規模は未測定」と書いたが誤りである。前 wave plan v2 に
  `600-850 changed LOC / 35-55 node` の見積りが実在した (レンズ B)。**未測定ではなく、
  過小だった。** 新見積りとの差は約 2 倍で、差の主因は (i) parametrize 展開を数えていない、
  (ii) adapter の v1 型 hard-coded 参照 20 箇所を数えていない、の 2 点である。
- 親 brief は test 面を「35 / 50 / 9 node」と書いたが、それは node ではなく**関数数**だった。

**A1' / A2' の境界を次で固定する。** 分割の必須 3 条件 (A1' 単独で production 整合・既存 test 緑・
境界 signature を今固定できる) は、レンズ A の分割判定 1 が現物で確認した。

## 2. A1' の scope (本 wave が実装する)

| # | 内容 | 受理集合の方向 |
|---|---|---|
| S1 | core に `load_attempt_registry_with_budget_counts(...)` を新設し、`assert_registry_rows` の budget accumulator を seed 可能な共通 replay helper へ抽出する。既存 2 API の signature と戻り型は不変 | 狭まる (横断予算) |
| S2 | adapter に `_registry_generation_paths_locked` と `_profile_and_binding_for_generation` を置き、`_atomic_update` が共有 root lock 内で他世代を replay して counts を累積する | 狭まる |
| S3 | **`_atomic_update` を外殻と `_atomic_update_locked(lock, ...)` へ 2 分割する。** prelock rendezvous hook は外殻に残し、lock 取得前にちょうど 1 回呼ぶ | 不変 |
| S4 | path API へ `protocol_sha256: str \| None = None` を足す (`None` = 正規 1 段 v1)。既存呼出しは不変 | 広がる (2 段 path、承認済み) |
| S5 | profile へ v2 の schema / layout / 5 軸 slot / codec / series・budget key を**加法的に**新設する。public mutation へは繋がない | 広がる (承認済み)。live には未到達 |
| S6 | `_row_is_for_slot` / `_rows_for_event` を codec の完全な slot identity 比較へ変える (11 call site)。v1 では no-op | 不変 (v1)、狭まる (v2) |
| S7 | `serialize_session_line(record) -> bytes` を profile 層に置く。既存 consumer の書き換えはしない | 不変 (純粋 helper) |
| S8 | 世代列挙の fail-closed 規則。64 hex real directory + no-follow regular `registry.jsonl` だけを世代とし、非 64 hex sibling は無視、64 hex symlink・非 directory・不完全世代・再構成不能 profile は拒否 | 狭まる |

## 3. A2' へ送る (本 wave は実装しない。境界を固定するだけ)

**レンズ A の blocker 3 件のうち 2 件と、plan の A4/A5 の残りをここへ送る。**

- **(E1) sealed terminal projection を launcher 所有の raw facts から再導出する。**
  レンズ A の所見 4 は real / blocker である。plan の `derive_s8b_terminal_projection(sealed_session_record)`
  は campaign の自己申告 `valid` / `excluded_reason` / `session_median` を読み直すだけで、
  前 wave 段 4 の A2-5 / B2-5 が要求した「launcher 所有の生の事実から再導出し、自己申告 field は
  比較対象にだけ使う」を満たさない。**承認済み裁定に反する形で実装してはならない。**
  生の事実 (probe / classification receipt / throughputs / exec failures / rep evidence) の
  所有層は launcher であり、単位 C の scope である。したがって A では API の形しか決められない。
  **A2' の境界 signature を次で固定する。**

  ```python
  def derive_s8b_terminal_projection(
      *,
      probe_outcome: Mapping[str, Any],
      classification_receipt: Mapping[str, Any],
      throughputs: Sequence[float],
      execution_failures: Sequence[Mapping[str, Any]],
      repetition_evidence: Mapping[str, Any],
      policy: S8BClassificationPolicy,
      sealed_session_record: Mapping[str, Any],
  ) -> S8BTerminalProjection
  ```

  `sealed_session_record` は**比較専用**であり、status / reason / primary value の導出入力に
  使ってはならない。不一致は拒否する。

- **(E2) 台帳専用理由語彙 4 語の active 化。** 親 brief は「狭まる」と書いたが**誤りで、
  raw core では広がる**。`_assert_null_matrix()` の retryable 分岐は理由が集合に含まれることを
  要求するため、現行の空集合は全 retryable terminal を恒真に拒否している (レンズ A 所見 5、レンズ B)。
  4 語を active にすると、これまで拒否していた形を受理する。同時にその 4 語を持つ
  terminal-failure は拒否するようになるため、方向は単純な拡大ではなく混合である。
  **(E1) の validator と同じ commit でしか active にしない。** A1' では v2 profile の
  retryable 集合を空のまま置く。

- **(E3) `_assert_profile` の schema 別 exact validator 化。** レンズ A の所見 8 は real / blocker で、
  plan の call-site inventory はこの 5 箇所を 0 件扱いで落としていた。現行 `_assert_profile()` は
  必ず v1 factory を再構築して object identity を要求するので、このままでは v2 profile が
  path 処理より前に全拒否される。**A1' は v2 mutation を開かないので A1' では赤にならない。**
  A2' で必須になる。exact 比較には新 field `terminal_row_validator` と
  `retryable_terminal_opens_next_attempt` も含める (`dataclasses.replace` による無効化を防ぐ)。

- (E4) v2 generation の create-only publish、B1 capability の消費経路
  (`_atomic_update_with_consumption_marker`)、claim v3、v2 resume、sealed terminal API。
  plan `:282-374` の signature をそのまま境界とする。

## 4. 設計点の裁定

- **(P1-b) 採用。** レンズ A・B とも現物で裏を取った。`_locked()` は毎回 `os.open()` した別 fd へ
  blocking `flock(LOCK_EX)` を掛けるので非再入で、再取得すれば自己待機する。
  訂正 2 件を採る — prelock hook は外殻に残す、capability の発行は lock 取得**前**に行う。
  A1' では marker 経路を作らないので、`_atomic_update_locked` に lock 生存 guard を**置かない**
  (置くと到達不能な防御 guard になり、変異が構造的に SURVIVED になる。DW-M01)。
  guard は A2' で marker 経路と同時に入れる。
- **(P1-c) 一部反証を採用し、fail-closed とする。** live 共有 root の合成 2 段 v1 は
  genesis から trusted profile を再構成できない。genesis の `recovery_policy_sha256` は
  `c7c753a9…`、現行 scheduler 権威から導出される値はレンズ B の実測で `79c8098c…` であり
  (plan は `6ac1b69…` と書いたが古い)、いずれにせよ一致しない。genesis は authority id も
  方針原文も持たない。**受理側へ戻すには新しい trust root を採用する裁定が要るので、
  親は決めずユーザーへ返す (裁定パッケージ 1)。**
- **(P1-d) 採用。** `consumption-catalog.jsonl` の literal を読む tracked production consumer は
  0 件。非 64 hex sibling は無視する。64 hex の file や symlink は世代権威を騙るので拒否する。
- (P1-e) 維持。login node の焦点走。

## 5. 親 brief の誤りの訂正 (レンズが指摘、全件採用)

1. DW-O09 の「pin は path 側にも key 側にも見つからない」は広すぎた。正しくは
   **「`FROZEN_MANIFEST` と tracked artifact の pin は 0 件」**。root path は直接 test が pin し、
   claim filename は slot payload の SHA-256、capability digest は schema と binding の SHA-256
   から導出される。凍結成果物の bytes pin は変わらない。
2. DW-O10 の書込み列挙は主体を混ぜていた。**consumption marker は adapter でなく admission の
   `consume_attempt_ticket()` が書く。** adapter が書くのは registry / claim / receipt / staging で、
   provisioning 経由で `ledger.lock` と `attempt-ledger.jsonl` も共有 root に生じる。
3. submodule の記述は現物と食い違う。両レンズとも `git submodule status --recursive` が rc=0 で
   googletest が `f8d7d77…` に展開済みと実測した。親の rc=1 は**着手直後の観測**であり、
   その後解消している。開始条件の説明に使わない。
4. t524 の重なりは production だけでなく test 2 file (`+16/-2`、`+5/-3`) にも及ぶ。ただし
   `git merge-tree` は core を含めて自動 merge し conflict を出さない。追加は
   `_parse_genesis()` 内の別 schema 専用 29 行で、A1' の主 hunk と分かれる。**衝突なし。**
5. アンカー表の意味上の誤り 2 件。`attempt_registry_core.py:654-725` は profile 構築でなく
   `_parse_genesis()` である。B1 capability のアンカーは使用時再検証と action 実行
   `:5140-5227` を落としていた。
6. `assert_registry_rows` の呼出しは plan の 11 件でなく **13 件** (`trial_registry.py` が
   callable として渡す 2 件)。inventory 未記載は `make_s8b_domain_profile` production 2 件、
   `S8B_REGISTRY_LAYOUT` production 4 参照、`_rows_for_event` 11 件。

## 6. real だが scope 外 (実装せず記録する)

- [レンズ A 所見 7] A1' の横断列挙後、`db07b575…` fixture freeze に対する正規 1 段 v1 の
  mutation は新たに停止する (同じ freeze 直下に未知 policy の 2 段世代が実在するため)。
  **安全側の狭まりであり、本番 freeze とは別。既存 bytes は書き換えない。** 裁定パッケージ 1 に含める。
- [レンズ A 所見 3] `marker.use(action=...)` の例外時、unlink 自体が失敗すると staging が残りうる。
  既存の性質であり本 wave では閉じない。
- [レンズ B] A 単体は certified 選択・材料レポート・proof chain のいずれにも発火しない。
  `launch_floor_attempt()` の production caller は現に 0 件、result はまだ v4。
  **これは意図どおりであり、A1' を「効いている」と書かない。**

## 7. 変異事前登録 (DW-M01)

実装前に登録する。各変異は、同じ入力を拒否する層が前後に無いことを確認した上で登録する。

| ID | 変異 | 期待 | 単一理由性の根拠 |
|---|---|---|---|
| M1 | core の seeded budget 適用を消す (seed を無視して空 dict から数える) | KILLED | 横断予算を数える層は他に無い。cap 超過は `[attempt-slot-order]` でだけ落ちる |
| M2 | `initial_started_budget_counts` の値検証 (bool / 負数 / 非 int) を消す | KILLED | seed の形検査は新設のこの 1 箇所だけ |
| M3 | `serialize_session_line` の separator を compact 側へ変える | KILLED | exact bytes 比較はこの helper の出力にだけ効く |
| M4 | `serialize_session_line` の末尾 newline を落とす | KILLED | M3 と別 byte 位置。両者は独立に落とせる |
| M5 | 世代列挙の symlink 拒否を片側だけ消す | **SURVIVED (mask)** | `_read_regular_bytes` が親 component の symlink を再検査する (レンズ B 実測) |
| M6 | M5 と `_read_regular_bytes` の no-follow 検査を**両層同時**に消す | KILLED | DW-M04。M5 の生存が「効かない」でなく「他方が拒否していた」ことを実証する |
| M7 | 世代列挙の不完全世代拒否 (`registry.jsonl` 欠落) を消す | KILLED | 欠落 file を拒否する層は列挙のこの 1 箇所 |
| M8 | profile resolver の recovery-policy digest 比較を消す | KILLED | 未知 policy を止める層はここだけ。live 合成 2 段 v1 が正の入力になる |
| M9 | profile resolver の directory 名と genesis `protocol_sha256` の比較を消す | KILLED | path と genesis の束縛を見る層はここだけ |
| M10 | prelock hook を `_atomic_update_locked` の中へ移す (lock 取得後にする) | KILLED | 既存 rendezvous test (`test_s8b_attempt_registry.py:1492-1529`) が lock 前の読みを要求する |
| M11 | `_rows_for_event` の slot 比較を 4 軸へ戻す | KILLED | v2 codec を直接渡す helper 単体 test で kill する (public API は v2 を拒否するので直接経路を使う) |

**過剰拒否の正例 (DW-M01、受理集合を縮小する wave の義務)。** 次はいずれも通らねばならない。

- P1: 正規 1 段 v1 の世代だけを持つ root で、start / classify / observe / terminal が従来どおり通る。
- P2: freeze 直下に非 64 hex の sibling file (`consumption-catalog.jsonl` と同 shape) があっても、
  列挙と mutation が通る。
- P3: seed 9 + 1 start = ちょうど 10 が受理される (境界の直下)。

## 8. 実装子への分割

**1 単位 1 実装子とする。** A1' の 8 項目は core / profile / adapter を跨ぐが、S1 の core 変更を
S2 の adapter が消費し、S5 の profile 型を S6 の adapter が消費するため、producer/consumer 契約が
単位を跨ぐ。**並列に分けると契約が壊れる。** 規模は約 900 changed LOC・新設 test 35-45 node で、
B1 (998 行 / 1 fix 巡で収束) と同程度である。

## 9. ユーザーへ返す裁定パッケージ

1. **合成 2 段 v1 残骸の受理をどうするか。** live 共有 root の `db07b575…` freeze には 193 行の
   2 段 v1 台帳が実在するが、genesis から trusted profile を再構成できない。本 wave は
   fail-closed 拒否を採る。受理側へ戻すには `campaign-fixture-recovery-authority` と
   policy digest を production trust root へ昇格させる明示裁定が要る。**受理面を広げる方向なので
   親だけでは選べない。** 併せて、この freeze に対する正規 1 段 v1 の mutation も新たに止まる。
2. **B1 が返した 5 件は未裁定のまま持ち越す** (旧世代 token の capability 発行入口、分類権限の
   宣言 object 駆動化、計測前 probe 除外の権限層、crash 回復の再取得層、journal TOCTOU 窓)。
   本 wave はいずれも触れていない。
