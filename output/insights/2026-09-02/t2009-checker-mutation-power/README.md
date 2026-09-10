# 2026-09-02 [T-2009] 検査器の弱体化を挙動で捕まえられているか — D799 が「通す」と予測した 5 件は 1 件も生存しなかった

```
status: MEASURED
machine_effect: NONE        # 実装面の差分ゼロ。tracked file は 1 byte も変えていない。
                            # 機械受理集合・凍結 bytes・proof chain・certified 選択はいずれも不変
```

絶対規律 7 は「弱体化の検出は、同一性ではなく**挙動**で行う (変異テスト、正例・負例)」と定める。
その挙動検査に実際の検出力があるかは**未実測だった**。本 wave は検査器を骨抜きにする変異を
実際に書いて走らせ、既存テストが落ちるかを測った。

- **測定 commit**: `28ebff456b9f57a927854950b5030fa77aec6529`
- **道具**: `tools/mutation_worktree.py` + `tools/mutation_harness.py`
  (spec schema `izanagi-dev-wave-mutation-spec/v1`)、runner は
  `python3 tools/run_tests.py --force-dispatch`
- **走行**: probe (全件 SURVIVED 期待で観測 node を収集) → 本走 (観測 node を完全集合として
  KILLED 期待で再登録)。本走は **7/7 が期待と一致**、baseline は `PASSED` (失敗 0)
- **repo の tracked file は 1 byte も変えていない** (変異は固定 commit の使い捨て worktree 内のみ)
- 数値の正本は [mutation-matrix.md](mutation-matrix.md)

## 結論 (2 つ)

### 1. D799 が「通してしまう」と挙げた 5 件は、既存スイートでは 1 件も生存しない

D799 決定 (2) は、`g6_silo_serial_1thread` と `r8_silo_broken_norw` の緑赤対が排除するのは
**定数 verdict 実装 2 種だけ**であり、次の 5 つは「2 つとも通してしまう」と記録している。
本 wave はこの 5 つを変異として書き、**全件 KILLED になった**。

| 変異 | 機械結果 | 挙動 node | 受理集合の遷移 | 層 |
|---|---|---|---|---|
| 分類器が常に `G2` を返す | KILLED | 1 | **なし** | diagnostic |
| 版比較が epoch を無視する | KILLED | 2 | non-serializable → certified | semantic |
| 長さ 4 以上の巡回を無視する | KILLED | 1 | non-serializable → indeterminate | semantic (fail-open ではない) |
| framing violation を受理判定から外す | KILLED | 5 | indeterminate → certified | semantic |
| 入力の出所で答える | KILLED | 40 | corpus 外入力が certified | semantic |
| (正例対照) rw 反依存辺を落とす | KILLED | 19 | non-serializable → certified、receipt 発行可へ | semantic |
| (等価対照) `u != v` → `not (u == v)` | SURVIVED | 0 | なし | — |

**本測定の範囲において、規律 7 が挙動検査へ移したことで開いた穴は 0 件である。**

D799 の記述自体は誤りではない。あの 5 件は **`g6` / `r8` の対**の射程についての記述であって、
既存スイート全体の射程についての記述ではなかった。本測定はその区別を実測で確定した。
D799 を読んだ後続レビューが「スイートに 5 つの穴がある」と読むのは誤読である。

分類器の変異 (`_classify` が常に `G2`) だけは KILLED でも**穴ではない**。`_classify` は
`Anomaly.phenomenon` を作るだけで、受理判定は `total_cycles == 0` と `Integrity.clean()` で
決まる。落ちた 1 node (`test_classify_branches`) は診断分類の pin であり、`DW-M03` の
semantic kill ではない。

### 2. 同一性層は、検査器を骨抜きにする変異と、何も変えない変異を、まったく同じ 53 node で赤にする

これは狙って測ったものではなく、等価対照を置いたことで出た。

**`E1` は意味を一切変えない。** `if u != v:` を `if not (u == v):` に書き換えるだけで、
`u` / `v` は parser が作る整数 txid なので受理集合・グラフ・生成物は完全に同一である。
にもかかわらず、分母を絞らない probe 走で **53 node が赤になった**。理由はすべて同一だった。

```
orchestrator.campaign.ident.IdentityMismatch: contract-loader-drift:
disk bytes が記録 commit blob と不一致: orchestrator/verifier/dsg.py
```

`orchestrator/campaign/campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS` は verifier の
7 source file を HEAD blob で pin し、`ident.py:394` の `verify_live_contract_loader_binding`
が照合する。**この 53 node は、rw 反依存辺を落として検査器を壊す `P1` に対しても、
何も壊さない `E1` に対しても、同じ集合で赤になる。** `P1` の赤 72 件のうち 53 件 (74%) が
この層である。

**同一性検査が無意味だという意味ではない。** 規律 7 自身が、束縛・完全性・意味互換性の検査
としての同一性検査を明示的に許している。言えるのは 1 つだけである —
**同一性層の赤を「弱体化を検出した」と読んではならない。** 読めば、等価変異でも同じ赤が出る
以上、検出力を 74% 水増しすることになる。

## 台帳との食い違い (訂正が要る)

`orchestrator/tests/fixtures/README.md` の「対で何を殺すか (射程を誇張しない)」節は、
長さ 4 以上の巡回について **「どの fixture も担っていない」** と書いている。**これは誤りである。**

`r5_nonlatest_transitive` は長さ 4 の G2 witness を持つ (verifier 実走の出力)。

```
#1 G2 (len 4): T2 → T3 → T4 → T50 → T2
  T2 → T3  [ww]  ww key=000000000000000a (1,2)→(1,3)
  T3 → T4  [ww]  ww key=000000000000000a (1,3)→(1,4)
  T4 → T50 [rw]  rw key=000000000000000c read(1,0)→overwritten(1,9)
  T50 → T2 [rw]  rw key=000000000000000a read(1,1)→overwritten(1,2)
```

同節の「規模で買えない限界」の測定 (実 Silo prefix では witness 長は常に 2 か 3、
`tid <= 1000` まで上げても変わらない) は否定しない。対象が**実 emitter 由来 fixture に
限られていた**だけで、手製 fixture の `r5` が長さ 4 を担っている。

**ただし r5 が担うのはグラフ事実の検出までである。** r5 は `missing_txids=46` で integrity が
unclean なので、変異前は `non-serializable`、変異後は `indeterminate` になり、
**どちらも certified ではない**。「長さ 4 以上の巡回を無視する verifier が、clean な入力で
certified を出す」ことを示す負例は、現在の fixture 集合に無い。

## 分母の条件 — 呼んでいるかではなく、判定を使っているか

verifier を import する test file と、verifier の弱体化を検出する test file は一致しない。

- `test_campaign.py` の `_red_vr()` 経路 (5966 行) は、実 verifier を呼んだ**直後にその結果を
  捨てて**固定の赤オブジェクトへ差し替える。この経路は検出力を持たない。
- 同じ file の `_mock_pipeline_multipass` (8029-8034 行) は差し替えないので、`P1` を実際に
  捕まえた (`test_pipeline_extra_correctness_second_pass_red_aborts_with_workload_tag`)。
- 保存済み JSON を consumer として検査するだけの file (mocc 系など) は、source 変異では
  結果が変わらない。

**分母の条件は「実 verifier を呼ぶか」ではなく「その判定を使うか」である。**

## 静的レビューが 2 者そろって外した点 (near miss)

段 2 プランと段 3 レンズ A は、いずれも「contract-loader の同一性 pin は
`capture_/verify_live_contract_loader_binding` を通ったときだけ発火し、推奨分母はその経路を
通らないので該当 node は 0 件」と結論した。**呼び出し関係の追跡自体は正しかったが、結論は
実測で覆った** — 分母に入れた `test_campaign.py` と `test_s1_direct_comparison.py` が
まさにその経路を通り、53 node が発火した。

もし静的結論のまま `--deselect` を「不要」と決めていたら、`P1` の検出力を 72 node と
記録していた。実際の挙動検出は 19 node である。**冗長 gate の集合は推測せず、
等価変異を 1 件走らせて実測する。**

## この測定が言えないこと

- **D387 の範囲。** 同一権限主体による意図的な偽造は対象外である。本測定が測ったのは
  **事故的退行の検出力**に限る。スイートが与える入力を**すべて**記憶した変異は定義上通るが、
  それは意図的な構成であって事故ではない。
- **固定 commit・exact 分母での測定である。** 測定 commit `28ebff456` と現行 main の間に
  `orchestrator/` と `tools/` の差分は無い (実測) が、将来は別の値になりうる。
- **7 変異は網羅ではない。** D799 が挙げた 5 件 + 対照 2 件であり、検査器の壊れ方の全体を
  張っていない。生存 0 件は「この 5 つの壊れ方は捕まる」であって「どんな壊れ方も捕まる」ではない。
- **repo 内の挙動検査は、gate と検査を同じ主体が変更できる限り、意図的な弱体化への完全な
  防壁ではない** (規律 7、D387)。本測定はこの限界を縮めない。

## 塞がず裁定へ返す項目

本 wave は「穴が見つかっても塞がない」境界で走った。次は候補であって実装ではない。

1. **長さ 4 以上の巡回を clean な入力で捕まえる負例が無い。** `r5` は unclean なので
   `non-serializable → indeterminate` までしか動かない。密な txid を持つ clean な長さ 4
   fixture を足すかどうか。D799 却下案 (a) は「実 prefix を大きくしても買えない」ことを
   確定させており、足すなら手製になる。
2. **`orchestrator/tests/fixtures/README.md` の「どの fixture も担っていない」の訂正。**
   本 insight が現行挙動の一次資料、README は当時の設計意図の一次資料である。
   README は D799 決定 (2) に基づいて書かれているので、訂正は D799 の射程の記述にも触れる。
3. **等価変異を対照として常設するかどうか。** 今回は等価変異 1 件で 53 node の冗長 gate を
   実測できた。制度化は独立 2 例 (`DW-G03`) を満たしていないので、本 wave の方法として
   記録するに留める。

## 収録物

- [mutation-matrix.md](mutation-matrix.md) — 数値の正本。失敗 node の完全集合、
  冗長 gate の完全集合、注入実在の確認を含む
- [mutation-spec-real.json](mutation-spec-real.json) — 本走の変異 spec (sha256
  `1112651ebf939d79c0d17cfff621dc7e667fed8832115af3f559cb8a5f708661`)
- [brief.md](brief.md) — 段 1 brief (実測で覆った前提を含む。訂正は s4-adjudication.md)
- [s4-adjudication.md](s4-adjudication.md) — 段 4 裁定と事前登録 (結果を見る前の予測)
- [verbatim/s2-plan.md](verbatim/s2-plan.md)、[verbatim/s3-lensA.md](verbatim/s3-lensA.md)、
  [verbatim/s3-lensB.md](verbatim/s3-lensB.md) — 子の出力逐語
