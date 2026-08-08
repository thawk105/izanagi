# [T-227] 段 6 review 子の reasoning を `high` に確定し、機械 pin を張った (2026-08-08)

wave = `dev-wave-t181-stage6-high` / branch = `worktree-dev-wave-t181-stage6-high` /
起点 main = `cf90afcc`。親の裁定要約は worklog の該当エントリ。

## 射程 (これを越える引用を禁じる)

本 wave が land したのは **docs 契約と、その書き換わりを止める機械 pin だけ**である。

- 段 6 の子は `DW-O01` の雛形どおり親が `codex exec -c model_reasoning_effort=<値>` を
  組み立てて起動する。`tools/codex_worker_launch.py` は要求値と実効値の一致しか検査せず、
  段から値を導出しない。`.codex/role-adapters/*.json` に段 6 対応 role は無く、
  `orchestrator/codex_roles/` は runtime blocked である。
- したがって **「段 6 の子が実際に `high` で起動する」ことの機械保証は入っていない。**
  それには launcher 結線が別途要る (本 wave の scope 外、次の一手へ起票)。
- pin 対象は `DW-S02`=max / `DW-S03`=max / `DW-S06-A`=high / `DW-S06-C`=high と
  `DW-O16` の effort 不在のみ。**`DW-S05-A` と `DW-S06-B` は pin 対象外**であり、
  「段 6 の全 child を機械 pin した」と書いてはならない。

## 証拠の状態 (これを隠して引用してはならない)

採用根拠は **2026-08-08 のユーザー裁定のみ**である。

- [T-181] の A/B は `aggregate` / `verify` ともに **`experiment_complete=false` /
  `decision=null`**、失敗理由は全 10 run の `snapshot oracle replay mismatch` で**未認証**。
- 同 insight の事前登録により、許される主張は「この 6 run で劣化を観測しなかった」だけであり、
  **非劣性・同等性・採用の証明ではない**。
- [T-181] が測ったのは**焦点再レビュー**の prompt 由来 benchmark だけで、
  **敵対レビュー 2 本は測っていない**。段 6 全体への適用はユーザーによる外挿の裁定である。
- 本裁定は 2026-08-01 の [T-227] 裁定 (値は `max`、下げる判断は [T-181] の 10 run 再走後、
  「他段へ外挿しない」) と [T-184] の再走前提を**明示 supersede する**。
  D207 の一般原則に対する**段 6 限定・人間裁定による例外**であり、一般 precedent にしない。

## 経緯 — 親 brief の前提が段 3 で覆った

親は brief で「段 6 は D207 の pin 対象外だから、これは引き下げでなく初回確定」と置いた。
段 3 レンズ B (B-09) が `docs/archive/worklog-phase3-0801-101.md` の既存ユーザー裁定
[T-227] / [T-184] を発見し、親が一次資料で裏を取って **real と裁定**した。
実体は「裁定済み `max` を、その裁定が課した条件 (10 run 再走) を満たさないまま反転する」変更
だったため、`DW-S04` に従い親は採否を決めず、選択肢 α / β / γ を付けてユーザーへ返した。
ユーザーが **β (high を採用)** と **既存欠陥 2 件も本 wave で直す**を選んだ。

**docs/decisions.md に無く archive worklog にしか無い裁定を、brief 前の検索が取りこぼした。**
これは memory の `check-withdrawal-rulings-before-wave` と同型の独立 2 例目である。

## 段 3 が止めた段 2 プランの欠陥 2 件

段 2 は workers.md の 2 行置換で +2 bytes に収める案を出した。機械面 (byte 会計、pin 挙動) は
親の独立再測と完全一致したが、意味論に 2 件の欠陥があり**採用しなかった**。

1. **受理集合の拡大。** 置換後 A から条件節「実装 wave は」が消え、`DW-C00` の
   「docs-only は子ゼロでよい」と衝突する無条件形になっていた。
2. **stale 主張の誤り。** 削除対象「焦点再レビューは全体へ 1 本でよい」の「1 本」は
   *1 巡あたりの reviewer 本数* の許可である。導入 commit `7deb54ef` の逐語
   「焦点再レビューは全体へ 1 本行えばよい。**fix 単位ごとの個別レビューは不要とする。**」が原義で、
   後半が byte 圧で削られた結果いまの曖昧形になった。F146 が stale としたのは *巡回数* と
   *対応表の担い手* である。削れば単一 reviewer の許可が消え、子とトークンが増える
   — 本 wave の動機と逆向き。

byte は `operations.md` 導入 2 文の縮約 (−67) で捻出した。**予算値は 1 byte も上げていない。**
aggregate は 25,185 → 25,169 / 25,200 (headroom 31)。

## 恒真ゲートが 3 巡出た — 本 wave の中心的な学び

「契約の書き換わりを止める pin」を作るのに、**文字列の存在を数えるだけでは 3 回とも恒真だった**。
いずれも段 6 レビュー / 焦点再レビューが production 経路の probe で `findings=[]` を実測して見つけた。

| 巡 | 実装 | 迂回 |
|---|---|---|
| 1 | `count(literal) == 1` | 規範文を消して `参考リンク: [例: \`reasoning=high\`](...)` にすれば通る |
| 2 | 規範文全文の `count(sentence) == 1` | 規範文を `> ...` (blockquote) や `参考（旧規範）: ...` に移せば通る |
| 3 | `splitlines().count(sentence) == 1` | `参考（旧規範）:<U+2028><規範文>` で通る (`splitlines()` は U+2028/U+2029/VT/FF/NEL も行境界にする) |

最終形は **CRLF を LF へ正規化して `"\n"` だけで分割し、規範文と完全一致する行がちょうど 1 行**。
値列検査 (`values != [expected]`) は相補層として残す — 前者は規範文の消失を、
後者は節内の別値混入を捕まえる。

## 同時に塞いだ既存欠陥 (本 wave の pin とは独立に成立していた)

- **節ごと不可視化。** `_reference_id_sections()` が raw text を走査するため、H2 見出しから本文まで
  fence / HTML comment / **raw HTML block** へ入れると reasoning pin と必須 H2 inventory の
  両方を通せた。`<x>\n` の 4 bytes で足りる。raw HTML も除去する
  `_visible_dispatch_inventory_text()` へ両側を揃えた。**片側だけでは他方が mask になる。**
- **曖昧値。** `` `reasoning=high/max` `` `` `reasoning=high.max` `` `` `reasoning=high"` `` が
  すべて `high` として通っていた。終端を明示 allowlist にした。
- **`DW-O16` の矛盾 effort。** 焦点再レビュー節に `reasoning=max` を足せて `DW-S06-C` と
  矛盾する契約が land できた。O16 節に effort 値が無いことを pin した
  (`DW-O01` の `model_reasoning_effort="<効いた値>"` は正当な起動雛形なので**対象外**)。
- **URL / path の過剰拒否。** `https://…/?reasoning=X` を effort 値として拾っていた。

## 変異 (`mutations/`)

事前登録は `prereg-v2.md`。**v1 (`prereg-v1-erratum.md`) は消さず erratum として残す** —
段 6 レビューが実装後のコードを読んで M4 / M5 / M6 の kill 意味論が成立しないと判定したため、
`DW-M03` / `DW-M04` に従って再照准した。

harness の `KILLED` は失敗 node 集合の**厳密一致**を要求する。素朴に全走すると 1 変異が
S02/S03 の既存テストまで巻き込んで集合がずれ帰属が曖昧になるため、**変異ごとに受領 node へ
走行範囲を絞って** 10 group に分け、単一理由の receipt を取った。全 baseline rc=0。

**15/15 が事前登録と一致。** ただし `DW-M08` に従い 3 つに分けて記録する。

| 区分 | 件数 | 内容 |
|---|---:|---|
| **受理集合を変える kill** | **12** | M1 (A pin 削除) / M2 (C pin 削除) / M3 (exact-list→membership) / M7 (可視化を両層 raw へ) / M8 (production 呼出し削除) / M9 (規範文 pin 削除) / M10 (規範文 pin + 終端 allowlist の両層) / M11 (可視化を両層 markdown-only へ) / M12 (O16 pin 削除) / M13 (独立行→substring) / M14 (LF 分割→`splitlines()`) / M15 (前方境界の復元) |
| **diagnostic sensitivity pin** | 2 | M4 / M5 — 可視化を片側だけ戻す。node は赤くなるが**他層が拒否を継続する**ため受理集合は変わらない。親が production 経路で実測 (fence 隠蔽ケースの S06 finding が 2 → 1 に減るだけ。0 になるのは両層同時の M7 のみ。raw HTML ケースで 0 になるのは M11 のみ) |
| **SURVIVED (事前登録どおり)** | 1 | M6 — 終端 allowlist だけ戻しても規範文 pin に mask され受理集合が変わらない。**「隠れるはず」と事前登録したとおりの結果**で、レビューの帰属分析の裏取りになる |

事前登録から外した候補: 段 2 案の変異 #7 (重複節の先頭だけ受理) は global H2 uniqueness が
独立に拒否し続けるため実効受理集合が変わらない。`DW-M03` に従い冗長 gate として除外した。

## 検査

- 受入全走 (**land 対象 tip = main merge 後**) **7393 passed / 20 skipped**
  (1189.88s、計算ノード dispatch、追加 flag なしの受入形)。
  fix 3 巡目の実装 commit 時点でも 1 度実施しており **7376 passed / 20 skipped** (1224.27s)。
  件数差は取り込んだ並行 wave のテスト追加分である。land 対象は前者。
- 焦点 `orchestrator/tests/test_check_docs.py`: 297 → **328 passed** (純増 31)
- `python3 tools/check_docs.py` rc=0、`python3 tools/check_ai_provenance.py` 新規違反なし
- 変異 15/15 が期待一致 (内訳は上表)

## 工程の差異 (裁定手順と実行手順、`DW-O12`)

- 段 4 は「停止条件に local main の SHA 比較を足す」と設計したが、**機械 gate としては実装せず**、
  親が投入前後に手で `git log --oneline -1 main` を確認する運用で代替した。
  結果として stale は踏まなかった (`b97ad3b5` の親は当時の main `cf90afcc`) が、
  設計どおりではない。次の一手へ起票する。
- 段 6 fix 3 巡目は、親が prompt に書いた期待値「CR-only 文書も通る」が誤りだったため、
  実装子が実測 (CR 全文で 12 findings) で食い違いを見つけ、**実装せず停止して報告した**
  (`verbatim/s6-fix3-halted.md`)。`DW-S06-B` の「期待値が誤りと判断したら実装を変えず報告して
  止める」が正しく発火した例である。親が期待値を訂正して同じ巡を投げ直した
  (`verbatim/s6-fix3.md`)。新規所見への対応ではないため `DW-O16` の巡回数には数えない。

## 裁定パッケージ (scope 外の real 所見)

1. **規範文 pin による文面凍結の代償。** 意味を変えない語順・助詞・空白の修正でも docs 単独では
   できず、docs + checker + test + 採用裁定を要求する。drift を強く止める意図した強度だが、
   正当な文面改善まで実装面変更へ昇格させる。
2. **実起動値の機械保証 (B-01)。** 上記「射程」のとおり docs pin は実起動を拘束しない。
   launcher 結線は [T-576] / [T-184] の所有。
3. **`DW-S05-A` / `DW-S06-B` の無 pin (B-06)。** 段 5 の high は pin されておらず、
   S06-B は意味的継承のみ。将来の drift を台帳が見逃す。
4. **CR-only 文書を共有節抽出が扱えない。** `_reference_id_sections()` と H2 inventory が
   LF を要求するため CR-only は 12 findings になる。本 wave では変更していない。

## 逐語の可逆最小正規化 (erratum、`DW-S07`)

codex の出力は markdown の hard line break として**行末に空白 2 個**を置く。`git diff --check` へ
抵触するため、**行末の空白のみ**を除去した。**可視文字は 1 文字も変えていない。**
復元法: 下表の各行について、除去行数分の行末へ空白 2 個を戻すと原文 sha256 に一致する
(原文は wave branch の job artifact `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t181-stage6-high/`
にも同一 bytes で残っている)。

| ファイル | 原文 sha256 | 原文 bytes | 正規化後 sha256 | 後 bytes | 除去行数 |
|---|---|---:|---|---:|---:|
| `s3-lensA.md` | `f2c22e96fc01eb1935125bb9657f37ace5ce211d8fe4e7d1dd85cfa6f7cd7742` | 14596 | `aa5155801949cdeb712d8d6f2f7e1e358752925ed3cf0cba25629db8f89b2b2f` | 14590 | 3 |
| `s6-fix1.md` | `e3b096a9a5a9a1d370cd413c34d8987eb8d8352c80bfab8b23f8f8ddd8be3990` | 3949 | `09636d74a48aac19ae71f102052f9b4d2b9872930abdcbe831f01b70da71916c` | 3941 | 4 |
| `s6-fix2.md` | `7a7a544549bdacceeb0b9cc9f02b04c86d723c2b6797231e8a6cf4a4e9f2d61c` | 4566 | `2211946e6d5fd6ff6398e63c46b96d304fe650ddb8c94071e41fdc2e3e5651e0` | 4558 | 4 |
| `s6-lensC.md` | `2d3ce3023f0560d557152af0a13592ecddacad331be6679f2aea3bb42f0a619f` | 6834 | `db7c105a244915836bde1b4ecc6cf0eeda87f9faa215da24f466b61206dd998d` | 6826 | 4 |
| `s6-refocus1.md` | `a2f7f69b7b5b672551b5237f15f8dec62d334ab15c9353f8ae9683b5f5eb8847` | 13917 | `ec4db6b82619741e845fb678e88477afad799b7c039f4680fdce4a3721bf1de9` | 13903 | 7 |
| `s6-refocus2.md` | `f964dd7735186da1d27357f2498388cc43475018d64f41ca753d5ce96fe955aa` | 16620 | `f1c00d0852a0e483773c236f43445d3da4490420eaa24fb2de98624010e23f84` | 16606 | 7 |

他の逐語ファイルは無変更である。

## 凍結ファイル

| ファイル | 役 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief (親) |
| `verbatim/s2-plan.md` | 段 2 Codex プラン (**不採用**。欠陥 2 件は本文参照) |
| `verbatim/s3-lensA.md` / `s3-lensB.md` | 段 3 敵対相談 (意味保存と受理集合 / gate の実効性と全層) |
| `verbatim/s4-ruling-package.md` | 段 4 裁定 + ユーザーへ返した選択肢 α/β/γ |
| `verbatim/s5-impl.md` | 段 5 実装子の報告 |
| `verbatim/s6-lensC.md` / `s6-lensD.md` | 段 6 敵対レビュー (両者 NO-GO) |
| `verbatim/s6-fix1.md` 〜 `s6-fix3.md` | 段 6 fix 3 巡 (`s6-fix3-halted.md` は親の期待値誤りで停止した回) |
| `verbatim/s6-refocus1.md` / `s6-refocus2.md` | 焦点再レビュー 2 巡 (2 巡目で `regressed=0`) |
| `mutations/prereg-v1-erratum.md` / `prereg-v2.md` | 変異事前登録 (v1 は erratum として保存) |
| `mutations/spec-*.json` / `ledger-*.json` | 変異 spec と台帳 (group A〜J) |
