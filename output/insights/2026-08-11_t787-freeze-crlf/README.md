# 2026-08-11 [T-787] 凍結発行・検証層への CR/LF 検査拡張 — 逐語と実測

裁定 (a)「CR/LF を NUL と同じ扱いで凍結発行・履歴検証の層でも fail-closed 拒否する」を実装した
dev-wave の一次資料。設計判断の正本は decisions、経緯の正本は worklog の該当エントリ。
ここには逐語と実測値を置く。

## 何を塞いだか

`evidence_contract_sha256()` は発効層の `load_contract_bytes()` を通らないため、証拠 path に
CR / LF を含む契約でも hash を返し、凍結発行 (`prepare_revision`) と履歴検証
(`validate_condition_freeze_at`) がその契約を凍結記録へ束縛できた。発効時にだけ
`contract-path-control-char` で倒れる非対称が残っていた。[T-739] が NUL について塞いだ穴の
CR/LF 側の残りであり、[T-714] (証拠同一性層の CR/LF 拒否) の先例と揃う。

## 実測 (probe は repo 外で走らせた運転用のもの。ここには逐語だけを置く)

| 測定 | 値 |
|---|---|
| `evidence_contract_sha256(CR 入り契約)` の変更前の戻り値 | `00205cec988138cc…` (拒否せず受理) |
| `evidence_contract_sha256(LF 入り契約)` の変更前の戻り値 | `e7e1e5857c11e578…` (拒否せず受理) |
| 同じ契約を `load_contract_bytes` へ | `contract-path-control-char` で拒否 |
| 現行契約の `evidence_contract_sha256` | `c4f3740202de302c9dafc9cecac39165bc2213ebf425d2da8cf7ede91b264471` (変更前後で不変) |
| 既発行 g1 の `protected_sha256` | `853e6c44442780f180997b86819efaa8cbf245ae15d1a37a83e5b9a4ee99286e` (不変) |
| 実契約の `path` field 数 | 38 (CR/LF/NUL を含むものは 0 件) |
| 前=CR 後=NUL の契約 (変更前) | `[evidence-contract-path-nul] '/conditions/11/consumer_requirement/path'` |
| 焦点テスト (段 5 実装後) | 349 passed / rc=0 / 42.07 秒 |
| 焦点テスト (段 6 fix 後) | 365 passed / rc=0 / 41.56 秒 |

**「前=CR 後=NUL」の実測が設計を決めた。**CR/LF を見つけた場で拒否すると、この契約の診断が
後方 NUL の pointer から前方 CR の pointer へ変わる。既存の NUL 診断契約を壊さないため、
CR/LF は文書順で最初の pointer だけ保留し、走査完了後に NUL が 1 件も無かった場合だけ拒否する。

## 変異

anchor commit は `35f2b309cdf8f642326635441b5b79474036cb9b`。runner は
`tools/run_tests.py --force-dispatch`、runner-mode は dispatch。
**期待 node は手打ちせず、`--collect-only` で得た 324 node の完全集合に対する述語で機械導出した。**
置換は全 15 箇所とも対象ファイルに exact 1 回だけ命中することを事前検査した。

### 受理集合を守る面 (8 件)

| id | 変異 | 期待 = 実測 |
|---|---|---|
| M1-revert-nul-only | 検査関数を wave 前の NUL-only 実装へ exact revert | 112 |
| M2-drop-cr | CR 判定だけ削除 | 56 |
| M3-drop-lf | LF 判定だけ削除 | 56 |
| M7-endswith | `in` を `endswith` へ狭める | 108 |
| M10-conditions-subtree-only | 走査を `/conditions/` 配下に限定 | 14 |
| M8-drop-is-path | `is_path` 条件を削除 (過剰拒否の正例) | 6 |
| M9a-all-c0 | CR/LF 判定を全 C0 へ拡大 (過剰拒否の正例) | 5 |
| M9b-unicode-newlines | U+0085 / U+2028 / U+2029 も拒否 (過剰拒否の正例) | 3 |

`M1` は wave 前の実コードの形そのものである。`M8` / `M9a` / `M9b` は承認外の過剰拒否を
検出する正例で、いずれも「拒否を強めた実装」を殺す向きに働く。

### 診断感度の pin (6 件)

受理集合は変えず、理由語・pointer・検査順だけを変える変異である。`DW-M08` に従い
受理集合の kill とは別枠に数える。

| id | 変異 | 期待 = 実測 |
|---|---|---|
| M4-crlf-immediate-raise | CR/LF を保留せずその場で拒否 | 2 |
| M5-crlf-last-pointer | 最初でなく最後の CR/LF pointer を採る | 4 |
| M6-scan-order-reversed | dict / list 両方の `reversed` を外す | 5 |
| M11-before-canonical | 検査を canonical 化の前へ移動 | 3 |
| M12-crlf-reason-unified | CR/LF の理由語を NUL 語へ統一 | 112 |
| M13-detail-carries-node | detail に pointer 以外を載せる | 110 |

### 初回 run の MISMATCH 1 件 (erratum、DW-M02)

初回 run は 13 KILLED / 1 MISMATCH だった (`mutation-ledger-run1.json`)。MISMATCH は
`M13-detail-carries-node` のみで、**原因は実装ではなく親の期待集合の誤り**である。
`ActivationReport` は `exc.reason` だけを載せて detail を持たない
(`s8c_preregistration.py` の `freeze_reason = exc.reason` → `freeze_reason_code=freeze_reason`)
ため、detail を汚す変異は `test_activation_report_marks_legacy_crlf_bound_freeze_invalid[cr|lf]`
の 2 node へ構造的に届かない。初回の期待はこの 2 node を含んでいた。
期待を 110 node へ訂正して同じ anchor で再走し、完全一致で KILLED になった
(`mutation-spec-m13-rerun.json` / `mutation-ledger-m13-rerun.json`)。
**初回台帳は消さずここに残す。**

## 受理集合の変化 (1 点のみ)

parse と canonical 化の両方に成功する入力のうち、key が exact `path` で値が `str`、かつ
CR (U+000D) または LF (U+000A) を含むものだけが新たに拒否される。次はいずれも従来どおり通る。

- `path` 以外の field の CR / LF / NUL
- `path` を key に持つが値が `str` でないもの (dict / list / number)
- CR / LF / NUL 以外の制御文字 (TAB・BS・FF・VT・U+0001) と U+0085 / U+2028 / U+2029
- 文字どおりの 2 文字 `\r` `\n` (backslash + 英字)
- NUL を含まない schema 違反

NUL 入り入力の理由語・pointer・優先順位は 1 つも変わらない。

## 敵対検証

段 3 (プラン) と段 6 (実装) で計 4 本。段 3 は 2 本とも NO-GO、段 6 は A=GO / B=NO-GO。
**レンズが親の設計と親のテスト要求の両方で実際に誤りを見つけた。**

- 段 2 起草が「node 内で NUL を先に見るだけでは不変条件が守れない」と親案を倒した (親が実測で裏取り)。
- 段 3 レンズ A が「NUL の全域優先は 1 契約内でしか成立せず、履歴では祖先順に決まる」ことを示した。
  親は不変条件の射程を単一 hash 呼出し内に限定する裁定で閉じ、履歴側の挙動をテストで固定した。
- 段 6 レンズ B が、発行 API (`prepare_revision`) の CR/LF テスト欠落と、
  「tip だけ新検査・祖先は旧経路」という弱実装が生存することを示した。
- 同レンズが、変異 M4/M5/M6/M11/M12 は受理集合でなく診断だけを変えるので kill と混同すべきでない
  ことを指摘した。本 README の別枠はその裁定の反映である。

一次資料は `verbatim/`。
