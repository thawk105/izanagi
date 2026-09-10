## 判定

**NO-GO。残 must-fix は 4 件です。** 静的検査のみで、pytest、編集、commit、job 投入は行っていません。

内訳は実装・回収経路 3 件と、段 7 へ移管済みの記録 1 件です。fix 3 による regression はありません。

## 段 6 裁定 F-0〜F-8

F-0 は段 6 §1 の非実行体化、F-1〜F-8 は裁定表の同番号として対応させています。

| 所見 | 状態 | 根拠 |
|---|---|---|
| F-0 submitter の非実行体化 | closed | `.sh.txt`、先頭は `# `、実 filesystem と Git index の mode はともに 644。repo 内 `.sh` 実行体ではない |
| F-1 ERR trap による二重結果 | closed | observer は scratch へ捕獲され、単一かつ parse 可能な prefixed JSON だけを一度転送する。[PBS:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1259-qsub-env-delivery/tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs:59)。rc=1 の正規負結果も二重化しない |
| F-2 request ID 固定 projection | closed | approval の存在・値・nonce から categorical/bool を導出し、内部整合も検査する。[probe.py:400](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1259-qsub-env-delivery/tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:400) |
| F-3 R2 argv 完全一致 | closed | 固定 argv との完全一致が acceptance に入り、extra argv、mode 変更、approval flag の負例が独立 literal で存在する |
| F-4 実行時 source identity | closed | observer 開始時に HEAD、detached、tracked-clean、untracked-empty を要求し、probe、PBS、campaign、実行 PBS bytes を hash 束縛する。[probe.py:232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1259-qsub-env-delivery/tools/pegasus/probes/t1259_qsub_env_delivery_probe.py:232) |
| F-5 scheduler preflight／可視性 | **partial** | `gen_S=ENA` と request ID＋job-name prefix は gate される。しかし own active request の内容は保存するだけで、owner・queued/running state も receipt の受理条件に入らない |
| F-6 group 証跡 | **partial** | qsub 前の create-only intent と request sidecar は実装済み。しかし裁定が別回収段へ移した terminal state、一次 stdout hash、completion manifest の実装・固定参照は射影内にない |
| F-7 submitter の非干渉閉包 | closed | 冒頭の core 無効化、repo 外 preflight、各 qsub 前と終了時の HEAD／clean／source hash 再検査がある |
| F-8 test の実装定数依存 | closed | fixture の schema、label、env 順序は独立 literal。実 call block を限定し、埋込み Python を動的負例で実行している |

`regressed` 判定の行はありません。

## レビュー A must-fix 対応表

| A 所見 | 状態 | 対応 |
|---|---|---|
| must-fix 1 非干渉 preflight | **partial** | queue state は閉じたが、own request 集合を拒否条件にしていない |
| must-fix 2 group manifest | **partial** | 途中投入の孤立は intent／receipt で閉じたが、別回収段と completion 成果物は未成立 |
| must-fix 3 queued job の source identity | closed | job 開始時の clean/detached/hash 束縛と前後 digest 比較を実装 |
| must-fix 4 Python 無出力時の fallback | closed | Python 無出力・複数行・不正 JSON は単一 shell fallback へ置換される |
| must-fix 5 argv と wiring test | closed | argv 完全一致、限定 block、動的負例を追加 |
| must-fix 6 「緑でも言えないこと」 | **partial** | F-9 として段 7 へ明示移管済みだが、fix 2 報告上も未実施。現 tip の完了事項ではない |

## レビュー B must-fix 対応表

| B 所見 | 状態 | 対応 |
|---|---|---|
| must-fix 1 ERR trap 二重出力 | closed | rc=1 を `if` で捕捉し、検証後に一度だけ転送 |
| must-fix 2 queued 中の source 変更 | closed | clean/detached/source bytes を manifest と実行時に再束縛 |
| must-fix 3 group completion 不在 | **partial** | intent と受付 sidecar は成立したが、completion 回収段は未実装 |
| must-fix 4 R1 固定 projection | closed | 観測 approval から導出 |
| must-fix 5 scheduler state／qstat | **partial** | `gen_S` と本文可視性は閉じたが、own requests、owner、job state は未判定 |
| must-fix 6 submitter core dump | closed | `ulimit -c 0` を fail-closed で適用し、repo 外 cwd と再検査を実装 |
| must-fix 7 未実測 submitter の local-ok | closed | repo execution inventory 外の `.txt` 非実行体へ変更 |
| must-fix 8 fixture の恒真化 | closed | 独立 literal contract と対象関数の動的検査へ変更 |

## fix 3 の regression

**regression なし。抽出の恒真化もありません。**

[test helper:731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1259-qsub-env-delivery/orchestrator/tests/test_t1259_qsub_env_delivery_probe.py:731) は開始・終了境界の一意性と末尾改行を要求し、実在する関数内の heredoc を抽出します。期待 rc、可視性、request label は実装から再取得せず literal です。

したがって request ID 照合、job-name prefix 照合、create-only mode、request 数・label の変更は静的 assert または動的実行を赤にします。fix 3 は誤った関数範囲を正したもので、検査意図を弱めていません。

ただし、現在の test は own request 非干渉、qstat の owner/state、completion 回収を検査していません。また [test:797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1259-qsub-env-delivery/orchestrator/tests/test_t1259_qsub_env_delivery_probe.py:797) は後述する silent exit の配置をむしろ固定しています。

## PBS 実機経路

通常経路は次のように一行へ収束します。

1. compute hostname、canonical repo、tracked source、scratch、Python 3.10 以上を確認。
2. observer stdout を scratch file へ捕獲。
3. observer rc=0／1／その他を ERR trap 外で取得。
4. stdout が「prefixed JSON ちょうど一行」なら、その一行だけを PBS stdout へ転送。
5. 無出力、複数行、非 JSON なら shell fallback を一行だけ出力。
6. R2 の期待拒否は observer 内で成功観測になるため rc=0。配送失敗などの正規負結果は詳細 JSON 一行を残して rc=1 になる。

ただし、全分岐では完走しません。

### must-fix 1 — PBS 冒頭に prefixed JSON がゼロ行になる経路がある

[PBS:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1259-qsub-env-delivery/tools/pegasus/probes/t1259_qsub_env_delivery_probe.pbs:25) の `ulimit -c 0 || exit 2` は、emitter 定義と ERR trap 設置より前です。`ulimit` が失敗すると stdout へ何も出さず終了します。

**成果物影響:** request の一次参照が「prefixed JSON ちょうど一行」からゼロ行へ変わり、shell 初期化失敗と env 未配送を区別できません。

## scheduler と group 回収

### must-fix 2 — scheduler 非干渉と request lifecycle の受理条件が不足している

[submitter:228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1259-qsub-env-delivery/tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh.txt:228) は own requests を採取しますが、内容を判定しません。[submitter:530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1259-qsub-env-delivery/tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh.txt:530) も ID と 8 文字 job-name prefix だけで、owner と queued/running stateを確認しません。

**成果物影響:** 競合 request が存在する run、および対象 owner/state を束縛していない行が `accepted=true` の receipt 集合へ入ります。

### must-fix 3 — group completion の生成経路がまだない

[submitter:700](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1259-qsub-env-delivery/tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh.txt:700) は最後まで `three-submissions-receipted-no-completion-judgment` を出すだけです。intent と receipt は十分な改善ですが、terminal state、prefixed stdout、結果 hash を束縛した create-only completion 成果物はありません。

**成果物影響:** group の最終参照が恒久的に indeterminate のままで、3 request の terminal result と一次 stdout hash を一つの受理集合へ確定できません。

## 非実行体契約

契約は保たれています。

- shebang なし。先頭は `# Non-executable...`
- 実 filesystem mode 644
- Git index mode 100644
- 拡張子 `.txt`
- repo 内に対応する `.sh` 実行体を置かない test がある

## 段 7 の残件

### must-fix 4 — 「緑でも言えないこと」の専用記録が未完了

これは段 6 裁定 F-9 により段 7 の親作業へ移管されています。fix 3 の regression ではありませんが、wave 全体の完了条件としては残っています。

**成果物影響:** diagnostic-only JSON が sanctioned submitter の認可証明や official campaign 実行許可として引用され、成果物参照の意味が本来より強くなり得ます。

## 総括

**NO-GO。残 must-fix 4 件です。**

fix 3 の test 抽出は恒真化しておらず regression もありません。一方、PBS 冒頭のゼロ stdout 経路、scheduler lifecycle の不完全な gate、group completion 不在が実機投入前の阻害要因です。加えて段 7 の専用記録が未完了です。