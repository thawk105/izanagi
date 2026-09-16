## 総括

**案 X を推す。既存の `gflags_expected_head` / `glog_expected_head` を pin の正本として再利用し、共有 policy に URL を追加する。** FetchContent 用の列挙権威は変更せず、gflags/glog 用の小さい列挙関数から既存 cache/hydrate 実装へ渡す。

完了条件は **実 consumer 1 本の結線＋hydrate した source からの依存ビルド＋実 CCBench configure の成功証拠**とする。結線先には、既に source-root 入力と依存ビルドを持つ `p3_s4_loop_pegasus.sh` を推す。残りの job 移行は T-585 に残す。

ただし、次は親へ返す必要がある。

- D1737 と段階移行の整合は、P1 の provisional 解釈を前提とする。
- 変更前 SHA だけでは変更後 bytes の正しさを固定できない。更新後 golden の独立算出手順が必要。
- 凍結 pin の直接依存は下記で特定したが、**間接依存を含む全テストの網羅証明まではできていない**。

以下のパスはすべて指定 worktree 内。編集・commit・テスト実行はしていない。

## 1. fetch/hydrate 機構の実体と最小差分

現行 CLI は **4 命令**である。

| 命令 | 実体 | 現行対象 |
|---|---|---|
| `fetch` | `tools/pegasus/fetch_third_party.py:540–602` | FetchContent 3 source。HTTPS clone、pin checkout、検証、create-only publish |
| `hydrate` | 同 `605–679` | cache を検証し、ローカル clone で staging に配置 |
| `verify` | 同 `525–537` | cache の HEAD・clean・origin 等を検証 |
| `verify-deps` | 同 `682–694` | policy の絶対パスにある gflags/glog を検証。取得・運搬はしない |

parser は同 `697–715`、dispatch は `723–751`。`verify-deps` も現状は `728` で cache-root の指定を要求する。

列挙の制約は次のとおり。

- `orchestrator/campaign/silo_ladder_rung1.py:66`：`THIRD_PARTY_NAMES` は3依存。
- 同 `875–899`：名前・順序・キー集合を exact 検査。
- 同 `901–930`：全項目について `CCBENCH_<NAME>_{REPO,TAG}` literal と同期。
- 同 `850–866`：gflags/glog の task 内 pin と共有 `*_expected_head` の一致を検査。

したがって、**既存 list に2依存を追加する案は採らない**。CMake 同期検査を条件分岐で弱める必要もない。

最小差分案：

1. `tools/pegasus/policy.json:101–102` 付近へ `gflags_source_url` / `glog_source_url` を追加。既存 `:16,18` の40桁 pin をそのまま利用する。途中への挿入を避け、既存項目の行番号を保つ。
2. `fetch_third_party.py:67–90` 近傍に、固定2依存だけを列挙する関数を追加。出力は既存エンジンと同じ `{name, source_name, url, pin}`。URL と pin は共有 policy から読む。
3. `:697–715,723–751` に、例えば `--include-build-deps` という明示選択を `fetch/hydrate/verify` に追加。指定時だけ既存3依存に2依存を加える。`verify-deps` の意味は変更しない。
4. `_fetch` / `_hydrate` / `_verify_cache` / `_verify_source` は既存実装を再利用する。
5. 新フィールドの検査は新入口を選んだときだけ行う。既存3依存だけの呼出しに、新しい拒否条件を持ち込まない。

これは旧経路への fallback ではない。既存 consumer の受理・拒否を保ちつつ、新 consumer が調達対象を明示する入口である。汎用 dependency framework は作らない。

## 2. 案 X / 案 Y の比較

| 観点 | 案 X：共有 policy に追加 | 案 Y：別 policy を新設 |
|---|---|---|
| 触る file:line | `policy.json:101`、`fetch_third_party.py:67,697,723` | 新規 policy、`policies/registry_v1.json:3–12`、fetch の同箇所 |
| pin の所有 | `policy.json:16,18` を直接使用。新しい pin の複製なし | URL＋pin を新 file に置くと既存 pin と二重所有。URL だけ置けば記述が2 file に分散 |
| 既存テストの赤 | §5 の共有 bytes 固定2 node | 登録漏れなら `test_pegasus_policy_registry.py::test_pegasus_policy_registry_is_complete_and_tracked` |
| 新たな pin 更新 | `pegasus_policy_expected_goldens.py:5–7` | 新 policy の内容を独立に固定するテストが必要。registry は内容の意味・pin までは検証しない |
| identity への影響 | T-126 の新しい series identity に波及 | 共有 policy の identity は不変。ただし新調達内容をどこで束縛するか別途必要 |
| 正本分裂の危険 | URL を加え、既存 pin を参照すれば抑えられる | pin 複製、照合層、または consumer 移行が必要になりやすい |

registry の検査実体は `orchestrator/tests/test_pegasus_policy_registry.py:354–431`。登録集合は directory から導出されるため、**新 file と registry を正しく追加しただけで既存テストが必ず赤になるわけではない**。

**推奨理由：案 X は共有 pin を再利用でき、正本分裂を防ぐための追加照合層が不要。**

## 3. (P3) 完了の下限と最小 consumer

**CLI とテストから到達できるので、機構だけでも厳密な意味の dead code ではない。しかし、研究経路の供給問題を解消した証拠にはならない。**

現行テストは、例えば次を検証する。

- `test_pegasus_thirdparty_fetch.py:67–81`：fixture source は `tracked.txt` 等の小さい Git repo。
- 同 `787–812`：fetch/verify/hydrate の JSON 出力と配置。
- 同 `814`：絶対パス依存の独立した検証。

これらは実 gflags/glog ビルドや実 CCBench finder の成功を証明しない。

最小 consumer は **P3 S4 job**を推す。

- `tools/pegasus/p3_s4_loop_pegasus.sh:105–115`：既存の third-party source-root 入力。
- `:369–404`：現在は policy から絶対 source path と pin を読む。
- `:409–463`：両依存の HEAD・dirty 検証と build/install。
- `:465`：prefix を供給。
- `:539–549`：実 prebuild に dependency prefix と3依存 source を渡す。

変更は `:369–404` を中心に、source path を既存 `thirdparty_root/gflags` / `thirdparty_root/glog` へ切り替える。pin は共有 policy のまま。旧絶対パスへ戻る分岐は置かない。新しい env seam も不要。

argv 等を固定する既存 node は、`orchestrator/tests/test_p3_s4_loop_job_contract.py` の以下。

- `::test_job_body_static_contract`（`:518`、固定 fragment は `:318–360`）
- `::test_static_contract_orders_all_job_stages`（`:558`）
- `::test_registered_fragment_mutants_have_one_static_failure[dependency-policy-fields]`
- 同 `[gflags-build-argv]`
- 同 `[glog-configure-definitions]`
- 同 `[glog-install-timeout]`
- 同 `[prebuild-dependency-prefix]`
- `::test_commented_dependency_policy_field_is_rejected`（`:939`）

これは全 argv の単一完全一致ではなく、**重要 fragment と順序の exact 検査**である。source の出所を変える検査だけ更新し、HEAD・dirty・build option・prefix の検出力は残す。

生死証拠は次を要求する。

1. 新入口で取得・hydrate した5 source の記録。
2. hydrate した2 source から、fresh build/install directory に依存を構築。
3. fresh build directory で実 `external/ccbench` を configure。
4. registry 残骸から解決していないことと、両 library/header が今回の prefix から解決されたことをログで確認。
5. consumer がその source root を実際に使用した証拠。

性能測定や14本の一括移行は、この完了条件に含めない。

## 4. 必ず触る file の確定

上記の **案 X＋P3 S4 結線**に対する変更集合は次の7 file。

| file | 触らざるを得ない理由 |
|---|---|
| `tools/pegasus/policy.json:101` | URL を共有 pin と結び付ける調達記述を追加 |
| `tools/pegasus/fetch_third_party.py:67,697,723` | 新列挙と明示入口を既存 cache/hydrate に接続 |
| `orchestrator/tests/test_pegasus_thirdparty_fetch.py:84,226,787` | 新2依存の取得・検証・運搬と拒否変異を検証 |
| `tools/pegasus/p3_s4_loop_pegasus.sh:369–404` | 実 consumer の source を hydrate 出力へ切替 |
| `orchestrator/tests/test_p3_s4_loop_job_contract.py:318,709,939` | 変更した source 所有契約を検査し直す |
| `orchestrator/tests/pegasus_policy_expected_goldens.py:5` | 現行 policy bytes の独立 golden を更新 |
| `tools/pegasus/README.md:295–320,369–377` | 新入口と P3 S4 用 source-root の準備手順を明示 |

`gflags_source_path` の literal を含む file のうち、この案で変更するのは **policy、README、fetch テスト、P3 S4 job、P3 S4 契約テスト**。fetch 本体は `:82` の動的キー参照なので literal 検索から漏れる。

以下は変更不要。

- `silo_ladder_rung1.py`：新列挙を fetch 側に置き、既存列挙権威を維持する。
- `floor_scoping.sh` / `floor_campaign.sh` と他 job：T-585 に残す。
- `qualification/contract.py` / `identity.py`：T-126 consumer の契約を変えない。
- `test_pegasus_tools.py`：旧 locator と pin を変更しない。
- 歴史 evidence・過去の job copy：更新対象にしない。

親 brief の「28 file」は同じ抽出条件では再現できなかった。tracked literal 検索には文書・保存済み job も入り、動的キー参照は入らないため、**28という数を変更対象の根拠には使わない**。

密結合の実装・テスト・golden 更新として単一単位で扱い、並列分割しない。

## 5. 凍結 pin の閉包

**提案どおり「既存値を保って URL 2項目を追加」した場合、現行 bytes の変更だけで赤になることを静的に確認できた node は次の2つ。**

| node id | 固定箇所 |
|---|---|
| `orchestrator/tests/test_t126_pegasus_tools.py::test_shared_pegasus_policy_owns_no_t126_qualification_keys` | `:1490–1499` |
| `orchestrator/tests/test_silo_ladder_rung1_evidence.py::test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head` | `:1263–1278` |

両者は同じ `pegasus_policy_expected_goldens.py:5–7` を参照する。今回読み取った変更前 SHA は以下で、既存 golden と一致した。

```text
a8806c4a4da81f2cbadcb5cbeee54ce7c1106bd0d291c1a2725f86b8b8a8032a
```

周辺の固定も区別する。

| 固定の種類 | 根拠・扱い |
|---|---|
| 歴史 SHA | golden `:8–10` と evidence binding は不変。現行 SHA に貼り替えない |
| key 名 | T-126 test `:1482` は `t126_` 接頭辞を拒否。新 URL key はこれを避ける |
| 既存 locator | `test_pegasus_tools.py:467–502` の gflags/glog stage テスト。locator は維持 |
| pin と既存 calibration | `test_silo_ladder_rung1_driver.py::test_dependency_pins_are_policy_bound_and_match_registered_calibration`（`:1022`）。pin は維持 |
| T-126 identity | `qualification/contract.py:76` が policy を required code identity に含む。`identity.py:138–145,166–171` は記録 commit の blob と照合 |
| dataclass 由来 hash | `campaign/env_contract.py:168–177` は contract dataclass を hash 化。共有 policy bytes を直接 hash 化するものではなく、今回その field を変更しない |
| 行番号 | 共有 policy の途中へ挿入しない。読んだ範囲では policy の特定行番号を固定する赤 node は発見していない |

T-126 の新しい series identity が変わることと、既存テストの固定 hash が壊れることは別である。過去の preimage を新 policy に合わせて再発行しない。

**D200 の適用上の未解決点：**変更前 bytes の hash は、変更後 bytes の expected hash には使えない。親が変更前 bytes と確定した追加内容から期待する変更後 bytes を独立に構成し、その SHA を実装側へ渡す必要がある。実装側が編集後 file を hash して golden に転記する手順は採らない。

なお、これは静的に追跡できた閉包であり、未知の間接 pin まで含む「全 node」の断定はしない。

## 6. 取得と運搬の分界点

境界は既に明確に分離されている。

- **取得：**`fetch_third_party.py:572–583`。URL から `protocol="https"` で clone・checkout。
- **cache 検証：**`:525–537`。ネットワーク取得をしない。
- **運搬：**`:633–641`。cache を source とし、`--no-hardlinks --no-checkout`、`protocol="file"` で clone。
- **外部取得の抑止：**`:154–165`。Git global/system config を外し、lazy fetch を無効化し、protocol を限定。
- **consumer への引渡し：**`:758–760` の `.source_root`。README `:316–318` も cache-root を渡さないよう規定。

新2依存はこの同じ流れに載せる。login で新入口の `fetch`、続いて offline `hydrate`。共有 filesystem 上の hydrate 出力を既存 P3 S4 source-root 入力へ渡す。計算ノードでは依存 build/install と実 configure を行い、GitHub へ取得しに行かない。

cache は名前別 directory の既存方式を維持する。pin 更新時の自動 fetch/pull や複数 version 管理の一般化は追加しない。

## 7. 規律 2 に触れる箇所

現行の最低線は `floor_scoping.sh:206–217,241–252`。

- source の存在
- HEAD と expected pin の完全一致
- `status --porcelain --untracked-files=all` が空

新経路では既存 `_verify_source` をそのまま使う。

| 検証 | 箇所 |
|---|---|
| 実 directory・Git metadata | `fetch_third_party.py:296–343` |
| HEAD 完全一致 | `:388–392` |
| tracked/untracked dirty 拒否 | `:393–399` |
| hydrate 内 ignored artifact 拒否 | `:400–409,670–679` |
| index の隠蔽 bit 拒否 | `:410–417` |
| origin 一致 | `:418–425` |
| publish 後再検証 | `:585–598,654–667` |

新2依存には通常の cache 契約を適用する。旧 `verify-deps` の `allow_shallow=True`（`:691`）を新 cache 経路へ持ち込まない。

P3 S4 側の `:413–419,440–446` の HEAD・dirty 検査も残し、hydrate 後から使用時までの変更を検出する。

新テストの変異 matrix は、2依存それぞれについて以下を必須とする。

- URL/40桁 pin の不正、HEAD 不一致、tracked/untracked dirty。
- origin 差替え、shallow、symlink、既存 hardened metadata 拒否。
- cache にある ignored artifact が hydrate へ混入しない。
- hydrate の clone が file-only・no-hardlinks。
- 新2依存が欠けても旧3依存だけの入口は従来どおり動く。
- 新 consumer が旧絶対 source path に依存せず、欠損・不正な hydrate source を拒否する。
- 実 CCBench finder が今回構築した prefix を解決する。

既存検査を削ってテストを通す変更はしない。

## 8. 親 brief の誤り・未確認事項

1. **「現行3命令」は誤り。** `verify-deps` を含む4命令。
2. **P3 S4 の「job body に供給経路が無い」は現在のコードには当てはまらない。** `p3_s4_loop_pegasus.sh:409–465,539–549` に依存ビルド・prefix 供給がある。残る問題は機体固有 source locator への依存。
3. **ThirdParty.cmake の制約は正しい。** gflags/glog を既存 list に足すだけでは成立しない。
4. **最小 config-mode probe では不十分という指摘も正しい。** 実 CCBench は `CMakeLists.txt:5,33–34` から module finder を使い、各 `Find*.cmake:5–11` が library/header を要求する。
5. **P1 は静的読解で確定できない。** 提案は新 pin を複製しないが、T-585 完了までは旧 locator を使う consumer が残る。これを D1737 の禁止する二重経路と解するなら、段4で裁定へ返す。
6. **28 file の集計条件、未知の行番号 pin、全間接 identity 閉包は未確定。** この部分を調査済みと装って実装へ渡さない。
7. login の system package・registry 汚染・ネットワーク・job 998862 の結果は再実測していない。親の実測情報として扱う。
8. 射影外で推測した一部 path は不在だったが、必読 file はすべて読取り可能だった。不在 path を停止理由にはしていない。