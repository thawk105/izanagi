# 段 4 裁定 (差分) — 取り残し成果の回収 + 裁定 #1 / #9 / #10

2026-08-13 08:40 JST 実測。base `168145e7` (local main `a3168d85` + 取り残し tip `44b4a9ba`)。

前 wave の段 4 裁定 (`../2026-08-13_t907-t908-t910-acceptance-integrity/s4-adjudication.md`) は
**そのまま有効**とする。変更面の骨格 (受入 receipt・走行後 fingerprint・untracked 検査) は同一で、
merge 結果の実装 blob は取り残し側と bytes 一致した。本書はその上に載る**差分だけ**を裁く。

## 0. 適用する新裁定と、その読み

`rulings-inbox/2026-08-13-rulings9-29rulings.md` の 3 件。選択肢集合で元パッケージと照合済み。

- **#1** (元 = `2026-08-13-acceptance-receipt-vs-known-red.md` の (a)/(b)/(c))。
  確定は **「(b) の変形 = checker 統合」**。批准既知赤 registry は作らない。
  receipt 発行条件を「rc=0 **または** 非帰属 checker 緑」へ拡張する。
  → **(b) の眼目である「赤の nodeid を receipt と land 結果に明記して緑を偽装させない」は、
  registry ではなく checker 判定の記録として引き継ぐ。**
- **#9** [T-1019]。waiter の receipt へ **log hash 束縛**。
  「checker 自身が受入走を所有する」案は**採らない**と明記されている。
- **#10** [T-1020]。新規機構は作らず、#1 裁定後に**本 wave の land で閉じる**。
  → land 側に足すのは #1 が要求する照合だけ。独立の receipt 機構を新設しない。

## 1. 親が段 4 で摘出した新事実 (実装前・コード実測)

`tools/check_acceptance_reds.py:919-925` の判定は次である。

```
if not nodeids:        rc, status = 0, "green"
elif attributable:     rc, status = 1, "attributable-red"
else:                  rc, status = 0, "non-attributable-only"
```

**`rc == 0` は 2 つの意味を持つ。** うち `status == "green"` は「log から赤 nodeid を 1 件も
取り出せなかった」であって「赤が非帰属だった」ではない。受入 command が非 0 で終わったのに
赤 nodeid が 0 件になる経路は実在する — collection error、internal error、crash、
`-p no:...` 事故、xdist worker の異常終了。

したがって **「rc=0 なら緑」と実装すると、落ちた受入が receipt を得る fail-open になる。**
これは本 wave の主題 (規律 2 = 正しさゲートを緩める変異を許さない) の直撃であり、
裁定 #1 の文言「非帰属 checker 緑」を機械語へ落とすときの唯一の分岐点である。

**裁定: 非 0 child のとき受理するのは `checker_rc == 0` かつ
`checker_status == "non-attributable-only"` のときだけ。**
`status == "green"` は判定不能として fail-closed。`rc == 1` (帰属赤) も `rc == 2` (判定不能) も
fail-closed (`DW-O18` の「rc=2 は非帰属の根拠にしない」と同じ向きで、rc=0/green へ拡張した)。

## 2. プラン v2 差分 (確定した実装内容)

### Δ1 — waiter が受入 log を所有する (裁定 #9 / [T-1019])

1. acceptance parser へ**必須** `--log-file PATH`。環境変数 fallback は作らない。
   preflight は `--receipt-file` と同形 — repo 外・親 directory 実在・target 未存在を claim 前に
   検査し、違反は `acceptance-log-preflight` / rc 2。
2. 受入 child の stdout / stderr は**待ち手自身が**この path へ捕獲する
   (親が渡した既存 log を受け取らない。これが [T-1019] の穴「任意の過去 log を渡せる」を閉じる)。
3. child 終了後に log bytes を読んで `log_sha256` を算出する。

### Δ2 — 非 0 child の非帰属判定 (裁定 #1)

4. `child_rc != 0` かつ走行後検査 (postrun-clean / index-flags / fingerprint) が**すべて通った**
   ときだけ、待ち手が `tools/check_acceptance_reds.py` を起動する。
   走行後検査の赤は従来どおり child rc に優先し、checker は起動しない。
5. 起動 argv は `[sys.executable, <repo>/tools/check_acceptance_reds.py, --log <捕獲 log>,
   --tested-main <main sha>, --wave-tip <tested tip>, --receipt <checker receipt path>,
   --probe-root <repo 外の probe root>]`。
   checker receipt と probe root も repo 外で、`--receipt-file` と同じ preflight 形にする。
6. 受理は **`checker_rc == 0` かつ `checker_status == "non-attributable-only"`** のときだけ (§1)。
7. checker の receipt を読み、次を**すべて**照合してから受理する。
   `log_sha256` が待ち手の算出値と一致 / `wave_tip == tested_tip` /
   `tested_main == 待ち手が観測した main sha` / `schema_version` が既知値 /
   `nodes` が全件 `classification == "non-attributable"`。
   1 つでも外れたら fail-closed (`acceptance-red-check`)。
8. `checker_blob_sha` = `git rev-parse <tested_tip>:tools/check_acceptance_reds.py` を receipt へ入れる
   (`waiter_blob_sha` と同じ束縛を checker にも張る)。

### Δ3 — receipt schema を v2 へ

9. `dev-wave-acceptance-receipt/**v2**`。field 集合は exact 一致で検査されるため版を上げる。
   追加 field: `tested_main` / `verdict` / `log_sha256` / `checker_rc` / `checker_status` /
   `checker_blob_sha` / `checker_receipt_sha256` / `red_nodeids`。
   `child_rc` は**実値**を書く (従来は常に 0 を焼き込んでいた)。
10. `verdict` は `"child-green"` か `"non-attributable-only"` の 2 値。
    `child-green` のとき checker 系 5 field は `null`、`red_nodeids` は `[]`。
    `non-attributable-only` のとき `child_rc != 0`、checker 系は全て非 null、
    `red_nodeids` は 1 件以上の文字列 list (sort 済み)。

### Δ4 — land 側の照合 (裁定 #10)

11. `_verify_acceptance_receipt` を v2 へ。`verdict` で分岐し、上記 §Δ3-10 の整合を全項目照合する。
    `checker_blob_sha` は land が `<tested_tip>:tools/check_acceptance_reds.py` を自分で解決して比較する
    (`waiter_blob_sha` と同じ経路)。`tested_main` は land が受け取っている tested main と一致必須。
12. `LandResult.as_json()` へ `acceptance_verdict` と `acceptance_red_nodeids` を追加する。
    **これが裁定 (b) の「赤の nodeid を台帳に残す」を registry 無しで満たす部分である。**
13. **bypass flag・環境変数・警告化の逃がし道を作らない。** 既存 rc は変えない
    (不正は `RC_AUDIT = 23`、stage `acceptance-receipt-rejected`)。

## 3. scope 外 (実装しない・裁定パッケージへも新規に起票しない)

- 前 wave が scope 外にした A2 完全形 / A6 / A10+B10 / B4 / B7 land gate / B11 は**そのまま scope 外**。
- 批准既知赤 registry (元 (b) の原形) は裁定により**作らない**。
- checker 自身が受入走を所有する形 ([T-1019] の対立案) は裁定により**採らない**。
- log の durable 保存 (land 後も log bytes を残す) は作らない。receipt が持つのは hash だけで、
  「log 本体は wave job dir にしか無い」ことを worklog に明記する。

## 4. 変異事前登録 (DW-M01 / DW-M07)

前 wave の M1〜M10 は実装が変わるため anchor と期待 node を fix 後に再導出して**再走**する
(`expected-nodes-rederived-after-fix-commit`)。本差分の実効 gate へ次を**追加**登録する。

| # | 実効 gate | 最小変異 | 期待 KILLED (完全集合は fix 後に再導出) | 層 |
|---|---|---|---|---|
| N1 | 非 0 child で `status=="green"` を拒否 | 受理条件から `status` 検査を外し `rc==0` だけにする | 赤 0 件 log + 非 0 child の拒否 test | negative |
| N2 | checker rc=1 / rc=2 の fail-closed | `rc != 0` でも受理する | 帰属赤 / 判定不能の拒否 test | negative |
| N3 | log hash 束縛 | checker receipt の `log_sha256` 照合を外す | log 差し替え検出 test | negative |
| N4 | waiter による log 所有 | 既存 log path を受理する (preflight の target 未存在検査を外す) | 既存 log 拒否 test | negative |
| N5 | land の `checker_blob_sha` 照合 | 照合を外す | tampered receipt test | negative |
| N6 | land の verdict 整合 | `child-green` で `child_rc != 0` を許す | tampered receipt test | negative |
| N7 | 走行後検査の優先 | 非 0 child のとき postrun 検査より先に checker を回す | 走行後汚染 + 非帰属赤の拒否 test | negative |
| P2 | 正常系 (非帰属経路) | 変異なし | 実 waiter → 実 checker → 実 land の end-to-end 成功 | positive |

各変異は登録前に「同じ入力を拒否する層が前後に無いこと」をコードで確認する (F28)。
`postrun-clean` は前 wave と同じく**冗長な診断 gate**として単独変異の証拠から外す (DW-M03)。

## 5. [T-1027] 依存の扱い

裁定 #1 は「[T-1027] の修正を先行させる」と書く。08:11 JST 時点で main に修正は無く、
peer session `p1 bug pytest nodeid mismatch` が着手直後だった。

- **実装は依存しない** — checker の起動と照合は本 wave で完結する。
- **緑側の実データ検証だけが依存する。** 本 wave の受入全走が rc=0 で終われば
  `child-green` 経路しか実走せず、`non-attributable-only` 経路は実 checker を
  合成 log へ当てる試験でしか通らない。その差は worklog に**限界として明記**し、
  「実データで 1 回通した」と書かない ([T-1028] の趣旨)。
- 受入全走が非 0 で終わったときは [T-1027] の land を取り込んでから再走する。
  取り込めない場合は fail-closed で停止し、land しない。

## 5b. 段 6 レビュー後の erratum (2026-08-13 08:58 JST、親が訂正)

敵対レビュー B の指摘により、本書の次の 2 箇所を訂正する。**訂正前の文は誤りである。**

1. **§5 の「実装は依存しない」は言い過ぎだった。** 正しくは
   **「argv の配線と照合ロジックだけが [T-1027] から独立で、実効 gate は依存する」**。
   [T-1027] が直るまで、実受入で赤が 1 件でも出た wave は checker rc=2 で receipt を得られず、
   裁定 #1 が解こうとした「既知赤が fleet 全体の land を止める」構造がそのまま残る。
   ただし**これは land 前より悪化はしない** (今日も赤は land を止めている)。
   ユーザー指示どおり [T-1027] の land を取り込んでから緑側を検証する。
2. **§Δ4-12 の「赤の nodeid を台帳に残す」も言い過ぎだった。** 正しくは
   **「land 結果 JSON (`LandResult.as_json()`) に残す」**。canonical worklog / spool への
   永続化は本 wave では作らない。job directory の JSON を失うと canonical 台帳だけからは
   非帰属受理の対象 nodeid を再構成できない。この限界は worklog に明記する。

あわせて、レビュー A の blocker を受けて **§Δ2-6 の受理条件を狭める**。
`child_rc != 0` ではなく **`child_rc == 1` ちょうど**を要求する。
根拠は実測 — `tools/run_tests.py` の main は `return subprocess.call(cmd, cwd=_REPO)` で
pytest の rc をそのまま返し、テストが落ちた走行は 1 を返す (2026-08-13 08:48 JST の焦点走で
4 failed の走行が rc=1 を返した)。`run_tests.py` 自身の失敗は
`_DELETION_GATE_RC = 13` / `_PEGASUS_DISPATCH_RC = 16` など 1 以外である。
**赤の非帰属は「走行が崩れたこと」を説明しない。**

## 6. 成果物影響 (DW-G05)

- Δ1〜Δ2 を実装しない: 既知赤が 1 件でもある間、fleet の全 wave が land 不能になる
  (前 wave が実測した停止がそのまま残る)。
- §1 の分岐 (`status=="green"` 拒否) を実装しない: **落ちた受入が受領証を得る。**
  受理集合が「緑の走行」から「緑または崩れた走行」へ広がり、台帳の受入結果が意味を失う。
- Δ4 を実装しない: [T-1020] が閉じず、land は受入結果を検証しないままになる。
