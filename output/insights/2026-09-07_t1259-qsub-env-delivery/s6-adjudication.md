# [T-1259] 段 6 レビューの裁定

レビュー A (裁定との一致・bypass・恒真化) が must-fix 6 件、レビュー B (実機走行性・測定成立・pin 閉包)
が must-fix 8 件。重なりを除くと 9 系統である。**全件 real、全件採用。**

## 1. 両レンズが逆の判断をした 1 件 — 親が実データで決めた

**submitter の admission 分類 (A の「適切」対 B の must-fix 7)。B が正しい。**

`docs/pegasus-runbook.md` の分類節が次を明記している。

- `local-ok` の grandfather は 4 本限りの例外であり、他 entry を `local-ok` にするには実測が要る。
  `legacy-admitted` を他 entry の許可根拠に流用しない。
- **AI セッション・子エージェント・自動化は分類の実測を自分で行わない。**
  実測が無い実行体は `unknown` に倒して**止め**、測定依頼をユーザーへ返す。
- hook は `tools/pegasus/` 配下の登録 path のうち `local-ok` でないものを login で拒否する。

したがって「投入 script を repo の `tools/pegasus/` へ置く」限り循環する。
`local-ok` にするには実測が要り、実測は AI が行えず、`unknown` にすると親が実行できない。
repo の別 subtree へ逃がすのは gate の迂回であり、runbook が明示的に禁じている。

**裁定: 投入 script を repo へ入れない。** 先行の [T-2228] は投入 script を repo に置かず、
`qsub` の呼び出しを `.pbs` 冒頭コメントに書いて親が直接打っている。この前例に合わせる。

- `tools/pegasus/probes/t1259_qsub_env_delivery_submit.sh` を repo から外す。
  registry・`test_hooks.py` の 2 辞書・runbook 投影表からも当該 entry を外す。
- 投入 script は Codex author が書いたうえで、親が repo 外の job dir へ退避してから実行する
  (`DW-C01`「子の成果物は repo 内に書かせ、親が実行後 repo 外へ退避」)。
- `.pbs` 冒頭コメントに、3 request の exact な `qsub` 呼び出しを書く。
- **正直に記す限界: repo 外の投入 script は単体検査で守られない。** 守るのは敵対レビューだけである。
  この非対称は insight に書く。

## 2. 採用する 9 系統

| # | 系統 | 出所 | 内容 |
|---|---|---|---|
| F-1 | PBS の ERR trap が `set +e` 下でも発火し、結果行が二重に出る | B-1 / A-4 | bash では `set +e` は `ERR` trap を無効化しない。Python が `ok=false` で rc=1 を返す**正規の負結果**で trap が先に `fail_pbs` を呼ぶ。**測りたい負結果 (2 本目が届かない) がまさにこの経路**であり、一次 evidence が壊れる。子 stdout を scratch へ捕獲し、prefixed JSON がちょうど 1 行あることを確認してから 1 度だけ出す。無い・複数・parse 不可のときだけ shell fallback を出す |
| F-2 | 実測結果でなく request ID で分岐する projection | B-4 | R1 は approval の到達可否に関係なく `projected_outcome="approval-bound"` を書く。**2 本目が届かない実測で JSON が「承認束縛済み」と言い、同じ JSON の `official_approval_bound=false` と矛盾する。** 観測値から導出し、categorical 値と bool の整合を invariant にする |
| F-3 | 未承認 driver の argv 完全一致がない | A-5 / B-8 | 事前登録は完全一致を要求した。現状は rc と文言だけを見るので `--resume PATH` を足しても緑。observer と test の双方で argv を固定配列へ完全一致させる |
| F-4 | 実行時の source identity が固定 SHA に束縛されていない | A-3 / B-2 | queue 待ちの間に submit-tree の tracked file が変わると、変わった後の `s8b_floor_campaign.py` を実行して緑になる。job 開始時に HEAD・detached・tracked-clean・untracked 空を再確認し、実行する campaign source と PBS の bytes を hash 束縛する |
| F-5 | 非干渉 preflight が内容を判定していない | A-1 / B-5 | rc しか見ないので `gen_S` が DIS/INA でも進む。qsub 後の可視性確認も無い。queue の semantic state を parse して停止条件にし、各 qsub 後に `qstat` 本文で request を確認する |
| F-6 | group manifest が途中失敗を記録できず完了へ遷移できない | A-2 / B-3 | 最初の qsub より前に create-only の group intent を書き、request ごとの受付 sidecar を残す。terminal state と結果 hash は別の回収段で確定する。**新しい実行 gate は作らない** |
| F-7 | 投入側に core dump 防止が無い | B-6 | submitter 冒頭で `ulimit -c 0`。preflight は repo 外の cwd で行い、各 qsub 直前と終了時に repo clean を再確認する |
| F-8 | test が実装定数を fixture へ戻して恒真化している | B-8 | 独立した literal contract を test 側に固定する。observer 側だけ変えても test が追随して緑になる状態を解く |
| F-9 | 「緑でも言えないこと」の専用節が無い | A-6 | **これは実装でなく記録の仕事**なので段 7 で親が insight へ書く。fix 子には出さない |

## 3. scope の確認

追加した機構はいずれも段 4 裁定が既に要求していたもの (exact 束縛・一次 evidence の stdout 化・
group 完了判定・queue 非干渉) の**実効化**であり、新しい一般化ではない。
ユーザーが scope 外とした「仮想リスク向けの gate・検査・台帳・一般化」には当たらない。
`test_hooks.py` の期待辞書は submitter entry を外す方向にだけ動く (受理集合は縮む)。

## 4. 変異事前登録の改訂 (DW-M07)

段 4 §4 の 12 件のうち、submitter を repo から外すことで M-11 の対象が減る。
fix 後の最終 commit で anchor と期待 node を再検証してから本走する。
F-1 / F-2 / F-3 は新しい実効 gate なので変異を足す。

| ID | 変異位置 | 期待 kill |
|---|---|---|
| M-13 | PBS の「prefixed 行がちょうど 1 行」検査を「1 行以上」へ緩める | 新 test の二重出力負例 |
| M-14 | projection を観測値でなく request ID から決める形へ戻す | 新 test の「届かない R1」負例 |
| M-15 | 未承認 driver の argv 完全一致を部分一致へ緩める | 新 test の余分 argv 負例 |
