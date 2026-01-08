"""Add AI assistant tables

Revision ID: 002_add_ai_assistant_tables
Revises: 001_add_oauth2_support
Create Date: 2026-01-07 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_ai_assistant_tables'
down_revision = '001_add_oauth2_support'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### Create email_message table ###
    op.create_table(
        'email_message',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.String(length=255), nullable=False),
        sa.Column('thread_id', sa.String(length=255), nullable=False),
        sa.Column('subject', sa.String(length=500), nullable=False),
        sa.Column('from_email', sa.String(length=255), nullable=False),
        sa.Column('to_email', sa.String(length=255), nullable=False),
        sa.Column('cc_emails', sa.Text(), nullable=True),
        sa.Column('bcc_emails', sa.Text(), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('snippet', sa.String(length=500), nullable=True),
        sa.Column('classification', sa.String(length=50), nullable=True),
        sa.Column('ai_analysis', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_message_message_id'), 'email_message', ['message_id'], unique=True)
    op.create_index(op.f('ix_email_message_thread_id'), 'email_message', ['thread_id'], unique=False)
    op.create_index(op.f('ix_email_message_user_id'), 'email_message', ['user_id'], unique=False)
    op.create_index(op.f('ix_email_message_from_email'), 'email_message', ['from_email'], unique=False)

    # ### Create draft_reply table ###
    op.create_table(
        'draft_reply',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email_message_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('draft_content', sa.Text(), nullable=False),
        sa.Column('original_draft', sa.Text(), nullable=False),
        sa.Column('ai_model_used', sa.String(length=100), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=False),
        sa.Column('analysis_context', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['email_message_id'], ['email_message.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_draft_reply_email_message_id'), 'draft_reply', ['email_message_id'], unique=False)
    op.create_index(op.f('ix_draft_reply_user_id'), 'draft_reply', ['user_id'], unique=False)
    op.create_index(op.f('ix_draft_reply_status'), 'draft_reply', ['status'], unique=False)

    # ### Create calendar_event table ###
    op.create_table(
        'calendar_event',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email_message_id', sa.Integer(), nullable=True),
        sa.Column('google_event_id', sa.String(length=255), nullable=False),
        sa.Column('calendar_id', sa.String(length=255), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=500), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False),
        sa.Column('is_all_day', sa.Boolean(), nullable=False),
        sa.Column('attendees', sa.Text(), nullable=True),
        sa.Column('created_from_email', sa.Boolean(), nullable=False),
        sa.Column('auto_created', sa.Boolean(), nullable=False),
        sa.Column('confidence_score', sa.Float(), nullable=True),
        sa.Column('notification_sent', sa.Boolean(), nullable=False),
        sa.Column('notification_sent_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('synced_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['email_message_id'], ['email_message.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendar_event_google_event_id'), 'calendar_event', ['google_event_id'], unique=True)
    op.create_index(op.f('ix_calendar_event_user_id'), 'calendar_event', ['user_id'], unique=False)
    op.create_index(op.f('ix_calendar_event_email_message_id'), 'calendar_event', ['email_message_id'], unique=False)
    op.create_index(op.f('ix_calendar_event_created_from_email'), 'calendar_event', ['created_from_email'], unique=False)

    # ### Create notification_preference table ###
    op.create_table(
        'notification_preference',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('email_notifications', sa.Boolean(), nullable=False),
        sa.Column('push_notifications', sa.Boolean(), nullable=False),
        sa.Column('notify_15_min_before', sa.Boolean(), nullable=False),
        sa.Column('notify_1_hour_before', sa.Boolean(), nullable=False),
        sa.Column('notify_1_day_before', sa.Boolean(), nullable=False),
        sa.Column('notify_new_draft', sa.Boolean(), nullable=False),
        sa.Column('notify_calendar_event_created', sa.Boolean(), nullable=False),
        sa.Column('notify_email_classified', sa.Boolean(), nullable=False),
        sa.Column('auto_approve_high_confidence', sa.Boolean(), nullable=False),
        sa.Column('confidence_threshold', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_preference_user_id'), 'notification_preference', ['user_id'], unique=True)

    # ### Create gmail_watch_subscription table ###
    op.create_table(
        'gmail_watch_subscription',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('history_id', sa.BigInteger(), nullable=False),
        sa.Column('expiration', sa.DateTime(timezone=True), nullable=False),
        sa.Column('topic_name', sa.String(length=255), nullable=False),
        sa.Column('subscription_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_renewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('renewal_failures', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_gmail_watch_subscription_user_id'), 'gmail_watch_subscription', ['user_id'], unique=True)
    op.create_index(op.f('ix_gmail_watch_subscription_is_active'), 'gmail_watch_subscription', ['is_active'], unique=False)

    # ### Create push_subscription table ###
    op.create_table(
        'push_subscription',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('endpoint', sa.Text(), nullable=False),
        sa.Column('p256dh_key', sa.String(length=255), nullable=False),
        sa.Column('auth_key', sa.String(length=255), nullable=False),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('device_name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('failure_count', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_push_subscription_endpoint'), 'push_subscription', ['endpoint'], unique=True)
    op.create_index(op.f('ix_push_subscription_user_id'), 'push_subscription', ['user_id'], unique=False)
    op.create_index(op.f('ix_push_subscription_is_active'), 'push_subscription', ['is_active'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### Drop all tables ###
    op.drop_index(op.f('ix_push_subscription_is_active'), table_name='push_subscription')
    op.drop_index(op.f('ix_push_subscription_user_id'), table_name='push_subscription')
    op.drop_index(op.f('ix_push_subscription_endpoint'), table_name='push_subscription')
    op.drop_table('push_subscription')

    op.drop_index(op.f('ix_gmail_watch_subscription_is_active'), table_name='gmail_watch_subscription')
    op.drop_index(op.f('ix_gmail_watch_subscription_user_id'), table_name='gmail_watch_subscription')
    op.drop_table('gmail_watch_subscription')

    op.drop_index(op.f('ix_notification_preference_user_id'), table_name='notification_preference')
    op.drop_table('notification_preference')

    op.drop_index(op.f('ix_calendar_event_created_from_email'), table_name='calendar_event')
    op.drop_index(op.f('ix_calendar_event_email_message_id'), table_name='calendar_event')
    op.drop_index(op.f('ix_calendar_event_user_id'), table_name='calendar_event')
    op.drop_index(op.f('ix_calendar_event_google_event_id'), table_name='calendar_event')
    op.drop_table('calendar_event')

    op.drop_index(op.f('ix_draft_reply_status'), table_name='draft_reply')
    op.drop_index(op.f('ix_draft_reply_user_id'), table_name='draft_reply')
    op.drop_index(op.f('ix_draft_reply_email_message_id'), table_name='draft_reply')
    op.drop_table('draft_reply')

    op.drop_index(op.f('ix_email_message_from_email'), table_name='email_message')
    op.drop_index(op.f('ix_email_message_user_id'), table_name='email_message')
    op.drop_index(op.f('ix_email_message_thread_id'), table_name='email_message')
    op.drop_index(op.f('ix_email_message_message_id'), table_name='email_message')
    op.drop_table('email_message')
    # ### end Alembic commands ###
