"""Migrate WhatsApp credentials from .env to channel_configurations per tenant"""
import asyncio
import uuid
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from app.config import settings
from app.channels.models import Channel, ChannelConfiguration, ChannelCredential, ChannelType
from app.companies.models import Company
from app.utils.encryption import encrypt_credential
from datetime import datetime

# Database setup
engine = create_async_engine(settings.database_url)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def migrate_whatsapp_configs():
    """Migrate WhatsApp credentials from .env to database"""
    async with async_session() as session:
        try:
            # Get all companies
            result = await session.execute(select(Company))
            companies = result.scalars().all()
            
            print(f"Found {len(companies)} companies")
            
            for company in companies:
                print(f"\nProcessing company: {company.name} ({company.id})")
                
                # Check if WhatsApp channel exists
                channel_result = await session.execute(
                    select(Channel).where(
                        Channel.company_id == company.id,
                        Channel.channel_type == ChannelType.WHATSAPP
                    )
                )
                channel = channel_result.scalar_one_or_none()
                
                if not channel:
                    print(f"  - No WhatsApp channel found, creating one...")
                    channel = Channel(
                        company_id=company.id,
                        channel_type=ChannelType.WHATSAPP,
                        name="WhatsApp Channel",
                        status="ACTIVE"
                    )
                    session.add(channel)
                    await session.flush()
                    print(f"  - Created channel: {channel.id}")
                else:
                    print(f"  - Existing channel: {channel.id}")
                
                # Check if configurations already exist
                config_result = await session.execute(
                    select(ChannelConfiguration).where(
                        ChannelConfiguration.channel_id == channel.id
                    )
                )
                existing_configs = config_result.scalars().all()
                existing_keys = {c.key for c in existing_configs}
                
                # Configuration keys to add
                configs_to_add = []
                
                # For System company, use values from .env
                if company.name == "System":
                    print("  - Using .env values for System company")
                    
                    if "meta_app_id" not in existing_keys:
                        configs_to_add.append(ChannelConfiguration(
                            channel_id=channel.id,
                            key="meta_app_id",
                            value=settings.meta_app_id if hasattr(settings, 'meta_app_id') else "1512138164296574"
                        ))
                    
                    if "meta_business_id" not in existing_keys:
                        configs_to_add.append(ChannelConfiguration(
                            channel_id=channel.id,
                            key="meta_business_id",
                            value=settings.meta_business_id if hasattr(settings, 'meta_business_id') else "232803093077664"
                        ))
                    
                    if "phone_number_id" not in existing_keys:
                        configs_to_add.append(ChannelConfiguration(
                            channel_id=channel.id,
                            key="phone_number_id",
                            value=settings.whatsapp_phone_number_id if hasattr(settings, 'whatsapp_phone_number_id') else ""
                        ))
                    
                    if "webhook_verify_token" not in existing_keys:
                        # Generate unique webhook verify token
                        verify_token = f"verify_{company.id}_{uuid.uuid4().hex[:8]}"
                        configs_to_add.append(ChannelConfiguration(
                            channel_id=channel.id,
                            key="webhook_verify_token",
                            value=verify_token
                        ))
                        print(f"  - Generated webhook_verify_token: {verify_token}")
                else:
                    print("  - Using placeholder values for non-System company")
                    
                    if "meta_app_id" not in existing_keys:
                        configs_to_add.append(ChannelConfiguration(
                            channel_id=channel.id,
                            key="meta_app_id",
                            value=""
                        ))
                    
                    if "meta_business_id" not in existing_keys:
                        configs_to_add.append(ChannelConfiguration(
                            channel_id=channel.id,
                            key="meta_business_id",
                            value=""
                        ))
                    
                    if "phone_number_id" not in existing_keys:
                        configs_to_add.append(ChannelConfiguration(
                            channel_id=channel.id,
                            key="phone_number_id",
                            value=""
                        ))
                    
                    if "webhook_verify_token" not in existing_keys:
                        verify_token = f"verify_{company.id}_{uuid.uuid4().hex[:8]}"
                        configs_to_add.append(ChannelConfiguration(
                            channel_id=channel.id,
                            key="webhook_verify_token",
                            value=verify_token
                        ))
                        print(f"  - Generated webhook_verify_token: {verify_token}")
                
                # Add configurations
                for config in configs_to_add:
                    session.add(config)
                    print(f"  - Added config: {config.key}")
                
                # Check if credentials already exist
                cred_result = await session.execute(
                    select(ChannelCredential).where(
                        ChannelCredential.channel_id == channel.id
                    )
                )
                existing_creds = cred_result.scalars().all()
                existing_cred_types = {c.credential_type for c in existing_creds}
                
                # Credentials to add
                creds_to_add = []
                
                # For System company, encrypt and add META_APP_SECRET and ACCESS_TOKEN
                if company.name == "System":
                    if "META_APP_SECRET" not in existing_cred_types:
                        app_secret = settings.meta_app_secret if hasattr(settings, 'meta_app_secret') else "22bc8b15890777fc545593241396fb46"
                        encrypted = encrypt_credential(app_secret)
                        creds_to_add.append(ChannelCredential(
                            channel_id=channel.id,
                            credential_type="META_APP_SECRET",
                            encrypted_value=encrypted,
                            iv=None
                        ))
                        print(f"  - Added META_APP_SECRET credential")
                    
                    if "ACCESS_TOKEN" not in existing_cred_types:
                        access_token = settings.whatsapp_access_token if hasattr(settings, 'whatsapp_access_token') else ""
                        if access_token:
                            encrypted = encrypt_credential(access_token)
                            creds_to_add.append(ChannelCredential(
                                channel_id=channel.id,
                                credential_type="ACCESS_TOKEN",
                                encrypted_value=encrypted,
                                iv=None
                            ))
                            print(f"  - Added ACCESS_TOKEN credential")
                else:
                    # Placeholder for other companies
                    if "META_APP_SECRET" not in existing_cred_types:
                        creds_to_add.append(ChannelCredential(
                            channel_id=channel.id,
                            credential_type="META_APP_SECRET",
                            encrypted_value="",
                            iv=None
                        ))
                    
                    if "ACCESS_TOKEN" not in existing_cred_types:
                        creds_to_add.append(ChannelCredential(
                            channel_id=channel.id,
                            credential_type="ACCESS_TOKEN",
                            encrypted_value="",
                            iv=None
                        ))
                
                # Add credentials
                for cred in creds_to_add:
                    session.add(cred)
                
                await session.commit()
                print(f"  ✓ Migration completed for {company.name}")
            
            print("\n✅ All migrations completed successfully!")
            
        except Exception as e:
            await session.rollback()
            print(f"\n❌ Error during migration: {e}")
            raise

if __name__ == "__main__":
    asyncio.run(migrate_whatsapp_configs())
