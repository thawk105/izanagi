# [T-673] 裁定パッケージ — 世代遷移述語の量化縮退に property-based テストを入れるか

2026-08-09 / wave `dev-wave-t673-transition-pbt-package` / 実測 tip `86842ee0` (probe `3912c7fc`)
段 6 焦点再レビューの NO-GO を受けて全面改訂した版 (改訂点は §9)。

**ユーザーの問い:** 遷移述語の量化縮退 (`changed[:N]`) は有限 fixture では族全体を殺せず、
現状は「4 env 固定 fixture + docstring の残穴明記」で処理されている。生成的 /
property-based テストを入れる案と現状維持の案を、コストと検出力の実測付きで返せ。

**答えの要約**

- PBT を入れると検出できる `N` の上限は **3 → 63** に上がる。ただし
  **同じ frontier は依存ゼロの stdlib 生成テスト (B1) でも得られた。**
  本 wave の測定範囲では、**hypothesis 固有の追加検出力は 1 マスも観測されなかった。**
- **現行および直近で land される入力 (env 2 個) では、この族で誤受理を作れない。**
- **実測が明確に支持するのは「B2 (hypothesis) を今 land する根拠が無い」ことまでである。**
  A (現状維持) / A′ (fixture 増量) / B1 (stdlib 生成) / D (本番側 guard) の優劣は
  **未決**であり、親は決めない。理由は §7。

**証拠の強さの区別 (重要):** 本文の主張には次の 3 種が混在する。取り違えないよう明示する。

- **[台帳]** = 変異台帳に記録された実測 (§2 の frontier 表)
- **[親測定]** = 親の測定器による実測。逐語出力を insights へ凍結 (§3.1 の pytest 秒、§3.3、§3.4)
- **[静的]** = コードを読んで導いた推論。実走していない (§4 の一部、§5 の D/E/F/G)

---

## 1. 何を測ったか

対象は `orchestrator/campaign/env_contract_activation.py` の
`_validate_activation_transition` にある 2 つの量化点。

- **量化点 G** (`:275`) `for successor in successor_rows:` — exactly +1 / no-op の走査範囲
- **量化点 P** (`:300`) `for predecessor, successor in changed:` — successor 述語の適用範囲

各点に `[:N]` (N = 1, 2, 3, 4, 8, 63, 64) を注入した。**distinct な変異は 14 種類**で、
それを 7 つの scope / 候補に対して実行したので **ledger entry は 92 件**である
(KILLED 59 / SURVIVED 33 / 事前登録との不一致 0)。**「92 種類の変異」ではない。**
使い捨て worktree で実行し、本番ファイルと既存テストは 1 byte も変えていない (§8 に検証法)。

---

## 2. 検出力 [台帳]

`K` = 検出、`S` = 見逃し。

| 案 | G-N1 | G-N2 | G-N3 | G-N4 | G-N8 | G-N63 | G-N64 | P-N1 | P-N2 | P-N3 | P-N4 | P-N8 | P-N63 | P-N64 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **A 現状維持** | K | K | K | **S** | S | S | S | K | K | K | **S** | S | S | S |
| A′ 8 env 手書き | K | K | K | K | **S** | S | S | K | K | K | K | **S** | S | S |
| B1 生成 (stdlib) | K | K | K | K | K | K | **S** | K | K | K | K | K | K | **S** |
| **B2 PBT (hypothesis)** | K | K | K | K | K | K | **S** | K | K | K | K | K | K | **S** |
| C1 AST 構造検査 | K | K | K | K | K | K | K | K | K | K | K | K | K | K |
| C3 runtime sentinel | K | K | K | K | K | K | K | **S** | S | S | S | S | S | S |

**読み方**

- **A の天井は N ≤ 3。** focal 4 node の matrix でも、テストファイル全体 (77 node) の matrix でも
  同じ結果で、scope による過小評価ではない (別 matrix で 2 度確認)。
- **B1 と B2 は frontier が完全に一致した。** ただし**一致するのは frontier だけ**である。
  B1 は不正 env の位置を先頭 / 中間 / 末尾に振る node を 6 件持つが、B2 は末尾 witness 固定で、
  挙動カバレッジは同じではない。「B1 と B2 は実質同一のテスト」ではない。
- **B2 の frontier は `@example(env_count=64)` が単独で決めている。** つまりこれは
  「Hypothesis で包んだ有界掃引」の評価であって、shrinking (反例最小化) や多軸探索を含む
  **PBT 一般の効用を測ったものではない。** 本 wave の結果から「PBT に価値がない」と
  一般化してはならない。
- **C1 が検出したのは「登録した直接 `iterator[:N]` 14 種すべて」である。**
  「族全体を閉じた」とは書けない — C1 が見逃す形が実在する (§3.3)。
- **C3 は非対称。** sentinel は引数 `successor_rows` にしか注入できず、関数内ローカルの
  `changed` には届かない。**量化点 P は 1 マスも閉じない。** また C3 が検出するのは
  「その tuple subclass への直接 `__getitem__(slice)` 呼出し」であって、走査の完全性ではない。
  `tuple(successor_rows)[:N]` や `islice` は sentinel を迂回する [静的]。

**A の既存検出は frontier だけでは表せない [台帳]:** [T-627] の既往台帳によれば、
`changed[:1]` は既存テストファイル全体で **10 node** を赤にする。うち受理集合が変わる意味的検出は
5 件 (2〜4 番目の env の述語 false、非 bool、例外)、残り 5 件は受否が変わらず call 列だけが
変わる診断 pin である。**候補の「純増」を評価するときは、この 5 件の意味的検出が
A に既にあることを差し引く必要がある。**
(なお worklog 2026-08-08 (318) はこれを「semantic 3 / diagnostic 7」と記録しているが誤りで、
正しくは 5 / 5 である。台帳の erratum として記録する。)

---

## 3. コスト

### 3.1 実行時間 — **単発観測では順位が付かなかった** [親測定]

| 案 | test node 数 | pytest 報告 session 時間 (単発) | 行数 |
|---|---|---|---|
| A′ 8 env 手書き | 2 | 2.38 s | 89 |
| B1 生成 (M を 2〜64 掃引) | 18 | 2.37 s | 150 |
| B2 PBT (64 examples × 2 property) | 2 | 2.45 s | 115 |
| C1 AST 構造検査 | 1 | 2.38 s | 149 |
| C3 runtime sentinel | 2 | 2.45 s | 59 |
| (参考) 既存テストファイル全体 | 77 | 5.41 s | — |

**この列は「pytest 自身が報告した session 時間」であって CI の wall time ではない。**
dispatch と collection を含む end-to-end の 1 変異あたり所要は **21.8〜26.9 秒**である
(候補ごとの台帳 `duration_s`)。

**各案 1 回しか測っていない。** 反復も、空テストの baseline も、分散も取っていない。
したがって言えるのは **「単発観測では候補間の順位を確定できなかった」**までであり、
「差が無い」「起動時間に埋もれる」と断定はできない。観測値自体にも 2.37〜2.45 s の幅がある。
少なくとも「M を 64 まで掃くと重くて使えない」という懸念を支持する兆候は出なかった。

### 3.2 依存 (B2 のみ) [親測定]

逐語証拠は insights の `dep-install.out`。

- hypothesis 6.165.2 + 推移依存 3 個 (sortedcontainers 2.4.0 / typing-extensions 4.16.0 /
  exceptiongroup 1.3.1)、Python 3.10.12
- 導入時間 3.25 s と 6.01 s の 2 回観測。**いずれも pip cache が温まった状態の、
  外部 network が使える login ノードでの単発値**である。cold cache・offline は未測定。
- footprint 6.3 MB (apparent 5.7 MB)、`.py` 117 ファイル
- **計算ノードは外部 network 不可**なので、共有 home (`--user`) か共有 FS への事前配置が
  恒久的に要る。既存の pytest-xdist と同じ機構であり、新機構ではない。
  wheel の offline 供給、lock、hash 固定、更新追随、全ノード展開は**未測定**。
- repo には依存宣言ファイルが 1 つも無い (`pyproject.toml` / `requirements*.txt` 不在)。
  **hypothesis は「初の第三者テスト依存」ではない** (pytest・pytest-xdist が既にある) が、
  **初の追加 test package であり、依存宣言機構の新設を伴う。**
- **B2 は import が module top-level にあり、hypothesis 未導入環境では collection error になって
  同じ収集単位の他テストを巻き込む** (skip に縮退しない)。これは候補逐語から確認できる。

### 3.3 C1 の代償 — 検出力と偽陽性が同じ 1 本の規則から出る [親測定]

C1 の判定コードを probe から逐語で取り出し、入力ソースだけを差し替えて測った。
逐語出力は insights の `parent-probe-c1-controls.out`。

| 入力 | C1 |
|---|---|
| 直接 slice `[:1]` 〜 `[:10^6]` (両量化点) | 検出 |
| 事前 slice 再束縛 (`changed = changed[:4]`) | 検出 |
| `del changed[4:]` | 検出 |
| decoy loop を足して実 loop を切る | 検出 |
| `islice` で実効集合を縮める | 検出 (ただし loop 名が変わるため。truncation を見たのではない) |
| **別名へ slice し loop 名は据置 + `continue` で絞る** | **見逃し** |
| **関数冒頭に `return` を置き 2 loop を到達不能にする** | **見逃し** |
| `tuple(changed)` 化 (意味保存) | **誤検出** |
| 変数 rename (定義側も含む、意味保存) | **誤検出** |
| 診断用 loop の追加 (意味保存) | **誤検出** |
| コメント行の追加 (無害の対照) | 通過 |

C1 は「その loop が厳密にその名前を回す形」を pin しているだけで、逸脱が悪性か良性かを
区別しない。**試した意味保存リファクタ 3/3 すべてで赤になる**一方、コメント追加では赤にならない
(闇雲に赤くなるわけではないことの対照)。C1 を採ると、正しさを守る効果と
リファクタリングを止める副作用が**同じ規則から不可分に出る。**

### 3.4 測っていないコスト (誠実のため明示)

いずれの案を land しても以下は未測定である。

- PR ごとの累積 CI 時間、collection / shard への影響、full-suite 差分
- 失敗時の切り分け人時、偽陽性 1 件を許す基準と修正 SLA
- 本番リファクタ時に誰がテスト側を追随させるか (所有者)
- 候補が既存テストの private helper (`_chain` / `_validate`) に sibling import で結合すること。
  この結合は pytest の import mode に暗黙依存し、別 checkout の同名 module が先に
  `sys.modules` へ入ると**誤った対象を検査して全 mutant を「見逃し」と誤判定しうる**
- C1 が本番の private 関数名・変数名・loop 構造に、C3 が private signature と
  tuple subclass 受理契約に結合すること
- hypothesis / Python / pytest 更新時の再測定、`database=None` と version 依存の
  `derandomize` 列による過去失敗の再現性
- **候補を land しない場合の再現コスト** — 変異 spec の anchor drift、依存の再配置、
  tracked commit の再作成。「測って捨てる」は無償でも完全可逆でもない

---

## 4. この穴は今どれくらい危険か

**ここが裁定の核心である。**

1. **main の現在の checkout では、定常 loader は遷移検査を呼ばない [静的+実データ]。**
   activation record は `00000001.json` の 1 件だけで、`:395` の
   `if previous_rows is not None` に入らない。
2. **発行 tool の publish 経路は今日でも発火する [静的]。**
   `tools/issue_env_contract_activation.py` は候補 serial 2 を既存 chain に足して同じ
   `validate_activation_records()` を通す。
3. **実 serial 2 は既に存在し、land 待ちである [実データ]。** commit `677d0952`
   (branch `worktree-dev-wave-t657-t660-g2-activation`、main 未取り込み) が
   `00000002.json` (linux-baremetal g1 / pegasus g2) と head=2 を作っている。
   これが land すれば遷移検査は**毎回の load で発火する。「遠い将来」ではない。**
4. **しかしその実 edge は、この変異族では誤受理を作れない [静的、独立に 2 者が確認]。**
   変化する env は pegasus 1 個だけなので `changed` は 1 要素で、`changed[:N]` は全 N ≥ 1 で恒等。
   `successor_rows[:1]` は変化 env を取りこぼして `changed` を空にし、no-op 拒否を引く —
   **誤受理ではなく fail-closed の誤拒否**である。`successor_rows[:N≥2]` は 2 行とも見る。

**したがって現状維持の根拠は「検査が呼ばれないから」ではない。**
正しくは **「未検出域が N ≥ 4 であり、現行および直近 land 予定の入力は env 2 個なので
その領域が恒等になるから」**である。危険が現実になるのは
**registered env が 5 個以上になり、かつ同時に変化する env の数か不正行の位置が
truncation bound より後ろに来たとき**である。

---

## 5. 選択肢

### 主たる二択 (ユーザーの元の問い)

| | **A. 現状維持** | **B2. PBT を入れる** |
|---|---|---|
| 検出できる N | ≤ 3 | ≤ 63 |
| pytest session 時間 | — | +2.45 s (単発、順位は付かず) |
| 行数 | 0 | +115 |
| 依存 | なし | hypothesis + 推移 3、宣言機構の新設、offline 配置運用 |
| 残穴 | N ≥ 4 | N ≥ 64 (**消えない。移るだけ**) |
| 現行入力への効果 | — | **なし** (env 2 個では誤受理を作れない) |
| 副作用 | — | 未導入環境で collection error |
| 本 wave での代替 | — | **B1 が依存ゼロで同じ frontier を出した** |

**どちらも「族全体を閉じる」ことはできない。** 有限の例で無限族は閉じられない。

### 対照実験として測った案 (二択の判断材料であり、それ自体も選べる)

- **A′ (8 env 手書き、89 行、依存なし):** frontier を 3 → 7 へ動かす。生成器も依存も不要。
- **B1 (stdlib 生成、150 行、依存なし):** **B2 と frontier が完全一致。**
  加えて不正位置の変種 6 node を持つ。**B2 を選ぶなら、B1 に対する優位を別に示す必要がある。**
- **C1 (AST 構造検査、149 行、依存なし):** 登録した直接 slice 14 種を全滅させる。代償は §3.3。
- **C3 (runtime sentinel、59 行、依存なし):** 量化点 G のみ。P には届かない。

### 併用可能な追加策 (二択とは直交する。どれを選んでも足せる) [すべて静的]

- **D. 本番側の走査完全性 guard —— 本 wave では未測定。不採用ではない。**
  「本番コードを編集しない」というユーザー指示により、**最も直接的かもしれない解を
  測定対象から外している。この事実を隠さずここに書く。** 想定形は、走査前に期待件数を保存し
  処理件数と一致しなければ通常の `if` で `ActivationRecordError` にするもの
  (`assert` でないので `python -O` でも消えない)。`[:N]` は件数不一致で fail-closed になる。
  D245 の「集約量で遷移の正否を判定しない」とは別物 (遷移の正否ではなく走査の健全性) として
  書き分ける必要がある。**overhead・診断・multi-site 変異耐性は未測定であり、
  B / C より劣るとは判断していない。**
- **E. 変異 spec の恒久登録。** この 14 変異を恒久 spec として保存し、関連 wave の段 4 で
  必ず再登録する。harness は恒久 matrix を自動発見せず (`--spec` 明示必須)、CI にも入っていない。
  **運用でしか担保できず、正しさ signal にはならない。**
- **F. docstring の記述強化のみ。** 検出力は 1 マスも増えない。
  リスク受容の記録としては意味があるが、**「閉じた」「保証した」とは書けない。**
- **G. loader / issuer への integration pin。** 現行の候補はすべて private gate を直接叩いており、
  実際に gate が効く 2 層 (production loader、発行 tool) を通っていない。
  M > N の合成 registry で両経路を通す pin は別途必要。

---

## 6. 実測が支持する結論 (ここまでが親の断定)

1. **B2 (hypothesis) を今 land する根拠は無い。** frontier は B1 (依存ゼロ) と完全に同一で、
   PBT 固有の追加検出力は観測されず、追加 package と collection 脆弱性だけが増える。
   B2 を採るなら根拠は frontier ではなく、shrinking や多軸探索など**本 wave が測っていない性質**に
   置く必要がある。
2. **現行および直近 land 予定の入力では、この族はいずれの案でも成果物を変えない。**
3. **C1 / C3 を「走査完全性の保証」として採ってはならない。** 実際に閉じるのは
   登録した直接 slice 族だけで、別構文の縮退は通す。

---

## 7. 親が決めないこと (ユーザーの裁定を仰ぐ)

**A / A′ / B1 / D の優劣は決めない。** 実測はここまでを支持しない。理由:

- A′ と B1 は**依存ゼロで frontier を広げる**。単発観測では時間の不利も出ていない。
  「依存が増えるから B2 は見送り」という論拠は、A′ / B1 には当てはまらない。
- 一方 A′ / B1 の恒久保守費 (§3.4) は未測定である。
- D は本番編集禁止により測定対象から外れただけで、優越する可能性が残る。

したがって以下を裁定していただきたい。

1. **(主) A / A′ / B1 / B2 のどれを採るか。** 親の推奨は「B2 は採らない」まで。
   A を採る場合、それは**現行 env 2 個に対する暫定的なリスク受容**であって、
   実測上の最適解ではない。
2. **A を採る場合、再裁定 trigger を何にし、誰が持つか。** T-627 は
   「保証を謳わないことをもって終端」としたが、**trigger の無い終端は将来の再訪責任を散逸させる。**
   親案: (i) registered env が 5 個以上になったとき、(ii) env 集合を変更する機構の設計に
   着手したとき、(iii) 直接 slice 以外の量化縮退が実欠陥として観測されたとき。
   **記録場所 (タスク台帳か phase doc か) と、trigger を見逃さないための機械的な発火面**も
   併せて決めていただきたい (人手の記憶に委ねると T-627 と同じ形になる)。
3. **D (本番側の走査完全性 guard) を別 wave で測ってよいか。**
   本 wave の「本番を編集しない」制約は今回限りか、恒久か。
4. **E (変異 spec の恒久登録) を運用に載せるか。** 載せるなら所有者と再登録 trigger。
5. **G (loader / issuer への integration pin) を起票するか。**
6. **候補テスト 5 本 (562 行) の保存方式。** land していない。逐語は insights へ凍結するが、
   将来採用時に再生成でよいか、side branch `worktree-dev-wave-t673-probe` を保持するか。

---

## 7bis. 付随して裁定が要るもの — dev-wave の docs 予算が上限ちょうどで余白ゼロ

本 wave の段 8 (スキル自己改善) で改善候補を 2 件得たが、**どちらも実装できなかった。**

- 候補 1 (`DW-M05`): 使い捨て worktree 経路 `tools/mutation_worktree.py --commit` の存在、
  `--scratch-root` は事前作成が要ること、`estimated_run_seconds` は総量でなく 1 run あたりで
  あること。後者を総量と誤読して preflight を 2 度やり直した。
- 候補 2 (`DW-M08`): 「新旧両走」を義務づけているのに、**同一 spec を使い回せない**制約
  (`SURVIVED` 期待は `expected_nodes` 空必須なので、新テストが殺すと `MISMATCH` になる) が
  未記載である。`MISMATCH` を kill と読み替える誘惑を作る。

**実装できなかった理由:** `docs/dev-wave/**` の L1.5 読量予算が **9566 / 9566 bytes と
上限ちょうど**で、余白が 1 byte も無い (両候補で +569 bytes)。
[T-627] wave (2026-08-08) も同じ壁に当たっており (当時の残余 16 bytes)、**2 波連続**である。

余白を作る手は次のいずれかだが、いずれも親の一存では採れない。

1. **既存の安全記述を削る** — 例えば `DW-M08` は「node 抽出は F71 に従う」と書いた直後に
   F71 の内容を括弧で再掲しており、byte としては重複である。しかし削れば、走行中に
   `docs/failures.md` を開かないと抽出規則が読めなくなる。
   **予算のために安全義務を弱めることは自己改善契約が禁じている**ため採らなかった。
2. **予算値を上げる** — 契約が「通常の自己改善に含めず、理由付きの独立審査対象にする」と
   定めている。親は提案しない。
3. **外出し** — dev-wave 系は読み込みが leaf 節単位なので削減 0 で、既に却下済みの案である。

**裁定していただきたいこと:** (a) 候補 2 (MISMATCH の誤読を防ぐ 1 文) だけでも入れるために、
どこから byte を空けるか。(b) それとも両候補を見送り、本エントリを唯一の記録とするか。
(c) L1.5 予算そのものを独立審査にかけるか。

---

## 8. 検証のしかた (この報告を疑うために)

- frontier 表: `mutation-ledger-*.json` の各 `mutations[].status` を読む。
  事前登録との一致は `summary.matching == summary.registered` で確認できる。
- 本番不変: `git diff 4be7a362 86842ee0 -- orchestrator/campaign/ orchestrator/tests/test_env_contract_activation.py` が空。
- probe が land に混入していないこと: `git merge-base --is-ancestor 3912c7fc 86842ee0` が非祖先。
- §3.1 の秒数: 各台帳の `baseline.artifact.stdout` の pytest 集計行。
- §3.3 / §3.2: insights の `parent-probe-c1-controls.out` / `dep-install.out` (逐語)。

**まだ埋まっていない情報** (これが無いと「A が最小総費用」とは言えない):
将来の env 数上限と分布、同時変更 env 数、activation edge の頻度、
反復した時間測定と full-suite 差分、D の overhead と検出力、
候補を保存しない場合の再現費、B2 の offline 配置証拠。

---

## 9. この版で直したこと (段 6 焦点再レビューの NO-GO を受けて)

1. 「92 変異」→「distinct 14 変異 / ledger entry 92 件」。攻撃面の多様性を誇張していた。
2. 「pytest 実時間」→「pytest 報告 session 時間」。end-to-end は 21.8〜26.9 秒と併記。
   「差が出なかった」「実測で否定された」を「単発観測では順位が付かなかった」へ後退。
3. §3.2 / §3.3 に [親測定] のラベルと逐語証拠ファイルを付け、証拠鎖を作った。
4. **C1 負制御の「変数 rename」が壊れた変更だった誤りを是正し、測り直した。**
   定義側も含めて正しく rename しても C1 は赤のままで、結論 (意味保存 3/3 で誤検出) は
   変わらなかった。誤りは指摘どおりだが、修正後も同じ結果になったことを明記する。
5. 「C1 だけが族全体を閉じる」「C3 は G を全 N 閉じる」を、登録した直接 slice 族の検出へ格下げ。
6. 冒頭の「docstring で閉じている」を削除 (§5 F の「閉じたとは書けない」と矛盾していた)。
7. 「以下すべて実測に基づく」を撤回し、[台帳] / [親測定] / [静的] の 3 ラベルを導入。
8. **推奨を「B2 は land しない」までに限定し、A / A′ / B1 / D は未決とした。**
   前版は A を既定推奨にしていたが、依存ゼロで frontier を広げる A′ / B1 と未測定の D を
   比較せずに現状維持へ誘導していた。
9. A の既存検出 (10 node、意味的 5 / 診断 5) と、B1 が持ち B2 が持たない位置変種を復活させた。
