# 段 4 裁定 — [T-714] CR/LF path の fail-closed 拒否

base: main `e91bf56d` を ff-only 取り込み済み。provenance 監査 rc=0 (2070 件、新規違反なし)。
親の独立裏取りは `premise_probe2.py` (blob OID / sha256 で同一性を測る版) で実施した。

## 親の独立実測 (probe v2、commit b0b84837 時点)

| 入力 | blob OID | 判定 |
|---|---|---|
| `CLAUDE.md` | `1744da0e…` (13812 bytes) | 基準 |
| `CLAUDE.md\r` | `1744da0e…` | **alias 成立** (OID 一致で確認、長さ一致ではない) |
| `CLAUDE.md\x00not-the-contract-path` | `1744da0e…` | **alias 成立 (NUL、同型欠陥)** |
| `CLAUDE.md\t` | — (missing) | alias しない |
| `./CLAUDE.md` | — | `_safe_path` が `contract-path` で拒否済み |
| `Path("CLAUDE.md")` (非 str) | `1744da0e…` | 非文字列も f-string 経由で通る |

## 所見の裁定

| # | 所見 | 判定 | 処置 |
|---|---|---|---|
| A1 | NUL が prefix blob へ alias する (CR/LF と同型) | **real (親が独立裏取り)** | **本 wave では実装しない (裁定 (a) の文言外、F186 の型)。裁定パッケージでユーザーへ返す。**保証文を「CR/LF alias のみ閉鎖」に狭める |
| A2 | 直接 `read_blob_at` には `./` 系 alias が残る | real・scope 外 | `read_blob_at` の guard を「CR/LF framing wall」と位置づけ、汎用 path validator と呼ばない。裁定パッケージへ従属所見として添える |
| A3 | `isinstance(path, str)` guard は非 str を素通し | **real・採用** | guard を「git へ渡す値そのもの」に掛ける形へ変更する (下記 plan v2 1)。受理集合は広げない (非 str の従来挙動は不変、CR/LF を含む場合だけ新たに拒否) |
| A4 | 親 probe は長さしか比べておらず「同一 blob」を実証していない | **real・採用** | probe v2 で OID / sha256 比較へ差し替え済み。以後の記録は probe v2 を根拠にする |
| A5 | brief の `_safe_path` 受理集合の記述が不正確 | **real・採用** | 記録時に「`strip()` は先頭・末尾の CR/LF/tab を落とす。埋め込み CR/LF は canonical・非 `..` 条件を満たす場合に受理される」と書き直す |
| A7 / B1 | module bytes 変化 → activation report digest → trial ledger へ波及 | **real・採用 (記録の訂正)** | brief の (iv)「producer 出力 bytes 不変」は誤り。凍結成果物 (FROZEN_MANIFEST / g1) は不変で再発行不要、一方 activation report の module hash と digest は commit 相応に変わる、と分けて記録する。実装変更なし |
| B3 | 不正 path 契約でも freeze 検証は通り、registry で初めて invalid | real・scope 外 | 既存挙動 (`..` 等でも同じ) で本 wave が変えるものではない。観測として記録し、freeze 側 schema 検査の要否は裁定パッケージへ |
| B4 | 埋め込み CR/LF の fixture が alias を実証していない | **real・採用** | prefix path (`alias-`) を別 bytes で commit し、guard 不在時に**別 blob が返る**ことを実証する形へ変える (plan v2 2) |
| B2 | caller 閉包に二重 namespace と派生 consumer が未記載 | should-fix・採用 | 実装子の完了報告で両 namespace と公開経路を列挙させる |
| A9 / B5 | 正例・既存回帰は guard 削除でも緑 | **real・採用** | 変異の帰属から外し、正例は「過剰拒否検出器」として別枠登録する (M13/M14) |
| B6 | HEAD 依存テストは cross-wave 差分で赤くなりうる | real・採用 | 変異の期待 first-failing nodeid から除外する |
| A6 / B7(i)-(iii) | 現行成果物への誤爆なし、pin 不在・契約 CR/LF 0 件・理由語 0 件は真 | 追認 | plan 維持 |

## plan v2 (段 2 プランからの差分だけを書く)

1. **`read_blob_at` の guard 形。** `isinstance` で分岐して非 str を素通しにせず、
   git へ渡す値を一度だけ文字列化し、**その同じ値**を検査してから spec を組む。

   ```python
   text = path if isinstance(path, str) else str(path)
   if "\r" in text or "\n" in text:
       raise PreregistrationError("path-control-char")
   ...
   spec = f"{resolved}:{text}"
   ```

   非 str は従来も f-string で `str()` 化されていたため、**CR/LF を含まない入力の受理集合は不変**。

2. **埋め込み CR/LF テストの fixture 強化。** 埋め込み LF/CR の実証は、
   guard 不在時に「missing になる」ではなく「**別 path の blob が返る**」ことを見せる形にする。
   `alias-` (prefix) と `alias-\r-target.txt` 相当の意図された path を**別 bytes**で commit し、
   guard 不在なら prefix の blob が返りうることを固定する。

3. **変異の帰属を新規 tmp-git テストと明示 reason loader テストに限定する。**
   HEAD 依存テスト (`test_current_repository_gap_reason_snapshot_...`、invariant の candidate test)
   を期待 first-failing から除外する。

4. **正例を過剰拒否検出器として登録する** (M13/M14、`DW-M01` の受理集合縮小 wave 要件)。

5. NUL・tab・その他制御文字・`./` 正規化・非 str 拒否・`ruleops.py`・freeze 側 schema 検査は
   **実装しない**。

## 変異事前登録 (DW-M01 / B-057)

production だけを変異させ、テストは固定する。各変異は「同じ入力を拒否する層が前後にない」ことを
確認済み (loader テストは git を触らず、core テストは loader を通らないため、両 guard は互いを mask しない)。

| # | file | 変異 | 期待 first-failing nodeid | 単一理由性の根拠 |
|---|---|---|---|---|
| M01 | `s8c_preregistration.py` | CR/LF guard 全削除 | core: 末尾 CR alias テスト | 前後層なし (git へ直行) |
| M02 | 同 | LF 条件を削除 (CR のみ検査) | core: 埋め込み LF テスト | 同上 |
| M03 | 同 | CR 条件を削除 (LF のみ検査) | core: 末尾 CR alias テスト | 同上 |
| M04 | 同 | reason を `blob-missing` へ改名 | core: 末尾 CR alias テスト | reason assert が単一理由 |
| M05 | 同 | 例外 detail に生 path を追加 | core: 単一行 message assert | 同上 |
| M06 | 同 | 文字列化前の値でなく `str(path)` 以外を検査 (非 str 素通し) | core: 非 str + CR テスト | 同上 |
| M07 | `s8c_preregistration_evidence.py` | `_safe_path` の guard 削除 | loader: 埋め込み CR テスト | `_nonempty_string` は埋め込みを拒否しない |
| M08 | 同 | guard を `_nonempty_string` の後へ移動 | loader: 末尾 CR の明示 reason テスト | 付随的 `contract-string` と区別する assert |
| M09 | 同 | LF 条件を削除 | loader: 埋め込み LF テスト | 前後層なし |
| M10 | 同 | reason を既存 `contract-path` へ変更 | loader: 埋め込み CR テスト | reason assert が単一理由 |
| M11 | 同 | detail に生 value を入れる | loader: 単一行 message assert | 同上 |
| M12 | 同 | required path の `_safe_path` を `_nonempty_string` へ置換 | loader: 埋め込み CR (required) | consumer 側は別変異 |
| M13 | `s8c_preregistration.py` | guard を無条件 raise (**過剰拒否**) | core: 正常 path の正例 | 正例が唯一の検出器 |
| M14 | `s8c_preregistration_evidence.py` | guard を無条件 raise (**過剰拒否**) | loader: 正常 path の正例 | 同上 |

## gate の署名 (DW-S04)

- 禁止: `read_blob_at(root, commit, path)` において `str(path)` が U+000D または U+000A を含む呼出し。
- 禁止: evidence contract の `required_evidence[*].path` および `consumer_requirement.path` が
  U+000D または U+000A を含む契約の読み込み。
- **通る正例:** `read_blob_at(root, HEAD, "CLAUDE.md")` は従来どおり blob bytes を返し、
  `required_evidence[*].path = "nested/evidence.py"` の契約は従来どおり load できる。
