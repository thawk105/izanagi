## 判定の範囲

静的レビューです。pytest・変異は実行していません。以下、T＝`test_s8b_oracle_driver.py`、M＝`t080_freeze_migration.py`、R＝`s8b_oracle_report.py`。T の行番号は patch 適用後です。

## must-fix

なし。追加 assert と、S＝{e2e, unit} に対する spec 2 本の期待 node 集合に、訂正が必要な誤りは見つかりませんでした。

## should

**A1 — 実 repo test を除外する理由の「差分が消える」は訂正する。**

- **根拠:** `s4-ruling.md:60–68`。M1/M2 は S でも既に旧新版とも KILLED であり、測る差分は失敗 node 集合への e2e の追加です。実 repo test は T:412–439、3820–3842 で独立期待値と完全一致比較するため、実行されれば M1/M2 に加えて M3 も検出します。
- **放置時の影響:** insight が、集約 status の差と node 集合の差を混同し、実 repo test を除外する必要性を誤って説明します。
- **是正案:** 「S は e2e の追加検出を既存 unit と比較する最小集合」と説明してください。実 repo test を実際に実行した場合の予測は次のとおりです。

| 変異 | 旧版の失敗集合 | 新版の失敗集合 |
|---|---|---|
| M1/M2 | {unit, real} | {unit, real, e2e} |
| M3 | {real} | {real, e2e} |

どちらも e2e が加わる差分は残ります。M3 の **SURVIVED→KILLED という集約 status の差**は消えます。

なお、現行焦点走では real は growth hold により未実行です（`focus1.log:24–30`、`conftest.py:2237–2245`）。単に node を追加するだけで必ず kill される、とは記せません。親の object 不在実測を前提とした、**hold が解除され、比較まで到達した場合の静的予測**としてください。

## nit

なし。

## patch の正しさ

**支持します。**

- 裁定 §3 の assert と T:2058–2075 は逐語一致しました。
- 旧版 `b7f970dfa` との全文比較でも、旧2055行直後への comment 2行＋assert 18行の追加だけでした。
- 既存の件数検査（T:2033）、先頭15件比較（T:2052–2055）、report 比較（T:2100–2101）は保持されています。
- literal SHA 2本は M:49–50 と一致し、test は production 定数を参照していません。
- comment の「同一 source」は、**同じ production 実装を再利用するため独立 oracle ではない**という意味で正確です。report は単なる転記ではなく再導出しますが、R:259–273 は `_classify_ancestry` と `_make_observation` を再利用し、R:311–322 でその結果と比較します。

## 変異 matrix と帰属

旧版 blob と新版現物それぞれについて、各 spec の置換文字列の出現数は **M1/M2/M3 すべて1箇所**でした。harness も `mutation_harness.py:1076–1090` で一意性を要求します。

| 変異 | 旧版の期待 | 新版の期待 | 静的判定 |
|---|---|---|---|
| M1 | KILLED {unit} | KILLED {unit, e2e} | 支持 |
| M2 | KILLED {unit} | KILLED {unit, e2e} | 支持 |
| M3 | SURVIVED {} | KILLED {e2e} | 支持 |

**M1/M2:** unit は `test_t080_freeze_migration.py:1227` で失敗します。report の R:215–222 は `not-ancestor`／`ancestor` と hex observed の組を許し、再導出も同じ変異実装に追随します。

**M3:** R:197–198 は subject に非空文字列だけを要求するため、末尾 `/` の追加を通します。再導出も追随します。unit は `_classify_ancestry` だけを検査し、subject を作る `_make_observation` を呼ばないため通過予測です。

**新 assert より前の失敗経路:** M1/M2 は `AncestryResult.refusal_reason` の既定値 None を変えません（M:143–147）。拒否への追加条件は M:2381–2383、observation 生成と state 決定は M:2426–2434 なので、`resolution.refusals == ()` と `active-valid` は維持されます。fixture 子プロセスの検査（T:1675–1683）も同様です。M3 は item の subject だけを変えます。

したがって、対象3変異について新版 e2e の最初の失敗は **T:2058 の追加 assert** と予測できます。実走時は失敗行も記録し、node 集合だけで帰属を確定しないでください。

**走行形式も成立します。** `run_tests.py:488–500` は `::` を分離してパスを正規化し、node 部分を保持します。`:712–730` の判定は受入全走かどうかの判定であり、nodeid の禁止ではありません。

単独選択でも shared base は module import 時に参加し（T:954–972）、必要時に構築します（T:926–950、991–1013）。real-repo lock は各 item の protocol hook に掛かるため、他 node の先行実行を必要としません（`conftest.py:2285–2303`）。harness は relay prefix と xdist group suffix を処理し、失敗集合を完全一致比較します（`:1230–1268`、`:2129–2144`）。

## 焦点走の評価

**焦点走全体は緑です。** `focus1.log:10,32` に child rc=0、**348 passed・7 skipped・303.24秒**があり、途中終了ではありません。failure/error はありません。

指定4ファイルを走らせたという入力条件とコード上の選択条件を合わせれば、対象 e2e・AST 検査・関連 pin 検査の成功を支持します。ただしログは非 verbose なので、各 node の PASS を個別列挙した証跡ではありません。

7 skip のうち6件はログに列挙された既存 growth hold です。残る1件はこのログだけでは node・理由を確定できません。追加した literal assert には skip を発生させる経路がなく、本 patch への帰属根拠はありません。したがって「4ファイル全 node が実行済み」とは記さないでください。

末尾の `recording-unavailable:series-invalid` は記録側の診断で、pytest の赤を示すものではありません。受入全走の成功とも扱えません。

## hermetic 前提

通常の Git と正常な fixture 構築を前提に、記録 commit が主 object store に入る経路は確認できませんでした。

T:1426 の `git init` 後、素材はファイル内容としてコピーされます。T:1534–1540 の submodule は別 object store であり、T:1010–1013 のコピー元も新設 fixture base です。Git 環境の剥離（T:369–377、M:559–568）と入口の拒否（M:636–654）も説明と整合します。

ただし、入口拒否や Git エラーまで `missing-commit` になるという意味ではありません。insight には次の1文が適切です。

「通常の Git と正常に構築された現行 fixture を前提に、記録 commit 2本を主 object store へ取り込む経路は確認できず、その不在という fixture 契約も固定するため、production から導出しない `missing-commit`／None の literal 期待値を採用した。」

## 総括

**must-fix 0件、patch は GO。** 変異 spec 2本の期待 node 集合は、S＝{e2e, unit} に対する静的予測として**支持**します。変異の実測帰属は未確認です。

焦点走は **348 passed・7 skipped、failure/error なしで緑**。実 repo test 除外理由の「差分が消える」は、上記 should のとおり insight で訂正してください。