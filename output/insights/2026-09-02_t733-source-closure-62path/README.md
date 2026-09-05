# [T-733] enforcement source closure を exact 24 path から exact 62 path へ広げた

- 日付: 2026-09-02
- branch: `worktree-dev-wave-t733-source-closure-transitive`
- 根拠裁定: D1075 (certified 経路の source closure を推移閉包へ広げる)
- 関連既裁定: D368 (正本リストの機械検査に静的 AST 解析を採らない)、D1128 (判定器が閉包の
  内側にある限界を明記する)、D1163 / D1245 (歴史閲覧と現行認証の分離)、F712 (現行 golden と
  凍結 golden の分離)

## 何をしたか

`orchestrator/campaign/campaign_lock.py` の `CONTRACT_LOADER_RELATIVE_PATHS` を
exact 24 path から exact 62 path へ広げた。既存 24 path の並び順は epoch preimage に効くため
1 本も変えず、新規 38 path を末尾へ repo-relative path の辞書順で追加した。

新規 38 path = 現行 24 member が直接 import する 36 module + Python が対象 module より先に
実行する package 初期化 2 module (`orchestrator/critic/__init__.py`、
`orchestrator/qualification/__init__.py`)。

D1075 が名指しした未収載の委譲先 (calibrator、buildcache、build_admission、source_digest、
env_attestation、site_policy) はすべてこの 38 に含まれる。

## 閉包の寸法 (2026-09-02 実測)

| 集合 | 件数 |
|---|---|
| 拡張前の閉包 | 24 |
| 現行 member の明示 import 先 (新規) | 36 |
| 実行時 package 初期化 (新規) | 2 |
| 拡張後の閉包 | **62** |
| first-party import の推移閉包 (発見集合) | 131 |
| 未収載 | **69** |

発見に使った import 解析は D368 に従い**発見補助にとどめ**、閉包の正本は curated exact tuple の
ままとした。段 3 の 2 レンズが独立に 131 を再導出して集合差ゼロだった。

## 親の測定が 2 回誤り、どちらも子が検出した

1. **相対 import の階層解決の不具合。** `from ..calibrator import runner` 形の 2 階層上への
   相対 import を解決し損ね、1 段目の委譲先を 30 と測った。正しくは明示 36。
   段 2 の plan 子が 6 本の漏れを file:line つきで指摘し、親が script を直して再現・確認した。
   落としていたのは `calibrator/effective_clock_policy.py`、`calibrator/runner.py`、
   `calibrator/schema_v2.py`、`calibrator/stability.py`、`critic/online_digest.py`、
   `holdout_observation.py`。
2. **実行時 package 初期化の見落とし。** 明示 import しか見ておらず、Python が対象 module より
   先に実行する `__init__.py` を落としていた。段 3 の 2 レンズが**独立に同じ 2 file** を挙げた。
   親は最上位 `orchestrator/__init__.py` が存在しない (namespace package) ことを確認し、
   追加はこの 2 本で閉じると裁定した。

親の brief には他に 3 件の誤りがあった。「閉包の成長は受理集合を狭める方向だけ」(正しくは
非互換な置換)、「authority = null」(正しくは schema-less v1 で authority key が無い)、
producer 一覧からの plotting 2 本の欠落である。

## 外部 lock 11 件が decode 不能になる (裁定パッケージへ)

親が `/work/1/SFC/tanab/b10-backoff-grid-runs5` と `/work/1/SFC/tanab/izanagi-measurements` を
走査すると、campaign lock **11 件すべてが現行 exact-24 map** だった (B10 格子 3 件、
paper-story A-2 認証 8 件)。段 3 レンズ B は 5 件と申告したが、古い数字だった。
閉包をどの大きさへ広げても同じ代償が出るので、段階の切り方の問題ではない。

旧 grammar の拒否そのものは、`test_v2_rejects_legacy_exact_two_source_blob_keys` と
`test_v2_rejects_pre_wave_exact_twelve_source_blob_keys` が過去の閉包拡張から一貫して固定して
いる意図的な挙動である。

### 親の段 4 裁定はここで誤った (受入で判明)

親は段 4 で「repo 側 consumer はこの 11 件を decode 経由で読んでいない」と裁定し、
受入は赤にならず図の再生成も壊れないと結論した。**これは誤りだった。**

親が確認したのは `test_b10_extended_figure_provenance.py` (外部 source を file bytes の
SHA-256 で束縛し decode を通さない) だけで、**別 file の
`test_plot_b10_extended_backoff.py` を見ていなかった**。同 test は
`tools/plotting/plot_b10_extended_backoff.py` の `load_measurements()` を実 root に対して呼び、
そこで外部 lock を `artifact_admission` 経由で decode する。

受入全走 (attempt 1) の結果は `1 failed, 19869 passed, 92 skipped` で、唯一の赤は

```
orchestrator/campaign/campaign_lock.py:263: CampaignLockCodecError:
authority.contract_loader_blob_sha256s の exact key 集合が不正
```

だった。lock は `b10-backoff-grid; workload=write-heavy` の外部 official lock である。
**閉包拡張に帰属する回帰であり、非帰属赤ではない。**
さらに同じ decode 経路は fig2c の生成器そのものなので、図の再生成も現状では通らない。

段 2 が提案した「pre-T733 exact-24 map を拒否するテストの新設」は、この扱いを先に
凍結してしまうため採らなかった。

### 決着 — 歴史閲覧限定の decoder を足した

ユーザー指示で codex 2 レンズへ相談した (`verbatim/s4b-consult-a.md`、`verbatim/s4b-consult-b.md`)。
**両レンズが独立に「歴史閲覧限定の decoder」を推し、独立に同じ条件を付けた** —
通常 decoder を union grammar へ広げてはならない。親が裏取りして採用した
(`verbatim/s4b-ruling.md`)。

他案を落とした理由:

- **11 件を新閉包で再発行する案**は規律 7 に反する。lock は WAL より前に live capture して
  作られる (`ident.py:575-602`)。測定後に残り 38 path の blob hash を計算しても、
  「測定時に disk bytes と blob が一致した」事実は復元できない。lock hash は B10 の
  completion / receipt chain と A2 の raw manifest / acquisition digest 鎖へ伝播しており、
  外部 20〜40 file の書き換えになる。凍結 provenance を変えない条件とも両立しない。
- **fig2c を bytes 束縛へ移す案**は作業量最小 (120〜260 行) だが、失うのが正しさ側の検査
  (activation tuple、記録 commit blob 照合、deny overlay、attempt topology、build receipt) である。

実装した設計:

- pre-T733 の 24 path を**順序込みの独立 literal**として置いた。現行 exact-62 tuple の slice では
  ないので、将来 exact-62 側が動いても歴史 grammar は動かない (親が AST で機械確認)。
- 歴史 decode は**別入口・別返却型** (`DecodedHistoricalCampaignLock`)。flag による緩和ではない。
- `purpose` を decode より前に exact enum で確定し、`HISTORICAL_RAW` のときだけ歴史 decoder を選ぶ。
- grammar は path 数でなく **exact ordered tuple** で識別する。subset / superset / 同数別集合 /
  順序違いはすべて拒否。
- 記録 commit blob との digest 照合は歴史 grammar の 24 path 全体で維持。
- 歴史 epoch は記録 grammar の順序と、その grammar 固有の scope 文言で計算し、現行適合は `unknown`。
- 互換実装は新 module へ分離せず既存 file の中に置いた (D1128 の自己参照問題を増やさないため)。
- **実在 corpus のある exact-24 だけ**を足した。8 / 12 / 14 / 25 / 27 は入れない。

### 呼び出し境界の赤と、その直し方

初回実装は `artifact_admission._verify_committed_loader_binding` から
`contract_loader_binding` の**私有 helper** (`_validated_root` / `_require_commit` / `_blob`) を
直接呼んでいた。`test_production_contract_loader_binding_call_sites_are_exact` が検出した。

期待一覧へ 4 件を足して済ませることはしなかった。私有 helper への到達は、その module が
公開面で保つ順序 (root 検証 -> commit 検証 -> blob 取得) を呼び手側で組み直すことであり、
この検査が守る境界そのものを壊す。`verify_committed_contract_loader_blobs()` を公開面へ足し、
呼び手は公開関数だけを使う形へ寄せた。親が実測して私有 helper 呼び出し 0 件、
呼び出し箇所 8 件 (増分は公開関数 1 件だけ) を確認した。

### 歴史 decoder の変異事前登録と結果

本走は 3/3 KILLED、SURVIVED 0。台帳は `mutation-ledger-historical.json`。

| # | 変異 | 結果 | 検出したテスト |
|---|---|---|---|
| M06 | 歴史 grammar の判定を exact ordered tuple から key 数へ緩める | KILLED | 同数別集合を弾く 2 件 |
| M07 | `purpose` の判定を外し、certified でも歴史 decoder へ落ちるようにする | KILLED | P4 (同じ bytes の certified 拒否) 1 件 |
| M08 | 歴史 decode で記録 commit blob との digest 照合を飛ばす | KILLED | 照合不一致を検出する 1 件 |

M07 と M08 は落ちるテストがちょうど 1 件で、理由が 1 本に絞れている。

教訓: 「外部成果物を repo が decode 経由で読んでいるか」は、1 つの test file を見て
結論してはならない。同じ成果物 root を指す consumer は複数 file に分かれ、
束縛の仕方 (bytes hash か decode か) が file ごとに違う。

## 検査が空回りしていた穴と、その塞ぎ方

期待 E1 が test 側の literal から再導出されるだけだったため、production tuple と test literal を
**同時に**並べ替えると検査が追随して緑になった。epoch の preimage は tuple 順に path と digest を
連結するので、順序は値に効く。

合成 fixture に対する E1 と、tuple 順に連結した path 列の SHA-256 を**固定文字列**として pin した。
固定値はどちらの literal からも導出されないため、両側同時変異でも落ちる。

- ordered path-list SHA-256: `b274387d0be033a98e86d54e5225667221bde79776832e73fb3d07cebfc6067a`
- synthetic fixture E1: `E1:78920efc47f4eb280b956a8fb92abed16b888495db544b62b1a15bf1f61004e9`

**この 2 値は子の計算を信用せず、親が production tuple から独立に計算して照合した。**
ordered list は `UTF-8(path) + 0x00` を tuple 順に連結して SHA-256。E1 は
`campaign-verifier-epoch/v1` に続けて各 path について
`UTF-8(path) + 0x00 + SHA-256(合成 blob)` を tuple 順に連結して SHA-256 し、`E1:` を付ける。

## 変異事前登録と結果

本走は 5/5 KILLED、SURVIVED 0。台帳は `mutation-ledger.json`、spec は `mutation-spec.json`。

| # | 変異 | 結果 | 検出したテスト数 |
|---|---|---|---|
| M01 | production tuple から `calibrator/runner.py` を落とす | KILLED | 196 |
| M02 | 記録側の blob 照合 (`verify_committed_contract_loader_binding`) を無効化 | KILLED | 63 |
| M03 | `_validate_authority` の exact key 検査を subset 許容へ緩める | KILLED | 64 |
| M04 | `verify_live_contract_loader_binding()` の loop を `[:-1]` にする | KILLED | 1 |
| M05 | 新規 38 path のうち 2 本を入れ替える (test literal は据え置き) | KILLED | 131 |

M04 が落とすのはちょうど 1 件、辞書順末尾の `qualification/series.py` のケースだけで、
理由が 1 本に絞れている。

### M02 は初回 probe で生存した (erratum、消していない)

当初の M02 は「新規 member `buildcache.py` の bytes を 1 つ変える」だった。probe 走で
**SURVIVED (rc=0、失敗 0 件)**。原因は、テスト側の drift 検査が実チェックアウトではなく
合成 fixture リポジトリを使って判定するため、実物のファイルを触っても検知経路に乗らないこと。
テスト設計としては正しい (実チェックアウトに依存しない) が、この変異では効いている gate を
撃てていなかった。

DW-M02 に従って実効 gate へ再照準し、記録側の照合を無効化する変異へ差し替えた。
初回の probe 台帳は `mutation-probe-attempt1.json`、再照準の probe は
`mutation-probe-attempt2.json` として残してある。

## 過剰拒否の正例 (受理集合を縮小する wave の義務)

| # | 正例 | 結果 |
|---|---|---|
| P1 | 新しい exact-62 map の lock が decode でき E1 を発行する | 通る |
| P2 | authority を持たない schema-less v1 lock が E0 として扱われ `HISTORICAL_RAW` で読める | 通る |

## 保証の文言

D1075 は「保証の文言は閉包が閉じるまで広げない」と命じている。`identity_scope` は
curated exact 62 path であること、発見集合 131 のうち何を収載したか、そして
**source-import 推移閉包ではない**ことを書く。`excluded_scope` は未収載 69 module に加えて、
data/schema・生成物・subprocess・外部 command/Git・toolchain・binary・動的 import を含む
非 import 委譲が対象外であり、**完全性を主張しない**ことを書く。

docstring は保証内容を言い直さず、この 2 定数を正本として参照するだけにした。
初回実装では定数だけが正しく更新され docstring 3 箇所が旧説明のまま残っており、
段 6 の敵対レビュー (レンズ A) がこれを検出して fix した。

非 import の委譲経路は列挙しても網羅を証明できない。段 2 とレンズ A が挙げた個別の
data file・外部 Git の一覧は**例示であって全件ではない**とし、文言へ焼かなかった。

## 凍結成果物

fig2b / fig2c / fig4 の PNG・PDF・provenance JSON はいずれも bytes を変えていない。
F712 の恒久対応どおり現行 golden と凍結 golden が分離されており、更新したのは現行側だけである。
両レンズが独立に、間接的な再生成要求が無いことを確認した。
