# [T-2101] 段 4 裁定 — plan v2 と変異事前登録

段 3 の 2 レーンは重複せず、それぞれ別の中核欠陥へ到達した。sol は「登録値がどの提案を指すか」を、
luna は「拒否がどこで起きるか」を割った。両者が別経路で同じ土台の問題 (S9/S14 と L3) を突いている。

## 0. 親 brief の訂正 (段 3 が指摘し、親が real と認めたもの)

- **(訂正 1) 「発火条件は今日以降の B-4 formal 実行のすべて」は誤り。** 事前登録 §5 は `未記入` で
  (`docs/phase3-b4-reflux-ablation-preregistration.md:154-167`)、全欄記入 commit が実走条件
  (`:624-626`)。launcher が要求する admission record 3 件も HEAD に存在しない。
  **現 HEAD で formal B-4 は開始できない。** 親の実測 5 は artifact 0 件までが real で、
  そこから導いた発火条件の一般化が false だった (sol S1、luna L17 が独立に再現)。
  **本 wave の位置づけは「今日発火する gate」ではなく「実走開始前に束縛を閉じる」である。**
  D1343 が却下した選択肢 (b)「束縛を閉じないまま実走する」を将来にわたって塞ぐ作業であり、
  実装を止める理由にはならない。
- **(訂正 2) 「拒否は build・lock・WAL より前」は real だが、「実行前」の広い読みでは不足。**
  3 driver とも照合の前に `pgrep` (単独性検査) と `git rev-parse` / `git status` (pin 検査) を
  spawn し、launcher bootstrap は照合前に campaign directory と sidecar を作る (luna L1/L2)。
  campaign lock・WAL・build・bench より前であることは luna L4 が独立に再現した (refuted 側)。
  **記述を「campaign 実行の副作用より前」へ弱め、先行する preflight process を非保証に列挙する。**
- **(訂正 3) 親 brief の実アンカー表は base loop の `load_proposal_file` を単一の関門として扱ったが、
  base だけが load 前に terminal receipt を完全検証し、sort/trigger は raw SHA しか計算しない
  (luna L11)。3 driver は同型ではない。**

## 1. 中核裁定 — 登録値が指す提案は「初期 (bootstrap) proposal」である

sol S9 / S14 と luna の指摘を受け、**親が一次資料で独立に検算した。** 結論は real である。

- 事前登録 §5.1 の適格性述語:「**初期 proposal が、事前に固定した bootstrap 集合に属する。
  実走開始後に足さない。**」(`docs/phase3-b4-reflux-ablation-preregistration.md:377`)
- 同 §:「`precursor_hash_mismatch` — 同じ block の両アームの `precursor_hash` が一致しない」(`:547`)
  → **1 block の on / off は同じ `precursor_hash` を持つ。**
- raw producer は `precursor_hash` を `registry_attempt.initial_proposal_sha256` から出す
  (`orchestrator/campaign/p3_b4_raw_record_producer.py:2033, 2328`)。

したがって `initial_proposal_sha256` は **block 共有の初期 proposal** の hash である。
一方 launcher の `--proposal` は、continuation では critic pair を実行した**後**に main session が
書く**アームごとに異なる次の synthesis** である (`p3_b4_launcher.py:574-609`)。

**帰結: continuation の `--proposal` を `initial_proposal_sha256` と比較してはならない。**
比較すれば 1 block の on / off に同一の提案を強制することになり、測ろうとしている treatment 効果を
構成的にゼロにする。これは正しさ防壁ではなく実験そのものの破壊である。

### 1.1 continuation 側を閉じられるか — 親の実測

continuation で登録値を強制する唯一の筋は「この campaign を種付けした初期 proposal が登録値と一致する」
の検査である。ループがそれを再導出できるかを実測した。

**再導出できない。** checkpoint に焼く辞書 (`p3_s4_loop.py:1083-1092` `state_to_dict`) は
whiteboard の 5 field (`iteration` / `direction` / `magnitude` / `result` / `delta_pct`) だけで、
**proposal の `value` も `implementation` も意図的に落としている** (D39 決定 3 の構造的リーク遮断、
規律 2/6)。初期 proposal を復元する経路はループ内に無い。

作るには新しい耐久 carrier (受領証・台帳) が要る。これはユーザーが本 wave の scope 外と明示した
「台帳の追加」に当たり、かつリーク遮断の設計判断に触れる。**親は発明せず裁定へ返す。**

### 1.2 したがって本 wave が閉じる範囲

- **bootstrap launch (`launch_bootstrap`、`b4_closed_critic_receipt_sha256 is None`) では
  `--proposal` が初期 proposal そのものである。** ここで登録値との一致を強制することは、
  事前登録 §5.1 の適格性述語「初期 proposal が事前固定 bootstrap 集合に属する」を
  実行時に強制することと同義であり、D1343 の文言どおりの実装である。**これを実装する。**
- **continuation は本 wave では束縛しない。** 挙動を変えず、非保証として逐語で列挙し、
  裁定パッケージ 1 として返す。**不履行の束縛引数を continuation で受け取ることもしない** —
  強制しない引数を要求するのは、D1343 が問題視した「ラベルを付けるだけ」の再生産だからである。

## 2. 所見の裁定

### real・採用 (plan v2 に反映)

| # | 所見 | 裁定 |
|---|---|---|
| S9 / S14 | 登録値は precursor / 初期 proposal であって次の synthesis ではない | real・採用 (§1)。**本 wave の scope を決める** |
| S2 | 固定 root/id では不一致入力列が構成でき、比較は恒真でない | real・採用 (§3 の非恒真性証拠) |
| S7 | end-to-end 変異は projection closure gate が先に赤を出しうる | real・採用 (§5 の変異設計) |
| S8 | 束縛不在の変異は argparse と driver の二重 gate で帰属が隠れる | real・採用 (§5 で境界別に分ける) |
| S10 | canonical serializer は `1` と `1.0` を区別するが実行 genome は同じ | real・採用 (§3.3 で identity を明示裁定) |
| L1 / L2 | 照合前に `pgrep` / Git / sidecar / campaign directory が先行する | real・採用 (訂正 2、非保証へ列挙) |
| L5 | launcher 前倒しと driver 再読取りの併用は二重 open の ABA を作る | real・採用 (§3.2。**launcher 前倒しを採らない決定的根拠**) |
| L9 | attempt_id だけで行を選ぶと別 driver の行を引ける | real・採用 (§3.4。行選択は本題の一部) |
| L11 | terminal receipt の検証順序が base と sort/trigger で非対称 | real・採用 (訂正 3、記述の訂正のみ) |
| L14 | `_production_launch_context` の 15 利用者が波及の中心 | real・採用 (§4 の実装指示) |
| L18 / L19 | 3 driver の projection digest が動き、v2 lock は再開時に drift で止まる | real・採用 (非保証へ列挙) |

### real だが本 wave の scope 外 — 非保証に明記し裁定パッケージへ回す

| # | 所見 | 裁定 |
|---|---|---|
| S3 / S5 | root を量化すると caller が `H(B)` を持つ別 publication を発行できる | real。**どの publication が権威かは上位層の問い。** 裁定パッケージ 2 |
| S12 / L22 | runtime 束縛の成功が耐久証拠に残らず、後から attempt を付け替えられる | real。耐久 carrier の新設が要る。裁定パッケージ 1 と同根 |
| S13 / L21 | manifest 201 行の外にある registry 行も実行できる | real。「formal = manifest 201 行」かの裁定が要る。裁定パッケージ 3 |
| L16 / L23 | 束縛が loader 内に閉じ、`drive_iteration` / `run_one_iteration` の型に載らない | real。formal launcher 限定か全 sink かの裁定。裁定パッケージ 4 |
| L20 | issuer 側の canonical hash producer が無い | real。T-2050 / T-2051 の領域。親 brief が既に scope 外と宣言済み |
| L3 | continuation は proposal が存在する前に critic 2 process と receipt を作る | real。**protocol 固有の順序であり欠陥ではない。** §1 の帰結として非保証へ列挙 |

### refuted

- **L7 (duplicate key を拒否すべき) — refuted・不採用。** 実行されるのは parse 結果であり、その
  canonical hash は登録値と一致する。**束縛されるのは「実行される提案」であって file の bytes ではない。**
  D1343 が要求するのは canonical hash であって raw bytes hash ではなく、D302 も内容の再導出を求める。
  raw-byte の固定性は本 wave が主張しない別命題なので、非保証へ 1 行書いて閉じる。
  仮想リスク向けの検査追加は scope 外という依頼にも従う。
- S4 / S6 / L4 / L8 / L10 / L12 — 段 3 自身が refuted と判定し、親も同意する。
  特に **L8 は「receipt key の追加・削除で hash を制御できない」ことを既存 receipt gate の
  順序から示した。この順序は plan v2 で保持する** (§3.2)。

## 3. plan v2 — 確定する設計

### 3.1 適用範囲

`b4_reflux_ablation=True` かつ **bootstrap** (terminal receipt 束縛なし) の経路だけを対象にする。
3 driver (base / sort / trigger) すべてに適用する。continuation と非 B-4 経路は挙動を変えない。

### 3.2 照合の位置 — loader 内、既存 receipt / schema gate の直後

luna L5 が決定的である。launcher で先に読んで driver が再度開けば二重 open の ABA が入る。
**照合は各 driver の loader 内に置き、proposal file を開くのはそこ 1 回だけとする。**
既存の receipt gate・closed schema 検査の**後**に置く (L8 の refutation を保つため)。
`drive_iteration` へ渡す前に完了させる。

campaign lock・WAL・build・bench・実 worktree 操作より前であることは luna L4 が再現済み。
先行する `pgrep` / Git / sidecar / campaign directory 作成は**非保証として列挙する** (訂正 2)。

### 3.3 canonical hash

段 2 プランの定義を採用する。`attempt_registry_core.canonical_json_bytes` (`:197-206`) に
parse 結果を渡した bytes の sha256。bootstrap では receipt key は存在しないため、除外規則は
continuation 用の将来互換として関数に残すだけで、本 wave の発火経路では効かない。

**identity の裁定 (S10 への回答):** 束縛するのは **document exact value** である。
`1` と `1.0` は別の提案として扱う。理由は、登録値が事前に固定された「その提案」を指すからであり、
実行 genome が同じになることは同一性の根拠にならない。key 順・空白・非 ASCII の表記差は
同じ hash になる (canonical 化の目的そのもの)。この選択を非保証と正例の両方に書く。

### 3.4 登録値の取得と行の選択

`load_b4_prerun_publication(publication_root)` (`p3_b4_prerun_issuer.py:1009`) の返す
封印済み registry から、`attempt_id` が exact に 1 件一致する行を選ぶ。
**その行の `driver` が実行中の driver と一致することも検査する (L9)。**
一致しなければ拒否する。これは追加 gate ではなく、**正しい登録値を引くための行選択の一部**である。
語彙 (`base` / `sort` / `trigger` と registry の `driver` 値) が一致しない場合は、
実装子は勝手に写像を発明せず**報告して止める**。

`workload` / `bootstrap_member` / manifest membership の照合は**しない** (裁定パッケージ 3)。

### 3.5 fail-closed の範囲

bootstrap かつ B-4 mode で、次はすべて拒否する。素通しの分岐を作らない。

- 束縛引数の欠落 (片方だけ・両方なし・空文字)
- publication root が相対 path・不在・load 失敗 (例外を握り潰さない)
- attempt_id が registry に無い / 複数一致
- 登録値が 64 hex でない
- 行の `driver` が実行中の driver と一致しない
- 再導出した canonical hash が登録値と一致しない

**continuation で束縛引数が渡された場合も拒否する** (§1.2)。非 B-4 経路で渡された場合も拒否する。

### 3.6 変更面

段 2 プランの編集面一覧から continuation 用の追加を除いたもの。launcher は `bootstrap` mode でのみ
両引数を必須にし、`_driver_argv` は bootstrap のときだけ argv へ載せる。

## 4. 段 5 の分割と実装子への個別指示

Codex `role=author` 1 単位。編集面が相互依存 (共通関数 → 3 driver → launcher) のため分割しない。
実装子には次を個別に明記する (契約文書にあるだけでは破られる)。

- docs を編集しない。commit しない。
- 既存テストの期待値を変更・反転・緩和・skip・削除しない。赤なら実装側が誤りとする。
  期待値が誤りと判断したら実装を変えず**報告して止める**。
- `_SOURCE_CLOSURE_PATHS` と凍結 closure 5 file を 1 byte も編集しない。
- 新しい台帳・受領証・署名・capability・一回性状態機械を作らない。
- continuation の挙動を変えない。非 B-4 経路の挙動を変えない。
- `test_p3_b4_closed_critic.py:109-160` の `_production_launch_context` は 15 利用者を持つ。
  helper 内で正当な publication fixture を用意して従来の検査目的を保つ (luna L14)。
- 既存の拒否順序を保つ: fixture / no-build 拒否は pin 検査より前という既存 pin
  (base `test_p3_s4_loop.py:5216-5237`、sort `:1210-1238`、trigger `:3153-3184`) を壊さない。
- 新規 test file には自走 harness
  `if __name__ == "__main__": raise SystemExit(pytest.main([__file__, "-q"]))` を置く。
- 緑には実走 nodeid と範囲を併記する。実走できなければ「実装済み・未実走」と書く。
- 完了報告に所有外 caller・共有 fixture・consumer test の波及可能性を静的列挙する。
- 期待値へ揮発 payload (working tree hash 等) を焼き込まない。

## 5. 変異事前登録 (DW-M01)

実装後に harness で走らせる。各変異は単一理由性を実装時にコードで確認し、確認できなければ
登録せず実効 gate へ再照準する。**sol S7 に従い、end-to-end launcher 経路の変異は
projection closure gate が先に赤を出しうるため、変異は loader / helper 水準の test node へ
帰属させる。** sol S8 に従い、束縛不在の変異は境界ごとに分けて登録する。

| ID | 変異位置 | 期待 kill 理由 (受理集合または fail-closed 挙動の変化) |
|---|---|---|
| M01 | 再導出 hash と登録値の等式比較を外す | 登録値と異なる bootstrap 提案が実行される |
| M02 | expected を registry でなく再導出した observed から取る | 自己比較になり、どの提案でも通る (恒真化) |
| M03 | driver 内の束縛引数必須検査を外す (launcher の `required` は残す) | 引数を持たない直接呼出しが素通しする |
| M04 | launcher argparse の `required=True` を外す (driver 側は残す) | argv に載らず、driver 到達前に束縛が落ちる |
| M05 | 行選択から `driver` 一致検査を外す | 別 driver の登録行の hash と比較して通る |
| M06 | canonical 化を parse 結果でなく raw file bytes の sha256 に変える | key 順・空白だけ違う正当な提案が拒否される (過剰拒否) |
| M07 | 照合を `drive_iteration` の後ろへ移す | 拒否前に campaign 実行が始まる (実行前性の喪失) |
| M08 | attempt_id lookup を「registry の先頭行」に変える | 指定した attempt と別の行の hash と比較する |
| M09 | publication load の例外を握り潰して素通しする | 壊れた publication が束縛なしで通る |
| M10 | sort driver だけ照合呼出しを外す | 片肺。sort の formal bootstrap が素通しする |
| M11 | trigger driver だけ照合呼出しを外す | 片肺。trigger の formal bootstrap が素通しする |
| M12 | continuation でも登録値との等式比較を強制する | **過剰拒否。**両アームに同一提案を強制し treatment を消す |
| M13 (正例) | 過剰拒否の検出。登録値と一致する正当な bootstrap 提案を、key 順と空白を変えた表記で与える | producer 固有の追加条件で拒否されないこと。**SURVIVED が期待値ではなく、この正例が緑であり続けること**を確認する |

M13 は DW-M01 の「受理集合を縮小する wave では承認外の過剰拒否を検出する正例も登録する」に対応する。
M12 は §1 の中核裁定を機械で守る変異であり、**実装が continuation へ滲み出した瞬間に赤になる**。

期待 node の完全集合は実装後 (DW-M07) に anchor 再検証して確定する。

## 6. ユーザーへ返す裁定パッケージ (scope 外・実装しない)

1. **continuation の提案束縛をどう閉じるか。** 登録値は block 共有の初期 proposal を指し、
   continuation の `--proposal` はアームごとに異なる次の synthesis である。ループは checkpoint から
   初期 proposal を再導出できない (`state_to_dict` が value と implementation を意図的に落とす)。
   閉じるには耐久 carrier の新設か、リーク遮断の設計変更が要る。どちらも本 wave の scope 外。
   一次資料 = 事前登録 §5.1 (`:377`, `:547`)、`p3_s4_loop.py:1083-1092`。
2. **どの publication が権威かを誰が決めるか。** publication root は caller が実行時に選び、
   issuer は別 root での再発行を防がない。任意の提案 B に対して `H(B)` を持つ registry を
   別 root に発行すれば必ず通る。本 wave の検査は「指定された組の不一致」を拒否するが、
   「事前固定した集合」であることを証明しない。一次資料 = sol S3/S5、`p3_b4_prerun_issuer.py:709-727`。
3. **formal B-4 の母集合は manifest 201 行か、registry 全行か。** 現在の設計では
   manifest 外の registry 行も実行でき、raw producer が後から拒否するまで build と WAL は進む。
   一次資料 = sol S13、`p3_b4_analysis_ledgers.py:1071-1105`、`p3_b4_raw_record_producer.py:945-954`。
4. **保証の境界は formal launcher 限定か、B-4 marked config を受ける全 sink か。**
   D1343 の文言は「実行ループ側」だが、束縛は loader 内に閉じ `drive_iteration` の型には載らない。
   一次資料 = luna L16/L23。

## 7. 非保証 (実装成果物へ逐語で載せる)

- continuation の提案は内容束縛されない (裁定パッケージ 1)。
- どの publication が権威かは強制されない (裁定パッケージ 2)。
- manifest membership は検査しない (裁定パッケージ 3)。
- 束縛の成功は耐久証拠に残らない (S12)。
- 束縛されるのは実行される提案 (parse 結果の canonical 形) であって file の raw bytes ではない。
- 照合の前に単独性検査 (`pgrep`)、Git pin 検査、launcher sidecar と campaign directory 作成が起きる。
- `1` と `1.0` は別の提案として扱う。実行 genome が同じでも hash は異なる。
