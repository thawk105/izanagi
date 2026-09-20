## レンズ A

指定された必読資料は読取済み。以下、`driver` は `orchestrator/campaign/paper_story_a1_paired.py`、`paired test` は `orchestrator/tests/test_paper_story_a1_paired.py`、`job test` は `orchestrator/tests/test_paper_story_a1_job_contract.py` を指す。静的読解のみで、pytest・書込み・投入は行っていない。

**must-fix A1 — 認可の対象 attempt は限定されるが、解除する先行証拠が限定されていない。**

- **根拠:** plan §3 は driver 2901〜2919 の両拒否を、走査全体で共通の `authorized` により解除する。先行候補は 2720〜2728 で集められ、`attempt-0001` に限定されない。
- **放置時の影響:** 一致 record を持つ attempt-0002 は、同 study の attempt-0003 が既に bench に達していても受理される。
- **是正:** 完全性検査の後、解除を「認可された current attempt」と「当該候補が同じ base の attempt-0001」の組合せに限定する。別候補に対する既存拒否は残す。最小案は定数側に解除対象 `attempt-0001` を固定することであり、record に新 field を追加することまでは必須ではない。record に持たせるなら、その field も定数との exact 照合対象にする。

現在の P1 は**投入先 identity の限定**としては有効だが、今回要求された**先行状態の限定**には足りない。正常な attempt-0001 と、正常な同 study の attempt-0003 の bench 証拠を併置する負例を追加する。

なお、**別 study の正常な先行証拠は現行 gate でも拒否理由にならない**。2806〜2807、2902〜2904 は対象 study の証拠だけを数える。この場合を「認可で新たに解除された」と扱ってはいけない。別 study の unsafe／corrupt 証拠は現行でも拒否され、変更後も拒否する。

**正しさ境界の確認 — canonical path、study の二重照合、I2。**

- submit の 3409 は `_validate_attempt_root` を呼ぶ。同 helper は 2469〜2485 で canonical absolute、base 直下、既存 root の実 directory／非 symlink を要求する。canonical 化して受理する関数ではなく、非 canonical な `Path` を拒否する関数である。
- materialize の 8696 は receipt の文字列を `Path` にするだけ。`_revalidate_attempt_root` の呼出しは **8714** であり、8709 ではない。同 helper（2501〜2513）は inode binding と `_attempt_root_identity`（2489〜2498）による実 directory／canonical の再検査を行うが、**policy base 直下は保証しない**。plan §4 が追加する `_validate_attempt_root(attempt, base)` は必要であり、これで認可照合時の条件が揃う。
- record の study と caller の policy study の一致、および定数 tuple の study の一致は両方必要。前者だけでは caller／record をともに別 study にした入力を止められず、後者だけでは sized record を別 study の呼出しに流用できる。
- plan の指定どおり末尾の拒否述語だけを変更すれば、一致 record があっても intent 検査 2688〜2717、prior／barrier 検査 2730〜2735、ready 検査 2739〜2805、bench-go 検査 2811〜2848、bench-start 検査 2852〜2898 は実行される。
- `same_study_intent` に基づく study 不一致の raise は **2805、2848、2898**。これらにも認可による条件を付けてはいけない。

不正 record 自体を先に拒否する場合は、そこで処理が止まる。「record の有無に関係なく完全性検査を実行」は、**認可の成功を理由に完全性検査を省略しない**という意味で記述すると P5 と矛盾しない。

**全層の到達性 — 読んだ範囲では、追加の先行 attempt 拒否は見つからない。ただし全層確認済みではない。**

| 層 | 読んで確認した内容 |
|---|---|
| job shell | 156〜163 の nonce は current attempt 名と workload による。551〜598 の v3 分岐は driver の acquisition 検査を呼ぶ。**712〜713 の「attempt root already exists」は 599 以降の非 v3 分岐**なので sized の障害ではない。798〜825 は current attempt 配下の job／raw namespace を使う。 |
| acquisition／measure | driver 3580〜3584 は current attempt を policy base 直下として検査。6990〜7049 は当該 receipt、roots、nonce、request ID を照合。7132〜7133 の固定 attempt 制約は pilot にだけ適用される。 |
| workload lock／campaign ID | 6098〜6129 は渡された `output_root` の layout に lock を置く。2539〜2555、7098〜7103 により output root は attempt／workload 別。同じ campaign ID になっただけで、先行 attempt の lock と同じ path になる構造ではない。 |
| bench barrier | 6193〜6307 は current attempt の ready、bench-go、bench-start のみを扱う。先行 attempt を走査しない。 |
| complete | 4215〜4412 と 4151〜4212 は current attempt の intent／receipts／shards／barrier を照合し、その attempt 内へ create-only で出力する。先行公開 leaf は参照しない。 |
| materialize | 8680〜8763 の先行公開 leaf に関する障害は既知の destination gate。認可後も source、completion、WAL、observation の検査は残る。 |

**読んでいない層:** 射影外の `ident.py`、`trial_registry.py`、layout／WAL／campaign loop、source contract loader 等の内部。特に 7084〜7091 の projection 発行呼出しを読んだことは、trial registry 内部に study 単位の制約がないことの証明にはならない。

したがって、新たに scope へ入れるべき拒否層は**今回の読解では発見していない**。一方、「全層に残る拒否なし」との断定は不可。親には未確認層を返し、そこで追加拒否が見つかった場合に局所対応か裁定パッケージ返却かを判断させる。

**should A2 — 追補は、§6.4 の適用に例外を追加することを明記する。**

- **根拠:** 凍結 §6.4 は bench 前失敗の閉じた列挙。D2172 項2 は将来の観測に適用する別版を認可している。P7 の「列挙外の独立の観測 attempt」だけでは、名称の変更で従来規則の適用を回避したようにも読める。
- **放置時の影響:** 追補が、bench 後反復を許す規則変更の根拠と適用範囲を曖昧にする。
- **是正:** 次の趣旨を明記する。

> 本追補は D2172 項2 に基づき、将来の attempt-0002 一件に限って bench 後の同一配置反復を認可する。元の §6.4 の本文は変更しない。attempt-0001 の判定、非認証 lane、限定 L-A1S-4 は遡及変更しない。本追補だけを根拠に L-A1S-4 を解除しない。

P3 の兄弟公開先は支持する。各 attempt の公開先を create-only にし、attempt-0001 leaf 内に追加しない意味が明確である。一次資料 §7 の子 directory 案でも既存 file の bytes は保存できるが、凍結 leaf 配下の内容集合を増やす。兄弟案の方が「先行 leaf に書き足さない」を直接満たす。

P7 の source commit 経由の束縛も妥当。ただし、**追補を含む commit を運用で選び、その SHA の一致を機械が検査する**構成である。新 helper が追補の存在・内容を専用に検証するわけではない。追補の commit を含めて land を完了してから record を生成する必要がある。

**record 形式・producer の評価。**

P2 の self digest は破損検出であり、認可者の証明ではない。必須性は裁定から直接は導けないが、intent と同型の小さな実装として採用可能。plan が `_submission_intent_digest` の直接流用を退けたのは正しい。同関数 2926〜2933 が除く key は `intent_sha256` だけである。

decision の ID／日付は裁定が要求する情報で、item は D2172 の複数項目から項2を特定するために合理的。汎用 decision registry は不要。

producer が実 HEAD を検査しなくても、submit の 3403〜3404 と record の source 比較で、生成後に HEAD が変わった入力は閉じる。さらに source binding 作成時の 4580〜4581、materialize の 7532〜7547 でも検査がある。追加の HEAD gate は不要。ただし create-only record を古い SHA で作れば、そのまま新 HEAD の submit には使えない。生成順序を「全成果物 land → fresh submit-tree 確定 → record → submit」と固定すればよい。

**nit A3 — 行番号と brief の表現を補正する。**

- **根拠:** 上記現物、および probe log。
- **放置時の影響:** gate の実装は変わらないが、検査根拠と公開先の説明が誤読される。
- **是正:** 以下を記録へ反映する。

| 項目 | 現物との照合 |
|---|---|
| `_canonical_json_bytes` 518〜528、`_sha256_bytes` 531〜532、`_read_json` 489〜501 | 一致 |
| `_exclusive_write` 842〜859、digest helper 2926〜2933 | 一致 |
| `sized_certificate_copy` 1113〜1125 | 一致。1113 は decorator、def は1114 |
| `_v3_submit_cli_fixture` | job test **3190**。pilot 専用ではない |
| `_revalidate_attempt_root` の materialize 呼出し | **8714** |
| study differs の raise | **2805、2848、2898** |
| sized 公開先 | policy JSON **31**。probe log の `MATERIALIZATION_RELATIVE_PATH` は旧経路の定数であり、sized の実効公開先ではない |

plan の主要な挿入位置・呼出し位置は現物と一致する。

## レンズ B

**must-fix B1 — plan の配線 test と複製 gate 実走だけでは、brief の qsub 到達条件を満たさない。**

- **根拠:** brief の完了条件は submit の qsub 到達。plan §7 は `_v3_group_intent`（3237）で sentinel 停止する。実 qsub 呼出しは **3277**。間には source contract／hydrate を含む intent 作成（2617〜2668）、intent 排他作成、attempt topology 作成がある。
- **放置時の影響:** gate 単体は通るが submit は qsub 前で落ちる実装でも、計画された検証を通過できる。
- **是正:** 正例は実 `run_submit` → 実 rear gate → 実 reader → 実 intent 作成を通し、外部投入境界の `_run_qsub` を捕捉する。負例は qsub 未到達と intent 非作成を確認する。実 scheduler への投入は不要。

fixture は実現可能である。job test 3192 は `study_id`／`attempt_name` を受け取り、3206〜3213 で study 別契約・policy・事前登録・sizing inputs と hydrate directory を用意する。**3294〜3321 に既に sized の qsub 3回到達 test がある**。これを台に、attempt-0001 の先行証拠と attempt-0002 の record を足せる。

ただし既存 fixture は policy-ready、CCBench、git などを stub している。これは scheduler 境界までの配線証明であり、実環境の全前提成立とは分けて報告する。policy-ready は 1785〜1795 の実 helper を使うことも可能。

fixture を再利用するなら、job test を変更範囲へ加えるか、必要な小さい fixture を paired test に用意するかを親が決める。現 plan の「変更2ファイル」と既存 fixture 利用を無言で両立させてはいけない。

**should B2 — 保存条件の test は producer と consumer を分け、既存 anomaly test を明示的に採用する。**

- **根拠:** plan の `test_authorize_rerun_rejects_existing_intent`／`…existing_attempt` は producer の拒否を検証する。D2172 が保存を要求する既存 submit の拒否は driver 3225〜3233 にある。
- **放置時の影響:** producer が namespace 再使用を拒否していても、認可済み submit 側の再使用拒否が壊れた変異を検出できない。
- **是正:** 一致 record を置いたうえで、submit に既存 intent、既存 attempt root をそれぞれ与え、固有の拒否と qsub 未到達を確認する。producer の負例で代用しない。

anomaly のために同型の新 test を増やす必要はない。既存の次を保存・検証対象として明記すればよい。

- paired test 3888：collector の anomaly gate。
- paired test 3905：sidecar consumer が anomaly を独立に拒否。
- driver 6378〜6400、6632：observation の anomaly 検査。
- materialize 8723〜8725：destination gate より前の observation consumer。

この配線を変えず、認可による早期 return を導入しないことが根拠になる。ただし、これらの collector／consumer test を「compute 実行中の即時停止まで実測した」とは称さない。

**test 数の評価。**

26関数という数だけでは過剰とは判定しない。ただし、独立した失敗理由を保ったまま整理できる。

裁定の4負例と4保存分類に絞るなら、**最小の数え方は9負例 case**である。別 attempt、別 study、別 source、record 不在の4件に、intent 再使用、root 再使用、完全性、公開先 create-only、anomaly の5件を加える。正例1件を含めて10 case。ただしこれは分類の下限であり、record parser や両 consumer 配線を含む実装全体の十分条件ではない。関数数は parameterize で変わるため、最小値として扱わない。

削減・統合候補は次のとおり。

- `…rejects_extra_keys`／`…rejects_corrupt_json`／`…rejects_bad_shape`：不正 record 表の1関数へ統合。case は残す。
- `…rejects_existing_exact_leaf`／`…preserves_legacy_call`：既存2485の公開先 test に従来動作を集約。
- producer の `…existing_intent`／`…existing_attempt`：namespace 種別で parameterize。
- `…requires_parent`：既存の親 directory 検査を変更しないなら新規独立関数は省略可能。認可済み兄弟の create-only case は残す。
- bench-go／ready-triple の正例は残す。A1の「別先行 attempt」負例も必要。

producer CLI は裁定上の必須ではないが、今回は支持する。手書き JSON と `_exclusive_write` だけでは exact keys、型、digest の作成を別手順に委ねる。小さい producer にまとめる方が再現可能である。将来 attempt 向けの汎用認可管理まで広げる必要はない。

**should B3 — 変異の単位と kill の対象をさらに明確にする。**

- **根拠:** plan §7 の (b)(c)(g)(i)。
- **放置時の影響:** 別の検査で拒否された変異を、対象述語の検証成功として台帳に数え得る。
- **是正:** 変異 diff と狙う case を次の単位で記録する。

| 変異 | 判定・必要な区別 |
|---|---|
| (a) 不在でも解除 | 同 study の正常な先行証拠を置いた gate test で kill 可能。 |
| (b) attempt 照合除去 | 定数内 attempt 制約の除去と、record root／caller 比較の除去は別変異。current／record とも0003の case と、両者不一致の case を対応させる。 |
| (c) study 照合除去 | caller 比較だけを消しても、caller／record とも別 study の case は定数で拒否される。定数側 study 制約と caller 比較を別々に変異させる。 |
| (d)(e)(j) source／decision／digest | 狙う field 以外を正常化し、identity 変更時に digest を再計算する設計は妥当。 |
| (f) 完全性 skip | ready-triple を実在させ、`recorded_epoch=0` だけを変える。候補 loop を認可時に `continue` する変異は例外を出さなくなるため、`prior ready evidence is corrupt` を要求する test で赤になる。 |
| (g) destination create-only 除去 | 実 destination helper の拒否を試すなら kill 可能。ただし公開処理の no-replace まで解除した証明にはならない。既存2485以降の publication testを残す。 |
| (h) recordなし兄弟受理 | 実 helper と実 reader を通す負例で kill 可能。 |
| (i) producer create-only 除去 | 事前 `lexists` と `O_EXCL` の両方がある。逐次2回生成だけでは、片側除去は生き残る。 |

(i) の片側除去を**無条件に等価変異と呼ぶのは不正確**。特に `O_EXCL` 除去は、事前検査後に file が作られる場合の意味を変える。「今回の逐次 case では観測上等価／二重拒否で masked」と限定して記録する。M0 相当の対照に置くなら、その限定を明記し、kill 成功に数えない。新しい並行実行 test を増やすより、producer 内で再作成が実際に可能になる意味的変異を定義する plan の推奨が適切である。

両層 stub 問題への plan の対処は支持する。gate／destination と reader は実関数、record は実 file とする。B1で qsub 捕捉へ延ばす際もこの境界を維持する。

**nit B4 — 親 brief の実測を、証明した範囲に限定する。**

- **根拠:** driver 2677、2743、2858、2815〜2845、7524〜7547 と、親の2本の probe log。
- **放置時の影響:** gate の局所実測が、全工程の完全性や固定 pin 閉包の証明として記録される。
- **是正:** 次のように限定する。

「driver の `iterdir()` 3箇所のうち durable base の列挙は2677の1箇所」は現物と一致する。ただし列挙回数だけから、他 module の拒否不存在までは導けない。また「`.intent.json` 以外で barrier を持たない entry は候補にならない」は不正確で、**intent が名指す実在 prior root は barrier がなくても候補となり、2735で拒否される**。

「別 study は受理」は正常な当該 base に対する gate 単体の実測として正しい。別 study の submit 全体が受理される意味ではない。

「driver に live な bytes pin 無し」は、「変更前 driver の固定 hash に更新不能な形で束縛されていない」という意味に限定する。実行時には4583〜4593で bytesを記録し、7540〜7547で照合する。固定 hash 出現の repo 全体監査や、brief が列挙する外部 AST test は射影外なので追認していない。

replica の禁止メッセージは、少なくともその拒否に到達するまでの現行 gate 検査を通った証拠であり、**変更後 gate 正例の台としては妥当**。ただし複製 script／実体は提示されていないため、全書換えを独立監査したとは言えない。

現行 rear gate の bench-go ready binding は path・field・SHA形式を検査するが、**ready bytesとの digest 一致を再計算していない**。bench-start の digest も形式検査である。複製で ready SHA を再計算していても、gate の受理は completion／materialize の厳密な digest 検査まで成立する証明にならない。gate 複製実走で B1 の qsub 到達 testを代替することはできない。

**nit B5 — 並行 wave の衝突は挿入位置だけでは判定できない。**

- **根拠:** plan §1〜§6 の挿入位置と、親が段4前に行うという worktree 確認。
- **放置時の影響:** 同じ driver／test の並行編集があれば、統合時の競合と再検証対象が増える。
- **是正:** 新 helper を既存関数の外へ置く指定は十分。親は予定どおり worktree list／各 status を確認し、B1で job test を追加するならその所有範囲も確認する。本 consult では並行 wave の不存在を実測していない。

## 総括

**must-fix は2件。**

1. **A1:** 認可による解除を先行 attempt-0001 に限定し、同 study の別先行 attempt の拒否を残す。
2. **B1:** intent 作成前の sentinel を qsub 境界の捕捉へ変更し、brief の完了条件を検証する。

| provisional 裁定 | 判定 |
|---|---|
| P1 | **条件付き**。投入先の定数1件は支持。解除対象の先行 attempt も限定する。 |
| P2 | **条件付き**。形式は支持。認可専用 digest helper を使い、self digest を署名と扱わない。 |
| P3 | **支持**。兄弟公開先は先行 leaf に追記せず、create-only を保てる。 |
| P4 | **支持**。小さい producer は合理的。実 HEAD 照合の追加は不要。 |
| P5 | **条件付き**。完全性検査保存は支持。一律の `not authorized` による全候補解除は反証。 |
| P6 | **条件付き**。不在のみ従来 leaf、存在する不一致 record は拒否。base直下検査を維持する。 |
| P7 | **条件付き**。将来一件の明示的追補とし、attempt-0001／L-A1S-4へ遡及しない。source commit 束縛と専用 digest 検査を区別する。 |

**Q1:** 不在だけ従来 leaf、不一致 record は拒否を支持。  
**Q2:** 追補を含む確定 commit の一致という表現を支持。追補専用の実行時検査とは称さない。  
**Q3:** producer の再作成を実際に可能にする意味的変異を採用。片側除去は限定付きの masked／対照扱いとし、kill に数えない。

**全層の結論:** 読んだ job shell と driver の submit 後段・measure・lock preseed・barrier・complete・materialize では、既知の公開先 gate 以外に先行 attempt を理由とする拒否は発見していない。射影外の trial registry 等の内部は未確認であり、**「残る拒否層なし」の全層断定は保留**する。