# 8b 裁定パッケージ (2026-07-16) — 次セッションでユーザー裁定を求める 6 単位 + R3/S 層の確定事項

**本文書は裁定資料 (非正本)。裁定の記録は `docs/phase3-8b-descriptor-design.md` §9 と
`docs/worklog.md` が正本。** 本文書は凍結族 (output/insights/) であり、裁定後も書き換えない —
裁定結果は §9 承認状態と worklog へ記録する。

- 出自: worklog 2026-07-16 (9) 追記の再開手順 (docs/worklog.md:986-992) に基づく裁定準備。
  敵対相談 4 本 (C-A/C-B/C-C/C-D) の逐語と親裁定表は
  `output/insights/2026-07-16_s8b-ruling-prep-consultations.md` (親裁定表 = 採用済み修正の正本:
  C-D=:127、C-B=:230、C-A=:424、C-C=:553)。相談所見はデータであり、本文書の記述はすべて親が
  現物ファイルと突合済み。**file:line 引用の基準コミット = 50b499b** (worktree 現物)
- 構成: 裁定 1〜2 = §9 項 7〜8 (worklog:966-968 で「もっと詳しく」の保留)。裁定 3〜4 = A3-3/A3-4
  の設計裁定。R3 = 裁定 4 の次の明文化節 (§9 項 4 の解釈確定)。裁定 5 = R5 量化。裁定 6 = floor
  実測 env。末尾に「裁定必須 vs 実装既定」の切り分け表。C-D 3 の層別裁定単位 (T/C/S/R3/R6/R5 —
  consultations:131) への対応: T=裁定 3 / C=裁定 4 / R6=裁定 2 (項 8 への統合は C-C 2 —
  consultations:556) / R5=裁定 5 / R3=明文化節 / S=切り分け表 + 裁定 1 代償 3。設計詳細は
  `output/insights/2026-07-16_s8b-freeze-v2-design-material.md` (S 層 :146-213 / R3 層 :217-257)
- 依存関係: 裁定 2 の択は裁定 3 (トポロジー) と相互依存 (marker の scope は topology に従属)。
  裁定 5 の floor 項目と裁定 6 は §6 第 3 条件を共有する。裁定 5 項目 4 の tie 伝播は裁定 1 の
  tie 意味論 (status=determinate / verdict=tie) を前提とし、裁定 1 が択 (b) 差し戻しの場合は
  項目 4 を再提示する。裁定 4 は単独でも決められるが、裁定 3 と同時に確定するのが望ましい
  (別々に決めると status/rc 契約が二度動く — 裁定 4 の代償欄)

---

## 裁定 1 — §9 項 7: oracle 集約 = median of medians の承認

### 裁定を求める文言

oracle winner の集約統計量を「各 trial 内の bench rep 中央値 → 構成ごとに trial 中央値たちの
中央値 (median of medians)」として §9 項 7 (docs/phase3-8b-descriptor-design.md:308-310) を
承認するか。

### 根拠

- 集約実装は実在する: `orchestrator/campaign/s8b_oracle_judge.py:104-105` が trial 内 median →
  trial medians の median を計算し、eligible cell の全 trial median をソート保存する
- §5.1 は一意最大の確定を規定するが集約統計量が未規定だった (§9 項 7 の凍結理由、
  docs/phase3-8b-descriptor-design.md:308-310)
- 二重中央値は独立で少数の外乱スパイクに頑健 (平均は 1 スパイクで汚染される) — 共有環境での
  計測に適合 (worklog:969-973 の保留時説明)
- floor は judge の入力にも argmax の tie-break にも使わない (s8b_oracle_judge.py:111-116 の
  docstring — 当該文は :115 — と実装 :226-234 の argmax が floor 非参照で一致)。floor の用途は §6 第 3 条件 (on/off 両予測構成間の oracle 実測差、
  docs/phase3-8b-descriptor-design.md:229) のみ — 第 1 条件 (on/off 予測 ID 差、同:227) には
  使わない

### 代償・限界 (C-A 親裁定 10/10 real を反映 — consultations:424-435)

1. **実装済み・ただし統計量を固定する回帰テストは未整備。** 現行テスト (fixture が対称 2×2 値)
   では median→mean 変異で unique-best / exact-tie の両テストが PASS することを親が in-process
   変異で再現済み (consultations:428)。「テスト済み」とは呼ばない。非対称 fixture + 数値 assert
   の追加は実装段 TODO
2. **exact tie は judge 上 `status=determinate` / `verdict=tie` / `winner=null`**
   (s8b_oracle_judge.py:226-234, :243-245)。「tie = 判定不能」ではなく「データとして確定した
   tie」。§6 の oracle 非一意 → 判定不能への写像は R5 結合 judge (未実装、裁定 5) の仕事
3. **rep 採否規則は未実装。** unstable / 部分 rep 欠測 / expected reps との束縛は judge に届かず
   (bench_values が非空・有限なら eligible — s8b_oracle_judge.py:90-102)、2/5 rep だけ成功した
   trial が 5/5 trial と同じ重みで winner を決め得る。これらの規則は freeze v2 の凍結項目
   (裁定後の再凍結で充填)
4. **頑健性の保証範囲は限定的。** 「1 スパイク耐性」は n/reps 未凍結 (現状 2 trial × 2 reps の
   テスト構成では二重中央値 = 全 4 値の平均と同値) の現状では成立しない。保証は凍結する
   n/reps・欠測規則・外乱の相関範囲に依存する。外乱が trial 過半に相関すれば奇数標本でも破れる
5. **practical tie band は置かない。** tie 判定は float の厳密 `==` のみ
   (s8b_oracle_judge.py:226-233)。floor 内の微小差 (100.0 対 100.0000001) でも point-estimate の
   oracle winner は一意になり得る。ただし §6 第 3 条件が別途 floor で締めるため、微小差の
   「成立」主張には至らない
6. **trial_medians 全件記録は eligible cell 限定。** unknown / correctness-disqualified cell は
   空配列 (s8b_oracle_judge.py:33, :80)。raw reps は別途 observations に残るが、sorted 保存に
   より trial/時系列対応は失われ、双峰性の機械 gate はない (事後監査材料)

### 選択肢

- **(a) 承認 (推奨):** 上記の限界を代償として明示したうえで median of medians を凍結。回帰
  テスト整備と rep 採否規則は freeze v2 側の TODO として同時に登録
- **(b) 差し戻し:** 別統計量 (trimmed mean 等) を再検討。代償: 頑健性と単純さの再設計、oracle
  実走がさらに遅延
- **(c) 条件付き承認:** 統計量固定テストと rep 採否規則の凍結を「実走前必須」に昇格して承認

---

## 裁定 2 — §9 項 8: 実走後 resume 拒否の承認 + crash 再走ポリシー

### 裁定を求める文言

§9 項 8 (実走後の途中再開拒否、docs/phase3-8b-descriptor-design.md:311-313) を承認するか。
承認する場合、**crash 後の再走を許すか否か**が中心裁定であり、択 (a)/(b) のどちらかを選ぶ。

### 根拠

- 拒否の動機: 実走後は WAL に holdout 条件が現れ、freeze の「結果を見ていない」保証 (未既知性
  検索) が失効する。途中再開を許すと「一部結果を見た後の再実行」と区別できず cherry-pick 経路に
  なる (worklog:974-980)
- 拒否分岐は実在し恒真 assert ではない: `orchestrator/campaign/s8b_oracle_driver.py:359` の
  条件付き raise (parsed WAL record が 1 件でもあれば拒否)

### 代償・限界 (C-A 5/6/7 + C-C 2/3 の親裁定を統合 — consultations:430-432, :556-557)

1. **実装の拒否境界は「実走後」ではなく「最初の有効 WAL record 以後」** — 凍結文言より安全側に
   広い。`_ensure_campaign` (s8b_oracle_driver.py:344-359) は holdout 結果の有無を見ず、
   campaign-start は budget 台帳生成より先に書かれる (同:391)。**bench 前の初期化・台帳失敗でも
   block が焼失する** = A3-3 との結合が本質 (third-wave-audit:38)
2. **回帰テスト不在。** 相談時の関数レベル確認のみ。production 経路は floor/budget non-null の
   freeze を v2 verifier 未実装として先に拒否する (s8b_oracle_driver.py:125) ため、:359 には
   通常経路で未到達。E2E 到達確認は v2 verifier 実装後
3. **迂回 2 経路は実在** (R6 で実証済み): `--output-root` 変更 (CLI が任意 path を許す —
   s8b_oracle_driver.py:617 付近) と campaign-start 1 行だけの truncated WAL。強化 (lock + WAL
   存在判定 + output-root 非依存の実走済みマーカー) は前提条件 (iv) として未実装
4. **強化案の「lock」は現行 `campaign.lock` とは別物の新設。** 現行 lock は非原子的な identity
   ファイル (exists 確認後に通常 `"w"` で書く — orchestrator/campaign/wal.py:146-152) であり
   相互排他ではない。原子的・耐久的な one-shot lock を新設する。marker のキーと scope は裁定 3
   のトポロジーで確定する

### 中心裁定: R6 マーカーと crash 再走は両立しない (C-C 2 — 骨子の内部矛盾として親が採用)

freeze 単位の marker は新 campaign_id での再走も拒否し、campaign 単位の marker は ID を変える
だけで迂回できる。二値論理上、次のどちらかしか選べない。

- **択 (a) marker 後再走なし = 項 8 現文言のまま承認 (こちらの含意):** 途中 crash は当該実験
  全体を判定不能へ倒す。代償: ハードウェア故障・停電のような正当な crash でも救済なし。6 セルの
  予測が残っても oracle が揃わず §6 結論は不能。同一 holdout での再挑戦 (再凍結してのやり直し) も
  不能 — holdout 実走後は未既知性検索が恒久に fail する (計測開始前にのみ成立する性質、
  s8b_holdout_freeze.py:595-597 の意図した fails-closed) ため、救済経路は存在しない
- **択 (b) 項 8 を改訂して再凍結:** freeze-wide の**事前割当 attempt registry** を導入 —
  最大再走数 K を実走前に凍結 / 再走は人手判断なしの自動発火のみ / **first-authorized-completed
  だけを採用** / correctness-red は全 attempt 横断で吸収的に disqualify / 複数 completed
  attempt は選択せず protocol violation (consultations:557 の採用規則)。予算面では **crash
  charge** (crash した attempt の実 bench 消費も総枠 B_total へ算入する課金規則 — C-C 12 で
  §5.2 整合を確認済み) と **contingency budget** (再走 K 回分を見込んだ予備枠) を実走前の予算へ
  含めて再凍結する (C-C 5)。代償: §9 項 8 の改訂は
  §8 手続き (docs/phase3-8b-descriptor-design.md:265-266) による再凍結 + 承認を要し、attempt
  registry・launch certificate の新規実装と検証が増える。「全 attempt 報告 + 予算拘束」だけでは
  cherry-pick は閉じない (悪い途中結果で crash → 新 ID 再走が予算内で反復可能) ため、上記の
  選択規則が必須

### 選択肢

- **(a)** 項 8 を現文言のまま承認 (crash = 実験全体判定不能を受け入れる)
- **(b)** 項 8 を改訂再凍結し attempt registry を導入 (実装コスト増を受け入れる)
- 参考: どちらでも迂回 2 経路の封鎖 (前提条件 iv) は必要。(a) は実装が最小、(b) は運用が現実的

---

## 裁定 3 — 実行トポロジー T 層 (A3-3 の処置)

### 裁定を求める文言

複数 block manifest で共有 budget 台帳が破綻する A3-3 (third-wave-audit:38-47) の処置として、
以下 4 点のトポロジー設計を承認するか (C-C 1/4/5/6 の親裁定 — consultations:555, :558-560)。

1. **manifest 単一 block 化:** schema で「1 manifest に block は正確に 1 件 + その block に予定
   全行 (n=1 なら 12 行) を含有」を強制し、build/verify 双方で `len(blocks)==1` を検査する。
   現行の campaign↔block 一対一検査 (orchestrator/campaign/s8b_oracle_manifest.py:485, :613) は
   複数 block を正式に許すため、これの言い換えでは A3-3 を直さない
2. **freeze-identity 束縛の累積台帳:** ledger/marker の identity を v2 freeze byte hash から
   導出し、header に generation/policy/schedule hash を固定する。現行 ledger header に freeze
   hash はない (orchestrator/campaign/s8b_budget.py:14-16 のスキーマ)。CLI の `--budget` path
   override (s8b_oracle_driver.py:618) は廃止するか canonical 一致を要求 — 別 path 指定 =
   別台帳、で総枠が複製される現状を塞ぐ
3. **事前一括 reservation → 実測精算:** attempt 開始前に全予定行の最大 bench 枠を freeze-wide
   lease 下で予約し、terminal 後に実測へ精算する。**crash 時は予約を解放しない**。現行は
   予算確認 → evaluate → 完了後に debit の順 (駆動側の debit は evaluate 後 —
   s8b_oracle_driver.py:441-449 の行単位 assert_available と :567-568 の debit 拒否処理) で、
   crash が append より前なら物理消費が台帳から消える。actual_bench_s と charged/reserved の
   分離、並行 campaign の禁止または reservation 直列化を含む
4. **budget_exhausted_before_attempt:** 一括 reservation が確保できない場合は一行も走らせず、
   全体を判定不能に倒す。§5.2 の「予算不足は未実施 arm を対称に判定不能へ倒す」
   (docs/phase3-8b-descriptor-design.md:209-212) と整合。残額が全行最大費用未満での再走開始は
   「途中停止を予定する行為」であり禁止

### 代償・限界

- 単一 block 化は「複数 block による時間分離」をトポロジーとして失う。時間分離が必要なら別
  freeze/campaign として設計し直す (§5.2 の時間分離 block 規定との関係は freeze v2 設計で明示)
- 事前一括 reservation は保守的 = 実消費より大きい枠を先取りするため、予算利用効率が下がる。
  crash 時非解放と合わせ「安全側で予算を余らせて判定不能」に倒れやすくなる — これは §5.2 の
  対称性維持のための意図的な代償
- 台帳の freeze-identity 束縛は別 worktree/host 間の共有問題を残す (共有不能なら execution site
  を一台へ固定する運用制約)

### 選択肢

- **(a) 上記 4 点を採用 (推奨 — C-C 親裁定):** A3-3 は「1 oracle = 1 block」拘束で解消
- **(b) 台帳継続 API (multi-block 対応):** A3-3 の (a) 経路 (2 block 目の BudgetError) を継続
  API で直す。代償: 共有計上経路の新規実装 + block 間 crash の意味論が裁定 2 と絡み複雑化
- どちらでも: 裁定 2 の marker scope はここで決まるトポロジーに従属する

---

## 裁定 4 — status/rc 契約 C 層 (A3-4 の処置)

### 裁定を求める文言

全行 binding-refused でも status=completed / rc 0 になる A3-4 (third-wave-audit:49-59) の処置と
して、以下の契約を承認するか (C-C 9 の親裁定 — consultations:563)。

- **completed の定義 = 「全 schedule 行に、report が受理できる一意の terminal outcome と対応する
  budget terminal record が耐久化済み」。** 現行は binding-refused で行が終わっても
  budget_stopped でなければ status="completed" になり (s8b_oracle_driver.py:593)、CLI は
  completed 以外を一律 rc 2 に潰す (同:637)
- **rc 優先順位の固定: internal-error(1) > protocol_violation(3) > budget-refused(2) >
  completed(0)。** 現行 rc: 例外=1 (同:642)、gate 拒否/非 completed=2 (同:630, :637) で、
  protocol violation の区別がない
- JSON schema と CLI subprocess テストを追加する

### 代償・限界

- 下流 report/judge は fail-closed のため、A3-4 は certified な false-green には至らない
  (third-wave-audit:53-55)。実害は「rc 0 を成功と読む自動化が黙って前進し、WAL 汚染 + resume
  拒否で再実行不能の campaign が成功表示になる」ことに限る — 緊急度は low、ただし裁定 3 の
  トポロジーと同時に決めないと契約が二度動く
- rc 3 (protocol_violation) と衝突する既存 consumer は確認されていない (C-C 12 攻撃失敗欄)

### 選択肢

- **(a) 上記契約を採用 (推奨)**
- **(b) status のみ直し rc は現状維持:** 自動化からの誤読リスクを残す
- gate-refused の rc (現行 2) を別値にするかは実装既定に委ねてよい (末尾の切り分け表)

---

## R3 — trusted prediction runner の契約明文化 (§9 項 4 の解釈確定)

C-D 3 の層別 (consultations:131) の R3 層。新規の選択規則ではなく、承認済み §9 項 4 (「予測は
2 holdout × 3 arm = 6 セルを各独立 1 回で固定 … 結果の再利用・不正出力の再試行をしない」—
docs/phase3-8b-descriptor-design.md:295-297) の crash 意味論の解釈確定であり、設計素材
(2026-07-16_s8b-freeze-v2-design-material.md:250-253) が本パッケージへの明文化を委譲した項目。
承認済み規則の適用確認であって新規緩和ではないが、裁定として明示確認を求める。

- **契約 = at-most-once。exactly-once は主張しない** (C-C 7 で骨子の exactly-once 主張を撤回・
  修正採用 — consultations:561)。ローカル台帳では実現不能: claim を call 前に書けば「claim 後・
  call 前 crash」でゼロ回、call 後に書けば「call 後・記帳前 crash」で再走時の二重呼出になる。
  宣言だけの遮断は F14 型
- **結果不明 crash = 当該セル missing で恒久確定 (再呼出なし)。** missing セルは §9 項 5 により
  `choice_id=null` で凍結され、§6 の該当条件が判定不能へ倒れる。救済再試行・fallback は置かない
  (承認済み項 4/5 を弱めない側の確定)
- durable claim 先行 + 実 invocation receipt + raw 応答 bytes を同一 append-only journal に束縛。
  claim なき応答・応答なき二重 claim はどちらも protocol violation。off arm 2 セルは invocation
  record を持たない static terminal record (§9 項 1 の static_default)
- journal 形式・claim 機構 (O_EXCL 等)・receipt 記録項目・off arm record の schema は実装既定
  (設計詳細 = 2026-07-16_s8b-freeze-v2-design-material.md:217-257)

---

## 裁定 5 — R5 量化: §6 判定表の truth table を逐語凍結する

### 裁定を求める文言

§6 の判定表 (docs/phase3-8b-descriptor-design.md:225-230) は存在量化の対象・符号・伝播を規定して
いない (C-C 10 — consultations:564)。prediction と oracle を結合する judge (未実装) の判定定義と
して、以下 5 項目を逐語 truth table で凍結する。各項目に推奨案と代替案を併記する。

1. **swapped 追従は両 holdout 必須か。**
   - 推奨: **両 holdout 必須。** holdout は 2 つしかなく (rr80/rr20 —
     output/s8b-freeze/holdout_freeze.json:40, :307)、derangement は 2 要素の相互 swap
     (同:617-618)。片側のみの追従は 6 構成からの偶然一致と区別しにくく、n=2 では「存在する」
     量化が実質 1 標本の主張になる
   - 代替: いずれか 1 holdout で成立 (§6 第 1 条件の存在量化と同型)。採る場合は偶然一致率
     (~1/6) を報告に併記する
2. **floor 差の方向: `oracle(on) − oracle(off) > floor_<holdout>` (方向付き) か絶対差か。**
   - 推奨: **方向付き。** 「descriptor が性能改善を駆動した」と主張するなら on 側が floor を
     超えて優ることが必要。絶対差では off が優る場合も「成立」になり主張と乖離する
   - 代替: `|oracle(on) − oracle(off)| > floor` (主張を「選択が floor 超の帰結差を持つ」まで
     弱める場合のみ)
3. **on/off 予測差と floor 超を同一 holdout に要求するか。**
   - 推奨: **同一 holdout に束縛する。** 予測が異なる holdout と実測差が出る holdout が別では
     「その選択差が性能差を生んだ」という因果の形にならない
   - 代替: 独立に評価 (弱い主張)。採る場合は §6 結論の文言を「選択差と性能差が別 holdout で
     観測された」へ弱める
4. **invalid / tie / excluded の三値伝播。**
   - 推奨: **fail-closed の伝播を凍結する** — selector 出力 invalid (§9 項 5、choice_id=null) は
     当該条件を判定不能へ / oracle exact tie (裁定 1 の限界 2) は §6 第 3 条件の「oracle 非一意」
     として判定不能へ / excluded 観測を含む cell は当該 holdout の oracle を判定不能へ。判定
     不能はいずれも §6 結論行の「前 3 条件のいずれかが判定不能」(同:230) へ伝播
   - 代替: 伝播粒度を cell 単位に細分し、無関係な holdout の成立可否を独立判定する (報告は
     複雑化する)
5. **rationale の扱い。**
   - 推奨: **診断材料に限定し、成立を昇格させる証拠に使わない。** parser は rationale の非空
     しか検査せず (C-C 10 の根拠)、候補 ID の列挙は「descriptor を消費した証明」にならない。
     descriptor 消費の証拠は swapped 追従 (§6 第 2 条件) が担う
   - 代替: なし (rationale を証拠へ昇格させる案は自己申告値の検査 = F14 型で却下)

### 代償・限界

- 推奨案はすべて fail-closed / 強い束縛の側であり、「成立」の達成が難しくなる。これは意図的 —
  §6 は不成立・判定不能を正直に報告する表であって、成立を作る装置ではない
- 結合 judge は未実装。truth table 凍結 → 実装 → テスト (受入ベクトル) の順で、実走前提条件
  (iii) (worklog:957-959) を満たす

---

## 裁定 6 — floor 実測 env: v2 数値を束縛する唯一の env-tag の選択

### 裁定を求める文言

§5.2 の対象別 between-run floor (docs/phase3-8b-descriptor-design.md:206-208 —
`floor_<holdout>` は holdout 単位のスカラー) の実測をどの env-tag で行い、**その env-tag を
freeze v2 の数値を束縛する唯一の env-tag とする**か。D59 (docs/decisions.md:2274) により異なる
env-tag の throughput は混ぜられない (同:2291) ため、これは二者併用でなく単一選択の裁定である
(ユーザー回答「普通に pegasus も cygnus も使う」— worklog:981-985 — は開発の併用であり、v2 数値の
束縛 env とは別問題)。他方の env での再現の扱いも本項の裁定に含める (C-D 8 — consultations:136):
D59 の混合禁止から「別 freeze/campaign とする」が自然だが、第二 env を independent replication
レーンとする構成 (C-B 8 逐語 — consultations:205) の採否はユーザーの択として残す。

### 実測対象と既存資産の事実

- 8b の holdout は **rr80 / rr20 の 2 件** (output/s8b-freeze/holdout_freeze.json:40, :307)。
  floor の対象集合 (holdout ごとに加え比較対ごとまで含むか — §5.2 の「holdout の各 workload と
  比較対に先行させる」docs/phase3-8b-descriptor-design.md:206-208 の解釈、C-B 2 逐語 —
  consultations:157) は floor protocol の凍結項目であり、本欄では確定しない
- 既存 between-run noise floor 資産は **rr5 / rr50 / rr95 のみ**
  (output/env/linux-baremetal/calibration/ の between_run_noise_t48_skew0p9_rr{5,50,95}_rmw0.json)。
  現行 driver の POINTS も同 3 点固定 (orchestrator/campaign/between_run_floor.py:57) で、8b の
  対象を一つも測っていない — 既存資産は動作点の参考まで。holdout freeze から target manifest を
  生成する専用 driver が必要 (POINTS 手編集・既存 3 点の値コピーは禁止)

### 工数 3 欄 (C-B 親裁定の構造 — consultations:232-241)

| 欄 | 内容 |
|---|---|
| **共通必須 (env 選択に関わらず必要)** | floor protocol の凍結 (対象集合・n・reps・時間分離 block・別 process/build の扱い・算出式・cross-block 統合規則 — 凍結前の工数値は未確定) / strict v2 verifier (現行 driver は floor/budget non-null freeze を拒否 — s8b_oracle_driver.py:125) / 裁定 3 のトポロジー確定 / **F3 pgrep ギャップ修正**: 競合検知の検索パターンが従来ビルド木 `build-variants/.*ycsb_.*\.exe` 固定 (orchestrator/calibrator/runner.py:71) で、8b は `s8b-build-cache` 配下でベンチを走らせる (s8b_oracle_driver.py:466) ため孤児 8b ベンチを見逃す — binary path 非依存の競合検知へ (failures F3 = docs/failures.md:36 の恒久対応の穴) |
| **cygnus (linux-baremetal) 差分** | reuse qualification (既存 calibration の hardware/kernel/toolchain/pin 契約照合 — 既存 artifact に計測日時・pin がなく鮮度未証明。ただし陳腐化の証拠もない) / 計測時間そのもの |
| **Pegasus 差分** | 専用 env-tag 新設 + calibration・noise floor 取り直し (D59 の 4 条件 — docs/decisions.md:2283-2285) / driver の env contract 化 (ENV_TAG/NUMA/THREADS/RECORDS/CLK の p2_2 直輸入 — between_run_floor.py:44-45 — と `numactl --interleave=all` hardcode — s8b_oracle_driver.py:36 — の除去) / NQSV キュー待ち |

### 方法論 (これ自体も裁定項目)

- **(A) between_run_floor 同型の 2 点計測:** 1 点 = within 10 rep + 8 セッション × 5 rep
  (between_run_floor.py:53-55) ≈ 548s、2 点 ≈ **18 分** (S-1 実績 54.8s/セッションからの親
  セッション外挿。protocol 凍結前は未確定値)。ただし同一 build・back-to-back セッションで
  「fresh 下限」にとどまる
- **(B) S-1 floor campaign 同型の 12 セル × 8:** ≈ **1.5h** (protocol 凍結前は未確定値)。
  時間分離・独立性が強い。参考: S-1 本走実績は 6.37h/12h (docs/worklog.md:705)
- **注意: budget は floor から自動では出ない。** `n × reps × extime × max_rounds` からの bench
  上限の事前導出 + 既知 workload の full-pipeline pilot による wall-time 校正が別途必要
  (§5.2 の予算契約 — docs/phase3-8b-descriptor-design.md:209-212)。full pipeline 工数の見積り
  (pilot 校正) も本項の裁定材料 (C-D 8 — consultations:136)

### 選択肢

- **(A) cygnus (linux-baremetal) で実測:** 既存 tag のまま。前提 = reuse qualification + 共通
  必須欄。最短だが実行責任・時刻の handoff が要る (下記テンプレート)
- **(B) Pegasus 専用 env-tag を新設して実測:** 現在の主戦場と一致。前提 = D59 4 条件の全費用 +
  driver の env contract 化。工数最大
- **(C) env-neutral 共通実装を先行 (推奨 — 順序として):** 共通必須欄 (protocol 凍結・v2
  verifier・トポロジー・F3 修正) は env 選択に依存しないため先に進め、env 裁定は「v2 数値を
  束縛する唯一の env-tag の選択」として分離して確定する。worklog 再開手順の (3)(4)
  (worklog:986-989) が実測より先行する順序と整合。(C) を選んでも env-tag の裁定自体は本項で
  得ておく (freeze v2 schema の env_tag field を空欄にしないため)

### 実行計画テンプレート (env 確定後に埋めて着手する — C-B 9 の親裁定)

- revision: 計測に使う committed HEAD / CCBench pin (未 commit 作業木では走らせない)
- preflight: 計測ノード上での単独性確認 (F3 修正後の競合検知 + pgrep)、calibration との動作点
  照合、trace-disabled build の確認 (絶対規律 1)
- 停止条件: 競合検知時は計測放棄 → 再計測。abort rate・CV の異常閾値を protocol で事前凍結
- artifact 回収: `output/env/<env-tag>/calibration/` へ JSON + md、freeze v2 への数値充填は
  §8 手続きの再凍結として別 commit
- 実行責任者・開始時刻: ユーザー裁定側 (本文書では埋めない)

---

## 末尾 — 裁定必須 vs 実装既定の切り分け表 (C-C 11 の親裁定 — consultations:565)

§8 (docs/phase3-8b-descriptor-design.md:265-266) の再凍結 + ユーザー承認を要するものと、承認済み
規則を弱めない範囲で実装が決めてよいものを分ける。

| 区分 | 項目 |
|---|---|
| **裁定・再凍結必須** | §9 項 7 (裁定 1) / §9 項 8 + crash 再走ポリシー (restart 許可条件・crash charge・最大 attempt 数・contingency budget — 裁定 2) / manifest 単一 block 化 (裁定 3) / status・rc 契約の意味論 (裁定 4) / R3 契約 = at-most-once + 結果不明 crash は missing 固定 (§9 項 4 の解釈確定 — 上記 R3 節、C-C 7 — consultations:561) / selector_basis の versioned preimage 拡張 (C-C 8 — consultations:562。発効済み §9 項 6 が凍結した部分 hash の束縛内容 — docs/phase3-8b-descriptor-design.md:301-307 — の変更であり §8 の再凍結 + ユーザー承認事項。設計詳細 = 2026-07-16_s8b-freeze-v2-design-material.md:170-177) / R5 量化 truth table (裁定 5) / v2 数値を束縛する env-tag と floor protocol・方法論 (裁定 6) / floor・budget・n・seed・block・extime/reps・機械故障一覧 (allowed_excluded_reasons)・検定 4 点の数値充填 (§5.2/§6/§8 — docs/phase3-8b-descriptor-design.md:315-316) / rep 採否規則の本体と数値・expected reps 束縛・世代 schema の field 列挙 (S 層 — 2026-07-16_s8b-freeze-v2-design-material.md:178-185, :205-207) |
| **実装既定でよい (承認済み規則を弱めない範囲)** | 検証済み bytes の単一 read object 使い回し (A3-6 — third-wave-audit:70) / atomic create / strict parse / freeze-wide reservation の機構詳細 / 台帳・freeze の改竄検出 / rc の詳細値 (gate-refused の別番号化等、裁定 4 の優先順位を崩さない範囲) / R1 のアーカイブ方式 (世代別不変 filename + supersedes_sha256 + frozen_at_head の git blob 束縛) / A3-5 の受理域証拠束縛 (third-wave-audit:61 — v2 実走前の強化候補、現状 fail-closed) |

裁定 1〜6 がすべて得られても、selector 予測の実実行にはさらに worklog:956-961 の前提条件
(i)〜(v) の実装完了を要する (§9 冒頭の承認状態 — docs/phase3-8b-descriptor-design.md:275-279)。
