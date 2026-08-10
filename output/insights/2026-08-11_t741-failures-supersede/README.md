# [T-741] failures fragment の supersede 追記 — 逐語と変異台帳

wave: `dev-wave-t741-failures-supersede` / 実装 + docs commit `0c1e115a`、
lease merge `dbae4a66` (作り直し前は `a59b6bdb`、tree 一致)、記録 `42195ee2`、
fold `466ce353`。経緯と裁定の正本は同日の worklog エントリ、文法の正本は
`docs/spool/failures/README.md`、fold 契約は `docs/spool/README.md`。

## この wave が何を変えたか

既存 F エントリの記述が後続の事実で古くなったことを、再発として誤記録せずに書ける文法を足した。

- fragment の H2 に `supersede 追記` を追加 (`新規` → `再発` → `supersede 追記` の任意部分列)
- item は `- F<n> **supersede: YYYY-MM-DD** — <本文>` の 1 物理行
- fold は対象 F エントリの**最後の非空行の直後**へ、行頭 `- ` を自分で付けて挿入する
- 描画後の F 見出し列を postcondition (`failure-topology`) で検査する
- `再発` 節に `- **supersede:` 相当の行を置くと拒否する (正規化投影で判定)

## 敵対レビューが暴いたもの (逐語は `verbatim/`)

| 出所 | 内容 | 帰結 |
|---|---|---|
| `s3-lens-a.md` 所見 1 | 本文をそのまま挿入する案では `### F203. ...` と書いて**偽の F 見出しを作れる** | 行頭 `- ` を fold が付ける + topology postcondition の 2 段構え |
| `s3-lens-b.md` 所見 1・2 | 「表現できない」は誤りで、`再発` payload が任意文字列なので**書けるが再発として誤記録される**。新節を足しても `再発` 経由で迂回できる | `再発` 節の排他検査 (`failure-recurrence-supersede-misuse`) |
| 親の probe | 挿入行の前に空行が 2 つ入り、次見出し直前の空行が消える (実 canonical の F196 が該当) | 挿入位置を最終非空行の直後へ変更 |
| `s6-review-a.md` 所見 1 | topology の expected 順が新規 entry の追加順とずれ、**正当な fold を誤って拒否**しうる | expected を追加順から構成し、allocation 多重集合とも照合 |
| `s6-review-a.md` 所見 2・3 | HTML comment 分割で誤用検査を迂回できる / U+2028 が validate を通り fold で消える | 除去投影と LF-only 統一 + 禁止 6 文字 |
| `s6-focus.md` | 先頭空白 1〜3 個・marker 直後 tab・ゼロ幅文字の迂回 | 正規化正規表現 `^ {0,3}-[ \t]+\*\*supersede:` |
| `s6-focus2.md` | HTML 文字参照 (`&#x73;`) による表示等価の偽装 | **親裁定で nit へ降格し裁定へ返した** (裁定 T 番号は worklog 参照) |

## 変異 matrix

`tools/mutation_harness.py`、runner-mode=dispatch、対象コマンドは
`python3 tools/run_tests.py --force-dispatch -q -rf -k "supersede or failure_topology or failure_list_marker"`
に `test_spool_fold.py` / `test_check_docs.py` / `test_dev_wave_land.py` を渡したもの。

| 走 | spec | ledger | 内容 |
|---|---|---|---|
| 1 | `mutation-spec.json` | `mutation-ledger.json` | 事前登録 7 件。M01/M03/M04/M06/M07 が KILLED、M02/M05 は MISMATCH |
| 2 | `mutation-spec-b.json` | `mutation-ledger-b.json` | M02/M05 を観測 node で再登録して再走 → 2/2 KILLED |

MISMATCH 2 件はいずれも変異が殺されており、期待 node が 1 件ずつ不足していたためである
(同じ不正入力を consumer 側テストと CLI 側テストも踏む)。F138 の 3 例目。初回台帳は erratum として保持する。

**挿入位置そのものへの変異は登録していない。** 合成 fixture の `docs/failures.md` は F1 が
最初かつ最後のエントリなので、位置を動かすとほぼ全 byte-exact テストが赤くなり、
harness が要求する期待 node の完全一致を事前に確定できない。位置は実 canonical の 3 境界
(空行なし / 空行 1 行 / EOF) と合成 1 件の byte-exact テスト計 4 本で固定した。

## 実測

- 受入全走: **8275 passed / 20 skipped / 526.68 秒 / rc=0** (tip `a59b6bdb`、tested main `b2411e11`)
- 焦点 3 file: 556 passed / 1 failed (赤は [T-731] の走行範囲依存の偽赤のみ)
- supersede / topology 選択走: 29 passed / rc=0
- `python3 tools/check_docs.py` rc=0、`check_ai_provenance.py` 2290 件・新規違反なし
- 実 canonical への挿入 bytes は、`spool_fold` を使わない独立計算で
  `--dry-run` の after hash (`726563271d9e...`) と一致することを確認した
