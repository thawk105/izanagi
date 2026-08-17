# 裁定パッケージ — [T-782] 承認 pin は縮小対象でなく、縮小してよいのは generator の bytes 照合だけである

```text
状態: 実測完了。実装差分ゼロ。durable artifact 0 件。APPROVED_SPEC_SHA256 は None のまま。
authority: 親 (dev-wave-t782-approval-sha-binding) の独立実測 + 段 3 敵対 1 本 (codex sol/max)。
  敵対は親の 4 命題を全件反証し、親の事実 3 件を訂正し、見落とし blocker を 1 群指摘した。
  親は 8 所見すべてを一次資料で独立に裏取りして採用し、**当初の推奨を撤回した**。
起点: 2026-08-12 第 6 束ユーザー裁定 [T-782] Q1 = (b) (archive worklog 510)。
branch: worktree-dev-wave-t782-approval-sha-binding (insights + spool fragment のみ)
実測基準: local main 699c9cae
```

## 要旨

依頼は 3 段構えだった。(i) 起票時 3 前提の生存を実測、(ii) 生きているものについて reviewed spec の
bytes を起草して canonical path と production 生成経路を用意、(iii) 承認値の確定時に SHA を
機械的代行で記入できる形まで配線。**(i) を実行した結果 (ii)(iii) を実行していない。**

そして依頼が併せて求めた衝突判定の答えは **「部分的に衝突している」** である。
束縛は 1 つではなく 2 つあり、**性質が正反対だった。**

| 束縛 | 実体 | D320 との関係 | 裁定 |
|---|---|---|---|
| 承認 pin | `APPROVED_SPEC_SHA256` と disk bytes の一致 | **対象外 (不変)** — 未承認の研究設計が official 経路へ入るのを止める admission gate | **縮小しない** |
| generator の bytes 照合 | `generator_versions` と production 5 source の live bytes の一致 | **見送り対象** — D302 自身が「defense-in-depth であり新規の受理集合縮小としては主張しない」と位置付ける | 縮小候補 (§5 Q1) |

**親は当初「承認 pin ごと hold へ入れる」を推奨したが、これは誤りだったので撤回した。** 理由は §4。

## §1 実測 — 起票時 3 前提はすべて生存 (現行 main 699c9cae)

| # | 事実 | 測り方 |
|---|---|---|
| M1 | `APPROVED_SPEC_SHA256 is None`。`load_approved_spec` は reason `no-approved-spec` を送出 | module を import して直接呼出 |
| M2 | `output/s8b-oracle-spec/` は不在。production の producer は 0 件。canonical path へ書く関数は **test 側の 5 箇所** (`s8b_oracle_spec_fixture.py:106-108, 119-121`、`test_s8b_oracle_manifest.py:266-268, 1104-1106, 1154-1156`) | `ls` と `git grep SPEC_REL` |
| M3 | `load_approved_spec` の production 呼出は **6 関数 7 箇所** — driver の gate 経路 490 / 500、driver の run 経路 1258、judge 456、report 1830、manifest 1186、verdict 1009 | `git grep` と関数境界の確認 |
| M4 | **今日の状態では gate 経路が承認 pin を直接踏む。** floor / budget がともに `null` のとき `_gate_check_core` は v1 verifier の枝 (`s8b_oracle_driver.py:445`) に入り `load_ratified_freeze` を呼ばず、490 / 500 で `load_approved_spec` を呼ぶ。残る 5 箇所では `load_ratified_freeze` が先に走り、例外送出または早期 return によって承認 pin に到達しない | 制御フロー読取 |
| M5 | `load_ratified_freeze` は今日 `RatifiedFreezeError [no-active]` を送出 | 直接呼出 |
| M6 | `holdout_freeze.json` の `floor` = `null`、`budget` = `null` | JSON 読取 |
| M7 | `test_schema_v1_has_no_durable_manifest_candidate_or_reviewed_spec` は緑 (単独走で 4 passed)。canonical directory に 1 file でも置くと赤 | 単独実走 |
| M8 | spec の `generator_versions` は production 5 source の live bytes を pin し、検証時に実ファイルと突合する (`s8b_oracle_manifest.py:430-471`) | ソース読取 |
| M9 | その 5 source は 2026-08-01 以降 **22 commit** で変更されている (file 別 touch は 17/6/3/0/2 = 28 だが同一 commit の重複を含む)。5 本のうち 4 本は直近 4 日以内にも変更 | `git log --format=%H \| sort -u` |
| M10 | `freeze_verification_hold.HELD_CHECK_IDS` は 21 件を held にしており、うち 2 件は `s8b-oracle.*`。`APPROVED_SPEC_SHA256` は held 集合に入っていない | ソース読取 |
| M11 | `load_approved_spec` の caller 集合を固定する inventory test は**存在しない**。`test_s8b_oracle_manifest_contract.py` が pin するのは `load_official_*` と `verify_manifest` の consumer だけである | 同 file の定数読取 |

**前提 A (研究設計値が未確定) — 生存。** `n` / `master_seed` / block ID / `campaign_ids` は未確定
([T-987] package §6)。`n` は [T-1142] が indifference-zone の pilot を納品したが (D466 / D467)、
`(δ, α)` の確定は集約規則の再凍結に属し未了である。

**前提 B (canonical path も production 生成経路も無い) — 生存。** M2 のとおり。

**前提 C (D302 の schema 据え置き前提に触れる) — 生存。** M7 のとおり tripwire は現に効いている。

## §2 承認 pin は今日 1 件の判定も律速していない (ただし挙動は変わる)

M4 + M5 + M6 から次が言える。

- **判定 (受理/拒否) はどの経路でも変わらない。** 5 箇所では承認 pin に実行が到達せず、
  gate 経路では到達するが `floor-null` と `budget-null` の refusal が必ず立つため gate は拒否のままである。
- **ただし「観測可能な挙動が変わらない」は偽である。** gate 経路の refusal 一覧から
  `manifest-verify: ... no-approved-spec` の 1 項目が消え、次段の診断へ変わる。
  親は当初これを「1 bit も変わらない」と書き、機構としても「常に手前の凍結読込が先に落ちる」と
  説明していた。**どちらも誤りで、敵対所見 A1 / A6 により訂正した。** 今日の floor / budget が
  ともに `null` である以上、gate 経路は凍結読込を経由しない。

**帰結は変わらない。** 承認 SHA を今日埋めても certified 選択・材料レポート・台帳は 0 件のままである。

## §3 承認の trust root — 新しい状態変化ではなく、受容済みの限界である

親は当初これを本 wave の新事実として提示したが、**敵対所見 A4 により格下げした。**

[T-868] は「署名方式と外部 trust root は設けない。自己発行可能な性質は明示したまま受容する」と
裁定済みで、これは archive worklog 546 (2026-08-13) の時点で既に引用されている。
2026-08-17 の [T-1258] 裁定「作らない。[T-868] と同じ扱い」はその再確認である。
すなわち **blocker ではなく、宣言済みの保証限界**である。

**それでも 1 点だけ現用文書の訂正が要る。** [T-987] package (2026-08-16) §2 は承認の trust root を
「[T-1116] と 1 回で決める。裁定待ちのまま」と書いているが、[T-868] に照らすと**既に決着済み**である。
同 §2 は「この決定が付くまで oracle spec の承認 branch は有効化できない」と結論しており、
その前提が事実と異なる。

## §4 承認 pin を hold へ入れてはならない (親の当初推奨の撤回)

親は当初、同族 21 件が hold に入っている不揃いを根拠に承認 pin の hold 化を推奨した。
**敵対所見 A3 がこれを反証し、親は独立に裏を取って撤回した。**

**理由は受理集合の向きである。** 現在 `APPROVED_SPEC_SHA256` が `None` なので、official manifest を
生成できる spec の集合は**空**である。pin を held にして照合を省略すると、この集合は
「canonical path に置かれた、schema を満たす**任意の** spec」へ広がる。
schema 検証と ratified freeze との cell 突合は残るが、**`n`・`master_seed`・`block_sizes`・
`campaign_ids`・`run_contract` の `reps` / `extime` / `clocks` / `bench_max_rounds` は
schema の範囲で自由**であり、これらは実験そのものを決める研究設計値である。

**すなわち hold 化は「未承認の研究設計を official 経路へ入れる」受理集合拡大であり、
規律 2 が名指しする reward hacking の経路を自分で開くことになる。**

D320 もこれと整合する。同決定は bytes 級 provenance 機構の新設・維持を既定見送りとしつつ、
**「対象外 (不変): 絶対規律 1〜3、正しさゲート (verifier / admission / 変異検査)」**と明記し、
さらに「本決定は…live な検査を黙って外す授権ではない」と書いている。
承認 pin は admission gate であり、この対象外に当たる。

親の当初の主張は「D302 の内容再導出が残るので門は弱まらない」だったが、これは誤りである。
**内容再導出は残るが、再導出の元が未承認のファイルになる。** D356 も
「欠けているのは内容束縛ではなく承認者の同一性である」として**内容束縛そのものは健全**と
明記しており、親はこの 2 つを混同していた。

**同族 21 件との不揃いは正しい不揃いである。** held の 21 件 (D328) は実装・測定の**同一性**検査で
あって admission gate ではない。性質が違うので扱いが違う。

## §5 主問

**Q1. `generator_versions` の live bytes 照合をどうするか。**

これは §4 と逆で、**縮小候補として成立する。** 根拠は D302 自身が
「`generator_versions` の比較は defense-in-depth であり、新規の受理集合縮小としては主張しない
(両側で canonical path と実 byte hash が既に強制されているため)」と位置付けていることである。
すなわち**これを緩めても受理集合は広がらない**と、決定本文が先に宣言している。
一方で維持費は実測で高い — M8 + M9 のとおり、durable spec を発行すれば 5 source のどれかを
触るたびに承認済み spec が無効化される。5 source は 17 日で 22 commit 変更されている。

- **(a) hold へ入れる** — `freeze_verification_hold` へ `s8b-oracle.generator-live-bytes` を加え、
  既存 21 件と同じ held marker 形にする。解除はユーザー明示命令のみ。
- **(b) 据え置き、durable 発行を決めるときに同時裁定する (親推奨)** — この照合が実際に噛むのは
  durable spec が存在するときだけである。今日は存在せず、§6 の blocker 群により当面存在しえない。
  **今決めても発効しない裁定に手番を使わない。** durable 発行そのものが裁定対象になる時点で、
  発行形式と一緒に決めるのが安い。
- **(c) 撤去する** — 親は推奨しない。D302 が defense-in-depth として明示的に置いた層であり、
  hold なら「保留」と機械可読に残るが撤去は痕跡が消える。

**親推奨 = (b)。** (a) は正しい方向だが今日発効しない。(c) は情報を捨てる。

**Q2. [T-782] の優先度と再訪条件。**

§2 のとおり本項は今日 1 件の判定も律速していない。**P1 から下げてよい。**

- **推奨: 条件付き保留とし、再訪条件を「durable な reviewed spec を発行するかどうかを決める段」に
  束縛する。** それは active ratified freeze の発効と §6 の blocker 解消が前提になる。

**Q3 (記録のみ、裁定不要). 承認 pin 自体は縮小対象でない。** §4 のとおり。本 wave は decisions へ記録する。

## §6 先に費用を向けるべき先 (敵対所見 A8、親が M1〜M11 で見落としていた群)

承認 pin を巡る議論より先に噛む未解決が 4 件ある。いずれも [T-987] package と
`preregistration-values.md` に記録済みで、本 wave の実測一覧には入っていなかった。

1. **judge の集約規則が未凍結。** `judge_oracle` の docstring 自身が「実測開始前に明示的な
   再凍結が必要」と書いている。
2. **spec 層が単一 block 契約 (A3-3) を検査しない。** 複数 block の spec は承認を通過し、
   manifest 生成で初めて落ちる。承認手番を消費した後に失敗する。
3. **`run_contract.contract_sha256` が activation 世代の進行で失効する。**
4. **`binding_identity` が active ratified freeze なしに導出不能。** authority は
   `LaunchValidatedFreeze.binaries_by_cell` である。

**active freeze が発効しても、この 4 件が残る限り approved spec を安全に確定できない。**

## §7 本 wave が行っていないこと

oracle spec と manifest candidate の canonical directory への書込 (0 byte)、
`APPROVED_SPEC_SHA256` の変更、contract test の変更、`SCHEMA_VERSION` の変更、
`freeze_verification_hold` の変更、機構 C1〜C6 の変更。すべてゼロである。
**fail-closed は 1 件も緩めていない。**

## §8 先行成果物との関係

同じ射程の裁定パッケージが 2 件、未裁定のまま積まれている。

- `output/insights/2026-08-12_t499-spec-producer-design/` (Q1〜Q4 未裁定)
- `output/insights/2026-08-16_t987-oracle-spec-prereg/` (D420 / D421)

**本 wave はそれらを再掲しない。** 新規差分は次の 3 点に限る。

1. **2 つの束縛の分離 (§4 と §5 Q1)。** 先行 2 パッケージは承認 pin と generator の bytes 照合を
   区別していない。D320 の対象外規定と D302 の defense-in-depth 宣言に照らすと、
   前者は不変、後者は縮小候補であり、**扱いが正反対**である。
2. **§2 の順序実測。** 今日の floor / budget が null である以上、gate 経路は凍結読込を経由せず
   承認 pin を直接踏む。先行 2 パッケージはこの経路を測っていない。
3. **§3 の現用文書訂正。** [T-987] §2 の「trust root は裁定待ち」は [T-868] に照らすと誤りである。

## §9 段 3 敵対検証の結果 (逐語は `verbatim-s3-consult-sol.md`)

親の 4 命題 (P1〜P4) は**全件反証**され、事実 3 件 (M2 の writer 数、M3 / M4 の経路数と順序、
M9 の commit 数) が訂正され、見落とし blocker 1 群 (§6) が追加された。
親は 8 所見すべてを一次資料で独立に裏取りしたうえで採用し、当初推奨を撤回した。

**この wave の主要な価値は敵対検証が生んだ。** 親単独の結論は
「承認 pin ごと hold へ入れる」であり、それは受理集合を空から任意 schema-valid spec へ広げる
規律 2 違反だった。実装差分ゼロの wave でも敵対検証を省いてはならない実例である。

## §10 dev-wave 自己改善候補 (実装せず裁定へ送る)

`DW-C00` の軽量版規定は次の順で書かれている。

> 設計択一が割れる・正しさ防壁に触る・受理集合が変わる段では独立の敵対検証子を省かない。
> …該当なしだけ**既定の軽量版**とし、段 2・3 と段 6 の review 子を省ける。
> 実装面があれば段 5 の Codex 実装子と fix 子は省略不可で、親は直接編集しない。
> **docs-only は子ゼロでよい。**

最後の 1 文は条件を再掲していないため、「docs-only なら無条件に子ゼロでよい」とも読める。
**本 wave は docs-only かつ実装差分ゼロだが、成果物そのものが受理集合に関する裁定であり、
親単独の結論は規律 2 違反の向きに倒れていた。** 敵対検証子を省いていれば、
その裁定がユーザーへ届いていた。

- **候補:** 「docs-only は子ゼロでよい」が先行する該当条件に従属することを明示する。
  受理集合・正しさ防壁・設計択一に触れる docs-only wave では段 3 を省けない。
- **本 wave では実装しない。** 自己改善契約が「段構成、実装子権限、正しさ防壁、裁定境界、
  予算の変更は実装せず裁定パッケージへ送る」と定めており、敵対検証子を省ける条件は
  正しさ防壁と裁定境界の双方に当たる。
- **参考値:** `docs/dev-wave/` の層予算は L1 = 10625 bytes、L1.5 = 9566 bytes、
  L2 単節 = 1000 bytes。`DW-C00` は L1 に属する。予算内に収まるかは実装を裁定した段で測る。
