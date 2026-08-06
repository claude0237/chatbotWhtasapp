"""Update bot to NATIVE mode using direct SQL"""
import asyncio
import asyncpg

async def update_bot():
    conn = await asyncpg.connect(
        'postgresql://postgres:postgres@localhost:5432/whatsapp_saas'
    )
    
    try:
        result = await conn.execute(
            "UPDATE bot_configurations SET bot_type = 'NATIVE', ml_enabled = false WHERE company_id = '229de9d2-46cc-4681-82e9-f54670870369';"
        )
        print('✅ Bot configuré en mode NATIF')
    except Exception as e:
        print(f'❌ Erreur: {e}')
    finally:
        await conn.close()

asyncio.run(update_bot())
