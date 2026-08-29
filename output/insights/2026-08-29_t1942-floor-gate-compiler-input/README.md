# [T-1942] 床値実測の投入前ゲート実測 — compiler input の赤は無条件である

- 日付: 2026-08-29 (JST)
- 対象 commit: `d03855e92` (main tip、worktree `worktree-dev-wave-t1942-floor-gate-probe`)
- 目的: T-1942 (現行 Pegasus 環境・workload 別 between-block 床値の実測) の投入直前ゲートとして、
  [T-2027] / [T-2043] が報告している s8b compiler input の赤が解消しているかを実測する。
- 結論: **解消していない。** さらに、従来の理解 (cache hit のときだけ落ちる) は狭く、
  **主経路は cache が空の初回実行でも落ちる**。ユーザー指示の停止条件が成立したため、
  実装差分ゼロで停止し、床値の測定・凍結・投入は行っていない。

---

## 1. 何を測ったか

| # | 測ったこと | 結果 |
|---|---|---|
| 1 | 現行 main に D1192 の是正が入っているか | **入っていない** |
| 2 | 現行 main のコードで赤が再現するか | **再現した** (同一エラー本文) |
| 3 | 赤を起こしている入力は何か | **588 件中 38 件**が 1 回かぎりで消える場所の絶対 path |
| 4 | 赤は cache hit 条件か、無条件か | **無条件** (cold cache でも落ちる) |
| 5 | 赤を導入した変更はどれか | **`0bc33ba8f`** (2026-08-27 06:19) |

---

## 2. コードの現状 (測定 1)

`orchestrator/campaign/s8b_compiler_input.py` の最終変更は
`0bc33ba8f3ef1d01431da958d67eee3956592ccf` (2026-08-27 06:19:25 +0900)。
D1192 が定めた「根の分類と根からの相対 path を持たせ、使用時に現在の canonical base へ
束縛し直す」に対応する実装は、**現行 main には無い**。
(同日の別 wave の実測によれば、これを実装した branch 自体は存在するが main の祖先ではない
— worklog エントリ 1088。「どこにも実装が無い」ではなく「まだ land していない」である。
新規に書き起こす前に、その branch の現況を必ず確かめること。)
`_external_entry()` は依然として

- 絶対 path をそのまま manifest へ保存し (`s8b_compiler_input.py:427-455`)、
- 検証時に `resolve(strict=True)` で厳格に再解決する (`s8b_compiler_input.py:435`)、
- 解決できなければ `external compiler input is unavailable` を送出する (`s8b_compiler_input.py:438`)

形のままである。

## 3. 赤の再現 (測定 2)

落ちた job `952631` が残した build cache entry

```
/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1981-holdout-oneshot-removal/mainprobe/
  output/s8b-build-cache/contracts/
  e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01/
  87aa2e6a61d85ef61b1ba88616bb19c39b5dfe49030f6f78fdc68175102d5c94/completion.json
```

の `compiler_input_manifest` を、現行 main の
`s8b_compiler_input.validate_compiler_input_manifest()` へそのまま通した。

- `manifest_sha256` = `4f072a8975823229cb61912fbde19493af40fd2fa5ffbbc5afc6dc0f337284cf`
- 送出された例外 = `CompilerInputError: external compiler input is unavailable`

これは job `952615` / `952631` を止めたエラー本文
(`binary admission receipt を発行できない: compiler input manifest の完全検証に失敗:
external compiler input is unavailable`) の内側と同一である。

probe は repo 外 (背景 job の一時領域) に置き、repo へは入れていない。
測定は login node 上の read-only 検査だけで、build も benchmark も qsub も行っていない。

## 4. 塞いでいる実体 (測定 3)

manifest は 588 件の入力を記録する。現時点で実在するか否かで分けると次のとおり。

| 置き場 | 件数 | 現存 |
|---|---|---|
| `/usr/include` | 415 | あり |
| `/usr/lib` | 96 | あり |
| snapshot 相対 path | 39 | (snapshot 基準で解決) |
| **build cache の作業用 directory** | **31** | **なし** |
| **job 専用作業領域** | **7** | **なし** |

消えている 38 件は、根が 2 種類ある。

1. **build cache の作業用 directory (31 件)**
   `…/contracts/<contract>/.staging-<PID>-<nonce>/_deps/masstree-src/*.hh`
   — `<PID>` は build を実行した process の ID、`<nonce>` は乱数。
2. **job 専用作業領域 (7 件)**
   `/scr/0_952631.nqsv/gflags-install/include/gflags/{gflags,gflags_declare,gflags_gflags}.h`
   `/scr/0_952631.nqsv/glog-install/include/glog/{export,log_severity,logging,vlog_is_on}.h`
   — **path に PBS の job 番号が埋め込まれている。**

どちらも「その 1 回の実行のためだけに作られ、実行ごとに別の名前になる」場所である。
したがって記録された絶対 path は、**別の実行からは原理的に再解決できない。**

## 5. 無条件に落ちること (測定 4 — 本稿の中心)

`orchestrator/campaign/buildcache.py` の v2 publish 手順を読むと、次の順で進む。

| 行 | 何をするか |
|---|---|
| `buildcache.py:2508` | 作業用 directory 名を `.staging-<PID>-<nonce>` として作る |
| `buildcache.py:2690-2699` | いま作った `compiler_input_manifest` を `completion` へ書き込む |
| `buildcache.py:2709` | `completion.json` を fsync して確定する |
| `buildcache.py:2712` | **`_discard_build_dir(staging)` — 作業用 directory を破棄する** |
| `buildcache.py:2722` | 清書済み entry を最終保存先へ `os.rename` して publish する |

つまり **manifest が指している 31 件の header は、`build_v2` が戻る前に、その build 自身によって
削除される。**

一方 `orchestrator/campaign/s8b_floor_campaign.py:4282-4384` は、`_invoke_build()` が戻った **後で**
`issue_binary_admission_receipt(... compiler_input_manifest=...)` を呼ぶ。その内側の
`s8b_compiler_input.py:632-639` は、記録された入力を 1 件ずつ
`_compiler_input_entry` → `_external_entry` → `resolve(strict=True)` に掛け直す。

**よって cache が空の初回実行でも、受領書の発行は必ず失敗する。**
これは推論だけではなく実測とも整合する — job `952631` は
`source_root = /scr/0_952631.nqsv/izanagi_wt__vugck6x/wt` で自前の新規 build を行い、
自分自身の `.staging-2092533-79aabeed6c1584d75a7e167d1a539d09/` を manifest に記録したうえで、
同じ段で落ちている。

**D1192 の前提「base が消えた後の cache hit で落ちる」は、この点で狭い。**
実際には run 間の cache 再利用の有無にかかわらず落ちる。

## 6. 赤を導入した変更 (測定 5)

`_external_entry`（`resolve(strict=True)` を持つ関数そのもの）は `0bc33ba8f` が**新規に追加**した。
同 commit は、それ以前の「manifest は snapshot 相対 path だけを持つ」形を
「snapshot の外は正規化した絶対 path + hash で持つ」形へ変えている。

時刻を並べると次のようになる。

| 時刻 (JST, 2026-08-27) | 出来事 |
|---|---|
| 05:54 | job `951456` — **この段を通過**し 350 秒地点の予約段まで到達 |
| **06:19** | **`0bc33ba8f` が `_external_entry` を導入** |
| 11:17 | `b215f1a27` (T-2043 が「原因ではない」と実測済み) |
| 14:02 | job `952615` / `952631` — **binary admission receipt 発行段で落ちる** |

T-2043 が「当日中に環境か main が変わった」と書いて未特定のまま残していた変更は、
**`0bc33ba8f`** である。環境の変化ではなく main の変化であった。

## 7. [T-2027] の実装者への申し送り (裁定事項)

D1192 の裁定文が名指ししている根は **build cache 側の 1 クラスだけ**である
(「job-local な FetchContent base 配下の絶対 path」「31 件実測した」)。
本稿の測定が示すとおり、消える根は **2 クラス**ある。

- 裁定文が捉えている 31 件 = build cache の `.staging-<PID>-<nonce>/_deps/…`
- 裁定文が捉えていない 7 件 = job 専用作業領域 `/scr/0_<jobid>.nqsv/{gflags,glog}-install/include/…`

**裁定文どおりに 1 クラスだけ根相対化しても、主経路は 7 件の方で赤のまま残る。**
射程を 2 クラスへ広げるかは裁定事項なので、実装せずユーザーへ返す。

なお D1192 が「run 間の cache 再利用を失う」という理由で却下した代替案
(base の絶対 path を cache identity へ入れて必ず fresh build にする) は、
**そもそも cold cache でも落ちるという本稿の測定の下では、赤を直さない。**
却下理由そのものは変わらないが、「これで直る候補ではない」点は追加の事実である。

## 7.5 別 wave による独立の裏付け (worklog エントリ 1088)

本稿の受入全走の最中に、別 wave ([T-1981]、branch `worktree-dev-wave-t1981-consumed-cell-remeasure`)
が同じ塞ぎ要因を独立に実測して land した。**数値は完全に一致する。**

| 項目 | 本稿 | エントリ 1088 |
|---|---|---|
| manifest の入力総数 | 588 | 588 |
| 現時点で解決できない件数 | 38 | 38 |
| job 作業領域の gflags/glog header | 7 | 7 |
| staging 配下の FetchContent masstree source | 31 | 31 |
| 同一 job 内で必ず消えるか | 消える | 消える |

**独立した 2 回の測定が一致したので、この事実の確度は 1 例より高い。**
一方で、本稿だけが持つ点が 3 つある。

1. 赤を導入した commit が `0bc33ba8f` であることの特定 (§6)。
2. **D1192 の裁定文が根を 1 クラスしか名指ししていない**という射程の問題と、
   そのままでは主経路が赤のまま残るという帰結 (§7)。
3. D1192 が却下した代替案が、赤が無条件である以上そもそも赤を直さないこと (§7)。

D1192 の「同じ赤を報告している別 wave の項目とは、選択肢集合を照合するまで 1 件へ束ねない」に従い、
本稿とエントリ 1088 は**束ねない**。相互参照に留める。

## 8. 本稿がしていないこと

- 床値の測定・判定規則の凍結・反復数の凍結・campaign の投入は**一切行っていない**。
  凍結はゲートが緑だった場合の条件付き手順だったため、条件不成立で実行していない。
- 実 job の投入 (qsub) は行っていない。ノードの単独性確認も、計測を行わないため不要である。
- 実装面 (コード・テスト・実行可能 probe の repo 内設置) の差分はゼロである。

## 9. 副次的に判明したこと

- `tools/pegasus/submit_floor.sh` は `output/` 以外に untracked path が 1 件でもあると
  投入を中止する。現行の main checkout はこの条件を満たさないため、実投入は clean な
  worktree から行う必要がある。
- 床値 build cache の実体は `<repo>/output/s8b-build-cache` で、checkout ごとに独立である。
  main checkout には存在しない。
