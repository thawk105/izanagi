# [T-2854] 残り (1) — 段 4 裁定 (親、2026-09-23 JST)

入力: s1-brief.md、codex/s2-plan.md、codex/s3-consult-A.md (A1〜A7)、codex/s3-consult-B.md (B1〜B8)。
裁定 inbox 再走査 (段 4 直前): 新着 2 件 (第 32 回 項 7 = 単位 11 の push 判断、2026-09-23 push 済み branch の食い違い) は push / 単位 11 の話で本 wave の verifier 変更に影響なし。

## 所見の裁定

| 所見 | 判定 | 採否・扱い |
|---|---|---|
| A1 / B2 (P1 は初期集合の検証でなく推定、brief が §3.3 を強めた) | real (表現の過大) / 実装の差し替えは refuted | 下の R1。P1 を「silo の版付けに裏付けられた段 1 の存在契約」として採用し、初期ロード集合そのものを検証したとは書かない。 |
| A2 (不存在・abort・自己読みの native 挙動) | real | 採用。自己版読みの試験は「合成形式の意味」の試験と明記し、実 emitter の証拠と区別する。 |
| A3 (P3 は必要) | real | 採用 (R3)。 |
| A4 (段 2 の再挿入・空 scan) | real だが scope 外 | 実装しない。insight の限界と後続 (単位 6〜9) への引継ぎに記録。 |
| A5 / B1 (cycle 優先順位の変更は不要) | real | 採用。`VerifyResult.verdict` は変えない (D2224「cycle は non-serializable として返す」を維持)。 |
| A6 (経路の実装条件) | real | 採用 (R5 の条件 4 つ)。 |
| A7 / B5 (変異の帰属・分割・等価正例) | real | 採用 (変異の事前登録)。 |
| B3 (完了条件 (c) は実装後の公開 API で) | real | 採用。親が実装後の木で `verify_trace_dir` を実 trace・protocol=silo・expected_commits=36156 で実行し certified=True を確認。repo 内の正負例・変異の代わりにはしない。 |
| B4 (後で削除された key の古い版の読み) | real | 採用 (試験に対を追加、変異 M11)。 |
| B6 (規模・試験の縮小) | 一部 real | 上限を採用 (production 300 行、試験 450 行、新規 test 関数 10 本以内)。詳細の決定的な並べ替えは残す (経路一致の不変条件 4 のため、V 件の sort は安い)。 |
| B7 (撤去の残骸 `is_v3`・`TxnV3` import・docstring) | real | 採用。使わなくなったものは削除。 |
| B8 (既存期待の変更は U 正常例だけ) | real | 採用 (限定表どおり)。 |

## R1 — 段 1 の初期存在 (P1) の契約と根拠

**規則:** (表, key) が genesis で存在する ⇔ その object の最初の committed write (版 = commit の (epoch, tid) 辞書順) が I でない。
一度も書かれない object の genesis 読みは存在する record の読み。

**根拠 (CCBench 現 pin e9e477ca の silo、親が確認):**
- 版 (1,0) を付けるのは初期ロード専用の `Tuple::init(thid, body, p)` だけ (`cc/silo/include/tuple.hh:40-47`、epoch=1・tid=0)。実行中の insert は
  epoch 0・absent・lock の record を作る (`:50-54`) ので、commit 前の record の版は (0,0)。実行中の commit が (1,0) 以下なら既存の genesis_commits で拒否。
  したがって「R が (1,0) を読んだ」は「初期ロードの record を読んだ」を意味する (trace の忠実さという既存前提の下で)。
- insert は key が木にあれば `WARN_ALREADY_EXISTS` で失敗する (`cc/silo/transaction.cc:74-80`、Masstree は編集面外)。absent な record への
  update は abort する (`:185-188`)。存在しない key の読みは read set に入らず R を出さない (相談 A2、`transaction.cc:230`, `:260`)。
  したがって「最初の committed write が I」は「その時点で木に無かった」を意味し、それより前に削除の committed write は無いので初期に無い。
- 残る穴 (限界として記録、認定を止める理由にしない): trace の行そのものの捏造・欠落 (既存の witness・framing が担う領分、D295 / D296 の限界と同型)。
  初期にある key への不正な I で、その初期版を誰も読まないもの — 辺を 1 本も変えないので直列化可能性の判定には影響しないが、insert の意味の検証にはならない。
  §4.3 の初期キー一覧 (単位 7) で段 2 に閉じる。
- 適用範囲: silo の版付け。mocc は単位 3 (並走 wave) で v3 emitter が載った時点で同じ 2 点 (初期版の値、insert の存在検査) を確かめる
  (本 wave では検査を足さない。insight の引継ぎに書く)。

brief の「§3.3 の規則で W 行から決める」は「§3.3 を、silo の版付けに裏付けられた段 1 の存在契約として実装する」に訂正する。

## R2 — 読みの違反 (P2)

R の**指定された版そのもの**の存在を見る。(a) genesis 版かつ初期不存在 → `read-unborn-genesis`、(b) producer があり op=D → `read-deleted-version`。
producer の無い非 genesis 版は既存 orphan_reads に任せ、新件数に数えない。R 行ごとに数える。

## R3 — 書きの連鎖 (P3)

版順で直前の状態 live に対し、I かつ live → `insert-on-live`、U かつ非 live → `update-on-absent`、D かつ非 live → `delete-on-absent`。
違反があっても op の事後状態 (I/U → 存在、D → 不存在) へ進む。

## R4 — 同一取引・同一 object・同一版の W 重複

同じ op の反復は 1 版。異なる op が混在する群は `ambiguous-write-version` を群ごとに 1 件とし、その object の P1〜P3 の派生診断を省く
(任意の op を選んで認定しないため)。

## R5 — 実装位置と条件

- dsg.py に v3 だけで動く共通の存在検査を 1 つ置き、object 入口 (`DSG.__init__` の `_build` 後) と compact 入口 (`DSG.from_compact` の `_build_compact` 後) の
  両方から呼ぶ。辺構築・worker・parse・report.py は触らない。v2 では adapter・map・sort・notes を一切動かさない。
- 条件: (1) compact の schema 判定は先頭 file だけを見ない (neutral file を許す既存 core と同じ判定)、(2) 表は key の token から取る
  (op token の表 -1 を使わない)、(3) winner 行だけを検査する、(4) worker・fallback の中では検査しない (親で 1 回)。
- version_dups > 0 または genesis_commits > 0 の run は存在検査を省き件数 0 (既存 integrity で indeterminate。この 0 を存在正常の証拠にしない)。
- 詳細は (txid, table, key, version, kind) の決定的な順に並べ、notes は先頭 5 件の見本。

## R6 — model / 出力

- `Integrity.existence_violations: int = 0`、`Integrity.existence_violation_details: Optional[List[ExistenceViolation]] = None`
  (None = v2 / 対象外、v3 の検査入口で [])。`ExistenceViolation` は model.py の frozen dataclass (txid, table, key, version, kind, ops)。
- `clean()` は `existence_violations == 0` を要求。`v3_existence_unverified` の field・clean 条件・core.py の設定と note を撤去。
  使わなくなった `is_v3` と `TxnV3` import も削除。
- `VerifyResult.verdict` は変更しない (存在違反だけ → indeterminate、cycle 併存 → non-serializable のまま、どちらも非認定)。
- report.py の `result_to_dict` は編集しない (旧 JSON では clean と notes だけに出る)。`core.result_to_dict_v3` は details が None でないときだけ
  integrity に `existence_violations` と `existence_violation_details` を足す。docstring を更新。
- note の文言: `<n> v3 existence violation(s) [<kind>×<k>, ...]: txn<t> table=<tb> key=<hex> ver=(<e>, <t>) kind=<kind>; ...` (見本 5 件)。

gate の禁止の署名と通る正例: 「v3 の run で、版 (1,0) の読みが、最初の committed write が I の (表, key) に向いていれば認定しない」。
通る正例: 同じ key を I の版 (2,1) で読む run は certified (他条件充足時)。

## R7 — 試験 (test_verifier.py だけ、新規 test file なし、T-2847 (1) の新規 file は触らない)

新規 test 関数 10 本以内・追加削除 450 行以内。最低限:
1. 負例 4 種 + 1 行修正の正例 (read-unborn-genesis、read-deleted-version、insert-on-live、update-on-absent / delete-on-absent)。各負例は cycle 無し・
   orphan 0・framing 0・X/P gate 充足・witness 一致で、`replace(ig, existence_violations=0).clean()` が真 (単一理由)。
2. 正常な履歴 (未書込み key の genesis 読み、最初が U の key の genesis 読み、I 版の読み、D→I→R(I 版)、**I@v1→D@v2 で R(v1) が certified、R(v2) が違反**) — データ表で。
3. 版順: txid / file 順と commit 順を逆転させた合法履歴、tid 優先・txid 順の誤実装で誤検出する形。
4. 表の分離: 表 5 の I と同じ hex の表 9 の genesis 読みは合法、R の表を 5 に直すと違反。
5. 同一取引の異種 op (I と D) → ambiguous-write-version 1 件、D を I に直すと certified。
6. 経路一致: 各違反種を含む代表 fixture を object / packed / tuple (workers 1 と 2)、既存の overflow (tuple 落ち・legacy 落ち) と実 worker 終了の fallback 試験に
   存在違反 fixture を足して件数・詳細・notes・verdict が一致。
7. 出力: result_to_dict_v3 の件数・詳細、旧 result_to_dict に新 key が無いこと、6 件以上で notes の見本 5 件、cycle 併存で non-serializable のまま件数が出ること。
8. 既存試験の書き換えは B8 の限定表だけ: `test_v3_existence_unverified_and_v2_control` を改名し、U 例は certified、I / D 例は非認定のまま新違反へ帰属、
   v2 の 3 例は certified・notes 空のまま。`test_v3_framing_and_neutral_files` の印参照は新件数 0 へ。`test_v3_serial_tables_types_and_ops` は存在件数 3・非認定を追加確認
   (serializable の純グラフ事実と辺数は維持)。他の既存期待値は変えない。

## R8 — 完了条件

(a) 上の負例が全経路で indeterminate・件数・詳細一致、(b) 1 行修正の正例が certified、(c) 実装後の木で実 trace が公開 API で certified
(親の probe、protocol=silo、ccbench_root=worktree の submodule (pin e9e477ca)、expected_commits=36156)、(d) 事前登録の非等価変異が全部 KILLED・等価変異 M0 が SURVIVED。

## 変異の事前登録 (実装後に照準・単一理由を確認、DW-M01)

| ID | 変異 | 期待 |
|---|---|---|
| M0 | 版の並べ替えを等価な key 指定 (`key=lambda v: (v[0], v[1])` 相当) に置換 | SURVIVED |
| M1 | 初期存在を常に真 (最初の I を見ない) | KILLED (read-unborn-genesis の負例) |
| M2 | D 版の読みの検査を外す | KILLED (read-deleted-version) |
| M3a / M3b / M3c | insert-on-live / update-on-absent / delete-on-absent の条件を個別に外す | 各 KILLED |
| M4 | D の後も live のまま | KILLED |
| M5 | clean() から existence_violations を外す | KILLED |
| M6 / M7 | object 入口 / compact 入口だけ検査を呼ばない | 各 KILLED |
| M8 | v2 にも検査を掛ける | KILLED (v2 対照) |
| M9 / M10 | 版順を (tid, epoch) / txid 順にする | 各 KILLED |
| M11 | 読みの判定を指定版でなくその key の最新 op で行う | KILLED (I→D で R(v1) の正例) |
| M12a / M12b | 異種 op 群を I / D に潰す | 各 KILLED |
| M13 | result_to_dict_v3 が詳細を出さない | KILLED |
| M14 | 存在検査の identity から表を落とす | KILLED (表の分離) |
