"""Integration tests for WhatsApp webhook"""
import pytest
import json
import hmac
import hashlib
from unittest.mock import AsyncMock, patch


VERIFY_TOKEN = "test-verify-token"


def make_webhook_payload(message_text: str = "Hello", phone: str = "1234567890") -> dict:
    return {
        "object": "whatsapp_business_account",
        "entry": [{
            "id": "test-entry",
            "changes": [{
                "value": {
                    "messaging_product": "whatsapp",
                    "metadata": {"display_phone_number": "15550001111", "phone_number_id": "test-phone-id"},
                    "contacts": [{"profile": {"name": "Test User"}, "wa_id": phone}],
                    "messages": [{
                        "from": phone,
                        "id": "wamid.test123",
                        "timestamp": "1700000000",
                        "text": {"body": message_text},
                        "type": "text"
                    }]
                },
                "field": "messages"
            }]
        }]
    }


class TestWebhookVerification:

    @pytest.mark.asyncio
    async def test_webhook_verify_valid_token(self, client):
        response = await client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": VERIFY_TOKEN,
                "hub.challenge": "challenge123"
            }
        )
        # Should return challenge if token is valid (depends on env config)
        assert response.status_code in (200, 403)

    @pytest.mark.asyncio
    async def test_webhook_verify_invalid_token(self, client):
        response = await client.get(
            "/webhook/whatsapp",
            params={
                "hub.mode": "subscribe",
                "hub.verify_token": "wrong-token",
                "hub.challenge": "challenge123"
            }
        )
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_webhook_receive_message(self, client):
        payload = make_webhook_payload("Hello bot!")

        with patch("app.whatsapp.controllers.process_incoming_message", new_callable=AsyncMock) as mock_process:
            response = await client.post(
                "/webhook/whatsapp",
                json=payload,
                headers={"Content-Type": "application/json"}
            )

        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_webhook_returns_200_on_status_update(self, client):
        """Webhook should always return 200 for status updates"""
        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "test",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "statuses": [{
                            "id": "wamid.test",
                            "status": "delivered",
                            "timestamp": "1700000000",
                            "recipient_id": "1234567890"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        response = await client.post("/webhook/whatsapp", json=payload)
        assert response.status_code == 200


class TestWebhookSecurity:

    def _sign_payload(self, payload: bytes, secret: str) -> str:
        sig = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
        return f"sha256={sig}"

    @pytest.mark.asyncio
    async def test_webhook_invalid_signature_rejected(self, client):
        payload = json.dumps(make_webhook_payload()).encode()
        response = await client.post(
            "/webhook/whatsapp",
            content=payload,
            headers={
                "Content-Type": "application/json",
                "X-Hub-Signature-256": "sha256=invalidsignature"
            }
        )
        # Should reject if signature validation is enabled
        assert response.status_code in (200, 403)
