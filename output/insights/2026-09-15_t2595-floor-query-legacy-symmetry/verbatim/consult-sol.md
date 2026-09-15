## 対称性の反例

以下、[A＝admission](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry/orchestrator/campaign/s8b_holdout_admission.py)、[C＝campaign](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry/orchestrator/campaign/s8b_floor_campaign.py)、[T＝既存テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2595-floor-query-legacy-symmetry/orchestrator/tests/test_s8b_holdout_admission.py) とする。

**real：修正後も query 全体と consume の受理集合は一致しない。**

再現入力 H1：`T:1825` の `_issued_cell` を起点とし、`c`、`p`、`s`、`r` はそこで得た cell、planned attempt、seq、round、`N=len(state.schedule)` とする。registry は不在。

```text
1. session-start: attempt_id=p, cell_id=c, seq=s,
                 round=r, kind=planned, trigger=null
2. session:       attempt_id=p, cell_id=c, seq=s,
                 round=r+1, kind=planned, valid=false
3. session-start: attempt_id=c::retry1, cell_id=c, seq=N,
                 round=r, kind=retry, retry_ordinal=1, trigger=p
```

- 修正後 query `(round_no=r)`：`A:5836` の完了行 round 検査で legacy 候補を落とし、`None`。
- consume の `_assert_retry_start_authorized_locked`：完了候補1件、recovery 0件。`A:5742–5746` は cell・kind・valid だけを検査し、round を見ないため受理する。
- 前段の start 検査もこの入力を拒否しない。完了行はその検査対象外（`A:4313–4316`、`s8b_floor_contract.py:234–274`）。

これは**既存の逆向き非対称**であり、今回の追加チェックが生む退行ではない。

**refuted：提案ブロックを通って legacy 認可を返した同一履歴を、指定の consume gate が拒否する反例。**

同じ state・records・trigger では反例なし。query が返却に到達すれば、完了候補は1件かつ canonical、追加 helper の recovery 候補は0件となり、`A:5765–5777` の legacy 受理条件を満たす。重複完了、座標破損 recovery、使用済み trigger、registry 不在を照合した。これは consume API 全体の券消費済み検査まで一致するという意味ではない。

## 例外か None か

比較対象 H2 は plan の負例そのものとする。

```text
journal:
  planned start P
  → canonical failed planned completion P
  → retry1 start(trigger=P)

registry:
  genesis
  → start S（P の slot、event_sha256=h）
  → recovery（同じ slot、start_event_sha256=h、
              receipt.target_start_event_sha256=h）
```

registry の完全な行は `T:1900–1997` の helper、journal は `T:3522–3533` で構成できる。

| query の処置 | 呼び手の扱い |
|---|---|
| 例外 | `C:6182–6185` が `CampaignAbort` に変換。runner まで到達していれば `C:7955–7961` が `terminal(status=aborted)` を記録 |
| `None` | `C:6190` がキャッシュし、`C:6170` が failed cells から除外。retry を作らず先へ進む |
| legacy 候補を落として探索継続 | H2 では他候補がなく `None` と同じ。他候補があればその認可で進むため、検出した両根拠の不整合を拒否として伝えない |

**refuted：例外を採ること自体が誤り。** 異常履歴を検出したという意味を保存する処置として整合する。

**real：P1 の「試行不足のまま finalize」という説明は、H2 の実経路を正しく表していない。**

まず通常の resume は、後述の cut-6 検査で query より先に拒否される。仮に query の呼び手まで H2 を届けて `None` を返しても、最終 inspection は既存 retry1 を `A:6645–6652` で再検査し、両根拠を拒否する。`C:7963–7983` は `artifact-invalid` とする。**H2 がそのまま正常完了する根拠にはならない。** P1 の例外選択は支持できるが、理由は修正が必要。

## 新しい赤の検査

helper とその呼出し先の例外条件は次のとおり。正常な内部 state を前提とし、資源枯渇などの一般的な実行環境例外は除く。

| 条件 | 現物 |
|---|---|
| freeze SHA が非文字列・空・非 canonical SHA | `A:5364` → `A:580–589` |
| registry layout が絶対パスまたは `..` を含む | `A:5367–5368` |
| 親パスの検査不能、symlink、途中の非 directory | `A:5373` → `A:1272–1295` |
| registry の stat/read 失敗、非 regular file、symlink | `A:5375–5385` |
| 空ファイル、サイズ超過、末尾改行欠落、空行 | `A:5386–5391` |
| UTF-8/JSON 不正、重複キー、NaN/Infinity 定数、非 object | `A:5392` → `A:785–805` |
| canonical JSON bytes との不一致 | `A:5393–5394` |
| JSON 再符号化不能 | `attempt_registry_core.py:222–231`。例：数値 `1e999` は復号後に無限大となり canonical 化で拒否 |
| hash 照合対象が list/dict | `A:5485–5486` の集合 membership が `TypeError`。例：canonical 行 `{"event":"recovery","start_event_sha256":[]}` |

authority、独立 receipt、registry replay、consume marker の検証は、この候補収集 helper 自体では実行しない。

**refuted：追加 helper の例外によって、同じ履歴を consume なら受理する新しい赤が生じる。反例なし。**

consume は `A:5759–5761` で、同じ helper を canonical 判定より先に無条件で呼ぶ。helper が例外になる同一入力を consume が受理する経路はない。

また H2 では、既存 query も未使用の `retry1` を対象として `A:5853` から registry 全体を読む。したがって framing/JSON 不正は追加ブロックより前から拒否される。

**real：事実6の「slot identity 不明なら空で返る」は無条件には成立しない。** `A:5454` の registry 読取が identity 判定に先行する。例えば `records=[]`、未知 trigger、registry がゼロバイトなら、空候補ではなく framing 例外になる。ただしこれは既存挙動であり、今回の I1/I3 違反ではない。

## 母集合の絞り込み (F593)

**refuted：提案が consume より狭い recovery 母集合を数える。**

両者は同じ `A:5450` の helper を使う。母集合は `A:5471–5495` の次の条件で一致する。

```text
event == recovery
かつ
  対象 slot の座標を主張する
  または start_event_sha256 が対象 start hash を指す
  または receipt の target_start_event_sha256 が対象 start hash を指す
```

座標だけを壊しても hash が残れば候補から落ちない。plan の `corrupt-one` と `valid-plus-corrupt` はこれに該当する。

「registry 全行に比べれば絞っている」は事実だが、**consume も同じ絞り込みをする**。提案による母集合差で通る履歴は見つからなかった。完了側も `A:5826–5832` が同じ trigger の全完了を数えてから canonical 判定する。

## 時点依存の述語 (F590)

**refuted：今回の追加条件が F590 型の「後続 retry が増えると過去の正当な認可が失効する」述語を新設する。**

legacy trigger は planned slot なので ordinal は常に0（`A:5416–5426`）。後続 retry start が増えても、この slot identity は変わらない。追加条件に「最新」「未使用」「現在の retry ordinal」は含まれない。

registry 自体を後から変更すれば候補非空の真偽は変わる。例えば registry 不在の H2 相当履歴で認可後、P を指す recovery を追加すれば、後の consume/inspection は拒否する。しかし後の履歴は両根拠を含むため、既存 XOR 規則による正しい拒否である。

既存の最新性検査は `A:5713` の `authorizing_new_start` で分岐し、inspection は `False` を渡す（`A:6647`）。提案はこの境界を変更しない。

## 親 brief の誤り

**最大の real 所見は、事実4と成果物影響の production 到達説明。**

H2 を未完了 round の resume journal に置くと、実経路は次になる。

```text
C:6593–6594  既存 retry1 の _replay_cut6_start
→ C:6432     floor_attempt_requires_cut6_replay
→ A:5341     _assert_attempt_authorized_by_journal
→ A:4342     _assert_retry_start_authorized_locked
→ A:5765     両根拠で拒否
→ C:6435     CampaignAbort
```

`C:6595` の `_retry_round` と本件 query に到達しない。plan:10 は、この直前の検査を経路説明から落としている。

| brief の項目 | 判定 |
|---|---|
| 事実1 | **確認**。H2 の直接 query は修正前に legacy を返す。他の異常・候補がないという限定が必要 |
| 事実2 | **確認**。H2 の consume は XOR 件数で拒否 |
| 事実3 | **確認**。逆方向チェックは `A:5866–5869` に存在 |
| 事実4 | **real：結論が誤り**。キャッシュは存在するが、H2 の通常 resume は query 前に拒否 |
| 事実5 | **確認、表現を限定**。`C:6412–6424` は同じ trigger で複数 retry を行う。ただし「枠を使い切るまで」には「有効な session が得られるまで」という停止条件もある |
| 事実6 | **real：早期 return の前提省略**。registry 読取成功が必要。前節参照 |
| 事実7 | **bytes pin 発見なし。ただし hit 列挙は不完全**。下記参照 |

**real：brief:10、16–18 の「測定1本空費→artifact-invalid」も不正確。**

仮に H2 に対する query 認可を使って retry2 start を作っても、`C:5998–6004` は測定 callback の**前**に consume し、拒否を `CampaignAbort` にする。callback は `C:6007–6012`。通常 resume では、さらに前述の cut-6 検査が拒否する。

**pin 閉包の検算：** path・記号検索に加え、`tools`、`hooks`、`.codex` と live な source 検査を確認した。brief が挙げていない以下の参照がある。

- `tools/check_docs.py:1843`：R33 source contract 検査。
- `T` とは別の `test_s8b_attempt_registry.py:2276–2284`：production source の adapter import 検査。
- `test_ccbench_spawn_sites.py:248`：`_run_git` の起動箇所数契約。

いずれも提案ブロックの bytes pin ではない。duration ledger の未知 test は `tools/acceptance_shards.py:397–404` で1秒を使うことを確認した。**「検索した範囲に変更を妨げる live bytes pin はない」は支持できるが、列挙だけで完全閉包を証明したとはいえない。**

不変条件は、**I1 の consume 不変更、I2、I3、I4、I5、I6 は提案内容と整合**する。ただし I1 を「全履歴の query/consume 判定一致」と読むなら H1 が反例。実装・テスト追加は未実施なので、保持の実測確認ではない。

## 変異の帰属

**refuted：登録4変異が別の既存 gate に先取りされ、指名テストへの帰属が成立しない。** 静的には全4件で成立する。

| 変異 | 指名入力と失敗理由 |
|---|---|
| `OMIT` | テスト1全ケース。P は使用済みなので既存 recovery ループで除外。追加判定を無効化すると legacy を返し、`pytest.raises` が失敗 |
| `MULTIPLE-ONLY` | `valid-one`、`corrupt-one`。候補数1なので変異条件が偽となり、同じく例外未発生 |
| `SINGLE-ONLY` | `valid-plus-corrupt`。候補数2なので変異条件が偽となり、同じく例外未発生 |
| `EMPTY-REJECT` | registry 不在のテスト2・3。空 tuple は `None` ではないため、正常な legacy query が例外になる |

テスト1で registry を読む未使用 start は retry1 だが、その slot ordinal は1。registry は P の ordinal 0を指すので、この段階の候補は0件（`A:5427–5441`、`A:5463–5495`）。したがって既存 `A:5860` の多重性検査も、authority/replay 検査も先取りしない。

注意点として、`EMPTY-REJECT` はテスト3の**fresh 側の初回 query**で落ちる。変異への帰属は成立するが、その kill 単独で resume 到達を証明するわけではない。変異実走はしていない。

## 裁定パッケージ候補 (scope 外の real 所見)

1. **legacy 完了の round 不整合を consume が受理する既存境界差。** 入力 H1、根拠 `A:5742–5746` 対 `A:5836`。今回の局所修正には混ぜない。
2. **registry の不正な hash 型が admission 例外に変換されず流出する既存挙動。** 正常な planned start に対し、registry を canonical な `{"event":"recovery","start_event_sha256":[]}` 行にすると `A:5485` で `TypeError`。`C:6182` はこれを捕捉しない。consume と共有する既存問題であり、今回の新しい赤ではない。

## 総括

**局所チェックの正しさ、F593 の母集合一致、4変異の帰属は静的に支持できる。consume が受理する履歴を新たに拒否する反例はない。**

一方、**親 brief の production resume 到達説明と「測定を空費して artifact-invalid」という影響説明は現物に反する**。また、全履歴での query/consume 対称性は達成されない。今回の主張は H2 の直接 query にある既存非対称の解消に限定すべきである。

ファイル変更、commit、pytest、変異実走は行っていない。