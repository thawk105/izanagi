# 段 4 裁定 — [T-244] 8c 結線の前提設計 wave

## 1. 結論

段 2 のプランを**基礎として採用し**、段 3 の 2 レンズが挙げた blocker 8 件・must-fix 8 件のうち
**16 件すべてを real と裁定**した。うち 11 件は設計本文へ織り込み、5 件は
「実装すれば受理集合・防壁・費用・批准値が変わる」ため裁定パッケージとしてユーザーへ返す。

レンズの判定は「このプランのまま設計本文を確定するのは NO-GO」であって、
「設計 wave をやめよ」ではない。**所見を織り込んだ設計本文を land する**のが本 wave の帰結である。

**実装差分は無い** — 差分は `docs/phase3-8c-wiring-design.md` (新規)、`docs/README.md` の 1 行、
本 insight、spool fragment だけである。したがって変異 matrix と受入全走は対象外 (`DW-S04`)。

## 2. 親が現物で裏取りした blocker (レンズの主張の検算)

以下は親が worktree の現コードを直接読んで確認した。レンズの逐語をそのまま採ったのではない。

### K1 — 末尾の全 tombstone batch は certifiable seal を通る (レンズ A-3、real)

`reflux_origin_ledger.py:1618-1629` の candidate 下限検査は
`0 < batch.sealed_distinct_candidate_count < minimum` である。**全 tombstone batch は左辺が 0 なので
検査に入らない。** floor は `state.sealed_queries` (non-tombstone のみ) を見るため、33 行成功後に
2 行の全 tombstone batch を足しても `sealed_queries=33` は変わらず `aborted=False` を送れる。
→ 設計 §4.1 条件 10 で consumer が禁止する。ledger 側で塞ぐかは **V-6**。

### K2 — production runtime の初期化経路が存在しない (レンズ B-3、real)

`reflux_origin_ledger.py:2917-2919` は `if not store.fixture: _fail("production runtime
initialization is forbidden")`。初期化を呼べるのは private な `_fixture_store_for_test` だけである。
つまり**発行 3 条件を満たしても、最初の `read_origin` / reserve は runtime 未初期化で失敗する。**
→ 設計 §9 に残余として明記。作り方は **V-7**。

### K3 — 同一 mask の重複行は現 campaign ループが物理実行しない (レンズ A-4、real)

`loop.py:242-246` は `v = variant_id(g, src_tok); if v in done: s.skipped += 1; continue`。
source の mask は validation sweep にも現れるため、同一 run 内では 2 回目が skip される。
skip は evidence record を持たないので tombstone となり、`sealed_queries ≤ 32` で floor 33 を割る。
→ 設計 §5.3 が「1 query ordinal = 1 campaign run」を要件化。費用 33 倍の是非は **V-8**。

### K4 — state commitment は authority 全体の global CAS (レンズ A-5 / B-4、real)

`_state_commitment` の preimage は `origins` (全 origin の event index・sha・semantic sha) と
runtime head を含む (`:2510-2542`)。`operation_id` も authority 全体で一意 (`:2656-2694`)。
よって「直前 receipt の `resulting_state_commitment` を次 event の expected にする」という
段 2 の回復手順は、別 origin が間に commit しただけで CAS mismatch になる。
→ 設計 §7.3 で「**次 event の base には `current_state_commitment` (または再読した snapshot) を使う**。
receipt を失った event の再送だけが envelope の元 base を使う」と訂正。

### K5 — `launch_admission_record` は exact 7 key で completeness が pin している (レンズ B-5、real)

`trial_registry.py:1295-1321` の返す 7 key と、`autonomous_trial_completeness.py:63-70` の
`_LAUNCH_ADMISSION_KEYS` が一致している。`origin_binding` を無条件に足すと**originless な既定経路の
bytes が変わり**、consumer が拒否する。
→ 設計 §6.5 で「capability 発行時だけ key を出す (`null` も置かない)」「consumer は同じ変更単位で
optional key として更新する」「既定 bytes は非揮発 field 集合の比較で守る」と規定。

## 3. 所見の real / refuted 裁定

### レンズ A (恒真化・正しさ境界)

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| A1 | create-only は issuer 認証ではなく物理実行 0 件経路が残る | **real** | 設計 §3.6 に保証限界として明記。権限分離の是非は **V-10** |
| A2 | formal-consumer receipt が未定義で恒真 gate になる | **real** | 設計 §4.3 で receipt の exact 要件 (state commitment 束縛・payload digest 束縛・one-shot) を規定 |
| A3 | 末尾の全 tombstone batch で certifiable にできる | **real (K1)** | 設計 §4.4 + **V-6** |
| A4 | source と同 mask の validation が duplicate skip される | **real (K3)** | 設計 §5.3 + **V-8** |
| A5 | crash replay が別 origin の interleave を扱えない | **real (K4)** | 設計 §7.3 |
| A6 | mask producer と検査器が同じ canonicalizer を使う | **real** | 設計 §2.2 で「実装 bytes を trust root にしない」と明記。independent golden の要求は既決 |
| A7 | 「series 内」保証は存在しない | **real** | 設計 §2.4 で「同一 authority blob 内」へ縮小し、consumer に 3 つ組 scope を義務化 |
| A8 | `certifying=False` と ledger の `certifiable` の境界が prose だけ | **real** | 設計 §6.4 で「ledger terminal を昇格根拠にしない」と規定 |
| A9 | 予約前の引き直し残余を prose で閉じたように見せている | **real** | 設計 §8 で run plan の作成時点を明示し、残余を D205 の下で受容と記録 |

### レンズ B (受理集合・順序・既定経路)

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| B1 | 33 record と 33 物理 attempt の双射が無い | **real** | 設計 §4.2 で双射 3 条件 (attempt id 相異・WAL 区間非重複・WAL の trigger binding 一致) を必須化 |
| B2 | receipt に schema も発行権限も無い | **real** | A2 と同一。設計 §4.3 |
| B3 | production bootstrap と public fixture 正例が無い | **real (K2)** | 設計 §9 + **V-7**。公開正例は §12-1 で実装 wave の受入条件へ |
| B4 | crash recovery が restart-safe でなく global CAS 連鎖が誤り | **real (K4)** | 設計 §7.3 + §7.5 (process crash で in-process seal を失う場合は非終端のまま記録する) |
| B5 | `origin_binding` 追加が既定 bytes と completeness を壊す | **real (K5)** | 設計 §6.5 |
| B6 | topology は parser 上成立するが producer と post-commit 余裕が無い | **real** | 設計 §5.4 で親が独立に検算し、post-commit crash 余裕が無いことを明記。再批准は **V-9** |
| B7 | §7 要件と下流層を brief が scope 外へ落としている | **real** | 設計 §12 で残り 5 要件と未着手 2 層 (completeness / 材料レポート renderer) を実装 wave の受入条件として明記 |

### 2 レンズが逆を向いた点

無い。両者は独立に NO-GO を返し、blocker の指す穴も重複が少なく相補的だった
(A は恒真化と物理実行の偽装、B は受理集合と経路の不在)。A3 と B6 だけが topology の同じ面を
別角度から撃っている。

## 4. 撤回する親の provisional 裁定

- **(P1) の「1 authority series 内」を撤回する。** 現 loader が保証するのは同一 authority blob 内の
  4-tuple 重複拒否だけである。設計は「同一 authority blob 内」へ縮小し、下流 consumer に
  `(authority_blob_sha256, origin_id, cell_key)` の 3 つ組 scope を義務づけた。
- **(P2) の「seal builder だけで閉じる」を撤回する。** ledger は evidence digest を dereference
  しないため、builder だけでは物理実行 0 件を防げない。formal consumer + 双射 + receipt 束縛を追加した。
- **(P3) の「33 行を 4 batch 以下へ割る」を撤回する。** P6 の一括 commit 条件と 1-open-batch FSM に
  より、**1 batch 33 行に強制される**。「行数下限 2 が自然に満たされる」という親の仮説自体は成立するが、
  「V-3 の不整合は探索側にだけ残る」は誤りだった — 33 outcome を 1 drive 内で生む producer は
  存在しないので、不整合は harness 側にも残る。
- **(P5) の「新 event は足さない」は条件付きで維持する。** 意味は既存 6 event で表現できるが、
  durable recovery envelope が無ければ再送 payload を復元できない。「足りないのは event ではなく
  材料」という条件を本文へ明記した。
- **(P4)・(P6) は維持する。** ただし (P4) は capability の束縛対象を authority blob・cell・
  source closure・expected axis/verifier/environment まで広げ、raw public API からの迂回禁止を加えた。

## 5. 段 1 実測値の一般化に対する訂正 (レンズの指摘を採用)

- `batch_count = min(imax, qmax // 2) = 4` は `_check_budget_codec_feasibility` の**容量計算上の
  batch 数**であって、実 producer の batch 数ではない。実 topology は 1 batch である。
- brief の phase 列は happy path であり、abandon・複数 batch・他 origin の interleave を
  含む FSM 全体ではない。
- 「sealed launch admission」は同一 process 内の issued-value gate であって durable capability ではない。
- 32 mask の正準集合は emitter の有限集合を示すだけで、32 物理 attempt producer の存在を示さない。
- codec bytes (75,206 / 30,753) は feasibility estimator の合成 frame 値であり、
  本 topology を公開経路で流した実測値ではない。
- outcome 受理表・`minimum=2`・FSM の合法遷移・公開 API の `_production_store()` 固定は
  静的コードと一致した。ここへの不同意は両レンズとも無い。

## 6. ユーザーへ返す裁定パッケージ (5 件)

正本は `docs/phase3-8c-wiring-design.md` §11。要旨のみ再掲する。

| # | 択一 | 親の推奨 |
|---|---|---|
| **V-6** | 末尾の全 tombstone batch を ledger 側でも拒否するか | **(a) 拒否する** (受理集合の変更) |
| **V-7** | production runtime の初期化経路 | **(a) 人間承認 provisioning と同じ手続で人間が一回だけ実行** |
| **V-8** | 物理実行の単位を「1 query = 1 campaign run」とするか (費用 33 倍) | **(a) そうする** |
| **V-9** | `imax` / `qmax` の再批准 (内訳が変わり post-commit 余裕が無い) | **(a) 内訳を差し替えて `4/68` を維持** |
| **V-10** | evidence writer の権限分離を作るか | **(a) 作らず保証限界として明記** |

## 7. 本 wave の射程 (`DW-S04`)

**実装差分が無いため、変異 matrix と受入全走は対象外である。** 変異事前登録も行っていない
(登録すべき変異面が存在しない)。将来の実装 wave 向けの変異登録候補は設計 §12-7 に置いた。
段 1 の前提実測は repo 外の使い捨て probe で行い、repo へは 1 byte も書いていない。
probe の逐語と出力は `parent-measured.md` へ凍結した (実行可能資材そのものは repo へ持ち込まない —
`docs/ai-provenance.md` の実装面契約に従い、probe の `.py` は commit しない)。

差分は docs 3 点 (新規設計・`docs/README.md` の 1 行・本 insight) と spool fragment だけであり、
`tools/check_docs.py` と fold dry-run を直接緑にして閉じる。
