# 判定: NO-GO

## 所見 1 — blocker: resolver の固定 HEAD が consumer まで伝わらず、証拠鎖が二つの commit に分裂する

根拠:

- `IndexedFloorProtocol` は path、document、bytes、SHA だけで、選択に使った `commit_oid` を保持しない。`orchestrator/campaign/s8b_floor_campaign.py:590-597`
- resolver 内部では HEAD を一度固定するが、CLI は path だけを出力する。`s8b_floor_campaign.py:931-968,6806-6816`
- shell は早期に `CURRENT_COMMIT` を H1 として固定する一方、依存 build 後に live HEAD から resolver を実行し、job-result には古い H1 を書く。`tools/pegasus/floor_campaign.sh:531-545,954-978,1130-1156`
- holdout admission も resolver 後に、固定 OID ではなく bare `HEAD` を二度読み直す。`orchestrator/campaign/s8b_holdout_admission.py:473-484,500-509`
- その Git 呼出しは resolver と異なり、ambient `GIT_*` を除去しない。`s8b_holdout_admission.py:267-272`

再現の筋道:

1. H1 と H2 を用意する。source と protocol namespace は同一だが、HEAD gitlink だけを P1 と P2 に変え、namespace には両 pin の record を含める。
2. job が H1 を `CURRENT_COMMIT` として submit receipt と照合した後、resolver 実行前に HEAD を H2 へ動かす。
3. resolver は H2 の gitlink により P2 record を返し、driver、manifest、result、holdout claim は P2 を使う。
4. job-result は保存済みの H1 を `source_commit` として記録する。
5. holdout 内でも resolver 直後に HEAD を動かせば、同じ protocol blobが両 commit にある限り bytes 比較は通り、別 commit が `measurement_head` になる。
6. `GIT_DIR` と `GIT_WORK_TREE` を別 repository と対象 worktree に向けても、resolver と後続 Git 検査が異なる Git authority を観測し得る。

成果物への影響: job-result の `source_commit=H1` に対して、レポートと試行台帳の `protocol_sha256`、`ccbench_pin`、`measurement_head` が H2 由来になり、一回性 holdout claimを消費した証拠鎖の参照が分裂する。

固定 commit を resolver recordに含め、holdout の blob読取と `measurement_head`、shell の receipt commitを同じ OIDへ束縛する必要がある。

## 所見 2 — major: singleton fallback は `E` を構成せず、gitlink 不在でも受理する

根拠:

- `len(C)==1` なら `_ccbench_gitlink` より前に返る。`orchestrator/campaign/s8b_floor_campaign.py:949-957`
- したがって実装は「`E` を `C` の部分集合として構成し、`len(E)==0 and len(C)==1` なら fallback」ではない。gitlink が不在・不正なら `E` は構成不能であり、空集合とは判定できない。
- テストもこの過剰受理を明示的に固定している。`orchestrator/tests/test_s8b_protocol_builder.py:1093-1102`

再現の筋道:

1. current contract に一致する legacy record だけを commitする。
2. HEAD から `external/ccbench` gitlink を除く。
3. `resolve_current_floor_protocol()` を呼ぶ。
4. `_ccbench_gitlink` は一度も呼ばれず、legacy recordが返る。
5. holdout admissionを直接呼べば、その protocol の任意の40桁 `ccbench_pin` を持つ claimを作成できる。

成果物への影響: 試行台帳の `key.ccbench_pin` を `measurement_head` の gitlinkへ結び付けられない repository 状態まで、holdout claimの受理集合に入る。

今日の legacy fallbackを維持する場合でも、gitlinkの実在と形式は先に確定し、その値に対して `E` を構成すべきである。

## 所見 3 — major: working tree の mode drift は拒否されない

根拠:

- working tree側は `S_ISREG` しか確認せず、permission bitsを検査しない。`orchestrator/campaign/s8b_floor_campaign.py:867-876`
- `100644` 検査は commit blobにだけ適用される。`s8b_floor_campaign.py:686-713,883`
- 新テストも「0755を commitした record」は検査するが、「100644で commit後に chmodした working tree」は検査しない。`orchestrator/tests/test_s8b_protocol_builder.py:1542-1558`

再現の筋道:

1. versioned protocolを mode 100644で commitする。
2. bytesを変えず `chmod 0755 <record>` を実行する。
3. `lstat()` は regular file、HEADは100644、bytesとpath集合は一致するため index化される。

成果物への影響: committed-only resolverの受理集合に、working treeの modeがcommitと異なるdirty artifactが入り、job-resultと試行台帳は「exact 100644 identity」と一致しない実体を参照する。

## 所見 4 — major: ancestor symlink の TOCTOU で repository 外の実体を sanctioned path として受理できる

根拠:

- ancestor検査はscan冒頭の一回だけ。`orchestrator/campaign/s8b_floor_campaign.py:761-779,815-816`
- その後の `iterdir()`、child `lstat()`、`read_bytes()` は同一directory fdへ束縛されていない。`s8b_floor_campaign.py:848-883`
- scan終了時にancestorを再検査しない。`s8b_floor_campaign.py:913-919`
- holdout側も最終fileだけを `lstat()` し、ancestor componentを検査しない。`orchestrator/campaign/s8b_holdout_admission.py:425-434`

再現の筋道:

1. cleanな committed namespaceを用意する。
2. `_assert_floor_protocol_ancestors()` の後で namespace directoryをrenameし、同じ committed bytesを持つ外部directoryへのsymlinkへ差し替える。
3. `iterdir()` はsymlink先を列挙する。各child自体はregular fileなのでsymlink検査を通る。
4. lexical relative path集合とbytesはHEADに一致し、index化される。
5. parent symlinkを維持したままholdout admissionへ進んでも、最終fileの `lstat()` はregularとなり通る。

成果物への影響: job-result、レポート、試行台帳はrepository内の sanctioned relative pathを記録する一方、実際の参照先はrepository外となり、証拠の由来参照が偽になる。

hardlink単体では異なるbytesを `raw_bytes` に入れられないが、外部aliasからの差替え窓は同じく残る。directory fdと `O_NOFOLLOW` 相当で、検査したinodeから直接読む必要がある。

## 反証できなかった点

- `E` は、gitlinkを実際に読む経路では `candidates` から作られている。stale contractをHEAD pin一致だけで選ぶ順序逆転はない。`s8b_floor_campaign.py:938-963`
- issuerの未commit post-write検査はresolverから呼ばれない。resolverは常に committed-only scanを通り、分離は呼出し方向としては一方向である。
- create-only、同一組拒否、read-back、strict parse、導出path、継承、canonical bytes検査は残っている。`s8b_floor_campaign.py:1023-1027,1058-1067,1094-1134`
- path名の正規表現と導出比較により、安定状態での `..`、case違い、非NFC名、nested entryは拒否される。Git pathにNULは格納できない。
- resolver自身のGit呼出しは `GIT_DIR`、replace object、config注入を除去している。問題はholdout側で固定OIDを失ってから再読する部分である。
- 実装は発火する。shell、holdout admission、CLIの3経路からresolverへのlive callを確認した。到達不能な新規gateは見つからなかった。

## 今日の repository での配線差

静止した現在のtreeでは、実CLIで次を確認した。

- indexはlegacy 1件。
- `resolve-current-protocol` は変更前のliteralと同じ `output/s8b-freeze/floor_protocol.json` を返す。
- contract SHA、protocol SHA、legacy pinも既存recordの値のまま。
- holdout admissionは同じlegacy HEAD blobとsupplied documentを比較する。

したがって、HEADやfilesystemが動かない今日の状態では受理判定のbitは変わらない。ただし所見1のHEAD移動時には配線前後の証拠参照が変わるため、一般的な等価性は成立しない。

## テスト監査

skip、xfail、test file削除、現行repository hashの直書き、揮発する診断payloadの固定は見つからなかった。

削除された3 test名は、committed-only化、動的配線、post-write分離に対応する置換だった。ただし次の穴がある。

- gitlink不在singletonの受理を正例として固定している。`test_s8b_protocol_builder.py:1093-1102`
- working treeだけのmode driftがない。
- HEAD移動をshell receipt、resolver、holdout claimの三者間で試すtestがない。
- canonical proof-chain E2Eのresolverがmockへ置換され、real resolverとの統合は別の予約testだけになった。
- shellの正例は実際の sanctioned path形式でない。`test_pegasus_floor_tools.py:2300-2333`

pytestは実行していない。Python 5ファイルのAST解析は通過した。親の213 passed / 2 skippedは親の実測としてのみ扱う。

**最終判定: NO-GO。** 少なくとも所見1はland前のblockerであり、所見2から4も正しさ境界の明示主張を満たしていない。

## 総括

- committed bytesそのものを別bytesへ差し替えてindexへ入れる単純経路は見つからなかった。
- しかし固定HEADのidentityがresolver recordとCLI出力から脱落し、consumerでlive HEADへ戻っている。
- その結果、source commit、protocol pin、measurement headが異なるcommitを指す試行台帳を作成できる。
- singleton fallbackはgitlink構成不能を空集合扱いし、本来fail-closedにすべきrepositoryを受理する。
- working treeのmode driftとancestor symlink raceも、主張された拒否集合から漏れている。
- 今日の静止したlegacy-only repositoryではpathと受理bitは変わらないが、並行HEAD移動時の証拠鎖は変わる。
- よってこの差分は現状のままlandできず、結論はNO-GOである。