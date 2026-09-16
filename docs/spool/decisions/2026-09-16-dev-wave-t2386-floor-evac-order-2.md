---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t2386-floor-evac-order
seq: 2
---

## {{D:floor-evacuation-order-one-way}}. official 床値成果物の退避と再配置は一方向の順序とし、再配置後の commit を candidate 生成の必要条件として扱う

**決定:** official 床値の走行フェーズと candidate 生成フェーズを分け、次の順序で運用する。

1. official を走らせ、`floor_campaign.sh` の driver 終了後検査が終わって wrapper が終了するまで待つ。
2. 当該 env の official namespace 全体を repo 外へ退避する。run directory と、空になった
   namespace directory を repo から除去する。
3. 次の official 起動は従来どおり clean scan に従う。**退避の成功は起動証明の代用ではなく、
   痕跡を消してよかったことの証明でもない。**
4. その holdout 集合の official 走行を**打ち切ると決めてから**、namespace 全体を元の repo 相対位置へ
   戻す。run・時刻・proto8 を選ぶ口は設けない。
5. 戻した成果物を commit する。
6. candidate を生成する。
7. **この commit を持つ branch では以後 official 床値を起動できない。**

**理由:**

- `_load_repo_object` と `parse_official_run_path` が repo 相対の official path を要求する一方、
  `clean_scan_digest` は repo 全域 (tracked と `--exclude-standard` を通った untracked の両方) で
  holdout の三軸 conjunction hit 0 件を要求する。除外は freeze namespace 1 件だけで、official run
  directory を入れる口はない。したがって同じ artifact について「在る」と「無い」を同時には
  満たせず、時間で分けるほかない。
- 再配置後の commit は運用上の都合ではなく機構の要求である。`_measurement_closure` は専用 6 path
  以外の走査 hit に captured HEAD の blob 一致を要求し、批准側の `_verify_generation_semantics` は
  世代 commit の tree に blob が実在し worktree が HEAD blob と一致することを要求する。
- 7 は 5 の帰結であって新しい制約ではない。成果物が repo に在る以上、以後の clean scan は正しく
  赤になる。これを避けるために除外や allowlist を広げることは絶対規律 2 に反する。

**却下した選択肢:**

- clean scan の除外集合 / freeze allowlist に official run directory を加える — 起動証明が
  意味を失う。allowlist は freeze namespace 専用の有界集合であり、そもそもこの用途の口ではない。
- 読取り側を repo 外の絶対 path に対応させる — official path であることの証明が exact 文法に
  依存しているため、path の official 性が失われる。
- 走行のたびに成果物を commit する — 以後の official 起動が恒久的に不可能になる。順序を
  一方向にする価値が消える。

## {{D:floor-evacuation-bundle-root-fixed}}. 床値退避先は git common dir 配下へ固定導出し、引数でも環境変数でも差し替えられないようにする

**決定:** 退避先を `<git common dir>/izanagi/s8b-floor-evacuation/<env_tag>/` に固定導出する。
退避側と再配置側は同じ導出を使い、退避先・run・時刻・proto8 を選ぶ引数を持たない。導出に使う
git 呼出しの環境からは、repository の選択・探索・設定を変えうる Git の環境変数を除去する。

**理由:**

- 「部分復元の口を作らない」だけでは足りない。退避先が呼出し引数である限り、run A を bundle X へ、
  run B を bundle Y へ退避し、Y だけを戻せば、最古適格 run 判定は B だけを見て通る。候補の
  `floor_source` と床値が A から B へ変わる。選択の口を API から構造的に消すほかない。
- D475 が失敗 artifact の退避について「退避先の root も固定し、環境変数による上書きを設けない」と
  既に定めており、同じ形を採る。
- 共有 admission 台帳が同じ git common dir 配下に在り、earlier run の適格性はその台帳から
  再導出される。bundle の寿命を台帳の寿命に合わせるのは正しい結合である。台帳が消えれば適格性は
  どのみち導出できない。
- git common dir は worktree の file 列挙に出ないので走査に hit せず、かつ全 worktree 共有なので
  使い捨ての測定木を捨てても payload が残る。

**残余 (主張しない限界):**

- filesystem を直接操作して bundle を差し替える攻撃は検出できない。共有 admission 台帳が既に
  「台帳を削除して同一 bytes を再構成する攻撃は検出できない」と宣言している残余と同じ類である。
- 除去する Git 環境変数は列挙方式であり、未列挙の変数まで包括的に無効化する保証ではない。
  現行の迂回変数を確認したわけではないが、列挙の限界は限界として記す。
- 公開と巻戻しが連続して失敗した場合、累積 bytes は耐久 path に保持され例外本文がその場所を
  名指しするが、正規位置への復旧は手動である。

**却下した選択肢:**

- 退避先を引数のまま残し、運用規約で「同じ bundle を使う」と約束する — 規約は機構ではない。
  敵対相談が具体的な操作列を示した。
- 共有 admission 台帳の run 集合と bundle の run 集合を突き合わせる検査を新設する — 本課題の
  scope 外であり、固定導出で口自体が消えるなら検査は要らない。
