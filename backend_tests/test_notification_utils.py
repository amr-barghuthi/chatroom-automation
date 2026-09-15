from unittest.mock import AsyncMock, patch

from django.db import IntegrityError, transaction
from django.test import TestCase

from apis.chatroom_dispatcher.chatroom_dispatcher_model import ChatroomDispatchConfig
from apis.company.company_model import Company
from apis.connectors.connectors_model import Connectors, Tenant
from apis.conversation.conversation_models import Conversation
from apis.lookup.lookup_models import ConversationStage
from apis.message.message_models import Message
from apis.notification.notification_model import Notification
from apis.notification.notification_utils import (
    create_chatroom_notifications_payload,
    create_new_message_notifications_payload,
)
from apis.role.role_model import Role
from apis.settings.settings_model import ChatroomNotification, NewMessageNotificationSettings
from apis.user.user_model import User


class NotificationBusinessLogicTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Django isolates these shared fixtures so changes in one test do not affect another.
        cls.company = Company.objects.create(company_name="Notifications QA", company_mobile="10001")
        other_company = Company.objects.create(company_name="Other QA", company_mobile="10002")
        # Separate agent and owner records let us verify which assignment receives the alert.
        # English keeps the expected notification titles consistent.
        cls.agent = User.objects.create(company=cls.company, name="Agent", mobile_number="101", lang="en")
        cls.owner = User.objects.create(company=cls.company, name="Owner", mobile_number="102", lang="en")
        # These users must be excluded from fallback and mention notifications.
        cls.inactive = User.objects.create(company=cls.company, name="Inactive", mobile_number="103", is_active=False)
        cls.outsider = User.objects.create(company=other_company, name="Outsider", mobile_number="104")
        # The connector identifies the conversation's company and requires a tenant.
        tenant = Tenant.objects.create(company=cls.company, name="QA")
        connector = Connectors.objects.create(company=cls.company, tenant=tenant, connector_name="QA", connector_type="whatsapp")
        cls.stage = ConversationStage.objects.create(name="Notification QA")
        cls.conversation = Conversation.objects.create(
            name="Customer", number="20001", default_connector=connector,
            stage=cls.stage, agent=cls.agent, contact_owner=cls.owner,
        )
        cls.conversation.connectors.add(connector)
        # New-message notifications require settings that include the conversation's stage.
        cls.preferences = NewMessageNotificationSettings.objects.create(
            company=cls.company, enabled=True,
            recipient=NewMessageNotificationSettings.RECIPIENT_AGENT,
        )
        cls.preferences.stages.add(cls.stage)

    def setUp(self):
        # Keep database writes real, but prevent external delivery.
        # enterContext restores each patched function automatically after the test.
        self.push = self.enterContext(patch("apis.notification.notification_utils._send_onesignal_push"))
        # These payload functions do not currently broadcast; guard the channel boundary too.
        channel_layer = self.enterContext(patch("apis.notification.notification_utils.get_channel_layer"))
        channel_layer.return_value.group_send = AsyncMock()
        # No message row is needed: notification creation only reads these fields.
        self.message = Message(conversation=self.conversation, text="Please help", ttype="text", from_me=False)

    def new_message(self, **kwargs):
        # Exercise the production entry point with this test's conversation and incoming message.
        return create_new_message_notifications_payload(self.conversation, self.message, **kwargs)

    def assert_recipients(self, payload, users, title, message):
        expected_ids = [user.id for user in users]
        records = Notification.objects.filter(conversation=self.conversation)
        # Database recipients and returned payload must agree, with no extra or duplicate alerts.
        self.assertCountEqual(records.values_list("user_id", flat=True), expected_ids)
        self.assertCountEqual(payload["notification_event"]["target_user_ids"], expected_ids)
        self.assertCountEqual([row["id"] for row in payload["notifications"]], records.values_list("id", flat=True))
        self.assertEqual(payload["notification_event"]["conversation_id"], self.conversation.id)
        self.assertEqual(payload["notification_event"]["title"], title)
        self.assertEqual(payload["notification_event"]["message"], message)
        # Every notification starts unread and points back to the correct conversation.
        for record in records:
            self.assertFalse(record.seen)
            self.assertEqual(record.conversation_ids, [self.conversation.id])
            self.assertEqual(record.title, title)
            self.assertEqual(record.message, message)
        # Pushes may be grouped; collect recipients across all calls without assuming order.
        self.assertTrue(self.push.called)
        self.assertCountEqual(
            [user.id for call in self.push.call_args_list for user in call.args[3]], expected_ids,
        )

    def assert_no_notification(self, payload):
        # Suppression must leave no payload, saved notification, or push attempt.
        self.assertEqual(payload, {"notifications": [], "notification_event": None})
        self.assertFalse(Notification.objects.exists())
        self.push.assert_not_called()

    def test_new_message_notifies_only_assigned_agent(self):
        # Both assignments exist, but the configured recipient is the agent.
        self.assert_recipients(self.new_message(), [self.agent], "New message from Customer", "Please help")

    def test_new_message_notifies_only_contact_owner_when_configured(self):
        # Switching the setting selects the owner even though an agent is also assigned.
        self.preferences.recipient = NewMessageNotificationSettings.RECIPIENT_CONTACT_OWNER
        self.preferences.save()
        self.assert_recipients(self.new_message(), [self.owner], "New message from Customer", "Please help")

    def test_unassigned_fallback_notifies_active_company_users_even_if_assignee_setting_disabled(self):
        # Fallback has its own switch and works independently of assignee notifications.
        # No dispatcher config is needed when dispatching is disabled.
        self.conversation.agent = None
        self.conversation.contact_owner = None
        self.preferences.enabled = False
        self.preferences.notify_all_users_on_new_conversation = True
        self.preferences.save()
        self.assert_recipients(self.new_message(), [self.agent, self.owner], "New message from Customer", "Please help")

    def test_unassigned_fallback_requires_opt_in(self):
        # An unassigned conversation alone is insufficient: fallback defaults to off.
        self.conversation.agent = None
        self.conversation.contact_owner = None
        self.assert_no_notification(self.new_message())

    def test_enabled_dispatcher_suppresses_unassigned_fallback(self):
        # Enabling dispatching prevents the all-user fallback, even when opted in.
        self.conversation.agent = None
        self.conversation.contact_owner = None
        self.preferences.notify_all_users_on_new_conversation = True
        self.preferences.save()
        ChatroomDispatchConfig.objects.create(company=self.company, is_enabled=True)
        self.assert_no_notification(self.new_message())

    def test_fallback_does_not_broadcast_when_either_assignment_exists(self):
        self.preferences.enabled = False
        self.preferences.notify_all_users_on_new_conversation = True
        self.preferences.save()
        # Disable direct alerts above to isolate fallback: either assignment blocks it.
        for agent, owner in ((self.agent, None), (None, self.owner)):
            with self.subTest(agent=agent, owner=owner):
                self.conversation.agent = agent
                self.conversation.contact_owner = owner
                self.assert_no_notification(self.new_message())

    def test_mentions_notify_only_active_mentioned_company_users_once_excluding_actor(self):
        # Mentions do not require stage notification rules or new-message settings.
        self.preferences.delete()
        # Repeat the owner to check deduplication; the actor, inactive user, and outsider
        # must receive nothing, leaving exactly one notification for the owner.
        payload = create_chatroom_notifications_payload(
            self.conversation, actor=self.agent,
            mentioned_user_ids=[self.owner.id, self.owner.id, self.agent.id, self.inactive.id, self.outsider.id],
        )
        title = "Agent mentioned you in a note on Customer"
        self.assert_recipients(payload, [self.owner], title, title)

    def test_note_mention_notifies_only_mentioned_user(self):
        # An active bystander must not receive the note alert just for sharing the company.
        User.objects.create(company=self.company, name="Bystander", mobile_number="105", lang="en")
        payload = create_chatroom_notifications_payload(
            self.conversation, actor=self.agent, mentioned_user_ids=[self.owner.id],
        )
        title = "Agent mentioned you in a note on Customer"
        self.assert_recipients(payload, [self.owner], title, title)

    def configure_stage_notification(self):
        # Role membership, company, and active status all matter for stage recipients.
        role = Role.objects.create(name="QA stage recipients")
        other_role = Role.objects.create(name="QA other stage recipients")
        for user in (self.owner, self.inactive, self.outsider):
            user.role = role
            user.save(update_fields=["role"])
        self.agent.role = other_role
        self.agent.save(update_fields=["role"])
        teammate = User.objects.create(
            company=self.company, name="Teammate", mobile_number="105", lang="en", role=role,
        )
        previous_stage = ConversationStage.objects.create(name="Previous QA stage")
        rule = ChatroomNotification.objects.create(
            company=self.company, role=role, stage=self.stage,
            message="Please review this conversation and follow up with the customer.",
        )
        # A rule for the old stage must not alert its role when entering the new stage.
        ChatroomNotification.objects.create(
            company=self.company, role=other_role, stage=previous_stage,
            message="This message belongs to the previous stage.",
        )
        return rule, previous_stage, teammate

    def test_stage_change_notifies_only_configured_role_with_settings_message(self):
        rule, previous_stage, teammate = self.configure_stage_notification()
        payload = create_chatroom_notifications_payload(
            self.conversation, old_stage_id=previous_stage.id, new_stage_id=self.stage.id,
        )
        self.assert_recipients(
            payload, [self.owner, teammate],
            "Conversation Customer moved to Notification QA", rule.message,
        )
        # The configured body must also survive serialization and reach push delivery.
        for notification in payload["notifications"]:
            self.assertEqual(notification["message"], rule.message)
        for push_call in self.push.call_args_list:
            self.assertEqual(push_call.args[1], rule.message)

    def test_stage_change_without_matching_settings_does_not_notify(self):
        self.configure_stage_notification()
        unconfigured_stage = ConversationStage.objects.create(name="Unconfigured QA stage")
        old_stage_id = self.conversation.stage_id
        self.conversation.stage = unconfigured_stage
        self.assert_no_notification(create_chatroom_notifications_payload(
            self.conversation, old_stage_id=old_stage_id, new_stage_id=unconfigured_stage.id,
        ))

    def test_unchanged_stage_does_not_notify_even_with_matching_settings(self):
        self.configure_stage_notification()
        self.assert_no_notification(create_chatroom_notifications_payload(
            self.conversation, old_stage_id=self.stage.id, new_stage_id=self.stage.id,
        ))

    def test_same_stage_sends_each_role_its_own_settings_message(self):
        rule, previous_stage, teammate = self.configure_stage_notification()
        other_rule = ChatroomNotification.objects.create(
            company=self.company, role=self.agent.role, stage=self.stage,
            message="Agent team: arrange a follow-up call.",
        )
        payload = create_chatroom_notifications_payload(
            self.conversation, old_stage_id=previous_stage.id, new_stage_id=self.stage.id,
        )
        expected = [
            (self.owner.id, rule.message), (teammate.id, rule.message),
            (self.agent.id, other_rule.message),
        ]
        records = Notification.objects.filter(conversation=self.conversation)
        # Check recipient/message pairs so a message sent to the wrong role cannot pass.
        self.assertCountEqual(records.values_list("user_id", "message"), expected)
        self.assertCountEqual(payload["notification_event"]["target_user_ids"], [uid for uid, _ in expected])
        self.assertCountEqual(
            [(row["id"], row["message"]) for row in payload["notifications"]],
            records.values_list("id", "message"),
        )
        self.assertCountEqual(
            [(user.id, call.args[1]) for call in self.push.call_args_list for user in call.args[3]],
            expected,
        )

    def test_other_company_stage_settings_do_not_trigger_notifications(self):
        rule, previous_stage, _ = self.configure_stage_notification()
        role = rule.role
        rule.delete()
        # Same stage and role, but only the other company has a matching rule.
        ChatroomNotification.objects.create(
            company=self.outsider.company, role=role, stage=self.stage,
            message="Other company's notification.",
        )
        self.assert_no_notification(create_chatroom_notifications_payload(
            self.conversation, old_stage_id=previous_stage.id, new_stage_id=self.stage.id,
        ))

    def test_stage_settings_message_resolves_conversation_placeholders(self):
        rule, previous_stage, teammate = self.configure_stage_notification()
        role = rule.role
        # Replace the setting using the supported delete-and-add workflow.
        rule.delete()
        ChatroomNotification.objects.create(
            company=self.company, role=role, stage=self.stage,
            message=("@conversation_name (@conversation_number) moved to @stage_name via "
                     "@connector_name; owner: @contact_owner; agent: @agent_name."),
        )
        payload = create_chatroom_notifications_payload(
            self.conversation, old_stage_id=previous_stage.id, new_stage_id=self.stage.id,
        )
        expected_message = "Customer (20001) moved to Notification QA via QA; owner: Owner; agent: Agent."
        self.assert_recipients(
            payload, [self.owner, teammate],
            "Conversation Customer moved to Notification QA", expected_message,
        )
        for row in payload["notifications"]:
            self.assertEqual(row["message"], expected_message)
        for call in self.push.call_args_list:
            self.assertEqual(call.args[1], expected_message)

    def test_mentions_do_not_also_notify_matching_stage_role(self):
        _, previous_stage, _ = self.configure_stage_notification()
        # Owner and teammate match the stage rule, but only the agent is mentioned.
        payload = create_chatroom_notifications_payload(
            self.conversation, old_stage_id=previous_stage.id, new_stage_id=self.stage.id,
            actor=self.owner, mentioned_user_ids=[self.agent.id],
        )
        title = "Owner mentioned you in a note on Customer"
        self.assert_recipients(payload, [self.agent], title, title)

    def test_duplicate_company_role_stage_setting_is_rejected(self):
        rule, _, _ = self.configure_stage_notification()
        # The database enforces one setting per company, role, and stage.
        # A savepoint lets us inspect the original row after the rejected insert.
        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                ChatroomNotification.objects.create(
                    company=self.company, role=rule.role, stage=self.stage,
                    message="A different message must not bypass uniqueness.",
                )
        self.assertEqual(ChatroomNotification.objects.filter(
            company=self.company, role=rule.role, stage=self.stage,
        ).count(), 1)
        original_message = rule.message
        rule.refresh_from_db()
        self.assertEqual(rule.message, original_message)
