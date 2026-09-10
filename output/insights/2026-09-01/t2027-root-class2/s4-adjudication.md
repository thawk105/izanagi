# 段 4 裁定 — [T-2027] 根クラス 2 / [T-2043]

親が段 2 plan と段 3 敵対相談 2 本を real / refuted、採用 / 不採用、scope 内 / 外に裁定し、
プラン v2 を確定する。変異事前登録は `DW-M01` に従い実装前に凍結する。

## 0. 裁定を変えた既裁定 — D1220 (親が段 4 直前の再走査で発見)

**D1220 (2026-08-28) 正式測定の cache 同一性から source root を外さない。**
逐語: 「正式 S8b の cache 同一性に絶対 source root が入り cache hit が起きない件について、
root-neutral 化しない。cache hit が起きない事実は限界として記録する。」
却下した選択肢に「root-neutral 化して cache hit を起こす — 受理集合を広げる変更を、
測定時間を理由に入れる」がある。

**帰結 2 点。**

1. **plan の形 B と、親 brief (P1-a) の provisional 裁定は、D1220 が既に却下した形である。**
   本 wave では実装しない。段 3 レンズ A 所見 2 とレンズ B 所見 4〜6 は、
   D1220 によって「そもそも採れない案への指摘」となるので、以後 scope 外として扱う。
2. **「別 job の cache hit は起きない」は 2026-08-28 に台帳へ記録済みであり、
   D1322 (2026-09-01) の裁定時に未見の事実ではない。** 親 brief の (M3) / (M4) は
   実測としては正しいが、「承認済み裁定の前提を覆す新事実」ではない。
   **親 brief の該当記述を訂正する。** D1322 は cache hit を起こすための裁定ではなく、
   D1192 が名指しした欠陥 —「manifest が job-local な絶対 path を保存する形」— を
   クラス 2 にも直す裁定である。発火しないことは D1220 が受け入れ済みの限界であって欠陥ではない。

`orchestrator/campaign/buildcache.py:2225-2228` の docstring も同じ事実を書いており
(`55900c9bc`、2026-08-27)、D1220 より前から実装側に記録がある。

## 1. D1322 の先行条件 (D1192 統合条件) の判定

**判定: 満たす。ただし brief (M1) の表現を訂正して記録する。**

段 3 の両レンズが「同一拒否述語」と「同一是正 3 択」を未実測と指摘した。**この指摘は real で、
採用する。** そのうえで、条件の充足そのものは次のとおり判定する。

| 条件 | 実測 | 判定 |
|---|---|---|
| 同一 cache entry | 両クラスは同一 completion (`contract=e576e9cd…`、`entry=87aa2e6a…`) の同一 manifest の入力 | **満たす** |
| 同一 descriptor | `target=ycsb_silo.exe`、`input_policy`、`contract_sha256`、`full_build_digest` が同一 | **満たす** |
| 同一拒否述語 | **コードの性質としては同一** (根が消えた入力を validator に通すと両クラスとも同じ述語で落ちる)。**production の lifetime では同一でない** — クラス 1 は build 自身が `buildcache.py:2765` で staging を捨てた後の受領書発行で落ちるが、クラス 2 の `/scr/0_<jobid>` は receipt 発行時にまだ生きており、現に落ちていない | **半分** (両方を記録する) |
| 同一是正 3 択 | 3 択の**集合**は同一。**効き方は違う** — (b) base 絶対 path を identity へ入れる案は、クラス 1 では staging が identity 確定 (`buildcache.py:2431-2454`) の後 (`:2540`) に PID + nonce で作られるので**構造的に不可能**、クラス 2 では**既に適用済み**かつ D1220 が解除を禁じている。(c) 消えた entry の cache miss 降格は、クラス 1 では fresh build 自身が staging を消すので直さず、クラス 2 には cross-job hit が無いので空振り。**したがって両クラスとも remedy になるのは (a) だけであり、選択は同一** | **満たす** (選択の同一性として) |

**親の裁定理由。** D1192 の同条項は F151 の再発防止であり、その目的は
「本文が同じというだけで別項目を束ねない」ことにある。守るべきは**是正の選択が分かれないこと**である。
実測の結果、両クラスとも採れる remedy は (a) だけで、選択は分かれない。したがって束ねてよい。

**両レンズと親の判断が割れた点なので、裁定パッケージに明記してユーザーへ返す** (下記 7)。
レンズは「効き方が違うのだから 4/4 とは書けない」と読み、親は「選択が同一なら条件の目的を満たす」と
読んだ。親は自分の読みで進めるが、割れた事実を消さない。

## 2. 所見の裁定表

| # | 出所 | 内容 | 判定 | 採否 | scope |
|---|---|---|---|---|---|
| A1/B1 | レンズ A 所見 1 / レンズ B 所見 1 | 「同一拒否述語」「同一是正 3 択」が未実測 | **real** | **採用** — (M1) を上表へ訂正 | 内 |
| A2 | レンズ A 所見 2 | 形 B は identity を変えても発火せず gate だけ増える | **real** | **採用** — ただし理由は D1220 の既裁定。形 B は不採用 | 内 |
| A3 | レンズ A 所見 3 | T-2043 の判定手続きでは「閉じた」証拠にならない | **real** | **採用** — 判定を 2 分する (下記 5) | 内 |
| A4/B8 | レンズ A 所見 4 / レンズ B 所見 8 | build-to-receipt bridge を検査する test が所有制約で置けない | **real** | **採用** — 所有競合しない**新規 test module** へ置く (レンズ B の是正案 2 番目) | 内 |
| A5 | レンズ A 所見 5 | 直接呼び手は 3 箇所でなく 4 箇所 (collector 自己検証を落としている) | **real** | **採用** — brief を訂正 | 内 |
| B2 | レンズ B 所見 2 | 新根タグは manifest の自己申告だけで origin 帰属を検証できない | **real** | **一部採用** — 下記 3 | 内 |
| B3 | レンズ B 所見 3 | issuer 既定値 `()` が「context 未提示」と「明示的に空」を区別しない | **real** | **採用** — `None` を「未提示」として拒否する | 内 |
| B4 | レンズ B 所見 4 | install tree digest が root 外 symlink の linker bytes を束縛しない | **real** | **不採用 (scope 外)** — 形 B 固有。D1220 で形 B を採らないので発火しない | 外 |
| B5 | レンズ B 所見 5 | cache-hit 負例が tree identity に mask される | **real** | **不採用 (scope 外)** — 同上 | 外 |
| B6 | レンズ B 所見 6 | 一部の正例と schema pin test が production 到達性を証明しない | **一部 real** | **一部採用** — basename / 順序非依存は「unit 契約」と明記する。schema pin test は形 B 前提部分を落とす | 内 |
| B7 | レンズ B 所見 7 | 既知 4 欠陥と root overlap の再発防止が v3 分岐で閉じていない | **real** | **採用** — 独立 node を足す | 内 |
| B9 | レンズ B 所見 9 | 変異候補 2 の赤理由がコードと一致しない (collector 自己検証が先に拒否) | **real** | **採用** — 事前登録から外し、probe で観測してから登録 | 内 |

## 3. B2 (origin 帰属の authority) の裁定 — 一部採用

**real である。** `filesystem` 根は `/` に錨を張るので位置が偽造できないが、
`dependency-prefix` 根は caller が渡す根に錨を張るので、その分だけ弱くなる。
7 件をこの根へ移すことは、**その 7 件については受理面を弱める**。

**しかしこれは D1192 / D1322 が承認した弱め方そのものである。** 既に着地したクラス 1
(`fetchcontent-masstree`) が同じ性質を持ち、D1192 はそれを決定として採っている。
是正の副作用で勝手に広げるのではなく、裁定された変更の内容である。

**採用するのは次の 2 点だけとし、新しい authority 機構は作らない**
(ユーザー指示「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」)。

1. **既存の canonical 性検査を新根へ広げる。** 現行 `s8b_compiler_input.py:925-937` は
   `filesystem` タグが live な special root を指すことを拒否する。special root 集合へ
   current dependency prefix 根を加える。これは**新設ではなく既存述語の射程合わせ**であり、
   欠かすと「新根の bytes を `filesystem` タグで指す」偽装が通る。
2. **B3 の `None` / 空 tuple の区別。** live 検証で `None` は「context 未提示」として拒否する。

**却下:** durable な root commitment / selector の新設 (レンズ B の是正案 1 番目)。
新しい機構であり、D1322 の射程外。**裁定パッケージへ送る** (下記 7)。

## 4. プラン v2 — 実装する形 (形 A のみ)

plan の「形 A」を採り、**形 B の全項目 (`buildcache.py:1816-1839` の identity 射影、
`_dependency_prefix_cache_identity`、tree digest、identity 前後の再検査) を落とす。**

### 4.1 `orchestrator/campaign/s8b_compiler_input.py`

- `PREVIOUS_MANIFEST_SCHEMA = "s8b-compiler-input/v2"` を追加、
  `MANIFEST_SCHEMA = "s8b-compiler-input/v3"` へ更新。
  `_V2_ROOTS` は**変えない**。`_V3_ROOTS = _V2_ROOTS | frozenset({"dependency-prefix"})`。
- `_normalized_v2_*` は旧 v2 専用として維持。`_normalized_v3_*` を新設。
  `_normalized_manifest()` は v1 / v2 / v3 を明示分岐。v2 に新タグを入れたら拒否。
- collector に `origin_dependency_prefix_roots` / `current_dependency_prefix_roots` を追加。
  分類順は `snapshot` → `fetchcontent-masstree` → `dependency-prefix` → `filesystem`。
  origin 根の**ちょうど 1 個**の配下にある external path だけを `dependency-prefix` にする。
  basename・配列 index・順序を root identity にしない (**unit 契約として明記**、B6)。
- validator に `current_dependency_prefix_roots` を追加。
  現在の根集合のうち相対 path が安全な regular file として存在する要素が
  **ちょうど 1 個**のときだけ hash 検証する。0 個・2 個以上・symlink・非 regular・bytes 差は拒否。
  **`None` は「context 未提示」として拒否**(B3)。
- special root 集合 (`s8b_compiler_input.py:925-937` 相当) へ current dependency 根を加える (B2-1)。
- 根の重なり検査 (`_roots_overlap`) を snapshot / masstree / dependency の全組へ広げる (B7)。

### 4.2 `orchestrator/campaign/buildcache.py`

- `_collect_compiler_inputs()` の signature introspection に origin / current dependency 根を追加。
  external policy 有効で collector が新引数を持たなければ従来どおり fail closed。
- `_validate_v2_entry()` に current dependency 根を追加し、cache-hit validator へ渡す。
- 「現在の canonical base」の正本は `buildcache.py:2379-2387` の `effective_dependency_prefix`
  の要素列。CMakeCache や receipt 時点の環境変数を読み直さない。
- `BuildResult` に runtime-only の
  `compiler_input_dependency_prefix_roots: tuple[str, ...] = ()` を追加。
  **絶対根を completion や durable receipt へ保存しない。**
- **`_v2_identity()` と `dependency_prefix` の identity 経路は 1 bit も変えない** (D1220)。
  `compiler_input_manifest_schema` が v3 になることによる identity 変化だけが生じる。

### 4.3 `orchestrator/campaign/s8b_binary_admission.py`

- `issue_binary_admission_receipt()` に
  `current_compiler_input_dependency_prefix_roots` を追加し validator へ渡す。
  既定値は `None` とし、v3 の dependency entry があるのに `None` なら拒否する (B3)。
- `validate_portable_binary_record()` は v3 を正規化するが live 根を要求せず bytes 再検証もしない。

### 4.4 `orchestrator/campaign/s8b_floor_campaign.py` (scope に含める)

依頼が名指しした 3 file の外だが、**この配線が無いと v3 の dependency entry が
受領書発行で拒否され、床値経路が壊れる。** 必要な最小の配線として scope に含める。

- `result.compiler_input_dependency_prefix_roots` を取得し、issuer へ明示的に渡す。
- build 呼び出しには新しい根引数を足さない (buildcache が実際に使った prefix から返す値を使う)。

### 4.5 テスト

- `test_s8b_compiler_input.py` / `test_buildcache_v2.py` / `test_s8b_binary_admission.py` へ
  plan の node を追加。ただし形 B 由来の node
  (`test_v3_job_dependency_prefix_identity_is_root_relative_and_content_bound`、
  `test_v3_dependency_prefix_tree_drift_changes_identity`、
  `test_v3_dependency_prefix_hit_validation_failure_never_rebuilds`) は**落とす**。
- B7 の独立 node を足す: v3 の path `"."` と先頭 `//`、dependency entry なしの v3 が
  明示的な空 context で受理されること、symlink 綴りの根が canonical 綴りと同結果、
  origin / current dependency 根と snapshot / masstree の全 overlap 拒否。
- **A4/B8 の bridge test は新規 module
  `orchestrator/tests/test_s8b_dependency_prefix_bridge.py` に置く**
  (所有競合を避ける)。`build_cells()` から issuer までを spy し、keyword 伝搬の欠落を殺す。
  新規 test file なので自走 harness (`if __name__ == "__main__"` からの pytest 起動) を付ける。
- `test_s8b_floor_campaign.py` は**編集しない**が、焦点走では**走らせる**。
- 既存テストの期待値は変えない。

## 5. [T-2043] の判定 — 2 つに分ける (A3 採用)

- **(判定 1) 現行 fresh floor 経路にクラス 2 由来の赤は無い。** 実測で示す。
  本 wave の実装後、7 件が `dependency-prefix` の根相対 entry として記録され、
  同じ job で生きている current roots に対する receipt 発行時検証が通ることを確かめる。
- **(判定 2) cross-job 再束縛の閉包は成立しない。** D1220 が
  「cache hit が起きない事実は限界として記録する」と裁定済みなので、
  **これは本 wave で閉じる項目ではない。** T-2043 を「閉じた」と書かず、
  「クラス 2 の是正は着地。cross-job 再束縛は D1220 の限界により未発火」と記録する。

床値 job の実投入を本 wave で行うかは、実装完了後に所要と占有を見て決める。
行わない場合は「実投入未実施」と正直に書き、判定 1 を unit / 統合テストの範囲に限定する。

## 6. 変異事前登録 (`DW-M01`、実装前に凍結)

`DW-M08` に従い、**まず全件 SURVIVED 期待の probe で観測 node を採取**し、
実測した完全 node 集合を KILLED 期待で本走へ登録する。
B9 の指摘により、plan の候補 2 は前段の collector 自己検証に mask されるので**登録しない**。
形 B 由来の候補 5 も**登録しない** (実装しないため)。

| id | file | old (逐語) | 置換 | 単一理由性の根拠 |
|---|---|---|---|---|
| m01 | `s8b_compiler_input.py` | `_V3_ROOTS = _V2_ROOTS \| frozenset({"dependency-prefix"})` | `_V3_ROOTS = _V2_ROOTS` | 正しい v3 dependency tag が root membership だけで拒否される。前段の shape / digest は正しく後段へ到達しない |
| m02 | `s8b_compiler_input.py` | current 根の一意性検査 `if len(matches) != 1:` | `if not matches:` | 2 根に同じ相対 file と同じ bytes を置いた負例だけが誤受理。schema / path / hash は全て正しく他の拒否層が無い |
| m03 | `s8b_compiler_input.py` | special root へ current dependency 根を加える行 | 加えない | current dependency 根を `filesystem` タグで指す再封印 manifest が誤受理。root-tag canonicality が唯一の拒否点 |
| m04 | `s8b_binary_admission.py` | `current_dependency_prefix_roots=` へ caller 値を渡す行 | `None` | 正しい v3 receipt の正例が issuer 内の live 検証でだけ落ちる。前段の admission / binding / snapshot 検査は同じ入力で通る |
| m05 | `s8b_floor_campaign.py` | `result.compiler_input_dependency_prefix_roots` を issuer へ渡す行 | 渡さない | 新規 bridge test だけが殺す。この node が無ければ登録できないので、bridge test の実在が登録の前提 |
| m06 | `s8b_compiler_input.py` | `None` を未提示として拒否する条件 | 条件を落とす | dependency entry があるのに context 未提示の manifest が誤受理。B3 の唯一の拒否点 |

**受理集合を縮小する側の過剰拒否の正例も登録する** (`DW-M01`)。
具体的には「dependency entry を持たない v3 manifest が、明示的な空 context で受理される」ことを
正例として固定し、m03 / m06 が過剰拒否へ倒れていないことを示す。

## 7. 裁定パッケージ (ユーザーへ返す) — 実装しない

1. **D1192 統合条件の読み方が親とレンズで割れた。** 「同一是正 3 択」を
   「選択が同一なら足りる」(親) と読むか「効き方まで同一でなければならない」(レンズ 2 本) と
   読むか。親は前者で進めた。後者なら D1322 の先行条件は未充足であり、
   本 wave の実装は差し戻しになる。
2. **`dependency-prefix` 根に durable な origin 帰属 authority を持たせるか。**
   本 wave は既存 canonical 性検査の射程合わせだけを行い、新機構は作っていない。
   クラス 1 (`fetchcontent-masstree`) も同じ弱さを持つので、やるなら両方に一度で。
3. **D1220 の限界を今後どうするか。** cross-job cache hit が起きない以上、
   D1192 が「run 間の cache 再利用は失わない」と書いた目的は、正式 S8b 経路では
   既に達成不能である。D1192 の理由部分と D1220 の整合を台帳で明示するかどうか。
