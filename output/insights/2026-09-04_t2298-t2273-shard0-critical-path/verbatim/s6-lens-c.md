## must-fix

1. **MF-1 — real: 実 fixture の reader / writer mode を実測検査が識別できない。**

   [現物:1496-1519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1496) は両 mode とも競合側に `LOCK_EX|LOCK_NB` を使っています。これは保持側が SH でも EX でも失敗するため、正しい mode の証明になりません。

   反例は [現物:1281-1284](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1281) を次のどちらかへ変えることです。

   - `access_mode="write"` 固定: 15 reader がすべて EX になっても実 fixture 検査は緑。
   - `access_mode="read"` 固定: M17/M18 が SH になっても同じ検査は緑。

   wrapper AST は [現物:1634-1651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1634) で外側 wrapper しか見ず、この中間配線変異を殺しません。helper 単体検査も直接 `_certified_evidence_lock_scope` を呼ぶため殺しません。

   実 reader scope では別 fd の SH 成功と EX-NB 失敗、実 writer scope では SH-NB 失敗を確認する必要があります。

   **放置時の成果物影響:** 受入が緑のまま reader 全直列化を再導入でき、逆方向では M17/M18 と reader が並走して certified evidence を一時破壊し、certified 選択や受入結果を不安定にします。

2. **MF-2 — real: 変異 g の検査は production seed の call edge を固定しておらず、SURVIVED が可能。**

   production の atomic publication は [現物:1279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1279) から helper を呼ぶことで成立します。一方、検査は [現物:1553-1585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1553) で helper を直接呼ぶだけです。

   再現反例: line 1279 を同じ JSON payload の `metadata_path.write_bytes(...)` に置換し、正しいが未使用になった helper を残すと、atomic metadata 検査はその helper を試して緑のままです。実 fixture 検査は seed が作った marker の原子性を観測していません。

   また検査は replace 元が metadata 自身でないことを確認していません。[現物:1578-1580](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1578) は同じ親と target だけを見るため、「metadata へ直接書込み・fsync・`os.replace(metadata_path, metadata_path)`」でも通ります。

   production seed が helper を通る AST/call-edge 検査を追加し、replace 元について `source != target` と temp 名を固定する必要があります。

   **放置時の成果物影響:** 非 transactional な ready marker を受入が緑のまま許し、worker 中断時に部分 JSON を次 worker が ready と誤認して certified fixture と受入結果を壊します。

## nit

- **real — `os.fdopen` 自体の例外では temp fd が閉じられません。** [現物:1197-1211](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1197) で `mkstemp` 後、`os.fdopen` が raise すると path は unlink されますが `temp_fd` は open のままです。`os.fdopen` を raise する mock で再現できます。lock fd ではなく通常条件では起きにくいため nit です。

- **real — M18 の最初の共有 evidence 変異が `try` の外です。** [現物:2154-2158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:2154) では `role_file.rename()` 後の `symlink_to()` が失敗すると復元 finally に入りません。次の worker は metadata があるため再 seed せず、欠損した role file を読むことになります。ただし起点の M18 自身が既に赤になるため、偽の受入緑ではなく失敗の連鎖・帰属悪化です。

- **real — writer 閉包 AST の taint は現行15 consumerには十分だが、一般的な直接 path 変異を見落とします。** [現物:1667-1684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1667) は `Path(x)` と `with_name()` は追いますが、`Path(evidence.on_layout.root) / "leaf"`、`joinpath()`、`resolve()`、`os.replace(..., evidence-derived-path)` は追いません。既存15本には該当書込みがないので現差分の blocker にはしません。

## 変異 a〜g の kill 可否表

| 変異 | 判定 | 実際に赤になる理由・帰属 |
|---|---|---|
| a: writer mode を SH | **KILL・単一** | [現物:1425-1442](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1425) の競合 SH が成功し、`pytest.raises` が失敗します。 |
| a2: writer wrapper が read を渡す | **KILL・単一** | [現物:1634-1651](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1634) の `wrapper_modes == fixture_modes` が失敗します。ただし中間 scope が mode を無視する変異は MF-1 のとおり SURVIVED。 |
| b: reader が本体 lock を取らない | **KILL・帰属非一意** | 先に [seeded no-EX:1388-1390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1388) の SH 存在 assertion、続いて [reader-blocks-writer:1399-1416](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1399) が赤になります。 |
| c: M17 writer 宣言を外す | **KILL** | reader fixture への一貫した置換なら [expected map:1591-1665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1591) だけが決定的に赤。引数だけを文字どおり削除する変異なら M17 自体も NameError となり帰属非一意です。 |
| c2: M18 writer 宣言を外す | **KILL** | c と同じ。整合した reader 置換は closure が殺しますが、引数だけの削除なら M18 自体の NameError も発生します。 |
| d: EX 後の double-check を外す | **KILL・単一** | [現物:1459-1493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1459) が EX 取得時に競合 marker を置くため、`seed.assert_not_called()` が失敗します。 |
| e: reader を EX のままにする | **KILL・帰属非一意** | [二 reader:1348-1364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1348) が先に競合例外で赤になり、[seeded no-EX:1367-1390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1367) も赤になります。 |
| f: unlock 後へ fixture yield を移す | **KILL・帰属非一意** | [実 scope:1496-1519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1496) が先に赤、[yield AST:1522-1550](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1522) も赤。内側 helper が unlock してから yield する変異では実 scope が殺し、AST は緑です。 |
| g: metadata を直接 write | **部分 KILL / SURVIVED あり** | helper 本体だけを単純な `write_bytes` に変える変異は [atomic test:1553-1585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1553) が単一理由で殺します。しかし production call site の直接 write、および direct-write + self-replace は MF-2 のとおり生存可能です。したがって現状の「登録する・単一」は成立しません。 |

## 総括

**lock 実装順序の食い違い — refuted。** 現物は契約順です。

1. fd open: [1223-1225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1223)
2. metadata 不在判定、EX: [1227-1230](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1227)
3. EX 後の再確認: line 1231
4. symlink/file/dir 残骸掃除: lines 1232-1236
5. seed: line 1237、現物定義は [1262-1279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1262)
6. temp 作成、write、flush、fsync、replace: [1197-1208](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1197)
7. 明示 UN: lines 1238-1239
8. reader SH / writer EX と取得: lines 1241-1246
9. metadata 読み: line 1286
10. patch: lines 1310-1315
11. yield は lock context 内: line 1316、外側 `with` は line 1281
12. finally unlock、close: lines 1248-1253

**EX→SH の直接変換 — refuted。** EX の後に line 1238 の `LOCK_UN` があり、SH/EX の本体取得は line 1245 です。

**指定された例外での lock/fd leak — refuted。** seed、metadata write、replace 前後の例外はいずれも [finally:1248-1253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1248) へ入り、lock fd は閉じられます。replace 前の temp は lines 1209-1211 で削除され、evidence 残骸は次 worker が lines 1232-1236 で除去します。SIGKILL で temp が残っても固有名であり、exact marker `evidence.json` ではないため次 seed を妨げません。`os.fdopen` 例外だけは nit の通常 fd leak があります。

**同じ open file description の誤使用 — refuted。** 競合側は `dup` ではなく毎回別 `os.open` です（[二 reader:1358](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1358)、[reader/writer 負例:1404,1430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1404)、[実 fixture:1507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1507)）。

**15 reader が共有 seed を書く疑い — refuted。** M01/M04と assembly は publication 側 artifact だけを書き、M02/M03/M05/M06/M07/M08/M10/M12/M13/M16、driver、non-guarantees は共有 evidence を変更しません。対象範囲は [M01開始:1804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:1804) から [reader末尾:2304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:2304) です。`_request` は純粋な dict 構築、`_publish` は producer への転送だけです（[780-803](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/test_p3_b4_raw_record_producer.py:780)）。共有 path の直接変異は M17 の receipt 書換え・復元と M18 の role file rename/symlink・復元だけです。

正例・負例9本自体はすべて存在しますが、実 fixture mode の識別は MF-1、atomic publication の production 経路は MF-2 が未固定です。したがって結論は、**lock 本体の実装は契約どおり、受入検査は2件 must-fix** です。read-only 指示に従い pytest は再実行していません。