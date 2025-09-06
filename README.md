# 📱 Receipt Print Service

スマホから選択した画像をプリントできるWebサービスです。

## 🚀 機能

- スマホ対応のレスポンシブUI
- ドラッグ&ドロップでの画像アップロード  
- 画像プレビュー機能
- プリント実行機能
- リアルタイムステータス表示

## 🛠 技術スタック

- **バックエンド**: Python + FastAPI
- **フロントエンド**: HTML + CSS + JavaScript (静的ファイル)
- **コンテナ**: Docker + Docker Compose

## 📋 必要要件

- Docker
- Docker Compose

## 🚀 起動方法

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd receipt-print
```

### 2. 環境変数の設定

```bash
cp .env.example .env
```

`.env` ファイルを編集:

```bash
# プリンターAPIホスト
API_HOST=http://your-printer-api:8080

# Cloudflareトンネルトークン（Cloudflareダッシュボードから取得）
CLOUDFLARE_TUNNEL_TOKEN=eyJh...（長いトークン文字列）
```

### 3. Docker Composeで起動

```bash
docker-compose up -d
```

### 4. ブラウザでアクセス

```
http://localhost:3000
```

## 📊 API エンドポイント

### アップロード
- **POST** `/api/upload`
- 画像ファイルをアップロードしてJob IDを取得

### プリント実行  
- **POST** `/api/print/{jobId}`
- 指定したJob IDの画像をプリント

### ステータス確認
- **GET** `/api/status/{jobId}`
- プリントジョブのステータスを確認

## 🔧 設定

### API_HOST 環境変数

プリンターAPIのホストURLを指定します:

```bash
# Docker Composeの場合
API_HOST=http://printer-api:8080

# ローカル開発の場合  
API_HOST=http://localhost:8080

# 外部サービスの場合
API_HOST=https://your-printer-api.com
```

## 📱 使い方

1. ブラウザで `http://localhost:3000` にアクセス
2. 「画像をクリックして選択」または画像をドラッグ&ドロップ
3. 画像プレビューを確認
4. 「画像をアップロード」ボタンをクリック
5. アップロード完了後、「プリント実行」ボタンをクリック
6. プリント完了まで待機

## 🔍 トラブルシューティング

### プリンターAPIに接続できない場合

1. API_HOST環境変数が正しく設定されているか確認
2. プリンターAPIが起動しているか確認
3. ネットワーク接続を確認

### 画像アップロードが失敗する場合

1. ファイルが画像形式（JPG、PNG、GIF）か確認
2. ファイルサイズが10MB以下か確認
3. ブラウザのコンソールでエラーログを確認

## 📝 開発

### ローカル開発

```bash
# Python環境のセットアップ
pip install -r requirements.txt

# 開発サーバー起動
python main.py
```

### ログ確認

```bash
docker-compose logs -f web
```

## 🌐 Cloudflare Tunnel で公開

### 1. Cloudflare Tunnel の作成

```bash
# Cloudflared をインストール
# https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/

# トンネルを作成
cloudflared tunnel create receipt-print-service
```

### 2. 認証情報の設定

```bash
# 生成された credentials.json をコピー
cp ~/.cloudflared/<tunnel-id>.json ./cloudflared-credentials.json
```

### 3. ドメインの設定

`cloudflared.yml` を編集:

```yaml
tunnel: receipt-print-service
credentials-file: /root/.cloudflared/cert.pem

ingress:
  - hostname: your-domain.com  # ← あなたのドメインに変更
    service: http://localhost:3000
  - service: http_status:404
```

### 4. DNS レコードの追加

```bash
cloudflared tunnel route dns receipt-print-service your-domain.com
```

### 5. 起動

```bash
docker-compose up -d
```

これで `https://your-domain.com` でスマホから世界中どこからでもアクセス可能！

### セットアップスクリプト

```bash
./setup-cloudflare-tunnel.sh
```

詳細な手順とトラブルシューティングガイドが表示されます。