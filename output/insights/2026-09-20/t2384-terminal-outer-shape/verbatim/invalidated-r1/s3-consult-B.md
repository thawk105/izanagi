## 所見一覧

| id | 重要度 | 対象 | 所見 | 放置時の成果物影響 1 行 |
|---|---|---|---|---|
| B1 | **must-fix** | plan | M4・M8 の `old` が terminal helper と既存 `_wal_trigger` の **2 箇所**に一致する。 | 正規 harness は注入前に停止し、予定した変異台帳を完成できない。先頭だけ置換すれば FC05C の変異を FC07 の証拠へ誤帰属する。 |
| B2 | nit | brief | P3 の「payload fallback は死ぬ」と P4 の「非 dict payload は常に上流拒否」は誤り。plan §6 の訂正を反映すべき。 | 現 plan は正しく補正しているため受理集合への影響はないが、等価変異の説明が親子で矛盾する。 |
| B3 | nit | brief | 焦点走 11 file は builder 利用箇所の閉包ではない。plan が追加した campaign issuer を反映すべき。 | 親が 11 file を使うと、変異台帳の実走範囲が plan の 12 file と異なる。具体的な追加 kill は未実測。 |
| B4 | nit | brief | checklist の「行 17」は項目番号。実際の位置は `docs/phase3-8c-wiring-design.md:893`。研究前進の記述も外部観測面を明示すると正確。 | 実装の受理集合・reason・receipt は変わらないが、追跡位置と研究成果の説明が曖昧に残る。 |

## 各所見の根拠

以下、plan は [s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2384-terminal-outer-shape/codex/s2-plan.md)、brief は [s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2384-terminal-outer-shape/s1-brief.md) を指す。検査は読み取りと静的照合のみで、pytest・collection・変異走は実行していない。

**B1 — 置換対象の一意性と変異の帰属**

plan:103 の M4 と plan:107 の M8 は、既存 consumer:1016–1017 にも一致する。plan の helper と呼出しをメモリ上で挿入して文字列出現数を数えると、次の結果だった。

| 変異 | `old` の一致数 | 静的な帰属判定 |
|---|---:|---|
| M1：逐語 B-057-M5 | 1 | root stage が先行 gate で必須となるため等価 |
| M3：superset 許容 | 1 | 新しい extra-root / root-shadow 負例が殺す |
| M4：bool 許容 | **2** | anchor 修正後、新しい terminal ts-bool 負例が殺す |
| M5：件数検査除去 | 1 | 新しい duplicate-terminal 2 負例が殺す |
| M6：gate 無効化 | 1 | 新しい外枠・型・重複負例が殺す |
| M7：payload 型述語無効化 | 1 | 他の先行検査によって等価 |
| M8：有限性述語無効化 | **2** | terminal に限定した注入後は等価予測 |

`tools/mutation_harness.py:1079–1092` は累積 source に対して `count == 1` を要求する。したがって現 anchor は DW-M04 に違反し、通常は誤った kill に至る前に停止する。

最小修正は、M4・M8 とも `ts = terminal["ts"]` から始まる複数行ブロックを `old/new` に使い、変更する述語だけを書き換えること。production の定数共有や `_wal_trigger` の変更は不要。

新 gate 固有の M3・M5・M6 は、新 test だけで検出できる静的構成になっている。

- **M3:** root attempt が正しければ resolver は root を採用する。extra-root / root-shadow を superset で通すと、既存 abort 判定も通って `P6Unavailable` に進む。
- **M5:** 同一 attempt の terminal を追加しても trigger は 1 件で、末尾の正常 abort は保存される。件数検査を外した場合だけ新負例が通過する。
- **M6:** 外枠だけを壊した新負例は、従来の attempt・stage・reason・verify 判定を満たすため gate 無効化を検出する。

一方、既存 `test_fc07_rejects_legacy_root_kind_terminal_shape`（test:1639）は、gate を外しても root stage 比較で FC07 になる。新設 gate の検出証拠には数えられない。新しい payload-only-stage と terminal-before-last も、M6 単独では旧 stage 判定に遮られる。plan が前者を M6 の kill 予測から除外しているのは正しい。

M2 は **1 mutation spec の `replacements` に M6 と M1 の 2 置換**を入れれば表現できる。harness は同一 file の累積置換を実装しており、両 anchor は相互に消さない。payload-only-stage はこの合成変異を新 test として検出する。ただし M2 は M6 の他の kill も継承するため、期待 node を payload-only-stage だけに固定してはいけない。plan:115 の probe による完全集合確定は DW-M07・M08 に合う。

**B2 — 等価性は結論と判定順を分けて記録する**

consumer:1095–1099 の `_wal_field` は root 優先、その次に dict payload を読む。

- exact outer keys の下では `stage` は root に必ずある。したがって M1 は等価。
- `build_attempt_id`・`reason`・`verify`・`verify_configs` は exact outer keys に含まれない。これらは **payload fallback が必要になる**。brief:12 の一般化は逆。
- `reflux_result_evidence.py:1573–1577,1636` は root attempt があれば非 dict payload でも attempt 検査を通す。この場合は新 gate の exact keys が先に拒否する。
- root attempt がなく非 dict payload なら resolver が拒否する。よって M7 の型述語だけを外しても受理集合は変わらない。
- M8 の非有限値は strict JSON / canonical serialization、frame ではさらに `wal.parse_line` の有限性検査で拒否され、FC07 の当該述語を独立に露出できない。

plan:90–91、§6 の補正は妥当。DW-M04 に従い、実走時には注入 diff を確認してから等価として確定する必要がある。

**B3 — 焦点走と pin 閉包**

`git grep` で builder を参照する tracked test file は **11 本**。その中に brief の集合にはない `test_reflux_campaign_issuer.py` がある。plan:145–170 の **直接参照 11 本＋間接利用の originless compatibility＝12 本**という整理を支持する。

pin について、変更対象の hash 不在だけでは結論できないが、今回の生成依存は閉じている。

- test:374–376 は test ごとの `tmp_path` に fixture を生成する。
- `_projection_records`（test:507）は読み出した records を deepcopy する。
- `_rewrite_wal`（test:468–492）はそのケースの source / projection bytes と参照 hash を書き換える。`_set_record`（test:452）はケース内の record と member digest を更新する。**builder を呼び戻したり既定値を変更したりする経路はない。**
- baseline は builder の既定出力を pin し、`test_reflux_origin_fixture_builder.py:107` から独立再計算する。
- result evidence の golden（test:39–42,511–538）も `build_result_evidence_record()` の既定出力を使う。consumer の gate や追加 test の本数には依存しない。
- builder のメタ検査（test:89 以降）は export・signature・baseline entry を固定する。consumer test の関数数や node 目録を固定していない。
- duration ledger の consumer entries は時間配分用。`tools/acceptance_shards.py:397–404` は未知 node を 1 秒として扱う。`test_update_acceptance_duration_ledger.py:305–319` の件数検査は **台帳内部の整合性**であり、現在の collection 数との一致ではない。

したがって baseline・golden・duration ledger を更新する必要は見つからない。追加 test のためにこれらを変更するのは不要な差分になる。

`_validate_wal_outcomes` の production caller は consumer:1448。確認した参照には FC07 の挙動を追加の hash・件数 literal で固定する箇所は見つからなかった。docs:893 は設計 checklist で、生成 bytes の pin ではない。不在の説明は tracked 範囲に限定し、未追跡 output 全体へ一般化しない。

**scope・全層適用・研究前進の確認**

plan の専用 helper は、key 集合・値の型・terminal 重複・root shadow の **4 項を扱う**。stage の型は JSON 値に対する commit / abort の tuple membership によって閉じる。payload key 集合は閉じず、非 terminal の外枠検査にも拡張していない。共通定数化・一般 helper 化・新台帳の追加はなく、削除すべき scope 超過は見つからない。

両入力経路への適用も成立する。

1. `reflux_result_evidence.py:1580–1586` の canonical-list 経路は `parse_line` を通らない。terminal 外枠 gate が必要。
2. frame 経路（同:1588–1606）は `parse_line` を通るため、外枠の型・keys は上流で検査済み。
3. 両経路は同:1640 の source/projection 一致検査を経て、consumer:1448 の同じ FC07 に入る。
4. `wal.py:367–368` が明記する通り、event topology は consumer の責務。**terminal 重複検査は frame 経路でも冗長ではない。**

したがって D1665 の canonical-list に関する理由は terminal にも成立する。frame の不正外枠が上流拒否となることまで FC07 に変更する必要はない。

B4 の研究前進行は、次の表現が適切。

> terminal 外枠が不正な projection を FC07 で拒否し、fixture 由来の形が後続判定と receipt 発行へ進む経路を閉じる。certified 選択集合は変えず、変わるのは拒否 reason と receipt / evidence-root 参照である。

「production abort 形」の正例は、正常な既存 fixture payload に production と同じ外枠を使う意味に限定する。全 production abort 経路の到達性を証明するものではない。

## 総括

must-fix は **1 件**。最重要は M4・M8 の非一意 anchor を terminal 専用ブロックへ直すこと。
新 gate 固有の変異は新 test で検出できる静的構成で、等価予測 3 本の判定順も妥当。
実装 2 file の scope を支持し、baseline・golden・duration ledger の更新は不要。
親 brief は P3/P4 と焦点走 12 file を plan に同期する。実走結果と kill 完全集合は親の測定待ち。
