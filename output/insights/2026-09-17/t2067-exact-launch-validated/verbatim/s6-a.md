## 受理集合の差分

**通常の production 入力について、旧 code が拒否した入力を新 code が受理する経路は見つからない。変更は受理集合の縮小である。** ただし、I1′の診断に関する文言は実装・plan v2 と一致していない。

以下、行参照の略記を用いる。

- `D` = `orchestrator/campaign/s8b_oracle_driver.py`
- `T` = `orchestrator/tests/test_s8b_gate_core_exact_launch_validated.py`
- `R` = 指定の `stage4-ruling.md`
- `Δ` = 指定の `s5-implementation.diff`

現物の `git diff` は、指定された production 差分と一致した。

旧 v2 枝は、token が無ければ注入された `ratified`、それも無ければ static loader の結果を使い、hash 一致で通過した（`Δ:41–54`）。新 v2 枝では token 欠落を拒否する（`D:488–492`）。exact token 有りの document/hash 選択、型拒否、後続 predicates は維持されている。

| 不変条件 | 判定 |
|---|---|
| I1′ | admission 拒否は成立。ただし「必ず M・集約継続」は無条件には成立しない。RA-1 参照 |
| I2 | 成立。core に static loader 呼出しは無い。public の `D:634` は残る |
| I3 | production の非 fallback 経路で成立。v1、二読失敗、error 翻訳、正常 v2、private validated 経路は維持 |
| I4 | 成立。public signature は `D:585–589` のまま |
| I5 | 通常の入力・副作用契約下で成立。新たな受理経路は無い |
| I6 | 成立。core signature `D:402–412` に `ratified` は無い |

**RA-1 — real / severity: should：I1′の「必ず M」は強すぎる。**

- **根拠:** `R:38` に対し、`D:486–492` は `ratified_error` を優先し、token 無しでも `freeze-ratify:` だけを積む。subclass / Reverified は `D:432–439` で型不正として即 return し、M も後続集約も無い。これは `R:47` の限定された禁止署名、`R:84` の実装指示には一致する。
- **判定材料:** node 6 が error 優先を明示的に要求している（`T:162–172`）。実装の取り違えではなく、裁定内の量化の不整合。
- **推奨:** I1′を「非 exact token は型不正で拒否。通常の v2 枝では error を優先し、error も token も無い場合に M を積んで集約継続」と限定する。M の追加で error 翻訳の既存集合を変える修正は勧めない。

adapter 枝については `D:470` が v2 判定に先行する。裁定が明記したとおり、任意に偽造した document/hash/receipt の不整合まで含む普遍的な I1′は主張できない（`R:12`）。この既存境界を、今回新設された受理拡大とは数えない。

## fail-closed の組合せ表

ここでは adapter 非発火、receipt refusal 無し、manifest 無しとする。`freeze` は**core が選択した document**であり、exact token があれば `verified.document` より token 側が優先される（`D:447–452`）。

記号：

- `M`：exact token 必須
- `E`：`freeze-ratify: <ratified_error>`
- `X`：validated freeze object の型が不正
- `H`：`freeze-not-active-generation`
- `K`：known-axes 検証
- `F/B`：floor-null / budget-null

| 選択 document | token | error 無し | error 有り |
|---|---|---|---|
| v1 | None | v1 verifier、K、F、B → 拒否 | 同左。core では E を追加しない |
| v1 | exact | v1 verifier、K、F、B → 拒否 | 同左 |
| v1 | subclass | X で即拒否 | X で即拒否 |
| v1 | Reverified | X で即拒否 | X で即拒否 |
| v2 | None | M ＋ K ＋該当する F/B → 拒否 | E ＋ K ＋該当する F/B → 拒否。M 無し |
| v2 | exact | hash 非 None なら当該枝は通過。K、F/B 等が無ければ受理 | E ＋ K ＋該当する F/B → 拒否 |
| v2 | subclass | X で即拒否 | X で即拒否 |
| v2 | Reverified | X で即拒否 | X で即拒否 |
| None | None | known record 不在、F、B → 拒否 | 同左。E 無し |
| None | exact | known record 不在、F、B → 拒否 | 同左。E 無し |
| None | subclass | X で即拒否 | X で即拒否 |
| None | Reverified | X で即拒否 | X で即拒否 |

補足：

- v2 + exact + hash None は H を積む。error 有りなら E が優先し、H は積まない（`D:486–498`）。
- `freeze=None` が読込例外の結果なら、さらに `holdout-freeze-verify:` が付く（`D:455–457`）。None document を直接与えた場合には、この読込例外理由は付かない。
- `manifest_path` 有りでは後続の manifest 判定も継続する。freeze/hash 欠落なら検証不能理由が加わる（`D:520–527`）。
- **error と exact token が同時に non-None:** token の document/hash を選んだ後、v2 なら E で拒否する。token は error を打ち消さない。v1 / None document なら E の翻訳枝に到達しないが、F/B により拒否する。
- public `gate_check(ratified_error=...)` は別であり、document/token の処理前に E で return する（`D:598–601`）。
- adapter 発火時は adapter の結果が v1/v2 枝を置き換え、K も省略する。F/B と manifest 集約は残る（`D:470–473`, `500`, `515`）。

## 負例の旧 code での挙動

**node 1・2・11 は、旧 code で実際に `allowed=True` になる構成である。** AssertionError を捕捉させるだけの診断テストではない。

| node | 旧 code の挙動 | 証拠の種類 |
|---|---|---|
| 1 | 初回例外を public が受け、再読成功。旧 core が static fake を取得し hash 一致。refusal 無し、受理 | 受理境界 |
| 2 | 初回例外後、旧 call site が注入 `ratified` を core に渡す。旧 core がそれを採用し hash 一致。受理 | 受理境界 |
| 3[both] | static fake と hash 一致。受理 | 受理境界 |
| 3[floor-only] | B により拒否。M は無い | 診断・呼出し差 |
| 3[budget-only] | F により拒否。M は無い | 診断・呼出し差 |
| 5 | 既存 exact type 検査で拒否 | 型境界の回帰 pin |
| 6[両例外] | E ＋ B で拒否 | 診断維持 |
| 7 | public の E で即拒否 | 既存分岐維持 |
| 8 | 二読失敗＋known record 不在＋F/B で拒否 | 集約維持 |
| 9 | hash None により拒否 | 既存 hash 境界の pin |
| 10 | F/B で拒否 | v1 診断維持 |
| 11 | node 1 と同じ受理。JSON は `allowed=true`、rc=0 | 受理境界＋CLI 出力 |
| 12 | signature assertion が失敗 | 構造 pin |

node 1・2 の単一理由性は、`T:28–55` の hash 一致、`T:59–62` の空 receipt refusal、`T:69` の known-axes no-op、floor/budget 両方 non-null、manifest 無しによる。旧 fallback の根拠は `Δ:41–54`、旧注入 call site は `Δ:73`。

node 11 は本物の `main` → `gate_check` を通り、`D:2034–2039` が decision を JSON と終了コードへ写す。ただし**同一プロセス内の CLI entrypoint テスト**であり、subprocess 起動の証拠ではない。

node 4 は負例一括ではない。`both` は旧新とも受理する正例、片側 null の二つは旧新とも拒否する既存 predicate の pin である。

## 変異の帰属

以下は **新規ファイルの全17 node に対する静的予測の完全集合**。番号は裁定 §7 に対応する。既存 consumer を合わせた matrix 全体の失敗集合は、未実施の probe で別途確定する必要がある。

M3 は append を `pass` にする有効な Python 変異、M8 は error 優先を維持して token 欠落条件を常真化する変異として評価した。

| 変異 | 現物の変異位置 | 赤になる全 node | semantic な帰属 |
|---|---|---|---|
| M0 | `D:484–485` の comment | ∅ | 等価対照 |
| M1 | `D:488–492` を旧 static fallback に置換 | 1、2、3[both]、3[floor-only]、3[budget-only]、11 | 1・2・3[both]・11 は拒否→受理。片側 null は診断差 |
| M2 | `D:432–433` の exact 判定を isinstance 化 | 5 | 拒否→受理 |
| M3 | `D:489–492` の M append を除去 | 1、2、3[both]、3[floor-only]、3[budget-only]、11 | M1 と同じ受理反転。片側 null は診断差 |
| M4 | signature、2 call site、欠落 token 枝 | 2、12 | 2 は拒否→受理。12 は構造差 |
| M5 | `D:493–498` の hash 拒否節を除去 | 9 | 拒否→受理 |
| M6 | `D:473` を `floor is None` のみに変更 | 3[budget-only]、4[budget-only] | ともに拒否のまま、診断差 |
| M7 | `D:486–492` で token 欠落を error より優先 | 6[RatifiedFreezeError]、6[RuntimeError] | E→M。拒否維持 |
| M8 | `D:488` を常真化し、exact token にも M | 4[both]、4[floor-only]、4[budget-only]、9 | 4[both] は受理→拒否。他は診断差 |
| M9 | `D:474` の v1 枝に M 追加 | 10 | F/B に M 追加。拒否維持 |

**RA-2 — real / severity: should：代表 node を完全集合や semantic KILL 件数として転記してはいけない。**

- **根拠:** M6 は node 4[budget-only] も赤にする。v1 verifier が実行され、三キーだけの合成 document を拒否するためである（`D:473–481`、`T:29–36`, `132–134`、`s8b_holdout_freeze.py:1005–1008,1152–1153`）。
- **根拠:** 上記 M8 は node 9 も赤にする。期待 H が M に変わる（`T:203–211`）。`R:61` の代表 node だけでは完全集合にならない。
- **推奨:** 上表を新規17 node の予測として使い、既存 consumer を含む probe の実測と照合する。失敗 node 数と受理境界を変える変異数を別々に記録する。M8 の逐語置換方法も固定する。

分類自体は、**M1〜M5・M8 が KILL 候補、M6・M7・M9 が diagnostic pin**で妥当。ただし以下を区別すべきである。

- M1/M3 の片側 null fixture は後段の F/B が拒否をマスクする。受理境界の証拠は `both` 等から取る。
- M8 の単一理由の正例は node 4[both]。片側 null と node 9 は semantic KILL の追加証拠ではない。
- M4 の node 12 単独では受理集合の変化を証明しない。node 2 が必要。
- M2 は core 直呼びだから単一理由になる。private wrapper 経由では `D:685` の別の exact 判定がマスクする。既存 Reverified node も、Reverified は非継承型なので isinstance 化を検出しない。
- M5 の証拠は None hash。`freeze_sha` は token 自身から取るため、`!=` 部分だけを消す変異は通常の型契約下では等価（`D:449,494`）。独立した二入力の照合を壊した証拠とはならない。
- M6 は M の消失に加え、誤って入った v1 verifier と後段 F が拒否を残す。受理境界の変異としてはマスクされる。

M4 の具体的な置換案は次のとおり。これは**変異仕様案であり、実装修正案ではない**。

1. `D:412` の直前に旧 `ratified: Optional["s8b_ratified_freeze.RatifiedFreeze"] = None,` を戻す。
2. `D:610` と `D:623` の core 呼出しに `ratified=ratified,` を戻す。
3. `D:488–492` を以下へ置換する。error 優先と後続 token hash 判定は維持する。

```python
elif launch_validated is None:
    if (ratified is None or freeze_sha is None
            or ratified.sha256 != freeze_sha):
        refusals.append(
            "v2-execution: launch-validate: "
            "LaunchValidatedFreeze exact type が必要"
        )
```

この形なら node 2 だけが注入候補を利用して受理へ反転し、node 1・3・11 は token も注入候補も無いため拒否を維持する。

## patch 位置

**RA-3 — refuted / severity: should（検証懸念、修正不要）：seams が対象の v2 判定を空洞化している、という懸念は退ける。**

| patch | 位置・役割 | 判定 |
|---|---|---|
| `_resolve_t080_receipt` | `T:68`。receipt の別の拒否を除去 | 対象機構の外側 |
| `s1_known_axes_freeze.verify` | `T:69`。後続の独立検査を除去 | 外側 |
| `_load_verified_freeze` | `T:70`。初回失敗→再読成功を供給 | 入力取得境界 |
| `load_ratified_freeze` | `T:71`。旧 fallback に受理可能な static 候補を供給 | 新機構の外側。旧迂回の counterfactual seam |
| `launch_validate` | `T:72`。呼ばれないことを監視 | 今回の欠落 token 判定の外側 |
| node 10 の holdout `verify` | `T:220`。v1 の既存拒否集合を分離 | v2 機構の外側 |

**同じ Mock を見ることは現物で確認できる。** public の `D:606` と core の `D:455` は、いずれも driver module の `_load_verified_freeze` を直接参照する。`T:70` がその一つの属性を置換し、`T:88` 等の二要素 `side_effect` を両呼出しで順に消費する。

型判定 `D:432`、v2 分岐 `D:473`、error/token/hash 判定 `D:486–498`、集約 `D:500–578`、allowed 算出 `D:196` は置換されていない。

- **根拠:** `T:85–96,114–151,203–226`。
- **推奨:** patch の変更は不要。ただし、この合成テストを full launch validation の実物検証まで一般化しない。正常 public 経路の実物検証は既存 `test_v2_standalone_gate_check_requires_full_floor_validation` の責務である。

## 裁定との整合

**D1872 が要求する局所修正に整合している。規律2を緩める差分、scope 外の新機構は確認しなかった。**

通常の public v2 経路は引き続き `launch_validate(candidate, root)` を実行してから core へ進む（`D:631–674`）。初回 read 失敗経路は core の再読を残すが、再読結果が v2 でも static 候補だけでは受理しなくなった。これにより、D65(5) に反していた「launch validation 無しの public v2 受理」が閉じる。

「全分岐で成立」は、**拒否される分岐にも launch validation を必ず実行する**という意味ではない。自己検証を経ずに v2 を受理しない、という admission の不変条件として成立する。

P1 の再読維持、P2 の core 注入口削除、P3 の hash 一致 fake はいずれも実装されている。caller inventory test の新設、library 経路への token 強制、advisory / non-certifying 上限の解除は行っていない。

D1984 の「二読 fallback は未裁定」という逐語の不整合も、`R:16` が既に認識している。今回の実装根拠を D1872 と持ち越し本文に置く扱いでよい。

## 総括

**production の must-fix は発見しなかった。実装は受理集合を狭め、指定の fallback を閉じている。**

残る should は二点：

- **RA-1:** I1′の「必ず M・集約継続」を error 優先・型拒否の実挙動に合わせて限定する。
- **RA-2:** 変異の失敗完全集合と semantic KILL の帰属を分離する。特に M6 の node 4[budget-only]、M8 の node 9 を落とさない。

本レビューは静的検査のみ。ファイル変更・pytest・変異実走は行っていない。親提示の正常系実測は前提として扱ったが、変異 matrix と受入全走の成功は主張しない。