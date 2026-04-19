[README.md](https://github.com/user-attachments/files/26864553/README.md)
# 金買取価格比較表 セットアップ手順

## 用意するもの
- GitHubアカウント（無料）→ https://github.com/

---

## STEP 1｜GitHubでリポジトリを作る

1. GitHubにログインして右上の「+」→「New repository」をクリック
2. Repository name に「gold-price」と入力
3. Public を選択
4. 「Create repository」をクリック

---

## STEP 2｜ファイルをアップロードする

作成したリポジトリのページで「Add file」→「Upload files」をクリックし、
以下の3つのファイルをアップロードする。

- scraper.py
- gold_prices.json
- .github/workflows/update.yml ← フォルダごとアップロード

※ .github/workflows/ フォルダは「Add file」→「Create new file」で
  ファイル名に「.github/workflows/update.yml」と入力すると作れる

---

## STEP 3｜GitHub Actionsを有効にする

1. リポジトリの「Actions」タブをクリック
2. 「I understand my workflows, go ahead and enable them」をクリック
3. 左メニューの「金買取価格 毎日自動更新」をクリック
4. 「Run workflow」→「Run workflow」で手動実行してテスト
5. 実行後、gold_prices.json が更新されていればOK

---

## STEP 4｜WordPressに設定する

### 4-1. functions.phpにショートコードを追加

1. WordPressの管理画面 →「外観」→「テーマエディター」
2. 右側のファイル一覧から「functions.php」を選択
3. functions_snippet.php の内容を末尾にコピペ
4. コピペ後、以下の部分を自分のものに書き換える

```
define('GOLD_PRICE_JSON_URL', 'https://raw.githubusercontent.com/YOUR_GITHUB_USERNAME/YOUR_REPO_NAME/main/gold_prices.json');
```

↓ 例：GitHubユーザー名が「yamada-taro」、リポジトリ名が「gold-price」の場合

```
define('GOLD_PRICE_JSON_URL', 'https://raw.githubusercontent.com/yamada-taro/gold-price/main/gold_prices.json');
```

5. 「ファイルを更新」をクリック

### 4-2. ページに貼り付ける

比較表を表示したいページの本文に以下を貼るだけ。

```
[gold_price_table]
```

---

## 自動更新のスケジュール

- 平日（月〜金）の毎朝9時に自動実行
- 土日祝は実行されない（各社も更新しないため）
- GitHubの「Actions」タブでいつでも手動実行できる

---

## トラブルが起きたとき

### 価格が表示されない
→ GitHubのActionsタブで「Run workflow」を手動実行してみる
→ 実行後に gold_prices.json を開いて価格が入っているか確認

### 特定の業者だけ取得できていない
→ その業者がサイトのデザインを変更した可能性あり
→ Claudeに「◯◯の価格が取れなくなった」と伝えてスクリプトを修正してもらう

---

## ファイル構成（GitHubに置くもの）

```
gold-price/
├── scraper.py           ← 価格取得スクリプト
├── gold_prices.json     ← 価格データ（自動更新される）
└── .github/
    └── workflows/
        └── update.yml   ← 自動実行の設定
```
