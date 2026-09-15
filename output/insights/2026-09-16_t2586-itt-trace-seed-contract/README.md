# [T-2586] ITT trace 契約が seed を検査せず、producer の束縛と consumer の受理集合が食い違っていた

wave: `dev-wave-t2586-itt-trace-seed-contract`
実装 commit: `acd6bb281`

## 何を閉じたか

反実仮想 ITT (backoff counterfactual、cohort1 / cohort2) の trace 契約は、
`tools/pegasus/probes/t2187_adaptive_const_probe.py` の
`_validate_backoff_trace_contract` と `_artifact_contract_metadata` のどちらでも
`step_policy_seed` を一切見ていなかった。共通 gate `_validate_step_policy_seed` は
policy 2 セルが在るときに「`None` でないこと」しか要求しない。

一方 offline consumer は
`orchestrator/campaign/backoff_counterfactual_analysis.py:331` と
`orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py:403` で
`step_policy_seed is not one preregistered uint64 seed` として拒否する。

**事前登録に無い seed で走った成果物に producer が `counterfactual_preregistration` 束縛を
付けて受理し、その同じ成果物を consumer が必ず拒否する状態を作れた。** producer の束縛が
consumer の受理集合と食い違う穴であり、正しさ証拠の一貫性の問題である。

修正は 2 file・241 insertions / 1 deletion。

- 投入経路: 既存の軸検査を通したうえで、counterfactual 2 契約に限り
  `type(step_policy_seed) is int` かつ当該 cohort の登録済み 12 値への所属を要求する。
  違反は seed を名指しする専用 message で **build 前に**拒否する。
- 束縛付与: `_artifact_contract_metadata` の cohort1 / cohort2 枝の既存条件を残したまま、
  同じ型・所属条件を AND で足す。非登録 seed には束縛も cohort2 schema v4 も付かない。

## これは机上のリスクではなかった

段 3 の敵対レンズが実投入経路を辿り、反例を現物で示した。

`t2187_adaptive_const_probe.pbs` は seed を十進構文 (`:179`) と非空 (`:214`) でしか検査せず、
`:220` の exact axes 検査は登録 seed 集合と結合していない。`:544` / `:558` は
`--step-policy-seed 7` をそのまま実 producer へ渡す。**cohort2 の exact cells・3 workload・
threads 24+48・extime 6・rep 0 と、seed `7` は同時に成立する。**

段 6 のレビューが実装後に同じ経路を辿り直し、`7` が `P:4183` の必須検査を通ったのち
新しい `P:3538` / `:3543` で拒否されることを確認した。**この gate は死んでいない。**

## 凍結事前登録の読み方 — 段 2 の棄却を段 4 で覆した

段 2 のプランは、cohort1 の凍結事前登録 §3 の逐語

> **投入経路の契約は変更しない。** 上記の cell 集合・workload・threads・rep index は、
> `_validate_backoff_trace_contract` と投入スクリプトの exact literal 検査を**改訂せずに**通る。

を根拠に、投入経路を締めることを棄却し、束縛付与枝だけを直す案へ落とした。
その結果「build 前に拒否する」という完了判定は達成されない案になっていた。

**段 3 の 2 レンズが独立にこの読解を反証した。** 採った読解は
**「当該試験の実施方針の記述であり、将来の実装改訂を永久に禁じる条文ではない」**である。

- 同書は v2 が束縛するのは改訂後の再解析だけだと書いており、測定条件の束縛は v1 にある。
- 同書は v2 発効後の producer 実行を明示的に想定し、将来 cohort の解析は別に用意すると規定する。
- 正誤表 (`backoff-policy-performance-preregistration-erratum-1.md`) は
  **文書上の要求を変えるとき**に errata を使う先例であって、
  「実装述語なら errata なしで何でも締められる」という先例ではない。
- 逆向きも成立しない。「投入経路」を producer 全体への永久拘束と読むなら、
  `_artifact_contract_metadata` だけを例外にする根拠が別途要る。関数名が列挙されていないことだけでは、
  段 2 の非対称な扱いを支えられない。

登録済み 12 seed の走は引き続き通るので、凍結文が主張する「改訂せずに通る」は保たれている。
一般規則は決定台帳側へ分離した。

## 検査順序を固定したことが本質的だった

`_validate_backoff_trace_contract` の中で、**既存の軸検査を先に、seed の型・所属検査を後に**置いた。
seed 違反は既存とは別の、seed を名指しする message で raise する。

そうしないと、cells は正しい counterfactual 契約で別の軸だけがずれている既存負例 3 件
(threads ドリフト、cohort2 の extime 3、cohort2 の terminal 4,999,999) が
seed 違反で先に落ち、`pytest.raises(ValueError, match="one exact diagnostic cell set")` が外れる。
**既存 assert を書き換えずに済むかどうかが、順序 1 つで決まっていた。**

順序が意図の産物であって偶然ではないことは、変異 M9 が示す。

## 既存 test 4 件は fixture だけを直した

赤になる既存 test は 4 件で、いずれも**入力 fixture の seed だけ**を登録済み値へ直した。
assert・`match=` 文字列・期待辞書・ループ構造・既存 parametrize case は 1 文字も変えていない。
test 関数の削除・改名はゼロ (123 → 133)。

| nodeid | 直す前の入力 |
|---|---|
| `test_counterfactual_artifacts_record_exact_preregistration_sha_only_on_exact_axes` | seed 未指定 (既定 `None`) |
| `test_cohort2_trace_metadata_uses_independent_exact_v4_predicate` | 両 cohort とも seed 未指定 |
| `test_public_dispatch_keeps_policy_grid_and_trace_validators_disjoint` | trace ケースが `--step-policy-seed 7` |
| `test_backoff_trace_contract_accepts_only_four_exact_cell_literals` | helper `inputs()` が seed を渡さない |

**これを「テストを甘くする変更」と数えない理由。** 旧命題「seed 未指定・非登録 seed でも
exact axes なら束縛が付く」は、本 wave が閉じる穴そのものである。穴を述べる命題を保護と数えない。
`test_public_dispatch_...` は**同じ test 内の "policy" ケースが既に登録 seed
(`EXPECTED_SEEDS_BY_SLOT[4]`) を使っており**、trace ケースだけが非登録 `7` だった。同一 test 内の
既存様式へ揃えただけである。

失われる被覆は、**明示的な `None`** と **seed 引数そのものの省略**の負例を
両 cohort・両層に新設して置き換えた。後者は「既定値を登録 seed に変える」誤実装を殺す。

## 4 件目は親の列挙漏れだった

段 2 と段 3 の 2 レンズは metadata だけを締める前提で 2 件を挙げた。親は投入経路も締める裁定に
変えたとき、実測で 3 件目を足した。しかし 4 件目
(`test_backoff_trace_contract_accepts_only_four_exact_cell_literals`) は挙がらず、
**実装子が指示どおり止まって報告して初めて出た。**

原因は、親が「層を締めたとき赤になる既存 test」を**呼び出し点の全数から出さず、
レンズの列挙に足し算しただけだった**ことである。**裁定で層を変えた時点で、前段の列挙は
閉包でなくなっていた。** 正誤表で、`_validate_backoff_trace_contract` と
`_artifact_contract_metadata` の test file 内の全 20 呼び出し点を表にして閉じた。
段 6 の 2 レビューと焦点再レビューは、独立に 5 件目が無いことを確認している。

## 行番号 pin を持つ台帳を段 1 で見落とした

`orchestrator/tests/test_ccbench_spawn_sites.py` の `_DEFERRED_GATE_MEMBERS` は、build sink を
**(relative_path, kind, scope, lineno)** で pin する。本 wave が producer へ 31 行足したため、
同 file の 2 sink の行番号だけがずれた。

| sink scope | kind | 旧 | 新 |
|---|---|---:|---:|
| `<module>._certify_main._build_trace_binary` | `buildcache` | 3910 | 3941 |
| `<module>.main` | `buildcache` | 4303 | 4334 |

これで define × sink の cross-product が 28 triple 分「未審査」になり、受入全走が
決定的な赤 4 node を出した。**2 回の独立した受入走で同一**である。
sink・scope・kind・定義集合は同一で、build sink の追加も削除も無い。ずれているのは anchor だけ
なので、pin を動的導出へ書き換えず 3 箇所・計 5 整数を現行行へ直した
(`:958` `:971` `:2726` `:2730` `:2981`)。動的導出にすると、sink が本当に消えたときに
検出できなくなる。

**anchor が効いている負例は合成していない。** 受入全走が古い anchor で 2 回とも決定的に
赤くなったことが、production で取れた負例そのものである。

**原因は段 1 の pin 閉包検索を自分で切ったこと。**
`git grep -n "t2187_adaptive_const_probe" | grep -v <自 test> | head -40` を実行し、
表示された 40 行を閉包の全件として扱った。その 40 行は
`acceptance_duration_ledger.json` の node 行が大半を占め、`test_ccbench_spawn_sites.py` は
切った側にあった。是正として `git grep -l` で全件 (185 path) を出し直し、行番号を pin して
いるのがこの 1 file だけであることを確かめた。他の pin (`test_hooks.py`、
`admission_registry.json`、`submit_t2417_*.sh` 等) は path による分類だけで、
行番号も内容 hash も持たない。

## 保証しないこと

- **helper の直接呼出しまでは守らない。** `_counterfactual_row_metadata` は渡された hash を
  seed の所属に関係なく転記する。任意の呼び手がこれを直接呼べば、非登録 seed に束縛を載せた行を
  作れる。保証対象は **producer の通常実行**が書く成果物 JSON と journal JSONL である。
- **`main` の引数配線そのものを壊す誤りは検出しない。** JSON / journal の test は
  metadata と行 helper を直接呼んで組み立てるので、`main` が metadata へ seed を渡すのを
  やめる型の誤りは緑のまま通る。段 6 のレビューがこの誤実装を疑似コードで構成した。
  親はこれを scope 外と裁定した (仮想リスク向けの機構を足さない、というユーザー裁定に従う)。
- **cohort1 の新規出力は、そもそも seed 検査より手前で拒否される。** 現在の producer は
  事前登録文書の現 bytes を hash するが、cohort1 consumer は測定時の v1 hash を要求する。
  これは事前登録が明示的に正当化している既知の制限であり、本 wave は変えていない。
  seed の不整合自体は実在したが、cohort1 では拒否理由がこちらに先取りされる。
- **既存の 12 成果物は 1 byte も変えていない。** 一方、producer を編集した以上、
  今後の走の `driver_sha256` は変わる。これは provenance の正しい更新であり、旧値へ偽装していない。
- **repo 内の検査は、gate と検査を同じ主体が変更できる限り、意図的な弱体化への完全な防壁ではない。**

## 変異 matrix

probe → 本走の 2 段。spec と report は同 dir。

- **probe**: baseline PASSED、9 変異すべてで赤、生存 0。全件 `SURVIVED` 登録で観測 node を集めた。
- **本走**: **baseline PASSED / KILLED 9 / SURVIVED 0 / MISMATCH 0 / TIMEOUT 0、
  期待 node 完全一致 9/9、harness rc=0。** repo head `acd6bb281`、
  spec sha256 `2f7e5c40086dfc01b4b98a7308614eb01c54a4039689eb606441d0ca0593a394`。

| # | 変異 | 赤 node 数 | 帰属 |
|---|---|---:|---|
| M1 | cohort1 validator の所属条件を削除 | 5 | cohort1 validator 負例だけ |
| M2 | cohort2 validator の所属条件を削除 | 5 | cohort2 validator 負例だけ |
| M3 | cohort1 metadata の所属条件を削除 | 6 | cohort1 metadata 負例だけ |
| M4 | cohort2 metadata の所属条件を削除 | 6 | cohort2 metadata 負例だけ |
| M5 | cohort1 seed 表の slot 00 を 1 桁改竄 | 8 | 表一致検査 + slot00 を使う正例 |
| M6 | cohort1 の所属集合を両 cohort の**和集合**に緩める | **1** | cohort 取り違えの負例だけ |
| M7 | cohort1 の厳密な型検査を落とす | 2 | float 負例と `int` サブクラス負例 |
| M8 | cohort1 の所属を**1 値だけ**に過剰に狭める | 11 | 全数正例の slot 01〜11 |
| M9 | seed 検査を軸検査より**前**へ動かす | **1** | 軸違反 message を要求する既存負例 |

**単一理由性。** validator 層の負例は `_validate_backoff_trace_contract` を、
metadata 層の負例は `_artifact_contract_metadata` を直接呼ぶ。end-to-end で呼ぶと
validator が先に拒否して metadata 側の欠陥を隠すため、層ごとに直接呼んでいる。
M1〜M4 が層ごとに互いに素な node 集合で死ぬことがその裏付けである。

**M8 は「承認外の過剰拒否」の正例である。** 本 wave は受理集合を縮小するので、
狭めすぎを捕まえる正例を登録しないと縮小方向の誤りが素通りする。

**M7 が 2 node で死ぬことは、段 6 の fix が検出力を足した証拠である。** 段 6 のレビューは
「cohort1 の型負例が float だけなので、`type(...) is int` を `isinstance(...)` に弱める誤りを
殺せない」と指摘した。fix 子が `int` サブクラス負例を足し、producer を一時的に弱めて
その負例が赤になることを実測してから元へ戻した (sha256 で確認)。

## 採らなかった案

- **共通 gate `_validate_step_policy_seed` を締める。** この gate は certify 経路や
  policy performance 契約も通る。counterfactual 2 契約だけを狭めたいので、契約側に置いた。
- **cohort1 の 12 値を生成規則から導出する** (`sha256("izanagi-t2265-policy2-seed-NN")` の
  先頭 8 byte を big-endian uint64)。producer に新しい暗号計算を持ち込み、原典との一致検査が
  別途要る。凍結原典 §8.1 の逐語表を写し、三者照合で担保する方を採った。
- **cohort2 用に別表を作る。** 既存 `CERT_PREREGISTERED_STEP_POLICY_SEEDS` が cohort2 の
  登録集合と 12 値すべて一致し、既存 test が consumer / PBS との一致を既に監視している。
  複製表は同期の負債になるので直接参照した。
- **既定 seed を含む `CERT_POLICY2_STEP_POLICY_SEEDS` を使う。** 対象集合より広く、明確に不適切。

## 12 値の三者照合

cohort1 の 12 値は、凍結原典 `docs/backoff-counterfactual-preregistration.md` §8.1、
実装 (`t2187_adaptive_const_probe.py` の
`COUNTERFACTUAL_PREREGISTERED_STEP_POLICY_SEEDS`)、consumer
(`backoff_counterfactual_analysis.py` の `PREREGISTERED_SEEDS`) の三者で完全一致する。
親が抽出して機械照合し、段 3 の 1 レンズと段 6 の 1 レビューも独立に逐値照合した。

凍結事前登録 2 件は byte 単位で不変であり、sha256 も consumer の pin と一致する。

- cohort1: `526d9384d8a8c62f82b132c41672aa2eff32722788ad06858c09f80185ca495a`
- cohort2: `8b4127f4be895da0d25da88b0837f679ecf06d43ab656b16d2944146b9f7a9e9`

## 計測環境の注記

`tools/run_tests.py` は本 wave 中、子・親を通じて `qstat -Q` の preflight で
`_PEGASUS_DISPATCH_RC = 16` を返し続けた (計算ノードの混雑)。実測は自走 harness と、
`--force-dispatch` を明示した変異 harness の dispatch 経路で行った。
性能測定は一切行っていない。
