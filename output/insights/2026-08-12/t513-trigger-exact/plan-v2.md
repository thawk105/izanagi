# 段 4 裁定 + プラン v2 — dev-wave-t513-trigger-exact

親が段 3 の敵対相談 2 本 (consult-a.md = レンズ A、consult-b.md = レンズ B) を裁定した結果。
実装子はこの文書と `plan.md` を正本とし、両者が食い違う場合は**本書を優先**する。

## 所見の裁定

| # | 所見 | 判定 | 採否 | scope |
|---|---|---|---|---|
| A-1 | mask=20 の一般化は全 32 mask で成立 | refuted (親の実測は正しい) | — | — |
| A-2 | 複数行化は fail-closed | refuted | — | — |
| A-3 | **CRLF source が exact 比較を迂回する** | real | **採用** | scope 内 |
| A-4 | 比較変更は受理集合を拡大しない | refuted (包含証明は成立) | — | — |
| A-5 | **drift 検査の locator が非一意** | real | **採用** | scope 内 |
| A-6 | fixture 是正は正しさゲートの緩和ではない | refuted | — | — |
| A-7 | **binding 省略で exact admission を迂回できる** | real | **不採用** | **scope 外 → 裁定パッケージ** |
| B-1 | producer 列挙の記録不足 | real | **採用 (記録面のみ)** | scope 内 (docs) |
| B-2 | 7 nodeid 中 3 件は `.strip()` mutant を検出しない | real だが nit | 不採用 | — |

### A-3 を採用する理由

`parse_template_file` は `open(..., encoding="utf-8")` を newline 指定なしで開くため、
Python の universal-newline 変換で `I + E_m + b"\r\n"` が `"  " + E_m` へ復号される。
すなわち CR は比較前に消え、raw bytes では emitter が生成しない source が exact 比較を通る。
CR は旧 `.strip()` でも除去されていたので、これは T-513 が閉じるべき
「外周空白を保持した source」族そのものである。exact を名乗る以上、閉じなければ主張が偽になる。

**実装制約:** 共有 parser (`parse_template_file`) の newline 挙動を変えてはならない
(quarantine 経路の全 consumer に波及する)。`_require_materialized_trigger_predicate` の内側だけで、
hole の**物理行 raw bytes** を検証すること。`parse_template_file` は hole の行番号の特定にだけ使い、
比較は同じファイルを binary で読み直した bytes で行う。

### A-5 を採用する理由

`+#if BACKOFF_TRIGGER_GATING` は patch 内に 11 箇所ある。generic な検索で位置を決めると、
実 hole が drift しても別ブロックを掴んで緑になりうる (恒真ではないが偽陰性)。
`+  // EVOLVE-BLOCK-BEGIN <MARKER_ID>` と `+  // EVOLVE-BLOCK-END <MARKER_ID>` が
**各 1 回だけ**出現することを assert し、その閉区間の内側でだけ `#if` / `#else` を探すこと。

### A-7 を不採用 (scope 外) にする理由

閉じるには s8a sweep / S-1 direct comparison / S8b oracle / S8b floor / S-1 extime calibration の
5 経路へ binding を結線するか、build gateway 側で trigger axis を検出して semantic admission を
必須化する必要がある。これは裁定 (「exact 比較へ」) が認可した受理集合変更の範囲を超える
**新規の受理要件**であり、親が勝手に採用しない (DW-S04)。裁定パッケージとしてユーザーへ返す。

**その代わり、成果物の主張を狭める。** 本 wave が閉じたのは
「binding を伴う lane の build admission」であって、trigger source 一般ではない。
worklog / insights にはこの限定を明記し、「build admission の穴を閉じた」と無限定に書かない。

## gate の署名 (DW-S04)

```
admission_accepts(source S, mask m) :=
      parse_template_file(S, MARKER_ID) が marker を返す
    ∧ hole がちょうど 1 物理行
    ∧ その物理行の raw bytes == b"  " + emit_predicate(TriggerGateIR(m)).encode("utf-8")
```

行末の `\n` / `\r\n` / EOF は物理行の payload に含めない
(改行そのものは payload ではない) が、**`\r` は payload の一部として拒否する**。

**通る正例 (必ず 1 つ添える):**
骨格 (`+  izanagi_gate_pass = true;` を hole に持つ EVOLVE-BLOCK) に対し
`render_hole(base_text, marker, emit_predicate(TriggerGateIR(m)))` を適用し、
LF 改行で書き出した source。この source は全 32 mask で受理されなければならない。

## 実装 scope (プラン v2)

`plan.md` の内容を次の 3 点で上書きする。それ以外は `plan.md` どおり。

1. **比較を raw bytes で行う** (A-3)。`_require_materialized_trigger_predicate` は
   hole の行番号を `parse_template_file` から得たうえで、同ファイルを binary で読み直し、
   その物理行の bytes を `b"  " + emit_predicate(...)` と比較する。
   `\r` を含む source は拒否されること。共有 parser は変更しない。
2. **drift 検査の locator を BEGIN/END 閉区間で一意化する** (A-5)。
   BEGIN / END の出現回数が各 1 であることも assert する。
3. **テストを 2 本追加する** (計 9 nodeid)。
   - `..._rejects_materialized_predicate_with_crlf_line_ending` — `I+E_m+b"\r\n"` を拒否
   - `..._rejects_materialized_predicate_with_cr_only_line_ending` — CR-only 行末を拒否
   (名前は実装子が既存命名規約へ合わせてよい。攻撃形が閉じることが要件)

## 変異事前登録 (DW-M01)

実装前に次を登録する。期待 node の**完全集合**は統合 commit 後に再導出する (DW-M07)。

| ID | category | 変異位置 | 単一理由性 | 期待 |
|---|---|---|---|---|
| M1 | negative | `pipeline.py` の比較を旧 `.strip()` 形へ戻す | 攻撃テストは admission 関数を直接呼ぶため手前の層が同じ入力を拒否しない | KILLED (外周空白 4 形の攻撃テスト) |
| M2 | positive-control (過剰拒否検出) | `PREDICATE_HOLE_INDENT` を `"  "` → `"    "` | 定数は admission / fixture / drift の 3 箇所で使われる冗長 gate。過剰拒否を検出する正例が目的なので完全集合で記録する | KILLED (正例 + drift + 4 空白攻撃テスト) |
| M3 | negative | raw bytes 読み直しを parsed text 比較へ戻す | CRLF テストだけがこの分岐に依存 | KILLED (CRLF / CR-only テスト) |
| M4 | negative | `patches/silo-...-variant.patch` の hole 行 indent を 2→4 空白へ変える | drift 検査だけが patch 実バイトを読む | KILLED (drift テスト) |

M2 は受理集合を縮める wave における「承認外の過剰拒否を検出する正例」の登録である (DW-M01)。

## 不変条件 (再掲・実装子が守る)

- 受理集合は縮む方向のみ。変更前に拒否され変更後に通るものを 1 つも作らない。
- `emit_predicate` / `canonicalize_predicate` / 正準集合 / `parse_template_file` を変更しない。
- 例外文言 `trigger binding predicate が materialized source と不一致` を変更しない。
- 8c 結線 wave 所有ファイル (`reflux_origin_artifacts.py` / `reflux_source_closure.py` /
  `s8b_descriptor.py` / `orchestrator/campaign/wal.py`) に触らない。
