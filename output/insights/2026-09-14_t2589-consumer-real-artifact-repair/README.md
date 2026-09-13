# [T-2589] T-1998 対 consumer の実成果物非互換を是正し、balanced の対を認証した

前 wave ([T-2557]、`output/insights/2026-09-13_t2557-balanced-stock-inline/README.md`) で
balanced stock-inline の正式測定は完走したが、consumer が拒否を返した。原因は測定側ではなく
consumer 側で、合成 fixture に対してだけ検証された述語 2 系統が実成果物では成立しなかった。

本 wave はその 2 件を是正し、**保全してあった同じ成果物を再測定なしで認証した。**

## 1. 認証された結果

事前登録 `docs/t1998-balanced-stock-inline-preregistration.md` v1 の下での判定である。

| 項目 | 値 |
|---|---|
| status | **accepted** |
| reason | `preregistered-balanced-stock-inline-pair` |
| ratio | 1.1122537536191646 |
| improvement_percent | **11.225375361916456** |

| arm | genome | 5 sample (tps) | median | cv | unstable |
|---|---|---|---|---|---|
| baseline | `BACK_OFF=0`, `BACKOFF_FIXED=-1` | 4079966 / 3891020 / 3978513 / 3859794 / 3893509 | 3893509 | 0.022721229214372803 | false |
| target | `BACK_OFF=1`, `BACKOFF_FIXED=5` | 4437166 / 4326276 / 4361949 / 4330570 / 4289164 | 4330570 | 0.012790608817328908 | false |

成果物が記録した identity は事前登録 §4 と全項一致した。

| 対象 | 値 |
|---|---|
| repository_commit | `a551cdd3014708993475108f014aacbf32c21137` |
| CCBench gitlink | `511c9538e4e8efa54b45cda62e72389ed3b706ec` |
| 環境契約 digest | `e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01` |
| job body script sha256 | `dff913cb1044858b56f25721f2d0aac6539bbcf2a7ddb63b9e6b4bbcac7aecd8` |
| baseline の performance binary sha256 | `660543647aa9b8bf0b6ff087ec461c901fd186296dc2751cd7d1deb89ae565d9` |
| target の performance binary sha256 | `6c89ebd91efddfd6c01fa5fbff1d5d6cf16e8488b7e2fc85f98ec76e1a8dfec4` |
| campaign_id | `backoff-sweep-silo-balanced-sweep-0dd37c05` |
| 事前登録 blob sha256 (成果物側・解析規則側とも) | `464e3af59a1ef0f776cad022a52ab87e1fdf2709abfc2062c058203bc813719c` |

事前登録の版は v1 のまま。本 wave は事前登録の bytes を 1 byte も変えていない。
成果物 root は repo 外の
`/work/1/SFC/tanab/t1998-balanced-stock-inline-runs/t1998-balanced-stock-inline-20260913T132723Z-548740-balanced`。
判定の全文は job dir の `decision-final.json`。

**旧 headline の +11.3% は事前登録が期待値として固定しなかった値である** (§3 が明記していた)。
現行環境での prospective 測定が近い値を出したことは事後の観察であって、事前の予測ではない。

## 2. 直した 2 件

### 2.1 実行 wrapper 前置を環境契約から引く

consumer は `("numactl", "--interleave=all")` を module 定数で固定要求していた。これは
`linux-baremetal` 契約の値であり、事前登録が pin する `pegasus` 契約は空 prefix である。
D144 が単一 NUMA ノードという根拠を実測済みで、D924 は「env contract の値を計測側へ literal で
写す」形を却下し契約から引くよう定めている。

consumer が既に成果物と照合済みの環境契約 digest から
`env_contract.resolve_by_contract_sha256(...).contract.numactl` で hash 束縛のまま解決する形へ移した。
`lookup(env_tag)` は使わない — 測定時の契約へ束縛する必要があるためである。
実行対象と configure の build dir の一致検査は不変で、**この向きでは検査は緩んでいない。**

### 2.2 toolchain digest の腕内再導出を撤去

producer は `--version` 全文を含む manifest から `toolchain_record_sha256` を作るが、
WAL に載るのは `requested` / `realpath` / `version_first_line` の 3 key 射影だけである。
回収成果物 23 file に `complete_toolchain_manifest` は 0 件で、この digest は再導出できない。
consumer の「記録された digest == 記録された射影の canonical hash」はどの実成果物でも成立しない。

腕内の再導出だけを撤去した。残したのは、manifest の非空性、digest の形式、
**腕間の digest 一致**、腕間の manifest 一致、`result.toolchain` との一致である。
腕間比較は実成果物で通る健全な検査であり、欠陥ではない (境界は偵察で確定した)。

**受理集合は広がる。** 事前登録 §6 が列挙する判定規則は 1 つも動かないが、それだけを根拠にしない。
撤去したのは producer の証拠の意味を取り違えた等式であり、anomaly を出した variant や
非直列化実行を通す変更ではない。認証 admission、全記録の anomaly / verdict 検査、abort 拒否は残る。

### 2.3 保証しない範囲

consumer の module docstring に明記した。**この consumer が読む回収済み成果物**
(result.json、reservation.json、campaign の lock と WAL) が全文 manifest を持たないため、
digest の再計算と identity 射影との暗号学的対応は検証しない。
**両腕の digest を同じ別値へ置換した改竄は、この層では拒否できない。**
新しい検査でこの穴を塞いでいない。塞げないことを書くのが対応である。

build cache 側の completion manifest は全文 manifest とその sha256 を保存している。
無いのは回収成果物の側だけである。

## 3. 判断の経緯

ユーザー指示は「codex に相談して決める。過剰実装・過剰ガードレールは禁止」。

別系統モデル (read-only、静的検査) の相談は親案に同意したが、親の説明を 3 点否定した。3 点とも採用した。

- 「受理集合は変わらない」は誤り。案 A は拒否述語の撤去であり受理集合は広がる。
- D1876 は「保証しない範囲を明記する」前例ではあるが、**既存検査の撤去を認可した前例ではない。**
- fixture 自体が実 producer と別物であり、誤った等式を仕様化していたテストは撤去と両立しない。

親が独立に見つけた追加事項として、撤去対象のテストは **F909 の恒久対応そのもの**だった。
F909 の一般の教訓 (片側だけを変える負例は対称な層に mask される) は有効なままだが、
守っていた層が誤った等式だったので supersede 追記で現況を示した。

敵対レビュー 2 本 (正しさ境界 / 整合と実効性) はいずれも実装を止める所見を出さなかった。
レンズ A は producer 経路・導入 commit・実 WAL を辿って「旧等式が正しい対応検査になる反例は無い」と
確認し、レンズ B は「元の誤検査を戻すと新 fixture の受理例が落ちる」ことを示した。
レンズ A の real 所見 2 件は本 README §2.3 と §5 に反映した。
レンズ B の real 所見のうち F909 は §5 の supersede、受入台帳は §5 に記す。

逐語は `verbatim/` に置いた。

## 4. 変異検査

`tools/mutation_harness.py`、`--runner-mode dispatch`、repo_head `4d7cd40a9b125fd5bc04e2d47a980d8b772c9a31`。

事前登録は probe (全件 SURVIVED 登録) で観測 node を集め、本走で完全集合として固定した (DW-M08)。
**本走は baseline PASSED、3 変異すべて KILLED、期待 node 集合と完全一致 (matches_expectation=true)。**

| id | 変異 | 期待 node 数 | 結果 |
|---|---|---|---|
| M1-wrapper-prefix-ignored | prefix 比較を無効化し常に argv[0] を返す | 1 | KILLED |
| M2-contract-prefix-relittered | 契約解決を旧 literal `("numactl","--interleave=all")` へ戻す | 20 | KILLED |
| M3-cross-arm-digest-equality-vacuous | 腕間 digest 一致を無効化 | 1 | KILLED |

M1 と M3 は単一 node で、赤理由が一つに絞れている。M2 の 20 node は pegasus 成果物を読む
end-to-end テスト群であり、旧 literal では現行環境の成果物が軒並み拒否されることを示す。
spec と report は本 directory の 4 file。

**変異事前登録の時点について。** DW-M01 は変異を実装前に登録すると定めるが、本 wave では
実装子の投入後に spec を書いた。変異対象は親が段 5 の brief で実装前に確定させた 2 箇所と、
そこに対応する既存検査 1 箇所であり、実装子の出力を見て選んだものではない。
probe も本走も結果を見る前に登録している。この逸脱を隠さず記録する。

## 5. 本記録が閉じないもの

- **他の成果物での欠陥不存在。** 「残る検査に追加の欠陥は無い」は 1 成果物の受理からは導けない。
  言えるのは**この成果物では追加の拒否に遭遇しなかった**ことだけである
  (前 wave の README §4 の書き方はこの点で言い過ぎだった。同 README の追補で訂正した)。
- **F909 の恒久対応。** 撤去したテストを指しているため supersede 追記で現況を示した。
  一般の教訓は有効なままである。
- **受入台帳のずれ。** 削除した node が `orchestrator/tests/acceptance_duration_ledger.json` に
  `0.0` 秒で残り、追加した node は未登録である。敵対レビュー B はコード上の根拠つきで
  「この不一致だけで通常受入は赤にならない」と判定し、本 wave の受入全走でもそのとおりだった。
  台帳生成器の `--check` を別途走らせれば差分で終了値 1 になる。放置の判断であり、修正ではない。
- **単体テストの検査範囲。** 新しい単体テストは prefix だけの argv や長さの違う prefix を
  与えていない。敵対レビュー B が指摘したが、現実装の不具合ではなく、追加ガードは足していない。
- **compiler の同一性。** 事前登録 §9 の但し書きはそのまま残る。今回 `source-identity-unbound` に
  落ちなかったので、計算ノードの `g++` が事前登録の arm 別 source digest を再現したことは
  実測されたが、これは 1 回の観測である。
- **write-heavy と read-heavy。** 事前登録の対象外であり、本 wave も測っていない。
- **過去の成果物。** 本 wave の是正は過去の判定を遡って昇格させない。
