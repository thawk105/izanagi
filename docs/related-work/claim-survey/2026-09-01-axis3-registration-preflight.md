# 2026-09-01 — 軸 3 検索の registration preflight 実行記録 (凍結)

- **作成日:** 2026-09-01
- **入力 commit:** `2e7d9f85d8e53aeaa27fbfbe7bc6064cb352673a` — この commit の bytes で実走した
- **入力 digest の所在:** 生成物 4 件は
  `output/insights/2026-09-01_t1881-axis3-registration-preflight/` にあり、file ごとの SHA-256 を
  §2 に置く。封印対象 closure の各 file の digest は seal 自身 (`registration-seal.json`) が持つ
- **入力 path:**
  `docs/related-work/claim-survey/2026-09-01-axis3-search-amendment.md` (契約) /
  `docs/related-work/claim-survey/2026-08-27-axis3-search-preregistration.md` (旧登録) /
  `orchestrator/related_work_search.py` と `tools/run_axis3_search.py` (実行器) /
  `orchestrator/schemas/axis3_search_{catalog,checkpoint,page_evidence,registration_seal}.schema.json`
- **文献 cutoff:** 契約 §0 が旧登録 §2 から継承した暦年境界 **2026-12-31**
- **契約の正本:** `docs/related-work/claim-survey/2026-09-01-axis3-search-amendment.md`。
  **本文書は契約を 1 byte も変えていない。**

> **凍結物である。** 書いた後は上書きしない。更新は新しい日付のファイルで行う。
> 進行中の可変状態の正本は `docs/worklog.md` の末尾エントリであり、ここではない。

---

## 0. 総合判定

> **軸 3 は `RW0` である。本文書は検索を 1 本も完走させていない。**
> **外部 request は 1 本も出していない。世界の不在は支持しない。**

本文書が記録するのは、**network を 1 度も使わない registration preflight を実走した事実**だけである。
旧登録 §13.1 の blocking のうち **B4 (規範 parser の受入) だけ**がこの走行で閉じた。
B1・B2・B5 は閉じておらず、B3 は D1206 で裁定済みだが実装適合は本走行の範囲外である。

**これは「登録段までの実行器」の記録である。** live preflight と本走には、後続の実装と
人間裁定が要る (§5)。

## 1. 実行した command

作業 root は repository root。`--catalog` などの path は root からの相対である。

```
python3 tools/run_axis3_search.py register \
  --catalog output/insights/2026-09-01_t1881-axis3-registration-preflight/catalog.json \
  --seal output/insights/2026-09-01_t1881-axis3-registration-preflight/registration-seal.json \
  --registration-inputs output/insights/2026-09-01_t1881-axis3-registration-preflight/registration-inputs.json
```

```
python3 tools/run_axis3_search.py validate-registration \
  --catalog output/insights/2026-09-01_t1881-axis3-registration-preflight/catalog.json \
  --seal output/insights/2026-09-01_t1881-axis3-registration-preflight/registration-seal.json \
  --registration-inputs output/insights/2026-09-01_t1881-axis3-registration-preflight/registration-inputs.json
```

両方とも rc=0。`register` は `head_verified: true` / `valid: true`、
`validate-registration` は `valid: true` を返した。**transport を構築せず、socket を 1 度も開いていない。**

## 2. 生成物

| file | SHA-256 (file bytes) |
|---|---|
| `catalog.json` | `7dd14814ecd3a924d61ebfee707d604556624db639240318a95ce49e44185a58` |
| `registration-inputs.json` | `8566a172350f1c3ac2a2966e1bf501eae17d12d608858d11771e83588a33e236` |
| `registration-seal.json` | `5a5e0d799c7eebf4378b0874b5c3ad5de3defe52cbc34b0e5373c5b0416d695e` |
| `validate-registration.json` | `15458e6ecd688f41415b131efb3fe8525764e2403f2fc8d77cfc5d4dfcfccf28` |

**seal 内部が申告する canonical digest は file bytes の digest と別物である。** 混同してはならない。

- `catalog_sha256` = `7dd14814ecd3a924d61ebfee707d604556624db639240318a95ce49e44185a58`
  (catalog の canonical bytes。上表の file digest と一致する)
- `seal_sha256` = `fadda547b2126de5e135eeffb7d71f2eaac9146e6f9055c62f85f39f163dcd10`
  (seal 本体の canonical digest。`registration-seal.json` の file digest とは**一致しない**)
- `closure_sha256` = `f9130f67019381626d9a3b5723d11f6ccad7dd102d0821ab3b698ad12b9a0ad9`
- `argv_sha256` = `f3a7021a6da7c8187ce6d11a03dedba6307dfc643c342f712bd76bb9cfd1ad09`
- `fixture_sha256` = `dfcef2c4e5bf1cfa7d18e4dacfa70a1b29b8fd26a93359366cbea32cd57ce97e`
- `phase_argv_contracts_sha256` = `dc402ad9fac0cd0000ec0c75b9e2a5be0b7a0e35d6f3a56c81bc11f5b39078e3`
- `frozen_semantics_sha256` = `b1e3a611c2a61409df07e399e09fc96c5d251d58d830754cc9e8a0494a80bcf4`

## 3. 封印した closure (exact 8 file)

契約 §3 が定めるとおり、受理条件は**この 8 file について作業ツリーの bytes と `HEAD:<path>` の
blob が一致すること**である。repository 全体の HEAD 一致は要求しない。

| 種別 | path | SHA-256 |
|---|---|---|
| source | `orchestrator/related_work_search.py` | `30a57b6c78c9cda4807f3ba9cecffbd96f2338aa07ee8ae6c87211e7a85e1a7f` |
| source | `tools/run_axis3_search.py` | `20cb694002933a2636501ae154bb3b1e232a375c3027bf60a3d4930b1c17c973` |
| schema | `orchestrator/schemas/axis3_search_catalog.schema.json` | `67d8b2f266b9373dd4b9d74d3af2a309cb2b25079665577287e51ebcf8e37150` |
| schema | `orchestrator/schemas/axis3_search_checkpoint.schema.json` | `b305168482f85653466c1256035b4fa0ee4a7977f12462d73c4906db14c396da` |
| schema | `orchestrator/schemas/axis3_search_page_evidence.schema.json` | `2d4ab8865616f53ec044a807d06677ec1de1161dd03bd80ba84b6918f6f0df62` |
| schema | `orchestrator/schemas/axis3_search_registration_seal.schema.json` | `9bcc9b96a9212f16edad1710df675a40e869e73afee335f93f32b1617aa7b7dc` |
| frozen input | `docs/related-work/claim-survey/2026-08-27-axis3-search-preregistration.md` | `eace24a94ed3e206b401e8264675f81b7e7278b6aa90b39a55ac26353d1cb89c` |
| frozen input | `docs/related-work/claim-survey/2026-09-01-axis3-search-amendment.md` | `1fb7517081f5cc73a37021768aabf08443970b71365ba41816c623be90302b39` |

これに catalog・OQL fixture・argv/phase contract の digest が加わる。

**seal が排除するのは、列挙したこの closure の封印後 drift だけである。** それ以上を保証しない。
同一 UID による一括改変、remote attestation、CLI を起動した主体の人間性は保証範囲外である
(契約 §6)。実行環境は来歴としてだけ記録した — `cpython 3.10.12`、`jsonschema 3.2.0`。
**これらは受理条件に入れていない。**

## 4. catalog の内訳 (2122 行)

| 区分 | 件数 |
|---|---|
| 論理行 合計 | 2122 |
| main | 1893 |
| control | 21 |
| lookup | 20 |
| auxiliary | 188 |
| request factory が `complete` | 1929 |
| request factory が `blocked` | 193 |
| zero-wire の派生 control (別枠登録) | 3 |
| この走行の wire attempt | **0** |

`blocked` 193 の内訳は DBLP 題名 lookup 5 本と補助経路 188 本である。
**blocked を母集合から消していない。** 契約と旧登録の「母集合の外」の限定はすべて残る。

## 5. blocking 5 件の現状態

| # | 項目 | 状態 |
|---|---|---|
| B1 | alias 統合の判断 | **未着手。** 取得後に発見した alias を `要裁定` として記録し、人間裁定へ出す。実行器を回すだけでは閉じない |
| B2 | OpenAlex / DBLP での anchor 5 件の到達性 | **未評価。** live preflight を要する。DBLP 題名 lookup 5 本が `blocked` のままなので、この経路だけでは完全には閉じない |
| B3 | API 版番号の代用 | **裁定済み (D1206)。** ただし実装適合は本走行の範囲外である |
| B4 | 規範 parser の受入 | **閉じた。** OpenAlex OQL の正例 7 本・負例 6 本がこの走行で通り、fixture bytes の digest (`dfcef2c4…`) を seal が束縛している |
| B5 | 予算表の作成 | **未確定。** live preflight を要する。上限は全 wire attempt 20 万回と、最初の外部 request から 30 暦日 |

**non-blocking の N1〜N4 (OpenAlex の AND 順序、`meta.per_page` の最終ページ意味論、
最小 request 間隔と cooldown、無償枠の共有単位) はいずれも未観測である。**
旧登録 §13.2 のとおり `RW3` の前提ではない。

## 6. 次の担当者への引き継ぎ

### 6.1 live へ進む前に閉じる必要があるもの

- **U11 は hard stop である。** arXiv が同一 work ID を頁境界で 2 回返し、宣言総数では 1 回だけ
  数える事象が軸 1 の実行で観測されている。本実行器はこの再出現を完走拒否として扱う (厳格側)。
  **この扱いを維持するかは人間裁定に属し、裁定が付くまで `run-ready --live` を開始しない。**
- **control evaluator は未実装である。** 未評価の control は完走を主張しない (fail-closed)。
  演算子 control と anchor 包含 control の採点器が要る。
- **resolver は未実装である。** DBLP 題名 lookup 5 本と補助経路 188 本は `blocked` のままである。
- **`start_independent_pass` と `blocked_on_ruling` は schema 語彙としてのみ存在する。**
  checkpoint は両 action の完全 request を常に保持するが、resume executor はこの 2 つを実行しない。
  独立 2 走目や裁定待ちからの再開を要する走行は、先に producer/executor を実装する。
- 上記を実装した時点で **closure の bytes が変わるため、seal を作り直す** (`register` の再実行)。

### 6.2 live の相と完全 command の形

`<...>` は実行者が決める path である。**本文書が凍結しているのは registration の 2 相だけであり、
以下は実行器が受け付ける形の記録であって、実走記録ではない。**

```
python3 tools/run_axis3_search.py preflight --live \
  --catalog <CATALOG> --seal <SEAL> --registration-inputs <REGISTRATION_INPUTS> \
  --bundle <PREFLIGHT_BUNDLE> --output <PREFLIGHT_REPORT> --checkpoint <CHECKPOINT>

python3 tools/run_axis3_search.py run-ready --live \
  --catalog <CATALOG> --seal <SEAL> --registration-inputs <REGISTRATION_INPUTS> \
  --preflight-bundle <PREFLIGHT_BUNDLE> --preflight-report <PREFLIGHT_REPORT> \
  --bundle <FINAL_BUNDLE> --output <RUN_RESULT>

python3 tools/run_axis3_search.py resume --live \
  --catalog <CATALOG> --seal <SEAL> --registration-inputs <REGISTRATION_INPUTS> \
  --preflight-bundle <PREFLIGHT_BUNDLE> --bundle <BUNDLE>

python3 tools/run_axis3_search.py validate-bundle <BUNDLE> \
  --catalog <CATALOG> --seal <SEAL> --registration-inputs <REGISTRATION_INPUTS> \
  --preflight-bundle <PREFLIGHT_BUNDLE>
```

### 6.3 予算・停止条件・再開点

- **予算:** resolver・availability・preflight retry・本走 retry を含む全 wire attempt 20 万回。
  最初の外部 request から 30 暦日。
- **最初の外部 request:** `AX3A1-L-ID-01@openalex` に固定されている。
- **停止条件:** 最初の OpenAlex 429 で他 request を送らず checkpoint する。arXiv の年 shard が
  索引の結果窓を超えたらその ID を `blocked` とし本走しない (runner 内で細分化せず後続 amendment へ送る)。
  non-200 は当該 stream を不完走とする。未評価 control は完走を主張しない。
- **再開点:** bundle の WAL / ledger と `checkpoints/<連番>.json`。final の resume は末尾 checkpoint、
  preflight の resume は packed WAL の prefix を再導出する。

## 7. この走行で確かめていないこと

- 索引が実際に応答するか。**外部 request を 1 本も出していない。**
- anchor 5 件の到達性 (B2)。
- 予算が上限内に収まるか (B5)。
- alias / work-family の統合可否 (B1)。
- 取得した record の分類、感度監査、`RW3` / `RW4` の判定。

**これらのどれも、本文書の成功をもって充足したと書いてはならない。**

## 8. 実測の記録 (初回の赤を含む)

本実行器の焦点走は、段 6 の fix より前は**赤だった**。記録として残す。

| 走行 | checkout | 結果 |
|---|---|---|
| 1 回目 (fix 前) | 統合 commit 直後 | **rc=1。4 failed / 78 passed / 12 errors、21 分 55 秒** |
| 2 回目 (fix 後) | `2e7d9f85d` | **rc=0。107 passed、15.35 秒** |

1 回目の 12 errors は共有 fixture が 2122 行全体の preflight を実走して 13 MB の WAL を書き、
producer と replay で `record_count` の意味が食い違って finalize できなかったことによる。
所要 21 分 55 秒もこの fixture が原因である。2 回目は fixture を分解し、全 catalog の性質は
WAL を書かない report 検査で、耐久性は 1 page の WAL で保つようにした。
**検査を消して速くしたのではない。**
