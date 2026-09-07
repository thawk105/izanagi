# 段 1 brief — [T-2067] (a) oracle report / verdict / judge へ選択 identity の強制を入れる

## scope (確定)

D1526 (ユーザー裁定) の実装。oracle の 3 つの公式 CLI 経路が、床値の**選択規則の再強制**を
まったく通らずに結論へ到達できる穴を塞ぐ。

対象 (実アンカー表):

| 単位 | file:line | 現状 | 入れるもの |
|---|---|---|---|
| R | `orchestrator/campaign/s8b_oracle_report.py:2547` | `load_ratified_freeze(root)` の直後に強制なし | `assert_g1_floor_selection_identity(ratified, root)` |
| J | `orchestrator/campaign/s8b_oracle_judge.py:749` | 同上 | 同上 |
| V | `orchestrator/campaign/s8b_verdict.py:828` | 同上 | 同上 |
| M | `orchestrator/campaign/s8b_oracle_manifest.py:1019` (`verify_manifest`) | 選択 token を要求しない | (P1) 下記参照 |

先例は `orchestrator/campaign/s8b_oracle_manifest.py:1206` (`build_approved_manifest` が
`load_ratified_freeze` 直後に同じ 1 行を呼ぶ)。

## 穴の実測 (親が現物で確認済み)

- 強制の本体は `orchestrator/campaign/s8b_ratified_freeze.py:3321` の
  `if result_type is LaunchValidatedFreeze:` の枝の中にしかない。
- 3 経路が使う `reverify_published_freeze` は `result_type=ReverifiedFreeze` で
  `_launch_validate` を呼ぶため、この枝に入らない。**D1503 が述べた事実がコードで確認できた。**
- 実走経路 (`s8b_oracle_driver.py:664` / `:1351`) は `launch_validate` を呼ぶので強制済み。
  同 file の `:496` は freeze bytes の sha256 一致比較であり強制点ではない (引数の指摘どおり)。

## 確定済みユーザー裁定

- **D1526**: 「oracle の report / verdict / judge へも選択 identity の強制を入れる。これらは
  凍結成果物の生成元一覧に含まれるため bytes が動くが、凍結物の所定手続きで払う。」
  逐語は `D1526-verbatim.md`。
- **解除しないもの**: D1241 / D1313 の advisory / non-certifying 上限。本 wave はこれに触れない。
- 残件 (b) 母集合の数え直し / (c) `build_manifest`・`write_manifest` の公開迂回口 / (d) 導出被覆の穴は
  (a) の着地後の別 wave。本 wave の scope 外 (別 branch `worktree-dev-wave-t2067-bcd-selection-closure`
  が存在する)。

## 凍結 pin の閉包 (DW-O09、親が 4 軸すべて実施)

1. **path を key にする pin**: `orchestrator/campaign/s8b_oracle_manifest.py:65` の
   `_GENERATOR_SOURCES` が 5 file を canonical path として持つ。うち **report と judge が対象**
   (verdict / driver / manifest 自身は含まれない)。`_validate_generators`
   (同 file:458–496) が key 集合の**完全一致**と各 file の**実 byte hash 一致**を要求する。
2. **file 全体 sha256 を値で焼く pin**: 現在値
   - report = `f7ef6259f8feb3a6ccd7812d85132f19bc36e10fa4cd10cea28ecd145769c93b`
   - judge  = `0e6276ddcb6cde6e38f781bdbb8df1289520cfcce9653330d2c83a1db20784d3`
   この 2 値を repo 全体へ掛けた結果、**生きた pin は
   `orchestrator/tests/test_s8b_oracle_manifest.py` の `PIN_GATE_SPEC_RAW` (63–101 行) だけ**。
   他の hit は `output/insights/` 配下の過去 wave の逐語記録 (歴史記録、機械は読まない)。
   `PIN_GATE_SPEC_SHA256` (同 file:63) はその blob の sha なので連動して変わる。
3. **path 以外を key にする pin**: key 名 `"report"` / `"judge"` / `generator_versions` で引くと
   consumer は `_validate_generators` と `s8b_oracle_spec.validate_reviewed_spec`。
   fixture 側で `generator_versions` を持つのは
   `orchestrator/tests/s8b_oracle_spec_fixture.py`、`test_s8b_oracle_driver.py`、
   `test_s8b_oracle_report.py`、`test_s8b_oracle_manifest.py` の 4 つ。うち **hash を literal で
   焼いているのは `test_s8b_oracle_manifest.py` のみ** (軸 2 の値検索が権威)。他は実 file から
   live 計算しているため bytes 変更に追随する。
4. **output/ の凍結成果物**: `generator_versions` を含む json は `output/insights/` の 4 件だけで、
   いずれも過去 wave の変異記録・入力記録。**発行済みの公式 manifest は 0 件** ([T-608] の裁定:
   「生成器 source bytes の変更が pin を動かすのは設計どおり、発行済み manifest 0 件」)。
   `s8b_oracle_spec.APPROVED_SPEC_SHA256` は既定 `None` で、repo に生きた承認 spec は無い。

**結論**: 「凍結物の所定手続き」で払う対象は成果物の再発行ではなく、
`test_s8b_oracle_manifest.py` の `PIN_GATE_SPEC_RAW` / `PIN_GATE_SPEC_SHA256` の再 pin 1 か所。
F226 のとおり、report.py / judge.py へのどんな変異もこの golden を巻き込むので、
**変異事前登録の期待 node には常にこの pin test 群を含める。**

### test node 名を key にする登録簿 (追加調査)

`orchestrator/tests/conftest.py` には exact 集合の登録簿が複数ある
(`_REAL_REPO_NODE_INVENTORY`、`RECEIPT_MEMO_CONSUMER_NODES` は「34 関数 / 37 node」と
件数まで固定)。**対象 4 test file の node は 1 つもこれらに登録されていない**ため、
tmp_path 内で完結する新規テストを足す限り登録簿には触れない。
実 repo・共有 submodule・receipt memo を読むテストを書くと登録が要る — 書かないこと。

## 不変条件

- 規律 2 を緩めない。正しさゲートは強くなる方向にしか動かさない。
- 受理集合の変更は「選択規則を満たさない床値では 3 経路が拒否になる」方向のみ。
  正常系 (選択規則を満たす g1、および g2 以降) の受理は変えない
  (`assert_g1_floor_selection_identity` は `generation_number != 1` で素通りする)。
- D1241 / D1313 の advisory / non-certifying 上限を解除しない。
- 仮想リスク向けの gate・検査・台帳・一般化を足さない (DW-G05)。本題の実装だけ。
- テストを甘くして緑にしない。hash 再 pin は「実 file から再計算した値へ更新する」形にする。

## 割れうる前提 (攻撃対象)

- **(P1) `verify_manifest` に選択 token を要求させるか。**
  親の provisional 裁定: **要求させない。** 3 経路へ 1 行ずつ強制を入れる最小形にする。
  理由 — (i) D1526 の決定文が名指ししているのは report / verdict / judge の 3 経路であり、
  `verify_manifest` の signature 変更は本文に無い。(ii) token 化は `verify_manifest` の
  全呼び手 (production 5 か所 + test helper 多数) を巻き込み、変更面が本題より大きくなる。
  (iii) 迂回口の一般化は残件 (c) の主題であり、(a) の着地後と決まっている。
  **攻撃してよい点**: この裁定が D1526 の「防壁の非対称を残す」という理由と矛盾しないか。
  3 経路へ入れても `verify_manifest` を直接呼ぶ新しい consumer は素通りできる、という
  非対称が残るのではないか。残るとして、それは (c) の射程か本 wave の射程か。
- **(P2) verdict は `_GENERATOR_SOURCES` に含まれないので pin を動かさない**、という親の読み。
  `s8b_verdict.py` は 5 つの canonical path のどれでもない。攻撃点: verdict の bytes を
  束縛する別経路 (受領証・proof chain・事前登録) が本当に無いか。
- **(P3) 挿入位置は `load_ratified_freeze` の直後で、`reverify_published_freeze` の前**。
  攻撃点: 後段 (`verify_manifest` の後) に置くべき理由、あるいは
  `reverify_published_freeze` の内部へ入れるべき理由があるか。内部へ入れると
  D1503 が「被覆済みと数えるな」と決めた historical reverify の意味論を変えてしまわないか。

## 成果物の形

- コード: 上記 3 file に各 1 行の強制 + 例外 catch 節への型追加 (必要なら)。
- テスト: 3 経路それぞれに
  (a) 実体を名指しした負例 — 実 g1 で選択規則違反を作り、CLI が rc=2 で拒否し
      理由 (`floor-selection-rule-mismatch` 等) を保つこと。
      fixture は `test_s8b_ratified_freeze.build_production_emitter_g1` を使う (先例あり)。
  (b) 正例 — 選択規則を満たす場合に強制を通過して後段へ到達すること。
  (c) 呼び出し引数の照合 (`(ratified, root)` の順・object 同一性)。
  先例は `test_s8b_oracle_manifest.py:1485` / `:1499`。
- 再 pin: `PIN_GATE_SPEC_RAW` 内の report / judge の sha256 と `PIN_GATE_SPEC_SHA256`。
- docs: worklog 1 エントリ。decisions は D1526 の実装完了を worklog 側で示すのみ (新 D は立てない)。

## 並列分割方針

編集 path 所有が素集合になる 3 単位へ分ける。

- 単位 R: `orchestrator/campaign/s8b_oracle_report.py` + `orchestrator/tests/test_s8b_oracle_report.py`
- 単位 J: `orchestrator/campaign/s8b_oracle_judge.py` + `orchestrator/tests/test_s8b_oracle_judge.py`
- 単位 V: `orchestrator/campaign/s8b_verdict.py` + `orchestrator/tests/test_s8b_verdict.py`

`orchestrator/tests/test_s8b_oracle_manifest.py` の再 pin は R と J の両方の bytes に依存するため、
**R と J の完了後に親が別単位 P として 1 本だけ投入する** (同時所有を避ける)。

## 受入・実測環境

login node での全走 (`docs/worklog.md` の所在に従う)。新規の Pegasus 実行体は作らないので
計算ノード投入は不要。
