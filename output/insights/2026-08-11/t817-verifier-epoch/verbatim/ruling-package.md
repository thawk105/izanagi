# 裁定パッケージ — [T-817] は実測で前提が覆った: 突き合わせ対象は空で、除外の面は裁定の 4 倍広い

wave = `dev-wave-t817-verifier-epoch` / branch `worktree-dev-wave-t817-verifier-epoch`
base = main `276ab6cc` / **実装差分ゼロ** (段 4 で「実装しない」と裁定)
一次資料 = 同 directory の `brief.md` / `s2-plan.md` / `s3-lens-a.md` / `s3-lens-b.md` /
`s4-adjudication.md`、走査結果 `../log-survival-scan.txt`

---

## 0. 結論 — 裁定 (a) の条件節は空集合で、しかも「突き合わせ機構」は健全に作れない

[T-817] の裁定は **(a) 条件付き** だった。「当時の stdout ログ (`commit_counts_`) が残る記録は
再実行なしで突き合わせて白黒を付け、**ログが無く再評価不能な記録だけ**を検証不能として現行
certified 選択から除外する」。裁定文自身が「実装 wave はまずログ残存率を実測してから設計する」と
条件を付けていた。

**実測した。残存率は 0 である。** そして残存率が 0 であること以上に重い事実が 2 つ出た。

1. **突き合わせは、ログが残っていたとしても健全に作れない。** WAL と stdout を「同じ run」だと
   束縛する値が、どこにも記録されていない。
2. **「現行 certified 選択」の実体は replay/guided ではない。** 旧 certified / 旧 fitness を読んで
   順位・winner・certified 集合を作る生きた経路が **8 つ以上**ある。replay/guided だけを止めると、
   レポートは旧 winner を出し続け、成果物間で受理集合が食い違う。

よって親は本 wave で実装せず、新事実を添えて再裁定へ返す (DW-S04 は「親が不採用にせず、
新事実付きのユーザー再裁定待ちへ戻す」と定める)。

---

## 1. 実測 (一次資料 = 実 WAL 30 本、`output/` 全走査、git 全史)

| # | 実測 | 値 |
|---|---|---|
| M1 | 既存 WAL の `verify_done` | 572 件 (`certified=true` 571 / `false` 1) |
| M1 | 既存 WAL の `commit` | 459 件 |
| M1 | **`commit_witness` を持つ記録** | **0 件** |
| M2 | `output/` 走査 10,291 ファイル中、実 stdout (`commit_counts_:<数字>`) | 193 件 |
| M2 | そのうち **campaign pipeline の run に対応するもの** | **0 件** (全件が `output/env/pegasus/` 配下の別 producer = t141 較正 / silo_ladder_rung1 raw bundle / t139 probe / t155) |
| M2 | `/work/1/SFC/tanab/izanagi-jobs` 走査 | 0 件 |
| M2 | **git 全史で `output/campaigns` 配下に stdout 系 path** | **0 件** |
| M3 | 機序 | `pipeline._run_trace` は `capture_output=True` の stdout をその場で parse するだけで保存せず、trace_dir は `tempfile.mkdtemp` の使い捨て。**保存経路が存在しない** (消えたのではない) |
| M11 | 旧記録は世代を自己申告済み | `commit.payload.verify_configs` = `["legacy"]` 289 / `["legacy","s2"]` 111 / **不在 59**。`verify_done` の key 集合はちょうど 3 種 |
| M11 | **P2-2 の 24 件 (= replay/guided の材料全部)** | 最古の階層。`verify_configs` 不在・`aborts` 無し・`workload` 無し・`commit_witness` 無し |

除外の単位は verify 記録 (571) ではなく **committed attempt** である (敵対レンズ A の指摘を採用)。
すなわち **0/459** (全体)、**0/24** (P2-2)。

---

## 2. 新事実 — 突き合わせ機構は健全に作れない (これが最も重い)

裁定文は「stdout ログが残っていれば再実行なしで突き合わせ可能」を前提にしていた。**成立しない。**

- 現行 producer は WAL と stdout の**双方に共通する execution nonce を書かない**
  (`orchestrator/campaign/pipeline.py:349-362`)。
- WAL に残る `trace_bin` は 16 桁の**表示用 prefix** で、実装自身が identity 検査に使うなと明記して
  いる (`orchestrator/campaign/buildcache.py:37`)。実 P2-2 WAL にもこの短縮値しかない。
- したがって「lock SHA + WAL SHA + 行番号 + binary + stdout SHA + return code」を束ねた同伴 receipt を
  作っても、**それぞれの bytes を固定するだけで、同じ process が生んだ証明にはならない**。
  同じ binary で 2 回走らせ、run A の WAL 参照と run B の stdout を組んだ receipt が**通る**。

これは [T-756] wave が blocker として捕らえた「ladder の正式な correctness 証拠が、同じ run の
保存済み witness を使っていなかった」と**同型**である。突き合わせ機構を作ることは、same-run を
証明できない証拠を正証拠へ昇格させる経路を新設することであり、**絶対規律 2 に反する**。
しかも実 corpus では 1 件も発火しないので、**謳うだけで発火しない保証 (恒真な gate)** にもなる。

---

## 3. 新事実 — 「現行 certified 選択」の面は裁定の想定より広い

旧 `certified` / 旧 fitness を読んで順位・winner・certified 集合を作る**生きた経路** (実読で確認):

| 経路 | 何をするか |
|---|---|
| `campaign/replay.py` | P2-2 WAL から landscape を作り、`assert_complete` が「8 genome 全 certified」を要求 |
| `campaign/guided.py` | replay の certified をそのまま誘導 WAL へ書く |
| `campaign/search_baselines.py` | `assert_complete` を経由 |
| **`campaign/p2_2_report.py`** | **committed + median のみで winner を選ぶ。`certified` を一切見ない** |
| **`critic/digest.py`** | **committed のみで throughput 降順に並べ、先頭を fastest とする** |
| `campaign/s1_report.py` | WAL segment を certified sample として扱う |
| `campaign/s1_known_axes_freeze.py` | P2-2 commit の fitness argmax を選ぶ。**`test_s1_known_axes_freeze.py:85` が実 repo に対し `build_document()` を走らせる** = 凍結 producer は「走らせない」のではなくテストが実際に再構築している |
| `campaign/layer3_report.py` / `s8b_oracle_report.py` / `s8b_oracle_judge.py` | WAL の verifications / `certified` を直接読む |

**敵対レンズ 2 本が独立に同じ取り残しを発見した** (DW-G03 の「族一般化には独立 2 例」が成立)。
replay/guided だけに gate を置く実装は、`p2-2-summary.md` と critic 入力が旧 winner を現在値として
再発行するので、**成果物間で受理集合が食い違う**。

---

## 4. 新事実 — 識別子の衝突 (ユーザーが設定した停止条件に該当)

本 wave の起動時にユーザーは「識別子の設計が衝突したら止めて報告」と条件を付けた。該当する。

- `verifier_policy_sha256` は**未実装の設計語ではなく、実装済みの field** である —
  `orchestrator/campaign/reflux_origin_ledger.py:245` が `AuthorityManifest.verifier_policy_sha256`
  を持ち、`:257` の exact key 集合に入り、`:423 / :455 / :490 / :1854` で origin / cell identity の
  導出に使われる。段 2 プランはこれを「未実装の設計語」と誤認していた。
- build admission には別途 `policy_sha256` が実在する (`build_admission.py`)。
- 並走中の [T-804] は `spec_sha256` を manifest schema へ伝播中である。

新しい identity field を作るなら、この 3 つと**名前でも意味でも**分離する必要がある。

---

## 5. 新事実 — epoch を入れる土台は既に存在する (設計の追い風)

`campaign.lock` v2 の authority は、enforcement source closure 8 path の**blob SHA-256 を既に記録
している** (`campaign_lock.py:19-25, 29-38, 167-181`)。この 8 path には
`orchestrator/campaign/pipeline.py` — すなわち **witness gate 本体が住んでいるファイル** — が含まれる。

つまり **v2 lock を持つ campaign については、verifier policy に相当するコードの exact bytes が
既に campaign 単位で pin されている**。名前が付いていないだけである。
一方 **歴史 campaign の lock は v1** で authority を持たず、`search_config` に `build_admission` すら
無い (実測: P2-2 の `campaign.lock`)。歴史 campaign は元から id 再計算では到達できず、
dir 名 prefix discover だけが経路である (コード内に C1 として明文化済み)。

これは「epoch を新しい JSON artifact として発明する」より、**既存の authority 束縛に名前と検査を
与える**方が筋が良いことを示す (敵対レンズ A の「epoch SHA が実際の gate 実装に束縛されない」への
直接の答えになる)。

---

## 6. 裁定を求める 4 問

### Q1 (主問): 既存 WAL の witness なし certified をどう扱うか

| 選択肢 | 内容 | コスト / 帰結 |
|---|---|---|
| **(a)** | **§3 の 8 経路すべてを同じ gate に束縛し、E0 記録を現行 certified 選択から一律除外する** | 裁定文の趣旨に最も忠実。**P2-5 の replay/guided/baseline が停止**、`p2_2_report` と critic が旧 winner を出せなくなり、**凍結成果物の検証意味論にも触れる** (freeze 検証は再構築を走らせる)。専用の大型 wave が要る |
| **(b)** | **除外はせず、epoch を全記録に可視化する** — certified を名乗る成果物に「どの epoch の証拠に載るか」の表示を義務づけ、E0 = 現行 policy 未検証と明示する | 受理集合を変えない。実装は小さい。ただし裁定文の「除外する」を満たさない |
| **(c)** | **P2-2 を現行 policy で再計測して landscape を作り直す** | 除外せずに白黒が付く唯一の道。計測コストと旧 pin での再現性が要る |
| **(d)** | 現状維持 | **既に不採用と裁定済み**。参考として列挙 |

**親の推奨 = (a) を専用 wave として実施する。ただし「除外」の適用範囲を
「certified を名乗る受理集合」に限定し、歴史解析としての生値表示 (`p2_2_report` の raw 出力など) は
epoch 表示付きで残す。** 理由: 規律 2 の趣旨は「正しさが検証されていない証拠の上に certified を
積まない」であって「歴史記録を読めなくする」ことではない。除外を受理集合に限れば、失われるのは
「E0 の証拠で certified を主張する権利」だけで済み、Phase 2 の観測値そのものは残る。
**(b) 単独は推奨しない** — 表示だけでは `assert_complete` が「全 certified」を要求し続けるため、
規律 2 の穴 (未検証の証拠に載った certified) がそのまま残る。
**(c) は (a) と排他ではない** — (a) で止めた P2-5 を復活させたいなら (c) が唯一の手段になる。

### Q2: 「残存ログとの突き合わせ」機構を作るか

- **(a) 作らない** ← **親の推奨**。§2 のとおり same-run を証明できず、作れば規律 2 に反する経路を
  自作することになる。しかも実 corpus では発火しない恒真な gate になる。
- (b) 作る (同伴 receipt 方式)。**推奨しない。**
- (c) 作れるようにする = producer を変えて、今後の run では WAL と stdout の双方へ共通 nonce を
  出し、stdout を耐久保存する。**これは将来の記録にしか効かない** (過去へは遡及できない) が、
  同種の負債の再発は止まる。**別 T として起票する価値がある** (親の見立て = 有用)。

### Q3: epoch の識別子と束縛先

- **(a) `campaign_verifier_epoch` を新設し、v2 lock の既存 authority (`contract_loader_blob_sha256s`)
  へ束縛する** ← **親の推奨**。§5 のとおり土台が既にあり、実際の gate 実装 (pipeline.py) の bytes に
  束縛されるので「policy を変えずに受理意味論だけ変える」抜け道を塞げる。
- (b) 独立した policy JSON artifact を正本にする (段 2 プラン案)。実際の enforcement コードに
  束縛されない (レンズ A の所見 4)。**推奨しない。**
- (c) 既存 `search_config["verify"]` の意味論を拡張する。`verify` は pass 構成の軸なので二義化する。
  **推奨しない。**

いずれの場合も `verifier_policy_sha256` (Reflux)、`policy_sha256` (build admission)、
`spec_sha256` ([T-804]) と名前でも意味でも分離すること。

### Q4: scope 外の real 所見をどう扱うか

1. **S8b は独立 identity 層**である (manifest / driver / report / judge が通常の `ident.campaign_id`
   と別契約)。verifier epoch を通常 campaign identity にだけ足すと S8b の成果物は旧意味論のまま残り、
   逆に S8b manifest へ足すと凍結 manifest の pre-image が変わる。さらに selector role は **role 名を
   key にした pin** なので path 検索では漏れる (F30 型)。→ 別 T として起票するか、Q1 (a) の wave に
   含めるか。
2. **guided は witness / receipt 無しの `certified` を WAL へ書く** (`guided.py:126-141`)。
   guided WAL を「分析専用」と位置づけるか、正式な producer にするか。→ 別 T 候補。
3. **P2-2 は artifact admission の legacy overlay に存在しない** (`legacy_admission_overlay_v1.json`
   の記載は 3 campaign)。歴史 campaign の admission 上の位置づけを決める必要がある。→ 別 T 候補。

---

## 7. この裁定で変わらないこと

- CCBench (`external/ccbench`) は 1 bit も変えていない。
- 既存 WAL の bytes、`output/s1-freeze/*` / `output/s8b-freeze/*` の bytes は 1 bit も変えていない。
- [T-756] が入れた witness gate は不変 — **今後の run では witness が必須**であり、本 wave の議論は
  すべて**過去の記録の扱い**に関するものである。
- 絶対規律 1〜6。
