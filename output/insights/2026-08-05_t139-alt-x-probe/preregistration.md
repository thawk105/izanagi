# [T-139] 代替 X probe 再走 — 事前登録 (2026-08-05、実走前に commit する)

```text
authority: none
default_effect: no-state-change
study_label: engineering_screen / J=1 / uncalibrated / nonqualification
```

本書は **走行前に凍結する事前登録**である。可変状態の正本は `docs/worklog.md` 末尾、採用済み判断の
正本は `docs/decisions.md` であり、本書は当該 probe 1 本の設計を実走前に固定するためだけに存在する。
**結果を見てから本書を書き換えてはならない** (D126 決定 (4))。書き換えたら別 study である。

本書は適格性 (qualification) の主張ではない。D162 決定 (1)(3) のとおり producer は適格性を宣言できず、
権威は独立 validator だけが持つ。本 probe は validator を持たず、J=1 かつ未較正であるため、
`study_label` のとおり **engineering screen** にすぎない。

## 1. 何を確かめるか

劣化版 (mode1) に対し、回復候補 (modeX) が **部分回復するかどうかの生死確認**である。
D126 が記録したとおり、前候補 (2 stripe・padding 無し・key 全 byte 走査) は W2 で mode1 を
下回って**不成立**であった。本 study はユーザー裁定 [T-139] 択 (a) に従い、
**O(1) stripe 計算と cache line padding を備えた候補**で再走する。

## 2. 候補の同一性 (bytes で凍結)

- **modeX** = stripe 数 **4**、各 stripe の `std::mutex` を `alignas(64)` の wrapper で
  cache line 分離、stripe は **先頭窓・中央窓・末尾窓 (各 8 byte まで) + key 長 + storage** を
  固定回数の `memcpy` で読み、splitmix64 相当の finalizer を通して 4 で割った剰余とする。
  **per-byte loop を持たない。** record の address を使わず、`(storage, key)` の値だけから決まる
  安定写像である。
- **mode1** = 単一の大域 mutex (劣化版)。**stock** = 無改変。
- 3 arm 以外を足さない。
- mutex 枝の CAS は stock と同一 lvalue・同一 `expected` / `desired`・同一式であり、
  **stock loop の 1 iteration あたりちょうど 1 回**である。追加 CAS を置かず、動的再試行回数は
  stock と同じ。mutex 保持者は record lock を待たず、同時に 2 つ以上の stripe mutex を保持しない。

### stripe 分布の事前登録値 (login node で実測済み、4 stripe)

| key 族 | 最大 bucket 占有率 |
|---|---|
| YCSB 8 byte big-endian (100,000 件) | 25.06% |
| 共通 prefix + 共通 suffix・同一長の可変長 (90,000 件) | 27.10% |
| TPCC 相当 16 byte binary (100,000 件) | 25.71% |

末尾窓だけ、あるいは先頭窓と末尾窓だけの mixer は、共通 prefix と共通 suffix を持つ同一長の族で
**100% が 1 stripe へ退化する**ことを実測した。中央窓は必須である。

## 3. 測定構成 (凍結)

- 環境: Pegasus 計算ノード (gen_S)、48 thread、trace 無効。
- workload は 2 種を逐語で固定する。W1 = 高競合 write、W2 = 中競合 mixed。
  引数は driver 内の定義を正とし、実行時に変更しない。
- rep = 5、性能 run = 30 (2 workload × 3 arm × 5 rep)。
- **実行順序は固定 balanced schedule**とし、実行時乱数を使わない。両 workload 共通:

```
r1: stock  mode1  modeX
r2: mode1  modeX  stock
r3: modeX  stock  mode1
r4: stock  modeX  mode1
r5: modeX  mode1  stock
```

- liveness は `ADD_ANALYSIS` 有効の**別 build・別 run**で測る (規律 1)。性能計測 build には
  検証専用のものを残さない。liveness の 2 窓の定義は §4 の受理条件 2 を正とする。

### study identity の固定方法 (自己参照を避ける)

本書は自分自身の hash を書かない (F36)。凍結値は**投入前に別ファイルとして発行する
submission receipt** に置く。receipt は qsub より前に作り、少なくとも次を含める。

- 期待 commit (この commit を qsub 時に env で job へ渡し、job 側で HEAD と照合する)
- probe 3 file の sha256、`tools/pegasus/policy.json` の sha256、本書の repo 相対 path
- CCBench の pin、gflags / glog の root と pin、third-party 3 本の root と pin
- 上記 6 source それぞれの **tree SHA** (pin から導いた snapshot の同一性)
- submission ID (発行後に追記する)

**receipt は append-only とし、結果を見る前に全 submission を記録する。**

## 4. 受理条件 (primary)

各 workload について、**全標本が厳密に分離**すること。等値は不受理。

```
max(mode1) < min(modeX)   かつ   max(modeX) < min(stock)
```

**両 workload の同時成立**を要求する (連言 1 本の主張)。加えて次がすべて揃うこと。

1. 性能 row が exactly 30 行で、workload・arm・rep が事前登録どおり exact-one。
2. liveness が **2 つの非重複時間窓 × 48 worker × 3 arm × 2 workload = 576 セル**すべて成立。
   窓は **全 worker が共有する単一の起点** — 走行開始 barrier の解放後、いずれかの worker が
   最初に transaction 開始点へ到達した時刻 — から測り、**`[0, 1500ms)` と `[1500ms, 3000ms)`**
   の 2 つとする。**3000ms 以後は marker を出さない。**
   起点は成功 commit ではないので、初回 commit 後に飢餓した worker を検出できる。
3. build identity が実 compile database から exact に検査されること。性能 build は
   trace 無効かつ分析 counter 無効、liveness build は trace 無効かつ分析 counter 有効。
   検査対象は `transaction.cc` に加え、分析 counter が layout を変える共有 source
   (`result.cc` / `util.cc`) を含む。
4. **nm による補助検査**が通ること — 全 binary で trace 由来 symbol が 0 件であり、
   mutex 大域が stock に無く mode1 / modeX にあること。これは compile 検査の補助であって
   単独の権威ではない。
5. 依存 (CCBench・gflags・glog・third-party 3 本) が pin 一致・clean で、
   **Git object から作った不変 snapshot** から build されたこと。
6. 限定 screen 36/36 が記録されていること。

**限定 screen は単独性 (exclusivity) の証拠ではない。** 割当ノードの専有は主張しない。

## 5. 副次診断 (記録するが判定に使わない)

各 run の attempt rate と abort rate。**verdict には接続しない。**
機序の帰属には使わない (D126 決定 (5) を維持)。

## 6. 失敗の閉表 (D134 / T-338 Q8)

1. **exact verdict (true / false) が出た** → 終端。**retry 禁止。** true も false も科学的完了である。
2. **correctness / liveness 異常** → 候補の**終端 reject**。削除も置換もしない (規律 2)。
3. **性能 run 開始前**の build 失敗・依存検査失敗・限定 screen 違反・timeout → infra failure。
   結果を見る前に外部証拠で確定した場合に限り、**予備 1 本まで**置換投入してよい。
4. **性能 run 開始後**の timeout・失敗 → reject または判定不能。置換しない。
5. probe の bytes を変えたら**新しい study** (新 hash) とする。旧 submission も全件報告する。
6. **全 submission ID を報告し、不成立の job を省かない。**

## 7. 走行後の分岐 (事前登録)

- **pass** → この exact bytes を、RF 統計設計 (推定量・最小識別幅・floor・独立単位・標本数・
  帰無分布・多重比較・欠測・区間・事前登録方式・gate 実体化の 11 問) に準拠した後続 study の
  候補として送るだけとする。適格性・正例成立・cluster 間再現性はいずれも主張しない。
- **false** → **この exact 候補は終端不成立**とする。別候補は事前登録を伴う新しい wave で行う。
- **判定不能** → 候補の状態は不変とする。

## 8. 本書が主張しないこと

- 「正例 artifact ができた」— できない。本 study は J=1 の engineering screen である。
- 「代替 X は成立した / cluster 間で再現する」— J=1 からは言えない。
- 「回復の機序は padding である / stripe 計算である」— 本 study は 3 つの変更を同時に行うため
  機序の帰属はできない。ablation は別 study である。
- レコード数は未較正であり、この観測を性能比較・headline・calibration・floor の入力にしない。
