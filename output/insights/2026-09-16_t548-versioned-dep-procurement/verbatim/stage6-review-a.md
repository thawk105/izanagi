## 総括

**must-fix 1 件：裁定 R5 の「新 2 依存の使用直前に `_verify_source` 相当を適用する」が未実装です。** 正常 hydrate 後に source を変更しても、HEAD と porcelain だけでは見破れない入力が build に届きます。

現行 HEAD `99c9b9222` を静的に確認しました。編集・commit・テスト実行はしていません。

- 15 本で、既存の HEAD 完全一致・dirty 拒否・source 不在拒否を削った形跡はありません。
- P-1 以外に、**生存する検査が代替なく消えた**と断定できる例は見つかりませんでした。
- 凍結・歴史値の改竄は成立しませんでした。
- 変異登録は **M2・M7 が成立せず、M1・M3 も登録どおりの単一理由性を一律には認められません**。

以下、現物の行番号は worktree 相対です。「旧」は提供 diff 内の変更前行番号です。

## 1. 規律 2 の弱体化

15 本を個別に照合した結果です。「維持」は両依存について HEAD 完全一致、`--untracked-files=all` を含む dirty 拒否、不在拒否が変更前と同じ形で残ることを指します。

| 根拠：`tools/pegasus/` 配下 | 照合結果 | 重大度・成立判定 | 成果物への影響 |
|---|---|---|---|
| `a5_second_boot_backoff_sweep.sh:534` | 維持。両依存を同じループで検査 | nit・不成立 | この変更による検査の受理集合拡大なし |
| `b10_backoff_grid.sh:533` | 維持。同上 | nit・不成立 | 同上 |
| `certify_calibration.sh:443`, `:507` | 維持。Git の失敗 rc も検査 | nit・不成立 | 同上 |
| `floor_campaign.sh:1001`, `:1071` | 維持。Git の失敗 rc も検査 | nit・不成立 | 同上 |
| `floor_scoping.sh:205`, `:240` | 維持 | nit・不成立 | 同上 |
| `mocc_trace_pilot.sh:1531`, `:1579` | 維持 | nit・不成立 | 同上 |
| `oracle_n_pilot.sh:221`, `:272` | 維持 | nit・不成立 | 同上 |
| `p3_s4_loop_pegasus.sh:409`, `:436` | 維持 | nit・不成立 | 同上 |
| `paper_story_a1_paired.sh:1230`, `:1254` | 維持。絶対 path・pin 形式検査も残る | nit・不成立 | 同上 |
| `silo_ladder_rung1.sh:466` | 維持。不在は `git -C` の失敗と `set -e` (`:10`) で停止 | nit・不成立 | 同上 |
| `t126_qualification.sh:567` | 維持。directory・HEAD・porcelain の結合条件 | nit・不成立 | 同上 |
| `t141_region_profile.sh:692`, `:727` | 維持。共通検査を両依存に適用 | nit・不成立 | 同上 |
| `probes/t1683_rr5_cost_probe.pbs:89`, `:117` | 維持 | nit・不成立 | 同上 |
| `probes/t2187_adaptive_const_probe.pbs:450`, `:464`, `:479` | 維持 | nit・不成立 | 同上 |
| `probes/t2228_driver_gate_liveness_probe.pbs:166`, `:183`, `:198` | 維持 | nit・不成立 | 同上 |

ただし、これは「変更前の検査を消していない」という結論です。裁定で追加を要求された引渡し境界の検査は、§5 のとおり欠けています。

## 2. テストの骨抜き

| 対象・根拠 | 判定 | 重大度・成立判定 | 成果物への影響 |
|---|---|---|---|
| `test_t126_pegasus_tools.py:3296`, `:3302`, `:4591` | marker は新しい exact path の `rev-parse HEAD` を監視。診断文も改行込みの完全一致を維持 | nit・不成立 | reservation の受理集合・依存検査到達判定の緩和なし |
| `test_silo_ladder_rung1_evidence.py:1271`, `:1281`, `:1288` | path、現行 SHA、歴史 SHA、歴史≠現行を検査 | nit・不成立 | 凍結 binding の参照を曖昧にする変更なし |
| `test_ccbench_spawn_sites.py:90`, `:917`, `:2716` | 起動箇所 2→1、sink 行 127→118。現物 `b4_binary_record.py:79`, `:118` と一致。entry と exact 比較を維持 | nit・不成立 | 起動台帳の対象脱落なし |
| `test_mocc_trace_job_contract.py:238`, `:247`, `:248`, `:252`, `:263` | 18→16、添字 12→10・17→15。compiler mapping、policy SHA、duplicate 拒否を維持 | nit・不成立 | parser の材料値検査の緩和なし |
| `test_paper_story_a1_job_contract.py:1912` | 曖昧な `gflags-source` 検査から、両依存の具体的 configure path 検査へ移行 | nit・不成立 | source 参照検査の緩和なし |
| `test_b4_binary_record.py:208` | hydrate の先行、引数、7 呼出し、両 source path、prefix を検査 | nit・不成立 | 廃止命令以外の build 引渡し検査の脱落なし |

なお、新規の `test_build_dependency_policy_rejects_invalid_url_and_pin` は、`test_pegasus_thirdparty_fetch.py:893` で診断文を検査しています。**これが赤になることだけでは、M2 が受理集合を守っている証拠になりません。** 詳細は §6。

## 3. 乗り物ごと消えた検査 (P-1 以外)

削除された関数・case・assert 行を、置換を含めて列挙します。表内の test path は `orchestrator/tests/` 配下です。

| 削除箇所（旧行） | 消えた検査／現在の扱い | 分類 |
|---|---|---|
| `test_pegasus_thirdparty_fetch.py:749`、assert `:769`, `:770` | `test_verify_deps_allows_only_shallow_metadata_exception`。dangerous-config、commondir、sparse、assume-unchanged の4 case | **生き残る metadata 拒否＋廃止された shallow 例外の組合せ** |
| 同 `:814`、assert `:823`, `:825`, `:831` | `test_verify_deps_is_separate_and_accepts_existing_shallow_dependency`。成功 rc、JSON 全体、cache 非作成 | 消えた命令の検査 |
| 同 `:834`、assert `:843`～`:846`, `:850`, `:851` | cache root 必須、stderr、環境変数による指定 | **生き残る挙動。既知 P-1** |
| 同 `:173` | records の exact name list が3本→5本 | 生き残る列挙検査を移設。現行 `:176` |
| `test_b4_binary_record.py:226` | `verify-deps` × timeout False/True の2 case | 消えた呼出しの検査。hydrate の同じ診断検査は現行 `:225`～`:243` に残る |
| 同 `:208` | 先頭 `verify-deps` 要求 | 消えた命令の検査 |
| 同 `:210`, `:211` | 末尾 hydrate とその argv | 生き残る挙動を先頭呼出しへ移設。現行 `:208`, `:210` |
| 同 `:212` | 呼出し数8 | 廃止呼出し分を除き7へ。現行 `:211` |
| 同 `:213`, `:214` | gflags/glog の source path | 新しい exact path へ移設。現行 `:212`, `:213` |
| `test_hooks.py:3028` | sanctioned spelling の `verify-deps`。利用ループは現行 `:4462`, `:4487` | 廃止命令の spelling case |
| `test_mocc_trace_job_contract.py:233` | 関数名の `18` | 許可済みの改名 |
| 同 `:238`, `:247`, `:248`, `:252` | shell 本数、出力本数、compiler mapping、policy SHA | 生き残る検査を16値の並びへ移設 |
| `test_paper_story_a1_job_contract.py:1913` | configure と旧 source 名の部分一致 | 生き残る検査を両依存の具体的 path へ移設 |
| `test_pegasus_tools.py:469`, `:503` | 旧 locator の singleton | 廃止 locator の検査。新 URL の singleton へ移設 |

削除行が `assert` 自体でなく、その入力であるものも確認しました。

- `test_backoff_extended_sweep.py` 旧 `:1802`：旧 locator 2 key を presence 検査対象から除去。
- `test_p3_s4_loop_job_contract.py` 旧 `:319`, `:709`：policy fragment とその変異を pin key へ移設。case は残存。
- 同旧 `:941`：コメント化攻撃を旧 locator から `gflags_expected_head` へ移設。
- `test_pegasus_tools.py` 旧 `:393`：perf 配列の開始添字を11→9へ移設。
- `test_t126_pegasus_tools.py` 旧 `:4588`：完全一致診断文の path を新 staging へ移設。

**追加 P-2 候補：metadata 4 case の削除**

- **根拠:** 上表の旧 `:749` と、現行 `test_pegasus_thirdparty_fetch.py:566`, `:642`, `:684`。
- **重大度:** nit。
- **成立 / 不成立:** **検査対象が生存する点は成立。ただし代替なく検出力が消えたという攻撃は不成立。**
- **成果物への影響:** shared verifier の dangerous config・commondir・sparse・index bit 拒否は別テストに残り、追加の受理集合拡大は示せない。

旧4 case は shallow を併置していました。新経路では shallow 自体が拒否対象なので、そのまま移すと metadata 検査をマスクします。P-1 と同じ「単純な削除漏れ」とは判定しません。

## 4. 凍結と歴史の改竄

**歴史・現行 pin の移設に対する攻撃は不成立です。**

- **根拠:** `pegasus_policy_expected_goldens.py:5`, `:8`、`test_silo_ladder_rung1_evidence.py:83`, `:86`, `:1274`, `:1281`, `:1288`。
- **重大度:** nit。
- **成立 / 不成立:** 不成立。
- **成果物への影響:** 過去 evidence の参照値は維持され、現行 policy / job の無断変更も引き続き拒否される。

現物の SHA256 は、裁定・追補5の指定値と一致しました。

| 対象 | 現物 SHA256 |
|---|---|
| `tools/pegasus/policy.json` | `3a3c7d607de77e23368f9ce382b41e6e524de3ee1e2809e7c6d890ada95a6c90` |
| `tools/pegasus/silo_ladder_rung1.sh` | `117b3bb4a4789b00b2b2e8335ee78a6f329125e26aa42c6002283fd0ed894f0e` |

`EXPECTED_HISTORICAL_PEGASUS_POLICY_SHA256` は `b1c42e49…` のままです。`pbs_job` は現行 bytes の SHA を定数と完全一致させ、歴史 binding の完全一致と現行との不一致も検査するため、移設で byte 変更の検知を失っていません。

提供差分および `d97c423bd..0165027e0` の確認で、**`output/` 配下の差分は0件**でした。

## 5. 受理集合の意図しない拡大

**A-1：hydrate 後の引渡し境界に、要求された強い検証がない。**

- **根拠:** `tools/pegasus/p3_s4_loop_pegasus.sh:409`～`:424`、`certify_calibration.sh:443`～`:466`。対照は `fetch_third_party.py:385`, `:426`～`:441`。Python 側も `silo_ladder_rung1.py:2268`～`:2282`、`s3_mocc_lock_coverage.py:169`～`:187` は HEAD・status に留まる。
- **重大度:** **must-fix**。
- **成立 / 不成立:** **成立（静的経路として）**。
- **成果物への影響:** pin と clean の記録を保ったまま変更済み依存を build でき、試行台帳の source 記録と実際の材料が乖離する。その材料による測定値が downstream に渡り得る。

具体的な入力は、正常 hydrate 後に gflags の tracked source を `assume-unchanged` にして変更した tree です。

1. hydrate の検査は既に終了している。
2. HEAD は pin のまま。
3. porcelain に変更が出なければ、job の拒否条件は成立しない。
4. `cmake -S "$GFLAGS_SOURCE_PATH"` は変更済み working tree を読む。
5. `_verify_source` なら `ls-files -v` の小文字 tag を `:430` で拒否するが、job にその検査がない。

これは新しい一般化要求ではなく、裁定 R5・R9 が明示した調達経路内の未実装です。是正は、この引渡し境界へ既定の検証を適用し、正常 hydrate **後**の注入で確認する範囲に限れます。

**新列挙・cache 呼出し自体の緩和は不成立。**

- **根拠:** `fetch_third_party.py:81`～`:87` と `silo_ladder_rung1.py:887`～`:897`。cache 呼出しは `fetch_third_party.py:546`, `:564`, `:577`, `:594`, `:603`。
- **重大度:** nit。
- **成立 / 不成立:** 不成立。
- **成果物への影響:** URL の GitHub HTTPS 前置・`.git` 終端、小文字40桁 pin の受理集合は同じ。新2依存に shallow 許可や URL 検査省略は入っていない。

hydrate 側の expected URL は cache の絶対 path (`:641`, `:668`, `:676`, `:691`) です。これは local clone の origin に対応しており、`None` への緩和ではありません。

## 6. 変異 M1〜M7 の単一理由性

ここでの「成立」は、**登録への攻撃が成立するか**を表します。変異実行・KILLED の実証はしていません。

| 変異 | 現物での検算 | 重大度・成立判定 | 成果物への影響 |
|---|---|---|---|
| **M1** `.git` 要求除去 | 対象は `fetch_third_party.py:85`。前段の3依存検査は新URLを見ない。しかし現行テスト `test_pegasus_thirdparty_fetch.py:889`～`:891` は policy URL だけを変更して `verify` するため、緩和後も `fetch_third_party.py:440` が origin 不一致で拒否する | **nit・成立**。現在の入力では「後段にも拒否層がない」は誤り | 成功JSONの受理拡大をこの入力で示せず、赤は policy拒否→source拒否の差でも生じる |
| **M2** `fullmatch`→`search` | `fetch_third_party.py:86` の直後に `:102` の `_dependency_pins()`。`silo_ladder_rung1.py:859` が nested pin の形式、`:862`～`:863` が上位pinとの一致を検査。不正上位pinだけなら一致検査で拒否、両方を壊しても形式検査で拒否 | **nit・成立**。単一理由性なし | 不正pinの受理集合は拡大しない。現行テスト `:893` の赤を受理境界の検出力として数えると過大評価になる |
| **M3** `allow_shallow=True` | 呼出し箇所が未特定。`_verify_cache` の `:546` だけなら `verify` 経路を分離可能。一方 `_fetch` の `:564` と `:577` は同じ既存 source を二度検査し、片方だけ緩めてももう片方が拒否。hydrate は `:629` に加えて `:658` でも cache を再検査 | **nit・成立（登録の曖昧さ）**。全候補に単一理由性があるとは言えない | 呼出し位置によって受理集合が変わる場合と不変の場合があり、一律の実効変異数は確定できない |
| **M4** gflags の列挙除去 | `fetch_third_party.py:729` で合流した列挙を落とすなら、検証もその列挙に従い gflags を見なくなる。`test_pegasus_thirdparty_fetch.py:744`～`:768` の exact JSON が欠落を検出する | **nit・不成立**。main の列挙を対象にする限り有効 | 変異では取得・hydrate report の sources が4本になるため、値の差を直接検出できる |
| **M5** staging→`$HOME` 固定path | `test_p3_s4_loop_job_contract.py:319` の exact fragment、`test_pegasus_tools.py:485` 以降の assignment 検査で検出可能。実job経由なら `p3_s4_loop_pegasus.sh:409` の不在拒否が別理由になるが、登録は静的契約を指定している | **nit・不成立**。静的契約としての帰属は可能 | 誤った source 参照を直接検出できる |
| **M6** 現行goldenを旧値へ | `test_t126_pegasus_tools.py:1495` と `test_silo_ladder_rung1_evidence.py:1274` が現行bytesと定数を直接比較する。別のpolicy検査が先に同じ差を消す構造ではない | **nit・不成立** | 現行policyの受理が正しく赤に変わる。二つの検査の重複は、それ自体でマスクではない |
| **M7** 使用直前検証除去 | §5 A-1 のとおり、裁定 R5 の強い使用直前検証が存在しない。hydrate 内 `fetch_third_party.py:687` を対象にしても、正常hydrate後の入力を検査する境界にはならない | **must-fix・成立** | 未検証材料を拒否する受理境界が欠落したまま、M7達成を主張できてしまう |

M1 は新列挙関数を直接検査する入力、M3 は `_verify_cache` の具体的呼出しと `verify` 経路へ限定すれば再照準できます。M2 は現状の受理集合について独立した gate ではありません。M7 は登録修正だけでは閉じず、実装が必要です。

## 7. 攻めたが成立しなかったもの

- **隣接する検査行の巻き添え削除**
  - 根拠：§1 の15本。
  - 重大度：nit。**不成立**。
  - 成果物への影響：既存の不在・HEAD不一致・通常dirtyに対する受理集合の拡大は確認できない。

- **T-126 の exact 診断を部分一致へ緩和**
  - 根拠：`test_t126_pegasus_tools.py:4591`。
  - 重大度：nit。**不成立**。
  - 成果物への影響：新pathの誤りを見逃す形には変わっていない。

- **凍結 pbs_job の歴史化で現行bytesの検査が消失**
  - 根拠：`test_silo_ladder_rung1_evidence.py:1281`, `:1288`, `:1289`。
  - 重大度：nit。**不成立**。
  - 成果物への影響：歴史・現行それぞれの参照固定を維持している。

- **新2依存だけ shallow・origin 検査を省略**
  - 根拠：`fetch_third_party.py:380`, `:546`, `:637`, `:687`。
  - 重大度：nit。**不成立**。
  - 成果物への影響：cache/hydrate 自体で弱い source を追加受理する変更はない。問題はその後の使用境界にある。