## 判定と確認範囲

**NO-GO。must-fix は1件です。** P1' の数式は実装されていますが、object 名と同形の ref／reflog を共有 object と誤分類し、registry file の hardlink 拒否を弱めます。

指定資料を読み、静的照合と、現物から抽出した述語のメモリ内評価、読み取り専用の `git check-ref-format` を行いました。編集・pytest・撤去は実行していません。親の `focus-impl-1.log` は計算ノードで **150 passed in 4.39s、rc=0**。受入全走・段9の成功を示すログではありません。

以下、`tool`＝`tools/dev_wave_cleanup.py`、`test`＝`orchestrator/tests/test_dev_wave_cleanup.py`、`ruling`＝`s4-ruling.md` です。

## A1 — registry file を受理する名前形が残る

**自己判定：real／must-fix。**

`tool:759` は `ruling:28–31` の数式と一致します。しかし、その数式自体が registry 拒否という不変条件、および `ruling:32` の「`logs/**` は False」と衝突しています。

`H38` を `1` が38個の文字列とすると、現物の評価は次のとおりです。

| admin 相対パス | 述語 | 実体 |
|---|---:|---|
| `modules/sub/refs/objects/ab/H38` | True | loose ref |
| `modules/sub/logs/refs/objects/ab/H38` | True | 対応する reflog |
| `modules/objects/objects/ab/H38` | True | submodule 名が `objects` の真の store |
| `modules/objects/config` | False | registry file。component 数が3 |

最初の ref 名は `git check-ref-format refs/objects/ab/<実際の38桁>` が **rc=0**。Git が扱える ref 名です。files backend で loose ref として作成可能な形ですが、作成自体と本環境での hardlink 分布は未実測です。

snapshot の `tool:814` と撤去再読の `tool:988` は同じ述語を使い、ref 内容を object として解釈する検査もありません。したがって、この registry file を hardlink にすると両方で許容されます。

**放置時の帰結：** 他条件成立時、従来 preflight rc=20 だった対象が撤去継続・rc=0 になり得ます。削除は自 wave の entry の unlink に限られ、外部 alias の bytes は不変ですが、規律2の受理境界を破ります（`tool:991`）。

修正対象は `tool:757–759` の分類だけです。ref／reflog の同形パスを除外し、真の store・入れ子 store・submodule 名 `objects` の正例を維持してください。生存中の `HEAD/config` に依存する判定は、既裁定の理由から採らないでください（`ruling:25`）。既存負例は維持し、この同形 ref／reflog の hardlink 拒否を追加確認する必要があります。

## A2 — 狭すぎる名前形と regex の意味

**自己判定：real／nit。裁定どおりの限定です。**

`tool:752–759` は以下を False にします。

- `modules/sub/objects/info/packs`
- `modules/sub/objects/info/alternates`
- `modules/sub/objects/pack/multi-pack-index`
- `multi-pack-index-<hash>.bitmap` など、`pack-<hash>.<英小文字>` 以外の名前

これらは store 内の補助ファイルで、loose object／個別 pack の指定名前形には入りません。hardlink が存在すれば通常 snapshot で rc=20 が残ります。ただし `ruling:32` の11:10 JST観測は source store の `info/` が空、`pack/` が `.pack/.idx` のみで、この wave の阻害要因となる証拠はありません。将来の到達頻度は不確実です。

**自己判定：refuted — 標準名の `.bitmap/.keep/.promisor` が拒否される。**

`pack-<40桁または64桁hex>.bitmap`、`.keep`、`.promisor`、`.rev` はすべて True です。`[a-z]+` はこれらを含み、未知の英小文字拡張子も含みます（`tool:754,759`）。この受理は P1' どおりです。

`\Z` は `fullmatch` と終端制約が重複しますが、受理集合を変えません。`bool(...)` は正規表現の `Match`／`None` を真偽値に変換し、外側の比較と合わせて戻り値を bool にします。

**帰結：** 指定外の共有補助ファイルでは rc=20 を維持します。今回その範囲を拡大する修正は不要です。

## A3 — 入口条件と stable の保証

**自己判定：refuted — nlink==0 や特殊 file を追加受理する。**

`tool:765–769` の入口真理値表です。

| regular file | nlink | allow=False | allow=True |
|---|---:|---|---|
| False | 任意 | 拒否 | 拒否 |
| True | 0 | 拒否 | 拒否 |
| True | 1 | 受理 | 受理 |
| True | >1 | 拒否 | 受理 |

allow=False は現行条件と同値です。追加受理は、allow=True の regular file かつ nlink>1 に限られます。

**自己判定：real／nit、既裁定済み — ctime の変更履歴検出は弱まる。**

allow 時は `(dev, ino, mode, size, mtime_ns)`、registry 側は `(dev, ino, mode, nlink, size, mtime_ns, ctime_ns)` です。後者の7要素は patch 上も逐語不変です（`tool:773–776`）。

同 inode・同 size の上書き後に mtime を復元した場合、allow 側の metadata 比較では検出できません。snapshot と撤去再読の bytes が異なれば、length＋sha256 比較で拒否します（`tool:786–789,987–990`）。ただし、一時変更後に bytes も戻った場合や、両読取結果が同じ場合は変更履歴を検出しません。最終読取後から unlink までの書換えも捕まりませんが、この窓は既存実装にもあります。

**帰結：** object の変更履歴だけを理由とした拒否が通過に変わる場合があります。これは `ruling:13,35–37` の既裁定範囲であり、cleanup が外部 alias の bytes を書き換える経路は増えません。

## A4 — 残る拒否条件と撤去範囲

**自己判定：refuted — 他の読取や撤去対象まで緩和される。**

keyword なしの6呼出しを確認しました。

| 呼出し元 | 行 |
|---|---:|
| `_administrative_gitdirs_for_wave` の gitdir | `tool:631` |
| `_bind_admin` の gitdir／commondir | `tool:847,848` |
| `_load_admin_recovery` の journal | `tool:896` |
| `_remove_admin` の journal 2箇所 | `tool:1031,1052` |

semantic 集合は root 相対の `gitdir/commondir/HEAD/logs/HEAD` の完全一致で、`modules/` 始まりの述語とは交差しません（`tool:815–816`）。

marker 拒否は分類より前、symlink／特殊 file 拒否は regular 分岐の外にあり、読取にも `O_NOFOLLOW` と regular 判定が残ります（`tool:763,766,796–819`）。`locked` の許容は既存の `allow_locked` によるものです。

対象は backpointer を照合した自 wave の admin で、束縛した FD から再帰し、最後も `admin.name` だけを削除します（`tool:640,830–837,865–868,982,1048`）。`_mutate` の対象選択や禁止コマンドを追加する差分はありません（`tool:1265–1339`）。

**帰結：** A1 の誤分類を除き、これらの拒否条件と D2119 項8の撤去範囲は維持されます。外部 hardlink の nlink／ctime は変化しますが、bytes は削除・上書きされません。

## A5 — 負例4件と GIT_OPTIONAL_LOCKS

**自己判定：refuted — 現在の4 case が別理由で先に落ちる。**

| case | 拒否理由 |
|---|---|
| `gitdir` | root は述語 False。CLI は resolver `tool:631`、直接 assertion は snapshot で同じ hardlink を拒否 |
| `submodule-config` | `modules/sub/config` は False。helper の共有 object は許容対象 |
| `ref-named-objects` | `modules/sub/refs/objects/topic` は所定の末尾構造でなく False |
| `submodule-named-objects` | `modules/objects/config` は len(parts)=3 で False |

根拠は `test:1141–1178`。`_make_repo` は既定 unlocked で、lock 作成は `locked=True` の場合だけです（`test:61,85–86`）。この負例は `_prepare_state` を使わず、直接 `_admin_snapshot(fd)` が marker で先行拒否される構成ではありません。

ただし、現在の `ref-named-objects` は `topic` だけで、A1 の同形 ref を被覆しません。

**自己判定：refuted — `GIT_OPTIONAL_LOCKS=0` が hardlink 拒否を迂回させる。**

環境変数は tool の Git subprocess に継承されます（`test:1145`、`tool:259–266`）。したがって副作用まで完全に同じとはいえませんが、ここでは依頼文のとおり status の任意 index 更新を抑止する設定です。clean 判定は引き続き status 出力を検査し、hardlink 拒否は Python の stat 条件で決まります（`tool:564–572,766–769`）。

この fixture で受理・拒否を逆転させる経路は確認できません。比較から `index` を除く代替より、現案は index の inode／bytes も比較対象に残します（`test:1089–1092,1175`）。F27 に当たる期待値緩和とは判断しません。

**帰結：** 4 case は対象 hardlink を理由に rc=20・無撤去を要求したままです。A1 の未被覆境界は別途修正が必要です。

## A6 — fixture と既存テストへの波及

**自己判定：refuted — synthetic object では要求正例が成立しない。**

helper は任意 bytes ですが、実ファイルへ実 hardlink を作り、loose・`.pack`・`.idx`・入れ子 store を通します。成功後に admin 不在、外部 alias の bytes 不変、nlink=1 を確認します（`test:1095–1133`）。tool は Git object 形式を解釈しないため、今回のファイル読取と unlink の主張には有効です。

**自己判定：real／nit — live 成功は未確認。**

real submodule の構成、実 `.idx`、入れ子 store、高い nlink（依頼文の275〜293）と組み合わせた段9の結果は、synthetic の緑からは確定しません。段9の実測が埋めるのは、その時点の当該 wave の差だけです。F1026 の条件付き拒否を「全初期化済み worktree で必ず解消」と一般化できません。

**自己判定：refuted — 既存 assertion が削られた。**

patch の `---` ヘッダーを除く `-` 行は、**tool が9行、test が0行**です。既存 journal 負例（`test:1432–1454`）、recovery の parameter／既存 assertion は削除されていません。recovery への変更は helper と alias assertion の追加です。

node 名 pin も維持されています。

- `test_real_occupancy_scan_rejects_live_process_cwd`：定義 `test:900`、参照 `test_pytest_collection_config.py:370,390`
- `test_git_argv_spy_sees_only_allowlisted_cleanup_commands`：定義 `test:1618`、参照同 `:488`

**帰結：** 既存テストの削除・緩和による保証低下はありません。ただし150件の緑も、A1 の未被覆パスの拒否を証明しません。

## 総括

**(a) NO-GO。**

**(b) must-fix（real）**

- **A1 — `tools/dev_wave_cleanup.py:757–759`**：object 名と同形の ref／reflog を共有 object と誤分類する。名前による分類を局所修正し、registry hardlink の拒否を維持すること。真の store・入れ子 store・submodule 名 `objects` は維持し、既存負例を変更せず同形パスの拒否確認を追加すること。

**(c) should／nit**

- 指定外 store 補助ファイルの hardlink は rc=20 のまま。現環境で阻害する証拠はなく、拡張不要（`tool:759`、`ruling:32`）。
- ctime の履歴検出低下は既裁定の限界。追加の原子性検査は要求しない（`tool:773–779`、`ruling:37`）。
- synthetic／焦点走の成功と段9の live 成功を区別する（`test:1095–1133`、F1026）。

**(d) refuted**

- `.bitmap/.keep/.promisor` の標準 pack 名が拒否される：regex に一致。
- 初回 nlink==0／特殊 file が追加受理される：入口条件で拒否。
- registry の7要素比較、他6呼出し、semantic／marker／symlink 拒否が弱まる：該当部分は維持。ただし A1 の誤分類は例外。
- 外部 alias の bytes や他 wave の admin まで削除する：自 wave の entry の unlink に限定。
- 負例が locked で先行拒否される／環境設定で拒否が迂回される：fixture と呼出し経路上、根拠なし。
- 既存 assertion／node pin が削除された：test の削除行0、pin 維持。

**(e) 裁定パッケージ候補**

P1' の数式と registry 拒否の不変条件の衝突を、A1 の具体例付きで親へ差し戻す必要があります。registry 拒否を優先して分類を訂正してください。本題外の gate・一般検査・T-2778 の追加候補はありません。