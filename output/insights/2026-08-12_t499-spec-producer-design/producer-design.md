# 8b oracle reviewed spec producer の設計

`output/s8b-oracle-spec/reviewed_spec.json` へ人間承認済み bytes を配置するまでの手順の設計。

**本 wave は設計のみで実装差分ゼロ。** durable artifact を発行せず、`APPROVED_SPEC_SHA256` を
書かず、contract test を変更していない。ここに書いた実装項目はすべて別タスクである。

- 検証: 段 2 プラン子 + 段 3 敵対 2 本 (正しさ境界レンズ / 整合・実効性レンズ) + 親の独立実測
- 関連: `d302-schema-choice.md` (schema 択一)、`preregistration-approval-package-draft.md` (事前登録値)

---

## 1. 現状の実測

### 1.1 承認 gate が実際に見ているもの

`orchestrator/campaign/s8b_oracle_spec.py:182-200` `_load_approved_spec_bytes`

1. `APPROVED_SPEC_SHA256` が `None` なら `no-approved-spec` で拒否 (現在ここ)。
2. `SPEC_REL` の bytes を読み、SHA-256 が pin と一致しなければ拒否。

続いて `load_approved_spec` (`:258-275`) が strict canonical parse、canonical bytes の
byte-for-byte 一致、`validate_reviewed_spec` の全 schema 検査 (schedule 再生成一致、
run contract、campaign 一対一、binding、generator の**実 byte hash**) を通す。

**git provenance は一切見ない。** `_assert_user_commit` (`s8b_ratified_freeze.py:537`) は
freeze v2 の approval / pointer / revocation / cancellation record 専用で、
呼び手 4 か所すべてが同 module 内 (`:1113,:1128,:1143,:1156`)。
**oracle spec 経路からは呼ばれない。**

> 裁定控え `2026-08-12-t499-approval-turns-blocked.md` の
> 「`_assert_user_commit` の要求を満たす形で spec bytes を配置する」は前提の取り違えである。
> spec 側にその要求は存在しない。**課すかどうかは新規の設計判断である。**

### 1.2 内容束縛は恒真ではない (D302 は効いている)

D302 が禁じた「manifest に正しい spec hash を書くだけで通る」形は再導入されていない。
`verify_manifest` は schedule / campaign IDs / run contract / binding / 除外理由 /
generator versions を approved snapshot から再導出して完全比較する
(`s8b_oracle_manifest.py:1095-1129`)。**この層は健全である。**

### 1.3 TOCTOU 契約も守られている

`load_approved_spec` は fixed path を 1 回だけ読み、`validate_approved_spec_snapshot`
(`:203-255`) は disk を再読せず捕捉済み snapshot を再束縛する。driver も spec を 1 回だけ
load して同じ snapshot を manifest verification と gate に渡す
(`s8b_oracle_driver.py:1213-1237`)。**再読込へ戻してはならない。**

---

## 2. must-fix — 設計上の欠陥 4 件

段 3 の敵対レンズが挙げ、親が一次資料で確認した。**schema version をどちらにしても残る。**

### 2.1 人間承認が機械強制されていない (最重要)

**欠陥:** 現行の code pin も、段 2 プランが推奨した「receipt + code pin」も、
**同じ実装担当がすべて作成できる。** AI が bytes・hash・receipt・pin を作った場合でも、
値の一致検査はすべて通る。staged diff を人間が review する手順は**手続きであって、
runtime に機械表現されない。**

**T-810 は先例にならない (親の M7 を撤回する)。** 実測すると T-810 の prereg artifact 自身が

- `limitations.approval_receipt_trust_root_absent = True`
- `protocol.run_authorized = False`
- `authorization.stage1_satisfied = False`

を宣言し (`orchestrator/campaign/t810_preregistration.py:434-458`)、
`request_t810_launch` には**正例が構造的に存在しない** (常に例外送出、同 `:798-803`)。
すなわち T-810 は「trust root が無いことを明記した休眠 seal」であり、
**動いている承認機構の先例ではない。**

**成果物影響:** AI が選んだ `n` / seed / campaign ID / binding / run contract が
「人間承認済み」として candidate と official verdict へ流れ、winner と台帳 identity を変えうる。

**設計方針 (実装は別タスク):**
**AI が書けない trust root を必須にする。** 例: repo 外の allowlist key による detached
signature、または allowlist 済み署名 commit が exact spec hash / receipt scope / freeze SHA /
approval ID を署名し、production loader が検証する形。
**利用可能な trust root が無い間は、配置機構を実装しても有効化せず fail-closed に保つ。**

`_assert_user_commit` 相当 (非 merge・逐語 `AI-Agent: none`・祖先性) を spec 経路へ足すのは
履歴 topology の defense-in-depth として有用だが、**単独では人間承認を証明しない。**
`AI-Agent: none` は commit message の文字列であり誰でも書ける
(`docs/ai-provenance.md` は AI 非関与の宣言として定義するだけ)。
**「これで人間承認を機械確認した」と書いてはならない。**

### 2.2 lifecycle の状態機械が閉じていない

**欠陥:** 「spec があるなら」「candidate があるなら」という条件列では、次が未拒否のまま残る。

- pin だけがあり spec が無い / spec はあるが receipt が無い
- receipt が複数ある
- 複数 candidate、同一内容の別 path (candidate writer は root 以下の任意の深さを許す、
  `s8b_oracle_manifest.py:882-892`)
- broken symlink・FIFO・socket・symlink directory
  (現行 test も `is_file()` が偽の entry を数えない)
- receipt が指す freeze と現在の active freeze が異なる
- spec-only 状態で source / freeze が承認時から stale

**設計方針 (実装は別タスク):** exact な 3 状態を列挙し、全 namespace を `lstat` / no-follow で
列挙してその他の entry を種類を問わず拒否する。

| 状態 | 条件 |
|---|---|
| `UNAPPROVED` | pin `None`、receipt / spec / candidate すべて 0 件 (= 現在) |
| `APPROVED` | authenticated receipt 1、fixed-path spec 1、pin / hash / full validation 完全一致、candidate 0 |
| `CANDIDATE` | 上記に加え hash-derived fixed-path candidate 1、同一 snapshot と active freeze に対する full verify 成功 |

**同じ状態機械を test だけでなく production loader からも必須にする。**
contract test は runtime guard ではない (`d302-schema-choice.md` §2)。
receipt を test と staged checker だけが見る設計では、
4 つの production consumer が通る `load_approved_spec` の runtime gate に receipt が入らない。

### 2.3 pin 設定後から本走までの同時 drift が閉じていない

**欠陥:** loader は worktree の `SPEC_REL` を通常の `Path.read_bytes()` で読み
(`s8b_oracle_spec.py:189-196`)、pin source / spec namespace / receipt が HEAD blob と
一致することを検査しない。freeze 側の clean check も `output/s8b-freeze` だけである
(`s8b_ratified_freeze.py:346-356`)。

→ pin と bytes の**片方だけ**の差替えは hash mismatch で落ちるが、
**両方が対応して dirty になった状態は runtime で拒否されない。**
writer の `O_NOFOLLOW` は初回作成を守るが、後の loader は symlink を拒否しない。

**設計方針 (実装は別タスク):** HEAD を 1 回捕捉し、spec・receipt・approval authority を
同じ H の regular blob から読む H-pure loader にする。少なくとも関連 namespace と
pin authority source の HEAD / worktree 一致、no-follow regular-file 検査を runtime で要求し、
その後は現行どおり immutable snapshot を共有する。

### 2.4 binding の交差照合が one-shot marker 作成より後にある

**欠陥:** spec validator が binding に要求するのは cell 集合と自己 hash の整合だけ
(`s8b_oracle_manifest.py:487-537`)。`build_approved_manifest` も holdout / configuration の
軸だけを比較し、spec の binding をそのまま candidate へ渡す (`:1190-1225`)。
`verify_manifest` は manifest binding と spec binding の一致しか見ない (`:1118-1124`)。

authoritative な binding は `LaunchValidatedFreeze.binaries_by_cell`
(`s8b_ratified_freeze.py:1640-1719`) にある。しかし driver が実 binding と manifest binding を
比較するのは、**campaign marker と campaign-start を作った後**である。実測で確認した。

- `_ensure_campaign` + `campaign-start` の記録: `s8b_oracle_driver.py:1333-1345`
- 実 binding の比較 (`binding-refused`): 同 `:1440-1448`

→ **誤 binding は spec loader でも launch validation でも止まらず、初回 run を
protocol violation にして同じ freeze の再走を塞ぎうる。**

同様に `run_contract.ccbench_pin` は manifest 層では非空 identifier としか検査されず
(`:396-404`)、**ratified floor artifact の `ccbench_pin` との完全一致は誰も見ていない。**

**成果物影響:** 誤 binding は certified 選択を indeterminate にして freeze の one-shot run を
消費する。`ccbench_pin` 不一致は correctness 用 materialization と floor / performance binary の
source revision 同一性を保証できなくし、certified 値の正当性そのものを侵食する。

**設計方針 (実装は別タスク):** `LaunchValidatedFreeze` と approved spec を受け取る
必須 cross-validator を設け、**marker / WAL / budget 作成の前に**次を完全一致させる。

- 全 cell の `spec.binding_identity` と `binaries_by_cell[*].binding`
- `run_contract.ccbench_pin` と floor artifact の `ccbench_pin`
- receipt の freeze SHA と active ratified SHA
- run contract の env / contract と active environment authority

producer・install checker・candidate builder・runtime preflight が同じ検証済み snapshot を使う。

---

## 3. producer 本体の設計

### 3.1 所在

| 選択肢 | 得失 | 判断 |
|---|---|---|
| `s8b_oracle_spec.py` に CLI を追加 | validator に近いが、approval loader と生成・書込 capability が同居する | 非推奨 |
| **別 module に producer CLI** | loader を read-only authority のまま保てる。freeze / 環境契約 / binding 導出を producer 側へ隔離できる | **推奨** |
| 人間が bytes を直接配置 | compact canonical JSON、schedule hash、12 cell の binding、実 source hash を手作業で一致させる必要がある | 却下 |

推奨は別 module (仮称 `orchestrator/campaign/s8b_oracle_spec_producer.py`) で、
**`preview` と `install-approved` を分ける。**

- `preview` — canonical bytes・SHA-256・人間可読な射影を標準出力または承認パッケージへ返す。
  **公式 2 directory には 1 byte も書かない。**
- `install-approved` — 明示的なユーザー承認の後にのみ、再導出した hash が承認 authority と
  一致する場合に固定 path へ create-only で配置する。**任意 `--output` を持たせない。**

### 3.2 生成手順 (validator が要求する順)

1. `schedule_parameters` を exact 5 key で構成する
   (`n` / `master_seed` / `block_sizes` / `holdout_ids` / `configuration_ids`、
   `s8b_oracle_spec.py:35-41,112-121`)。
2. `build_schedule` だけを使って schedule を再生成する (`s8b_oracle_manifest.py:221-270`)。
   **block は正確に 1 件でなければならない** — `build_schedule` 自体は複数 block を許すが
   manifest の単一 block 契約が拒否する (`_validate_schedule:303-305`)。
3. `schedule_sha256(schedule)` を再計算して記録する。loader も同じ再計算との一致を要求する
   (`s8b_oracle_spec.py:131-137`)。
4. `campaign_ids` を block ID 集合と一対一にし、値も重複させない (同 `:147-158`)。
5. `run_contract` を exact 9 key にする (固定値は `preregistration-approval-package-draft.md` §3.1)。
6. `binding_identity` を全 schedule cell に 1 件ずつ置く。
   **freeze JSON の entry を手で写してはならない** — materializer が freeze entry と
   prepared binary から導出する (`s8b_materialization.py:98-146`)。
   authoritative source は `LaunchValidatedFreeze.binaries_by_cell` である。
7. `generator_versions` を exact 5 source の canonical path と実 byte hash で記録する
   (`s8b_oracle_manifest.py:53-62,430-470`)。**producer 自身を 6 件目として足すことはできない**
   (exact key 集合)。producer の provenance は承認 authority と code review で表現する。
8. `allowed_excluded_reasons` を非空文字列の重複なし list にする (`s8b_oracle_spec.py:171-177`)。
   **floor の 4 理由を流用してよいかは独立の承認事項** (同 §3.6)。
9. `validate_reviewed_spec` を通した後、`_manifest._canonical_bytes` で
   sort_keys / compact separator / UTF-8 / 非有限値拒否の bytes にする。
10. その bytes を strict loader へ戻し、duplicate key・不正 UTF-8・非有限値を拒否したうえで
    再 canonical 化した bytes と byte-for-byte 一致させる
    (`s8b_oracle_artifacts.py`、`s8b_oracle_spec.py:258-269`)。

**producer 自身の builder だけを信頼せず、production loader と同じ最終検査を通す。**

### 3.3 書込作法

`_write_approved_manifest` (`s8b_oracle_manifest.py:895-987`) の安全性を踏襲する —
dirfd 単位の traversal、`O_NOFOLLOW | O_DIRECTORY`、leaf の `O_EXCL`、regular-file 検査、
partial write を考慮した write loop、leaf と親 directory の `fsync`、
失敗時に同一 inode の partial leaf だけを回収。

**ただし直接再利用はできない** — この関数は pretty JSON と末尾 LF を生成する (同 `:903-905`)。
reviewed spec は compact canonical bytes を要求する。
dirfd primitive を byte 指向 helper として抽出するか、同じ安全契約を専用 writer に実装する。

### 3.4 `APPROVED_SPEC_SHA256` を書く手順

**前提: §2.1 の trust root が実在すること。** 無い間は配置しない。

1. schema 判断 (`d302-schema-choice.md` §6)、producer、lifecycle gate、
   approval authority loader を先に実装・commit する。この時点でも
   **公式 2 directory は空、pin は `None`** のまま。
2. clean HEAD と active ratified freeze を固定し、producer が exact bytes と SHA-256 を生成する。
3. 承認パッケージで全値・decoded JSON・raw byte SHA・active freeze・source hash を提示する。
   **ユーザーは hash ではなく内容を承認する** (D302: 「hash は識別子にすぎず、承認は内容の
   再導出を伴う」)。
4. 承認後、同じ clean HEAD から bytes を再導出し、承認 hash との一致を機械確認する。
5. **bytes・approval authority・pin を単一の staged change に置く。**
   bytes だけの commit と pin だけの commit に分けない。
6. 独立 checker が working tree ではなく **staged blob** の hash・staged pin・authority・
   strict loader・full validator の一致を検査する。
7. ユーザーがその staged diff を review して単一 commit にする。push は人間が行う。

**TOCTOU について:** 配置から pin 記入までの窓では pin が `None` なので loader は
fail-closed である。履歴上の分離は単一 commit で閉じ、commit 直前の差替えは staged blob 検査で
閉じる。**ただし §2.3 の「pin 設定後から本走までの同時 drift」はこの手順では閉じない。**

---

## 4. 承認の有効期間

承認済み spec が有効なのは、次のすべてが承認時 snapshot と一致している間だけである。

- generator 5 source の byte hash / active ratified freeze の generation と pointer /
  floor artifact (と binary hash) / 実行環境契約 / `ccbench_pin` / exact spec bytes

いずれか 1 つでも変われば expired で、再導出と再承認が要る。
**これは silent drift ではなく安全側の停止である** —
5 source のいずれかが変われば approved spec は拒否され、certified report は生成されない。

`generator_versions` が pin する 5 source は、直近 30 日で 40 commit の変更を受けている
(一意 commit 数。path 別の延べ数とは異なるため、数える規則を明記した)。
**「数日で自壊する」は必然ではなく、正確には「対象 source の次の変更時に意図どおり
fail-closed になる」である。** したがって、

> 最終承認は、この 5 source の改修が実質的に止まってからでなければ意味を持たない。

これは [T-499] Q1 = (b) の判断 (承認手番を今引き、先に設計を作る) を独立に裏づける。

**final approval / install の diff がこの 5 本を変更していないことを機械確認し、
変更時は hash の自動追随ではなく新しい exact bytes と再承認を要求する。**

---

## 5. 先行 blocker — 現在の律速は spec ではない

1. **active ratified freeze v2 が存在しない。** live pointer が無ければ `no-active`
   (`s8b_ratified_freeze.py:1214-1256`)。`build_approved_manifest` は spec より先に
   active freeze を読むため、spec を承認してもここで止まる。
2. **floor / budget が null。** driver は v2 実走を拒否する (`s8b_oracle_driver.py:469-472`)。
3. **official guard ([T-088]) が未解禁。** pilot 成果物は `eligible_for_refreeze=false`
   (`docs/phase3.md:118-122`)。
4. `BUDGET_APPROVAL_SHA256 = None` ([T-499] (B) の対象)。

→ **現在の先行 blocker は `no-approved-spec` ではなく `no-active-ratified-freeze` である。**

---

## 6. 別タスクへ分離する実装項目

本 wave では 1 つも実装しない。理由を添えて列挙する。

| 項目 | 分離理由 |
|---|---|
| 外部 trust root による authenticated approval receipt | 正しさ防壁の新設。設計択一 (署名方式・鍵の所在) がユーザー裁定を要する |
| H-pure / no-follow な approved-spec loader | production loader の受理集合を変える。単独で裁定と変異事前登録が要る |
| exact 3 状態 lifecycle gate と runtime 接続 | contract test の置換を伴い、受理集合が真に広がる。ユーザーの明示裁定が要る |
| `LaunchValidatedFreeze` との binding / freeze SHA / `ccbench_pin` cross-validator | driver の実行順序に触る。one-shot 実走の消費に関わるため単独検証が要る |
| producer CLI (`preview` / `install-approved`) と hardened writer | 上記 trust root と lifecycle gate が確定してからでないと形が決まらない |
| oracle 独自の除外理由表の承認と driver event 対応表 | 内容の承認事項であり、実装より先にユーザー裁定が要る |
| schema version の bump | 実 semantic delta が生じたときだけ。現時点では不要 (`d302-schema-choice.md` §6) |
| durable spec / candidate / receipt の発行と `APPROVED_SPEC_SHA256` 設定 | 上記すべてと事前登録値の確定が前提 |
