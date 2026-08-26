# 段 6 レビュー裁定 (親)

レビュー R1 (正しさ・受理集合) と R2 (検出力・契約整合) の所見を裁定する。
親は判定のために repo 外で 2 本の probe を実走した (`/home/SFC/tanab/.claude/jobs/c6619c4f/tmp/`)。

## 実測した受理差 (変更前 = `splitlines()`、変更後 = `split("\n")`、下流 gate は同一)

JSON 文字列の値の中に候補文字を 1 個含む event:

| 文字 | 変更前 | 変更後 | 差 |
|---|---|---|---|
| VT U+000B | 拒否 | 拒否 | なし |
| FF U+000C | 拒否 | 拒否 | なし |
| FS U+001C | 拒否 | 拒否 | なし |
| GS U+001D | 拒否 | 拒否 | なし |
| RS U+001E | 拒否 | 拒否 | なし |
| NEL U+0085 | 拒否 | 受理 | **新規受理** |
| LS U+2028 | 拒否 | 受理 | **新規受理** |
| PS U+2029 | 拒否 | 受理 | **新規受理** |

2 つの正当な object を候補文字で連結した入力: **8 文字すべてが新規拒否**。

## R1-1. U+0085 の新規受理と非 LF 区切りの新規拒否 — real、ただし修正案は却下

**判定: 事実は real。ただし R1 の「8 種の受理拡大」は過大で、実測では 3 文字だけである。**

- **新規受理は 3 文字 (U+0085 / U+2028 / U+2029) に限られる。** この 3 文字は
  **JSON 文字列の中で escape 不要の正当な文字**であり、`str.splitlines()` だけが
  行境界と誤認していた。制御文字 5 種 (VT / FF / FS / GS / RS) は JSON が
  未 escape を禁じるため、変更前後とも拒否で差が無い (実測)。
  つまり U+0085 の新規受理は**裁定した修理と同一の欠陥クラス**であって、
  裁定外の受理拡大ではない。正しさゲートを緩めるものでもない
  (受理されるのは元から正当な JSON である)。
- **非 LF 区切りの新規拒否は、裁定した U+2028 / U+2029 についても等しく起きる** (実測)。
  すなわち裁定された修理そのものに内在する性質であり、追加の逸脱ではない。
  JSONL は LF 区切りが定義であり、非 LF 区切りの入力は正常入力ではない。

**却下: R1 の修正案 (JSON 文字列の quote / escape 状態を追う splitter の新設)。**
理由は 3 つ。(a) その案は「文字列の外に現れた U+2028 は依然として境界」という挙動を残すが、
実測ではその入力は変更前後とも拒否されるので、直す対象が存在しない。
(b) 手書きの JSON scanner を新設することは、行分割 1 手法の置換という裁定の範囲を大きく超え、
新しい欠陥面を作る。(c) `strict_json_loads` という既存の権威と二重の JSON 解釈を持つことになる。

**採用する対応:** 挙動を隠さず**テストで明示的に固定する**。
新規テストの separator parametrize へ `""` を加え、
U+0085 が U+2028 / U+2029 と同じく受理されることを pin する。
実測した受理差の表は段 7 で台帳へ逐語記録する。

## R1-2. CR だけの空行が blank skip される — 本 wave の変更ではない

**判定: real な事実。ただし本 wave が作った差分ではない。scope 外。**

実測 (probe 4):

- 変更前 `complete.splitlines()` → `[b'{"a":1}', b'', b'{"b":2}']` (空要素は blank skip)
- 変更後 `complete.split(b"\n")` → `[b'{"a":1}', b'\r', b'{"b":2}']` (`b"\r".strip()` は空なので同じく skip)

**変更前後で挙動が同一**である。したがってこれは本 wave の回帰ではなく、既存の性質である。
なお `parse_jsonl` (str 経路) では `_decode_jsonl` が分割前に CR を拒否するため、
CRLF 空行を含む入力はそもそも拒否される (実測: `JSONL の改行は LF のみ`)。
影響が残るのは bytes 側 5 箇所の「行に分ける前の blank skip」だけである。

`DW-G05` の成果物影響も実質ゼロである。親は封印済み codex event artifact 3,678 件を走査し、
CR を含む file が 0 件であることを実測している。

**裁定: must-fix にしない。** 拒否分岐の新設は裁定が却下した方向であり、
「6 式以外を変えない」という scope の更新を要する。段 7 で failures へ記録し、
裁定パッケージとしてユーザーへ返す。

**採用する対応:** 実装子の報告文言「CR / CRLF の過受理を拒否」は実物より広い。
台帳には**「非空の CR / CRLF 終端 event を拒否する。CR だけの空行は従来どおり skip される
(本 wave で不変)」**と正確に書く。

## R2-1. 自走 harness が import で止まる — must-fix、採用

親が実測した。`python3 orchestrator/tests/test_codex_jsonl_line_split.py` は
`ModuleNotFoundError: No module named 'orchestrator'` で rc=1。
repo 由来の import より前に `sys.path` の bootstrap が無い。

**裁定: real・must-fix・採用。** fix 子が bootstrap を足す。
`orchestrator/tests/README.md` の allowlist は編集しない。

**成果物影響:** 直接実行経路で 10 node が 1 件も走らず、二重 runner 契約を満たさない。

## R2-2. 横断メタ契約の実物監査が未閉 — 採用 (親が実施)

**裁定: real・採用。ただしコード修正ではない。**
親が焦点走の対象へ `orchestrator/tests/test_pytest_collection_config.py` と
`orchestrator/tests/test_skip_classification.py` を追加する。
親の静的確認では、新規 file は skip を持たず、書込みは `tmp_path` 内だけで、
実 repo を触らないため直列化登録の対象外である。最終的な確定は受入全走が行う。

## R2-3. 変異 #1 の killer は 4 nodeid へ展開する — nit、採用

`[u2028/u2029]` は実在する nodeid ではない。台帳と変異 spec には
parametrize 後の個別 nodeid を書く。`""` 追加後は 6 nodeid になる。

## R2-4. 2 つの fixture が過剰決定 — nit、採用 (`DW-M03`)

`test_recorded_summary_skips_crlf_terminated_event` は 2 event とも CRLF にしており、
`test_recompute_metering_rollout_rejects_crlf_terminated_event` も同様である。
どちらも対応する変異では正しく赤になるが、失敗時にどの event の CR 保存を観測したかが
一意に決まらない。

**裁定: 採用。** fix 子が単一理由へ差し替える。
`test_parse_jsonl_still_rejects_malformed_and_oversized_lines` は
冗長 gate と明記したまま変異の証拠から外す (実装子の判断は正しい)。

## fix 子へ渡す作業 (3 件)

1. 新規テスト file に `sys.path` bootstrap を足し、直接実行で 10 node 以上が走るようにする。
2. separator の parametrize (2 箇所) へ `""` を追加し、id を `u0085` とする。
3. 過剰決定の 2 fixture を単一理由へ差し替える。

**変えてはならないもの:** production の 6 式、`:327`、既存テストの期待値、
拒否分岐の新設、quote 追跡 splitter の新設。
