# [T-086] PKG-2 FROZEN_MANIFEST exact key-set — 逐語凍結 (codex plan + 敵対相談 2 + 敵対レビュー 2)

本 wave (2026-07-24) の各段 codex 逐語。gpt-5.6-sol / reasoning=max (実装子のみ high) / read-only
(実装子は workspace-write)。path 接頭辞 (worktree 絶対・job-tmp) は durable 化のため正規化済。
F34: 三軸 conjunction 機械検査を通してから凍結。

---

## 段2: プラン起草 (codex, read-only, max)

## 結論

- P1: 明示的な `FROZEN_KEYSET` を採用する。
- assert は新しい test node にせず、既存 `test_manifest_shape_is_exact()` の末尾へ追加する。
- P2: 狭義 R2（同数 path 差し替え）を閉じるのに disk→manifest 閉包は不要。ただし、凍結族全体の閉包は別の未解決 gap として残る。
- P3: 群件数 assert は追加しない。exact key-set に対して冗長で、同一群内差し替えを検出できない。

ファイル編集・pytest 実行は行っていない。23 件の現物 SHA と positive-control は read-only の静的シミュレーションで確認した。

## 1. 実装プラン

対象は [test_frozen_artifacts.py:38](orchestrator/tests/test_frozen_artifacts.py:38) のみ。

1. `FROZEN_MANIFEST` の閉じ括弧である現行 L85 の直後、`_sha256()` が始まる現行 L88 より前に、次を追加する。

   - 定数名: `FROZEN_KEYSET`
   - 型: `frozenset`
   - 要素: manifest の key literal 23 本を独立に再列挙する。
   - 参照する現行 key 行: L39, L41, L43, L45, L47, L49, L51, L53, L55, L57, L59, L61, L63, L65, L67, L69, L71, L73, L75, L77, L79, L81, L83。
   - `frozenset(FROZEN_MANIFEST)` や filesystem glob から導出してはならない。これは恒真化になる。
   - コメントには「現行 23 件だけの暫定独立 pin。恒久 freeze-family membership を表さない」と明記する。

2. [test_manifest_shape_is_exact:110](orchestrator/tests/test_frozen_artifacts.py:110) を強化する。

   - 現行の `len == 23`（L112）、prefix 検査（L116）、64hex 検査（L117）を一切変更しない。
   - 現行 L118 の後、既存検査をすべて通過した位置へ以下を追加する。

```python
    actual_keys = frozenset(FROZEN_MANIFEST)
    assert actual_keys == FROZEN_KEYSET, (
        "FROZEN_MANIFEST の key-set 不一致:"
        f"\nmissing_from_manifest={sorted(FROZEN_KEYSET - actual_keys)}"
        f"\nunexpected_in_manifest={sorted(actual_keys - FROZEN_KEYSET)}"
    )
```

   `sorted()` により failure message を決定論的にする。

3. 以下は無変更とする。

   - manifest→disk の既存検査 [test_frozen_artifacts.py:96](orchestrator/tests/test_frozen_artifacts.py:96)
   - `_sha256()`（現行 L88）
   - `_run()` [test_frozen_artifacts.py:121](orchestrator/tests/test_frozen_artifacts.py:121)
   - seal OID [test_s8b_floor_campaign.py:3021](orchestrator/tests/test_s8b_floor_campaign.py:3021)

4. harness への追加配線は不要。

   `_run()` は L122–L123 で既存の `test_` 関数を列挙し、L127 で呼び出す。強化対象の関数名を変えないため自走 runner と pytest の双方へ自動的に載る。新しい test node を増やさないので、D76 が既存 node として列挙する [freeze-permanent-design-s2.md:2678](docs/freeze-permanent-design-s2.md:2678) と L2679 も陳腐化させない。

## 2. P1 — 推奨機構

明示 `frozenset` を推奨する。

| 観点 | 明示 `FROZEN_KEYSET` | key-set digest |
|---|---|---|
| 同数差し替え | 集合の数学的完全一致で確実に拒否 | 衝突耐性に依存する |
| 符号化 | 不要 | sort後の区切り・UTF-8・canonical encoding の仕様が必要 |
| レビュー | 期待 path が直接読める | 64hex だけでは期待集合を査読できない |
| failure message | missing/unexpected を直接表示可能 | pin の preimage がないため期待側の欠落 path を復元できない |
| 一括置換への耐性 | manifest と keyset の両方を一括置換すると通り得る | path の一括置換だけなら digest pin が残って検出する |

digest には「同じファイル内の path 一括置換で oracle まで変わりにくい」という利点がある。ただし、意図的に digest まで更新すれば両方式とも通る。同一 repo 内の可変 test literal は悪意ある協調編集に対するセキュリティ境界ではなく、この限界は [freeze-permanent-design.md:369](docs/freeze-permanent-design.md:369) と L373–L375 でも既認識である。

本件ではレビュー透明性、正確な差分 message、canonicalization 不要という利点が上回る。positive-control の変異パッチは manifest 内の occurrence だけを変更し、blind な全置換にしないことが必須となる。

## 3. positive-control 変異

一対一の置換は次とする。

- 除去する manifest entry:
  - path: [test_frozen_artifacts.py:47](orchestrator/tests/test_frozen_artifacts.py:47)
  - SHA（L48）: `150438a4ce2d0e5cab772c3eb9bfa05f44307a5dae5e47a1034778a3e3d9f6ba`
- 追加する実在 path:
  - [2026-07-16_s8b-ruling-package.md:1](output/insights/2026-07-16_s8b-ruling-package.md:1)
  - 現物 SHA: `a87d9b4d0abc6717ec2aa0bdb9f387b438d52886a1513e0c5653dbdb7e0e0fb1`
  - tracked regular file であり、現行 manifest には未登録。
- `FROZEN_KEYSET` 側は変更しない。

この変異の帰属は次のとおり。

1. `test_frozen_artifacts_match_manifest`:

   - replacement は実在 regular file なので L101 を通る。
   - SHA を現物値へ更新するため L104–L106 を通る。

2. 既存 shape 条件:

   - 1 件削除・1 件追加なので L112 の `len == 23` を通る。
   - path は `output/` 始まりなので L116 を通る。
   - SHA は lowercase 64hex なので L117–L118 を通る。

3. 新 exact-key assert のみが次で落とす。

```text
missing_from_manifest=['output/insights/2026-07-16_s8b-floor-protocol-package.md']
unexpected_in_manifest=['output/insights/2026-07-16_s8b-ruling-package.md']
```

リポジトリ検索上、`FROZEN_MANIFEST` を実行時に読むコードはこのテストファイルだけだった。静的シミュレーションでも、現行 match 条件=`PASS`、現行 shape 条件=`PASS`、exact key-set=`FAIL` を確認済みであり、F28 の「先行検査に食われる」型には該当しない。[failures.md:364](docs/failures.md:364) の単一理由条件を満たす。

## 4. P2・P3 と恒久設計との境界

P2 は狭義 R2 について妥当である。swap 先が disk 上に存在していても、manifest key-set が独立 literal と異なるため拒否できる。disk 全列挙は同数差し替え検出の必要条件ではない。

ただし、replacement 自身が [ruling-package.md:4](output/insights/2026-07-16_s8b-ruling-package.md:4) で「凍結族」と自称しているのに manifest 外である。したがって次の命題は本件では閉じない。

> disk 上で凍結扱いされる全成果物が manifest に含まれる。

これを R2 に含める定義なら、件数 23 不変と現物が衝突するため本実装では解決不能であり、別裁定パッケージへ返すべきである。必要な裁定項目は「凍結族 membership の正本」「insights の選別規則」「現行未登録凍結文書の扱い」である。

P3 の群件数 assert は不要。exact 23 path が一致すれば群件数も自動的に固定される。一方、件数だけでは同一群内の差し替えを検出できない。今回の floor-protocol package → ruling package は双方とも裁定資料なので、群件数を保ったまま成立する具体例である。

恒久設計との衝突もない。

- D75 は将来の literal 更新と exact key-set を W-e で扱う [freeze-permanent-design.md:325](docs/freeze-permanent-design.md:325)。
- 本件は receipt、G/R/A/X、production root、active-bundle pointer を一切導入しない。
- D75/D76 は `FROZEN_MANIFEST` 8 件、将来 12 件を前提としており、現行 23 件との再整合は将来 wave の裁定事項である。本件では更新しない。
- 新 test node を作らないため、D76 の required-node 設計も先取りしない。

## 5. edge case・risk

- manifest と `FROZEN_KEYSET` を協調して更新すれば通る。同一ファイル oracle の既知限界であり、機械的には防げない。
- Python dict literal 内の同一 key 二重記載は runtime で潰れる。全 23 key が最終的に残る形の source-level duplicate は今回の集合検査でも検出しない。必要なら別の AST/lint 課題。
- `os.path.isfile()` は symlink を追う。path は同じまま symlink 化し同一 bytes を指す変異は R2 の対象外。
- disk→manifest 閉包、凍結族の意味付け、群分類の機械正本は未実装であり、閉じたと主張しない。
- baseline の 23 件は静的 SHA 照合で全一致を確認したが、依頼どおり pytest 実測は親担当とする。

---

## 段3: 敵対相談 lens1 (正しさ境界・実効性)

総合判定: **狭義 R2 を閉じる実効性は real、反対攻撃は refuted**。同数 path 差し替えは新 assert だけで拒否される。scoped blocker はない。ただし、同一ファイル oracle と凍結族閉包には real な残余がある。positive-control は親 MUT-A の方が証拠として明瞭。

静的結果は次のとおり。pytest・編集は行っていない。

```text
pristine: 23件、現物SHA不一致 0
plan変異:   match=PASS, shape=PASS, exact-key=FAIL
親 MUT-A:   match=PASS, shape=PASS, exact-key=FAIL
```

1. **refuted — exact-key assert は恒真でなく、狭義 R2 を閉じる**

   - (a) 入力: manifest の1キーだけを実在非manifest pathへ交換し、SHAも交換先の実値へ更新。既存 match/shape は通るが、`frozenset(FROZEN_MANIFEST) != FROZEN_KEYSET` となり新 assert が拒否する。誤受理は再現しない。
   - (b) manifest は [test_frozen_artifacts.py:38](orchestrator/tests/test_frozen_artifacts.py:38)、既存 match は [同:96](orchestrator/tests/test_frozen_artifacts.py:96)、shape は [同:110](orchestrator/tests/test_frozen_artifacts.py:110)。独立 literal を要求し動的導出を禁止する箇所は [plan_out.md:18]([wave-artifact]/plan_out.md:18)。
   - (c) 影響: 受理集合は「任意の23本の `output/` path」から「現行23本の完全一致」へ真に狭まる。

2. **refuted — plan 変異・親 MUT-A とも F28 の先行失敗／過剰決定はない**

   - (a) plan 変異先 `ruling-package.md` は tracked regular file、SHA=`a87d9b4d…e0fb1`。親 MUT-A の `output/README.md` も tracked regular file、SHA=`83a6fb26…13657`。双方とも件数23、`output/` prefix、lowercase 64hexを維持する。`isfile` と SHA 比較を通過し、新 assert だけが落とす。`_run()` では match が先に走るが緑である。
   - (b) `isfile`／SHA は [test_frozen_artifacts.py:99](orchestrator/tests/test_frozen_artifacts.py:99)、shape 条件は [同:112](orchestrator/tests/test_frozen_artifacts.py:112)、自動列挙・呼出しは [同:121](orchestrator/tests/test_frozen_artifacts.py:121)。manifest 側だけを変える指定も [plan_out.md:64]([wave-artifact]/plan_out.md:64) と [同:77]([wave-artifact]/plan_out.md:77) にある。
   - (c) 影響: kill は exact-key assertion へ排他帰属でき、既存 match/shape の kill と誤計上されない。

3. **real — plan の positive-control は意味論的に汚れている**

   - (a) plan の交換先 `ruling-package.md` は自身を「凍結族」と宣言している。凍結族完全性まで成果物と誤読した場合、この交換は既知の不正入力でなく、「現在のmanifestから漏れた正当候補」を新 assert が誤拒否する事例になる。親 MUT-A の一般 README にはこの曖昧さがない。
   - (b) 凍結族宣言は [2026-07-16_s8b-ruling-package.md:4](output/insights/2026-07-16_s8b-ruling-package.md:4)。README の役割は [output/README.md:1](output/README.md:1)。plan 自身もこの矛盾を [plan_out.md:105]([wave-artifact]/plan_out.md:105) で認めている。
   - (c) 影響: 機械的な単一理由性は保つが、広義の「凍結族完全性」を実証する positive-control にはならない。実測台帳には親 MUT-A を使うべき。

4. **real / scope外残余 — 同一ファイル oracle の協調更新は通る**

   - (a) 入力: manifest のキーとSHAを交換し、同じ commit で `FROZEN_KEYSET` 側も同じキーへ交換する。match、shape、exact-key の全てが緑になる。manifest occurrenceだけを変える positive-control ではこの共通モード故障を測れない。
   - (b) 同一ファイル配置は [plan_out.md:12]([wave-artifact]/plan_out.md:12)、この限界の自認は [同:122]([wave-artifact]/plan_out.md:122)。D76 の恒久形は別ファイルの golden を要求している [freeze-permanent-design-s2.md:2062](docs/freeze-permanent-design-s2.md:2062)。
   - (c) 影響: 狭義の「manifestだけの差し替え」は閉じるが、独立した改竄境界にはならない。「暫定 pin」以上を主張してはいけない。

5. **real / scope外残余 — disk→manifest／凍結族閉包は閉じない**

   - (a) 入力: `ruling-package.md` のような凍結族ファイルをmanifest外に置いたままにする。matchは列挙済み23本しか読まず、exact-keyも「期待23本との差」を見るだけなので全緑になる。
   - (b) 一方向走査は [test_frozen_artifacts.py:99](orchestrator/tests/test_frozen_artifacts.py:99)、凍結族宣言は [ruling-package.md:4](output/insights/2026-07-16_s8b-ruling-package.md:4)。
   - (c) 影響: 成果物は「現行23 pinの保存」であり、「凍結族の完全 inventory」ではない。planの限定主張なら許容範囲。

6. **refuted — 既存ゲートの弱体化、F27、OID波及はない**

   - (a) 入力: planどおり新定数と末尾assertだけを追加。既存の不在・SHA不一致・件数・prefix・hex拒否はそのまま先に発火し、以前の拒否入力が新たに通る経路はない。対象テストファイルのSHA／Git blob OIDを全repo検索しても pin はなく、凍結23ファイルは全て現物SHA一致だった。
   - (b) 既存拒否群は [test_frozen_artifacts.py:101](orchestrator/tests/test_frozen_artifacts.py:101) と [同:112](orchestrator/tests/test_frozen_artifacts.py:112)。seal OID は [test_s8b_floor_campaign.py:3021](orchestrator/tests/test_s8b_floor_campaign.py:3021)、ancestry は [同:3061](orchestrator/tests/test_s8b_floor_campaign.py:3061)、seal target の後続不変は [同:3180](orchestrator/tests/test_s8b_floor_campaign.py:3180)。
   - (c) 影響: 凍結bytes、件数23、OID `82803d6d…`、既存受理集合は不変で、追加分は拒否集合を狭めるだけ。

7. **refuted — D75/D76 の恒久設計先取りには当たらない**

   - (a) 入力: 既存 test node 内へ暫定23-key assertだけを追加。receipt、production root、別file golden、required-node manifest、generation移行は導入されない。将来W-eの12-key恒久設計は依然未実装である。
   - (b) D75の恒久exact-keyは [freeze-permanent-design.md:325](docs/freeze-permanent-design.md:325)、D76の既存node名は [freeze-permanent-design-s2.md:2678](docs/freeze-permanent-design-s2.md:2678) と [同:2679](docs/freeze-permanent-design-s2.md:2679)。
   - (c) 影響: required-node集合も恒久freeze受理集合も動かさず、T-086の狭いR2だけを閉じる。

したがって、実装機構自体への scoped 反証はない。ただし mutation evidence は plan案ではなく、意味論的に汚れていない親 MUT-A を manifest occurrence限定で使うのが妥当です。

---

## 段3: 敵対相談 lens2 (整合・scope・全層網羅)

## 総合判定

**as-written は NO-GO。** exact key-set assert 自体は狭義 R2 を実効的に殺すが、brief と plan は D75/D76 の状態を誤認し、`durable`／`lineage`／凍結族 membership を過大に扱っている。

### 1. REAL — D75/D76 の裁定状態が stale

(a) brief と plan は R1..R16 を「裁定待ち」とするが、R1..R16 は全項承認済み。未了は U-A1 と conformance literal の2件だけである。承認済みでも未実装なので、先取り禁止自体は残る。

(b) [plan_out.md:117]([wave-artifact]/plan_out.md:117)、[freeze-permanent-design.md:3](docs/freeze-permanent-design.md:3)、[freeze-permanent-design-s2.md:3](docs/freeze-permanent-design-s2.md:3)

(c) 影響: brief／plan の状態説明を訂正し、R1..R16 を再裁定事項として扱わないこと。

### 2. REAL — 現行23件と恒久設計12件は未整合

(a) 承認済み D75 は W-e で「旧8件＋新4件＝12件」を要求する。一方、現行は seal 後の23件である。将来の期待集合が12、27、その他のどれになるかは未裁定で、汎用名 `FROZEN_KEYSET` を今置くと恒久形に見える。さらに D76 の恒久形は別ファイル・別値源の independent golden を要求しており、同一ファイル内の複製とは異なる。

(b) [freeze-permanent-design.md:325](docs/freeze-permanent-design.md:325)、[test_frozen_artifacts.py:112](orchestrator/tests/test_frozen_artifacts.py:112)、[t080-prediction-seal.md:15](output/insights/2026-07-24_t080-prediction-seal.md:15)、[freeze-permanent-design-s2.md:2060](docs/freeze-permanent-design-s2.md:2060)、[freeze-permanent-design-s2.md:2820](docs/freeze-permanent-design-s2.md:2820)

(c) 影響: **scope 外の real 所見 — 裁定パッケージ候補。** 「82803d6d 後の15 pinを W-e の旧集合へどう統合するか」と暫定 pin の廃止・移行条件を決める必要がある。

### 3. REAL / partial — 同一ファイル pin は “durable” を狭くしか満たさない

(a) manifest と明示 `frozenset` が隣接すれば、blind な全置換や協調編集で両方が同時に変わる。manifest だけを変える一方向 drift は検出するが、同一変更内の desync には弱い。digest は少なくとも blind 置換への摩擦が強く、恒久 D76 は別ファイル golden でさらに分離する。plan の「機械的には防げない」は過大である。

(b) [plan_out.md:60]([wave-artifact]/plan_out.md:60)、[plan_out.md:122]([wave-artifact]/plan_out.md:122)、[freeze-permanent-design.md:493](docs/freeze-permanent-design.md:493)、[freeze-permanent-design-s2.md:2064](docs/freeze-permanent-design-s2.md:2064)

(c) 影響: 暫定実装なら `PROVISIONAL_..._82803D6D` のように seal 固有名へ狭め、「manifest-only 編集に対する運用 sentinel」と明記すべき。改竄耐性としての R2 closure は主張不可。

### 4. REAL — P3 の “lineage” 解釈は根拠不足

(a) 元の R2 は exact key-set 欠落による同数差し替えであり、commit ancestry／実走真正性まで含まない。最新 worklog の広義 lineage は C02/R3/R4 と外部 attestation を要求する。exact key-set＋既存SHAは membership/bytes を固定するだけで、82803d6d の ancestry は別の E2E test が担っている。また `23=...` は現在 assertion message に書かれるだけで、群分類 predicate ではない。

(b) [t080-prediction-seal.md:65](output/insights/2026-07-24_t080-prediction-seal.md:65)、[worklog.md:779](docs/worklog.md:779)、[test_frozen_artifacts.py:113](orchestrator/tests/test_frozen_artifacts.py:113)、[test_s8b_floor_campaign.py:3021](orchestrator/tests/test_s8b_floor_campaign.py:3021)、[test_s8b_floor_campaign.py:3061](orchestrator/tests/test_s8b_floor_campaign.py:3061)

(c) 影響: 成果物の主張は「manifest membership の狭義 R2 を閉じる」に限定すること。広義 lineage を閉じるなら **scope 外の裁定パッケージ候補**であり、本 assert では不足。

### 5. REFUTED — 群件数 assert は狭義 R2 には不要

(a) 期待23 path の完全一致が保たれる限り、各群件数は論理的帰結であり、件数 assert は受理集合を追加で狭めない。群件数だけでは同一群内差し替えも検出できない。

(b) [test_frozen_artifacts.py:38](orchestrator/tests/test_frozen_artifacts.py:38)、[test_frozen_artifacts.py:112](orchestrator/tests/test_frozen_artifacts.py:112)、[plan_out.md:111]([wave-artifact]/plan_out.md:111)

(c) 影響: 群件数 assert は追加不要。ただし「群構造を独立に機械検査した」とは主張してはならない。

### 6. REFUTED — disk→manifest 閉包は狭義 R2 の必要条件ではない

(a) 同数差し替えでは、差し替え先が disk 上に存在することは既存 match test を通す条件にすぎない。独立期待集合との比較は disk 全列挙なしで必ず差集合を出す。read-only 再計算でも、提案 mutant は既存 match=`PASS`、shape=`PASS`、exact key-set=`FAIL` だった。

(b) [test_frozen_artifacts.py:96](orchestrator/tests/test_frozen_artifacts.py:96)、[test_frozen_artifacts.py:110](orchestrator/tests/test_frozen_artifacts.py:110)

(c) 影響: P2 の繰延は狭義 R2 について妥当。未manifest成果物の検出は、membership classifier を要する別命題である。

### 7. REFUTED — `ruling-package.md` の self-claim は manifest membership を生まない

(a) 4行目の「凍結族」自称は実在する。しかし過去の集合確定では同ファイルを明示的に非含有とし、現行 manifest も「裁定資料2本」として別の2本だけを列挙する。`output/README.md` も insights 全体を機械防護対象とはしていない。したがって plan の「membership gap」推論は成立しない。

(b) [s8b-ruling-package.md:4](output/insights/2026-07-16_s8b-ruling-package.md:4)、[worklog-phase3-0717-0718.md:456](docs/archive/worklog-phase3-0717-0718.md:456)、[test_frozen_artifacts.py:33](orchestrator/tests/test_frozen_artifacts.py:33)、[output/README.md:49](output/README.md:49)

(c) 影響: 同ファイルを manifest へ加える裁定パッケージは不要。必要なら「編集上の凍結」と「byte-pin membership」の用語整理だけを別候補にする。

### 8. REAL（plan の論証不足）／REFUTED（実際の consumer 取り残し）

(a) `FROZEN_MANIFEST` の名前検索だけでは、同じ集合を別 literal・journal・動的列挙で扱う proof 経路を発見できない。ただし精読結果、selector-runs は journal↔disk 双方向 exact、official preflight は固定4＋宣言集合＋chain集合を exact に閉じ、E2E は seal commit/diffを別に pin している。いずれも manifest変更を必要としない。

(b) [s8b_prediction_runner.py:1290](orchestrator/campaign/s8b_prediction_runner.py:1290)、[s8b_prediction_runner.py:1351](orchestrator/campaign/s8b_prediction_runner.py:1351)、[s8b_floor_campaign.py:1408](orchestrator/campaign/s8b_floor_campaign.py:1408)、[s8b_floor_campaign.py:1523](orchestrator/campaign/s8b_floor_campaign.py:1523)、[test_s8b_floor_campaign.py:3176](orchestrator/tests/test_s8b_floor_campaign.py:3176)

(c) 影響: 実装 scope は引き続き `test_frozen_artifacts.py` のみでよいが、plan にこの全層非波及根拠を追記すべき。

### 9. REFUTED — assert の実発火・harness 配線

(a) 23件すべての現物SHA一致を再計算した。提案 mutant は既存二検査を通り、新集合差分だけで落ちる。既存関数を強化するため `_run()` と pytest の双方に載り、D76 の既存 node 名も変わらない。

(b) [test_frozen_artifacts.py:99](orchestrator/tests/test_frozen_artifacts.py:99)、[test_frozen_artifacts.py:121](orchestrator/tests/test_frozen_artifacts.py:121)、[freeze-permanent-design-s2.md:2678](docs/freeze-permanent-design-s2.md:2678)

(c) 影響: 新 node・conftest・runner変更は不要。test-only 条件を満たす。

### 10. REAL / low — positive-control が seal lineage を直接攻撃していない

(a) mutant は pre-B の floor-protocol package を除去する。集合比較の一般性は示すが、82803d6d で追加された14 evidence の保持を直接攻撃しないため、P3 の lineage 主張とは代表性がずれる。

(b) [test_frozen_artifacts.py:47](orchestrator/tests/test_frozen_artifacts.py:47)、[test_frozen_artifacts.py:57](orchestrator/tests/test_frozen_artifacts.py:57)、[t080-prediction-seal.md:17](output/insights/2026-07-24_t080-prediction-seal.md:17)

(c) 影響: mutant の除去側を prediction または selector-runs の1件へ変えるべき。実装 scope は増えない。

結論として、disk closure・群件数・production consumer変更は不要。ただし、暫定 pin を恒久 `lineage` と呼ばず、D75/D76 の post-seal 23件再整合を裁定パッケージへ返すことが GO 条件である。pytest は実行せず、ファイル変更も行っていない。

---

## 段6: 敵対レビュー lens1 (正しさ・受理集合・F27)

判定: **real 0 / refuted 5。レンズ1は GO**。must-fix 所見なし。pytest 緑ではなく、指定変異の実発火で裏取りした。

- **refuted — 恒真ゲート化:** `known_axes_freeze.json` を削除し、実在する非 manifest の `output/README.md` と実 SHA `83a6fb26…` を追加、件数23を維持。既存 match は受理、既存 shape 条件も受理した一方、新 assert は missing/unexpected を示して拒否した。[test_frozen_artifacts.py:125-153](orchestrator/tests/test_frozen_artifacts.py:125)

- **refuted — 23キー列挙ミス:** manifest 23、pin literal 23、pin unique 23。全23件を一件ずつ照合し、完全一致、missing/extra とも空。pin は23個の独立 string literalで、AST上の参照名は `frozenset` のみ。manifest/glob導出ではない。[test_frozen_artifacts.py:90-114](orchestrator/tests/test_frozen_artifacts.py:90)

- **refuted — 既存受理集合の弱体化:** match検査はHEADとbyte-identical。shapeの既存 `len==23`・prefix・64hex部分もAST上そのままのprefixで、新条件が末尾に追加されただけ。  
  `A_new = A_old ∩ {keys == K_82803d6d}` で、受理集合の拡大はない。[test_frozen_artifacts.py:139-153](orchestrator/tests/test_frozen_artifacts.py:139)

- **refuted — 凍結値・所有外変更:** manifestブロックは seal `82803d6d`、HEAD、worktreeの三者で同一3123 bytes・SHA256 `2520644b…`。23 path/SHA、`_sha256`、`_run` は不変。[test_frozen_artifacts.py:38-85](orchestrator/tests/test_frozen_artifacts.py:38)  
  `git diff --stat` は対象1ファイル・35追加・削除0のみ。seal testのworktree blobもHEADと一致し、OIDは `82803d6d245d80a82954d61e065404fb15b3eeab` のまま。[test_s8b_floor_campaign.py:3021](orchestrator/tests/test_s8b_floor_campaign.py:3021)

- **refuted — F27:** fixture・既存hash期待値の更新なし。追加物は固定path集合と比較assertだけで、working-tree hashや揮発診断値の焼き込みもない。`impl.diff` は現在のworktree diffと完全一致。

real所見がないため、指定された失敗シナリオ・成果物影響を伴うmust-fix項目はない。

---

## 段6: 敵対レビュー lens2 (整合・限界・過大主張)

判定: **REAL 0 / REFUTED 5**。段4裁定からの逸脱はない。scope 外 real／裁定パッケージ候補もなし。pytest 緑は根拠にしていない。

1. **REFUTED — 過大主張**
   [test_frozen_artifacts.py:87](orchestrator/tests/test_frozen_artifacts.py:87) は「seal 時点」「暫定」「運用 sentinel」と限定し、同:88–89 で独立改竄境界・恒久 membership の双方を明示否定している。`durable`／`lineage` の主張も差分内にない。

2. **REFUTED — 42-node baseline の陳腐化**
   test node は [既存2関数](orchestrator/tests/test_frozen_artifacts.py:125) のまま。追加 assert は既存 `test_manifest_shape_is_exact` の末尾 [同:148](orchestrator/tests/test_frozen_artifacts.py:148)。D76 の既存2 node 列挙（`freeze-permanent-design-s2.md` §S2-8.3、2678–2679）と一致する。

3. **REFUTED — D75/D76 topology の先取り**
   差分は同一ファイル内の `frozenset` literal と集合等価 assert のみ。receipt、G/R/A/X、active-bundle、別ファイル golden はない。D75/D76 の未実装境界にも踏み込んでいない。

4. **REFUTED — 23件の恒久化**
   [同:87–89](orchestrator/tests/test_frozen_artifacts.py:87) は「現行23件だけ」「恒久 membership ではない」と明記。D76 の恒久12件との未整合を解消済みとは主張していない。実際、23 path は seal commit `82803d6d` の manifest と一致した。

5. **REFUTED — scope 外層への侵入**
   新処理は `frozenset(FROZEN_MANIFEST)` の等価比較だけ。disk 閉包、群件数、classifier、production consumer、ancestry／attestation は一切参照していない。

実装子自己報告の「3検査系統」は表現がやや緩いが、同報告自身が test node は2件と記載しており、成果物・scope・claim を変える real 所見にはならない。