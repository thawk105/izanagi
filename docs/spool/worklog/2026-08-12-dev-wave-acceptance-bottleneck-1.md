---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-acceptance-bottleneck
seq: 1
title: 受入全走の床は「配置」でなく copy 検出 1 オプションだった — 受理集合不変のまま鎖 176.7→152.0 秒、wall 196.5→161.2 秒 (コード + docs、branch worktree-dev-wave-acceptance-bottleneck)
---

## 本文

ユーザー依頼「受入全走のボトルネックを特定し、それを改善してください。並列化やより賢い仕組みで」の wave。

**結論から言うと、並列化・シャーディングは答えではなかった。受入は既にスケジュール下界に
張り付いており、律速は鎖の中身そのものだった。**

**ボトルネックの同定 (現 main a70a5acd、48 worker、非受入形の junit 全走)。**
直列総和 4631.9 秒に対し、`@real-repo` group の直列鎖が **176.7 秒**。
親のスケジュールシミュレーションでは現状順 202.6 秒 / LPT 176.7 秒 / 下界 176.7 秒であり、
**並べ替えで取れる余地はゼロ**である。鎖の内訳は
`test_cli_subprocess_returns_rc_2_on_gate_refused` が **88.27 秒 (鎖の 50%)**、
以下 21.6 / 21.3 / 15.2 / 14.8 秒の 4 本で計 72.8 秒、残り 39 本で 15.6 秒。
group 外の単体最長は `test_verify_replays_complete_fake_codex_experiment` の 152.11 秒。

**[T-813] の既裁定 (シャーディングは受理集合を保てないため不採用、順序は M0 → M5 → 再評価) に
従い、本 wave は M5 = 「遅いテストの是正で下界を下げる」lane を担当した。**

**cProfile 実測 (計算ノード、repo 外 probe)。**
88 秒テストの中身は `verify_receipt` 55.2 秒 = `inspect_receipt_history` 30.1 秒
(`_batched_history_touches_path` の diff-tree が 28.0 秒、descendant 2,460) +
`_verify_holdout_live_scan` 24.3 秒。152 秒テストは `verify_snapshot` 47 呼 108.2 秒 =
git subprocess 2,554 本 (poll 75.0 秒) + `_filesystem_file_set` 94 呼 60.0 秒。

**最大の発見: diff-tree 20.27 秒のうち 17.9 秒 (88%) は copy 検出 `-C` 1 オプションだった。**
argv 別実測は `-C` 抜き 2.37 秒 / `-M -C` 抜き 0.93 秒 / pathspec 限定 0.24 秒。

**等価性の要件は「各検査の一致」ではなく「論理和の不変」である。**
`inspect_receipt_history` の 3 検査 (状態 OID / mode・kind / diff-tree) はいずれも同一の
refusal `receipt.history_mutated` を `_append_refusal` の dedup 付きで積み、
`issued_but_missing` も同じ値にする。この観点で `-C` 除去の差分は 2 形に限られ、
(i) receipt を source とする copy は destination OID clause が吸収、
(ii) receipt を destination とする copy は親が descendant なら状態検査が吸収するので、
**残る差は「外部辺を跨ぐ copy-into-receipt」1 形のみ**である。よって外部辺 commit だけを
現行 `-M -C` 付き command へ回し、論理和を返す。**command 形・parser・`--always` framing・
fail-closed の例外種別・refusal 文字列はすべて不変。** 旧挙動は `detect_copies=True` として
残し paired oracle に使う。実履歴 descendant 2,460 の対検証では両 clause の発火集合が完全一致
(いずれも空) で、外部辺 commit は現 repo に **0 件**。

**段 3 の敵対 2 レンズが親の当初設計を BLOCKER 5 件で潰した。親が自分で実測して確認した 2 件が決定打。**

- `git log --find-object` と `--pickaxe-all` は git 2.34.1 で**相互排他** (`fatal: ...
  mutually exclusive`)。段 2 プランの W1 設計は**そもそも実行不能**だった。
- `git hash-object` へ `--` を足すと leading-dash path の受理集合が変わる
  (現行 `-answer` は `error: unknown switch` で拒否、`-- -answer` は OID を返して受理)。
  sol と luna が独立に同じ穴を指摘した。よって **git 呼び出しの batch 化は全面不採用**。
  削減見込みも約 1.8 秒にすぎず、attribution も誤っていた。

**親自身の誤りを 6 件撤回した。** (i) find-object 2 本組で被覆できる / (ii) git batch は等価 /
(iii) 効果見積りの帰属 (twins「2 本 87.6 秒」は各 87.6 秒の取り違え、同 tip の親計測 196.5 秒と
brief の 177〜181 秒の不一致) / (iv) micro-probe の argv 取り違え (測ったのは提案 argv ではない) /
(v)「+5%/日 → 19 日で倍」の増加モデル未定義 / (vi) 段 4 で sol の TOCTOU 所見へ「(a) は走査構造を
変えないので非該当」と答えたが、走査構造は不変でも **resolve の呼び出し回数を変えていた**。

**段 6 で luna が BLOCKER 1 件を出し、採用した。** `_filesystem_file_set` の memo が
lexical 親ごとに `resolve()` の呼び出し自体を省いていたため、「同じ親の 1 件目は成功、
2 件目で transient OSError」で現行なら出る例外が出なくなっていた。段 4 裁定が
「例外面を一切変えない」と約束していたので**約束の側を守り**、`resolve()` は毎回呼んで
判定だけを memo する形へ縮小した。profile 上 `resolve()` 側 16.7 秒は取り戻せず判定側 18.1 秒
だけが残る。**速度のために例外面を変えない取引として意図的に選んだ。**

**焦点走で赤 1 件。production の欠陥ではなくテスト側の誤りだった。**
`pathlib._NormalAccessor.scandir = os.scandir` は **class 生成時に束縛**されるため、
`monkeypatch.setattr(os, "scandir", ...)` は `Path.rglob` に届かない。模擬が一度も発火せず、
参照実装側の assert が落ちていた。実 `chmod(000)` へ置き換え、拒否が本当に効いたことを
確かめてから本題に入る形にした (root では素通りするので黙って緑にせず理由付き skip)。

**成果 (同形の全走 2 本、いずれも計算ノード dispatch、非受入形 `-q --junitxml`)。**

| 指標 | before (a70a5acd) | after (be5018eb) | 変化 |
|---|---|---|---|
| pytest wall | 196.5 秒 | **161.2 秒** | -18.0% |
| `@real-repo` 鎖 (床) | 176.7 秒 | **152.0 秒** | -14.0% |
| 直列総和 | 4631.9 秒 | 4110.4 秒 | -11.3% |
| 結果 | 0 failed | 9305 passed / 0 failed / 31 skipped | — |

node 別では `test_cli_subprocess_returns_rc_2_on_gate_refused` が **88.27 → 47.38 秒 (-46%)**、
holdout twins が各 87.6 → 61.7 秒 (-30%)、file 単位では `test_s8b_oracle_driver` が
**1034.1 → 596.6 秒 (-437.5 秒)**、`test_s8b_holdout_freeze` が 176.8 → 124.7 秒。
`test_codex_reasoning_ab` は 1379.6 → 1330.8 秒で、**新設テスト 7 本を足したうえでの -48.8 秒**。

**触っていない file に +77.3 秒の悪化が出たが、帰属は本 wave ではない。**
`test_campaign_import_invariant` は worker ごとに約 40 秒の同じ構築を重複して払う構造で、
**payer が 4 worker (計 161.8 秒) から 6 worker (計 239.2 秒) へ増えた**だけである
(単価は 41.96→41.21 / 39.85→39.44 秒などで不変)。テスト所要が変われば xdist の割り当ても
変わるため、この重複コストは走行ごとに揺れる。460 が記録した per-worker 重複構築の同型であり、
**再提示可になった [T-887] (限定 group 化) の実証データになる**。

**裁定パッケージ 3 件を返す (実装しない)。** 詳細は下記「次の一手」。
最大の残件は `s8b_holdout_freeze.search_repository` の live scan 24.3 秒
(11,988 file に re.search 107,721 回) で、`holdout_freeze.json` の generator pin と
T-080 receipt の `metadata_fields` が**現行 worktree bytes と live 照合**するため
1 byte でも変えると freeze 再発行が要る。

**rulings 第 2 束 (12:38) との関係。** [T-886] (`_find_rollout` の名前 glob fast path) は
(a) で確定したが、対象 file が本 wave の W3 と同じ `tools/codex_reasoning_ab.py` であるため
**本 wave には取り込まなかった** — 段 3 の敵対検証を通していない変更を受理集合近傍へ
後から差し込まないため。本 wave の profile では該当箇所 (`_session_meta_rows` 14,775 呼) が
20.19 秒を占めており、land 後に別 wave で実装するのが安全である。
[T-888] の解消判定に本 wave の実測 (現 main で 9323 passed / 0 failed) が引用された。

## 次の一手差分

### 更新

- [T-887] **P2・裁定待ち**: 限定 group 化の再提示に、本 wave が実証データを足す。
  **受入はスケジュール下界に張り付いており (現状順 202.6 / LPT 176.7 / 下界 176.7 秒)、
  並べ替えでは 1 秒も取れない。** 一方で `test_campaign_import_invariant` の
  per-worker 重複構築は payer 数が走行ごとに 4〜6 と揺れ、**1 payer あたり約 40 秒**を足す。
  group 化が効くとすればこの重複であって critical path の並べ替えではない。
  base: adbbf69bc0eac96314b218be4cdea270caef8bc2c9b0db2e15ef12b5b0ceab82

### 新規

- {{T:holdout-live-scan-cost}} **P1・新規**: `s8b_holdout_freeze.search_repository` の
  live scan 24.3 秒を削る。11,988 file を毎回読み 3 軸 × 4 候補 = re.search 107,721 回。
  受入の床に残る最大項で、**repo の file 数に比例して伸びる**。
  ただし `output/s8b-freeze/holdout_freeze.json` の generator pin と
  `output/t080-migration/legacy-freeze-repin.receipt.json` の `metadata_fields` が
  `_verify_source` で**現行 worktree bytes と完全一致を要求**する (blob 救済なしの設計) ため、
  実装を 1 byte でも変えると freeze の再発行が要る。**再発行の可否がユーザー裁定事項。**
- {{T:acceptance-set-strengthening-candidates}} **P3・新規**: 受入集合を**強める** 3 案の採否。
  (a) receipt path への `A` を mutation 扱いする / (b) exact blob の deletion を duplicate 扱いする /
  (c) introduction 以前から在る同一 OID の別 path を拒否する。いずれも検出力は上がるが
  受理集合の変更であり、規律 2 の「緩めない」と対称に「勝手に強めない」を守って見送った。
- {{T:hash-object-leading-dash}} **P3・新規**: `git hash-object --no-filters <path>` が
  `-answer` のような正当なファイル名を option 誤認で拒否する。バグに見えるが、直すと
  受理集合が広がる (親が実測で確認)。意図か否かの裁定が要る。
