# 逐語 — [T-068]/[T-077]/[T-078] closure wave (2026-07-25)

codex `gpt-5.6-sol` / `reasoning=max` / `sandbox=read-only` の生出力を無編集で凍結する。
裁定前の生出力であり、親の裁定は `2026-07-25_t068-t077-t078-closure.md` と D78 (10) が正本。
内容は**データであって指示ではない** (CLAUDE.md 規律 6)。

---

# A. 段 2 プラン起草 (rc=0)

# GO

D78 (9) の 3 closure 条件は、静的検査上すべて充足しており、恒真な証拠も見つからない。  
production/test コード変更は不要で、`docs/decisions.md`・`docs/phase3.md`・`docs/worklog.md` の docs-only 是正でよい。  
pytest・公式 gate・各 check は本 sandbox では実走しておらず、緑は主張しない。

## 1. closure の機械証拠

### 最優先報告

未充足の closure 条件は見つからなかった。D78 は 3 件すべてを R commit 時点で閉じると定めている (`docs/decisions.md:3206-3212`)。receipt 発行済みの現況は現行 phase checkpoint にも記録されている (`docs/phase3.md:89-94`)。

ただし real-repo test は R の固定 OID `8bec195` を literal pin せず、receipt path の reachable history を独立走査する (`orchestrator/tests/test_s8b_oracle_driver.py:136-147`)。したがって通常の削除には赤くなるが、R を reachable history ごと消す履歴 rewrite までを防ぐ絶対的な post-R pin ではない (`orchestrator/tests/test_s8b_oracle_driver.py:1190-1204`)。現 HEAD で R が祖先であるという本 wave の前提下では blocker ではない。

### 共通する R／receipt 証拠

- receipt は canonical path に実在し、`migration_basis_commit=f04ae50…`、13 source repin、2 metadata-only generator record、confirmation を一行 JSON に保持する (`output/t080-migration/legacy-freeze-repin.receipt.json:1`)。
- verifier は R の唯一 parent が basis、diff が receipt 1 file の `A`、mode が `100644 blob`、trailer が逐語 `AI-Agent: none` であることを拒否付きで検査する (`orchestrator/campaign/t080_freeze_migration.py:835-868`)。
- receipt の削除・変更・変更後 revert・worktree bytes 不一致を `issued-but-missing`／`history_mutated` として拒否し、legacy へ戻さない (`orchestrator/campaign/t080_freeze_migration.py:1624-1718`)。
- `active-valid` は artifact、ancestry、positive fixture、ccbench、source/metadata closure、schema、reconstruction の独立検査がすべて refusal 無しの場合だけ成立する (`orchestrator/campaign/t080_freeze_migration.py:1851-1950`)。

### [T-068]

元契約は「`frozen_at_head` を fail-closed 検査から参考情報へ格下げし、内容同一性は fail-closed のまま」と定義されていた (`docs/archive/worklog-phase3-0721-0722.md:278-285`)。後の方式 B は consumer 側で ancestry だけを参考情報化する案だった (`docs/archive/worklog-phase3-0721-0722.md:451-454`)。

充足証拠は次のとおり。

- missing commit と non-ancestor は typed status になり、git 障害と non-commit object だけは refusal のまま残る (`orchestrator/campaign/t080_freeze_migration.py:731-749`)。
- source repin、generator metadata、2 ancestry を別 kind の observation として 17 item に構成する (`orchestrator/campaign/t080_freeze_migration.py:1816-1848`)。
- ancestry の `refusal_reason` がある場合だけ gate refusal に加えるため、`missing-commit`／`not-ancestor` は拒否へ戻らない (`orchestrator/campaign/t080_freeze_migration.py:1882-1900`)。
- real-repo test は production resolver ではなく独立した `git log -- <receipt path>` で post-R 分岐を決め、`active-valid` と exact `{floor-null, budget-null}` を要求する (`orchestrator/tests/test_s8b_oracle_driver.py:1186-1208`)。
- D78 自身が R commit をもって「移行契約により superseded」とする closure を裁定済みである (`docs/decisions.md:3209-3212`)。

したがって [T-068] は「元の方式 B をそのまま実装した」のではなく、より強い一回限りの移行契約によって承認どおり superseded された、と閉じるのが正確である。

### [T-077]

D78 の条件は「R の design_source 再 pin + generator M 化」である (`docs/decisions.md:3210-3212`)。

- production の固定仕様は holdout `/design_source/sha256` を source repin、known/holdout `/generator/sha256` を metadata spec として分離する (`orchestrator/campaign/t080_freeze_migration.py:100-120`)。
- receipt schema は source repin exact 13 件、metadata exact 2 件、metadata disposition exact `metadata-only` を要求する (`orchestrator/campaign/t080_freeze_migration.py:433-454`)。
- design source と両 generator の migration hash は basis commit の blob bytes から再計算し、receipt 値との一致を要求する (`orchestrator/campaign/t080_freeze_migration.py:984-1010`)。
- receipt の決定論 field 全体は H_mig から再導出されるため、receipt に自己申告 hash を書くだけでは `active-valid` にならない (`orchestrator/campaign/t080_freeze_migration.py:1061-1118`)。
- test 側には旧 recorded 値の独立 literal があり、production spec から動的生成していない (`orchestrator/tests/test_s8b_oracle_driver.py:71-89`)。
- post-R test は `repinned-to-basis-blob` と `metadata-only` の exact item を組み立てる (`orchestrator/tests/test_s8b_oracle_driver.py:1211-1227`)。

よって [T-077] の design repin と generator M 化は実体・schema・H_mig 再導出・test の四面で確認できる。

### [T-078]

D78 の条件は S2-4.6 の外部固定 fixture と predicate-only mutant の 1→0→1 である (`docs/decisions.md:3211-3212`)。

- 承認正本は path、root key、raw 3 行、SHA-256 を固定し、baseline 1 hit／predicate-only mutant 0 hit／revert 1 hit を要求する (`docs/freeze-permanent-design-s2.md:2058-2081`)。
- fixture bytes はその 3 行だけである (`orchestrator/tests/data/freeze_holdout_positive_control_v1.txt:1-3`)。
- test-side pin は production とは別ファイルに承認値を literal 固定する (`orchestrator/tests/t080_fixture_roots.py:9-15`)。
- production 側にも同じ path/root/hash を literal として持つ (`orchestrator/campaign/t080_freeze_migration.py:48-51`)。
- raw bytes hash と test/production literal の一致を別 node で検査する (`orchestrator/tests/test_s8b_holdout_freeze.py:63-73`)。
- mutant は fixture bytes を変えず、rratio predicate だけを 50→51 に変え、hit count を 1→0→1 と exact assert する (`orchestrator/tests/test_s8b_holdout_freeze.py:76-102`)。
- gate 側も fixture raw hash を独立に検査する (`orchestrator/campaign/t080_freeze_migration.py:1721-1727`)。

これは「fixture と期待値を同時に動かせば常に通る」形ではない。raw root、test literal、production literal、検索 predicate の四面が分離されている (`docs/freeze-permanent-design-s2.md:2060-2081`)。

### post-R pin と receipt 削除時

- 現在の R が reachable な限り、独立 helper は `None` にならず post-R branch に入り、production resolver が `never-issued` 等へ退行すれば `active-valid` assert が失敗する (`orchestrator/tests/test_s8b_oracle_driver.py:136-147`, `orchestrator/tests/test_s8b_oracle_driver.py:1186-1204`)。
- worktree または descendant commit で receipt を削除すると、history verifier は `receipt.issued_but_missing` を積む (`orchestrator/campaign/t080_freeze_migration.py:1686-1714`)。
- committed delete の状態遷移と再発行拒否にも専用 test がある (`orchestrator/tests/test_t080_freeze_migration.py:568-575`, `orchestrator/tests/test_s8b_oracle_driver.py:659-688`)。
- stub-free E2E も receipt unlink 後を `issued-but-missing` と exact assert する (`orchestrator/tests/test_s8b_oracle_driver.py:471-494`)。
- 一方、R を history ごと除去すれば helper は pre-R branch を許す (`orchestrator/tests/test_s8b_oracle_driver.py:1190-1199`)。これは固定 OID pin でないという限定であり、通常の additive commit による削除 fail-open ではない。

また現在の floor/budget refusal がある GateDecision 自体の observation は `None` であり、17 item は receipt resolution 側にある (`orchestrator/campaign/s8b_oracle_driver.py:111-123`, `orchestrator/tests/test_s8b_oracle_driver.py:1209-1212`)。docs ではこの二つを混同してはならない。

## 2. stale 記述の網羅列挙

### 2.1 現行正本として修正する箇所

| 箇所 | 現在の逐語 | 判定 |
|---|---|---|
| `docs/decisions.md:3115` | 「機構実装済み・人間 receipt 発行待ち」 | 現在虚偽 |
| `docs/decisions.md:3122-3123` | 「**発効はしていない** — 公式 gate は receipt 発行 (人間) まで現行 4 拒否のまま」 | 現在虚偽 |
| `docs/decisions.md:3150-3151` | 「receipt 不在時 **(現在)**: 現行挙動を…4 拒否 exact」 | `(現在)` と「現行」が虚偽。never-issued の条件契約自体は有効 |
| `docs/decisions.md:3206-3207` | 「機構実装済み・receipt 発行待ち…と記す (**R 前後どちらでも虚偽にならない**)」 | 「発行待ち」は R 後に虚偽で、状態中立という自己評価も誤り |
| `docs/worklog.md:966-971` | 「[T-088] ユーザー裁定待ち (U-1〜U-5)」「[T-068]…着手可能」「[T-077]…」「[T-078]…閉じる」 | U-5 は本依頼で確定し、3 件は「着手可能」でなく R 時点閉鎖済み |

### 2.2 worklog の過去エントリ

過去エントリは凍結され、直接書き換えてはならない (`docs/worklog.md:12-20`)。以下は現在状態として読めば stale だが、新規末尾エントリで supersede する。

- pre-R の次の一手:

  - `docs/worklog.md:83-85`: 「発効と同時に閉じる」「人間同席再 pin で解消」「外部固定 fixture 契約で再定義」。
  - `docs/worklog.md:171-173`, `docs/worklog.md:267-269`: 「それまで開いたまま」。
  - `docs/worklog.md:337-339`, `docs/worklog.md:406-408`, `docs/worklog.md:466-468`, `docs/worklog.md:522-524`, `docs/worklog.md:582-584`: closure 条件を「変わらず」と繰り越す。

- R 後にも未閉鎖扱いした次の一手:

  - `docs/worklog.md:633-635`, `docs/worklog.md:679-681`, `docs/worklog.md:724-726`, `docs/worklog.md:781-783`, `docs/worklog.md:830-832`: 「R commit で…確定」「…で閉じる。変わらず」。
  - `docs/worklog.md:866-868`, `docs/worklog.md:910-912`: 「承認済 (発行待ち)」。
  - `docs/worklog.md:969-971`: 「blocker 解消。承認済みで着手可能」。

- `docs/worklog.md:96` の見出し「機構完了・人間 receipt 発行待ち」と `docs/worklog.md:116-118` の「公式 gate は依然 4 拒否」は、2026-07-22 の pre-R 実装結果としては歴史的に正しいため修正対象外である。
- `docs/worklog.md:929-933` は発行済みを発見した歴史記録として正しいが、「要ユーザー確認 = U-5」までの当時状態なので、今回の新規末尾エントリで closure 確定を追記する。

アーカイブにも次の current-state 形式が残るが、すべて歴史記録として不修正とする。

- `docs/archive/worklog-phase3-0721-0722.md:145-147`, `:218-220`: 「[T-068] **裁定待ち (新規)**」。
- `docs/archive/worklog-phase3-0721-0722.md:353-354`, `:376`: 「[T-005] [T-068] は消化せず」「ユーザー裁定待ちへ差し戻し」。
- `docs/archive/worklog-phase3-0721-0722.md:451-468`: 「[T-068] **承認済み実装 wave**」「方式 B は…4 件 → 3 件」。
- `docs/archive/worklog-phase3-0721-0722.md:505-508`, `:537`, `:541-555`: 「ユーザー再裁定待ち」「[T-077] 裁定パッケージ」「[T-078] 裁定パッケージ」。
- `docs/archive/worklog-phase3-0721-0722.md:621-625`, `:679-683`, `:725-728`: 同じ 3 件を再裁定・再評価・待ちとして繰り越す。
- `docs/archive/worklog-phase3-0721-0722.md:751-753`, `:764-767`: 「それまで ID は開いたまま」「発効まで開いたまま」「実装まで開いたまま」。
- `docs/archive/worklog-phase3-0721-0722.md:814-816`, `:861-863`, `:910-912`: 同じ open 状態の反復。
- `docs/archive/worklog-phase3-0721-0722.md:952-954`, `:997-999`: closure 条件を「変わらず」として繰り越す。

### 2.3 過去 decisions／設計文書

次は後続 D78 に supersede された当時の裁定・設計であり、本文を書き換えない。

- D72 の「[T-068]…実装しない」 (`docs/decisions.md:2781-2785`)。
- D73 の「[T-068]…ユーザー再裁定へ戻す」 (`docs/decisions.md:2850-2855`, `docs/decisions.md:2884-2889`)。
- D75 の「いずれも本 wave では閉じていない」 (`docs/decisions.md:3021-3024`)。
- 第1設計段の「三件とも本書では閉じない」 (`docs/freeze-permanent-design.md:329-336`) と R10〜R12 の将来形 (`docs/freeze-permanent-design.md:413-420`)。同文書は design 段完了後に凍結する運用である (`docs/freeze-permanent-design.md:363-365`)。

### 2.4 output/insights の歴史スナップショット

以下は現在状態としては stale だが、逐語・裁定過程の凍結物なので修正しない。

- `output/insights/2026-07-21_s1-freeze-downgrade-loop.md:29`: 「公式 oracle gate の現在の拒否集合はちょうど 4 件」。
- `output/insights/2026-07-21_t067-exact-refusal-and-s1-repackage.md:7`, `:15`, `:1234`, `:1262`, `:1324-1334`, `:1368`: [T-068] を未実装／再裁定待ち、gate を 4 件とする当時の記録。
- `output/insights/2026-07-22_t080-freeze-permanent-design.md:19`: 「本設計の確定後に再評価 — 本 wave では閉じない」。
- `output/insights/2026-07-22_t080-freeze-design-stage2.md:35`: 「開いたまま…本 wave で閉じない」。
- `output/insights/2026-07-22_t080-migration-contract.md:93-98`, `:126-128`, `:632`: wave 中は receipt 未発効・4 refusal とする pre-R 記録。
- `output/insights/2026-07-22_t080-migration-contract.md:1015-1016`, `:1957-1958`: 「receipt 発行待ち」が R 前後とも正しいとする誤った「状態中立」評価。
- `output/insights/2026-07-22_t080-migration-contract.md:1662`: worklog を「receipt 発行待ち」と記録する実装計画。
- `output/insights/2026-07-25_t088-official-unlock-design.md:142-143`: 三件を「着手可能・承認済み」へ上げる U-5 案。
- `output/insights/2026-07-25_t088-official-unlock-design.md:155` と `output/insights/2026-07-25_t088-official-unlock-verbatim.md:242`, `:377`: `docs/phase3.md:89-94` も receipt 待ちで stale とする記述。現行 phase3 は既に「発行済み」へ是正されている (`docs/phase3.md:89-94`)。verbatim は裁定前の生出力を原文保存するファイルなので修正しない (`output/insights/2026-07-25_t088-official-unlock-verbatim.md:3-10`)。

### 2.5 状態中立・修正不要

- D78 の never-issued／active-valid／invalid の条件分岐自体は有効である (`docs/decisions.md:3147-3153`)。直すのは `(現在)` と「現行」だけ。
- D78 の「R commit 時点で確定」という closure rule は R 前後で意味が変わらない条件文なので残す (`docs/decisions.md:3209-3212`)。
- D78 の検証プロセスにある「前提実測: gate 4 拒否」は当時の実測履歴である (`docs/decisions.md:3194-3204`)。
- state machine の `never-issued → legacy 4 refusal` は条件付き契約であり current-state 主張ではない (`output/insights/2026-07-22_t080-migration-contract.md:934-942`, `:1681-1689`)。
- output README の「発効は人間 R commit のみ」は主体・方式の契約であり、「未発効」の主張ではない (`output/README.md:24`)。
- `docs/phase3.md:89-99` は receipt 発行済み・残 gate を正しく記録しており、三タスクの closure 一文を補うだけでよい。
- F35 は発行待ち誤記そのものを記録した failure で、現在も正しい (`docs/failures.md:477-498`)。
- orchestrator の docstring/comment に T-068/T-077 の stale 状態記述はない。T-078 の comment は production literal の所有説明である (`orchestrator/campaign/t080_freeze_migration.py:48-51`, `orchestrator/tests/t080_fixture_roots.py:2-15`)。
- `orchestrator/tests/test_s8b_oracle_driver.py:66-68` の「v2 未発効」は別の ratified-freeze v2 refusal literal で、T-080 receipt の状態ではない。

## 3. 各修正の具体案

### 3.1 `docs/decisions.md`

#### 見出し

対象: `docs/decisions.md:3115`

現在:

> `## D78. ... — 機構実装済み・人間 receipt 発行待ち (2026-07-22)`

置換案:

> `## D78. 一回限りの移行契約 (T-080 最小抽出) — 機構実装 2026-07-22・人間 receipt 発行／発効 2026-07-24`

#### 冒頭の現況断定

対象: `docs/decisions.md:3122-3123`

置換案:

> `output/insights/2026-07-22_t080-migration-contract.md。人間 receipt は 2026-07-24 の R commit 8bec195 で発行・発効済みである。発効実績と三タスクの closure は下記 (10) に記録する。`

#### never-issued の条件表現

対象: `docs/decisions.md:3150-3151`

現在:

> `receipt 不在時 (現在): 現行挙動を byte 単位で保存 (real-repo golden が 4 拒否 exact を pin)。`

置換案:

> `receipt が reachable history に一度も導入されていない never-issued 時: legacy 挙動を byte 単位で保存 (never-issued fixture が legacy 4 拒否 exact を pin)。`

これにより受理集合は変えず、current-state 語だけを除く。never-issued exact 4 refusal は既存 test が保持する (`orchestrator/tests/test_s8b_oracle_driver.py:1281-1288`)。

#### D78 (9) の誤った状態中立表現

対象: `docs/decisions.md:3206-3208`

置換案:

> `(9) **発効前の記録と発効手順。** 機構実装完了から R commit まで、docs は「機構実装済み・receipt 発行待ち。発効後の期待 = gate 拒否 {floor-null, budget-null} の 2 件 exact」と記録した。これは pre-R 引き渡し状態の記録であり、post-R の発効実績は (10) に追記する。発効はユーザーの draft 確認 → finalize → R commit → post-R 受入…`

後続の手順と closure 条件 `docs/decisions.md:3208-3212` は一字も落とさない。

#### D78 (10) の追記

挿入位置: `docs/decisions.md:3212` の後、D79 見出し `docs/decisions.md:3214` の前。

文案:

> `(10) **発効実績と closure (2026-07-24)。** ユーザーの R commit 8bec195 が canonical receipt を発行し、一回限りの移行契約を発効させた。receipt bytes は以後不変とし、再 finalize・再発行を行わない。本 closure wave の確認では receipt resolution は active-valid・receipt refusal 空で、source repin 13 件、generator metadata-only 2 件、ancestry 2 件の typed observation を構成する。公式 gate は allowed=False のまま、拒否集合は {floor-null, budget-null} の 2 件 exact であり、GateDecision observation は refusal が残るため null である。`
>
> `この R により (9) の条件が発火し、[T-068] は「移行契約により superseded」、[T-077] は design_source 再 pin + generator M 化、[T-078] は S2-4.6 外部固定 fixture と predicate-only 1→0→1 契約の充足として、いずれも R commit 時点で閉鎖済みと確定する。[T-088] の official gate 解禁と [T-011] の floor 実測は別裁定・別 wave であり、本追記は公式 gate の受理集合を変更しない。`

「typed observation」は receipt resolution 側であることを明記し、GateDecision の `None` と混同しない (`orchestrator/tests/test_s8b_oracle_driver.py:1209-1250`)。

### 3.2 `docs/phase3.md`

挿入位置: receipt/protocol 発効記録 `docs/phase3.md:89-94` の直後。

追記案:

> `D78 (9) の closure 条件は R commit 8bec195 で発火済みであり、[T-068] は移行契約により superseded、[T-077] は design_source 再 pin + generator M 化、[T-078] は S2-4.6 外部固定 fixture 契約の充足として、三件とも R commit 時点で閉鎖済み。`

既存の [T-088]/[T-011] 残 gate 記述 `docs/phase3.md:95-99` は変更しない。

### 3.3 `docs/worklog.md`

過去行を変更せず、EOF `docs/worklog.md:984` の後へ新規エントリを追加する (`docs/worklog.md:14`)。

文案の骨格:

```markdown
## 2026-07-25 (3) — [T-068][T-077][T-078] D78 R-closure 確定 (docs-only、コード・receipt・凍結成果物 0 byte)

ユーザーが D78 (9) の既承認 closure を確認。R commit 8bec195 で条件は既に発火済みであり、
三件を R 時点閉鎖として確定した。公式 gate 解禁 [T-088] と floor 実測 [T-011] は本 wave の scope 外。
機械証拠と現況追記の正本 = D78 (10) / docs/phase3.md 現行チェックポイント。
本 wave の pytest・check 実測値は親の実行後にのみ記録する。

### 消化した ID

- [T-068] **消化** — R commit をもって「移行契約により superseded」。
- [T-077] **消化** — R の design_source 再 pin + generator M 化。
- [T-078] **消化** — S2-4.6 外部固定 fixture と predicate-only 1→0→1 契約。

### 次の一手

1. [T-088] ユーザー裁定待ち (U-1〜U-4)。U-5 は本エントリで消化。U-1 未承認なら以降停止。
2. [T-011] 科学レーン floor 実測。残 gate は [T-088] 裁定 → PBS floor wrapper → 実行 revision 束縛 → lineage。
3. [T-090] VerifiedFreeze.document の mutable dict hardening 候補。1 cycle 後へ延期。
4. [T-085] PKG-1 採用裁定済。floor 実測後の hardening wave で実装。
5. [T-087] W-e 着手時に整合を決める裁定済。延期。
6. [T-089] 二重 reason-tag 描画の診断欠陥候補。延期。
7. [T-009] AGENTS.md 追記は 1 cycle 後。延期。
8. [T-060] WAL 用語運用の明文化は 1 cycle 後。延期。
9. [T-010] B-008 再試験は 1 cycle 後に再評価。延期。
10. [T-012] pilot 凍結維持。延期。
11. [T-082] 全 caller 移行は 1 cycle 後。延期。
```

これで最新「次の一手」の全 ID を消化または継続し、D70 の保存則を守る (`docs/worklog.md:25-41`, `docs/worklog.md:966-984`)。

### 3.4 既存制約の保持確認

上記変更は次を削除・変更しない。

- 最小抽出・恒久一般化の繰延・no-touch 宣言 (`docs/decisions.md:3117-3121`)。
- H_mig 再導出、ccbench、unknownness、schema/pairing の fail-closed 検査 (`docs/decisions.md:3136-3145`)。
- git-error／non-commit refusal の維持 (`docs/decisions.md:3147-3153`)。
- 承認済み残余・損失表 (`docs/decisions.md:3169-3186`)。
- receipt の byte 不変・再発行禁止 lifecycle (`docs/decisions.md:3188-3192`)。
- post-R 受入手順と三 closure 条件 (`docs/decisions.md:3206-3212`)。
- no-touch 12 file の完全な manifest (`output/insights/2026-07-22_t080-migration-contract.md:1887-1903`)。

## 4. 実装コードが必要か

**不要。P1 は正しい。**

理由:

- R topology、receipt history、post-R 削除拒否は既に production にある (`orchestrator/campaign/t080_freeze_migration.py:835-868`, `:1624-1718`)。
- T-068 の typed ancestry と拒否境界は実装済みである (`orchestrator/campaign/t080_freeze_migration.py:731-749`, `:1882-1900`)。
- T-077 の design repin／metadata-only／H_mig 再導出は実装済みである (`orchestrator/campaign/t080_freeze_migration.py:984-1010`, `:1061-1118`)。
- T-078 の外部固定 fixture、raw root、predicate-only mutant test は実装済みである (`orchestrator/tests/test_s8b_holdout_freeze.py:63-102`)。
- real-repo post-R test は production resolver から独立した history 判定を用いる (`orchestrator/tests/test_s8b_oracle_driver.py:136-147`, `:1186-1250`)。

P4 の固定 OID 非 pin は限定だが、R が祖先である現行履歴では receipt delete を見逃さないため、この closure wave で test を変更する必要はない (`orchestrator/campaign/t080_freeze_migration.py:1686-1714`)。

### 親が実施する受入確認

本回答では未実走。親は docs 適用後に以下を実行し、期待と異なれば closure commit を止める。

1. receipt verify が `active-valid`、receipt refusals 空であることを再確認する。entry point は `orchestrator/campaign/t080_freeze_migration.py:1851-1950`。
2. 少なくとも次の node を実走する。

   - `orchestrator/tests/test_s8b_oracle_driver.py:448-494`
   - `orchestrator/tests/test_s8b_oracle_driver.py:659-688`
   - `orchestrator/tests/test_s8b_oracle_driver.py:1186-1250`
   - `orchestrator/tests/test_s8b_holdout_freeze.py:63-102`

3. 公式 gate が `allowed=False`、refusal exact `{floor-null, budget-null}` のままであることを確認する。production の二拒否は `orchestrator/campaign/s8b_oracle_driver.py:415-418`、test expectation は `orchestrator/tests/test_s8b_oracle_driver.py:1205-1208`。
4. closure wave 基準 `1b9abd1` から receipt と no-touch 12 file の diff が空であることを確認する。対象リストは `output/insights/2026-07-22_t080-migration-contract.md:1887-1903`。
5. 親環境で全走、`python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py` を実行し、commit 後に `python3 tools/check_ai_provenance.py` を実行するという repo 規律に従う。
6. 実測結果は実際の出力だけを新 worklog entry に記録し、既提示の 2919/18 を機械的にコピーしない。

## 5. 変異事前登録の候補

**対象外。**

production/test コード変更を提案しないため、新しい mutant は登録しない。docs-only correction にコード mutant を捏造しても変更の検出力を示さない。

## 6. 親 brief の誤り・注意点

| 対象 | 判定 |
|---|---|
| P1 | **正しい。** closure に必要な production/test 面は実装済み (`orchestrator/campaign/t080_freeze_migration.py:1851-1950`, `orchestrator/tests/test_s8b_oracle_driver.py:1186-1250`)。 |
| P2 | **結論は正しいが説明に誤り。** stale 修正は conformance だが、現文「receipt 発行待ち」は実際には R 後に虚偽であり、もともと状態中立ではなかった (`docs/decisions.md:3206-3207`)。「状態中立契約への適合」ではなく「状態中立を意図したが失敗した文面の事実訂正」と書くべき。 |
| P3 | **正しい。** 新しい政策判断ではなく D78 (9) の発火実績なので、D78 (10) 追記が適切 (`docs/decisions.md:3206-3212`)。 |
| P4 | **現行履歴では正しい。ただし限定あり。** receipt delete は赤になるが、test は固定 R OID を pin せず、R を reachable history ごと除去した場合は pre-R branch を許す (`orchestrator/tests/test_s8b_oracle_driver.py:136-147`, `:1190-1204`)。現行の R 祖先不変条件下では nit のままでよい。 |
| P5 | **正しい。** F35 は `check_docs.py` 機械化を「追加候補」「未実装」と明記し、現在の恒久対応実体を DW-S01 に置く (`docs/failures.md:491-498`)。本 wave で族一般化しない。 |
| P6 | **closure 結論は正しいが、理由付けは不正確。** 元の [T-068] は `frozen_at_head` ancestry の格下げであり (`docs/archive/worklog-phase3-0721-0722.md:284-285`)、post-R に消えた二つの gate refusal は source/design drift である。移行契約は source repin と ancestry typed 化の両方を実装した (`orchestrator/campaign/t080_freeze_migration.py:1821-1838`)。[T-068] を閉じる直接根拠は「drift 2 件が消えたから方式 B と同値」ではなく、D78 (9) が明示的に superseded と裁定したこと (`docs/decisions.md:3209-3212`)。 |

追加の注意:

- 親の「observation の中身」は receipt resolution の observation と解釈すれば正しいが、現在の GateDecision observation は floor/budget refusal が残るため `None` である (`orchestrator/campaign/s8b_oracle_driver.py:115-122`, `orchestrator/tests/test_s8b_oracle_driver.py:1209-1212`)。D78 (10) では主体を明記する必要がある。
- [T-088] と [T-011] は現行 checkpoint でも残 gate であり、本 wave で status や受理集合を変更してはならない (`docs/phase3.md:95-99`)。
- no-touch 12 file と receipt に触れない docs-only 所有なら、不変条件 1〜4 と衝突しない (`output/insights/2026-07-22_t080-migration-contract.md:1887-1903`, `docs/decisions.md:3188-3192`)。

## 未確認事項

- pytest、receipt verify CLI、公式 gate、全走、`check_docs`、`check_codex_agents`、`check_ai_provenance` は本 sandbox では実走していない。
- 親提示の「2919 passed / 18 skipped」「provenance 333 件」等の実測値は独立再測定していない。
- 本プランの line 番号は現 HEAD `1b9abd1` の挿入前位置であり、追記後は後続行が移動する。
- R を reachable history ごと除去する rewrite に対する運用・remote 側防壁は本 wave の scope 外で、固定 OID test pin も提案していない。

---

# B. 段 3 敵対相談 レンズ A = 正しさ境界と防壁 (rc=0)

# NO-GO

R commit による裁定上の closure 発火自体は確認できるが、「機械証拠で確定的に閉じた・コード変更不要」は支持できない。  
post-R pin と H_mig 再導出の赤化保証に穴があり、D78 の in-place 置換は承認済み証拠を弱める。pytest・gate・各 check は未実走。

## 所見一覧

1. **[BLOCKER]** `orchestrator/campaign/t080_freeze_migration.py:1061-1118,1920-1944`、`orchestrator/tests/test_t080_freeze_migration.py:379-397`、`orchestrator/tests/test_s8b_oracle_driver.py:691-710`  
   production は現在 H_mig blob から決定論 field を再導出しているが、負例は内部 `_assert_deterministic_fields()` を直接呼ぶだけで、public `verify_receipt()` の `_verify_receipt_derivation()` を no-op にする変異を発火させる test がない。active fixture の一部は同関数を明示的に成功 stub 化している。  
   **成果物影響:** 手製 receipt の虚偽 `repin_report`・reconstruction hash が `active-valid` となり、試行台帳が本来拒否すべき campaign を開始し、receipt を参照する report の proof chain が虚偽値を指し得る。

2. **[BLOCKER]** `orchestrator/tests/test_s8b_oracle_driver.py:136-147,1186-1208`  
   real-repo test は R `8bec195` を pin せず、reachable history から receipt commit が消えると pre-R の 4-refusal 分岐を正解として受理する。通常の descendant delete は production が拒否する (`orchestrator/campaign/t080_freeze_migration.py:1686-1696`) が、R ごとの履歴除去には防壁がない。  
   **成果物影響:** closure docs を pre-R graph へ載せ直した状態でも検査が pre-R 状態を受理し、refusal が 2 件から 4 件へ戻り、17-item receipt observation とその参照が消える。

3. **[BLOCKER]** `tools/check_docs.py:24-27,297`、`docs/decisions.md:3115-3123,3206-3212`  
   repository 自身が decisions を「書いた時点で凍結した追記型記録」と分類している。プランの見出し・冒頭・(3)・(9) の in-place 置換 (`out/plan.md:162-194`) は、承認時の状態と誤りの発生履歴を消す。D78 (10) の additive erratum はよいが、既存本文の置換は不可。  
   **成果物影響:** 後続 report／裁定が参照する「R 前は4拒否」「Rが遷移境界」という承認済み履歴が失われ、どの受理集合をいつ承認したか追跡不能になる。

4. **[MUST]** `docs/decisions.md:3150-3153`、`orchestrator/tests/test_s8b_oracle_driver.py:721-729,1275-1288`  
   「receipt 不在」を `never-issued` と明確化する意味自体は production 状態機械と整合する。しかしプランは証拠を real-repo golden から、legacy verifier 二本を mock する hermetic fixture へ差し替えており、同値な証拠ではない。  
   **成果物影響:** legacy verifier 本体が freeze drift を見逃す退行でも mock が refusal を生成し、never-issued の拒否集合・将来の受理集合が変わったまま proof chain が成立し得る。

5. **[MUST]** `docs/decisions.md:3181-3182`、`orchestrator/tests/test_s8b_oracle_driver.py:1214-1249`  
   D78 (6)(f) は「H_mig 確定まで observed 値を literal pin 不能」と残余化したが、現在は H_mig が確定済みである。それでも real-repo test の13+2件の `observed` は receipt 自身から期待値を作っており、新 hash の独立 pin ではない。  
   **成果物影響:** R・receipt・production spec を整合的に差し替える履歴改変で、15件の observed hash・basis・receipt hash が変わっても、report の参照変更を独立面が検出しない。

6. **[MUST]** `orchestrator/campaign/t080_freeze_migration.py:456-480,1078-1089`、`docs/decisions.md:3169-3175`  
   `active-valid` は完全な非自己申告ではない。`live_scan_sha256` は64hex形式だけを検査し、H_mig 再導出対象から除外される。live scan 自体は別に再実行されるが、stored hash との一致は保証されない。これは D78 (6)(b) の承認済み残余であり、closure 追記で「全機械証拠が充足」と上書きしてはならない。  
   **成果物影響:** receipt raw hashを参照する report が、実走値から導出されていない `live_scan_sha256` を証拠の一部として保持する。

7. **[MUST]** `output/t080-migration/legacy-freeze-repin.receipt.json:1`、`docs/failures.md:15,477-498`、`docs/worklog.md:929-934`、`docs/phase3.md:89-94`  
   receipt の `confirmed_at` は 2026-07-23 であり、2026-07-24 は誤り。さらに failures ledger は追記専用なので、P7 の F35 本文直接修正は規律違反になる。プラン自身も誤日付を再転記している (`out/plan.md:164,172,204`)。  
   **成果物影響:** R 前後の trial／receipt／protocol chronology が1日ずれ、どの成果物が activation 前後に生成されたかという参照関係を誤る。

8. **[MUST]** `docs/worklog.md:763,819,901-902`、`output/insights/2026-07-24_e2e-real-seal.md:37`、`docs/failures.md:458-475`  
   4件の `<反映>` は F34 恒久対応の実行証拠にならない。`check_docs` も意味的な反映漏れを検出しないと明記する (`tools/check_docs.py:7-10`)。独立3 wave は族一般化条件を満たす (`docs/dev-wave/core.md:45-48`) ため、P8 の「新 gate なので見送る」は根拠不足。  
   **成果物影響:** docs commit 後に repo scan invariant が赤でも、試行台帳が wave を閉鎖済みとして扱い、汚染された repository state を次 campaign の基準にし得る。

9. **[SHOULD]** `orchestrator/campaign/s8b_floor_campaign.py:193-203,2646-2669`、`output/insights/2026-07-25_t088-official-unlock-design.md:126-143`  
   現在の official mode は依然無条件拒否である。D78 (10) では「T-080 migration receipt の発効」と「official mode activation」を別名で明示すべきで、単に「移行契約が発効」と書くと T-088 の U-1 を既成事実化しやすい。  
   **成果物影響:** Rをlaunch authorizationと誤読してofficial guardを外すと、official受理集合が空集合から非空へ拡大する。

## 親 brief の P1〜P8

- **P1 — 反対。** 裁定上の R-trigger は発火済みだが、機械的な恒真防止は未完成。代案は、固定 R OID／receipt hash の post-R test、public `verify_receipt()` で不正 `repin_report` を拒否する負例、H_mig確定値13+2件の独立 literal pinを先に追加すること。

- **P2 — 条件付き。** stale 状態の是正は必要だが、D78本文を置換せず、D78 (10) の erratum と phase3 現況更新で行う。日付は2026-07-23、確認時 HEAD も明記する。

- **P3 — 条件付き支持。** 新政策ではないためD78 (10)への追記でよい。ただし additive のみ。既存証拠を別 fixture に差し替えるなら新裁定または再承認が必要。

- **P4 — 反対。** `None` 枝はコード上到達可能で、R消失を正解化する。代案は real-repo test を `8bec195` の祖先性・blob hash必須へ変更し、pre-R契約は既存hermetic testだけで検査すること。

- **P5 — 条件付き支持。** 「発行待ち文言とreceipt実在」の専用lintは単発族として保留可能。ただし今回の日付誤記はF1型の再発なので、F1/F35へ追記erratumが必要。P8のplaceholder族とは分ける。

- **P6 — 支持。** [T-068] の直接根拠はD78 (9)の明示的 supersedeであり、drift 2 refusal消失との同値主張ではない (`docs/decisions.md:3209-3212`)。

- **P7 — 反対。** phase3は直接訂正、worklogは新規erratumでよいが、F35本文は置換せずerratum追記とする。元の誤りを保存する方が失敗台帳の防壁として強い。

- **P8 — 反対。** retroactiveな数値穴埋め禁止は支持する。しかし「当時の実行有無・結果は確認不能、緑の根拠に使用禁止」と4管所を列挙し、F36相当の失敗型と、新規placeholderを拒否するlintを入れるべき。既存4件はexact allowlistで歴史的欠測として固定する。

## プランへの判定

採用してよいのは、receipt・凍結成果物・productionを変更しない方針、phase3の現況訂正、worklogへの新規追記、[T-068]の理由訂正、GateDecision observationとreceipt-resolution observationの区別、[T-088]を別裁定とする境界である。

危険なのは、GO／docs-only断定、2026-07-24の転記、D78既存本文の置換、real-repo証拠からmock fixtureへの差替え、P4のnit扱い、placeholder検査の見送りである。修正版はtest-only防壁を含むため、もはやdocs-onlyではない。

D78の制約は次のように扱うべきである。

- `docs/decisions.md:3117-3121` の最小抽出・恒久一般化繰延・no-touchは保持。
- `docs/decisions.md:3136-3167` のH_mig再導出、layer2、git-error拒否、observation条件、人間性の非暗号学的限界は保持。
- `docs/decisions.md:3169-3186` の残余 (a)〜(g) はすべて「未解消のまま」とD78 (10)で明記する。特に (f) はH_mig確定により独立pin可能になった。
- `docs/decisions.md:3188-3192` のbyte不変・in-place supersede禁止は保持。
- `docs/decisions.md:3206-3212` の誤った「状態中立」自己評価は消さず、erratumで否定する。
- `receipt不在→never-issued` の語義明確化は妥当だが、証拠をmock fixtureへ置換しない。

[T-078] のpredicate-only 1→0→1は、静的には恒真ではない。fixture hash (`orchestrator/tests/test_s8b_holdout_freeze.py:63-73`)、mutant結果 (`:76-102`)、別のraw bytes literal (`orchestrator/tests/test_t080_freeze_migration.py:935-939`) が分離されており、fixtureとhashだけの同時変更では足りない。ただしtest本文・raw literal・predicateまで協調編集する攻撃はtest trust boundaryなので、「変更不能」ではなく「複数面レビューで検出する」と限定すべきである。

規律2・3との整合上、現在のproduction verifierを緩める変更はないが、赤化しない再導出変異を残したまま「閉じたので今後検査不要」と読む運用は防壁の実質緩和になる (`CLAUDE.md:65-74,93`)。

## 未確認事項

- pytest、receipt verify CLI、oracle gate、official mode、全走、`check_docs`、`check_codex_agents`、`check_ai_provenance` は実走していない。
- 親報告の2919 passed／18 skipped、provenance 333件は独立再測定していない。
- 上記変異のsurvival判定は参照探索と制御フローによる静的判定で、実際のmutation runではない。
- remote server側のbranch protection／force-push防止は確認していない。ローカルの`origin/main`参照がRを含むことだけ確認した。

---

# C. 段 3 敵対相談 レンズ B = 記録の整合と実効性 (rc=0)

# NO-GO

closure の実体は確認できるが、現プランは R 発行日を再び 1 日ずらし、凍結済み記録を上書きする。  
日付・append-only erratum・N2 の証拠区分・機械再検証可能な closure 記録を直した plan v2 なら docs-only で進められる。

## 所見一覧

### 親 A 節の独立突合

| 事実 | 判定 |
|---|---|
| R と発行日 | `git show/cat-file` で R=`8bec195d096f852fd2b47070aa18a3b151613f0a`、author/committer=`2026-07-23 21:49:33 +0900` を独立確認。receipt も `confirmed_at=2026-07-23T12:49:16Z`、`confirmed_by=thawk105` で一致する。`output/t080-migration/legacy-freeze-repin.receipt.json:1`、`output/insights/2026-07-25_t088-official-unlock-design.md:24-29` |
| receipt resolution | public `verify` を実行し、rc=0、`active-valid`、refusal 空、13 source-repin + 2 metadata + 2 ancestry を確認した。17 件の構成と fail-closed count は `orchestrator/campaign/t080_freeze_migration.py:1816-1848`。 |
| official gate | public `gate-check` を実行し、rc=2、`allowed=False`、拒否が `floor-null` / `budget-null` の exact 2 件、GateDecision observation=null を確認した。生成条件は `orchestrator/campaign/s8b_oracle_driver.py:111-123,415-418`。 |
| 三件の closure 条件 | `[T-068]/[T-077]/[T-078]` を R 時点で閉じる裁定は D78 (9) に逐語で存在する。`docs/decisions.md:3206-3212` |
| 全 pytest | **独立実走していない**。親ログに 2919 passed / 18 skipped / rc=0 があることだけ確認した。`/home/SFC/tanab/.claude/jobs/c4f664a6/tmp/wave-t068-closure/logs/baseline-full.log:49-50` |

### Findings

- **[BLOCKER] 本 wave 自身が F35 と同じ日付ドリフトを再現している。** 一次資料は 2026-07-23 なのに、プランは D78 見出し・冒頭・(10) に 2026-07-24 を再掲する。`output/t080-migration/legacy-freeze-repin.receipt.json:1`、`/home/SFC/tanab/.claude/jobs/c4f664a6/tmp/wave-t068-closure/out/plan.md:164,172,204`。既存誤記は `docs/failures.md:479`、`docs/worklog.md:930`、`docs/phase3.md:89` の三箇所である。  
  **成果物影響:** certified 選択値・受理集合は直ちには変わらないが、レポートと試行台帳が R の provenance を誤った日付へ結び、後続監査の参照時点が 1 日ずれる。

- **[BLOCKER] D78 の既存本文を置換する案は凍結記録の改竄になる。** リポジトリ自身が decisions を「書いた時点で凍結された追記型記録」に分類しているのに、プランは見出し・導入・条件表現・(9) を直接置換する。`tools/check_docs.py:24-27,295-300`、`/home/SFC/tanab/.claude/jobs/c4f664a6/tmp/wave-t068-closure/out/plan.md:152-196`。2026-07-22 時点の「未発効」「receipt 不在時」は当時の歴史として真であり、誤りは「R 前後どちらでも虚偽にならない」という自己評価である。`docs/decisions.md:3115-3123,3147-3153,3206-3208`。代案は、既存 byte を残して D78 (10) に発効実績と (9) の erratum/supersession を追記すること。  
  **成果物影響:** 上書きすると proof-chain report から pre-R→post-R の状態遷移が消え、どの受理集合がいつ有効だったかを後から復元できなくなる。

- **[MUST] P7 の F35 直接修正は failures ledger の append-only 契約違反である。** 同型再発は既存項目に `再発: 日付` を追記して顕在化させる契約で、原文置換ではない。`docs/failures.md:10-16`、親案は `context.md:97-99`。F35 の誤った 2026-07-24 は残し、例えば「再発: 2026-07-25 — F35 自身が R 日付を誤記。正しくは 2026-07-23」と追記すべきである。`docs/failures.md:477-498`。  
  **成果物影響:** 直接修正すると F35 の「再発ゼロ」という台帳指標が偽に改善され、将来のレポートが恒久対応の実効性を過大評価する。

- **[MUST] N2 を一括して「当時の値は記録されなかった」とするのは事実に反する。** E2E の placeholder は既に前 wave の裁定パッケージで既知だったため、N2 全体を「新事実」とする主張も正しくない。`output/insights/2026-07-25_t088-official-unlock-design.md:155-156`。また T086 と T067 の全走値自体はそれぞれ 2919/18 として残っている。欠けているのは主として「その docs commit 後の check/repo-scan 結果」である。`output/insights/2026-07-24_t086-keyset.md:57-60`、`output/insights/2026-07-25_t067-exact-residual.md:80-83`。したがって erratum は wave/field ごとに「全走値あり」「post-record 検査の durable record なし」「E2E は受入値自体を確認不能」と分ける必要がある。  
  **成果物影響:** 一括して未記録とすると既存の試行結果を受理証拠から誤って除外し、逆に「実行されなかった」と断定すると trial ledger の実行履歴を捏造する。

- **[MUST] placeholder 検出は今すぐ実装せず、ただし stable ID 付き裁定パッケージへ送るべきである。** 三つの独立 wave に同型欠陥があり、既存 artifact path も明示できるため DW-G03/G04 の実装資格自体は満たす。`docs/worklog.md:763,819,902`、`output/insights/2026-07-24_e2e-real-seal.md:37`、`docs/dev-wave/core.md:45-53`。しかし whole-tree lint は既存四件を直ちに赤にし、引用例・verbatim・歴史記録まで誤検出するため、既知例の fingerprint allowlist、worklog rotation、対象ファイル族の設計が先に必要である。現プランの次の一手にはこの裁定 atom の ID がない。`/home/SFC/tanab/.claude/jobs/c4f664a6/tmp/wave-t068-closure/out/plan.md:240-252`。  
  **成果物影響:** ID なしで送ると機械化 finding が次 wave で消え、未実走の placeholder を受入済みとして参照するレポート／試行台帳が再発し得る。

  裁定パッケージでは、候補検出対象を少なくとも `<反映>`、`<受入結果を反映>`、`<受入全走結果を反映>` の exact literal、対象を `docs/worklog.md`、`docs/archive/worklog-*.md`、非-verbatim の `output/insights/*.md` とし、既存四件は path だけでなく「含有行 digest + token count」で固定する案を比較すべきである。単なる `<[^>]*反映[^>]*>` は日本語メタ変数や欠陥説明の引用を誤検出する。

- **[MUST] 「三件を閉じた」という散文だけでは機械的に再確認できない。** D78 (10) 案は短縮 OID、件数、状態だけで、完全な R/basis/validation HEAD、receipt raw SHA、`confirmed_at`、再現コマンドと期待 rc、task→predicate→evidence の対応を保持しない。`/home/SFC/tanab/.claude/jobs/c4f664a6/tmp/wave-t068-closure/out/plan.md:198-208`。verifier は receipt SHA、basis、validation HEAD、17 items を既に機械出力できる。`orchestrator/campaign/t080_freeze_migration.py:1841-1848`。D78 は結論だけに絞り、別の authority-none closure evidence JSON/insight に完全 OID、canonical path、digest、二つの public command、期待 rc/JSON、三 task の predicate map を残すべきである。`output/README.md:45-52,70`。  
  **成果物影響:** 現案では後日の監査者が同じ受理集合を再構成できず、report の「closed」参照が現在の receipt/history に対応するか機械判定できない。

- **[SHOULD] D70 の既存 ID 保存則は通るが、意味上の atom が検査網から落ちている。** 機械照合した source/sink 集合はいずれも `{T-009,T-010,T-011,T-012,T-060,T-068,T-077,T-078,T-082,T-085,T-087,T-088,T-089,T-090}` で、**前エントリ由来の欠落 ID はゼロ**である。`docs/worklog.md:962-984`、`plan.md:234-252`。ただし U-1〜U-5 を一つの `[T-088]` に詰め、U-5 だけ消化しながら同じ ID を継続する案は「1 atom = 1 ID」に反する。`docs/worklog.md:32-40,966-968`、`plan.md:242`。  
  **成果物影響:** U-5 の消化と U-1〜U-4 の未裁定が機械的に区別できず、official gate の受理集合を変更する atom が誤って完了扱いされ得る。

- **[SHOULD] 2026-07-24 の一括置換は禁止すべきである。** 正すべき receipt 発行日の三箇所とは別に、2026-07-24 は post-R test wave の実施日、protocol 実凍結日、selector/E2E 実施日として正しい。`docs/worklog.md:597-604`、`docs/phase3.md:93-96`、`output/insights/2026-07-24_t080-postr-test-debt-fix.md:3-10`。また `output/insights/2026-07-25_t088-official-unlock-design.md:30` は「2026-07-24 (1) worklog」を指すので変更対象外である。  
  **成果物影響:** blanket replacement は protocol/seal/test の report provenance まで 2026-07-23 に誤接続し、複数成果物の参照時系列を壊す。

- **[NIT] docs-only である以上、全 pytest 再走を必須とするプランは過剰である。** 「実装しない」裁定では変異 matrix と受入全走を射程外と明記する契約である一方、記録 commit 後の repo-scan invariant と影響検査は必要である。`docs/dev-wave/core.md:61-68,76-81`、`plan.md:283-299`。成果物値への直接影響はなく、実行コストの問題に留まる。

### stale sweep の結論

追跡済み `docs/**` と `output/insights/**` を `receipt/発行/発効/待ち/未発効/4拒否/8bec195` の別表現で検索した範囲では、追加で直接修正すべき receipt 日付誤りは上記三箇所だけだった。旧 worklog、archive、D72/D73、T088 insight/verbatim に残る pre-R 表現は当時の凍結記録であり、本文を直さず新しい erratum/status record から supersede させるべきである。`tools/check_docs.py:24-27,295-300`、`output/insights/2026-07-25_t088-official-unlock-design.md:142-156`。

## 親 brief の P1〜P8

| 項目 | 判定 | 理由・代案 |
|---|---|---|
| P1 | **条件付き支持** | R と verifier/gate の closure predicate は充足しており、production/test 実装は不要。`docs/decisions.md:3209-3212`、`orchestrator/campaign/t080_freeze_migration.py:1816-1848`。ただし記録の再現可能性を補う docs/output artifact は必要。 |
| P2 | **反対** | D78 は dated/frozen decision で、現在状態の living doc ではない。`tools/check_docs.py:24-27`。既存本文を置換せず、D78 (10) に発効実績と (9) erratum を追記する。 |
| P3 | **支持** | 新 D は不要。既存裁定の発火実績なので D78 (10) が妥当。`docs/decisions.md:3206-3212`。 |
| P4 | **条件付き支持** | `independent is None` は additive history では到達不能だが、history rewrite なら再び到達し得る。`orchestrator/tests/test_s8b_oracle_driver.py:1186-1204`。この wave では触らない。 |
| P5 | **支持** | F35 の receipt-waiting 検出は同型独立二例がなく、裁定パッケージ送りでよい。`docs/failures.md:491-497`、`docs/dev-wave/core.md:45-48`。ただし stable ID を付ける。 |
| P6 | **支持** | closure の直接根拠は drift 件数の同値性ではなく D78 (9) の explicit supersession である。`docs/decisions.md:3209-3212`。 |
| P7 | **反対** | phase3 は living doc なので直接修正、過去 worklog は新 erratum でよい。`docs/README.md:18-20`。F35 は原文を変えず `再発:` 追記にする。`docs/failures.md:15-16`。日付は 2026-07-23。 |
| P8 | **条件付き** | retroactive 穴埋め禁止は支持するが、「当時の値は記録されなかった」という一括断定は反対。既存全走値と欠けた post-record 検査を field 単位で分ける。機械検出は今 wave では送るが、DW-G03/G04 未充足ではなく例外設計と scope の問題として stable ID 付きで送る。`docs/dev-wave/core.md:45-53,61-68`。 |

## プランへの判定

採用してよい部分:

- public verifier/gate による `[T-068]/[T-077]/[T-078]` の closure mapping。
- receipt resolution の 17-item observation と、refusal が残る GateDecision observation=null の区別。`orchestrator/campaign/s8b_oracle_driver.py:111-123`。
- D78 (10) への追記、phase3 の living checkpoint 更新、最新 worklog で三 ID を消化する方針。
- official gate `[T-088]` と floor `[T-011]` を変更せず、歴史 worklog/insight/verbatim を直接直さない方針。`docs/phase3.md:95-99`。

危険な部分:

- D78 の既存本文を置換すること。
- 2026-07-24 を再掲すること。
- F35 原文を直接直すこと。
- N2 を「全値未記録」と一括処理し、既知 finding を新事実扱いすること。
- closure の根拠を短い prose だけに置き、完全 OID・digest・再現 command を残さないこと。
- placeholder 機械化パッケージを次の一手の stable ID に載せないこと。
- worklog 骨格が索引の 10〜15 行を超えて D78/phase3 を再説明していること。`docs/worklog.md:16-23`、`plan.md:226-253`。

以上を直せば、docs-only は「やった感だけ」の空 wave ではない。phase3 の誤日付・最新 worklog の三件未閉鎖扱い・F35 再発・N2 の空証明を訂正することは、将来作業者の task selection と report provenance を実際に変える。逆に P4 の branch、二種の lint 実装、T088 解禁、T011 floor 実測は scope 外に維持すべきである。`docs/dev-wave/core.md:61-73`。

## 未確認事項

- pytest は一件も実行していない。2919 passed / 18 skipped は親ログを読んだだけで、私の独立 green 主張ではない。`/home/SFC/tanab/.claude/jobs/c4f664a6/tmp/wave-t068-closure/logs/baseline-full.log:49-50`
- placeholder 各 wave の「実際には検査したが記録だけ失敗した」可能性は否定できない。確認できたのは、T086/T067 の pre-record 全走値と、post-record 結果欄が durable record に残っていないことだけである。`output/insights/2026-07-24_t086-keyset.md:57-60`、`output/insights/2026-07-25_t067-exact-residual.md:80-83`
- stale sweep は tracked text の `docs/**` と `output/insights/**` が中心で、全 raw output、外部一時ログ、binary、remote-only history は網羅していない。
- read-only のため修正後の `check_docs`、repo-scan invariant、影響検査は未実施である。現行 `check_docs` と provenance check は実行したが、`check_docs` 自身が意味的ドリフトを検出しない限界を明記している。`tools/check_docs.py:4-10`
