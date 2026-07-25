# [T-094] リテラル placeholder の機械検出 — 材料レポート (2026-07-25)

- 対象: `docs/failures.md` の F36 恒久対応 2 の実体化 ([T-094])
- branch: `worktree-dev-wave-t094-placeholder-gate`、基準 = `1d2d298`、統合 commit = `8ba4aed`
- 成果物: `tools/check_docs.py` (+621 行)、`orchestrator/tests/test_check_docs.py` (+1372 行)
- 逐語 = 同 `-verbatim.md`、変異台帳 = 同 `-mutation-ledger.json`
- **表記規約**: 検出対象の 3 バイト列そのものは本文へ再掲しない。以下では
  `tools/check_docs.py` の `LITERAL_PLACEHOLDERS` の要素を宣言順に **LP-1 / LP-2 / LP-3** と呼ぶ。
  この規約は本 gate の自己発火を避けるための実務でもある (§4-1)。

## 1. 何を作ったか

対象 3 族 (`docs/worklog.md`、`docs/archive/worklog-*.md`、`output/insights/*.md`) の **raw text** を
走査し、LP-1〜LP-3 の出現を拒否する exact-literal gate を `check_docs.py` に追加した。
既知の 9 行は 2 つの台帳で固定した。

| 台帳 | 意味 | 件数 | 束縛 |
|---|---|---|---|
| `KNOWN_PLACEHOLDER_DEBTS` | 埋め戻し失敗の歴史的債務 (F36 が retroactive な修正を禁じる) | 4 | worklog 族 = 直前 H2 見出し行の digest / insights = path |
| `KNOWN_PLACEHOLDER_MENTIONS` | placeholder について語っている説明行 (債務ではない) | 5 | 同上 |

台帳の key は `(scope, 行 digest)` で、行番号は持たない。digest は「改行終端だけを除いた論理行の
UTF-8 bytes」の SHA-256 で、strip・Unicode 正規化をしない。論理行の分割は CRLF / LF / CR だけに
限定する。総 occurrence 数 (4 / 5) を独立定数で pin し、台帳を黙って増補できないようにした。

## 2. 敵対レビューが否定した親の裁定 (段 3 で 4 件、段 6 で 1 件)

段 3 の両レンズ、段 6 の両レビュー、焦点再レビュー 2 本の **すべてが NO-GO** を返した。
親の provisional 裁定のうち次が否定された。

| 裁定 | 親の当初案 | 否定の理由 | 確定 |
|---|---|---|---|
| P2 / P4 | inline code と code fence 内を除外して偽陽性を消す | 記録者が装飾を 1 つ付けるだけで結果欄を不可視化できる **gate bypass**。規律 2 に反する受理集合拡大 | 除外機構を**全廃**し raw text を検査 |
| P3 | allowlist を path 非依存の行 digest multiset で持つ | 旧行を消して同じ bytes を新レコードへ置けば総数不変で緑 = **例外権の譲渡** | scope 束縛 (下記) |
| N-5 | 本 wave の記録は LP を「必ず含む」ので除外機構が必要 | 記号参照や HTML entity で書ける。**自己言及を理由に gate を緩める必要はない** | 記号参照で記録 |
| P6 | D 起票は不要 (既裁定の lint 追加) | 対象族・台帳の閉性・凍結 waiver は長期の受理集合設計 | **D88 を起票** |
| verbatim 除外 | `-verbatim.md` suffix のファイルを除外 | 誰でも作れる**全ファイル除外スイッチ**。実在 106 Markdown のうち 47 件以上が逐語または逐語混合で suffix 分類と一致しない | `output/insights/*.md` を**全件**対象に |

段 6 では親の「path 束縛」も **regressed** と判定された: `(path, digest)` では同一ファイル内で
旧 H2 から消して新 H2 へ移す replay を遮断できない。これを受けて key を H2 エントリ scope へ変更し、
副産物として**正規のローテーション (H2 エントリごと archive へ移動) では台帳を変更しなくてよい**
性質を得た。さらに焦点再レビュー round 2 が、H2 判定が既存 parser (`WORKLOG_H2_RE`) と食い違い
**タブ区切り H2 を見落とす**ことを検出したため、判定を既存定数へ統一し、H2 raw bytes の
一意性検査を追加した。

## 3. 併せて直した既存欠陥 (レビューが検出、本 wave の scope 内と裁定)

1. **読取失敗が集約報告に到達しない**: 新 checker が読取失敗を finding 化しても、後続の既存
   checker が同じファイルを無防備に `read_text()` して例外を送出し、header・件数・先の finding が
   traceback に置き換わっていた。読取不能を「不明」として扱い、依存する検査だけを停止する
   共通 safe-reader を導入した。
   - 停止範囲は worklog 族と insights 族で分離した (無関係な insights が読めないだけで
     worklog 内の台帳不一致が隠れることを防ぐ)。
   - 構造抽出の失敗 (見送り台帳、archive entry) も「不明」として扱い、非隣接 archive の比較や
     空集合扱いによる偽 finding の派生を止めた。
2. **symlink / 非 regular file の追跡**: safe-reader が final component だけでなく repo 内の親
   component も検査し、symlink を含む path と非 regular file を開かないようにした
   (`docs/archive` が symlink のとき `README.md` 自体は symlink でないため見落とす経路があった)。
   command / reference の読取経路も同じ safe-reader を通した。

## 4. 射程と限界 (正直な記述)

### 4-1 この gate が防ぐもの

対象 3 族の raw text における LP-1〜LP-3 の **exact な出現**だけである。inline code の中でも
code fence の中でも `-verbatim.md` という名前のファイルでも検出する。

### 4-2 この gate が防がないもの (受容した偽陰性)

- **意味的に同じ別表記**: 「結果を反映」等の類似表現、HTML entity 表記、全角括弧などは検出しない。
  検出語彙の一般化 (正規表現化) は裁定で却下済みであり、拡張は [T-100] の裁定対象。
- **未実測の予測値の先書き** (F36 の再発型、worklog 2026-07-25 (4)): 空欄ではなく具体値を
  実測前に書く形は、literal 検出では**原理的に検出できない**。F36 の再発クラスはこの gate では閉じない。
- **対象 3 族の外**: `docs/phase3.md`、`docs/decisions.md`、`docs/failures.md`、`docs/handoff/`、
  `output/insights/*.json` (変異台帳を含む)、campaign の JSON producer は対象外。
  とくに `*-mutation-ledger.json` は実際に受入結果を記録しており、同型欠陥が残る ([T-097])。
  campaign の selector は `rationale` を非空文字列としか検証しないため、sentinel を freeze へ
  seal できる ([T-098])。
- **既知債務 4 行は解消されていない**。台帳に登録して固定しただけである (retroactive な埋め戻しは
  F36 が禁じる)。`check_docs` の「違反なし」は「未許可 hit がない」の意味であり、
  「placeholder が存在しない」の意味ではない。

### 4-3 凍結成果物との二重拘束 (未設計、[T-099])

`FROZEN_MANIFEST` は insights 5 件の bytes を pin している (うち 3 件は `-consultations.md` 形式の
逐語)。将来そこに正当な引用 hit が入ると、(a) bytes 修正は freeze 違反、(b) 実測値を埋めるのは
F36 の捏造、(c) 一般台帳へ足すのは gate 弱体化 — の三択になる。専用 waiver
(`path + frozen file SHA-256 + decision ref + erratum ref` 束縛) の設計は裁定パッケージへ送る。

## 5. 変異 matrix (13 変異、統合 commit `8ba4aed` に対して本走)

**13/13 KILLED / expected node hit 12/13**。post_restore は内容比較で一致、pytest rc=0。

単独理由の検出力の証拠として使えるのは、落ちた node 数が 12 以下の 9 変異
(M2/M3/M6/M7/M9/M10/M11/M12/M13) である。M1/M4/M5/M8 は台帳照合が同時に赤くなり
68〜71 node が落ちる**過剰決定**であり、DW-M03 に従って単独理由の証拠から外した。

| ID | 変異 | 落ちた node 数 | 期待 node |
|---|---|---:|---|
| M2 | LP-2 を検出語彙から削除 | 3 | HIT |
| M3 | `main()` の checker 呼び出しを空集合へ置換 | 9 | HIT |
| M6 | archive 族の glob を既知命名へ縮退 | 5 | HIT |
| M7 | insights 族の glob を既知命名へ縮退 | 6 | HIT |
| M9 | VT でも論理行を分割する (bug の復活) | 1 | HIT |
| M10 | 未許可 hit の finding を no-op 化 | 12 | HIT |
| M11 | member と safe-reader の symlink 拒否を同時に外す (2 点累積) | 3 | HIT |
| M12 | 観測数の超過側を検査しない | 2 | HIT |
| M13 | H2 判定をタブ非対応へ退行させる | 1 | HIT |

erratum 3 件を台帳に同梱した (初回走行の node 照合バグ、M4 の期待 node 登録誤り、過剰決定の明示)。
M4 は期待 node が MISS だったが、`check_docs` が実 repo で総数不一致を検出しており (rc=1)、
受理集合は変わる。テストが総数 pin を node 粒度で固定していない点は **nit** とした
(production が検出するため成果物影響がない)。

## 6. 検査

| 検査 | 結果 |
|---|---|
| 受入全走 (統合 commit 直前) | 2994 passed / 18 skipped / 赤 0 (rc=0、264 秒) |
| 焦点 `test_check_docs.py` | 113 passed (rc=0) |
| `python3 tools/check_docs.py` 単独 | rc=0、違反なし |
| 波及先 consumer (dev_waves 系 + run_tests) | 177 passed |
| `check_ai_provenance` | 346 件、違反なし |
| 変異 matrix | 13/13 KILLED、post_restore 一致 |

親が独立に実測して子の報告と照合した事実: 対象族 115 ファイルの hit = 9 logical lines で digest
9/9 一致、worklog 族の H2 = 234 件すべて一意、repo 内 symlink 0 件、CR byte 0 件。

## 7. 裁定パッケージ (本 wave では実装しない)

| ID | 内容 | 根拠 |
|---|---|---|
| [T-097] | 対象族の拡張 — `docs/phase3.md` / `decisions.md` / `failures.md` / `*-mutation-ledger.json` / handoff。claim-bearing artifact 族の定義が必要 | 段 3 レンズ B 所見 1、段 6 レビュー A 所見 8 |
| [T-098] | campaign の `rationale` sentinel 拒否 (`s8b_selector_output.py` の producer validator) | 段 3 レンズ B 所見 6 |
| [T-099] | 凍結成果物に将来 placeholder が入った場合の専用 waiver 契約 | 段 3 レンズ B 所見 5、段 6 レビュー B 所見 4 |
| [T-100] | 検出語彙の拡張 (別表記・HTML entity) と、予測値先書きの構造的検出 (実走 artifact 参照の必須化) | 段 6 レビュー A 所見 9、レビュー B 所見 5 |

## 8. 逐語の defang (F36 と本 gate の衝突を回避する実務)

子出力 13 本には LP-1〜LP-3 が合計 27 箇所あり、そのまま凍結すると本 gate が自己発火する。
**全角山括弧への 1:1 可逆置換**を施し、置換後に 0 hit であることを機械検査した。
原文 SHA-256 と byte 数は逐語ファイルの冒頭 manifest に併記した。
(焦点再レビューは Base64 全文変換を推奨したが、逐語の実用価値 — 人が読み grep できること — を
壊すため採らなかった。可逆性と同一性検証は SHA-256 で担保される。)
