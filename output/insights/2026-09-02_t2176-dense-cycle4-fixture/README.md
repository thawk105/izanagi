# [T-2176] clean な入力で長さ 4 の巡回を捕まえる負例 — 2026-09-02

裁定は D1455。実装 commit は `dd43f92e2cc277d2f3d9ae9dbe8a60c3221f9c32`
(branch `worktree-dev-wave-t2176-dense-cycle4-fixture`)。

## 何が穴だったか

verifier の判定は 2 軸ある。`serializable` は DSG が非巡回かというグラフ事実、
`certified` は「それを安全に信用してよいか」で、integrity が unclean なら
`indeterminate` へ倒れて certified にならない。

wave 開始時点で、**clean な入力で長さ 4 以上の巡回を捕まえる負例が 1 つも無かった**。
既存 fixture 18 件を全て verify した実測は次のとおり。

- 長さ 4 の anomaly を持つのは `r5_nonlatest_transitive` だけ。ただし `missing_txids=46` で
  `integrity.clean()` は偽。
- clean な fixture の最長巡回は `r3_cycle3` の 3。

したがって「長さ 4 以上の巡回を無視する」変異を当てても、r5 は
`non-serializable → indeterminate` までしか動かない。**certified へ誤って倒れる経路を
殺せていなかった。** D799 が「実 prefix を大きくしても長さ 4 は買えない」を確定させていたので、
残る経路は手製 fixture だけだった。

## 足したもの

`orchestrator/tests/fixtures/r9_dense_cycle4/` — txid 0..3 が密で integrity が完全に clean、
`wr` 3 本 + `rw` 1 本の長さ 4 の単一 cycle だけを持つ手製 trace。

```
T0 --wr--> T1 --wr--> T2 --wr--> T3 --rw--> T0
```

各 key の実版は 1 個だけなので `ww` 辺は 0 本、chord も無く、長さ 2・3 の巡回は生じない。
4 本目の `rw` は T3 の genesis 読み (`R 3 <key> 1 0`) で作る。producer 不在かつ
`rv == GENESIS` なので orphan にはならず、直後版 (T0 の `(1,1)`) へ anti-dependency が張られる。

**2 thread 構成にした理由。** 段 2 のプラン子が親の 1 file 案を却下した。1 file = 1 thread は
逐次実行を意味し、「T3 が genesis を読んだまま、その間に T0→T1→T2 が commit し、最後に T3 が
commit する」という実行を表せない。1 file に押し込むと非物理な trace になる。

テストは `orchestrator/tests/test_verifier.py::test_dense_cycle4_clean_g2`。
`certified` を直接 assert し、加えて `abort_reasons == {}` と
`(txid, thid, commit)` の 4 組を pin する。

## この負例が効くことの証拠

`mutation-matrix.md` が正本。要点だけ書くと、

- 「clean な入力の長さ 4 以上の巡回を落とす」変異 (M2) は、**変更前の木では SURVIVED**。
  verifier を参照する 17 file・1562 node のどれも赤にならなかった。
- **変更後の木では KILLED**。赤くなったのは新テスト 1 件だけ。
- 挙動を変えない等価変異 (M3) では新テストは赤にならない。恒真な assert ではない。

## 副産物 — 同一性層は「壊した変異」と「何も変えない変異」を区別しない

`dsg.py` を 1 byte でも変えると `CONTRACT_LOADER_RELATIVE_PATHS` の HEAD blob 束縛が発火し、
分母 1562 node のうち **97 node** が `contract-loader-drift` で赤になる。等価変異 M3 でも
同じ 97 node が赤になり、M1・M2 の失敗集合はこの 97 を部分集合として含む。

絶対規律 7 が「弱体化の検出は同一性でなく挙動で行う」と定める理由の実物である。
D1422 / worklog 1176 が別の分母 (53 node) で測った現象を、本 wave が別の分母で再現した。
本 wave の変異走ではこの 97 node を根拠付きで deselect している。

## 意図的に塞がなかったもの

- **file 名と `thid` の対応。** T3 の frame を `trace_0.log` へ移して `trace_1.log` を空にする改変は、
  `(txid, thid, commit)` の pin では捕まらない。`_V2_FIXTURE_FILES` が `trace_1.log` の実在を
  pin することで部分的に塞がるだけである。専用の検査器は新設しなかった。
- **`fixtures/README.md` の「長さ 4 以上の巡回を無視する (どの fixture も担っていない)」の記述。**
  この訂正は D1466 が別に裁定しており、「r5 が担うのはグラフ事実の検出までで certified への遷移は
  担っていない」区別を落とさずに書くことを求めている。本 wave は表へ r9 の行を足すだけにした。
- **downstream の層。** verifier が誤って `certified=True` を発行した場合、campaign pipeline・
  commit receipt・artifact admission・oracle driver / report・層 3 report はいずれも DSG を
  再計算せずその値を運ぶ。同じ壊れ方は全層を通過する。段 3 の検査 B が file:line で示した
  (`verbatim/s3-lensB.md` 所見 4)。本 wave の scope 外として裁定へ返した。

## 収録物

- `brief.md` — 段 1 brief (親の実測を含む)
- `s4-ruling.md` — 段 4 裁定 (所見の real/refuted、変異事前登録)
- `mutation-matrix.md` — 変異 matrix の正本
- `mutation-before.json` / `mutation-after.json` — 変異 spec
- `verbatim/` — 子の出力逐語 (段 2 プラン、段 3 検査 2 本、段 5 実装、段 6 レビュー 2 本)
