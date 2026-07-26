# [T-103] never-issued × real-artifact refusal vector — 調査と「実装しない」裁定

- 日付: 2026-07-26
- wave: `/dev-wave` (引数なし、worklog 候補から [T-103] を選択)
- branch: `worktree-dev-wave-t091-093-hardening`、基準 commit: `796262c`
- 差分: **コード 0 byte** (段 4 で「実装しない」と裁定し `DW-S04` の `4→7→8→9` を採った)
- 逐語: 同ディレクトリ `2026-07-26_t103-never-issued-vector-verbatim.md` (原文 SHA-256 併記)
- 計測: なし

**実装差分がないため、変異事前登録・変異 matrix・受入全走は本 wave の対象外である。**

---

## 1. 何を調べたか

[T-103] は前 wave (2026-07-26 (1)) の敵対相談 A-6 が出した対案である。[T-092] が
`test_real_freeze_gate_lists_floor_and_budget_null` の pre-R 分岐を削除した際、
「T-080 receipt が履歴に無い (never-issued) とき、実 artifact に対する legacy verifier 2 本の拒否 +
floor + budget = 4 件が gate に出る」という assert が失われた。post-R では到達不能な分岐だったので
実効検出力の低下は 0 だが、A-6 は「never-issued 固定の別 node を実物 freeze に対して撃つ」ことを
検出力の**追加**として提案し、親は scope 外として次の一手へ送っていた。

本 wave はそれを実装するつもりで着手し、**実装しないという結論に至った**。

## 2. 親が段 1 前に実測した事実 (模擬なし、実ファイルへの実走)

実行環境 = REPO 直下、`git submodule update --init` 済み (`external/ccbench` = `d706650`)。

**実測 1 — post-R の実 repo でも legacy verifier 2 本は現に赤である。**

- `s8b_holdout_freeze.verify(output/s8b-freeze/holdout_freeze.json, root=REPO)`
  → `FreezeError: design_source sha256 不一致: recorded=1829af7f… actual=5fbdd7ef…`
  (`design_source` = `docs/phase3-8b-descriptor-design.md`)
- `s1_known_axes_freeze.verify(output/s1-freeze/known_axes_freeze.json, source_resolver=REPO/rel)`
  → `FreezeError: source sha256 不一致: orchestrator/campaign/s8a_trigger_sweep.py
     recorded=3e94735a… actual=8c3abd48…`

つまり **legacy 契約は現物 artifact に対して成立していない**。gate が通るのは
active-valid receipt が legacy 経路を迂回させているからである。

**実測 2 — never-issued fixture へ無改竄で `gate_check` を撃つと refusal はちょうど 4 件。**
`_t080_stub_free_e2e_repo(tmp_path, issue_receipt=False)` に対し
`allowed=False`、refusal 4 件 (holdout design_source / known source / floor-null / budget-null)、
`t080_freeze_migration_observation is None`、`verify_receipt.state = never-issued` かつ refusals `()`。
fixture 内の `actual` SHA-256 は実 repo の値と一致した。

**実測 3 — 既存テストが同じ vector を部分的に既に撃っている。**
`test_never_issued_generator_tamper_reaches_public_driver_gate_g7`
(`orchestrator/tests/test_s8b_oracle_driver.py:2394`) が同じ builder を `issue_receipt=False` で使い、
legacy verifier を stub せずに 4 件の refusal を assert している。ただし
`design_source` と `generator` を記録 bytes へ**復元してから** `generator` を人工改竄するため
自然 drift の `design_source` 拒否は消えており、known 拒否は **prefix 一致のみ**である。

## 3. 段 2 プランと段 3 敵対相談の結果

- 段 2 (codex `gpt-5.6-sol` / `reasoning=max` / `sandbox=read-only`): 2 node の純追加プランを起草し、
  親 brief の 6 前提のうち **4 件を「要修正」**と判定した。
- 段 3 敵対相談 2 本 (同設定、レンズ A = 正しさ境界 / レンズ B = 整合・実効性): **両方 NO-GO**。
  blocker 6 件 (A-1〜A-4、B-1、B-2)、must-fix 6 件、nit 2 件。

**親の provisional 裁定の帰結**

| 前提 | 裁定 | 根拠 |
|---|---|---|
| (P1) 新 node は g7 の複製でない | **部分 refuted** | 制御フロー (builder / public gate / 4 件集約 / `allowed=False`) は g7 と実質重複。純増は自然 design drift の payload と known payload の exact 化と observation の 3 点だけ |
| (P2) fixture は実 repo と同一 payload を再現する | **部分 refuted** | 現行 bytes と pin の下では一致するが一般保証ではない。ccbench は recorded pin へ checkout され、known generator は resolver でなく module `ROOT` を読む |
| (P3) N2 (実 repo へ legacy を直接当てる) は scope 内 | **refuted** | kill set が N1 の部分集合で限界検出力ゼロ (B-1)。かつ live worktree に対する非原子的 sentinel で、並行編集に対して偽赤になる (A-6) |
| (P4) refusal を exact 4 件で固定できる | **妥当 (限定付き)** | 「この snapshot の fail-fast 表示が 4 件」であって潜在 drift が 4 個という意味ではない (A-5) |
| (P5) 走査順依存で pin は brittle かもしれない | **refuted (方向が逆)** | `_iter_sources` の depth-first insertion order と固定 JSON 順により**決定的**。親の「非決定的かもしれない」は誤り。ただし brittleness そのものは別途 real (A-2 / B-5) |
| (P6) `DW-O09` 非発火 | **部分 refuted** | 結論は妥当だが理由が不足。「新規ファイルなし・既存 path のみ・三軸 canonical encoding を新規コードへ同居させない」で補強した |

## 4. 「実装しない」と裁定した理由

**決め手は `DW-G02`** — 初回 E2E cycle 前の hardening は「correctness 判定、selected/tie、数値、
proof 参照、試行欠落を実際に変える欠陥」だけを blocker とし、それ以外は 1 cycle 後へ送る。

レンズ B が独立に棚卸しした結果、T-103 が守る対象は**そのどれでもない**。

| 成果物 | T-103 対象変異で変わるか |
|---|---|
| certified 選択・受理集合 | 変わらない |
| 材料レポート | 生成経路に到達しない |
| proof chain / verdict | 変わらない |
| 試行台帳・WAL | gate 後なので作られない |
| 実際に変わる値 | standalone gate の `refusals` **診断文字列だけ** |

理由は構造的である。実 freeze は v1 (floor / budget が `null`) なので、active-valid receipt が
legacy 2 拒否を消しても **floor / budget の 2 拒否は必ず残り、gate は常に `allowed=False`** である。
既存 real gate テスト自身が `not decision.allowed` を要求している。したがって legacy 2 呼出しが
丸ごと消えても、campaign も試行も 1 件も増えない。

**加えて、入れることに害がある。** レンズ B-5 が指摘したとおり、この node は
`assert actual != recorded` を通じて「**legacy artifact が修復されるとテストが失敗する**」という
逆向きの圧力を作る。重い一体試験が無関係な正当変更でも落ちれば、担当者が exact assert を
prefix 化・削除する誘因になる。これは絶対規律 2 (正しさゲートを緩める変異を許さない) に対する
構造的リスクの**新設**であり、成果物影響ゼロの pin と引き換えにするものではない。

**前例との整合**: 初回 cycle 前に実装したテスト強化 ([T-091] / [T-092] / [T-093] / [T-098] /
[T-106] / [T-107]) は**すべてユーザーが名指しで裁定済み**である。[T-103] は worklog 上「未着手」で
裁定を受けておらず、`DW-G02` の既定が生きる。親が独断で既定を上書きしてはならない。

## 5. 素材 — 本 wave が新しく掘り当てた事実

### 5-1. 「stub していない」と「fixture に対する実 verifier」は別である (A-4)

`_t080_stub_free_e2e_repo` は receipt 発行経路では隔離 subprocess を起動し、
`migration.ROOT == known.ROOT == holdout.ROOT == fixture root` を assert する。しかし
`issue_receipt=False` は**その subprocess の手前で return する** (`:493-495`)。よって
never-issued fixture に対する gate は、親 process が import 済みの **実 repo の module** を使う。

`s1_known_axes_freeze.verify_document` を見ると、注入された `source_resolver` を使うのは
source record の走査だけで、

- generator hash (`:724`)
- `frozen_at_head` の ancestor 検査と `ccbench_pin` (`:748-757`)
- 末尾の `build_document` による機械再構成 (`:759-766`)

は **module-level `ROOT` に束縛**されている。本 vector は source loop の 5 件目で先に raise するため
これらに到達しないが、「fixture に対して実 verifier を通した」という表現は成立しない。

### 5-2. root-isolation 変異を誰も殺していない (A-3)

`s8b_oracle_driver.py:409-411` の `source_resolver=lambda relative: root / relative` を
`ROOT / relative` に変えても、

- 提案 N1: fixture と実 repo の当該 source bytes が同一なので同じ refusal → SURVIVE
- 提案 N2: 元から `ROOT` を使う → SURVIVE
- 既存 `test_t080_gate_hermetic_primary_states_exact`: verifier 自体を stub → SURVIVE
- 既存 g7: known source を変更しない → SURVIVE

**この変異を殺す control はテスト集合のどこにも無い。** 殺すには fixture 側だけ bytes を分岐させる
必要がある (既存 `distinct_basis_blob=True` が holdout 側で同型の手法を使っている)。

### 5-3. 提案していた変異はほぼ帰属不成立だった (A-3)

事前登録候補になりそうだった変異は、次のとおり既存テストが先に殺す。

| 変異位置 | 先に殺す既存テスト |
|---|---|
| holdout legacy 呼出し `:373` の削除 | `..._primary_states_exact`、g7 |
| known legacy 呼出し `:409-411` の削除 | 同上 |
| floor / budget refusal `:415-418` の削除 | real gate、primary states、g7 |
| `allowed` の退化 `:117` | g7 |
| refusal 時の observation 漏出 `:119-122` | primary states、stub-free B5 |
| never-issued 判定の変更 | builder 内の既存 assert |
| design source 比較の無効化 | `test_s8b_holdout_freeze.py` |
| known source 比較の無効化 | `test_s1_known_axes_freeze.py` |

新テスト固有になり得たのは known 拒否の `recorded=/actual=` suffix を落とす変異と `_iter_sources` の
順序変更だけで、いずれも**受理境界ではなく診断 payload / 診断順**の変異である。

### 5-4. 親の実測の一般化が過大だった (A-5 / B-6)

- known の drift は **unique path 3 件**だが、source **record は 12 件**である
  (`t080_freeze_migration.py:86-99` に同じ 3 path の 12 repin cell が列挙されている)。
- holdout の drift は `design_source` だけでなく **`generator` にも存在する**
  (`test_s8b_oracle_driver.py:178-181` が recorded / actual を既に固定している)。
  したがって「refusal ちょうど 4 件」は fail-fast 表示が 4 件という意味であって、
  潜在欠陥が 4 個という意味ではない。design drift だけを直しても holdout は generator drift で
  なお拒否し、件数は 4 のまま payload だけが変わる。

### 5-5. 費用の実体 (B-4)

`_t080_stub_free_e2e_repo` の call site は 6 箇所、parameter 展開後 **11 実行**。N1 追加で 12 実行
(builder cohort 比 +9.1%)。1 回あたりの静的な I/O 下限は ignore 適用後で
`output` 1,842 files / 19.26 MB、`orchestrator` 247 files / 5.05 MB、required 再 copy 35 操作 /
0.58 MB、ccbench worktree 405 files / 2.35 MB。**これは静的列挙であり実測時間ではない。**

## 6. scope 外として裁定パッケージへ送る real 所見

`DW-S04` に従い、scope 外の real 所見は実装せずユーザーへ返す。

1. **[T-112]** `s1_known_axes_freeze` の root 束縛不完全 (5-1)。generator / Git / ccbench / 再構成を
   `source_resolver` と同じ root へ束縛するか。**本番コード変更**のため測定前後の扱いに裁定が要る。
2. **[T-113]** root-isolation 変異の control 不在 (5-2)。fixture 側だけ bytes を分岐させる
   driver-level control をテストへ足すか。テストのみだが `DW-G02` の判断が要る。
3. **[T-114]** never-issued の全層 scope 漏れ (B-3)。`run_block` の campaign-start / result / WAL、
   report の never-issued 歴史照合が未被覆。report 側は autouse monkeypatch で Git 履歴から
   隔離されている (`test_s8b_oracle_report.py:74`)。
4. **[T-103] 自身の再裁定** — (a) 1 cycle 後へ送る (**AI 推奨**)、(b) B-5 案の最小 node
   (軽量 fixture + `design_source` のみ) を今実装、(c) 取り下げ。

## 7. 検査 (記録 commit 前の実測)

**受入全走と変異 matrix は対象外である** — 実装差分が 0 byte なので、走らせるべき変更が無い
(`DW-S04`)。代わりに記録成果物そのものに対する gate を実走した。

- **三軸 conjunction (holdout 未既知性)**: 走査 3 ファイル (材料レポート / 逐語 / handoff)、
  rr80 と rr20 の両方で **conjunction hit 0**。per-axis も全軸 0。
- **defang の必要性を反実仮想で実測した**: defang を適用しない逐語 (子出力 5 本の連結) は
  **rr80 で conjunction hit 1** (rratio / skew / rmw の三軸すべてが同一ファイル内で一致) になる。
  レンズ A の所見 A-7 が三軸の canonical encoding を名指ししているためである。
  したがって本 wave の defang は装飾ではなく、**実際の自己発火を 1 件防いだ**。
  置換は三軸 key 直後の半角 `=` を全角へ 1:1 で置き換えるだけの可逆操作で、**3 箇所**に適用した。
  原文 SHA-256 と byte 数は逐語の冒頭表に併記した。
- **literal placeholder**: `python3 tools/check_docs.py` **rc=0** (違反なし)。
  D88 (1) により `output/insights/*.md` は検査対象族に含まれる。

**記録後検査 (F34、記録 commit の後に再走した実測)**: `check_docs` **rc=0**、
`check_ai_provenance` = **366 件・違反なし**、焦点 (repo scan invariant + `test_check_docs` +
real-repo serialization) = **117 passed**。

## 8. 射程 (これを閉じたと書いてはならない)

- 本 wave は**コードを 1 byte も変えていない**。受理集合・凍結 bytes・proof chain は不変である。
- [T-103] は**消化していない**。1 cycle 後への送りを推奨した状態で裁定待ちに戻る。
- 5-1 / 5-2 の欠陥は**現存する**。本 wave は検出しただけで塞いでいない。
- 「never-issued 経路が全層で検証された」とは記録しない。standalone gate 層のみが既存テストで
  被覆されており、campaign / WAL / report 層は未被覆である。
