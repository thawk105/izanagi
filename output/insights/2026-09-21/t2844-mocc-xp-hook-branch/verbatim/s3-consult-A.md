# 判定と範囲

**P1 の容器変更と、P2 の旧 6 走への縮小は概ね支持する。ただし「旧 14 check の all_pass が単一理由性を示す」「正規化 objdump＋D297 が `.text` bytes 比較を代替する」という読み方は反証する。** hot 2 走・独立 proof-surface key・21 key 一式を復活させる必要はない。

本回答は **未実走・静的読解**。指定資料・コード・保存済みログを読み、実装、patch 適用、コンパイル、テスト、計測は行っていない。以下の「保存実測」は親のログの内容であり、今回の再現結果ではない。

参照の `J` は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2844-mocc-xp-hook-branch`、repo 内の path は投入先 worktree 基準とする。

# 1. P1 — unordered_multiset の意味論

| 所見 | 判定・重大度 | 根拠 file:line | 放置時の帰結 |
|---|---|---|---|
| hash 衝突や bucket 順で P が偽緑になる | **不成立／must-fix 仮説を棄却** | `patches/instr-mocc-lock-coverage.patch:21,29,34`、`J/prev/s2-plan.md:28` | 指定型・既定 hash/equality では pointer ごとの多重度を比較し、P の受理集合は変わらない |
| TRACE=1 の負荷・確保挙動まで旧版と同じ | **real／should** | 同 patch `:22,32`、`J/prev/p7-candidate-ids.log:13` | 実行件数・スケジュール・メモリ消費は変わり得るため、旧実測値の転記は不正確 |
| `<unordered_set>` が供給されず候補が必ず compile error | **不成立／must-fix 仮説を棄却** | `external/ccbench/cc/mocc/transaction.cc:13`、`external/ccbench/include/trace.hh:25,33` | BASE 固定・transaction.cc だけ変更という条件では必要な宣言を得られる |
| `-Werror` 成功を前 wave の D297 pass から導く | **real／should、P9 で対処済みの計画** | `J/prev/p4-keep-line17.log:10`、`J/s1-brief.md:24` | 未確認の候補に driver・固定期待値を作り、後から作り直す可能性がある |

`std::unordered_multiset<const void*>` は pointer を逆参照せず、その値と多重度を保存する。hash 値そのものを比較する方式ではなく、衝突した別 pointer が同一要素として消えることはない。既定の pointer equality と要素の等値が整合し、前後で同じ型を使うため、D1686 が要求する「size と `rcdptr_` multiset 保存」に合う。key、op、payload、CLL 順序、lock 所有者は保証対象外である。

確保失敗などの例外挙動は旧 multiset と同一ではない。ただし、この driver は実行失敗・timeout を正常結果として verifier に渡さない（`s3_mocc_lock_coverage.py:350,358`）。例外を捕捉して P 検査だけを省略する処理も候補本文にはない。したがって、ここから今回の driver における certified 偽緑への経路は見つからない。

静的には、新規宣言を飛び越す goto、未使用変数、明らかな signedness 警告の原因は見当たらない。これは警告ゼロの実証ではない。

vector＋sort は正しさ上の改善として必要ない。採るなら pointer の全順序を保証する comparator が必要で、確保失敗もなくならない。今回の 3 箇所変更より実装・レビュー対象を増やす理由は弱い。

# 2. X/P の位置と負例の単一理由性

| 復元点 | BASE 上の位置・候補で保存する意味 |
|---|---|
| `17` | trace include 後の空行。`using namespace std;` は論理行 18 |
| `990` | pre-sort snapshot の直後、`sort(write_set_)` |
| `991` | post-sort P 検査の直後、validation の lock 取得 loop |
| `1158` | writePhase の C/R/W emit と入口 X 検査の直後 |
| `1169` | UPDATE の保持検査後、payload `memcpy` |
| `1187` | DELETE の保持検査後、`remove_value_if_present` |
| `1195` | 非 INSERT の publish 前検査後、tidword store |

根拠は `external/ccbench/cc/mocc/transaction.cc:990,991,1158,1169,1187,1195` と `patches/instr-mocc-lock-coverage.patch:12,25,44,71,84,98,113`。

| 所見 | 判定・重大度 | 根拠 file:line | 放置時の帰結 |
|---|---|---|---|
| P1 の型変更で X/P の条件・挿入位置が変わる | **不成立／must-fix 仮説を棄却** | `J/prev/p7-candidate-ids.log:9`、計装 patch `:20,53,79,93,107` | 目標 blob と一致する限り、検査条件・reason・対象操作は保存される |
| 旧 14 check の all_pass が負例の単一理由性まで保証する | **real／must-fix M1** | `orchestrator/campaign/s3_mocc_lock_coverage.py:542,558,568` | 他の integrity 異常を併発した負例も材料レポートの all_pass に入り、因果の説明が過大になる |
| lockskip-high も X だけで赤になる | **不成立／その要求を棄却** | `output/env/pegasus/calibration/s3_mocc_lock_coverage.json:14953` | 保存実測は cycle=3,754、non-serializable。これを単一理由の対照として記載すると試行台帳が誤る |

既存負例の作用位置は保存される。

- lockskip は validation の writer 取得だけを省く。
- permutation-erase は sort 後・P 検査前に一要素を落とす。
- early-unlock は入口検査後に解放し、publish 検査後に再取得する。保持 2 点では解放状態を観測し、最後の通常 unlock を壊さない。

ただし **適用可能性と単一理由性は別**である。具体的には、正常な lockskip-single の結果へ `permutation_violations=1` を加えても旧 check は落ちない。early-single も同様で、3 本の single 負例はいずれも `_other_integrity_clean` を要求していない。framing 異常などが併発しても、要求された X/P と `indeterminate` が残れば通り得る。

M1 の最小修正は、今回の候補材料で single 負例の他 integrity 異常ゼロを確認し、X 負例では P=0、P 負例では X=0 を保存・照合すること。旧 helper・旧 JSON の意味を変える必要はなく、追加実走も不要である。そこまで行わないなら、材料の主張を「所定 X/P の発火と拒否を観測」に限定し、「一つの理由で赤」は書かない。

# 3. P7 — D297 の一般化と負例対照

| 所見 | 判定・重大度 | 根拠 file:line | 放置時の帰結 |
|---|---|---|---|
| eb8dc6fe の pass を任意の C へ継承できる | **real／should、P7 の正式再実走で解消** | `tools/check_trace0_preprocess_identity.py:560,664,678` | 別 blob・環境・context を旧 report で承認した材料になる |
| BASE＋旧 patch の拒否は有効な負例対照である | **支持／追加 must-fix 不成立** | 同 checker `:547`、`J/prev/p2-d297-asis.log:3` | include 契約の検出力を示せる。ただし他の比較経路の検出力までは示さない |
| clang の rc=1 を候補不一致と読む | **real／should、P7 の記録方針を支持** | `J/prev/p6-d297-clang.log:4` | 「比較未完了」が「候補拒否」または「3 compiler 合格」へ誤変換される |

保存 GCC 11 report は、指定 blob、include 11 行、16 context、include 比較 `exact_identity`、pass を記録している。16 件は SILO_SPACE の列挙と overlay の積で、実際の mocc defines には重複がある。16 種類の独立した MOCC 構成を覆ったという説明は不可。

同じ親・通常 file の mode・差分 path・blob なら tree は一致する。しかし checker は tree だけでなく、compiler、head defines、不在 macro の確認なども入力に取る。**本物の最終 C に対する P7 の再実走は適切で、checker を緩める必要はない。**

負例対照では rc=1 だけでなく、期待する include 不一致の stderr を確認する。compiler 不在などによる rc=1 を検出成功に数えない。

D2150 の GCC 2 版受容は e9e477ca の承認であり、C の pin 承認ではない。今回の GCC 2 版＋clang 試行は材料作成として支持するが、clang 未完了の開示と将来の再承認は残る。

# 4. P2 — TRACE=0 と `.text` bytes

| 所見 | 判定・重大度 | 根拠 file:line | 放置時の帰結 |
|---|---|---|---|
| 正規化 objdump＋D297 が `.text` bytes 一致と同じ保証を持つ | **real／must-fix M2** | `orchestrator/campaign/s3_mocc_lock_coverage.py:439,451`、`J/verbatim/D1687.md:5` | `.text` bytes が違う出力も比較を通り得るのに、材料では bytes 同一と誤記できてしまう |
| 既存 `_trace0_record` は観測者効果の証拠として無価値 | **不成立／must-fix 仮説を棄却** | 同 driver `:444,466,481` | 指定 build の symbol/string 漏れと逆アセンブル差分を確認する補助証拠にはなる |
| これらの一致が trace 完全除去の十分条件 | **不成立／その主張を棄却** | `tools/check_trace0_preprocess_identity.py:5`、`J/verbatim/D780.md:5` | 完全除去・全 TU・全 toolchain の保証へ過大一般化する |

[既存比較](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2844-mocc-xp-hook-branch/orchestrator/campaign/s3_mocc_lock_coverage.py:451) は `objdump -d --no-show-raw-insn` を使い、さらに命令行・symbol 行の先頭アドレスを除去する。比較対象は raw bytes ではない。命令の複数 encoding が同じ逆アセンブル表記になる場合、bytes の差を区別できない。D297 も生成 binary の encoding を比較しないため、この不足を補わない。

これは **C が実際に異なる bytes を生成したという指摘ではない**。brief の代替可能性の説明が成立しないという指摘である。旧 JSON も `text_identical=true` を記録する一方、binary 全体の SHA は異なっている（同 JSON `:14905`）。T-2294 の `.text` bytes 一致は、insight §2.1 の別の login 実測に支えられていた。

M2 の修正は、候補 mode の補助 witness として既に build する BASE/C binary から `.text` を抽出し、非空・size・直接一致・digest を新 JSON に記録することを推奨する。[D1687](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2844-mocc-xp-hook-branch/verbatim/D1687.md:3) の補助証拠を保持する修正であり、追加 benchmark や21 key 一式は不要である。

同時に、plan の論理行列比較は残す。等長にする対象は build dir だけでなく source path も含む。等長でも path の文字列自体は同じにならず、binary 全体・`.rodata` 全体の同一性までは主張しない。

# 5. certification gate と proof-surface key の不採用

| 所見 | 判定・重大度 | 根拠 file:line | 放置時の帰結 |
|---|---|---|---|
| stock の certified から gate 真を導く推論は誤り | **不成立／must-fix 仮説を棄却** | `orchestrator/verifier/model.py:450,466,518` | 実 C の source root を渡す限り推論は正しく、独立した真偽 key は冗長 |
| gate 真だけで certified・pin 採用可能とする | **不成立／現 brief・plan にその十分条件の断定は認めない** | `J/prev/s2-plan.md:11`、`J/s1-brief.md:26` | 現行の限定を維持すれば、診断結果が探索用承認へ昇格することはない |

`certified ⇒ Integrity.clean() ⇒ certification_gate_satisfied()` はコード上成立する。したがって、**候補 stock の実走で certified を要求する既存 key があれば、「C の gate 真」を確認する別 key は不要**である。

ただし、成立するのは verifier に渡した snapshot についてである。driver は各 binary を build した source root を `_variant_run` → `_verify` へ渡す必要がある（`s3_mocc_lock_coverage.py:387,417`）。別の計装済み tree を渡せば C についての結論にならない。plan の source-routing test は残す。

この推論から BASE の gate 偽、I absent、hot の実発火、全実行の正しさは導けない。BASE/C の静的 proof-surface 対照は可搬 test に残せばよく、compute key に重ねる必要はない。

# 6. 入力由来 check と候補の束縛

| 所見 | 判定・重大度 | 根拠 file:line | 放置時の帰結 |
|---|---|---|---|
| 旧 14 check が定数 True で恒真化されている | **不成立／must-fix 仮説を棄却** | `orchestrator/campaign/s3_mocc_lock_coverage.py:493`、`orchestrator/tests/test_mocc_proof_surface.py:798` | 実測値から導出され、各 key の入力破壊対照も存在する |
| 単一親・1 path だけで目標 blob を保証できる | **real／should S1** | `J/s1-brief.md:16,17,20`、`J/prev/s2-plan.md:95` | transaction.cc の別内容も構造 check を通る。D297 合格も TRACE=1 の内容一致を保証しない |
| 旧 JSON に全 check 入力 field が保存されている | **real／should S2** | `J/s1-brief.md:39`、driver `:424,489,722` | 保存 JSON だけから全 check を再導出できるという説明が誤る |

親列を厳密に `[BASE]` と比較すれば、孫 commit・複数親を拒否する。raw diff を通常 file・mode 不変・transaction.cc の変更 1 件と比較すれば、第二 path や mode 変更を拒否する。これらには歯があるが、内容の仕様までは証明しない。

S1 は P5 の削除を求める所見ではない。**P2 の「追加は親と path だけ」を、P5 の内容束縛まで削る指示にしないこと**が修正要求である。必要な関係は以下で足りる。

1. 親が BASE＋候補 patch の blob を目標 `e393efbf…` と照合する。
2. driver が実 C の blob と可搬 patch の再構成結果を照合する。
3. 新 consumer が、実測値から独立に固定した C/tree/blob と再構成結果を照合する。

専用 check key にするか、実走前の拒否条件にするかは実装判断でよい。目標 blob と異なる候補に D297 を走らせること自体は正しいが、**その pass を目標内容への適合の代わりにはできない**。不一致なら差分を明示して再レビューする。

S2 の具体例は `_other_integrity_clean` である。run 中には存在するが `_public_run_record` が除去する。touch set の生値も旧 JSON に保存されない。条件表は「driver 内の実測入力として存在し、公開 JSON にはその一部と判定を保存」に訂正する。M1 を閉じる候補側の単一理由性の結果は公開 field に残す。

# 7. hot 2 走と同サイズ P 対照

| 所見 | 判定・重大度 | 根拠 file:line | 放置時の帰結 |
|---|---|---|---|
| hot 2 走を省くと今回の候補が偽 certified になる具体的経路がある | **不成立／must-fix 仮説を棄却** | `external/ccbench/cc/mocc/transaction.cc:459,986,1115`、`J/verbatim/D1686.md:3` | 目標内容の束縛がある限り、共通検査を hot だけ無効化する変更はない |
| 旧 6 走で hot 経路も C 上で再立証したと言える | **不成立／その主張を棄却** | `orchestrator/campaign/s3_mocc_lock_coverage.py:52`、`J/prev/s2-plan.md:107` | workload が hot 到達を固定しておらず、材料の経路被覆が過大になる |
| perm-erase が pointer 多重度比較の動的な歯を立証する | **real／should S3** | 計装 patch `:29,31`、`orchestrator/verifier/parse.py:101` | size 不一致では pointer 比較を実行せず、その実発火を試行台帳に記録できない |

hot 正負例の不採用を支持する。D1686 が指定する負例は既存 3 本であり、hot-update-unlock の命題を今回すべて再取得する必要はない。C の検査は hot/cold が合流した validation/writePhase に残る。ただし、hot の独立実証や既知の owner-ID 不在問題を閉じたとは書かない。

P については、同サイズの `[a,b]→[a,c]` と、同じ distinct pointer 集合を保つ `[a,a,b]→[a,b,b]` がどちらも非等値になることを、型・挿入対象・比較条件の対照として残す。後者は unordered_set 化を明確に区別する。

今回の最小変換・標準容器の意味論・構造検査を合わせれば、追加の compute 負例を必須にするほどの穴は見つからない。新 runtime を増やさず、plan の構造対照を残し、**動的証拠は size 違反まで**と明記するのが妥当である。

# 8. P9 — 生死確認の最小経路

| 所見 | 判定・重大度 | 根拠 file:line | 放置時の帰結 |
|---|---|---|---|
| D297 用の include 除去前処理で TRACE=1 build を代用できる | **不成立／must-fix 仮説を棄却** | `orchestrator/tests/test_mocc_proof_surface.py:117,123`、driver `:257,314` | 型・header・実 CMake flags の問題を見逃す |
| 生死確認を driver 完成後まで遅らせる | **real／should、P9 を支持** | `J/s1-brief.md:24,30`、`J/prev/s2-plan.md:394` | 候補変更により C/OID/blob・consumer・report をまとめて作り直す |

単一 TU compile は、実 CMake configure で依存 header・生成物・compile command が揃っていれば可能である。`transaction.cc` を裸の `g++ -c` に渡し、flags を手で推測する方法は同じ確認にならない。既存 driver は gflags/glog の install と masstree 等の source を configure に渡している（`s3_mocc_lock_coverage.py:224,257`）。

最小の前倒し確認は、実 compile command による C の transaction.cc の TRACE=1 object compile。P9 の完了確認としては TRACE=1/0 の `ycsb_mocc.exe` build まで行う方が明確である。T-2294 insight §2.1 の保存値は各 8〜10 秒であり、依存物が揃うなら単一 TU 専用経路を新設する利点は小さい。

login での build は親の通常の `tools/run_tests.py` 経路に任せる。今回は依存 cache の現存・利用可能性を確認しておらず、「いま login で通せる」とは断定しない。benchmark は compute 本走に残す。

# 9. plan §8 の変異案の修正

| 変更要求 | 判定・重大度 | 根拠 file:line | 放置時の帰結 |
|---|---|---|---|
| hot reason 変異を削除し、21 key の固定期待値を確定集合へ更新 | **real／should S4** | `J/prev/s2-plan.md:232,374,412`、`J/s1-brief.md:17` | 存在しない分岐・key を対象にした変異台帳になる |
| 親/path check の恒真化と実 C 以外への source routing を直接壊す対照を残す | **real／should S4** | `J/prev/s2-plan.md:95,99,371`、driver `:387` | JSON の識別子だけ正しい別 source の実走を、候補 C の材料と誤認できる |
| M1 の他 integrity 異常の無視を破壊対照に含める | **real／should S4** | driver `:542,568` | 単一理由性の確認を追加しても恒真化を検出できない |
| P 比較を「恒真化して違反を抑止」という記述を具体化する | **real／nit N1** | `J/prev/s2-plan.md:361`、計装 patch `:34` | `!=` 条件の恒真化は逆に違反を増やし、変異の目的と期待結果が食い違う |

P の抑止変異は、`if (post != pre)` を `if (false)` にする、または post snapshot に pre snapshot を流用する、と明記する。比較式・型・挿入対象の意味検査を主 killer にし、patch hash 不一致だけを「歯」の証拠に数えない。

X は入口だけでなく UPDATE・DELETE・publish の各条件抑止も構造検査へ当てる。DELETE の runtime 未被覆は既知であり、ここを静的検査の台帳として区別する。`.text` bytes witness を残す場合はその恒真化対照を残し、省く場合は存在しない key の変異を登録しない。

旧 test を保持する実装上の注意として、`test_mocc_proof_surface.py:670` は `scratch / "trace0-base"` 等の出現回数を 1 回に固定している。候補経路をコピーして同じ式を増やすと、動作が正しくても旧 test が赤になる。旧 test の書換えではなく候補側の構成で避ける。

## 総括

- **must-fix M1:** 旧 14 check の all_pass を単一理由性と同一視しない。候補 single 負例の他異常ゼロを確認・保存するか、材料の主張を狭める。
- **must-fix M2:** 正規化 objdump＋D297 は `.text` bytes 比較の代替ではない。D1687 の補助 witness を候補 JSON に残し、完全除去の十分条件とは書かない。
- **should S1:** P2 の縮小後も、目標 blob・可搬 patch・実 C の内容束縛を P5 と整合させて残す。
- **should S2:** 「旧 JSON に全入力 field が存在」は訂正し、候補の単一理由性の確認結果は公開 field に保存する。
- **should S3:** 同サイズ pointer 置換・多重度変更の構造対照を残し、perm-erase の動的証拠と区別する。
- **should S4:** 変異案から hot 専用項目・21 key 前提を除き、候補束縛・source routing・単一理由性の破壊対照へ合わせる。
- **nit N1:** P 比較の「恒真化」の対象を具体的な式・代入として書く。

| 裁定 | 判定 |
|---|---|
| P1 | **支持**。目標 bytes の最小変更は意味論上妥当。build 成功は未確認 |
| P2 | **部分支持・部分反証**。旧 6 走、hot 省略、proof-surface key 省略、21 key 一括不採用は支持。M1/M2 は修正が必要 |
| P3 | **支持**。BASE の単一子、新規 local branch |
| P4 | **支持**。最終 C を保存対象とし、message amend 後は B・report・consumer の OID も同期する |
| P5 | **支持**。C object 不在でも可搬に検査し、実 C との関係は実測と独立期待値で束縛する |
| P6 | **支持**。I absent を残し、X/P gate の成立から I 被覆を導かない |
| P7 | **支持**。最終 C の正式再実走、期待理由付き負例、clang 比較未完了の開示で材料を作る |
| P8 | **方針支持**。45 件の個別分類の正しさは本レンズでは認定しない |
| P9 | **支持**。実依存・実 flags による build を driver 実装前に置く |

修正要求は、**単一理由性、TRACE=0 の保証名と補助 bytes 証拠、候補内容の束縛、縮小後の変異案**に限る。hot の追加本走、I 実装、verifier や D297 の変更、21 key 一式の復活は要求しない。