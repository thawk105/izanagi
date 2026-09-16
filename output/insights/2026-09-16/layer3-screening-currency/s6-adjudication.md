# 段 6 裁定 — 敵対レビュー 2 本の所見と、親の裏取り

レンズ A (「このテストは本当に主張を pin しているか」) と
レンズ B (「契約違反と、親が書こうとしている docs の誤り」) の所見を裁定する。
**親が一次資料で裏取りした項目には「親実測」と付す。子の逐語をそのまま採らない。**

## 実装差分の判定

**採用。契約違反なし。** 変更は `orchestrator/tests/test_layer3_report.py` の
import 1 行 + テスト 5 本 (204 行追加・削除 0)。production・schema・既存 helper・既存 assertion・
所要台帳はいずれも不変。monkeypatch も共有 fixture も新設していない。両レンズが独立に同じ判定。

**親実測** — test 関数名集合の差分は追加 5・削除 0 (`comm` で突合)。
焦点走 `test_layer3_report.py` は **222 passed** (変更前 217)。
台帳 coverage の node は**新テスト込みで 1 passed** (53.21 秒、実走)。

**恒真化はゼロ** (レンズ A)。5 本とも期待値を生成後 WAL から独立に読み、report からは作っていない。
T1 が literal で書く variant `610e879931c4` は tracked WAL の保存値で、
**保存資料そのものを編集しない限り動かない** (レンズ A が `git ls-files --stage` で確認)。

## 変異事前登録の差し替え (real / must-fix、レンズ A)

段 4 初版の M1〜M5 のうち **4 件が過剰決定**だった。**親実測**で再照準した結果が下である。
初版は消さず erratum として残す (`DW-M02`)。詳細は wave dir の `mutation-design.md`。

| 初版 | 判定 | 理由 (親が現物で確認) |
|---|---|---|
| M1 | **採用 (MUT-A へ)** | 単一理由。ただし `_view_row` の payload は浅いコピーなので、**新しい dict を作らないと入力と一次配置まで壊れる** (レンズ A の指摘) |
| M2 | **却下** | `test_abort_event_renders_abort_view_and_commit_absent_reject` が既に殺す |
| M3 | **却下** | producer の `_assert_bijection` 自身が fail-closed で殺す |
| M4 | **却下** | `verify_done` 不在で例外を出す変異は、既存の `_campaign(tmp_path, [_bench()])` 系を広く殺す |
| M5 | **却下** | `test_body_event_omission_is_detected` が殺す。比較を 1 本だけ無効化すると T4 は**例外メッセージの不一致**で赤くなるだけで、`DW-M03` が禁じる「診断文字列だけの赤」に当たる |

**本走で使う 3 件** (anchor はいずれも `layer3_report.py` 内で一意。親が `grep -c` で 1 を確認):

| ID | 位置 | 変異 | 新 tip | 変更前 commit |
|---|---|---|---|---|
| MUT-A | `_view_row` の return | 返す dict の `screen` から `margin` を落とす (新しい dict を作る) | T1 KILLED | SURVIVED |
| MUT-B | `build_report` の rejects 構築 | `canonical_record_ref("wal", events[-1])` → `events[0]` | T2 KILLED | SURVIVED |
| MUT-C | `build_report` の verifications 構築 | abort event から架空の verification 行を足す | T5 KILLED | SURVIVED |

**正直な非主張 — T3 と T4 の検出力は既存 gate と分離できない。**
T3 が見る性質 (abort ref の多重度、`source_refs` 区画、`_report_primary_refs` の一致) も、
T4 が見る性質 (件数同一の一次配置改変の拒否) も、producer の `_assert_bijection` が
**無条件に強制している**。崩す変異は必ず producer 自身の fail-closed を先に踏む。
この 2 本は確認用の pin であり、kill の証拠に数えない。

**この wave が新しく得た検出力は T1・T2・T5 の 3 点**であり、それはちょうど
**producer が強制していない 3 つの性質** — view の値の完全性、reject の `source_ref` の指し先、
架空 verification の不在 — に対応する。**これは [T-326] が所見として記録した内容そのものである。**

## docs 起草文の事実誤り (real / must-fix、レンズ B。4 件とも親が裏取りして採用)

### B-1. 描画を可能にした commit の役割 (採用)

**親実測** — `git show --stat` の現物:

- **`b8318b956`** (2026-08-25 15:29、[T-1291]) — `layer3_schema.json` へ
  `screening` / `screening_disabled` を排他制約つき optional property として追加 (+13 行)、
  producer 側に 17 key の runtime 閉包検査を置いた。commit message に
  **「実 artifact backoff-sweep-silo-read-heavy-sweep-6f169f90 が
  `Additional properties are not allowed ('screening' was unexpected)` で描画できなかった」**と明記。
  同 message は「この commit は段 5 の統合断面であり、テストはまだ緑ではない」とも書く。
- **`ed251424d`** (2026-08-25 16:27) — `layer3_schema.json` の
  `"settled": {"type": "boolean"}` を `{"type": ["boolean", "null"]}` へ広げた (1 行)。
  **`layer3_report.py` は 1 行も変えていない。** commit message に
  **「名指し artifact … が build_report を最後まで通ることを親が実測で確認した
  (runs 2 行、うち 1 行が screening true)」**と明記。

**したがって起草文の「renderer 側 `ed251424d`」は誤り。** 描画を可能にしたのは
**schema の 2 段の変更** (screening property 追加 + `settled` の null 許容) であり、
renderer は関与していない。**さらに重い事実**: 2026-08-25 の commit message 自身が
「親が実測で確認した」と記録しているのに、翌日以降の版 (2026-08-26 / 09-02 / 09-05 / 09-14) が
4 版続けて「対象外」と書き続けた。

### B-2. 既存 7 件の内訳 (採用)

**親実測** — 保存済みレポートの path 一覧は trigger **sweep 6 件 + trigger loop autonomous 1 件**。
起草文の「p3-s8a-trigger-sweep 系」は誤り。「trigger 系 (sweep 6 件・loop 1 件)」に直す。
loop の lock も trigger 軸なので、D170 による結論は変わらない。

### B-3. 「執筆時点で腐っている箇所は無い」の発言元 (採用)

**親実測** — 当該文言は **`docs/paper-story/README.md` の現行記述**であり、
2026-09-14 版の本文には無い。起草文の「同版が…と書いたのは誤りだった」は帰属を誤っている。
**「本 README が同版について『執筆時点で腐っている箇所は無い』としたのは誤り」**に直す。

また B-9 の箇所は「対象外」の逐語ではなく「対応が要る」という未対応扱いなので、
**「計 6 箇所で未対応として扱っている」**と書く。

### B-4. `classification` の参照先 (採用)

**親実測** — `jq 'has("classification")'` = `false`、`has("admission_status")` = `false`、
`has("admission_decision")` = `true`。
**top-level の `classification` と `admission_status` は null 値ではなく key 自体が無い。**
段 4 裁定 R1 の表もこの点を区別できていなかったので、ここで訂正する。
正しい参照先は `admission_decision.classification` と `admission_decision.admission_status`。

## 取り残し (real / must-fix、レンズ B。採用)

**`docs/glossary.md` の `low-fidelity proxy` 項が、bench-first screening v2 を
「方針採用済み・未実装 (D58)」と書き続けている。**
`docs/phase3.md` は同じ機構を「実装済み (2026-07-15、D58。監査 must-fix 対応込み)」と書く。
glossary は `tools/check_docs.py` の `LIVING_DOCS` に入る現況文書である。

**裁定: 直す。** 本 wave の主題 (screening に関する現況主張の鮮度) と同じ面であり、
1 行の訂正で、適用制限 (偵察 sweep / 8b の opt-in に限る) はそのまま残す。
**隣接訂正であることを記録に明記する。**

## 採番方式の訂正 (real / must-fix、レンズ B。採用)

**親実測** — `docs/spool/README.md` の「placeholder (遅延採番)」節:
「新しい T / D / F 番号は **fragment に書かない**。書くのは名前 (slug) だけで、実番号は fold が付ける」
「fold 後に `{{` `}}` が 1 つでも残れば停止する」「**wave 側で fold してはならない**」。

**したがって段 4 裁定 R6 の「段 7 直前に再走査して番号を確定し docs へ差し込む」は誤り。**

- spool fragment では `{{T:slug}}` を使う。**実番号は書かない。**
- **通常 docs (`phase3.md` / `paper-story/README.md` / `glossary.md`) には未確定 ID を書かない。**
  fold は spool fragment しか書き換えないので、通常 docs に残した placeholder は
  `check_docs.py` で赤になる。参照は insight の path・日付・節名で行う。
- land 前に `python3 tools/spool_fold.py --dry-run --show-diff` を rc=0 まで通す。

レンズ B が挙げた fragment の形式要件 (file 名、frontmatter、H2 は `## 本文` と `## 次の一手差分` の
2 つだけ、`### 新規` の `- {{T:slug}} ...`、既存 active ID の `base:`、`完了` の `remaining: none`、
**未登録の wave 自身に架空の ID を付けない**) は段 7 で正本を読んで従う。

## refuted (不採用)

| # | 所見 | 反証 |
|---|---|---|
| F1 | 期待値の自己参照・恒真化 (レンズ A が自ら refuted) | 5 本とも生成後 WAL から独立に期待値を作る |
| F2 | variant literal が揮発しうる | tracked WAL の保存値。資料を編集しない限り動かない |
| F3 | helper の variant 置換・時刻の誤用 | `ts` を 1.0/2.0/3.0 に明示しており、reject 参照が確実に abort を選ぶ |
| F4 | 4 本の逐語重複が壊れる | 現状では壊れない。将来の保守負担であって現在の検出欠陥ではない。共有 fixture 新設の根拠にしない |
| F5 | 非公開 API の直接呼び出しが慣行外 | 既存テストが `_view_row` / `_validate_schema` を直接呼んでいる。慣行内 |
| F6 | 周辺 4 file を構造的に赤にする | 収集規約・group・fixture 閉包のいずれにも触れない。**ただし未実走なので通過の断定はしない** — 段 7 後の受入全走で確かめる |
| F7 | 台帳 coverage が閾値を割る | **親実測で 1 passed** (新テスト 5 本込み、53.21 秒)。件数の議論ではなく実走で確定した |

## fix の要否

**実装差分への fix は不要** (契約違反 0、恒真化 0)。
must-fix はすべて**親が書く docs と変異登録**の側にあり、段 5 の実装子へ戻す必要はない。
したがって段 6 の fix 子は起動しない。
