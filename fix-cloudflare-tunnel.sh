#!/bin/bash

echo "🔧 Cloudflare Tunnel トラブルシューティング"
echo ""

echo "1. DNSレコードの確認と作成..."
echo "以下のコマンドを実行してDNSレコードを作成してください:"
echo ""
echo "cloudflared tunnel route dns e60ca077-d425-43a3-90ab-711dd32475fc receipt-print.ueckoken.club"
echo ""

echo "2. 現在のDNSレコードを確認:"
echo "dig receipt-print.ueckoken.club"
echo ""

echo "3. Cloudflareのトンネル状態を確認:"
echo "cloudflared tunnel list"
echo ""

echo "4. DNSが正しく設定されたら、コンテナを再起動:"
echo "docker-compose restart cloudflared"
echo ""

echo "5. ログを確認:"
echo "docker-compose logs -f cloudflared"
echo ""

echo "📋 確認事項:"
echo "- Cloudflareダッシュボードでトンネルが表示されているか"
echo "- DNSレコードが正しく設定されているか" 
echo "- ドメイン (receipt-print.ueckoken.club) がCloudflareで管理されているか"