# 裁定パッケージ — [T-750] 統合実装 wave が返す 4 件

wave = `dev-wave-t750-freeze-v2-manifest`、base main = `0c0fbf25` → `f4db7036` 取り込み。
`DW-S04`「承認済み裁定を止めてよいのは裁定時点で未見の新事実がある場合だけ。止めるときも親が
不採用にせず、新事実付きのユーザー再裁定待ちへ戻す」に従う。

| # | 対象 | 状態 |
|---|---|---|
| **P-1** | reviewed spec / budget approval の trust root | 実装は pinned literal で暫定。**恒久形はユーザー裁定が要る** |
| **P-2** | A-9 の全層封鎖 (manifest schema への spec 伝播) | scope 拡大のため実装せず返す |
| **P-3** | budget authorization を proof chain へ通す | transition table 変更を伴うため実装せず返す |
| **P-4** | 旧 writer の任意 path 受理 | v1 受理集合の不変と衝突するため親が決めない |

---

## P-1 — 「人間が承認した」を機械で表す形が未確定

### 何が裁定されていたか

[T-782] = **(b)**: 「reviewed spec を凍結成果物として先に作り、manifest CLI はその bytes を
hash 照合するだけにする。**spec の承認者と時点は起票文で明示する**」。
[T-750](2) = **(a)**: 「後段の人間承認が budget 数値そのものを承認する契約に含める」。

### 新事実 (段 3 レンズ A・段 6 レビュー 1 が独立に指摘)

段 2 プランは承認を **「非 merge commit + 逐語 `AI-Agent: none` の Git trailer」** で表そうとした。
これは D86(8)「認可の実体はユーザーの明示指示であり、submission artifact はその指示が実行された
記録にとどまる。artifact の存在を認可の証明として扱ってはならない」に**正面から抵触する**。
AI は同じ commit を自分で作れるため、承認が**恒真化**する。

### 親が採った暫定形 (本 wave の実装)

承認 authority を **module 内の pinned literal** にした
(`BUDGET_APPROVAL_SHA256` / `APPROVED_SPEC_SHA256`、いずれも現在 `None`)。

- `None` のあいだは**あらゆる入力で fail-closed** する (`budget-approval-not-ratified` /
  `no-approved-spec`)。変異 MU-5 / MU-6 でこの分岐が実効 gate であることを裏取りした。
- 非 `None` のときだけ、固定 path の bytes hash と定数の exact 一致を要求する。
- **AI が承認者になるには、人間がコード diff をレビューして定数を置くしかない。**
  これは `V1_FREEZE_SHA256` や env contract の reviewed golden と**同じ既存パターン**である。
- approval 発行 CLI・`--approver`・既定補完は**実装していない**。

### ユーザーに決めてほしいこと

1. **この pinned literal 形を [T-782](b) の「hash 照合」の実装として承認するか。**
   (親の推奨 = **承認**。理由 = repo に既存の同型 trust root があり、AI 側に発行面が無く、
   未承認のあいだ機構全体が止まる fail-closed である)
2. **spec の承認者と時点**を確定する。親の想定 = 承認者はユーザー、時点は将来の実凍結手番。
   その手番でユーザーが行うのは (i) candidate spec の内容確認、(ii) canonical path への設置、
   (iii) 定数への hash 記入、の 3 つである。
3. レンズ A が示した恒久案「**人間だけが保持する鍵による署名**」を将来採るか。
   親は本 wave では不採用とした (repo に鍵管理の trust root が無く、新設は D86 の再裁定が要る)。

---

## P-2 — A-9 (縮小 schedule) は CLI では閉じない。choke point での最小封鎖だけ実装した

### 新事実 (段 4 の親実測 N-2 / N-3、段 6 レビュー 2 が追認)

- `s8b_oracle_driver.py:1119-1129` の `run-block` は **任意の `--manifest` path** を受け取り
  `verify_manifest` に通すだけである。report も同じ generic verifier を使う。
  → **approved CLI を足しても誰も通らない。** choke point は CLI ではなく `verify_manifest`。
- `s8b_oracle_judge.py:194-203` に部分的な product 検査はあるが、
  **全 holdout で一様に間引いた schedule は捕捉しない**。

### 親が採った措置 ([T-782](b) の文言を超える追加)

`verify_manifest` に **cell-product 検査**を足した。

- `schedule の holdout 集合 == set(freeze["holdouts"])` を先に要求する。
- 期待 cell 積を **freeze の全 holdout × 各 holdout の構成集合**から導き、exact 一致を要求する。
- `build_manifest` (generic API) の受理集合は**変えていない** (縮小は verify 側のみ)。
- 方向は**受理集合の縮小のみ**で fail-open 方向の変更を含まない。
- 既存 consumer への影響は実測ゼロ (driver / report / judge を含む 7 file が
  **498 passed / 1 skipped / rc=0**)。

**段 6 で自分の実装の穴も出た**: 最初の実装は期待積の holdout 集合を schedule 自身から導いており、
**holdout を丸ごと落とした manifest を受理していた**。レビュー 2 本が独立に指摘し fix 済み。

### ユーザーに決めてほしいこと

1. **この追加を事後承認するか** (親の推奨 = **承認**。(b) の機構だけでは certified 選択の
   直接改変が閉じないため)。
2. **残る穴を閉じるか。** cell 集合以外 (`n` / `master_seed` / campaign ID / run contract) は
   approved spec を迂回して変更でき、試行数・WAL 所有・report 数値が変わる。
   閉じるには **manifest schema へ `spec_sha256` を持たせ、driver / report / judge の全層で
   approved spec を再検証する**必要がある。これは [T-782] で不採択となった (a) 側の scope 拡大で、
   既存 manifest fixture 群の全面改修を伴う。
   択 = (A) 今回の choke point 封鎖で止める / (B) schema 伝播まで行う wave を起票 /
   (C) oracle 結線 wave へ送る。**親の推奨は (B) の起票**だが、規模は本 wave と同等以上。

---

## P-3 — budget 承認が ratified proof chain に残らない

### 新事実 (段 6 レビュー 2)

本 wave の producer は budget と承認 record の一致を**生成時に**検査するが、その事実は
candidate の非構造化 `refreeze_note` に文字列として入るだけである。

- v2 schema (`s8b_ratified_freeze.py:96-104`) に budget authorization の field が無い。
- transition table (`:128-141`) は `/budget` を**自由変更可能**としている。
- equality chain (`:146-179`) に対応する edge が無い。

→ **producer を経ずに作った自己整合な g1 でも、任意の budget が世代承認を通りうる。**

### なぜ実装しなかったか

構造化 field の追加は **transition table の変更**であり、本 wave の不変条件 3
(transition table を変えない) と、凍結契約そのものに触れる。
`DW-S04` により親は不採用にせず、新事実つきで返す。

### 択一 (親は決めない)

- **(a)** v2 schema へ `budget_authorization` を追加し、transition・ratified verifier・
  proof adjacency で trusted approval bytes と exact 束縛する (凍結契約の変更)。
- **(b)** `refreeze_note` の監査文字列に留め、budget の権威は人間手番の運用規律に委ねる
  (受理集合が広いままであることを明示受諾する)。
- **(c)** [T-657] の世代交代・恒久 freeze 機構と合流させる。

---

## P-4 — 旧 writer の任意 path 受理

`s8b_holdout_freeze.generate(output_path=...)` と `s8b_oracle_manifest.write_manifest(path, ...)` は
任意 path を受理し続けるため、programmatic には canonical namespace
(`output/s8b-freeze/`) へ到達できる。到達すると `resolve_active_generation` が
`namespace-dirty` に倒れ、certified 選択・レポート・台帳がすべて欠落する。

本 wave が閉じたのは**新設経路のみ** (v2 candidate writer と manifest CLI writer は
固定 candidate root 限定・dirfd + `O_NOFOLLOW` + `O_EXCL`)。
旧 API を狭めると **v1 の受理集合が変わる**ため、本 wave の不変条件 1 と衝突する。

択 = (a) v1 不変条件を「document 判定」に限定すると裁定し直して旧 writer を狭める /
(b) canonical namespace を OS 権限で writer から隔離する / (c) 現状維持で終端。
