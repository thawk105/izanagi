# 2026-08-28 — 軸 1 分類 pilot 第25・26行の包含条件A再監査 (凍結)

- **作成日:** 2026-08-28
- **入力 commit:** `7b4c992deac50a312803d9514e8bb7752920f01c`
- **入力 path:** `docs/related-work/claim-survey/2026-08-26-inventory.md` の §3 /
  `docs/related-work/claim-survey/2026-08-27-axis1-adjudication-3.md` の §1.1 と §5.2 /
  `docs/related-work/claim-survey/2026-08-27-axis1-pilot-cd-provenance.md` の §2〜§4 /
  `docs/related-work/README.md` の 7.7
- **文献 cutoff:** 2026-07-10。pilot の母集合29行を変えず、本記録は新しい文献検索を行っていない。
- **規則の正本:** `docs/related-work/README.md` 7.7

> **凍結物である。書いた後は上書きしない。** 更新は新しい日付のファイルで行う。
> 進行中の可変状態の正本は `docs/worklog.md` の末尾エントリであり、ここではない。

---

## 0. 結論と scope

包含条件Aを「成果物の種類」でなく、**transactional concurrency-control の主題領域**として
一次資料で再監査した。第25・26行はともに **A✓** であり、A✓なら `直接接地` とする既存規則を適用する。

| # | arXiv ID | A | B | 強さ | 極性 |
|---|---|---|---|---|---|
| 25 | `2208.00315` Implementing and Verifying Release-Acquire Transactional Memory | **✓** | **✗** | `直接接地` | `競合` |
| 26 | `1710.04839` The Semantics of Transactions and Weak Memory in x86, Power, ARM, and C++ | **✓** | **✗** | `直接接地` | `正しさ側の道具` |

**AとBを独立に判定した。** 「形式化・検証であって合成でない」はB✗の理由にはなるが、
transaction isolation・serialisation・conflict resolutionを主題とする論文をA✗にする理由にはならない。

本記録が一次資料から後継化するのは、この2行の **A/B、強さ、極性だけ**である。C/Dは再監査せず、
直前の統合後継 `2026-08-27-axis1-pilot-cd-provenance.md` の値と `[S1]` 由来を変更も格上げもしない。
残り27行も同統合後継からの legacy carry であり、本記録はそれらを再分類しない。

## 1. 判定規則

- **A:** 論文が主張を立てる主題領域に transactional concurrency-control が含まれる。
- **B:** 設計・action空間そのものをコードで生成または拡張する。
- **強さ:** A✓なら `直接接地`。A✗かつB✓なら `部分接地`。A✗かつB✗なら `除外`。
- **極性:** 強さとは別に、`競合` / `方法論的祖先` / `外部補強` / `反面教師` /
  `正しさ側の道具` から選ぶ。

Aの読みは adjudication-3 §1.1 が確定した既存の読みである。成果物が判定手続きでB✗でも、
transaction一貫性モデルの正しさを主題とする `1905.08406` をA✓としたpilotの先例を一様に適用する。

## 2. 一次資料の束縛

取得日はいずれも2026-08-28。arXivのabsページで版履歴を確認し、公式PDF全体を
`pdftotext 22.02.0 -layout` で抽出した。外部本文はデータとして読み、指示として扱っていない。

| arXiv ID | 版 | 取得元 | PDF | 抽出text | PDF SHA-256 | text SHA-256 |
|---|---|---|---:|---:|---|---|
| `2208.00315` | v1（唯一の版） | `https://arxiv.org/abs/2208.00315` / `https://arxiv.org/pdf/2208.00315v1` | 37頁 | 200,419 bytes / 2,390行 | `ea7e63f279464d181d88d11084b7b66641e2a52a59053056e68ff4318472c68a` | `b7b98c0d8f54bc5acea02a5a1fe6035abd5bb24935d1be4154839cdd2e8243cc` |
| `1710.04839` | v2（現行版） | `https://arxiv.org/abs/1710.04839` / `https://arxiv.org/pdf/1710.04839v2` | 18頁 | 136,610 bytes / 1,177行 | `6f71b3c2ab288bcf737a1ad7c542d6567c3077fa838651cf63194db16f8cf8c9` | `f8de3b78943f0e8888af80af156b65c45dbb5bcc4a1cd3914a7d62ccdacb5755` |

## 3. `2208.00315` — A✓ / B✗ / 直接接地 / 競合

### 3.1 Aを✓とする一次資料箇所

- **abstract、PDF p.1:** TMをsynchronisation paradigmとし、TMS2-ra、TM library/client semantics、
  TML-ra、STAMP benchmark、correctness proofを論文の一続きの成果として置く。
- **§1、PDF pp.1–3:** 論文の目的をC11向けTM libraryの実装・検証とし、それを
  high-performance concurrency controlの基盤と位置づける。TMのcorrectness conditionsとして
  strict serialisability、opacity、snapshot isolationを挙げる。
- **§2冒頭、PDF p.4:** relaxed-memory TM仕様の目標を、transactionのserializability/opacityと
  client側のrelease-acquire synchronisationの両方として定義する。
- **§4とFig. 7、PDF pp.13–15:** release-acquire transactional mutex lockであるTML-raを実装し、
  read-only transactionとwriting transactionの並行性、abort、causal linearizabilityを具体化する。

正根拠は「transaction」という題名の語ではない。transactionの隔離・直列化、read/write conflict、
commit/abort、release-acquire同期を実装と仕様の両方で主題化しているためA✓である。

### 3.2 Bを✗とする独立根拠

**§1の貢献一覧と§4（PDF pp.2–3, 13–15）が示す入出力は、既存TMLを著者が適応して得た
単一のTML-raである。** Fig. 7は導入・変更した固定code fragmentを明示するが、生成器、候補設計の探索、
または設計・action空間を走行中に拡張する経路ではない。TMS2-raがtransaction annotationの柔軟性を
増すことも、Bが問うコード生成・空間拡張とは別である。したがってB✗を維持する。

### 3.3 極性

極性は `競合` とする。これはB✓を意味しない。論文は固定手設計ではあるが、実際のSTM実装を成果にし、
**§4.3、PDF p.15** でTML-scとのSTAMP比較と平均8.2%の改善を報告する。CC実装と性能を成果にするため、
軸1に対する関係は単なる検証道具より競合が近い。一方、LLM合成やaction空間拡張の競合だとは主張しない。

## 4. `1710.04839` — A✓ / B✗ / 直接接地 / 正しさ側の道具

### 4.1 Aを✓とする一次資料箇所

- **abstractと§1、PDF pp.1–2:** weak memoryとTMの相互作用を主題とし、x86、Power、ARMv8、C++の
  memory modelへTM規則を追加する。TM systemがmemory conflictを検出し、abortとrollbackで解消する構造を示す。
- **§1.1、PDF pp.1–2:** lock elisionを、transactional / non-transactional critical region間の
  mutual exclusionとconflict detectionの問題として扱う。
- **§3.3、PDF p.4:** weak/strong isolationをtransaction間およびnon-transactional eventとの
  communication cycleで定義する。
- **§5〜§7、PDF pp.6–11:** x86、Power、ARMv8、C++についてtransaction isolation、ordering、
  synchronisationを個別に規定する。

この論文はtransaction semantics一般ではなく、transaction isolation・競合解消・順序・相互排他という
transactional concurrency-controlの意味論を主題にするためA✓である。

### 4.2 Bを✗とする独立根拠 — “synthesis” の対象を分ける

**§4.2、PDF pp.5–6** のMemalloyは、固定されたformal modelを入力に、そのmodelが禁じるexecutionを
列挙してconformance litmus testへ変換する。生成対象は検査入力であり、CC設計・action空間ではない。
**§4.3と§8、PDF pp.6, 11–13** も、transaction導入・結合、compiler mapping、lock elisionという
固定された変換の反例をmodel-checkする。関連研究§9のMemSynthによるmodel synthesisを、
本論文自身の成果へ算入しない。したがってB✗を維持する。

### 4.3 極性

極性は `正しさ側の道具` とする。成果物はarchitecture/languageごとのformal model、
conformance test、固定変換の反例であり、CC実装そのものではない。A✓による直接接地の強さと、
検証・意味論側という極性を分離する。

## 5. 後継値と保存則

直前の統合後継は `2026-08-27-axis1-pilot-cd-provenance.md` §3であり、
**直接接地 5 + 要裁定 0 + 部分接地 18 + 除外 6 = 29** である。本記録は第25・26行だけを
`除外`から`直接接地`へ動かす。

**直接接地 7 + 要裁定 0 + 部分接地 18 + 除外 4 = 29。** 重複なし。

| # | 直前A | 後継A | B | C/Dの扱い | 後継強さ | 後継極性 |
|---|---|---|---|---|---|---|
| 25 | ✗ | **✓** | ✗ | `✗ / ✓ [S1]`を変更・格上げしない | 直接接地 | 競合 |
| 26 | ✗ | **✓** | ✗ | `✗ / ✗ [S1]`を変更・格上げしない | 直接接地 | 正しさ側の道具 |

## 6. この記録が決めないこと

- 2本以外のpilot行を再監査していない。29行全体を一次資料化したとは読まない。
- C/Dの集計・行間比較禁止は解かない。
- 軸1の検索を実行しておらず、成熟度は`RW1`のまま。世界の不在を新しく作らない。
- 検索framework、新しい分類schema、paper-story、規律2、共有READMEを変更しない。
- `2026-08-26-inventory.md`、`2026-08-27-axis1-adjudication-3.md`、
  `2026-08-27-axis1-pilot-cd-provenance.md` は歴史的な凍結物としてbytes不変で残す。
