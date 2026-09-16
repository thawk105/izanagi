## 総括

30 件を `pending` で記帳し、各 OID を直接指す救出 ref の作成・到達性再検査後、全件を `rescued` に更新する案を採る。  
内容一致は 16 commit／37 path で確認できるが、それ自体を人間の個別の喪失受容とは扱わない。  
台帳の変更は現在の 116 行目を 30 本の単一行 JSON に置換するだけとし、契約・実装・テスト期待値は変更しない。  
最大の risk は、30 本の ref が対象 commit の祖先・tree・blob も保持し、台帳 commit とは別に維持されることである。  
指定資料の静的照合のみ実施した。書き込み、ref 作成、pytest 実走は行っていない。

## 1. 台帳追記の形 (file:line)

[docs/unreachable-object-ledger.md:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2640-unreachable-ledger/docs/unreachable-object-ledger.md:116) の `現在、記録済み entry はない。` を削除し、後掲表の OID 順に 30 行を置く。現在の 1〜115 行はそのまま保持する。更新後の entry は 116〜145 行となる。

各行は、次の式で生成する**完全な JSON object**とする。

```python
"- " + json.dumps(entry, ensure_ascii=False, separators=(",", ":")) + "\n"
```

26 field は schema 表の順で構築する。説明文・見出し・コードフェンスを entry 間へ挿入しない。判断理由は `resolution_note`、詳細な根拠は insight README に置く。

整合する根拠は以下。

| 根拠箇所 | 守る条件 |
|---|---|
| `tools/check_branch_rescue.py:1762` | parser は節の範囲によらず全文の `- ` 行を読む。全追加行を `- {` で始める。 |
| 同 `:1677` | 26 field の追加・欠落なし。 |
| 同 `:1640`、`:1780` | JSON key、`entry_id`、`object_oid` の重複なし。 |
| 同 `:1730` | 初回は `pending`、解決 3 field は null。救出確認後、同じ entry を更新する。 |
| `orchestrator/tests/test_branch_rescue_ledger.py:187` | schema 表と field 順は変更しない。 |
| 同 `:199`、`:330`、`:337` | 状態遷移・stale・rc・retention・除外範囲の散文を変更しない。 |
| 同 `:257`、`:291` | `rescued` に日時・full refname・非空 note を揃える。 |
| `orchestrator/tests/test_check_branch_rescue.py:848` | 救出後に audit が再報告した場合は stale として扱う。期待値を変更しない。 |
| 同 `:1484` | sample threshold を実効 `gc.auto` から導く。 |

`pending` の中間状態と最終状態は job 側の証拠へ残し、repo に commit する台帳は解決済みの 30 行とする。これにより台帳 `:48` の初期状態と `:50` の遷移を実際に踏む。

## 2. 26 field の決め方 (表)

以下の `R` は [tools/check_branch_rescue.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2640-unreachable-ledger/tools/check_branch_rescue.py)、`T` は親が**救出前に取得する評価時刻 UTC**を指す。

**既存の `--ledger-check` JSON だけでは field は埋まらない。** 提供資料では `gc=null`、閉包は空である。候補なしの CLI は個別 retention／landed assessment を実行しない（`R:2007`、`:2100`）。架空の削除候補を作らず、親の job 内の一回限りの収集コードから既存関数を利用する。

| # | field | 値の決め方・実装との対応 |
|---:|---|---|
| 1 | `schema` | 固定値 `izanagi-unreachable-object-ledger-v1`。 |
| 2 | `entry_id` | `t2640-<40桁OID>`。30 件で一意。 |
| 3 | `recorded_at` | 実際に初回記帳した UTC 時刻を `R:150` の `_utc_text` と同じ形式で保存。過去の削除日時を推定しない。 |
| 4 | `source_refs` | `[]`。監査由来で削除起点 ref は不明。救出 ref や推定 branch を入れない。`R:1716` は空配列を許す。 |
| 5 | `source_tips` | `{}`。対応する削除前 tip の観測がないため。`R:1718` は空 object を許す。 |
| 6 | `assessment_report_sha256` | **当該 OID の landed checker stdout 生 bytes 全体**の SHA-256。末尾改行を含める。`R:1629` の `hashlib.sha256(result.stdout).hexdigest()` と同一。audit の hash、再整形した JSON の hash は使わない。 |
| 7 | `object_oid` | `findings.json`、audit、ledger-check の共通集合の full OID。集合一致を確認して転記。 |
| 8 | `object_type` | `commit`。`_cat_types`／`_retention` の `cat_file_type` で各件を再確認する。 |
| 9 | `assessment_schema` | 当該 stdout の schema を確認し、`izanagi-branch-landed-v1`。`R:1598`。 |
| 10 | `assessment_verdict` | 各 OID の実測 `decision.verdict`。既報は `indeterminate` だが、4 件の観測を残りへコピーしない。内容照合から `landed` を作らない。 |
| 11 | `assessment_reason` | `str(decision.get("reason", ""))` を転記（`R:1624`）。既報は `assessment-timeout`。issue の文章と混同しない。 |
| 12 | `storage_kind` | `_retention(...)[0]["storage_kind"]` を転記。`R:1377` の優先順位は loose-and-packed → loose → local packed → alternate → missing → indeterminate。loose 不在だけで packed と断定しない。 |
| 13 | `object_mtime` | retention の `loose_mtime` を転記。packed-only は null。`pack_mtime_observed`、author date、commit date は入れない（`R:1390`、`:1475`）。 |
| 14 | `loss_possible_not_before` | retention の同名値をそのまま転記。loose＋相対期限は `max(T, loose_mtime + span)`（`R:1425`）、packed は `T`（`:1435`）。さらに観測された usable temporary roots の下界と max を取る（`:1462`）。 |
| 15 | `lower_bound_basis` | retention の同名文字列をそのまま転記。通常 loose は `loose-object-mtime-plus-prune-expire`、packed は `assessment-time-conservative-floor`。temporary root による下界延長後も実装はこの文字列を変更しない。 |
| 16 | `gc_auto_threshold` | `_gc_observation` が `_parse_integer_config(config["gc_auto"])` で読む実効値。既報は 6700。設定の未指定を null としない（`R:842`）。 |
| 17 | `gc_auto_sample_fanout` | `gc.auto_trigger.sample_fanout`、固定 `"17"`。 |
| 18 | `gc_auto_sample_count` | `gc.auto_trigger.sample_entry_count`。`objects/17` の全 directory entry 数（`R:1289`）。既報 18 は当時の観測であり、再収集値へ置き換える。 |
| 19 | `gc_auto_sample_threshold` | `gc.auto_trigger.threshold`。6700 なら 27。今回の正の設定では `ceil(auto/256)` と validator の `(auto+255)//256` が一致する（`R:1293`、`:1705`）。 |
| 20 | `gc_auto_heuristic_version` | `gc.auto_trigger.heuristic`＝`git-2.34.1-fanout-17-sample`。実行 Git の version 一致も証拠へ残す。 |
| 21 | `loose_count_at_loss` | **null**。今回、到達不能になった時点の総 loose 数は未観測。`R:1330` は現在の `count_objects["count"]` を返すだけで過去値を計算しない。現在の総数は観測日時付きで別の証拠へ保存し、fanout 数 18 や対象数 30 を代入しない。 |
| 22 | `status` | 初回 `pending`、§4 成功後 `rescued`。後掲 30 行は目標とする最終状態。 |
| 23 | `resolved_at` | 個別 ref の到達性確認成功後の UTC 時刻。初回は null。 |
| 24 | `rescue_ref` | `refs/rescue/t2640/<40桁OID>`。初回は null。 |
| 25 | `resolution_note` | 初回 null。解決時は監査由来・削除元不明、照合結果と証拠所在、作成 ref、到達性確認結果、喪失時 loose 数不明を具体的に記す。 |
| 26 | `object_retention_provided` | 常に `false`。ref が保持を提供しても台帳自体は提供しない。 |

収集コードは `R:840` の config、`:856` の snapshot、`:1343` の pack index、`:1281` の GC、`:1367` の retention を再利用する。snapshot は削除候補なしで取得し、実測された `temporary_roots` と alternates を渡す。便宜的な空リストで下界を短縮しない。分類・stat・config の失敗を正常値で埋めない。

landed checker は各 OID について次の形で起動し、stdout・stderr・rc を別々に保存する。

```bash
python3 tools/check_branch_landed.py --repo "$repo" --timeout-seconds 300 "$oid"
```

`R:1592`〜`:1618` と同じ schema、対象 OID、rc/verdict、conclusive、authorization の整合を確認する。外側の timeout 等で有効な stdout が得られなければ hash を捏造しない。`COMMAND_TIMEOUT_SECONDS = 5.0` は変更しない。

**loose 4 件の算術訂正：**

| OID 接頭辞 | `object_mtime` | mtime＋2週間 |
|---|---|---|
| `1d41c417` | `2026-09-09T04:23:58Z` | `2026-09-23T04:23:58Z` |
| `54d4dd9b` | `2026-09-09T04:28:58Z` | `2026-09-23T04:28:58Z` |
| `c656d831` | `2026-09-09T04:28:53Z` | `2026-09-23T04:28:53Z` |
| `f181f703` | `2026-09-09T04:24:06Z` | `2026-09-23T04:24:06Z` |

これは `evidence.json` の epoch 秒からの換算である。再観測でも pure loose、設定が 2 週間、temporary root による延長なしなら、この値と `T` の大きい方が下界になる。

## 3. 30 件の status 表 (oid / status / 根拠 1 行)

根拠の `C:行番号` は [content-match.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2640-unreachable-ledger/content-match.json) の該当 OID 行を示す。「一致」は**audit が報告した path**の範囲であり、commit 全体の着地証明ではない。

一致 16 件も、個別の喪失受容へ読み替えず commit を保存する。追加承認を待つ手順は設けず、授権された救出を選ぶ。

| oid | status | 根拠 1 行 |
|---|---|---|
| `0b92c254b830bc333386eacafdc5d113292116be` | `rescued` | C:100：T1348 spec 1/1 が gzip 展開後一致。元 commit も保存する。 |
| `0decf0a4eae5be07e59961e1d9fc735b42bae962` | `rescued` | C:202：T1348 spec 1/1 が gzip 展開後一致。元 commit も保存する。 |
| `1aa5ae77aa862ea68f5a5509ee748bd26ce18dab` | `rescued` | C:213：T812 spec の同一内容が見つからない。 |
| `1d41c41714b66ecb54eb23d52602fb7f8170602a` | `rescued` | C:1026：中断 wave README の同一内容が見つからない。 |
| `2620635f74883f6162a4838b547344c3d8695b1c` | `rescued` | C:1059：T1262 result 1/1 が gzip 展開後一致。元 commit も保存する。 |
| `2ba0ade14cdd253c53135ec24e8a6d1783d2a1fd` | `rescued` | C:1128,1333,1615：T1348 の 3/3 が gzip 展開後一致。元 commit も保存する。 |
| `2f5b2c1773e9f193417dd3c42fc2aba52b30c8c7` | `rescued` | C:1717：T1348 spec 1/1 が gzip 展開後一致。元 commit も保存する。 |
| `3905db91ed815d051e0916f12144e01934431d0a` | `rescued` | C:1786,1991,2273：T1348 の 3/3 が gzip 展開後一致。元 commit も保存する。 |
| `3ea6ed7428605ce73ce5e05121fc74d5985146f1` | `rescued` | C:2291：T1798 acceptance receipt の同一内容が見つからない。 |
| `4a62da8c3c3302d0e11a5cf951736e8be10e68b3` | `rescued` | C:2305,2318,2332：T1155/T1178 の 3/3 が gzip 展開後一致。元 commit も保存する。 |
| `4c2b4805915416a8ca8ce520a20e220b391ea176` | `rescued` | C:2401,2606,2708,2990：T1250 の 4/4 が gzip 展開後一致。元 commit も保存する。 |
| `54d4dd9b3eb270307e6294b9ac9b1484f7ba868f` | `rescued` | C:3803：T2487 中断 README の同一内容が見つからない。 |
| `5b3ff770ddf2de1d7df528596636c1abcfd3d55b` | `rescued` | C:3812：handoff blob `64281f…` が未保全。吸収済みとする証拠もない。 |
| `66dccb28fedca606f96dcf9baf5c7f7a6979a599` | `rescued` | C:4017：T190 ledger 1/1 が gzip 展開後一致。元 commit も保存する。 |
| `6902920cdf39e03e1fdfcbc3e6dc18e31a564918` | `rescued` | C:4222：T1109 ledger 1/1 が gzip 展開後一致。元 commit も保存する。 |
| `75d55ccd8d192203b0f04b3fa46130735edb967b` | `rescued` | C:4233：T2265 の `verbatim/analyze.py` が未保全。実行せず保存する。 |
| `8c2e4e3f8ed8a7925072a5b9a381a5ee9257c8b5` | `rescued` | C:4242：handoff blob `a83bfd…` が未保全。 |
| `aab5adbbcb599a72a9355e060ec32e825028298a` | `rescued` | C:4311,4516,4798：T1348 の 3/3 が gzip 展開後一致。元 commit も保存する。 |
| `accabf0b5d9e9cf3e8ec33008a92c8f41a158787` | `rescued` | C:4816,4914：T930 の 2/2 が gzip 展開後一致。元 commit も保存する。 |
| `c0439777fcf27a56605821d206519d4efa6487e5` | `rescued` | C:4923：handoff blob `8c44a8…` が未保全。 |
| `c3e2218c383e8c6a47ae2343fe78e558241d4e01` | `rescued` | C:4934：T812 の別版 spec が未保全。 |
| `c5d79e7050fecc229fd81f4879137be8bae49cb7` | `rescued` | C:4948,5153,5435：T657 の 3/3 が gzip 展開後一致。元 commit も保存する。 |
| `c656d831e30ee0c261538889991af6c30bb45e89` | `rescued` | C:6248,6257,6266：lock audit の README・TSV・snapshot 全 3 件が未保全。 |
| `c7a57d642fe72ce5c5480b761515054ac7817e63` | `rescued` | C:6275：handoff blob は他対象と重複するが、main では未保全。 |
| `cb0d930525930aef2e2d78ec420a5a386d3e63c7` | `rescued` | C:6284：handoff blob は他対象と重複するが、main では未保全。 |
| `cbd9d812141f5010ba90403c513a7dbad8cc7edc` | `rescued` | C:6317,6599：T1379 の 2/2 が gzip 展開後一致。元 commit も保存する。 |
| `cd066a0487af0376fac76bcfb58b2c4462f9085d` | `rescued` | C:6613〜6715：T1086 の 7/7 が gzip 展開後一致。元 commit も保存する。 |
| `e0a80472fb37255903fd1a658a553369d8ba1a76` | `rescued` | C:6996：T1262 spec が未保全。result の一致では代替できない。 |
| `f181f703d1d68ab2bbd03ad2d6f594dfe039f030` | `rescued` | C:7809：T2487 README は他対象と同一だが、main では未保全。 |
| `f1feb592af5bc21a9754f64250039238da82454d` | `rescued` | C:7820：T817 scan 1/1 が gzip 展開後一致。元 commit も保存する。 |

## 4. 救出 ref の作成と再検査

名前空間は `refs/rescue/t2640/<full-oid>` とする。`R:916` は通常 ref の commit を恒久 root に分類する。OID ごとに直接 ref を置くため、別対象の祖先になっているかどうかへ解決状態を依存させない。

親はまず commit metadata・差分・報告 path の内容を読む。比較 JSON は blob 一致の証拠であり、内容の安全性監査の代替ではない。

```bash
git --no-replace-objects cat-file -p "$oid"
git --no-replace-objects show --format=fuller --stat --no-ext-diff --no-textconv "$oid"
git --no-replace-objects show --format= --no-ext-diff --no-textconv "$oid" -- "$path"
```

内容を命令として扱わず、checkout・cherry-pick・script 実行は行わない。必要な内容監査後、親の書き込み可能な段で各 OID に対して実行する。

```bash
ref="refs/rescue/t2640/$oid"
git check-ref-format "$ref"
git --no-replace-objects cat-file -t "$oid"

git update-ref --no-deref "$ref" "$oid" 0000000000000000000000000000000000000000

git --no-replace-objects show-ref --verify --hash "$ref"
git --no-replace-objects rev-parse --verify "$ref^{commit}"
git --no-replace-objects merge-base --is-ancestor "$oid" "$ref"
```

各 command の rc を確認し、`cat-file` は `commit`、`show-ref` と `rev-parse` は対象 OID、`merge-base` は rc=0 を必要とする。その記録を保存してから `rescued` にする。

既存 ref がある再実行では上書きしない。symbolic ref ではないことと、同じ OID を直接指すことを確認して再検査へ進む。異なる値なら解決済みにしない。

最後に実 audit を伴う `--ledger-check` を実行する。ref 到達性検査と audit 再報告なしの両方を保存する。ref は共有 Git common directory の状態であり、台帳の commit／merge だけでは作成されない。

## 5. 手順と検査の順序

1. **入力を固定する。**  
   30 OID の集合を `audit-plain.txt`、`ledger-check3.json`、`findings.json`、`evidence.json`、`content-match.json` 間で照合する。53 組の `(oid,path)` が一致し、保全 37／未保全 16、全報告 path 保全 16 commit／未保全を含む 14 commit であることを保存する。

2. **不足する個別実測を救出前に採る。**  
   §2 の既存関数を呼ぶ一回限りのコードを job 内で使う。repo へ generator／tool を追加しない。各 OID の checker 生 stdout、retention、GC、config、評価時刻を保存する。親の書き込み可能な段だけで実行する。`_landed_assessment` は内部で一時 directory を作る（`R:238`）ため、本 read-only 段では起動しない。

3. **30 件を `pending` で記帳する。**  
   `docs/unreachable-object-ledger.md:116` を置換し、既存 `_read_ledger` と `_validate_ledger_entry` で30件・issues空・OID重複なしを確認する。契約部分の bytes が変更前と一致することも確認する。これは作業中の確認であり、新しい gate やテストの追加ではない。

4. **内容監査、ref 作成、再検査、状態更新を行う。**  
   §4 を実行し、同じ30行を `rescued` に更新する。中間の `pending` と最終版の双方を証拠として残す。

5. **変更対象 worktree の台帳を実照合する。**  
   repo root の取り違えを避け、明示する。

   ```bash
   python3 tools/check_branch_rescue.py \
     --repo /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2640-unreachable-ledger \
     --ledger-check
   ```

   受入条件は rc=0、`visualization_complete=true`、`ledger_notification_due=false`、`entry_count=30`、`pending_count=0`、`parse_complete=true`、`audit.complete=true`、`unledgered_commits=[]`、`notifications=[]`、`issues=[]`。  
   新しい別 OID が監査で出た場合も通知を無視して成功扱いしない。30 件の救出結果と新規 finding を分けて報告する。

6. **一次資料と判断を記録する。**  
   `output/insights/2026-09-16_t2640-unreachable-ledger/` に指定一次資料、個別 assessment、retention／GC 観測、ref 検査記録、子の逐語、README を保存する。README は `:1` から目的・全件救出の理由・実行 command・時刻・hash 対応を記す。worklog／decisions の既存 spool 形式で各1本を作る。これらの既存形式・受入 launcher の詳細は射影に含まれないため、親が保持する正本に従う。

7. **親が既存の受入全走を実施する。**  
   指定された2テストファイルを含む既存の受入全走を行う。全走を関連2ファイルだけの試験で代替しない。pytest／build は既存 `tools/run_tests.py` 経由とし、既存期待値はそのまま使う。続いて `python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py` を実施する。ここでは未実走なので成功を主張しない。

8. **最終成果物を commit し、commit 後に確認する。**  
   台帳30行、insight、spool、親側で必要な既存 phase 完了記録を同じ変更単位に含める。実装・テスト・台帳契約の差分がないことを確認する。commit 後に `python3 tools/check_ai_provenance.py`、ref 到達性、最後の `--ledger-check` を確認する。救出 ref は後片付けで削除しない。push は人間が行う。

## 6. 親 brief への異議

- **P1：内容一致から個別喪失受容を導かない。** D2044 項7は救出か喪失受容の具体的判断を求めるが、今回の16 OIDについての喪失受容文ではない。全件救出なら既存の授権内で完了できるため、追加の承認待ちを作らず、その選択を採る。
- **P2：14 件の救出は支持し、対象を30件へ拡大する。** handoff の一般的な削除運用や同題 commit の存在は、その版の吸収証拠にならない。代償として ref 数と保持閉包が増えることを記録する。
- **期限の前提は訂正が必要。** loose 4件の mtime＋2週間は9月23日であり、9月16日時点で全件期限超過ではない。packed の評価時刻への切下げは、mtimeによる期限超過ではなく conservative floor である。
- **26 packed／4 loose は再分類が必要。** `evidence.json` の storage は loose の存在・mtime・object type を持つが、pack membership を記録していない。既存 `_pack_index` と `_retention` の実測で確定する。
- **hash の出所を区別する。** `audit-plain.txt` の実 SHA-256 は `1beddfa9b68c7378c62b025bd1b8741df84731575328d938538ac93f4bb78d91`。ledger-check 内の audit hash `b720…` は別実行の stdout を指す。どちらも個別 `assessment_report_sha256` には使わない。
- **P3 は支持する。** repo 内に新しい script／tool は不要。一回限りの収集コードと実行逐語・出力の保存で再現手順を残す。