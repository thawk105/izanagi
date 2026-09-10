# 裁定パッケージ — [T-714] 実装中に見つかった同型欠陥 (NUL ほか)

wave: `dev-wave-t714-evidence-path-ctrlchar` / 2026-08-10 / base main `e91bf56d`

[T-714] は裁定 (a) どおり CR/LF を fail-closed 拒否として実装した。その過程で、
**同じ機序の穴が NUL でも成立する**ことを親が独立に実測した。承認された裁定の文言は
CR/LF であり、親が承認外の gate を足すのは過去の失敗型 (F186) なので**実装せず裁定へ返す**。

## R1 (新規・要裁定) — NUL 付き path が prefix blob へ alias する

### 実測 (worktree HEAD b0b84837、`premise_probe2.py`、blob OID で照合)

| 入力 | blob OID | bytes |
|---|---|---|
| `CLAUDE.md` | `1744da0e…` | 13812 |
| `CLAUDE.md\r` | `1744da0e…` | 13812 |
| **`CLAUDE.md\x00not-the-contract-path`** | **`1744da0e…`** | **13812** |
| `CLAUDE.md\t` | — (missing) | — |

`git cat-file --batch-check` は要求行を NUL で切り詰めるため、NUL 以降が捨てられて
prefix の blob が返る。CR/LF の場合と**完全に同型**である。

### 現状の防壁

- 本 wave の実装後も、`_safe_path` と `read_blob_at` は **NUL を受理する**。
- `_nonempty_string` の `value != value.strip()` は NUL を落とさない
  (Python の `strip()` の空白集合に NUL は含まれない)。
- したがって、契約が `foo\x00bar` を参照すると `foo` の blob を証拠として採用できる。

### 影響 (実装しない場合)

`EvidenceRef` の path / hash 対応、12 述語の status、activation report の digest、
certified 選択と trial ledger の参照が、実在しない path の証拠で満たされうる。
CR/LF について今回塞いだ穴と同じ値・同じ受理集合・同じ参照が対象である。

### 選択肢

- **(a) NUL も同じ 2 層で fail-closed 拒否する (推奨)。** 変更は今回と同型で、
  受理集合が狭まる対象は「証拠として一意に解決できない path」だけである。
  実 git path に NUL は入れられないため、正当な path を失わない。
- (b) 制御文字一般 (C0 全体) を拒否する。tab などは alias しないと実測済みなので、
  同一性の観点では過剰。ただし path として異常な値を一括で閉じられる。
- (c) 現状維持。CR/LF だけ閉じ、NUL の経路は残す。

## R2 (従属・低優先) — 直接 caller には `./` 系 alias が残る

`read_blob_at("./CLAUDE.md")` は `CLAUDE.md` の blob を返す (git の revision 構文)。
ただし契約経路では `_safe_path` が `contract-path` で既に拒否するため、
現行の production 経路に穴はない。`read_blob_at` を汎用 path validator と
みなさない (「CR/LF framing wall」と位置づける) 記述上の整理で足りる、というのが親の判断。
primitive 自体に canonical path 契約を持たせるなら CR/LF 以外の受理集合変更になるため裁定が要る。

## R3 (観測・実装不要) — freeze と activation の状態分離

不正 path を含む契約でも `validate_condition_freeze_at` は raw hash しか見ないため
freeze-valid になり、registry 評価で初めて `evidence-contract-invalid` になる。
これは `..` を含む path でも同じ既存挙動で、本 wave が変えたものではない。
freeze 側にも schema/path 検査を置くかは別裁定。

## 親が実装した範囲 (参考)

CR/LF のみ。`read_blob_at` は git へ渡す値そのものに検査を掛け (str subclass の
`__format__` 上書きでも破れない形)、`_safe_path` は `_nonempty_string` より前に
明示拒否する。NUL・tab・その他制御文字・`./` 正規化・非文字列拒否は実装していない。
