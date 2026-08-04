# [T-452] `effective_clock.tolerance_pct` の権威設計案 v2 — 裁定パッケージ

2026-08-04 / wave `dev-wave-t452-clock-tolerance-authority` / base = local main `a98916a`

**本 wave は実装しない。** 成果物はこの設計案と、末尾の設計択一 (U-1〜U-8) である。
方向裁定 (2026-08-04 /rulings) = 「権威は **policy 固定値の方向**で設計する。実測 smoke 分布由来は
採らない方向で起草し、最終形は設計案で確定する」。

構成: 段 2 に codex read-only の設計起草を 1 本、段 3 に敵対 2 レンズ (恒真ゲート / 整合・consumer) を
並列で当て、段 4 で親が裁定した。両レンズとも NO-GO を返し、**所見 12 件はすべて real** で
採用した。逐語は同ディレクトリの `s2-plan.md` / `s3-lensA.md` / `s3-lensB.md` / `s4-ruling.md`、
prompt は `prompts/`。

---

## 1. 何が壊れているか (実測)

`attestation_profile.effective_clock.tolerance_pct` には**権威の出所が無い**。値は較正取得 CLI の
引数として人が渡し、境界検査は `(0, 100]` だけである (`orchestrator/calibrator/cli.py:487`、
`orchestrator/calibrator/schema_v2.py:236-239`)。

- **述語** (`orchestrator/campaign/execution_guard.py:182-199`) は
  `allowed_delta = |median(expected)| * tol/100` を取り、**observed の全要素**が帯内であることを要求する。
- `tol=100` のとき帯は `[0, 2*median]` になる。**literal な恒真ではない** — median の 2 倍を超える
  標本は落ちる — が、正の標本しか schema を通らないため**実質恒真**である。
- 取得時の自己整合 gate (`orchestrator/calibrator/cli.py:381-391, 608-615`) は
  **publish される profile 自身の tolerance** で自己比較する。したがって 100 を渡せばこの gate も自明に通る。
- 手入力面は 4 段で運ばれている: `tools/pegasus/submit_certify.sh:7-42,177` →
  環境変数 `PEGASUS_EFFECTIVE_CLOCK_TOLERANCE_PCT` → `tools/pegasus/certify_calibration.sh:154-164,730`
  → CLI。
- 実行時観測側 (`orchestrator/campaign/env_attestation.py:433-440`) は
  「observed は自前の policy を持たない」ことを `tolerance_pct=100.0` という **sentinel** で表している。

登録済み較正 `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json` は
48 標本のうち 47 個が `2101.0`、1 個が `3080.935` (median から **+46.641 %**) で、
`tolerance_pct=2.0` でも `5.0` でも**自分自身の述語を通らない** (F97 / F108)。
通すには `46.65 %` 以上が要る。**policy 値の選び方でこの artifact を救済する道は無い。**

---

## 2. 権威の所在 (推奨)

新規 leaf module `orchestrator/calibrator/effective_clock_policy.py` に単一識別子を置く。

```python
EFFECTIVE_CLOCK_TOLERANCE_PCT: Final[float] = 2.0
```

env tag 別の表・setter・fallback・環境変数参照を持たせない。参照者は 4 者:
producer (`orchestrator/calibrator/cli.py:549-551`)、loader
(`orchestrator/campaign/env_attestation.py:674-692`)、issuer の独立比較 (同 `:576-592`)、
canonical consumer (`orchestrator/campaign/execution_guard.py:182-199`)。
**issuer の比較計算は独立実装のまま残す** — D155 決定 (2) の相互裏取りを壊さない。共有するのは
数値の権威だけである。

却下した配置:

- **`env_contract.REGISTRY` の env_tag 別 field** — env 追加担当者が特定環境だけ `100.0` にできる。
  同じ述語の意味が環境ごとに変わる。
- **`CalibrationRef` への field 追加** — pin 更新者が policy も同時に書き換えられ、artifact 内の値と
  二重正本になる (`orchestrator/campaign/env_contract.py:63-79`)。
- **artifact 内の `tolerance_pct` 自身を権威とする** — 検査対象が自分の受理幅を宣言する自己署名構造で、
  現在の欠陥そのもの。
- **環境変数 / shell / JSON 設定** — 投入 script・scheduler export・job script のいずれかが差し替えられる。

## 3. 固定値と根拠

**`2.0 %`。** 根拠は smoke 分布への fitting ではなく述語の意味である。D143 が正とした意味は
「`governor=performance` 下で、定格帯から外れたコアが一つも無いこと」(`docs/decisions.md:6976-6985`)。
`2.0` は周波数表示の量子化・制御誤差に有限の余白を与えつつ、turbo・別 governor・競合負荷という
「定格から外れた状態」を許容しない境界である。

値の変更は通常の設定変更として扱わない。次をすべて必要条件とする —
(1) ユーザー裁定と decisions への「述語の意味がなぜ変わるか」の記録、
(2) smoke 分布からの逆算ではない手書き反証 vector (境界内 / 境界外 ε) の提示、
(3) policy wiring test の literal 更新、
(4) `attestation_mode="required"` の全較正の新 policy での再取得、
(5) calibration path+SHA・registry・contract 世代・依存 evidence・テスト pin・既知例外を
    **一つの migration closure** として更新、
(6) 旧 artifact は履歴として parse 可能に保ち、current admission には通さない。

## 4. observed sentinel との衝突と解き方

expected と observed が同じ `EffectiveClockProfile` を共有している
(`orchestrator/calibrator/schema_v2.py:218-239`) ことが衝突の根である。schema 上限を狭めると
observed の sentinel `100.0` が schema 違反になる。

**推奨は型の分離。** `EffectiveClockProfile` は expected 専用として残し、probe は
`samples_mhz` / `method` / `governor` の 3 field だけを持つ observed 専用型を返す。
「policy を持たない」を数値ではなく**構造的事実**にする。receipt の observed 比較値は
既に tolerance を落としているため (`orchestrator/campaign/env_attestation.py:545-547`)、
receipt bytes は変わらない。

**ただし版上げが必須である (段 3 B-3、実測)。** staging の observed artifact 15 件は
`pegasus-probe-output/v1` で clock key が 4 個ある
(`output/env/pegasus/calibration/job-staging/0:867876.nqsv/attestation-pre.json`)。
3 key の新 shape を同じ version 名で出すと、同一 schema 名が二つの形を意味することになり、
`orchestrator/qualification/t126_driver.py:439-455` の `observed_profile_sha256` は
同じ schema 名のまま preimage が変わる。したがって:

- tolerance-free 出力を **`pegasus-probe-output/v2`** として発行する。
- v1 は「clock key がちょうど 4 個かつ sentinel が厳密に `100.0`」の **legacy parser** で
  内部型へ射影し、履歴 replay を保つ。
- full-profile hash にも版付き projection を置き、同一 schema 名で hash の意味を変えない。

expected schema は `100.0` を拒否するよう上限を `<100.0` へ狭める。ただし **current policy との
完全一致は schema の責務にしない** — 旧 policy artifact を履歴として parse できる余地を残し、
完全一致は producer・loader・issuer・consumer の trust boundary が担う。

## 5. 恒真化を塞ぐ機械と、それを撃つ変異

値域を狭めるだけでは publish 値を人が選べる構造が残る。層を重ね、一層の脱落を他層が検出する。
**各行の「壊す変異」は、段 3 が「無効化しても現行/提案テストが緑のままである」ことをコード上で
確認したものである。実装 wave はこれを `DW-M01` の事前登録の起点にする。**

| 層 | 置くもの | 壊す変異 | 変異を殺す検査 (v2) |
|---|---|---|---|
| policy 正本 | `effective_clock_policy.py` の単一定数 `2.0` | 各層に literal `2.0` を直書きし、policy module を参照しない (A-4) | **wiring / metamorphic**: policy を schema-valid な `3.0` に差し替えると producer・loader・issuer・consumer が一斉に追従する。値一致 golden だけにしない |
| 投入面 | `submit_certify.sh` の引数・環境変数搬送と `certify_calibration.sh` の転送を撤去 | 分割表記・別名 option / 別名 env で入力面を復活 (A-8) | parser の **`dest` 集合**を検査し、旧 flag へ `2.0` と `100.0` の双方を渡して attempt 前拒否を確認。shell は hostile な追加引数・env を実行検査で拒否 |
| CLI 検証 | 手入力 option (`cli.py:131-132`) と `(0,100]` 検証を撤去 | legacy option を再受理 | `--effective-clock-tolerance-pct` 指定が attempt 作成**前**に rc≠0 |
| expected schema | 上限を `<100.0` へ | `if tolerance == 100.0: fail` の一点判定に退行 (A-7) | `99.999…` を受理し、`100.0`・`100.0+ε`・十分大きな有限値を拒否する境界テスト |
| observed 型 | tolerance field を持たない専用型 + v2 schema | observed に field を戻す / v1 と同名で 3 key を出す (B-3) | probe が tolerance-free 型を返すこと、v1 legacy parser が 4 key + 厳密 `100.0` だけを射影すること |
| producer 注入 | `cli.py:551` は args でなく policy 定数を代入 | literal / env / 引数値を代入 | artifact の値が policy 由来であることを wiring test で固定 |
| 取得時 gate | 自己整合 gate を policy 注入後の profile に適用し publish 前に拒否 | helper を `return True` / **外れ値 index を slice で除外** / gate を publish 後へ移動 (A-2) | 外れ値位置を **parameterize** した負例 (最低 first / middle / last、推奨は全 48 index)。現行負例は index 47 固定で slice 変異を殺せない |
| loader admission | `load_verified_calibration()` で expected tolerance と policy の完全一致を検査 | equality を削除 | 負例を **schema-valid な非 policy 値 (`5.0` / `99.0`)** にする (A-1)。`100.0` は schema が手前で落とすため負例にならない |
| registry 不変条件 | required entry 全件で policy 一致と self-pass を要求し、U-2 後は例外集合を空へ | loop 内で `passes = True` に固定 (A-5) | 検査を入力可能な helper にし、**schema-valid・policy 一致・self-fail** の artifact を明示的に拒否する負例を与える。件数 assert (空 loop 殺し) と併用 |
| issuer 独立比較 | expected tolerance が policy と不一致なら fail。計算は独立のまま | artifact の値をそのまま使う / 常に pass | issuer verdict を直接検査。consumer 側の独立性テストと併走 |
| runtime guard | canonical 述語が policy 一致を検査し、delta は policy から計算 | equality を削除して expected の値を使う | golden vector に **unauthorized 非 policy 値**を置く |
| receipt shape | effective-clock の **observed を exact `{samples_mhz}`**、expected を exact `{samples_mhz, tolerance_pct}` で検証 | delta を `observed.get("tolerance_pct", policy)` から取る (A-3) | **実測**: `execution_guard.py:216-221` の `_json_value` は Mapping を任意 key で再帰許可するため、現 `validate_receipt_v2` は observed に `tolerance_pct` を足した forged receipt を通す。exact key 集合で閉じ、注入 receipt / 歴史 raw fixture の拒否テストを置く |

### 恒真になっていないことの自己点検

- policy test は production 定数から期待値を生成せず、独立の literal を持つ。
- negative control は壊れた JSON ではなく、**SHA まで再計算した well-formed artifact** を loader へ渡す。
- registry test は required entry の件数を assert し、空 loop を成功させない。
- publish test は helper 単体でなく `registered/` の非生成まで観測する。
- issuer と consumer は別々に呼び、片方を constant-pass に変異させた receipt をもう片方が拒否する。

## 6. 移行 — contract 世代の問題 (段 3 B-1、実測)

**この設計を単体で入れても較正は再登録できない。** 順序は次で固定する。

1. **[T-419] U-1 probe 実験** — F108 の観測者効果を計算ノードで確定する。
   現行 probe のままでは、policy `2.0` を注入した candidate が取得時 gate で必ず落ちる
   (実経路: `cli.py:525-551` → policy 注入 → bench → self gate `:598-610` → accepted のときだけ
   publish `:611-638`)。**`100.0` で迂回する経路を閉じること自体が本設計の目的**であるから、
   これは設計の欠陥ではなく前提条件である。
2. **probe 方式の裁定と実装** — 本設計は方式を決めない (T-419 の所有)。
3. **policy authority の実装** — 型分離・入力面撤去・各 trust boundary の policy 検査。
   現登録 artifact の tolerance は既に `2.0` なので、policy 一致の導入**だけ**では loader を新たに壊さない。
4. **[T-419] U-2 較正再取得** — 新 CLI が policy を自動注入し、self-comparison を通った artifact だけを publish。
5. **pin closure と contract 世代移行** (下記)。
6. **その後に campaign / certified 選択を再開。** 移行途中の current calibration で certified campaign を開かない。

### pin 閉包 — `FROZEN_MANIFEST` に `output/env/` が無いことは「影響なし」を意味しない

calibration の path/SHA を動かすと `contract_sha256` が動く
(`orchestrator/campaign/env_contract.py:145-160`)。**実測**: 凍結された
`output/s8b-freeze/floor_protocol.json` は `contract_sha256 = e576e9cd1369bba3…` を内包し、
同 file は `FROZEN_MANIFEST` の pin 対象である (`orchestrator/tests/test_frozen_artifacts.py:38-46`)。
したがって U-2 は次の 2 つの間に挟まれる — 旧 protocol bytes をそのままにすれば current registry と
照合する validator が拒否し、書き換えれば凍結 manifest・protocol SHA・selector journal・独立 golden が破れる。

**推奨は世代 (generation) 付き移行。** 旧 frozen protocol は**旧 contract を厳密に解決できるまま保持**し、
新 calibration は新 contract 世代・新 protocol・新 evidence に束縛する。
**旧 frozen bytes の貼り替えを pin closure に含めてはならない。**

閉包に含める要素:

- `orchestrator/campaign/env_contract.py:180-192` の path+sha256
- `orchestrator/tests/test_env_contract.py` の lookup golden / 既知例外 literal / contract SHA golden
- 自己不整合の既知例外 (`test_env_contract.py:436-463`) を空集合へ反転
- `output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json` の binding (path+sha256+contract_sha256)
  とその current-registry 結合テスト、driver の current-binding gate
- `output/s8b-freeze/floor_protocol.json` の contract 参照と `FROZEN_MANIFEST`、selector journal、
  protocol builder golden

**旧 silo evidence の binding を新 SHA へ書き換えてはならない。** その試行が新較正を使ったという
虚偽の履歴になる。旧 evidence は自己完結した歴史資料として保持し、current eligibility を外し、
新較正を使った後続 evidence を別 artifact として作る。

### fixture / golden 移行 matrix (段 3 B-4)

任意 tolerance を前提にした canonical golden vectors (`orchestrator/tests/test_execution_guard.py:360-470`)、
clamped E2E probe fixture (F109)、silo の median 再導出、独立 calibration/contract literal は、
policy 一致の導入で一斉に期待値が変わる。実装前に移行 matrix を作り、
**admission 用の検査は literal `2.0` に限定し、任意幅の数学的境界 vector は admission に露出しない
純粋 helper へ分離する。** F109 の fixture は tolerance-free 型へ移すが、**synthetic clamp である事実は
保持する** — 削除や恒真化で処理しない。

## 7. 本設計が保証しない範囲 (段 3 A-6)

本設計が固定するのは **current admission における tolerance 値**までである。
policy `2.0` かつ self-pass な JSON を合成すれば、次の経路は依然として登録できる —
git 直接追加、attempt からの複製、旧 worktree からの持ち込み、registry pin だけの更新、
CLI 以外の producer、fixture からの直接構築。**実測**: registry の canonical path 検査
(`orchestrator/tests/test_env_contract.py:339-371`) は `output/env/<key>/calibration/` 配下を
要求するだけで `registered/` も content-addressed filename も要求しない。

producer provenance の束縛 (content-addressed path の強制、publish receipt と policy source の束縛) は
**別の防壁として独立に設計する**。本設計の保証範囲に含めない。

---

## 8. ユーザー裁定へ返す設計択一

| # | 論点 | 選択肢 | 推奨 | 理由と不利材料 |
|---|---|---|---|---|
| **U-1** | policy の配置 | (a) 独立単一定数 module / (b) `env_contract.REGISTRY` の env_tag 表 | **(a)** | 変更面が 1 識別子に限定され、env 追加担当者が局所的に受理集合を広げられない。不利: contract hash への束縛は artifact SHA 経由の間接束縛になる |
| **U-2** | 固定値 | (a) `2.0` / (b) 別値を裁定 | **(a)** | 述語の意味 (定格から外れたコアが無い) から導かれる。現 artifact は値の選択では救済できない (要 46.65 % 以上) ため、救済目的での緩和は選択肢にしない |
| **U-3** | CLI 互換面 | (a) option を完全撤去 / (b) 残して policy 一致値のみ受理 | **(a)** | 権威と誤認される入力面が消える。不利: 投入 script・job script・既存テストの同時移行が要る。互換が要るなら期限付きで (b) とし、非 policy 値の拒否テストを置く |
| **U-4** | observed の表現 | (a) tolerance を持たない専用型 + schema v2 / (b) 共有型で `Optional` / (c) sentinel を明示化 | **(a)** | 「policy を持たない」が構造的事実になる。不利: probe / compare / 型注釈 / full-profile consumer の移行面が広く、v1 legacy parser の追加が要る |
| **U-5** | schema と policy の結合度 | (a) schema は構造的値域のみ、完全一致は trust boundary / (b) schema 自体が完全一致を要求 | **(a)** | 旧 artifact を履歴として parse できる。不利: loader / issuer / consumer の重複防壁が必須になる |
| **U-6** | **[T-453] との結合** | (a) T-453 を authority 完了の前提にする / (b) 同一 landing closure にする / (c) 別々に進める | **(b)** | `silo_ladder_rung1.py:1964,3407` の median 比較はどの防壁も通らない独立経路であり、放置すると同じ観測に二つの verdict が残る。(c) は同じ 2 箇所を二度変更する二重実装になる。**T-453 は別タスクの所有のため親は裁定せず推奨のみ** |
| **U-7** | **contract 世代移行の所有** | (a) 新タスクとして起票し U-2 の前提にする / (b) T-419 U-2 に含める | **(a)** | 凍結 floor protocol・selector journal・golden まで届く独立した設計課題であり、較正再取得の作業単位に混ぜると閉包が見えなくなる。**親は起票までを行い、順序の確定は裁定へ返す** |
| **U-8** | landing 単位 | (a) authority 実装を先に land し、campaign を閉じたまま U-2 と pin closure を続ける / (b) 一つの最終 commit へ集約 | **(a)** | 新 CLI を clean source として計算ノードで使える。不利: 途中状態では既知例外が残るため certified campaign を開けない。(a) を採るなら 2 commit を同じ T-419 サイクル内で連続させ、間の campaign を禁止する |

---

## 9. 成果物影響 (`DW-G05`)

| 項目 | 実装しなかった場合に certified 選択・材料レポート・試行台帳がどう変わるか |
|---|---|
| 権威の一元化 (§2) | 受理集合を CLI 操作者が実行ごとに変えられ、台帳に比較不能な tolerance の trial が混在する |
| 固定値 (§3) | 同じ観測でも accepted/rejected が変わり、材料レポートが述語の意味を説明できない |
| observed の型分離 (§4) | sentinel が expected へ漏れれば受理帯が `[0, 2*median]` へ広がり、逆に上限だけ狭めれば probe 自体が schema reject され、いずれも certified 結果を作れない |
| 恒真化防壁 (§5) | 非 policy artifact が取得時 gate と実行時 guard を通り、環境同一性を未証明のまま certified 受理され、台帳に偽の pass receipt が残る |
| contract 世代移行 (§6) | 較正再取得の瞬間に凍結 floor protocol の contract 参照が current registry から解決不能になり、既存 certified floor 選択の受理集合が実質空になる |
| T-453 の結合 (U-6) | silo ladder の `all_pass` と台帳だけが広い median 受理集合を維持し、同じ観測に canonical receipt と異なる verdict を記録する |
| provenance の射程 (§7) | tolerance は `2.0` でも expected samples を人為的に選んだ artifact を登録でき、certified 受理集合の参照元を変更できる |

## 10. この wave が触っていないもの

コード・テスト・凍結 bytes・pin・受理集合を 1 bit も変更していない。実装差分が無いため
変異 matrix は射程外である (段 3 が構成した変異は §5 に候補として凍結した)。
述語を緩める案・attestation を campaign から外す案・issuer の独立実装を canonical へ統合する案は
D143 / D155 で却下済みであり、本設計案でも再提案していない。
