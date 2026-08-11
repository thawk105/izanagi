# [T-139] land 2 session 2 — 裁定パッケージ

段 2 (プラン起草) と段 3 の敵対 2 レンズが**独立に NO-GO** を返し、親が段 4 で
「RP-1 (a) の 8 件は本 session で実装しない」と裁定した。その根拠と、ユーザー裁定を要する論点を返す。

**本 session が実装したのは §S7 #2 (Git trust root 部分集合) の 1 件だけである。**
実装済みの範囲は `README.md` を参照。

親は各問に推奨を付ける。推奨は親の判断であり、覆してよい。

---

## 0. 何が起きたか (3 行)

1. 承認済み `record-items-v2.md` が固定 semantic validator に要求する検査のうち **4 件**は、
   同じく承認済みの `receipt-schema-v1.json` に**入力が存在しない**ため実装不能である。
2. D291 の land により承認根が 2 本 (`F_r` / `F_p`) になり、**両者の exact 閉包を 1 枚の manifest に
   同居させられない**ことが判明した。manifest 表現が未裁定である。
3. D292 の land により、**確定裁定 RP-4 (a) の「公表 core 3 文書の凍結承認 + fold = pilot 解禁条件」は
   失効した。**

---

## Q1. semantic validator の入力欠落 4 件をどう解消するか (最重要)

### 事実

段 2 と段 3 の 2 レンズが独立に、**「承認済み記録要件が要求する検査を、承認済み受領証 schema の
情報だけでは構成できない」**欠落を 4 件検出した。

**4 件は同型ではない。** 段 6 レビュー B の指摘を受けて分解する
(**初稿はこの 4 件を「schema に入力そのものが無い内部矛盾」と一括していた。その一括は撤回する。**)

| ID | 欠落の型 | 要求している承認済み逐語 | schema 側の実体 | 実装不能になる項目 |
|---|---|---|---|---|
| **B1** | **raw pointer そのものの欠落** | §6.3 が configure argv / `compile_commands` / **`CMakeCache.txt`** の 3 者再読を要求 (`record-items-v2.md:600-608`) | `cmake_cache` は**値 object** のみで、`CMakeCache.txt` の `fileRecord` が**存在しない** (`receipt-schema-v1.json:94-171`) | **§7.1(12)** 申告値と実体の 3 者一致 |
| **B2** | **外部 authority (母集合) の欠落** | §4.13 が qsub 前の durable intent、create-only、全 attempt の exact 被覆を要求 (`record-items-v2.md:450-476`)、§6.2 が qsub 失敗 row も含む母集合との照合 (`:581-582`) | attempt ごとの `intent_ref` は**実在する** (`receipt-schema-v1.json:1092-1138`)。欠けるのは authoritative な母集合 index / canonical namespace / `O_EXCL` 発行履歴 | **§7.1(16)** `intent_ref` / marker の create-only 性 |
| **B3** | **receipt-set の discovery / consumer 契約が未裁定** | §6.1 が別 stage の受領証に**同じ** verification allocation を**同じ bytes** で記録することを要求 (`record-items-v2.md:583-585`) | 1 stage 1 receipt の exact top-level のみ。**peer receipt を誰がどう同定するか**が定まっていない | **§6.1** の stage 間整合 |
| **B4** | **raw grammar と authority binding の欠落** | §4.12 が transcript の再計算を要求 (`record-items-v2.md:421-444`)、§6.8 が main の slot 数を再導出した `J` と一致させる (`:677-684`) | transcript の raw pointer は**実在する** (`receipt-schema-v1.json:941-955`)。欠けるのは canonical byte grammar / authority binding / 数値実装契約 | **§4.12 / §6.8** |

**B3 の分類は途中で変えた。** 段 3 の 2 レンズは割れた — lensA は「pilot/main の両 path を受ける
receipt-set consumer を次 session で作れば閉じる」、lensC は「schema に peer receipt pointer が
無いので内部矛盾」。親は段 4 で lensC を採ったが、**段 6 レビュー B が
「schema へ peer pointer を足すことが唯一の解とは限らない」と指摘し、親はこれを認める。**
確実に言えるのは **canonical な receipt-set namespace / discovery 契約が未定義である**ことまでで、
解が schema 変更かどうかは開いている。

**4 件に共通するのは次の 1 点である。** いずれも**承認済み文書だけからは受理述語を一意に
構成できない。** `receipt-schema-v1.json` と `record-items-v2.md` は D282 で exact bytes
承認されており、**本 session はその bytes を 1 bit も変更できない。**

**両レンズが最大 risk として名指しした失敗モード:** 存在しない入力を producer の申告値
(`cmake_cache` / `fixed_inputs` / `len(consumed_cluster_slots)`) で代用し、
**通ってしまう validator を「実装済み」として記録すること。** §8 の否定検査はまさにこれらの field を
「受理条件の入力に使ってはならない」と列挙している (`record-items-v2.md:784-799`)。

### 反証を試みた結果 (refuted になったもの)

段 2 が挙げた B5 (「観測終了から exec まで他の作業なし」を見る event stream が無い) は
**refuted** である。ただし**初稿は根拠の引用を誤っていた** (段 6 レビュー B が指摘)。
`record-items-v2.md` §9 の `:803-813` は**経路 3 の偽 raw に限定された**残余であり、
B5 の義務 (`:623-630`) を引き受けた逐語ではない。**この引用は撤回する。**

正しい根拠は §9 の次の項である —
「**producer が実際とは異なる bytes や schedule で走らせながら整合した受領証を作る偽造は
検出できない。**受領証の三つ組と `measurement_head` の照合が検出するのは『producer が書いた
2 つの文書の食い違い』であり、実測 checkout の一致ではない」。
観測終了から exec までの隠れ作業は「実際とは異なる schedule で走らせる」に含まれる。

**この解釈に伴う上限を明記する。** validator が保証できるのは
**「記録された窓・間隔・時刻が相互に整合すること」までであり、「実際に他の作業が無かったこと」は
保証しない。**「他の作業が無かった」と記録してはならない (絶対規律 3)。
この解釈自体が誤りだと判断される場合は、canonical decision で正すべき論点として返す。

### 問い

B1 / B2 / B3 / B4 をどう解消するか。

- **(a) 4 件を閉じる新しい canonical decision を 1 本起こす** (親推奨)。
  **ただし解が全部 schema 変更とは限らない。** 型ごとに手当てが違う —
  B1 は `cmake_cache_raw: fileRecord` の追加 (schema 変更)、
  B2 は producer 権限外の intent 母集合 authority と canonical namespace の新設、
  B3 は receipt-set の discovery / consumer 契約の確定 (schema 変更を伴うとは限らない)、
  B4 は `j_derivation` transcript の canonical byte grammar と authority binding の確定。
  **理由:** 4 件は「承認済み文書だけでは受理述語が一意に決まらない」という同じ根を持ち、
  **同じ承認 payload (D282 の pin 集合) に触れる。** 別々に裁定すると承認三つ組と実装 pin が
  4 回連鎖して動く。**1 本にまとめるのが最も壊すものが少ない。**
- (b) 4 件それぞれを独立の decision で閉じる。
  → 親は反対する。上記のとおり pin が 4 回連鎖する。
- (c) 実装可能な項目だけで semantic validator を作り、4 件は
  「未実装」を明示する専用の rejection で hard-stop する。
  → 親は条件付きで可と考えるが**推奨しない。** 「§7.1 の 20 項目を担う」と承認済み文書が
  定めている以上、16 項目だけ実装したものを semantic validator と呼ぶと、
  land 1 の §S8-2 が言う「schema の適合は受理ではない」と同じ誤読を validator の層で再生産する。
  ただし (a) の decision が出るまでの**暫定**としてなら意味がある。
  **(a) と (c) は排他ではない** — (c) を先に入れ、(a) の後に残り 4 項目を足す順序もありうる。
  この順序を採るかも同じ問いとして裁定を求める。

---

## Q2. approval manifest の表現 (D282 と D291 の二重閉包)

### 事実

- **D282** (`F_r`) は三つ組 7 件 (target core 1 + approved blobs 6)、`erratum_application_order`、
  `composed_sha256`、`not_approved_as_record_items_root`、`operational_boundary` の exact 一致を要求する。
- **D291** (`F_p`) は `exact_closure` として **approved role ちょうど 2 件**、
  `(path, commit, sha256)` の allowlist、`document_relations` の**節全体** exact 一致
  (「括弧内に挙がっていない field も照合対象。key の追加も削除も解決失敗」)、
  `historical_candidates_rejected_for_role` の**拒否義務**を要求する。
- **両レンズが独立に同じ結論へ達した** — **共有 1 個の `approved_blobs` 集合へ両者の role を
  union する形**では両立しない。
  - flat union にすると D291 の「2 role ちょうど」を破る
  - D291 の 2 role だけにすると D282 の三つ組・erratum 順序・schema root が落ちる
- **ただし「平坦な表現は一切不可能」ではない** (段 6 レビュー B が指摘。
  **初稿の不可能性・唯一性の主張は撤回する**)。反証されたのは上の 2 形だけであり、
  decision 別に修飾した field を持つ単一 object や、manifest 2 枚を禁じる逐語は
  D282 にも D291 にも無い。D291 の `exact_closure` は「**本 decision が承認する集合について**」の
  scope 限定を明記している。したがって下の (a)(b) はいずれも成立しうる設計であり、
  **どれを正本とするかが裁定事項である。**
- **`addendum_b` の承認は D291 側にしか無い。** D282 の `approved_blobs` に `addendum_b` role は
  存在しない。`resolve_effective_preregistration` は `addendum_b` を引数に取る署名なので、
  承認根なしで解決すると §S7 #1 の穴を `addendum_b` role で**新設する**ことになる。

### 問い

manifest をどう表現するか。

- **(a) 固定 manifest envelope の中に role 別の namespaced projection を置く** (親推奨)。
  lensC の提案どおり `approval_manifest/v2` の下に `d282_record_approval` (fold root = `F_r`) と
  `d291_publication_approval` (fold root = `F_p`、`document_relations` 全体 +
  historical rejects + `role_coupling`) の 2 区画を持ち、`conformance_vectors` は別 namespace とする。
  **root の選択は caller にも manifest にも渡さず、role からの内部固定写像にする。**
  **理由:** 両 decision の閉包をそれぞれ自分の区画の中で exact に保て、
  区画を跨いだ role の融通が構造的にできない。**(唯一の形だとは主張しない。)**
- (b) manifest を 2 枚に分ける。
  → 親は反対しないが (a) を推す。2 枚だと「どちらを読むか」の選択が resolver の外に漏れやすく、
  D291 の `role_coupling` (「parse 失敗・trust root 失敗は両承認を同時に落とす」) を
  実装で保証しにくい。
- (c) `addendum_b` を manifest の外に置き、resolver が D291 payload から直接読む。
  → 親は反対する。第 1 矢印 (台帳 → manifest) を `addendum_b` role で失う。

**同束で決めたいこと:** `alpha_reservation` は RP-1 で「manifest へ再掲せず resolver が D282 payload
から直接読む」と裁定済みだが、レンズは「**manifest が D282 payload 全体を exact に表すこと**とは
別問題であり、payload 直読の別 namespace か固定参照が要る」と指摘した。
`alpha_reservation` の 6 field (`ledger_path` / `family_root` / `ordinal` /
`entry_canonical_bytes` / `reservation_entry_sha256` / `ledger_blob_sha256` /
`entry_serialization` / `ledger_introduction` / `reservation_commit`) を manifest の照合対象から
外したまま、「manifest は D282 payload と exact 一致する」と言えるか。

- **(a) 言える。** `alpha_reservation` は resolver が payload から直読する別経路として明示し、
  manifest の exact-key 閉包に**含めない**と契約に書く (親推奨。RP-1 の裁定と整合)
- (b) manifest の別 namespace に含めるが、resolver は payload 側を権威として読む

---

## Q3. RP-4 (a) の解禁条件 — pilot / 本走をいつ開けるか

### 事実

**初稿は 2 点を誤っていた** (段 6 レビュー B が指摘)。訂正した形で書く。

- **RP-4 (a)** (2026-08-11 第 9 回) = 「pilot 解禁条件 = 公表 core 3 文書の凍結承認 + その fold」。
  ここでの 3 文書は **新 core v2 / 追補 B 再発行版 / 追補 P 草案**である。
- **【訂正 1】3 文書の凍結承認は成立していない。** D291 (`F_p` = `b13b7ea8`) が exact bytes 承認したのは
  **`publication_core` と `source_addendum_b` の 2 role ちょうど**であり、
  **追補 P の blob は明示的に未承認**である (`blob_approved = false`、
  `addendum_p_blob_approved = false`。承認したのは `p01` / `p02` の**値だけ**)。
  D291 は追補 P の凍結を「公表台帳の実体が確定した後」と条件づけている。
  **初稿の「3 文書の凍結承認 + fold は D291 として既に起きた」は撤回する。**
- D291 自身が `operational_state_on_fold` で
  `pilot_submission = forbidden` / `main_submission = forbidden` /
  `source_main_run_gate = not_implemented` を固定した。
- **D292** が「禁止を解除できるのは canonical 台帳へ fold された decision だけ。
  **wave の自己申告・manifest の宣言・実装 wave の完了報告・handoff の記載では解除しない。**
  解除条件の中身は本決定では定めない。pilot と本走は根拠が異なるため解除もそれぞれ別に裁定する」
  と定めた。
- **【訂正 2】D292 が失効させたのは「その条件が揃えば自動的に解禁される」という十分性だけである。**
  D292 は**解除権限と手続き**を定めたのであって、解除条件の中身は定めていない。
  したがって **3 文書の凍結承認が将来の解除条件の候補から外れたわけではない。**
  **初稿の「RP-4 (a) は失効した」という書き方は過大であり、撤回する。**

**残る帰結は次の 2 点である。**

1. **RP-4 (a) の条件が揃っても、それだけでは pilot は開かない。**
   別の canonical decision が要る (D292)。
2. RP-4 (a) のうち「§S7 #7 を [T-793] へ委譲し `b03` consumer を書かない」部分は
   **D292 と衝突せず、有効なままである** (本 session はこれを守り、`b03` consumer を 1 行も書いていない)。

### 問い

RP-4 (a) の解禁条件をどう記録するか。

- **(a) 「RP-4 (a) の条件だけでは自動解除できず、別の canonical decision を要する」と記録し、
  3 文書の凍結承認は将来の解除 decision へ提出する条件候補として保持する** (親推奨)。
  **理由:** D292 の逐語から導けるのはここまでである。条件そのものを否定する根拠は無い。
- (b) RP-4 (a) の解禁条件部分を全面的に失効させ、解除条件を白紙から起こす。
  → 親は反対する。D292 は解除条件の中身を定めていないので、
  既存の条件候補を捨てる根拠が canonical に無い。

**あわせて:** peer (`t139 core c2c2bc4`) が返した未裁定 R1 のうち、
**解除権限は D292 で決着している** (canonical decision の専権)。
**残る未裁定は「解除条件」と「成立証拠」の 2 つ**である。
本 session の scope 外だが、Q1 の 4 件が閉じるまで pilot の gate は実装完了しないため、
**先に決めても実装が追いつかない。**親推奨は「Q1 が閉じてから解除条件を問う」である。

---

## Q4. 次 session の scope をどう組むか

### 事実

- 段 2 の見積り改訂: production 2,680〜3,340 行 + test 2,900〜3,670 行 + vector data 1,800〜2,600 行。
  RP-1 (a) 裁定時の見積り (production 1,900 / test 2,400) の約 1.5 倍である。
- **本 session が閉じたのは §S7 #2 のみ。** #1 と #3 は Q1 / Q2 の裁定待ちで着手できなかった。
- 両レンズが指摘した追加要件:
  - `PreregBinding` は **identity-only** とし、`pilot_ready` 等の投入可否 field / 命名を持たせない。
    投入には canonical 解除 decision から mint される別の authorization を要求する (D292 と整合)
  - resolver の `repository_root` が caller 供給では「指定された一つの canonical local main」を
    同定できない (`operational_boundary` の逐語)。canonical root と `git-common-dir` の identity を
    caller の外で固定する必要がある
  - snapshot closure は `fileRecord` だけでなく `immutableArtifact` / `execWitness` /
    `performanceStartedMarker` も覆う必要がある
  - **変異の単一理由帰属が現状では成立しない** — schema → resolver → binding/writer → semantic の
    順に前段が先に拒否するため、後段 validator の変異が先取りされる。
    変異は「期待する node」ではなく「最初の拒否点」を記録しなければならない

**次 session の必須 acceptance (段 6 レビュー B の指摘で追加。初稿はこれらを落としていた):**

1. **実 production call edge を acceptance node で固定する。**
   official producer → 受領証 writer、および persisted receipt path → semantic validator → consumer。
   **これが無い限り §S7 #1〜#3 は「実装した」だけで production では発火しない。**
   本 session の時点で `orchestrator/preregistration/` を呼ぶ production コードは **0 件**である
   (test を除く caller が存在しない。`s8c_preregistration` は別 module であり無関係)。
2. **§6.7(8) の第 3 consumer (材料 report) による独立な全履歴走査。**
   resolver と validator の 2 consumer だけでは §6.7 を閉じたと記録できない。
3. **受領証 writer の canonical destination と series uniqueness を sink 側で固定する。**
   repo には既に generic な publisher が複数あり (`tools/pegasus/dispatch_compute.py`、
   `orchestrator/qualification/atomic_publish.py`)、AST の literal 検査では
   official receipt namespace へ到達する全 writer を覆えない。
4. **D291 の full projection** — `document_relations` 節全体、`historical_candidates_rejected_for_role`、
   `approved_values_for_future_addendum_p` と `value_projection`、`operational_state_on_fold`、
   `role_coupling`。三つ組の照合だけでは D291 の `exact_closure` を満たさない。
5. **`argv_raw` の byte grammar、snapshot の metadata / size cap、`reason_code` 経路 3 の
   条件表現** — いずれも現承認済み文書では一意でない。Q1 の decision に含めるか別途裁定する。
6. **`PreregBinding` / raw snapshot API** を (a) の component 一覧へ明記する
   (事実欄だけに書くと session scope から落ちうる)。

### 問い

次 session の編成をどうするか。

- **(a) Q1 と Q2 の裁定を先に確定させ、その後に 1 session で
  manifest + resolver + writer + validator + vectors を組む** (親推奨。RP-1 (a) の再実行)。
  **理由:** RP-1 (a) の裁定理由 (順序制約と支配点が同じ session に入って初めて
  「§S7 #1・#2 が発火する」と言える) は今も正しい。壊れたのは前提であって理由ではない。
  Q1 / Q2 が閉じれば同じ編成が成立する。
- (b) Q1 の裁定を待たず、Q2 (manifest 表現) だけ先に裁定して manifest + resolver を組み、
  writer + validator + vectors を次々 session へ回す。
  → 親は反対する。resolver だけの session は本 session と同じく foundation-only で終わり、
  「実装したが 1 度も呼ばれないコード」を積む。これは RP-1 (a) が明示的に避けた形である。
- (c) `submit_pilot` / driver / collector など producer 側を先に作る。
  → 親は反対する。D292 が投入を禁止している間に投入経路を作っても発火しない。

---

## Q5. dev-wave 改善候補 3 件 — RP-5 と同じ予算制約で [T-789] へ回付する

### 事実 (本 session の実測)

段 8 で 5 件の改善候補が出た。**2 件は本 session で処理し、3 件は `docs/dev-wave/**` の
L1.5 予算に当たるため回付する。** RP-5 (a) の裁定 (「argv 制約 2 件は [T-789] の独立審査へ、
審査が済むまで `DW-O01` は現状のまま」) と**同じ制約・同じ routing 先**である。

**回付する 3 件:**

1. **`DW-O01` が `--max-cli-reported-tokens` の既定 100 万では read-only consult に足りないことを
   述べていない。** 本 wave の第 2 レンズは必読資料を読み切る前に 110 万で SIGTERM され、
   23 分・50 model call を消費して**成果物ゼロ**になった。`--max-*` が「非権威の運用既定」
   (= caller が上げてよい) であることは `--help` の本文にしかない。
2. **重い read-only 子の prompt へ「予算が尽きそうなら途中結論を出力形式どおり書いて終われ」を
   入れる規律が無い。** 無出力で打ち切られるのが最悪の結果である。routing 先は `DW-O05`。
3. **必読資料に repo 内 path を書くとき、worktree が local main より遅れていると fail-closed する。**
   本 wave の lensB 初回は peer が land したばかりの insight を `$R/...` で指定して即停止した
   (正しい fail-closed だが 1 巡無駄)。親が job dir へ取り出して渡すのが正解。routing 先は `DW-O02`。

**本 session で処理した 2 件:**

- 待ち手 script が「exit 0・stdout 空」で完了通知を出す事象を 5 回実測した
  (producer 生存、`.done` も成果物も無し)。3 点照合で偽と判定して張り直せば回復する。
  **結果を job dir のファイルへも `tee` で書く**運用を memory へ追記した (docs 予算の外)。
- 変異 spec の root exact key 契約 (`timeout_seconds` / `hang_timeout_seconds` 必須) で 1 度弾かれたが、
  **これは既存 memory が既に正しく記述していた。**新規記録はせず、親の適用漏れとして記録する。

### 問い

- **(a) 3 件を [T-789] の独立審査へ追加し、審査が済むまで `docs/dev-wave/**` は現状のままとする**
  (親推奨)。RP-5 (a) と同じ形である。実害はいずれも
  「即死または 1 巡無駄で成果物ゼロ」であり、**黙って誤った結果を出す種類の失敗ではない。**
- (b) `docs/dev-wave/**` から陳腐化した規則を探して削除し、空いた予算で入れる。
  → 親は反対する。削除候補の判定は repo 全体の意味検索を要し、本 wave の scope から外れる。

---

## 付録 A. 本 session が撤回した親の裁定・主張

| ID | 内容 | 撤回理由 |
|---|---|---|
| 段 1 brief | 「binary の SHA-256 が同一だから親子は同じ file を見ている」 | lensA: 同一 SHA-256 は bytes の一致しか示さず、同じ file object / inode / mount を示さない。byte-identical copy・bind mount・overlay 上の別 inode も同じ digest を持つ。親が主張してよいのは「sandbox の uid 表示を親環境の事実へ移せない」までである |
| 段 1 brief | 「承認根は D282 @ `F_r` の 1 本」(暗黙の前提) | D291 の land で `addendum_b` の承認根が `F_p` に立った |
| 段 1 brief | 「RP-4 (a) がそのまま pilot 解禁条件になる」 | D292 により、条件が揃っても別の canonical decision なしには解禁しない (Q3) |
| 段 1 brief | 「本 session が §6 全件・§7.1 全 20 項目を閉じる」 | Q1 の 4 件が構成不能。加えて §6.7(8) の第 3 consumer が scope 外で、両レンズが「§6 全件を閉じたと記録してはならない」で一致 |
| (P2) | vectors → digest → manifest の順序依存を「別 lane が書き込む」で解く | 順序依存自体は 1 session 内で閉じる (lensA)。閉じない原因は循環ではなく manifest 表現の未裁定だった。したがって (P2) は誤りではないが**前提が成立していない** |

**段 6 レビュー B の指摘で本パッケージ自身から撤回したもの (初稿 → 現行):**

| # | 初稿の主張 | 撤回・訂正の理由 |
|---|---|---|
| 1 | Q1 の 4 件を「同じ型 = schema に入力そのものが無い内部矛盾」と一括 | B2 の `intent_ref` と B4 の transcript pointer は**実在する**。欠けるのは authority / grammar であり型が違う。B3 は schema 変更が唯一の解とは限らない。→ Q1 を 4 型へ分解した |
| 2 | B5 refuted の根拠に §9 `:803-813` を引用 | 当該項は**経路 3 の偽 raw 限定**で、B5 の義務 (`:623-630`) を引き受けた逐語ではない。→ 「異なる bytes / schedule での偽造は検出できない」の項へ差し替え、validator の保証上限を明記した |
| 3 | 「1 枚の平坦な manifest では両立しない」「namespaced projection が唯一の形」 | 反証したのは**共有 1 個の `approved_blobs` へ union する形**と**D291 の 2 role だけにする形**の 2 つだけ。平坦な表現全般を禁じる逐語は無い。→ 不可能性・唯一性の主張を撤回した |
| 4 | 「3 文書の凍結承認 + fold は D291 として既に起きた」 | **偽。**D291 が承認したのは 2 role ちょうどで、**追補 P の blob は明示的に未承認**である。→ Q3 の事実欄を訂正した |
| 5 | 「RP-4 (a) は D292 により失効した」 | D292 が失効させたのは**自動解除としての十分性だけ**であり、条件候補としては残る。→ 「条件が揃っても別 decision を要する」へ弱めた |
| 6 | README「新規の休眠コードを積むことではなく既存の穴を塞ぐこと」 | production 結線済みと誤読させる。**この package を呼ぶ非 test caller は 0 件**である。→ 「穴は既存基盤層にあるが、その穴を通る production 経路もまだ無い」へ訂正した |
| 7 | Q4 の次 session 要件 | production call edge、§6.7(8) 第 3 consumer、writer sink の支配点、D291 full projection、`argv_raw` grammar 等が落ちていた。→ 必須 acceptance 6 項目を追加した |

## 付録 B. RP-2 (a) の却下理由 1 本が実測で消えた

RP-2 の事実欄は「本環境の `/usr/bin/git` は owner `uid/gid = 65534/65534` (nobody) であり、
『root 所有必須』を採ると本環境を拒否する」を (b) の却下理由に挙げていた。

**親の実測では `/usr/bin/git` の owner は `uid/gid = 0/0` (root) である。**
`65534/65534` は段 3 lensA が **codex 子の sandbox 内**で観測した値で、
lensA (本 session) が `/proc/self/uid_map` を読み「host UID 31609 だけを namespace UID 0 へ写す構成で、
host root が overflow UID 65534 に見える」ことを確認した。

**RP-2 (a) の選択と実装部分集合は変わらない** (部分集合は owner を受理条件に使わない)。
ただし両レンズが一致して次を指摘した — **RP-2 (a) を「owner に依存しないので十分」と
記録してはならない。** owner が root であることは一般 user による binary 置換の可能性を下げるが、
bind / overlay、shared library、trusted root 侵害を閉じず、**部分集合の十分性を独立には証明しない。**
