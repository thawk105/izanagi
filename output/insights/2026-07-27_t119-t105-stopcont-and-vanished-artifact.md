# [T-119] + [T-105] 全走 flake の根を本番で塞ぎ、消失 artifact を fail-closed にした (2026-07-27)

[T-117] (2026-07-27) の続き。前 wave が「全走 flake 1 走 1〜2 件の単一の根」と特定しながら
本番接触の制約で保留していた SIGSTOP/SIGCONT 競合を、ユーザー裁定 (2026-07-27、`tools/dev_waves/`
は床値測定の対象系ではないので制約の射程外) を受けて修正した。同じ裁定で [T-105] の
`FileNotFoundError` 素通しも同 wave に入れた。

一次資料: 窓の実測 = job 871785 (bnode010, gen_S)、受入全走 = job 871787。
変異台帳 = `2026-07-27_t119-t105-stopcont-and-vanished-artifact-mutation-ledger.json`。
先行記録 = `output/insights/2026-07-27_t117-loadgroup-and-stopcont-race.md`。

## 1. [T-119] 窓は実在し、負荷でだけ開く

`_preexec` は `os.closerange` で exec-error pipe を閉じてから自分に `SIGSTOP` を送る。親の
`Popen` は pipe が閉じた時点で返るので、**親は子が停止する前に走り得る**。その窓で送った
SIGCONT は取り消すべき停止がまだ無いため捨てられ、子は per-wave 締切まで停止したまま
1 byte も出さずに kill される。

窓の開き方を計算ノードで実測した (probe は本番非改変。実 `_spawn_stopped` を呼び、`Popen` が
返った直後の `/proc/<pid>/stat` の state を採る)。

| 条件 | 窓が開いた割合 | 停止までの実待ち (最大) |
|---|---|---|
| 無負荷、逐次 300 回 | 0 / 300 (0%) | — |
| 16 並列 probe、burner なし、960 回 | 0 / 960 (0%) | — |
| 逐次 + CPU burner 96 本、300 回 | **10 / 300 (3.3%)** | 314 us |
| 16 並列 probe + burner 48 本、960 回 | **102 / 960 (10.6%)** | 860 us |

**窓は CPU 過剰予約でだけ開く。** これは全走 `-n 16..48` がノードに掛ける負荷そのもので、
「無負荷の単独再走では再現しないのに全走では 1 走 1〜2 件出る」という [T-057] 以来の
flake の性質を説明する。実待ちは最大 860 us で、導入した 5 秒上限の 5800 分の 1 である。

### 修正

`_signal_cont_verified` は、`/proc/<pid>/stat` の state が `T` になるのを有界に待ってから
CONT を送る。既に終了 (`Z`/`X`) していれば signal せず既存の exit 経路へ流す。上限超過は
`AMBIGUOUS_RECOVERY` (kind=`stop-handshake-timeout`) で fail-closed。

あわせて `_proc_stat` を `(state, pgid, start_ticks)` の 3-tuple にし、state と identity を
**1 回の `/proc` 読み**から取るようにした。2 回に分けると、その間に PID が再利用された場合に
他プロセスの state を子のものとして読み得る。`_identity_matches` は新しい `_verified_state`
の薄い述語になり、判定内容 (boot_id + start_ticks + pgid) は変えていない。

締切を伸ばして flake を隠す変更は行っていない。`ReasonCode` の新設もしていない。

## 2. [T-105] 消失 artifact — 一律 fail-closed にはしなかった

`_run_artifact_bytes` は `os.walk` の列挙後に各 entry を `lstat` する。ledger スレッドが
`status.json` / `summary.md` を書き換えるとき `<name>.tmp.<pid>.<tid>` を作って `os.replace`
するので、列挙と `lstat` の間に scratch が消えると素の `FileNotFoundError` が
`DevWavesError` にならずに逃げていた。

本番非改変 probe (実 `Supervisor._run_artifact_bytes` を stub layout へ束縛し、ledger と同型の
churn を並走) で確定した。

| tree | 10 秒あたりの正常 walk | 素の `FileNotFoundError` | typed `DevWavesError` |
|---|---|---|---|
| 修正前 (7770463) | 14,184 | **17,142** | 0 |
| 修正後、実 ledger 名の scratch が消える | 24,994 | 0 | 0 |
| 修正後、認識外の名前が消える | 17,290 | 0 | **7,528** |

**「fail-closed」を一律 raise にはしなかった。** rewrite scratch の消失は設計上必ず起きる良性の
競合で、それを run 失敗に変えると flake の形が変わるだけになる。代わりに ledger 側へ writer と
対になる recognizer (`cache_transient_name` / `is_cache_transient_name`) を置き、
**認識できた scratch だけを 0 byte として飛ばす**。run 配下の他の artifact はすべて create-only
(`O_CREAT|O_EXCL`、rename も unlink も無い) なので、消えたら改竄か欠陥であり fail-closed が正しい。

writer 側は `CACHED_NAMES` 以外を渡されたら `ValueError` で止まる。writer と recognizer が
同じ閉集合を見るので、片方だけに名前が増えて drift することができない。

`os.walk` / rename / unlink を `tools/dev_waves/` 全体で棚卸しし、run dir 内で消え得るのは
ledger の scratch だけであることを確認した (`ledger.py` の 2 箇所の `os.unlink` はどちらも
その scratch、`daemon.py` の `_atomic_json` は**未使用のデッドコード**で呼び出し 0 件、
`protocol.py` の socket unlink は run dir 外)。

## 3. 変異 matrix — 生存 2 件はどちらも既存の被覆漏れだった

10 変異を事前登録して走らせ、8 件が kill、2 件が生存した。生存 2 件は本 wave が持ち込んだ
退行ではなく、既存の被覆漏れである。DW-M02 に従って実効 gate へ再照準し、再走で両方 kill した。

| # | 変異 | 初回 | 再照準後 |
|---|---|---|---|
| M1 | 停止観測なしで CONT (= 修正前の本番) | KILLED | — |
| M2 | 待ちの有界性を外す | KILLED-BY-HANG | — |
| M3 | 停止判定を恒真にする | KILLED (2 node) | — |
| M4 | `start_ticks` 検査を外す | KILLED (2 node) | — |
| M5 | **pgid 束縛を外す** | **SURVIVED** | KILLED |
| M6 | 良性 scratch も run 失敗にする | KILLED | — |
| M7 | 消失をすべて黙って飛ばす | KILLED (2 node) | — |
| M8 | recognizer が base 名を見ない (ledger 側) | KILLED | — |
| M8b | **同変異を consumer 側から撃つ** | **SURVIVED** | KILLED |
| M9 | writer の閉集合 guard を外す | KILLED | — |

- **M5**: 子が自分の process group の leader であることを撃つテストが 1 本も無かった。
  この束縛が無いと記録した PID が他人の PGID を兼ね、resume も terminate も無関係な group へ飛ぶ。
  group を継承しただけの子に対して 3 つの経路がすべて拒否することを撃つ node を足した。
- **M8b**: fail-closed 側の subcase が `status.json` / `events.jsonl` / `durable-artifact.json`
  の 3 つで、いずれも `<base>.tmp.<pid>.<tid>` の形を**していない**。だから「形だけで一致する」
  recognizer でも挙動が変わらず、consumer 側からは穴が見えなかった。
  **教訓 = 判別述語の変異は、判別が実際に分岐する入力を consumer 側の subcase に持たせないと
  撃てない。** 書き換えない base に scratch の接尾辞を着せた名前を subcase へ足して塞いだ。

### harness の誤記録 (erratum)

初回走の verdict 欄は**全件 SURVIVED と誤って記録された**。harness が事前登録の bare 名
(`test_foo`) と、DW-M08 が要求する `file::name` 形式の節点 ID を直接突き合わせていたためで、
集合の積が常に空になっていた。**節点一覧 (一次証拠) は正しく記録されていた**ので、
再測定はせず節点一覧から verdict を再計算した。台帳には初回値
(`verdict_as_first_recorded`) と訂正値の両方を残している。

## 4. 検出力 — 新テストを修正前の本番へ当てた結果

新テストを変更前 HEAD (7770463) の本番へ当てて、何が実際に検出できるかを確認した。

- `test_cont_waits_for_the_child_to_be_observed_stopped` → **`ReasonCode.TIMEOUT` で赤**。
  これは [T-117] が記録した flake の形そのもの (子が 0 byte のまま締切で kill される) であり、
  診断文字列ではなく受理集合の差で落ちている。
- `test_vanished_rewrite_scratch_is_skipped_but_lost_artifact_fails_closed` と
  `test_capacity_gate_stays_closed_when_an_artifact_vanishes_mid_measure` → **素の
  `FileNotFoundError` で赤**。欠陥そのもので落ちている。
- 新規の白箱テスト 5 本 (`_verified_state` / `_await_stopped_child` を直接呼ぶもの) は
  旧版に該当シンボルが無く `AttributeError` になる。**構造束縛であって検出力の証拠ではない**
  ので、そう明記して数えない。

## 5. 受入 — flake は 4 走連続で出なかった

job 871787 (bnode001, gen_S 48 core、単独性はノード上で確認)。HEAD = 824f04e。

| 走 | 並列度 | 結果 | wall |
|---|---|---|---|
| 1 | `-n 16` | 3081 passed / 19 skipped / **0 failed** | 71.6s |
| 2 | `-n 16` | 3081 passed / 19 skipped / **0 failed** | 71.5s |
| 3 | `-n 16` | 3081 passed / 19 skipped / **0 failed** | 71.3s |
| 4 | `-n 48` | 3081 passed / 19 skipped / **0 failed** | 73.7s |

[T-117] 時点は 1 走あたり 1〜2 件の赤が出ていた。**4 走連続で 0 件**である。

**wall は 69 → 72 秒へ 3 秒伸びた。これは本 wave が足したテストの費用であり、本番の低下ではない。**
新しい integration test 2 本は `test_dev_waves_integration.py` の**ファイル単位 group** に入り、
[T-117] が「現 wall の正体」と特定した直列 67.2 秒の鎖をそのまま延ばす。worker 側の control 2 本も
窓を決定的に開くため合計 1.2 秒の意図的な sleep を持つ。**この 3 秒は [T-120] (group 分割) が
そのまま回収する対象**であり、[T-120] の優先度をむしろ上げる。

## 6. 次の lever

1. **[T-120]**: `dev-waves-integration` の file 単位 group を分割する (直列 67.2 秒 = 現 wall の
   正体)。分割は子 spawn の同時数を増やすが、その発火確率を上げていた [T-119] は本 wave で
   閉じたので順序の前提が満たされた。
2. **[T-121]**: real-repo group の reader/writer 分離。[T-120] の実測後に再判断 (裁定済み)。
3. **[T-122]**: `verify_receipt` の `search_repository` 重複 (4.5 秒)。測定後 (裁定済み)。
4. **`daemon.py` の `_atomic_json` は呼び出し 0 件のデッドコード**。削除の可否は衛生項目として
   別途 (本 wave の scope 外なので触っていない)。
