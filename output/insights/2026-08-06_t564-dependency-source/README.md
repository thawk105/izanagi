# [T-564] 依存 source の所在を home の外へ移す — 逐語と台帳

wave: `dev-wave-t564-dependency-source` / branch: `worktree-dev-wave-t564-dependency-source`

## 何をしたか

certification job が pin する gflags / glog の source tree が home 配下から消えており、
job は `gflags source path missing` で 11 秒 fail-closed していた。共有
`tools/pegasus/policy.json` の `gflags_source_path` / `glog_source_path` を
`/work/SFC/tanab/github/{gflags,glog}` へ移し、この 2 値を固定していた境界テストを
D96 の手続に従って同じ変更単位で追随させた。

## この wave が名乗らないこと

- certify の**完走**、accepted calibration の**取得**、較正の**活性化・登録**。
  それぞれ別の blocker を持つ (名乗りの段階表は `s6-ruling.md`)。
- 計算ノード可視性の**普遍命題**。実測は 1 job・1 host・1 時刻で、専有は確認していない。
- 「pin 閉包」の一般化。実測したのは**受入 test が観測した pin 閉包**であって、
  PBS job script・手動 CLI・production 経路の閉包ではない。

## 一次資料

| ファイル | 内容 |
|---|---|
| `s1-brief.md` | 段 1 brief と前提実測 (変異を当てた受入全走で赤 4 件を特定) |
| `s4-ruling.md` | 段 3 敵対 2 レンズ 10 所見の裁定、plan v2、変異事前登録 v1 |
| `s6-ruling.md` | 段 6 レビュー 2 本 8 所見の裁定、段 4 裁定の是正 5 件、変異事前登録 v2 |
| `mutation-spec.json` | 変異 spec (sha256 `a5474e1ad069537cb76458774ef858e951fbf2fccfbf238aba587a3aa6d30142`) |
| `mutation-ledger.json` | 変異本走の台帳 |

段 2 プラン、段 3 レンズ、段 5 / 段 6 の子報告、可視性 probe の生出力は repo 外の
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t564-dependency-source/` に置いた。

## 検知力の設計 — なぜこの形か

変更前、2 つの test はいずれも「凍結 evidence が記録した policy の sha256 == 現在の bytes」を
要求していた。これは **policy を正当に更新するたびに、過去の走行記録の側を書き換える圧力**を生む。
記録の書き換えは歴史の改竄なので採らない。

そこで検知の根拠を「凍結 evidence と一致」から「現行 bytes の明示 pin と一致」へ移した。
歴史値と現行値の 2 定数は `orchestrator/tests/pegasus_policy_expected_goldens.py` に 1 箇所だけ置き、
**2 つの test がそれぞれ単独で 3 条件を検査する。**

- 現行 `policy.json` の sha256 == 現行 oracle
- 凍結 binding == 歴史 oracle
- 凍結 binding != 現行 bytes

段 5 の最初の実装はこの 3 条件を 2 つの test で**分担**させており、単独 nodeid 実行では
検知力が後退していた。段 6 のレビュー A がこれを検出し、fix で各 test 自己完結型へ直した。
**検出力は「増加」ではなく「保存」である** — 変更前も変更後も policy の任意の byte 変更は赤になる。

現行 bytes の定数は、親が変更前 bytes から独立に算出して実装子へ与えた。
実装子が自分の書いたファイルから算出すると、誤った編集にも一致する自己成就 pin になるためである。
段 6 のレビュー A が `git show HEAD:tools/pegasus/policy.json` から独立再計算して一致を確認した。

## 変異台帳

anchor = merge commit `a6f6f37f`。harness = `tools/mutation_harness.py`、runner-mode = `dispatch`。
runner command:

```
python3 tools/run_tests.py orchestrator/tests/test_pegasus_tools.py \
  orchestrator/tests/test_silo_ladder_rung1_evidence.py \
  orchestrator/tests/test_t126_pegasus_tools.py -rf
```

**baseline PASSED、5/5 KILLED、期待 node と実測 node は全件完全一致。** erratum なし。

| ID | 変異 | 期待赤 node 数 | 結果 | 種別 |
|---|---|---|---|---|
| M1 | `expected_cpu_model` 行のコロン直後の空白を 1 → 2 (JSON の意味は不変) | 2 | KILLED | 現行 bytes pin の非空虚性。**単独で有効な負例** |
| M2 | `gflags_source_path` を旧 home path へ戻す | 3 | KILLED | **冗長 (3 層)**。path oracle の単独証拠には数えない |
| M3 | `glog_source_path` を旧 home path へ戻す | 3 | KILLED | **冗長 (3 層)**。同上 |
| M4 | 歴史 oracle 定数を現行 hash へ書き換える | 2 | KILLED | 歴史値が現行値へ流されたら赤くなることの証拠 |
| M5 | 現行 oracle 定数を旧 hash へ書き換える | 2 | KILLED | 現行 pin が実ファイルの bytes を見ていることの証拠 |

M1 の注入 anchor は `expected_cpu_model` 行に固定した。`"project": "SFC",` は policy.json 内に
2 箇所あり一意でないため anchor に使えない。M2 と M3 を**同時に**当てると policy.json が
元 bytes へ完全に戻り `!= 現行` も追加で落ちるが、harness では単独適用した。

段 4 で M1・M4 を「単一理由」と登録したが、段 6 の fix で両 test が独立に同じ性質を拒否する形へ
直したため、**この 2 件の期待赤は 2 node である**。これは冗長ではなく、fix の目的そのものである。
段 4 の「単一理由」という記載は段 6 裁定で撤回済み。

## 受入と検査

| 検査 | 結果 | request |
|---|---|---|
| 段 1 前提実測 (変異を当てた受入全走) | 4 failed / 6728 passed / 20 skipped | `892356.nqsv` |
| 計算ノード可視性 probe | bnode004 で 2 表記とも可視・HEAD 一致・porcelain 空 | `892394.nqsv` |
| 焦点 4 file (fix 後) | 311 passed | `892606.nqsv` |
| **受入全走 (tip `a6f6f37f`)** | **6774 passed / 20 skipped / 0 failed** (869.81s) | `892674.nqsv` |
| provenance 監査 (full history) | 1525 件・違反なし | `892617.nqsv` |
| 変異 matrix | baseline PASSED、5/5 KILLED | (harness 内で dispatch) |

## 裁定パッケージ (scope 外の real 所見、ユーザーへ返す)

1. **production の current/history binding 境界に直接テストが無い。** `validate_current_bindings` は
   凍結 evidence を現行 bytes と等値比較して拒否するが、その境界を固定する test が無い。
   段 6 のレビュー A が挙げた `test_collect_fixture_bundle_publishes_without_self_rejection` は
   production validator を monkeypatch しているため証拠にならない。`driver` binding が歴史値に
   なった時点から既に存在する状態で、本 wave の新規回帰ではない。
2. **`submit_certify.sh` の `--repo-root` と `PBS_O_WORKDIR` が分離しうる。** 別 directory から
   `--repo-root` を使うと、submitter が clean 検査した木と job が実行する木が食い違う。
3. **機体固有の絶対 path を repo へ書く結合そのものの除去。** 択一 (c) の verified hydrate は
   可搬性と [T-443]/[T-444] の source proof を同時に改善しうる。
4. **`submit_certify.sh` が scheduler 出力を repo 外へ向けない。** repo を submit directory に
   する job は `-o` / `-e` をファイル path で渡す規範が runbook にあるのに、この submitter は
   従っていない。放置すると job のたびに repo が dirty になり、次の submit と land を塞ぐ。
