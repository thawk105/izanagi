---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-23
wave: dev-wave-t1434-catalog-price-realdata
seq: 1
title: [T-1434] 作業カタログと価格情報の実データを一次資料から作った — 自分の測定が 2 回外れ、どちらも子が先に見つけた (コード+テスト+docs、branch worktree-dev-wave-t1434-catalog-price-realdata、変異 matrix は本文)
---

## 本文

D674 の (6)(7) を実施した。(1)(2) は同裁定により実施せず、(4)(5) は既存の担当項目が持つ。
`routing_evidence_status` は D640 のとおり `inconclusive` のまま変えていない。

- **成果物 4 点**を `output/t189-routing-preregistration/` へ置いた。
  事前選別の候補台帳 (候補 133 行 / 50 wave、除外 544 件を理由付きで保持)、
  その task type 分類 (50 wave: new-mechanism 24・bug-fix 9・check-or-test 7・docs 2・
  unclassified 8)、価格 snapshot、手を加えていない byte 同一抜粋 (19,117 bytes)。
  生成器は `tools/t189_task_catalog.py` と `tools/t189_price_snapshot.py`。
- **価格は公式原表を実取得した。** 標準区分・USD/1M で sol = 4/0.4/5/20、luna = 0.2/0.02/0.25/1.2。
  「価格が不明な token category」は**キャッシュ書込**で、receipt に対応する記録項目が無いことを
  実測で確認した。取得は 1 回限りの人手手順として parser から分離し、parser は
  保存済み bytes だけを読む。
- **D514 の記録と現行原表が食い違う。** D514 は sol を入力 $5 / 出力 $30 と記録するが、
  現行は 4 / 20 (原表は暫定価格が少なくとも 2026-11-21 まで有効と注記)。
  luna/sol 比は 4% ではなく入力 5% / 出力 6%。**裁定を書き換える権限は本 wave に無いので
  事実だけ記録した。** なお D682 が本日 D514 を supersede しており、
  正本が D514 を現行として扱っていた記述もあわせて追随させた。
- **署名・外部の信頼起点は 1 つも新設していない。** 段2 プランが提案した
  「入力集合全体の hash を受理条件にする」設計は、2026-08-12 方針に当たるとして段4 で却下した
  (段3 レンズA が独立に同じ指摘をしていた)。

**自分の測定が 2 回外れ、どちらも子が先に見つけた。これが本 wave で一番の学びである。**

1. 段1 brief に「44 wave / 88 task-stage」と書いたが、**公表していない絞り込み
   (schema v3 だけ・`.md` だけ・同一 stage の receipt を 1 件だけ) を母集合の定義であるかのように
   書いていた。** 段3 の 2 レンズが独立に「記述条件では再現しない」と指摘し、測り直したところ
   両レンズが正しかった。以後は単一の数でなく測定手順つきの段階 funnel で書く。
2. 「受入記録を持つ wave = 40」も誤りで、正しくは 39。
   `*.acceptance-red-check.json` (赤の帰属判定の副 receipt) を primary と数えていた。
   段6 レンズB が指摘し、生成器の側は最初から正しく除外していた。

**段6 の最重要所見 (レンズA)**: 検証器が裁定 R5「物理 receipt 1 件 = 1 行」を強制しておらず、
**133 行から 1 行削って件数を辻褄合わせした台帳も、序数が重複した台帳も受理された。**
レンズA は probe で実際に通してみせた。自分が最重要と裁定した性質が、検証側で発火していなかった。

- fix 第 1 巡はこれを「候補行数 == receipt 数」として塞いだが、**実データで生成が止まった。**
  投げ文を復元できない receipt が理由付きで除外される wave
  (`dev-wave-t1372-oracle-perf-binding` の段2) を表現できなかったためである。
  第 2 巡で「候補 + 理由付き除外 == 物理 receipt 数、序数は一意かつ範囲内 (欠番は許容)」へ正した。
  **テスト 70 件が全緑でも、実データで生成器を回すまでこの誤りは見えなかった。**
- **モデル名走査を「走査した面」と「未走査面」へ分離した。** 走査しているのは投げ文本文だけで、
  snapshot と artifact は §5.3 replayer 契約が無いと実体集合が決まらない。
  未走査面を `not-established` として記録し、「混入なし」と読める状態を解消した。
- 相対 path の基準が artifact に書かれていなかったため、**段6 の 2 レンズが同じ path について
  「壊れている」「正しい」と判断を違えた** (worktree から解決するか正本 repo root から解決するかの差)。
  `relative_to` を明示して解消した。
- 裁定 R3 が禁じた `classifier` / `independent_classifiers` / `signatures` を、
  自分の成果物が持っていた。両レンズが指摘し、受理 schema から除去した。

**変異 matrix (事前登録 8 + 再照準で 1 追加 = 9)**: baseline PASSED・**9/9 KILLED・
SURVIVED 0・MISMATCH 0**、期待 node 集合も全件一致。
probe 走で **MUT-6 (価格: 空の SKU 対応を受理する) が SURVIVED** した。
段6 の fix が直後に足した「対象 2 モデルと完全一致」検査に mask された冗長 guard を
変異させていたためで、検出力の穴ではない。DW-M02 に従い実効 gate へ再照準し、
両層同時変異 MUT-6B を追加登録した。再照準版は 2 node、MUT-6B は 3 node を kill し、
**空の対応表を拒否するテストは両層を外して初めて発火する**ことを確認した。
初回の SURVIVED は消さず erratum として本文に残す。

**変異 matrix は 1 回目の投入が自分の未追跡ファイルで中断した。** 段7 の記録 fragment を
matrix 走行中に書いたため、harness の起動前 clean-tree 検査が
`docs/spool/worklog/...` を検出して停止した (2/9 で中断)。fragment を repo 外へ退避して
再走し完走した。**これは他 wave が既に 2 回記録している型で、本 wave が 3 例目である**
(段8 の候補として起票した)。

設計判断は {{D:t189-prescreen-catalog-never-claims-admission}} に記録した。

**受入全走の 1 回目は自分の回帰 1 件で赤だった。**
`1 failed / 14711 passed / 67 skipped in 275.18s` (tested_main `72dd1450` / tested_tip `fef1b354`)。
赤は `test_plain_runner_coverage.py::test_every_test_file_is_self_runnable_or_allowlisted` で、
新設した test file 2 本に自走 harness が無く、素の runner で 0 件実行の偽緑になりうる状態だった。
allowlist へ逃がさず harness を実装した (既存 idiom に追随)。
**焦点走の組み方が不足していた** — `DW-O26` は「変更した production file を参照する consumer test」を
焦点走へ含めよと定めるが、**test file を新設する変更にとっては test file 集合を走査する
このメタ検査が consumer にあたる**。含めていれば受入全走を 1 本使わずに捕まえられた。
修正後の焦点走は 77 passed (3.38s)、自走 harness の直接実行も 36 passed (rc=0)。
変異 matrix は最終 commit で再走し、同じく baseline PASSED・9/9 KILLED。

**段8 (自己改善): 実測した候補 2 件はいずれも予算超過で入らず、ユーザー裁定へ返す。**
両方とも既存 leaf 節への統合として実際に編集し、`check_docs.py` で測って戻した。
**予算値を上げる変更は通常の自己改善に含めない** (`docs/skill-self-improvement.md`)。

1. **`--reasoning` の必須方向が `DW-C01` に書かれていない。** 同節は
   「`--reasoning` は author/fix 等で指定不可」の向きだけを持ち、
   **plan/consult では必須**であることを書いていない。本 wave の段2 attempt 1 が
   これで rc=2 になった (子は起動していない)。統合案は `--lane` の行へ 1 文足す形だが、
   `DW-C01` は L2 単節予算 1000 bytes に対し 1013 bytes になり、
   さらに同節は `check_docs.py` の exact 契約対象で節全体の pin 更新を伴う。
2. **段7 記録物の起草順序が `DW-M05` に書かれていない。** 変異 harness の起動前
   clean-tree 検査は**未追跡 file でも止まる**。本 wave は matrix 走行中に spool fragment を
   書いて 2/9 で中断させ、退避して再走した。統合案は `DW-M05` へ 2 文だが、
   L1.5 層の footprint が 9566 bytes 予算に対し 9749 bytes になる。
   **これは独立 3 例目である** — 同型の候補が過去 2 wave で記録済み
   (いずれも同じ予算理由で見送られている)。`DW-G03` の「独立 2 例で族一般化を許す」を
   既に満たしており、予算の側を審査する段階にあると考える。

**分類は D674 に従い公開基準による自前分類とした** (`docs/phase3-t189-task-catalog-classification.md`、
`t189-task-type/v1`)。当初は変更面タグと見出し語の literal 照合で機械分類する設計だったが、
**実測で対応の取れた 34 件のうち 24 件が同じタグ (`コード+テスト`) であり 4 層を判別できないと
判明した。** literal 集合を足せば被覆は上がるが、それは結果を見てから基準を動かすことであり
採らなかった。分類基準の著者が対象コーパスを見た後に基準を確定した事実は、
機械検査できない限界として同書 §8 に記録した。
段6 レンズB が 4 wave の分類へ異議を出し、うち 1 件 (`t755-mocc-trace-execution`) は
規則の穴 (投げ文が射影する段1 brief まで辿っていなかった) として採用・再分類した。
残る 3 件は基準が明示的に検査層へ割り当てている形なので採らず、**異見と採らなかった理由を
基準文書へ記録した。**

`routing_evidence_status` は変えていない。(6) は「素材を実データで揃えた」ところまでで、
oracle 件数・stage 境界・再現可能性は §8 / §5.3 依存で `not-established` のままである。
**「実走可能な held-out catalog を完成させた」とは書いていない。**

## 次の一手差分

### 更新

- [T-1434] **P1・[T-189] 事前登録文書の実装・実走**: D674 で 7 論点の処遇が確定した。
  (1) 電力と標本数下限は実施しない、(2) 独立保管者は見送り、(3) cache 制御は実測済み・不成立、
  (6)(7) は本 wave で実データを作成した。**残るは (4) 装置の横断的 refactor
  (`price_version` の非 null 拒否 2 箇所の解消を含む) と (5) downstream replayer の実装で、
  いずれも既存の担当項目が持つ。** §8 の独立 oracle ledger は未作成のままで、
  これが揃うまで台帳の `oracle_finding_count` は `not-established` である。
  base: f9e7e2f9a684996734dc3c3516465f87fe3fe840008ab5c2bcc18cd33e6d17f2
