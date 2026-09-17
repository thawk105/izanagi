## 所見対応表 (closed / partial / regressed)

**判定は NO-GO です。cleanup の公開途中停止に退行があり、登録前検証にも不変条件 h′ との差が残っています。** 焦点走の成功件数は照合できました。変異は実行していません。

以下の行番号は統合後の現物です。略記は次のとおりです。

- L：[dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/tools/dev_wave_land.py)
- T：[test_dev_wave_land.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/orchestrator/tests/test_dev_wave_land.py)
- C：[dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/tools/dev_wave_cleanup.py)
- CT：[test_dev_wave_cleanup.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/orchestrator/tests/test_dev_wave_cleanup.py)

`closed` は記載した問題に限定した判定です。変異検出力や未記録の個別実走まで認定するものではありません。

| 所見 | 判定 | 現物・ログとの照合 |
|---|---|---|
| U1 R1：provenance 分類 | closed | L:3620 の共通分類を早期終端と完全 verifier が使用。違反 rc のみ非 retryable。T:9700・9763・9769 は違反時の削除、rc16／signal 時の seq 保持を確認する。焦点走に失敗なし。 |
| U1 R2：二者による死亡票回収 | closed | L:3065 付近で最新の digest 検証済み record 全体を比較し、古い観測から再追記しない。T:3962 は同じ観測を二者に渡し、追記一回・連番・grant を検査。 |
| U1 R3：初回 registry 公開前死亡 | closed | L:2755 付近で空 registry を ticket 作成前に永続化。T:3754 は初回 rename 前に実子 process を kill し、journal 不在と後続成功を検査する。個別実走の証跡については後述。 |
| U1 R4：gate 後 receipt の retryable 消失 | closed | L:6102 以降で acceptance 再検証を汎用 fold 例外変換の外に置き、`_Reject` を再送出。T:4045 は receipt I/O 障害の rc23・retryable・seq 保持を検査。 |
| U1 N1：同 key 完了解消 | closed | L:3070 以降で `done`、FD close、seq 削除、引渡し。T:4006 は ff 完了を already-landed、finalize 済みを既存 stale-main とし、双方で票の完了を検査。 |
| U1 B1：後続 FIFO の観測不足 | closed | T:4497・4515 に grant 順の圧縮列 `1..8`、独立 wave 側には終了順 `1..8` の assertion がある。 |
| U1 B2：shape-B mark 前未到達 | closed | T:4148 の `shape-b-mark-ticket/fd` が `applied` state を作って再入する。mark／finalize／apply の開始も直接観測する。 |
| U1 B3：recovery 元票の観測不足 | closed | T:4071 が元 key・seq、後続 grant 不取得、transaction、origin、採番、FOLDED、fold commit 一個を確認する。 |
| U1 B4：M7 の帰属 | partial | SURVIVED 対照への再分類はコードと整合する。ただし M7b の hint は入力不変の成功例であり、「後段が変更を拒否した」証拠にはならない。 |
| U1 B5：実 subprocess 死亡 | partial | T:3731 に実 `Popen`／SIGKILL／FD 解放／後続 grant／land の test がある。焦点ログは集計のみで、この node の個別 PASS は記録されていない。 |
| U1 B6：exact 変異登録 | partial | 20 置換の一意性・構文を再確認。ただし probe JSON は全件 `expected_nodes=[]`、`expected_status=SURVIVED`。hint は報告書側にあり、最終的な帰属登録・単独結果は未了。 |
| fix-1 A 群：runner 関連 | partial | shape 三種、欠落二種、digest、child-green、D987 の最終拒否／受理検査は残る。焦点走は緑。ただし runner 固定 object 検査を登録後へ移したため h′ 違反が残る。 |
| fix-1 A 群：checker 欠落／symlink | closed | T:5672 は missing／leaf の rc29 を保持。ancestor は waiter 不在による登録前 rc23、監査未起動を確認。T:5742 で checker 自身の ancestor 拒否を別途確認。 |
| fix-1 B 群：時間予算 | closed | T:4604 は180秒枠非補充、3600秒期限、残60秒への切詰めを確認。 |
| fix-1 B/C：merge 子 | closed | T:8321 は3600秒期待と `finally` 内の子完了待ちに変更。common-lock FD 継承の検査は維持。 |
| fix-1 C 群：rollback 四件 | closed | T:7348 付近・9838 は実登録／grant／common flock を持つ setup。rollback の既存結果 assertion は維持。 |
| fix-1 D 群：非 authoritative provenance | closed | R1 と同じ共通分類に接続。seq 保持 assertion も追加されている。 |
| fix-4 D16：gitlink 変更 | closed | T:2952 は未同期／誤同期の成功を禁止。L:5632 の早期成功撤去により既存 preflight へ進む。 |
| fix-4 D16：gitlink 削除 | closed | T:3014 は worktree・nested metadata の残存拒否を維持。 |
| fix-4 D16：通常 tree への置換 | closed | T:3078 は残存 submodule identity の拒否と置換先内容の保持を維持。 |
| fix-4 D16：通常 blob への置換 | closed | T:3160 は metadata 残存拒否と blob 内容保持を維持。以上四件の既存 test に diff はない。 |
| fix-4：poll 保存縮小 | closed | L:2780 付近は正規化 bytes が変わった場合だけ保存。T:3560 は読取り時の inode／bytes 不変と更新時の永続化を確認。 |
| U2 A1：更新 index の取り込み | closed | C:910 付近で基準 snapshot と完全比較。live は安全再確認後に固定、state c は bind 時点を保持。CT:1207 以降に bytes／inode × a／b／c の六ケース。 |
| U2 B1：公開途中停止 | **regressed** | 不完全 JSON の公開は解消したが、`link` 後・`unlink` 前の停止で再入不能になる。下記の must-fix。 |
| U2 B2/A3：snapshot 容量・負荷 | partial | C:773 は通常 file を長さ＋SHA-256、意味検査用四種だけ raw 保存。反復全体読取りと大きな意味検査用 file の負荷は残る。 |
| U2 A8/B4：M10 | partial | 直接 `subprocess.run` する置換で argv gate を迂回できる。foreign stale admin 消失で殺せる構造だが、未実走。 |
| Lustre `renameat2` → `os.link` | **regressed** | 通常公開の互換性改善と既存 final 非上書きは確認。ただし crash 境界の再入性が失われている。親の link probe 成功ではこの問題は閉じない。 |

**must-fix 1：cleanup の link/unlink 間停止。**

[C:968](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/tools/dev_wave_cleanup.py:968) で final を link した直後、969行の一時名 unlink 前に SIGKILL、または unlink エラーが起きると、final と temporary が同一 inode を参照し、`st_nlink == 2` が残ります。

再入は C:860 の recovery 読取りから [C:752](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/tools/dev_wave_cleanup.py:752) の `nlink != 1` 拒否へ進みます。temporary を照合して処理する経路はなく、同じ要求を繰り返しても rc20 です。admin flock は死亡時に解放されますが、リンク数は戻りません。

これは U2 B1 と同じ「公開途中停止による恒常的な再入不能」であり、scope 内です。CT:1243 の停止点は公開前だけです。公開後・一時名削除前の再入処理と、その境界の test が必要です。単に全 admin file の nlink 検査を緩める修正は適切ではありません。

## 派生値の再計算

| 対象 | 再計算 | 判定 |
|---|---|---|
| land 焦点走 | progress 行の `.`＝357、`s`＝1。summary＝`357 passed, 1 skipped in 20.55s` | 一致。20.6秒は丸め値。 |
| cleanup 焦点走 | ANSI 除去後の progress 行の `.`＝141。summary＝`141 passed in 6.81s` | 一致。6.8秒は丸め値。 |
| storm-e 着地 | `results_timeline` の rc0＝0、`landed=[]`、final の landed＝0 | 一致。 |
| main 不変 | before／after とも `374d232f39808b665c1e0ec9bc49ad3001ed2dbd` | 一致。 |
| 終端151回 | timeline 長＝151、rc 分布＝`{11:151}`。`trace_counts.result=151` | 一致。 |
| initial 12／post-provenance 1 | final 13件の reason を集計。index 4 だけ post-provenance | 一致。ただし**151終端全体の phase 分布ではない**。 |
| 監査18回 | `audit_calls=18`、`trace_counts.audit-start=18`、`audit-return=18` | 三項目は一致。ただし生 trace が JSON にないため、18イベントの独立再計数はできない。 |

storm-e の到着列は `0,20,…,240` の13本、in-lock 240秒、監査430秒、retry delay 120秒、horizon 4560秒＝76分です。timeline の終端時刻は200〜4540秒。`wall_s=8.5` なので、76分はモデル時間です。

JSON には storm-d 等も含まれ、storm-d は着地しています。「旧 tree のすべての policy が着地ゼロ」とは読めません。

両焦点ログは受入形でない旨を明記しています。合計498 passed／1 skipped を受入全走の結果には置き換えません。

## 不変条件の最終確認

| 条件 | 判定 | 根拠 |
|---|---|---|
| a′：common flock 内 mutation | 維持 | initial／再取得の binding 検証、ff 前・apply 前・shape-B mark／finalize 前の接続を確認。票だけを mutation guard にする経路はない。 |
| b′：mutation 前拒否で main 不変 | 維持 | 登録・観測解消は registry／journal の操作。apply 開始前の ownership 拒否から rollback へ入らない分岐も残る。 |
| c：監査・gate 中の解放 | 維持 | L:4664 の `lock.close()` → runner 一回 → 再取得。 |
| d：完全再検査・receipt 束縛 | 維持 | provenance 後と gate 後の control、fingerprint、完全 preflight、receipt、active state、closure 検査を維持。登録時 digest と完全検証時 digest も比較。 |
| e：FD による生存判定 | 維持 | L:2791 の別 open description による flock。pid／mtime／TTL を生存判定に使用しない。 |
| f′：死亡 mutating の解消・recovery | 維持 | 五分岐、同 key 優先、異なる landing tip の拒否、最新 record 再照合を確認。 |
| g′：mutation 直前の所有再確認 | 維持 | L:6249、5160、5345、5374。grant、生存、ticket／repository binding を再確認。 |
| h′：登録前の固定入力検証 | **不適合** | runner の tested-main／tip blob shape・実行 bytes digest 照合が L:1178 の locked 側に移っている。 |
| i：knob 不追加 | 維持 | 新設定は module 定数。CLI／環境変数の追加は見当たらない。 |
| j：自 wave・衝突対象検査 | 維持 | 非 protected child のみ open 前に除外。自 wave、protected 集合、handoff 名前集合、fold state の検査は残る。 |

**must-fix 2：h′ の登録前検証が不足しています。**

[L:1197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-land-turn-ticket/tools/dev_wave_land.py:1197) の runner digest 比較は tested-main の固定 object に対する検査で、common lock に依存しません。しかし登録前の `_verify_acceptance_static` は digest の文字列形式までしか検査しません。

したがって、有効 receipt の `runner_executed_sha256` だけを別の64桁値にすると、登録・seq 消費・grant 待ちを通過し、完全 verifier で初めて拒否されます。最終 land の誤受理は防がれていますが、裁定の「固定 blob／bytes 検証を通した request だけ登録」に反します。fix-1 A 群の緑だけでは、この分割は正当化できません。

受理集合については、land の無関係 child の反転は裁定範囲内です。一方、既報の cleanup 非 canonical gitdir 拒否は C:388 に残り、旧実装より受理が狭まっています。これは既報 nit として残し、今回の must-fix へ昇格させません。

lease の TTL と順番票の期限は別です。T:3837 は TTL 超過後に別 holder が取得した lease を消さず、land 成功と release の `not-owner` を分けて確認しています。

## 変異 spec の妥当性

20件すべてについて、現物で `old` の一致数1と置換後の `ast.parse` 成功を再確認しました。以下の hint は fix 報告から対応付けたものです。**JSON 自体には hint／期待 node がありません。**

| 変異 | 機構・指定 node 単独での静的評価 |
|---|---|
| M0 | コメントのみ。真の等価対照として妥当。 |
| M1 | `_wait_land_turn` を迂回。累積8本 test の全件成功・順序検査で検出可能。ただし後段拒否で殺される可能性もあり、「grant 前流入を直接検出」との帰属は実測で区別する。 |
| M2 | 再入 seq を新規採番へ変更。`retry_preserves_sequence` の元 seq assertion に直結。 |
| M3 | FD 生存中でも古い mtime で死亡扱い。test は `os.utime(...,(1,1))` 済みで、TTL 変異に届く。 |
| M4a | ff 前 marking を省略。[ff] の拒否・main 不変検査で検出可能。 |
| M4b | apply 前 marking を省略。[fold] の apply 不開始検査で検出可能。 |
| M4c1 | shape-B mark 前だけを省略。[shape-b-mark-ticket] は `applied` 再入へ到達する。 |
| M4c2 | shape-B finalize 前だけを省略。[shape-b] が対応する。 |
| M5a | 選出時に mutating 票を削除。元票保存・通常 grant 停止の直接 assertion がある。 |
| M5b | 完了観測で state 判定前に票を削除。後続 grant／元票検査があるため、後段 recovery 拒否だけでは緑にできない。 |
| M6a | provenance payload の再取得を旧180秒残枠へ戻す。[provenance] の220秒競合・成功期待に届く。 |
| M6b | fold payload だけ同様に変更。[fold] に届く。 |
| M7a | fingerprint 比較を無効化。hint の main 変更は後段 preflight でも拒否でき、非OKだけを見るため SURVIVED 予測は妥当。 |
| M7b | gate 後比較を無効化。hint は入力不変の成功例なので SURVIVED 予測は妥当。ただし冗長な拒否機構の証明ではない。 |
| M8 | 非 protected child の `continue` を除去。foreign open 不在 assertion が直接検出する。 |
| M9 | 自 wave inode 比較を除去。[ff-wave] は mutation 直前に実 directory を差し替える。main 不変 assertion に届く形。 |
| M10 | 対象限定削除を直接 subprocess の全体 prune に変更。[stale] の foreign admin snapshot 比較へ届く形。 |
| M11 | static verifier の拒否を握りつぶして登録へ進む。hint は登録 directory 不在・lock／audit 未起動も検査するため、後段拒否では隠れない。ただし今回発見した runner digest 未検査までは覆わない。 |
| M12 | 引渡し前 registry を追加公開。保存回数と公開内容の assertion が検出する。registry flock 自体は保持したままなので、「他 process が二 transaction 間へ割り込む変異」とは区別する。 |
| M13 | 非ゼロ provenance の早期終端を無効化。holder が lock を保持し続ける hint で、sleep 不在・即時 RC_PROVENANCE の検査に届く。 |

M4 系は呼出し省略とともに wrapper 内の故障注入も消えます。「故障した所有権を無視した」場合だけでなく、「故障注入なしで mutation が成功した」ために赤になる点を帰属記録に残す必要があります。

M7a/b は全入力について等価ではありません。特定 hint に対する SURVIVED 対照として扱うのが妥当です。

M10 は `_git`／`_must_git` を通らず、argv 禁止で先に止まる問題を回避しています。自 admin と foreign stale admin が prune され、自 cleanup の成功検査後、CT:1085 の `_admin_tree_state(admin)` が消失した foreign root の `lstat` で失敗する予測です。**この失敗箇所の実測は未取得です。**

なお、probe JSON の全件 SURVIVED／期待 node 空欄は探索用設定としては利用できますが、そのまま「17件の KILLED 期待と3件の SURVIVED 対照を登録済み」とは扱えません。

## 残る懸念 (実測が要るもの)

- **変異20件の単独結果**：KILLED／SURVIVED、失敗 node、失敗理由、exact diff digest の対応が必要です。現資料から KILLED 実測済みと数えられるものはありません。
- **subprocess 死亡 test の個別証跡**：実装はあります。焦点 suite の集計は成功していますが、死亡二 node の PASS と唯一の skip の node 名は提示ログから特定できません。
- **cleanup の link 後停止**：静的に再入不能が成立します。修正後、link 成功直後・temporary unlink 前の SIGKILL／unlink エラーから再入できることを確認すべきです。
- **Lustre**：通常の `os.link` は親が probe 済みという前提を受け入れます。その結果を停止境界の回復性や電源断耐久性の証明には拡張しません。
- **旧負例の証拠精度**：151終端は timeline から再計数可能ですが、監査18回は集計値同士の照合です。必要なら生 trace で補強してください。
- scheduler の独立した死亡回収交代点、horizon 終了時の unwind 順、trace 時刻表現、cleanup の反復読取り負荷など既報 nit は残ります。scope 外の自動復旧主体や生存 hang 対策を今回の must-fix にはしません。

## 総括

**NO-GO。scope 内の must-fix は二件です。**

1. cleanup の `os.link` 後・temporary unlink 前の停止から再入できない退行。
2. runner 固定 blob／bytes 検証を登録後へ移したことによる h′ 不適合。

357 passed／1 skipped、141 passed、および storm-e の着地ゼロ・151終端・final phase 12／1 は照合できました。既存所見の多くは解消していますが、この二件と変異の単独実測が未完のため、統合後の受入完了は支持しません。
